"""
Complete installation and test runner for Certify Studio
This ensures all dependencies are properly installed in the uv environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_cmd(cmd, description="Running command"):
    """Run a command and return success status."""
    print(f"\n{description}...")
    print(f"Command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Success")
        if result.stdout and result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    else:
        print(f"✗ Failed with code {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return False

def main():
    """Main installation and test routine."""
    
    print("=== Certify Studio Complete Setup ===")
    print(f"Working directory: {os.getcwd()}")
    
    # Step 1: Install ALL dependencies including dev
    print("\n📦 Step 1: Installing all dependencies...")
    
    # First, ensure we have the dev dependencies in pyproject.toml
    success = run_cmd(
        "uv add --dev pytest pytest-asyncio pytest-cov pytest-mock faker httpx",
        "Adding dev dependencies"
    )
    
    # Sync everything
    if success:
        run_cmd("uv sync --all-extras", "Syncing all dependencies")
    
    # Step 2: Verify installation
    print("\n🔍 Step 2: Verifying installation...")
    
    # Check Python version in uv
    run_cmd("uv run python --version", "Checking Python version")
    
    # Check if key packages are installed
    run_cmd(
        'uv run python -c "import sqlalchemy, pydantic, fastapi, pytest; print(\'Core packages OK\')"',
        "Checking core packages"
    )
    
    # Step 3: Run detailed import test
    print("\n🧪 Step 3: Running detailed import test...")
    success = run_cmd("uv run python test_imports_uv.py", "Testing all imports")
    
    if not success:
        print("\n⚠️  Import test failed. Attempting to fix missing dependencies...")
        
        # Install any missing core dependencies
        core_deps = [
            "sqlalchemy>=2.0.23",
            "pydantic>=2.5.0", 
            "pydantic-settings>=2.0.0",
            "fastapi>=0.104.0",
            "asyncpg>=0.29.0",
            "alembic>=1.12.1"
        ]
        
        for dep in core_deps:
            run_cmd(f"uv add {dep}", f"Installing {dep}")
        
        # Retry import test
        run_cmd("uv run python test_imports_uv.py", "Retrying import test")
    
    # Step 4: Run pytest
    print("\n🚀 Step 4: Running tests...")
    test_success = run_cmd(
        "uv run pytest tests/unit/test_simple.py -v",
        "Running unit tests"
    )
    
    if not test_success:
        print("\n Trying alternative test command...")
        run_cmd(
            "uv run python -m pytest tests/unit/test_simple.py -v",
            "Running tests with python -m pytest"
        )
    
    # Step 5: Summary
    print("\n\n📊 Summary")
    print("="*50)
    
    if test_success:
        print("✅ Setup complete! Tests are passing.")
        print("\nNext steps:")
        print("1. Run all unit tests: uv run pytest tests/unit/ -v")
        print("2. Run integration tests: uv run pytest tests/integration/ -v")
        print("3. Run with coverage: uv run pytest --cov=certify_studio --cov-report=html")
    else:
        print("⚠️  Setup complete but tests are not passing.")
        print("\nTroubleshooting:")
        print("1. Check imports: uv run python test_imports_uv.py")
        print("2. List packages: uv pip list")
        print("3. Check virtual env: uv venv")
        print("4. Reinstall everything: uv sync --reinstall")
    
    print("\n💡 Useful commands:")
    print("- Start API server: uv run python -m certify_studio.app")
    print("- Run specific test: uv run pytest path/to/test.py::test_name")
    print("- Run tests matching pattern: uv run pytest -k 'test_pattern'")
    print("- Run tests with output: uv run pytest -s")

if __name__ == "__main__":
    main()
