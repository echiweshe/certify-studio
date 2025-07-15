@echo off
echo ===============================================
echo    Certify Studio - Test Workflow
echo ===============================================
echo.

REM Navigate to project root
cd /d "%~dp0"

echo Step 1: Testing Backend Connectivity
echo ------------------------------------
python tests\test_backend_connectivity.py

echo.
echo Step 2: Running AWS AI Practitioner Test
echo ----------------------------------------
echo.

REM Run the AWS specific test using uv
uv run python tests\run_comprehensive_tests.py --aws

echo.
echo ===============================================
echo    Test workflow completed!
echo ===============================================
echo.
echo Next steps:
echo 1. Start backend if not running: uv run uvicorn certify_studio.main:app --reload
echo 2. Run full test suite: run_comprehensive_tests.bat
echo 3. Start frontend: cd frontend ^&^& npm run dev
echo.
pause
