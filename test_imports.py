#!/usr/bin/env python3
"""Test problematic imports directly"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__) / "src"))

print("Testing imports...")

try:
    print("1. Testing dependencies import...")
    from certify_studio.api.dependencies import get_current_verified_user, get_db
    print("✓ Dependencies imported successfully")
except Exception as e:
    print(f"✗ Dependencies import failed: {e}")

try:
    print("\n2. Testing user schema import...")
    from certify_studio.api.schemas.user import User
    print("✓ User schema imported successfully")
except Exception as e:
    print(f"✗ User schema import failed: {e}")

try:
    print("\n3. Testing routers import...")
    from certify_studio.api.routers import domains_router
    print("✓ Domains router imported successfully")
except Exception as e:
    print(f"✗ Domains router import failed: {e}")

try:
    print("\n4. Testing main API import...")
    from certify_studio.api.main import api_router
    print("✓ API router imported successfully")
except Exception as e:
    print(f"✗ API router import failed: {e}")

print("\nDone!")
