#!/usr/bin/env python3
"""Quick test to see if all imports work"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing imports in order...")
print("-" * 40)

try:
    print("1. Config...")
    from certify_studio.config import settings
    print("   ✓ Config loaded")
    
    print("2. Database...")
    from certify_studio.database import Base
    print("   ✓ Database loaded")
    
    print("3. API main...")
    from certify_studio.api.main import api_router
    print("   ✓ API router loaded")
    
    print("4. Main app...")
    from certify_studio.main import app
    print("   ✓ Main app loaded")
    
    print("\n✓ All imports successful!")
    
    # Test app properties
    print("\nApp info:")
    print(f"  Title: {app.title}")
    print(f"  Version: {app.version}")
    print(f"  Routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
    
except Exception as e:
    print(f"\n✗ Import failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
