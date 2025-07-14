"""
Authentication router - handles user authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ...core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import (
    get_db,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_request_id
)
from ..schemas import (
    User,
    AuthTokenResponse,
    User,
    ErrorResponse,
    BaseResponse,
    StatusEnum,
    PlanType
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)


@router.post(
    "/register",
    response_model=BaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account"
)
async def register(
    email: str,
    password: str,
    username: str,
    full_name: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Register a new user."""
    try:
        # Check if user exists
        # result = await db.execute(
        #     select(User).where((User.email == email) | (User.username == username))
        # )
        # if result.scalar_one_or_none():
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="User with this email or username already exists"
        #     )
        
        # Create user
        hashed_password = get_password_hash(password)
        user_id = UUID()
        
        # user = User(
        #     id=user_id,
        #     email=email,
        #     username=username,
        #     full_name=full_name,
        #     hashed_password=hashed_password,
        #     plan_type=PlanType.FREE,
        #     created_at=datetime.utcnow(),
        #     updated_at=datetime.utcnow()
        # )
        # db.add(user)
        # await db.commit()
        
        # Send verification email in background
        background_tasks.add_task(
            send_verification_email,
            email,
            user_id
        )
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="User registered successfully. Please check your email to verify your account.",
            request_id=UUID(request_id)
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
    response_model=AuthTokenResponse,
    summary="User login",
    description="Authenticate user and receive access tokens"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> AuthTokenResponse:
    """Login and receive tokens."""
    try:
        # Authenticate user
        # result = await db.execute(
        #     select(User).where(User.email == form_data.username)
        # )
        # user = result.scalar_one_or_none()
        
        # For demo purposes, create a mock user
        user = User(
            id=UUID(),
            email=form_data.username,
            username=form_data.username.split("@")[0],
            full_name="Demo User",
            is_active=True,
            is_verified=True,
            is_admin=False,
            plan_type=PlanType.FREE,
            total_generations=0,
            total_storage_mb=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # if not user or not verify_password(form_data.password, user.hashed_password):
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Incorrect email or password",
        #         headers={"WWW-Authenticate": "Bearer"}
        #     )
        
        # if not user.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Account is inactive"
        #     )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Update last login
        # await db.execute(
        #     update(User).where(User.id == user.id).values(
        #         last_login_at=datetime.utcnow()
        #     )
        # )
        # await db.commit()
        
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            plan_type=user.plan_type.value
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
    response_model=AuthTokenResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access token"
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> AuthTokenResponse:
    """Refresh access token."""
    try:
        # Decode refresh token
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
                detail="Invalid token"
            )
        
        # Get user
        # user = await db.get(User, UUID(user_id))
        # if not user or not user.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="User not found or inactive"
        #     )
        
        # For demo, create mock user
        user = User(
            id=UUID(user_id),
            email="demo@example.com",
            username="demo",
            full_name="Demo User",
            is_active=True,
            is_verified=True,
            is_admin=False,
            plan_type=PlanType.FREE,
            total_generations=0,
            total_storage_mb=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            plan_type=user.plan_type.value
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
    description="Invalidate user session"
)
async def logout(
    current_user: User = Depends(get_current_user),
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Logout user."""
    # In a real implementation, you would:
    # 1. Add the token to a blacklist
    # 2. Clear any session data
    # 3. Log the logout event
    
    logger.info(f"User {current_user.id} logged out")
    
    return BaseResponse(
        status=StatusEnum.SUCCESS,
        message="Logged out successfully",
        request_id=UUID(request_id)
    )


@router.post(
    "/verify-email/{token}",
    response_model=BaseResponse,
    summary="Verify email address",
    description="Verify user email with verification token"
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Verify email address."""
    try:
        # Decode verification token
        # In production, implement proper token verification
        # user_id = decode_verification_token(token)
        
        # Update user
        # await db.execute(
        #     update(User).where(User.id == user_id).values(
        #         is_verified=True,
        #         updated_at=datetime.utcnow()
        #     )
        # )
        # await db.commit()
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="Email verified successfully. You can now log in.",
            request_id=UUID(request_id)
        )
        
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


@router.post(
    "/forgot-password",
    response_model=BaseResponse,
    summary="Request password reset",
    description="Send password reset email"
)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Request password reset."""
    try:
        # Check if user exists
        # result = await db.execute(
        #     select(User).where(User.email == email)
        # )
        # user = result.scalar_one_or_none()
        
        # Always return success to prevent email enumeration
        # if user:
        #     background_tasks.add_task(
        #         send_password_reset_email,
        #         email,
        #         user.id
        #     )
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="If an account exists with this email, you will receive password reset instructions.",
            request_id=UUID(request_id)
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Still return success to prevent enumeration
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="If an account exists with this email, you will receive password reset instructions.",
            request_id=UUID(request_id)
        )


@router.post(
    "/reset-password",
    response_model=BaseResponse,
    summary="Reset password",
    description="Reset password with reset token"
)
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_request_id)
) -> BaseResponse:
    """Reset password."""
    try:
        # Decode reset token
        # user_id = decode_reset_token(token)
        
        # Update password
        # hashed_password = get_password_hash(new_password)
        # await db.execute(
        #     update(User).where(User.id == user_id).values(
        #         hashed_password=hashed_password,
        #         updated_at=datetime.utcnow()
        #     )
        # )
        # await db.commit()
        
        return BaseResponse(
            status=StatusEnum.SUCCESS,
            message="Password reset successfully. You can now log in with your new password.",
            request_id=UUID(request_id)
        )
        
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )


@router.get(
    "/me",
    response_model=User,
    summary="Get current user",
    description="Get current authenticated user information"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user information."""
    return current_user


@router.put(
    "/me",
    response_model=User,
    summary="Update current user",
    description="Update current user information"
)
async def update_me(
    full_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Update current user information."""
    try:
        # Update user
        # if full_name is not None:
        #     await db.execute(
        #         update(User).where(User.id == current_user.id).values(
        #             full_name=full_name,
        #             updated_at=datetime.utcnow()
        #         )
        #     )
        #     await db.commit()
        #     
        #     # Refresh user data
        #     await db.refresh(current_user)
        
        # For demo, return updated mock user
        if full_name is not None:
            current_user.full_name = full_name
            current_user.updated_at = datetime.utcnow()
            
        return current_user
        
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


# Helper functions for email sending (implement in production)
async def send_verification_email(email: str, user_id: UUID):
    """Send verification email."""
    # In production, implement actual email sending
    logger.info(f"Would send verification email to {email} for user {user_id}")


async def send_password_reset_email(email: str, user_id: UUID):
    """Send password reset email."""
    # In production, implement actual email sending
    logger.info(f"Would send password reset email to {email} for user {user_id}")


# Import required modules
from uuid import UUID
from jose import JWTError, jwt
from ...core.config import settings
from ..dependencies import get_request_id
