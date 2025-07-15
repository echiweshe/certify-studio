@echo off
echo ===============================================
echo    Certify Studio - PostgreSQL Setup
echo ===============================================
echo.

REM Navigate to scripts directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Install required Python packages
echo Installing required packages...
pip install psycopg2-binary --quiet

echo.
echo Starting PostgreSQL setup...
echo.

REM Run the setup script
python setup_postgresql.py

echo.
echo ===============================================
echo    Setup process completed
echo ===============================================
pause
