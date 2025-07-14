"""
User repository for database operations.

This module provides repository classes for user-related
database operations including authentication and authorization.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import secrets
import hashlib
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from .base_repo import BaseRepository, RepositoryError
from ..models.user import (
    User, Role, Permission, UserRoleAssignment,
    APIKey, RefreshToken, PasswordResetToken,
    OAuthConnection
)
from ..models.base import utcnow


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    @property
    def model(self):
        return User
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.get_by(email=email.lower())
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by(username=username.lower())
    
    async def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Get user by email or username."""
        identifier = identifier.lower()
        query = select(User).where(
            or_(
                User.email == identifier,
                User.username == identifier
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_roles(self, user_id: UUID) -> Optional[User]:
        """Get user with roles loaded."""
        query = select(User).where(User.id == user_id).options(
            selectinload(User.roles).selectinload(UserRoleAssignment.role)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        **kwargs
    ) -> User:
        """Create a new user."""
        email = email.lower()
        username = username.lower()
        
        # Check for duplicates
        if await self.exists(email=email):
            raise RepositoryError("User with this email already exists")
        if await self.exists(username=username):
            raise RepositoryError("User with this username already exists")
        
        return await self.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            **kwargs
        )
    
    async def update_last_login(self, user_id: UUID, ip_address: Optional[str] = None) -> None:
        """Update user's last login information."""
        user = await self.get_by_id(user_id)
        if user:
            await self.update(
                user,
                last_login_at=utcnow(),
                last_login_ip=ip_address,
                login_count=user.login_count + 1
            )
    
    async def increment_failed_login(self, user_id: UUID) -> None:
        """Increment failed login count."""
        user = await self.get_by_id(user_id)
        if user:
            await self.update(
                user,
                failed_login_count=user.failed_login_count + 1
            )
    
    async def reset_failed_login(self, user_id: UUID) -> None:
        """Reset failed login count."""
        await self.update_by_id(user_id, failed_login_count=0)
    
    async def search_users(
        self,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[User]:
        """Search users by name, email, or username."""
        search_query = select(User).where(
            or_(
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
                User.username.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit)
        
        result = await self.session.execute(search_query)
        return list(result.scalars().all())
    
    async def get_active_users_count(self) -> int:
        """Get count of active users."""
        return await self.count({"is_active": True})
    
    async def get_users_by_plan(self, plan_type: str) -> List[User]:
        """Get all users with a specific plan type."""
        return await self.filter({"plan_type": plan_type})
    
    async def update_subscription(
        self,
        user_id: UUID,
        plan_type: str,
        expires_at: Optional[datetime] = None,
        stripe_subscription_id: Optional[str] = None
    ) -> Optional[User]:
        """Update user's subscription information."""
        return await self.update_by_id(
            user_id,
            plan_type=plan_type,
            plan_expires_at=expires_at,
            stripe_subscription_id=stripe_subscription_id
        )


class RoleRepository(BaseRepository[Role]):
    """Repository for Role model operations."""
    
    @property
    def model(self):
        return Role
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return await self.get_by(name=name)
    
    async def get_with_permissions(self, role_id: UUID) -> Optional[Role]:
        """Get role with permissions loaded."""
        query = select(Role).where(Role.id == role_id).options(
            selectinload(Role.permissions).selectinload(
                RolePermissionAssignment.permission
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_role(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        is_system: bool = False,
        priority: int = 0
    ) -> Role:
        """Create a new role."""
        if await self.exists(name=name):
            raise RepositoryError(f"Role '{name}' already exists")
        
        return await self.create(
            name=name,
            display_name=display_name,
            description=description,
            is_system=is_system,
            priority=priority
        )
    
    async def get_system_roles(self) -> List[Role]:
        """Get all system roles."""
        return await self.filter({"is_system": True})


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission model operations."""
    
    @property
    def model(self):
        return Permission
    
    async def get_by_name(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        return await self.get_by(name=name)
    
    async def get_by_resource_action(self, resource: str, action: str) -> Optional[Permission]:
        """Get permission by resource and action."""
        return await self.get_by(resource=resource, action=action)
    
    async def create_permission(
        self,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """Create a new permission."""
        if await self.exists(resource=resource, action=action):
            raise RepositoryError(f"Permission for {resource}:{action} already exists")
        
        return await self.create(
            name=name,
            resource=resource,
            action=action,
            description=description
        )
    
    async def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """Get all permissions for a resource."""
        return await self.filter({"resource": resource})


class UserRoleRepository(BaseRepository[UserRoleAssignment]):
    """Repository for UserRoleAssignment operations."""
    
    @property
    def model(self):
        return UserRoleAssignment
    
    async def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        granted_by: Optional[UUID] = None,
        expires_at: Optional[datetime] = None
    ) -> UserRoleAssignment:
        """Assign a role to a user."""
        if await self.exists(user_id=user_id, role_id=role_id):
            raise RepositoryError("User already has this role")
        
        return await self.create(
            user_id=user_id,
            role_id=role_id,
            granted_by=granted_by,
            expires_at=expires_at
        )
    
    async def revoke_role(self, user_id: UUID, role_id: UUID) -> bool:
        """Revoke a role from a user."""
        assignment = await self.get_by(user_id=user_id, role_id=role_id)
        if assignment:
            await self.delete(assignment)
            return True
        return False
    
    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user."""
        query = select(Role).join(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_expired_assignments(self) -> List[UserRoleAssignment]:
        """Get all expired role assignments."""
        query = select(UserRoleAssignment).where(
            and_(
                UserRoleAssignment.expires_at.isnot(None),
                UserRoleAssignment.expires_at < utcnow()
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for APIKey operations."""
    
    @property
    def model(self):
        return APIKey
    
    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        scopes: List[str] = None,
        expires_at: Optional[datetime] = None,
        rate_limit: int = 1000
    ) -> tuple[APIKey, str]:
        """Create a new API key and return the key and raw value."""
        # Generate the key
        raw_key, key_hash, key_prefix = APIKey.generate_key()
        
        # Create the API key record
        api_key = await self.create(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            description=description,
            scopes=scopes or [],
            expires_at=expires_at,
            rate_limit=rate_limit
        )
        
        return api_key, raw_key
    
    async def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by its hash."""
        return await self.get_by(key_hash=key_hash)
    
    async def validate_and_update_usage(self, key_hash: str, ip_address: Optional[str] = None) -> Optional[APIKey]:
        """Validate API key and update usage statistics."""
        api_key = await self.get_by_key_hash(key_hash)
        
        if not api_key or not api_key.is_valid():
            return None
        
        # Update usage
        await self.update(
            api_key,
            last_used_at=utcnow(),
            last_used_ip=ip_address,
            usage_count=api_key.usage_count + 1
        )
        
        return api_key
    
    async def revoke_api_key(self, api_key_id: UUID, reason: Optional[str] = None) -> bool:
        """Revoke an API key."""
        api_key = await self.get_by_id(api_key_id)
        if api_key and not api_key.is_revoked:
            await self.update(
                api_key,
                is_revoked=True,
                revoked_at=utcnow(),
                revoked_reason=reason
            )
            return True
        return False
    
    async def get_user_api_keys(self, user_id: UUID, include_revoked: bool = False) -> List[APIKey]:
        """Get all API keys for a user."""
        filters = {"user_id": user_id}
        if not include_revoked:
            filters["is_revoked"] = False
        
        return await self.filter(filters, order_by="created_at", order_desc=True)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken operations."""
    
    @property
    def model(self):
        return RefreshToken
    
    async def create_refresh_token(
        self,
        user_id: UUID,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_days: int = 30
    ) -> tuple[RefreshToken, str]:
        """Create a new refresh token."""
        # Generate token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Create token record
        refresh_token = await self.create(
            user_id=user_id,
            token_hash=token_hash,
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=utcnow() + timedelta(days=expires_in_days)
        )
        
        return refresh_token, raw_token
    
    async def validate_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Validate a refresh token."""
        token = await self.get_by(token_hash=token_hash)
        
        if token and token.is_valid():
            return token
        return None
    
    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        token = await self.get_by(token_hash=token_hash)
        if token and not token.is_revoked:
            await self.update(
                token,
                is_revoked=True,
                revoked_at=utcnow()
            )
            return True
        return False
    
    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user."""
        return await self.update_many(
            {"user_id": user_id, "is_revoked": False},
            {"is_revoked": True, "revoked_at": utcnow()}
        )
    
    async def cleanup_expired_tokens(self) -> int:
        """Delete expired refresh tokens."""
        query = delete(RefreshToken).where(
            RefreshToken.expires_at < utcnow()
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """Repository for PasswordResetToken operations."""
    
    @property
    def model(self):
        return PasswordResetToken
    
    async def create_reset_token(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> tuple[PasswordResetToken, str]:
        """Create a password reset token."""
        # Generate token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Create token record
        reset_token = await self.create(
            user_id=user_id,
            token_hash=token_hash,
            ip_address=ip_address,
            expires_at=utcnow() + timedelta(hours=expires_in_hours)
        )
        
        return reset_token, raw_token
    
    async def validate_and_use_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Validate and mark token as used."""
        token = await self.get_by(token_hash=token_hash)
        
        if token and token.is_valid():
            await self.update(
                token,
                is_used=True,
                used_at=utcnow()
            )
            return token
        return None
    
    async def cleanup_expired_tokens(self) -> int:
        """Delete expired password reset tokens."""
        query = delete(PasswordResetToken).where(
            or_(
                PasswordResetToken.expires_at < utcnow(),
                PasswordResetToken.is_used == True
            )
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount


# Export repositories
__all__ = [
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "UserRoleRepository",
    "APIKeyRepository",
    "RefreshTokenRepository",
    "PasswordResetTokenRepository"
]
