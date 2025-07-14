#!/bin/bash
# Production-ready installation script for Certify Studio

set -e  # Exit on error

echo "=== Certify Studio Production Installation ==="
echo

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "ERROR: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version"

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install dependencies
echo "Installing production dependencies..."
uv pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
uv pip install -e ".[dev]"

# Create necessary directories
echo "Creating directory structure..."
mkdir -p uploads exports temp exports/videos
mkdir -p logs data/cache data/embeddings data/knowledge_base data/models

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# Certify Studio Environment Configuration

# Application
APP_NAME="Certify Studio"
APP_VERSION="0.1.0"
DEBUG=true
ENVIRONMENT=development

# Security
SECRET_KEY="your-secret-key-here"
JWT_SECRET_KEY="your-jwt-secret-here"
ENCRYPTION_KEY="your-encryption-key-here"

# Database
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/certify_studio"

# Redis
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"

# AI Services (add your API keys)
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""

# AWS (optional)
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_REGION="us-east-1"

# File Storage
STORAGE_BACKEND="local"
UPLOAD_DIR="./uploads"
EXPORT_DIR="./exports"
TEMP_DIR="./temp"
EOF
    echo "✓ Created .env file - please update with your API keys"
fi

# Initialize database
echo "Setting up database..."
if command -v docker &> /dev/null; then
    echo "Starting PostgreSQL with Docker..."
    docker run -d \
        --name certify-postgres \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=certify_studio \
        -p 5432:5432 \
        postgres:15-alpine 2>/dev/null || echo "PostgreSQL container already exists"
    
    echo "Starting Redis with Docker..."
    docker run -d \
        --name certify-redis \
        -p 6379:6379 \
        redis:7-alpine 2>/dev/null || echo "Redis container already exists"
    
    echo "Starting Neo4j with Docker..."
    docker run -d \
        --name certify-neo4j \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/password \
        neo4j:5-community 2>/dev/null || echo "Neo4j container already exists"
    
    echo "Starting Qdrant with Docker..."
    docker run -d \
        --name certify-qdrant \
        -p 6333:6333 \
        qdrant/qdrant 2>/dev/null || echo "Qdrant container already exists"
    
    echo "Waiting for services to start..."
    sleep 10
else
    echo "WARNING: Docker not found. Please install PostgreSQL, Redis, Neo4j, and Qdrant manually."
fi

# Run database migrations
echo "Running database migrations..."
cd src/certify_studio/database/migrations
alembic upgrade head
cd ../../../..

# Install pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    uv pip install pre-commit
    pre-commit install
fi

echo
echo "=== Installation Complete ==="
echo
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run tests: uv run pytest"
echo "3. Start development server: uv run uvicorn certify_studio.main:app --reload"
echo "4. Start Celery worker: uv run celery -A certify_studio.integration.background worker --loglevel=info"
echo
echo "For production deployment, see docs/deployment.md"
