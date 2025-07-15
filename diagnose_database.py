"""
Database Diagnostic Tool
========================
Checks database configuration and connectivity.
"""

import asyncio
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent / "src"))

from certify_studio.config import settings

def check_database_config():
    """Check database configuration"""
    print("🔍 Database Configuration Check")
    print("="*50)
    
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    
    # Check if it's SQLite
    if "sqlite" in settings.DATABASE_URL:
        print("\n📁 SQLite Database Configuration:")
        
        # Extract database file path
        db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("./", "")
        full_path = Path(__file__).parent / db_path
        
        print(f"Database file: {db_path}")
        print(f"Full path: {full_path}")
        
        # Check if database file exists
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ Database file exists (Size: {size:,} bytes)")
        else:
            print("❌ Database file does not exist (will be created on first run)")
            
            # Check if directory is writable
            parent_dir = full_path.parent
            if os.access(parent_dir, os.W_OK):
                print(f"✅ Directory is writable: {parent_dir}")
            else:
                print(f"❌ Directory is not writable: {parent_dir}")
    
    print("\n" + "="*50)

async def test_connection():
    """Test database connection"""
    from certify_studio.database import database_manager
    
    print("\n🧪 Testing Database Connection...")
    
    try:
        # Initialize database
        await database_manager.initialize()
        
        if not database_manager.engine:
            print("❌ Database engine not created (check configuration)")
            return False
        
        # Test health check
        is_healthy = await database_manager.health_check()
        
        if is_healthy:
            print("✅ Database connection successful!")
            
            # Try to query tables
            async with database_manager.engine.begin() as conn:
                from sqlalchemy import text
                
                if "sqlite" in settings.DATABASE_URL:
                    result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                    tables = result.fetchall()
                    
                    if tables:
                        print(f"\n📊 Found {len(tables)} existing tables:")
                        for table in tables[:5]:  # Show first 5
                            print(f"   - {table[0]}")
                        if len(tables) > 5:
                            print(f"   ... and {len(tables) - 5} more")
                    else:
                        print("\n⚠️ No tables found. Run database initialization.")
        else:
            print("❌ Database health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await database_manager.close()
    
    return True

async def main():
    """Main diagnostic function"""
    print("🏥 Certify Studio Database Diagnostics")
    print("="*50)
    
    # Check configuration
    check_database_config()
    
    # Test connection
    success = await test_connection()
    
    if success:
        print("\n✅ Database diagnostics passed!")
        print("Ready to run initialization or tests.")
    else:
        print("\n❌ Database diagnostics failed!")
        print("\nTroubleshooting tips:")
        print("1. Check DATABASE_URL in .env file")
        print("2. Ensure aiosqlite is installed: pip install aiosqlite")
        print("3. Check file permissions for SQLite database")
        print("4. Try running: init_database.bat")

if __name__ == "__main__":
    asyncio.run(main())
