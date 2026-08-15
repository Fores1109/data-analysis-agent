"""全局配置：读取项目根目录 .env 文件。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get(key, default=None):
    return os.getenv(key, default)


# ---- LLM ----
LLM_PROVIDER = get("LLM_PROVIDER", "deepseek")          # deepseek | openai | ollama
DEEPSEEK_API_KEY = get("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = get("DEEPSEEK_MODEL", "deepseek-chat")  # 注意 reasoner 不支持函数调用
DEEPSEEK_BASE_URL = get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
OPENAI_API_KEY = get("OPENAI_API_KEY")
OPENAI_MODEL = get("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# ---- 数据 ----
DB_URL = get("DB_URL", "sqlite:///./data/app.db")        # sqlite:/// | mysql+pymysql:// | postgresql+psycopg2://

# ---- 输出目录 ----
REPORT_DIR = BASE_DIR / "data" / "reports"
CHART_DIR = BASE_DIR / "data" / "charts"
for _d in (REPORT_DIR, CHART_DIR):
    _d.mkdir(parents=True, exist_ok=True)
