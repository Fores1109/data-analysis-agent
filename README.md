# 📊 数据分析 Agent — 算法 / 数据科学作品集项目

![CI](https://github.com/Fores1109/data-analysis-agent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> **一句话定位**：基于 LangGraph 的**自研 ReAct 数据分析 Agent** 平台，具备 **AutoML 自动调参、SHAP 可解释性、SARIMA 时序预测、因果推断、A/B 实验** 等算法能力；内置 **Olist 巴西电商真实数据集（9.9 万订单 / 11.2 万明细行）** 与 **游戏数据分析场景包（留存/关卡/付费/LTV/流失预警）**，Streamlit 网页界面 + FastAPI 服务，开箱即用。

---

## 🏆 项目亮点（简历直接抄）

| 亮点 | 说明 |
|---|---|
| **自研 Agent（非套壳）** | 抛弃已废弃的 `create_pandas_dataframe_agent`，用 **LangGraph 手写显式 ReAct 循环**（agent 节点 → 工具节点 → 条件边）：自定义工具集（探索工具 + 通用执行工具）、**多轮对话记忆**、循环上限与全流程消息审计 |
| **硬沙箱（代码执行安全）** | python_repl 工具**四道防线**：AST 静态检查（禁 os/subprocess/open/eval/写文件属性）→ 受限执行环境（白名单模块 + 安全 builtins）→ **独立子进程**（崩溃不影响主进程）→ **超时熔断**（30s 强制终止） |
| **AutoML** | Optuna(TPE) 对随机森林/梯度提升/线性模型做超参搜索，输出调参过程曲线与模型对比；CV 优化目标与最终排序指标一致（分类 F1(weighted) / 回归 R²） |
| **模型可解释性** | SHAP TreeExplainer：特征贡献排序、单样本 waterfall、特征依赖图——回答"模型为什么这么预测" |
| **时序建模** | SARIMA(1,1,1)×(0,1,1,7) 周季节模型 + STL 分解 + IsolationForest 异常检测，带 90% 置信区间 |
| **因果推断（statsmodels）** | OLS（**HC1 异方差稳健标准误** + 95% 置信区间 + F 检验）+ 双重差分 DID，附统计显著性与平实解释 |
| **流失预警 v2** | **窗口特征**（近 7/14 天活跃、活跃趋势、距上次付费天数、关卡推进速度）+ 3 模型（LR/RF/**HistGB**）+ **时间切分**（用过去预测未来，避免泄漏）+ **Youden's J 最佳阈值**，AUC 从 0.54 → **0.65** |
| **多 Agent 流水线** | LangGraph 状态机流水线 v2：规划 Agent → 分析 Agent（失败自动重试）→ 报告 Agent，全流程审计日志，人工审核扩展位 |
| **双垂直场景包** | ① Olist 巴西电商真实数据（9.9 万订单 / 11.2 万明细行）→ 销售预测/RFM ② 游戏厂商分析 → 留存矩阵/关卡漏斗/首充转化/Cohort LTV/流失预警 |
| **统计严谨性** | A/B 双比例 z 检验默认 **Yates 连续性校正**；Cohen's d 自由度加权合并标准差；AutoML CV 指标统一 |
| **安全加固** | API 层 **data_path 路径白名单**（跨平台一致）；Agent 执行 **硬沙箱**（见上）；README 明确安全边界 |
| **工程化** | Streamlit + FastAPI + 12 页面 + **7 套自动化测试**（含沙箱安全测试）+ GitHub Actions CI（3.11/3.12）+ 依赖锁定 + Docker |

## 🧭 功能页面

1. 💬 **自然语言问答**（**自研 ReAct Agent** / LangGraph 多 Agent 流水线可切换，含审计日志）
2. 📈 图表可视化（7 种交互图 + 悬停解释器）
3. 🗄️ SQL 助手（表结构可视化、语句补全、生成/优化 SQL）
4. 🧪 **A/B 实验**（Welch t 检验 / 转化率 z 检验（Yates 校正）/ 模拟实验）
5. 🤖 **机器学习**（Optuna 自动调参 + 调参曲线 + 特征重要性）
6. 🔗 **因果推断**（OLS 稳健标准误 / 双重差分 DID，含置信区间）
7. 📑 报告生成（汇总问答与图表导出 Markdown/HTML）
8. 🔍 **模型解释 SHAP**（重要性 / waterfall / 依赖图）
9. 📈 **销售预测**（SARIMA 预测 + STL 分解 + 异常检测，Olist 数据）
10. 👥 **RFM 用户分层**（Olist 客户价值分层与运营画像）
11. 🎮 **游戏数据分析**（同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU）
12. 🎯 **游戏深度分析**（关卡漏斗、首充转化、Cohort LTV、**流失预警 v2**——窗口特征 + 3 模型 + 时间切分 + 最佳阈值）

## 🏗️ 架构

```
用户
 │
 ▼
Streamlit 前端（12 个页面，统一主题，含安全须知提示）
 │
 ├── 数据源层    CSV / Excel / 数据库(SQLAlchemy) / API
 │               · Olist 电商数据集（9.9 万订单）· 游戏模拟/上传数据
 ├── Agent 层    自研 ReAct Agent（LangGraph 显式循环：agent→tools→条件边）
 │               ├── 工具集：df_shape/df_columns/df_head/df_describe/df_value_counts
 │               │          + python_repl（沙箱执行）
 │               ├── 沙箱：AST 静态检查 → 受限执行环境 → 独立子进程 → 超时熔断
 │               ├── 记忆：多轮对话历史（max_history 截断）
 │               └── 多 Agent 流水线 v2（规划→分析[重试]→报告，审计日志）
 ├── 算法层      AutoML(Optuna) · SHAP · SARIMA/STL · IsolationForest
 │               · 流失预警 v2(LR/RF/HistGB+窗口特征+时间切分) · RFM
 │               · OLS/DID(statsmodels, HC1 稳健) · A/B 检验(Yates) · 留存/关卡/LTV
 ├── 服务层      FastAPI（路径白名单安全校验，Docker 一键起）
 ├── 质量层      GitHub Actions CI（7 套测试）+ 依赖锁定 requirements.lock.txt
 └── 存储        本地数据（大数据集不入库，脚本下载）+ 报告/图表导出
```

## 🛡️ 安全说明（请务必阅读）

本项目「自然语言问答」会让 LLM 生成 **Python 代码并在沙箱中执行**。安全设计（自研 Agent 的 python_repl 工具）是**硬约束**而非提示词软约束：

1. **AST 静态检查**：执行前逐节点扫描——禁止 `os/subprocess/socket/open/eval/exec/__import__` 等危险调用、非白名单 `import`、写文件属性（`to_csv/to_pickle/to_excel/read_csv` 等），违规直接拒绝（返回「[安全拦截] …」）；
2. **受限执行环境**：只暴露 `pandas/numpy/math/statistics/datetime/json/re/collections` 白名单模块 + 过滤后的安全 builtins；
3. **独立子进程**：代码在单独进程中运行（`subprocess` + pickle 传输），崩溃 / 死循环不影响主进程；
4. **超时熔断**：默认 30 秒强制终止（可调 `sandbox_timeout`）。

配套措施：
- **API 路径白名单**：`/api/analyze` 等接口的 `data_path` 只允许解析到项目 `data/` 目录内（`api/main.py`），跨平台统一拒绝 `../` 穿越、绝对路径、盘符路径（403/400/404 分级）；
- **提示词安全约束**：系统提示词仍要求 Agent 只做只读分析、拒绝危险请求（软约束，作为第一道心理防线）；
- **使用建议**：只对可信数据与问题使用问答功能；不要在含密钥/密码的文件上提问；部署建议容器/受限账户 + 限制网络出口。

已知边界：沙箱为"静态分析 + 受限环境 + 进程隔离"，面向 LLM 生成的常规 pandas 分析足够；如需对抗性安全（防御精心构造的逃逸载荷），建议叠加容器级隔离（如 gVisor / Firecracker），这是业界通用做法。

## 🚀 快速开始（Windows）

```powershell
# 1. 双击「启动数据分析Agent.bat」（自动装依赖 + 启动）
# 2. 首次需编辑 .env 填入 DEEPSEEK_API_KEY（https://platform.deepseek.com 免费注册）
# 3. 浏览器打开 http://localhost:8501
```

手动方式：

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # 填 DEEPSEEK_API_KEY
streamlit run web/app.py
```

> 需要完全复现开发环境时：`pip install -r requirements.lock.txt`（精确版本锁定）。

## 📦 数据获取（Olist 真实数据集）

Olist 巴西电商 CSV（约 60MB，`data/olist/`）**不纳入 Git 仓库**（已被 `.gitignore` 排除），新克隆后运行：

```bash
python scripts/download_data.py            # 下载全部 8 个 CSV（已存在则跳过）
python scripts/download_data.py --dry-run  # 只检查远程文件是否可下载
```

- 数据源：Kaggle 数据集 [olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 的公开 GitHub 镜像（免 Kaggle 账号）
- 未下载数据时，`tests/test_algo.py` 会自动改用合成数据做轻量验证，**不影响 CI 与其余功能**
- 游戏场景数据由内置模拟生成器产出（幂律留存衰减 + 渠道差异 + 帕累托付费），无需下载

## ✅ 测试（7 套，全部通过，不消耗 LLM token；CI 自动运行）

```bash
python tests/test_smoke.py         # 数据/图表/A-B/OLS(statsmodels)/DID/机器学习
python tests/verify_fixes.py       # API 路径白名单/规划解析/Yates 校正/Cohen's d
python tests/test_sandbox.py       # 沙箱安全：危险代码拦截/超时熔断/工具集（无需 LLM）
python tests/test_algo.py          # AutoML/SHAP/时序/RFM（Olist 缺失时自动降级合成数据）
python tests/test_game.py          # 游戏留存/活跃/付费（模拟数据）
python tests/test_game_advanced.py # 关卡漏斗/首充转化/LTV/流失预警 v2
python tests/test_web.py           # 12 个页面渲染
python tests/test_agent_e2e.py     # 自研 Agent 端到端（真实 LLM，需 .env 密钥，CI 不跑）
```

## 📦 部署

```bash
cp .env.example .env
docker compose up -d         # API: http://localhost:8000/docs
```

- API 的 `data_path` 参数只接受 `data/` 目录内的相对路径（如 `sample_sales.csv`、`olist/olist_orders_dataset.csv`），白名单校验见 `api/main.py`
- 生产部署建议：容器内运行 + 限制网络出口 + 仅挂载必要的 `data/` 子目录 + 前置鉴权（API 当前未内置认证，请勿直接暴露公网）

## 🎙️ 面试讲稿（5 分钟版）

**背景**：市面上数据分析工具要么是纯聊天、要么是固定报表，我做了个结合两者的平台——自然语言驱动 + 算法深度，并覆盖电商与游戏两个垂直场景。

**三个最值得讲的技术点**：
1. **自研 Agent（不是套壳）**：LangChain 官方的 `create_pandas_dataframe_agent` 已标记 experimental 且无法注入安全控制，所以我用 LangGraph 手写了显式 ReAct 循环——agent 节点（LLM 决策）→ 工具节点（执行）→ 条件边（继续/结束），自定义工具集、多轮记忆、循环上限可审计。面试官问"Agent 是怎么实现的"，我可以直接讲图结构、工具协议（tool calling）、状态管理。
2. **硬沙箱**：LLM 会生成代码，我的 python_repl 工具在**执行前做 AST 静态检查**（禁 os/subprocess/open/写文件属性），再放进**受限执行环境**（白名单模块 + 安全 builtins），最后**独立子进程 + 30s 超时**运行。这四道防线是代码级硬约束，不是提示词软约束——`tests/test_sandbox.py` 里 13 个用例覆盖 import os、open()、to_csv、eval、socket、死循环等攻击面。
3. **AutoML / 可解释性**：Optuna(TPE) 调参曲线 + SHAP TreeExplainer，CV 优化目标与排序指标统一（分类 F1(weighted)）。

**垂直场景的故事（游戏流失预警 v2）**：v1 的随机切分会信息泄漏，我改成**时间切分**（按最近活跃日期排序，用过去预测未来）；特征工程加了**近 7/14 天活跃天数、活跃趋势、距上次付费天数**等窗口特征捕捉"活跃度衰减"；模型从 2 个加到 3 个（新增 HistGB）；最后用 **Youden's J 最佳阈值**生成高危名单。这套组合把 AUC 从 0.54 提到 0.65，更重要的是整个流程（预警→召回→再评估闭环）是业务可用的。

**统计严谨性**：DID 用 statsmodels OLS + **HC1 异方差稳健标准误** + 95% 置信区间；A/B 双比例 z 检验默认 **Yates 连续性校正**；Cohen's d 用自由度加权合并标准差——每个都是可以展开讲的统计细节。

**数据**：Olist 巴西电商 9.9 万订单（11.2 万明细行）——SARIMA 周季节预测、RFM 分层 9.8 万客户、异常检测 37 个异常点（全部真实结果）。

**可以准备的问题**：ReAct 循环如何避免死循环？tool calling 协议怎么设计？AST 检查的绕过面有哪些？沙箱为什么要子进程？SARIMA 为什么用周季节？DID 的平行趋势假设？Shapley 值的公理化性质？类别不平衡怎么处理？时间切分 vs 随机切分？LTV 的口径？次留/7留/30留的行业基准？

## 📜 原创性与参考声明

- 本项目**核心代码全部为本人独立实现**（自研 Agent 循环与沙箱、AutoML、SHAP 解释、时序建模、因果推断、游戏分析等模块），未复制任何开源项目代码
- **架构模式**（LangChain/LangGraph + Streamlit 前端 + FastAPI 后端）参考了开源项目 [khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent) 的组织方式，在此致谢；Agent 层已从官方 experimental 封装重构为自研实现
- **第三方依赖**（LangChain / LangGraph / Optuna / SHAP / statsmodels / scikit-learn / Streamlit / FastAPI 等）按各自开源许可证（MIT / Apache-2.0 / BSD）使用，详见各库文档
- **数据**：Olist 巴西电商数据集来自 [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，遵循其许可（CC BY-NC-SA 4.0，仅限学习/非商业展示）；游戏场景数据为本项目内置的模拟数据生成器（幂律留存衰减模型）产出，可复现
- 本项目以 **MIT License** 开源（见 [LICENSE](LICENSE)），欢迎学习与二次开发

## 📚 参考与致谢

- 架构灵感：[khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent)
- 数据：[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)（下载脚本使用公开 GitHub 镜像）
- 依赖：LangChain / LangGraph / Optuna / SHAP / statsmodels / scikit-learn / Streamlit / FastAPI
