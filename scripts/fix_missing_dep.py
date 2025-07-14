"""
Quick fix for missing dependencies
"""

import subprocess
import sys

print("Installing missing dependency: itsdangerous")

try:
    subprocess.run([sys.executable, "-m", "pip", "install", "itsdangerous>=2.1.2"], check=True)
    print("✅ itsdangerous installed successfully")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to install: {e}")
    sys.exit(1)

print("\nYou can now run: uv run python scripts/launch.py")
