"""
Trace all imports to find missing dependencies
"""

import subprocess
import sys
import ast
import os
from pathlib import Path

def find_imports_in_file(file_path):
    """Extract all imports from a Python file."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def find_all_imports(src_dir):
    """Find all imports in the source directory."""
    all_imports = set()
    src_path = Path(src_dir)
    
    for py_file in src_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            imports = find_imports_in_file(py_file)
            all_imports.update(imports)
    
    return all_imports

def check_import_availability(module_name):
    """Check if a module can be imported."""
    try:
        result = subprocess.run(
            f'uv run python -c "import {module_name}"',
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def main():
    print("=== Analyzing All Imports in Certify Studio ===\n")
    
    # Find all imports
    src_dir = "src/certify_studio"
    print(f"Scanning {src_dir} for imports...")
    all_imports = find_all_imports(src_dir)
    
    # Filter out standard library and internal modules
    external_imports = {
        imp for imp in all_imports 
        if not imp.startswith('certify_studio') and 
        not imp.startswith('_') and
        imp not in ['os', 'sys', 'json', 'typing', 'enum', 'pathlib', 
                    'datetime', 'uuid', 'asyncio', 're', 'time', 'math',
                    'collections', 'itertools', 'functools', 'random',
                    'subprocess', 'logging', 'warnings', 'copy', 'io',
                    'abc', 'dataclasses', 'contextlib', 'inspect',
                    'importlib', 'ast', 'xml', 'hashlib', 'base64',
                    'urllib', 'http', 'email', 'csv', 'tempfile',
                    'shutil', 'glob', 'platform', 'socket', 'struct',
                    'queue', 'threading', 'multiprocessing', 'concurrent']
    }
    
    print(f"\nFound {len(external_imports)} external imports to check:")
    
    missing_imports = []
    for imp in sorted(external_imports):
        if check_import_availability(imp):
            print(f"✓ {imp}")
        else:
            print(f"✗ {imp} - MISSING")
            missing_imports.append(imp)
    
    if missing_imports:
        print(f"\n{len(missing_imports)} Missing imports found:")
        for imp in missing_imports:
            print(f"  - {imp}")
        
        # Map common import names to package names
        package_mapping = {
            'markdown': 'markdown',
            'yaml': 'pyyaml',
            'bs4': 'beautifulsoup4',
            'PIL': 'pillow',
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'jwt': 'python-jose[cryptography]',
            'jose': 'python-jose[cryptography]',
            'httpx': 'httpx',
            'aiofiles': 'aiofiles',
            'manim': 'manim',
            'networkx': 'networkx',
            'qdrant_client': 'qdrant-client',
            'neo4j': 'neo4j',
            'prometheus_client': 'prometheus-client',
            'structlog': 'structlog',
            'loguru': 'loguru',
            'tenacity': 'tenacity',
            'chromadb': 'chromadb',
            'pypdf': 'pypdf',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
        }
        
        print("\nInstalling missing packages...")
        for imp in missing_imports:
            package = package_mapping.get(imp, imp)
            print(f"\nInstalling {package}...")
            subprocess.run(f"uv add {package}", shell=True)
    
    # Final sync and test
    print("\nSyncing dependencies...")
    subprocess.run("uv sync", shell=True)
    
    print("\nRunning tests...")
    subprocess.run("uv run pytest tests/unit/test_simple.py -v", shell=True)

if __name__ == "__main__":
    main()
