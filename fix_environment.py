"""
Fix environment and run tests properly with uv
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and report status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} successful")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"✗ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Exception during {description}: {e}")
        return False

def main():
    """Main script to fix environment and run tests."""
    
    print("=== Certify Studio Environment Fix ===")
    
    # Step 1: Install dev dependencies (including pytest)
    print("\n1. Installing dev dependencies (including pytest)...")
    run_command("uv sync --all-extras", "Installing all dependencies including dev extras")
    
    # Step 2: List installed packages using uv
    print("\n2. Checking installed packages...")
    print("\nLangchain packages:")
    run_command('uv pip list | findstr "langchain"', "Listing langchain packages")
    
    print("\nCore packages:")
    run_command('uv pip list | findstr "pytest sqlalchemy pydantic"', "Listing core packages")
    
    # Step 3: Run test imports with uv
    print("\n3. Testing imports with uv environment...")
    run_command("uv run python test_imports.py", "Testing imports")
    
    # Step 4: Run pytest
    print("\n4. Running pytest with uv...")
    success = run_command("uv run pytest tests/unit/test_simple.py -v", "Running tests")
    
    if not success:
        print("\n5. Attempting alternative test run...")
        run_command("uv run python -m pytest tests/unit/test_simple.py -v", "Running tests with python -m pytest")
    
    print("\n\n=== Additional Commands to Try ===")
    print("1. Check Python version in uv environment:")
    print("   uv run python --version")
    print("\n2. Check if pytest is installed:")
    print("   uv run python -c \"import pytest; print(pytest.__version__)\"")
    print("\n3. Run all tests:")
    print("   uv run pytest -v")
    print("\n4. If pytest is not found, install it directly:")
    print("   uv add --dev pytest pytest-asyncio pytest-cov")

if __name__ == "__main__":
    main()
