@echo off
echo Cleaning and reinstalling dependencies...
cd /d "%~dp0\.."
uv run python scripts/clean_reinstall.py
pause
