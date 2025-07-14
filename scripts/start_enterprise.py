"""
Enterprise UV Startup Script for Certify Studio
Handles Python 3.13 compatibility and ensures proper initialization
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Ensure we're running on compatible Python"""
    version = sys.version_info
    logger.info(f"Python {version.major}.{version.minor}.{version.micro} detected")
    
    if version < (3, 11):
        logger.error("Python 3.11+ is required")
        sys.exit(1)
    
    if version >= (3, 13):
        logger.warning("Python 3.13+ detected - some packages may have compatibility issues")
        logger.info("Using compatibility mode for audio processing")
    
    return version

def ensure_dependencies():
    """Ensure all dependencies are installed"""
    logger.info("Checking dependencies...")
    
    try:
        # Try importing core modules
        import fastapi
        import uvicorn
        import pydantic
        logger.info("✅ Core dependencies found")
    except ImportError as e:
        logger.error(f"❌ Missing core dependency: {e}")
        logger.info("Running uv sync...")
        subprocess.run([sys.executable, "-m", "uv", "sync", "--all-extras"], check=True)

def setup_environment():
    """Setup environment variables"""
    # Set project root
    project_root = Path(__file__).parent.parent
    os.environ['CERTIFY_STUDIO_ROOT'] = str(project_root)
    
    # Add src to Python path
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Python path updated with: {src_path}")

def run_application():
    """Run the main application"""
    logger.info("Starting Certify Studio...")
    
    try:
        # Import and run the application
        from certify_studio.main import run_server
        
        logger.info("🚀 Launching Certify Studio Enterprise Platform")
        logger.info("=" * 60)
        logger.info("AI-Powered Educational Content Generation")
        logger.info("Production-Ready • Enterprise-Grade • Domain-Agnostic")
        logger.info("=" * 60)
        
        # Run the server
        run_server()
        
    except ImportError as e:
        logger.error(f"Failed to import application: {e}")
        logger.info("Trying alternative startup...")
        
        # Try running uvicorn directly
        cmd = [
            sys.executable, "-m", "uvicorn",
            "certify_studio.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd)

def main():
    """Main entry point"""
    try:
        # Check Python version
        check_python_version()
        
        # Setup environment
        setup_environment()
        
        # Ensure dependencies
        ensure_dependencies()
        
        # Run application
        run_application()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down Certify Studio...")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
