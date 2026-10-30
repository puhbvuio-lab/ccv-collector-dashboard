@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"
"%PYTHON%" monitor.py --duration 20 --auto-charts
echo.
echo 本次监测已结束（跑满20分钟，或所有跟踪直播提前结束）。图表已生成到 charts\。
pause
