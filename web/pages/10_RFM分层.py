"""👥 RFM 用户分层：基于 Olist 电商真实订单的客户价值分层与运营画像。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.olist_loader import available, describe, merged
from app.rfm import rfm_table
from app.theme import apply_theme, page_header

st.set_page_config(page_title="RFM 用户分层", page_icon="👥", layout="wide")
apply_theme()
page_header("👥", "RFM 用户分层",
            "基于最近购买时间(R)/购买频次(F)/消费金额(M)对客户打分分层，输出价值画像与运营建议（Olist 真实数据）")

if not available():
    st.error("Olist 数据集未找到（data/olist/），请先下载数据集。")
    st.stop()


@st.cache_data(show_spinner=False)
def load_merged():
    return merged()


m = load_merged()
st.info(f"数据集：{describe()}")

if st.button("🧮 计算 RFM 分层", key="rfm_run"):
    with st.spinner("计算约 10 万订单的 RFM 打分与分层（约 10-30 秒）..."):
        try:
            g, summary = rfm_table(m, customer_id="customer_id",
                                   date_col="order_purchase_timestamp", amount_col="price")
            st.session_state["rfm"] = {"g": g, "summary": summary}
        except Exception as e:
            st.error(f"计算失败：{e}")
            st.session_state.pop("rfm", None)

r = st.session_state.get("rfm")
if r:
    g, summary = r["g"], r["summary"]

    st.subheader("分层汇总（按金额占比排序）")
    st.dataframe(summary, width='stretch')

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(summary, x="客户分层", y="金额占比", color="客户分层",
                     title="各层客户金额占比 (%)")
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.pie(summary, names="客户分层", values="客户数", title="各层客户数量占比")
        st.plotly_chart(fig, width='stretch')

    st.subheader("运营建议（可直接抄进简历/报告）")
    for _, row in summary.head(5).iterrows():
        st.markdown(f"- **{row['客户分层']}**（{row['客户数']:,} 人，金额占比 {row['金额占比']}%）：{row['画像']}")

    with st.expander("查看客户明细（前 500 行）"):
        st.dataframe(g.head(500), width='stretch')
