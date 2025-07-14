@echo off
REM Simple test runner with environment variables

echo Setting environment variables...
set TF_USE_LEGACY_KERAS=1
set TF_ENABLE_ONEDNN_OPTS=0

echo.
echo Running tests...
uv run pytest tests/unit/test_simple.py -v

pause
