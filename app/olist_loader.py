"""Olist 巴西电商数据集加载（垂直场景数据包）。

数据集：10 万订单、2016-2018、多个巴西市场。文件位于 data/olist/。
"""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "olist"


def available() -> bool:
    return (DATA_DIR / "olist_orders_dataset.csv").exists()


def merged() -> pd.DataFrame:
    """订单 × 明细合并表（含 price / freight_value），RFM 与销售时序共用。"""
    orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
    items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv",
                        usecols=["order_id", "price", "freight_value"])
    m = orders.merge(items, on="order_id", how="inner")
    m["order_purchase_timestamp"] = pd.to_datetime(m["order_purchase_timestamp"], errors="coerce")
    return m


def describe() -> str:
    """数据集说明（用于 README / 页面展示）。"""
    orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv",
                         usecols=["order_id", "customer_id", "order_purchase_timestamp", "order_status"])
    items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv",
                        usecols=["order_id", "price"])
    m = orders.merge(items, on="order_id", how="inner")
    total = m["price"].sum()
    return (f"订单数 {len(orders):,} · 明细行 {len(m):,} · 总销售额 ¥{total/1e6:.1f}M"
            f" · 时间范围 {orders['order_purchase_timestamp'].min()[:10]} ~ {orders['order_purchase_timestamp'].max()[:10]}")
