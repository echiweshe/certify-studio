"""
Certify Studio - Enterprise Launch Script
Handles Python 3.13 compatibility and graceful startup
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("certify-studio-launcher")

def print_banner():
    """Display startup banner"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                   CERTIFY STUDIO                              ║
║         AI-Powered Educational Content Platform               ║
╠═══════════════════════════════════════════════════════════════╣
║  🚀 Enterprise-Grade • Production-Ready • Domain-Agnostic     ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    print(f"Python Version: {sys.version}")
    print(f"Project Root: {project_root}\n")

def check_python_compatibility():
    """Check Python version and warn about compatibility"""
    version = sys.version_info
    
    if version < (3, 11):
        logger.error("❌ Python 3.11+ is required")
        sys.exit(1)
    
    if version >= (3, 13):
        logger.warning("⚠️  Python 3.13+ detected")
        logger.warning("   Some scientific packages have limited compatibility")
        logger.info("✅ Using fallback implementations where needed")
        print()

def ensure_environment():
    """Ensure environment is properly configured"""
    # Set environment variables
    os.environ['CERTIFY_STUDIO_ENV'] = os.environ.get('CERTIFY_STUDIO_ENV', 'development')
    os.environ['PYTHONPATH'] = str(project_root / "src")
    
    # Development settings
    if os.environ['CERTIFY_STUDIO_ENV'] == 'development':
        os.environ['DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'INFO'
        
        # Use defaults for secrets in development
        if not os.environ.get('SECRET_KEY'):
            os.environ['SECRET_KEY'] = 'dev-secret-key-change-this'
        if not os.environ.get('JWT_SECRET_KEY'):
            os.environ['JWT_SECRET_KEY'] = 'dev-jwt-secret-change-this'

def check_dependencies():
    """Check if core dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        logger.info("✅ Core dependencies found")
        return True
    except ImportError as e:
        logger.warning(f"⚠️  Missing dependency: {e}")
        return False

def install_dependencies():
    """Install dependencies using UV"""
    logger.info("📦 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "uv", "sync", "--all-extras"],
            check=True,
            cwd=project_root
        )
        logger.info("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def start_server():
    """Start the FastAPI server"""
    try:
        logger.info("🚀 Starting Certify Studio server...")
        
        # Import here to ensure dependencies are installed
        import uvicorn
        from certify_studio.config import get_settings
        
        settings = get_settings()
        
        # Override for development
        if settings.ENVIRONMENT == 'development':
            host = "0.0.0.0"
            port = 8000
            reload = True
        else:
            host = settings.HOST
            port = settings.PORT
            reload = settings.DEBUG
        
        print(f"\n📡 Server starting on http://{host}:{port}")
        print(f"📚 API Documentation: http://localhost:{port}/docs")
        print(f"❤️  Health Check: http://localhost:{port}/health")
        print("\nPress Ctrl+C to stop the server\n")
        
        # Run the server
        uvicorn.run(
            "certify_studio.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main entry point"""
    # Show banner
    print_banner()
    
    # Check Python compatibility
    check_python_compatibility()
    
    # Setup environment
    ensure_environment()
    
    # Check and install dependencies if needed
    if not check_dependencies():
        install_dependencies()
    
    # Verify installation worked
    try:
        import certify_studio
        logger.info("✅ Certify Studio modules loaded successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import Certify Studio: {e}")
        logger.info("Try running: uv sync --all-extras")
        sys.exit(1)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
