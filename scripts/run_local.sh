#!/usr/bin/env bash
# 一键启动（macOS / Linux）
set -e
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  已生成 .env，请填入 DEEPSEEK_API_KEY 后重新运行"
  exit 1
fi

echo "🚀 启动中... http://localhost:8501"
streamlit run web/app.py
