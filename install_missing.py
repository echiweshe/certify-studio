"""
Install remaining missing dependencies
"""

import subprocess
import sys

def install_missing_deps():
    """Install the remaining missing dependencies."""
    
    print("=== Installing Missing Dependencies ===\n")
    
    missing_deps = [
        "python-jose[cryptography]",  # For JWT
        "soundfile",  # For audio processing
        "librosa",  # Often used with soundfile
    ]
    
    for dep in missing_deps:
        print(f"Installing {dep}...")
        result = subprocess.run(
            f"uv add {dep}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ {dep} installed successfully")
        else:
            print(f"✗ Failed to install {dep}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
    
    # Sync after adding
    print("\nSyncing dependencies...")
    subprocess.run("uv sync", shell=True)
    
    # Test imports again
    print("\n=== Testing Imports Again ===")
    subprocess.run("uv run python test_imports_uv.py", shell=True)
    
    # Run the tests
    print("\n=== Running Tests ===")
    subprocess.run("uv run pytest tests/unit/test_simple.py -v", shell=True)

if __name__ == "__main__":
    install_missing_deps()
