@echo off
REM Fix python-docx issue

echo Fixing python-docx compatibility issue...
echo.

echo Removing old docx if present...
call uv remove docx

echo.
echo Installing correct python-docx package...
call uv add python-docx

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
