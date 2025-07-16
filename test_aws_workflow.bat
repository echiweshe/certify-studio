@echo off
echo =====================================
echo Running AWS AI Practitioner E2E Test
echo =====================================
echo.

REM Activate virtual environment
call uv sync

REM Run the test
echo Starting test...
uv run pytest tests/e2e/test_aws_ai_practitioner_complete.py -v -s

echo.
echo Test completed!
echo Check the outputs directory for generated content.
pause
