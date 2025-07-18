@echo off
echo Quick Database Setup
echo ====================

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Setting up database...
set PYTHONPATH=%cd%\src
python quick_db_setup.py

echo.
echo Done!
pause
