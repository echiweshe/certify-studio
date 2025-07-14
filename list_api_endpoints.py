#!/usr/bin/env python3
"""List all available API endpoints"""

import requests
import json

base_url = "http://127.0.0.1:8000"

print("Fetching OpenAPI schema to list all endpoints...")
print("=" * 60)

try:
    # Get OpenAPI schema
    response = requests.get(f"{base_url}/openapi.json")
    if response.status_code == 200:
        schema = response.json()
        
        print(f"API Title: {schema['info']['title']}")
        print(f"Version: {schema['info']['version']}")
        print("\nAvailable Endpoints:")
        print("-" * 60)
        
        # Extract and display all paths
        paths = schema.get('paths', {})
        
        # Group by tag
        endpoints_by_tag = {}
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    tags = details.get('tags', ['untagged'])
                    summary = details.get('summary', 'No description')
                    
                    for tag in tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        endpoints_by_tag[tag].append({
                            'method': method.upper(),
                            'path': path,
                            'summary': summary
                        })
        
        # Display grouped endpoints
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            print(f"\n{tag.upper()}:")
            for ep in sorted(endpoints, key=lambda x: x['path']):
                print(f"  {ep['method']:6} {ep['path']:40} - {ep['summary']}")
        
        print("\n" + "=" * 60)
        print(f"Total endpoints: {sum(len(eps) for eps in endpoints_by_tag.values())}")
        
    else:
        print(f"Failed to fetch OpenAPI schema: {response.status_code}")
        print("Trying alternative locations...")
        
        # Try other possible locations
        for alt_url in ["/api/openapi.json", "/api/v1/openapi.json"]:
            response = requests.get(f"{base_url}{alt_url}")
            if response.status_code == 200:
                print(f"Found at {alt_url}")
                break
        else:
            print("Could not find OpenAPI schema")
            
except Exception as e:
    print(f"Error: {e}")

print("\nTo view interactive documentation, visit:")
print(f"  {base_url}/docs")
print(f"  {base_url}/redoc")
