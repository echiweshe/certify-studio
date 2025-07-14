"""
Find and fix encoding issues in Python files
"""

import os
import sys
from pathlib import Path

def check_file_encoding(file_path):
    """Check if a file has encoding issues"""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return True, encoding, content
        except UnicodeDecodeError as e:
            continue
    
    return False, None, None

def fix_encoding_issues(root_dir):
    """Find and fix encoding issues in all Python files"""
    root_path = Path(root_dir)
    problematic_files = []
    
    for py_file in root_path.rglob("*.py"):
        # Skip venv and cache directories
        if any(part in str(py_file) for part in ['.venv', '__pycache__', 'site-packages']):
            continue
            
        success, encoding, content = check_file_encoding(py_file)
        
        if not success:
            print(f"❌ Cannot read: {py_file}")
            problematic_files.append(py_file)
        elif encoding != 'utf-8':
            print(f"⚠️  Non-UTF8 encoding ({encoding}): {py_file}")
            # Convert to UTF-8
            try:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Converted to UTF-8: {py_file}")
            except Exception as e:
                print(f"❌ Failed to convert: {e}")

    return problematic_files

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("Checking for encoding issues...")
    print("=" * 60)
    
    problematic = fix_encoding_issues(src_dir)
    
    if problematic:
        print(f"\n❌ Found {len(problematic)} files with encoding issues")
        for file in problematic:
            print(f"  - {file}")
    else:
        print("\n✅ All files are properly encoded")
