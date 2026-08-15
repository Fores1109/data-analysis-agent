"""RFM 用户分层（电商经典场景）：价值分层 + 客户画像。"""
import numpy as np
import pandas as pd

SEGMENTS = [
    "重要价值客户", "重要发展客户", "重要保持客户", "重要挽留客户",
    "一般价值客户", "一般发展客户", "一般保持客户", "一般挽留客户",
]


def _score(series, reverse=False, n=4):
    """分位数打分 1..n（reverse=True 时值越大分越高）。"""
    try:
        out = pd.qcut(series.rank(method="first"), n, labels=list(range(1, n + 1))).astype(int)
    except ValueError:
        out = pd.Series(2, index=series.index)
    if reverse:
        out = n + 1 - out
    return out


def _segment(row):
    r, f, m = row["R"], row["F"], row["M"]
    if m >= 3:  # 高价值（按金额）
        if r >= 3 and f >= 3: return "重要价值客户"
        if r >= 3:            return "重要发展客户"
        if f >= 3:            return "重要保持客户"
        return "重要挽留客户"
    else:
        if r >= 3 and f >= 3: return "一般价值客户"
        if r >= 3:            return "一般发展客户"
        if f >= 3:            return "一般保持客户"
        return "一般挽留客户"


def rfm_table(df: pd.DataFrame, customer_id: str = "customer_id",
              date_col: str = "order_purchase_timestamp", amount_col: str = "price"):
    """计算 RFM 打分与分层。

    返回 (明细表, 分层汇总)。明细表含 recency/frequency/monetary/R/F/M/分层。
    """
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col, customer_id])
    d[amount_col] = pd.to_numeric(d[amount_col], errors="coerce").fillna(0)
    if len(d) == 0:
        raise ValueError("订单数据为空")

    now = d[date_col].max() + pd.Timedelta(days=1)
    g = d.groupby(customer_id).agg(
        recency=(date_col, lambda x: int((now - x.max()).days)),
        frequency=(date_col, "count"),
        monetary=(amount_col, "sum"),
    ).reset_index()

    g["R"] = _score(g["recency"], reverse=True)   # 越近越好
    g["F"] = _score(g["frequency"])               # 越频繁越好
    g["M"] = _score(g["monetary"])                # 金额越高越好
    g["RFM码"] = (g["R"].astype(str) + g["F"].astype(str) + g["M"].astype(str))
    g["客户分层"] = g.apply(_segment, axis=1)

    # 分层汇总
    summary = []
    for seg in SEGMENTS:
        sub = g[g["客户分层"] == seg]
        if len(sub) == 0:
            continue
        summary.append({
            "客户分层": seg,
            "客户数": int(len(sub)),
            "客户占比": round(len(sub) / len(g) * 100, 2),
            "金额占比": round(sub["monetary"].sum() / g["monetary"].sum() * 100, 2),
            "平均客单价": round(sub["monetary"].mean(), 2),
            "平均购买次数": round(sub["frequency"].mean(), 2),
            "平均最近购买天数": round(sub["recency"].mean(), 1),
            "画像": _portrait(seg),
        })
    summary.sort(key=lambda x: x["金额占比"], reverse=True)
    return g, pd.DataFrame(summary)


def _portrait(seg: str) -> str:
    return {
        "重要价值客户": "高价值高活跃，重点维护，提供 VIP 权益与专属服务",
        "重要发展客户": "消费力强但活跃度偏低，通过新品推荐/优惠刺激复购",
        "重要保持客户": "消费力强但近期未购买，定向召回（邮件/短信）防止流失",
        "重要挽留客户": "高价值但活跃度极低，大力度挽回或作为流失预警",
        "一般价值客户": "中等价值较活跃，培养消费习惯，交叉销售",
        "一般发展客户": "中等价值活跃度低，内容营销提升粘性",
        "一般保持客户": "中等价值近期未购买，常规触达维持",
        "一般挽留客户": "低活跃低价值，控制营销成本，观察期处理",
    }[seg]
