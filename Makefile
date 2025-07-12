.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  dev          - Start development environment"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean temporary files"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd src && poetry install
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Setting up pre-commit hooks..."
	poetry run pre-commit install

# Development environment
dev:
	@echo "Starting development environment..."
	docker-compose up -d postgres redis
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Running database migrations..."
	cd src && poetry run alembic upgrade head
	@echo "Starting backend..."
	cd src && poetry run uvicorn certify_studio.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend..."
	cd frontend && npm run dev &
	@echo "Development environment started!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

# Testing
test:
	@echo "Running tests..."
	cd src && poetry run pytest tests/ -v --cov=certify_studio --cov-report=html

test-unit:
	@echo "Running unit tests..."
	cd src && poetry run pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	cd src && poetry run pytest tests/integration/ -v

test-e2e:
	@echo "Running e2e tests..."
	cd src && poetry run pytest tests/e2e/ -v

# Code quality
lint:
	@echo "Running linting..."
	cd src && poetry run flake8 certify_studio/
	cd src && poetry run mypy certify_studio/
	cd frontend && npm run lint

format:
	@echo "Formatting code..."
	cd src && poetry run black certify_studio/
	cd src && poetry run isort certify_studio/
	cd frontend && npm run format

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf temp/*
	rm -rf logs/*

# Docker operations
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Database operations
db-migrate:
	@echo "Running database migrations..."
	cd src && poetry run alembic upgrade head

db-revision:
	@echo "Creating new migration..."
	cd src && poetry run alembic revision --autogenerate -m "$(msg)"

db-reset:
	@echo "Resetting database..."
	docker-compose down postgres
	docker volume rm certify-studio_postgres_data
	docker-compose up -d postgres
	sleep 10
	cd src && poetry run alembic upgrade head

# Asset management
download-assets:
	@echo "Downloading cloud provider assets..."
	cd scripts/setup && python download_assets.py

update-icons:
	@echo "Updating provider icons..."
	cd scripts/maintenance && python update_icons.py

# Production deployment
deploy-staging:
	@echo "Deploying to staging..."
	cd scripts/deployment && python deploy_to_aws.py --environment staging

deploy-production:
	@echo "Deploying to production..."
	cd scripts/deployment && python deploy_to_aws.py --environment production

# Security
security-scan:
	@echo "Running security scan..."
	cd src && poetry run safety check
	cd src && poetry run bandit -r certify_studio/

# Documentation
docs-build:
	@echo "Building documentation..."
	cd docs && mkdocs build

docs-serve:
	@echo "Serving documentation..."
	cd docs && mkdocs serve

# Performance testing
perf-test:
	@echo "Running performance tests..."
	cd src && poetry run pytest tests/performance/ -v --benchmark-only

# Monitoring
health-check:
	@echo "Checking application health..."
	curl -f http://localhost:8000/health || exit 1

# Setup for new developers
setup:
	@echo "Setting up development environment for new developer..."
	@make install
	@make download-assets
	@make docker-up
	@make db-migrate
	@echo "Setup complete! Run 'make dev' to start development."
