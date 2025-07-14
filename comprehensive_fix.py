"""
Comprehensive fix for all dependency issues
"""

import subprocess
import os
import sys

def set_env_and_run():
    """Set environment variables and run tests."""
    
    print("=== Comprehensive Dependency Fix ===\n")
    
    # Set environment variables
    print("1. Setting environment variables...")
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN custom operations
    
    # Install tf-keras
    print("\n2. Installing tf-keras...")
    subprocess.run("uv add tf-keras", shell=True)
    
    # Install any other missing packages we've discovered
    print("\n3. Installing other missing packages...")
    missing_packages = [
        "markdown",
        "pyyaml",
        "beautifulsoup4",
        "lxml",
        "html2text",
    ]
    
    for package in missing_packages:
        print(f"   Installing {package}...")
        subprocess.run(f"uv add {package}", shell=True)
    
    # Sync
    print("\n4. Syncing dependencies...")
    subprocess.run("uv sync", shell=True)
    
    # Create a test runner script that sets env vars
    print("\n5. Creating test runner with env vars...")
    test_runner = '''
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import subprocess
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit/test_simple.py", "-v"],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)
'''
    
    with open("run_test_with_env.py", "w") as f:
        f.write(test_runner)
    
    # Run the test
    print("\n6. Running tests with environment variables set...")
    subprocess.run("uv run python run_test_with_env.py", shell=True)
    
    # Alternative: Run directly with env vars
    print("\n7. Alternative test run...")
    if sys.platform == "win32":
        cmd = 'set "TF_USE_LEGACY_KERAS=1" && uv run pytest tests/unit/test_simple.py -v'
    else:
        cmd = 'TF_USE_LEGACY_KERAS=1 uv run pytest tests/unit/test_simple.py -v'
    
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    set_env_and_run()
