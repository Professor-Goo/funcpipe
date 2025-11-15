"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables with validation.
"""

from typing import List, Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Metadata
    api_title: str = Field(default="FuncPipe API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(
        default="Functional Data Processing Pipeline API",
        description="API description"
    )
    environment: str = Field(default="development", description="Environment name")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    reload: bool = Field(default=True, description="Auto-reload on code changes")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials")
    cors_methods: List[str] = Field(default=["*"], description="Allowed methods")
    cors_headers: List[str] = Field(default=["*"], description="Allowed headers")

    # Storage Configuration
    upload_dir: Path = Field(default=Path("storage/uploads"), description="Upload directory")
    result_dir: Path = Field(default=Path("storage/results"), description="Result directory")
    temp_dir: Path = Field(default=Path("storage/temp"), description="Temporary directory")
    max_upload_size_mb: int = Field(default=100, ge=1, description="Max upload size in MB")
    allowed_extensions: List[str] = Field(
        default=[".csv", ".json", ".tsv", ".txt"],
        description="Allowed file extensions"
    )

    # File Retention
    result_retention_hours: int = Field(default=24, ge=1, description="Result retention hours")
    temp_file_cleanup_hours: int = Field(default=1, ge=1, description="Temp cleanup hours")

    # Database
    database_url: str = Field(
        default="sqlite:///./storage/funcpipe.db",
        description="Database URL"
    )

    # Security
    secret_key: str = Field(
        default="change-this-to-a-random-secret-key-in-production",
        description="Secret key for JWT"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="Access token expiration"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, ge=1, description="Rate limit")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    @field_validator("upload_dir", "result_dir", "temp_dir", mode="after")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()


# Validate critical settings on startup
def validate_settings():
    """Validate critical settings and warn about issues."""
    warnings = []
    errors = []

    # Check secret key in production
    if settings.is_production() and settings.secret_key == "change-this-to-a-random-secret-key-in-production":
        errors.append("SECRET_KEY must be changed in production!")

    # Check CORS origins in production
    if settings.is_production() and "http://localhost" in str(settings.cors_origins):
        warnings.append("CORS origins include localhost in production")

    # Check database in production
    if settings.is_production() and "sqlite" in settings.database_url:
        warnings.append("Using SQLite in production - consider PostgreSQL")

    # Return validation results
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
