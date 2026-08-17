"""流失预警：特征工程 + 机器学习预测「未来 N 天是否活跃」（v2：窗口特征 + GBDT + 时间切分 + 阈值优化）。

思路（与真实业务一致）：
  以 cut = 最后活跃日 - horizon 为切点，
  特征窗口 [start, cut] 构造用户行为特征（活跃/频率/间隔/付费/关卡 + 近因窗口特征），
  标签 = 用户在 (cut, end] 是否还有活跃记录。
  训练逻辑回归 + 随机森林 + HistGradientBoosting，输出特征重要性（可解释「什么特征预示流失」）
  和高危用户名单（按最佳阈值过滤 + 概率排序，供运营触达）。

v2 相对 v1 的改进：
  - 特征工程：新增「最近 7/14 天活跃天数」「活跃趋势」「距上次付费天数」「关卡推进速度」等窗口特征，
    捕捉"近期活跃度下降"这一最强流失信号；
  - 模型：新增 HistGradientBoostingClassifier（GBDT 族，通常比 RF/LR 更强）；
  - 时间切分：默认按「最近活跃日期」排序切分训练/验证（用过去预测未来，避免随机切分的信息泄漏）；
  - 阈值优化：在验证集上按 Youden's J 找最佳分类阈值，高危名单与阈值口径一致。
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score, roc_curve)


def build_features(login_df, users_df, pay_df=None, level_df=None, horizon=7):
    """构造特征表（含标签列「未来是否活跃」）。

    返回的特征列除业务特征外，含「最近活跃日期」（时间切分排序键，不进模型）。
    """
    d = login_df.copy()
    d["date"] = pd.to_datetime(d["date"])
    users = users_df.copy()
    users["reg_date"] = pd.to_datetime(users["reg_date"])
    end = d["date"].max()
    cut = end - pd.Timedelta(days=horizon)

    feat = d[d["date"] <= cut].copy()
    rows = []
    for uid, g in feat.groupby("user_id"):
        dates = g["date"].sort_values()
        days_active = int(dates.nunique())
        span = max(int((cut - dates.min()).days), 1)
        recency = int((cut - dates.max()).days)
        gaps = dates.diff().dt.days.dropna()
        weekend = float(dates.dt.weekday.isin([5, 6]).mean()) if len(dates) else 0.0
        # 近因窗口特征：最近 7/14 天活跃天数（捕捉活跃度衰减）
        win7 = int(dates[dates >= cut - pd.Timedelta(days=7)].nunique())
        win14 = int(dates[dates >= cut - pd.Timedelta(days=14)].nunique())
        # 活跃趋势：cut 前 1/3 时段 vs 后 2/3 时段的日均活跃比
        t0, t1, t2 = dates.min(), cut - pd.Timedelta(days=span // 3), cut
        early = int(dates[(dates >= t0) & (dates < t1)].nunique())
        late = int(dates[(dates >= t1) & (dates <= t2)].nunique())
        trend = round(late / max(early, 1), 4) if early > 0 else round(late + 1, 4)
        rows.append({
            "user_id": int(uid),
            "活跃天数": days_active,
            "活跃频率": round(days_active / span, 4),
            "最近活跃距今(天)": recency,
            "平均活跃间隔(天)": round(float(gaps.mean()), 2) if len(gaps) else 0.0,
            "间隔标准差": round(float(gaps.std()), 2) if len(gaps) > 1 else 0.0,
            "周末活跃占比": weekend,
            "最近7天活跃天数": win7,
            "最近14天活跃天数": win14,
            "活跃趋势(后半/前半)": trend,
            "最近活跃日期": dates.max(),
        })
    df = pd.DataFrame(rows)

    # 付费特征（cut 之前）
    if pay_df is not None and len(pay_df):
        p = pay_df.copy()
        p["date"] = pd.to_datetime(p["date"])
        p_cut = p[p["date"] <= cut]
        pay_g = p_cut.groupby("user_id").agg(
            付费金额=("amount", "sum"), 付费次数=("amount", "size"),
            最近付费日期=("date", "max"))
        df = df.merge(pay_g, on="user_id", how="left")
        df["付费金额"] = df["付费金额"].fillna(0.0)
        df["付费次数"] = df["付费次数"].fillna(0).astype(int)
        # 距上次付费天数（未付费用户给一个大值，如 span）
        df["距上次付费天数"] = (cut - df["最近付费日期"]).dt.days.fillna(span).astype(int)
        df = df.drop(columns=["最近付费日期"])
    else:
        df["付费金额"] = 0.0
        df["付费次数"] = 0
        df["距上次付费天数"] = span

    # 关卡特征（cut 之前达到的最高关卡 + 推进速度）
    if level_df is not None and len(level_df):
        lv = level_df.copy()
        lv["date"] = pd.to_datetime(lv["date"])
        max_lv = lv[lv["date"] <= cut].groupby("user_id")["level"].max().rename("最高关卡")
        df = df.merge(max_lv, on="user_id", how="left")
        df["最高关卡"] = df["最高关卡"].fillna(0).astype(int)
    else:
        df["最高关卡"] = 0
    df["关卡推进速度"] = round(df["最高关卡"] / df["活跃天数"].replace(0, 1), 4)

    # 标签：cut 之后是否活跃
    future = d[d["date"] > cut]["user_id"].unique()
    df["未来是否活跃"] = df["user_id"].isin(future).astype(int)
    return df


def _best_threshold(y_true, proba):
    """Youden's J 最优阈值：最大化 敏感度 + 特异度 - 1。"""
    fpr, tpr, thrs = roc_curve(y_true, proba)
    if len(thrs) == 0:
        return 0.5
    j = tpr - fpr
    return float(thrs[int(np.argmax(j))])


