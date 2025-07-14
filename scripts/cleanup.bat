@echo off
REM Cleanup script for Certify Studio

echo === Certify Studio Cleanup ===
echo.

echo This will remove:
echo - Virtual environments (.venv, venv)
echo - Python cache files (__pycache__)
echo - Test coverage reports
echo - Temporary files
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Cleaning up...

REM Remove virtual environments
if exist .venv (
    echo Removing .venv...
    rmdir /s /q .venv
)
if exist venv (
    echo Removing venv...
    rmdir /s /q venv
)

REM Remove Python cache files
echo Removing Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"
for /r . %%f in (*.pyo) do @if exist "%%f" del "%%f"

REM Remove coverage reports
if exist .coverage del .coverage
if exist htmlcov rmdir /s /q htmlcov
if exist coverage.xml del coverage.xml

REM Remove pytest cache
if exist .pytest_cache rmdir /s /q .pytest_cache

REM Remove egg-info
for /d %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo Cleanup complete!
echo.
echo To reinstall, run: setup.bat
pause
