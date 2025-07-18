@echo off
echo Initializing Database with Admin User...
echo ========================================

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Running database migrations...
set PYTHONPATH=%cd%\src
alembic upgrade head

echo.
echo Creating admin user and roles...
python src\certify_studio\database\migrations\init_db.py

echo.
echo ========================================
echo Database initialized!
echo.
echo Login credentials:
echo   Email: admin@certifystudio.com
echo   Password: admin123
echo.
echo ⚠️  IMPORTANT: Change the admin password after first login!
echo ========================================
pause
