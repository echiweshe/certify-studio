@echo off
echo Starting Certify Studio Server...
echo ================================

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

REM Fix indentation first
echo Fixing any indentation issues...
python fix_indentation.py

echo.
echo Starting server with different methods...
echo.

REM Try method 1: Add src to Python path and run module
echo Method 1: Running as module with PYTHONPATH...
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -m certify_studio.main

REM If that fails, try method 2
if errorlevel 1 (
    echo.
    echo Method 1 failed. Trying method 2: Direct file execution...
    cd src
    python -m certify_studio.main
)

REM If that also fails, try method 3
if errorlevel 1 (
    echo.
    echo Method 2 failed. Trying method 3: Using uvicorn with uv...
    cd ..
    uv run uvicorn certify_studio.main:app --reload --host 0.0.0.0 --port 8000
)

REM If all fail, show the error
if errorlevel 1 (
    echo.
    echo All methods failed. Please check the error messages above.
    echo.
    echo You can also try running directly:
    echo   cd src
    echo   python certify_studio\main.py
)

pause
