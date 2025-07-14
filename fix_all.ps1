# PowerShell script to fix dependencies and run tests

Write-Host "=== Fixing All Dependencies ===" -ForegroundColor Green

# Set environment variables
Write-Host "`n1. Setting environment variables..." -ForegroundColor Yellow
$env:TF_USE_LEGACY_KERAS = "1"
$env:TF_ENABLE_ONEDNN_OPTS = "0"

# Install tf-keras
Write-Host "`n2. Installing tf-keras..." -ForegroundColor Yellow
uv add tf-keras

# Install other missing packages
Write-Host "`n3. Installing other missing packages..." -ForegroundColor Yellow
$packages = @("markdown", "pyyaml", "beautifulsoup4", "lxml", "html2text")
foreach ($package in $packages) {
    Write-Host "   Installing $package..." -ForegroundColor Cyan
    uv add $package
}

# Sync dependencies
Write-Host "`n4. Syncing dependencies..." -ForegroundColor Yellow
uv sync

# Run tests
Write-Host "`n5. Running tests..." -ForegroundColor Yellow
uv run pytest tests/unit/test_simple.py -v

Write-Host "`n=== Complete ===" -ForegroundColor Green
