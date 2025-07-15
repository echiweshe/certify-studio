@echo off
echo Starting Certify Studio Backend for Testing...
echo ==========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Starting backend server...
start cmd /k "uv run uvicorn certify_studio.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Waiting for server to start...
timeout /t 5 /nobreak > nul

echo.
echo Testing server status...
curl -s http://localhost:8000/health

echo.
echo ==========================================
echo Backend server should be running at:
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo ==========================================
echo.
pause
