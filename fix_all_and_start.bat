@echo off
echo ============================================================
echo     Comprehensive Import Fix & Restart
echo ============================================================
echo.

echo Fixing all imports...
uv run python scripts/fix_all_imports.py

echo.
echo Starting Certify Studio...
uv run python scripts/uv_enterprise_start.py

pause
