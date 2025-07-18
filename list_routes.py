"""
List all available routes in the FastAPI application
"""

import requests

try:
    # Get the OpenAPI schema which lists all routes
    response = requests.get("http://localhost:8000/openapi.json")
    if response.status_code == 200:
        openapi = response.json()
        print("Available endpoints:")
        print("=" * 60)
        for path, methods in openapi.get("paths", {}).items():
            for method in methods:
                print(f"{method.upper():<8} {path}")
    else:
        print(f"Could not get OpenAPI schema: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying alternate documentation endpoints...")
    
    # Try other common endpoints
    for url in ["/docs", "/api/docs", "/redoc", "/api/redoc"]:
        try:
            response = requests.get(f"http://localhost:8000{url}")
            print(f"{url:<20} -> {response.status_code}")
        except:
            pass
