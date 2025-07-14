@echo off
cls
echo Testing imports after middleware fix...
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run python test_all_imports.py
pause
