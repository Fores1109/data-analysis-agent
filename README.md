# 📊 数据分析 Agent — 算法 / 数据科学作品集项目

![CI](https://github.com/Fores1109/data-analysis-agent/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> **一句话定位**：基于 LangChain + LangGraph 的多功能数据分析平台，具备 **AutoML 自动调参、SHAP 可解释性、SARIMA 时序预测、因果推断、A/B 实验** 等算法能力；内置 **Olist 巴西电商真实数据集（9.9 万订单 / 11.2 万明细行）** 与 **游戏数据分析场景包（留存/关卡/付费/LTV/流失预警）**，Streamlit 网页界面 + FastAPI 服务，开箱即用。

---

## 🏆 项目亮点（简历直接抄）

| 亮点 | 说明 |
|---|---|
| **AutoML** | Optuna(TPE) 对随机森林/梯度提升/线性模型做超参搜索，输出调参过程曲线与模型对比（区别于"调几个默认模型"）；CV 优化目标与最终排序指标一致（分类 F1(weighted) / 回归 R²） |
| **模型可解释性** | SHAP TreeExplainer：特征贡献排序、单样本 waterfall、特征依赖图——回答"模型为什么这么预测" |
| **时序建模** | SARIMA(1,1,1)×(0,1,1,7) 周季节模型 + STL 分解 + IsolationForest 异常检测，带 90% 置信区间 |
| **因果推断** | numpy 实现的 OLS（控制混杂）+ 双重差分 DID，附统计显著性与平实解释 |
| **流失预警** | 特征工程（活跃/间隔/付费/关卡）+ 逻辑回归 & 随机森林（class_weight 处理类别不平衡），输出特征重要性与高危用户名单 |
| **多 Agent 编排** | LangGraph 状态机流水线 v2：规划 Agent → 分析 Agent（**失败自动重试，不中断**）→ 报告 Agent；**全流程审计日志**（每步状态/耗时），为人工审核节点预留扩展位 |
| **双垂直场景包** | ① Olist 巴西电商真实数据（9.9 万订单 / 11.2 万明细行）→ 销售预测/RFM ② 游戏厂商分析 → 留存矩阵/关卡漏斗/首充转化/Cohort LTV/流失预警（内置可复现模拟数据 + 支持上传） |
| **统计严谨性** | A/B 双比例 z 检验默认带 **Yates 连续性校正**；Cohen's d 用自由度加权的合并标准差；AutoML CV 目标与排序指标统一 |
| **安全加固** | API 层 **data_path 路径白名单**（防路径遍历/任意文件读取）；Agent 系统提示词强制**只读分析约束**；README 明确安全边界与隔离部署建议 |
| **工程化** | Streamlit 前端 + FastAPI 服务 + 12 个功能页面 + 5 套自动化测试（Olist 缺失时自动降级合成数据）+ **GitHub Actions CI** + 依赖锁定 + Docker 部署 + 统一视觉主题 |

## 🧭 功能页面

1. 💬 **自然语言问答**（经典单 Agent / LangGraph 多 Agent 流水线可切换，含审计日志）
2. 📈 图表可视化（7 种交互图 + 悬停解释器）
3. 🗄️ SQL 助手（表结构可视化、语句补全、生成/优化 SQL）
4. 🧪 **A/B 实验**（Welch t 检验 / 转化率 z 检验（Yates 校正）/ 模拟实验）
5. 🤖 **机器学习**（Optuna 自动调参 + 调参曲线 + 特征重要性）
6. 🔗 **因果推断**（OLS 控制混杂 / 双重差分 DID）
7. 📑 报告生成（汇总问答与图表导出 Markdown/HTML）
8. 🔍 **模型解释 SHAP**（重要性 / waterfall / 依赖图）
9. 📈 **销售预测**（SARIMA 预测 + STL 分解 + 异常检测，Olist 数据）
10. 👥 **RFM 用户分层**（Olist 客户价值分层与运营画像）
11. 🎮 **游戏数据分析**（同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU，内置模拟数据+支持上传真实日志）
12. 🎯 **游戏深度分析**（关卡通过漏斗、付费转化漏斗（首充）、Cohort LTV、流失预警——机器学习预测未来活跃并输出高危用户名单）

## 🏗️ 架构

```
用户
 │
 ▼
Streamlit 前端（12 个页面，统一主题，含安全须知提示）
 │
 ├── 数据源层    CSV / Excel / 数据库(SQLAlchemy) / API
 │               · Olist 电商数据集（9.9 万订单）· 游戏模拟/上传数据（留存·关卡·付费）
 ├── Agent 层    经典单 Agent (pandas agent) │ LangGraph 多 Agent 流水线 v2
 │               (规划→分析[失败自动重试]→报告，全流程审计日志，人工审核扩展位)
 ├── 算法层      AutoML(Optuna) · SHAP · SARIMA/STL · IsolationForest
 │               · 流失预测(逻辑回归/随机森林) · RFM · OLS/DID · A/B 检验(含Yates校正) · 留存/关卡/LTV
 ├── 服务层      FastAPI（路径白名单安全校验，Docker 一键起）
 ├── 质量层      GitHub Actions CI（5 套测试）+ 依赖锁定 requirements.lock.txt
 └── 存储        本地数据（大数据集不入库，脚本下载）+ 报告/图表导出
```

## 🛡️ 安全说明（请务必阅读）

本项目「自然语言问答」会让 LLM 生成 **Python 代码并在您的环境里执行**（LangChain 的 pandas agent 机制），因此安全边界需要明确：

- **Agent 只读约束**：系统提示词强制 Agent 仅做只读数据分析（禁止删改文件、访问网络、执行系统命令、读取敏感信息）。这是"软约束"，可被强提示词攻击绕过，不能替代隔离。
- **API 路径白名单**：`/api/analyze` 等接口的 `data_path` 只允许解析到项目 `data/` 目录内（`api/main.py` 的 `_resolve_data_path`），杜绝 `../` 路径穿越与任意文件读取。
- **使用建议**：
  1. 只对**您信任的数据文件与问题**使用问答功能；
  2. 不要在包含密钥/密码/令牌的文件上提问；
  3. 部署时建议运行在**隔离环境**（Docker 容器 / 沙箱 VM / 受限账户），见下方部署一节。
- **已知边界**：受限于 LangChain `create_pandas_dataframe_agent` 机制，当前无法在进程内对生成代码做沙箱隔离；如需硬隔离，请将服务部署在容器内并限制网络出口。

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

## ✅ 测试（5 套，全部通过，不消耗 LLM token）

```bash
python tests/test_smoke.py         # 数据/图表/A-B/OLS/DID/机器学习
python tests/test_algo.py          # AutoML/SHAP/时序/RFM（Olist 缺失时自动降级合成数据）
python tests/test_game.py          # 游戏留存/活跃/付费（模拟数据）
python tests/test_game_advanced.py # 关卡漏斗/首充转化/LTV/流失预警
python tests/test_web.py           # 12 个页面渲染
```

CI（GitHub Actions，Python 3.11/3.12）会自动运行以上全部测试：`.github/workflows/ci.yml`。

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
1. **AutoML**：为什么用 Optuna 而不是网格搜索？——超参空间随维度指数膨胀，TPE 用历史试验结果建模概率分布，采样更有希望的区域；我对比了 3 个模型族的调参曲线，说明"调参过程本身可观测"。为消除口径争议，CV 优化目标与最终排序指标统一（分类 F1(weighted) / 回归 R²）。
2. **SHAP**：TreeExplainer 利用树结构在 O(树深×特征数) 内精确计算 Shapley 值；单样本 waterfall 展示每个特征把预测从基准值推高/拉低了多少——解决"黑盒不可信"。
3. **LangGraph 流水线 v2**：把"一句话→回答"拆成规划/分析/报告三阶段状态机；规划解析兼容多种列表格式，单步失败自动重试不中断，每一步都有状态/耗时审计日志；`require_review=True` 可为接入人工审核节点预留扩展位。

**安全是个加分话题**：LLM 会执行生成的代码，所以我在 API 层做了 data_path 路径白名单（防路径穿越），Agent 提示词强制只读约束，并在 README 里明确"仅信任数据 + 隔离部署"的安全边界——面试官问"AI 应用的安全风险"时可以直接展开。

**垂直场景的故事（游戏）**：流失预警是亮点——未来 7 天不活跃的用户占 83~87%（严重类别不平衡），用 `class_weight='balanced'` 处理；特征重要性显示「活跃频率 / 最近活跃距今 / 平均活跃间隔」权重最高，说明"沉默唤醒"比"新用户补贴"更值得投入；输出高危用户 TopN 名单给运营做召回，形成 预警→召回→再评估 的闭环。同期群留存矩阵、首充转化漏斗、Cohort LTV 覆盖了游戏数据分析师的核心工作流。

**数据**：Olist 巴西电商 9.9 万订单（11.2 万明细行）——SARIMA 周季节预测、RFM 分层 9.8 万客户、异常检测 37 个异常点（全部真实结果）；游戏场景用可复现的模拟数据（幂律留存衰减 + 渠道差异 + 帕累托付费），也支持上传真实日志。

**可以准备的问题**：SARIMA 为什么用周季节？STL 鲁棒分解的原理？DID 的平行趋势假设？Shapley 值的公理化性质？qcut 打分 vs 自定义阈值？类别不平衡怎么处理？LTV 的口径（含未付费用户）？次留/7留/30留的行业基准？**AI 生成代码的安全风险与缓解方案？**

## 📜 原创性与参考声明

- 本项目**核心代码全部为本人独立实现**（Agent 封装、AutoML、SHAP 解释、时序建模、因果推断、游戏分析等模块），未复制任何开源项目代码
- **架构模式**（LangChain Agent + Streamlit 前端 + FastAPI 后端）参考了开源项目 [khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent) 的组织方式，在此致谢
- **第三方依赖**（LangChain / LangGraph / Optuna / SHAP / statsmodels / scikit-learn / Streamlit / FastAPI 等）按各自开源许可证（MIT / Apache-2.0 / BSD）使用，详见各库文档
- **数据**：Olist 巴西电商数据集来自 [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，遵循其许可（CC BY-NC-SA 4.0，仅限学习/非商业展示）；游戏场景数据为本项目内置的模拟数据生成器（幂律留存衰减模型）产出，可复现
- 本项目以 **MIT License** 开源（见 [LICENSE](LICENSE)），欢迎学习与二次开发

## 📚 参考与致谢

- 架构灵感：[khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent)
- 数据：[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)（下载脚本使用公开 GitHub 镜像）
- 依赖：LangChain / LangGraph / Optuna / SHAP / statsmodels / scikit-learn / Streamlit / FastAPI
