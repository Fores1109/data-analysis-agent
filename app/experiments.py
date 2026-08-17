"""A/B 实验与因果推断（教育级简化实现，供数据分析场景使用）。

包含：
  - ab_ttest: 两组均值差异检验（Welch t 检验 + Cohen's d 效应量）
  - ab_proportion: 两组转化率差异检验（z 检验）
  - ols: 带控制变量的多元回归（numpy 实现，输出系数/标准误/t/p/R²）
  - did: 双重差分估计（DID）
"""
import numpy as np
import pandas as pd
from scipy import stats


def _conclusion(p, d_effect, metric="均值"):
    """把 p 值和效应量翻译成一句人话。"""
    if np.isnan(p):
        return "样本不足或数据异常，无法给出结论。"
    if p < 0.05:
        part = f"差异具有统计显著性（p={p:.4f} < 0.05）"
    else:
        part = f"差异不显著（p={p:.4f} ≥ 0.05）"
    size = "无" if abs(d_effect) < 0.2 else ("小" if abs(d_effect) < 0.5 else ("中" if abs(d_effect) < 0.8 else "大"))
    return f"{part}，效应量 {size}（d={d_effect:+.3f}）。{'建议谨慎下结论' if p >= 0.05 else '可认为实验组与对照组存在差异'}。"


def ab_ttest(control, treatment):
    """两组连续指标 A/B 检验。control/treatment 为 array-like。"""
    a = pd.to_numeric(pd.Series(control), errors="coerce").dropna().values
    b = pd.to_numeric(pd.Series(treatment), errors="coerce").dropna().values
    if len(a) < 3 or len(b) < 3:
        raise ValueError("每组至少需要 3 个有效样本")
    t, p = stats.ttest_ind(a, b, equal_var=False)
    # Cohen's d：pooled SD 用自由度加权的合并标准差（而非两组 std 的简单平均）
    n1, n2 = len(a), len(b)
    s1, s2 = a.std(ddof=1), b.std(ddof=1)
    pooled = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2)) if n1 + n2 > 2 else 0.0
    d = (b.mean() - a.mean()) / pooled if pooled > 0 else 0.0
    return {
        "对照组均值": round(float(a.mean()), 4),
        "实验组均值": round(float(b.mean()), 4),
        "差异": round(float(b.mean() - a.mean()), 4),
        "t 值": round(float(t), 4),
        "p 值": round(float(p), 4),
        "Cohen's d": round(float(d), 4),
        "结论": _conclusion(p, d),
    }


def ab_proportion(control_success, control_n, treat_success, treat_n, correct: bool = True):
    """两组转化率 A/B 检验（双比例 z 检验，默认带 Yates 连续性校正）。

    correct=True 时对 z 统计量做 Yates 连续性校正（更保守，小样本更稳妥；
    样本量较大时校正影响可忽略，与主流统计库行为一致）。
    """
    p1, p2 = control_success / control_n, treat_success / treat_n
    p_pool = (control_success + treat_success) / (control_n + treat_n)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / control_n + 1 / treat_n))
    diff = p2 - p1
    if correct:
        # Yates 连续性校正：|差异| 减去半个单位频数对应的比例差，保留方向
        correction = 0.5 * (1 / control_n + 1 / treat_n)
        diff = max(0.0, abs(diff) - correction) * np.sign(diff)
    z = diff / se if se > 0 else 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    d = (p2 - p1) / np.sqrt(p_pool * (1 - p_pool)) if 0 < p_pool < 1 else 0.0
    return {
        "对照组转化率": round(float(p1), 4),
        "实验组转化率": round(float(p2), 4),
        "转化率提升": f"{100 * (p2 - p1):+.2f}%",
        "z 值": round(float(z), 4),
        "p 值": round(float(p), 4),
        "连续性校正": correct,
        "结论": _conclusion(p, d, "转化率"),
    }


def simulate_ab(n_per_group=500, effect=0.5, control_mean=100, std=20, seed=42):
    """生成模拟 A/B 数据用于演示：返回 (control, treatment)。"""
    rng = np.random.default_rng(seed)
    control = rng.normal(control_mean, std, n_per_group)
    treatment = rng.normal(control_mean + effect * std, std, n_per_group)
    return control, treatment


# ---------- 因果推断 ----------
def ols(df: pd.DataFrame, outcome: str, predictors: list):
    """多元线性回归（numpy OLS）：返回系数表与拟合指标。

    注意：回归只能控制已观测混杂，不能证明因果；报告里会给出提示。
    """
    d = df.copy()
    X = d[predictors].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(d[outcome], errors="coerce")
    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]
    n, k = len(y), X.shape[1] + 1
    if n < k + 2:
        raise ValueError(f"有效样本 {n} 太少，无法估计 {k} 个参数")
    Xd = np.column_stack([np.ones(n), X.values])
    names = ["const"] + list(X.columns)
    beta = np.linalg.lstsq(Xd, y.values, rcond=None)[0]
    resid = y.values - Xd @ beta
    dof = max(n - k, 1)
    sigma2 = float(resid @ resid / dof)
    cov = sigma2 * np.linalg.pinv(Xd.T @ Xd)
    se = np.sqrt(np.abs(np.diag(cov)))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), df=dof)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid / ss_tot) if ss_tot > 0 else 0.0

    coefs = {}
    for name, b, s, tv, pv in zip(names, beta, se, t, p):
        coefs[name] = {"系数": round(float(b), 4), "标准误": round(float(s), 4),
                       "t": round(float(tv), 4), "p": round(float(pv), 4)}
    return {"系数表": coefs, "R²": round(r2, 4), "样本量": int(n), "自由度": int(dof)}


def did(df: pd.DataFrame, outcome: str, group_col: str, treated_value,
        time_col: str, post_value, confounders: list = None):
    """双重差分（DID）：需要面板数据（每个单元有 前/后 两个时点）。

    DID 系数 = 实验组前后变化 − 对照组前后变化。
    """
    d = df.copy()
    d["_treated"] = (d[group_col].astype(str) == str(treated_value)).astype(int)
    d["_post"] = (d[time_col].astype(str) == str(post_value)).astype(int)
    d["_treated_post"] = d["_treated"] * d["_post"]
    preds = ["_treated", "_post", "_treated_post"] + list(confounders or [])
    res = ols(d, outcome, preds)
    did_coef = res["系数表"].get("_treated_post", {})
    p = did_coef.get("p", float("nan"))
    note = "（p<0.05，统计显著）" if not np.isnan(p) and p < 0.05 else "（不显著）"
    return {
        "DID 估计值": did_coef.get("系数"),
        "p 值": did_coef.get("p"),
        "显著性": note,
        "完整回归": res,
        "提示": "DID 假设平行趋势；本工具为教学级实现，正式研究请使用专业因果推断库。",
    }
