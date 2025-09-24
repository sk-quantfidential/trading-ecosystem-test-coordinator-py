"""Configuration service client for Test Coordinator service."""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import httpx
import structlog

from test_coordinator.infrastructure.service_discovery import ServiceDiscovery
from test_coordinator.infrastructure.constants import (
    DEFAULT_CACHE_TTL_SECONDS,
    VALID_CONFIG_TYPES,
    CONFIGURATION_SERVICE_NAME
)
from test_coordinator.infrastructure.performance_monitor import (
    performance_monitor,
    timed_operation
)

logger = structlog.get_logger()


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, key: Optional[str] = None):
        """Initialize configuration error.

        Args:
            message: Error message
            key: Configuration key that caused the error
        """
        self.key = key
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.key:
            return f"Configuration error for key '{self.key}': {self.args[0]}"
        return f"Configuration error: {self.args[0]}"


@dataclass
class ConfigurationValue:
    """Configuration value with type validation and conversion."""
    key: str
    value: str
    type: str
    environment: str = "production"

    def __post_init__(self):
        """Validate configuration type."""
        if self.type not in VALID_CONFIG_TYPES:
            raise ValueError(f"Invalid configuration type: {self.type}. Valid types: {VALID_CONFIG_TYPES}")

    def validate(self) -> bool:
        """Validate configuration value.

        Returns:
            True if valid, raises ValueError if invalid
        """
        try:
            if self.type == "number":
                float(self.value)
            elif self.type == "boolean":
                if self.value.lower() not in ["true", "false"]:
                    raise ValueError("Boolean value must be 'true' or 'false'")
            elif self.type == "json":
                json.loads(self.value)
            # String type always valid
            return True
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid value '{self.value}' for type '{self.type}': {e}")

    def as_string(self) -> str:
        """Get value as string."""
        return self.value

    def as_float(self) -> float:
        """Get value as float."""
        if self.type != "number":
            logger.warning("Converting non-number type to float", key=self.key, type=self.type)
        return float(self.value)

    def as_int(self) -> int:
        """Get value as integer."""
        if self.type != "number":
            logger.warning("Converting non-number type to int", key=self.key, type=self.type)
        return int(float(self.value))

    def as_bool(self) -> bool:
        """Get value as boolean."""
        if self.type != "boolean":
            logger.warning("Converting non-boolean type to bool", key=self.key, type=self.type)
        return self.value.lower() == "true"

    def as_json(self) -> Dict[str, Any]:
        """Get value as JSON object."""
        if self.type != "json":
            logger.warning("Converting non-json type to JSON", key=self.key, type=self.type)
        return json.loads(self.value)


