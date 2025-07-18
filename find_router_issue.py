import os
import sys

# Search for duplicate router includes
api_main_path = r'C:\ZBDuo_Share\Labs\src\BttlnsCldMCP\certify-studio-github-pull\src\certify_studio\api\main.py'

with open(api_main_path, 'r') as f:
    content = f.read()
    
# Find all include_router calls
import re
matches = re.findall(r'app\.include_router\([^)]+\)', content)

print("Found include_router calls:")
for match in matches:
    print(f"  {match}")
    
# Also check for prefix="/api"
if 'prefix="/api"' in content:
    print("\nFound prefix='/api' in api/main.py")
