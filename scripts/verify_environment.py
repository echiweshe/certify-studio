"""
Environment Verification Script for Certify Studio
Checks dependencies and compatibility
"""

import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 13):
        print("⚠️  Python 3.13+ detected - some scientific packages may have compatibility issues")
    elif version >= (3, 11):
        print("✅ Python version is compatible")
    else:
        print("❌ Python 3.11+ required")
    
    return version

def check_package(package_name: str, import_name: str = None) -> bool:
    """Check if a package is installed and can be imported"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name}: {str(e)}")
        return False

def check_core_dependencies():
    """Check core dependencies"""
    print("\n=== Core Dependencies ===")
    
    core_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("sqlalchemy", "sqlalchemy"),
        ("redis", "redis"),
        ("celery", "celery"),
    ]
    
    return all(check_package(pkg, imp) for pkg, imp in core_packages)

def check_ai_dependencies():
    """Check AI/ML dependencies"""
    print("\n=== AI/ML Dependencies ===")
    
    ai_packages = [
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("langchain", "langchain"),
        ("torch", "torch"),
        ("numpy", "numpy"),
        ("sentence-transformers", "sentence_transformers"),
    ]
    
    return all(check_package(pkg, imp) for pkg, imp in ai_packages)

def check_audio_dependencies():
    """Check audio processing dependencies"""
    print("\n=== Audio Dependencies ===")
    
    audio_packages = [
        ("soundfile", "soundfile"),
        ("pydub", "pydub"),
        ("scipy", "scipy"),
        ("webrtcvad", "webrtcvad"),
    ]
    
    all_good = True
    for pkg, imp in audio_packages:
        all_good &= check_package(pkg, imp)
    
    # Check optional packages
    print("\n--- Optional Audio Packages ---")
    check_package("librosa", "librosa")
    check_package("torchaudio", "torchaudio")
    
    return all_good

def check_document_dependencies():
    """Check document processing dependencies"""
    print("\n=== Document Processing Dependencies ===")
    
    doc_packages = [
        ("pypdf", "pypdf"),
        ("python-docx", "docx"),
        ("beautifulsoup4", "bs4"),
        ("markdown", "markdown"),
        ("ebooklib", "ebooklib"),
    ]
    
    return all(check_package(pkg, imp) for pkg, imp in doc_packages)

def check_media_dependencies():
    """Check media generation dependencies"""
    print("\n=== Media Dependencies ===")
    
    media_packages = [
        ("opencv-python", "cv2"),
        ("pillow", "PIL"),
        ("matplotlib", "matplotlib"),
        ("manim", "manim"),
        ("moviepy", "moviepy"),
        ("imageio", "imageio"),
    ]
    
    return all(check_package(pkg, imp) for pkg, imp in media_packages)

def check_certify_studio_modules():
    """Check if Certify Studio modules can be imported"""
    print("\n=== Certify Studio Modules ===")
    
    modules = [
        "certify_studio",
        "certify_studio.core",
        "certify_studio.api",
        "certify_studio.media.audio",
        "certify_studio.domain",
        "certify_studio.knowledge",
    ]
    
    all_good = True
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {str(e)}")
            all_good = False
    
    return all_good

def suggest_fixes(python_version):
    """Suggest fixes based on the environment"""
    print("\n=== Recommendations ===")
    
    if python_version >= (3, 13):
        print("""
⚠️  Python 3.13 Compatibility Notes:
- Some scientific packages (librosa, torchaudio) are not yet compatible
- We've implemented fallback solutions for audio processing
- The platform will work without these packages
""")
    
    print("""
To fix missing dependencies:
1. Run: uv sync --all-extras
2. If that fails, try: python scripts/clean_and_sync.py
3. For specific packages: uv pip install <package-name>
""")

def main():
    """Main verification routine"""
    print("=== Certify Studio Environment Verification ===\n")
    
    # Check Python version
    python_version = check_python_version()
    
    # Check dependencies
    core_ok = check_core_dependencies()
    ai_ok = check_ai_dependencies()
    audio_ok = check_audio_dependencies()
    doc_ok = check_document_dependencies()
    media_ok = check_media_dependencies()
    modules_ok = check_certify_studio_modules()
    
    # Summary
    print("\n=== Summary ===")
    print(f"Core Dependencies: {'✅' if core_ok else '❌'}")
    print(f"AI/ML Dependencies: {'✅' if ai_ok else '❌'}")
    print(f"Audio Dependencies: {'✅' if audio_ok else '❌'}")
    print(f"Document Dependencies: {'✅' if doc_ok else '❌'}")
    print(f"Media Dependencies: {'✅' if media_ok else '❌'}")
    print(f"Certify Studio Modules: {'✅' if modules_ok else '❌'}")
    
    # Recommendations
    suggest_fixes(python_version)
    
    if all([core_ok, ai_ok, audio_ok, doc_ok, media_ok, modules_ok]):
        print("\n✅ All dependencies are installed! You can run the application.")
    else:
        print("\n❌ Some dependencies are missing. Please install them before running.")

if __name__ == "__main__":
    main()
