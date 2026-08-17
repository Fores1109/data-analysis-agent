"""算法模块冒烟测试（不调 LLM）：AutoML / SHAP / 时序预测 / 异常检测 / RFM。

优先用 Olist 真实数据（data/olist/，可用 scripts/download_data.py 下载）；
数据缺失时自动改用合成数据做轻量验证，保证 CI / 新克隆仓库也能跑通。
运行：python tests/test_algo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from app.automl import automl_train
from app.explain import dependence, explain_sample, shap_values
from app.forecast import daily_series, decompose, detect_anomalies, forecast
from app.olist_loader import available as olist_available
from app.olist_loader import merged
from app.rfm import rfm_table


def _fallback_series() -> pd.Series:
    """数据缺失时用带周季节性的合成日序列覆盖时序 / 异常检测路径。"""
    idx = pd.date_range("2024-01-01", periods=90, freq="D")
    rng = np.random.default_rng(42)
    base = 100 + 20 * np.sin(np.arange(90) * 2 * np.pi / 7)  # 周季节性
    noise = rng.normal(0, 5, 90)
    noise[30] += 200  # 注入异常点
    return pd.Series(base + noise, index=idx, name="sales")


def _fallback_table() -> pd.DataFrame:
    """数据缺失时用合成分类数据覆盖 AutoML / SHAP 路径。"""
    rng1 = np.random.default_rng(1)
    rng2 = np.random.default_rng(2)
    small = pd.DataFrame({
        "x1": rng1.normal(size=400),
        "x2": rng2.normal(size=400),
    })
    small["_target"] = (small["x1"] + small["x2"] > 0).astype(int)
    return small


def main():
    ok = []
    if olist_available():
        m = merged()
        ok.append(f"Olist 合并数据: {m.shape}")

        g, summary = rfm_table(m, customer_id="customer_id",
                               date_col="order_purchase_timestamp", amount_col="price")
        ok.append(f"RFM: {len(g)} 个客户、{len(summary)} 个分层")

        s = daily_series(m, "order_purchase_timestamp", "price")
        small = m[["price", "freight_value", "order_status"]].head(400).copy()
        small["_target"] = (small["price"] > small["price"].median()).astype(int)
    else:
        print("⚠️ 未找到 Olist 数据（data/olist/），改用合成数据做轻量验证；"
              "运行 scripts/download_data.py 可下载真实数据。")
        s = _fallback_series()
        small = _fallback_table()

    # 时序：预测 + STL 分解 + 异常检测
    fc = forecast(s, 30)
    ok.append(f"预测: 模型={fc['模型']}，未来 {len(fc['预测'])} 天")
    dc = decompose(s)
    ok.append(f"STL 分解: {'/'.join(dc.keys())}")
    an = detect_anomalies(s, "isolation")
    ok.append(f"异常检测: {len(an['异常点'])} 个异常点")

    # AutoML（小样本加速测试）
    r = automl_train(small, "_target", n_trials=5)
    ok.append(f"AutoML: 任务={r['task']}，最优={r['最优模型']}，模型数={len(r['模型对比'])}")

    # SHAP
    sh = shap_values(small, "_target")
    ok.append(f"SHAP: {len(sh['特征重要性'])} 个特征")
    w = explain_sample(small, "_target", 0, shap_res=sh)
    ok.append(f"waterfall: 预测值={w['预测值']}")
    top_feat = list(sh["特征重要性"].keys())[0]
    d = dependence(small, "_target", top_feat, shap_res=sh)
    ok.append(f"依赖图: {len(d['x'])} 个点")

    print("✓ 算法模块冒烟测试全部通过：")
    for line in ok:
        print("  -", line)


if __name__ == "__main__":
    main()
