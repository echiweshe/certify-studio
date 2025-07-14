@echo off
echo ============================================================
echo     Fixing Router Imports and Restarting
echo ============================================================
echo.

echo Fixing router imports...
uv run python scripts/fix_router_imports.py

echo.
echo Starting Certify Studio...
uv run python scripts/uv_enterprise_start.py

pause
