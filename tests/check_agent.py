"""验证 Agent 构建（不调用 LLM、不花 token）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from langchain_openai import ChatOpenAI

from app.agent import build_agent

df = pd.DataFrame({"月份": ["1月", "2月", "3月"], "销售额": [100, 200, 300]})
llm = ChatOpenAI(model="deepseek-chat", api_key="sk-placeholder", base_url="https://api.deepseek.com")
agent = build_agent(df, llm)
print("✓ Agent 构建成功:", type(agent).__name__)
print("✓ 绑定工具:", ", ".join(t.name for t in agent.tools))
