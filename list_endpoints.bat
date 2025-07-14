@echo off
cls
echo Listing all API endpoints...
echo.
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run python list_api_endpoints.py
echo.
pause
