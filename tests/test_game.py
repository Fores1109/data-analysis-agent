"""游戏数据分析模块冒烟测试（不调 LLM）。运行：python tests/test_game.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.game_analytics import (activity_metrics, payment_metrics,
                                retention_by_channel, retention_curve,
                                retention_matrix, simulate_game_data)


def main():
    ok = []
    login, pay, users = simulate_game_data(n_users=800, days=60, seed=7)
    ok.append(f"模拟数据: 活跃记录 {len(login):,}、付费记录 {len(pay):,}、用户 {len(users):,}")

    ret = retention_matrix(login, users)
    ok.append(f"留存矩阵: {ret.shape[0]} 个注册周 × {ret.shape[1]} 个留存点")
    assert ret.shape[1] == 5, "应有 5 个留存周期"

    curve = retention_curve(login, users, max_day=7)
    ok.append(f"留存曲线: 第0天={curve.loc[0, '留存率%']}%（应≈100），第1天={curve.loc[1, '留存率%']}%")
    assert 90 < curve.loc[0, "留存率%"] <= 100

    by_ch = retention_by_channel(login, users, periods=(1, 7))
    ok.append(f"渠道留存: {len(by_ch)} 行（{by_ch['渠道'].nunique()} 个渠道）")

    act = activity_metrics(login)
    ok.append(f"活跃: DAU均值={act['DAU均值']}，粘性={act['DAU/MAU粘性%']}%")

    pay_m = payment_metrics(pay, users)
    ok.append(f"付费: 付费率={pay_m['付费率%']}%、ARPU=¥{pay_m['ARPU']}、ARPPU=¥{pay_m['ARPPU']}")

    print("✓ 游戏分析模块冒烟测试全部通过：")
    for line in ok:
        print("  -", line)


if __name__ == "__main__":
    main()
