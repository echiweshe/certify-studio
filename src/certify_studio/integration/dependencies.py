"""
Dependency Injection for FastAPI

This module provides dependency injection functions for FastAPI endpoints.
It handles database sessions, authentication, and repository instantiation.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from datetime import datetime

from ..database import get_db_session
from ..database.repositories import (
    UserRepository,
    ContentGenerationRepository,
    ContentPieceRepository,
    MediaAssetRepository,
    ExportTaskRepository,
)
from ..database.models import User
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Security
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        Database session that auto-commits on success, rolls back on error
    """
    async with get_db_session() as db:
        try:
            yield db.session
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
            
        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
            
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current superuser.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if they are a superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    
    Args:
        credentials: Optional JWT token
        db: Database session
        
    Returns:
        Current user or None
    """
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# Repository dependencies
async def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


async def get_content_generation_repository(
    db: AsyncSession = Depends(get_db)
) -> ContentGenerationRepository:
    """Get content generation repository instance."""
    return ContentGenerationRepository(db)


async def get_content_piece_repository(
    db: AsyncSession = Depends(get_db)
) -> ContentPieceRepository:
    """Get content piece repository instance."""
    return ContentPieceRepository(db)


async def get_media_asset_repository(
    db: AsyncSession = Depends(get_db)
) -> MediaAssetRepository:
    """Get media asset repository instance."""
    return MediaAssetRepository(db)


async def get_export_task_repository(
    db: AsyncSession = Depends(get_db)
) -> ExportTaskRepository:
    """Get export task repository instance."""
    return ExportTaskRepository(db)


# Permission checking dependencies
class PermissionChecker:
    """Dependency class for checking user permissions."""
    
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        user_repo: UserRepository = Depends(get_user_repository)
    ) -> User:
        """
        Check if user has required permission.
        
        Args:
            current_user: Current authenticated user
            user_repo: User repository
            
        Returns:
            User if they have permission
            
        Raises:
            HTTPException: If user lacks permission
        """
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user
            
        # Check user permissions
        has_permission = await user_repo.check_permission(
            current_user.id,
            self.resource,
            self.action
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.resource}:{self.action}"
            )
            
        return current_user


# Pagination dependencies
class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Cap at 1000
        
        
# API Key authentication
async def get_user_from_api_key(
    api_key: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get user from API key.
    
    Args:
        api_key: API key from header
        db: Database session
        
    Returns:
        User associated with API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_api_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
        
    # Update API key last used timestamp
    await user_repo.update_api_key_last_used(api_key)
    
    return user
