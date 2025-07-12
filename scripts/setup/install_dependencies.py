#!/usr/bin/env python3
"""
Certify Studio Setup Script

Comprehensive setup and initialization script for development and production.
Handles dependencies, database setup, asset downloads, and environment configuration.
"""

import os
import sys
import subprocess
import shutil
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional
import argparse

class SetupManager:
    """Manages Certify Studio setup and initialization."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent.parent
        self.requirements_met = True
        
    def check_system_requirements(self) -> bool:
        """Check if system meets requirements."""
        print("🔍 Checking system requirements...")
        
        requirements = {
            "python": {"command": ["python", "--version"], "min_version": "3.11"},
            "node": {"command": ["node", "--version"], "min_version": "18.0"},
            "docker": {"command": ["docker", "--version"], "min_version": "20.0"},
            "poetry": {"command": ["poetry", "--version"], "min_version": "1.0"},
            "ffmpeg": {"command": ["ffmpeg", "-version"], "min_version": "4.0"},
            "graphviz": {"command": ["dot", "-V"], "min_version": "2.0"}
        }
        
        for tool, config in requirements.items():
            if not self._check_command_exists(config["command"]):
                print(f"❌ {tool} not found or below minimum version {config['min_version']}")
                self.requirements_met = False
            else:
                print(f"✅ {tool} found")
        
        return self.requirements_met
    
    def _check_command_exists(self, command: List[str]) -> bool:
        """Check if command exists and is executable."""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def setup_python_environment(self):
        """Setup Python virtual environment and dependencies."""
        print("🐍 Setting up Python environment...")
        
        os.chdir(self.project_root)
        
        # Install Python dependencies with Poetry
        try:
            subprocess.run(["poetry", "install"], check=True)
            print("✅ Python dependencies installed")
            
            # Install pre-commit hooks if in development
            if self.environment == "development":
                subprocess.run(["poetry", "run", "pre-commit", "install"], check=True)
                print("✅ Pre-commit hooks installed")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python dependencies: {e}")
            sys.exit(1)
    
    def setup_frontend_environment(self):
        """Setup Node.js environment and dependencies."""
        print("⚛️ Setting up frontend environment...")
        
        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            print("⚠️ Frontend directory not found, skipping frontend setup")
            return
        
        os.chdir(frontend_dir)
        
        try:
            # Install Node.js dependencies
            subprocess.run(["npm", "install"], check=True)
            print("✅ Frontend dependencies installed")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            sys.exit(1)
        finally:
            os.chdir(self.project_root)
    
    def create_environment_file(self):
        """Create environment configuration file."""
        print("🔧 Creating environment configuration...")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            print("⚠️ .env file already exists, skipping creation")
            return
        
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your configuration")
        else:
            print("❌ .env.example not found")
    
    def create_directories(self):
        """Create necessary directories."""
        print("📁 Creating directory structure...")
        
        directories = [
            "logs",
            "temp", 
            "uploads",
            "exports",
            "assets/icons/aws",
            "assets/icons/azure", 
            "assets/icons/gcp",
            "assets/icons/kubernetes",
            "assets/templates",
            "assets/fonts",
            "assets/images",
            "assets/videos",
            "assets/audio"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {directory}")
    
    def download_assets(self):
        """Download cloud provider assets and icons."""
        print("🎨 Downloading cloud provider assets...")
        
        assets_config = {
            "aws": {
                "base_url": "https://d1.awsstatic.com/webteam/architecture-icons/q4-2022/",
                "icons": [
                    "Arch_Compute/64/Arch_Amazon-EC2_64.svg",
                    "Arch_Storage/64/Arch_Amazon-Simple-Storage-Service_64.svg",
                    "Arch_Database/64/Arch_Amazon-RDS_64.svg",
                    "Arch_Networking-Content-Delivery/64/Arch_Amazon-VPC_64.svg",
                ]
            }
        }
        
        for provider, config in assets_config.items():
            provider_dir = self.project_root / "assets" / "icons" / provider
            provider_dir.mkdir(parents=True, exist_ok=True)
            
            for icon_path in config["icons"]:
                icon_url = config["base_url"] + icon_path
                icon_filename = Path(icon_path).name
                local_path = provider_dir / icon_filename
                
                try:
                    urllib.request.urlretrieve(icon_url, local_path)
                    print(f"✅ Downloaded {provider}/{icon_filename}")
                except Exception as e:
                    print(f"⚠️ Failed to download {icon_filename}: {e}")
    
    def setup_database(self):
        """Setup database and run migrations."""
        print("🗄️ Setting up database...")
        
        if self.environment == "development":
            # Start Docker services for development
            try:
                subprocess.run(
                    ["docker-compose", "up", "-d", "postgres", "redis"], 
                    check=True,
                    cwd=self.project_root
                )
                print("✅ Database services started")
                
                # Wait for database to be ready
                import time
                print("⏳ Waiting for database to be ready...")
                time.sleep(10)
                
                # Run database migrations
                subprocess.run(
                    ["poetry", "run", "alembic", "upgrade", "head"],
                    check=True,
                    cwd=self.project_root / "src"
                )
                print("✅ Database migrations completed")
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Database setup failed: {e}")
                print("💡 Make sure Docker is running and try again")
    
    def generate_secrets(self):
        """Generate secure secrets for configuration."""
        print("🔐 Generating security keys...")
        
        import secrets
        import string
        
        def generate_key(length: int = 32) -> str:
            alphabet = string.ascii_letters + string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(length))
        
        secrets_file = self.project_root / "secrets.txt"
        with open(secrets_file, "w") as f:
            f.write("# Generated secrets for Certify Studio\n")
            f.write("# Copy these to your .env file\n\n")
            f.write(f"SECRET_KEY={generate_key(64)}\n")
            f.write(f"JWT_SECRET_KEY={generate_key(64)}\n") 
            f.write(f"ENCRYPTION_KEY={generate_key(32)}\n")
        
        print(f"✅ Security keys generated in {secrets_file}")
        print("📝 Copy these keys to your .env file")
    
    def validate_setup(self):
        """Validate that setup completed successfully."""
        print("✅ Validating setup...")
        
        validations = [
            ("Python environment", lambda: (self.project_root / "poetry.lock").exists()),
            ("Environment file", lambda: (self.project_root / ".env").exists()),
            ("Directory structure", lambda: (self.project_root / "logs").exists()),
            ("Assets directory", lambda: (self.project_root / "assets" / "icons").exists()),
        ]
        
        all_valid = True
        for name, check in validations:
            if check():
                print(f"✅ {name}")
            else:
                print(f"❌ {name}")
                all_valid = False
        
        return all_valid
    
    def print_next_steps(self):
        """Print next steps for the user."""
        print("\n🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your API keys and configuration")
        print("2. Start the development environment:")
        print("   make dev")
        print("3. Access the application:")
        print("   - Backend API: http://localhost:8000")
        print("   - API Documentation: http://localhost:8000/docs")
        print("   - Frontend: http://localhost:3000 (if enabled)")
        print("\n📚 Documentation:")
        print("   - Architecture: docs/architecture/README.md")
        print("   - Development: docs/development/README.md")
        print("   - User Guide: docs/user-guide/README.md")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Certify Studio Setup")
    parser.add_argument(
        "--environment", 
        choices=["development", "production", "testing"],
        default="development",
        help="Target environment"
    )
    parser.add_argument(
        "--skip-requirements",
        action="store_true", 
        help="Skip system requirements check"
    )
    parser.add_argument(
        "--skip-assets",
        action="store_true",
        help="Skip asset downloads"
    )
    parser.add_argument(
        "--skip-database",
        action="store_true",
        help="Skip database setup"
    )
    
    args = parser.parse_args()
    
    print("🚀 Certify Studio Setup")
    print(f"Environment: {args.environment}")
    print("-" * 50)
    
    setup = SetupManager(args.environment)
    
    try:
        # Check system requirements
        if not args.skip_requirements:
            if not setup.check_system_requirements():
                print("\n❌ System requirements not met")
                print("Please install missing dependencies and try again")
                sys.exit(1)
        
        # Create directories
        setup.create_directories()
        
        # Setup Python environment
        setup.setup_python_environment()
        
        # Setup frontend environment
        setup.setup_frontend_environment()
        
        # Create environment file
        setup.create_environment_file()
        
        # Generate secrets
        setup.generate_secrets()
        
        # Download assets
        if not args.skip_assets:
            setup.download_assets()
        
        # Setup database
        if not args.skip_database and args.environment == "development":
            setup.setup_database()
        
        # Validate setup
        if setup.validate_setup():
            setup.print_next_steps()
        else:
            print("\n❌ Setup validation failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
