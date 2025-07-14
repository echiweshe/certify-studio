@echo off
REM Direct test runner with environment variables

echo === Running Certify Studio Tests ===
echo.

REM Set environment variables
set TF_USE_LEGACY_KERAS=1
set TF_ENABLE_ONEDNN_OPTS=0

REM Run the tests
echo Running tests with environment variables set...
uv run pytest tests/unit/test_simple.py -v

echo.
echo === Test Run Complete ===
pause
