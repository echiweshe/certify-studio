@echo off
echo ========================================
echo CERTIFY STUDIO - COMPLETE TEST SUITE
echo ========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Installing test dependencies...
uv pip install pytest pytest-asyncio aioresponses psutil requests aiohttp

echo.
echo Starting test suite...
echo.

cd tests
uv run python run_all_tests.py

echo.
echo ========================================
echo Testing complete!
echo ========================================
pause
