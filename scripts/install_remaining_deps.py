"""
Install remaining missing packages
"""

import subprocess
import sys

packages = [
    "webvtt-py",  # For WebVTT caption files
    "pillow",  # For image processing (PIL)
    "networkx",  # For graph operations
    "pyvis",  # For graph visualization
    "matplotlib",  # For plotting
    "seaborn",  # For statistical plots
    "opencv-python",  # For computer vision
    "moviepy",  # For video processing
    "manim",  # For mathematical animations
]

print("Installing missing packages...")

for package in packages:
    print(f"\nInstalling {package}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        print(f"✅ {package} installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install {package}: {e}")
        print("   (This package might be optional)")

print("\nDone! Try running the server again.")
