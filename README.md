# Test Coordinator

A sophisticated chaos engineering orchestrator built in Python that executes complex multi-service failure scenarios, validates system responses, and provides comprehensive scenario management for the trading ecosystem simulation.

## 🎯 Overview

The Test Coordinator serves as the central chaos engineering brain of the trading ecosystem, orchestrating complex failure scenarios across multiple services with precise timing and comprehensive validation. It translates high-level scenario definitions into coordinated API calls across exchanges, custodians, market data services, and trading engines while monitoring system responses and validating recovery behavior.

### Key Features
- **YAML-Driven Scenarios**: Declarative scenario definitions with complex timing and dependencies
- **Multi-Service Orchestration**: Coordinated chaos injection across all ecosystem components
- **Automated Validation**: Built-in assertions to verify expected system responses
- **Scenario Templates**: Reusable templates for common failure patterns
- **Real-Time Monitoring**: Live scenario execution monitoring with detailed logging
- **Failure Recovery Validation**: Automated verification of system recovery after chaos
- **Report Generation**: Comprehensive post-scenario analysis and reporting
- **CLI & API Interface**: Both command-line and programmatic scenario execution

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Test Coordinator                         │
├─────────────────────────────────────────────────────────┤
│  Scenario Management                                    │
│  ├─YAML Parser (Scenario definition parsing)           │
│  ├─Template Engine (Reusable scenario patterns)        │
│  ├─Scenario Validator (Pre-execution validation)       │
│  └─Scenario Library (Built-in scenario collection)     │
├─────────────────────────────────────────────────────────┤
│  Orchestration Engine                                   │
│  ├─Execution Scheduler (Multi-phase timing control)    │
│  ├─Chaos API Manager (Service chaos API coordination)  │
│  ├─Dependency Resolver (Inter-scenario dependencies)   │
│  └─Rollback Manager (Safe scenario termination)        │
├─────────────────────────────────────────────────────────┤
│  Validation Framework                                   │
│  ├─Assertion Engine (Expected behavior verification)   │
│  ├─System Monitor (Real-time system state tracking)    │
│  ├─Recovery Validator (Post-chaos recovery checks)     │
│  └─Performance Analyzer (System performance impact)    │
├─────────────────────────────────────────────────────────┤
│  Reporting & Analytics                                  │
│  ├─Execution Logger (Detailed scenario execution logs) │
│  ├─Report Generator (Post-scenario analysis reports)   │
│  ├─Metrics Publisher (Scenario execution metrics)      │
│  └─Timeline Reconstructor (Event sequence analysis)    │
├─────────────────────────────────────────────────────────┤
│  External Service Interfaces                           │
│  ├─Exchange Chaos APIs (Trading disruption injection)  │
│  ├─Custodian Chaos APIs (Settlement failure injection) │
│  ├─Market Data Chaos APIs (Price manipulation)        │
│  ├─Risk Monitor APIs (Risk system state monitoring)    │
│  └─Audit Correlator APIs (Event correlation tracking)  │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Docker and Docker Compose
- Access to all ecosystem service APIs
- YAML scenario definitions

### Development Setup
```bash
# Clone the repository
git clone <repo-url>
cd test-coordinator

# Install dependencies
go mod download

# Build the application
make build

# Validate scenario definitions
make validate-scenarios

# Run tests
make test

# Start development server
make run-dev
```

### Docker Deployment
```bash
# Build container
docker build -t test-coordinator .

# Run with docker-compose (recommended)
docker-compose up test-coordinator

# Verify health
curl http://localhost:8084/health
```

### Quick Scenario Execution
```bash
# Execute a predefined scenario
./test-coordinator execute --scenario stablecoin-depeg --duration 2h

# Execute from YAML file
./test-coordinator execute --file scenarios/market-crash.yaml

# List available scenarios
./test-coordinator list

# Validate scenario before execution
./test-coordinator validate --file scenarios/custom-scenario.yaml
```

## 📡 API Reference

### gRPC Services

#### Scenario Execution Service
```protobuf
service ScenarioExecutionService {
  rpc ExecuteScenario(ExecuteScenarioRequest) returns (ExecutionResponse);
  rpc GetExecutionStatus(ExecutionStatusRequest) returns (ExecutionStatus);
  rpc StopExecution(StopExecutionRequest) returns (StopExecutionResponse);
  rpc ListActiveExecutions(ListExecutionsRequest) returns (ListExecutionsResponse);
}
```

#### Scenario Management Service
```protobuf
service ScenarioManagementService {
  rpc ListScenarios(ListScenariosRequest) returns (ListScenariosResponse);
  rpc ValidateScenario(ValidateScenarioRequest) returns (ValidationResponse);
  rpc CreateScenario(CreateScenarioRequest) returns (CreateScenarioResponse);
  rpc GetScenarioResults(ResultsRequest) returns (ScenarioResults);
}
```

### REST Endpoints

#### Scenario Execution APIs
```
POST   /api/v1/scenarios/execute
GET    /api/v1/scenarios/active
GET    /api/v1/scenarios/{execution_id}/status
POST   /api/v1/scenarios/{execution_id}/stop
GET    /api/v1/scenarios/{execution_id}/logs
```

