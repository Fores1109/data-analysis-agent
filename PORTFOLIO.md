# 📊 作品集：数据分析 Agent 平台

> 求职方向：数据分析师 / 数据科学 / 算法工程师
> 项目仓库：`https://github.com/<你的用户名>/data-analysis-agent`（上传后替换）
> 技术栈：Python · LangChain · LangGraph · Optuna · SHAP · statsmodels · scikit-learn · Streamlit · FastAPI · Docker

---

## 项目一句话

基于 LangChain + LangGraph 的自然语言数据分析平台，具备 **AutoML 自动调参、SHAP 可解释性、SARIMA 时序预测、因果推断、A/B 实验** 等算法能力；内置 **Olist 巴西电商真实数据集（9.9 万订单 / 11.2 万明细行）** 与 **游戏数据分析场景包**，开箱即用。

## 量化成果（全部为实测数据，可现场演示）

| 指标 | 数值 |
|---|---|
| 电商订单分析 | **99,441 订单 / 112,650 明细行**（Olist 巴西电商真实数据） |
| RFM 客户分层 | 98,666 客户 → 8 类价值分层 + 运营画像 |
| 电商时间序列 | 730 天日销售序列，SARIMA 预测未来 30 天（90% 置信区间） |
| 电商异常检测 | IsolationForest 检出 37 个异常点 |
| 游戏留存分析 | 同期群留存矩阵（次日/3/7/14/30 日）+ 留存曲线（100%→23.75% 平滑衰减） |
| 游戏付费转化 | 注册→活跃→首充→复购 四段漏斗（800→710→191→23），首充中位数 4 天 |
| 游戏 Cohort LTV | 按注册周累计 LTV 矩阵（LTV = 累计收入÷注册用户） |
| 游戏流失预警 | 逻辑回归/随机森林 AUC≈0.60，特征「活跃频率/最近活跃距今/活跃间隔」最权重，输出高危用户 TopN |
| 功能页面 | 12 个（问答 / AutoML / SHAP / 预测 / RFM / 因果 / A-B / 游戏留存 / 游戏深度） |
| 自动化测试 | 5 套，全部通过（不消耗 LLM token）；GitHub Actions CI 自动运行 |
| 工程化 | Docker 部署 + 依赖锁定（requirements.lock.txt）+ 大数据集不入库（下载脚本） |

---

## 版本一：简历项目描述（中文，推荐）

**数据分析 Agent 平台｜Python / LangChain / LangGraph / Optuna / SHAP / Streamlit**

- 开发基于 **LangChain + LangGraph** 的多功能数据分析平台：自然语言提问驱动 Agent 自动编写 pandas 代码完成分析，并实现**多 Agent 流水线 v2**（规划→逐项分析→报告生成，单步失败自动重试、每步状态/耗时审计日志、人工审核扩展位），支持 CSV/Excel/数据库/API 多数据源接入
- 实现 **AutoML**：基于 **Optuna(TPE)** 对随机森林/梯度提升/线性模型做超参搜索并输出调参过程曲线，自动完成特征编码、缺失值处理、交叉验证与多模型对比；**CV 优化目标与最终排序指标统一**（分类 F1(weighted) / 回归 R²）
- 实现模型可解释模块：基于 **SHAP TreeExplainer** 输出特征贡献排序、单样本 waterfall 解释与特征依赖图，回答"模型为什么这样预测"
- 构建时间序列分析模块：**SARIMA(1,1,1)×(0,1,1,7)** 周季节模型预测未来 30 天销售（含 90% 置信区间）、**STL** 鲁棒季节分解、**IsolationForest** 异常检测
- 实现**因果推断**（OLS 控制混杂 / 双重差分 DID）与 **A/B 实验**（Welch t 检验 / 双比例 z 检验（Yates 连续性校正）/ 效应量，Cohen's d 用自由度加权合并标准差），输出统计显著性与业务结论
- 基于 **Olist 巴西电商真实数据集**（9.9 万订单、11.2 万明细行、9.8 万客户）完成全流程分析：RFM 客户价值分层（8 类画像+运营建议）、销售预测、异常检测（检出 37 个异常点）
- 构建**游戏厂商分析模块**：同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU、关卡通过漏斗、首充转化漏斗、Cohort LTV；并实现**流失预警**——特征工程（活跃/间隔/付费/关卡）+ 逻辑回归与随机森林（class_weight 处理 83~87% 流失率的类别不平衡），输出特征重要性与高危用户召回名单
- **安全与工程质量**：API 层 **data_path 路径白名单**（防路径遍历/任意文件读取）、Agent 提示词强制**只读分析约束**、GitHub Actions CI（5 套测试）、依赖锁定、大数据集移出仓库（一键下载脚本）、Docker 部署

