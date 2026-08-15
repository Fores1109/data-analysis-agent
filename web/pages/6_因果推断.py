"""🔗 因果推断：多元回归（控制混杂）与双重差分 DID，附逐变量解释。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from app.experiments import did, ols
from app.theme import apply_theme, page_header

st.set_page_config(page_title="因果推断", page_icon="🔗", layout="wide")
apply_theme()
page_header("🔗", "因果推断", "教学级实现：多元回归控制已观测混杂 / 双重差分 DID；回归只能控制已观测变量，不能证明因果。解释变量建议选数值列（类别列请先在数据源中编码为数字）")

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df
hints = st.session_state.get("column_hints", {})
cols = list(df.columns)

method = st.radio("分析方法", ["多元回归（控制混杂）", "双重差分 DID"])

result = None
if method == "多元回归（控制混杂）":
    outcome = st.selectbox("结果变量 Y（被解释）", cols)
    predictors = st.multiselect("解释变量（建议包含你的处理变量/关注因素）", [c for c in cols if c != outcome])
    if st.button("运行回归", key="causal_ols"):
        if not predictors:
            st.error("至少选择一个解释变量")
        else:
            try:
                result = ols(df, outcome, predictors)
            except Exception as e:
                st.error(f"回归失败：{e}")

    if result:
        st.subheader("回归结果")
        coef_df = pd.DataFrame(result["系数表"]).T.reset_index().rename(columns={"index": "变量"})
        st.dataframe(coef_df, width='stretch')
        c1, c2 = st.columns(2)
        c1.metric("R²", result["R²"])
        c2.metric("样本量", result["样本量"])

        st.subheader("📖 逐变量解释（悬停解释器）")
        for var, row in result["系数表"].items():
            if var == "const":
                continue
            p = row["p"]
            sig = "显著" if p < 0.05 else "不显著"
            desc = hints.get(var, "")
            st.markdown(
                f"- **{var}**：系数 {row['系数']:+.4f}（p={p:.4f}，{sig}）。"
                f"解释：在控制其他变量后，{var} 每增加 1 个单位，{outcome} 平均{'增加' if row['系数'] >= 0 else '减少'} {abs(row['系数']):.4f}。"
                + (f" 列说明：{desc}" if desc else "")
            )
        st.info("⚠️ 相关不等于因果：仅当处理变量外生（随机分配/自然实验）时才可做因果解读。")

else:  # DID
    st.caption("DID 需要面板数据：每个单元同时有「实验组/对照组」标识与「前/后」两个时点。")
    c1, c2, c3 = st.columns(3)
    outcome = c1.selectbox("结果变量 Y", cols)
    group_col = c2.selectbox("分组列（组别标识）", cols)
    time_col = c3.selectbox("时点列（前/后标识）", cols)
    gv = st.text_input("实验组标识值（分组列中代表实验组的取值）", value="1")
    pv = st.text_input("后时点标识值（时点列中代表「后」的取值）", value="1")
    confounders = st.multiselect("控制变量（可选）", [c for c in cols if c not in (outcome, group_col, time_col)])
    if st.button("运行 DID", key="causal_did"):
        try:
            result = did(df, outcome, group_col, gv, time_col, pv, confounders or None)
        except Exception as e:
            st.error(f"DID 失败：{e}")

    if result:
        st.subheader("DID 结果")
        c1, c2 = st.columns(2)
        c1.metric("DID 估计值（处理效应）", result["DID 估计值"])
        c2.metric("p 值", result["p 值"])
        st.write(result["显著性"])
        st.markdown(f"**解释：** 实验组相对对照组在「前后」之间的变化差异为 {result['DID 估计值']} {result['显著性']}，"
                    f"可理解为干预带来的净效应估计。")
        st.info(result["提示"])
        with st.expander("查看完整回归表"):
            coef_df = pd.DataFrame(result["完整回归"]["系数表"]).T.reset_index().rename(columns={"index": "变量"})
            st.dataframe(coef_df, width='stretch')
