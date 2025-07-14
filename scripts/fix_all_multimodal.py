"""
Find all instances of MultiModalLLM (wrong) vs MultimodalLLM (correct)
"""

import os
import re
from pathlib import Path

def find_wrong_imports(root_dir):
    """Find all files with the wrong import"""
    root_path = Path(root_dir)
    wrong_pattern = re.compile(r'MultiModalLLM')
    
    files_to_fix = []
    
    for py_file in root_path.rglob("*.py"):
        # Skip venv and cache
        if any(part in str(py_file) for part in ['.venv', '__pycache__', 'site-packages']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if wrong_pattern.search(content):
                files_to_fix.append(py_file)
                print(f"\nFound in: {py_file}")
                # Show the lines containing the pattern
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'MultiModalLLM' in line:
                        print(f"  Line {i+1}: {line.strip()}")
                        
        except Exception as e:
            continue
    
    return files_to_fix

def fix_imports(files):
    """Fix the imports in all files"""
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the wrong import
            fixed_content = content.replace('MultiModalLLM', 'MultimodalLLM')
            
            if fixed_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"✅ Fixed: {file_path}")
                
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("Searching for MultiModalLLM (incorrect) imports...")
    print("=" * 60)
    
    files_to_fix = find_wrong_imports(src_dir)
    
    if files_to_fix:
        print(f"\n\nFound {len(files_to_fix)} files to fix")
        response = input("\nFix all these files? (y/n): ")
        if response.lower() == 'y':
            fix_imports(files_to_fix)
            print("\n✅ All files fixed!")
        else:
            print("Skipped fixing")
    else:
        print("\n✅ No incorrect imports found!")
