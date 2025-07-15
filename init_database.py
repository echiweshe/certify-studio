"""
Initialize Certify Studio Database
==================================
Creates all tables and initial data.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent / "src"))

from certify_studio.database import database_manager, Base
from certify_studio.database.models import *  # Import all models to register them
from certify_studio.config import settings
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize database with all tables"""
    print("🗄️ Initializing Certify Studio Database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        # Initialize database manager
        await database_manager.initialize()
        
        if not database_manager.engine:
            print("⚠️ Database not configured, using mock mode")
            return
        
        # Create all tables
        print("Creating database tables...")
        await database_manager.create_tables()
        
        # Verify tables were created
        async with database_manager.engine.begin() as conn:
            if "sqlite" in settings.DATABASE_URL:
                result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            else:
                result = await conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public';"
                ))
            tables = result.fetchall()
            
            print(f"\n✅ Successfully created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
                
        print("\n✅ Database initialization complete!")
        
        # Test database connection
        health_ok = await database_manager.health_check()
        if health_ok:
            print("✅ Database connection test passed!")
        else:
            print("❌ Database health check failed!")
            
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        logger.exception("Database initialization failed")
        raise
    finally:
        await database_manager.close()

async def create_test_data():
    """Create initial test data"""
    from certify_studio.services.auth_service import AuthService
    
    print("\n📝 Creating test data...")
    
    # Re-initialize database manager for this operation
    await database_manager.initialize()
    
    if not database_manager.async_session_maker:
        print("⚠️ Database not available for test data")
        return
    
    auth_service = AuthService()
    
    # Create test users
    test_users = [
        {
            "email": "admin@certify-studio.com",
            "password": "AdminPass123!",
            "full_name": "Admin User",
            "is_active": True,
            "is_superuser": True
        },
        {
            "email": "test@certify-studio.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False
        },
        {
            "email": "aws-test@certify-studio.com",
            "password": "AWSTest123!",
            "full_name": "AWS Test User",
            "is_active": True,
            "is_superuser": False
        }
    ]
    
    async with database_manager.get_session() as db:
        for user_data in test_users:
            try:
                # Check if user exists
                from sqlalchemy import select
                from certify_studio.database.models import User
                
                stmt = select(User).where(User.email == user_data["email"])
                result = await db.execute(stmt)
                existing = result.first()
                
                if not existing:
                    # Create user using auth service
                    user = await auth_service.create_user(
                        db,
                        email=user_data["email"],
                        password=user_data["password"],
                        full_name=user_data["full_name"]
                    )
                    
                    # Set admin status if needed
                    if user_data.get("is_superuser"):
                        user.is_superuser = True
                        await db.commit()
                    
                    print(f"   ✅ Created user: {user_data['email']}")
                else:
                    print(f"   ℹ️ User already exists: {user_data['email']}")
                    
            except Exception as e:
                print(f"   ⚠️ Could not create user {user_data['email']}: {e}")
                logger.exception(f"Failed to create user {user_data['email']}")
    
    await database_manager.close()
    print("\n✅ Test data creation complete!")

async def main():
    """Main function"""
    try:
        await init_database()
        
        # Ask if user wants to create test data
        if database_manager.engine:
            create_test = input("\nCreate test data? (y/n): ").lower().strip()
            if create_test == 'y':
                await create_test_data()
        
        print("\n🎉 Database setup complete! You can now run the tests.")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
