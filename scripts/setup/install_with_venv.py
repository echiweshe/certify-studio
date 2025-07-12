#!/usr/bin/env python3
"""
Alternative setup script using traditional venv instead of Poetry
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class VenvSetupManager:
    """Setup using traditional Python venv."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.venv_path = self.project_root / "venv"
        self.pip_path = self._get_pip_path()
        self.python_path = self._get_python_path()
        
    def _get_pip_path(self) -> Path:
        """Get pip executable path based on OS."""
        if platform.system() == "Windows":
            return self.venv_path / "Scripts" / "pip.exe"
        else:
            return self.venv_path / "bin" / "pip"
            
    def _get_python_path(self) -> Path:
        """Get python executable path based on OS."""
        if platform.system() == "Windows":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def create_venv(self):
        """Create virtual environment."""
        print("🐍 Creating virtual environment...")
        
        if self.venv_path.exists():
            print("⚠️  Virtual environment already exists")
            return
            
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True
            )
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            sys.exit(1)
    
    def upgrade_pip(self):
        """Upgrade pip to latest version."""
        print("📦 Upgrading pip...")
        
        try:
            subprocess.run(
                [str(self.pip_path), "install", "--upgrade", "pip"],
                check=True
            )
            print("✅ Pip upgraded")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to upgrade pip: {e}")
    
    def install_requirements(self):
        """Install requirements from pyproject.toml."""
        print("📚 Installing dependencies...")
        
        # First, we need to extract dependencies from pyproject.toml
        # For now, let's create a requirements.txt
        self.create_requirements_file()
        
        requirements_file = self.project_root / "requirements.txt"
        
        try:
            subprocess.run(
                [str(self.pip_path), "install", "-r", str(requirements_file)],
                check=True
            )
            print("✅ Dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)
    
    def create_requirements_file(self):
        """Create requirements.txt from pyproject.toml dependencies."""
        requirements = [
            # Core Framework
            "fastapi>=0.104.1",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.1.0",
            
            # Database
            "sqlalchemy>=2.0.23",
            "alembic>=1.13.1",
            "asyncpg>=0.29.0",
            "redis>=5.0.1",
            
            # Security
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.6",
            "cryptography>=41.0.7",
            
            # AWS
            "boto3>=1.34.0",
            "aioboto3>=12.0.0",
            
            # AI/ML
            "langchain>=0.0.350",
            "openai>=1.3.0",
            "anthropic>=0.7.8",
            
            # Manim and Graphics
            "manim>=0.18.0",
            "Pillow>=10.1.0",
            "opencv-python>=4.8.1.78",
            "diagrams>=0.23.4",
            "graphviz>=0.20.1",
            
            # Utils
            "httpx>=0.25.2",
            "pandas>=2.1.4",
            "numpy>=1.26.2",
            "loguru>=0.7.2",
            "pytest>=7.4.3",
            "black>=23.11.0",
        ]
        
        requirements_file = self.project_root / "requirements.txt"
        with open(requirements_file, "w") as f:
            f.write("\n".join(requirements))
        
        print("📝 Created requirements.txt")
    
    def create_activation_script(self):
        """Create activation helper script."""
        if platform.system() == "Windows":
            activate_script = self.project_root / "activate.bat"
            content = f"@echo off\n{self.venv_path}\\Scripts\\activate.bat"
        else:
            activate_script = self.project_root / "activate.sh"
            content = f"#!/bin/bash\nsource {self.venv_path}/bin/activate"
            
        with open(activate_script, "w") as f:
            f.write(content)
            
        if platform.system() != "Windows":
            os.chmod(activate_script, 0o755)
            
        print(f"✅ Created activation script: {activate_script.name}")
    
    def print_instructions(self):
        """Print usage instructions."""
        print("\n🎉 Setup completed!")
        print("\n📝 To activate the virtual environment:")
        
        if platform.system() == "Windows":
            print(f"   .\\activate.bat")
            print(f"   # or")
            print(f"   .\\venv\\Scripts\\activate")
        else:
            print(f"   source activate.sh")
            print(f"   # or")
            print(f"   source venv/bin/activate")
            
        print("\n🚀 To start development:")
        print("   python -m uvicorn src.certify_studio.main:app --reload")
        
        print("\n📦 To install additional packages:")
        print("   pip install <package-name>")
        print("   pip freeze > requirements.txt  # to update requirements")

def main():
    """Main setup function."""
    print("🚀 Certify Studio Setup (venv version)")
    print("-" * 50)
    
    setup = VenvSetupManager()
    
    try:
        # Create virtual environment
        setup.create_venv()
        
        # Upgrade pip
        setup.upgrade_pip()
        
        # Install requirements
        setup.install_requirements()
        
        # Create activation script
        setup.create_activation_script()
        
        # Print instructions
        setup.print_instructions()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
