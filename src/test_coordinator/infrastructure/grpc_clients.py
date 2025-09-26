"""gRPC client implementations for Test Coordinator service."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, AsyncGenerator
import grpc
import structlog

from test_coordinator.infrastructure.service_discovery import ServiceDiscovery
from test_coordinator.infrastructure.constants import (
    DEFAULT_GRPC_TIMEOUT,
    DEFAULT_RISK_MONITOR_PORT,
    DEFAULT_TRADING_SYSTEM_ENGINE_PORT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_BACKOFF_MULTIPLIER,
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
    RISK_MONITOR_SERVICE_NAME,
    TRADING_SYSTEM_ENGINE_SERVICE_NAME
)
from test_coordinator.infrastructure.performance_monitor import (
    performance_monitor,
    timed_operation
)

logger = structlog.get_logger()


# Data Models for gRPC Communication
@dataclass
class StrategyStatus:
    """Strategy status data model."""
    strategy_id: str
    status: str
    positions: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: str = ""


@dataclass
class Position:
    """Position data model."""
    instrument_id: str
    quantity: float
    value: float
    side: str


@dataclass
class RiskReport:
    """Risk report data model."""
    scenario_id: str
    timestamp: str
    portfolio_value: float
    risk_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChaosEvent:
    """Chaos event data model."""
    event_type: str
    target_component: str
    event_id: str
    timestamp: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthResponse:
    """Health response data model."""
    status: str
    service: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)


class ServiceCommunicationError(Exception):
    """Exception raised for service communication errors."""

    def __init__(self, message: str, service: Optional[str] = None):
        """Initialize service communication error.

        Args:
            message: Error message
            service: Service name that caused the error
        """
        self.service = service
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.service:
            return f"Service communication error with {self.service}: {self.args[0]}"
        return f"Service communication error: {self.args[0]}"


@dataclass
class ConnectionStats:
    """Statistics for connection management."""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0


@dataclass
class ClientStats:
    """Statistics for individual clients."""
    requests_sent: int = 0
    responses_received: int = 0
    errors_encountered: int = 0
    connection_status: str = "disconnected"
    average_response_time: float = 0.0
    last_request_time: Optional[str] = None


@dataclass
class StrategyStatus:
    """Strategy status information."""
    strategy_id: str
    status: str
    positions: List['Position'] = field(default_factory=list)
    last_updated: str = ""


@dataclass
class Position:
    """Position information."""
    instrument_id: str
    quantity: float
    value: float
    side: str


@dataclass
class RiskReport:
    """Risk report data."""
    scenario_id: str
    timestamp: str
    portfolio_value: float
    risk_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChaosEvent:
    """Chaos event data."""
    event_type: str
    target_component: str
    event_id: str
    timestamp: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


class BaseGrpcClient:
    """Base class for gRPC clients with common functionality."""

    def __init__(self, host: str, port: int, settings, timeout: float = DEFAULT_GRPC_TIMEOUT):
        """Initialize base gRPC client.

        Args:
            host: Service host
            port: Service port
            settings: Application settings
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.settings = settings
        self.timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None
        # OpenTelemetry tracing attributes
        self._tracer = None  # Would be initialized with actual tracer in production
        self._create_span = self._create_span_method
        self.is_connected = False
        self._stats = ClientStats()
        self._max_retries = DEFAULT_MAX_RETRIES
        self._retry_delay = DEFAULT_RETRY_DELAY
        self._backoff_multiplier = DEFAULT_BACKOFF_MULTIPLIER

    def _create_span_method(self, operation: str):
        """Create a tracing span for an operation (placeholder)."""
        # In production, this would create an actual OpenTelemetry span
        return None

    @property
    def endpoint(self) -> str:
        """Get gRPC endpoint address."""
        return f"{self.host}:{self.port}"

    @timed_operation("grpc_client", "connection")
    async def connect(self) -> None:
        """Establish gRPC connection."""
        try:
            if self._channel:
                await self._channel.close()

            self._channel = grpc.aio.insecure_channel(self.endpoint)

            # Test connection with a timeout
            await asyncio.wait_for(
                self._channel.channel_ready(),
                timeout=5.0
            )

            self.is_connected = True
            self._stats.connection_status = "connected"
            logger.info("gRPC connection established", endpoint=self.endpoint)

            # Record successful connection
            performance_monitor.record_custom_metric(
                component="grpc_client",
                metric_name="connections_established",
                value=1,
                labels={"endpoint": self.endpoint}
            )

        except asyncio.TimeoutError:
            raise ServiceCommunicationError(f"Connection timeout to {self.endpoint}")
        except Exception as e:
            self.is_connected = False
            self._stats.connection_status = "failed"
            self._stats.errors_encountered += 1

            # Record failed connection
            performance_monitor.record_custom_metric(
                component="grpc_client",
                metric_name="connections_failed",
                value=1,
                labels={"endpoint": self.endpoint}
            )

            raise ServiceCommunicationError(f"Connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close gRPC connection."""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None
            self.is_connected = False
            self._stats.connection_status = "disconnected"
            logger.info("gRPC connection closed", endpoint=self.endpoint)

    async def _ensure_connected(self) -> None:
        """Ensure connection is established."""
        if not self.is_connected or not self._channel:
            await self.connect()

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry logic.

        Args:
            operation: Async function to execute
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result

        Raises:
            ServiceCommunicationError: If all retries fail
        """
        last_exception = None
        delay = self._retry_delay

        for attempt in range(self._max_retries + 1):
            try:
                start_time = time.time()
                self._stats.requests_sent += 1

                result = await operation(*args, **kwargs)

                response_time = time.time() - start_time
                self._stats.responses_received += 1
                self._stats.average_response_time = (
                    (self._stats.average_response_time * (self._stats.responses_received - 1) + response_time) /
                    self._stats.responses_received
                )
                self._stats.last_request_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                return result

            except Exception as e:
                last_exception = e
                self._stats.errors_encountered += 1
                logger.warning(
                    "Request failed, retrying",
                    attempt=attempt,
                    max_attempts=self._max_retries,
                    error=str(e),
                    endpoint=self.endpoint
                )

                if attempt < self._max_retries:
                    await asyncio.sleep(delay)
                    delay *= self._backoff_multiplier
                    # Try to reconnect
                    try:
                        await self.connect()
                    except Exception:
                        pass  # Will retry on next attempt

        raise ServiceCommunicationError(
            f"Request failed after {self._max_retries + 1} attempts: {str(last_exception)}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "requests_sent": self._stats.requests_sent,
            "responses_received": self._stats.responses_received,
            "errors_encountered": self._stats.errors_encountered,
            "connection_status": self._stats.connection_status,
            "average_response_time": self._stats.average_response_time,
            "last_request_time": self._stats.last_request_time,
            "endpoint": self.endpoint
        }

    async def health_check(self) -> HealthResponse:
        """Perform health check."""
        # For now, just test the connection
        try:
            await self._ensure_connected()
            return HealthResponse(
                status="SERVING",
                service=self.__class__.__name__,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )
        except Exception as e:
            raise ServiceCommunicationError(f"Health check failed: {str(e)}")


class RiskMonitorClient(BaseGrpcClient):
    """gRPC client for Risk Monitor service."""

    def __init__(self, host: str, port: int, settings, timeout: float = DEFAULT_GRPC_TIMEOUT):
        """Initialize Risk Monitor gRPC client."""
        super().__init__(host, port, settings, timeout)

    async def submit_risk_report(self, risk_report: Dict[str, Any]) -> Dict[str, Any]:
        """Submit risk report to risk monitor.

        Args:
            risk_report: Risk report data

        Returns:
            Response from risk monitor

        Raises:
            ServiceCommunicationError: If request fails
        """
        async def _submit():
            await self._ensure_connected()
            # TODO: Implement actual gRPC call when proto files are available
            # For now, simulate the call
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"status": "accepted", "report_id": f"risk_{int(time.time())}"}

        try:
            return await self._execute_with_retry(_submit)
        except Exception as e:
            raise ServiceCommunicationError(f"Failed to submit risk report: {str(e)}", "risk-monitor")

    async def get_risk_limits(self) -> Dict[str, Any]:
        """Get current risk limits.

        Returns:
            Risk limits configuration

        Raises:
            ServiceCommunicationError: If request fails
        """
        async def _get_limits():
            await self._ensure_connected()
            # TODO: Implement actual gRPC call when proto files are available
            # For now, simulate the call
            await asyncio.sleep(0.1)
            return {
                "max_position_size": 1000000.0,
                "max_daily_loss": 50000.0,
                "var_limit": 100000.0
            }

        try:
            return await self._execute_with_retry(_get_limits)
        except Exception as e:
            raise ServiceCommunicationError(f"Failed to get risk limits: {str(e)}", "risk-monitor")

    async def subscribe_to_risk_alerts(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to risk alerts stream.

        Yields:
            Risk alert messages

        Raises:
            ServiceCommunicationError: If subscription fails
        """
        try:
            await self._ensure_connected()
            # TODO: Implement actual gRPC streaming call when proto files are available
            # For now, simulate with a simple generator
            for i in range(3):
                await asyncio.sleep(1)
                yield {
                    "alert_id": f"alert_{i}",
                    "severity": "medium",
                    "message": f"Test alert {i}",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
        except Exception as e:
            raise ServiceCommunicationError(f"Risk alerts subscription failed: {str(e)}", "risk-monitor")


class TradingSystemEngineClient(BaseGrpcClient):
    """gRPC client for Trading System Engine service."""

    def __init__(self, host: str, port: int, settings, timeout: float = DEFAULT_GRPC_TIMEOUT):
        """Initialize Trading System Engine gRPC client."""
        super().__init__(host, port, settings, timeout)

    async def get_strategy_status(self, strategy_id: str) -> StrategyStatus:
        """Get strategy status.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Strategy status information

        Raises:
            ServiceCommunicationError: If request fails
        """
        async def _get_status():
            await self._ensure_connected()
            # TODO: Implement actual gRPC call when proto files are available
            # For now, simulate the call
            await asyncio.sleep(0.1)
            return StrategyStatus(
                strategy_id=strategy_id,
                status="ACTIVE",
                positions=[
                    Position(
                        instrument_id="BTC/USD",
                        quantity=0.5,
                        value=25000.0,
                        side="LONG"
                    )
                ],
                last_updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )

        try:
            return await self._execute_with_retry(_get_status)
        except Exception as e:
            raise ServiceCommunicationError(f"Failed to get strategy status: {str(e)}", "trading-system-engine")

    async def trigger_chaos_event(self, chaos_event: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger chaos event on trading engine.

        Args:
            chaos_event: Chaos event configuration

        Returns:
            Response from trading engine

        Raises:
            ServiceCommunicationError: If request fails
        """
        async def _trigger_chaos():
            await self._ensure_connected()
            # TODO: Implement actual gRPC call when proto files are available
            # For now, simulate the call
            await asyncio.sleep(0.1)
            return {
                "status": "triggered",
                "event_id": chaos_event.get("event_id", f"chaos_{int(time.time())}"),
                "message": "Chaos event initiated successfully"
            }

        try:
            return await self._execute_with_retry(_trigger_chaos)
        except Exception as e:
            raise ServiceCommunicationError(f"Failed to trigger chaos event: {str(e)}", "trading-system-engine")

    async def subscribe_to_strategy_updates(self) -> AsyncGenerator[StrategyStatus, None]:
        """Subscribe to strategy updates stream.

        Yields:
            Strategy status updates

        Raises:
            ServiceCommunicationError: If subscription fails
        """
        try:
            await self._ensure_connected()
            # TODO: Implement actual gRPC streaming call when proto files are available
            # For now, simulate with a simple generator
            for i in range(3):
                await asyncio.sleep(2)
                yield StrategyStatus(
                    strategy_id=f"strategy_{i}",
                    status="ACTIVE" if i % 2 == 0 else "PAUSED",
                    positions=[],
                    last_updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                )
        except Exception as e:
            raise ServiceCommunicationError(f"Strategy updates subscription failed: {str(e)}", "trading-system-engine")


class InterServiceClientManager:
    """Manager for inter-service gRPC clients."""

    def __init__(self, settings, service_discovery: Optional[ServiceDiscovery] = None):
        """Initialize inter-service client manager.

        Args:
            settings: Application settings
            service_discovery: Optional service discovery client
        """
        self.settings = settings
        self.service_discovery = service_discovery
        self._clients: Dict[str, BaseGrpcClient] = {}
        self._connection_stats = ConnectionStats()
        self.is_initialized = False

        # Circuit breaker state
        self._circuit_breaker_state: Dict[str, str] = {}  # service -> state (open/closed/half-open)
        self._failure_count: Dict[str, int] = {}  # service -> failure count
        self._last_failure_time: Dict[str, float] = {}  # service -> last failure timestamp

    async def initialize(self) -> None:
        """Initialize the client manager."""
        self.is_initialized = True
        logger.info("Inter-service client manager initialized")

    async def _get_service_endpoint(self, service_name: str, default_port: int) -> tuple[str, int]:
        """Get service endpoint from discovery or fallback.

        Args:
            service_name: Name of the service
            default_port: Default port if service discovery fails

        Returns:
            Tuple of (host, port)
        """
        if self.service_discovery:
            try:
                service_info = await self.service_discovery.get_service(service_name)
                if service_info:
                    return service_info.host, service_info.grpc_port
            except Exception as e:
                logger.warning(
                    "Service discovery failed, using fallback",
                    service=service_name,
                    error=str(e)
                )

        return "localhost", default_port

    def _is_circuit_breaker_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for a service.

        Args:
            service_name: Service name

        Returns:
            True if circuit breaker is open
        """
        state = self._circuit_breaker_state.get(service_name, "closed")
        if state == "open":
            # Check if we should transition to half-open
            last_failure = self._last_failure_time.get(service_name, 0)
            if time.time() - last_failure > CIRCUIT_BREAKER_TIMEOUT:
                self._circuit_breaker_state[service_name] = "half-open"
                return False
            return True
        return False

    def _record_failure(self, service_name: str) -> None:
        """Record a failure for circuit breaker.

        Args:
            service_name: Service name
        """
        self._failure_count[service_name] = self._failure_count.get(service_name, 0) + 1
        self._last_failure_time[service_name] = time.time()

        if self._failure_count[service_name] >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:
            self._circuit_breaker_state[service_name] = "open"
            logger.warning("Circuit breaker opened", service=service_name)

    def _record_success(self, service_name: str) -> None:
        """Record a success for circuit breaker.

        Args:
            service_name: Service name
        """
        self._failure_count[service_name] = 0
        self._circuit_breaker_state[service_name] = "closed"

    async def get_risk_monitor_client(self, use_fallback: bool = False) -> RiskMonitorClient:
        """Get or create risk monitor client.

        Args:
            use_fallback: Whether to use fallback endpoint

        Returns:
            RiskMonitorClient instance

        Raises:
            ServiceCommunicationError: If circuit breaker is open
        """
        service_name = RISK_MONITOR_SERVICE_NAME
        client_key = f"{service_name}_client"

        if not use_fallback and self._is_circuit_breaker_open(service_name):
            raise ServiceCommunicationError(f"Circuit breaker open for {service_name}")

        if client_key not in self._clients:
            try:
                if use_fallback:
                    host, port = "localhost", DEFAULT_RISK_MONITOR_PORT
                else:
                    host, port = await self._get_service_endpoint(service_name, DEFAULT_RISK_MONITOR_PORT)

                client = RiskMonitorClient(host, port, self.settings)
                self._clients[client_key] = client
                self._connection_stats.total_connections += 1
                self._connection_stats.active_connections += 1

                # Test connection
                try:
                    await client.connect()
                    self._record_success(service_name)
                except Exception as e:
                    self._record_failure(service_name)
                    self._connection_stats.failed_connections += 1
                    raise ServiceCommunicationError(f"Connection failed: {str(e)}", service_name)

            except Exception as e:
                if not use_fallback:
                    self._record_failure(service_name)
                raise

        return self._clients[client_key]

    async def get_trading_system_engine_client(self, use_fallback: bool = False) -> TradingSystemEngineClient:
        """Get or create trading system engine client.

        Args:
            use_fallback: Whether to use fallback endpoint

        Returns:
            TradingSystemEngineClient instance

        Raises:
            ServiceCommunicationError: If circuit breaker is open
        """
        service_name = TRADING_SYSTEM_ENGINE_SERVICE_NAME
        client_key = f"{service_name}_client"

        if not use_fallback and self._is_circuit_breaker_open(service_name):
            raise ServiceCommunicationError(f"Circuit breaker open for {service_name}")

        if client_key not in self._clients:
            try:
                if use_fallback:
                    host, port = "localhost", DEFAULT_TRADING_SYSTEM_ENGINE_PORT
                else:
                    host, port = await self._get_service_endpoint(service_name, DEFAULT_TRADING_SYSTEM_ENGINE_PORT)

                client = TradingSystemEngineClient(host, port, self.settings)
                self._clients[client_key] = client
                self._connection_stats.total_connections += 1
                self._connection_stats.active_connections += 1

                # Test connection
                try:
                    await client.connect()
                    self._record_success(service_name)
                except Exception as e:
                    self._record_failure(service_name)
                    self._connection_stats.failed_connections += 1
                    raise ServiceCommunicationError(f"Connection failed: {str(e)}", service_name)

            except Exception as e:
                if not use_fallback:
                    self._record_failure(service_name)
                raise

        return self._clients[client_key]

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get manager statistics.

        Returns:
            Dictionary with manager statistics
        """
        return {
            "total_connections": self._connection_stats.total_connections,
            "active_connections": self._connection_stats.active_connections,
            "failed_connections": self._connection_stats.failed_connections,
            "circuit_breaker_states": dict(self._circuit_breaker_state),
            "failure_counts": dict(self._failure_count),
            "initialized": self.is_initialized,
            "average_response_time": sum(
                client.get_stats().get("average_response_time", 0)
                for client in self._clients.values()
            ) / len(self._clients) if self._clients else 0,
            "request_rate": sum(
                client.get_stats().get("requests_sent", 0)
                for client in self._clients.values()
            ),
            "error_rate": sum(
                client.get_stats().get("errors_encountered", 0)
                for client in self._clients.values()
            ) / max(1, sum(
                client.get_stats().get("requests_sent", 0)
                for client in self._clients.values()
            ))
        }

    async def cleanup(self) -> None:
        """Close all client connections and cleanup resources."""
        for client in self._clients.values():
            try:
                await client.disconnect()
                self._connection_stats.active_connections -= 1
            except Exception as e:
                logger.warning("Error during client cleanup", error=str(e))

        self._clients.clear()
        self.is_initialized = False
        logger.info("Inter-service client manager cleanup completed")