"""
Final UV Enterprise Startup Script with Python 3.13 Compatibility
"""

import sys
import os
import subprocess
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment
os.environ['CERTIFY_STUDIO_ENV'] = 'development'
os.environ['PYTHONPATH'] = str(project_root / "src")

print("=" * 60)
print("🚀 CERTIFY STUDIO - Enterprise Platform")
print("=" * 60)
print(f"Python: {sys.version}")
print(f"Project: {project_root}")
print("=" * 60)

async def main():
    """Main startup routine"""
    try:
        # Check if we need to sync dependencies
        try:
            import fastapi
            import uvicorn
            print("✅ Core dependencies found")
        except ImportError:
            print("📦 Installing dependencies...")
            subprocess.run([sys.executable, "-m", "uv", "sync", "--all-extras"], check=True)
        
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
    # Handle Python 3.13 compatibility warning
    if sys.version_info >= (3, 13):
        print("⚠️  Python 3.13 detected - using compatibility mode")
        print("   Some audio features may be limited\n")
    
    # Run the async main
    asyncio.run(main())
