"""Configuration management for Test Coordinator service."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    http_port: int = Field(default=8082, gt=0, le=65535)
    grpc_port: int = Field(default=9092, gt=0, le=65535)

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # External services
    redis_url: str = "redis://localhost:6379"
    docker_socket: str = "unix:///var/run/docker.sock"

    # Test coordination settings
    scenario_timeout_seconds: int = 3600  # 1 hour default
    chaos_injection_enabled: bool = True
    scenario_results_retention_days: int = 7


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()