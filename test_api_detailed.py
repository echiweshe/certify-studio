#!/usr/bin/env python3
"""Test API endpoints with detailed output"""

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
    print(f"   Headers:")
    for header, value in response.headers.items():
        if header.startswith(('X-', 'Strict-', 'Referrer-', 'Permissions-')):
            print(f"     {header}: {value}")
except Exception as e:
    print(f"   Error: {e}")

# Test API info endpoint  
print("\n2. Testing /api/v1/info endpoint...")
try:
    response = requests.get(f"{base_url}/api/v1/info")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   API Name: {data.get('name')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Agents: {len(data.get('agents', []))}")
        print(f"   Capabilities: {', '.join(data.get('capabilities', []))}")
    else:
        print(f"   Response: {response.text}")
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

# Test docs endpoint
print("\n4. Testing /docs endpoint...")
try:
    response = requests.get(f"{base_url}/docs")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
except Exception as e:
    print(f"   Error: {e}")

# Test a protected endpoint
print("\n5. Testing protected endpoint /api/v1/generation/start...")
try:
    response = requests.post(f"{base_url}/api/v1/generation/start")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json() if response.text else 'No content'}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 50)
print("API test complete!")
