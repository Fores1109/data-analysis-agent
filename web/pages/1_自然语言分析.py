"""💬 自然语言问答分析：经典单 Agent 或 LangGraph 多 Agent 流水线。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from app.agent import build_agent
from app.llm import create_llm
from app.pipeline import build_pipeline
from app.theme import apply_theme, page_header

st.set_page_config(page_title="自然语言分析", page_icon="💬", layout="wide")
apply_theme()
page_header("💬", "自然语言问答分析", "对当前数据用自然语言提问；可切换「经典单 Agent」或「LangGraph 多 Agent 流水线（规划→分析→报告）」")

with st.expander("🛡️ 安全须知（重要）"):
    st.markdown(
        "本页面会让 AI 生成并**执行 pandas 代码**来分析您的数据（代码在您的机器上运行）。\n\n"
        "- 系统提示词已约束 Agent **只做只读分析**：禁止删改文件、访问网络、执行系统命令；\n"
        "- 请**仅对您信任的数据文件和问题**使用本功能，不要在包含密钥/密码的文件上提问；\n"
        "- 更严格的隔离方案（容器/沙箱运行）见 README「安全说明」。"
    )

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df

try:
    llm = create_llm()
except Exception as e:
    st.error(f"LLM 配置错误：{e}")
    st.stop()

engine = st.radio("分析引擎", ["经典单 Agent（快）", "多 Agent 流水线（LangGraph）"],
                  horizontal=True, key="engine")
key = st.session_state.get("data_key")

# 按引擎分别缓存（数据变化时重建）
if engine == "多 Agent 流水线（LangGraph）":
    if "pipeline" not in st.session_state or st.session_state.get("_pipe_key") != key:
        with st.spinner("正在初始化 LangGraph 流水线..."):
            try:
                st.session_state["pipeline"] = build_pipeline(df, llm)
                st.session_state["_pipe_key"] = key
            except Exception as e:
                st.error(f"流水线初始化失败：{e}")
                st.stop()
    engine_obj = st.session_state["pipeline"]
else:
    if "agent" not in st.session_state or st.session_state.get("_agent_key") != key:
        with st.spinner("正在初始化 Agent..."):
            try:
                st.session_state["agent"] = build_agent(df, llm)
                st.session_state["_agent_key"] = key
            except Exception as e:
                st.error(f"Agent 初始化失败：{e}")
                st.stop()
    engine_obj = st.session_state.get("agent")
    if engine_obj is None:
        st.error("Agent 尚未就绪，请回到「首页」重新加载数据。")
        st.stop()

if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

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
        if engine == "多 Agent 流水线（LangGraph）":
            with st.spinner("流水线执行中：规划 → 逐项分析 → 生成报告（可能较慢）..."):
                try:
                    result = engine_obj.invoke({"question": q})
                    with st.expander(f"📋 规划（{len(result['plan'])} 步）"):
                        for i, step in enumerate(result["plan"], 1):
                            st.markdown(f"{i}. {step}")
                    for i, res in enumerate(result.get("results", []), 1):
                        with st.expander(f"🔧 第 {i} 步分析结果"):
                            st.markdown(res)
                    audit = result.get("audit", [])
                    if audit:
                        with st.expander("📜 审计日志（每步状态 / 耗时 / 错误）"):
                            st.dataframe(pd.DataFrame(audit), width='stretch')
                    ans = result.get("report", "")
                    st.markdown("---")
                    st.markdown(ans)
                except Exception as e:
                    ans = f"❌ 流水线出错：{e}"
                    st.write(ans)
        else:
            with st.spinner("分析中（可能需要几步代码）..."):
                try:
                    ans = engine_obj.invoke({"input": q}).get("output", "")
                except Exception as e:
                    ans = f"❌ 出错：{e}"
            st.write(ans)
    st.session_state["qa_history"].append((q, ans))
