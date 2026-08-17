"""AutoML：基于 Optuna 的超参数自动搜索 + 多模型对比。

相比固定默认参数的模型，Optuna 会搜索随机森林 / 梯度提升 / 线性模型的
超参数空间（TPE 采样），并给出调参过程曲线 —— 这是求职作品里
「算法深度」的核心展示点。
"""
import numpy as np
import pandas as pd
import optuna

from sklearn.ensemble import (GradientBoostingClassifier,
                              GradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from .ml_runner import _prepare

optuna.logging.set_verbosity(optuna.logging.WARNING)

MODEL_NAMES = ["随机森林", "梯度提升", "线性模型"]


def _build_model(task: str, trial, name: str):
    """按 trial 的超参建议构建模型。"""
    if name == "随机森林":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 20),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 6),
        }
        model = (RandomForestClassifier(**params, random_state=42)
                 if task == "classification"
                 else RandomForestRegressor(**params, random_state=42))
        return model, params

    if name == "梯度提升":
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=50),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        }
        model = (GradientBoostingClassifier(**params, random_state=42)
                 if task == "classification"
                 else GradientBoostingRegressor(**params, random_state=42))
        return model, params

    # 线性模型（无超参搜索）
    model = (LogisticRegression(max_iter=2000, C=1.0)
             if task == "classification" else LinearRegression())
    return model, {}


def automl_train(df: pd.DataFrame, target: str, n_trials: int = 30,
                 test_size: float = 0.2, random_state: int = 42, cv: int = 3):
    """对每个模型族做 Optuna 搜索，返回可 JSON 序列化的完整结果。"""
    X, y, task, features = _prepare(df, target)
    if len(y) < 20:
        raise ValueError(f"有效样本只有 {len(y)} 条，建议至少 20 条")
    if len(features) == 0:
        raise ValueError("没有可用特征列（全部为高基数文本或全空）")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state,
        stratify=(y if task == "classification" else None),
    )
    # 优化目标与最终排序指标保持一致：分类用 F1(weighted)，回归用 R²
    scoring = "f1_weighted" if task == "classification" else "r2"
    metric_keys = ("F1", "准确率") if task == "classification" else ("R²", "RMSE")

    results, best_study = [], None
    for name in MODEL_NAMES:
        def objective(trial, _name=name):
            model, _ = _build_model(task, trial, _name)
            try:
                return float(cross_val_score(model, X_train, y_train, cv=min(cv, len(y_train) // 5),
                                             scoring=scoring, n_jobs=1).mean())
            except Exception:
                return -1.0

        study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=random_state))
        study.optimize(objective, n_trials=n_trials)

        best_model, best_params = _build_model(task, optuna.trial.FixedTrial(study.best_params), name)
        best_model.fit(X_train, y_train)
        pred = best_model.predict(X_test)

        if task == "classification":
            metrics = {
                "准确率": round(float(accuracy_score(y_test, pred)), 4),
                "F1": round(float(f1_score(y_test, pred, average="weighted", zero_division=0)), 4),
            }
        else:
            metrics = {
                "R²": round(float(r2_score(y_test, pred)), 4),
                "RMSE": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
            }

        # 调参曲线：每次 trial 的得分
        trials = [{"trial": t.number, "得分": round(float(t.value), 4)}
                  for t in study.trials if t.value is not None]

        results.append({
            "模型": name,
            "最优CV得分": round(float(study.best_value), 4),
            **metrics,
            "最优参数": {k: (int(v) if isinstance(v, (int, np.integer)) else round(float(v), 4))
                        for k, v in best_params.items()},
            "调参曲线": trials,
            "_model": best_model,
        })

    results.sort(key=lambda r: r.get("F1" if task == "classification" else "R²", -1e9), reverse=True)
    best = results[0]

    # 特征重要性（最优模型）
    importance = {}
    model = best.get("_model")
    if model is not None and hasattr(model, "feature_importances_"):
        importance = dict(zip(features, np.round(model.feature_importances_, 4)))
    elif model is not None and hasattr(model, "coef_"):
        coef = np.asarray(model.coef_).ravel()
        importance = dict(zip(features, np.round(np.abs(coef), 4)))

    # 去掉内部对象，保证可 JSON 序列化
    for r in results:
        r.pop("_model", None)

    return {
        "task": "回归" if task == "regression" else "分类",
        "样本数": int(len(y)),
        "特征数": int(X.shape[1]),
        "最优模型": best["模型"],
        "测试集指标": {k: v for k, v in best.items() if k in metric_keys},
        "模型对比": results,
        "特征重要性": importance,
        "说明": "每个模型用 Optuna(TPE) 搜索超参；得分=交叉验证均值（分类 F1(weighted) / 回归 R²），与最终排序指标一致。",
    }
