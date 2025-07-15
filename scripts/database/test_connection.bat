@echo off
echo Testing PostgreSQL Connection...
echo ================================
echo.

cd /d "%~dp0"
python test_connection.py

echo.
pause