#### Scenario Management APIs
```
GET    /api/v1/scenarios/available
POST   /api/v1/scenarios/validate
GET    /api/v1/scenarios/{scenario_id}/definition
POST   /api/v1/scenarios/upload
GET    /api/v1/scenarios/{execution_id}/report
```

#### Real-Time Monitoring APIs
```
WebSocket /ws/scenario-execution (Live execution updates)
GET    /api/v1/system/state
GET    /api/v1/metrics/scenario-performance
GET    /debug/execution-timeline
```

## 📝 Scenario Definition Language

### Basic Scenario Structure
```yaml
# scenarios/basic-example.yaml
apiVersion: chaos.trading/v1
kind: Scenario
metadata:
  name: "basic-market-disruption"
  description: "Basic market disruption with exchange latency"
  version: "1.0"
  author: "chaos-engineering-team"
  tags: ["market", "exchange", "latency"]

spec:
  duration: "30m"
  timeout: "35m"
  
  phases:
    - name: "baseline"
      duration: "5m"
      description: "Establish baseline system behavior"
      actions: []
      assertions:
        - type: "system_health"
          expect: "all_services_healthy"
    
    - name: "chaos_injection"
      duration: "20m"
      description: "Inject exchange latency"
      actions:
        - service: "exchange-simulator"
          action: "inject_latency"
          parameters:
            delay_ms: 500
            operations: ["place_order", "cancel_order"]
            affected_accounts: ["strategy-arbitrage"]
      
      assertions:
        - type: "risk_alert"
          expect: "alert_generated"
          within: "2m"
          parameters:
            alert_type: "execution_latency"
        - type: "trading_adaptation"
          expect: "strategy_adjusts"
          within: "5m"
    
    - name: "recovery"
      duration: "5m"  
      description: "Validate system recovery"
      actions:
        - service: "exchange-simulator"
          action: "clear_chaos"
      
      assertions:
        - type: "system_recovery"
          expect: "normal_operations"
          within: "3m"
        - type: "alert_resolution"
          expect: "alerts_cleared"
          within: "2m"

  rollback:
    on_failure: true
    actions:
      - service: "exchange-simulator"
        action: "clear_all_chaos"
      - service: "market-data-simulator"
        action: "clear_all_chaos"
```

### Complex Multi-Service Scenario
```yaml
# scenarios/stablecoin-depeg.yaml
apiVersion: chaos.trading/v1
kind: Scenario
metadata:
  name: "stablecoin-depeg-scenario"
  description: "Gradual USDT depeg over 36 hours with settlement delays"
  version: "2.1"
  
spec:
  duration: "36h"
  timeout: "37h"
  
  variables:
    depeg_target: -0.05  # 5% depeg
    settlement_delay: 24h
    
  phases:
    - name: "setup"
      duration: "1h"
      description: "Establish normal trading conditions"
      actions:
        - service: "trading-engine"
          action: "start_strategy"
          parameters:
            strategy: "arbitrage"
            config:
              min_spread_bps: 5
              max_position_size: 10.0
      
      assertions:
        - type: "strategy_active"
          expect: "arbitrage_running"
          service: "trading-engine"
    
    - name: "gradual_depeg"
      duration: "24h"
      description: "Gradually depeg USDT from USD"
      actions:
        - service: "market-data-simulator"
          action: "stablecoin_depeg"
          parameters:
            symbol: "USDT-USD"
            target_deviation: "{{ .Variables.depeg_target }}"
            duration_hours: 24
            pattern: "gradual_linear"
      
      # Parallel chaos injection
      parallel_actions:
        - delay: "12h"  # Start settlement delays halfway through
          service: "custodian-simulator"
          action: "delay_settlements"
          parameters:
            settlement_types: ["crypto_external"]
            delay_duration: "{{ .Variables.settlement_delay }}"
      
      assertions:
        - type: "price_divergence"
          expect: "usdt_depegged"
          within: "25h"
          parameters:
            symbol: "USDT-USD"
            min_deviation: 0.02
        - type: "arbitrage_opportunity"
          expect: "increased_activity"
          within: "2h"
        - type: "risk_alert"
          expect: "correlation_breach_alert"
          within: "4h"
    
    - name: "peak_stress"
      duration: "6h"
      description: "Peak depeg stress with multiple failures"
      actions:
        - service: "exchange-simulator"
          action: "reduce_liquidity"
          parameters:
            symbols: ["USDT-BTC", "USDT-ETH"]
            reduction_factor: 0.5
      
      assertions:
        - type: "liquidity_crisis"
          expect: "wider_spreads"
          within: "30m"
        - type: "position_limits"
          expect: "limits_breached"
          within: "2h"
        - type: "emergency_procedures"
          expect: "risk_escalation"
          within: "1h"
    
    - name: "recovery"
      duration: "5h"
      description: "Gradual recovery and system stabilization"
      actions:
        - service: "market-data-simulator"
          action: "price_recovery"
          parameters:
            symbol: "USDT-USD"
            target_price: 1.000
            recovery_hours: 4
        - service: "custodian-simulator"
          action: "resume_normal_settlement"
        - service: "exchange-simulator"
          action: "restore_liquidity"
      
      assertions:
        - type: "price_recovery"
          expect: "usdt_repeg"
          within: "5h"
          parameters:
            symbol: "USDT-USD"
            max_deviation: 0.005
        - type: "system_stabilization"
          expect: "normal_operations"
          within: "4h"
        - type: "performance_recovery"
          expect: "strategy_performance_normalized"
          within: "6h"

  success_criteria:
    - "all_phases_completed"
    - "no_critical_system_failures"  
    - "risk_system_correctly_identified_all_breaches"
    - "system_recovered_within_sla"
  
  reporting:
    generate_timeline: true
    include_performance_impact: true
    correlate_with_audit_logs: true
```

