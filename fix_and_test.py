"""
Fix Dependencies and Run Tests Script
"""

import subprocess
import sys
import os
from pathlib import Path

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
    """Main script to fix dependencies and run tests."""
    
    print("=== Certify Studio Dependency Fix and Test Runner ===")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Step 1: Install missing dependencies
    print("\n1. Installing missing dependencies...")
    packages = [
        "langchain-anthropic",
        "langchain-openai", 
        "langchain-core",
        "langchain-community",
        "anthropic"
    ]
    
    for package in packages:
        run_command(f"uv add {package}", f"Installing {package}")
    
    # Step 2: Sync all dependencies
    print("\n2. Syncing all dependencies...")
    run_command("uv sync", "Dependency sync")
    
    # Step 3: Run the simple test
    print("\n3. Running simple test...")
    success = run_command(
        "uv run pytest tests/unit/test_simple.py -v", 
        "Running test_simple.py"
    )
    
    if success:
        print("\n✅ Tests passed! The environment is properly configured.")
        print("\nNext steps:")
        print("1. Run all unit tests: uv run pytest tests/unit/ -v")
        print("2. Run integration tests: uv run pytest tests/integration/ -v")
        print("3. Run all tests: uv run pytest -v")
    else:
        print("\n❌ Tests failed. Debugging information:")
        print("\nTrying to import modules directly...")
        
        # Try direct import to see specific error
        try:
            import certify_studio
            print("✓ certify_studio imports successfully")
        except Exception as e:
            print(f"✗ Failed to import certify_studio: {e}")
        
        try:
            from certify_studio.database.models import User
            print("✓ Database models import successfully")
        except Exception as e:
            print(f"✗ Failed to import database models: {e}")
        
        try:
            from certify_studio.integration import EventBus
            print("✓ Integration module imports successfully")
        except Exception as e:
            print(f"✗ Failed to import integration module: {e}")
            
        print("\nTroubleshooting suggestions:")
        print("1. Check if .venv is activated")
        print("2. Verify all dependencies are installed: uv pip list")
        print("3. Check for syntax errors in source files")
        print("4. Ensure PYTHONPATH includes the src directory")

if __name__ == "__main__":
    main()
