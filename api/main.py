"""FastAPI 服务（部署预留）：把核心能力暴露为 HTTP API。

启动：uvicorn api.main:app --host 0.0.0.0 --port 8000
文档：http://localhost:8000/docs
"""
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

app = FastAPI(title="数据分析 Agent API", version="0.1.0")


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
    """自然语言问答分析：对指定 CSV 数据文件提问。"""
    try:
        df = load_file(req.data_path)
        return {"answer": ask(df, req.question)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/train")
def ml_train(data_path: str, target: str):
    """机器学习：自动选模型训练评估。"""
    try:
        return auto_train(load_file(data_path), target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ab/test")
def ab_test(data_path: str, control_col: str, treatment_col: str):
    """A/B 检验：两组连续指标 t 检验。"""
    try:
        df = load_file(data_path)
        return ab_ttest(df[control_col], df[treatment_col])
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
