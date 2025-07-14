"""
Python 3.12 Setup Script for Certify Studio
Ensures compatibility with all required packages
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           CERTIFY STUDIO - Python 3.12 Setup                  ║
╠═══════════════════════════════════════════════════════════════╣
║  This script will help you set up Python 3.12 for full       ║
║  compatibility with all audio and ML libraries.               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

def check_current_python():
    """Check current Python version"""
    version = sys.version_info
    print(f"\nCurrent Python: {sys.version}")
    print(f"Python Path: {sys.executable}")
    
    if version.major == 3 and version.minor == 12:
        print("✅ Already running Python 3.12!")
        return True
    return False

def get_python_312_installer_url():
    """Get the appropriate Python 3.12 installer URL"""
    system = platform.system()
    machine = platform.machine()
    
    if system == "Windows":
        if machine.endswith('64'):
            return "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
        else:
            return "https://www.python.org/ftp/python/3.12.7/python-3.12.7.exe"
    elif system == "Darwin":  # macOS
        return "https://www.python.org/ftp/python/3.12.7/python-3.12.7-macos11.pkg"
    else:  # Linux
        return None

def install_with_pyenv():
    """Install Python 3.12 using pyenv (cross-platform)"""
    print("\n📦 Installing Python 3.12 using pyenv...")
    
    # Check if pyenv is installed
    try:
        subprocess.run(["pyenv", "--version"], check=True, capture_output=True)
        print("✅ pyenv found")
    except:
        print("❌ pyenv not found. Installing pyenv first...")
        
        if platform.system() == "Windows":
            print("""
Please install pyenv-win:
1. Open PowerShell as Administrator
2. Run: Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
3. Restart your terminal
4. Run this script again
            """)
            return False
        else:
            print("Installing pyenv...")
            subprocess.run(["curl", "-L", "https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer", "|", "bash"], shell=True)
    
    # Install Python 3.12
    try:
        print("Installing Python 3.12.7...")
        subprocess.run(["pyenv", "install", "3.12.7"], check=True)
        subprocess.run(["pyenv", "local", "3.12.7"], check=True)
        print("✅ Python 3.12.7 installed and set as local version")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python 3.12: {e}")
        return False

def create_venv_with_python312():
    """Create a virtual environment with Python 3.12"""
    print("\n🔧 Creating virtual environment with Python 3.12...")
    
    # Find Python 3.12
    python312_paths = [
        "python3.12",
        "python312",
        r"C:\Python312\python.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe",
        "/usr/bin/python3.12",
        "/usr/local/bin/python3.12",
    ]
    
    python312 = None
    for path in python312_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True)
            if "3.12" in result.stdout:
                python312 = path
                print(f"✅ Found Python 3.12 at: {path}")
                break
        except:
            continue
    
    if not python312:
        print("❌ Python 3.12 not found in common locations")
        return False
    
    # Create virtual environment
    venv_path = Path.cwd() / ".venv312"
    print(f"Creating virtual environment at {venv_path}...")
    
    try:
        subprocess.run([python312, "-m", "venv", str(venv_path)], check=True)
        print("✅ Virtual environment created")
        
        # Get activation command
        if platform.system() == "Windows":
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
        
        print(f"\n📌 To activate the environment, run:")
        print(f"   {activate_cmd}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def setup_with_uv():
    """Set up Python 3.12 with UV"""
    print("\n🚀 Setting up Python 3.12 with UV...")
    
    try:
        # Install Python 3.12 with UV
        print("Installing Python 3.12...")
        subprocess.run(["uv", "python", "install", "3.12"], check=True)
        
        # Create virtual environment with Python 3.12
        print("Creating virtual environment...")
        subprocess.run(["uv", "venv", "--python", "3.12"], check=True)
        
        # Sync dependencies
        print("Installing dependencies...")
        subprocess.run(["uv", "sync", "--all-extras"], check=True)
        
        print("✅ Python 3.12 environment set up successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ UV setup failed: {e}")
        return False

def main():
    """Main setup routine"""
    print_banner()
    
    # Check if already on Python 3.12
    if check_current_python():
        print("\nYou're already using Python 3.12!")
        print("Run: uv sync --all-extras")
        return
    
    print("\n🔍 Detecting best installation method...")
    
    # Try UV first (easiest)
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✅ UV detected - using UV for setup")
        if setup_with_uv():
            print("\n✅ Setup complete! Run: uv run python scripts/launch.py")
            return
    except:
        print("UV not found, trying other methods...")
    
    # Try pyenv
    if platform.system() != "Windows" or os.environ.get("PYENV"):
        if install_with_pyenv():
            create_venv_with_python312()
            return
    
    # Try direct venv creation
    if create_venv_with_python312():
        return
    
    # Manual instructions
    print("\n📋 Manual Installation Instructions:")
    
    installer_url = get_python_312_installer_url()
    if installer_url:
        print(f"\n1. Download Python 3.12 from:\n   {installer_url}")
        print("\n2. Install Python 3.12 (make sure to check 'Add to PATH')")
        print("\n3. Run this script again")
    else:
        print("\nFor Linux, use your package manager:")
        print("   Ubuntu/Debian: sudo apt install python3.12")
        print("   Fedora: sudo dnf install python3.12")
        print("   Arch: sudo pacman -S python312")

if __name__ == "__main__":
    main()
