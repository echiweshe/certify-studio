@echo off
echo ========================================
echo CERTIFY STUDIO - DATABASE INITIALIZATION
echo ========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Installing database dependencies...
uv pip install aiosqlite

echo.
echo Initializing database...
uv run python init_database.py

echo.
echo ========================================
echo Database initialization complete!
echo ========================================
pause
