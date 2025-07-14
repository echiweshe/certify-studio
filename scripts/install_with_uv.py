"""
Install packages using UV
"""

import subprocess
import sys

packages = [
    "pyttsx3",  # Text-to-speech
    "webvtt-py",  # WebVTT captions
]

for package in packages:
    print(f"Installing {package}...")
    try:
        subprocess.run(["uv", "pip", "install", package], check=True)
        print(f"✅ {package} installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")

print("\nDone!")
