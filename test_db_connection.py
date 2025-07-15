"""
Test PostgreSQL connection from the application context
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from pathlib import Path
from dotenv import load_dotenv

async def test_db_connection():
    # Load environment variables
    load_dotenv()
    
    # Get DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL found: {database_url}")
    
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False
    
    try:
        # Create async engine
        engine = create_async_engine(database_url, echo=True)
        
        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✓ Successfully connected to PostgreSQL!")
            
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'certify_studio'
            """))
            count = result.scalar()
            print(f"✓ Found {count} tables in certify_studio schema")
            
            # Check some data
            result = await conn.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM certify_studio.users) as users,
                    (SELECT COUNT(*) FROM certify_studio.agents) as agents
            """))
            row = result.fetchone()
            print(f"✓ Users: {row[0]}, Agents: {row[1]}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_db_connection())
