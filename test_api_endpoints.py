#!/usr/bin/env python3
"""Test API endpoints using Python requests"""

import requests
import json

base_url = "http://127.0.0.1:8000"

print("Testing Certify Studio API Endpoints")
print("=" * 50)

# Test health endpoint
print("\n1. Testing /health endpoint...")
try:
    response = requests.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test API info endpoint
print("\n2. Testing /api/info endpoint...")
try:
    response = requests.get(f"{base_url}/api/info")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   API Name: {data.get('name')}")
    print(f"   Version: {data.get('version')}")
    print(f"   Agents: {len(data.get('agents', []))}")
except Exception as e:
    print(f"   Error: {e}")

# Test root endpoint
print("\n3. Testing / endpoint...")
try:
    response = requests.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Check response headers
print("\n4. Checking security headers...")
try:
    response = requests.get(f"{base_url}/health")
    headers = dict(response.headers)
    security_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "X-Request-ID"
    ]
    for header in security_headers:
        if header in headers:
            print(f"   ✓ {header}: {headers[header]}")
        else:
            print(f"   ✗ {header}: Missing")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 50)
print("API test complete!")
