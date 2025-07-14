@echo off
echo.
echo ============================================
echo Certify Studio - Full Stack Startup
echo AI Agent Operating System for Educational Excellence
echo ============================================
echo.

cd /d "%~dp0"

echo Starting Backend and Frontend services...
echo.

:: Start Backend in a new window
echo Launching Backend API...
start "Certify Studio Backend" cmd /k "cd /d "%~dp0" && start.bat"

:: Wait a moment for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

:: Start Frontend in a new window
echo Launching Frontend UI...
start "Certify Studio Frontend" cmd /k "cd /d "%~dp0frontend" && start.bat"

echo.
echo ============================================
echo Certify Studio is starting up!
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Both services are running in separate windows.
echo Close this window when done.
echo ============================================
echo.

pause