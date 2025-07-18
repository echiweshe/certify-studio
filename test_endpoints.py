"""
Test the API endpoints to debug routing issues.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing API Endpoints")
print("=" * 60)

# Test different URL patterns
urls_to_test = [
    "/",
    "/health",
    "/api/v1/info",
    "/api/info",
    "/api/v1/auth/login",
    "/api/auth/login",
    "/api/v1/api/v1/auth/login",  # The problematic double prefix
]

print("Testing GET endpoints:")
for url in urls_to_test:
    try:
        response = requests.get(BASE_URL + url, timeout=2)
        print(f"{url:<40} -> {response.status_code}")
    except Exception as e:
        print(f"{url:<40} -> ERROR: {e}")

print("\nTesting login endpoints:")
login_data = {
    "username": "admin@certifystudio.com",
    "password": "admin123"
}

login_urls = [
    "/api/v1/auth/login",
    "/api/auth/login",
    "/v1/auth/login",
    "/auth/login"
]

for url in login_urls:
    try:
        response = requests.post(
            BASE_URL + url,
            data={"username": login_data["username"], "password": login_data["password"]},
            timeout=2
        )
        print(f"POST {url:<35} -> {response.status_code}")
        if response.status_code == 200:
            print(f"     SUCCESS! This is the correct endpoint")
            break
    except Exception as e:
        print(f"POST {url:<35} -> ERROR: {e}")
