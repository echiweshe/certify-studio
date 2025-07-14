#!/usr/bin/env python
"""
Enterprise Development utilities for Certify Studio.
UV-ONLY. NO PIP. PRODUCTION GRADE.
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil


class UVDevTools:
    """Development tools using UV exclusively."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.uv_path = self._find_uv()
    
    def _find_uv(self) -> Path:
        """Find UV executable."""
        uv_cmd = shutil.which("uv")
        if uv_cmd:
            return Path(uv_cmd)
        raise RuntimeError("UV not found in PATH. Install it first!")
    
    def run_api_dev(self):
        """Run the API in development mode using UV."""
        print("🚀 Starting Certify Studio API in development mode...")
        
        os.chdir(self.project_root / "src")
        subprocess.run([
            str(self.uv_path), "run", "uvicorn",
            "certify_studio.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload-dir", str(self.project_root / "src")
        ])
    
    def run_api_prod(self):
        """Run the API in production mode using UV."""
        print("🚀 Starting Certify Studio API in production mode...")
        
        os.chdir(self.project_root / "src")
        subprocess.run([
            str(self.uv_path), "run", "uvicorn",
            "certify_studio.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "4"
        ])
    
    def format_code(self):
        """Format code with black and ruff using UV."""
        print("🎨 Formatting code...")
        
        # Run black
        print("Running black...")
        subprocess.run([
            str(self.uv_path), "run", "black",
            "src", "tests"
        ], cwd=self.project_root)
        
        # Run ruff
        print("Running ruff...")
        subprocess.run([
            str(self.uv_path), "run", "ruff",
            "check", "--fix", "src", "tests"
        ], cwd=self.project_root)
        
        print("✅ Code formatting complete!")
    
    def type_check(self):
        """Run type checking with mypy using UV."""
        print("🔍 Running type checks...")
        
        result = subprocess.run([
            str(self.uv_path), "run", "mypy", "src"
        ], cwd=self.project_root)
        
        if result.returncode == 0:
            print("✅ Type checking passed!")
        else:
            print("❌ Type checking failed!")
        
        return result.returncode
    
    def lint_code(self):
        """Run linting checks using UV."""
        print("🔍 Running linting checks...")
        
        result = subprocess.run([
            str(self.uv_path), "run", "ruff",
            "check", "src", "tests"
        ], cwd=self.project_root)
        
        if result.returncode == 0:
            print("✅ Linting passed!")
        else:
            print("❌ Linting failed!")
        
        return result.returncode
    
    def run_tests(self, test_type: str = "all"):
        """Run tests using UV."""
        print(f"🧪 Running {test_type} tests...")
        
        cmd = [str(self.uv_path), "run", "pytest"]
        
        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "e2e":
            cmd.extend(["-m", "e2e"])
        
        # Add coverage if running all tests
        if test_type == "all":
            cmd.extend(["--cov=certify_studio", "--cov-report=html"])
        
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode == 0:
            print(f"✅ {test_type.capitalize()} tests passed!")
        else:
            print(f"❌ {test_type.capitalize()} tests failed!")
        
        return result.returncode
    
    def security_check(self):
        """Run security checks with bandit using UV."""
        print("🔒 Running security checks...")
        
        result = subprocess.run([
            str(self.uv_path), "run", "bandit",
            "-r", "src", "-ll"
        ], cwd=self.project_root)
        
        if result.returncode == 0:
            print("✅ Security checks passed!")
        else:
            print("⚠️  Security issues found!")
        
        return result.returncode
    
    def create_migration(self):
        """Create a new database migration using UV."""
        print("📊 Creating database migration...")
        
        message = input("Migration message: ")
        subprocess.run([
            str(self.uv_path), "run", "alembic",
            "revision", "--autogenerate", "-m", message
        ], cwd=self.project_root)
    
    def run_migration(self):
        """Run database migrations using UV."""
        print("📊 Running database migrations...")
        
        subprocess.run([
            str(self.uv_path), "run", "alembic",
            "upgrade", "head"
        ], cwd=self.project_root)
    
    def install_deps(self):
        """Install/sync all dependencies using UV."""
        print("📦 Syncing dependencies with UV...")
        
        subprocess.run([
            str(self.uv_path), "sync", "--all-extras"
        ], cwd=self.project_root)
        
        print("✅ Dependencies synced!")
    
    def update_deps(self):
        """Update all dependencies using UV."""
        print("📦 Updating dependencies...")
        
        subprocess.run([
            str(self.uv_path), "sync", "--upgrade"
        ], cwd=self.project_root)
        
        print("✅ Dependencies updated!")
    
    def check_all(self):
        """Run all checks (lint, type, security, tests)."""
        print("🔍 Running all checks...")
        
        checks = [
            ("Formatting", self.format_code),
            ("Linting", self.lint_code),
            ("Type checking", self.type_check),
            ("Security", self.security_check),
            ("Unit Tests", lambda: self.run_tests("unit")),
        ]
        
        failed = []
        
        for name, func in checks:
            print(f"\n{'='*50}")
            print(f"Running {name}...")
            print('='*50)
            
            try:
                result = func()
                if result != 0 and result is not None:
                    failed.append(name)
            except Exception as e:
                print(f"Error in {name}: {e}")
                failed.append(name)
        
        if failed:
            print(f"\n❌ Checks failed: {', '.join(failed)}")
            return 1
        else:
            print("\n✅ All checks passed!")
            return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Certify Studio development utilities (UV-only)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # API commands
    subparsers.add_parser("api", help="Run API in development mode")
    subparsers.add_parser("api-prod", help="Run API in production mode")
    
    # Code quality
    subparsers.add_parser("format", help="Format code with black and ruff")
    subparsers.add_parser("lint", help="Run linting checks")
    subparsers.add_parser("type-check", help="Run type checking")
    subparsers.add_parser("security", help="Run security checks")
    subparsers.add_parser("check-all", help="Run all checks")
    
    # Testing
    subparsers.add_parser("test", help="Run all tests")
    subparsers.add_parser("test-unit", help="Run unit tests")
    subparsers.add_parser("test-integration", help="Run integration tests")
    subparsers.add_parser("test-e2e", help="Run end-to-end tests")
    
    # Database
    subparsers.add_parser("db-migrate", help="Run database migrations")
    subparsers.add_parser("db-revision", help="Create new migration")
    
    # Dependencies
    subparsers.add_parser("deps-install", help="Install/sync dependencies")
    subparsers.add_parser("deps-update", help="Update all dependencies")
    
    args = parser.parse_args()
    
    tools = UVDevTools()
    
    commands = {
        "api": tools.run_api_dev,
        "api-prod": tools.run_api_prod,
        "format": tools.format_code,
        "lint": tools.lint_code,
        "type-check": tools.type_check,
        "security": tools.security_check,
        "check-all": tools.check_all,
        "test": lambda: tools.run_tests("all"),
        "test-unit": lambda: tools.run_tests("unit"),
        "test-integration": lambda: tools.run_tests("integration"),
        "test-e2e": lambda: tools.run_tests("e2e"),
        "db-migrate": tools.run_migration,
        "db-revision": tools.create_migration,
        "deps-install": tools.install_deps,
        "deps-update": tools.update_deps,
    }
    
    if args.command in commands:
        return commands[args.command]()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
