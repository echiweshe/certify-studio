@echo off
echo.
echo ========================================
echo Starting Certify Studio Frontend
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js found!
echo.

if not exist node_modules (
    echo Installing dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
)

if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
)

echo Starting development server...
echo.
echo Frontend will be available at: http://localhost:3000
echo Backend API expected at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

npm run dev