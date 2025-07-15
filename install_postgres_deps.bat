@echo off
echo Installing PostgreSQL dependencies...
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Installing asyncpg for PostgreSQL support...
uv pip install asyncpg

echo.
echo Dependencies installed!
pause
