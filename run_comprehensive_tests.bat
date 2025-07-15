@echo off
echo ===============================================
echo    Certify Studio - Comprehensive Test Suite
echo ===============================================
echo.

REM Navigate to project root
cd /d "%~dp0\.."

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Install test dependencies if needed
echo Installing test dependencies...
uv pip install pytest pytest-asyncio pytest-cov pytest-json-report httpx websocket-client colorama coverage --quiet

echo.
echo Starting comprehensive test suite...
echo.

REM Run the comprehensive test suite
python tests\run_comprehensive_tests.py %*

echo.
echo ===============================================
echo    Test execution completed
echo ===============================================
pause
