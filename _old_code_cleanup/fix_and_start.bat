@echo off
REM Quick fix and restart script for Windows

echo Installing missing dependencies...
.venv\Scripts\python.exe -m pip install aiosqlite

echo.
echo Starting Certify Studio...
.venv\Scripts\python.exe scripts\quickstart.py