## 版本二：精简版（简历空间紧张时）

**数据分析 Agent 平台**：基于 LangChain/LangGraph 的自然语言数据分析平台，含 **Optuna AutoML、SHAP 可解释性、SARIMA 时序预测、因果推断（DID）、RFM 客户分层** 等模块；在 Olist 电商真实数据集（9.9 万订单）上完成销售预测、异常检测与用户分层全流程，并实现**游戏场景**的留存/关卡/付费/LTV 分析与**流失预警**（机器学习+类别不平衡处理）；多 Agent 流水线（失败重试+审计日志）、API 路径白名单安全加固、CI 自动化；Streamlit + FastAPI + Docker 工程化交付。

## 版本三：英文版（外企 / GitHub）

**Data Analysis Agent Platform | Python / LangChain / LangGraph / Optuna / SHAP / Streamlit**

- Built an LLM-powered data analysis platform where natural-language questions drive a LangChain pandas agent to write and execute analysis code; implemented a **LangGraph multi-agent pipeline v2** (plan → analyze → report) with per-step auto-retry, auditable status/elapsed logs, and a reserved human-review hook; multi-source data ingestion (CSV/Excel/SQL/API)
- Implemented **AutoML** with **Optuna (TPE)** hyperparameter search across Random Forest / Gradient Boosting / Linear models, including tuning-curve visualization, automatic feature encoding, missing-value imputation, and cross-validation (CV objective aligned with final ranking metric: F1-weighted for classification, R² for regression)
- Built model interpretability with **SHAP TreeExplainer**: feature contribution ranking, per-sample waterfall explanations, and dependence plots
- Developed time-series analytics with **SARIMA(1,1,1)×(0,1,1,7)** weekly-seasonal 30-day forecasting (90% CIs), **STL** decomposition, and **IsolationForest** anomaly detection
- Implemented causal inference (OLS with confounders, difference-in-differences) and A/B testing (Welch's t-test, two-proportion z-test with **Yates continuity correction**, effect size with degrees-of-freedom-weighted pooled SD)
- Delivered end-to-end analysis on the **Olist Brazilian e-commerce dataset** (99K orders / 112K order items / 98K customers): RFM customer segmentation (8 segments with action plans), sales forecasting, and anomaly detection (37 flagged outliers)
- Built a **game analytics suite**: cohort retention matrix, retention curves, DAU/WAU/MAU stickiness, ARPU/ARPPU, level-progression funnel, first-purchase funnel, and cohort LTV; implemented **churn early-warning** with feature engineering (activity/intervals/payment/level) and logistic regression & random forest with class-weight balancing (83–87% churn imbalance), outputting feature importance and a high-risk user list for re-engagement campaigns
- Security & engineering: **API path-whitelist** (blocks path traversal / arbitrary file reads), read-only agent constraints, **GitHub Actions CI** (5 test suites), dependency lockfile, large datasets kept out of Git with a one-command download script, FastAPI + Docker deployment

---

## 面试高频追问准备

| 追问 | 回答要点 |
|---|---|
| 为什么用 Optuna 而不是网格搜索？ | 超参空间随维度指数膨胀，网格搜索不可行；TPE 基于历史试验结果建模概率密度，采样更有希望的区域，样本效率更高 |
| SHAP 是怎么算的？ | Shapley 值满足效率/对称/虚拟/可加性四条公理；TreeExplainer 利用树结构在 O(树深×特征数) 内精确计算 |
| 为什么 SARIMA 用周季节？ | Olist 销售数据呈明显 7 天周期（周末波动），先用 STL 分解确认季节性再定季节阶数 |
| DID 的前提假设？ | 平行趋势假设：若无干预，实验组与对照组变化趋势一致；本实现为教学级（numpy OLS），正式研究用 statsmodels/DoWhy |
| RFM 为什么用 qcut 打分？ | 等频分箱保证每档样本量均衡，避免阈值拍脑袋；缺点是极端值会被压缩，可换自定义阈值 |
| 多 Agent 比单 Agent 好在哪？ | 任务分解降低单次推理复杂度、中间产物可审计可干预、各节点可独立替换/测试；v2 还支持单步失败自动重试与审计日志 |
| **A/B 检验为什么用 Yates 校正？** | 双比例 z 检验用正态近似，小样本/边缘频数时近似偏差大；Yates 连续性校正把 |差异| 减去半个单位频数对应的比例差，更保守，大样本下影响可忽略 |
| **Cohen's d 的合并标准差怎么算？** | 用自由度加权合并：sqrt(((n1-1)s1²+(n2-1)s2²)/(n1+n2-2))，而不是两组 std 的简单平均 |
| **流失预警怎么处理类别不平衡？** | 未来 7 天不活跃的用户占 83~87%，直接训练会偏向多数类；用 class_weight='balanced' 反向加权少数类，让召回名单真正命中高危用户 |
| **LTV 的口径是什么？** | 我用的口径是「累计收入 ÷ 该 cohort 注册用户数」（含未付费用户），这是评估拉新 ROI 的口径；若口径改为 ARPPU 口径则只看付费用户，两者面试时要讲清楚 |
| **留存怎么定义？** | 同期群（cohort）按注册周分群，第 N 日留存 = 注册满 N+1 天的用户中第 N 天仍活跃的比例；分母要排除注册不足 N 天的新 cohort，避免"虚高" |
| **LLM 会执行生成的代码，怎么保证安全？** | 三层：① Agent 提示词强制只读约束（禁删改文件/网络/系统命令）；② API 层 data_path 路径白名单（防路径穿越）；③ 部署建议隔离环境（容器/沙箱）+ 仅信任数据。同时诚实说明：提示词是软约束，硬隔离靠部署环境 |
| **游戏行业基准知道吗？** | 次留 35% 及格 / 40%+ 良好、7 留 15-20%、30 留 5-10%、付费率 2-5%、DAU/MAU 粘性 20%+ 算健康 |

---

## 演示与文档

- **运行方式**：Windows 双击「启动数据分析Agent.bat」（自动装依赖），或 `streamlit run web/app.py`
- **数据获取**：`python scripts/download_data.py`（Olist 数据不入库，一键下载约 60MB）
- **完整 README**：含架构图、功能清单、安全说明、部署方式、5 分钟面试讲稿
- **测试**：`python tests/test_smoke.py` / `test_algo.py` / `test_game.py` / `test_game_advanced.py` / `test_web.py`（CI 自动运行）
- **演示路径建议**：进「12_游戏深度分析」→ 生成模拟数据 → 分别点关卡漏斗 / 付费转化 / Cohort LTV / 流失预警，全程 1 分钟出结果

> 📌 Demo 视频建议：录一段 1-2 分钟操作录屏（留存矩阵 + 流失预警高危名单是最好看的两个画面），放 YouTube/B 站后把链接贴到这里，面试官点开即看。
