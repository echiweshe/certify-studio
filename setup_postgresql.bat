@echo off
echo ========================================
echo PostgreSQL Setup for Certify Studio
echo ========================================
echo.

REM Set PostgreSQL bin path (adjust version if needed)
set PGPATH="C:\Program Files\PostgreSQL\15\bin"
set PATH=%PGPATH%;%PATH%

echo 1. Creating database and user...
echo.

REM Create a SQL script for setup
echo CREATE DATABASE certify_studio; > setup_db.sql
echo CREATE USER certify_user WITH ENCRYPTED PASSWORD 'CertifyStudio2024!'; >> setup_db.sql
echo GRANT ALL PRIVILEGES ON DATABASE certify_studio TO certify_user; >> setup_db.sql
echo \c certify_studio >> setup_db.sql
echo GRANT ALL ON SCHEMA public TO certify_user; >> setup_db.sql
echo ALTER DATABASE certify_studio OWNER TO certify_user; >> setup_db.sql

echo Please enter the postgres superuser password (from installation):
psql -U postgres -f setup_db.sql

echo.
echo 2. Testing connection...
psql -U certify_user -d certify_studio -c "SELECT version();"

echo.
echo ========================================
echo PostgreSQL setup complete!
echo.
echo Database: certify_studio
echo User: certify_user
echo Password: CertifyStudio2024!
echo ========================================
echo.
echo Next step: Update your .env file with:
echo DATABASE_URL=postgresql+asyncpg://certify_user:CertifyStudio2024!@localhost:5432/certify_studio
echo.
pause

REM Clean up
del setup_db.sql
