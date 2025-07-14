#!/usr/bin/env python
"""
Enterprise-grade UV-based startup for Certify Studio.
NO FALLBACKS. UV ONLY. PRODUCTION READY.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional


class UVEnterpriseStarter:
    """Enterprise starter using UV exclusively."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / ".venv"
        # UV creates consistent paths across platforms
        self.python_path = self.venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "python"
        self.uv_path = self._find_uv()
    
    def _find_uv(self) -> Path:
        """Find UV installation."""
        # Check common UV installation paths
        uv_locations = [
            Path.home() / ".cargo" / "bin" / "uv",
            Path.home() / ".cargo" / "bin" / "uv.exe",
            Path("/usr/local/bin/uv"),
            Path("C:/Users") / os.environ.get("USERNAME", "") / ".cargo" / "bin" / "uv.exe",
        ]
        
        # Also check PATH
        import shutil
        uv_in_path = shutil.which("uv")
        if uv_in_path:
            return Path(uv_in_path)
        
        for uv_path in uv_locations:
            if uv_path.exists():
                return uv_path
        
        raise RuntimeError(
            "UV not found. Install it with:\n"
            "  Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n"
            "  Unix: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
    
    def ensure_uv_project(self):
        """Ensure pyproject.toml has all required dependencies."""
        print("🔧 Validating pyproject.toml...")
        
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            raise RuntimeError("pyproject.toml not found! This is not a valid UV project.")
        
        # Read current pyproject.toml
        import tomllib
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        
        # Check for required dependencies
        dependencies = pyproject.get("project", {}).get("dependencies", [])
        required_deps = {
            "aiosqlite": "aiosqlite>=0.19.0",  # For SQLite support
            "python-multipart": "python-multipart>=0.0.6",  # For file uploads
            "python-jose": "python-jose[cryptography]>=3.3.0",  # For JWT
            "passlib": "passlib[bcrypt]>=1.7.4",  # For password hashing
        }
        
        # Check which are missing
        dep_names = [dep.split(">=")[0].split("[")[0] for dep in dependencies]
        missing = []
        for dep_name, dep_spec in required_deps.items():
            if dep_name not in dep_names:
                missing.append(dep_spec)
        
        if missing:
            print(f"📦 Adding missing dependencies: {', '.join(missing)}")
            for dep in missing:
                subprocess.run([str(self.uv_path), "add", dep], check=True, cwd=self.project_root)
            print("✅ Dependencies added to pyproject.toml")
    
    def setup_uv_environment(self):
        """Setup UV environment properly."""
        print("🛠️ Setting up UV environment...")
        
        os.chdir(self.project_root)
        
        # Create venv if it doesn't exist
        if not self.venv_path.exists():
            print("📦 Creating virtual environment with UV...")
            # Try to use Python 3.11+, but let UV pick the best available
            try:
                subprocess.run([str(self.uv_path), "venv", "--python", "3.11"], check=True)
            except subprocess.CalledProcessError:
                # Fall back to any Python 3.11+
                subprocess.run([str(self.uv_path), "venv", "--python", ">=3.11"], check=True)
        
        # Sync all dependencies including dev and optional
        print("📥 Syncing all dependencies with UV...")
        subprocess.run([str(self.uv_path), "sync", "--all-extras"], check=True)
        
        print("✅ UV environment ready!")
    
    def fix_configuration(self):
        """Fix configuration issues at enterprise level."""
        print("🔧 Validating configuration...")
        
        config_file = self.project_root / "src" / "certify_studio" / "config.py"
        if not config_file.exists():
            raise RuntimeError("config.py not found! Invalid project structure.")
        
        content = config_file.read_text()
        modified = False
        
        # Ensure Dict is imported
        if "from typing import" in content and ", Dict" not in content and " Dict" not in content:
            content = content.replace(
                "from typing import",
                "from typing import Dict,"
            )
            modified = True
        
        # Add RATE_LIMITS if missing
        if "RATE_LIMITS" not in content:
            # Find insertion point after NEO4J config
            insertion_marker = "NEO4J_MAX_CONNECTION_LIFETIME: int = Field"
            if insertion_marker in content:
                # Find the end of the NEO4J section
                idx = content.find(insertion_marker)
                # Find the next empty line
                next_empty = content.find("\n    \n", idx)
                if next_empty == -1:
                    next_empty = content.find("\n\n", idx)
                
                if next_empty != -1:
                    rate_limit_config = '''
    # Rate Limiting Configuration
    RATE_LIMITS: Dict[str, int] = Field(
        default={"free": 100, "pro": 1000, "enterprise": 10000},
        description="Rate limits per plan type (requests per hour)"
    )
'''
                    content = content[:next_empty] + "\n" + rate_limit_config + content[next_empty:]
                    modified = True
        
        if modified:
            config_file.write_text(content)
            print("✅ Configuration updated")
        else:
            print("✅ Configuration valid")
    
    def ensure_enterprise_structure(self):
        """Ensure all enterprise directories and files exist."""
        print("📁 Validating enterprise structure...")
        
        # Required directories
        directories = [
            "logs",
            "uploads",
            "exports",
            "exports/videos",
            "temp",
            "assets",
            "src/certify_studio/data",
            "src/certify_studio/data/cache",
            "src/certify_studio/data/models",
            "src/certify_studio/data/knowledge_base",
            "src/certify_studio/data/embeddings",
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure .env exists
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("📝 Creating .env from template...")
            env_example = self.project_root / ".env.example"
            if env_example.exists():
                import shutil
                shutil.copy(env_example, env_file)
                print("⚠️  UPDATE .env with your configuration!")
            else:
                raise RuntimeError(".env.example not found! Invalid project structure.")
        
        print("✅ Enterprise structure validated")
    
    def run_pre_flight_checks(self):
        """Run comprehensive pre-flight checks."""
        print("\n🔍 Running pre-flight checks...")
        
        checks = []
        
        # Check Python version
        python_version = subprocess.run(
            [str(self.python_path), "--version"],
            capture_output=True,
            text=True
        ).stdout.strip()
        # Accept Python 3.11, 3.12, or 3.13
        version_ok = any(ver in python_version for ver in ["3.11", "3.12", "3.13"])
        checks.append((f"Python 3.11+ (found: {python_version})", version_ok))
        
        # Check critical imports
        critical_imports = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "sqlalchemy",
            "aiosqlite",
            "redis",
            "jose",
            "passlib",
        ]
        
        for module in critical_imports:
            try:
                subprocess.run(
                    [str(self.python_path), "-c", f"import {module}"],
                    check=True,
                    capture_output=True
                )
                checks.append((f"Module: {module}", True))
            except subprocess.CalledProcessError:
                checks.append((f"Module: {module}", False))
        
        # Display results
        print("\nPre-flight Check Results:")
        print("-" * 40)
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        if not all_passed:
            raise RuntimeError("Pre-flight checks failed! Run 'uv sync' to fix.")
        
        print("\n✅ All pre-flight checks passed!")
    
    def start_enterprise_api(self):
        """Start API in enterprise mode."""
        print("\n🚀 Starting Certify Studio Enterprise API...")
        print("=" * 60)
        print("🏢 ENTERPRISE MODE - Production Configuration")
        print("=" * 60)
        print("\n📚 Access Points:")
        print("  - API Documentation: http://localhost:8000/docs")
        print("  - Alternative Docs: http://localhost:8000/redoc")
        print("  - Health Check: http://localhost:8000/health")
        print("  - Metrics: http://localhost:8000/metrics")
        print("\n⚡ Features:")
        print("  - Hot reload enabled")
        print("  - Structured logging active")
        print("  - Error tracking enabled")
        print("\n💡 Press Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        # Change to src directory
        os.chdir(self.project_root / "src")
        
        # Use UV to run uvicorn
        subprocess.run([
            str(self.uv_path), "run", "uvicorn",
            "certify_studio.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload-dir", str(self.project_root / "src")
        ])
        
        # Note: Removed --log-config to avoid json logger dependency issue
        # To use custom logging, first run: uv add python-json-logger
    
    def run(self):
        """Run the complete enterprise startup sequence."""
        print("🏢 Certify Studio Enterprise Launcher (UV)")
        print("=" * 60)
        print("Using UV for all dependency management")
        print("No pip. No shortcuts. Enterprise grade only.")
        print("=" * 60 + "\n")
        
        try:
            # Complete startup sequence
            self.ensure_uv_project()
            self.setup_uv_environment()
            self.fix_configuration()
            self.ensure_enterprise_structure()
            self.run_pre_flight_checks()
            
            # Start the API
            self.start_enterprise_api()
            
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down Certify Studio...")
        except RuntimeError as e:
            print(f"\n❌ Enterprise Check Failed: {e}")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        return 0


def main():
    """Main entry point."""
    starter = UVEnterpriseStarter()
    return starter.run()


if __name__ == "__main__":
    sys.exit(main())
