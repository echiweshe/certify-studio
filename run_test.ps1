# PowerShell test runner
$env:TF_USE_LEGACY_KERAS = "1"
$env:TF_ENABLE_ONEDNN_OPTS = "0"

Write-Host "Running tests with environment variables set..." -ForegroundColor Green
uv run pytest tests/unit/test_simple.py -v
