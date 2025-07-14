"""
Fix all incorrect VisionProcessor imports
"""

import os
from pathlib import Path

def fix_vision_imports(root_dir):
    """Fix all incorrect VisionProcessor imports"""
    root_path = Path(root_dir)
    
    files_fixed = 0
    
    for py_file in root_path.rglob("*.py"):
        # Skip venv and cache
        if any(part in str(py_file) for part in ['.venv', '__pycache__', 'site-packages']):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it has the wrong import
            if "from ....core.vision import VisionProcessor" in content:
                # Replace with correct import
                fixed_content = content.replace(
                    "from ....core.vision import VisionProcessor",
                    "from ....core.llm.vision_processor import VisionProcessor"
                )
                
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                print(f"✅ Fixed: {py_file}")
                files_fixed += 1
                
        except Exception as e:
            continue
    
    return files_fixed

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("Fixing VisionProcessor imports...")
    print("=" * 60)
    
    fixed = fix_vision_imports(src_dir)
    
    if fixed:
        print(f"\n✅ Fixed {fixed} files!")
    else:
        print("\n✅ No incorrect imports found!")