### Scenario Template System
```yaml
# templates/exchange-disruption.template.yaml
apiVersion: chaos.trading/v1
kind: Template
metadata:
  name: "exchange-disruption"
  description: "Template for exchange-related chaos scenarios"
  
parameters:
  - name: "target_exchange"
    type: "string"
    required: true
  - name: "disruption_type"
    type: "enum"
    values: ["latency", "downtime", "order_rejection", "partial_fills"]
    required: true
  - name: "duration"
    type: "duration"
    default: "15m"
  - name: "intensity"
    type: "float"
    default: 0.5
    min: 0.0
    max: 1.0

spec:
  duration: "{{ .Parameters.duration + 10m }}"  # Add recovery time
  
  phases:
    - name: "baseline"
      duration: "5m"
      actions: []
      assertions:
        - type: "exchange_health"
          expect: "healthy"
          service: "{{ .Parameters.target_exchange }}"
    
    - name: "chaos"
      duration: "{{ .Parameters.duration }}"
      actions:
        - service: "{{ .Parameters.target_exchange }}"
          action: "{{ .Parameters.disruption_type }}"
          parameters:
            intensity: "{{ .Parameters.intensity }}"
      
      assertions:
        - type: "trading_impact"
          expect: "degraded_performance"
          within: "2m"
    
    - name: "recovery"
      duration: "5m"
      actions:
        - service: "{{ .Parameters.target_exchange }}"
          action: "clear_chaos"
      
      assertions:
        - type: "performance_recovery"
          expect: "normal_operations"
          within: "3m"
```

## 🎭 Built-in Scenario Library

### Market Scenarios
```go
// Pre-built scenarios available out of the box
var BuiltinScenarios = map[string]ScenarioDefinition{
    "market-crash": {
        Name: "15% Market Crash",
        Description: "Coordinated 15% price drop across all major assets",
        Duration: 30 * time.Minute,
        Category: "market",
    },
    "stablecoin-depeg": {
        Name: "Gradual Stablecoin Depeg", 
        Description: "USDT slowly depegs over 36 hours",
        Duration: 36 * time.Hour,
        Category: "market",
    },
    "volatility-spike": {
        Name: "Extreme Volatility",
        Description: "10x normal volatility for 2 hours",
        Duration: 2 * time.Hour,
        Category: "market",
    },
}

var TradingScenarios = map[string]ScenarioDefinition{
    "strategy-runaway": {
        Name: "Strategy Runaway Trading",
        Description: "Strategy malfunctions and sends massive orders",
        Duration: 10 * time.Minute,
        Category: "trading",
    },
    "risk-system-test": {
        Name: "Risk System Stress Test",
        Description: "Multiple simultaneous risk limit breaches",
        Duration: 20 * time.Minute,
        Category: "risk",
    },
}

var OperationalScenarios = map[string]ScenarioDefinition{
    "custodian-offline": {
        Name: "Custodian Downtime",
        Description: "Custodian unavailable for 4 hours",
        Duration: 4 * time.Hour,
        Category: "operational",
    },
    "settlement-cascade-failure": {
        Name: "Settlement Cascade Failure",
        Description: "Multiple settlement failures creating liquidity crisis",
        Duration: 6 * time.Hour,
        Category: "settlement",
    },
}
```

## 🤖 Chaos API Coordination

### Service API Managers
```go
type ServiceAPIManager interface {
    InjectChaos(action ChaosAction) error
    ClearChaos(chaosID string) error
    GetChaosStatus() (ChaosStatus, error)
    ValidateAction(action ChaosAction) error
}

type ExchangeChaosManager struct {
    client     *http.Client
    baseURL    string
    apiTimeout time.Duration
}

func (e *ExchangeChaosManager) InjectChaos(action ChaosAction) error {
    switch action.Action {
    case "inject_latency":
        return e.injectLatency(action.Parameters)
    case "reject_orders":
        return e.rejectOrders(action.Parameters)
    case "simulate_downtime":
        return e.simulateDowntime(action.Parameters)
    case "manipulate_spreads":
        return e.manipulateSpreads(action.Parameters)
    default:
        return fmt.Errorf("unknown chaos action: %s", action.Action)
    }
}

func (e *ExchangeChaosManager) injectLatency(params map[string]interface{}) error {
    request := LatencyInjectionRequest{
        DelayMS:     params["delay_ms"].(int),
        Operations:  params["operations"].([]string),
        Duration:    params["duration"].(string),
        Accounts:    params["affected_accounts"].([]string),
    }
    
    response, err := e.client.Post(
        e.baseURL+"/chaos/inject-latency",
        "application/json",
        bytes.NewBuffer(marshalJSON(request)),
    )
    
    if err != nil {
        return fmt.Errorf("failed to inject latency: %w", err)
    }
    
    if response.StatusCode != http.StatusOK {
        return fmt.Errorf("latency injection failed with status: %d", response.StatusCode)
    }
    
    return nil
}
```

