#!/usr/bin/env python3
"""
Basic gRPC clients validation for test-coordinator-py
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_coordinator.infrastructure.config import Settings
from test_coordinator.infrastructure.grpc_clients import (
    InterServiceClientManager,
    RiskMonitorClient,
    TradingSystemEngineClient,
    ServiceCommunicationError,
    DEFAULT_GRPC_TIMEOUT,
    DEFAULT_RISK_MONITOR_PORT,
    DEFAULT_TRADING_SYSTEM_ENGINE_PORT,
    StrategyStatus,
    Position,
    RiskReport,
    ChaosEvent,
    HealthResponse
)
from test_coordinator.infrastructure.service_discovery import ServiceDiscovery, ServiceInfo


class TestGrpcClientsBasic:
    """Test basic gRPC clients functionality."""

    def test_imports_work(self):
        """Test that all required imports work."""
        # If we get here, imports worked
        print("✅ All gRPC client imports working")

    def test_constants_available(self):
        """Test that required constants are available."""
        assert DEFAULT_GRPC_TIMEOUT > 0
        assert DEFAULT_RISK_MONITOR_PORT > 0
        assert DEFAULT_TRADING_SYSTEM_ENGINE_PORT > 0
        print("✅ Constants available and valid")

    def test_data_models_creation(self):
        """Test that data models can be created."""
        # Test StrategyStatus
        strategy = StrategyStatus(
            strategy_id="test_strategy",
            status="ACTIVE",
            positions=[],
            last_updated="2025-09-24T00:00:00Z"
        )
        assert strategy.strategy_id == "test_strategy"

        # Test Position
        position = Position(
            instrument_id="BTC/USD",
            quantity=0.5,
            value=25000.0,
            side="LONG"
        )
        assert position.instrument_id == "BTC/USD"

        # Test RiskReport
        risk_report = RiskReport(
            scenario_id="test_scenario",
            timestamp="2025-09-24T00:00:00Z",
            portfolio_value=1000000.0,
            risk_metrics={"var_95": 50000.0}
        )
        assert risk_report.scenario_id == "test_scenario"

        # Test ChaosEvent
        chaos_event = ChaosEvent(
            event_type="latency_injection",
            target_component="order_processor",
            event_id="chaos_001",
            timestamp="2025-09-24T00:00:00Z"
        )
        assert chaos_event.event_type == "latency_injection"

        # Test HealthResponse
        health = HealthResponse(
            status="SERVING",
            service="test-coordinator",
            timestamp="2025-09-24T00:00:00Z"
        )
        assert health.status == "SERVING"

        print("✅ All data models created successfully")

    def test_service_communication_error(self):
        """Test ServiceCommunicationError creation."""
        error = ServiceCommunicationError("Test error")
        assert "Test error" in str(error)

        error_with_service = ServiceCommunicationError("Connection failed", service="risk-monitor")
        assert "risk-monitor" in str(error_with_service)
        print("✅ ServiceCommunicationError working")

    def test_manager_creation(self):
        """Test InterServiceClientManager creation."""
        settings = Settings(environment="testing")
        manager = InterServiceClientManager(settings)

        assert manager.settings == settings
        assert manager.service_discovery is None
        assert not manager.is_initialized
        print("✅ InterServiceClientManager creation working")

    def test_risk_monitor_client_creation(self):
        """Test RiskMonitorClient creation."""
        settings = Settings(environment="testing")
        client = RiskMonitorClient("localhost", DEFAULT_RISK_MONITOR_PORT, settings)

        assert client.host == "localhost"
        assert client.port == DEFAULT_RISK_MONITOR_PORT
        assert not client.is_connected
        print("✅ RiskMonitorClient creation working")

    def test_trading_engine_client_creation(self):
        """Test TradingSystemEngineClient creation."""
        settings = Settings(environment="testing")
        client = TradingSystemEngineClient("localhost", DEFAULT_TRADING_SYSTEM_ENGINE_PORT, settings)

        assert client.host == "localhost"
        assert client.port == DEFAULT_TRADING_SYSTEM_ENGINE_PORT
        assert not client.is_connected
        print("✅ TradingSystemEngineClient creation working")

    @pytest.mark.asyncio
    async def test_manager_lifecycle(self):
        """Test manager initialization and cleanup."""
        settings = Settings(environment="testing")
        manager = InterServiceClientManager(settings)

        # Should start uninitialized
        assert not manager.is_initialized

        # Initialize
        await manager.initialize()
        assert manager.is_initialized

        # Get stats
        stats = manager.get_manager_stats()
        assert isinstance(stats, dict)
        assert "total_connections" in stats

        # Cleanup
        await manager.cleanup()
        assert not manager.is_initialized

        print("✅ Manager lifecycle working")

    def test_client_stats(self):
        """Test client statistics."""
        settings = Settings(environment="testing")
        client = RiskMonitorClient("localhost", DEFAULT_RISK_MONITOR_PORT, settings)

        stats = client.get_stats()
        assert isinstance(stats, dict)
        assert "requests_sent" in stats
        assert "responses_received" in stats
        assert "errors_encountered" in stats
        assert "connection_status" in stats

        print("✅ Client statistics working")


def run_basic_validation():
    """Run basic validation and print results."""
    print("🚀 Running Basic gRPC Clients Validation")
    print("=" * 50)

    try:
        test_class = TestGrpcClientsBasic()

        # Run all test methods
        test_class.test_imports_work()
        test_class.test_constants_available()
        test_class.test_data_models_creation()
        test_class.test_service_communication_error()
        test_class.test_manager_creation()
        test_class.test_risk_monitor_client_creation()
        test_class.test_trading_engine_client_creation()

        # Run async tests
        asyncio.run(test_class.test_manager_lifecycle())
        test_class.test_client_stats()

        print("\n🎉 All gRPC clients basic functionality working - GREEN phase successful!")
        return True

    except Exception as e:
        print(f"❌ Error in GREEN phase: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_basic_validation()
    sys.exit(0 if success else 1)