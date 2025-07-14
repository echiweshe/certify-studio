@echo off
REM Run tests with fixed imports

echo Setting environment variable...
set TF_USE_LEGACY_KERAS=1

echo.
echo Running tests...
uv run pytest tests/unit/test_simple.py -v

pause
