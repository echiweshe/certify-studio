"""
Quick dependency installer for missing packages
"""

import subprocess
import sys

packages = [
    "librosa",
    "numba",  # Required by librosa
    "soundfile",  # Required by librosa
]

print("Installing missing audio packages for Python 3.12...")

for package in packages:
    print(f"\nInstalling {package}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        print(f"✅ {package} installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")

print("\nDone! Try running the server again.")
