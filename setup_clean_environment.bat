@echo off
echo ================================================
echo Certify Studio - Clean Setup from GitHub Pull
echo ================================================
echo.
echo Starting fresh from last known working version
echo.

cd /d C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull

echo Step 1: Creating virtual environment...
echo --------------------------------------
uv venv
call .venv\Scripts\activate.bat

echo.
echo Step 2: Installing core dependencies...
echo --------------------------------------
uv pip install --upgrade pip
uv pip install fastapi uvicorn sqlalchemy asyncpg psycopg2-binary alembic
uv pip install pydantic pydantic-settings python-jose passlib python-multipart
uv pip install httpx aiofiles loguru structlog
uv pip install langchain langchain-anthropic langchain-openai langchain-community
uv pip install PyPDF2 networkx markdown
uv pip install pytest pytest-asyncio

echo.
echo Step 3: Copying PostgreSQL configuration...
echo ------------------------------------------
if not exist ".env" (
    copy "C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio\.env" ".env"
    echo ✓ Copied .env with PostgreSQL settings
) else (
    echo ⚠ .env already exists, skipping copy
)

echo.
echo Step 4: Testing imports...
echo -------------------------
python -c "from src.certify_studio.agents.orchestrator import AgenticOrchestrator; print('✓ Orchestrator imports successfully')"
python -c "from src.certify_studio.database.connection import database_manager; print('✓ Database imports successfully')"
python -c "from src.certify_studio.api.main import create_app; print('✓ API imports successfully')"

echo.
echo Step 5: PostgreSQL Status
echo ------------------------
echo Database: certify_studio
echo User: certify_user  
echo Host: localhost:5432
echo.
psql --version

echo.
echo ================================================
echo Setup Complete!
echo.
echo Next steps:
echo 1. Run: start_clean_server.bat
echo 2. Visit: http://localhost:8000/docs
echo ================================================
pause
