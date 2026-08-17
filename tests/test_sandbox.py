"""沙箱安全单元测试：验证 python_repl 的执行与拦截行为。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from app.agent import build_tools, run_code_sandboxed

df = pd.DataFrame({
    "城市": ["北京", "上海", "北京", "广州", "上海"] * 20,
    "销售额": [5988, 25415, 53940, 19800, 18905] * 20,
})

ok = []

# 1. 正常执行：聚合分析
r = run_code_sandboxed("_result = df.groupby('城市')['销售额'].sum()", df)
ok.append(("正常聚合执行", r.get("ok") is True and "北京" in r.get("text", "")))

# 2. 正常执行：head + 多步
r = run_code_sandboxed("x = df['销售额'].mean()\n_result = round(x, 2)", df)
ok.append(("多步计算", r.get("ok") is True and r.get("text", "").replace(" ", "") != ""))

# 3. 拦截：import os
r = run_code_sandboxed("import os\n_result = os.getcwd()", df)
ok.append(("拦截 import os", r.get("ok") is False and "安全拦截" in r.get("error", "")))

# 4. 拦截：open() 写文件
r = run_code_sandboxed("f = open('x.txt', 'w')\n_result = 1", df)
ok.append(("拦截 open()", r.get("ok") is False and "安全拦截" in r.get("error", "")))

# 5. 拦截：to_csv 写文件
r = run_code_sandboxed("_result = df.to_csv('x.csv')", df)
ok.append(("拦截 to_csv", r.get("ok") is False and "禁止访问属性" in r.get("error", "")))

# 6. 拦截：subprocess
r = run_code_sandboxed("import subprocess\n_result = subprocess.run(['whoami'])", df)
ok.append(("拦截 subprocess", r.get("ok") is False and "安全拦截" in r.get("error", "")))

# 7. 拦截：eval/exec
r = run_code_sandboxed("_result = eval('1+1')", df)
ok.append(("拦截 eval", r.get("ok") is False))

# 8. 拦截：socket 网络
r = run_code_sandboxed("import socket\n_result = 1", df)
ok.append(("拦截 socket", r.get("ok") is False))

# 9. 超时熔断：死循环
r = run_code_sandboxed("while True:\n    pass", df, timeout=3)
ok.append(("超时熔断", r.get("ok") is False and "超时" in r.get("error", "")))

# 10. 语法错误
r = run_code_sandboxed("_result = df[['销售额']", df)
ok.append(("语法错误处理", r.get("ok") is False))

# 11. 异常传递（如列不存在）
r = run_code_sandboxed("_result = df['不存在的列']", df)
ok.append(("运行时异常传递", r.get("ok") is False and "KeyError" in r.get("error", "")))

# 12. 工具注册与调用（探索工具）
tools = build_tools({"data": df})
by_name = {t.name: t for t in tools}
shape = by_name["df_shape"].invoke({"df_name": "data"})
ok.append(("df_shape 工具", "100 行" in str(shape)))
vc = by_name["df_value_counts"].invoke({"df_name": "data", "column": "城市"})
ok.append(("df_value_counts 工具", "北京" in str(vc) and "上海" in str(vc)))

print("===== 沙箱安全测试 =====")
fails = 0
for name, passed in ok:
    print(f"{'✓' if passed else '❌'} {name}")
    if not passed:
        fails += 1
print(f"\n结果：{len(ok) - fails}/{len(ok)} 通过")
sys.exit(1 if fails else 0)
