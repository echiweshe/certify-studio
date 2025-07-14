@echo off
echo Starting Certify Studio...
cd /d "%~dp0"
uv run python scripts/launch_clean.py
pause
