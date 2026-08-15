"""💬 自然语言问答分析：对当前数据用自然语言提问，Agent 自动写 pandas 代码分析。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.agent import build_agent
from app.llm import create_llm
from app.theme import apply_theme, page_header

st.set_page_config(page_title="自然语言分析", page_icon="💬", layout="wide")
apply_theme()
page_header("💬", "自然语言问答分析", "对当前数据用自然语言提问，Agent 自动编写并执行 pandas 代码，返回结论")

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df

try:
    llm = create_llm()
except Exception as e:
    st.error(f"LLM 配置错误：{e}")
    st.stop()

# 数据变化时重建 Agent（缓存于会话中，避免重复初始化）
key = st.session_state.get("data_key")
if "agent" not in st.session_state or st.session_state.get("_agent_key") != key:
    with st.spinner("正在初始化 Agent..."):
        try:
            st.session_state["agent"] = build_agent(df, llm)
            st.session_state["_agent_key"] = key
        except Exception as e:
            st.error(f"Agent 初始化失败：{e}")
            st.stop()
agent = st.session_state.get("agent")
if agent is None:
    st.error("Agent 尚未就绪，请回到「首页」重新加载数据。")
    st.stop()

if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

# 渲染历史
for q, a in st.session_state["qa_history"]:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write(a)

q = st.chat_input("例如：哪个月的销售额最高？各城市平均销售额是多少？")
if q:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        with st.spinner("分析中（可能需要几步代码）..."):
            try:
                ans = agent.invoke({"input": q}).get("output", "")
            except Exception as e:
                ans = f"❌ 出错：{e}"
        st.write(ans)
    st.session_state["qa_history"].append((q, ans))
