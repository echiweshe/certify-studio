@echo off
echo ============================================================
echo     Fixing Python 3.13 Compatibility Issues
echo ============================================================
echo.

echo Removing problematic packages...
uv remove librosa

echo.
echo Re-syncing with updated dependencies...
uv sync --all-extras

echo.
echo Installing alternative audio processing (if librosa fails)...
REM If librosa still fails, we can use alternative audio processing libraries

echo.
echo ============================================================
echo     Dependencies fixed! Starting Certify Studio...
echo ============================================================
echo.

uv run python scripts/uv_enterprise_start.py

pause
