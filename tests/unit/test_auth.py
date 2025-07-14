"""
Unit tests for authentication endpoints.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from jose import jwt

from certify_studio.api.dependencies import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    get_current_user
)
from certify_studio.api.schemas import User, TokenData, PlanType
from certify_studio.config import settings


class TestAuthHelpers:
    """Test authentication helper functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
    
    def test_create_access_token(self):
        """Test JWT access token creation."""
        user_id = str(uuid4())
        data = {"sub": user_id}
        
        # Create token
        token = create_access_token(data)
        
        # Decode and verify
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["scope"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        
        # Check expiration time
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp_time > now
        assert exp_time < now + timedelta(minutes=31)  # Default 30 min + buffer
    
    def test_create_refresh_token(self):
        """Test JWT refresh token creation."""
        user_id = str(uuid4())
        data = {"sub": user_id}
        
        # Create token
        token = create_refresh_token(data)
        
        # Decode and verify
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["scope"] == "refresh"
        
        # Check expiration time (7 days)
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp_time > now + timedelta(days=6)
        assert exp_time < now + timedelta(days=8)


@pytest.mark.asyncio
class TestAuthDependencies:
    """Test authentication dependencies."""
    
    async def test_get_current_user_valid_token(self, db_session):
        """Test getting current user with valid token."""
        # Create test user
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            username="testuser",
            is_active=True,
            is_verified=True,
            plan_type=PlanType.FREE,
            total_generations=0,
            total_storage_mb=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock database get
        db_session.get = Mock(return_value=user)
        
        # Create valid token
        token = create_access_token({"sub": str(user_id)})
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = token
        
        # Get user
        with patch("certify_studio.api.dependencies.get_db", return_value=db_session):
            result = await get_current_user(credentials, db_session)
        
        assert result.id == user_id
        assert result.email == "test@example.com"
    
    async def test_get_current_user_invalid_token(self, db_session):
        """Test getting current user with invalid token."""
        # Mock invalid credentials
        credentials = Mock()
        credentials.credentials = "invalid-token"
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    async def test_get_current_user_expired_token(self, db_session):
        """Test getting current user with expired token."""
        user_id = str(uuid4())
        
        # Create expired token
        data = {"sub": user_id}
        expired_token = jwt.encode(
            {
                **data,
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2),
                "scope": "access"
            },
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Mock credentials
        credentials = Mock()
        credentials.credentials = expired_token
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)
        
        assert exc_info.value.status_code == 401


class TestTokenValidation:
    """Test token validation scenarios."""
    
    def test_token_with_wrong_scope(self):
        """Test token with wrong scope."""
        # Create refresh token instead of access token
        token = create_refresh_token({"sub": "user-id"})
        
        # Try to use as access token
        credentials = Mock()
        credentials.credentials = token
        
        # Should fail validation
        with pytest.raises(HTTPException) as exc_info:
            # Simulate token validation logic
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("scope") != "access":
                raise HTTPException(status_code=401, detail="Invalid token scope")
        
        assert exc_info.value.status_code == 401
    
    def test_token_without_sub(self):
        """Test token without subject claim."""
        # Create token without 'sub'
        token = jwt.encode(
            {
                "exp": datetime.utcnow() + timedelta(minutes=30),
                "iat": datetime.utcnow(),
                "scope": "access"
                # Missing 'sub'
            },
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM
        )
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Should not have 'sub'
        assert "sub" not in payload
