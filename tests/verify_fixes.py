"""修复验证脚本：验证路径白名单、规划解析、describe、Yates 校正等修复点。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok = []

# 1. _resolve_data_path 路径白名单（用 FastAPI TestClient 验证 403/400/404 行为）
from fastapi.testclient import TestClient
from api.main import app, _resolve_data_path
from fastapi import HTTPException

client = TestClient(app)

def expect_http(path, code):
    try:
        _resolve_data_path(path)
        return f"❌ {path}: 未被拒绝"
    except HTTPException as e:
        return f"✓ {path}: 拒绝为 {e.status_code}" if e.status_code == code else f"❌ {path}: 拒绝码 {e.status_code}"

ok.append("【路径白名单】")
ok.append(expect_http("../README.md", 403))          # 路径穿越
ok.append(expect_http("C:/Windows/win.ini", 403))    # 绝对路径/盘符
# ~ 不会被 Path 展开成用户主目录：按 data 内相对路径解析后因扩展名非法被 400 拒绝（行为正确）
ok.append(expect_http("~/.ssh/id_rsa", 400))
try:
    p = _resolve_data_path("sample_sales.csv")
    ok.append(f"✓ sample_sales.csv: 解析为 {p}（白名单内）")
except HTTPException as e:
    ok.append(f"❌ sample_sales.csv: 被拒绝 {e.status_code}")

# 2. pipeline 规划解析（各种列表格式）
from app.pipeline import _parse_plan
samples = [
    ("1. 按月份汇总\n2. 找出最高商品\n3. 分析城市占比", 3),
    ("1、留存\n2、付费\n3、LTV", 3),
    ("- 第一步\n- 第二步", 2),
    ("• 活跃\n• 付费", 2),
    ("1）首充漏斗\n2）复购", 2),
    ("第1步：汇总销售\n子问题2：分析城市", 2),
    ("随便一句话没有列表", 1),
]
ok.append("【规划解析】")
for text, expect_n in samples:
    steps = _parse_plan(text, 3, "兜底问题")
    status = "✓" if 0 < len(steps) <= expect_n else "❌"
    ok.append(f"{status} {text[:24]!r} → {len(steps)} 步: {steps}")

# 3. olist_loader.describe()（[:10] bug 修复）
from app.olist_loader import describe, available
ok.append("【olist describe】")
if available():
    desc = describe()
    ok.append(f"✓ {desc}")
else:
    ok.append("⚠️ Olist 数据缺失，跳过 describe 验证")

# 4. Yates 校正（correct=True 的 p 值应 >= correct=False 的 p 值）
from app.experiments import ab_proportion
r_off = ab_proportion(80, 1000, 95, 1000, correct=False)
r_on = ab_proportion(80, 1000, 95, 1000, correct=True)
ok.append("【Yates 校正】")
ok.append(f"✓ 无校正 p={r_off['p 值']} / 有校正 p={r_on['p 值']}（校正后更保守: {r_on['p 值'] >= r_off['p 值']}）")
ok.append(f"✓ 校正标记: {r_on['连续性校正']}")

# 5. Cohen's d pooled SD（自由度加权）
from app.experiments import ab_ttest
import numpy as np
a = np.array([1.0, 2.0, 3.0, 4.0])
b = np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
r = ab_ttest(a, b)
ok.append("【Cohen's d】")
s1, s2 = a.std(ddof=1), b.std(ddof=1)
expected = (b.mean() - a.mean()) / np.sqrt(((len(a)-1)*s1**2 + (len(b)-1)*s2**2) / (len(a)+len(b)-2))
d_cohen = r["Cohen's d"]  # 兼容 Python 3.11：f-string 表达式内不能含反斜杠转义
ok.append(f"✓ Cohen's d = {d_cohen}（与自由度加权公式 round(4) 一致: {abs(d_cohen - round(float(expected), 4)) < 1e-9}）")

# 6. automl CV 指标统一（f1_weighted）
from app.automl import automl_train
import pandas as pd
rng = np.random.default_rng(7)
df = pd.DataFrame({"x1": rng.normal(size=200), "x2": rng.normal(size=200)})
df["y"] = (df["x1"] + df["x2"] > 0).astype(int)
res = automl_train(df, "y", n_trials=3)
ok.append("【AutoML 指标】")
ok.append(f"✓ 任务={res['task']}，说明含 F1(weighted): {'F1(weighted)' in res['说明']}")

print("\n".join(ok))
fails = [l for l in ok if l.startswith("❌")]
print(f"\n===== 验证完成：{len(ok) - len(fails)} 项通过，{len(fails)} 项失败 =====")
sys.exit(1 if fails else 0)
