"""LangGraph 多 Agent 流水线：规划 → 分析 → 报告（v2：健壮解析 / 自动重试 / 可审计）。

把「问一句话 → 直接回答」升级为可观测的多阶段流水线：
  规划 Agent（拆解子任务）→ 分析 Agent（对每步执行 pandas 代码，失败自动重试）→ 报告 Agent（汇总成报告）

v2 相对 v1 的改进：
  - 规划解析更健壮：支持 "1. " / "1、" / "1) " / "1）" / "1: " / "- " / "* " / "• " 等
    常见列表格式，兼容 markdown 列表与中文序号，带引号/冒号前缀的条目也能正确提取；
  - 单步失败不中断：分析步骤失败自动重试（默认 1 次），仍失败则记录错误、继续后续步骤；
  - 全流程可审计：返回每步的 状态 / 耗时 / 错误信息，前端可展开查看；
  - 预留人工审核位：require_review=True 时报告标记为「待审核」，为接入人工审核节点留扩展位。

这是求职作品的技术架构亮点：展示了 Agent 编排（LangGraph 状态机）、
可观测的中间产物（计划 / 各步结果 / 审计日志），也为将来加入人工审核节点留了位置。
"""
import re
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .agent import build_agent


class PipelineState(TypedDict):
    question: str
    plan: list
    results: list
    report: str
    audit: list  # 每步执行的审计信息 [{step, status, elapsed, error}]


PLANNER_PROMPT = """你是数据分析规划师。请把用户的问题拆解成不超过 3 个可独立执行的子问题，
每个子问题必须能用 pandas 直接算出来，并注意子问题之间不要重复。

用户问题：{question}

只输出编号列表，例如：
1. 按月份汇总总销售额
2. 找出销售额最高的商品
3. 分析各城市销售占比"""

REPORT_PROMPT = """你是数据分析报告撰写人。根据下面的分析结果，用中文写一份简洁的 Markdown 报告：
包含「核心结论」「关键数据」「建议」三部分。必须引用结果中的具体数字，不要编造。

用户问题：{question}

分析过程与结果：
{body}"""

# 兼容多种列表格式：1. / 1、 / 1) / 1） / 1: / - / * / • / · 等
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*•·]|\d+[.、)）:])\s*(.+?)\s*$")
# 去掉「第1步：」「子问题1：」这类序号前缀
_STEP_PREFIX_RE = re.compile(r"^(?:第\s*\d+\s*[步个]?[：:]\s*|子问题\s*\d+[：:]\s*)")


def _parse_plan(text: str, max_steps: int, fallback: str) -> list:
    """从 LLM 输出中提取步骤列表；解析失败时用整句兜底。"""
    steps = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _LIST_ITEM_RE.match(line)
        step = m.group(1).strip().strip('"\'`“”‘’') if m else line
        step = _STEP_PREFIX_RE.sub("", step).strip()
        if step and step not in steps:
            steps.append(step)
    if not steps:  # 兜底：把整句当一步
        steps = [fallback]
    return steps[:max_steps]


def _run_step(agent, step: str, max_retries: int):
    """执行单个分析步骤，失败自动重试。返回 (status, output, error)。"""
    last_err = None
    for _ in range(max_retries + 1):
        try:
            out = agent.invoke({"input": step}).get("output", "")
            if out.strip():
                return "成功", out, None
            last_err = "无输出"
        except Exception as e:  # noqa: BLE001 - 单步失败不应中断整条流水线
            last_err = str(e)
    return "失败", "", last_err


def build_pipeline(df, llm, max_steps: int = 3, verbose: bool = False,
                   max_retries: int = 1, require_review: bool = False):
    """构建 LangGraph 多 Agent 流水线。

    参数:
        max_steps: 最多拆解几个子问题（默认 3）
        max_retries: 单个分析步骤失败后的重试次数（默认 1）
        require_review: True 时在报告前标记「待人工审核」（预留人工审核节点扩展位）
    """

    def _plan(state: PipelineState) -> dict:
        resp = llm.invoke(PLANNER_PROMPT.format(question=state["question"]))
        text = resp.content if hasattr(resp, "content") else str(resp)
        return {"plan": _parse_plan(text, max_steps, state["question"])}

    def _analyze(state: PipelineState) -> dict:
        agent = build_agent(df, llm, verbose=verbose)
        results, audit = [], []
        for step in state["plan"]:
            start = time.time()
            status, out, error = _run_step(agent, step, max_retries)
            if not out.strip():
                out = f"（该步分析失败：{error or '无输出'}）"
            results.append(f"**{step}**\n\n{out}")
            audit.append({
                "step": step,
                "status": status,
                "elapsed": round(time.time() - start, 2),
                "error": error or "",
            })
        return {"results": results, "audit": audit}

    def _report(state: PipelineState) -> dict:
        body = "\n\n".join(state["results"])
        resp = llm.invoke(REPORT_PROMPT.format(question=state["question"], body=body))
        text = resp.content if hasattr(resp, "content") else str(resp)
        if require_review:
            text = "> ⏳ 本报告待人工审核后发布（require_review 已开启）。\n\n" + text
        return {"report": text}

    graph = StateGraph(PipelineState)
    graph.add_node("规划", _plan)
    graph.add_node("分析", _analyze)
    graph.add_node("报告", _report)
    graph.add_edge(START, "规划")
    graph.add_edge("规划", "分析")
    graph.add_edge("分析", "报告")
    graph.add_edge("报告", END)
    return graph.compile()


def run_pipeline(df, question, llm, max_steps: int = 3, verbose: bool = False, **kwargs) -> dict:
    """运行一次流水线，返回 {plan, results, report, audit}。kwargs 透传给 build_pipeline。"""
    app = build_pipeline(df, llm, max_steps=max_steps, verbose=verbose, **kwargs)
    return app.invoke({"question": question})
