"""🗄️ SQL 助手：表结构可视化、语句补全、自然语言生成 SQL、执行计划、优化建议。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app import config
from app.llm import create_llm
from app.sql_assistant import (autocomplete, explain_sql, generate_sql,
                               get_schema, optimize_sql)
from app.theme import apply_theme, page_header

st.set_page_config(page_title="SQL 助手", page_icon="🗄️", layout="wide")
apply_theme()
page_header("🗄️", "SQL 助手（Copilot 式辅助）", "连接数据库 → 可视化表结构 → 自动补全 → 自然语言生成 SQL → 执行计划 → 优化建议")

url = st.text_input("数据库连接串", value=config.DB_URL)

if st.button("📐 读取表结构", key="schema_load"):
    try:
        st.session_state["schema"] = get_schema(url)
        st.session_state["schema_url"] = url
        st.success("表结构读取成功")
    except Exception as e:
        st.error(f"读取失败：{e}")

schema = st.session_state.get("schema")
if not schema:
    st.info("点击上方「读取表结构」开始")
    st.stop()

st.subheader("📐 表结构可视化")
for t, c in schema.items():
    with st.expander(f"表 {t}（{len(c)} 列）"):
        st.write("、".join(c))

st.divider()

# ---- 语句补全 ----
st.subheader("⌨️ 语句补全")
prefix = st.text_input("输入表名/列名前缀（本地即时匹配，不消耗 token）", placeholder="例如输入 sa 或 sales")
if prefix.strip():
    sugg = autocomplete(prefix, schema)
    st.write("补全建议：", "、".join(sugg) if sugg else "（无匹配）")

st.divider()

# ---- 自然语言生成 SQL ----
st.subheader("✨ 自然语言 → SQL")
question = st.text_area("描述你想查什么", placeholder="例如：查询 2025 年 1 月各城市的总销售额，按降序排列")
if st.button("生成 SQL"):
    try:
        with st.spinner("LLM 生成中..."):
            st.session_state["sql_editor"] = generate_sql(question, schema, create_llm())
    except Exception as e:
        st.error(f"生成失败：{e}")

sql = st.text_area("SQL（可编辑后查看执行计划 / 优化建议）",
                   value=st.session_state.get("sql_editor", ""), height=140, key="sql_editor")
col1, col2 = st.columns(2)
if col1.button("🔍 查看执行计划 (EXPLAIN)"):
    if sql.strip():
        try:
            st.code(explain_sql(sql, url), language="text")
        except Exception as e:
            st.error(f"执行计划失败（请确认 SQL 可执行）：{e}")
if col2.button("💡 优化建议（LLM）"):
    if sql.strip():
        try:
            with st.spinner("LLM 分析中..."):
                st.write(optimize_sql(sql, schema, create_llm()))
        except Exception as e:
            st.error(f"分析失败：{e}")
