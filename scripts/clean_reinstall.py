"""
Clean UV cache and reinstall dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent

print("🧹 Cleaning UV cache and lock files...")

# Remove lock file
lock_file = project_root / "uv.lock"
if lock_file.exists():
    print(f"Removing {lock_file}")
    lock_file.unlink()

# Clear UV cache
print("Clearing UV cache...")
subprocess.run([sys.executable, "-m", "uv", "cache", "clean"], check=True)

# Sync dependencies
print("\n📦 Installing dependencies...")
result = subprocess.run(
    [sys.executable, "-m", "uv", "sync", "--all-extras"],
    cwd=project_root,
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Dependencies installed successfully!")
else:
    print("❌ Failed to install dependencies:")
    print(result.stderr)
    sys.exit(1)

print("\n🚀 Ready to launch! Run: uv run python scripts/launch.py")
