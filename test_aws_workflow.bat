@echo off
echo ========================================
echo Running AWS AI Practitioner Workflow Test
echo ========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Checking backend connectivity...
uv run python tests\test_backend_connectivity.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Backend is not running!
    echo Please start the backend first:
    echo   uv run uvicorn certify_studio.main:app --reload
    echo.
    pause
    exit /b 1
)

echo.
echo Running AWS AI Practitioner E2E Test...
echo This will test the complete workflow with real AWS materials.
echo.

uv run pytest tests\e2e\test_aws_ai_practitioner_complete.py -v -s

echo.
echo ========================================
echo Test Complete!
echo Check tests\outputs\aws-ai-practitioner\ for generated content
echo ========================================
pause