### Market Data Chaos Coordination
```go
type MarketDataChaosManager struct {
    client  *http.Client
    baseURL string
}

func (m *MarketDataChaosManager) InjectPriceShock(symbol string, shockPct float64, duration time.Duration) error {
    request := PriceShockRequest{
        Symbol:            symbol,
        ShockPercentage:   shockPct,
        DurationSeconds:   int(duration.Seconds()),
        Pattern:           "sudden_drop",
        RecoveryTimeSeconds: int(duration.Seconds() * 2), // 2x duration for recovery
    }
    
    _, err := m.client.Post(
        m.baseURL+"/chaos/price-shock",
        "application/json", 
        bytes.NewBuffer(marshalJSON(request)),
    )
    
    return err
}

func (m *MarketDataChaosManager) InjectStablecoinDepeg(symbol string, deviation float64, hours int) error {
    request := StablecoinDepegRequest{
        Symbol:          symbol,
        TargetDeviation: deviation,
        DurationHours:   hours,
        Pattern:         "gradual_linear",
        VolatilityIncrease: 5.0, // Increase volatility during depeg
    }
    
    _, err := m.client.Post(
        m.baseURL+"/chaos/stablecoin-depeg",
        "application/json",
        bytes.NewBuffer(marshalJSON(request)),
    )
    
    return err
}
```

## ✅ Validation & Assertion Framework

### Assertion Engine
```go
type AssertionEngine struct {
    validators map[string]AssertionValidator
    monitor    *SystemMonitor
    timeout    time.Duration
}

type AssertionValidator interface {
    Validate(ctx context.Context, assertion Assertion) (AssertionResult, error)
}

// Risk Alert Assertion Validator
type RiskAlertValidator struct {
    riskMonitorClient *RiskMonitorClient
}

func (r *RiskAlertValidator) Validate(ctx context.Context, assertion Assertion) (AssertionResult, error) {
    params := assertion.Parameters
    alertType := params["alert_type"].(string)
    
    // Poll risk monitor for expected alert
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return AssertionResult{
                Passed:      false,
                Message:     fmt.Sprintf("Timeout waiting for %s alert", alertType),
                Timestamp:   time.Now(),
                Evidence:    r.getActiveAlerts(),
            }, nil
            
        case <-ticker.C:
            alerts, err := r.riskMonitorClient.GetActiveAlerts()
            if err != nil {
                continue
            }
            
            for _, alert := range alerts {
                if alert.Type == alertType {
                    return AssertionResult{
                        Passed:    true,
                        Message:   fmt.Sprintf("Expected %s alert generated", alertType),
                        Timestamp: time.Now(),
                        Evidence:  alert,
                    }, nil
                }
            }
        }
    }
}

// System Recovery Assertion Validator  
type SystemRecoveryValidator struct {
    services map[string]ServiceHealthChecker
}

func (s *SystemRecoveryValidator) Validate(ctx context.Context, assertion Assertion) (AssertionResult, error) {
    // Check all services are healthy
    healthyServices := 0
    totalServices := len(s.services)
    
    for serviceName, checker := range s.services {
        if checker.IsHealthy() {
            healthyServices++
        } else {
            return AssertionResult{
                Passed:    false,
                Message:   fmt.Sprintf("Service %s not healthy during recovery", serviceName),
                Timestamp: time.Now(),
            }, nil
        }
    }
    
    if healthyServices == totalServices {
        return AssertionResult{
            Passed:    true,
            Message:   "All services recovered successfully",
            Timestamp: time.Now(),
            Evidence: map[string]interface{}{
                "healthy_services": healthyServices,
                "total_services":   totalServices,
            },
        }, nil
    }
    
    return AssertionResult{
        Passed:  false,
        Message: fmt.Sprintf("Only %d/%d services healthy", healthyServices, totalServices),
    }, nil
}
```

### Custom Assertion Types
```yaml
# Custom assertion examples in scenarios
assertions:
  - type: "risk_alert"
    expect: "alert_generated"
    within: "2m"
    parameters:
      alert_type: "position_limit_breach"
      severity: "high"
      
  - type: "trading_performance"
    expect: "degraded_execution"
    within: "5m"
    parameters:
      max_latency_ms: 1000
      min_success_rate: 0.90
      
  - type: "system_recovery"
    expect: "normal_operations"  
    within: "3m"
    parameters:
      required_services: ["exchange", "custodian", "risk-monitor"]
      health_check_passes: 3
      
  - type: "audit_correlation"
    expect: "events_correlated"
    within: "1m"
    parameters:
      correlation_threshold: 0.95
      expected_event_count: 5
```

## 📊 Scenario Execution & Monitoring

