#!/usr/bin/env python
"""
Quick Start Script for Certify Studio
Simplified launcher for first-time setup and running.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Quick start the Certify Studio platform."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 Certify Studio Quick Start")
    print("=" * 50)
    
    # Check if virtual environment exists
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print("📦 First time setup detected. Installing dependencies...")
        print("This may take a few minutes...\n")
        
        # Run dependency setup
        subprocess.run([
            sys.executable,
            str(project_root / "scripts" / "setup_dependencies.py")
        ])
        print("\n✅ Dependencies installed!")
    
    # Activate virtual environment and run
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    print("\n🎯 Starting Certify Studio API...")
    print("-" * 50)
    print("📚 Once started, visit:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Health: http://localhost:8000/health")
    print("\n💡 Press Ctrl+C to stop\n")
    
    # Change to src directory for imports to work
    os.chdir(project_root / "src")
    
    # Run the API
    subprocess.run([
        str(python_path), "-m", "uvicorn",
        "certify_studio.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


if __name__ == "__main__":
    main()
