@echo off
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
echo Testing API startup...
uv run uvicorn certify_studio.main:app --port 8001
