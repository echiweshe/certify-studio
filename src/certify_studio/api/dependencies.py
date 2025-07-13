"""
FastAPI dependencies for authentication, database, and common functionality.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from redis import asyncio as aioredis
import aiofiles

from ..database import get_session
from ..core.config import settings
from ..core.logging import get_logger
from .schemas import User, TokenData, RateLimitInfo

logger = get_logger(__name__)

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

# Redis client for caching and rate limiting
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with get_session() as session:
        yield session


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "scope": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "scope": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        if payload.get("scope") != "access":
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(
            sub=user_id,
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            jti=payload.get("jti"),
            scope=payload.get("scope")
        )
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = await db.get(User, UUID(token_data.sub))
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def check_rate_limit(
    request: Request,
    user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis)
) -> RateLimitInfo:
    """Check rate limit for user."""
    # Rate limit key
    key = f"rate_limit:{user.id}:{request.url.path}"
    
    # Get current count
    current = await redis.get(key)
    if current is None:
        current = 0
    else:
        current = int(current)
    
    # Check limit based on user plan
    limit = settings.RATE_LIMITS.get(user.plan_type, 100)
    
    if current >= limit:
        # Calculate reset time
        ttl = await redis.ttl(key)
        reset_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_at.timestamp())),
                "Retry-After": str(ttl)
            }
        )
    
    # Increment counter
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 3600)  # 1 hour window
    await pipe.execute()
    
    remaining = limit - current - 1
    reset_at = datetime.utcnow() + timedelta(hours=1)
    
    return RateLimitInfo(
        limit=limit,
        remaining=remaining,
        reset_at=reset_at
    )


async def get_api_key(
    api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate API key and return user."""
    # In production, implement proper API key validation
    # This is a simplified version
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "API-Key"},
    )
    
    # Validate API key format
    if not api_key or len(api_key) != 32:
        raise credentials_exception
    
    # Get user by API key (implement in database)
    # user = await db.query(User).filter(User.api_key == api_key).first()
    # if not user:
    #     raise credentials_exception
    
    # For now, return a mock user
    raise NotImplementedError("API key authentication not yet implemented")


def require_admin(current_user: User = Depends(get_current_verified_user)) -> User:
    """Require admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class UploadFile:
    """Handle file uploads securely."""
    
    def __init__(
        self,
        max_size: int = 100 * 1024 * 1024,  # 100MB default
        allowed_types: Optional[list] = None
    ):
        self.max_size = max_size
        self.allowed_types = allowed_types or [
            "application/pdf",
            "text/plain",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/epub+zip"
        ]
    
    async def __call__(self, file: UploadFile) -> Dict[str, Any]:
        """Validate and process uploaded file."""
        # Check file size
        contents = await file.read()
        if len(contents) > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {self.max_size} bytes"
            )
        
        # Check content type
        if file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_types)}"
            )
        
        # Generate secure filename
        file_id = UUID()
        extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
        secure_filename = f"{file_id}.{extension}"
        
        # Save file
        upload_path = os.path.join(settings.UPLOAD_DIR, secure_filename)
        async with aiofiles.open(upload_path, "wb") as f:
            await f.write(contents)
        
        return {
            "upload_id": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(contents),
            "path": upload_path
        }


# Dependency aliases for cleaner imports
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
AdminUser = Annotated[User, Depends(require_admin)]
Database = Annotated[AsyncSession, Depends(get_db)]
Redis = Annotated[aioredis.Redis, Depends(get_redis)]
RateLimit = Annotated[RateLimitInfo, Depends(check_rate_limit)]


# WebSocket authentication
async def get_ws_user(token: str, db: AsyncSession) -> Optional[User]:
    """Get user from WebSocket token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            user = await db.get(User, UUID(user_id))
            return user
    except JWTError:
        pass
    return None


# Pagination dependencies
def get_pagination(
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100
) -> Dict[str, int]:
    """Get pagination parameters."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > max_page_size:
        page_size = max_page_size
    
    offset = (page - 1) * page_size
    
    return {
        "page": page,
        "page_size": page_size,
        "offset": offset
    }


# Request ID for tracking
def get_request_id(
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
) -> str:
    """Get or generate request ID."""
    if x_request_id:
        return x_request_id
    return str(UUID())
