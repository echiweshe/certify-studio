# Dependency Management Guide for Certify Studio

## Overview

Certify Studio uses **UV** as its primary dependency management tool. UV is a modern, fast Python package manager that provides better dependency resolution and reproducible builds compared to traditional pip.

## Quick Start

```bash
# First time setup
python scripts/quickstart.py

# Or if you want more control
python scripts/launch.py --mode dev
```

## Dependency Management Strategy

### 1. **UV + pyproject.toml (Primary)**
- **Purpose**: Modern dependency management with lock file support
- **File**: `pyproject.toml` - Source of truth for all dependencies
- **Lock**: UV automatically creates lock files for reproducible builds
- **Usage**: All development and deployment

### 2. **requirements.txt (Secondary)**
- **Purpose**: Compatibility with Docker, legacy systems, and some cloud providers
- **File**: `requirements.txt` - Generated from UV environment
- **Usage**: Docker builds, legacy deployments

## Why UV Instead of pip/requirements.txt?

1. **Faster**: 10-100x faster than pip
2. **Deterministic**: Lock files ensure exact same versions everywhere
3. **Better Resolution**: Smarter dependency conflict resolution
4. **Modern**: Follows latest Python packaging standards (PEP 517/518)
5. **Integrated**: Works seamlessly with pyproject.toml

## Common Commands

### Using UV

```bash
# Install UV (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Create virtual environment
uv venv

# Sync all dependencies from pyproject.toml
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Generate requirements.txt (if needed)
uv pip freeze > requirements.txt
```

### Development Workflow

```bash
# 1. First time setup
python scripts/setup_dependencies.py

# 2. Activate virtual environment
source .venv/bin/activate  # Unix
# or
.venv\Scripts\activate  # Windows

# 3. Run development server
python scripts/dev.py api

# 4. Run tests
python scripts/run_tests.py

# 5. Format code
python scripts/dev.py format

# 6. Run all checks
python scripts/dev.py check-all
```

## Dependency Organization

### Core Dependencies (pyproject.toml)
- **Framework**: FastAPI, Uvicorn, Pydantic
- **Database**: SQLAlchemy, AsyncPG, Alembic
- **AI/ML**: OpenAI, Anthropic, LangChain, Transformers
- **Caching**: Redis
- **Processing**: Document parsers, NLP tools

### Optional Dependencies
- **dev**: Testing, linting, formatting tools
- **aws**: AWS SDK and tools
- **azure**: Azure SDK and tools
- **gcp**: Google Cloud SDK and tools

## Docker Compatibility

When building Docker images, UV is used internally but requirements.txt is generated for the final image:

```dockerfile
# Build stage with UV
FROM python:3.11 as builder
RUN pip install uv
COPY pyproject.toml .
RUN uv sync
RUN uv pip freeze > requirements.txt

# Final stage with pip
FROM python:3.11-slim
COPY --from=builder requirements.txt .
RUN pip install -r requirements.txt
```

## Troubleshooting

### UV Not Found
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Add to PATH if needed
export PATH="$HOME/.cargo/bin:$PATH"
```

### Dependencies Not Installing
```bash
# Clean install
rm -rf .venv
uv venv
uv sync --all-extras
```

### Import Errors
```bash
# Ensure virtual environment is activated
which python  # Should show .venv/bin/python
# Reinstall
uv sync --reinstall
```

## Best Practices

1. **Always use UV** for adding/removing dependencies
2. **Commit pyproject.toml** changes, not requirements.txt
3. **Use virtual environments** for isolation
4. **Run tests** after dependency updates
5. **Keep dependencies minimal** - use optional groups

## Migration from requirements.txt

If you have an existing requirements.txt:

```bash
# Import into UV
uv pip install -r requirements.txt

# Then generate pyproject.toml entries
# (Manual step - review and add to pyproject.toml)
```

## Conclusion

UV provides a modern, fast, and reliable dependency management solution for Certify Studio. By using UV with pyproject.toml, we ensure consistent environments across development, testing, and production while maintaining compatibility with legacy systems through generated requirements.txt files when needed.
