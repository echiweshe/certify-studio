@echo off
echo ========================================
echo PostgreSQL Database Setup for Certify Studio
echo ========================================
echo.

REM Adjust path if your PostgreSQL is installed elsewhere
set PGPATH="C:\Program Files\PostgreSQL\16\bin"
set PATH=%PGPATH%;%PATH%

echo Setting up Certify Studio database...
echo.

echo Please enter the postgres superuser password:
psql -U postgres -f setup_certify_studio_db.sql

echo.
echo Testing connection with new user...
psql -U certify_user -d certify_studio -c "SELECT current_database(), current_user, version();"

echo.
echo ========================================
echo Database setup complete!
echo ========================================
pause
