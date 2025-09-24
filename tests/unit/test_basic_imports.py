#!/usr/bin/env python3
"""
Basic import and functionality validation for test-coordinator-py
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_coordinator.infrastructure.config import Settings
from test_coordinator.infrastructure.configuration_client import (
    ConfigurationServiceClient,
    ConfigurationValue,
    ConfigurationError,
    DEFAULT_CACHE_TTL_SECONDS,
    VALID_CONFIG_TYPES
)
from test_coordinator.infrastructure.service_discovery import ServiceDiscovery, ServiceInfo


class TestBasicImports:
    """Test basic imports and functionality work correctly."""

    def test_settings_import_and_creation(self):
        """Test Settings can be imported and created."""
        settings = Settings(environment="testing")
        assert settings.environment == "testing"
        print("✅ Settings import and creation working")

    def test_configuration_client_import_and_creation(self):
        """Test ConfigurationServiceClient can be imported and created."""
        settings = Settings(environment="testing")
        client = ConfigurationServiceClient(settings)
        assert client.settings.environment == "testing"
        print("✅ ConfigurationServiceClient import and creation working")

    def test_service_discovery_import_and_creation(self):
        """Test ServiceDiscovery can be imported and created."""
        discovery = ServiceDiscovery()
        assert discovery.redis_url == "redis://localhost:6379"
        print("✅ ServiceDiscovery import and creation working")

    def test_configuration_value_creation_and_validation(self):
        """Test ConfigurationValue creation and validation."""
        config_value = ConfigurationValue(
            key="test.key",
            value="test_value",
            type="string"
        )

        assert config_value.key == "test.key"
        assert config_value.value == "test_value"
        assert config_value.type == "string"
        assert config_value.validate() is True
        print("✅ ConfigurationValue creation and validation working")

    def test_configuration_value_type_conversions(self):
        """Test ConfigurationValue type conversion methods."""
        # String conversion
        string_config = ConfigurationValue(
            key="app.name",
            value="test-coordinator",
            type="string"
        )
        assert string_config.as_string() == "test-coordinator"

        # Number conversion
        number_config = ConfigurationValue(
            key="app.port",
            value="8083",
            type="number"
        )
        assert number_config.as_float() == 8083.0
        assert number_config.as_int() == 8083

        # Boolean conversion
        bool_config = ConfigurationValue(
            key="app.enabled",
            value="true",
            type="boolean"
        )
        assert bool_config.as_bool() is True

        print("✅ ConfigurationValue type conversions working")

    def test_service_info_creation(self):
        """Test ServiceInfo can be created."""
        service_info = ServiceInfo(
            name="test-coordinator",
            version="1.0.0",
            host="localhost",
            http_port=8082,
            grpc_port=9092,
            status="healthy"
        )

        assert service_info.name == "test-coordinator"
        assert service_info.host == "localhost"
        assert service_info.http_port == 8082
        assert service_info.grpc_port == 9092
        print("✅ ServiceInfo creation working")

    def test_constants_available(self):
        """Test that required constants are available."""
        assert DEFAULT_CACHE_TTL_SECONDS == 300
        assert "string" in VALID_CONFIG_TYPES
        assert "number" in VALID_CONFIG_TYPES
        assert "boolean" in VALID_CONFIG_TYPES
        assert "json" in VALID_CONFIG_TYPES
        assert len(VALID_CONFIG_TYPES) == 4
        print("✅ Constants available and correct")

    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        settings = Settings(environment="testing")
        client = ConfigurationServiceClient(settings)

        stats = client.get_cache_stats()
        expected_stats = {
            "cache_size": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0,
            "total_requests": 0
        }
        assert stats == expected_stats
        print("✅ Cache statistics working")

    def test_configuration_error_creation(self):
        """Test ConfigurationError can be created."""
        error = ConfigurationError("Test error message")
        assert str(error) == "Configuration error: Test error message"

        error_with_key = ConfigurationError("Not found", key="missing.key")
        assert "missing.key" in str(error_with_key)
        print("✅ ConfigurationError creation working")


def run_basic_validation():
    """Run basic validation and print results."""
    print("🚀 Running Basic Import and Functionality Validation")
    print("=" * 60)

    try:
        test_class = TestBasicImports()

        # Run all test methods
        test_class.test_settings_import_and_creation()
        test_class.test_configuration_client_import_and_creation()
        test_class.test_service_discovery_import_and_creation()
        test_class.test_configuration_value_creation_and_validation()
        test_class.test_configuration_value_type_conversions()
        test_class.test_service_info_creation()
        test_class.test_constants_available()
        test_class.test_cache_statistics()
        test_class.test_configuration_error_creation()

        print("\n🎉 All basic functionality working - GREEN phase successful!")
        return True

    except Exception as e:
        print(f"❌ Error in GREEN phase: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_basic_validation()
    sys.exit(0 if success else 1)