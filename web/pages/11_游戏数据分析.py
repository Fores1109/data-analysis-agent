"""🎮 游戏数据分析：留存矩阵 / 留存曲线 / DAU-WAU-MAU / 付费指标（游戏厂商视角）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.data_source import load_file
from app.game_analytics import (INDUSTRY_BENCHMARKS, activity_metrics,
                                payment_metrics, retention_by_channel,
                                retention_curve, retention_matrix,
                                simulate_game_data)
from app.theme import apply_theme, page_header

st.set_page_config(page_title="游戏数据分析", page_icon="🎮", layout="wide")
apply_theme()
page_header("🎮", "游戏数据分析",
            "游戏厂商核心指标：同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU；内置模拟数据，也支持上传真实日志")

st.session_state.setdefault("game_data", None)

with st.sidebar:
    st.header("🎮 数据来源")
    src = st.radio("选择", ["内置模拟数据（演示）", "上传文件"], key="game_src")
    if src == "内置模拟数据（演示）":
        c1, c2 = st.columns(2)
        n_users = c1.number_input("用户数", 500, 10000, 3000, 500)
        days = c2.number_input("天数", 30, 365, 120, 10)
        if st.button("🎲 生成模拟数据", key="game_gen"):
            with st.spinner("生成玩家活跃/付费日志..."):
                st.session_state["game_data"] = simulate_game_data(int(n_users), int(days))
            st.success("已生成")
    else:
        f_login = st.file_uploader("登录日志（user_id, date）", type=["csv"], key="game_login")
        f_pay = st.file_uploader("付费日志（可选：user_id, date, amount）", type=["csv"], key="game_pay")
        f_users = st.file_uploader("用户表（可选：user_id, reg_date, channel）", type=["csv"], key="game_users")
        if f_login is not None:
            try:
                login = load_file(f_login)
                pay = load_file(f_pay) if f_pay is not None else None
                users = load_file(f_users) if f_users is not None else None
                st.session_state["game_data"] = (login, pay, users)
                st.success("已加载")
            except Exception as e:
                st.error(f"加载失败：{e}")

gd = st.session_state.get("game_data")
if gd is None:
    st.info("👈 请在左侧选择数据来源（建议先用「内置模拟数据」体验）")
    st.stop()

login_df, pay_df, users_df = gd
n_users = len(users_df) if users_df is not None else login_df["user_id"].nunique()
n_days = (pd.to_datetime(login_df["date"]).max() - pd.to_datetime(login_df["date"]).min()).days + 1
c1, c2, c3, c4 = st.columns(4)
c1.metric("用户数", f"{n_users:,}")
c2.metric("观测天数", n_days)
c3.metric("活跃记录", f"{len(login_df):,}")
c4.metric("付费记录", f"{0 if pay_df is None else len(pay_df):,}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 留存分析", "📈 活跃分析", "💰 付费分析", "📖 行业基准"])

# ---------- 留存 ----------
with tab1:
    if st.button("🧮 计算留存", key="ret_run"):
        with st.spinner("计算同期群留存..."):
            try:
                st.session_state["ret"] = {
                    "matrix": retention_matrix(login_df, users_df),
                    "curve": retention_curve(login_df, users_df, max_day=30),
                    "by_ch": retention_by_channel(login_df, users_df) if users_df is not None else None,
                }
            except Exception as e:
                st.error(f"留存计算失败：{e}")

    ret = st.session_state.get("ret")
    if ret:
        st.subheader("同期群留存矩阵（行=注册周，格=该周用户第 N 日留存率 %）")
        mat = ret["matrix"]
        fig = px.imshow(mat.T, text_auto=".1f", color_continuous_scale="Blues",
                        labels=dict(x="注册周", y="", color="留存率%"))
        fig.update_layout(height=420)
        st.plotly_chart(fig, width='stretch')

        st.subheader("整体留存曲线（第 0 天 = 注册当天）")
        fig = px.line(ret["curve"], x="第N天", y="留存率%", markers=True,
                      title="留存衰减曲线")
        st.plotly_chart(fig, width='stretch')

        if ret["by_ch"] is not None and len(ret["by_ch"]):
            st.subheader("各渠道留存对比")
            fig = px.bar(ret["by_ch"], x="渠道", y="留存率%", color="指标", barmode="group")
            st.plotly_chart(fig, width='stretch')

# ---------- 活跃 ----------
with tab2:
    if st.button("📈 计算活跃指标", key="act_run"):
        with st.spinner("计算 DAU/WAU/MAU..."):
            try:
                st.session_state["act"] = activity_metrics(login_df)
            except Exception as e:
                st.error(f"活跃计算失败：{e}")
    act = st.session_state.get("act")
    if act:
        c1, c2, c3 = st.columns(3)
        c1.metric("DAU 均值", act["DAU均值"])
        c2.metric("峰值 DAU", act["峰值DAU"])
        c3.metric("DAU/MAU 粘性", f"{act['DAU/MAU粘性%']}%")
        fig = px.line(act["DAU"], title="DAU 日活趋势")
        st.plotly_chart(fig, width='stretch')
        fig = px.line(pd.DataFrame({"WAU": act["WAU"], "MAU": act["MAU"]}),
                      title="WAU / MAU 趋势")
        st.plotly_chart(fig, width='stretch')

# ---------- 付费 ----------
with tab3:
    if pay_df is not None and st.button("💰 计算付费指标", key="pay_run"):
        with st.spinner("计算付费指标..."):
            try:
                st.session_state["pay"] = payment_metrics(pay_df, users_df)
            except Exception as e:
                st.error(f"付费计算失败：{e}")
    if pay_df is None:
        st.info("当前数据没有付费日志（上传时提供 user_id, date, amount 即可）。")
    pay = st.session_state.get("pay")
    if pay:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("总收入", f"¥{pay['总收入']:,.0f}")
        c2.metric("付费率", f"{pay['付费率%']}%")
        c3.metric("ARPU", f"¥{pay['ARPU']}")
        c4.metric("ARPPU", f"¥{pay['ARPPU']}")
        fig = px.line(pd.Series(pay["每日收入"]), title="每日收入")
        st.plotly_chart(fig, width='stretch')

# ---------- 基准 ----------
with tab4:
    st.subheader("游戏行业参考基准（解读用）")
    st.table(pd.DataFrame(
        [{"指标": k, "行业参考": v} for k, v in INDUSTRY_BENCHMARKS.items()]
    ))
    st.caption("来源：行业经验值，品类差异大，仅作解读参考。")
