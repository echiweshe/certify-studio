#!/usr/bin/env python
"""
Smart Startup Script for Certify Studio
Handles common startup issues automatically.
"""

import os
import sys
import subprocess
from pathlib import Path
import json


class CertifyStudioStarter:
    """Smart starter that handles common issues."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / ".venv"
        if sys.platform == "win32":
            self.python_path = self.venv_path / "Scripts" / "python.exe"
            self.pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:
            self.python_path = self.venv_path / "bin" / "python"
            self.pip_path = self.venv_path / "bin" / "pip"
    
    def check_and_fix_dependencies(self):
        """Check and install missing dependencies."""
        print("🔍 Checking dependencies...")
        
        # Check if aiosqlite is installed
        try:
            subprocess.run([
                str(self.python_path), "-c", 
                "import aiosqlite"
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("📦 Installing aiosqlite for SQLite support...")
            subprocess.run([
                str(self.pip_path), "install", "aiosqlite"
            ], check=True)
    
    def fix_config_issues(self):
        """Fix configuration issues."""
        print("🔧 Checking configuration...")
        
        # Check if config.py has RATE_LIMITS
        config_file = self.project_root / "src" / "certify_studio" / "config.py"
        if config_file.exists():
            content = config_file.read_text()
            if "RATE_LIMITS" not in content:
                print("📝 Adding RATE_LIMITS to config...")
                # Add import for Dict if not present
                if "from typing import" in content and "Dict" not in content:
                    content = content.replace(
                        "from typing import List, Optional, Union, Any",
                        "from typing import List, Optional, Union, Dict, Any"
                    )
                
                # Find a place to add RATE_LIMITS (after Neo4j config)
                insertion_marker = "NEO4J_MAX_CONNECTION_LIFETIME: int = Field(default=3600, env=\"NEO4J_MAX_CONNECTION_LIFETIME\")"
                if insertion_marker in content:
                    insertion_point = content.find(insertion_marker) + len(insertion_marker)
                    rate_limits_config = '''
    
    # Rate Limiting
    RATE_LIMITS: Dict[str, int] = Field(
        default={"free": 100, "pro": 1000, "enterprise": 10000},
        env="RATE_LIMITS"
    )'''
                    content = content[:insertion_point] + rate_limits_config + content[insertion_point:]
                    config_file.write_text(content)
                    print("✅ Added RATE_LIMITS configuration")
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        print("📁 Ensuring directories...")
        
        directories = [
            "logs", "uploads", "exports", "temp",
            "src/certify_studio/data/cache",
            "src/certify_studio/data/models",
            "src/certify_studio/data/knowledge_base"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    def check_env_file(self):
        """Ensure .env file exists."""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("📝 Creating .env file...")
            env_example = self.project_root / ".env.example"
            if env_example.exists():
                import shutil
                shutil.copy(env_example, env_file)
            else:
                # Create minimal .env
                env_content = '''# Certify Studio Environment Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-this
JWT_SECRET_KEY=dev-jwt-secret-key-change-this
DATABASE_URL=sqlite+aiosqlite:///./certify_studio.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
'''
                env_file.write_text(env_content)
            print("✅ Created .env file")
    
    def start_api(self):
        """Start the API server."""
        print("\n🚀 Starting Certify Studio API...")
        print("-" * 50)
        print("📚 Once started, visit:")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Health: http://localhost:8000/health")
        print("\n💡 Press Ctrl+C to stop\n")
        
        # Change to src directory
        os.chdir(self.project_root / "src")
        
        # Start uvicorn
        subprocess.run([
            str(self.python_path), "-m", "uvicorn",
            "certify_studio.api.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    
    def run(self):
        """Run all checks and start the API."""
        print("🚀 Certify Studio Smart Starter")
        print("=" * 50)
        
        try:
            # Run all checks and fixes
            self.check_and_fix_dependencies()
            self.fix_config_issues()
            self.ensure_directories()
            self.check_env_file()
            
            print("\n✅ All checks passed!")
            
            # Start the API
            self.start_api()
            
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down Certify Studio...")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nPlease check the logs and try again.")
            return 1
        
        return 0


def main():
    """Main entry point."""
    starter = CertifyStudioStarter()
    return starter.run()


if __name__ == "__main__":
    sys.exit(main())
