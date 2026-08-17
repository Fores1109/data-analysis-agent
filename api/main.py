"""FastAPI 服务（部署预留）：把核心能力暴露为 HTTP API。

启动：uvicorn api.main:app --host 0.0.0.0 --port 8000
文档：http://localhost:8000/docs

安全说明：
  - data_path 参数只允许访问项目 data 目录内的文件（路径白名单），
    防止路径遍历（../ 逃逸、绝对路径、~ 展开、盘符）与任意文件读取；
  - /api/analyze 会执行 LLM 生成的 pandas 代码（只读约束见 app/agent.py），
    请仅对可信数据调用，并建议将服务部署在隔离环境（Docker 容器内）。
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agent import ask
from app.data_source import load_file
from app.experiments import ab_proportion, ab_ttest
from app.ml_runner import auto_train
from app.sql_assistant import generate_sql, get_schema, optimize_sql

app = FastAPI(title="数据分析 Agent API", version="0.2.0")

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
