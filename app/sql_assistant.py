"""SQL 助手（Copilot 式辅助）：表结构可视化、SQL 生成、语句补全、优化建议、执行计划。"""
from sqlalchemy import create_engine, inspect, text

from . import config
from .llm import create_llm


def get_schema(db_url: str = None) -> dict:
    """读取数据库全部表结构：{表名: [列名, ...]}。"""
    url = db_url or config.DB_URL
    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        schema = {}
        for table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            schema[table] = cols
        return schema
    finally:
        engine.dispose()


def schema_to_text(schema: dict) -> str:
    """把表结构渲染成给 LLM 看的文本。"""
    lines = []
    for table, cols in schema.items():
        lines.append(f"表 {table}: 列 = {', '.join(cols)}")
    return "\n".join(lines) or "（数据库中没有表）"


def generate_sql(question: str, schema: dict, llm=None) -> str:
    """根据自然语言问题和表结构生成 SQL（只返回 SQL 语句）。"""
    llm = llm or create_llm()
    prompt = (
        "你是 SQL 专家。根据下面的表结构，把用户的问题翻译成一条 SQL 查询。\n"
        f"表结构：\n{schema_to_text(schema)}\n\n"
        f"用户问题：{question}\n\n"
        "只输出 SQL 语句本身，不要任何解释、注释或 markdown 代码块标记。"
    )
    resp = llm.invoke(prompt)
    sql = (resp.content if hasattr(resp, "content") else str(resp)).strip()
    sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
    return sql


def autocomplete(prefix: str, schema: dict, limit: int = 20) -> list:
    """语句补全：按前缀/包含匹配表名与列名（本地快速，不调 LLM）。"""
    prefix = (prefix or "").strip().lower()
    if not prefix:
        return []
    candidates = []
    for table, cols in schema.items():
        if table.lower().startswith(prefix) or prefix in table.lower():
            candidates.append(table)
        for col in cols:
            if col.lower().startswith(prefix) or prefix in col.lower():
                candidates.append(f"{table}.{col}")
    # 去重保序
    seen, out = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:limit]


def explain_sql(sql: str, db_url: str = None):
    """执行 EXPLAIN 并返回执行计划文本（SQLite/MySQL/PostgreSQL 通用尝试）。"""
    url = (db_url or config.DB_URL).strip()
    engine = create_engine(url)
    try:
        if url.startswith("sqlite"):
            sqlx = "EXPLAIN QUERY PLAN " + sql
        else:
            sqlx = "EXPLAIN " + sql
        with engine.connect() as conn:
            df = pd_read(conn, sqlx)
        return df.to_string(index=False)
    finally:
        engine.dispose()


def pd_read(conn, sqlx):
    import pandas as pd
    return pd.read_sql(text(sqlx), conn)


def optimize_sql(sql: str, schema: dict, llm=None) -> str:
    """让 LLM 审查 SQL 并给出优化建议（索引、写法、隐患）。"""
    llm = llm or create_llm()
    prompt = (
        "你是数据库优化专家。请审查下面的 SQL 和表结构，给出优化建议：\n"
        "1. 可以加哪些索引；2. 写法上有哪些可以改进；3. 潜在的性能/正确性隐患。\n\n"
        f"表结构：\n{schema_to_text(schema)}\n\nSQL：\n{sql}\n\n"
        "用中文简洁回答，分点列出。"
    )
    resp = llm.invoke(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)
