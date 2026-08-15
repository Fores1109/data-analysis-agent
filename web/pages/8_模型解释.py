"""🔍 模型解释：SHAP 特征重要性 / 单样本 waterfall / 特征依赖图。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.explain import dependence, explain_sample, shap_values
from app.theme import apply_theme, page_header

st.set_page_config(page_title="模型解释 SHAP", page_icon="🔍", layout="wide")
apply_theme()
page_header("🔍", "模型解释（SHAP）",
            "训练树模型并用 SHAP 回答「模型为什么这么预测」：特征贡献排序、单样本 waterfall、特征依赖图")

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df

target = st.selectbox("选择目标列", list(df.columns))
st.caption("说明：内部训练梯度提升树做解释（不是对生产模型解释）；样本多时计算较慢。")

if st.button("🧠 计算 SHAP 解释", key="shap_run"):
    with st.spinner("训练树模型并计算 SHAP（约几十秒）..."):
        try:
            st.session_state["shap_res"] = shap_values(df, target)
            st.session_state["shap_target"] = target
        except Exception as e:
            st.error(f"SHAP 计算失败：{e}")
            st.session_state.pop("shap_res", None)

s = st.session_state.get("shap_res")
if s:
    st.subheader(f"目标列：{target}")

    # 1) 特征重要性
    st.subheader("1️⃣ SHAP 特征重要性（平均 |贡献|）")
    imp = pd.DataFrame(list(s["特征重要性"].items()), columns=["特征", "平均|SHAP|"]).head(20)
    fig = px.bar(imp.iloc[::-1], x="平均|SHAP|", y="特征", orientation="h",
                 title="SHAP 特征重要性 TOP20")
    st.plotly_chart(fig, width='stretch')

    # 2) 单样本 waterfall
    st.subheader("2️⃣ 单样本解释（waterfall）")
    idx = st.number_input("样本序号", min_value=0, value=0)
    w = explain_sample(df, target, int(idx), shap_res=s)
    c1, c2 = st.columns(2)
    c1.metric("模型基准值", w["基准值"])
    c2.metric("该样本预测值", w["预测值"])
    contrib = w["贡献"][:15]
    fig = go.Figure(go.Bar(
        y=[c["特征"] for c in contrib][::-1],
        x=[c["贡献"] for c in contrib][::-1],
        orientation="h",
        marker_color=["#4F6EF7" if c["贡献"] >= 0 else "#F43F5E" for c in contrib][::-1],
    ))
    fig.update_layout(title=f"样本 {idx}：各特征对预测的贡献（蓝=推高预测，红=拉低）",
                      xaxis_title="SHAP 贡献值")
    st.plotly_chart(fig, width='stretch')

    # 3) 依赖图
    st.subheader("3️⃣ 特征依赖图（SHAP 值 vs 特征值）")
    feat = st.selectbox("选择特征", list(s["特征重要性"].keys()))
    d = dependence(df, target, feat, shap_res=s)
    fig = px.scatter(d, x="x", y="shap", trendline="lowess",
                     title=f"特征「{feat}」的 SHAP 依赖图",
                     labels={"x": feat, "shap": "SHAP 贡献"})
    st.plotly_chart(fig, width='stretch')
