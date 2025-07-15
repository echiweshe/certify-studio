@echo off
echo Installing PostgreSQL Python dependencies...
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Installing asyncpg for async PostgreSQL support...
uv pip install asyncpg psycopg2-binary

echo.
echo ✅ Dependencies installed!
echo.

echo Testing database connection...
uv run python diagnose_database.py

pause
