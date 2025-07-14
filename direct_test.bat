@echo off
echo Running direct test...
echo.

cd /d "C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio"

uv run python scripts/direct_test.py

echo.
pause
