"""
Diagnostic Script for Certify Studio
Identifies all issues preventing the system from running
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple

class ImportDiagnostic:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        self.issues = []
        self.import_fixes = {}
        
    def check_file_imports(self, file_path: Path) -> List[Dict]:
        """Check all imports in a Python file."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    level = node.level
                    
                    # Check relative imports
                    if level > 0:
                        # Calculate the correct import path
                        current_package = file_path.parent
                        for _ in range(level - 1):
                            current_package = current_package.parent
                        
                        # Try to resolve the import
                        if module:
                            target_path = current_package / module.replace('.', '/')
                            if not (target_path.exists() or 
                                   (target_path.with_suffix('.py')).exists() or
                                   (target_path / '__init__.py').exists()):
                                issues.append({
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': node.lineno,
                                    'import': f"{'.' * level}{module}",
                                    'type': 'relative_import_not_found',
                                    'suggestion': self.suggest_fix(file_path, module, level)
                                })
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        # Check if it's a local module
                        if module_name.startswith('certify_studio'):
                            if not self.can_import_module(module_name):
                                issues.append({
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': node.lineno,
                                    'import': module_name,
                                    'type': 'module_not_found',
                                    'suggestion': f"Check if module exists in src/"
                                })
        
        except Exception as e:
            issues.append({
                'file': str(file_path.relative_to(self.project_root)),
                'error': str(e),
                'type': 'parse_error'
            })
        
        return issues
    
    def suggest_fix(self, file_path: Path, module: str, level: int) -> str:
        """Suggest import fix based on file structure."""
        # Common fixes after recovery
        if level == 3 and module.startswith('database'):
            return f"Try: from ..{module} (2 dots instead of 3)"
        elif level == 2 and module.startswith('core'):
            return f"Try: from ..{module} (correct)"
        else:
            return "Check relative import levels"
    
    def can_import_module(self, module_name: str) -> bool:
        """Check if a module can be imported."""
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except:
            return False
    
    def scan_project(self) -> Dict:
        """Scan entire project for import issues."""
        all_issues = []
        files_scanned = 0
        
        # Key files to check first
        priority_files = [
            "src/certify_studio/main.py",
            "src/certify_studio/app.py",
            "src/certify_studio/config.py",
            "src/certify_studio/api/main.py",
            "src/certify_studio/api/v1/auth.py",
            "src/certify_studio/agents/base.py",
            "src/certify_studio/database/connection.py"
        ]
        
        # Check priority files
        for file_path in priority_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                issues = self.check_file_imports(full_path)
                if issues:
                    all_issues.extend(issues)
                files_scanned += 1
        
        # Check all Python files
        for py_file in (self.src_path / "certify_studio").rglob("*.py"):
            if str(py_file.relative_to(self.project_root)) not in priority_files:
                issues = self.check_file_imports(py_file)
                if issues:
                    all_issues.extend(issues)
                files_scanned += 1
        
        return {
            'total_files': files_scanned,
            'total_issues': len(all_issues),
            'issues': all_issues
        }

def check_database_config(project_root: Path) -> Dict:
    """Check database configuration."""
    env_path = project_root / ".env"
    issues = []
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
        
        if 'DATABASE_URL' in content:
            # Extract DATABASE_URL
            for line in content.split('\n'):
                if line.startswith('DATABASE_URL'):
                    db_url = line.split('=', 1)[1].strip()
                    if 'postgresql' in db_url:
                        issues.append({
                            'status': 'configured',
                            'url': db_url.replace('postgresql://', 'postgresql://***:***@')
                        })
                    break
        else:
            issues.append({'status': 'missing', 'error': 'DATABASE_URL not found in .env'})
    else:
        issues.append({'status': 'missing', 'error': '.env file not found'})
    
    return {'database': issues}

def check_dependencies(project_root: Path) -> Dict:
    """Check if key dependencies are installed."""
    required = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'asyncpg',
        'pydantic',
        'python-jose',
        'python-multipart'
    ]
    
    missing = []
    for dep in required:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            missing.append(dep)
    
    return {
        'required': required,
        'missing': missing,
        'status': 'ok' if not missing else 'missing_dependencies'
    }

def main():
    """Run full diagnostic."""
    project_root = Path(__file__).parent
    
    print("CERTIFY STUDIO DIAGNOSTIC")
    print("=" * 50)
    
    # Add src to path
    sys.path.insert(0, str(project_root / "src"))
    
    # Check imports
    print("\n1. CHECKING IMPORTS...")
    diagnostic = ImportDiagnostic(project_root)
    results = diagnostic.scan_project()
    
    print(f"   Files scanned: {results['total_files']}")
    print(f"   Issues found: {results['total_issues']}")
    
    if results['issues']:
        print("\n   IMPORT ISSUES:")
        for issue in results['issues'][:10]:  # Show first 10
            print(f"   - {issue['file']}:{issue.get('line', '?')}")
            print(f"     Import: {issue.get('import', issue.get('error', 'Unknown'))}")
            print(f"     Type: {issue['type']}")
            if 'suggestion' in issue:
                print(f"     Fix: {issue['suggestion']}")
    
    # Check database
    print("\n2. CHECKING DATABASE CONFIG...")
    db_config = check_database_config(project_root)
    for item in db_config['database']:
        print(f"   Status: {item['status']}")
        if 'url' in item:
            print(f"   URL: {item['url']}")
        if 'error' in item:
            print(f"   Error: {item['error']}")
    
    # Check dependencies
    print("\n3. CHECKING DEPENDENCIES...")
    deps = check_dependencies(project_root)
    print(f"   Status: {deps['status']}")
    if deps['missing']:
        print(f"   Missing: {', '.join(deps['missing'])}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    if results['total_issues'] > 0:
        print(f"Found {results['total_issues']} import issues that need fixing")
        print("Run: python fix_imports.py to attempt automatic fixes")
    else:
        print("No import issues found!")
    
    if deps['missing']:
        print(f"Install missing dependencies: pip install {' '.join(deps['missing'])}")
    
    # Save detailed report
    report_path = project_root / "diagnostic_report.json"
    import json
    with open(report_path, 'w') as f:
        json.dump({
            'imports': results,
            'database': db_config,
            'dependencies': deps
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main()
