# Certify Studio Complete Setup Guide

## Important: Using PostgreSQL (NOT SQLite)

Your system uses PostgreSQL as the primary database, not SQLite. All configuration is set up for PostgreSQL.

## Current Issues Identified

From the error output, we're missing several key dependencies:
- ✗ loguru (logging library)
- ✗ sqlalchemy (database ORM) 
- ✗ langchain_anthropic (AI framework)
- ✗ Other AI/ML dependencies

## Quick Fix Steps

### 1. Install Dependencies
Run ONE of these options:

**Option A - Batch Script:**
```batch
install_dependencies.bat
```

**Option B - Python Script:**
```batch
python install_deps.py
```

**Option C - Manual with uv:**
```batch
uv pip install sqlalchemy asyncpg psycopg2-binary alembic loguru
uv pip install langchain langchain-anthropic langchain-openai langchain-community
uv pip install PyPDF2 networkx structlog
```

### 2. Setup PostgreSQL Database

**Check if PostgreSQL is installed:**
```batch
psql --version
```

**Create database and user:**
```sql
-- Connect as superuser
psql -U postgres

-- Create user and database
CREATE USER certify_user WITH PASSWORD 'certify_password';
CREATE DATABASE certify_studio OWNER certify_user;
GRANT ALL PRIVILEGES ON DATABASE certify_studio TO certify_user;
\q
```

### 3. Run Complete Setup
```batch
setup_and_run.bat
```

This will:
1. Install dependencies
2. Fix agent architecture
3. Start the application

## Files Created for You

1. **install_deps.py** - Installs all missing dependencies
2. **check_status.py** - Checks what's installed/missing
3. **setup_and_run.bat** - Complete setup and run script
4. **POSTGRESQL_SETUP.md** - Detailed PostgreSQL setup guide
5. **fix_agent_architecture.py** - Fixes the BDI/orchestrator compatibility

## PostgreSQL Connection Details

From your `.env` file:
- **URL**: `postgresql://certify_user:certify_password@localhost:5432/certify_studio`
- **Host**: localhost
- **Port**: 5432
- **Database**: certify_studio
- **User**: certify_user
- **Password**: certify_password

## Architecture Fix Summary

The BDI "improvement" that broke your system has been fixed:
- Original orchestrator preserved
- BDI architecture available but not forced
- All agents work with simple BaseAgent
- No functionality lost

## Quick Commands

**Check status:**
```batch
python check_status.py
```

**Just run the app (if deps installed):**
```batch
uv run python -m certify_studio.main
```

**Access the application:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Next Steps

1. Run `python install_deps.py` to install missing packages
2. Ensure PostgreSQL is running
3. Run `setup_and_run.bat` to start everything

Your sophisticated AI Agent Operating System is ready to be restored!