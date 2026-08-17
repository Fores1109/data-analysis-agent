"""自研数据分析 Agent（v3）：LangGraph 显式 ReAct 循环 + 自定义工具集 + 沙箱代码执行 + 分层记忆。

替换 LangChain 官方 create_pandas_dataframe_agent（已标记 experimental）：
  - 显式 ReAct 循环：agent 节点（LLM 决策）→ 工具节点（执行）→ 条件边（继续 / 结束），
    循环上限 max_iterations，全流程消息可审计；
  - 自定义工具集：只读探索工具（df_head / df_columns / df_describe / df_shape / df_value_counts）
    + python_repl（通用 pandas 分析，双层安全防护）；
  - 分层记忆（app/memory.py）：工作记忆（最近 N 轮原文）+ 滚动摘要（LLM 递归压缩早期对话）
    + 长期记忆（结论文档字符级 TF-IDF 向量检索），每轮动态注入 system prompt。

安全设计（硬约束，区别于提示词软约束）——python_repl 的四道防线：
  1. AST 静态检查：执行前逐节点扫描，禁止 os/subprocess/socket/open/eval/exec 等危险调用、
     非白名单 import、写文件属性（to_csv/to_pickle 等）；
  2. 受限执行环境：只暴露 pandas/numpy/math 等白名单模块 + 过滤后的安全 builtins；
  3. 独立子进程执行：代码在单独进程运行，崩溃 / 死循环不影响主进程；
  4. 超时熔断：默认 30 秒强制终止。

接口兼容：build_agent(df) 返回带 .invoke({"input": q}) → {"output": str} 的对象，
api/main.py、app/pipeline.py、web 页面无需改动即可使用新引擎。
"""
import ast
import pickle
import subprocess
import sys
from typing import Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from .llm import create_llm
from .memory import AgentMemory

# ---------------------------------------------------------------------------
# 安全层：AST 静态检查 + 受限执行环境（在沙箱子进程中运行，见 _SANDBOX_WRAPPER）
# ---------------------------------------------------------------------------

# 允许导入的模块（根名）
ALLOWED_IMPORTS = {"pandas", "numpy", "math", "statistics", "datetime", "json", "re", "collections"}
# 禁止直接调用的名字
FORBIDDEN_CALLS = {
    "open", "eval", "exec", "compile", "__import__", "input", "exit", "quit",
    "help", "breakpoint", "globals", "locals", "vars", "getattr", "setattr",
    "delattr", "super", "classmethod", "staticmethod", "memoryview",
}
# 禁止访问的属性（写文件 / 外部 IO）
FORBIDDEN_ATTRS = {
    "to_csv", "to_pickle", "to_excel", "to_hdf", "to_parquet", "to_feather",
    "to_stata", "to_json", "read_csv", "read_excel", "read_pickle", "read_json",
    "read_sql", "read_parquet", "read_feather", "read_hdf", "read_table", "read_fwf",
}


class UnsafeCodeError(Exception):
    """生成的代码触发了安全策略。"""


