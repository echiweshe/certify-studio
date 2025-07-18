@echo off
echo ========================================
echo CERTIFY STUDIO FULL SYSTEM RESTORATION
echo ========================================
echo.
echo Restoring your AI Agent Operating System...
echo.

REM Step 1: Run diagnostics
echo Step 1: Running system diagnostics...
uv run python diagnose_system.py
echo.
pause

REM Step 2: Fix imports
echo.
echo Step 2: Fixing import paths...
uv run python fix_imports.py
echo.
pause

REM Step 3: Test the restoration
echo.
echo Step 3: Starting the FULL system (not simplified)...
echo.
echo This will start:
echo - FastAPI with full authentication
echo - PostgreSQL database connection
echo - AI Agent orchestration
echo - WebSocket real-time updates
echo - All enterprise features
echo.

REM Set proper environment
set PYTHONPATH=%CD%\src
set ENVIRONMENT=development
set DEBUG=True

REM Start the real system
echo Starting Certify Studio...
uv run python -m certify_studio.main

pause
