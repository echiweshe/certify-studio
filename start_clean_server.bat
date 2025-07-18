@echo off
echo Starting Certify Studio (Clean Version)...
echo =========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting server...
echo Visit: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

set PYTHONPATH=%cd%\src
uv run python -m certify_studio.main

pause
