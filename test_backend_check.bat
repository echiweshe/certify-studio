@echo off
echo ========================================
echo Quick Backend Connectivity Test
echo ========================================
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

uv run python tests\test_backend_connectivity.py

echo.
pause
