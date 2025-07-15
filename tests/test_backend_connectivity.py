"""
Quick backend connectivity test
"""

import requests
import json
from datetime import datetime

def test_backend_connectivity():
    """Test if backend is accessible"""
    print("Testing Backend Connectivity...")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Root endpoint
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✓ Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False
    
    # Test 2: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"\n✓ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Version: {data.get('version', 'unknown')}")
            print(f"  Services: {json.dumps(data.get('services', {}), indent=2)}")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
        return False
    
    # Test 3: API info
    try:
        response = requests.get(f"{base_url}/api/v1/info", timeout=5)
        print(f"\n✓ API Info endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Platform: {data.get('platform', {}).get('name', 'unknown')}")
            print(f"  Agents: {data.get('agents', {}).get('status', 'unknown')}")
    except Exception as e:
        print(f"✗ API Info endpoint failed: {e}")
        
    # Test 4: API documentation
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"\n✓ API Documentation: {response.status_code}")
        print(f"  Swagger UI available at: {base_url}/docs")
        print(f"  ReDoc available at: {base_url}/redoc")
    except Exception as e:
        print(f"✗ API Documentation failed: {e}")
    
    print("\n" + "=" * 50)
    print("Backend connectivity test completed!")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True


if __name__ == "__main__":
    success = test_backend_connectivity()
    if not success:
        print("\n⚠️  Backend is not running!")
        print("Please start the backend with:")
        print("  uv run uvicorn certify_studio.main:app --reload")