def _call_name(func) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _check_ast(code: str):
    """AST 静态检查：在沙箱外先做第一道扫描，快速失败。"""
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise UnsafeCodeError(f"禁止导入模块：{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise UnsafeCodeError(f"禁止导入模块：{node.module}")
            for alias in node.names:
                if alias.name == "*" or alias.name in FORBIDDEN_CALLS:
                    raise UnsafeCodeError(f"禁止导入：{alias.name}")
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name and (name in FORBIDDEN_CALLS or name.startswith("__")):
                raise UnsafeCodeError(f"禁止调用：{name}")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                raise UnsafeCodeError(f"禁止访问属性：{node.attr}（写文件 / 外部 IO 不被允许）")
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_CALLS:
                raise UnsafeCodeError(f"禁止使用：{node.id}")
    return tree


# 沙箱子进程脚本：stdin 收 pickle 载荷 {code, df}，stdout 回 pickle 结果
# 独立进程保证：主进程不受崩溃 / 死循环影响；超时由 subprocess timeout 熔断
_SANDBOX_WRAPPER = r"""
import pickle, sys, io, ast, contextlib

payload = pickle.loads(sys.stdin.buffer.read())
code, df = payload["code"], payload["df"]

ALLOWED_IMPORTS = {"pandas", "numpy", "math", "statistics", "datetime", "json", "re", "collections"}
FORBIDDEN_CALLS = {"open", "eval", "exec", "compile", "__import__", "input", "exit", "quit",
                   "help", "breakpoint", "globals", "locals", "vars", "getattr", "setattr",
                   "delattr", "super", "classmethod", "staticmethod", "memoryview"}
FORBIDDEN_ATTRS = {"to_csv", "to_pickle", "to_excel", "to_hdf", "to_parquet", "to_feather",
                   "to_stata", "to_json", "read_csv", "read_excel", "read_pickle", "read_json",
                   "read_sql", "read_parquet", "read_feather", "read_hdf", "read_table", "read_fwf"}

class UnsafeCodeError(Exception): pass

def call_name(func):
    if isinstance(func, ast.Name): return func.id
    if isinstance(func, ast.Attribute): return func.attr
    return None

def check(code):
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    raise UnsafeCodeError(f"禁止导入模块: {a.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise UnsafeCodeError(f"禁止导入模块: {node.module}")
            for a in node.names:
                if a.name == "*" or a.name in FORBIDDEN_CALLS:
                    raise UnsafeCodeError(f"禁止导入: {a.name}")
        elif isinstance(node, ast.Call):
            name = call_name(node.func)
            if name and (name in FORBIDDEN_CALLS or name.startswith("__")):
                raise UnsafeCodeError(f"禁止调用: {name}")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                raise UnsafeCodeError(f"禁止访问属性: {node.attr} (写文件/外部IO)")
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_CALLS:
                raise UnsafeCodeError(f"禁止使用: {node.id}")
    return tree

def safe_builtins():
    import builtins
    drop = {"open", "eval", "exec", "compile", "__import__", "input", "exit", "quit", "help",
            "breakpoint", "memoryview", "getattr", "setattr", "delattr", "globals", "locals",
            "vars", "super", "classmethod", "staticmethod", "bytes", "bytearray",
            "copyright", "credits", "license"}
    return {k: v for k, v in vars(builtins).items() if k not in drop}

def fmt(v):
    try:
        import pandas as pd
        if isinstance(v, pd.DataFrame):
            return f"DataFrame {v.shape}:\n{v.head(30).to_string()}"
        if isinstance(v, pd.Series):
            return f"Series len={len(v)}:\n{v.head(30).to_string()}"
    except Exception:
        pass
    return repr(v)

out = {"ok": False, "text": "", "stdout": "", "error": ""}
buf = io.StringIO()
try:
    tree = check(code)
    import pandas as pd, numpy as np, math, statistics, datetime, json, re, collections
    restricted = {"pandas": pd, "pd": pd, "numpy": np, "np": np, "math": math,
                  "statistics": statistics, "datetime": datetime, "json": json,
                  "re": re, "collections": collections, "df": df, "_result": None}
    restricted["__builtins__"] = safe_builtins()
    with contextlib.redirect_stdout(buf):
        exec(compile(tree, "<sandbox>", "exec"), restricted)
    out["ok"] = True
    out["text"] = fmt(restricted.get("_result"))
    out["stdout"] = buf.getvalue()[-2000:]
except UnsafeCodeError as e:
    out["error"] = f"[安全拦截] {e}"
except Exception as e:
    out["error"] = f"{type(e).__name__}: {e}"
out["stdout"] = (out["stdout"] or "")[-2000:]
sys.stdout.buffer.write(pickle.dumps(out))
"""


def run_code_sandboxed(code: str, df, timeout: int = 30) -> dict:
    """在独立子进程中执行用户/LLM 生成的 pandas 代码（双层防护 + 进程隔离 + 超时熔断）。"""
    if not code or not code.strip():
        return {"ok": False, "text": "", "stdout": "", "error": "代码为空"}
    # 第一道闸：主进程先做 AST 静态检查（快速失败，不启动进程）
    try:
        _check_ast(code)
    except UnsafeCodeError as e:
        return {"ok": False, "text": "", "stdout": "", "error": f"[安全拦截] {e}"}
    except SyntaxError as e:
        return {"ok": False, "text": "", "stdout": "", "error": f"语法错误：{e}"}
    payload = pickle.dumps({"code": code, "df": df})
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _SANDBOX_WRAPPER],
            input=payload, capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "text": "", "stdout": "", "error": f"代码执行超时（>{timeout}s），已强制终止"}
    if proc.returncode != 0:
        return {"ok": False, "text": "", "stdout": "",
                "error": f"执行进程异常退出：{proc.stderr.decode('utf-8', 'replace')[-1000:]}"}
    try:
        return pickle.loads(proc.stdout)
    except Exception:
        return {"ok": False, "text": "", "stdout": "", "error": "无法解析执行结果"}


# ---------------------------------------------------------------------------
# 自定义工具集
# ---------------------------------------------------------------------------

