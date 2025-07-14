"""
Quick install for accessibility dependencies
"""

import subprocess
import sys

packages = [
    "pyttsx3",  # Text-to-speech
    "webvtt-py",  # WebVTT captions
]

for package in packages:
    print(f"Installing {package}...")
    subprocess.run([sys.executable, "-m", "pip", "install", package])

print("Done!")
