# Noopur API Contract - CreatorCore Backend

**Version**: 1.0.0  
**Target**: Noopur (Creator Backend Developer)  
**Integration Point**: Core Integrator → CreatorCore Backend

## Required Endpoints

### 1. POST /generate
**Purpose**: Generate creative content  
**Called by**: BridgeClient.generate()

**Request Format**:
```json
{
  "prompt": "string (required)",
  "topic": "string (optional)",
  "goal": "string (optional)", 
  "type": "string (optional, default: story)"
}
```

**Response Format**:
```json
{
  "generation_id": "string (REQUIRED - used for feedback mapping)",
  "generated_text": "string (required)",
  "related_context": ["array of context objects (optional)"],
  "metadata": {
    "model": "string",
    "timestamp": "ISO 8601 string"
  }
}
```

**Error Response**:
```json
{
  "error": "string",
  "error_code": "GENERATION_FAILED|INVALID_INPUT|RATE_LIMITED",
  "details": "string (optional)"
}
```

### 2. POST /feedback
**Purpose**: Accept feedback for generated content  
**Called by**: BridgeClient.feedback()

**Request Format** (Canonical Schema):
```json
{
  "generation_id": "string (required)",
  "command": "string (required: +2|+1|-1|-2)",
  "user_id": "string (optional)",
  "timestamp": "ISO 8601 string (optional)"
}
```

**Response Format**:
```json
{
  "status": "success|error",
  "message": "string",
  "feedback_recorded": true
}
```

### 3. GET /history
**Purpose**: Retrieve generation history  
**Called by**: BridgeClient.history()

**Query Parameters**:
- `topic` (optional): Filter by topic
- `limit` (optional): Max results (default: 10)

**Response Format**:
```json
[
  {
    "generation_id": "string",
    "prompt": "string",
    "generated_text": "string",
    "timestamp": "ISO 8601 string",
    "feedback_score": "number (optional)"
  }
]
```

### 4. GET /system/health
**Purpose**: Health check endpoint  
**Called by**: Gateway health monitoring

**Response Format**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO 8601 string",
  "components": {
    "database": "healthy|unhealthy",
    "ai_model": "healthy|unhealthy"
  }
}
```

## Authentication & Headers

**Required Headers**:
```
Content-Type: application/json
Authorization: Bearer <API_KEY> (if authentication enabled)
```

**Optional Headers**:
```
X-Request-ID: <unique_request_id>
X-User-Agent: Core-Integrator/1.0.0
```

## Error Handling

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (invalid API key)
- `429`: Rate Limited
- `500`: Internal Server Error
- `503`: Service Unavailable

**Error Response Format**:
```json
{
  "error": "Human readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": "Additional context (optional)",
  "timestamp": "ISO 8601 string"
}
```

## Rate Limiting

**Limits**:
- `/generate`: 100 requests/minute per API key
- `/feedback`: 1000 requests/minute per API key
- `/history`: 200 requests/minute per API key

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Configuration Requirements

**Environment Variables**:
```bash
CREATORCORE_PORT=5001
CREATORCORE_API_KEY=your_secret_key
CREATORCORE_DB_PATH=./creatorcore.db
CREATORCORE_MODEL_PATH=./models/
```

## Testing Endpoints

**Test Data**:
```bash
# Test generation
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a short story about robots"}'

# Test feedback
curl -X POST http://localhost:5001/feedback \
  -H "Content-Type: application/json" \
  -d '{"generation_id": "gen_123", "command": "+1"}'

# Test health
curl http://localhost:5001/system/health
```

## Integration Checklist

- [ ] All endpoints return correct HTTP status codes
- [ ] `generation_id` is always included in `/generate` responses
- [ ] Feedback endpoint accepts canonical schema format
- [ ] Health endpoint returns structured status
- [ ] Error responses follow standard format
- [ ] Rate limiting headers are included
- [ ] Authentication works (if enabled)
- [ ] Database persistence is working
- [ ] AI model is loaded and responding

## Support

**Contact**: Noopur (Creator Backend Developer)  
**Documentation**: This file  
**Testing**: Use `tests/test_noopur_integration.py`