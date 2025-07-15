@echo off
echo Updating .env file with PostgreSQL configuration...
echo ==================================================
echo.

cd /d "%~dp0"
python update_env.py

echo.
pause
