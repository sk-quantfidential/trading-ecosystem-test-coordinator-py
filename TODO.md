# test-coordinator-py TODO

## epic-TSE-0001: Foundation Services & Infrastructure

### 🏗️ Milestone TSE-0001.1b: Python Services Bootstrapping
**Status**: ✅ COMPLETED
**Priority**: High

**Tasks**:
- [x] Create Python service directory structure following clean architecture
- [x] Implement health check endpoint (REST and gRPC)
- [x] Basic structured logging with levels
- [x] Error handling infrastructure
- [x] Dockerfile for service containerization
- [x] Update to Python 3.13

**BDD Acceptance**: All Python services can start, respond to health checks, and shutdown gracefully

---

### 🔗 Milestone TSE-0001.3c: Python Services gRPC Integration
**Status**: ✅ **COMPLETED** (100% complete - ALL tasks done!)
**Priority**: High ➡️ DELIVERED
**Branch**: `feature/TSE-0001.3c-complete-grpc-integration` ✅ READY FOR MERGE

**Completed Tasks** (Full TDD Red-Green-Refactor Cycle):
- [x] **Task 1**: Create failing tests for configuration service client integration ✅ (RED phase)
- [x] **Task 2**: Implement configuration service client to make tests pass ✅ (GREEN phase)
- [x] **Task 3**: Create failing tests for inter-service communication ✅ (RED phase)
- [x] **Task 4**: Implement inter-service gRPC client communication ✅ (GREEN phase)
- [x] **Task 5**: Refactor and optimize implementation ✅ (REFACTOR phase)
- [x] **Task 6**: Validate BDD acceptance criteria and create completion documentation ✅ (VALIDATION)

**FINAL IMPLEMENTATION INCLUDES**:
- ✅ ConfigurationServiceClient with caching, validation, and performance monitoring
- ✅ InterServiceClientManager with connection pooling and circuit breaker patterns
- ✅ RiskMonitorClient and TradingSystemEngineClient with full gRPC capabilities
- ✅ Service discovery integration for dynamic endpoint resolution
- ✅ Performance monitoring with comprehensive metrics collection
- ✅ Production-ready error handling and resource management
- ✅ Complete data models for all inter-service communication types
- ✅ Constants module for centralized configuration management
- ✅ Comprehensive validation script demonstrating all functionality

**BDD Acceptance**: ✅ **VALIDATED** - Python services can discover and communicate with each other via gRPC

**Dependencies**: TSE-0001.1b (Python Services Bootstrapping), TSE-0001.3a (Core Infrastructure)

**Technical Implementation Details**:
- **Configuration Service Client**: Create client to fetch configuration from central config service
- **Service Discovery Integration**: Use existing ServiceDiscovery to find configuration service endpoint
- **Inter-Service Communication**: Implement gRPC client calls to other Python services (risk-monitor, trading-system-engine)
- **Testing Strategy**: TDD with failing tests first, then implementation to make tests pass
- **Error Handling**: Graceful fallback when services unavailable, retry mechanisms
- **Observability**: Performance monitoring and structured logging for all service-to-service calls

---

### 🏢 Milestone TSE-0001.12.0: Named Components Foundation (Multi-Instance Infrastructure)
**Status**: ✅ COMPLETED (2025-10-09)
**Priority**: High
**Branch**: `feature/TSE-0001.12.0-named-components-foundation`

**Completed Tasks**:
- [x] Add service_instance_name to infrastructure/config.py
- [x] Add environment field with "docker" support
- [x] Update health endpoint with instance metadata
- [x] Add structured logging with instance context binding
- [x] Update Dockerfile for standard ports (8080/50051)
- [x] Add docker-compose deployment configuration
- [x] Add prometheus scraping configuration
- [x] Add field_validator for case-insensitive log_level
- [x] Update data adapter configuration initialization
- [x] Create comprehensive startup tests (19 tests)
- [x] Validate Clean Architecture compliance

**Deliverables**:
- ✅ Instance-aware configuration (singleton and multi-instance ready)
- ✅ Health endpoint returns: service, instance, version, environment, timestamp
- ✅ Structured logging includes instance context in all logs
- ✅ Docker deployment with proper environment variables
- ✅ 19 startup tests validating instance awareness (all passing)
- ✅ All 174 tests passing (155 existing + 19 new)
- ✅ 100% Clean Architecture compliance (no domain contamination)

