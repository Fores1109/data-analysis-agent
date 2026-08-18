# 📊 作品集：数据分析 Agent 平台

> 求职方向：数据分析师 / 数据科学 / 算法工程师
> 项目仓库：`https://github.com/Fores1109/data-analysis-agent
> 技术栈：Python · LangChain · LangGraph · Optuna · SHAP · statsmodels · scikit-learn · Streamlit · FastAPI · Docker

---

## 项目简介

基于 LangGraph 的**自研 ReAct 数据分析 Agent**（非官方封装）平台，具备 **AutoML 自动调参、SHAP 可解释性、SARIMA 时序预测、因果推断、A/B 实验** 等算法能力；内置 **Olist 巴西电商真实数据集（9.9 万订单 / 11.2 万明细行）** 与 **游戏数据分析场景包**，开箱即用。

## 量化成果

| 指标 | 数值 |
|---|---|
| 电商订单分析 | **99,441 订单 / 112,650 明细行**（Olist 巴西电商真实数据） |
| RFM 客户分层 | 98,666 客户 → 8 类价值分层 + 运营画像 |
| 电商时间序列 | 730 天日销售序列，SARIMA 预测未来 30 天（90% 置信区间） |
| 电商异常检测 | IsolationForest 检出 37 个异常点 |
| 游戏留存分析 | 同期群留存矩阵（次日/3/7/14/30 日）+ 留存曲线（100%→23.75% 平滑衰减） |
| 游戏付费转化 | 注册→活跃→首充→复购 四段漏斗（800→710→191→23），首充中位数 4 天 |
| 游戏 Cohort LTV | 按注册周累计 LTV 矩阵（LTV = 累计收入÷注册用户） |
| 游戏流失预警 | **v2：窗口特征 + 3 模型（LR/RF/HistGB）+ 时间切分 + 最佳阈值，AUC 0.54 → 0.65**，输出高危用户 TopN |
| 功能页面 | 12 个（问答 / AutoML / SHAP / 预测 / RFM / 因果 / A-B / 游戏留存 / 游戏深度） |
| 自动化测试 | **7 套**（含沙箱安全测试），全部通过（不消耗 LLM token）；GitHub Actions CI 自动运行 |
| 工程化 | Docker 部署 + 依赖锁定（requirements.lock.txt）+ 大数据集不入库（下载脚本） |

---

## 简历项目描述

**数据分析 Agent 平台｜Python / LangGraph / Optuna / SHAP / Streamlit**

- **自研 ReAct Agent（非官方封装）**：用 **LangGraph 手写显式 Agent 循环**（agent 节点 → 工具节点 → 条件边，循环上限可审计）替代已废弃的 `create_pandas_dataframe_agent`；自定义工具集（数据探索工具 + 通用 python_repl）、**分层记忆**（工作记忆 + LLM 滚动摘要 + 结论文档 TF-IDF 向量检索，支持跨轮引用）、**硬沙箱代码执行**（AST 静态检查 → 受限执行环境 → 独立子进程 → 30s 超时熔断，13 个安全用例覆盖 import os/open/to_csv/eval/socket/死循环等攻击面）
- 实现**多 Agent 流水线 v2**（规划→逐项分析→报告生成，单步失败自动重试、每步状态/耗时审计日志、人工审核扩展位），支持 CSV/Excel/数据库/API 多数据源接入
- 实现 **AutoML**：基于 **Optuna(TPE)** 对随机森林/梯度提升/线性模型做超参搜索并输出调参过程曲线；**CV 优化目标与最终排序指标统一**（分类 F1(weighted) / 回归 R²）
- 实现模型可解释模块：基于 **SHAP TreeExplainer** 输出特征贡献排序、单样本 waterfall 解释与特征依赖图
- 构建时间序列分析模块：**SARIMA(1,1,1)×(0,1,1,7)** 周季节模型预测未来 30 天销售（含 90% 置信区间）、**STL** 鲁棒季节分解、**IsolationForest** 异常检测
- 实现**因果推断**（statsmodels OLS，**HC1 异方差稳健标准误 + 95% 置信区间**；双重差分 DID）与 **A/B 实验**（Welch t 检验 / 双比例 z 检验（Yates 连续性校正）/ 效应量，Cohen's d 用自由度加权合并标准差）
- 基于 **Olist 巴西电商真实数据集**（9.9 万订单、11.2 万明细行、9.8 万客户）完成全流程分析：RFM 客户价值分层（8 类画像+运营建议）、销售预测、异常检测（检出 37 个异常点）
- 构建**游戏厂商分析模块**：同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU、关卡通过漏斗、首充转化漏斗、Cohort LTV；并实现**流失预警 v2**——**窗口特征**（近 7/14 天活跃、活跃趋势、距上次付费天数、关卡推进速度）+ 逻辑回归/随机森林/**HistGB**（class_weight 处理 83~87% 流失率的类别不平衡）+ **时间切分**（按最近活跃日期排序，用过去预测未来，避免泄漏）+ **Youden's J 最佳阈值**，AUC 从 0.54 提升至 **0.65**，输出特征重要性与高危用户召回名单
- **安全与工程质量**：API 层 **data_path 路径白名单**（跨平台拒绝路径穿越/盘符/绝对路径）、Agent 执行**硬沙箱**（见上）、GitHub Actions CI（**7 套测试**，Python 3.11/3.12）、依赖锁定、大数据集移出仓库（一键下载脚本）、Docker 部署

## 精简版

**数据分析 Agent 平台**：**自研 ReAct Agent**（LangGraph 显式循环 + 自定义工具集 + **硬沙箱代码执行**：AST 静态检查/受限环境/独立进程/超时熔断），含 **Optuna AutoML、SHAP 可解释性、SARIMA 时序预测、因果推断（statsmodels DID）、RFM 客户分层** 等模块；在 Olist 电商真实数据集（9.9 万订单）上完成销售预测、异常检测与用户分层全流程，并实现**游戏场景**的留存/关卡/付费/LTV 分析与**流失预警 v2**（窗口特征 + 3 模型 + 时间切分 + 最佳阈值，AUC 0.54→0.65）；API 路径白名单安全加固、CI 自动化；Streamlit + FastAPI + Docker 工程化交付。

## 英文版

**Data Analysis Agent Platform | Python / LangGraph / Optuna / SHAP / Streamlit**

- Built a **custom ReAct agent** (not a wrapper) with LangGraph: an explicit agent→tools→conditional-edge loop, a custom toolset (data-exploration tools + a general `python_repl`), **layered memory** (working memory + LLM rolling-summary + conclusion-store TF-IDF vector retrieval for cross-turn reference), and a **hard code-execution sandbox** — AST static analysis (blocks os/subprocess/open/to_csv/eval/socket…), a restricted execution environment (whitelisted modules + sanitized builtins), an **isolated subprocess**, and a 30s timeout kill (13 security test cases)
- Implemented a **LangGraph multi-agent pipeline v2** (plan → analyze with auto-retry → report) with auditable per-step status/elapsed logs and a reserved human-review hook; multi-source data ingestion (CSV/Excel/SQL/API)
- Implemented **AutoML** with **Optuna (TPE)** across Random Forest / Gradient Boosting / Linear models with tuning-curve visualization (CV objective aligned with the final ranking metric: F1-weighted / R²)
- Built model interpretability with **SHAP TreeExplainer**: feature contribution ranking, per-sample waterfall explanations, and dependence plots
- Developed time-series analytics with **SARIMA(1,1,1)×(0,1,1,7)** weekly-seasonal 30-day forecasting (90% CIs), **STL** decomposition, and **IsolationForest** anomaly detection
- Implemented causal inference (**statsmodels OLS with HC1 robust SEs and 95% CIs**, difference-in-differences) and A/B testing (Welch's t-test, two-proportion z-test with **Yates continuity correction**, degrees-of-freedom-weighted pooled SD)
- Delivered end-to-end analysis on the **Olist Brazilian e-commerce dataset** (99K orders / 112K order items / 98K customers): RFM segmentation (8 segments), sales forecasting, anomaly detection (37 flagged outliers)
- Built a **game analytics suite** (retention, DAU/WAU/MAU, ARPU/ARPPU, funnels, cohort LTV) and **churn early-warning v2**: window features (recent 7/14-day activity, activity trend, days-since-last-payment, level-progression speed), 3 models (LR/RF/**HistGB**) with class-weight balancing, **temporal train/test split** to avoid leakage, and **Youden's-J optimal threshold** — AUC improved from 0.54 to 0.65, outputting a high-risk user list for re-engagement campaigns
- Security & engineering: **API path-whitelist** (cross-platform), **hard sandbox** for code execution, **GitHub Actions CI** (7 test suites on Python 3.11/3.12), dependency lockfile, large datasets kept out of Git with a one-command download script, FastAPI + Docker deployment

---

## 面试高频追问准备

| 追问 | 回答要点 |
|---|---|
| 为什么用 Optuna 而不是网格搜索？ | 超参空间随维度指数膨胀，网格搜索不可行；TPE 基于历史试验结果建模概率密度，采样更有希望的区域，样本效率更高 |
| SHAP 是怎么算的？ | Shapley 值满足效率/对称/虚拟/可加性四条公理；TreeExplainer 利用树结构在 O(树深×特征数) 内精确计算 |
| 为什么 SARIMA 用周季节？ | Olist 销售数据呈明显 7 天周期（周末波动），先用 STL 分解确认季节性再定季节阶数 |
| DID 的前提假设？ | 平行趋势假设：若无干预，实验组与对照组变化趋势一致；我用 statsmodels OLS + HC1 稳健标准误实现，正式研究可扩展面板/事件研究 |
| RFM 为什么用 qcut 打分？ | 等频分箱保证每档样本量均衡，避免阈值拍脑袋；缺点是极端值会被压缩，可换自定义阈值 |
| **ReAct 循环怎么防止死循环？** | ① 条件边只在"有 tool_calls 且 steps < max_iterations（默认 8）"时回工具节点，否则结束；② 工具执行有 30s 超时熔断；③ 每轮消息都在 state 里可审计 |
| **记忆管理怎么做？** | 三层：① 工作记忆保留最近 N 轮原文；② 超过阈值用 LLM 滚动压缩早期对话成摘要（旧摘要+溢出→新摘要，防止上下文膨胀）；③ 每轮 (问,答) 结论文档入库，字符级 n-gram TF-IDF 稀疏向量 + cosine 做本地语义检索（零 embedding API 依赖），每轮注入最相关结论——实测第 5 轮能跨轮引用第 1 轮的数字结论 |
| **滚动摘要 vs 直接截断？** | 截断会丢早期关键结论；滚动摘要在保留语义的同时压缩 token；代价是摘要可能丢失细节（如精确数字），所以长期记忆（逐轮结论原文）正好补上——摘要给"全局脉络"，检索给"精确细节" |
| **TF-IDF 检索 vs embedding 检索？** | TF-IDF：零依赖、确定性、可解释（字符 n-gram 对中文友好），但无语义泛化（同义词/改写召回弱）；embedding：语义更强但依赖外部 API/模型。项目选 TF-IDF 是为了零成本可复现，架构上检索接口已抽象，可无缝换 embedding |
| **工具协议怎么设计？** | 用 LLM 原生 function calling（bind_tools）：工具 = 类型注解 + docstring 描述，LLM 返回结构化 tool_calls；工具节点按 id 匹配结果回填 ToolMessage，保证多工具并行/串行都正确 |
| **AST 沙箱的绕过面？** | 诚实说明：静态检查挡常规攻击面（import/call/属性），但理论上可利用 pandas 内部漏洞或编码技巧；所以叠加受限 builtins + 独立子进程 + 超时，生产级再加容器隔离 |
| 多 Agent 比单 Agent 好在哪？ | 任务分解降低单次推理复杂度、中间产物可审计可干预、各节点可独立替换/测试；v2 还支持单步失败自动重试与审计日志 |
| **A/B 检验为什么用 Yates 校正？** | 双比例 z 检验用正态近似，小样本/边缘频数时近似偏差大；Yates 连续性校正把 |差异| 减去半个单位频数对应的比例差，更保守，大样本下影响可忽略 |
| **Cohen's d 的合并标准差怎么算？** | 用自由度加权合并：sqrt(((n1-1)s1²+(n2-1)s2²)/(n1+n2-2))，而不是两组 std 的简单平均 |
| **流失预警为什么 AUC 提升了？** | 三个改动：① 窗口特征（近 7/14 天活跃、活跃趋势、距上次付费天数）捕捉"活跃度衰减"信号；② 时间切分替代随机切分，避免信息泄漏；③ 新增 HistGB + Youden's J 最佳阈值。AUC 0.54 → 0.65 |
| **时间切分 vs 随机切分？** | 随机切分会把"未来"的数据混进训练集（泄漏），业务上不可用；时间切分按最近活跃日期排序，前段训练/后段验证，模拟真实部署"用过去预测未来" |
| **流失预警怎么处理类别不平衡？** | 未来 7 天不活跃的用户占 83~87%，直接训练会偏向多数类；用 class_weight='balanced'（LR/RF/HistGB）反向加权少数类，让召回名单真正命中高危用户 |
| **LTV 的口径是什么？** | 我用的口径是「累计收入 ÷ 该 cohort 注册用户数」（含未付费用户），这是评估拉新 ROI 的口径；若口径改为 ARPPU 口径则只看付费用户，两者面试时要讲清楚 |
| **留存怎么定义？** | 同期群（cohort）按注册周分群，第 N 日留存 = 注册满 N+1 天的用户中第 N 天仍活跃的比例；分母要排除注册不足 N 天的新 cohort，避免"虚高" |
| **LLM 会执行生成的代码，怎么保证安全？** | **硬沙箱四道防线**：① AST 静态检查（禁 os/subprocess/open/eval/写文件属性/非白名单 import）；② 受限执行环境（白名单模块 + 安全 builtins）；③ 独立子进程（崩溃不影响主进程）；④ 30s 超时熔断。再加 API 路径白名单与提示词只读约束；生产部署建议叠加容器级隔离 |
| **游戏行业基准知道吗？** | 次留 35% 及格 / 40%+ 良好、7 留 15-20%、30 留 5-10%、付费率 2-5%、DAU/MAU 粘性 20%+ 算健康 |

---

## 演示与文档

- **运行方式**：Windows 双击「启动数据分析Agent.bat」（自动装依赖），或 `streamlit run web/app.py`
- **数据获取**：`python scripts/download_data.py`（Olist 数据不入库，一键下载约 60MB）
- **完整 README**：含架构图、功能清单、安全说明、部署方式、5 分钟面试讲稿
- **测试**：`test_smoke.py` / `verify_fixes.py` / `test_sandbox.py` / `test_algo.py` / `test_game.py` / `test_game_advanced.py` / `test_web.py`（7 套，CI 自动运行）
- **演示路径建议**：进「12_游戏深度分析」→ 生成模拟数据 → 分别点关卡漏斗 / 付费转化 / Cohort LTV / 流失预警，全程 1 分钟出结果

> 📌 Demo 视频建议：录一段 1-2 分钟操作录屏（留存矩阵 + 流失预警高危名单是最好看的两个画面），放 YouTube/B 站后把链接贴到这里，面试官点开即看。
