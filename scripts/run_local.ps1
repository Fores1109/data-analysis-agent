# 一键启动（Windows PowerShell）
# 用法：右键「使用 PowerShell 运行」或  .\scripts\run_local.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not (Test-Path '.venv')) { python -m venv .venv }

$py = Join-Path $root '.venv\Scripts\python.exe'
& $py -m pip install --upgrade pip --quiet
& $py -m pip install -r requirements.txt --quiet

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host '⚠️  已生成 .env 文件，请先用记事本填入 DEEPSEEK_API_KEY，然后重新运行本脚本。' -ForegroundColor Yellow
    Read-Host '按回车退出'
    exit 1
}

Write-Host '🚀 启动中... 浏览器访问 http://localhost:8501 （Ctrl+C 停止）' -ForegroundColor Green
& $py -m streamlit run web/app.py
