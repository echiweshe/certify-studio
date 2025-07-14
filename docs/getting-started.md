# Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker (for services) or individual installations of:
  - PostgreSQL 15+
  - Redis 7+
  - Neo4j 5+
  - Qdrant

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/certify-studio/certify-studio.git
cd certify-studio
```

### 2. Run setup
```bash
# Windows
setup.bat

# Linux/Mac
./scripts/setup.sh
```

### 3. Configure environment
Copy `.env.example` to `.env` and update with your API keys:
```
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
```

### 4. Start services
```bash
# Start required services (PostgreSQL, Redis, etc.)
run.bat services

# Or use Docker Compose for all services
run.bat docker
```

### 5. Initialize database
```bash
init_db.bat
```

## Running the Application

### Development Server
```bash
run.bat
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Run Tests
```bash
test.bat          # Run unit tests
test.bat all      # Run all tests
test.bat coverage # Run with coverage
```

### Start Workers
In a separate terminal:
```bash
run.bat worker
```

## Project Structure

```
certify-studio/
├── src/              # Source code
├── tests/            # Test suites
├── scripts/          # Utility scripts
├── deployments/      # Docker and K8s configs
├── docs/             # Documentation
├── setup.bat         # Quick setup
├── run.bat          # Run services
├── test.bat         # Run tests
└── init_db.bat      # Initialize database
```

## Next Steps

- Read the [Architecture Overview](architecture.md)
- Explore the [API Reference](api-reference.md)
- Learn about [Agent Development](agents.md)
