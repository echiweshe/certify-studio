"""
Fix Keras compatibility issue
"""

import subprocess

def fix_keras_issue():
    print("=== Fixing Keras Compatibility Issue ===\n")
    
    # First, let's install tf-keras as suggested
    print("1. Installing tf-keras for backwards compatibility...")
    subprocess.run("uv add tf-keras", shell=True)
    
    # We might also need to ensure we have the right TensorFlow version
    print("\n2. Checking TensorFlow installation...")
    subprocess.run("uv add tensorflow", shell=True)
    
    # Set environment variable to use tf-keras
    print("\n3. Setting environment variable...")
    import os
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    
    # Sync dependencies
    print("\n4. Syncing dependencies...")
    subprocess.run("uv sync", shell=True)
    
    # Try running tests again
    print("\n5. Running tests...")
    result = subprocess.run(
        "uv run pytest tests/unit/test_simple.py -v",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    if result.returncode != 0:
        print("\nIf still failing, trying alternative approach...")
        
        # Alternative: Set environment variable permanently for this session
        print("\n6. Setting TF_USE_LEGACY_KERAS=1 environment variable...")
        subprocess.run('set TF_USE_LEGACY_KERAS=1 && uv run pytest tests/unit/test_simple.py -v', shell=True)

if __name__ == "__main__":
    fix_keras_issue()
