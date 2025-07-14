"""
Base repository pattern for database operations.

This module provides a base repository class that implements
common CRUD operations and can be extended for specific models.
"""

from typing import TypeVar, Type, Generic, Optional, List, Dict, Any, Union
from datetime import datetime
from abc import ABC, abstractmethod

from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from loguru import logger

from ..models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class DuplicateError(RepositoryError):
    """Raised when trying to create a duplicate entity."""
    pass


class BaseRepository(Generic[T], ABC):
    """
    Base repository class providing common database operations.
    
    This class should be extended for each model to provide
    model-specific operations.
    """
    
    @property
    @abstractmethod
    def model(self) -> Type[T]:
        """The SQLAlchemy model class."""
        pass
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # CREATE operations
    
    async def create(self, **kwargs) -> T:
        """Create a new entity."""
        try:
            entity = self.model(**kwargs)
            self.session.add(entity)
            await self.session.flush()
            return entity
        except IntegrityError as e:
            raise DuplicateError(f"Entity already exists: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to create entity: {str(e)}")
    
    async def create_many(self, entities: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities."""
        try:
            instances = [self.model(**entity) for entity in entities]
            self.session.add_all(instances)
            await self.session.flush()
            return instances
        except IntegrityError as e:
            raise DuplicateError(f"One or more entities already exist: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating multiple {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to create entities: {str(e)}")
    
    # READ operations
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """Get an entity by its ID."""
        return await self.session.get(self.model, id)
    
    async def get_by_id_or_fail(self, id: Any) -> T:
        """Get an entity by its ID or raise an exception."""
        entity = await self.get_by_id(id)
        if not entity:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return entity
    
    async def get_by(self, **kwargs) -> Optional[T]:
        """Get a single entity by field values."""
        query = select(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[T]:
        """Get all entities with pagination."""
        query = select(self.model)
        
        # Apply ordering
        if order_by:
            order_column = getattr(self.model, order_by, None)
            if order_column:
                query = query.order_by(desc(order_column) if order_desc else asc(order_column))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def filter(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include: Optional[List[str]] = None
    ) -> List[T]:
        """Filter entities with complex criteria."""
        query = select(self.model)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if isinstance(value, list):
                        filter_conditions.append(column.in_(value))
                    elif isinstance(value, dict):
                        # Handle complex filters like {"gt": 5, "lt": 10}
                        for op, val in value.items():
                            if op == "gt":
                                filter_conditions.append(column > val)
                            elif op == "gte":
                                filter_conditions.append(column >= val)
                            elif op == "lt":
                                filter_conditions.append(column < val)
                            elif op == "lte":
                                filter_conditions.append(column <= val)
                            elif op == "ne":
                                filter_conditions.append(column != val)
                            elif op == "like":
                                filter_conditions.append(column.like(f"%{val}%"))
                            elif op == "ilike":
                                filter_conditions.append(column.ilike(f"%{val}%"))
                    else:
                        filter_conditions.append(column == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply eager loading
        if include:
            for relation in include:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))
        
        # Apply ordering
        if order_by:
            order_column = getattr(self.model, order_by, None)
            if order_column:
                query = query.order_by(desc(order_column) if order_desc else asc(order_column))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if isinstance(value, list):
                        filter_conditions.append(column.in_(value))
                    else:
                        filter_conditions.append(column == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, **kwargs) -> bool:
        """Check if an entity exists."""
        query = select(func.count()).select_from(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        query = query.limit(1)
        
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
    
    # UPDATE operations
    
    async def update(self, entity: T, **kwargs) -> T:
        """Update an entity."""
        try:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            await self.session.flush()
            return entity
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to update entity: {str(e)}")
    
    async def update_by_id(self, id: Any, **kwargs) -> Optional[T]:
        """Update an entity by its ID."""
        entity = await self.get_by_id(id)
        if entity:
            return await self.update(entity, **kwargs)
        return None
    
    async def update_many(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update multiple entities matching filters."""
        try:
            query = update(self.model)
            
            # Apply filters
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)
            
            # Apply updates
            query = query.values(**updates)
            
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount
        except Exception as e:
            logger.error(f"Error updating multiple {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to update entities: {str(e)}")
    
    # DELETE operations
    
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        try:
            await self.session.delete(entity)
            await self.session.flush()
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to delete entity: {str(e)}")
    
    async def delete_by_id(self, id: Any) -> bool:
        """Delete an entity by its ID."""
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
            return True
        return False
    
    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """Delete multiple entities matching filters."""
        try:
            query = delete(self.model)
            
            # Apply filters
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount
        except Exception as e:
            logger.error(f"Error deleting multiple {self.model.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to delete entities: {str(e)}")
    
    # Utility methods
    
    async def refresh(self, entity: T) -> None:
        """Refresh an entity from the database."""
        await self.session.refresh(entity)
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()
    
    async def execute_query(self, query: Any) -> Any:
        """Execute a raw query."""
        return await self.session.execute(query)


# Export items
__all__ = [
    "BaseRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError"
]
