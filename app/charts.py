"""图表生成：基于 plotly 的常用分析图表，返回交互式 figure。

悬停解释器：plotly 图表自带悬浮信息；配合列说明字典可让悬浮框带解释文字。
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def bar(df, x, y=None, title=""):
    if y:
        fig = px.bar(df, x=x, y=y, title=title, text_auto=".2s")
    else:  # 未指定 Y 时按 X 统计数量
        fig = px.bar(df, x=x, title=title or f"{x} 数量统计", text_auto=".2s")
    return _tidy(fig)


def line(df, x, y, title=""):
    fig = px.line(df, x=x, y=y, title=title, markers=True)
    return _tidy(fig)


def scatter(df, x, y, color=None, title=""):
    fig = px.scatter(df, x=x, y=y, color=color, title=title, trendline="ols")
    return _tidy(fig)


def histogram(df, col, bins=30, title=""):
    fig = px.histogram(df, x=col, nbins=bins, title=title or f"{col} 分布")
    return _tidy(fig)


def box(df, y, x=None, title=""):
    fig = px.box(df, y=y, x=x, title=title or f"{y} 箱线图")
    return _tidy(fig)


def heatmap_corr(df, title="数值列相关性热力图"):
    num = df.select_dtypes(include="number")
    if num.shape[1] < 2:
        raise ValueError("至少需要两列数值列才能画相关性热力图")
    fig = px.imshow(num.corr(), text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, title=title)
    return _tidy(fig)


def time_series(df, date_col, value_col, agg="sum", title=""):
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    grouped = d.groupby(d[date_col].dt.date)[value_col].agg(agg).reset_index()
    fig = px.line(grouped, x=date_col, y=value_col, markers=True,
                  title=title or f"{value_col} 按日期{agg}")
    return _tidy(fig)


def _tidy(fig):
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=20, t=60, b=40),
        title_font_size=16,
    )
    return fig


def with_hover_hints(fig, column_hints: dict):
    """悬停解释器：把列说明注入悬浮信息（尽力而为，不抛错）。"""
    try:
        hints = {k: v for k, v in (column_hints or {}).items() if v}
        if not hints:
            return fig
        note = " | ".join(f"{k}: {v}" for k, v in list(hints.items())[:6])
        fig.update_layout(
            annotations=[
                dict(text=f"💡 {note}", xref="paper", yref="paper",
                     x=0, y=1.06, showarrow=False, font=dict(size=11, color="#555"))
            ]
        )
    except Exception:
        pass
    return fig


def figure_to_html(fig) -> str:
    """把 figure 转成可嵌入 HTML 报告的片段。"""
    return fig.to_html(full_html=False, include_plotlyjs="cdn")
