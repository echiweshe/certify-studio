@echo off
REM Enterprise UV Launcher for Certify Studio
REM NO PIP. UV ONLY. ENTERPRISE GRADE.

echo.
echo ============================================================
echo     Certify Studio - Enterprise UV Launcher
echo ============================================================
echo.

REM Use UV to run Python (ensures we use the right environment)
uv run python scripts/uv_enterprise_start.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ============================================================
    echo     ERROR: Startup failed. Check logs above.
    echo ============================================================
    echo.
    pause
)
