"""
Test database connection
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from pathlib import Path

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./certify_studio.db")


async def test_database_connection():
    """Test database connection and basic operations"""
    print(f"Testing database connection to: {DATABASE_URL}")
    
    try:
        # Create engine
        engine = create_async_engine(
            DATABASE_URL,
            echo=True,  # Enable SQL logging
            future=True
        )
        
        # Test connection
        async with engine.begin() as conn:
            # Simple query to test connection
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1
            print("✓ Database connection successful")
            
            # Check if we can query tables (if they exist)
            try:
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = result.fetchall()
                print(f"✓ Found {len(tables)} tables in database")
                for table in tables:
                    print(f"  - {table[0]}")
            except Exception as e:
                print(f"  Note: Could not list tables: {e}")
        
        # Test session creation
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Test transaction
            result = await session.execute(text("SELECT 1 + 1"))
            value = result.scalar()
            assert value == 2
            print("✓ Session and transaction test successful")
        
        # Close engine
        await engine.dispose()
        print("\n✅ All database tests passed!")
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the database is running")
        print("2. Check DATABASE_URL environment variable")
        print("3. For SQLite, ensure the database file is accessible")
        print(f"4. Current working directory: {os.getcwd()}")
        
        # Create database file if using SQLite and it doesn't exist
        if "sqlite" in DATABASE_URL:
            db_path = DATABASE_URL.split("///")[-1]
            if not os.path.exists(db_path):
                print(f"\nCreating SQLite database at: {db_path}")
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                Path(db_path).touch()
                print("Database file created. Please run migrations.")
        
        raise


async def test_database_models():
    """Test database models if they exist"""
    try:
        from certify_studio.database.models import User, GenerationJob
        print("\n✓ Database models imported successfully")
        
        # You can add more model tests here
        
    except ImportError as e:
        print(f"\n⚠️  Could not import models: {e}")
        print("This is normal if models haven't been created yet")


async def main():
    """Run all database tests"""
    print("=" * 60)
    print("Certify Studio - Database Connection Test")
    print("=" * 60)
    
    # Test connection
    await test_database_connection()
    
    # Test models
    await test_database_models()
    
    print("\n" + "=" * 60)
    print("Database tests completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
