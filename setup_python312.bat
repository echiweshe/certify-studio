@echo off
echo ========================================
echo Certify Studio - Python 3.12 Setup
echo ========================================
echo.

REM Check if UV is available
where uv >nul 2>1
if %errorlevel% == 0 (
    echo UV found! Setting up Python 3.12...
    echo.
    
    REM Install Python 3.12 with UV
    echo Installing Python 3.12...
    uv python install 3.12
    
    REM Remove existing .venv if it exists
    if exist .venv (
        echo Removing existing virtual environment...
        rmdir /s /q .venv
    )
    
    REM Create new venv with Python 3.12
    echo Creating virtual environment with Python 3.12...
    uv venv --python 3.12
    
    REM Sync all dependencies
    echo Installing all dependencies...
    uv sync --all-extras
    
    echo.
    echo ========================================
    echo Setup Complete!
    echo ========================================
    echo.
    echo To start Certify Studio, run:
    echo   uv run python scripts/launch.py
    echo.
    
) else (
    echo UV not found!
    echo.
    echo Please install UV first:
    echo   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo Or download Python 3.12 manually from:
    echo   https://www.python.org/downloads/release/python-3127/
    echo.
)

pause