def churn_prediction(login_df, users_df, pay_df=None, level_df=None,
                     horizon=7, top_k=20, test_size=0.3, seed=42, split="time"):
    """训练流失预测模型，返回结构化结果（模型对比 / 特征重要性 / 高危名单 / 最佳阈值）。

    参数:
        split: "time"（默认，按最近活跃日期切分，用过去预测未来）| "random"（随机分层）
    """
    feats = build_features(login_df, users_df, pay_df, level_df, horizon=horizon)
    feature_cols = [c for c in feats.columns
                    if c not in ("user_id", "未来是否活跃", "最近活跃日期")]
    if len(feats) < 50:
        raise ValueError(f"有效样本只有 {len(feats)}，请增加数据或减小 horizon")
    X = feats[feature_cols].fillna(0)
    y = feats["未来是否活跃"]

    if split == "time":
        # 时间切分：按最近活跃日期排序，前段训练 / 后段验证（避免信息泄漏）
        order = feats["最近活跃日期"].reset_index(drop=True).argsort()
        X, y = X.reset_index(drop=True).iloc[order], y.reset_index(drop=True).iloc[order]
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        split_note = f"时间切分（按最近活跃日期：前 {split_idx} 训练 / 后 {len(X) - split_idx} 验证）"
    else:
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=seed, stratify=y)
        split_note = f"随机分层切分（训练 {len(X_train)} / 验证 {len(X_test)}）"

    zoo = {
        "逻辑回归": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "随机森林": RandomForestClassifier(n_estimators=200, max_depth=6,
                                           random_state=seed, class_weight="balanced"),
        "梯度提升(HistGB)": HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.05, max_depth=4,
            class_weight="balanced", random_state=seed),
    }
    results = []
    for name, model in zoo.items():
        try:
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            proba = model.predict_proba(X_test)[:, 1]
            results.append({
                "模型": name,
                "准确率": round(float(accuracy_score(y_test, pred)), 4),
                "F1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
                "AUC": round(float(roc_auc_score(y_test, proba)), 4)
                if len(set(y_test)) > 1 else None,
                "_model": model,
            })
        except Exception as e:  # noqa: BLE001 - 单模型失败不影响整体
            results.append({"模型": name, "错误": str(e)})

    def key(r):
        return r.get("AUC") if r.get("AUC") is not None else (r.get("F1", -1) if "F1" in r else -1)
    results.sort(key=key, reverse=True)
    best = next((r for r in results if "_model" in r), None)
    if best is None:
        raise ValueError("所有模型训练失败")

    model = best["_model"]
    if hasattr(model, "feature_importances_"):
        imp = dict(zip(feature_cols, np.round(model.feature_importances_, 4)))
    else:
        imp = dict(zip(feature_cols, np.round(np.abs(model.coef_[0]), 4)))

    # 阈值优化：验证集 Youden's J 最佳阈值
    proba_test = model.predict_proba(X_test)[:, 1]
    best_thr = _best_threshold(y_test.values, proba_test)
    # 高危名单：全量用户按最佳阈值过滤（兜底：不足 top_k 时按概率取前 top_k）
    proba_all = model.predict_proba(X)[:, 1]
    warn = pd.DataFrame({"user_id": feats["user_id"].values, "流失概率": np.round(proba_all, 4)})
    warn = warn[warn["流失概率"] >= best_thr].sort_values("流失概率", ascending=False)
    if len(warn) < min(top_k, len(feats)):
        warn = pd.DataFrame({"user_id": feats["user_id"].values,
                             "流失概率": np.round(proba_all, 4)}).sort_values(
            "流失概率", ascending=False)
    warn = warn.head(top_k).reset_index(drop=True)

    return {
        "口径": f"预测未来 {horizon} 天是否活跃（流失=不活跃）",
        "样本数": int(len(y)),
        "流失率%": round(float((1 - y.mean()) * 100), 2),
        "切分方式": split_note,
        "最佳阈值": round(best_thr, 4),
        "模型对比": [{k: v for k, v in r.items() if k != "_model"} for r in results],
        "最优模型": best["模型"],
        "特征重要性": imp,
        "高危用户": warn,
    }