class ConfigurationServiceClient:
    """Client for interacting with the configuration service."""

    def __init__(self, settings, service_discovery: Optional[ServiceDiscovery] = None):
        """Initialize configuration service client.

        Args:
            settings: Application settings
            service_discovery: Optional service discovery client
        """
        self.settings = settings
        self.service_discovery = service_discovery
        self._cache: Dict[str, tuple] = {}  # key -> (config_value, timestamp)
        self.cache_hits = 0
        self._cache_misses = 0
        self._cache_ttl = DEFAULT_CACHE_TTL_SECONDS
        self._http_timeout = 30.0

    @timed_operation("configuration_client", "service_discovery")
    async def _get_service_endpoint(self) -> str:
        """Get configuration service endpoint.

        Returns:
            Service endpoint URL
        """
        if self.service_discovery:
            try:
                service_info = await self.service_discovery.get_service(CONFIGURATION_SERVICE_NAME)
                if service_info:
                    endpoint = f"http://{service_info.host}:{service_info.http_port}"
                    performance_monitor.record_custom_metric(
                        component="configuration_client",
                        metric_name="service_discovery_success",
                        value=1,
                        labels={"service": CONFIGURATION_SERVICE_NAME}
                    )
                    return endpoint
            except Exception as e:
                logger.warning("Failed to discover configuration service", error=str(e))
                performance_monitor.record_custom_metric(
                    component="configuration_client",
                    metric_name="service_discovery_failure",
                    value=1,
                    labels={"service": CONFIGURATION_SERVICE_NAME}
                )

        # Fallback to default endpoint
        return "http://localhost:8090"

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache entry is still valid.

        Args:
            timestamp: Cache entry timestamp

        Returns:
            True if cache entry is valid, False if expired
        """
        return (time.time() - timestamp) < self._cache_ttl

    def _get_from_cache(self, key: str) -> Optional[ConfigurationValue]:
        """Get configuration from cache.

        Args:
            key: Configuration key

        Returns:
            ConfigurationValue if found and valid, None otherwise
        """
        if key in self._cache:
            config_value, timestamp = self._cache[key]
            if self._is_cache_valid(timestamp):
                self.cache_hits += 1
                logger.debug("Cache hit", key=key)
                return config_value
            else:
                # Remove expired entry
                del self._cache[key]
                logger.debug("Cache entry expired", key=key)

        self._cache_misses += 1
        return None

    def _store_in_cache(self, key: str, config_value: ConfigurationValue) -> None:
        """Store configuration in cache.

        Args:
            key: Configuration key
            config_value: Configuration value to cache
        """
        self._cache[key] = (config_value, time.time())
        logger.debug("Stored in cache", key=key, cache_size=len(self._cache))

    async def get_configuration(self, key: str, use_cache: bool = True) -> ConfigurationValue:
        """Get configuration value by key.

        Args:
            key: Configuration key
            use_cache: Whether to use cache

        Returns:
            ConfigurationValue object

        Raises:
            ConfigurationError: If configuration not found or service error
        """
        # Check cache first
        if use_cache:
            cached_value = self._get_from_cache(key)
            if cached_value:
                return cached_value

        # Fetch from service
        endpoint = await self._get_service_endpoint()
        url = f"{endpoint}/api/v1/configuration/{key}"

        try:
            async with httpx.AsyncClient(timeout=self._http_timeout) as client:
                response = await client.get(
                    url,
                    params={"environment": self.settings.environment}
                )

                if response.status_code == 404:
                    raise ConfigurationError(f"Configuration not found: {key}", key=key)
                elif response.status_code != 200:
                    error_text = getattr(response, 'text', 'Unknown error')
                    raise ConfigurationError(
                        f"Configuration service error (HTTP {response.status_code}): {error_text}",
                        key=key
                    )

                config_data = response.json()
                config_value = ConfigurationValue(
                    key=config_data["key"],
                    value=config_data["value"],
                    type=config_data["type"],
                    environment=config_data.get("environment", self.settings.environment)
                )

                # Validate configuration
                config_value.validate()

                # Store in cache
                if use_cache:
                    self._store_in_cache(key, config_value)

                logger.info("Configuration fetched", key=key, type=config_value.type,
                           environment=config_value.environment)

                return config_value

        except httpx.TimeoutException:
            raise ConfigurationError(f"Configuration service timeout for key: {key}", key=key)
        except httpx.RequestError as e:
            raise ConfigurationError(f"Configuration service request failed: {str(e)}", key=key)
        except (KeyError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Invalid configuration response format: {str(e)}", key=key)

    async def get_configurations(self, keys: List[str], use_cache: bool = True) -> Dict[str, ConfigurationValue]:
        """Get multiple configurations concurrently.

        Args:
            keys: List of configuration keys
            use_cache: Whether to use cache

        Returns:
            Dictionary mapping keys to ConfigurationValue objects
        """
        tasks = [
            self.get_configuration(key, use_cache=use_cache)
            for key in keys
        ]

        results = {}
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        for key, result in zip(keys, completed_tasks):
            if isinstance(result, ConfigurationError):
                logger.warning("Configuration fetch failed", key=key, error=str(result))
                # Re-raise the exception for individual key failures
                raise result
            elif isinstance(result, Exception):
                logger.error("Unexpected error fetching configuration", key=key, error=str(result))
                raise ConfigurationError(f"Unexpected error: {str(result)}", key=key)
            else:
                results[key] = result

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_hits + self._cache_misses
        hit_rate = (self.cache_hits / total_requests) if total_requests > 0 else 0.0

        return {
            "cache_size": len(self._cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info("Cache cleared", previous_size=cache_size)

    async def health_check(self) -> Dict[str, Any]:
        """Check health of configuration service.

        Returns:
            Health status information
        """
        endpoint = await self._get_service_endpoint()
        url = f"{endpoint}/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "endpoint": endpoint,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "endpoint": endpoint,
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": endpoint,
                "error": str(e)
            }

    async def cleanup(self) -> None:
        """Cleanup resources and clear cache."""
        self.clear_cache()
        self.cache_hits = 0
        self._cache_misses = 0
        logger.info("Configuration client cleanup completed")