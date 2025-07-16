@echo off
echo =====================================
echo Certify Studio - Comprehensive Tests
echo =====================================
echo.

REM Activate virtual environment
call uv sync

REM Install test dependencies if needed
echo Installing test dependencies...
uv pip install pytest pytest-asyncio pytest-json-report httpx websockets aiofiles

REM Run comprehensive tests
echo.
echo Starting comprehensive test suite...
uv run python tests/run_comprehensive_tests.py

echo.
echo Test suite completed!
pause
