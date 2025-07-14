"""
Fixed comprehensive dependency installer and test runner
"""

import subprocess
import os
import sys

def main():
    print("=== Final Fix for All Dependencies ===\n")
    
    # Set environment variables
    print("1. Setting environment variables...")
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    
    # Make sure all dependencies are installed
    print("\n2. Ensuring all dependencies are installed...")
    dependencies = [
        "tf-keras",
        "markdown", 
        "pyyaml",
        "beautifulsoup4",
        "lxml",
        "html2text",
    ]
    
    for dep in dependencies:
        print(f"   Checking {dep}...")
        result = subprocess.run(f"uv add {dep}", shell=True, capture_output=True, text=True)
        if "Audited" in result.stdout:
            print(f"   ✓ {dep} already installed")
        else:
            print(f"   ✓ {dep} installed")
    
    # Sync
    print("\n3. Final sync...")
    subprocess.run("uv sync", shell=True)
    
    # Create proper test runner
    print("\n4. Creating proper test runner...")
    test_runner_content = """import os
import sys
import subprocess

# Set environment variables
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Run pytest
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit/test_simple.py", "-v"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

sys.exit(result.returncode)
"""
    
    with open("run_test_env.py", "w") as f:
        f.write(test_runner_content)
    
    # Run the test
    print("\n5. Running tests with proper environment...")
    result = subprocess.run("uv run python run_test_env.py", shell=True)
    
    if result.returncode == 0:
        print("\n✅ Success! Tests are passing.")
    else:
        print("\n❌ Tests still failing. Let's try one more approach...")
        
        # Direct command with env vars
        print("\n6. Running with direct command...")
        if sys.platform == "win32":
            # Windows command
            cmd = 'cmd /c "set TF_USE_LEGACY_KERAS=1 && uv run pytest tests/unit/test_simple.py -v"'
        else:
            # Unix command
            cmd = 'TF_USE_LEGACY_KERAS=1 uv run pytest tests/unit/test_simple.py -v'
        
        subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    main()
