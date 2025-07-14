"""
Check all dependencies and fix missing ones
"""

import subprocess
import importlib
import sys

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✓ {module_name} is available")
        return True
    except ImportError:
        print(f"✗ {module_name} is missing")
        if package_name:
            print(f"  Installing {package_name}...")
            subprocess.run(f"uv add {package_name}", shell=True)
        return False

def main():
    print("=== Checking All Dependencies ===\n")
    
    # Core dependencies
    print("1. Core Dependencies:")
    check_import("sqlalchemy", "sqlalchemy>=2.0.23")
    check_import("pydantic")
    check_import("pydantic_settings", "pydantic-settings>=2.0.0")
    check_import("fastapi")
    check_import("uvicorn")
    
    # Authentication
    print("\n2. Authentication Dependencies:")
    check_import("jose", "python-jose[cryptography]")
    check_import("passlib", "passlib[bcrypt]")
    check_import("jwt", "python-jose[cryptography]")
    
    # AI/ML
    print("\n3. AI/ML Dependencies:")
    check_import("openai")
    check_import("anthropic")
    check_import("langchain")
    check_import("langchain_anthropic")
    check_import("langchain_openai")
    check_import("langchain_core")
    check_import("langchain_community")
    
    # Media processing
    print("\n4. Media Processing:")
    check_import("PIL", "pillow")
    check_import("soundfile", "soundfile")
    check_import("numpy")
    check_import("cv2", "opencv-python")
    
    # Background tasks
    print("\n5. Background Tasks:")
    check_import("celery")
    check_import("redis")
    check_import("kombu")
    
    # Testing
    print("\n6. Testing Dependencies:")
    check_import("pytest")
    check_import("pytest_asyncio")
    
    # Final sync
    print("\n7. Final Sync:")
    subprocess.run("uv sync", shell=True)
    
    # Test the simple test
    print("\n8. Running Simple Test:")
    result = subprocess.run(
        "uv run pytest tests/unit/test_simple.py -v",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✅ All dependencies installed and tests passing!")
    else:
        print("\n❌ Tests still failing:")
        print(result.stdout)
        print(result.stderr)

if __name__ == "__main__":
    main()
