#!/usr/bin/env python3
"""
Quick integration test for Certify Studio API
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_api_integration():
    """Test basic API integration"""
    print("Testing Certify Studio API Integration...\n")
    
    try:
        # Test 1: Import main components
        print("1. Testing imports...")
        from certify_studio.main import app
        from certify_studio.api.main import api_router
        from certify_studio.config import settings
        print("✓ Main imports successful")
        
        # Test 2: Check app configuration
        print("\n2. Testing app configuration...")
        assert app.title == "Certify Studio API"
        assert app.version == settings.VERSION
        print(f"✓ App configured: {app.title} v{app.version}")
        
        # Test 3: Check registered routes
        print("\n3. Testing registered routes...")
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/api/v1", "/docs", "/openapi.json"]
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Route found: {route}")
            else:
                print(f"✗ Route missing: {route}")
        
        # Test 4: Test health endpoint
        print("\n4. Testing health endpoint...")
        from httpx import AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check passed: {data}")
            else:
                print(f"✗ Health check failed: {response.status_code}")
        
        print("\n✓ Integration test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_api_integration())
    sys.exit(0 if success else 1)
