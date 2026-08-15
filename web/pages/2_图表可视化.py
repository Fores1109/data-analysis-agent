"""📈 图表可视化：交互式图表 + 悬停解释器。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app import charts

st.set_page_config(page_title="图表可视化", page_icon="📈", layout="wide")
st.title("📈 图表可视化")
st.caption("选择图表类型与字段生成交互图表；开启「悬停解释」后悬浮提示会带上列说明。")

if "df" not in st.session_state:
    st.warning("请先到「首页」加载数据")
    st.stop()
df = st.session_state.df
hints = st.session_state.get("column_hints", {})

cols = list(df.columns)
c1, c2, c3 = st.columns(3)
ctype = c1.selectbox("图表类型", ["柱状图", "折线图", "散点图", "直方图", "箱线图", "相关性热力图", "时间序列"])
use_hints = c2.checkbox("悬停解释", value=True)
x_col = c3.selectbox("X 轴 / 分类字段", cols)

y_col, opt_col, bins = None, None, 30
c4, c5, c6 = st.columns(3)
if ctype in ("柱状图", "折线图", "散点图", "时间序列"):
    y_col = c4.selectbox("Y 轴 / 数值字段", [c for c in cols if c != x_col])
if ctype == "散点图":
    opt_col = c5.selectbox("颜色分组（可选）", ["（无）"] + cols)
if ctype == "直方图":
    bins = c6.slider("分箱数", 5, 100, 30)

try:
    if ctype == "柱状图":
        fig = charts.bar(df, x_col, y_col, title=f"{y_col} 按 {x_col}")
    elif ctype == "折线图":
        fig = charts.line(df, x_col, y_col, title=f"{y_col} 随 {x_col} 变化")
    elif ctype == "散点图":
        fig = charts.scatter(df, x_col, y_col, color=None if opt_col == "（无）" else opt_col,
                             title=f"{y_col} vs {x_col}")
    elif ctype == "直方图":
        fig = charts.histogram(df, x_col, bins=bins)
    elif ctype == "箱线图":
        y2 = st.selectbox("数值字段", cols, key="box_y")
        fig = charts.box(df, y2, x=x_col, title=f"{y2} 按 {x_col}")
    elif ctype == "相关性热力图":
        fig = charts.heatmap_corr(df)
    else:  # 时间序列
        fig = charts.time_series(df, x_col, y_col)

    if use_hints:
        fig = charts.with_hover_hints(fig, hints)
    st.plotly_chart(fig, use_container_width=True)

    if st.button("➕ 把这张图加入报告"):
        st.session_state.setdefault("report_charts", []).append(fig)
        st.success("已加入报告（见「报告生成」页面）")
except Exception as e:
    st.error(f"生成图表失败：{e}")
    st.info("提示：柱状图/折线图需要 X 与 Y 都选择；时间序列的 X 列应为日期格式。")
