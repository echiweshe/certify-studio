"""
Configuration management for Certify Studio.

Handles environment-based configuration with validation,
security, and development/production settings.
"""

import os
from functools import lru_cache
from typing import List, Optional, Union, Dict, Any
from pathlib import Path

from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Uses Pydantic for validation and type conversion.
    Supports environment files and override hierarchy.
    """
    
    # Application Basic Settings
    APP_NAME: str = Field(default="Certify Studio", env="APP_NAME")
    APP_VERSION: str = Field(default="0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # Security
    SECRET_KEY: SecretStr = Field(..., env="SECRET_KEY")
    JWT_SECRET_KEY: SecretStr = Field(..., env="JWT_SECRET_KEY")
    ENCRYPTION_KEY: SecretStr = Field(..., env="ENCRYPTION_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=1440, env="JWT_EXPIRE_MINUTES")  # 24 hours
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # AI Service Configuration
    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[SecretStr] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_BEDROCK_REGION: str = Field(default="us-east-1", env="AWS_BEDROCK_REGION")
    
    # Azure Configuration
    AZURE_CLIENT_ID: Optional[str] = Field(default=None, env="AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET: Optional[SecretStr] = Field(default=None, env="AZURE_CLIENT_SECRET")
    AZURE_TENANT_ID: Optional[str] = Field(default=None, env="AZURE_TENANT_ID")
    
    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        default=None, env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT")
    
    # File Storage Configuration
    STORAGE_BACKEND: str = Field(default="local", env="STORAGE_BACKEND")  # local, s3, azure, gcs
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    EXPORT_DIR: str = Field(default="./exports", env="EXPORT_DIR")
    TEMP_DIR: str = Field(default="./temp", env="TEMP_DIR")
    VIDEO_OUTPUT_DIR: str = Field(default="./exports/videos", env="VIDEO_OUTPUT_DIR")
    MAX_UPLOAD_SIZE: int = Field(default=100 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 100MB
    
    # S3 Configuration
    S3_BUCKET_NAME: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")
    S3_REGION: str = Field(default="us-east-1", env="S3_REGION")
    
    # Azure Storage Configuration
    AZURE_CONTAINER_NAME: Optional[str] = Field(default=None, env="AZURE_CONTAINER_NAME")
    AZURE_STORAGE_CONNECTION_STRING: Optional[SecretStr] = Field(
        default=None, env="AZURE_STORAGE_CONNECTION_STRING"
    )
    
    # GCS Configuration
    GCS_BUCKET_NAME: Optional[str] = Field(default=None, env="GCS_BUCKET_NAME")
    
    # Manim Configuration
    MANIM_TEMP_DIR: str = Field(default="/tmp/manim", env="MANIM_TEMP_DIR")
    MANIM_QUALITY: str = Field(default="high", env="MANIM_QUALITY")  # low, medium, high, production
    MANIM_FPS: int = Field(default=30, env="MANIM_FPS")
    MANIM_RESOLUTION: str = Field(default="1920x1080", env="MANIM_RESOLUTION")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    
    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=1000, env="WS_MAX_CONNECTIONS")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")  # seconds
    WS_MESSAGE_MAX_SIZE: int = Field(default=1024 * 1024, env="WS_MESSAGE_MAX_SIZE")  # 1MB
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="structured", env="LOG_FORMAT")  # structured, simple
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Monitoring and Observability
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    ENABLE_TRACING: bool = Field(default=False, env="ENABLE_TRACING")
    JAEGER_ENDPOINT: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    
    # Content Generation Settings
    MAX_CONCURRENT_GENERATIONS: int = Field(default=5, env="MAX_CONCURRENT_GENERATIONS")
    GENERATION_TIMEOUT: int = Field(default=1800, env="GENERATION_TIMEOUT")  # 30 minutes
    QUALITY_CHECK_ENABLED: bool = Field(default=True, env="QUALITY_CHECK_ENABLED")
    
    # Export Settings
    EXPORT_FORMATS: List[str] = Field(
        default=["mp4", "pdf", "pptx", "html"],
        env="EXPORT_FORMATS"
    )
    VIDEO_QUALITY: str = Field(default="high", env="VIDEO_QUALITY")
    AUDIO_QUALITY: str = Field(default="medium", env="AUDIO_QUALITY")
    
    # Development Settings
    AUTO_RELOAD: bool = Field(default=False, env="AUTO_RELOAD")
    PROFILING_ENABLED: bool = Field(default=False, env="PROFILING_ENABLED")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file
        
        # Settings source customization removed for compatibility
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_environments = ["development", "staging", "production", "testing"]
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level setting."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("STORAGE_BACKEND")
    def validate_storage_backend(cls, v):
        """Validate storage backend setting."""
        valid_backends = ["local", "s3", "azure", "gcs"]
        if v not in valid_backends:
            raise ValueError(f"Storage backend must be one of: {valid_backends}")
        return v
    
    @validator("MANIM_QUALITY")
    def validate_manim_quality(cls, v):
        """Validate Manim quality setting."""
        valid_qualities = ["low", "medium", "high", "production"]
        if v not in valid_qualities:
            raise ValueError(f"Manim quality must be one of: {valid_qualities}")
        return v
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("EXPORT_FORMATS", pre=True)
    def parse_export_formats(cls, v) -> List[str]:
        """Parse export formats from string or list."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == "testing"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def manim_resolution_tuple(self) -> tuple:
        """Get Manim resolution as tuple."""
        width, height = self.MANIM_RESOLUTION.split("x")
        return (int(width), int(height))
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration based on backend."""
        if self.STORAGE_BACKEND == "s3":
            return {
                "backend": "s3",
                "bucket": self.S3_BUCKET_NAME,
                "region": self.S3_REGION,
                "access_key": self.AWS_ACCESS_KEY_ID,
                "secret_key": self.AWS_SECRET_ACCESS_KEY.get_secret_value() if self.AWS_SECRET_ACCESS_KEY else None,
            }
        elif self.STORAGE_BACKEND == "azure":
            return {
                "backend": "azure",
                "container": self.AZURE_CONTAINER_NAME,
                "connection_string": self.AZURE_STORAGE_CONNECTION_STRING.get_secret_value() if self.AZURE_STORAGE_CONNECTION_STRING else None,
            }
        elif self.STORAGE_BACKEND == "gcs":
            return {
                "backend": "gcs",
                "bucket": self.GCS_BUCKET_NAME,
                "credentials": self.GOOGLE_APPLICATION_CREDENTIALS,
                "project": self.GOOGLE_CLOUD_PROJECT,
            }
        else:  # local
            return {
                "backend": "local",
                "upload_dir": self.UPLOAD_DIR,
                "export_dir": self.EXPORT_DIR,
                "temp_dir": self.TEMP_DIR,
            }
    
    def get_ai_service_config(self) -> Dict[str, Any]:
        """Get AI service configuration."""
        return {
            "openai": {
                "api_key": self.OPENAI_API_KEY.get_secret_value() if self.OPENAI_API_KEY else None,
                "enabled": bool(self.OPENAI_API_KEY),
            },
            "anthropic": {
                "api_key": self.ANTHROPIC_API_KEY.get_secret_value() if self.ANTHROPIC_API_KEY else None,
                "enabled": bool(self.ANTHROPIC_API_KEY),
            },
            "aws_bedrock": {
                "region": self.AWS_BEDROCK_REGION,
                "access_key": self.AWS_ACCESS_KEY_ID,
                "secret_key": self.AWS_SECRET_ACCESS_KEY.get_secret_value() if self.AWS_SECRET_ACCESS_KEY else None,
                "enabled": bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY),
            },
            "azure_openai": {
                "client_id": self.AZURE_CLIENT_ID,
                "client_secret": self.AZURE_CLIENT_SECRET.get_secret_value() if self.AZURE_CLIENT_SECRET else None,
                "tenant_id": self.AZURE_TENANT_ID,
                "enabled": bool(self.AZURE_CLIENT_ID and self.AZURE_CLIENT_SECRET),
            },
            "google_vertex": {
                "project": self.GOOGLE_CLOUD_PROJECT,
                "credentials": self.GOOGLE_APPLICATION_CREDENTIALS,
                "enabled": bool(self.GOOGLE_CLOUD_PROJECT and self.GOOGLE_APPLICATION_CREDENTIALS),
            }
        }
    
    def validate_required_settings(self):
        """Validate that required settings are present for the current environment."""
        errors = []
        
        # Always required
        if not self.SECRET_KEY:
            errors.append("SECRET_KEY is required")
        if not self.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY is required")
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        # Production-specific requirements
        if self.is_production:
            if self.DEBUG:
                errors.append("DEBUG must be False in production")
            if not self.ENCRYPTION_KEY:
                errors.append("ENCRYPTION_KEY is required in production")
            if not any([self.OPENAI_API_KEY, self.ANTHROPIC_API_KEY, 
                       self.AWS_ACCESS_KEY_ID, self.AZURE_CLIENT_ID]):
                errors.append("At least one AI service must be configured in production")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    settings = Settings()
    
    # Validate settings
    try:
        settings.validate_required_settings()
    except ValueError as e:
        if settings.ENVIRONMENT != "testing":
            raise e
    
    return settings


# Export settings instance
settings = get_settings()
