"""流失预警：特征工程 + 机器学习预测「未来 N 天是否活跃」。

思路（与真实业务一致）：
  以 cut = 最后活跃日 - horizon 为切点，
  特征窗口 [start, cut] 构造用户行为特征（活跃/频率/间隔/付费/关卡），
  标签 = 用户在 (cut, end] 是否还有活跃记录。
  训练逻辑回归 + 随机森林，输出特征重要性（可解释「什么特征预示流失」）
  和高危用户 TopN（流失概率排序，供运营触达）。
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split


def build_features(login_df, users_df, pay_df=None, level_df=None, horizon=7):
    """构造特征表（含标签列「未来是否活跃」）。"""
    d = login_df.copy()
    d["date"] = pd.to_datetime(d["date"])
    users = users_df.copy()
    users["reg_date"] = pd.to_datetime(users["reg_date"])
    end = d["date"].max()
    cut = end - pd.Timedelta(days=horizon)

    feat = d[d["date"] <= cut].copy()
    rows = []
    for uid, g in feat.groupby("user_id"):
        days_active = int(g["date"].nunique())
        span = max(int((cut - g["date"].min()).days), 1)
        recency = int((cut - g["date"].max()).days)
        gaps = g["date"].sort_values().diff().dt.days.dropna()
        weekend = float(g["date"].dt.weekday.isin([5, 6]).mean()) if len(g) else 0.0
        rows.append({
            "user_id": int(uid),
            "活跃天数": days_active,
            "活跃频率": round(days_active / span, 4),
            "最近活跃距今(天)": recency,
            "平均活跃间隔(天)": round(float(gaps.mean()), 2) if len(gaps) else 0.0,
            "间隔标准差": round(float(gaps.std()), 2) if len(gaps) > 1 else 0.0,
            "周末活跃占比": weekend,
        })
    df = pd.DataFrame(rows)

    # 付费特征（cut 之前）
    if pay_df is not None and len(pay_df):
        p = pay_df.copy()
        p["date"] = pd.to_datetime(p["date"])
        pay_g = p[p["date"] <= cut].groupby("user_id").agg(
            付费金额=("amount", "sum"), 付费次数=("amount", "size"))
        df = df.merge(pay_g, on="user_id", how="left")
        df["付费金额"] = df["付费金额"].fillna(0.0)
        df["付费次数"] = df["付费次数"].fillna(0).astype(int)
    else:
        df["付费金额"] = 0.0
        df["付费次数"] = 0

    # 关卡特征（cut 之前达到的最高关卡）
    if level_df is not None and len(level_df):
        lv = level_df.copy()
        lv["date"] = pd.to_datetime(lv["date"])
        max_lv = lv[lv["date"] <= cut].groupby("user_id")["level"].max().rename("最高关卡")
        df = df.merge(max_lv, on="user_id", how="left")
        df["最高关卡"] = df["最高关卡"].fillna(0).astype(int)
    else:
        df["最高关卡"] = 0

    # 标签：cut 之后是否活跃
    future = d[d["date"] > cut]["user_id"].unique()
    df["未来是否活跃"] = df["user_id"].isin(future).astype(int)
    return df


def churn_prediction(login_df, users_df, pay_df=None, level_df=None,
                     horizon=7, top_k=20, test_size=0.3, seed=42):
    """训练流失预测模型，返回结构化结果（模型对比 / 特征重要性 / 高危名单）。"""
    feats = build_features(login_df, users_df, pay_df, level_df, horizon=horizon)
    feature_cols = [c for c in feats.columns if c not in ("user_id", "未来是否活跃")]
    if len(feats) < 50:
        raise ValueError(f"有效样本只有 {len(feats)}，请增加数据或减小 horizon")
    X = feats[feature_cols].fillna(0)
    y = feats["未来是否活跃"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y)

    zoo = {
        "逻辑回归": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "随机森林": RandomForestClassifier(n_estimators=200, max_depth=6,
                                           random_state=seed, class_weight="balanced"),
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
        except Exception as e:
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

    proba_all = model.predict_proba(X)[:, 1]
    warn = pd.DataFrame({"user_id": feats["user_id"], "流失概率": np.round(proba_all, 4)})
    warn = warn.sort_values("流失概率", ascending=False).head(top_k).reset_index(drop=True)

    return {
        "口径": f"预测未来 {horizon} 天是否活跃（流失=不活跃）",
        "样本数": int(len(y)),
        "流失率%": round(float((1 - y.mean()) * 100), 2),
        "模型对比": [{k: v for k, v in r.items() if k != "_model"} for r in results],
        "最优模型": best["模型"],
        "特征重要性": imp,
        "高危用户": warn,
    }
