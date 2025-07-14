#!/usr/bin/env python
"""
Enterprise-level dependency setup for Certify Studio.
Uses UV for modern Python dependency management.
"""

import subprocess
import sys
import os
from pathlib import Path
import platform


def check_uv_installed():
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv():
    """Install uv if not present."""
    print("📦 Installing uv (modern Python package manager)...")
    
    if platform.system() == "Windows":
        # Windows installation
        subprocess.run([
            "powershell", "-c",
            "irm https://astral.sh/uv/install.ps1 | iex"
        ], check=True)
    else:
        # Unix-like installation
        subprocess.run([
            "curl", "-LsSf",
            "https://astral.sh/uv/install.sh", "|", "sh"
        ], shell=True, check=True)
    
    print("✅ UV installed successfully!")


def setup_virtual_environment():
    """Create and setup virtual environment using uv."""
    print("🔧 Setting up virtual environment...")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Create virtual environment with Python 3.11
    subprocess.run(["uv", "venv", "--python", "3.11"], check=True)
    
    print("✅ Virtual environment created!")


def sync_dependencies():
    """Sync all dependencies from pyproject.toml."""
    print("📥 Syncing dependencies from pyproject.toml...")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Sync main dependencies
    subprocess.run(["uv", "sync"], check=True)
    
    # Install all optional dependencies for full feature set
    subprocess.run(["uv", "sync", "--all-extras"], check=True)
    
    print("✅ All dependencies synced!")


def install_spacy_models():
    """Install required spaCy language models."""
    print("🧠 Installing spaCy language models...")
    
    # Activate virtual environment and install spaCy models
    if platform.system() == "Windows":
        python_path = ".venv\\Scripts\\python.exe"
    else:
        python_path = ".venv/bin/python"
    
    subprocess.run([
        python_path, "-m", "spacy",
        "download", "en_core_web_sm"
    ], check=True)
    
    print("✅ spaCy models installed!")


def generate_requirements_txt():
    """Generate requirements.txt from current environment (for Docker/legacy systems)."""
    print("📝 Generating requirements.txt for compatibility...")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Export current environment to requirements.txt
    subprocess.run([
        "uv", "pip", "freeze", ">", "requirements.txt"
    ], shell=True, check=True)
    
    print("✅ requirements.txt generated!")


def setup_pre_commit():
    """Setup pre-commit hooks for code quality."""
    print("🎣 Setting up pre-commit hooks...")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if platform.system() == "Windows":
        python_path = ".venv\\Scripts\\python.exe"
    else:
        python_path = ".venv/bin/python"
    
    subprocess.run([
        python_path, "-m", "pre_commit", "install"
    ], check=True)
    
    print("✅ Pre-commit hooks installed!")


def verify_installation():
    """Verify all components are properly installed."""
    print("\n🔍 Verifying installation...")
    
    checks = {
        "UV": ["uv", "--version"],
        "Python": ["python", "--version"],
        "FastAPI": ["python", "-c", "import fastapi; print(f'FastAPI {fastapi.__version__}')"],
        "Pydantic": ["python", "-c", "import pydantic; print(f'Pydantic {pydantic.__version__}')"],
        "SQLAlchemy": ["python", "-c", "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"],
    }
    
    if platform.system() == "Windows":
        python_cmd = ".venv\\Scripts\\python.exe"
    else:
        python_cmd = ".venv/bin/python"
    
    # Update Python commands
    for key in ["FastAPI", "Pydantic", "SQLAlchemy"]:
        checks[key][0] = python_cmd
    
    all_passed = True
    for component, cmd in checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ {component}: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            print(f"❌ {component}: Not found or error")
            all_passed = False
    
    return all_passed


def main():
    """Main setup orchestration."""
    print("🚀 Certify Studio Enterprise Setup")
    print("=" * 50)
    
    # Check and install UV if needed
    if not check_uv_installed():
        install_uv()
    
    # Setup virtual environment
    setup_virtual_environment()
    
    # Sync all dependencies
    sync_dependencies()
    
    # Install additional models
    install_spacy_models()
    
    # Setup development tools
    setup_pre_commit()
    
    # Optional: Generate requirements.txt for compatibility
    # generate_requirements_txt()
    
    # Verify installation
    if verify_installation():
        print("\n✅ Setup completed successfully!")
        print("\n📚 Next steps:")
        print("1. Activate the virtual environment:")
        if platform.system() == "Windows":
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")
        print("2. Run the development server:")
        print("   python scripts/dev.py api")
        print("3. Visit http://localhost:8000/docs for API documentation")
    else:
        print("\n⚠️  Setup completed with warnings. Check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
