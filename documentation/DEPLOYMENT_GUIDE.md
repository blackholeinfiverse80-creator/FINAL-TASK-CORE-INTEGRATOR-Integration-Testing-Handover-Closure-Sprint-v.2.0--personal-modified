# Deployment Guide - Core Integrator

**Version**: 1.0.0  
**Target**: All Team Members (Ashmit, Noopur, Sankalp)

## Quick Deployment

### 1. Core Integrator (Ashmit)
```bash
# Clone and setup
git clone https://github.com/blackholeinfiverse80-creator/FINAL-INTEGRATION-ROLE-COMPLETION-TASK.git
cd FINAL-INTEGRATION-ROLE-COMPLETION-TASK
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start server
python main.py
# Server runs on http://localhost:8001
```

### 2. CreatorCore Backend (Noopur)
```bash
# Start your CreatorCore service on port 5001
# Ensure it implements the API contract in NOOPUR_API_CONTRACT.md

# Test connectivity
curl http://localhost:5001/system/health
```

### 3. InsightFlow (Sankalp)
```bash
# Configure ingestion endpoint (provide to Ashmit)
# Review event samples in reports/insightflow_event_samples.json
# Implement ingestion according to INSIGHTFLOW_INTEGRATION.md
```

## Environment Configuration

### Core Integrator (.env)
```bash
# Security
SSPL_ENABLED=true
SSPL_ALLOW_DRIFT_SECONDS=300

# Database
USE_MONGODB=true
MONGODB_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE_NAME=core_integrator

# External Services
INTEGRATOR_USE_NOOPUR=true
NOOPUR_BASE_URL=http://localhost:5001
NOOPUR_API_KEY=your_api_key

# Logging
LOG_LEVEL=INFO
```

### CreatorCore Backend (Noopur)
```bash
CREATORCORE_PORT=5001
CREATORCORE_API_KEY=your_secret_key
CREATORCORE_DB_PATH=./creatorcore.db
CREATORCORE_MODEL_PATH=./models/
```

### InsightFlow (Sankalp)
```bash
INSIGHTFLOW_INGESTION_URL=https://your-endpoint.com/api/v1/events
INSIGHTFLOW_API_KEY=your_api_key
INSIGHTFLOW_BATCH_SIZE=100
```

## Service Dependencies

### Required Services
1. **Core Integrator**: Port 8001 (main service)
2. **CreatorCore Backend**: Port 5001 (Noopur's service)
3. **MongoDB Atlas**: Cloud database (optional, SQLite fallback)
4. **InsightFlow**: Telemetry ingestion (Sankalp's service)

### Service Startup Order
1. MongoDB Atlas (if used)
2. CreatorCore Backend (Noopur)
3. Core Integrator (Ashmit)
4. InsightFlow ingestion (Sankalp)

## Health Checks

### Core Integrator Health
```bash
curl http://localhost:8001/system/health
# Expected: {"status": "healthy", "components": {...}}
```

### CreatorCore Health
```bash
curl http://localhost:5001/system/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

### Integration Health
```bash
curl http://localhost:8001/system/diagnostics
# Expected: {"integration_ready": true, "integration_score": 1.0}
```

## Testing Integration

### 1. End-to-End Test
```bash
# Test generation flow
curl -X POST http://localhost:8001/core \
  -H "Content-Type: application/json" \
  -d '{
    "module": "creator",
    "intent": "generate", 
    "user_id": "test_user",
    "data": {"prompt": "Write a short story"}
  }'
```

### 2. Feedback Flow Test
```bash
# Test feedback (use generation_id from above)
curl -X POST http://localhost:8001/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "generation_id": "gen_123",
    "command": "+1",
    "user_id": "test_user"
  }'
```

### 3. Telemetry Test
```bash
# Generate telemetry events
curl http://localhost:8001/system/health
curl http://localhost:8001/system/diagnostics
# Check InsightFlow ingestion logs
```

## Security Setup (SSPL Phase III)

### 1. Generate Test Keys
```python
from nacl.signing import SigningKey
import base64

# Generate keypair
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

print("Private Key:", base64.b64encode(bytes(signing_key)).decode())
print("Public Key:", base64.b64encode(bytes(verify_key)).decode())
```

### 2. Test Signed Request
```bash
# Use security_client.py for testing
python security_client.py
```

## Troubleshooting

### Common Issues

**1. Core Integrator won't start**
```bash
# Check dependencies
pip install -r requirements.txt

# Check environment
cat .env

# Check logs
tail -f logs/bridge/*.log
```

**2. CreatorCore connection failed**
```bash
# Check if service is running
curl http://localhost:5001/system/health

# Check configuration
echo $NOOPUR_BASE_URL
```

**3. MongoDB connection failed**
```bash
# Check connection string
echo $MONGODB_CONNECTION_STRING

# Test connection
python -c "from pymongo import MongoClient; print(MongoClient('your_connection_string').admin.command('ping'))"
```

**4. InsightFlow events not appearing**
```bash
# Check event generation
curl http://localhost:8001/system/health | jq .insightflow_event

# Check ingestion endpoint
curl -X POST $INSIGHTFLOW_INGESTION_URL \
  -H "Authorization: Bearer $INSIGHTFLOW_API_KEY" \
  -d '{"test": "event"}'
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py

# Run with verbose output
python main.py --log-level DEBUG
```

## Production Deployment

### 1. Docker Deployment
```bash
# Build image
docker build -t core-integrator .

# Run container
docker run -p 8001:8001 --env-file .env core-integrator
```

### 2. Docker Compose
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Environment Variables
```bash
# Production settings
SSPL_ENABLED=true
USE_MONGODB=true
INTEGRATOR_USE_NOOPUR=true
LOG_LEVEL=INFO
```

## Monitoring

### Key Endpoints
- Health: `GET /system/health`
- Diagnostics: `GET /system/diagnostics`
- Logs: `GET /system/logs/latest`

### Metrics to Monitor
- Response time < 200ms
- Integration score > 0.8
- Error rate < 1%
- Uptime > 99.9%

## Support Contacts

- **Ashmit**: Core Integrator deployment and configuration
- **Noopur**: CreatorCore backend API implementation
- **Sankalp**: InsightFlow telemetry ingestion and monitoring

## Deployment Checklist

### Pre-deployment
- [ ] All environment variables configured
- [ ] Dependencies installed
- [ ] Database connections tested
- [ ] API contracts validated
- [ ] Security keys generated (if SSPL enabled)

### Deployment
- [ ] Core Integrator started successfully
- [ ] CreatorCore backend accessible
- [ ] Health checks passing
- [ ] Integration tests passing
- [ ] Telemetry events generating

### Post-deployment
- [ ] End-to-end flow tested
- [ ] Monitoring dashboard configured
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team handover completed