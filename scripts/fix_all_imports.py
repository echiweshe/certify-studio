#!/usr/bin/env python
"""
Comprehensive import fixer for all API files.
UV-only, enterprise-grade fixes.
"""

import re
from pathlib import Path
from typing import Set, Dict, List


class ImportFixer:
    """Fix all import issues systematically."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src" / "certify_studio"
        
        # Common imports that are often missing
        self.common_imports = {
            "UUID": "from uuid import UUID",
            "Dict": "from typing import Dict",
            "List": "from typing import List",
            "Any": "from typing import Any",
            "Optional": "from typing import Optional",
            "AsyncSession": "from sqlalchemy.ext.asyncio import AsyncSession",
            "Depends": "from fastapi import Depends",
            "HTTPException": "from fastapi import HTTPException",
            "status": "from fastapi import status",
            "User": "from ..schemas import User",
            "BaseResponse": "from ..schemas import BaseResponse",
        }
    
    def find_undefined_names(self, content: str) -> Set[str]:
        """Find potentially undefined names in the code."""
        undefined = set()
        
        # Look for NameError patterns
        for name in self.common_imports.keys():
            # Check if name is used but not imported
            if re.search(rf'\b{name}\b', content):
                # Check if it's imported
                import_pattern = rf'(from .* import .*\b{name}\b|import .*\b{name}\b)'
                if not re.search(import_pattern, content):
                    undefined.add(name)
        
        return undefined
    
    def add_missing_imports(self, content: str, undefined: Set[str]) -> str:
        """Add missing imports to the file."""
        if not undefined:
            return content
        
        # Group imports by their source
        typing_imports = []
        fastapi_imports = []
        sqlalchemy_imports = []
        other_imports = []
        
        for name in undefined:
            import_stmt = self.common_imports.get(name)
            if import_stmt:
                if "from typing import" in import_stmt:
                    typing_imports.append(name)
                elif "from fastapi import" in import_stmt:
                    fastapi_imports.append(name)
                elif "from sqlalchemy" in import_stmt:
                    sqlalchemy_imports.append(name)
                else:
                    other_imports.append(import_stmt)
        
        # Find where to insert imports
        lines = content.split('\n')
        insert_pos = 0
        
        # Find the first import statement
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i
                break
        
        # Update existing typing imports
        if typing_imports:
            typing_updated = False
            for i, line in enumerate(lines):
                if "from typing import" in line:
                    # Extract current imports
                    match = re.search(r'from typing import (.+)', line)
                    if match:
                        current = set(name.strip() for name in match.group(1).split(','))
                        current.update(typing_imports)
                        lines[i] = f"from typing import {', '.join(sorted(current))}"
                        typing_updated = True
                        break
            
            if not typing_updated:
                # Add new typing import line
                lines.insert(insert_pos, f"from typing import {', '.join(sorted(typing_imports))}")
                insert_pos += 1
        
        # Add other imports
        for import_stmt in sorted(set(other_imports)):
            if import_stmt not in content:
                lines.insert(insert_pos, import_stmt)
                insert_pos += 1
        
        return '\n'.join(lines)
    
    def fix_file(self, file_path: Path) -> bool:
        """Fix imports in a single file."""
        try:
            content = file_path.read_text()
            original = content
            
            # Find undefined names
            undefined = self.find_undefined_names(content)
            
            if undefined:
                print(f"  Found undefined: {', '.join(undefined)}")
                content = self.add_missing_imports(content, undefined)
            
            # Also fix common patterns
            replacements = {
                "db: Database": "db: AsyncSession",
                "user: VerifiedUser": "user: User",
                "VerifiedUser = Depends": "User = Depends",
            }
            
            for old, new in replacements.items():
                if old in content:
                    content = content.replace(old, new)
                    print(f"  Fixed: {old} -> {new}")
            
            if content != original:
                file_path.write_text(content)
                return True
            
            return False
            
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def fix_all_api_files(self):
        """Fix all API files."""
        print("🔧 Fixing imports in all API files...")
        
        # Fix all Python files in api directory
        api_dir = self.src_dir / "api"
        fixed_count = 0
        
        for py_file in api_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            print(f"\nChecking {py_file.relative_to(self.src_dir)}...")
            if self.fix_file(py_file):
                print(f"✅ Fixed {py_file.name}")
                fixed_count += 1
            else:
                print(f"  No changes needed")
        
        print(f"\n✅ Fixed {fixed_count} files!")
        return fixed_count > 0


def main():
    """Main entry point."""
    fixer = ImportFixer()
    fixer.fix_all_api_files()
    
    print("\n🎉 Import fixes complete!")
    print("You can now run: uv run python scripts/uv_enterprise_start.py")


if __name__ == "__main__":
    main()
