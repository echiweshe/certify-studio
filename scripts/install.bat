@echo off
REM Production-ready installation script for Certify Studio (Windows)

echo === Certify Studio Production Installation ===
echo.

REM Check Python version
echo Checking Python version...
python --version 2>&1 | findstr /R "3\.1[1-9]" >nul
if errorlevel 1 (
    echo ERROR: Python 3.11 or higher is required.
    exit /b 1
)
echo Python version OK

REM Install uv if not already installed
where uv >nul 2>nul
if errorlevel 1 (
    echo Installing uv package manager...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv
)

REM Install dependencies
echo Installing production dependencies...
uv pip install -e .

REM Install development dependencies  
echo Installing development dependencies...
uv pip install -e ".[dev]"

REM Create necessary directories
echo Creating directory structure...
if not exist "uploads" mkdir uploads
if not exist "exports" mkdir exports
if not exist "exports\videos" mkdir exports\videos
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "data\cache" mkdir data\cache
if not exist "data\embeddings" mkdir data\embeddings
if not exist "data\knowledge_base" mkdir data\knowledge_base
if not exist "data\models" mkdir data\models

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    (
        echo # Certify Studio Environment Configuration
        echo.
        echo # Application
        echo APP_NAME="Certify Studio"
        echo APP_VERSION="0.1.0"
        echo DEBUG=true
        echo ENVIRONMENT=development
        echo.
        echo # Security
        echo SECRET_KEY="your-secret-key-here"
        echo JWT_SECRET_KEY="your-jwt-secret-here" 
        echo ENCRYPTION_KEY="your-encryption-key-here"
        echo.
        echo # Database
        echo DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/certify_studio"
        echo.
        echo # Redis
        echo REDIS_URL="redis://localhost:6379/0"
        echo CELERY_BROKER_URL="redis://localhost:6379/1"
        echo CELERY_RESULT_BACKEND="redis://localhost:6379/2"
        echo.
        echo # AI Services ^(add your API keys^)
        echo OPENAI_API_KEY=""
        echo ANTHROPIC_API_KEY=""
        echo.
        echo # AWS ^(optional^)
        echo AWS_ACCESS_KEY_ID=""
        echo AWS_SECRET_ACCESS_KEY=""
        echo AWS_REGION="us-east-1"
        echo.
        echo # File Storage
        echo STORAGE_BACKEND="local"
        echo UPLOAD_DIR="./uploads"
        echo EXPORT_DIR="./exports"
        echo TEMP_DIR="./temp"
    ) > .env
    echo Created .env file - please update with your API keys
)

REM Check for Docker and start services
where docker >nul 2>nul
if errorlevel 1 (
    echo WARNING: Docker not found. Please install PostgreSQL, Redis, Neo4j, and Qdrant manually.
    echo.
    echo You can download Docker Desktop from: https://www.docker.com/products/docker-desktop/
) else (
    echo Starting PostgreSQL with Docker...
    docker run -d --name certify-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=certify_studio -p 5432:5432 postgres:15-alpine 2>nul || echo PostgreSQL container already exists
    
    echo Starting Redis with Docker...
    docker run -d --name certify-redis -p 6379:6379 redis:7-alpine 2>nul || echo Redis container already exists
    
    echo Starting Neo4j with Docker...
    docker run -d --name certify-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community 2>nul || echo Neo4j container already exists
    
    echo Starting Qdrant with Docker...
    docker run -d --name certify-qdrant -p 6333:6333 qdrant/qdrant 2>nul || echo Qdrant container already exists
    
    echo Waiting for services to start...
    timeout /t 10 /nobreak >nul
)

REM Run database migrations
echo Running database migrations...
uv run alembic upgrade head

echo.
echo === Installation Complete ===
echo.
echo Next steps:
echo 1. Update .env file with your API keys
echo 2. Run tests: uv run pytest
echo 3. Start development server: uv run uvicorn certify_studio.main:app --reload
echo 4. Start Celery worker: uv run celery -A certify_studio.integration.background worker --loglevel=info
echo.
echo For production deployment, see docs\deployment.md
pause
