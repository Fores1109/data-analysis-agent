"""游戏深度分析模块冒烟测试（不调 LLM）。运行：python tests/test_game_advanced.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.game_churn import churn_prediction
from app.game_deep import (cohort_ltv, first_pay_funnel, level_funnel,
                           simulate_game_data_full)


def main():
    ok = []
    gd = simulate_game_data_full(n_users=800, days=60, seed=7)
    login, pay, users, levels = gd["login"], gd["pay"], gd["users"], gd["levels"]
    ok.append(f"完整模拟数据: 活跃 {len(login):,}、付费 {len(pay):,}、关卡 {len(levels):,}、用户 {len(users):,}")

    # 关卡漏斗
    lv = level_funnel(levels)
    ok.append(f"关卡漏斗: {len(lv)} 关，第1关通过率={lv.loc[0, '累计通过率%']}%")
    assert lv.loc[0, "累计通过率%"] == 100.0
    assert lv["到达人数"].is_monotonic_decreasing

    # 付费转化
    stages, dist = first_pay_funnel(login, pay, users)
    ok.append(f"付费漏斗: {' → '.join(str(s) for s in stages['人数'])}（应递减）")
    assert stages["人数"].is_monotonic_decreasing
    ok.append(f"首充时间分布: {len(dist)} 条，中位数 {int(dist['首充天数'].median())} 天")

    # Cohort LTV
    ltv = cohort_ltv(pay, users, week_periods=8)
    ok.append(f"Cohort LTV: {ltv.shape[0]} 周 × {ltv.shape[1]} 周，最大周 LTV={ltv.iloc[:, -1].max()} 元")
    assert ltv.shape[1] == 8

    # 流失预警
    churn = churn_prediction(login, users, pay, levels, horizon=7, top_k=10)
    ok.append(f"流失预警: 样本 {churn['样本数']}、流失率 {churn['流失率%']}%、最优 {churn['最优模型']}")
    ok.append(f"  模型对比: {churn['模型对比']}")
    ok.append(f"  高危用户: {len(churn['高危用户'])} 人，概率区间 {churn['高危用户']['流失概率'].min()}~{churn['高危用户']['流失概率'].max()}")
    assert len(churn["高危用户"]) == 10

    print("✓ 游戏深度分析冒烟测试全部通过：")
    for line in ok:
        print("  -", line)


if __name__ == "__main__":
    main()
