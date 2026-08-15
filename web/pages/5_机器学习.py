"""🤖 机器学习：自动推断任务类型、自动选择模型、训练测试、指标对比、特征重要性。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from app.ml_runner import auto_train

st.set_page_config(page_title="机器学习", page_icon="🤖", layout="wide")
st.title("🤖 机器学习：自动选模型与训练")
st.caption("选择目标列后自动判断分类/回归任务，对比多个模型，输出测试集指标与特征重要性")

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df

target = st.selectbox("选择目标列（要预测的指标）", list(df.columns))
test_size = st.slider("测试集比例", 0.1, 0.4, 0.2, 0.05)
st.caption("说明：数值型目标且取值较多 → 回归；否则 → 分类。类别列会自动编码，空值自动填充。")

if st.button("🚀 自动训练", key="ml_run"):
    with st.spinner("训练多个模型并对比（可能需要十几秒）..."):
        try:
            st.session_state["ml_result"] = auto_train(df, target, test_size=test_size)
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

    st.subheader("候选模型对比")
    st.dataframe(pd.DataFrame(res["候选结果"]), width='stretch')

    st.subheader("测试集指标")
    st.write(res["测试集指标"])

    if res["特征重要性"]:
        st.subheader("特征重要性")
        imp = pd.DataFrame(sorted(res["特征重要性"].items(), key=lambda x: -x[1]),
                           columns=["特征", "重要性"])
        st.bar_chart(imp.set_index("特征"))
