@echo off
REM Certify Studio Launcher

cd /d "%~dp0\.."
echo Starting Certify Studio...
uv run python scripts/launch.py
pause
