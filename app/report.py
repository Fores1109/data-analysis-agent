"""报告生成：把问答历史、数据概览、图表汇总为 Markdown / HTML 报告。"""
import datetime
from pathlib import Path

import markdown as md_lib

from . import config


def build_md(title: str, data_name: str, qa_pairs: list, overview: str = "", extra_sections: list = None) -> str:
    """生成 Markdown 报告。

    参数:
        qa_pairs: [(问题, 回答), ...]
        extra_sections: [{"heading": str, "body": str}, ...]
    """
    lines = [
        f"# {title}",
        "",
        f"- 生成时间：{datetime.datetime.now():%Y-%m-%d %H:%M}",
        f"- 数据来源：{data_name or '未记录'}",
        "",
        "---",
        "",
        "## 1. 数据概览",
        "",
        overview or "（无概览信息）",
        "",
        "## 2. 分析问答记录",
        "",
    ]
    if not qa_pairs:
        lines.append("（暂无问答记录）")
    for i, (q, a) in enumerate(qa_pairs, 1):
        lines += [f"### Q{i}. {q}", "", str(a), ""]

    for sec in extra_sections or []:
        lines += ["---", "", f"## {sec['heading']}", "", str(sec["body"]), ""]

    return "\n".join(lines)


def md_to_html(md_text: str) -> str:
    return md_lib.markdown(md_text, extensions=["tables", "fenced_code"])


def save_report(md_text: str, name: str = None) -> Path:
    name = name or f"report_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    md_path = config.REPORT_DIR / f"{name}.md"
    md_path.write_text(md_text, encoding="utf-8")
    return md_path


def embed_charts_html(charts_html: list) -> str:
    """把若干 figure.to_html() 片段拼成一段 HTML。"""
    return "\n".join(f"<div style='margin:12px 0'>{h}</div>" for h in charts_html if h)
