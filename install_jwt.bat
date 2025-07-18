@echo off
echo Installing PyJWT...
cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

call .venv\Scripts\activate.bat

uv pip install PyJWT

echo Done!
pause
