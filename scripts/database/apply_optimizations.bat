@echo off
echo Applying Performance Optimizations...
echo =====================================
echo.

cd /d "%~dp0"
python apply_optimizations.py

echo.
pause
