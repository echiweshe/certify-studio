#!/usr/bin/env python3
"""Step by step import test to identify issues"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Step-by-step import test...")
print("=" * 50)

try:
    print("1. Testing config import...")
    from certify_studio.config import get_settings
    settings = get_settings()
    print(f"   ✓ Settings loaded: {settings.APP_NAME}")
except Exception as e:
    print(f"   ✗ Config failed: {e}")
    sys.exit(1)

try:
    print("\n2. Testing database connection import...")
    from certify_studio.database.connection import database_manager
    print("   ✓ Database manager imported")
except Exception as e:
    print(f"   ✗ Database connection failed: {e}")
    sys.exit(1)

try:
    print("\n3. Testing observability imports...")
    from certify_studio.integrations.observability.logging import setup_logging
    from certify_studio.integrations.observability.metrics import setup_metrics
    print("   ✓ Observability modules imported")
except Exception as e:
    print(f"   ✗ Observability failed: {e}")
    sys.exit(1)

try:
    print("\n4. Testing API router import...")
    from certify_studio.api.main import api_router
    print("   ✓ API router imported")
except Exception as e:
    print(f"   ✗ API router failed: {e}")
    sys.exit(1)

try:
    print("\n5. Testing middleware imports...")
    from certify_studio.api.middleware import (
        LoggingMiddleware,
        RateLimitMiddleware,
        SecurityHeadersMiddleware
    )
    print("   ✓ Middleware classes imported")
except Exception as e:
    print(f"   ✗ Middleware failed: {e}")
    sys.exit(1)

try:
    print("\n6. Testing main app import...")
    from certify_studio.main import app
    print("   ✓ Main app imported successfully!")
    print(f"\n   App title: {app.title}")
    print(f"   App version: {app.version}")
except Exception as e:
    print(f"   ✗ Main app failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✓ All imports successful! The API is ready to run.")
print("=" * 50)
