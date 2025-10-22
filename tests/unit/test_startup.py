"""Tests for Test Coordinator startup behavior and instance awareness.

This test suite validates that the test-coordinator-py correctly initializes
with instance-aware configuration, enabling multi-instance deployment patterns.

Test Coverage:
- Service initialization with singleton configuration
- Service initialization with multi-instance configuration
- Instance name auto-derivation
- Logger binding with instance context
- Data adapter configuration with service identity
- Settings validation
- Environment configuration
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from test_coordinator.infrastructure.config import Settings, get_settings


class TestSettingsInstanceAwareness:
    """Test Settings configuration with instance awareness."""

    def test_settings_singleton_instance(self):
        """Should correctly configure singleton instance."""
        settings = Settings(
            service_name="test-coordinator",
            service_instance_name="test-coordinator",
        )
        assert settings.service_name == "test-coordinator"
        assert settings.service_instance_name == "test-coordinator"
        assert settings.environment == "development"  # default

    def test_settings_multi_instance(self):
        """Should correctly configure multi-instance deployment."""
        settings = Settings(
            service_name="test-coordinator",
            service_instance_name="test-coordinator-Chaos1",
            environment="production",
        )
        assert settings.service_name == "test-coordinator"
        assert settings.service_instance_name == "test-coordinator-Chaos1"
        assert settings.environment == "production"

    def test_settings_auto_derive_instance_name(self):
        """Should auto-derive instance name from service name when not provided."""
        settings = Settings(
            service_name="test-coordinator",
            service_instance_name="",  # Empty triggers auto-derivation
        )
        assert settings.service_instance_name == "test-coordinator"

    def test_settings_docker_environment(self):
        """Should support docker environment."""
        settings = Settings(
            service_name="test-coordinator",
            environment="docker",
        )
        assert settings.environment == "docker"
        assert settings.service_instance_name == "test-coordinator"

    def test_settings_log_level_normalization(self):
        """Should normalize log level to uppercase."""
        settings = Settings(
            service_name="test-coordinator",
            log_level="info",  # lowercase
        )
        assert settings.log_level == "INFO"  # normalized to uppercase

    def test_settings_default_ports(self):
        """Should use standard ports for Python services."""
        settings = Settings()
        assert settings.http_port == 8080  # Standard Python service HTTP port
        assert settings.grpc_port == 50051  # Standard Python service gRPC port


class TestLifespanInstanceContext:
    """Test lifespan manager with instance context."""

    @pytest.mark.asyncio
    async def test_lifespan_binds_logger_context(self):
        """Should bind instance context to logger during startup."""
        from test_coordinator.main import lifespan
        from fastapi import FastAPI

        app = FastAPI()

        with patch('test_coordinator.main.get_settings') as mock_get_settings:
            with patch('test_coordinator.main.structlog.get_logger') as mock_get_logger:
                with patch('test_coordinator.main.AdapterFactory') as mock_adapter_factory:
                    # Setup mocks
                    mock_settings = Mock()
                    mock_settings.service_name = "test-coordinator"
                    mock_settings.service_instance_name = "test-coordinator"
                    mock_settings.environment = "testing"
                    mock_settings.version = "0.1.0"
                    mock_settings.postgres_url = "postgresql://test"
                    mock_settings.redis_url = "redis://test"
                    mock_get_settings.return_value = mock_settings

                    mock_logger = Mock()
                    mock_bound_logger = Mock()
                    mock_logger.bind.return_value = mock_bound_logger
                    mock_get_logger.return_value = mock_logger

                    mock_factory = AsyncMock()
                    mock_factory.initialize = AsyncMock()
                    mock_factory.health_check = AsyncMock(return_value={
                        "postgres": {"connected": True},
                        "redis": {"connected": True},
                    })
                    mock_factory.cleanup = AsyncMock()
                    mock_adapter_factory.return_value = mock_factory

                    # Execute lifespan
                    async with lifespan(app):
                        pass

                    # Verify logger binding
                    mock_logger.bind.assert_called_once_with(
                        service_name="test-coordinator",
                        instance_name="test-coordinator",
                        environment="testing",
                    )

    @pytest.mark.asyncio
    async def test_lifespan_configures_adapter_with_identity(self):
        """Should configure data adapter with service identity."""
        from test_coordinator.main import lifespan
        from fastapi import FastAPI
        from test_coordinator_data_adapter import AdapterConfig

        app = FastAPI()

        with patch('test_coordinator.main.get_settings') as mock_get_settings:
            with patch('test_coordinator.main.AdapterFactory') as mock_adapter_factory:
                with patch('test_coordinator.main.AdapterConfig', wraps=AdapterConfig) as mock_adapter_config:
                    with patch('test_coordinator.main.structlog.get_logger'):
                        # Setup mocks
                        mock_settings = Mock()
                        mock_settings.service_name = "test-coordinator"
                        mock_settings.service_instance_name = "test-coordinator-Chaos2"
                        mock_settings.environment = "production"
                        mock_settings.version = "0.1.0"
                        mock_settings.postgres_url = "postgresql://prod"
                        mock_settings.redis_url = "redis://prod"
                        mock_get_settings.return_value = mock_settings

                        mock_factory = AsyncMock()
                        mock_factory.initialize = AsyncMock()
                        mock_factory.health_check = AsyncMock(return_value={
                            "postgres": {"connected": True},
                            "redis": {"connected": True},
                        })
                        mock_factory.cleanup = AsyncMock()
                        mock_adapter_factory.return_value = mock_factory

                        # Execute lifespan
                        async with lifespan(app):
                            pass

                        # Verify AdapterConfig was called with service identity
                        # Check the keyword arguments passed to AdapterConfig
                        call_kwargs = mock_adapter_config.call_args[1]

                        assert call_kwargs.get("service_name") == "test-coordinator"
                        assert call_kwargs.get("service_instance_name") == "test-coordinator-Chaos2"
                        assert call_kwargs.get("environment") == "production"
                        assert call_kwargs.get("postgres_url") == "postgresql://prod"
                        assert call_kwargs.get("redis_url") == "redis://prod"


class TestInstanceNameValidation:
    """Test instance name validation and patterns."""

    def test_instance_name_matches_service_name_singleton(self):
        """Singleton should have matching service and instance names."""
        settings = Settings(
            service_name="test-coordinator",
            service_instance_name="test-coordinator",
        )
        assert settings.service_name == settings.service_instance_name

    def test_instance_name_differs_for_multi_instance(self):
        """Multi-instance should have different service and instance names."""
        settings = Settings(
            service_name="test-coordinator",
            service_instance_name="test-coordinator-Chaos1",
        )
        assert settings.service_name != settings.service_instance_name
        assert settings.service_instance_name.startswith(settings.service_name)

    def test_complex_instance_names(self):
        """Should handle complex instance naming patterns."""
        settings = Settings(
            service_name="test-coordinator",
            service_instance_name="test-coordinator-Chaos-Alpha-1",
        )
        assert settings.service_instance_name == "test-coordinator-Chaos-Alpha-1"


class TestEnvironmentConfiguration:
    """Test environment-specific configuration."""

    def test_development_environment(self):
        """Should configure development environment."""
        settings = Settings(environment="development")
        assert settings.environment == "development"
        assert not settings.debug  # default

    def test_testing_environment(self):
        """Should configure testing environment."""
        settings = Settings(environment="testing")
        assert settings.environment == "testing"

    def test_production_environment(self):
        """Should configure production environment."""
        settings = Settings(environment="production")
        assert settings.environment == "production"

    def test_docker_environment(self):
        """Should configure docker environment."""
        settings = Settings(environment="docker")
        assert settings.environment == "docker"


class TestSettingsCaching:
    """Test settings caching behavior."""

    def test_get_settings_returns_cached_instance(self):
        """Should return cached settings instance."""
        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # Should be same instance (cached)
        assert settings1 is settings2

    def test_settings_cache_clear(self):
        """Should support cache clearing."""
        get_settings.cache_clear()
        settings1 = get_settings()

        get_settings.cache_clear()
        settings2 = get_settings()

        # Should be different instances after cache clear
        assert settings1 is not settings2


class TestCoordinatorSettings:
    """Test coordinator-specific settings."""

    def test_coordinator_defaults(self):
        """Should have correct coordinator defaults."""
        settings = Settings()
        assert settings.scenario_timeout_seconds == 3600  # 1 hour
        assert settings.chaos_injection_enabled is True
        assert settings.scenario_results_retention_days == 7

    def test_coordinator_custom_values(self):
        """Should support custom coordinator values."""
        settings = Settings(
            scenario_timeout_seconds=7200,
            chaos_injection_enabled=False,
            scenario_results_retention_days=14,
        )
        assert settings.scenario_timeout_seconds == 7200
        assert settings.chaos_injection_enabled is False
        assert settings.scenario_results_retention_days == 14
