from fastapi import FastAPI, HTTPException, Depends
from typing import List, Dict, Any, Optional
import os
import sqlite3
from pathlib import Path
from src.core.models import CoreRequest, CoreResponse
from src.core.feedback_models import FeedbackRequest
from src.core.gateway import Gateway
from src.db.memory import ContextMemory
from config.config import DB_PATH

# Optional SSPL - can be disabled for testing
SSPL_ENABLED = os.getenv("SSPL_ENABLED", "false").lower() in ("true", "1", "yes")

if SSPL_ENABLED:
    from src.utils.sspl_dependency import require_sspl
else:
    async def require_sspl():
        return True

app = FastAPI(
    title="Unified Backend Bridge",
    description="Central orchestration layer for Finance, Education, and Creator agents",
    version="1.0.0"
)

# Initialize gateway and memory
gateway = Gateway()
memory = ContextMemory(DB_PATH)

@app.post("/core", response_model=CoreResponse)
async def core_endpoint(request: CoreRequest, _sspl=Depends(require_sspl)) -> CoreResponse:
    """Main gateway endpoint for processing agent requests"""
    try:
        response = gateway.process_request(
            module=request.module,
            intent=request.intent, 
            user_id=request.user_id,
            data=request.data
        )
        # Validate response structure before creating CoreResponse
        if not isinstance(response, dict) or 'status' not in response:
            raise HTTPException(status_code=500, detail="Invalid agent response format")
        
        # Ensure required fields exist
        response.setdefault('message', 'No message provided')
        response.setdefault('result', {})
        
        return CoreResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Response validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-history")
async def get_history(user_id: str) -> List[Dict[str, Any]]:
    """Get full interaction history for a user"""
    try:
        history = memory.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-context") 
async def get_context(user_id: str) -> List[Dict[str, Any]]:
    """Get recent context (last 3 interactions) for a user"""
    try:
        context = memory.get_context(user_id)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Unified Backend Bridge API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/system/health")
async def system_health():
    """System health check with MongoDB and Noopur connectivity"""
    components = {}
    
    # SQLite database check
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("SELECT 1").fetchone()
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
    
    # MongoDB check (if enabled)
    from config.config import USE_MONGODB
    if USE_MONGODB:
        try:
            from src.db.mongodb_adapter import MongoDBAdapter
            from config.config import MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME
            mongo_adapter = MongoDBAdapter(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)
            # Simple ping test
            mongo_adapter.client.admin.command('ping')
            components["mongodb"] = "healthy"
        except Exception as e:
            components["mongodb"] = f"unhealthy: {str(e)}"
    
    # Noopur reachability check (if enabled)
    from config.config import INTEGRATOR_USE_NOOPUR, NOOPUR_BASE_URL
    if INTEGRATOR_USE_NOOPUR:
        try:
            from src.utils.noopur_client import NoopurClient
            noopur_client = NoopurClient(NOOPUR_BASE_URL)
            # Simple connectivity test
            result = noopur_client.session.get(f"{NOOPUR_BASE_URL}/health", timeout=3)
            if result.status_code == 200:
                components["noopur"] = "healthy"
            else:
                components["noopur"] = f"unhealthy: HTTP {result.status_code}"
        except Exception as e:
            components["noopur"] = f"unreachable: {str(e)}"
    
    components["gateway"] = "healthy"
    components["modules"] = len(gateway.agents)
    
    # Overall status
    unhealthy_components = [k for k, v in components.items() if "unhealthy" in str(v) or "unreachable" in str(v)]
    overall_status = "degraded" if unhealthy_components else "healthy"
    
    return {
        "status": overall_status,
        "components": components,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
    }

