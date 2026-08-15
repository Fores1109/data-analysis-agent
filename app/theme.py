"""全局界面主题：为 Streamlit 页面注入统一视觉样式。

用法（每个页面开头调用）：
    from app.theme import apply_theme, page_header
    apply_theme()
    page_header("💬", "页面标题", "页面副标题")
"""
import streamlit as st

# 主题色板
PRIMARY = "#4F6EF7"   # 主蓝
ACCENT = "#8B5CF6"    # 辅紫
INK = "#1E293B"       # 主文字
MUTED = "#64748B"     # 次要文字

THEME_CSS = """
<style>
:root {
  --p:#4F6EF7; --p2:#8B5CF6; --ink:#1E293B; --muted:#64748B;
  --card:#FFFFFF; --line:rgba(148,163,184,.22);
}
html, body, [class*="css"] {
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}
/* ---------- 全局背景（浅色渐变 + 光斑） ---------- */
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(900px 520px at 6% -12%, rgba(79,110,247,.10), transparent 60%),
    radial-gradient(820px 520px at 106% 8%, rgba(139,92,246,.10), transparent 55%),
    linear-gradient(160deg, #eef2fb 0%, #f8fafd 52%, #eef0f9 100%);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: rgba(255,255,255,.78);
  border-right: 1px solid var(--line);
  backdrop-filter: blur(8px);
}
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px; }

/* ---------- 页头渐变横幅 ---------- */
.page-banner {
  display:flex; align-items:center; gap:16px;
  background: linear-gradient(120deg, #4F6EF7 0%, #8B5CF6 100%);
  color:#fff; border-radius:18px; padding:22px 26px; margin-bottom:20px;
  box-shadow: 0 12px 32px rgba(79,110,247,.30);
}
.page-banner .icon { font-size:36px; filter: drop-shadow(0 2px 6px rgba(0,0,0,.18)); }
.page-banner .title { font-size:23px; font-weight:700; letter-spacing:.6px; }
.page-banner .sub { font-size:13px; opacity:.90; margin-top:4px; line-height:1.5; }

/* ---------- 指标卡片 ---------- */
[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px 18px;
  box-shadow: 0 4px 14px rgba(30,41,59,.06);
}
[data-testid="stMetricLabel"] { color: var(--muted); font-size: 13px; }
[data-testid="stMetricValue"] { color: var(--ink); font-weight: 700; }
[data-testid="stMetricDelta"] { font-size: 12px; }

/* ---------- 按钮 ---------- */
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(120deg, var(--p), var(--p2));
  border: none; color: #fff; font-weight: 600;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(79,110,247,.35);
  transition: transform .12s ease, filter .12s ease;
}
[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); transform: translateY(-1px); }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-tertiary"] {
  border-radius: 10px; font-weight: 600;
}

/* ---------- 输入控件 ---------- */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div,
[data-testid="stFileUploader"] section {
  border-radius: 10px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--p) !important;
  box-shadow: 0 0 0 3px rgba(79,110,247,.18) !important;
}
[data-testid="stNumberInput"] input { border-radius: 10px !important; }

/* ---------- 页签 / 展开 / 单选 ---------- */
[data-testid="stTabs"] button { font-weight: 600; }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--p); }
[data-testid="stExpander"] {
  border-radius: 12px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,.62);
}
[data-testid="stRadio"] label:hover { cursor: pointer; }

/* ---------- 聊天消息 ---------- */
[data-testid="stChatMessage"] {
  border-radius: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 2px 8px rgba(30,41,59,.05);
  background: rgba(255,255,255,.7);
}

/* ---------- 表格 / 数据 ---------- */
[data-testid="stDataFrame"] {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--line);
}
[data-testid="stDataFrame"] canvas { border-radius: 12px; }
[data-testid="stTable"] { border-radius: 12px; overflow: hidden; }

/* ---------- 标题文字 ---------- */
h1, h2, h3 { color: var(--ink); letter-spacing: .3px; }
[data-testid="stCaptionContainer"] { color: var(--muted); }

/* ---------- 隐藏默认菜单与页脚 ---------- */
#MainMenu, footer { visibility: hidden; }
</style>
"""


def apply_theme():
    """注入全局 CSS（在每个页面顶部调用一次）。"""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    """渲染统一的渐变页头横幅。"""
    sub = f'<div class="sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="page-banner"><div class="icon">{icon}</div>'
        f'<div><div class="title">{title}</div>{sub}</div></div>',
        unsafe_allow_html=True,
    )
