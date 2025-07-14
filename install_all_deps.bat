@echo off
REM Complete dependency installation for Certify Studio

echo === Installing All Missing Dependencies ===
echo.

echo Installing markdown and related packages...
call uv add markdown beautifulsoup4 lxml html2text pyyaml

echo.
echo Checking for any other missing packages...
call uv add markdownify xmltodict

echo.
echo Syncing all dependencies...
call uv sync

echo.
echo Running tests...
call uv run pytest tests/unit/test_simple.py -v

echo.
echo === Installation Complete ===
pause
