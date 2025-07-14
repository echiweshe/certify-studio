@echo off
REM Run Certify Studio services

if "%1"=="" goto :dev
if "%1"=="dev" goto :dev
if "%1"=="docker" goto :docker
if "%1"=="worker" goto :worker
if "%1"=="services" goto :services
goto :help

:dev
echo Starting development server...
uv run uvicorn certify_studio.main:app --reload
goto :end

:docker
echo Starting all services with Docker Compose...
cd deployments
docker-compose up -d
cd ..
echo.
echo Services started. Access the API at http://localhost:8000
echo Flower (Celery monitoring) at http://localhost:5555
goto :end

:worker
echo Starting Celery worker...
uv run celery -A certify_studio.integration.background worker --loglevel=info
goto :end

:services
echo Starting required services with Docker...
docker run -d --name certify-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=certify_studio -p 5432:5432 postgres:15-alpine 2>nul || echo PostgreSQL already running
docker run -d --name certify-redis -p 6379:6379 redis:7-alpine 2>nul || echo Redis already running
docker run -d --name certify-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community 2>nul || echo Neo4j already running
docker run -d --name certify-qdrant -p 6333:6333 qdrant/qdrant 2>nul || echo Qdrant already running
echo Services started.
goto :end

:help
echo Usage:
echo   run.bat         - Start development server
echo   run.bat dev     - Start development server
echo   run.bat docker  - Start all services with Docker Compose
echo   run.bat worker  - Start Celery worker
echo   run.bat services - Start required services (PostgreSQL, Redis, etc.)
goto :end

:end
