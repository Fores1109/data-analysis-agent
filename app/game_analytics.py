"""游戏厂商数据分析：留存 / 活跃 / 付费（游戏行业垂直模块）。

数据约定（用户上传或内置模拟生成）：
- 登录日志 login_df: user_id, date            —— 每行 = 某用户某天活跃
- 付费日志 pay_df:   user_id, date, amount
- 用户表 users_df:   user_id, reg_date, channel（可缺省，缺省时从登录日志推最早活跃日）

核心指标（游戏行业标准）：
- 留存：次日/3日/7日/14日/30日留存率；按注册周分群的同期群留存矩阵
- 活跃：DAU / WAU / MAU、DAU/MAU 粘性
- 付费：付费率、ARPU（人均收入）、ARPPU（付费用户人均）、每日收入
"""
import numpy as np
import pandas as pd


def simulate_game_data(n_users: int = 3000, days: int = 120, seed: int = 42,
                       start: str = "2024-01-01"):
    """生成逼真的模拟游戏数据（幂律留存衰减 + 渠道差异 + 周末加成 + 帕累托付费）。

    返回 (login_df, pay_df, users_df)。
    """
    rng = np.random.default_rng(seed)
    start_ts = pd.Timestamp(start)
    reg_days = rng.integers(0, max(days - 30, 10), n_users)
    channels = rng.choice(["自然量", "买量投放", "活动拉新"], n_users, p=[0.5, 0.3, 0.2])
    base_r1 = rng.uniform(0.30, 0.55, n_users)     # 次日留存基数
    alpha = rng.uniform(0.55, 0.95, n_users)       # 衰减指数（越大衰减越快）
    base_r1 = np.where(channels == "买量投放", base_r1 * 0.8, base_r1)   # 买量留存略低
    base_r1 = np.where(channels == "活动拉新", base_r1 * 1.15, base_r1)  # 活动用户略高

    login_rows, pay_rows = [], []
    for i in range(n_users):
        uid, reg, ch = i + 1, int(reg_days[i]), channels[i]
        r1, a = base_r1[i], alpha[i]
        for d in range(reg, days):
            age = d - reg
            p = 1.0 if age == 0 else r1 * (age + 1) ** (-a)   # 注册当天必活跃
            weekday = (start_ts + pd.Timedelta(days=d)).weekday()
            if weekday >= 5:
                p *= 1.15                            # 周末加成
            if rng.random() < p:
                date = (start_ts + pd.Timedelta(days=d)).date()
                login_rows.append((uid, date, ch, age))
                if rng.random() < 0.08:              # 活跃日约 8% 概率付费
                    amt = float(np.round(rng.pareto(1.8) * 30 + 6, 2))
                    pay_rows.append((uid, date, amt))

    login_df = pd.DataFrame(login_rows, columns=["user_id", "date", "channel", "day_age"])
    pay_df = pd.DataFrame(pay_rows, columns=["user_id", "date", "amount"])
    users_df = pd.DataFrame({
        "user_id": np.arange(1, n_users + 1),
        "reg_date": [start_ts + pd.Timedelta(days=int(d)) for d in reg_days],
        "channel": channels,
    })
    return login_df, pay_df, users_df


def _users_from_login(login_df, user_col, date_col):
    """没有用户表时，用最早活跃日当注册日。"""
    g = login_df.groupby(user_col)[date_col].min().reset_index()
    g.columns = [user_col, "reg_date"]
    g["channel"] = "未知渠道"
    return g


def _normalize_cols(df, mapping):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df.rename(columns={v: k for k, v in mapping.items()})


def retention_matrix(login_df, users_df=None, user_col="user_id", date_col="date",
                     periods=(1, 3, 7, 14, 30)):
    """同期群留存矩阵：行=注册周，列=第 N 日留存率(%)。"""
    login_df = _normalize_cols(login_df, {"user_id": user_col, "date": date_col})
    user_col, date_col = "user_id", "date"
    u = users_df if users_df is not None else _users_from_login(login_df, user_col, date_col)
    u = _normalize_cols(u, {"user_id": user_col, "reg_date": "reg_date", "channel": "channel"})

    m = login_df.merge(u[["user_id", "reg_date"]], on="user_id")
    m[date_col] = pd.to_datetime(m[date_col])
    m["reg_date"] = pd.to_datetime(m["reg_date"])
    m["age"] = (m[date_col] - m["reg_date"]).dt.days
    m["cohort"] = m["reg_date"].dt.to_period("W").astype(str)

    u["reg_date"] = pd.to_datetime(u["reg_date"])
    end = m[date_col].max()
    u["max_age"] = (end - u["reg_date"]).dt.days
    u["cohort"] = u["reg_date"].dt.to_period("W").astype(str)
    denom_all = u.groupby("cohort")["user_id"].nunique()

    out = {}
    for p in periods:
        num = m[m["age"] == p].groupby("cohort")["user_id"].nunique()
        denom = u[u["max_age"] >= p].groupby("cohort")["user_id"].nunique()
        out[f"第{p}日"] = (num / denom * 100).round(2)
    df = pd.DataFrame(out).fillna(0).sort_index()
    df.index.name = "注册周"
    return df


