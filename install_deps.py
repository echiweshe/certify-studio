"""
Install missing dependencies for Certify Studio
"""

import subprocess
import sys

def install_dependencies():
    """Install missing langchain dependencies."""
    
    packages = [
        "langchain-anthropic",
        "langchain-openai", 
        "langchain-core",
        "langchain-community",
        "anthropic"
    ]
    
    print("Installing missing langchain dependencies...")
    
    for package in packages:
        print(f"\nInstalling {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "uv", "add", package
            ])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            # Continue with other packages
    
    print("\nAll dependencies installation attempted.")
    print("\nYou can now run: uv run pytest tests/unit/test_simple.py -v")

if __name__ == "__main__":
    install_dependencies()
