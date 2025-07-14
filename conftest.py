"""
Test configuration for Certify Studio.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/certify_studio_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use different Redis DB for tests

# Test configuration
pytest_plugins = [
    "pytest_asyncio",
]
