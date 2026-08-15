"""🧪 A/B 实验：两组均值 t 检验、转化率 z 检验、模拟实验运行。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from app.experiments import ab_proportion, ab_ttest, simulate_ab
from app.theme import apply_theme, page_header

st.set_page_config(page_title="A/B 实验", page_icon="🧪", layout="wide")
apply_theme()
page_header("🧪", "A/B 实验", "对两组数据进行统计检验：Welch t 检验（连续指标）/ 双比例 z 检验（转化率），含效应量与结论解读")


def show_result(res: dict):
    """渲染检验结果：指标行 + 结论高亮。"""
    df = pd.DataFrame([{k: v for k, v in res.items() if k != "结论"}])
    st.dataframe(df, width='stretch')
    st.markdown(f"**📌 结论：** {res['结论']}")


tab1, tab2, tab3 = st.tabs(["连续指标检验", "转化率检验", "模拟实验运行"])

# ---------------- 连续指标 ----------------
with tab1:
    mode = st.radio("数据输入方式", ["从当前数据选两列", "手动粘贴两组数值"], key="ab_mode")
    if mode == "从当前数据选两列":
        if "df" not in st.session_state:
            st.warning("请先到「首页」加载数据")
        else:
            cols = list(st.session_state.df.columns)
            a = st.selectbox("对照组列", cols, key="ab_col_a")
            b = st.selectbox("实验组列", cols, key="ab_col_b", index=min(1, len(cols) - 1))
            if st.button("运行 t 检验", key="ab_run_cols"):
                try:
                    show_result(ab_ttest(st.session_state.df[a], st.session_state.df[b]))
                except Exception as e:
                    st.error(f"检验失败：{e}")
    else:
        a = st.text_area("对照组数值（逗号分隔）", "100,102,99,105,101,98")
        b = st.text_area("实验组数值（逗号分隔）", "108,110,105,112,107,109")
        if st.button("运行 t 检验", key="ab_run_paste"):
            try:
                pa = [float(x) for x in a.replace("，", ",").split(",") if x.strip()]
                pb = [float(x) for x in b.replace("，", ",").split(",") if x.strip()]
                show_result(ab_ttest(pa, pb))
            except Exception as e:
                st.error(f"检验失败：{e}")

# ---------------- 转化率 ----------------
with tab2:
    c1, c2, c3, c4 = st.columns(4)
    cs = c1.number_input("对照组成功数", min_value=0, value=80)
    cn = c2.number_input("对照组总人数", min_value=1, value=1000)
    ts = c3.number_input("实验组成功数", min_value=0, value=95)
    tn = c4.number_input("实验组总人数", min_value=1, value=1000)
    if st.button("运行转化率检验", key="ab_run_prop"):
        if cs > cn or ts > tn:
            st.error("成功数不能大于总人数")
        else:
            try:
                show_result(ab_proportion(int(cs), int(cn), int(ts), int(tn)))
            except Exception as e:
                st.error(f"检验失败：{e}")

# ---------------- 模拟实验 ----------------
with tab3:
    st.caption("生成两组模拟数据并检验：把样本量调大、效应量调大，观察 p 值如何变化（模拟运行实验）")
    c1, c2, c3 = st.columns(3)
    n = c1.slider("每组样本量", 50, 5000, 500, step=50)
    eff = c2.slider("效应量 (Cohen's d)", 0.0, 1.0, 0.2, 0.05)
    seed = c3.number_input("随机种子", min_value=0, max_value=99999, value=42)
    if st.button("模拟并检验", key="ab_run_sim"):
        ctrl, trt = simulate_ab(n_per_group=int(n), effect=float(eff), seed=int(seed))
        show_result(ab_ttest(ctrl, trt))
