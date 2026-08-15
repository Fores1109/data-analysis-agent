"""核心 Agent：基于 LangChain 官方 create_pandas_dataframe_agent。

架构参考 khang3004/DataAnalysis_Agent：
  - 用户自然语言问题 → Agent 自动编写并执行 pandas 代码 → 返回分析结论
  - 本模块是二次开发主战场，可在此扩展自定义工具
"""
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent

from .llm import create_llm

SYSTEM_PREFIX = """你是一位资深数据分析师。用户提供了一张数据表（DataFrame）。
请根据用户的自然语言问题，编写 pandas/Python 代码完成分析，并给出清晰的中文结论。

要求：
1. 先执行代码得到真实结果，再回答；严禁编造数字；
2. 关键指标给出具体数值（可带单位、百分比）；
3. 若问题含糊，先简述你的理解，再给出最有用的一层分析；
4. 输出精炼，可用要点列表，不要贴大段代码；
5. 如需清洗（空值、类型转换），先做预处理并简要说明。"""


def build_agent(df, llm=None, verbose=False, max_iterations=20):
    """构建一个可与 DataFrame 对话的 Agent。

    参数:
        df: pandas.DataFrame
        llm: 支持函数调用的 ChatModel；为 None 时按 .env 配置创建
        verbose: 打印思考过程（调试用）
        max_iterations: 单次回答最多执行几步代码
    """
    llm = llm or create_llm()
    # 数据很大时不把 DataFrame 塞进提示词，节省 token（Agent 会自己用代码读取）
    include_df_in_prompt = (df.shape[0] * df.shape[1]) < 20000
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        prefix=SYSTEM_PREFIX,
        verbose=verbose,
        agent_type=AgentType.OPENAI_FUNCTIONS,  # DeepSeek/OpenAI/Ollama(qwen) 均支持函数调用
        include_df_in_prompt=include_df_in_prompt,
        allow_dangerous_code=True,              # LangChain 官方要求显式允许执行 pandas 代码
        max_iterations=max_iterations,
        handle_parsing_errors=True,
    )


def ask(df, question, llm=None, verbose=False):
    """一句话封装：给定数据和问题，返回 Agent 的回答文本。"""
    agent = build_agent(df, llm=llm, verbose=verbose)
    result = agent.invoke({"input": question})
    return result.get("output", "")
