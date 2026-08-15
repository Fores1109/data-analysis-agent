# 📊 作品集：数据分析 Agent 平台

> 求职方向：数据分析师 / 数据科学 / 算法工程师
> 项目仓库：`https://github.com/<你的用户名>/data-analysis-agent`（上传后替换）
> 技术栈：Python · LangChain · LangGraph · Optuna · SHAP · statsmodels · scikit-learn · Streamlit · FastAPI · Docker

---

## 项目一句话

基于 LangChain + LangGraph 的自然语言数据分析平台，具备 **AutoML 自动调参、SHAP 可解释性、SARIMA 时序预测、因果推断、A/B 实验** 等算法能力，内置 **Olist 巴西电商真实数据集（11 万订单）** 场景包，开箱即用。

## 量化成果（全部为实测数据，可现场演示）

| 指标 | 数值 |
|---|---|
| 分析订单量 | 112,650 单（Olist 巴西电商真实数据） |
| RFM 客户分层 | 98,666 客户 → 8 类价值分层 + 运营画像 |
| 时间序列 | 730 天日销售序列，SARIMA 预测未来 30 天（90% 置信区间） |
| 异常检测 | IsolationForest 检出 37 个异常点 |
| 功能页面 | 12 个（含 AutoML / SHAP / 预测 / RFM / 因果 / A/B / **游戏留存·关卡·付费·流失分析**） |
| 自动化测试 | 3 套，全部通过（不消耗 LLM token） |

---

## 版本一：简历项目描述（中文，推荐）

**数据分析 Agent 平台｜Python / LangChain / LangGraph / Optuna / SHAP / Streamlit**

- 开发基于 **LangChain + LangGraph** 的多功能数据分析平台：自然语言提问驱动 Agent 自动编写 pandas 代码完成分析，并实现**多 Agent 流水线**（规划→逐项分析→报告生成，中间产物可审计），支持 CSV/Excel/数据库/API 多数据源接入
- 实现 **AutoML**：基于 **Optuna(TPE)** 对随机森林/梯度提升/线性模型做超参搜索并输出调参过程曲线，自动完成特征编码、缺失值处理、交叉验证与多模型对比
- 实现模型可解释模块：基于 **SHAP TreeExplainer** 输出特征贡献排序、单样本 waterfall 解释与特征依赖图，回答"模型为什么这样预测"
- 构建时间序列分析模块：**SARIMA(1,1,1)×(0,1,1,7)** 周季节模型预测未来 30 天销售（含 90% 置信区间）、**STL** 鲁棒季节分解、**IsolationForest** 异常检测
- 实现**因果推断**（OLS 控制混杂 / 双重差分 DID）与 **A/B 实验**（Welch t 检验 / 双比例 z 检验 / 效应量），输出统计显著性与业务结论
- 基于 **Olist 巴西电商真实数据集**（11.3 万订单、9.8 万客户）完成全流程分析：RFM 客户价值分层（8 类画像+运营建议）、销售预测、异常检测（检出 37 个异常点）
- 工程化：**FastAPI** 服务化（Docker 部署）、Streamlit 统一主题前端（11 个页面）、3 套自动化测试（含页面渲染测试）、完整 GitHub 提交历史
- 垂直场景扩展：**游戏厂商分析模块**——同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU、**关卡通过漏斗、首充转化漏斗、Cohort LTV、流失预警**（机器学习预测未来活跃并输出高危用户名单；内置可复现的模拟数据生成器 + 支持上传真实日志）

## 版本二：精简版（简历空间紧张时）

**数据分析 Agent 平台**：基于 LangChain/LangGraph 的自然语言数据分析平台，含 **Optuna AutoML、SHAP 可解释性、SARIMA 时序预测、因果推断（DID）、RFM 客户分层** 等模块；在 Olist 电商真实数据集（11 万订单）上完成销售预测、异常检测与用户分层全流程；Streamlit + FastAPI + Docker 工程化交付。

## 版本三：英文版（外企 / GitHub）

**Data Analysis Agent Platform | Python / LangChain / LangGraph / Optuna / SHAP / Streamlit**

- Built an LLM-powered data analysis platform where natural-language questions drive a LangChain pandas agent to write and execute analysis code; implemented a **LangGraph multi-agent pipeline** (plan → analyze → report) with auditable intermediate outputs and multi-source data ingestion (CSV/Excel/SQL/API)
- Implemented **AutoML** with **Optuna (TPE)** hyperparameter search across Random Forest / Gradient Boosting / Linear models, including tuning-curve visualization, automatic feature encoding, missing-value imputation, and cross-validation
- Built model interpretability with **SHAP TreeExplainer**: feature contribution ranking, per-sample waterfall explanations, and dependence plots
- Developed time-series analytics with **SARIMA(1,1,1)×(0,1,1,7)** weekly-seasonal 30-day forecasting (90% CIs), **STL** decomposition, and **IsolationForest** anomaly detection
- Implemented causal inference (OLS with confounders, difference-in-differences) and A/B testing (Welch's t-test, two-proportion z-test, effect size)
- Delivered end-to-end analysis on the **Olist Brazilian e-commerce dataset** (112K orders, 98K customers): RFM customer segmentation (8 segments with action plans), sales forecasting, and anomaly detection (37 flagged outliers)
- Engineering: FastAPI service with Docker deployment, themed Streamlit frontend (10 pages), 3 automated test suites, clean Git history

---

## 面试高频追问准备

| 追问 | 回答要点 |
|---|---|
| 为什么用 Optuna 而不是网格搜索？ | 超参空间随维度指数膨胀，网格搜索不可行；TPE 基于历史试验结果建模概率密度，采样更有希望的区域，样本效率更高 |
| SHAP 是怎么算的？ | Shapley 值满足效率/对称/虚拟/可加性四条公理；TreeExplainer 利用树结构在 O(树深×特征数) 内精确计算 |
| 为什么 SARIMA 用周季节？ | Olist 销售数据呈明显 7 天周期（周末波动），先用 STL 分解确认季节性再定季节阶数 |
| DID 的前提假设？ | 平行趋势假设：若无干预，实验组与对照组变化趋势一致；本实现为教学级（numpy OLS），正式研究用 statsmodels/DoWhy |
| RFM 为什么用 qcut 打分？ | 等频分箱保证每档样本量均衡，避免阈值拍脑袋；缺点是极端值会被压缩，可换自定义阈值 |
| 多 Agent 比单 Agent 好在哪？ | 任务分解降低单次推理复杂度、中间产物可审计可干预、各节点可独立替换/测试 |

---

## 演示与文档

- **运行方式**：Windows 双击「启动数据分析Agent.bat」（自动装依赖），或 `streamlit run web/app.py`
- **完整 README**：含架构图、功能清单、部署方式、5 分钟面试讲稿
- **测试**：`python tests/test_smoke.py` / `test_algo.py` / `test_web.py`

> 📌 Demo 视频建议：录一段 1 分钟操作录屏（进 RFM 页面 → 点计算 → 展示分层结果），放 YouTube/B 站后把链接贴到这里，面试官点开即看。
