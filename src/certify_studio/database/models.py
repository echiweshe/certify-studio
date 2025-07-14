"""
Database models for Certify Studio.

This module will contain all SQLAlchemy models.
For now, it's a placeholder to ensure imports work.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .connection import Base


class User(Base):
    """User model (placeholder for now)."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    plan_type = Column(String, default="free")
    total_generations = Column(Integer, default=0)
    total_storage_mb = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)


# More models will be added here as needed
