"""Service discovery integration for Test Coordinator service."""

import json
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


@dataclass
class ServiceInfo:
    """Information about a discovered service."""
    name: str
    version: str
    host: str
    http_port: int
    grpc_port: int
    status: str
    last_heartbeat: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class ServiceDiscovery:
    """Service discovery client using Redis backend."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize service discovery client.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self.service_key_prefix = "services:"

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self._redis = redis.from_url(self.redis_url)
            await self._redis.ping()
            logger.info("Service discovery initialized", redis_url=self.redis_url)
        except Exception as e:
            logger.error("Failed to initialize service discovery", error=str(e))
            raise

    async def register_service(self, service_info: ServiceInfo) -> None:
        """Register a service in the discovery system.

        Args:
            service_info: Service information to register
        """
        if not self._redis:
            await self.initialize()

        key = f"{self.service_key_prefix}{service_info.name}"

        service_data = {
            "name": service_info.name,
            "version": service_info.version,
            "host": service_info.host,
            "http_port": service_info.http_port,
            "grpc_port": service_info.grpc_port,
            "status": service_info.status,
            "last_heartbeat": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": service_info.metadata or {}
        }

        try:
            await self._redis.hset(key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in service_data.items()
            })
            # Set TTL for automatic cleanup of stale services
            await self._redis.expire(key, 300)  # 5 minutes

            logger.info("Service registered", service_name=service_info.name,
                       host=service_info.host, status=service_info.status)
        except Exception as e:
            logger.error("Failed to register service", service_name=service_info.name,
                        error=str(e))
            raise

    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get service information by name.

        Args:
            service_name: Name of the service to lookup

        Returns:
            ServiceInfo object if found, None otherwise
        """
        if not self._redis:
            await self.initialize()

        key = f"{self.service_key_prefix}{service_name}"

        try:
            service_data = await self._redis.hgetall(key)
            if not service_data:
                logger.warning("Service not found", service_name=service_name)
                return None

            # Decode bytes and parse JSON where needed
            decoded_data = {}
            for k, v in service_data.items():
                k_str = k.decode() if isinstance(k, bytes) else k
                v_str = v.decode() if isinstance(v, bytes) else v

                # Try to parse JSON for complex fields
                if k_str in ["metadata"]:
                    try:
                        decoded_data[k_str] = json.loads(v_str)
                    except (json.JSONDecodeError, TypeError):
                        decoded_data[k_str] = {}
                else:
                    decoded_data[k_str] = v_str

            return ServiceInfo(
                name=decoded_data.get("name", service_name),
                version=decoded_data.get("version", "unknown"),
                host=decoded_data.get("host", "localhost"),
                http_port=int(decoded_data.get("http_port", 8080)),
                grpc_port=int(decoded_data.get("grpc_port", 9090)),
                status=decoded_data.get("status", "unknown"),
                last_heartbeat=decoded_data.get("last_heartbeat"),
                metadata=decoded_data.get("metadata", {})
            )

        except Exception as e:
            logger.error("Failed to get service", service_name=service_name, error=str(e))
            return None

    async def list_services(self) -> Dict[str, ServiceInfo]:
        """List all registered services.

        Returns:
            Dictionary mapping service names to ServiceInfo objects
        """
        if not self._redis:
            await self.initialize()

        services = {}
        try:
            pattern = f"{self.service_key_prefix}*"
            async for key in self._redis.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                service_name = key_str.replace(self.service_key_prefix, "")

                service_info = await self.get_service(service_name)
                if service_info:
                    services[service_name] = service_info

        except Exception as e:
            logger.error("Failed to list services", error=str(e))

        return services

    async def unregister_service(self, service_name: str) -> None:
        """Unregister a service from discovery.

        Args:
            service_name: Name of the service to unregister
        """
        if not self._redis:
            await self.initialize()

        key = f"{self.service_key_prefix}{service_name}"

        try:
            await self._redis.delete(key)
            logger.info("Service unregistered", service_name=service_name)
        except Exception as e:
            logger.error("Failed to unregister service", service_name=service_name,
                        error=str(e))

    async def update_service_status(self, service_name: str, status: str) -> None:
        """Update service status and heartbeat.

        Args:
            service_name: Name of the service to update
            status: New status for the service
        """
        if not self._redis:
            await self.initialize()

        key = f"{self.service_key_prefix}{service_name}"

        try:
            await self._redis.hset(key, mapping={
                "status": status,
                "last_heartbeat": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
            # Refresh TTL
            await self._redis.expire(key, 300)

            logger.debug("Service status updated", service_name=service_name, status=status)
        except Exception as e:
            logger.error("Failed to update service status", service_name=service_name,
                        error=str(e))

    async def cleanup(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Service discovery connection closed")