@echo off
REM Fix Keras compatibility and run tests

echo === Fixing Keras Compatibility Issue ===
echo.

echo Installing tf-keras...
call uv add tf-keras

echo.
echo Setting environment variable...
set TF_USE_LEGACY_KERAS=1

echo.
echo Running tests with legacy Keras...
call uv run pytest tests/unit/test_simple.py -v

pause
