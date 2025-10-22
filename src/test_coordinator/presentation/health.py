"""Health check endpoints for Test Coordinator service."""
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, status
from pydantic import BaseModel

from test_coordinator.infrastructure.config import get_settings
from test_coordinator.infrastructure.logging import get_logger

router = APIRouter()
logger = get_logger()


class HealthResponse(BaseModel):
    """Health check response model with instance metadata."""
    status: str
    service: str
    instance: str
    version: str
    environment: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    status: str
    checks: Dict[str, str]


@router.get("/health", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint with instance metadata."""
    settings = get_settings()

    logger.info("Health check requested")

    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        instance=settings.service_instance_name,
        version=settings.version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", status_code=status.HTTP_200_OK, response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check with dependency validation."""
    logger.info("Readiness check requested")

    # TODO: Add actual dependency checks (Docker, Redis, etc.)
    checks = {
        "docker": "ok",
        "redis": "ok",
        "scenario_engine": "ok",
    }

    return ReadinessResponse(
        status="ready",
        checks=checks,
    )