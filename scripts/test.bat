@echo off
REM Test runner for Certify Studio

echo === Certify Studio Test Runner ===
echo.

if "%1"=="" (
    echo Running all unit tests...
    uv run pytest -v -m unit
) else if "%1"=="all" (
    echo Running all tests...
    uv run pytest -v
) else if "%1"=="unit" (
    echo Running unit tests...
    uv run pytest -v -m unit
) else if "%1"=="integration" (
    echo Running integration tests...
    uv run pytest -v -m integration
) else if "%1"=="coverage" (
    echo Running tests with coverage...
    uv run pytest --cov=certify_studio --cov-report=html --cov-report=term
) else if "%1"=="specific" (
    if "%2"=="" (
        echo Error: Please specify a test file
        echo Usage: test.bat specific path/to/test_file.py
        exit /b 1
    )
    echo Running specific test: %2
    uv run pytest -v %2
) else (
    echo Unknown option: %1
    echo.
    echo Usage:
    echo   test.bat          - Run unit tests
    echo   test.bat all      - Run all tests
    echo   test.bat unit     - Run unit tests
    echo   test.bat integration - Run integration tests
    echo   test.bat coverage - Run tests with coverage report
    echo   test.bat specific path/to/test.py - Run specific test file
)

echo.
pause
