# Starting Certify Studio - Enterprise Edition

## UV-Only Approach - No pip, No shortcuts

This project uses **UV exclusively** for dependency management. UV is a modern, fast Python package manager that ensures reproducible builds and enterprise-grade dependency resolution.

## Prerequisites

1. **Python 3.11 or 3.12** installed
2. **UV** package manager installed

### Installing UV

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Unix/Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Starting the Application

### Option 1: Enterprise Launcher (Recommended)

**Windows:**
```batch
start_enterprise.bat
```

**Unix/Linux/macOS:**
```bash
uv run python scripts/uv_enterprise_start.py
```

This will:
- ✅ Validate UV installation
- ✅ Check and install all dependencies via pyproject.toml
- ✅ Fix any configuration issues
- ✅ Create necessary directories
- ✅ Run comprehensive pre-flight checks
- ✅ Start the API with enterprise configuration

### Option 2: Using Dev Tools

```bash
# First time: sync dependencies
uv sync --all-extras

# Run the API
uv run python scripts/dev.py api

# Or directly
cd src
uv run uvicorn certify_studio.api.main:app --reload
```

## Development Commands

All commands use UV exclusively:

```bash
# API Development
uv run python scripts/dev.py api          # Start API in dev mode
uv run python scripts/dev.py api-prod     # Start API in production mode

# Code Quality
uv run python scripts/dev.py format       # Format with black & ruff
uv run python scripts/dev.py lint         # Run linting
uv run python scripts/dev.py type-check   # Type checking with mypy
uv run python scripts/dev.py security     # Security scan with bandit
uv run python scripts/dev.py check-all    # Run all checks

# Testing
uv run python scripts/dev.py test         # Run all tests with coverage
uv run python scripts/dev.py test-unit    # Run unit tests only
uv run python scripts/dev.py test-integration  # Run integration tests
uv run python scripts/dev.py test-e2e     # Run end-to-end tests

# Database
uv run python scripts/dev.py db-migrate   # Run migrations
uv run python scripts/dev.py db-revision  # Create new migration

# Dependencies
uv run python scripts/dev.py deps-install # Sync dependencies
uv run python scripts/dev.py deps-update  # Update all dependencies
```

## NO pip Commands!

This project does **NOT** use pip. All dependency management is through UV:

- ❌ `pip install ...` → ✅ `uv add ...`
- ❌ `pip freeze` → ✅ `uv pip freeze`
- ❌ `requirements.txt` → ✅ `pyproject.toml`
- ❌ `pip install -r requirements.txt` → ✅ `uv sync`

## Access Points

Once running:
- 📚 API Documentation: http://localhost:8000/docs
- 📖 Alternative Docs: http://localhost:8000/redoc
- 💚 Health Check: http://localhost:8000/health
- 📊 Metrics: http://localhost:8000/metrics

## Troubleshooting

### UV not found
Ensure UV is in your PATH after installation. You may need to restart your terminal.

### Dependencies not installing
```bash
# Force reinstall all dependencies
rm -rf .venv
uv venv
uv sync --all-extras
```

### Import errors
Always use UV to run commands:
```bash
# Wrong
python scripts/dev.py api

# Right
uv run python scripts/dev.py api
```

## Enterprise Standards

This setup ensures:
- 🔒 Locked dependencies with UV
- 🚀 Fast, reproducible builds
- 📦 Single source of truth (pyproject.toml)
- 🏢 Enterprise-grade tooling
- ✅ No dependency conflicts

Remember: **UV only. No pip. No shortcuts. Enterprise grade.**
