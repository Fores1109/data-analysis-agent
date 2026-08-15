# 📊 数据分析 Agent（Data Analysis Agent）

基于 **LangChain** 的多功能数据分析助手，架构参考 [khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent)
（LangChain Agent + Streamlit 前端 + FastAPI 后端）。在自己的电脑上一键运行，也预留了 Docker 部署与 GitHub 发布方式。

## ✨ 功能清单

| 模块 | 说明 | 对应页面 |
|---|---|---|
| 💬 自然语言问答 | Agent 自动写 pandas 代码分析 CSV/Excel/数据库/API 数据 | 1_自然语言分析 |
| 📈 图表可视化 | 柱状/折线/散点/直方/箱线/相关性热力图/时间序列，**悬停解释器** | 2_图表可视化 |
| 🗄️ SQL 助手 | **表结构可视化**、语句**自动补全**、自然语言→SQL、EXPLAIN 执行计划、**优化建议**（Copilot 式） | 3_SQL助手 |
| 🧪 A/B 实验 | t 检验 / 转化率 z 检验 / 效应量 / **模拟实验运行** | 4_A_B实验 |
| 🤖 机器学习 | 自动判断分类/回归、**自动选模型**、训练测试、指标对比、特征重要性 | 5_机器学习 |
| 🔗 因果推断 | 多元回归（控制混杂）、双重差分 DID，逐变量**解释** | 6_因果推断 |
| 📑 报告生成 | 汇总问答历史+图表+数据概览，导出 Markdown/HTML | 7_报告生成 |
| 📥 数据源 | 上传文件 / 示例数据 / **数据库查询** / **API 接口** | 首页侧边栏 |

## 🚀 快速开始（本地）

### Windows
```powershell
.\scripts\run_local.ps1
```
脚本会自动创建虚拟环境、安装依赖；首次运行会生成 `.env`，填入 `DEEPSEEK_API_KEY` 后重跑即可。

### 手动方式
```bash
cd data-analysis-agent
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 填入 DEEPSEEK_API_KEY
streamlit run web/app.py    # 打开 http://localhost:8501
```

> LLM 支持 DeepSeek（默认，国内直连）/ OpenAI / Ollama 本地，切换见 `.env`。
> 没有 API 密钥也想体验？`.env` 里 `LLM_PROVIDER=ollama` + 本地装 Ollama 即可免费使用。

### 验证安装（不花 token）
```bash
python tests/test_smoke.py
```
应输出「✓ 冒烟测试全部通过」，验证数据加载、图表、A/B、OLS/DID、机器学习全部正常。

## 🗺️ 项目结构

```
data-analysis-agent/
├── app/                        # ★ 核心业务（前后端共用）
│   ├── agent.py                #   LangChain pandas Agent（二次开发主战场）
│   ├── llm.py                  #   DeepSeek/OpenAI/Ollama 配置
│   ├── data_source.py          #   CSV/Excel/数据库/API 接入
│   ├── charts.py               #   plotly 图表 + 悬停解释
│   ├── sql_assistant.py        #   表结构/SQL 生成/补全/优化
│   ├── ml_runner.py            #   自动选模型与训练评估
│   ├── experiments.py          #   A/B 检验 + OLS + DID
│   ├── report.py               #   报告生成
│   └── config.py               #   .env 配置
├── web/
│   ├── app.py                  # Streamlit 首页（数据源+概览+列说明）
│   └── pages/                  # 7 个功能页面
├── api/
│   ├── main.py                 # FastAPI 服务（部署预留）
│   └── requirements-api.txt
├── scripts/                    # 一键启动脚本（Windows/macOS）
├── data/                       # 示例数据 + 输出目录
├── tests/test_smoke.py         # 冒烟测试
├── Dockerfile / docker-compose.yml
└── requirements.txt
```

## 🚢 部署（预留）

```bash
cp .env.example .env    # 填好密钥
docker compose up -d    # API 服务 http://localhost:8000/docs
```
Streamlit 前端也可以单独跑：`streamlit run web/app.py`（如部署到服务器，用 `--server.address 0.0.0.0`）。

## ☁️ 推送到 GitHub

```bash
cd data-analysis-agent
git init && git add . && git commit -m "init: LangChain 数据分析 Agent"
git branch -M main
git remote add origin https://github.com/<你的用户名>/data-analysis-agent.git
git push -u origin main
```
> 推送前先在 GitHub 网页新建同名空仓库；若用 SSH：`git@github.com:<用户名>/data-analysis-agent.git`。

## 🔧 二次开发指南

- **改分析风格**：`app/agent.py` 的 `SYSTEM_PREFIX`
- **新增数据源**：`app/data_source.py`（如接 ClickHouse、MongoDB）
- **新增图表类型**：`app/charts.py` + `web/pages/2_图表可视化.py`
- **新增模型**：`app/ml_runner.py` 的模型池 `_CLF_ZOO` / `_REG_ZOO`
- **新增 API 端点**：`api/main.py`，复用 `app/` 里的函数即可
- **LLM 提示优化**：SQL 生成/优化提示词在 `app/sql_assistant.py`

## ⚠️ 注意

- Agent 会执行 LLM 生成的 Python 代码（pandas），请只分析可信数据
- 因果推断为教学级实现（numpy OLS/DID），正式研究请用专业库（statsmodels、DoWhy）
- 本仓库交付时已通过冒烟测试逻辑审查；首次运行请先执行 `python tests/test_smoke.py`

## 📚 参考

- [khang3004/DataAnalysis_Agent](https://github.com/khang3004/DataAnalysis_Agent)（本架构的灵感来源）
- [LangChain 官方 create_pandas_dataframe_agent](https://python.langchain.com/)
- [lenaar/financial-ai-agent](https://github.com/lenaar/financial-ai-agent)（LangGraph 多步流水线参考）
