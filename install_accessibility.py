"""
Install all potentially missing dependencies for accessibility features
"""

import subprocess

def install_accessibility_deps():
    """Install all accessibility-related dependencies."""
    
    print("=== Installing Accessibility Dependencies ===\n")
    
    deps = [
        "webvtt-py",  # For WebVTT caption files
        "pycaption",  # For caption format conversion
        "speechrecognition",  # For audio transcription
        "pydub",  # For audio processing
        "mutagen",  # For audio metadata
    ]
    
    for dep in deps:
        print(f"Installing {dep}...")
        result = subprocess.run(f"uv add {dep}", shell=True, capture_output=True, text=True)
        if "Audited" in result.stdout or result.returncode == 0:
            print(f"✓ {dep} installed/verified")
        else:
            print(f"✗ Failed to install {dep}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
    
    print("\nSyncing...")
    subprocess.run("uv sync", shell=True)
    
    print("\nRunning tests...")
    import os
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    subprocess.run("uv run pytest tests/unit/test_simple.py -v", shell=True)

if __name__ == "__main__":
    install_accessibility_deps()
