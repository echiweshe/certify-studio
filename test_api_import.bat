@echo off
cls
echo Testing API import fix...
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run python test_minimal_api.py
pause
