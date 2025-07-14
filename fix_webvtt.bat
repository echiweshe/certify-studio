@echo off
REM Install webvtt and run tests

echo Installing webvtt-py...
call uv add webvtt-py

echo.
echo Syncing dependencies...
call uv sync

echo.
echo Setting environment variable...
set TF_USE_LEGACY_KERAS=1

echo.
echo Running tests...
uv run pytest tests/unit/test_simple.py -v

pause
