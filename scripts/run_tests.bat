@echo off
echo Running Certify Studio Tests...
echo.

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using global Python
)

REM Run pytest with verbose output
echo Running unit tests...
python -m pytest tests/unit/test_basic.py -v --tb=short

echo.
echo Tests completed.
pause