@app.get("/system/diagnostics")
async def system_diagnostics():
    """System diagnostics with module load status and integration readiness"""
    # Module load status
    module_load_status = {}
    for name, agent in gateway.agents.items():
        if agent is None:
            module_load_status[name] = "invalid"
        else:
            module_load_status[name] = "valid"
    
    # Get memory stats
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM interactions")
            total_interactions = cursor.fetchone()[0]
            cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM interactions")
            unique_users = cursor.fetchone()[0]
        db_healthy = True
    except Exception:
        total_interactions = 0
        unique_users = 0
        db_healthy = False
    
    # Check security components
    nonce_db_exists = os.path.exists("data/nonce_store.db")
    
    # Compute integration_ready status
    integration_checks = {
        "core_modules_loaded": all(status == "valid" for status in module_load_status.values()),
        "database_accessible": db_healthy,
        "gateway_initialized": gateway is not None,
        "memory_adapter_ready": gateway.memory is not None
    }
    
    # Additional integration checks
    from config.config import USE_MONGODB, INTEGRATOR_USE_NOOPUR
    
    if USE_MONGODB:
        try:
            from src.db.mongodb_adapter import MongoDBAdapter
            from config.config import MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME
            mongo_adapter = MongoDBAdapter(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)
            mongo_adapter.client.admin.command('ping')
            integration_checks["mongodb_ready"] = True
        except Exception:
            integration_checks["mongodb_ready"] = False
    
    if INTEGRATOR_USE_NOOPUR:
        try:
            from src.utils.noopur_client import NoopurClient
            from config.config import NOOPUR_BASE_URL
            noopur_client = NoopurClient(NOOPUR_BASE_URL)
            result = noopur_client.session.get(f"{NOOPUR_BASE_URL}/health", timeout=2)
            integration_checks["noopur_ready"] = result.status_code == 200
        except Exception:
            integration_checks["noopur_ready"] = False
    
    # Compute overall integration readiness and detailed reasons
    integration_ready = all(integration_checks.values())

    failing_components = [k for k, v in integration_checks.items() if not v]

    # integration score: proportion of passing checks (0.0 - 1.0)
    total_checks = len(integration_checks) if integration_checks else 0
    passing = sum(1 for v in integration_checks.values() if v)
    integration_score = round((passing / total_checks) if total_checks else 0.0, 3)

    readiness_reason = "all_checks_passed" if integration_ready else ";".join(failing_components) if failing_components else "unknown"

    return {
        "module_load_status": module_load_status,
        "integration_ready": integration_ready,
        "integration_checks": integration_checks,
        "integration_score": integration_score,
        "readiness_reason": readiness_reason,
        "failing_components": failing_components,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        "signature": None,
        "modules": {name: type(agent).__name__ for name, agent in gateway.agents.items() if agent is not None},
        "memory": {
            "total_interactions": total_interactions,
            "unique_users": unique_users,
            "db_path": DB_PATH,
            "adapter_type": type(gateway.memory).__name__
        },
        "security": {
            "nonce_store_enabled": nonce_db_exists,
            "sspl_middleware": SSPL_ENABLED
        },
        "version": "1.0.0"
    }

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest, _sspl=Depends(require_sspl)):
    """Submit feedback for generated content"""
    try:
        response = gateway.process_request(
            module="creator",
            intent="feedback",
            user_id=request.user_id or "anonymous",
            data=request.dict()
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/creator/history")
async def get_creator_history(user_id: str = "all"):
    """Get creator generation history"""
    try:
        response = gateway.process_request(
            module="creator",
            intent="history",
            user_id=user_id if user_id != "all" else None,
            data={}
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/logs/latest")
async def system_logs_latest(limit: int = 50):
    """Get latest log entries"""
    log_dir = Path("logs/bridge")
    if not log_dir.exists():
        return {"logs": [], "message": "No logs available"}
    
    log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not log_files:
        return {"logs": [], "message": "No log files found"}
    
    latest_log = log_files[0]
    try:
        with open(latest_log, 'r') as f:
            lines = f.readlines()[-limit:]
        return {
            "log_file": str(latest_log),
            "entries": [line.strip() for line in lines],
            "count": len(lines)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)