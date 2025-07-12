"""
API Dependencies

Common dependencies used across API endpoints including authentication,
database sessions, and request validation.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db
from ..config import settings

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    This is a placeholder implementation. In production, you would:
    1. Decode and validate the JWT token
    2. Extract user information
    3. Verify user exists in database
    4. Return user object
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If authentication fails
    """
    # TODO: Implement actual JWT validation
    # For now, return a mock user for development
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In production, decode JWT token here
    # token = credentials.credentials
    # payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    
    # Mock user for development
    return {
        "id": "user_123",
        "email": "dev@certifystudio.com",
        "role": "admin"
    }


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """
    Get current active user.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active user information
        
    Raises:
        HTTPException: If user is inactive
    """
    # Check if user is active
    if current_user.get("is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def require_admin_user(
    current_user: Annotated[dict, Depends(get_current_active_user)]
) -> dict:
    """
    Require admin role for endpoint access.
    
    Args:
        current_user: Active user from dependency
        
    Returns:
        Admin user information
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


# Optional authentication - returns None if not authenticated
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Get user if authenticated, otherwise return None.
    
    Useful for endpoints that have different behavior for
    authenticated vs anonymous users.
    
    Args:
        credentials: Optional bearer token
        
    Returns:
        User information or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# Database session dependency is re-exported for convenience
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "require_admin_user",
    "get_optional_user"
]
