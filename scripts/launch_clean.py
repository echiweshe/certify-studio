"""
Certify Studio - Enterprise Launch Script with Warning Suppression
Handles deprecation warnings from dependencies
"""

import sys
import os
import warnings
import logging
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*langchain-community.*")

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment
os.environ['CERTIFY_STUDIO_ENV'] = 'development'
os.environ['PYTHONPATH'] = str(project_root / "src")

# Configure logging to suppress deprecation warnings
logging.captureWarnings(True)
logging.getLogger("py.warnings").setLevel(logging.ERROR)

print("=" * 60)
print("🚀 CERTIFY STUDIO - Enterprise Platform")
print("=" * 60)
print(f"Python: {sys.version}")
print(f"Project: {project_root}")
print("=" * 60)

async def main():
    """Main startup routine"""
    try:
        # Import and configure the application
        from certify_studio.config import get_settings
        settings = get_settings()
        
        # Override settings for development
        settings.HOST = "0.0.0.0"
        settings.PORT = 8000
        settings.DEBUG = True
        
        print(f"\n🌐 Starting server on http://{settings.HOST}:{settings.PORT}")
        print("📚 API Docs: http://localhost:8000/docs")
        print("❤️  Health: http://localhost:8000/health")
        print("\nPress Ctrl+C to stop\n")
        
        # Run the server
        import uvicorn
        await uvicorn.Server(
            uvicorn.Config(
                "certify_studio.main:app",
                host=settings.HOST,
                port=settings.PORT,
                reload=True,
                log_level="info"
            )
        ).serve()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
