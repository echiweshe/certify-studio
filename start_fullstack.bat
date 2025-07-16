@echo off
echo =====================================
echo Certify Studio - Full Stack Startup
echo =====================================
echo.

REM Start backend in a new window
echo Starting backend server...
start "Certify Studio Backend" cmd /k "uv run uvicorn certify_studio.main:app --reload --port 8000"

REM Wait a moment for backend to start
timeout /t 5 /nobreak > nul

REM Start frontend in a new window
echo Starting frontend development server...
start "Certify Studio Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =====================================
echo Both servers are starting...
echo =====================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
pause > nul

REM Kill all node and python processes (be careful with this!)
echo.
echo Stopping servers...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
taskkill /F /IM python.exe 2>nul

echo Servers stopped.
pause
