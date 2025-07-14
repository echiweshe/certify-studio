@echo off
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
echo Running full test suite...
uv run pytest tests/test_comprehensive.py -v --tb=short
