#!/usr/bin/env python3
"""
Comprehensive test runner with detailed diagnostics
"""

import pytest
import sys
from pathlib import Path
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_tests():
    """Run tests with detailed output"""
    print("=" * 60)
    print("Certify Studio Test Suite - Detailed Diagnostics")
    print("=" * 60)
    print()
    
    # First, test imports directly
    print("Pre-test Import Verification:")
    print("-" * 40)
    
    try:
        print("1. Testing config import...")
        from certify_studio.config import settings
        print(f"   ✓ Config loaded: {settings.APP_NAME}")
    except Exception as e:
        print(f"   ✗ Config import failed: {e}")
        traceback.print_exc()
        return 1
    
    try:
        print("2. Testing database import...")
        from certify_studio.database import Base
        print("   ✓ Database models loaded")
    except Exception as e:
        print(f"   ✗ Database import failed: {e}")
        traceback.print_exc()
        return 1
    
    try:
        print("3. Testing agent imports...")
        from certify_studio.agents import MultimodalOrchestrator
        print("   ✓ Agents loaded")
    except Exception as e:
        print(f"   ✗ Agent import failed: {e}")
        traceback.print_exc()
        return 1
    
    try:
        print("4. Testing API imports...")
        from certify_studio.api.main import api_router
        print("   ✓ API loaded successfully")
    except Exception as e:
        print(f"   ✗ API import failed: {e}")
        traceback.print_exc()
        return 1
    
    print()
    print("Running pytest suite...")
    print("-" * 40)
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        "tests/test_comprehensive.py",
        "-v",
        "-s",
        "--tb=short",
        "--no-header"
    ])
    
    print()
    print("=" * 60)
    if exit_code == 0:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(run_tests())
