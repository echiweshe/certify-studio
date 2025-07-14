@echo off
echo ============================================================
echo     Adding LangChain Dependencies & Restarting
echo ============================================================
echo.

echo Adding langchain-community and related packages...
uv add langchain-community langchain-openai langchain-anthropic

echo.
echo Syncing all dependencies...
uv sync --all-extras

echo.
echo Starting Certify Studio...
uv run python scripts/uv_enterprise_start.py

pause
