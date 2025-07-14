"""
Find where MultiModalLLM is being imported
"""

import os
import re
from pathlib import Path

def find_multimodal_imports(root_dir):
    """Find all files importing MultiModalLLM"""
    root_path = Path(root_dir)
    pattern = re.compile(r'MultiModalLLM')
    
    for py_file in root_path.rglob("*.py"):
        # Skip venv and cache
        if any(part in str(py_file) for part in ['.venv', '__pycache__', 'site-packages']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if pattern.search(content):
                print(f"\nFound in: {py_file}")
                # Show the lines containing the pattern
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'MultiModalLLM' in line:
                        print(f"  Line {i+1}: {line.strip()}")
                        
        except Exception as e:
            print(f"Error reading {py_file}: {e}")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("Searching for MultiModalLLM imports...")
    print("=" * 60)
    
    find_multimodal_imports(src_dir)
