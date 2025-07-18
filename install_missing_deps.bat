@echo off
echo Installing Missing Dependencies...
echo ==================================

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Installing missing packages...
echo -----------------------------

echo Installing PIL (Pillow)...
uv pip install Pillow

echo Installing Redis...
uv pip install redis aioredis

echo Installing other potentially missing packages...
uv pip install python-dotenv
uv pip install prometheus-client
uv pip install emails

echo.
echo Testing imports again...
echo -----------------------
python -c "from PIL import Image; print('✓ PIL (Pillow) working')"
python -c "import redis; print('✓ Redis module working')"
python -c "from src.certify_studio.agents.orchestrator import AgenticOrchestrator; print('✓ Orchestrator imports successfully')"
python -c "from src.certify_studio.api.main import create_app; print('✓ API imports successfully')"

echo.
echo Done! You can now run: start_clean_server.bat
pause
