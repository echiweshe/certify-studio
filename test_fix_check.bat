@echo off
cls
echo Running the test that was failing...
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run python run_tests_diagnostic.py
pause
