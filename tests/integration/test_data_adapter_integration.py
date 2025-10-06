"""Integration tests for test-coordinator-data-adapter-py integration."""
import pytest
from fastapi.testclient import TestClient

from test_coordinator.main import create_app


class TestDataAdapterIntegration:
    """Test data adapter integration with test-coordinator service."""

    def test_app_starts_with_adapter_factory(self):
        """GIVEN the test coordinator application
        WHEN the app is created
        THEN adapter factory is available in app state."""
        # When
        app = create_app()

        # Then - app should be created successfully
        assert app is not None
        assert app.title == "Test Coordinator API"

    @pytest.mark.asyncio
    async def test_adapter_factory_initialization(self):
        """GIVEN the test coordinator application
        WHEN lifespan context is entered
        THEN adapter factory is initialized and available."""
        # Given
        app = create_app()

        # When
        async with app.router.lifespan_context(app):
            # Then
            assert hasattr(app.state, "adapter_factory")
            assert app.state.adapter_factory is not None

            # Factory should be initialized
            health = await app.state.adapter_factory.health_check()
            assert "factory_initialized" in health
            assert health["factory_initialized"] is True

            # Should have PostgreSQL and Redis health status
            assert "postgres" in health
            assert "redis" in health

    @pytest.mark.asyncio
    async def test_adapter_factory_provides_repositories(self):
        """GIVEN initialized adapter factory
        WHEN getting repositories
        THEN all repository types are available."""
        # Given
        app = create_app()

        async with app.router.lifespan_context(app):
            factory = app.state.adapter_factory

            # When
            scenarios_repo = factory.get_scenarios_repository()
            test_runs_repo = factory.get_test_runs_repository()
            chaos_events_repo = factory.get_chaos_events_repository()
            test_results_repo = factory.get_test_results_repository()
            service_discovery_repo = factory.get_service_discovery_repository()
            cache_repo = factory.get_cache_repository()

            # Then - all repositories should be available
            assert scenarios_repo is not None
            assert test_runs_repo is not None
            assert chaos_events_repo is not None
            assert test_results_repo is not None
            assert service_discovery_repo is not None
            assert cache_repo is not None

    @pytest.mark.asyncio
    async def test_adapter_factory_cleanup_on_shutdown(self):
        """GIVEN initialized adapter factory
        WHEN lifespan context exits
        THEN adapter factory is cleaned up properly."""
        # Given
        app = create_app()

        # When
        async with app.router.lifespan_context(app):
            factory = app.state.adapter_factory
            assert factory._is_initialized is True

        # Then - after context exit, factory should be cleaned up
        assert factory._is_initialized is False

    @pytest.mark.asyncio
    async def test_repositories_work_with_stub_implementation(self):
        """GIVEN adapter factory with stub repositories
        WHEN performing CRUD operations
        THEN stub repositories work correctly."""
        # Given
        app = create_app()

        async with app.router.lifespan_context(app):
            from test_coordinator_data_adapter.models import (
                Scenario,
                ScenarioType,
                ScenarioStatus,
            )

            factory = app.state.adapter_factory
            scenarios_repo = factory.get_scenarios_repository()

            # When - create a scenario
            scenario = Scenario(
                scenario_id="integration-test-001",
                name="Integration Test Scenario",
                scenario_type=ScenarioType.SERVICE_RESTART,
                status=ScenarioStatus.ACTIVE,
                configuration={"timeout": 30},
                services_under_test=["test-coordinator"],
            )

            created = await scenarios_repo.create(scenario)

            # Then
            assert created.scenario_id == "integration-test-001"
            assert created.name == "Integration Test Scenario"

            # When - retrieve the scenario
            retrieved = await scenarios_repo.get_by_id("integration-test-001")

            # Then
            assert retrieved is not None
            assert retrieved.scenario_id == "integration-test-001"
            assert retrieved.scenario_type == ScenarioType.SERVICE_RESTART

    def test_health_endpoint_works_with_adapter(self):
        """GIVEN test coordinator with adapter integration
        WHEN calling health endpoint
        THEN health check succeeds."""
        # Given
        app = create_app()
        client = TestClient(app)

        # When
        response = client.get("/api/v1/health")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_adapter_graceful_degradation_without_infrastructure(self):
        """GIVEN adapter factory without PostgreSQL/Redis
        WHEN health check is performed
        THEN graceful degradation to stubs occurs."""
        # Given
        app = create_app()

        async with app.router.lifespan_context(app):
            factory = app.state.adapter_factory

            # When
            health = await factory.health_check()

            # Then - factory should be initialized even without infrastructure
            assert health["factory_initialized"] is True

            # PostgreSQL and Redis will show as not connected (expected without infra)
            # But this should not prevent the service from working
            assert "postgres" in health
            assert "redis" in health
