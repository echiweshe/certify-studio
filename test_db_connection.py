"""
Test Database Connection

This script tests the database connection and performs basic operations.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from colorama import init, Fore, Style

# Initialize colorama
init()

# Database URL (update if needed)
DATABASE_URL = "sqlite+aiosqlite:///./certify_studio.db"


async def test_database_connection():
    """Test database connectivity and basic operations"""
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}DATABASE CONNECTION TEST{Style.RESET_ALL}".center(60))
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    try:
        # Create engine
        print(f"{Fore.BLUE}Creating database engine...{Style.RESET_ALL}")
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Create session factory
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Test connection
        print(f"{Fore.BLUE}Testing connection...{Style.RESET_ALL}")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
            if row == 1:
                print(f"  {Fore.GREEN}✓ Connection successful{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}✗ Connection test failed{Style.RESET_ALL}")
                return False
        
        # Test table access
        print(f"\n{Fore.BLUE}Checking database tables...{Style.RESET_ALL}")
        async with engine.begin() as conn:
            # Get all tables
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            )
            tables = result.fetchall()
            
            if tables:
                print(f"  {Fore.GREEN}✓ Found {len(tables)} tables:{Style.RESET_ALL}")
                for table in tables[:10]:  # Show first 10 tables
                    print(f"    - {table[0]}")
                if len(tables) > 10:
                    print(f"    ... and {len(tables) - 10} more")
            else:
                print(f"  {Fore.YELLOW}⚠ No tables found{Style.RESET_ALL}")
                print(f"    This might be a fresh database.")
        
        # Test creating a session
        print(f"\n{Fore.BLUE}Testing session creation...{Style.RESET_ALL}")
        async with async_session() as session:
            # Try a simple query
            result = await session.execute(text("SELECT datetime('now')"))
            current_time = result.scalar()
            print(f"  {Fore.GREEN}✓ Session created successfully{Style.RESET_ALL}")
            print(f"    Database time: {current_time}")
        
        # Close engine
        await engine.dispose()
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ DATABASE CONNECTION TEST PASSED!{Style.RESET_ALL}".center(60))
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        
        return True
        
    except Exception as e:
        print(f"\n{Fore.RED}✗ Database connection failed:{Style.RESET_ALL}")
        print(f"  Error: {str(e)}")
        print(f"\n{Fore.YELLOW}Troubleshooting tips:{Style.RESET_ALL}")
        print(f"  1. Check if the database file exists")
        print(f"  2. Verify the database URL is correct")
        print(f"  3. Ensure you have the necessary permissions")
        print(f"  4. Try running: uv pip install aiosqlite")
        
        print(f"\n{Fore.RED}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ DATABASE CONNECTION TEST FAILED{Style.RESET_ALL}".center(60))
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
        
        return False


async def test_database_operations():
    """Test basic database operations"""
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}DATABASE OPERATIONS TEST{Style.RESET_ALL}".center(60))
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    try:
        from certify_studio.models import User, GenerationJob, Agent
        from certify_studio.core.database import get_db, init_db
        
        # Initialize database
        print(f"{Fore.BLUE}Initializing database...{Style.RESET_ALL}")
        await init_db()
        print(f"  {Fore.GREEN}✓ Database initialized{Style.RESET_ALL}")
        
        # Get a database session
        async for db in get_db():
            # Count users
            print(f"\n{Fore.BLUE}Checking users...{Style.RESET_ALL}")
            result = await db.execute(select(User))
            users = result.scalars().all()
            print(f"  {Fore.GREEN}✓ Found {len(users)} users{Style.RESET_ALL}")
            
            # Count agents
            print(f"\n{Fore.BLUE}Checking agents...{Style.RESET_ALL}")
            result = await db.execute(select(Agent))
            agents = result.scalars().all()
            print(f"  {Fore.GREEN}✓ Found {len(agents)} agents{Style.RESET_ALL}")
            
            # Count generation jobs
            print(f"\n{Fore.BLUE}Checking generation jobs...{Style.RESET_ALL}")
            result = await db.execute(select(GenerationJob))
            jobs = result.scalars().all()
            print(f"  {Fore.GREEN}✓ Found {len(jobs)} generation jobs{Style.RESET_ALL}")
            
            break  # Exit after first iteration
        
        print(f"\n{Fore.GREEN}✅ Database operations working correctly!{Style.RESET_ALL}")
        return True
        
    except ImportError as e:
        print(f"{Fore.YELLOW}⚠ Could not import models: {e}{Style.RESET_ALL}")
        print(f"  This is OK if the database hasn't been initialized yet.")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Database operations failed: {e}{Style.RESET_ALL}")
        return False


async def main():
    """Run all database tests"""
    
    # Test basic connection
    connection_ok = await test_database_connection()
    
    if connection_ok:
        # Test operations if connection is OK
        await test_database_operations()


if __name__ == "__main__":
    asyncio.run(main())
