"""
Quick database setup - Create tables and admin user directly.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from certify_studio.database.models import Base, User
from certify_studio.config import settings
from passlib.context import CryptContext
from sqlalchemy import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_async_db_url():
    """Get async database URL."""
    db_url = settings.DATABASE_URL
    if not db_url.startswith("postgresql+asyncpg://"):
        # Convert regular postgresql:// to postgresql+asyncpg://
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    return db_url


async def create_all():
    """Create tables and admin user in one go."""
    print("Setting up database...")
    
    # Get async database URL
    db_url = get_async_db_url()
    print(f"Using database URL: {db_url}")
    
    # Create engine
    engine = create_async_engine(db_url, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Created all database tables")
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create admin user
    async with async_session() as session:
        # Check if admin exists
        result = await session.execute(
            select(User).where(User.email == "admin@certifystudio.com")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            # Create admin user
            admin = User(
                email="admin@certifystudio.com",
                username="admin",
                hashed_password=pwd_context.hash("admin123"),
                full_name="System Administrator",
                is_admin=True,
                is_active=True,
                is_verified=True
            )
            session.add(admin)
            await session.commit()
            print("✓ Created admin user")
            print("  Email: admin@certifystudio.com")
            print("  Password: admin123")
        else:
            print("✓ Admin user already exists")
    
    await engine.dispose()


async def main():
    """Quick setup."""
    print("Quick Database Setup")
    print("===================")
    
    try:
        await create_all()
        print("\n✅ Setup complete! You can now log in.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Also update the .env to use async URL if needed
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        content = env_path.read_text()
        if "postgresql://" in content and "postgresql+asyncpg://" not in content:
            new_content = content.replace("postgresql://", "postgresql+asyncpg://")
            env_path.write_text(new_content)
            print("Updated .env to use async database URL")
    
    asyncio.run(main())
