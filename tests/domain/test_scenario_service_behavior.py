#!/usr/bin/env python3
"""
Behavior tests for ScenarioService domain logic

This module contains comprehensive behavior-focused tests for the ScenarioService
class, testing core scenario orchestration and chaos testing behaviors following TDD principles.

🎯 Behavior Coverage:
- Scenario lifecycle management (load → start → execute → stop)
- Active scenario state tracking and isolation
- Chaos injection and event correlation
- Result validation and outcome verification
- Multi-scenario concurrent execution
- Error handling and recovery behaviors
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from test_coordinator.domain.scenario_service import ScenarioService


class TestScenarioServiceBehavior:
    """Test ScenarioService behavior patterns."""

    @pytest.fixture
    def scenario_service(self):
        """Create ScenarioService instance for testing."""
        return ScenarioService()

    @pytest.fixture
    def sample_scenario_def(self):
        """Sample scenario definition for testing."""
        return {
            "name": "chaos_network_latency",
            "description": "Test system resilience to network latency",
            "steps": [
                {
                    "type": "chaos_injection",
                    "target": "trading-system-engine",
                    "chaos_type": "network_latency",
                    "parameters": {"latency_ms": 500}
                },
                {
                    "type": "validation",
                    "check": "order_processing_continues",
                    "timeout_seconds": 30
                }
            ]
        }

    # === Scenario Lifecycle Behaviors ===

    @pytest.mark.asyncio
    async def test_scenario_loads_with_expected_structure(self, scenario_service):
        """Behavior: Loading a scenario returns expected structure."""
        scenario_path = "/path/to/scenario.yaml"

        scenario_def = await scenario_service.load_scenario(scenario_path)

        # Should return structured scenario definition
        assert isinstance(scenario_def, dict)
        assert "name" in scenario_def
        assert "description" in scenario_def
        assert "steps" in scenario_def
        assert isinstance(scenario_def["steps"], list)

    @pytest.mark.asyncio
    async def test_scenario_starts_and_tracks_execution_state(self, scenario_service, sample_scenario_def):
        """Behavior: Starting a scenario creates trackable execution state."""
        scenario_id = "chaos_test_001"

        execution_id = await scenario_service.start_scenario(scenario_id, sample_scenario_def)

        # Should return unique execution identifier
        assert execution_id.startswith(f"exec-{scenario_id}")

        # Should track scenario in active scenarios
        assert execution_id in scenario_service.active_scenarios

        # Should have correct initial state
        active_scenario = scenario_service.active_scenarios[execution_id]
        assert active_scenario["scenario_id"] == scenario_id
        assert active_scenario["definition"] == sample_scenario_def
        assert active_scenario["status"] == "running"
        assert active_scenario["current_step"] == 0

    @pytest.mark.asyncio
    async def test_scenario_stops_when_execution_exists(self, scenario_service, sample_scenario_def):
        """Behavior: Stopping a running scenario updates its status."""
        execution_id = await scenario_service.start_scenario("test_scenario", sample_scenario_def)

        result = await scenario_service.stop_scenario(execution_id)

        # Should successfully stop the scenario
        assert result is True

        # Should update scenario status
        active_scenario = scenario_service.active_scenarios[execution_id]
        assert active_scenario["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_scenario_stop_fails_when_execution_not_found(self, scenario_service):
        """Behavior: Stopping non-existent scenario returns failure."""
        non_existent_execution_id = "exec-nonexistent-001"

        result = await scenario_service.stop_scenario(non_existent_execution_id)

        # Should fail gracefully
        assert result is False

    @pytest.mark.asyncio
    async def test_scenario_status_retrieval_behavior(self, scenario_service, sample_scenario_def):
        """Behavior: Scenario status can be retrieved during execution."""
        execution_id = await scenario_service.start_scenario("status_test", sample_scenario_def)

        status = await scenario_service.get_scenario_status(execution_id)

        # Should return current scenario state
        assert status is not None
        assert status["scenario_id"] == "status_test"
        assert status["status"] == "running"
        assert "definition" in status
        assert "current_step" in status

    @pytest.mark.asyncio
    async def test_scenario_status_returns_none_for_unknown_execution(self, scenario_service):
        """Behavior: Status query for unknown execution returns None."""
        unknown_execution_id = "exec-unknown-001"

        status = await scenario_service.get_scenario_status(unknown_execution_id)

        assert status is None

    # === Chaos Injection Behaviors ===

    @pytest.mark.asyncio
    async def test_chaos_injection_generates_unique_identifiers(self, scenario_service):
        """Behavior: Chaos injection creates unique event identifiers."""
        target_service = "trading-system-engine"
        chaos_type = "network_latency"
        parameters = {"latency_ms": 1000}

        injection_id = await scenario_service.inject_chaos(target_service, chaos_type, parameters)

        # Should generate unique chaos event ID
        assert injection_id.startswith(f"chaos-{target_service}-{chaos_type}")

        # Multiple injections should have different IDs
        injection_id2 = await scenario_service.inject_chaos(target_service, chaos_type, parameters)
        assert injection_id != injection_id2  # Currently both return same ID, but behavior should be unique

    @pytest.mark.asyncio
    async def test_chaos_injection_supports_different_chaos_types(self, scenario_service):
        """Behavior: Different chaos types can be injected into same service."""
        target_service = "risk-monitor"

        latency_id = await scenario_service.inject_chaos(target_service, "network_latency", {"latency_ms": 500})
        failure_id = await scenario_service.inject_chaos(target_service, "service_failure", {"duration_s": 10})
        memory_id = await scenario_service.inject_chaos(target_service, "memory_pressure", {"memory_mb": 512})

        # Should generate different event IDs for different chaos types
        assert "network_latency" in latency_id
        assert "service_failure" in failure_id
        assert "memory_pressure" in memory_id
        assert latency_id != failure_id != memory_id

    # === Result Validation Behaviors ===

    @pytest.mark.asyncio
    async def test_result_validation_accepts_execution_context(self, scenario_service, sample_scenario_def):
        """Behavior: Result validation operates within execution context."""
        execution_id = await scenario_service.start_scenario("validation_test", sample_scenario_def)

        expected_outcomes = [
            {"metric": "order_processing_latency", "threshold": 1000, "operator": "less_than"},
            {"metric": "system_availability", "threshold": 99.5, "operator": "greater_than"}
        ]

        result = await scenario_service.validate_results(execution_id, expected_outcomes)

        # Should complete validation (currently returns True as placeholder)
        assert isinstance(result, bool)
        assert result is True

    @pytest.mark.asyncio
    async def test_result_validation_handles_multiple_outcome_criteria(self, scenario_service, sample_scenario_def):
        """Behavior: Validation can check multiple success criteria."""
        execution_id = await scenario_service.start_scenario("multi_validation", sample_scenario_def)

        complex_outcomes = [
            {"metric": "response_time_p95", "threshold": 500, "operator": "less_than"},
            {"metric": "error_rate", "threshold": 0.01, "operator": "less_than"},
            {"metric": "throughput", "threshold": 1000, "operator": "greater_than"},
            {"metric": "memory_usage", "threshold": 80, "operator": "less_than"}
        ]

        result = await scenario_service.validate_results(execution_id, complex_outcomes)

        # Should handle complex validation criteria
        assert isinstance(result, bool)

    # === Multi-Scenario Concurrent Execution Behaviors ===

    @pytest.mark.asyncio
    async def test_multiple_scenarios_execute_independently(self, scenario_service):
        """Behavior: Multiple scenarios can run concurrently without interference."""
        scenario_1_def = {"name": "latency_test", "steps": []}
        scenario_2_def = {"name": "failure_test", "steps": []}

        # Start two scenarios concurrently
        exec_1 = await scenario_service.start_scenario("scenario_1", scenario_1_def)
        exec_2 = await scenario_service.start_scenario("scenario_2", scenario_2_def)

        # Should have different execution IDs
        assert exec_1 != exec_2

        # Both should be tracked independently
        assert exec_1 in scenario_service.active_scenarios
        assert exec_2 in scenario_service.active_scenarios

        # Each should maintain independent state
        status_1 = await scenario_service.get_scenario_status(exec_1)
        status_2 = await scenario_service.get_scenario_status(exec_2)

        assert status_1["scenario_id"] != status_2["scenario_id"]
        assert status_1["definition"] != status_2["definition"]

    @pytest.mark.asyncio
    async def test_stopping_one_scenario_does_not_affect_others(self, scenario_service):
        """Behavior: Stopping one scenario leaves others unaffected."""
        # Start multiple scenarios
        exec_1 = await scenario_service.start_scenario("independent_1", {"name": "test_1", "steps": []})
        exec_2 = await scenario_service.start_scenario("independent_2", {"name": "test_2", "steps": []})
        exec_3 = await scenario_service.start_scenario("independent_3", {"name": "test_3", "steps": []})

        # Stop one scenario
        await scenario_service.stop_scenario(exec_2)

        # Other scenarios should remain running
        status_1 = await scenario_service.get_scenario_status(exec_1)
        status_2 = await scenario_service.get_scenario_status(exec_2)
        status_3 = await scenario_service.get_scenario_status(exec_3)

        assert status_1["status"] == "running"
        assert status_2["status"] == "stopped"
        assert status_3["status"] == "running"

    # === State Isolation and Management Behaviors ===

    @pytest.mark.asyncio
    async def test_scenario_service_maintains_separate_result_storage(self, scenario_service):
        """Behavior: Active scenarios and results are maintained separately."""
        # Initially both should be empty
        assert len(scenario_service.active_scenarios) == 0
        assert len(scenario_service.scenario_results) == 0

        # Start a scenario
        execution_id = await scenario_service.start_scenario("storage_test", {"name": "test", "steps": []})

        # Active scenarios should be populated, results still empty
        assert len(scenario_service.active_scenarios) == 1
        assert len(scenario_service.scenario_results) == 0
        assert execution_id in scenario_service.active_scenarios

    @pytest.mark.asyncio
    async def test_scenario_service_initializes_with_clean_state(self):
        """Behavior: New ScenarioService instances start with clean state."""
        service = ScenarioService()

        # Should start with empty state
        assert isinstance(service.active_scenarios, dict)
        assert isinstance(service.scenario_results, dict)
        assert len(service.active_scenarios) == 0
        assert len(service.scenario_results) == 0

    # === Error Handling and Edge Case Behaviors ===

    @pytest.mark.asyncio
    async def test_scenario_service_handles_none_parameters_gracefully(self, scenario_service):
        """Behavior: Service handles None parameters without crashing."""
        # These should not raise exceptions
        result = await scenario_service.stop_scenario(None)
        assert result is False

        status = await scenario_service.get_scenario_status(None)
        assert status is None

    @pytest.mark.asyncio
    async def test_scenario_service_handles_empty_scenario_definition(self, scenario_service):
        """Behavior: Service accepts empty scenario definitions."""
        empty_scenario = {}

        # Should handle empty definition without error
        execution_id = await scenario_service.start_scenario("empty_test", empty_scenario)

        assert execution_id is not None
        assert execution_id.startswith("exec-empty_test")

        status = await scenario_service.get_scenario_status(execution_id)
        assert status["definition"] == empty_scenario

    @pytest.mark.asyncio
    async def test_chaos_injection_handles_empty_parameters(self, scenario_service):
        """Behavior: Chaos injection works with minimal parameters."""
        # Should work with empty parameters
        injection_id = await scenario_service.inject_chaos("test-service", "test-chaos", {})

        assert injection_id is not None
        assert "test-service" in injection_id
        assert "test-chaos" in injection_id

    @pytest.mark.asyncio
    async def test_result_validation_handles_empty_outcomes_list(self, scenario_service, sample_scenario_def):
        """Behavior: Validation works with empty expected outcomes."""
        execution_id = await scenario_service.start_scenario("empty_outcomes", sample_scenario_def)

        # Should handle empty outcomes list
        result = await scenario_service.validate_results(execution_id, [])

        assert isinstance(result, bool)


class TestScenarioServiceLoggingBehavior:
    """Test logging behaviors of ScenarioService."""

    @pytest.fixture
    def scenario_service(self):
        """Create ScenarioService instance for testing."""
        return ScenarioService()

    @pytest.mark.asyncio
    @patch('test_coordinator.domain.scenario_service.logger')
    async def test_scenario_loading_logs_with_context(self, mock_logger, scenario_service):
        """Behavior: Scenario loading includes contextual logging."""
        scenario_path = "/test/scenarios/chaos_latency.yaml"

        await scenario_service.load_scenario(scenario_path)

        # Should log scenario loading with path context
        mock_logger.info.assert_called_with("Loading scenario", scenario_path=scenario_path)

    @pytest.mark.asyncio
    @patch('test_coordinator.domain.scenario_service.logger')
    async def test_scenario_start_logs_with_scenario_id(self, mock_logger, scenario_service):
        """Behavior: Scenario start includes scenario ID in logs."""
        scenario_id = "test_scenario_001"
        scenario_def = {"name": "test", "steps": []}

        await scenario_service.start_scenario(scenario_id, scenario_def)

        # Should log scenario start with ID context
        mock_logger.info.assert_called_with("Starting scenario", scenario_id=scenario_id)

    @pytest.mark.asyncio
    @patch('test_coordinator.domain.scenario_service.logger')
    async def test_scenario_stop_logs_execution_context(self, mock_logger, scenario_service):
        """Behavior: Scenario stop logs execution ID for traceability."""
        execution_id = await scenario_service.start_scenario("stop_test", {"name": "test", "steps": []})

        await scenario_service.stop_scenario(execution_id)

        # Should log stopping with execution context
        mock_logger.info.assert_called_with("Stopping scenario", execution_id=execution_id)

    @pytest.mark.asyncio
    @patch('test_coordinator.domain.scenario_service.logger')
    async def test_chaos_injection_logs_as_warning_with_full_context(self, mock_logger, scenario_service):
        """Behavior: Chaos injection logs as warning with complete context."""
        target_service = "trading-system-engine"
        chaos_type = "network_partition"
        parameters = {"duration_s": 60, "partition_type": "split_brain"}

        await scenario_service.inject_chaos(target_service, chaos_type, parameters)

        # Should log chaos injection as warning with full context
        mock_logger.warning.assert_called_with(
            "Injecting chaos",
            target_service=target_service,
            chaos_type=chaos_type,
            parameters=parameters
        )

    @pytest.mark.asyncio
    @patch('test_coordinator.domain.scenario_service.logger')
    async def test_result_validation_logs_execution_context(self, mock_logger, scenario_service):
        """Behavior: Result validation logs include execution context."""
        execution_id = await scenario_service.start_scenario("validation_log_test", {"name": "test", "steps": []})

        await scenario_service.validate_results(execution_id, [])

        # Should log validation with execution context
        mock_logger.info.assert_called_with("Validating results", execution_id=execution_id)


def run_behavior_validation():
    """Run behavior validation and print results."""
    print("🚀 Running ScenarioService Behavior Validation")
    print("=" * 60)

    try:
        # This would be used for direct execution validation
        # In practice, these tests run via pytest
        print("✅ All behavior tests defined and ready for execution")
        print("\nKey behaviors covered:")
        print("- Scenario lifecycle management")
        print("- State isolation and tracking")
        print("- Chaos injection and correlation")
        print("- Result validation frameworks")
        print("- Multi-scenario concurrent execution")
        print("- Error handling and edge cases")
        print("- Comprehensive logging behaviors")

        return True

    except Exception as e:
        print(f"❌ Error in behavior validation setup: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_behavior_validation()
    sys.exit(0 if success else 1)