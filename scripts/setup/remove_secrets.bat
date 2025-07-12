@echo off
REM Script to remove secrets from git history using git filter-branch

cd C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio

echo Removing file from git history...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch '.env copy.example'" --prune-empty --tag-name-filter cat -- --all

echo Cleaning up...
FOR /F "tokens=*" %%G IN ('git for-each-ref --format="%(refname)" refs/original/') DO git update-ref -d %%G

git reflog expire --expire=now --all
git gc --prune=now

echo Force pushing to remote...
git push origin main --force

echo Done! The file has been removed from git history.
pause
