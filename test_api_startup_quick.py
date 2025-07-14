#!/usr/bin/env python3
"""Test API startup without running full server"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing API startup...")
print("-" * 40)

try:
    print("1. Importing app...")
    from certify_studio.main import app
    print("✓ App imported successfully")
    
    print("\n2. Checking app configuration...")
    print(f"   Title: {app.title}")
    print(f"   Version: {app.version}")
    print(f"   Debug: {app.debug}")
    
    print("\n3. Listing registered routes...")
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
    
    print(f"   Total routes: {len(routes)}")
    print("   Key routes:")
    for route in ["/health", "/api/v1/auth/login", "/api/v1/generation/start", "/api/v1/quality/check"]:
        if any(route in r for r in routes):
            print(f"   ✓ {route}")
        else:
            print(f"   ✗ {route} (missing)")
    
    print("\n✓ API startup test passed!")
    
except Exception as e:
    print(f"\n✗ API startup failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
