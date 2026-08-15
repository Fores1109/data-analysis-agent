"""算法模块冒烟测试（不调 LLM）：AutoML / SHAP / 时序预测 / 异常检测 / RFM。

用 Olist 真实数据验证，运行：python tests/test_algo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.automl import automl_train
from app.explain import dependence, explain_sample, shap_values
from app.forecast import daily_series, decompose, detect_anomalies, forecast
from app.olist_loader import merged
from app.rfm import rfm_table


def main():
    ok = []

    # 数据
    m = merged()
    ok.append(f"Olist 合并数据: {m.shape}")

    # RFM 分层
    g, summary = rfm_table(m, customer_id="customer_id",
                           date_col="order_purchase_timestamp", amount_col="price")
    ok.append(f"RFM: {len(g)} 个客户、{len(summary)} 个分层")

    # 时序
    s = daily_series(m, "order_purchase_timestamp", "price")
    ok.append(f"日销售序列: {len(s)} 天")

    fc = forecast(s, 30)
    ok.append(f"预测: 模型={fc['模型']}，未来 {len(fc['预测'])} 天")

    dc = decompose(s)
    ok.append(f"STL 分解: {'/'.join(dc.keys())}")

    an = detect_anomalies(s, "isolation")
    ok.append(f"异常检测: {len(an['异常点'])} 个异常点")

    # AutoML（小样本加速测试）
    small = m[["price", "freight_value", "order_status"]].head(400).copy()
    small["_target"] = (small["price"] > small["price"].median()).astype(int)
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
