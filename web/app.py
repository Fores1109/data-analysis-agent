"""📊 数据分析 Agent —— 首页：数据源加载与数据概览。

启动：streamlit run web/app.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from app import config
from app.data_source import load_api, load_db, load_file

st.set_page_config(page_title="数据分析 Agent", page_icon="📊", layout="wide")
st.title("📊 数据分析 Agent")
st.caption("基于 LangChain 的多功能数据分析助手：自然语言问答 · 图表 · SQL 助手 · A/B 实验 · 机器学习 · 因果推断 · 报告")


def remember(df, name):
    """把加载的数据存入会话，并让其他页面感知数据已更换。"""
    st.session_state["df"] = df
    st.session_state["data_name"] = name
    st.session_state["data_key"] = f"{name}_{df.shape[0]}x{df.shape[1]}"
    for k in ("agent", "_agent_key", "column_hints", "qa_history", "ml_result", "schema"):
        st.session_state.pop(k, None)


# ---------- 侧边栏：数据源 ----------
with st.sidebar:
    st.header("📥 数据源")
    source = st.radio("选择数据来源", ["上传文件", "示例数据", "数据库查询", "API 接口"], key="source_type")

    if source == "上传文件":
        f = st.file_uploader("CSV / Excel / JSON", type=["csv", "xlsx", "xls", "json"])
        if f is not None:
            try:
                remember(load_file(f), f.name)
                st.success(f"已加载 {f.name}")
            except Exception as e:
                st.error(f"读取失败：{e}")

    elif source == "示例数据":
        if st.button("加载示例销售数据"):
            try:
                remember(load_file("data/sample_sales.csv"), "示例销售数据 sales.csv")
                st.success("已加载示例数据")
            except Exception as e:
                st.error(f"加载失败：{e}")

    elif source == "数据库查询":
        url = st.text_input("数据库连接串", value=config.DB_URL, key="db_url_input")
        query = st.text_area("SQL 查询", "SELECT * FROM table_name LIMIT 1000", key="db_query_input")
        if st.button("执行查询", key="db_run"):
            try:
                remember(load_db(query, url), f"数据库：{url}")
                st.success("查询成功")
            except Exception as e:
                st.error(f"查询失败：{e}")

    elif source == "API 接口":
        url = st.text_input("接口地址", key="api_url_input")
        path = st.text_input("数据路径（可选，如 data.items）", key="api_path_input")
        if st.button("请求接口", key="api_run"):
            try:
                remember(load_api(url, json_path=path or None), f"API：{url}")
                st.success("请求成功")
            except Exception as e:
                st.error(f"请求失败：{e}")

    st.divider()
    st.caption("💡 加载数据后，用左侧导航进入各功能页面（会话数据会共享）。")

# ---------- 主页：概览 ----------
df = st.session_state.get("df")
if df is None:
    st.info("👈 请先在左侧选择数据源并加载数据")
    st.stop()

st.subheader(f"数据概览：{st.session_state.get('data_name', '未命名')}")
c1, c2, c3 = st.columns(3)
c1.metric("行数", df.shape[0])
c2.metric("列数", df.shape[1])
c3.metric("缺失值总数", int(df.isna().sum().sum()))

tab1, tab2, tab3 = st.tabs(["数据预览", "统计描述", "数据类型"])
with tab1:
    st.dataframe(df.head(100), width='stretch')
with tab2:
    num = df.select_dtypes(include="number")
    if num.shape[1]:
        st.dataframe(num.describe().T, width='stretch')
    else:
        st.info("当前没有数值列")
with tab3:
    st.dataframe(
        pd.DataFrame({"列名": df.columns, "类型": df.dtypes.astype(str).values}),
        width='stretch',
    )

# ---------- 悬停解释设置 ----------
st.subheader("📖 悬停解释设置")
st.caption("为列写一句话说明（图表悬浮提示、回归系数解释会用到）；也可一键让 LLM 自动生成。")
if "column_hints" not in st.session_state:
    st.session_state["column_hints"] = {c: "" for c in df.columns}

hints = st.session_state["column_hints"]
col_left, col_right = st.columns([3, 1])
with col_right:
    if st.button("🤖 LLM 生成列解释"):
        try:
            from app.llm import create_llm
            from langchain_core.prompts import ChatPromptTemplate
            llm = create_llm()
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是数据字典专家。为以下每列写一句不超过 20 字的中文说明，格式：列名：说明。"),
                ("user", "列名列表：{cols}"),
            ])
            resp = llm.invoke(prompt.format(cols="、".join(df.columns)))
            text = resp.content if hasattr(resp, "content") else str(resp)
            for line in text.splitlines():
                if "：" in line:
                    k, _, v = line.partition("：")
                    k = k.strip().strip("-").strip()
                    if k in hints:
                        hints[k] = v.strip()
            st.success("已生成，请查看下方并可手动修改")
        except Exception as e:
            st.error(f"生成失败：{e}")
with col_left:
    with st.expander("编辑列说明"):
        for col in df.columns:
            hints[col] = st.text_input(f"{col}", value=hints.get(col, ""), key=f"hint_{col}")
