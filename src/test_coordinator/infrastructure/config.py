"""Configuration management for Test Coordinator service."""
import re
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with multi-instance support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Identity (NEW for multi-instance support)
    service_name: str = Field(default="test-coordinator", description="Service name")
    service_instance_name: str = Field(default="", description="Instance identifier (defaults to service_name)")

    # Application settings
    version: str = "0.1.0"
    environment: Literal["development", "testing", "production", "docker"] = "development"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    http_port: int = Field(default=8080, gt=0, le=65535)  # Standard HTTP port (docker-compose maps to external)
    grpc_port: int = Field(default=50051, gt=0, le=65535)  # Standard gRPC port (docker-compose maps to external)

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # External services
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trading_ecosystem"
    docker_socket: str = "unix:///var/run/docker.sock"

    # Test coordination settings
    scenario_timeout_seconds: int = 3600  # 1 hour default
    chaos_injection_enabled: bool = True
    scenario_results_retention_days: int = 7

    @field_validator('log_level', mode='before')
    @classmethod
    def normalize_log_level(cls, v: Any) -> str:
        """Normalize log level to uppercase for Literal validation.

        This allows environment variables like LOG_LEVEL=info to work correctly,
        as Literal validation requires exact case matching.
        """
        if isinstance(v, str):
            return v.upper()
        return v

    def model_post_init(self, __context: Any) -> None:
        """Derive instance-specific configuration after model initialization.

        This hook runs after Pydantic validation and automatically derives
        service_instance_name from service_name if not explicitly provided.
        """
        if not self.service_instance_name:
            self.service_instance_name = self.service_name

    @model_validator(mode='after')
    def validate_instance_name(self) -> 'Settings':
        """Validate instance name is DNS-safe after all initialization."""
        name = self.service_instance_name

        if not name:
            raise ValueError("instance name cannot be empty after initialization")

        # DNS-safe pattern: lowercase alphanumeric + hyphens, must start/end with alphanumeric
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', name):
            raise ValueError(
                f"instance name must be DNS-safe: lowercase, alphanumeric, "
                f"hyphens only, must start and end with letter or number (got: {name})"
            )

        # Max 63 characters (DNS label limit)
        if len(name) > 63:
            raise ValueError(f"instance name exceeds 63 character limit (got: {len(name)} characters)")

        return self


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()