### Execution Engine
```go
type ScenarioExecutor struct {
    serviceManagers map[string]ServiceAPIManager
    assertionEngine *AssertionEngine
    logger          *StructuredLogger
    metrics         *MetricsPublisher
}

func (s *ScenarioExecutor) ExecuteScenario(ctx context.Context, scenario *Scenario) (*ExecutionResult, error) {
    executionID := s.generateExecutionID()
    
    s.logger.Info("Starting scenario execution", map[string]interface{}{
        "execution_id":  executionID,
        "scenario_name": scenario.Metadata.Name,
        "duration":      scenario.Spec.Duration,
    })
    
    // Create execution context with timeout
    execCtx, cancel := context.WithTimeout(ctx, scenario.Spec.Timeout)
    defer cancel()
    
    result := &ExecutionResult{
        ExecutionID: executionID,
        Scenario:    scenario,
        StartTime:   time.Now(),
        Status:      ExecutionStatusRunning,
        Phases:      make([]PhaseResult, 0, len(scenario.Spec.Phases)),
    }
    
    // Execute phases sequentially
    for i, phase := range scenario.Spec.Phases {
        s.logger.Info("Starting phase", map[string]interface{}{
            "execution_id": executionID,
            "phase_name":   phase.Name,
            "phase_index":  i,
        })
        
        phaseResult := s.executePhase(execCtx, phase, executionID)
        result.Phases = append(result.Phases, phaseResult)
        
        if !phaseResult.Success {
            s.logger.Error("Phase failed", map[string]interface{}{
                "execution_id": executionID,
                "phase_name":   phase.Name,
                "error":        phaseResult.Error,
            })
            
            if scenario.Spec.Rollback.OnFailure {
                s.executeRollback(execCtx, scenario.Spec.Rollback, executionID)
            }
            
            result.Status = ExecutionStatusFailed
            break
        }
    }
    
    if result.Status == ExecutionStatusRunning {
        result.Status = ExecutionStatusCompleted
    }
    
    result.EndTime = time.Now()
    result.Duration = result.EndTime.Sub(result.StartTime)
    
    s.logger.Info("Scenario execution completed", map[string]interface{}{
        "execution_id": executionID,
        "status":       result.Status,
        "duration":     result.Duration,
    })
    
    return result, nil
}

func (s *ScenarioExecutor) executePhase(ctx context.Context, phase Phase, executionID string) PhaseResult {
    phaseCtx, cancel := context.WithTimeout(ctx, phase.Duration)
    defer cancel()
    
    result := PhaseResult{
        PhaseName: phase.Name,
        StartTime: time.Now(),
        Actions:   make([]ActionResult, 0),
        Assertions: make([]AssertionResult, 0),
    }
    
    // Execute actions
    for _, action := range phase.Actions {
        actionResult := s.executeAction(phaseCtx, action, executionID)
        result.Actions = append(result.Actions, actionResult)
        
        if !actionResult.Success {
            result.Success = false
            result.Error = actionResult.Error
            return result
        }
    }
    
    // Execute parallel actions if any
    if len(phase.ParallelActions) > 0 {
        s.executeParallelActions(phaseCtx, phase.ParallelActions, executionID)
    }
    
    // Validate assertions
    for _, assertion := range phase.Assertions {
        assertionResult := s.validateAssertion(phaseCtx, assertion, executionID)
        result.Assertions = append(result.Assertions, assertionResult)
        
        if !assertionResult.Passed {
            result.Success = false
            result.Error = fmt.Sprintf("Assertion failed: %s", assertionResult.Message)
            return result
        }
    }
    
    result.EndTime = time.Now()
    result.Duration = result.EndTime.Sub(result.StartTime)
    result.Success = true
    
    return result
}
```

### Real-Time Monitoring
```go
type ExecutionMonitor struct {
    activeExecutions sync.Map
    subscribers      map[string]chan ExecutionUpdate
    metrics          *MetricsPublisher
}

func (m *ExecutionMonitor) StartMonitoring(executionID string, scenario *Scenario) {
    monitor := &ScenarioMonitor{
        ExecutionID:    executionID,
        Scenario:       scenario,
        StartTime:      time.Now(),
        SystemMetrics:  make(map[string]interface{}),
        ServiceStatus:  make(map[string]ServiceStatus),
    }
    
    m.activeExecutions.Store(executionID, monitor)
    
    // Start monitoring goroutine
    go m.monitorExecution(monitor)
}

func (m *ExecutionMonitor) monitorExecution(monitor *ScenarioMonitor) {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            // Collect system metrics
            systemState := m.collectSystemState()
            monitor.SystemMetrics = systemState
            
            // Check service health
            for serviceName := range monitor.ServiceStatus {
                status := m.checkServiceHealth(serviceName)
                monitor.ServiceStatus[serviceName] = status
            }
            
            // Publish update
            update := ExecutionUpdate{
                ExecutionID:   monitor.ExecutionID,
                Timestamp:     time.Now(),
                SystemState:   systemState,
                ServiceStatus: monitor.ServiceStatus,
            }
            
            m.publishUpdate(update)
            
        case <-monitor.StopChan:
            return
        }
    }
}
```

## 📊 Monitoring & Observability

### Prometheus Metrics
```
# Scenario execution metrics
test_coordinator_scenarios_executed_total{scenario_name, status="success|failed|timeout"}
test_coordinator_scenario_duration_seconds{scenario_name, phase_name}
test_coordinator_assertion_results_total{assertion_type, result="passed|failed"}

# Chaos injection metrics  
test_coordinator_chaos_actions_total{service, action_type, status="success|failed"}
test_coordinator_chaos_duration_seconds{service, action_type}
test_coordinator_rollback_triggered_total{reason}

# System impact metrics
test_coordinator_system_recovery_time_seconds{scenario_name}
test_coordinator_performance_impact{metric_name, service}
test_coordinator_service_availability{service, during_chaos="true|false"}

# Validation metrics
test_coordinator_assertion_validation_time_seconds{assertion_type}
test_coordinator_expected_behaviors_verified_total{behavior_type}
test_coordinator_scenario_success_rate{scenario_category}
```

