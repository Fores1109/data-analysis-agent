"""FastAPI 服务（部署预留）：把核心能力暴露为 HTTP API。

启动：uvicorn api.main:app --host 0.0.0.0 --port 8000
文档：http://localhost:8000/docs

安全说明：
  - data_path 参数只允许访问项目 data 目录内的文件（路径白名单），
    防止路径遍历（../ 逃逸、绝对路径、~ 展开、盘符）与任意文件读取；
  - /api/analyze 会执行 LLM 生成的 pandas 代码（只读约束见 app/agent.py），
    请仅对可信数据调用，并建议将服务部署在隔离环境（Docker 容器内）。
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.io as pio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app import charts, report
from app.agent import ask, ask_stream
from app.data_source import load_file
from app.experiments import ab_proportion, ab_ttest, did, ols, simulate_ab
from app.ml_runner import auto_train
from app.sql_assistant import generate_sql, get_schema, optimize_sql

app = FastAPI(title="数据分析 Agent API", version="0.3.0")

# API 允许访问的数据根目录（白名单；默认项目 data 目录，可用环境变量 DATA_ROOT 覆盖）
DATA_ROOT = Path(os.getenv("DATA_ROOT", str(Path(__file__).resolve().parent.parent / "data"))).resolve()
ALLOWED_SUFFIXES = (".csv", ".xlsx", ".xls", ".json")
# Windows 盘符路径（C:\ 或 C:/）：在 Linux 上不会被识别为绝对路径，需显式拒绝
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def _resolve_data_path(data_path: str) -> Path:
    """解析并校验用户传入的 data_path：必须位于 DATA_ROOT 白名单内。

    规则：
      - 相对路径（如 olist/orders.csv）按 data 目录解析；
      - 绝对路径 / ../ 逃逸 / ~ 展开 / Windows 盘符路径 一律拒绝（403，跨平台一致）；
      - 只允许 .csv/.xlsx/.xls/.json 后缀，且文件必须存在。
    """
    raw = (data_path or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="data_path 不能为空")
    # 显式拒绝盘符路径：Windows 上本就是绝对路径，Linux 上若当相对路径解析会绕过预期
    if _WINDOWS_DRIVE_RE.match(raw):
        raise HTTPException(status_code=403, detail="data_path 越权：不允许盘符/绝对路径")
    p = Path(raw)
    if not p.is_absolute():
        p = (DATA_ROOT / p).resolve()
    try:
        p.relative_to(DATA_ROOT)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="data_path 越权：仅允许访问 data 目录内的文件（相对路径，如 olist/olist_orders_dataset.csv）",
        )
    if p.suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{p.suffix or '无扩展名'}")
    if not p.is_file():
        raise HTTPException(status_code=404, detail=f"文件不存在：{p}")
    return p


class AnalyzeReq(BaseModel):
    data_path: str
    question: str


class SQLReq(BaseModel):
    question: str


class ProportionReq(BaseModel):
    """双比例 z 检验：两组成功数/总数。"""

    control_success: int
    control_n: int
    treat_success: int
    treat_n: int


class TestValuesReq(BaseModel):
    """直接粘贴两组数值做 Welch t 检验。"""

    control: list[float]
    treatment: list[float]


class SimulateReq(BaseModel):
    """模拟 A/B 实验：生成两组正态数据并检验。"""

    n_per_group: int = 500
    effect: float = 0.5
    seed: int = 42


class OlsReq(BaseModel):
    """多元回归（因果推断）：控制已观测混杂。"""

    data_path: str
    outcome: str
    predictors: list[str]
    robust: str = "HC1"


class DidReq(BaseModel):
    """双重差分 DID：面板数据（实验/对照 × 前/后）。"""

    data_path: str
    outcome: str
    group_col: str
    treated_value: str
    time_col: str
    post_value: str
    confounders: list[str] = []
    robust: str = "HC1"


class ChartReq(BaseModel):
    """图表生成：chart_type 取值 bar|line|scatter|histogram|box|heatmap|time_series。"""

    data_path: str
    chart_type: str
    x: str = ""
    y: str = ""
    color: str = ""
    bins: int = 30


class ReportReq(BaseModel):
    """报告生成：汇总问答记录、图表与数据概览为 Markdown / HTML。"""

    title: str = "数据分析报告"
    data_name: str = ""
    data_path: str = ""
    qa_pairs: list[dict] = []
    charts: list[dict] = []
    save: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(req: AnalyzeReq):
    """自然语言问答分析：对 data 目录内的 CSV 数据文件提问。"""
    try:
        path = _resolve_data_path(req.data_path)
        df = load_file(path)
        return {"answer": ask(df, req.question)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/stream")
async def analyze_stream(req: AnalyzeReq):
    """自然语言问答分析（SSE 流式）：逐 token 返回最终回答。"""
    try:
        path = _resolve_data_path(req.data_path)
        df = load_file(path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    async def gen():
        try:
            async for token in ask_stream(df, req.question):
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:  # noqa: BLE001 - 流中异常转为 SSE error 事件
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/ml/train")
def ml_train(data_path: str, target: str):
    """机器学习：自动选模型训练评估（data_path 为 data 目录内相对路径）。"""
    try:
        path = _resolve_data_path(data_path)
        return auto_train(load_file(path), target)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ab/test")
def ab_test(data_path: str, control_col: str, treatment_col: str):
    """A/B 检验：两组连续指标 t 检验（data_path 为 data 目录内相对路径）。"""
    try:
        path = _resolve_data_path(data_path)
        df = load_file(path)
        return ab_ttest(df[control_col], df[treatment_col])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ab/test_values")
def ab_test_values(req: TestValuesReq):
    """A/B 检验：直接传入两组数值（手动粘贴 / 模拟数据）。"""
    try:
        return ab_ttest(req.control, req.treatment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ab/proportion")
def ab_proportion_api(req: ProportionReq):
    """A/B 检验：两组转化率双比例 z 检验（默认 Yates 连续性校正）。"""
    try:
        if req.control_success > req.control_n or req.treat_success > req.treat_n:
            raise ValueError("成功数不能大于总人数")
        return ab_proportion(req.control_success, req.control_n, req.treat_success, req.treat_n)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ab/simulate")
def ab_simulate(req: SimulateReq):
    """A/B 模拟实验：生成两组正态数据并立即检验。"""
    try:
        control, treatment = simulate_ab(
            n_per_group=max(10, min(req.n_per_group, 20000)),
            effect=req.effect,
            seed=req.seed,
        )
        return {
            "n": int(len(control)),
            "control_mean": round(float(control.mean()), 4),
            "treatment_mean": round(float(treatment.mean()), 4),
            "control": [round(float(x), 4) for x in control],
            "treatment": [round(float(x), 4) for x in treatment],
            "test": ab_ttest(control, treatment),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/preview")
def data_preview(data_path: str):
    """读取 data 目录内数据集的列信息与前 50 行预览（供前端表单使用）。

    head 用 df.to_json 序列化：NaN → null、时间戳 → ISO 字符串（避免 json.dumps 报错）。
    """
    try:
        path = _resolve_data_path(data_path)
        df = load_file(path)
        return {
            "shape": [int(df.shape[0]), int(df.shape[1])],
            "columns": list(df.columns),
            "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
            "head": json.loads(
                df.head(50).to_json(orient="records", date_format="iso", force_ascii=False)
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/causal/ols")
def causal_ols(req: OlsReq):
    """因果推断-多元回归：控制已观测混杂（statsmodels OLS，默认 HC1 稳健标准误）。"""
    try:
        path = _resolve_data_path(req.data_path)
        df = load_file(path)
        return ols(df, req.outcome, req.predictors, robust=req.robust)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/causal/did")
def causal_did(req: DidReq):
    """因果推断-双重差分 DID：面板数据（实验/对照 × 前/后 两个时点）。"""
    try:
        path = _resolve_data_path(req.data_path)
        df = load_file(path)
        return did(
            df,
            req.outcome,
            req.group_col,
            req.treated_value,
            req.time_col,
            req.post_value,
            req.confounders or None,
            robust=req.robust,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/charts/generate")
def charts_generate(req: ChartReq):
    """图表生成：返回 plotly figure JSON（data/layout/config），前端用 plotly.js 渲染。"""
    try:
        path = _resolve_data_path(req.data_path)
        df = load_file(path)
        t = req.chart_type
        if t == "bar":
            fig = charts.bar(df, req.x, req.y or None)
        elif t == "line":
            fig = charts.line(df, req.x, req.y)
        elif t == "scatter":
            fig = charts.scatter(df, req.x, req.y, color=req.color or None)
        elif t == "histogram":
            fig = charts.histogram(df, req.x, bins=max(2, min(req.bins, 200)))
        elif t == "box":
            fig = charts.box(df, req.y or req.x, x=req.x)
        elif t == "heatmap":
            fig = charts.heatmap_corr(df)
        elif t == "time_series":
            fig = charts.time_series(df, req.x, req.y)
        else:
            raise ValueError(f"不支持的图表类型：{t}")
        return json.loads(fig.to_json())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/report/generate")
def report_generate(req: ReportReq):
    """报告生成：问答记录 + 图表 + 数据概览 → Markdown / HTML。"""
    try:
        overview = ""
        if req.data_path:
            path = _resolve_data_path(req.data_path)
            df = load_file(path)
            overview = f"共 {df.shape[0]} 行 × {df.shape[1]} 列。"
            num = df.select_dtypes(include="number")
            if num.shape[1]:
                overview += "\n\n数值列统计：\n\n" + num.describe().T.to_string()

        qa = [(p.get("question", ""), p.get("answer", "")) for p in req.qa_pairs]
        md_text = report.build_md(req.title, req.data_name, qa, overview=overview)
        html_body = report.md_to_html(md_text)

        charts_html = ""
        if req.charts:
            parts = []
            for fig_json in req.charts:
                try:
                    fig = pio.from_json(json.dumps(fig_json))
                    parts.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
                except Exception:  # noqa: BLE001 - 单个图失败不影响整体报告
                    continue
            charts_html = report.embed_charts_html(parts)

        full_html = (
            "<html><head><meta charset='utf-8'>"
            f"<title>{req.title}</title></head>"
            "<body style='font-family:sans-serif;max-width:960px;margin:0 auto;padding:24px'>"
            f"{html_body}{charts_html}</body></html>"
        )
        saved_path = None
        if req.save:
            saved_path = str(report.save_report(md_text))
        return {"markdown": md_text, "html": full_html, "saved_path": saved_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/db/schema")
def db_schema():
    """读取 .env 配置的数据库表结构。"""
    try:
        return get_schema()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sql/generate")
def sql_generate(req: SQLReq):
    """自然语言 → SQL。"""
    try:
        return {"sql": generate_sql(req.question, get_schema())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sql/optimize")
def sql_optimize(req: SQLReq):
    """SQL 优化建议。"""
    try:
        return {"advice": optimize_sql(req.question, get_schema())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
