"""Streamlit 页面渲染冒烟测试（AppTest，无需浏览器）。

运行：python tests/test_web.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF = pd.read_csv(os.path.join(ROOT, "data/sample_sales.csv"))


def check(name, relpath, session=None):
    at = AppTest.from_file(os.path.join(ROOT, relpath), default_timeout=30)
    if session:
        for k, v in session.items():
            at.session_state[k] = v
    at.run()
    if at.exception:
        for e in at.exception:
            print(f"  ❌ {name}: {e}")
        return False
    print(f"  ✓ {name}")
    return True


def main():
    ok = True
    ok &= check("首页 数据概览", "web/app.py")
    ok &= check("页面1 自然语言分析", "web/pages/1_自然语言分析.py", {"df": DF})
    ok &= check("页面2 图表可视化", "web/pages/2_图表可视化.py", {"df": DF})
    ok &= check("页面3 SQL助手", "web/pages/3_SQL助手.py")
    ok &= check("页面4 A/B实验", "web/pages/4_A_B实验.py", {"df": DF})
    ok &= check("页面5 机器学习", "web/pages/5_机器学习.py", {"df": DF})
    ok &= check("页面6 因果推断", "web/pages/6_因果推断.py", {"df": DF})
    ok &= check("页面7 报告生成", "web/pages/7_报告生成.py", {"df": DF})
    ok &= check("页面8 模型解释", "web/pages/8_模型解释.py", {"df": DF})
    ok &= check("页面9 销售预测", "web/pages/9_销售预测.py")
    ok &= check("页面10 RFM分层", "web/pages/10_RFM分层.py")
    ok &= check("页面11 游戏数据分析", "web/pages/11_游戏数据分析.py")
    ok &= check("页面12 游戏深度分析", "web/pages/12_游戏深度分析.py")
    print("✓ Streamlit 页面全部渲染正常" if ok else "✗ 存在页面异常")


if __name__ == "__main__":
    main()
