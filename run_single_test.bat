@echo off
cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio
uv run pytest tests/test_comprehensive.py::TestImports::test_api_imports -v -s
