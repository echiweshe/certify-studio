"""
Database Connection Management

Handles database connection pooling, session management,
and provides async database operations using SQLAlchemy.
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from ..config import settings

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        
    async def initialize(self):
        """Initialize database engine and session maker."""
        logger.info("Initializing database connection...")
        
        # Create async engine
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before use
            # Use NullPool for serverless/Lambda deployments
            poolclass=NullPool if settings.ENVIRONMENT == "production" else None
        )
        
        # Create session maker
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Test connection
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
            
    async def health_check(self) -> bool:
        """Check database health."""
        if not self.engine:
            return False
            
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
            
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager."""
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized")
            
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                
    async def create_tables(self):
        """Create all database tables."""
        if not self.engine:
            raise RuntimeError("Database not initialized")
            
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database tables created")
        
    async def drop_tables(self):
        """Drop all database tables (use with caution)."""
        if not self.engine:
            raise RuntimeError("Database not initialized")
            
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
        logger.info("Database tables dropped")


# Create global database manager instance
database_manager = DatabaseManager()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with database_manager.get_session() as session:
        yield session
