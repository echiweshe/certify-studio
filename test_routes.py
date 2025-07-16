"""
Quick test to list all available routes in the FastAPI app
"""

import asyncio
import httpx
from pprint import pprint


async def test_available_routes():
    """Test what routes are actually available"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Get OpenAPI schema to see all routes
        try:
            response = await client.get("/openapi.json")
            if response.status_code == 200:
                openapi = response.json()
                print("Available paths from OpenAPI:")
                for path in sorted(openapi.get("paths", {}).keys()):
                    print(f"  {path}")
            else:
                print(f"OpenAPI not available: {response.status_code}")
        except Exception as e:
            print(f"Could not get OpenAPI: {e}")
        
        # Try common endpoints
        print("\nTesting common endpoints:")
        endpoints = [
            "/",
            "/health",
            "/api/v1/info",
            "/api/v1/auth/register",
            "/api/auth/register",
            "/auth/register",
            "/docs"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(endpoint)
                print(f"  GET {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"  GET {endpoint}: Error - {e}")


if __name__ == "__main__":
    asyncio.run(test_available_routes())
