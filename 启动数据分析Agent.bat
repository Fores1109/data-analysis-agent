@echo off
title Data Analysis Agent Launcher
echo ============================================
echo   Data Analysis Agent is starting...
echo   Then open http://localhost:8501 in browser
echo ============================================
echo.
cd /d "%~dp0"
where pwsh >nul 2>nul
if errorlevel 1 goto use_powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_local.ps1"
goto done
:use_powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_local.ps1"
:done
echo.
echo ============================================
echo   App exited. Press any key to close.
echo ============================================
pause