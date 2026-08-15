"""机器学习模块：自动推断任务类型、自动选模型、训练/测试、指标对比、特征重要性。"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

_CLF_ZOO = {
    "逻辑回归": LogisticRegression(max_iter=1000),
    "随机森林": RandomForestClassifier(n_estimators=100, random_state=42),
}
_REG_ZOO = {
    "线性回归": LinearRegression(),
    "随机森林回归": RandomForestRegressor(n_estimators=100, random_state=42),
}


def _prepare(df: pd.DataFrame, target: str):
    """特征工程：数值化、补空值。返回 (X, y, task, feature_names)。"""
    d = df.copy()
    if target not in d.columns:
        raise ValueError(f"目标列不存在: {target}")

    # 只保留数值列 + 低基数类别列（编码后使用）
    keep = []
    for col in d.columns:
        if col == target:
            continue
        if pd.api.types.is_numeric_dtype(d[col]):
            keep.append(col)
        elif d[col].nunique(dropna=True) <= 20:  # 低基数类别列
            keep.append(col)
    d = d[keep + [target]].copy()

    # 目标列编码
    y_raw = d[target]
    if pd.api.types.is_numeric_dtype(y_raw) and y_raw.nunique(dropna=True) > 10:
        task = "regression"
        y = pd.to_numeric(y_raw, errors="coerce")
    else:
        task = "classification"
        le = LabelEncoder()
        y = pd.Series(le.fit_transform(y_raw.astype(str)), index=d.index)

    # 特征编码
    X = d[keep].copy()
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = LabelEncoder().fit_transform(X[col].astype(str))

    # 补空值（数值列用中位数）
    imp = SimpleImputer(strategy="median")
    X = pd.DataFrame(imp.fit_transform(X), columns=X.columns)

    mask = y.notna()
    return X[mask], y[mask], task, list(X.columns)


def auto_train(df: pd.DataFrame, target: str, test_size: float = 0.2, random_state: int = 42):
    """自动训练多个候选模型，返回最优模型及完整评估结果。"""
    X, y, task, feature_names = _prepare(df, target)
    if len(y) < 20:
        raise ValueError(f"有效样本只有 {len(y)} 条，建议至少 20 条")

    zoo = _CLF_ZOO if task == "classification" else _REG_ZOO
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=(y if task == "classification" else None)
    )

    results = []
    for name, model in zoo.items():
        try:
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            cv = cross_val_score(model, X, y, cv=min(5, max(2, len(y) // 10)), scoring="accuracy" if task == "classification" else "r2")
            if task == "classification":
                metrics = {
                    "准确率": round(accuracy_score(y_test, pred), 4),
                    "F1": round(f1_score(y_test, pred, average="weighted", zero_division=0), 4),
                }
            else:
                metrics = {
                    "R²": round(r2_score(y_test, pred), 4),
                    "RMSE": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
                }
            results.append({
                "模型": name,
                "交叉验证均值": round(float(cv.mean()), 4),
                **metrics,
                "_model": model,
                "_task": task,
                "_pred": pred,
            })
        except Exception as e:
            results.append({"模型": name, "交叉验证均值": None, "错误": str(e)})

    # 选最优：分类看 F1，回归看 R²
    def score_key(r):
        if "错误" in r:
            return -1e9
        return r.get("F1" if task == "classification" else "R²", -1e9)

    results.sort(key=score_key, reverse=True)
    best = results[0]

    # 特征重要性（随机森林用 feature_importances_，线性用 |系数|）
    importance = {}
    model = best.get("_model")
    if model is not None and hasattr(model, "feature_importances_"):
        importance = dict(zip(feature_names, np.round(model.feature_importances_, 4)))
    elif model is not None and hasattr(model, "coef_"):
        coef = np.asarray(model.coef_).ravel()
        importance = dict(zip(feature_names, np.round(np.abs(coef), 4)))

    summary = {
        "task": "回归" if task == "regression" else "分类",
        "样本数": int(len(y)),
        "特征数": int(X.shape[1]),
        "最优模型": best.get("模型"),
        "候选结果": [{k: v for k, v in r.items() if not k.startswith("_")} for r in results],
        "特征重要性": importance,
        "测试集指标": {k: v for k, v in best.items() if k in ("F1", "R²", "RMSE", "准确率")},
    }
    return summary
