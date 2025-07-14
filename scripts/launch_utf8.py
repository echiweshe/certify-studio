"""
Launch with proper encoding
"""

import sys
import os
import asyncio
from pathlib import Path
import locale
import io

# Force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment
os.environ['CERTIFY_STUDIO_ENV'] = 'development'
os.environ['PYTHONPATH'] = str(project_root / "src")

print("=" * 60)
print("CERTIFY STUDIO - Enterprise Platform")
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
        
        print(f"\nStarting server on http://{settings.HOST}:{settings.PORT}")
        print("API Docs: http://localhost:8000/docs")
        print("Health: http://localhost:8000/health")
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
        print("\n\nShutting down gracefully...")
    except ImportError as e:
        print(f"\nImport Error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