def _get_df(dfs: dict, df_name: str):
    if df_name not in dfs:
        raise ValueError(f"数据表不存在：{df_name}（可用：{list(dfs)}）")
    return dfs[df_name]


def build_tools(dfs: dict):
    """构建自定义工具集。dfs: {名称: DataFrame}。"""
    import pandas as pd

    @tool
    def df_shape(df_name: str = "data") -> str:
        """查看数据表形状（行数、列数）。"""
        df = _get_df(dfs, df_name)
        return f"形状：{df.shape[0]} 行 × {df.shape[1]} 列"

    @tool
    def df_columns(df_name: str = "data") -> str:
        """查看数据表所有列名与数据类型。"""
        df = _get_df(dfs, df_name)
        return "\n".join(f"- {c}（{str(dt)}）" for c, dt in zip(df.columns, df.dtypes))

    @tool
    def df_head(df_name: str = "data", n: int = 5) -> str:
        """查看数据表前 n 行（默认 5 行）。"""
        df = _get_df(dfs, df_name)
        return df.head(max(1, min(int(n), 50))).to_string()

    @tool
    def df_describe(df_name: str = "data") -> str:
        """数值列的统计描述（count/mean/std/min/分位数/max）。"""
        df = _get_df(dfs, df_name)
        return df.describe().to_string()

    @tool
    def df_value_counts(df_name: str = "data", column: str = "", top_n: int = 10) -> str:
        """统计某列取值分布（频数、占比），用于类别列/分组字段。"""
        df = _get_df(dfs, df_name)
        if column not in df.columns:
            raise ValueError(f"列不存在：{column}")
        vc = df[column].value_counts(dropna=False).head(max(1, min(int(top_n), 50)))
        pct = (vc / len(df) * 100).round(2)
        return pd.DataFrame({"取值": vc.index, "频数": vc.values, "占比%": pct.values}).to_string(index=False)

    @tool
    def python_repl(code: str, df_name: str = "data") -> str:
        """执行 pandas/Python 代码做自定义分析（在安全沙箱中运行）。

        约定：
        - 数据表变量名为 df（可通过 df_name 指定其它表）；
        - 把最终结果赋给 _result（如 _result = df.groupby('城市')['销售额'].sum()）；
        - 只读分析：禁止写文件、访问网络、执行系统命令（有静态检查拦截）；
        - 代码超时 30 秒会被强制终止。
        """
        df = _get_df(dfs, df_name)
        res = run_code_sandboxed(code, df)
        if not res.get("ok"):
            return f"执行失败：{res.get('error', '未知错误')}"
        parts = []
        if res.get("text"):
            parts.append(res["text"])
        if res.get("stdout", "").strip():
            parts.append(f"[print 输出]\n{res['stdout'].strip()}")
        return "\n".join(parts) or "（代码执行成功，无输出；请把结果赋给 _result）"

    return [df_shape, df_columns, df_head, df_describe, df_value_counts, python_repl]


# ---------------------------------------------------------------------------
# LangGraph 显式 ReAct 循环
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    question: str
    messages: list          # 本次运行的消息（AI 决策 / 工具结果）
    answer: str
    steps: int
    memory_context: str     # 分层记忆注入的上下文（摘要 + 检索结论 + 最近对话）


def _system_prompt(df, include_preview: bool) -> str:
    cols = "\n".join(f"- {c}（{str(dt)}）" for c, dt in zip(df.columns, df.dtypes))
    return f"""你是一位资深数据分析师，通过工具分析一张数据表（变量名 df）。

数据表概览：
- 形状：{df.shape[0]} 行 × {df.shape[1]} 列
- 列：
{cols}
{"- （数据量大，未在提示词中展示明细，请用 df_head/df_describe/python_repl 自行探查）" if not include_preview else ""}

工作方式：
1. 先用 df_shape / df_columns / df_head / df_describe 了解数据，再决定分析方案；
2. 需要自定义计算时用 python_repl：把最终结果赋给 _result（如 _result = df.groupby('城市')['销售额'].sum()）；
3. 得到结果后用中文给出结论：关键指标给出具体数值（可带单位/百分比），输出精炼，不要贴大段代码；
4. 若问题含糊，先简述你的理解，再给出最有用的一层分析；
5. 回答必须基于工具返回的真实结果，严禁编造数字。

安全约束（工具层已强制，仍需遵守）：
- 只做只读数据分析；禁止写文件、访问网络、执行系统命令；
- 如用户要求危险操作，礼貌拒绝并说明。"""


