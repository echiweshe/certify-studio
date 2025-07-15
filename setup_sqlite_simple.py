"""
Simple Database Setup
====================
Minimal database initialization for SQLite.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from certify_studio.config import settings

async def setup_sqlite():
    """Simple SQLite setup"""
    print(f"Setting up SQLite database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Create engine directly
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    try:
        # Import all models to register them
        from certify_studio.database.models import Base
        from certify_studio.database.models.auth import User, Role, Permission
        from certify_studio.database.models.content import ContentGeneration, ContentPiece
        from certify_studio.database.models.analytics import GenerationAnalytics
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tables created!")
            
            # Verify
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = result.fetchall()
            print(f"\nCreated {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_sqlite())
