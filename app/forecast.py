"""时间序列：销售预测（SARIMA/ETS）、STL 分解、异常检测。

算法岗亮点：统计建模（SARIMA 季节模型）+ 异常检测（IsolationForest/IQR）。
"""
import numpy as np
import pandas as pd


def daily_series(df: pd.DataFrame, date_col: str, value_col: str, agg: str = "sum") -> pd.Series:
    """把明细数据聚合成按日时序，缺失日期补 0。"""
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    s = d.groupby(d[date_col].dt.normalize())[value_col].agg(agg).sort_index()
    if len(s) < 2:
        raise ValueError("数据太少，无法形成时序")
    s = s.asfreq("D").fillna(0.0)
    return s


def forecast(s: pd.Series, periods: int = 30):
    """预测未来 periods 天。

    优先 SARIMA(1,1,1)x(0,1,1,7)（周季节性）；数据过短或拟合失败时
    降级为 ETS 指数平滑。返回历史/预测/置信区间，供前端绘图。
    """
    s = s.astype(float)
    if len(s) < 15:
        raise ValueError(f"至少需要 15 天数据，当前 {len(s)} 天")

    # 1) SARIMA（带周季节性）
    if len(s) >= 21:
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            model = SARIMAX(s, order=(1, 1, 1), seasonal_order=(0, 1, 1, 7),
                            enforce_stationarity=False, enforce_invertibility=False)
            fit = model.fit(disp=False)
            fc = fit.get_forecast(periods)
            ci = fc.conf_int(alpha=0.1)
            return {
                "历史": s, "预测": fc.predicted_mean,
                "下限": ci.iloc[:, 0], "上限": ci.iloc[:, 1],
                "模型": "SARIMA(1,1,1)×(0,1,1,7) 周季节",
            }
        except Exception:
            pass

    # 2) ETS 指数平滑
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    seasonal = "add" if len(s) >= 2 * 7 else None
    model = ExponentialSmoothing(s, trend="add",
                                 seasonal=seasonal,
                                 seasonal_periods=7 if seasonal else None)
    fit = model.fit()
    fc = fit.forecast(periods)
    return {"历史": s, "预测": fc, "下限": None, "上限": None,
            "模型": "ETS(加法趋势" + ("+周季节)" if seasonal else ")")}


def decompose(s: pd.Series, period: int = 7):
    """STL 季节分解：趋势 / 季节 / 残差。"""
    from statsmodels.tsa.seasonal import STL
    if len(s) < 2 * period + 1:
        period = max(2, len(s) // 3)
    if len(s) < period * 2 + 1:
        raise ValueError(f"数据不足（{len(s)} 天），无法做季节分解")
    stl = STL(s.astype(float), period=period, robust=True).fit()
    return {"观测": s, "趋势": stl.trend, "季节": stl.seasonal, "残差": stl.resid}


def detect_anomalies(s: pd.Series, method: str = "isolation"):
    """异常检测。method: isolation（机器学习）/ iqr（统计）。"""
    if method == "isolation":
        from sklearn.ensemble import IsolationForest
        d = pd.DataFrame({"v": s.astype(float)})
        d["lag1"] = d["v"].shift(1)
        d["lag7"] = d["v"].shift(7)
        d["ma7"] = d["v"].rolling(7, min_periods=1).mean()
        d = d.dropna()
        if len(d) < 30:
            return _iqr_detect(s)
        clf = IsolationForest(contamination=0.05, random_state=42)
        pred = clf.fit_predict(d.values)
        outliers = d.index[pred == -1]
        return {"异常点": s.loc[outliers], "方法": "IsolationForest(滞后+滚动特征)", "全部": s}
    return _iqr_detect(s)


def _iqr_detect(s: pd.Series):
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = s[(s < lo) | (s > hi)]
    return {"异常点": outliers, "方法": "IQR(1.5×) 箱线图法则", "全部": s}