def build_agent(df, llm=None, verbose=False, max_iterations=8, df_prompt_cells=20000,
                sandbox_timeout=30, memory=None, memory_kwargs=None):
    """构建自研数据分析 Agent（LangGraph 显式 ReAct 循环 + 沙箱工具 + 分层记忆）。

    参数:
        df: pandas.DataFrame
        llm: 支持函数调用的 ChatModel；为 None 时按 .env 配置创建
        verbose: 打印思考过程（调试用）
        max_iterations: 单次回答最多工具调用轮数
        df_prompt_cells: 数据元素总数超过该值时不把数据明细塞进提示词
        sandbox_timeout: python_repl 单次执行超时（秒）
        memory: 传入现成的 AgentMemory 实例（多 Agent 共享记忆时用）；默认新建
        memory_kwargs: AgentMemory 构造参数（如 {"working_rounds": 4, "summarize_at": 8, "top_k": 3}）
    """
    import pandas as pd

    llm = llm or create_llm()
    dfs = {"data": df}
    tools = build_tools(dfs)
    tools_by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)
    include_preview = (df.shape[0] * df.shape[1]) < df_prompt_cells
    base_system = _system_prompt(df, include_preview)

    def agent_node(state: AgentState) -> dict:
        content = base_system
        mem_ctx = state.get("memory_context", "")
        if mem_ctx:
            content = f"{base_system}\n\n{mem_ctx}"
        messages = [SystemMessage(content=content)] + list(state.get("messages", [])) + [
            HumanMessage(content=state["question"])
        ]
        if verbose:
            print(f"[agent] 第 {state.get('steps', 0) + 1} 轮决策...", file=sys.stderr)
        resp = llm_with_tools.invoke(messages)
        new_msgs = list(state.get("messages", [])) + [resp]
        return {"messages": new_msgs, "steps": state.get("steps", 0) + 1}

    def tool_node(state: AgentState) -> dict:
        last = state["messages"][-1]
        results = []
        for tc in getattr(last, "tool_calls", []) or []:
            t = tools_by_name.get(tc.get("name", ""))
            if t is None:
                results.append(ToolMessage(content=f"未知工具：{tc.get('name')}",
                                           tool_call_id=tc.get("id", "")))
                continue
            try:
                out = t.invoke(tc.get("args", {}))
            except Exception as e:  # noqa: BLE001 - 工具失败转成可读消息喂回 LLM
                out = f"工具执行失败：{type(e).__name__}: {e}"
            results.append(ToolMessage(content=str(out), tool_call_id=tc.get("id", "")))
        if verbose:
            for r in results:
                print(f"[tool] {r.content[:200]}", file=sys.stderr)
        return {"messages": state["messages"] + results}

    def route(state: AgentState) -> str:
        last = state["messages"][-1]
        has_calls = bool(getattr(last, "tool_calls", None))
        if has_calls and state.get("steps", 0) < max_iterations:
            return "tools"
        return "end"

    def end_node(state: AgentState) -> dict:
        last = state["messages"][-1]
        return {"answer": getattr(last, "content", "") or "（Agent 未能生成回答）"}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("end", end_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", "end": "end"})
    graph.add_edge("tools", "agent")
    graph.add_edge("end", END)
    app = graph.compile()
    return AgentRuntime(app, llm=llm, memory=memory, memory_kwargs=memory_kwargs)


class AgentRuntime:
    """Agent 运行时：分层记忆（工作/摘要/长期检索）+ 兼容旧接口（.invoke({"input": q}) → {"output": str}）。"""

    def __init__(self, app, llm=None, memory=None, memory_kwargs=None):
        self._app = app
        self._memory = memory or AgentMemory(llm=llm, **(memory_kwargs or {}))

    def invoke(self, payload: dict, config: dict | None = None) -> dict:
        question = payload.get("input", "")
        mem_ctx = self._memory.build_context(question)
        result = self._app.invoke({
            "question": question,
            "messages": [],
            "answer": "",
            "steps": 0,
            "memory_context": mem_ctx,
        }, config=config)
        answer = result.get("answer", "")
        # 记忆：问答结束后入库（长期记忆 + 工作记忆 + 可能的滚动摘要）
        self._memory.remember(question, answer)
        return {"output": answer}

    def clear_history(self):
        self._memory.clear()


def ask(df, question, llm=None, verbose=False, **kwargs):
    """一句话封装：给定数据和问题，返回 Agent 的回答文本。"""
    agent = build_agent(df, llm=llm, verbose=verbose, **kwargs)
    return agent.invoke({"input": question}).get("output", "")
