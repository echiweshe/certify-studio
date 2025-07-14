"""
Run diagnostics and fix imports for Certify Studio.
"""

import subprocess
import sys
import os

def main():
    # Set PYTHONPATH
    os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')
    
    print("Running Certify Studio diagnostics...")
    print("=" * 50)
    
    # Run the diagnostic script
    result = subprocess.run(
        [sys.executable, "diagnose_imports.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    print("\n" + "=" * 50)
    print("Running basic test...")
    
    # Try to run a simple test
    test_result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/test_basic.py", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(test_result.stdout)
    if test_result.stderr:
        print("Test errors:")
        print(test_result.stderr)
    
    return test_result.returncode

if __name__ == "__main__":
    sys.exit(main())
