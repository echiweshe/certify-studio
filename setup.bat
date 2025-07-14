@echo off
REM Certify Studio Setup and Test Script for Windows

echo === Certify Studio Setup ===
echo.

echo Step 1: Adding dev dependencies...
call uv add --dev pytest pytest-asyncio pytest-cov pytest-mock faker httpx

echo.
echo Step 2: Syncing all dependencies...
call uv sync --all-extras

echo.
echo Step 3: Checking environment...
call uv run python --version

echo.
echo Step 4: Testing imports...
call uv run python test_imports_uv.py

echo.
echo Step 5: Running unit tests...
call uv run pytest tests/unit/test_simple.py -v

echo.
echo === Setup Complete ===
echo.
echo If tests passed, you can now run:
echo   - All unit tests: uv run pytest tests/unit/ -v
echo   - All tests: uv run pytest -v
echo   - Start API: uv run python -m certify_studio.app
echo.
pause
