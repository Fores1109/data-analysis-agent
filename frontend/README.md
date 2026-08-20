# 🖥️ 数据分析 Agent — 现代前端（Next.js 16 + shadcn/ui）

基于 [Next.js](https://nextjs.org/) App Router + [shadcn/ui](https://ui.shadcn.com/) + Tailwind CSS v4 的现代前端骨架，对接项目自带的 FastAPI（`api/main.py`），用于替代/并列现有 Streamlit 界面。

## 功能页面

| 路由 | 页面 | 对接 API |
|---|---|---|
| `/` | 仪表盘（概览 + 健康检查） | `GET /health` |
| `/analyze` | 💬 自然语言分析（聊天，**SSE 流式输出**） | `POST /api/analyze/stream`、`POST /api/analyze` |
| `/charts` | 📈 图表可视化（7 种交互图，plotly） | `POST /api/charts/generate` |
| `/sql` | 🗄️ SQL 助手（生成 / 优化） | `POST /api/sql/generate`、`POST /api/sql/optimize` |
| `/abtest` | 🧪 A/B 实验（t 检验 / 转化率 z 检验 / 模拟实验） | `POST /api/ab/test`、`/api/ab/test_values`、`/api/ab/proportion`、`/api/ab/simulate` |
| `/ml` | 🤖 机器学习（训练） | `POST /api/ml/train` |
| `/causal` | 🔗 因果推断（多元回归 OLS / 双重差分 DID） | `POST /api/causal/ols`、`/api/causal/did` |
| `/report` | 📑 报告生成（问答 + 图表 → Markdown / HTML） | `POST /api/report/generate` |
| `/data` | 📂 数据源（数据集浏览） | `GET /api/data/preview` |

> 说明：
> - **流式输出**：`/api/analyze/stream` 为 SSE 接口（LangGraph `astream` 真实逐 token），BFF 代理流式透传；聊天页支持中途停止，问答自动存入 localStorage 供报告页使用。
> - **报告数据流**：聊天页问答 → localStorage → 报告页汇总；图表页「加入报告」→ localStorage → 报告嵌入（HTML 版含图表）。
> - 更多算法页面（SHAP / 预测 / RFM / 游戏分析）可照 `/causal`、`/abtest` 的模板继续扩展。

## 快速开始

```bash
# 1. 先启动 FastAPI 后端（项目根目录）
cd .. && .venv\Scripts\activate && uvicorn api.main:app --host 0.0.0.0 --port 8000

# 2. 安装依赖并启动前端
npm install
cp .env.example .env        # 默认 API 地址 http://localhost:8000
npm run dev                 # http://localhost:3000
```

## 目录结构

```
app/                 # App Router 页面
  layout.tsx         # 根布局（字体 + 全局壳：侧边栏/顶栏）
  page.tsx           # 仪表盘
  analyze/ sql/ data/ ml/   # 功能页
components/
  layout/            # 侧边栏 / 顶栏 / 应用壳
  chat/              # 聊天消息列表与输入框
  ui/                # shadcn/ui 组件
lib/
  api.ts             # FastAPI 客户端（fetch 封装 + 错误处理）
  types.ts           # API 响应类型
```

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | FastAPI 基地址（浏览器端直接访问，需允许跨域；本地开发可省略） |

## 与 Streamlit 前端的关系

- Streamlit 版：`web/`（本地一键 `streamlit run web/app.py`，8501 端口）
- 本前端：`frontend/`（对接 FastAPI，3000 端口）
- 两者可并存；后续若以本前端为主，建议为 FastAPI 增加 CORS 中间件与鉴权后再部署。

## 开发备注（Next.js 16）

- Next.js 16 存在破坏性变更，写代码前先阅读 `node_modules/next/dist/docs/` 中的相关指南。
- 页面默认是 Server Component；需要交互（状态/事件）的组件顶部加 `"use client"`。