### Structured Logging
```json
{
  "timestamp": "2025-09-16T14:23:45.123Z",
  "level": "info",
  "service": "test-coordinator",
  "execution_id": "exec-abc123",
  "event": "phase_started",
  "scenario_name": "stablecoin-depeg-scenario",
  "phase_name": "gradual_depeg",
  "phase_duration": "24h",
  "chaos_actions": [
    {
      "service": "market-data-simulator",
      "action": "stablecoin_depeg",
              "parameters": {
        "symbol": "USDT-USD",
        "target_deviation": -0.05,
        "duration_hours": 24
      }
    }
  ],
  "expected_assertions": ["price_divergence", "arbitrage_opportunity", "risk_alert"],
  "correlation_id": "scenario-depeg-001"
}
```

## 🧪 Testing Framework

### Scenario Validation Testing
```go
type ScenarioValidator struct {
    serviceClients map[string]ServiceClient
    templateEngine *TemplateEngine
}

func (v *ScenarioValidator) ValidateScenario(scenario *Scenario) []ValidationError {
    var errors []ValidationError
    
    // Validate scenario structure
    if structErrors := v.validateStructure(scenario); len(structErrors) > 0 {
        errors = append(errors, structErrors...)
    }
    
    // Validate service availability
    if serviceErrors := v.validateServiceAvailability(scenario); len(serviceErrors) > 0 {
        errors = append(errors, serviceErrors...)
    }
    
    // Validate chaos action parameters
    if actionErrors := v.validateChaosActions(scenario); len(actionErrors) > 0 {
        errors = append(errors, actionErrors...)
    }
    
    // Validate assertion logic
    if assertionErrors := v.validateAssertions(scenario); len(assertionErrors) > 0 {
        errors = append(errors, assertionErrors...)
    }
    
    return errors
}

func (v *ScenarioValidator) validateChaosActions(scenario *Scenario) []ValidationError {
    var errors []ValidationError
    
    for phaseIdx, phase := range scenario.Spec.Phases {
        for actionIdx, action := range phase.Actions {
            // Check if service exists
            if _, exists := v.serviceClients[action.Service]; !exists {
                errors = append(errors, ValidationError{
                    Type:    "unknown_service",
                    Phase:   phase.Name,
                    Message: fmt.Sprintf("Unknown service: %s", action.Service),
                    Location: fmt.Sprintf("phases[%d].actions[%d]", phaseIdx, actionIdx),
                })
                continue
            }
            
            // Validate action is supported by service
            client := v.serviceClients[action.Service]
            if !client.SupportsAction(action.Action) {
                errors = append(errors, ValidationError{
                    Type:    "unsupported_action",
                    Phase:   phase.Name,
                    Message: fmt.Sprintf("Service %s does not support action: %s", action.Service, action.Action),
                    Location: fmt.Sprintf("phases[%d].actions[%d]", phaseIdx, actionIdx),
                })
            }
            
            // Validate action parameters
            if paramErrors := client.ValidateActionParameters(action.Action, action.Parameters); len(paramErrors) > 0 {
                for _, paramError := range paramErrors {
                    errors = append(errors, ValidationError{
                        Type:    "invalid_parameter",
                        Phase:   phase.Name,
                        Message: fmt.Sprintf("Invalid parameter for %s.%s: %s", action.Service, action.Action, paramError),
                        Location: fmt.Sprintf("phases[%d].actions[%d].parameters", phaseIdx, actionIdx),
                    })
                }
            }
        }
    }
    
    return errors
}
```

### Integration Testing
```bash
# Run scenario validation tests
make test-scenario-validation

# Test chaos API coordination
make test-chaos-coordination

# Test assertion engine
make test-assertion-engine

# Full integration test with all services
make test-integration-full
```

### Dry Run Testing
```bash
# Execute scenario in dry-run mode (no actual chaos injection)
./test-coordinator execute --scenario market-crash --dry-run

# Validate scenario timing and dependencies
./test-coordinator validate --file scenarios/complex-scenario.yaml --check-timing

# Test scenario template rendering
./test-coordinator render-template --template exchange-disruption --parameters params.yaml
```

## ⚙️ Configuration

### Environment Variables
```bash
# Core settings
TEST_COORDINATOR_PORT=8084
TEST_COORDINATOR_GRPC_PORT=50056
TEST_COORDINATOR_LOG_LEVEL=info

# Service endpoints
EXCHANGE_SIMULATOR_URL=http://exchange-simulator:8080
CUSTODIAN_SIMULATOR_URL=http://custodian-simulator:8081
MARKET_DATA_SIMULATOR_URL=http://market-data-simulator:8082
TRADING_ENGINE_URL=http://trading-engine:8083
RISK_MONITOR_URL=http://risk-monitor:8080

# Execution settings
DEFAULT_SCENARIO_TIMEOUT=2h
MAX_CONCURRENT_EXECUTIONS=3
ENABLE_ROLLBACK_ON_FAILURE=true
ASSERTION_TIMEOUT=5m

# Reporting
GENERATE_DETAILED_REPORTS=true
REPORT_RETENTION_DAYS=30
ENABLE_REAL_TIME_MONITORING=true
```

