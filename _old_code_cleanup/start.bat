@echo off
echo.
echo ========================================
echo     Certify Studio - Smart Launcher
echo ========================================
echo.

REM Run the smart start script
.venv\Scripts\python.exe scripts\smart_start.py

REM If it fails, pause to see the error
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause > nul
)
