# 📊 数据分析 Agent — 算法 / 数据科学作品集项目

> **一句话定位**：基于 LangChain + LangGraph 的多功能数据分析平台，具备 **AutoML 自动调参、SHAP 可解释性、SARIMA 时序预测、因果推断、A/B 实验** 等算法能力，内置 **Olist 巴西电商真实数据集（11 万订单）** 场景包，Streamlit 网页界面 + FastAPI 服务，开箱即用。

---

## 🏆 项目亮点（简历直接抄）

| 亮点 | 说明 |
|---|---|
| **AutoML** | Optuna(TPE) 对随机森林/梯度提升/线性模型做超参搜索，输出调参过程曲线与模型对比（区别于"调几个默认模型"） |
| **模型可解释性** | SHAP TreeExplainer：特征贡献排序、单样本 waterfall、特征依赖图——回答"模型为什么这么预测" |
| **时序建模** | SARIMA(1,1,1)×(0,1,1,7) 周季节模型 + STL 分解 + IsolationForest 异常检测，带 90% 置信区间 |
| **因果推断** | numpy 实现的 OLS（控制混杂）+ 双重差分 DID，附统计显著性与平实解释 |
| **多 Agent 编排** | LangGraph 状态机流水线：规划 Agent → 分析 Agent → 报告 Agent，中间产物可观测 |
| **垂直场景数据包** | 内置 Olist 巴西电商公开数据集（10 万订单、2016-2018），RFM 客户分层直接出结果 |
| **工程化** | Streamlit 前端 + FastAPI 服务 + 10 个功能页面 + 3 套自动化测试 + Docker 部署 + 统一视觉主题 |

## 🧭 功能页面

1. 💬 **自然语言问答**（经典单 Agent / LangGraph 多 Agent 流水线可切换）
2. 📈 图表可视化（7 种交互图 + 悬停解释器）
3. 🗄️ SQL 助手（表结构可视化、语句补全、生成/优化 SQL）
4. 🧪 **A/B 实验**（Welch t 检验 / 转化率 z 检验 / 模拟实验）
5. 🤖 **机器学习**（Optuna 自动调参 + 调参曲线 + 特征重要性）
6. 🔗 **因果推断**（OLS 控制混杂 / 双重差分 DID）
7. 📑 报告生成（汇总问答与图表导出 Markdown/HTML）
8. 🔍 **模型解释 SHAP**（重要性 / waterfall / 依赖图）
9. 📈 **销售预测**（SARIMA 预测 + STL 分解 + 异常检测，Olist 数据）
10. 👥 **RFM 用户分层**（Olist 客户价值分层与运营画像）
11. 🎮 **游戏数据分析**（同期群留存矩阵、留存曲线、DAU/WAU/MAU 粘性、付费率/ARPU/ARPPU，内置模拟数据+支持上传真实日志）

## 🏗️ 架构

```
用户
 │
 ▼
Streamlit 前端（10 个页面，统一主题）
 │
 ├── 数据源层    CSV / Excel / 数据库(SQLAlchemy) / API / Olist 内置数据集
 ├── Agent 层    经典单 Agent (pandas agent) │ LangGraph 多 Agent 流水线(规划→分析→报告)
 ├── 算法层      AutoML(Optuna) · SHAP · SARIMA/STL · IsolationForest
 │               · RFM · OLS/DID · A/B 检验
 ├── 服务层      FastAPI（部署预留，Docker 一键起）
 └── 存储        本地数据 + 报告/图表导出
```

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

## ✅ 测试（全部通过，不消耗 LLM token）

```bash
python tests/test_smoke.py   # 数据/图表/A-B/OLS/DID/机器学习
python tests/test_algo.py    # AutoML/SHAP/时序/RFM（Olist 真实数据）
python tests/test_web.py     # 10 个页面渲染
```

## 📦 部署

```bash
cp .env.example .env
docker compose up -d         # API: http://localhost:8000/docs
```

## 🎙️ 面试讲稿（5 分钟版）

**背景**：市面上数据分析工具要么是纯聊天、要么是固定报表，我做了个结合两者的平台——自然语言驱动 + 算法深度。

**三个最值得讲的技术点**：
1. **AutoML**：为什么用 Optuna 而不是网格搜索？——超参空间随维度指数膨胀，TPE 用历史试验结果建模概率分布，采样更有希望的区域；我对比了 3 个模型族的调参曲线，说明"调参过程本身可观测"。
2. **SHAP**：TreeExplainer 利用树结构在 O(树深×特征数) 内精确计算 Shapley 值；单样本 waterfall 展示每个特征把预测从基准值推高/拉低了多少——解决"黑盒不可信"。
3. **LangGraph 流水线**：把"一句话→回答"拆成规划/分析/报告三阶段状态机，中间产物（计划、每步结果）可审计，为接入人工审核节点留了扩展位。

**数据**：Olist 巴西电商 11 万订单——SARIMA 周季节预测、RFM 分层 9.8 万客户、异常检测 37 个异常点（全部真实结果）。

**可以准备的问题**：SARIMA 为什么用周季节？STL 鲁棒分解的原理？DID 的平行趋势假设？Shapley 值的公理化性质？qcut 打分 vs 自定义阈值？

## 📚 参考与致谢

- 架构灵感：[khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent)
- 数据：[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- 依赖：LangChain / LangGraph / Optuna / SHAP / statsmodels / scikit-learn / Streamlit / FastAPI
