@echo off
echo ===================================
echo Certify Studio Test Suite
echo ===================================
echo.

cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Running Integration Test...
echo ---------------------------
uv run python tests/test_integration.py
if %errorlevel% neq 0 (
    echo Integration test failed!
    pause
    exit /b 1
)
echo.

echo Running Unit Tests...
echo ---------------------------
uv run pytest tests/test_comprehensive.py -v --tb=short
if %errorlevel% neq 0 (
    echo Unit tests failed!
    pause
    exit /b 1
)

echo.
echo ===================================
echo All tests completed!
echo ===================================
pause
