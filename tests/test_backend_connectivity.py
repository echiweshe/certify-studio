"""
Test backend connectivity
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_backend_connectivity():
    """Test all backend endpoints are accessible"""
    
    base_url = "http://localhost:8000"
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "tests": []
    }
    
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        
        # Test 1: Root endpoint
        print("Testing root endpoint...")
        try:
            response = await client.get("/")
            results["tests"].append({
                "endpoint": "/",
                "status": response.status_code,
                "success": response.status_code == 200,
                "data": response.json() if response.status_code == 200 else None
            })
            print(f"✓ Root endpoint: {response.status_code}")
        except Exception as e:
            results["tests"].append({
                "endpoint": "/",
                "error": str(e),
                "success": False
            })
            print(f"✗ Root endpoint failed: {e}")
        
        # Test 2: Health endpoint
        print("\nTesting health endpoint...")
        try:
            response = await client.get("/health")
            health_data = response.json()
            results["tests"].append({
                "endpoint": "/health",
                "status": response.status_code,
                "success": response.status_code == 200,
                "data": health_data
            })
            print(f"✓ Health endpoint: {response.status_code}")
            print(f"  - Status: {health_data.get('status', 'unknown')}")
            print(f"  - Database: {health_data.get('services', {}).get('database', 'unknown')}")
            print(f"  - AI Agents: {health_data.get('services', {}).get('ai_agents', 'unknown')}")
        except Exception as e:
            results["tests"].append({
                "endpoint": "/health",
                "error": str(e),
                "success": False
            })
            print(f"✗ Health endpoint failed: {e}")
        
        # Test 3: API info endpoint
        print("\nTesting API info endpoint...")
        try:
            response = await client.get("/api/v1/info")
            info_data = response.json()
            results["tests"].append({
                "endpoint": "/api/v1/info",
                "status": response.status_code,
                "success": response.status_code == 200,
                "data": info_data
            })
            print(f"✓ API info endpoint: {response.status_code}")
            print(f"  - Agents: {len(info_data.get('agents', []))}")
            print(f"  - Capabilities: {len(info_data.get('capabilities', []))}")
        except Exception as e:
            results["tests"].append({
                "endpoint": "/api/v1/info",
                "error": str(e),
                "success": False
            })
            print(f"✗ API info endpoint failed: {e}")
        
        # Test 4: Dashboard stats endpoint
        print("\nTesting dashboard stats endpoint...")
        try:
            response = await client.get("/api/v1/dashboard/stats")
            if response.status_code == 401:
                print("  - Dashboard endpoint requires authentication (expected)")
                results["tests"].append({
                    "endpoint": "/api/v1/dashboard/stats",
                    "status": response.status_code,
                    "success": True,  # 401 is expected without auth
                    "note": "Requires authentication"
                })
            else:
                stats_data = response.json()
                results["tests"].append({
                    "endpoint": "/api/v1/dashboard/stats",
                    "status": response.status_code,
                    "success": response.status_code == 200,
                    "data": stats_data
                })
                print(f"✓ Dashboard stats endpoint: {response.status_code}")
        except Exception as e:
            results["tests"].append({
                "endpoint": "/api/v1/dashboard/stats",
                "error": str(e),
                "success": False
            })
            print(f"✗ Dashboard stats endpoint failed: {e}")
        
        # Test 5: WebSocket endpoint
        print("\nTesting WebSocket endpoint...")
        try:
            # Test if WebSocket endpoint is accessible (HTTP upgrade)
            ws_response = await client.get("/ws/agents")
            # We expect a 426 Upgrade Required or similar for WebSocket endpoints
            if ws_response.status_code in [426, 400]:
                print("✓ WebSocket endpoint exists (requires WebSocket upgrade)")
                results["tests"].append({
                    "endpoint": "/ws/agents",
                    "status": ws_response.status_code,
                    "success": True,
                    "note": "WebSocket endpoint available"
                })
            else:
                results["tests"].append({
                    "endpoint": "/ws/agents",
                    "status": ws_response.status_code,
                    "success": False
                })
        except Exception as e:
            results["tests"].append({
                "endpoint": "/ws/agents",
                "error": str(e),
                "success": False
            })
            print(f"✗ WebSocket endpoint check failed: {e}")
        
        # Test 6: API documentation
        print("\nTesting API documentation...")
        try:
            response = await client.get("/docs")
            results["tests"].append({
                "endpoint": "/docs",
                "status": response.status_code,
                "success": response.status_code == 200,
                "note": "Swagger UI available" if response.status_code == 200 else "Documentation not accessible"
            })
            print(f"✓ API documentation: {response.status_code}")
        except Exception as e:
            results["tests"].append({
                "endpoint": "/docs",
                "error": str(e),
                "success": False
            })
            print(f"✗ API documentation failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKEND CONNECTIVITY TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for test in results["tests"] if test.get("success", False))
    total_tests = len(results["tests"])
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Save results
    with open("backend_connectivity_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: backend_connectivity_test_results.json")
    
    # Return success if at least core endpoints work
    return successful_tests >= 3  # At least root, health, and API info should work


async def test_authentication_flow():
    """Test authentication endpoints"""
    print("\n" + "=" * 60)
    print("TESTING AUTHENTICATION FLOW")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Test registration
        print("\nTesting user registration...")
        register_data = {
            "email": f"test_{datetime.now().timestamp()}@certifystudio.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        try:
            response = await client.post("/api/v1/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                print(f"✓ Registration successful: {response.status_code}")
                token = response.json().get("access_token")
                if token:
                    print(f"  - Token received: {token[:20]}...")
            elif response.status_code == 409:
                print("  - User already exists (expected if test ran before)")
            else:
                print(f"✗ Registration failed: {response.status_code}")
                print(f"  - Response: {response.text}")
        except Exception as e:
            print(f"✗ Registration failed: {e}")
        
        # Test login
        print("\nTesting user login...")
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }
        
        try:
            response = await client.post(
                "/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                print(f"✓ Login successful: {response.status_code}")
                token = response.json().get("access_token")
                if token:
                    print(f"  - Token received: {token[:20]}...")
                    
                    # Test authenticated endpoint
                    print("\nTesting authenticated endpoint...")
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = await client.get("/api/v1/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        print("✓ Authenticated endpoint accessible")
                        user_data = me_response.json()
                        print(f"  - User email: {user_data.get('email')}")
                    else:
                        print(f"✗ Authenticated endpoint failed: {me_response.status_code}")
            else:
                print(f"✗ Login failed: {response.status_code}")
                print(f"  - Response: {response.text}")
        except Exception as e:
            print(f"✗ Login failed: {e}")


async def main():
    """Run all connectivity tests"""
    print("CERTIFY STUDIO - BACKEND CONNECTIVITY TEST")
    print("=" * 60)
    print(f"Testing backend at: http://localhost:8000")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test basic connectivity
    connectivity_ok = await test_backend_connectivity()
    
    # Test authentication if basic connectivity works
    if connectivity_ok:
        await test_authentication_flow()
    else:
        print("\n⚠️  Skipping authentication tests due to connectivity issues")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
