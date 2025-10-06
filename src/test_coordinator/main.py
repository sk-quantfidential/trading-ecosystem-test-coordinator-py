"""Main application entry point for Test Coordinator service."""
import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI

from test_coordinator.infrastructure.config import get_settings
from test_coordinator.infrastructure.logging import setup_logging
from test_coordinator.presentation.health import router as health_router

# Data adapter integration
from test_coordinator_data_adapter import AdapterFactory, AdapterConfig


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()
    logger = structlog.get_logger()

    logger.info("Starting Test Coordinator service", version=settings.version)

    # Initialize data adapter
    adapter_config = AdapterConfig(
        postgres_url=getattr(settings, 'postgres_url', AdapterConfig().postgres_url),
        redis_url=getattr(settings, 'redis_url', AdapterConfig().redis_url),
        service_name="test-coordinator",
        service_version=settings.version,
    )

    adapter_factory = AdapterFactory(adapter_config)

    # Store adapter factory in app state for route access
    app.state.adapter_factory = adapter_factory

    # Initialize connections (will use stubs if infrastructure not available)
    try:
        await adapter_factory.initialize()
        health = await adapter_factory.health_check()
        logger.info(
            "Data adapter initialized",
            postgres_connected=health["postgres"]["connected"],
            redis_connected=health["redis"]["connected"],
        )
    except Exception as e:
        logger.warning(
            "Data adapter initialization failed, using stub repositories",
            error=str(e),
            error_type=type(e).__name__,
        )

    # Startup logic here
    yield

    # Shutdown logic here
    logger.info("Shutting down Test Coordinator service")

    # Cleanup data adapter
    try:
        await adapter_factory.cleanup()
        logger.info("Data adapter cleaned up successfully")
    except Exception as e:
        logger.error("Data adapter cleanup failed", error=str(e))


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Test Coordinator API",
        description="Scenario orchestration and chaos testing framework",
        version=settings.version,
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(health_router, prefix="/api/v1", tags=["health"])

    return app


def setup_signal_handlers() -> None:
    """Setup graceful shutdown signal handlers."""
    def signal_handler(signum: int, frame) -> None:
        logging.info(f"Received signal {signum}, shutting down gracefully")
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


async def main() -> None:
    """Main application entry point."""
    setup_logging()
    setup_signal_handlers()

    settings = get_settings()
    app = create_app()

    config = uvicorn.Config(
        app=app,
        host=settings.host,
        port=settings.http_port,
        log_config=None,  # Use our own logging
        access_log=False,
    )

    server = uvicorn.Server(config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())