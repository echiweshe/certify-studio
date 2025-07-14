@echo off
echo Adding missing dependency and restarting...
echo.

REM Add the missing dependency using UV
uv add python-json-logger

echo.
echo Starting Certify Studio with UV...
uv run python scripts/uv_enterprise_start.py
