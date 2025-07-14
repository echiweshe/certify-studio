@echo off
REM Quick fix for missing dependencies

echo Installing missing dependencies...

echo.
echo Installing python-jose with cryptography...
call uv add "python-jose[cryptography]"

echo.
echo Installing soundfile...
call uv add soundfile

echo.
echo Syncing...
call uv sync

echo.
echo Testing imports...
call uv run python test_imports_uv.py

echo.
echo Running tests...
call uv run pytest tests/unit/test_simple.py -v

pause
