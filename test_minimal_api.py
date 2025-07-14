#!/usr/bin/env python3
"""Minimal test to check API startup"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("Minimal API Startup Test")
print("=" * 60)
print()

try:
    print("1. Loading config...")
    from certify_studio.config import settings
    print(f"   ✓ Config loaded: {settings.APP_NAME}")
    
    print("\n2. Importing FastAPI app...")
    from certify_studio.main import app
    print(f"   ✓ App imported: {app.title}")
    
    print("\n3. Checking routes...")
    route_count = len([r for r in app.routes if hasattr(r, 'path')])
    print(f"   ✓ Routes registered: {route_count}")
    
    print("\n✓ API can start successfully!")
    
except Exception as e:
    print(f"\n✗ Failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
