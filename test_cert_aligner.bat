@echo off
set TF_USE_LEGACY_KERAS=1
uv run pytest tests/unit/test_simple.py -v
pause
