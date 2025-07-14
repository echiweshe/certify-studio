@echo off
cls
echo ============================================================
echo Certify Studio - Test Suite After Fixes
echo ============================================================
echo.

cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Running diagnostic test suite...
echo.

uv run python run_tests_diagnostic.py

echo.
echo ============================================================
echo Press any key to exit...
echo ============================================================
pause > nul
