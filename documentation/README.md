# Core Integrator Sprint 1.1 - Unified Backend Bridge

## Overview
FastAPI-based orchestration platform with SSPL Phase III security, multi-database support, and resilient HTTP communication.

## Features
- **SSPL Phase III Security**: Ed25519 signatures, nonce replay protection, timestamp validation
- **Multi-Database Support**: MongoDB Atlas (primary), SQLite (fallback), Noopur integration
- **Agent System**: Finance, Education, Creator modules with memory management
- **HTTP Communication**: Direct HTTP calls with timeout handling and error management
- **Observability**: Health checks, diagnostics, logging endpoints
- **InsightFlow Telemetry**: Structured event generator with heartbeats, degraded alerts, and integration_ready signals
- **BridgeClient (Canonical)**: `BridgeClient` v1.0.0 is the single, versioned integration surface for CreatorCore. All gateway flows use it for external service communication.
- **Deterministic Feedback Mapping**: Generation lifecycle mapping (generation_id → interaction) persisted in memory for guaranteed feedback retrieval and replay.
- **Testing Suite**: Security validation, database testing, comprehensive coverage

## Quick Start

1. **Clone & Setup**
   ```bash
   git clone <repository-url>
   cd Core-Integrator-Sprint-1.1-
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Run Server**
   ```bash
   python main.py
   ```

3. **Run CI-Safe Tests**
   ```bash
   python -m pytest tests/test_ci_safe.py -v
   ```

## Configuration

### Security Settings
- `SSPL_ENABLED=true` - Enable/disable security
- `SSPL_ALLOW_DRIFT_SECONDS=300` - Timestamp tolerance

### Database Settings
- `USE_MONGODB=true` - Use MongoDB Atlas
- `MONGODB_CONNECTION_STRING` - Atlas connection string
- `MONGODB_DATABASE_NAME=core_integrator` - Database name

## Testing

### CI-Safe Test Suite
- `tests/test_ci_safe.py` - Complete test suite with mocked dependencies
- `tests/test_feedback_schema_validation.py` - Feedback schema validation tests
- `tests/test_noopur_integration.py` - Noopur client integration tests

### Test Scenarios
1. **CI Pipeline**: Run `pytest tests/test_ci_safe.py` (no external services)
2. **Local Development**: Full test suite with optional external services
3. **Integration Testing**: Health and diagnostics endpoint validation

## API Endpoints

### Core Endpoints
- `POST /core` - Main processing endpoint (requires SSPL headers when enabled)
- `GET /get-context?user_id=USER` - Retrieve user context
- `GET /system/health` - System health check
- `GET /system/diagnostics` - System diagnostics
- `GET /system/logs/latest` - Recent logs

### Available Modules
- `finance` - Financial reports and analysis
- `education` - Educational content generation
- `creator` - Creative content with external service integration

### Feedback System
- `POST /feedback` - Submit feedback with canonical schema validation
- Supported commands: `+2` (excellent), `+1` (good), `-1` (poor), `-2` (terrible)
- Automatic forwarding to external services when available

## Security Headers (SSPL Phase III)
When security is enabled, all requests to `/core` require:
- `X-SSPL-Timestamp` - Unix timestamp
- `X-SSPL-Nonce` - Unique request identifier
- `X-SSPL-Signature` - Ed25519 signature (base64)
- `X-SSPL-Public-Key` - Ed25519 public key (base64)

## Database Priority
1. **MongoDB Atlas** (if configured and available)
2. **Noopur** (if enabled and available)
3. **SQLite** (fallback, always available)

## Files Structure
- `main.py` - FastAPI application
- `src/core/gateway.py` - Central routing and processing
- `src/db/memory.py` - SQLite memory adapter
- `src/db/mongodb_adapter.py` - MongoDB Atlas adapter
- `src/utils/noopur_client.py` - Noopur service integration
- `src/utils/sspl.py` - Security validation
- `src/utils/bridge_client.py` - CreatorCore HTTP client (canonical integration surface)
- `src/utils/insightflow.py` - Telemetry event generator
- `src/utils/resilient_client.py` - HTTP client with circuit breaker (available but not used in main flow)
- `security_client.py` - Security testing client

## Team Integration Guides
- `documentation/DEPLOYMENT_GUIDE.md` - Complete deployment instructions for all teams
- `documentation/NOOPUR_API_CONTRACT.md` - API specification for CreatorCore backend (Noopur)
- `documentation/INSIGHTFLOW_INTEGRATION.md` - Telemetry integration guide (Sankalp)
- `documentation/BRIDGE_CLIENT.md` - BridgeClient contract and usage (Ashmit)

## Production Ready
- ✅ CI-safe test suite (11/11 tests passing)
- ✅ Canonical feedback schema with validation
- ✅ Deterministic health monitoring
- ✅ Multi-database fallback (MongoDB → SQLite)
- ✅ BridgeClient canonical integration surface
- ✅ Active InsightFlow telemetry integration
- ✅ Comprehensive error handling and logging

## Monitoring & Observability
- **Health Endpoint**: `/system/health` - Component status with external service checks
- **Diagnostics Endpoint**: `/system/diagnostics` - Integration readiness and module status
- **Structured Logging**: JSON format with InsightFlow telemetry events
- **Integration Ready Signal**: Computed boolean from all system dependencies