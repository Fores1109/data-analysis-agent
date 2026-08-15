"""SHAP 模型解释：特征贡献、单样本 waterfall、依赖图。

用训练好的树模型 + SHAP TreeExplainer，把「黑盒模型为什么这么预测」
变成可解释的贡献值 —— 算法岗面试的高频追问点。
"""
import numpy as np
import pandas as pd

from .ml_runner import _prepare

_TREE_MODEL = None  # 模块级缓存，避免重复训练（页面内再包一层 st.cache_data）


def train_tree(df: pd.DataFrame, target: str):
    """训练一个用于解释的树模型（梯度提升），返回 (model, X, y, task, features)。"""
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

    X, y, task, features = _prepare(df, target)
    if len(features) == 0:
        raise ValueError("没有可用特征")
    model = (GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42)
             if task == "classification"
             else GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42))
    model.fit(X, y)
    return model, X, y, task, features


def shap_values(df: pd.DataFrame, target: str):
    """返回 SHAP 摘要：均值绝对贡献排序的特征重要性。"""
    import shap

    model, X, y, task, features = train_tree(df, target)
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    if isinstance(sv, list):          # 分类模型返回每类别一组
        sv = np.mean(sv, axis=0)      # 多类别取平均贡献
    sv = np.asarray(sv, dtype=float)

    mean_abs = np.abs(sv).mean(axis=0)
    importance = dict(sorted(zip(features, mean_abs), key=lambda x: -float(x[1])))
    return {
        "特征重要性": importance,
        "_sv": sv,
        "_X": X,
        "_features": features,
        "_expected": float(np.asarray(explainer.expected_value).mean()),
    }


def explain_sample(df: pd.DataFrame, target: str, index: int = 0, shap_res: dict = None):
    """单个样本的逐特征贡献（waterfall 数据）。shap_res 可传入 shap_values 的缓存结果。"""
    s = shap_res or shap_values(df, target)
    sv, X, features = s["_sv"], s["_X"], s["_features"]
    idx = min(int(index), len(X) - 1)
    vals = sv[idx]
    base = s["_expected"]
    items = sorted(zip(features, vals), key=lambda x: -abs(float(x[1])))
    return {
        "基准值": round(float(base), 4),
        "预测值": round(float(base + float(vals.sum())), 4),
        "样本序号": int(idx),
        "贡献": [{"特征": str(f), "贡献": round(float(v), 4)} for f, v in items],
    }


def dependence(df: pd.DataFrame, target: str, feature: str, shap_res: dict = None):
    """特征依赖图数据：x=特征值，y=SHAP 贡献。shap_res 可传入缓存结果。"""
    s = shap_res or shap_values(df, target)
    X, sv, features = s["_X"], s["_sv"], s["_features"]
    if feature not in features:
        raise ValueError(f"特征不存在: {feature}")
    i = features.index(feature)
    return {
        "特征": feature,
        "x": [round(float(v), 4) for v in X[feature].tolist()],
        "shap": [round(float(v), 4) for v in sv[:, i].tolist()],
    }
