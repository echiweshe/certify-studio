"""
User and authentication models for Certify Studio.

This module contains all user-related database models including
user accounts, roles, permissions, API keys, and authentication tokens.
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timedelta
import secrets
import hashlib

from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, JSON, DateTime,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from .base import (
    BaseModel, FullAuditModel, UserRole, PlanType,
    generate_uuid, utcnow
)

if TYPE_CHECKING:
    from .content import ContentGeneration
    from .analytics import UserActivity


class User(FullAuditModel):
    """Main user model with authentication and profile information."""
    
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
        Index("ix_users_plan_type", "plan_type"),
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'", name="ck_users_email_valid"),
        CheckConstraint("length(username) >= 3", name="ck_users_username_length"),
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_beta_tester: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Subscription information
    plan_type: Mapped[str] = mapped_column(String(50), default=PlanType.FREE)
    plan_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Usage limits and tracking
    monthly_generation_limit: Mapped[int] = mapped_column(Integer, default=10)
    monthly_generations_used: Mapped[int] = mapped_column(Integer, default=0)
    storage_limit_gb: Mapped[float] = mapped_column(Float, default=1.0)
    storage_used_gb: Mapped[float] = mapped_column(Float, default=0.0)
    api_rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # requests per hour
    
    # Account metadata
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Additional settings
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Relationships
    roles: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    oauth_connections: Mapped[List["OAuthConnection"]] = relationship(
        "OAuthConnection",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Content relationships (defined in content.py)
    content_generations: Mapped[List["ContentGeneration"]] = relationship(
        "ContentGeneration",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Activity relationships (defined in analytics.py)
    activities: Mapped[List["UserActivity"]] = relationship(
        "UserActivity",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email})>"
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(ra.role.name == role_name for ra in self.roles if ra.role)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        for role_assignment in self.roles:
            if role_assignment.role:
                for perm in role_assignment.role.permissions:
                    if perm.permission.name == permission_name:
                        return True
        return False
    
    def can_generate_content(self) -> bool:
        """Check if user can generate more content this month."""
        if self.plan_type == PlanType.ENTERPRISE:
            return True  # Unlimited for enterprise
        return self.monthly_generations_used < self.monthly_generation_limit
    
    def increment_generation_count(self) -> None:
        """Increment the monthly generation count."""
        self.monthly_generations_used += 1
    
    def reset_monthly_usage(self) -> None:
        """Reset monthly usage counters."""
        self.monthly_generations_used = 0


class Role(BaseModel):
    """Role model for role-based access control."""
    
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("name", name="uq_roles_name"),
        Index("ix_roles_name", "name"),
    )
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    users: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment",
        back_populates="role"
    )
    permissions: Mapped[List["RolePermissionAssignment"]] = relationship(
        "RolePermissionAssignment",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Role(name={self.name})>"


class Permission(BaseModel):
    """Permission model for fine-grained access control."""
    
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
        Index("ix_permissions_resource", "resource"),
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    roles: Mapped[List["RolePermissionAssignment"]] = relationship(
        "RolePermissionAssignment",
        back_populates="permission"
    )
    
    def __repr__(self) -> str:
        return f"<Permission(name={self.name}, resource={self.resource}, action={self.action})>"


class UserRoleAssignment(BaseModel):
    """Many-to-many relationship between users and roles."""
    
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role_assignments"),
        Index("ix_user_role_assignments_user_id", "user_id"),
        Index("ix_user_role_assignments_role_id", "role_id"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow
    )
    granted_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="roles")
    role: Mapped["Role"] = relationship("Role", back_populates="users")


class RolePermissionAssignment(BaseModel):
    """Many-to-many relationship between roles and permissions."""
    
    __tablename__ = "role_permission_assignments"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission_assignments"),
        Index("ix_role_permission_assignments_role_id", "role_id"),
        Index("ix_role_permission_assignments_permission_id", "permission_id"),
    )
    
    role_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    permission_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="roles")


class APIKey(FullAuditModel):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_key_hash", "key_hash"),
        Index("ix_api_keys_expires_at", "expires_at"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # For display
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Permissions and limits
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)  # per hour
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_ip: Mapped[Optional[str]] = mapped_column(String(45))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    
    @classmethod
    def generate_key(cls) -> tuple[str, str]:
        """Generate a new API key and its hash."""
        # Generate a secure random key
        key = f"csk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:10]
        return key, key_hash, key_prefix
    
    def is_valid(self) -> bool:
        """Check if the API key is valid."""
        if self.is_revoked:
            return False
        if self.expires_at and self.expires_at < utcnow():
            return False
        return True


class RefreshToken(BaseModel):
    """Refresh token model for JWT authentication."""
    
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(String(100))
    device_name: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
    
    def is_valid(self) -> bool:
        """Check if the refresh token is valid."""
        if self.is_revoked:
            return False
        if self.expires_at < utcnow():
            return False
        return True


class PasswordResetToken(BaseModel):
    """Password reset token model."""
    
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
        Index("ix_password_reset_tokens_user_id", "user_id"),
        Index("ix_password_reset_tokens_expires_at", "expires_at"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")
    
    def is_valid(self) -> bool:
        """Check if the reset token is valid."""
        if self.is_used:
            return False
        if self.expires_at < utcnow():
            return False
        return True


class OAuthConnection(BaseModel):
    """OAuth connection model for third-party authentication."""
    
    __tablename__ = "oauth_connections"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_connections"),
        Index("ix_oauth_connections_user_id", "user_id"),
        Index("ix_oauth_connections_provider", "provider"),
    )
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # google, github, etc.
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255))
    provider_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Additional provider data
    provider_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_connections")


# Create indexes for better query performance
Index("ix_users_last_login", User.last_login_at)
Index("ix_users_created_at", User.created_at)
Index("ix_api_keys_last_used", APIKey.last_used_at)
