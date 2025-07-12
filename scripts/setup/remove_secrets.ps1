# PowerShell script to clean git history and remove secrets

Write-Host "Starting git history cleanup..." -ForegroundColor Green

# Remove file from all commits
Write-Host "Removing file from git history..." -ForegroundColor Yellow
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch '.env copy.example'" --prune-empty --tag-name-filter cat -- --all

# Clean up references
Write-Host "Cleaning up references..." -ForegroundColor Yellow
git for-each-ref --format="%(refname)" refs/original/ | ForEach-Object { git update-ref -d $_ }

# Expire reflog
Write-Host "Expiring reflog..." -ForegroundColor Yellow
git reflog expire --expire=now --all

# Garbage collection
Write-Host "Running garbage collection..." -ForegroundColor Yellow
git gc --prune=now

# Force push
Write-Host "Force pushing to remote..." -ForegroundColor Yellow
git push origin main --force

Write-Host "Done! The file has been removed from git history." -ForegroundColor Green
Write-Host "IMPORTANT: Remember to regenerate your API keys!" -ForegroundColor Red