**BDD Acceptance**: ✅ **VALIDATED** - Test Coordinator can be deployed as singleton (test-coordinator) or multi-instance (test-coordinator-Chaos1, test-coordinator-Chaos2) with automatic schema/namespace derivation via test-coordinator-data-adapter-py

**Dependencies**: TSE-0001.3c (Python Services gRPC Integration)

**Integration Points**:
- test-coordinator-data-adapter-py: Derives PostgreSQL schema and Redis namespace from instance name
- orchestrator-docker: Deployed with SERVICE_INSTANCE_NAME=test-coordinator (singleton)
- Prometheus: Scrapes metrics with instance_name label on port 8087

---

### 📊 Milestone TSE-0001.12.0b: Prometheus Metrics (Clean Architecture)
**Status**: ✅ COMPLETED (2025-10-10)
**Priority**: High
**Branch**: `feature/TSE-0001.12.0b-prometheus-metrics-client`

**Completed Tasks**:
- [x] Create domain layer MetricsPort interface (protocol)
- [x] Create domain layer MetricsLabels helper dataclass
- [x] Write 8 BDD tests for domain layer (all passing)
- [x] Create PrometheusMetricsAdapter implementing MetricsPort
- [x] Create RED metrics middleware using MetricsPort
- [x] Write 11 BDD tests for infrastructure layer (all passing)
- [x] Create metrics router at /metrics endpoint
- [x] Update main.py with metrics initialization
- [x] Verify Prometheus configuration (already correct)
- [x] All 180 tests passing (19 new + 161 existing)

**Deliverables**:
- ✅ MetricsPort abstraction (Clean Architecture domain layer)
- ✅ PrometheusMetricsAdapter (infrastructure implementation)
- ✅ RED pattern middleware (Rate, Errors, Duration)
- ✅ Metrics endpoint at /metrics in Prometheus text format
- ✅ 19 comprehensive BDD tests (100% passing)
- ✅ Python runtime metrics included
- ✅ Constant labels (service, instance, version)
- ✅ Thread-safe lazy initialization
- ✅ Future-ready for OpenTelemetry migration

**BDD Acceptance**: ✅ **VALIDATED** - test-coordinator exposes /metrics endpoint with RED pattern metrics using Clean Architecture (domain never depends on Prometheus)

**Dependencies**: TSE-0001.12.0 (Named Components Foundation)

**Integration Points**:
- Prometheus: Scrapes metrics from 172.20.0.87:8080/metrics
- Grafana: Visualizes test-coordinator metrics alongside other services
- Clean Architecture: Zero Prometheus dependencies in domain layer

---

### 🧪 Milestone TSE-0001.9: Test Coordination Framework (PRIMARY)
**Status**: Not Started
**Priority**: CRITICAL - Enables chaos testing and validation

**Tasks**:
- [ ] YAML-based scenario definitions
- [ ] Basic scenario orchestration (start/stop services)
- [ ] Simple chaos injection (service restart)
- [ ] Result validation framework
- [ ] Scenario execution engine
- [ ] Test result reporting
- [ ] Integration with audit correlator
- [ ] Automated assertion framework

**BDD Acceptance**: Can execute a scenario that restarts a service and validates recovery

**Dependencies**: TSE-0001.3c (Python Services gRPC Integration)

---

### 📈 Milestone TSE-0001.12d: Chaos Testing Integration (PRIMARY)
**Status**: Not Started
**Priority**: CRITICAL - Validates complete system resilience

**Tasks**:
- [ ] Basic chaos scenario (service restart during trading)
- [ ] Scenario validation framework integration
- [ ] Automated test suite for system resilience
- [ ] Chaos injection verification through audit correlation
- [ ] Docker Compose deployment with single command startup

**BDD Acceptance**: System maintains functionality and provides audit trails during chaos scenarios

**Dependencies**: TSE-0001.9 (Test Coordination Framework), TSE-0001.12c (Audit Integration)

---

## Implementation Notes

- **Scenario Engine**: YAML-driven test scenarios for repeatability
- **Chaos Injection**: Controlled failure injection across all services
- **Validation Framework**: Automated assertions for scenario outcomes
- **Integration Testing**: Orchestrates complete system testing
- **Reporting**: Comprehensive test results and validation reports
- **CI/CD Ready**: Design for automated testing pipeline

---

**Last Updated**: 2025-10-10