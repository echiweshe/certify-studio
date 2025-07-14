@echo off
REM Quick setup script for Certify Studio development

echo === Certify Studio Quick Setup ===
echo.

REM Step 1: Clean up old environments
echo Step 1: Cleaning up old environments...
if exist venv rmdir /s /q venv 2>nul
if exist .venv rmdir /s /q .venv 2>nul

REM Step 2: Create fresh virtual environment
echo Step 2: Creating virtual environment...
uv venv

REM Step 3: Install dependencies
echo Step 3: Installing dependencies...
uv pip sync requirements.txt requirements-test.txt 2>nul || (
    echo requirements-test.txt not found, installing from requirements.txt only
    uv pip sync requirements.txt
)

REM Step 4: Install project in editable mode
echo Step 4: Installing project...
uv pip install -e .

REM Step 5: Run database migrations
echo Step 5: Running database migrations...
uv run alembic upgrade head 2>nul || (
    echo Note: Database migrations failed - make sure PostgreSQL is running
)

echo.
echo === Setup Complete ===
echo.
echo To run tests: uv run pytest -v -m unit
echo To start server: uv run uvicorn certify_studio.main:app --reload
echo.
pause
