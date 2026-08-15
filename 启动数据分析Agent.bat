@echo off
chcp 65001 >nul
title 数据分析 Agent 启动器
echo ============================================
echo   📊 数据分析 Agent 启动中...
echo   首次运行会自动安装依赖（需要联网）
echo   启动后请用浏览器打开 http://localhost:8501
echo ============================================
echo.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_local.ps1"
echo.
echo 程序已退出。
pause
