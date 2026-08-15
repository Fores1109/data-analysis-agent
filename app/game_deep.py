"""游戏深度分析：关卡漏斗 / 付费转化（首充） / Cohort LTV。

配合 game_analytics 的留存/活跃/付费指标，构成完整的游戏厂商分析链路。
"""
import numpy as np
import pandas as pd

from .game_analytics import simulate_game_data


def simulate_levels(users_df, login_df, seed=42, max_level=60):
    """生成关卡进度事件（user_id, date, level）：活跃日按用户技能推进关卡。

    技能服从 Beta(2,3) 分布（大多数玩家水平中等），每天推进量 ~ Poisson。
    """
    rng = np.random.default_rng(seed)
    skill = rng.beta(2, 3, len(users_df))
    login = login_df.copy().sort_values(["user_id", "date"])
    rows = []
    for uid, g in login.groupby("user_id"):
        lvl = 0
        s = skill[int(uid) - 1]
        for _, row in g.iterrows():
            lvl += int(max(rng.poisson(1 + s * 3), 1))   # 活跃日至少推进 1 关
            rows.append((int(uid), row["date"], min(lvl, max_level)))
    return pd.DataFrame(rows, columns=["user_id", "date", "level"])


def simulate_game_data_full(n_users=3000, days=120, seed=42):
    """完整模拟数据：登录 / 付费 / 用户 / 关卡进度。返回 dict。"""
    login, pay, users = simulate_game_data(n_users, days, seed)
    levels = simulate_levels(users, login, seed=seed + 1)
    return {"login": login, "pay": pay, "users": users, "levels": levels}


def level_funnel(level_df, max_level=30, user_col="user_id", level_col="level"):
    """关卡通过漏斗：达到各关卡的用户数、相对通过率、累计通过率。"""
    d = level_df.copy()
    d[level_col] = pd.to_numeric(d[level_col], errors="coerce")
    total = int(d[user_col].nunique())
    rows, prev = [], total
    for lv in range(1, max_level + 1):
        n = int(d[d[level_col] >= lv][user_col].nunique())
        rows.append({
            "关卡": f"第{lv}关",
            "到达人数": n,
            "相对通过率%": round(n / prev * 100, 2) if prev else 0.0,
            "累计通过率%": round(n / total * 100, 2) if total else 0.0,
        })
        prev = n
    return pd.DataFrame(rows)


def first_pay_funnel(login_df, pay_df, users_df, active_days=2):
    """付费转化漏斗：注册 → 活跃≥N天 → 首充 → 复购。

    返回 (阶段表, 首充时间分布 DataFrame)。
    """
    u = users_df.copy()
    u["reg_date"] = pd.to_datetime(u["reg_date"])
    n_reg = int(len(u))
    act_counts = login_df.groupby("user_id")["date"].nunique()
    n_act = int((act_counts >= active_days).sum())

    if pay_df is None or len(pay_df) == 0:
        n_first, n_repeat, dist = 0, 0, None
    else:
        pay = pay_df.copy()
        pay["date"] = pd.to_datetime(pay["date"])
        pay_counts = pay.groupby("user_id")["date"].nunique()
        n_first = int((pay_counts >= 1).sum())
        n_repeat = int((pay_counts >= 2).sum())
        fp = pay.sort_values("date").groupby("user_id").first().reset_index()
        fp = fp.merge(u[["user_id", "reg_date"]], on="user_id")
        fp["首充天数"] = (fp["date"] - fp["reg_date"]).dt.days
        dist = fp[fp["首充天数"] >= 0][["首充天数"]]

    stages = pd.DataFrame({
        "阶段": ["注册用户", f"活跃≥{active_days}天", "首充用户", "复购用户"],
        "人数": [n_reg, n_act, n_first, n_repeat],
    })
    stages["转化率%"] = (stages["人数"] / stages["人数"].shift(1) * 100).round(2)
    stages.loc[0, "转化率%"] = 100.0
    return stages, dist


def cohort_ltv(pay_df, users_df, week_periods=12):
    """Cohort LTV 矩阵：行=注册周，列=注册后第 N 周，值=累计收入/该 cohort 注册用户数（元）。

    口径：LTV = 累计收入 ÷ 注册用户（含未付费用户），是评估拉新 ROI 的核心指标。
    """
    u = users_df.copy()
    u["reg_date"] = pd.to_datetime(u["reg_date"])
    u["cohort"] = u["reg_date"].dt.to_period("W").astype(str)
    n_users = u.groupby("cohort")["user_id"].count()

    pay = pay_df.copy()
    pay["date"] = pd.to_datetime(pay["date"])
    m = pay.merge(u[["user_id", "reg_date", "cohort"]], on="user_id")
    m["week"] = ((m["date"] - m["reg_date"]).dt.days // 7).astype(int)
    m = m[m["week"] < week_periods]
    piv = m.groupby(["cohort", "week"])["amount"].sum().unstack(fill_value=0)
    piv = piv.reindex(index=n_users.index, columns=range(week_periods), fill_value=0)
    ltv = piv.div(n_users, axis=0).cumsum(axis=1).round(2)
    ltv.columns = [f"第{w + 1}周" for w in ltv.columns]
    return ltv
