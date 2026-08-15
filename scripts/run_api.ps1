# 一键启动 FastAPI 后端（部署调试用）
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not (Test-Path '.venv')) { python -m venv .venv }

$py = Join-Path $root '.venv\Scripts\python.exe'
& $py -m pip install --upgrade pip --quiet
& $py -m pip install -r (Join-Path $root 'api\requirements-api.txt') --quiet

Write-Host '🚀 API 启动中... 文档 http://localhost:8000/docs' -ForegroundColor Green
& $py -m uvicorn api.main:app --host 0.0.0.0 --port 8000
