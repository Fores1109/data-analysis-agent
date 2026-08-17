"""🎮 游戏深度分析：关卡漏斗 / 付费转化（首充）/ Cohort LTV / 流失预警（机器学习）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.data_source import load_file
from app.game_churn import churn_prediction
from app.game_deep import (cohort_ltv, first_pay_funnel, level_funnel,
                           simulate_game_data_full)
from app.theme import apply_theme, page_header

st.set_page_config(page_title="游戏深度分析", page_icon="🎯", layout="wide")
apply_theme()
page_header("🎯", "游戏深度分析",
            "关卡通过漏斗 · 付费转化（首充）· Cohort LTV · 流失预警（机器学习预测未来活跃）")

st.session_state.setdefault("game_full", None)

with st.sidebar:
    st.header("🎯 数据来源")
    src = st.radio("选择", ["内置完整模拟数据", "上传文件"], key="gd_src")
    if src == "内置完整模拟数据":
        c1, c2 = st.columns(2)
        n_users = c1.number_input("用户数", 500, 10000, 3000, 500)
        days = c2.number_input("天数", 60, 365, 120, 10)
        if st.button("🎲 生成完整模拟数据", key="gd_gen"):
            with st.spinner("生成登录/付费/用户/关卡进度..."):
                st.session_state["game_full"] = simulate_game_data_full(int(n_users), int(days))
            st.success("已生成")
    else:
        f_login = st.file_uploader("登录日志（必填）", type=["csv"], key="gd_login")
        f_pay = st.file_uploader("付费日志（可选）", type=["csv"], key="gd_pay")
        f_users = st.file_uploader("用户表（可选）", type=["csv"], key="gd_users")
        f_levels = st.file_uploader("关卡进度（可选：user_id,date,level）", type=["csv"], key="gd_levels")
        if f_login is not None:
            try:
                st.session_state["game_full"] = {
                    "login": load_file(f_login),
                    "pay": load_file(f_pay) if f_pay is not None else None,
                    "users": load_file(f_users) if f_users is not None else None,
                    "levels": load_file(f_levels) if f_levels is not None else None,
                }
                st.success("已加载")
            except Exception as e:
                st.error(f"加载失败：{e}")

gd = st.session_state.get("game_full")
if gd is None:
    st.info("👈 请在左侧生成或上传数据（建议先用「内置完整模拟数据」体验）")
    st.stop()

login_df, pay_df, users_df, level_df = gd["login"], gd["pay"], gd["users"], gd["levels"]
if users_df is None:
    users_df = login_df.groupby("user_id")["date"].min().rename("reg_date").reset_index()
    users_df["channel"] = "未知"

tab1, tab2, tab3, tab4 = st.tabs(["🎯 关卡漏斗", "💳 付费转化", "📈 Cohort LTV", "🚨 流失预警"])

# ---------- 关卡漏斗 ----------
with tab1:
    if level_df is not None and len(level_df):
        if st.button("🎯 计算关卡漏斗", key="lv_run"):
            with st.spinner("统计关卡通过率..."):
                st.session_state["lv"] = level_funnel(level_df)
        lv = st.session_state.get("lv")
        if lv is not None:
            fig = go.Figure(go.Funnel(
                y=lv["关卡"], x=lv["到达人数"], textinfo="value+percent initial",
                marker=dict(color="rgba(79,110,247,.8)"),
            ))
            fig.update_layout(title="关卡通过漏斗（到达各关的用户数）")
            st.plotly_chart(fig, width='stretch')
            st.dataframe(lv, width='stretch')
            worst = lv.loc[lv["相对通过率%"].idxmin()]
            st.info(f"💡 **流失最严重的关卡：{worst['关卡']}**（相对通过率仅 {worst['相对通过率%']}%），"
                    f"建议排查该关难度/卡点——这是运营调优的直接依据。")
    else:
        st.info("未提供关卡进度数据（上传含 user_id,date,level 的 CSV 即可）。")

# ---------- 付费转化 ----------
with tab2:
    if st.button("💳 计算付费转化漏斗", key="fp_run"):
        with st.spinner("统计首充转化..."):
            try:
                st.session_state["fp"] = first_pay_funnel(login_df, pay_df, users_df)
            except Exception as e:
                st.error(f"计算失败：{e}")
    fp = st.session_state.get("fp")
    if fp is not None:
        stages, dist = fp
        fig = go.Figure(go.Funnel(
            y=stages["阶段"], x=stages["人数"], textinfo="value+percent initial",
            marker=dict(color="rgba(139,92,246,.85)"),
        ))
        fig.update_layout(title="付费转化漏斗：注册 → 活跃 → 首充 → 复购")
        st.plotly_chart(fig, width='stretch')
        st.dataframe(stages, width='stretch')
        if dist is not None and len(dist):
            st.subheader("首充时间分布（注册后第几天完成首充）")
            fig = px.histogram(dist, x="首充天数", nbins=30,
                               title=f"首充天数分布（中位数 {int(dist['首充天数'].median())} 天）")
            st.plotly_chart(fig, width='stretch')
        st.info("💡 首充转化率与首充时间直接影响付费设计：转化低 → 检查付费引导时机；"
                "首充过晚 → 考虑新手礼包/首充双倍等激励。")

# ---------- Cohort LTV ----------
with tab3:
    if pay_df is not None and len(pay_df):
        if st.button("📈 计算 Cohort LTV", key="ltv_run"):
            with st.spinner("计算各注册周累计 LTV..."):
                st.session_state["ltv"] = cohort_ltv(pay_df, users_df)
        ltv = st.session_state.get("ltv")
        if ltv is not None:
            fig = px.imshow(ltv, text_auto=".1f", color_continuous_scale="Mint",
                            labels=dict(x="注册后周数", y="注册周", color="累计LTV(元)"))
            fig.update_layout(height=520, title="Cohort LTV：累计收入 ÷ 该周注册用户（含未付费）")
            st.plotly_chart(fig, width='stretch')
            st.caption("LTV 口径 = 累计收入 / 注册用户数。对比不同注册周的 LTV 曲线可评估拉新渠道质量与版本迭代效果。")
    else:
        st.info("未提供付费日志（上传含 user_id,date,amount 的 CSV 即可）。")

# ---------- 流失预警 ----------
with tab4:
    st.caption("v2：窗口特征（近 7/14 天活跃、活跃趋势、距上次付费天数）+ 3 个模型（LR/RF/HistGB）+ 时间切分 + 最佳阈值")
    horizon = st.slider("预测未来 N 天是否活跃（N 天内不活跃视为流失）", 3, 30, 7, 1)
    if st.button("🚨 训练流失预警模型", key="churn_run"):
        with st.spinner("特征工程 + 训练逻辑回归/随机森林/梯度提升..."):
            try:
                st.session_state["churn"] = churn_prediction(
                    login_df, users_df, pay_df, level_df, horizon=int(horizon))
            except Exception as e:
                st.error(f"训练失败：{e}")
    churn = st.session_state.get("churn")
    if churn:
        st.subheader(f"口径：{churn['口径']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("样本数", churn["样本数"])
        c2.metric("流失率", f"{churn['流失率%']}%")
        c3.metric("最优模型", churn["最优模型"])
        c4.metric("最佳阈值", churn.get("最佳阈值", "-"))
        st.caption(churn.get("切分方式", ""))
        st.subheader("模型对比")
        st.dataframe(pd.DataFrame(churn["模型对比"]), width='stretch')
        st.subheader("特征重要性（什么特征预示流失）")
        imp = pd.DataFrame(sorted(churn["特征重要性"].items(), key=lambda x: -x[1]),
                           columns=["特征", "重要性"])
        fig = px.bar(imp, x="重要性", y="特征", orientation="h", title="流失预测特征重要性")
        st.plotly_chart(fig, width='stretch')
        st.subheader(f"🚨 高危用户 TOP{len(churn['高危用户'])}（建议运营优先触达）")
        st.dataframe(churn["高危用户"], width='stretch')
        st.info("💡 预警闭环：高危名单 → 推送召回（礼包/活动）→ 下一周期评估召回后留存提升。"
                "特征重要性可指导产品优化（如「最近活跃距今」权重最高 → 做沉默唤醒）。")
