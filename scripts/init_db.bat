@echo off
REM Initialize database for Certify Studio

echo === Database Initialization ===
echo.

REM Run migrations
echo Running database migrations...
uv run alembic upgrade head

if errorlevel 1 (
    echo.
    echo ERROR: Failed to run migrations. Make sure:
    echo 1. PostgreSQL is running
    echo 2. Database 'certify_studio' exists
    echo 3. Connection details in .env are correct
    echo.
    pause
    exit /b 1
)

REM Initialize data
echo.
echo Initializing default data...
uv run python src/certify_studio/database/migrations/init_db.py

echo.
echo === Database initialization complete ===
pause
