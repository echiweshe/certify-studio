@echo off
echo Running import diagnostics...
echo.

cd /d "C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio"

REM First run the minimal test without conftest
echo Running minimal test...
uv run pytest tests/unit/test_minimal.py -v --no-header

echo.
echo Running import test...
uv run pytest tests/unit/test_imports.py -v --no-header -s

pause
