@echo off
REM Quick test runner to verify imports are working

echo Testing imports...
echo.

cd /d "C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio"

echo Running simple test...
uv run pytest tests/unit/test_simple.py -v

echo.
pause
