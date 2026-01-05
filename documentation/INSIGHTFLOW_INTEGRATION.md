# InsightFlow Integration Guide

**Version**: 1.0.0  
**Target**: Sankalp (InsightFlow/Telemetry Layer)  
**Integration Point**: Core Integrator → InsightFlow Telemetry System

## Overview

Core Integrator generates structured telemetry events for InsightFlow ingestion. Events are emitted from health and diagnostics endpoints with standardized schema.

## Event Schema

### Base Event Structure
```json
{
  "insightflow_version": "1.0.0",
  "event_type": "string",
  "component": "string", 
  "status": "string",
  "details": {},
  "timestamp": "ISO 8601 string"
}
```

### Event Types

#### 1. Heartbeat Events
**Purpose**: Regular health signals  
**Frequency**: Every health check call  
**Event Type**: `heartbeat`

```json
{
  "insightflow_version": "1.0.0",
  "event_type": "heartbeat",
  "component": "core_integrator",
  "status": "healthy|degraded",
  "details": {
    "database": "healthy|unhealthy",
    "mongodb": "healthy|unhealthy", 
    "external_service": "healthy|unhealthy",
    "gateway": "healthy",
    "modules": 3
  },
  "timestamp": "2025-12-30T12:00:00Z"
}
```

#### 2. Integration Ready Events
**Purpose**: System readiness signals  
**Frequency**: Every diagnostics call when ready  
**Event Type**: `integration_ready`

```json
{
  "insightflow_version": "1.0.0",
  "event_type": "integration_ready",
  "component": "core_integrator",
  "status": "healthy",
  "details": {
    "integration_checks": {
      "core_modules_loaded": true,
      "database_accessible": true,
      "gateway_initialized": true,
      "memory_adapter_ready": true,
      "mongodb_ready": true,
      "external_service_ready": true
    },
    "module_load_status": {
      "finance": "valid",
      "education": "valid", 
      "creator": "valid"
    },
    "readiness_reason": "all_checks_passed"
  },
  "integration_score": 1.0,
  "timestamp": "2025-12-30T12:00:00Z"
}
```

#### 3. Degraded Alert Events
**Purpose**: System degradation alerts  
**Frequency**: Every diagnostics call when degraded  
**Event Type**: `degraded_alert`

```json
{
  "insightflow_version": "1.0.0",
  "event_type": "degraded_alert",
  "component": "core_integrator",
  "status": "degraded",
  "details": {
    "integration_checks": {
      "core_modules_loaded": true,
      "database_accessible": true,
      "gateway_initialized": true,
      "memory_adapter_ready": true,
      "mongodb_ready": false,
      "external_service_ready": false
    },
    "readiness_reason": "mongodb_ready;external_service_ready"
  },
  "integration_score": 0.67,
  "failing_components": ["mongodb_ready", "external_service_ready"],
  "timestamp": "2025-12-30T12:00:00Z"
}
```

## Field Mappings

### Required Fields
- `insightflow_version`: Always "1.0.0"
- `event_type`: One of: `heartbeat`, `integration_ready`, `degraded_alert`
- `component`: Always "core_integrator"
- `status`: One of: `healthy`, `degraded`, `unhealthy`
- `timestamp`: ISO 8601 UTC timestamp

### Optional Fields
- `details`: Object with event-specific data
- `integration_score`: Float 0.0-1.0 (proportion of passing checks)
- `failing_components`: Array of failed component names

### Status Mapping
- `healthy`: All systems operational
- `degraded`: Some systems failing but core functionality works
- `unhealthy`: Critical systems failing

## Event Sources

### 1. Health Endpoint
**URL**: `GET /system/health`  
**Events**: `heartbeat`  
**Trigger**: Every health check call

### 2. Diagnostics Endpoint  
**URL**: `GET /system/diagnostics`  
**Events**: `integration_ready`, `degraded_alert`  
**Trigger**: Every diagnostics call

## Integration Requirements

### 1. Event Ingestion
**Expected Ingestion Method**: HTTP POST to InsightFlow endpoint

**Payload Format**:
```json
{
  "events": [
    {
      "insightflow_version": "1.0.0",
      "event_type": "heartbeat",
      "component": "core_integrator",
      "status": "healthy",
      "details": {...},
      "timestamp": "2025-12-30T12:00:00Z"
    }
  ]
}
```

### 2. Ingestion Endpoint Specification
**Required from InsightFlow Team**:
- Ingestion endpoint URL
- Authentication method (API key, OAuth, etc.)
- Rate limits
- Batch size limits
- Retry policy requirements

### 3. Field Processing
**Integration Score**: 
- Type: Float
- Range: 0.0 (all failing) to 1.0 (all passing)
- Calculation: `passing_checks / total_checks`

**Failing Components**:
- Type: Array of strings
- Contains: Names of failed integration checks
- Empty when all checks pass

## Sample Events

See `/reports/insightflow_event_samples.json` for complete examples.

## Testing

### 1. Generate Test Events
```bash
# Generate heartbeat event
curl http://localhost:8001/system/health

# Generate integration_ready event  
curl http://localhost:8001/system/diagnostics
```

### 2. Event Validation
```python
# Validate event schema
import json
from src.utils.insightflow import make_event

event = make_event("heartbeat", "core_integrator", "healthy")
assert "insightflow_version" in event
assert event["event_type"] == "heartbeat"
```

### 3. Integration Testing
```bash
# Run InsightFlow integration tests
python -m pytest tests/test_insightflow.py -v
```

## Monitoring Dashboard Requirements

### Key Metrics to Track
1. **System Health**: Percentage of healthy heartbeats
2. **Integration Score**: Average integration score over time
3. **Component Failures**: Count of failing components by type
4. **Event Frequency**: Events per minute/hour
5. **Degradation Alerts**: Count and duration of degraded states

### Recommended Alerts
1. **Critical**: Integration score < 0.5 for > 5 minutes
2. **Warning**: Integration score < 0.8 for > 10 minutes  
3. **Info**: New component failures detected

## Configuration

### Core Integrator Side
```bash
# Enable telemetry generation (always on)
INSIGHTFLOW_ENABLED=true
```

### InsightFlow Side (Required from Sankalp)
```bash
# Ingestion endpoint
INSIGHTFLOW_INGESTION_URL=https://insightflow.example.com/api/v1/events
INSIGHTFLOW_API_KEY=your_api_key
INSIGHTFLOW_BATCH_SIZE=100
INSIGHTFLOW_TIMEOUT=30
```

## Deployment Checklist

- [ ] Event schema validation working
- [ ] All three event types generating correctly
- [ ] Integration score calculation accurate
- [ ] Failing components array populated correctly
- [ ] Timestamps in UTC ISO 8601 format
- [ ] InsightFlow ingestion endpoint configured
- [ ] Authentication working
- [ ] Rate limiting respected
- [ ] Error handling for ingestion failures
- [ ] Monitoring dashboard configured

## Support

**Contact**: Sankalp (InsightFlow/Telemetry Layer)  
**Sample Events**: `/reports/insightflow_event_samples.json`  
**Generator Code**: `src/utils/insightflow.py`  
**Tests**: `tests/test_insightflow.py`