### Service Configuration
```yaml
# config.yaml
test_coordinator:
  name: "chaos-orchestrator"
  version: "1.0.0"
  
execution:
  max_concurrent_scenarios: 3
  default_timeout: "2h"
  assertion_timeout: "5m"
  enable_parallel_actions: true
  
services:
  exchange-simulator:
    url: "http://exchange-simulator:8080"
    chaos_api_path: "/chaos"
    health_endpoint: "/health"
    timeout: "30s"
    
  custodian-simulator:
    url: "http://custodian-simulator:8081"
    chaos_api_path: "/chaos"
    health_endpoint: "/health"
    timeout: "30s"
    
  market-data-simulator:
    url: "http://market-data-simulator:8082"
    chaos_api_path: "/chaos"
    health_endpoint: "/health"
    timeout: "30s"
    
  trading-engine:
    url: "http://trading-engine:8083"
    health_endpoint: "/health"
    timeout: "30s"
    
  risk-monitor:
    url: "http://risk-monitor:8080"
    api_path: "/api/v1"
    health_endpoint: "/health"
    timeout: "30s"

scenarios:
  library_path: "/app/scenarios"
  templates_path: "/app/templates"
  custom_scenarios_path: "/data/custom-scenarios"
  
validation:
  strict_mode: true
  validate_service_availability: true
  check_parameter_types: true
  verify_assertion_logic: true
  
reporting:
  output_dir: "/data/reports"
  formats: ["json", "html", "csv"]
  include_timeline: true
  include_metrics: true
  retention_days: 30

rollback:
  enabled: true
  timeout: "10m"
  aggressive_cleanup: false
  notify_on_rollback: true
```

## 📋 CLI Interface

### Command Line Usage
```bash
# Scenario execution commands
./test-coordinator execute --scenario <name>           # Execute built-in scenario
./test-coordinator execute --file <yaml-file>         # Execute custom scenario
./test-coordinator execute --template <template> --params <params-file>

# Scenario management commands  
./test-coordinator list                                # List available scenarios
./test-coordinator list --category market            # List scenarios by category
./test-coordinator validate --file <yaml-file>       # Validate scenario definition
./test-coordinator render-template --template <name> --params <params-file>

# Execution monitoring commands
./test-coordinator status                             # Show active executions
./test-coordinator status --execution-id <id>        # Show specific execution
./test-coordinator stop --execution-id <id>          # Stop running execution
./test-coordinator logs --execution-id <id>          # Show execution logs

# Reporting commands
./test-coordinator report --execution-id <id>        # Generate execution report
./test-coordinator report --execution-id <id> --format html
./test-coordinator timeline --execution-id <id>      # Show execution timeline
./test-coordinator metrics --execution-id <id>       # Show performance metrics

# Service management
./test-coordinator services                           # List configured services
./test-coordinator health-check                       # Check all service health
./test-coordinator clear-chaos --service <name>      # Clear chaos from specific service
./test-coordinator clear-chaos --all                 # Clear all active chaos
```

### Example CLI Workflows
```bash
# Quick market crash test
./test-coordinator execute --scenario market-crash --duration 15m

# Custom exchange disruption using template
./test-coordinator execute \
  --template exchange-disruption \
  --params "target_exchange=exchange-simulator,disruption_type=latency,duration=10m"

# Validate complex scenario before execution
./test-coordinator validate --file scenarios/stablecoin-depeg.yaml --strict

# Monitor long-running scenario
./test-coordinator execute --file scenarios/36h-stress-test.yaml &
EXEC_ID=$(./test-coordinator status --json | jq -r '.executions[0].id')
./test-coordinator logs --execution-id $EXEC_ID --follow

# Generate comprehensive report after execution
./test-coordinator report --execution-id $EXEC_ID --format html --output report.html
```

## 📊 Report Generation

### Execution Report Structure
```go
type ExecutionReport struct {
    Metadata         ReportMetadata          `json:"metadata"`
    Scenario         ScenarioSummary         `json:"scenario"`
    Execution        ExecutionSummary        `json:"execution"`
    SystemImpact     SystemImpactAnalysis    `json:"system_impact"`
    ValidationResults ValidationSummary       `json:"validation_results"`
    Timeline         []TimelineEvent         `json:"timeline"`
    Metrics          MetricsCollection       `json:"metrics"`
    Recommendations  []string               `json:"recommendations"`
}

type SystemImpactAnalysis struct {
    ServicesAffected    []string                    `json:"services_affected"`
    PerformanceImpact   map[string]PerformanceMetric `json:"performance_impact"`
    RecoveryTimes       map[string]time.Duration     `json:"recovery_times"`
    AlertsGenerated     []AlertSummary              `json:"alerts_generated"`
    CircuitBreakersTriggered []CircuitBreakerEvent   `json:"circuit_breakers_triggered"`
}

type ValidationSummary struct {
    TotalAssertions    int                 `json:"total_assertions"`
    PassedAssertions   int                 `json:"passed_assertions"`
    FailedAssertions   int                 `json:"failed_assertions"`
    AssertionDetails   []AssertionResult   `json:"assertion_details"`
    UnexpectedBehaviors []UnexpectedBehavior `json:"unexpected_behaviors"`
}
```

