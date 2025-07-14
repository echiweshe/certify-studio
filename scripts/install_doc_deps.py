"""
Install missing dependencies
"""

import subprocess
import sys

packages = [
    "pypdf",  # Modern PDF library (replaces PyPDF2)
    "python-docx",  # For DOCX processing
    "ebooklib",  # For EPUB processing
    "pytesseract",  # For OCR (optional)
    "pdf2image",  # For PDF to image conversion
]

print("Installing missing document processing packages...")

for package in packages:
    print(f"\nInstalling {package}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        print(f"✅ {package} installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")

print("\nDone! Try running the server again.")
