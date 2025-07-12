@echo off
echo Adding all files...
git add -A

echo.
echo Git status:
git status --short

echo.
echo Creating commit...
git commit -F COMMIT_MESSAGE.txt

echo.
echo Commit created successfully!
echo.
echo To push to your repository:
echo 1. git remote add origin ^<your-repo-url^> (if not already added)
echo 2. git push origin main
