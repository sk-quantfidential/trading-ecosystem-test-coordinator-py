# Implementation Plan: TSE-0001.12.0 Named Components Foundation (test-coordinator-py)

## Branch
`feature/TSE-0001.12.0-named-components-foundation`

## Objective
Implement multi-instance infrastructure foundation for test-coordinator-py, following the proven pattern from risk-monitor-py and trading-system-engine-py. Enable deployment as singleton (test-coordinator) or multi-instance (test-coordinator-Chaos1, test-coordinator-Chaos2) with automatic PostgreSQL schema and Redis namespace derivation.

## Implementation Strategy

### Pattern to Follow
Based on successful implementations in:
- risk-monitor-py (TSE-0001.12.0) ✅
- trading-system-engine-py (TSE-0001.12.0) ✅

### Changes Required

#### 1. Configuration Layer (config.py)
**Current State:**
- No `service_instance_name` field
- No `environment: docker` support
- Ports: 8082/9092 (non-standard for Python services)
- No log_level validator

**Target State:**
- Add `service_instance_name: str` with auto-derivation
- Add `environment: Literal["development", "testing", "production", "docker"]`
- Add `@field_validator` for log_level normalization
- Change default ports: 8080/50051 (standard Python service ports)
- Add `model_post_init` for instance name derivation

#### 2. Health Endpoint (health.py)
**Current State:**
```python
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
```

**Target State:**
```python
class HealthResponse(BaseModel):
    status: str
    service: str
    instance: str      # NEW
    version: str
    environment: str   # NEW
    timestamp: str     # NEW (ISO 8601 UTC)
```

#### 3. Structured Logging (main.py)
**Current State:**
- Basic logger without instance context binding

**Target State:**
- Bind instance context to logger in `lifespan()`:
  - service_name
  - instance_name
  - environment

#### 4. Data Adapter Integration (main.py)
**Current State:**
```python
adapter_config = AdapterConfig(
    postgres_url=...,
    redis_url=...,
    service_name="test-coordinator",
    service_version=settings.version,
)
```

**Target State:**
```python
adapter_config = AdapterConfig(
    service_name=settings.service_name,
    service_instance_name=settings.service_instance_name,
    environment=settings.environment,
    postgres_url=settings.postgres_url,
    redis_url=settings.redis_url,
)
```

#### 5. Dockerfile
**Current State:**
- Ports: 8082/9092
- Health check: localhost:8082/api/v1/health

**Target State:**
- Ports: 8080/50051 (standardized)
- Health check: localhost:8080/api/v1/health
- Maintain Docker CLI installation (unique to test-coordinator)

#### 6. Docker Compose (orchestrator-docker/docker-compose.yml)
**Current State:**
- Not yet added to docker-compose.yml

**Target State:**
- Add test-coordinator service
- Port mapping: 8087:8080, 50055:50051 (next available external ports)
- IP: 172.20.0.87 (next available)
- Environment variables for service identity

#### 7. Prometheus (orchestrator-docker/prometheus/prometheus.yml)
**Target State:**
- Add scrape target for test-coordinator
- Labels: service=test-coordinator, instance_name=test-coordinator, service_type=singleton

## TDD Implementation Phases

### Phase 1: Config Tests (RED)
Create `tests/unit/test_startup.py` with failing tests:
- TestSettingsInstanceAwareness (6 tests)
- TestLifespanInstanceContext (2 async tests)
- TestInstanceNameValidation (3 tests)
- TestEnvironmentConfiguration (4 tests)
- TestSettingsCaching (2 tests)
- TestCoordinatorSettings (2 tests for coordinator-specific settings)

**Expected**: 19 tests failing

### Phase 2: Config Implementation (GREEN)
Update `src/test_coordinator/infrastructure/config.py`:
- Add service_instance_name field
- Add environment with "docker" support
- Add @field_validator for log_level
- Add model_post_init for auto-derivation
- Change ports to 8080/50051

**Expected**: Config tests passing

### Phase 3: Health Tests (RED)
Update existing health tests or create new ones:
- Update HealthResponse model tests
- Test instance metadata presence
- Test timestamp format (ISO 8601 UTC)

**Expected**: Health tests failing

### Phase 4: Health Implementation (GREEN)
Update `src/test_coordinator/presentation/health.py`:
- Update HealthResponse model
- Add instance, environment, timestamp fields
- Return ISO 8601 UTC timestamp

Update `src/test_coordinator/main.py`:
- Add logger binding with instance context
- Update adapter config with service identity

**Expected**: All tests passing

### Phase 5: Dockerfile Update
Update `Dockerfile`:
- Change EXPOSE to 8080/50051
- Update HEALTHCHECK to port 8080
- Keep Docker CLI installation

### Phase 6: Docker Compose & Prometheus
Update `orchestrator-docker/docker-compose.yml`:
- Add test-coordinator service
- Set ports, network, environment variables

Update `orchestrator-docker/prometheus/prometheus.yml`:
- Add test-coordinator scrape target

### Phase 7: Validation
- Run all tests: `pytest tests/ -v`
- Verify 100% test pass rate
- Check test coverage

### Phase 8: Documentation
Create `docs/prs/feature-TSE-0001.12.0-named-components-foundation.md`

Update `TODO.md`:
- Add TSE-0001.12.0 milestone
- Mark as COMPLETED

### Phase 9: Master TODO Update
Update `project-plan/TODO-MASTER.md`:
- Document test-coordinator-py completion

### Phase 10: Commit Changes
Commit in repositories:
- test-coordinator-py
- orchestrator-docker
- project-plan

## BDD Acceptance Criteria

✅ Test Coordinator can be deployed as singleton (test-coordinator) or multi-instance (test-coordinator-Chaos1) with automatic schema/namespace derivation via test-coordinator-data-adapter-py

## Success Metrics

- All existing tests still passing
- 19 new startup tests passing
- Health endpoint returns instance metadata
- Dockerfile uses standard ports 8080/50051
- Docker-compose configured with unique external ports
- Prometheus scraping configured
- Clean Architecture maintained (no domain contamination)

## Dependencies

- test-coordinator-data-adapter-py (must support multi-instance derivation)
- orchestrator-docker (docker-compose.yml and prometheus.yml)

---

**Created**: 2025-10-09
**Epic**: TSE-0001 (Foundation Services & Infrastructure)
**Priority**: High
