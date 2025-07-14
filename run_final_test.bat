@echo off
REM Final test run with all fixes

echo Setting environment variable...
set TF_USE_LEGACY_KERAS=1

echo.
echo Running tests...
uv run pytest tests/unit/test_simple.py -v

echo.
echo If tests pass, you can run all tests with:
echo   uv run pytest -v

pause
