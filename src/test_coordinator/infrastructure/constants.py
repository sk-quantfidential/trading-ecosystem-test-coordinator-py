"""Constants and configuration values for Test Coordinator infrastructure."""

# gRPC Configuration
DEFAULT_GRPC_TIMEOUT = 30.0
DEFAULT_RISK_MONITOR_PORT = 50056
DEFAULT_TRADING_SYSTEM_ENGINE_PORT = 50057

# Retry Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60.0  # seconds

# Configuration Service
DEFAULT_CACHE_TTL_SECONDS = 300  # 5 minutes
VALID_CONFIG_TYPES = ["string", "number", "boolean", "json"]

# Service Discovery
SERVICE_KEY_PREFIX = "services:"
SERVICE_DISCOVERY_TTL = 300  # 5 minutes

# Performance Monitoring
PERFORMANCE_METRICS_WINDOW_SIZE = 100
PERFORMANCE_METRICS_RETENTION_SECONDS = 3600  # 1 hour

# Health Check Configuration
HEALTH_CHECK_TIMEOUT = 5.0
HEALTH_CHECK_INTERVAL = 30.0

# Connection Pool Configuration
MAX_CONCURRENT_CONNECTIONS = 10
CONNECTION_IDLE_TIMEOUT = 300.0  # 5 minutes

# Observability
ENABLE_TRACING = True
ENABLE_METRICS = True
TRACE_SAMPLE_RATE = 0.1  # 10% sampling

# Test Coordination Settings
DEFAULT_SCENARIO_TIMEOUT = 3600  # 1 hour
DEFAULT_CHAOS_EVENT_DURATION = 300  # 5 minutes
MAX_CONCURRENT_SCENARIOS = 5

# Service Names
RISK_MONITOR_SERVICE_NAME = "risk-monitor"
TRADING_SYSTEM_ENGINE_SERVICE_NAME = "trading-system-engine"
CONFIGURATION_SERVICE_NAME = "configuration-service"