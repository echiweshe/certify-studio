#!/usr/bin/env python
"""
Install missing dependencies script.
Quick fix for any missing packages.
"""

import subprocess
import sys
from pathlib import Path


def install_missing_deps():
    """Install any missing dependencies."""
    project_root = Path(__file__).parent.parent
    
    # Determine Python path
    if sys.platform == "win32":
        python_path = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        python_path = project_root / ".venv" / "bin" / "python"
    
    print("📦 Installing missing dependencies...")
    
    # Install aiosqlite for development database
    subprocess.run([
        str(python_path), "-m", "pip", "install", "aiosqlite"
    ], check=True)
    
    print("✅ Dependencies installed!")


if __name__ == "__main__":
    install_missing_deps()
