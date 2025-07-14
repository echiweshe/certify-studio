#!/usr/bin/env python3
"""Quick test to verify imports are working"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing import chain...")

try:
    print("1. Importing quality assurance models...")
    from certify_studio.agents.specialized.quality_assurance.models import (
        QARequest, QAReportData, QAFeedback, ContinuousMonitoring
    )
    print("✓ QA models imported successfully")
    
    print("\n2. Importing quality router...")
    from certify_studio.api.routers.quality import router as quality_router
    print("✓ Quality router imported successfully")
    
    print("\n3. Importing API main...")
    from certify_studio.api.main import api_router
    print("✓ API main imported successfully")
    
    print("\n4. Importing main app...")
    from certify_studio.main import app
    print("✓ Main app imported successfully")
    
    print("\n✓ All imports successful!")
    
except Exception as e:
    print(f"\n✗ Import failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
