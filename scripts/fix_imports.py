#!/usr/bin/env python3
"""
Fix import issues throughout the codebase.
Systematically fixes Config imports to use Settings.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'__pycache__', '.git', '.venv', 'venv', '.mypy_cache'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def fix_config_imports(file_path: Path) -> bool:
    """Fix Config imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix import statements
        patterns = [
            # Fix: from ...config import Config -> from ...config import Settings
            (r'from (\.+)config import Config\b', r'from \1config import Settings'),
            # Fix: from ...core.config import Config -> from ...core.config import Settings  
            (r'from (\.+)core\.config import Config\b', r'from \1core.config import Settings'),
            # Fix type hints: config: Config -> config: Settings
            (r'(\w+):\s*Config\b', r'\1: Settings'),
            # Fix function signatures: (config: Config) -> (config: Settings)
            (r'\(([^)]*?)\bconfig:\s*Config\b', r'(\1config: Settings'),
            # Fix generic Config references
            (r'\bConfig\s*\(', r'Settings('),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Special case: if file imports Settings but uses Config
        if 'from' in content and 'Settings' in content and 'Config' in content:
            # Replace standalone Config usage with Settings
            content = re.sub(r'\bConfig\b(?!\w)', 'Settings', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix imports."""
    # Get the src directory
    script_dir = Path(__file__).parent
    src_dir = script_dir.parent / 'src'
    
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}")
        return
    
    print(f"Scanning for Python files in: {src_dir}")
    
    python_files = find_python_files(src_dir)
    print(f"Found {len(python_files)} Python files")
    
    fixed_files = []
    
    for file_path in python_files:
        if fix_config_imports(file_path):
            fixed_files.append(file_path)
            print(f"Fixed: {file_path.relative_to(src_dir)}")
    
    print(f"\nFixed {len(fixed_files)} files")
    
    if fixed_files:
        print("\nFiles modified:")
        for file_path in fixed_files:
            print(f"  - {file_path.relative_to(src_dir)}")

if __name__ == "__main__":
    main()
