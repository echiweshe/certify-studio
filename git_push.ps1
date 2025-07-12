# Git setup and push script for Certify Studio (PowerShell)

Write-Host "🚀 Certify Studio - Git Setup and Push Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "`n📦 Initializing git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}

# Configure git (optional - update with your details)
Write-Host "`n📝 Git Configuration" -ForegroundColor Yellow
Write-Host "If you haven't configured git, uncomment and update these lines:"
Write-Host "# git config user.name 'Your Name'" -ForegroundColor Gray
Write-Host "# git config user.email 'your.email@example.com'" -ForegroundColor Gray

# Add all files
Write-Host "`n📂 Adding all files to git..." -ForegroundColor Yellow
git add -A
Write-Host "✅ All files added" -ForegroundColor Green

# Show status
Write-Host "`n📊 Git Status:" -ForegroundColor Yellow
git status --short

# Create initial commit
Write-Host "`n💾 Creating initial commit..." -ForegroundColor Yellow
git commit -F COMMIT_MESSAGE.txt
Write-Host "✅ Initial commit created" -ForegroundColor Green

# Add remote (update with your repository URL)
Write-Host "`n🔗 Add your remote repository:" -ForegroundColor Yellow
Write-Host "git remote add origin https://github.com/YOUR_USERNAME/certify-studio.git" -ForegroundColor Cyan
Write-Host "`nOr if using SSH:" -ForegroundColor Yellow
Write-Host "git remote add origin git@github.com:YOUR_USERNAME/certify-studio.git" -ForegroundColor Cyan

# Push instructions
Write-Host "`n📤 To push to GitHub:" -ForegroundColor Yellow
Write-Host "1. Create a new repository on GitHub named 'certify-studio'" -ForegroundColor White
Write-Host "2. Don't initialize it with README, license, or .gitignore" -ForegroundColor White
Write-Host "3. Run: git remote add origin <your-repo-url>" -ForegroundColor White
Write-Host "4. Run: git branch -M main" -ForegroundColor White
Write-Host "5. Run: git push -u origin main" -ForegroundColor White

Write-Host "`n✨ Done! Your code is ready to be pushed to GitHub." -ForegroundColor Green
