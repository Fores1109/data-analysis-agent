"""冒烟测试：验证核心逻辑（不调用 LLM、不花 token）。

运行：python tests/test_smoke.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from app import charts
from app.data_source import load_file
from app.experiments import ab_proportion, ab_ttest, did, ols, simulate_ab
from app.ml_runner import auto_train


def main():
    ok = []

    # 1. 数据加载（自动编码识别）
    df = load_file("data/sample_sales.csv")
    assert df.shape[1] == 7, f"列数不对: {df.shape}"
    ok.append(f"数据加载: {df.shape}")

    # 2. 图表
    fig = charts.bar(df, "城市", "销售额")
    ok.append(f"图表生成: {type(fig).__name__}")

    # 3. A/B 检验
    res = ab_ttest([1, 2, 3, 4, 5], [3, 4, 5, 6, 7])
    assert "p 值" in res and "结论" in res
    ok.append(f"A/B t 检验: p={res['p 值']}")

    res2 = ab_proportion(80, 1000, 95, 1000)
    ok.append(f"A/B 转化率检验: p={res2['p 值']}")

    ctrl, trt = simulate_ab()
    ok.append(f"模拟实验数据: 每组 {len(ctrl)} 条")

    # 4. OLS / DID
    rng = np.random.default_rng(1)
    n = 200
    sim = pd.DataFrame({
        "y": rng.normal(0, 1, n) + 2 * rng.normal(0, 1, n),
        "x": rng.normal(0, 1, n),
        "group": ["A"] * 100 + ["B"] * 100,
        "time": ["pre"] * 50 + ["post"] * 50 + ["pre"] * 50 + ["post"] * 50,
    })
    sim.loc[(sim["group"] == "B") & (sim["time"] == "post"), "y"] += 3  # 注入效应
    r_ols = ols(sim, "y", ["x"])
    assert "系数表" in r_ols
    ok.append(f"OLS: R²={r_ols['R²']}")

    r_did = did(sim, "y", "group", "B", "time", "post")
    est = r_did["DID 估计值"]
    assert est is not None
    ok.append(f"DID 估计值: {est:.3f}（注入的真实效应为 3.0）")

    # 5. 机器学习
    ml = auto_train(df, "销售额")
    assert ml["最优模型"]
    ok.append(f"机器学习: 任务={ml['task']}，最优模型={ml['最优模型']}，样本={ml['样本数']}")

    print("✓ 冒烟测试全部通过：")
    for line in ok:
        print("  -", line)


if __name__ == "__main__":
    main()
