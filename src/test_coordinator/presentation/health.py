"""Health check endpoints for Test Coordinator service."""
from typing import Dict

from fastapi import APIRouter, status
from pydantic import BaseModel

from test_coordinator.infrastructure.config import get_settings
from test_coordinator.infrastructure.logging import get_logger

router = APIRouter()
logger = get_logger()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    status: str
    checks: Dict[str, str]


@router.get("/health", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    settings = get_settings()

    logger.info("Health check requested")

    return HealthResponse(
        status="healthy",
        service="test-coordinator",
        version=settings.version,
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