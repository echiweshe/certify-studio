"""
Updated Authentication Router with Database Integration

This module handles user authentication and registration,
now fully integrated with the database layer.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from ...integration.dependencies import (
    get_db,
    get_current_user,
    get_user_repository
)
from ...integration.services import UserService
from ...integration.events import get_event_bus, UserRegisteredEvent
from ...database.models import User
from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response models
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request model."""
    username: str  # Can be username or email
    password: str


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: Registration data
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If username/email already exists
    """
    user_service = UserService(db)
    user_repo = get_user_repository(db)
    
    # Check if user exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = await user_service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    # Emit event
    event_bus = get_event_bus()
    await event_bus.emit(UserRegisteredEvent(
        user_id=user.id,
        email=user.email,
        username=user.username
    ))
    
    logger.info(f"New user registered: {user.username}")
    
    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    """
    Login with username/email and password.
    
    Args:
        form_data: OAuth2 form with username and password
        db: Database session
        
    Returns:
        Access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = await user_service.authenticate_user(
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create access token
    access_token = await user_service.create_access_token(
        user=user,
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Update last login
    user_repo = get_user_repository(db)
    await user_repo.update_last_login(user.id)
    
    logger.info(f"User logged in: {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: With JWT tokens, logout is typically handled client-side
    by removing the token. This endpoint can be used for audit logging.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.username}")
    
    # Could invalidate refresh tokens here if using them
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile
    """
    return UserResponse.from_orm(current_user)


@router.put("/me")
async def update_current_user_profile(
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Update current user profile.
    
    Args:
        update_data: Fields to update
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user profile
    """
    user_repo = get_user_repository(db)
    
    # Only allow updating certain fields
    allowed_fields = {"full_name", "preferences"}
    update_dict = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if update_dict:
        for key, value in update_dict.items():
            setattr(current_user, key, value)
        await db.commit()
        
    return UserResponse.from_orm(current_user)


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token
        db: Database session
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    user_repo = get_user_repository(db)
    
    # Validate refresh token
    token_obj = await user_repo.get_refresh_token(refresh_token)
    if not token_obj or token_obj.revoked or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user = token_obj.user
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Create new access token
    user_service = UserService(db)
    access_token = await user_service.create_access_token(
        user=user,
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    # Update refresh token last used
    token_obj.last_used_at = datetime.utcnow()
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/api-key")
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new API key for the current user.
    
    Args:
        name: Name for the API key
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created API key (only shown once)
    """
    user_repo = get_user_repository(db)
    
    # Generate API key
    import secrets
    key = f"cs_{secrets.token_urlsafe(32)}"
    
    # Create API key
    api_key = await user_repo.create_api_key(
        user_id=current_user.id,
        name=name,
        key=key
    )
    
    logger.info(f"API key created for user: {current_user.username}")
    
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": key,  # Only returned on creation
        "created_at": api_key.created_at
    }


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List user's API keys.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of API keys (without the actual keys)
    """
    user_repo = get_user_repository(db)
    api_keys = await user_repo.get_user_api_keys(current_user.id)
    
    return [
        {
            "id": str(key.id),
            "name": key.name,
            "created_at": key.created_at,
            "last_used_at": key.last_used_at,
            "is_active": key.is_active
        }
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Revoke an API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If key not found or not owned by user
    """
    user_repo = get_user_repository(db)
    
    # Get API key
    api_key = await user_repo.get_api_key_by_id(key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Revoke key
    await user_repo.revoke_api_key(key_id)
    
    logger.info(f"API key revoked: {key_id}")
    
    return {"message": "API key revoked successfully"}
