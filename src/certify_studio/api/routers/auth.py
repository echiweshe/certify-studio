"""
Authentication router - handles user registration, login, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.logging import get_logger
from ...core.config import settings
from ..dependencies import (
    get_db,
    Database,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
    CurrentUser
)
from ..schemas import (
    BaseResponse,
    AuthResponse,
    UserResponse,
    ErrorResponse,
    StatusEnum,
    User
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password"
)
async def register(
    email: str = Body(..., description="User email address"),
    password: str = Body(..., min_length=8, description="User password (min 8 chars)"),
    username: str = Body(..., min_length=3, max_length=50, description="Username"),
    db: Database = Depends()
) -> AuthResponse:
    """Register a new user."""
    try:
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Check if username already exists
        result = await db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
        
        # Create new user
        user_id = uuid4()
        hashed_password = get_password_hash(password)
        
        user = User(
            id=user_id,
            email=email,
            username=username,
            password_hash=hashed_password,
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            plan_type="free"
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Create response
        user_response = UserResponse(
            status=StatusEnum.SUCCESS,
            message="Registration successful",
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            plan_type=user.plan_type,
            total_generations=0,
            total_storage_bytes=0,
            preferences={},
            quota_remaining={"generations": 10, "storage_mb": 100}
        )
        
        return AuthResponse(
            status=StatusEnum.SUCCESS,
            message="Registration successful",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User login",
    description="Login with email and password to get access tokens"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Database = Depends()
) -> AuthResponse:
    """Authenticate user and return tokens."""
    try:
        # Find user by email (username field in OAuth2 form)
        result = await db.execute(
            select(User).where(User.email == form_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Get user stats (in production, these would come from aggregated data)
        user_response = UserResponse(
            status=StatusEnum.SUCCESS,
            message="Login successful",
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            plan_type=user.plan_type,
            total_generations=user.total_generations or 0,
            total_storage_bytes=user.total_storage_bytes or 0,
            preferences=user.preferences or {},
            quota_remaining={
                "generations": 10 - (user.total_generations or 0),
                "storage_mb": 100
            }
        )
        
        return AuthResponse(
            status=StatusEnum.SUCCESS,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access token"
)
async def refresh_token(
    refresh_token: str = Body(..., description="Refresh token"),
    db: Database = Depends()
) -> AuthResponse:
    """Refresh access token using refresh token."""
    try:
        # Decode refresh token
        from jose import jwt, JWTError
        
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get("scope") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token scope"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await db.get(User, UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Create new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Create response
        user_response = UserResponse(
            status=StatusEnum.SUCCESS,
            message="Token refreshed",
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            plan_type=user.plan_type,
            total_generations=user.total_generations or 0,
            total_storage_bytes=user.total_storage_bytes or 0,
            preferences=user.preferences or {},
            quota_remaining={
                "generations": 10 - (user.total_generations or 0),
                "storage_mb": 100
            }
        )
        
        return AuthResponse(
            status=StatusEnum.SUCCESS,
            message="Token refreshed successfully",
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post(
    "/logout",
    response_model=BaseResponse,
    summary="User logout",
    description="Logout user and invalidate tokens"
)
async def logout(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: Database = Depends()
) -> BaseResponse:
    """Logout user."""
    try:
        # In production, you would:
        # 1. Add the token to a blacklist
        # 2. Clear any server-side sessions
        # 3. Log the logout event
        
        # For now, we'll just log the event
        logger.info(f"User {current_user.id} logged out")
        
        # You could also clear refresh tokens from the database here
        # await db.execute(
        #     delete(RefreshToken).where(RefreshToken.user_id == current_user.id)
        # )
        # await db.commit()
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
async def get_me(
    current_user: CurrentUser,
    db: Database = Depends()
) -> UserResponse:
    """Get current user information."""
    try:
        # Get fresh user data
        user = await db.get(User, current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            status=StatusEnum.SUCCESS,
            message="User retrieved successfully",
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            plan_type=user.plan_type,
            total_generations=user.total_generations or 0,
            total_storage_bytes=user.total_storage_bytes or 0,
            preferences=user.preferences or {},
            quota_remaining={
                "generations": 10 - (user.total_generations or 0),
                "storage_mb": 100
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post(
    "/verify-email",
    response_model=BaseResponse,
    summary="Verify email address",
    description="Verify user's email address with verification token"
)
async def verify_email(
    token: str = Body(..., description="Email verification token"),
    db: Database = Depends()
) -> BaseResponse:
    """Verify user's email address."""
    try:
        # In production, decode the verification token
        # For now, this is a placeholder
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="Email verified successfully"
        )
        
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post(
    "/forgot-password",
    response_model=BaseResponse,
    summary="Request password reset",
    description="Send password reset email to user"
)
async def forgot_password(
    email: str = Body(..., description="User email address"),
    background_tasks: BackgroundTasks,
    db: Database = Depends()
) -> BaseResponse:
    """Request password reset."""
    try:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Always return success to prevent email enumeration
        if user:
            # In production, send password reset email
            # background_tasks.add_task(send_password_reset_email, user)
            logger.info(f"Password reset requested for {email}")
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="If the email exists, a password reset link has been sent"
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post(
    "/reset-password",
    response_model=BaseResponse,
    summary="Reset password",
    description="Reset password using reset token"
)
async def reset_password(
    token: str = Body(..., description="Password reset token"),
    new_password: str = Body(..., min_length=8, description="New password"),
    db: Database = Depends()
) -> BaseResponse:
    """Reset user password."""
    try:
        # In production, validate the reset token and update password
        # For now, this is a placeholder
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="Password reset successfully"
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# Note: In production, you'll need to:
# 1. Implement proper User model in database
# 2. Add email verification functionality
# 3. Implement password reset with secure tokens
# 4. Add token blacklisting for logout
# 5. Implement proper session management
# 6. Add OAuth2 providers (Google, GitHub, etc.)
