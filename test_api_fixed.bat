@echo off
cls
echo Testing API endpoints after fixes...
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run python test_api_detailed.py
pause
