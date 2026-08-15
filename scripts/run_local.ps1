# 一键启动数据分析 Agent（由 启动数据分析Agent.bat 调用，也可手动运行）
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$py = Join-Path $root '.venv\Scripts\python.exe'

# 1. 虚拟环境（没有则创建）
if (-not (Test-Path $py)) {
    Write-Host '首次运行：创建虚拟环境...' -ForegroundColor Cyan
    $syspy = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $syspy) { $syspy = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" }
    & $syspy -m venv .venv
    if (-not (Test-Path $py)) {
        Write-Host '❌ 虚拟环境创建失败：未找到 Python，请安装 Python 3.10+ 后重试。' -ForegroundColor Red
        Read-Host '按回车退出'
        exit 1
    }
}

# 2. 依赖检查（已装好则直接跳过，不联网、秒启动）
& $py -c "import importlib.util,sys; sys.exit(0 if all(importlib.util.find_spec(m) for m in ['streamlit','langchain','pandas','sklearn','plotly']) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host '首次运行：安装依赖（需要联网，约几分钟）...' -ForegroundColor Cyan
    & $py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        Write-Host '❌ 依赖安装失败，请检查网络后重试。' -ForegroundColor Red
        Read-Host '按回车退出'
        exit 1
    }
} else {
    Write-Host '依赖已就绪 ✓' -ForegroundColor Green
}

# 3. .env 配置检查
if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host '⚠️  已生成 .env 文件，请用记事本填入 DEEPSEEK_API_KEY 后重新运行。' -ForegroundColor Yellow
    Read-Host '按回车退出'
    exit 1
}


# 3.5 预填 Streamlit 首次运行向导（失败也不影响启动）
try {
    $stCred = Join-Path $env:USERPROFILE '.streamlit\credentials.toml'
    if (-not (Test-Path $stCred)) {
        New-Item -ItemType Directory -Force -Path (Split-Path $stCred) | Out-Null
        "[general]`nemail = `"`"" | Set-Content -Path $stCred -Encoding UTF8
    }
} catch { Write-Host '（跳过 Streamlit 配置写入，无影响）' -ForegroundColor DarkGray }
# 4. 启动
Write-Host '🚀 启动中... 浏览器访问 http://localhost:8501（Ctrl+C 停止）' -ForegroundColor Green
& $py -m streamlit run web/app.py --server.address 127.0.0.1 --browser.gatherUsageStats false --server.headless true
