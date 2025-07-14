"""
Database session management utilities.

This module provides utilities for managing database sessions,
transactions, and connection pooling.
"""

from typing import AsyncGenerator, Optional, TypeVar, Type, List, Any
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload, contains_eager
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from loguru import logger

from .connection import database_manager
from .models.base import BaseModel, generate_uuid

T = TypeVar("T", bound=BaseModel)


class DatabaseSession:
    """Enhanced database session with utility methods."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, model: Type[T], id: Any) -> Optional[T]:
        """Get a single record by ID."""
        return await self.session.get(model, id)
    
    async def get_or_404(self, model: Type[T], id: Any) -> T:
        """Get a single record by ID or raise an exception."""
        result = await self.get(model, id)
        if not result:
            raise ValueError(f"{model.__name__} with id {id} not found")
        return result
    
    async def get_by(self, model: Type[T], **kwargs) -> Optional[T]:
        """Get a single record by field values."""
        query = select(model)
        for key, value in kwargs.items():
            query = query.where(getattr(model, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_many(
        self,
        model: Type[T],
        filters: Optional[List[Any]] = None,
        order_by: Optional[Any] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """Get multiple records with filtering and pagination."""
        query = select(model)
        
        if filters:
            query = query.where(and_(*filters))
        
        if order_by is not None:
            query = query.order_by(order_by)
        
        if limit:
            query = query.limit(limit)
        
        if offset:
            query = query.offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, model: Type[T], filters: Optional[List[Any]] = None) -> int:
        """Count records matching filters."""
        query = select(func.count()).select_from(model)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, model: Type[T], **kwargs) -> bool:
        """Check if a record exists."""
        query = select(func.count()).select_from(model)
        for key, value in kwargs.items():
            query = query.where(getattr(model, key) == value)
        query = query.limit(1)
        
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
    
    async def create(self, model: Type[T], **kwargs) -> T:
        """Create a new record."""
        instance = model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def update(self, instance: T, **kwargs) -> T:
        """Update an existing record."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance
    
    async def delete(self, instance: T) -> None:
        """Delete a record."""
        await self.session.delete(instance)
        await self.session.flush()
    
    async def bulk_create(self, model: Type[T], data: List[dict]) -> List[T]:
        """Create multiple records efficiently."""
        instances = [model(**item) for item in data]
        self.session.add_all(instances)
        await self.session.flush()
        return instances
    
    async def bulk_update(self, model: Type[T], data: List[dict]) -> None:
        """Update multiple records efficiently."""
        if not data:
            return
        
        await self.session.execute(
            update(model),
            data
        )
        await self.session.flush()
    
    async def execute_query(self, query: Any) -> Any:
        """Execute a raw query."""
        return await self.session.execute(query)
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()
    
    async def refresh(self, instance: T) -> None:
        """Refresh an instance from the database."""
        await self.session.refresh(instance)


class TransactionManager:
    """Manage database transactions with proper isolation."""
    
    @staticmethod
    @asynccontextmanager
    async def transaction(session: Optional[AsyncSession] = None):
        """Create a database transaction context."""
        if session:
            # Use existing session
            async with session.begin():
                yield DatabaseSession(session)
        else:
            # Create new session
            async with database_manager.get_session() as session:
                yield DatabaseSession(session)
    
    @staticmethod
    @asynccontextmanager
    async def savepoint(session: AsyncSession, name: Optional[str] = None):
        """Create a savepoint within a transaction."""
        if not name:
            name = f"sp_{generate_uuid().hex[:8]}"
        
        async with session.begin_nested() as savepoint:
            yield savepoint


class BatchProcessor:
    """Process database operations in batches for efficiency."""
    
    def __init__(self, session: AsyncSession, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size
        self.pending_creates = []
        self.pending_updates = []
    
    def add_create(self, model: Type[T], **kwargs):
        """Add a create operation to the batch."""
        self.pending_creates.append((model, kwargs))
    
    def add_update(self, instance: T, **kwargs):
        """Add an update operation to the batch."""
        self.pending_updates.append((instance, kwargs))
    
    async def flush(self):
        """Execute all pending batch operations."""
        # Process creates
        if self.pending_creates:
            creates_by_model = {}
            for model, data in self.pending_creates:
                if model not in creates_by_model:
                    creates_by_model[model] = []
                creates_by_model[model].append(data)
            
            for model, data_list in creates_by_model.items():
                for i in range(0, len(data_list), self.batch_size):
                    batch = data_list[i:i + self.batch_size]
                    instances = [model(**item) for item in batch]
                    self.session.add_all(instances)
                    await self.session.flush()
        
        # Process updates
        if self.pending_updates:
            for instance, data in self.pending_updates:
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
            await self.session.flush()
        
        # Clear pending operations
        self.pending_creates.clear()
        self.pending_updates.clear()


class RetryableTransaction:
    """Handle transient database errors with retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 0.1,
        exponential_backoff: bool = True
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
    
    async def execute(self, func, *args, **kwargs):
        """Execute a function with retry logic for database errors."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except IntegrityError as e:
                # Don't retry integrity errors
                raise
            except SQLAlchemyError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt if self.exponential_backoff else 1)
                    logger.warning(
                        f"Database error on attempt {attempt + 1}/{self.max_retries}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Database error after {self.max_retries} attempts: {e}")
        
        raise last_error


# Convenience functions
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[DatabaseSession, None]:
    """Get a database session with enhanced functionality."""
    async with database_manager.get_session() as session:
        yield DatabaseSession(session)


async def atomic_operation(func):
    """Decorator for atomic database operations."""
    async def wrapper(*args, **kwargs):
        async with TransactionManager.transaction() as tx:
            return await func(tx, *args, **kwargs)
    return wrapper


# Export commonly used items
__all__ = [
    "DatabaseSession",
    "TransactionManager",
    "BatchProcessor",
    "RetryableTransaction",
    "get_db_session",
    "atomic_operation"
]
