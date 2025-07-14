"""
Test imports within uv environment
Run this with: uv run python test_imports_uv.py
"""

import sys
import os

print("=== Environment Information ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"\nPython path:")
for p in sys.path:
    print(f"  - {p}")

print("\n=== Testing Imports ===")

# Test 1: Core dependencies
print("\n1. Testing core dependencies...")
try:
    import sqlalchemy
    print(f"✓ SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"✗ SQLAlchemy not found: {e}")

try:
    import pydantic
    print(f"✓ Pydantic version: {pydantic.__version__}")
except ImportError as e:
    print(f"✗ Pydantic not found: {e}")

try:
    import pydantic_settings
    print(f"✓ Pydantic Settings imported")
except ImportError as e:
    print(f"✗ Pydantic Settings not found: {e}")

try:
    import fastapi
    print(f"✓ FastAPI version: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ FastAPI not found: {e}")

# Test 2: Langchain packages
print("\n2. Testing langchain packages...")
try:
    import langchain
    print(f"✓ Langchain version: {langchain.__version__}")
except ImportError as e:
    print(f"✗ Langchain not found: {e}")

try:
    import langchain_anthropic
    print(f"✓ Langchain Anthropic imported")
except ImportError as e:
    print(f"✗ Langchain Anthropic not found: {e}")

try:
    import langchain_openai
    print(f"✓ Langchain OpenAI imported")
except ImportError as e:
    print(f"✗ Langchain OpenAI not found: {e}")

try:
    import langchain_core
    print(f"✓ Langchain Core imported")
except ImportError as e:
    print(f"✗ Langchain Core not found: {e}")

try:
    import langchain_community
    print(f"✓ Langchain Community imported")
except ImportError as e:
    print(f"✗ Langchain Community not found: {e}")

# Test 3: Testing tools
print("\n3. Testing dev dependencies...")
try:
    import pytest
    print(f"✓ Pytest version: {pytest.__version__}")
except ImportError as e:
    print(f"✗ Pytest not found: {e}")

# Test 4: Certify Studio imports
print("\n4. Testing Certify Studio imports...")
try:
    from certify_studio.database.models.base import BaseModel
    print("✓ Database models imported")
except ImportError as e:
    print(f"✗ Database models import error: {e}")

try:
    from certify_studio.core.config import Settings
    print("✓ Core config imported")
except ImportError as e:
    print(f"✗ Core config import error: {e}")

try:
    from certify_studio.integration.events import EventBus
    print("✓ Integration module imported")
except ImportError as e:
    print(f"✗ Integration module import error: {e}")

try:
    from certify_studio.api.router import api_router
    print("✓ API router imported")
except ImportError as e:
    print(f"✗ API router import error: {e}")

print("\n=== Import Test Complete ===")
