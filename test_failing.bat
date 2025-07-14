@echo off
echo Testing specific test that was failing...
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run pytest tests/test_comprehensive.py::TestImports::test_api_imports -v -s
pause
