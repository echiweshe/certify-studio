@echo off
echo Checking Python version...
echo.

REM Check system Python
python --version

echo.
echo Checking UV Python...
uv run python --version

echo.
echo Checking .venv Python...
.venv\Scripts\python.exe --version

echo.
pause