def retention_curve(login_df, users_df=None, max_day: int = 30,
                    user_col="user_id", date_col="date"):
    """整体留存曲线：第 N 天活跃用户 / 注册满 N+1 天的用户。"""
    login_df = _normalize_cols(login_df, {"user_id": user_col, "date": date_col})
    user_col, date_col = "user_id", "date"
    u = users_df if users_df is not None else _users_from_login(login_df, user_col, date_col)
    u = _normalize_cols(u, {"user_id": user_col, "reg_date": "reg_date"})

    m = login_df.merge(u[["user_id", "reg_date"]], on="user_id")
    m[date_col] = pd.to_datetime(m[date_col])
    m["reg_date"] = pd.to_datetime(m["reg_date"])
    m["age"] = (m[date_col] - m["reg_date"]).dt.days
    end = m[date_col].max()

    rows = []
    for age in range(0, max_day + 1):
        num = m[m["age"] == age]["user_id"].nunique()
        denom = int((u["reg_date"] <= end - pd.Timedelta(days=age)).sum())
        rows.append({"第N天": age, "留存率%": round(num / denom * 100, 2) if denom else 0.0})
    return pd.DataFrame(rows)


def retention_by_channel(login_df, users_df, periods=(1, 7, 30),
                         user_col="user_id", date_col="date"):
    """各渠道的 N 日留存对比。"""
    login_df = _normalize_cols(login_df, {"user_id": user_col, "date": date_col})
    u = _normalize_cols(users_df, {"user_id": user_col, "reg_date": "reg_date", "channel": "channel"})
    rows = []
    for ch in u["channel"].dropna().unique():
        sub_u = u[u["channel"] == ch]
        ret = retention_matrix(login_df, sub_u, periods=periods)
        for p in periods:
            rows.append({"渠道": ch, "指标": f"第{p}日留存", "留存率%": float(ret[f"第{p}日"].mean())})
    return pd.DataFrame(rows)


def activity_metrics(login_df, user_col="user_id", date_col="date"):
    """DAU / WAU / MAU 与 DAU/MAU 粘性。返回各序列 DataFrame。"""
    d = _normalize_cols(login_df, {"user_id": user_col, "date": date_col})
    d["date"] = pd.to_datetime(d["date"]).dt.normalize()
    d = d.set_index("date").sort_index()
    dau = d["user_id"].resample("D").nunique()
    wau = d["user_id"].resample("W").nunique()
    mau = d["user_id"].resample("ME").nunique()
    stickiness = round(float(dau.mean() / mau.mean() * 100), 2) if mau.mean() else 0.0
    return {"DAU": dau, "WAU": wau, "MAU": mau, "DAU/MAU粘性%": stickiness,
            "DAU均值": int(dau.mean()), "峰值DAU": int(dau.max())}


def payment_metrics(pay_df, users_df=None, user_col="user_id",
                    date_col="date", amount_col="amount"):
    """付费率 / ARPU / ARPPU / 每日收入。"""
    p = _normalize_cols(pay_df, {"user_id": user_col, "date": date_col, "amount": amount_col})
    p["date"] = pd.to_datetime(p["date"])
    total = float(p["amount"].sum())
    payers = int(p["user_id"].nunique())
    n_users = len(users_df) if users_df is not None else payers
    daily = p.groupby(p["date"].dt.date)["amount"].sum().sort_index()
    return {
        "总收入": round(total, 2),
        "付费用户数": payers,
        "付费率%": round(payers / n_users * 100, 2) if n_users else 0.0,
        "ARPU": round(total / n_users, 2) if n_users else 0.0,
        "ARPPU": round(total / payers, 2) if payers else 0.0,
        "每日收入": daily,
    }


# 行业参考基准（面试/解读用）
INDUSTRY_BENCHMARKS = {
    "次日留存": "35% 及格、40%+ 良好、50%+ 优秀（休闲游戏更高，重度略低）",
    "7日留存": "15% 及格、20%+ 良好",
    "30日留存": "5% 及格、8-10% 良好",
    "付费率": "2%-5% 属常见区间，SLG/数值卡牌可更高",
    "DAU/MAU 粘性": "20% 以上算活跃健康，低于 15% 说明老用户流失快",
    "ARPPU": "品类差异大：休闲 1-10 元，中重度 50-500 元",
}
