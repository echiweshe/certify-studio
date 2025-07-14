@echo off
cls
echo Running import test after fixes...
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run python run_tests_diagnostic.py
