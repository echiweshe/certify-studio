"""
Import Fixer for Certify Studio
Automatically fixes common import issues after recovery
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

class ImportFixer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixes_applied = []
        
    def fix_file(self, file_path: Path) -> bool:
        """Fix imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Common fixes after recovery
            fixes = [
                # Fix triple dots to double dots for database imports
                (r'from \.\.\.database', 'from ..database'),
                (r'from \.\.\.core', 'from ..core'),
                (r'from \.\.\.integration', 'from ..integration'),
                
                # Fix api imports
                (r'from \.\.\.api', 'from ..api'),
                
                # Fix shared imports
                (r'from \.\.\.shared', 'from ..shared'),
                
                # Fix agent imports
                (r'from \.agents\.', 'from .agents.'),
                
                # Fix absolute imports that should be relative
                (r'from certify_studio\.', 'from .'),
                
                # Fix WebSocket import
                (r'from \.\.\.websocket', 'from ..integration.websocket'),
                
                # Fix logging imports
                (r'from \.\.\.core\.logging', 'from ..core.logging'),
                
                # Fix database model imports
                (r'from \.\.\.database\.models', 'from ..database.models'),
                
                # Fix services imports
                (r'from \.\.\.services', 'from ..services'),
            ]
            
            for pattern, replacement in fixes:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    self.fixes_applied.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'fix': f"{pattern} -> {replacement}"
                    })
            
            # Write back if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def fix_all(self) -> dict:
        """Fix all Python files in the project."""
        files_fixed = 0
        files_checked = 0
        
        # Priority files to fix first
        priority_files = [
            "src/certify_studio/main.py",
            "src/certify_studio/app.py",
            "src/certify_studio/config.py",
            "src/certify_studio/api/main.py",
            "src/certify_studio/api/v1/auth.py",
            "src/certify_studio/integration/dependencies.py",
            "src/certify_studio/database/connection.py",
            "src/certify_studio/agents/base.py"
        ]
        
        # Fix priority files
        for file_path in priority_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                files_checked += 1
                if self.fix_file(full_path):
                    files_fixed += 1
                    print(f"Fixed: {file_path}")
        
        # Fix all other Python files
        for py_file in (self.project_root / "src" / "certify_studio").rglob("*.py"):
            rel_path = py_file.relative_to(self.project_root)
            if str(rel_path) not in priority_files:
                files_checked += 1
                if self.fix_file(py_file):
                    files_fixed += 1
                    print(f"Fixed: {rel_path}")
        
        return {
            'files_checked': files_checked,
            'files_fixed': files_fixed,
            'fixes_applied': self.fixes_applied
        }

def create_missing_init_files(project_root: Path):
    """Create any missing __init__.py files."""
    created = []
    
    for dir_path in (project_root / "src" / "certify_studio").rglob("*"):
        if dir_path.is_dir() and not dir_path.name.startswith('__'):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                created.append(str(init_file.relative_to(project_root)))
    
    return created

def main():
    """Run the import fixer."""
    project_root = Path(__file__).parent
    
    print("CERTIFY STUDIO IMPORT FIXER")
    print("=" * 50)
    
    # Create missing __init__.py files
    print("\n1. Creating missing __init__.py files...")
    created = create_missing_init_files(project_root)
    if created:
        print(f"   Created {len(created)} __init__.py files")
        for file in created[:5]:
            print(f"   - {file}")
    else:
        print("   All __init__.py files present")
    
    # Fix imports
    print("\n2. Fixing imports...")
    fixer = ImportFixer(project_root)
    results = fixer.fix_all()
    
    print(f"\n   Files checked: {results['files_checked']}")
    print(f"   Files fixed: {results['files_fixed']}")
    
    if results['fixes_applied']:
        print("\n   Fixes applied:")
        for fix in results['fixes_applied'][:10]:
            print(f"   - {fix['file']}: {fix['fix']}")
    
    # Save report
    import json
    report_path = project_root / "import_fixes_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    print("\nNext step: Run 'python -m certify_studio.main' to test")

if __name__ == "__main__":
    main()
