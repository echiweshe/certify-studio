# Certify Studio Documentation

## Project Structure

```
certify-studio/
├── src/certify_studio/      # Main source code
│   ├── agents/              # AI agents (core, specialized)
│   ├── api/                 # FastAPI application
│   ├── core/                # Core utilities
│   ├── database/            # Database models and repositories
│   ├── knowledge/           # Unified GraphRAG system
│   └── integrations/        # External service integrations
├── tests/                   # Comprehensive test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── e2e/                # End-to-end tests
│   └── fixtures/           # Test data
├── scripts/                 # Development and utility scripts
│   ├── setup.py            # Initial setup script
│   ├── run_tests.py        # Test runner
│   └── dev.py              # Development utilities
├── examples/                # Usage examples
│   └── api_usage.py        # API client example
├── docs/                    # Documentation
│   ├── IMMUTABLE_VISION/   # Core vision (never modify)
│   ├── CONTINUATION.md     # Development progress
│   └── architecture/       # Architecture diagrams
└── deployments/            # Deployment configurations
    ├── docker/             # Docker files
    └── kubernetes/         # K8s manifests
```

## Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/certify-studio/certify-studio.git
cd certify-studio

# Install uv (fast Python package manager)
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment
uv venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings (especially API keys)
notepad .env  # or your preferred editor
```

### 3. Run Setup

```bash
# Run setup script
python scripts/setup.py

# Install spaCy model
python -m spacy download en_core_web_sm
```

### 4. Start API Server

```bash
# Development mode with auto-reload
python scripts/dev.py api

# Or directly with uvicorn
cd src
uvicorn certify_studio.api.main:app --reload
```

### 5. Access API

- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## Development Workflow

### Running Tests

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test types
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --e2e

# Run with coverage
pytest --cov=certify_studio --cov-report=html
```

### Code Quality

```bash
# Format code
python scripts/dev.py format

# Run linting
python scripts/dev.py lint

# Type checking
python scripts/dev.py type-check

# Run all checks
python scripts/dev.py check-all
```

### Using the API

See `examples/api_usage.py` for a complete example:

```python
from examples.api_usage import CertifyStudioClient

async with CertifyStudioClient() as client:
    # Login
    await client.login("user@example.com", "password")
    
    # Upload content
    result = await client.upload_file("guide.pdf")
    
    # Generate course
    generation = await client.generate_content(
        upload_id=result["upload_id"],
        title="My Course",
        cert_type="aws-saa"
    )
```

## Architecture Overview

### Core Components

1. **Multimodal Orchestrator**
   - Coordinates all agents
   - Manages generation workflow
   - Handles progress tracking

2. **Specialized Agents**
   - **Pedagogical Reasoning**: Learning path optimization
   - **Content Generation**: Creates animations, diagrams
   - **Domain Extraction**: Extracts concepts and relationships
   - **Quality Assurance**: Validates content quality

3. **Unified GraphRAG**
   - Neo4j-based knowledge graph
   - Vector search capabilities
   - Integrated educational + troubleshooting

4. **API Layer**
   - RESTful endpoints
   - WebSocket for real-time updates
   - JWT authentication
   - Rate limiting

### Key Features

- 🤖 **4 Specialized AI Agents** with BDI architecture
- 📚 **Multimodal Content** (video, interactive, PDF)
- 🧠 **Cognitive Load Optimization**
- ♿ **WCAG AA Accessibility**
- 📊 **Real-time Quality Monitoring**
- 🔄 **Unified Knowledge System**

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - Create account
- `GET /api/auth/me` - Get current user

### Content Generation
- `POST /api/generation/upload` - Upload content
- `POST /api/generation/generate` - Start generation
- `GET /api/generation/status/{task_id}` - Check progress

### Domain Extraction
- `POST /api/domains/extract` - Extract knowledge
- `GET /api/domains/graph/{id}` - Get knowledge graph
- `POST /api/domains/search` - Search concepts

### Quality Assurance
- `POST /api/quality/check` - Run quality checks
- `POST /api/quality/feedback` - Submit feedback
- `GET /api/quality/benchmarks/{type}` - Get benchmarks

### Export
- `POST /api/export/` - Export content
- `GET /api/export/{id}/download` - Download export
- `GET /api/export/formats` - Available formats

## Configuration

### Required Environment Variables

```env
# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/certify_studio

# AI Services
OPENAI_API_KEY=your-openai-key

# Optional: Neo4j for GraphRAG
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Optional Services

- **Redis**: For caching and rate limiting
- **Neo4j**: For GraphRAG knowledge system
- **PostgreSQL**: For persistent storage

## Deployment

### Docker

```bash
# Build image
docker build -t certify-studio .

# Run container
docker run -p 8000:8000 --env-file .env certify-studio
```

### Kubernetes

See `deployments/kubernetes/` for manifests.

## Troubleshooting

### Common Issues

1. **Import errors**
   ```bash
   # Ensure virtual environment is activated
   # Reinstall in development mode
   uv pip install -e .
   ```

2. **Neo4j connection failed**
   - Neo4j is optional for initial testing
   - Install from https://neo4j.com/download/
   - Or use Docker: `docker run -p 7474:7474 -p 7687:7687 neo4j`

3. **Missing spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Contributing

1. Follow the architecture in `docs/IMMUTABLE_VISION/`
2. Write tests for all new features
3. Maintain >80% test coverage
4. Use type hints throughout
5. Follow the commit conventions

## License

[License information here]

## Support

- Documentation: See `/docs` directory
- Issues: GitHub Issues
- Discussions: GitHub Discussions
