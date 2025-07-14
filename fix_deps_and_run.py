"""
Complete solution to fix dependencies and run tests for Certify Studio
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Fix all dependencies and run tests."""
    
    print("=== Certify Studio Dependency Fix ===\n")
    
    # Step 1: First, let's install the missing packages
    print("Step 1: Installing missing langchain packages...")
    
    packages_to_install = [
        "langchain-anthropic",
        "langchain-openai",
        "langchain-core", 
        "langchain-community",
        "anthropic"
    ]
    
    for package in packages_to_install:
        print(f"\nInstalling {package}...")
        result = subprocess.run(
            f"uv add {package}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {package} installed successfully")
        else:
            print(f"✗ Failed to install {package}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
    
    # Step 2: Sync dependencies
    print("\n\nStep 2: Syncing all dependencies...")
    result = subprocess.run("uv sync", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Dependencies synced successfully")
    else:
        print("✗ Failed to sync dependencies")
        if result.stderr:
            print(f"  Error: {result.stderr}")
    
    # Step 3: Run the test
    print("\n\nStep 3: Running pytest...")
    print("Command: uv run pytest tests/unit/test_simple.py -v\n")
    
    # Run pytest with full output
    subprocess.run("uv run pytest tests/unit/test_simple.py -v", shell=True)
    
    print("\n\n=== Summary ===")
    print("If the tests still fail, try the following:")
    print("1. Run: python test_imports.py")
    print("   This will show which specific imports are failing")
    print("\n2. Run: uv pip list | grep langchain")
    print("   This will show all installed langchain packages")
    print("\n3. Make sure you're in the correct directory:")
    print(f"   Current directory: {os.getcwd()}")
    print("\n4. If imports still fail, the issue might be with the module structure")
    print("   or with missing __init__.py files in some directories")

if __name__ == "__main__":
    main()
