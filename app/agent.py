"""核心 Agent：基于 LangChain 官方 create_pandas_dataframe_agent。

架构参考 khang3004/DataAnalysis_Agent：
  - 用户自然语言问题 → Agent 自动编写并执行 pandas 代码 → 返回分析结论
  - 本模块是二次开发主战场，可在此扩展自定义工具

安全说明（重要）：
  - LangChain 要求显式开启 allow_dangerous_code 才能让 Agent 执行生成的代码，
    这本质上是在运行 LLM 生成的任意 Python 代码。
  - 本模块的缓解措施：
      1) 系统提示词（SYSTEM_PREFIX）约束 Agent 只做只读数据分析，
         禁止删改文件、访问网络、执行系统命令、读取敏感信息；
      2) API 层对 data_path 做了路径白名单校验（见 api/main.py）；
      3) 仍建议仅在隔离环境（Docker 容器 / 沙箱 VM / 受限账户）部署，
         且只对可信数据与可信问题使用该功能（详见 README「安全说明」）。
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
5. 如需清洗（空值、类型转换），先做预处理并简要说明。

安全约束（必须无条件遵守）：
1. 只允许做只读数据分析：读取、统计、聚合、可视化 DataFrame；
2. 严禁执行任何修改/删除/写入文件系统的操作，严禁访问网络
   （requests/urllib/socket 等），严禁执行系统命令
   （os.system/subprocess/shell/exec 等），严禁导入危险模块；
3. 严禁读取或输出敏感信息（API 密钥、密码、令牌等）；
4. 如果用户要求执行上述危险操作，礼貌拒绝并解释这是只读分析环境。"""


def build_agent(df, llm=None, verbose=False, max_iterations=20, df_prompt_cells=20000):
    """构建一个可与 DataFrame 对话的 Agent。

    参数:
        df: pandas.DataFrame
        llm: 支持函数调用的 ChatModel；为 None 时按 .env 配置创建
        verbose: 打印思考过程（调试用）
        max_iterations: 单次回答最多执行几步代码
        df_prompt_cells: DataFrame 元素总数超过该值时不把数据塞进提示词
                         （节省 token；Agent 会自己用代码读取）
    """
    llm = llm or create_llm()
    include_df_in_prompt = (df.shape[0] * df.shape[1]) < df_prompt_cells
    return create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        prefix=SYSTEM_PREFIX,
        verbose=verbose,
        agent_type=AgentType.OPENAI_FUNCTIONS,  # DeepSeek/OpenAI/Ollama(qwen) 均支持函数调用
        include_df_in_prompt=include_df_in_prompt,
        allow_dangerous_code=True,              # LangChain 官方要求显式允许执行 pandas 代码（见模块顶部安全说明）
        max_iterations=max_iterations,
    )


def ask(df, question, llm=None, verbose=False):
    """一句话封装：给定数据和问题，返回 Agent 的回答文本。"""
    agent = build_agent(df, llm=llm, verbose=verbose)
    result = agent.invoke({"input": question})
    return result.get("output", "")
