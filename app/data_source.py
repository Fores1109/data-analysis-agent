"""数据源接入：CSV / Excel / JSON / 数据库(SQL) / API 接口，统一输出 pandas.DataFrame。

说明：本模块是「对接数据库/API」需求的实现位置，可继续扩展更多数据源。
"""
import io
from pathlib import Path

import pandas as pd
import requests

from . import config

CSV_ENCODINGS = ("utf-8-sig", "gbk", "utf-8")


# ---------- 文件 ----------
def _read_csv_bytes(data: bytes) -> pd.DataFrame:
    for enc in CSV_ENCODINGS:
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别 CSV 编码，请另存为 UTF-8")


def load_csv(path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    for enc in CSV_ENCODINGS:
        try:
            return pd.read_csv(p, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别 CSV 编码，请另存为 UTF-8")


def load_file(src) -> pd.DataFrame:
    """智能加载：兼容文件路径和 Streamlit 的 UploadedFile 对象。"""
    if hasattr(src, "getvalue"):  # Streamlit UploadedFile
        name = (src.name or "").lower()
        data = src.getvalue()
        if name.endswith((".csv", ".txt")):
            return _read_csv_bytes(data)
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(data))
        if name.endswith(".json"):
            return pd.json_normalize(_json_loads(data))
        raise ValueError(f"不支持的文件类型: {src.name}")
    # 文件路径
    name = str(src).lower()
    if name.endswith((".csv", ".txt")):
        return load_csv(src)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(src)
    if name.endswith(".json"):
        return pd.json_normalize(_json_loads(Path(src).read_bytes()))
    raise ValueError(f"不支持的文件类型: {src}")


def _json_loads(data: bytes):
    import json
    return json.loads(data.decode("utf-8"))


# ---------- 数据库 ----------
def load_db(query: str, db_url: str = None) -> pd.DataFrame:
    """执行 SQL 查询并返回 DataFrame。db_url 示例：
    sqlite:///./data/app.db
    mysql+pymysql://user:pass@host:3306/db
    postgresql+psycopg2://user:pass@host:5432/db
    """
    from sqlalchemy import create_engine, text

    url = db_url or config.DB_URL
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)
    finally:
        engine.dispose()


# ---------- API ----------
def load_api(url: str, params: dict = None, headers: dict = None, json_path: str = None,
             timeout: int = 30) -> pd.DataFrame:
    """请求 JSON 接口并转为 DataFrame。

    参数:
        url: 接口地址
        params/headers: 请求参数
        json_path: 若返回结构嵌套，如 {"code":0,"data":{"items":[...]}} 传 "data.items"
    """
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if json_path:
        for key in json_path.split("."):
            data = data[key]
    if isinstance(data, dict):
        data = [data]
    return pd.json_normalize(data)
