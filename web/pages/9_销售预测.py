"""📈 销售预测：SARIMA/ETS 未来预测 + STL 季节分解 + 异常检测（Olist 真实数据）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.forecast import daily_series, decompose, detect_anomalies, forecast
from app.olist_loader import available, describe, merged
from app.theme import apply_theme, page_header

st.set_page_config(page_title="销售预测", page_icon="📈", layout="wide")
apply_theme()
page_header("📈", "销售预测与异常检测",
            "基于 Olist 电商真实数据（10 万订单）：SARIMA/ETS 未来销售预测、STL 季节分解、IsolationForest 异常检测")

if not available():
    st.error("Olist 数据集未找到（data/olist/），请先下载数据集。")
    st.stop()


@st.cache_data(show_spinner=False)
def load_merged():
    return merged()


m = load_merged()
st.info(f"数据集：{describe()}")

value_col = st.radio("预测指标", ["销售额（price+运费）", "订单量"], horizontal=True)
if value_col == "销售额（price+运费）":
    m["_value"] = m["price"] + m["freight_value"]
    agg = "sum"
else:
    m["_value"] = m["order_id"]
    agg = "count"

c1, c2 = st.columns(2)
periods = c1.slider("预测未来天数", 7, 90, 30, 7)
anom_method = c2.radio("异常检测方法", ["IsolationForest（机器学习）", "IQR（统计）"], horizontal=True)

if st.button("📊 开始分析", key="fc_run"):
    with st.spinner("建模预测 + STL 分解 + 异常检测中（约 10-30 秒）..."):
        try:
            s = daily_series(m, "order_purchase_timestamp", "_value", agg=agg)
            st.session_state["fc"] = {
                "s": s,
                "fc": forecast(s, int(periods)),
                "decomp": decompose(s),
                "anom": detect_anomalies(s, method="isolation" if "Isolation" in anom_method else "iqr"),
            }
        except Exception as e:
            st.error(f"分析失败：{e}")
            st.session_state.pop("fc", None)

r = st.session_state.get("fc")
if r:
    s, fc, decomp, anom = r["s"], r["fc"], r["decomp"], r["anom"]

    # 1) 预测
    st.subheader(f"1️⃣ 未来 {periods} 天预测 —— 模型：{fc['模型']}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s.index, y=s.values, name="历史实际",
                             line=dict(color="#4F6EF7", width=2)))
    fig.add_trace(go.Scatter(x=fc["预测"].index, y=fc["预测"].values, name="预测",
                             line=dict(color="#F59E0B", width=2, dash="dash")))
    if fc["下限"] is not None:
        xs = list(fc["预测"].index) + list(fc["预测"].index)[::-1]
        ys = list(fc["上限"].values) + list(fc["下限"].values)[::-1]
        fig.add_trace(go.Scatter(x=xs, y=ys, fill="toself",
                                 fillcolor="rgba(245,158,11,.15)", line=dict(width=0),
                                 name="90% 置信区间"))
    fig.update_layout(hovermode="x unified", title=f"销售预测（{fc['模型']}）")
    st.plotly_chart(fig, width='stretch')

    # 2) STL 分解
    st.subheader("2️⃣ STL 季节分解（周周期）")
    dc = decomp
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        subplot_titles=["观测", "趋势", "季节", "残差"])
    for i, name in enumerate(["观测", "趋势", "季节", "残差"], 1):
        fig.add_trace(go.Scatter(x=dc[name].index, y=dc[name].values, name=name,
                                 line=dict(width=1.5)), row=i, col=1)
    fig.update_layout(height=720, showlegend=False, hovermode="x unified")
    st.plotly_chart(fig, width='stretch')

    # 3) 异常检测
    st.subheader(f"3️⃣ 异常检测 —— {anom['方法']}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=anom["全部"].index, y=anom["全部"].values, name="时序",
                             line=dict(color="#94A3B8", width=1.5)))
    if len(anom["异常点"]):
        fig.add_trace(go.Scatter(x=anom["异常点"].index, y=anom["异常点"].values,
                                 mode="markers", name=f"异常点（{len(anom['异常点'])} 个）",
                                 marker=dict(color="#F43F5E", size=9)))
    fig.update_layout(hovermode="x unified", title="异常点标注")
    st.plotly_chart(fig, width='stretch')
    st.write(f"共检出 **{len(anom['异常点'])}** 个异常点。")
