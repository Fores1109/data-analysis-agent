"""🤖 机器学习：Optuna 自动调参 + 多模型对比 + 调参过程 + 特征重要性。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.automl import automl_train
from app.theme import apply_theme, page_header

st.set_page_config(page_title="机器学习", page_icon="🤖", layout="wide")
apply_theme()
page_header("🤖", "机器学习：Optuna 自动调参",
            "选择目标列 → 对随机森林 / 梯度提升 / 线性模型做超参搜索（TPE）→ 对比测试集指标与调参过程曲线")

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df

target = st.selectbox("选择目标列（要预测的指标）", list(df.columns))
c1, c2 = st.columns(2)
n_trials = c1.slider("每个模型的调参试验次数", 10, 60, 30, 5)
test_size = c2.slider("测试集比例", 0.1, 0.4, 0.2, 0.05)
st.caption("说明：数值目标且取值较多 → 回归，否则 → 分类。类别列自动编码、空值自动填充。"
           "30 次试验 × 3 个模型约 1-2 分钟，样本量大时更久。")

if st.button("🚀 开始自动调参", key="ml_run"):
    with st.spinner(f"Optuna 正在搜索超参数（{n_trials} 次试验 × 3 个模型，TPE 采样）..."):
        try:
            st.session_state["ml_result"] = automl_train(df, target, n_trials=int(n_trials),
                                                         test_size=test_size)
        except Exception as e:
            st.error(f"训练失败：{e}")
            st.session_state.pop("ml_result", None)

res = st.session_state.get("ml_result")
if res:
    st.subheader(f"任务类型：{res['task']} ｜ 最优模型：{res['最优模型']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("样本数", res["样本数"])
    c2.metric("特征数", res["特征数"])
    c3.metric("最优模型", res["最优模型"])

    # 模型对比表（参数 dict 转字符串便于展示）
    rows = []
    for r in res["模型对比"]:
        rows.append({k: (str(v) if isinstance(v, dict) else v) for k, v in r.items()
                     if k != "调参曲线"})
    st.subheader("模型对比（Optuna 调参后）")
    st.dataframe(pd.DataFrame(rows), width='stretch')

    # 调参过程曲线
    st.subheader("调参过程（每次试验的交叉验证得分）")
    for r in res["模型对比"]:
        if r["调参曲线"]:
            fig = px.line(pd.DataFrame(r["调参曲线"]), x="trial", y="得分", markers=True,
                          title=f"{r['模型']} — 最优 CV 得分 {r['最优CV得分']}")
            st.plotly_chart(fig, width='stretch')

    # 特征重要性
    if res["特征重要性"]:
        st.subheader("特征重要性（最优模型）")
        imp = pd.DataFrame(sorted(res["特征重要性"].items(), key=lambda x: -x[1]),
                           columns=["特征", "重要性"])
        fig = px.bar(imp, x="重要性", y="特征", orientation="h", title="特征重要性")
        st.plotly_chart(fig, width='stretch')

    with st.expander("📖 方法论说明（面试讲稿）"):
        st.markdown(res["说明"])
