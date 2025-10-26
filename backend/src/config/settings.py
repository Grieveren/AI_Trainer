"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    app_name: str = "AI Trainer"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/aitrainer"
    )

    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Garmin OAuth
    garmin_client_id: Optional[str] = None
    garmin_client_secret: Optional[str] = None
    garmin_callback_url: str = "http://localhost:8000/api/v1/garmin/callback"

    # Celery
    celery_broker_url: str = "redis://localhost:6380/1"
    celery_result_backend: str = "redis://localhost:6380/2"

    # Claude AI
    anthropic_api_key: Optional[str] = None

    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    allowed_hosts: list[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()
