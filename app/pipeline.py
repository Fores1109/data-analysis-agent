"""LangGraph 多 Agent 流水线：规划 → 分析 → 报告。

把「问一句话 → 直接回答」升级为可观测的多阶段流水线：
  规划 Agent（拆解子任务）→ 分析 Agent（对每步执行 pandas 代码）→ 报告 Agent（汇总成报告）

这是求职作品的技术架构亮点：展示了 Agent 编排（LangGraph 状态机）、
可观测的中间产物（计划/各步结果），也为将来加入人工审核节点留了位置。
"""
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .agent import build_agent


class PipelineState(TypedDict):
    question: str
    plan: list
    results: list
    report: str


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


def build_pipeline(df, llm, max_steps: int = 3, verbose: bool = False):
    """构建 LangGraph 多 Agent 流水线。"""

    def _plan(state: PipelineState) -> dict:
        resp = llm.invoke(PLANNER_PROMPT.format(question=state["question"]))
        text = resp.content if hasattr(resp, "content") else str(resp)
        steps = []
        for line in text.splitlines():
            m = re.match(r"^\s*\d+[.、)）]\s*(.+)$", line)
            if m:
                step = m.group(1).strip()
                if step and step not in steps:
                    steps.append(step)
        if not steps:  # 兜底：把整句当一步
            steps = [state["question"]]
        return {"plan": steps[:max_steps]}

    def _analyze(state: PipelineState) -> dict:
        agent = build_agent(df, llm, verbose=verbose)
        results = []
        for step in state["plan"]:
            try:
                out = agent.invoke({"input": step}).get("output", "")
            except Exception as e:
                out = f"（该步分析失败：{e}）"
            results.append(f"**{step}**\n\n{out}")
        return {"results": results}

    def _report(state: PipelineState) -> dict:
        body = "\n\n".join(state["results"])
        resp = llm.invoke(REPORT_PROMPT.format(question=state["question"], body=body))
        text = resp.content if hasattr(resp, "content") else str(resp)
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


def run_pipeline(df, question, llm, max_steps: int = 3, verbose: bool = False) -> dict:
    """运行一次流水线，返回 {plan, results, report}。"""
    app = build_pipeline(df, llm, max_steps=max_steps, verbose=verbose)
    return app.invoke({"question": question})
