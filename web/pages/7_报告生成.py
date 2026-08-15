"""📑 报告生成：汇总问答历史 + 图表 + 数据概览，输出 Markdown / HTML 报告。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app import charts, config, report
from app.theme import apply_theme, page_header

st.set_page_config(page_title="报告生成", page_icon="📑", layout="wide")
apply_theme()
page_header("📑", "自动生成分析报告", "汇总当前会话的数据概览、问答记录与图表，一键导出 Markdown / HTML")

df = st.session_state.get("df")
if df is None:
    st.warning("请先到「首页」加载数据")
    st.stop()

title = st.text_input("报告标题", value="数据分析报告")
data_name = st.session_state.get("data_name", "未记录")

qa = st.session_state.get("qa_history", [])
figs = st.session_state.get("report_charts", [])
c1, c2 = st.columns(2)
c1.metric("问答记录", len(qa))
c2.metric("已加入图表", len(figs))

# 数据概览文本
overview = f"共 {df.shape[0]} 行 × {df.shape[1]} 列。"
num = df.select_dtypes(include="number")
if num.shape[1]:
    overview += "\n\n数值列统计：\n\n" + num.describe().T.to_string()

if st.button("📄 生成报告", key="report_gen"):
    md_text = report.build_md(title, data_name, qa, overview=overview)
    st.session_state["md_text"] = md_text
    st.session_state["md_html"] = report.md_to_html(md_text)
    # 图表嵌入
    charts_html = report.embed_charts_html([charts.figure_to_html(f) for f in figs])
    st.session_state["full_html"] = (
        f"<html><head><meta charset='utf-8'><title>{title}</title></head>"
        f"<body style='font-family:sans-serif;max-width:960px;margin:0 auto;padding:24px'>"
        f"{st.session_state['md_html']}{charts_html}</body></html>"
    )
    st.success("报告已生成，可预览与下载")

md_text = st.session_state.get("md_text")
if md_text:
    st.subheader("预览")
    st.markdown(md_text)
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.download_button("⬇️ 下载 Markdown", md_text, file_name=f"{title}.md", mime="text/markdown")
    col2.download_button("⬇️ 下载 HTML", st.session_state.get("full_html", ""),
                         file_name=f"{title}.html", mime="text/html")
    if col3.button("💾 保存到 data/reports"):
        path = report.save_report(md_text)
        st.success(f"已保存：{path}")