### HTML Report Template
```html
<!-- report_template.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Chaos Scenario Execution Report</title>
    <style>
        .timeline-event { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .passed { color: green; }
        .failed { color: red; }
        .metric-chart { width: 100%; height: 300px; }
    </style>
</head>
<body>
    <h1>Scenario Execution Report: {{.Scenario.Name}}</h1>
    
    <section class="summary">
        <h2>Executive Summary</h2>
        <p><strong>Status:</strong> <span class="{{.Execution.Status}}">{{.Execution.Status}}</span></p>
        <p><strong>Duration:</strong> {{.Execution.Duration}}</p>
        <p><strong>Assertions Passed:</strong> {{.ValidationResults.PassedAssertions}}/{{.ValidationResults.TotalAssertions}}</p>
    </section>
    
    <section class="timeline">
        <h2>Execution Timeline</h2>
        {{range .Timeline}}
        <div class="timeline-event">
            <strong>{{.Timestamp.Format "15:04:05"}}</strong> - {{.Event}} 
            {{if .ChaosAction}}({{.ChaosAction.Service}}.{{.ChaosAction.Action}}){{end}}
        </div>
        {{end}}
    </section>
    
    <section class="system-impact">
        <h2>System Impact Analysis</h2>
        <h3>Performance Impact</h3>
        {{range $service, $impact := .SystemImpact.PerformanceImpact}}
        <p><strong>{{$service}}:</strong> Latency +{{$impact.LatencyIncrease}}ms, Throughput {{$impact.ThroughputChange}}%</p>
        {{end}}
        
        <h3>Recovery Times</h3>
        {{range $service, $time := .SystemImpact.RecoveryTimes}}
        <p><strong>{{$service}}:</strong> {{$time}}</p>
        {{end}}
    </section>
    
    <section class="validation-results">
        <h2>Validation Results</h2>
        {{range .ValidationResults.AssertionDetails}}
        <div class="assertion {{if .Passed}}passed{{else}}failed{{end}}">
            <strong>{{.Type}}:</strong> {{.Message}}
            {{if .Evidence}}<pre>{{.Evidence}}</pre>{{end}}
        </div>
        {{end}}
    </section>
    
    <section class="recommendations">
        <h2>Recommendations</h2>
        <ul>
        {{range .Recommendations}}
            <li>{{.}}</li>
        {{end}}
        </ul>
    </section>
</body>
</html>
```

## 🐳 Docker Configuration

### Dockerfile
```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o test-coordinator cmd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates tzdata curl
WORKDIR /root/

COPY --from=builder /app/test-coordinator .
COPY --from=builder /app/scenarios ./scenarios
COPY --from=builder /app/templates ./templates
COPY --from=builder /app/config ./config

EXPOSE 8084 50056
CMD ["./test-coordinator", "--config=config/config.yaml"]
```

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8084/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Docker Compose Integration
```yaml
# docker-compose.yaml
version: '3.8'
services:
  test-coordinator:
    build: .
    ports:
      - "8084:8084"
      - "50056:50056"
    environment:
      - TEST_COORDINATOR_LOG_LEVEL=info
      - EXCHANGE_SIMULATOR_URL=http://exchange-simulator:8080
      - CUSTODIAN_SIMULATOR_URL=http://custodian-simulator:8081
      - MARKET_DATA_SIMULATOR_URL=http://market-data-simulator:8082
    volumes:
      - ./scenarios:/app/custom-scenarios
      - ./reports:/data/reports
    depends_on:
      - exchange-simulator
      - custodian-simulator
      - market-data-simulator
      - trading-engine
      - risk-monitor
    networks:
      - trading-network
```

## 🚀 Performance

### Benchmarks
- **Scenario Execution**: Support for 3+ concurrent long-running scenarios
- **API Coordination**: <100ms latency for chaos action coordination
- **Assertion Validation**: <5s validation time for complex assertions
- **Report Generation**: <10s for comprehensive HTML reports

### Resource Usage
- **Memory**: ~150MB baseline + ~50MB per active scenario execution
- **CPU**: <25% single core during scenario execution
- **Network**: <1MB/hour service coordination traffic
- **Disk**: <100MB scenario definitions and reports

## 🤝 Contributing

### Adding New Scenario Types
1. Create scenario YAML definition following schema
2. Add corresponding assertion validators if needed
3. Test scenario with dry-run mode
4. Document expected system behavior and validation criteria
5. Add to built-in scenario library if generally useful

### Creating Custom Assertion Validators
1. Implement the `AssertionValidator` interface
2. Register validator with assertion engine
3. Add unit tests for validator logic
4. Document assertion parameters and expected behavior

### Service Integration
1. Implement `ServiceAPIManager` interface for new services
2. Add chaos API endpoints to target service
3. Create integration tests for service coordination
4. Update configuration templates and documentation

## 📚 References

- **Chaos Engineering Principles**: [Link to chaos engineering best practices]
- **Scenario Definition Schema**: [Link to YAML schema documentation]  
- **Service API Specifications**: [Link to chaos API documentation]
- **Assertion Framework Guide**: [Link to assertion development guide]

---

**Status**: 🚧 Development Phase  
**Maintainer**: [Your team]  
**Last Updated**: September 2025
