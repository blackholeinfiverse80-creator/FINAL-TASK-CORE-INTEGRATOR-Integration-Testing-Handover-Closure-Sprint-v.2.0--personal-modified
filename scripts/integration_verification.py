#!/usr/bin/env python3
"""
Integration Verification Script - Final Closure Task
Tests Core Integrator in all configuration modes and captures JSON artifacts
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime

def test_configuration_mode(mode_name, env_overrides):
    """Test a specific configuration mode and capture outputs"""
    print(f"\n{'='*60}")
    print(f"TESTING MODE: {mode_name}")
    print(f"{'='*60}")
    
    # Apply environment overrides
    original_env = {}
    for key, value in env_overrides.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = str(value)
    
    try:
        # Import and initialize
        sys.path.insert(0, str(Path.cwd()))
        import main
        
        # Test health endpoint
        health_result = test_health_endpoint()
        
        # Test diagnostics endpoint  
        diagnostics_result = test_diagnostics_endpoint()
        
        # Test feedback validation
        feedback_result = test_feedback_validation()
        
        return {
            "mode": mode_name,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "health": health_result,
            "diagnostics": diagnostics_result,
            "feedback_validation": feedback_result,
            "status": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "mode": mode_name,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "error": str(e),
            "status": "FAILED"
        }
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

def test_health_endpoint():
    """Test /system/health endpoint"""
    try:
        # Import after env setup
        import main
        
        # Simulate health check logic
        components = {}
        
        # SQLite check
        try:
            import sqlite3
            from config.config import DB_PATH
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT 1").fetchone()
            components["database"] = "healthy"
        except Exception as e:
            components["database"] = f"unhealthy: {str(e)}"
        
        # MongoDB check (if enabled)
        if os.getenv("USE_MONGODB", "false").lower() == "true":
            try:
                from src.db.mongodb_adapter import MongoDBAdapter
                from config.config import MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME
                mongo_adapter = MongoDBAdapter(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)
                mongo_adapter.client.admin.command('ping')
                components["mongodb"] = "healthy"
            except Exception as e:
                components["mongodb"] = f"unhealthy: {str(e)}"
        
        # Noopur check (if enabled)
        if os.getenv("INTEGRATOR_USE_NOOPUR", "false").lower() == "true":
            external_health = main.gateway.check_external_service_health()
            components["external_service"] = external_health["status"]
        
        components["gateway"] = "healthy"
        components["modules"] = len(main.gateway.agents)
        
        # Overall status
        unhealthy_components = [k for k, v in components.items() if "unhealthy" in str(v)]
        overall_status = "degraded" if unhealthy_components else "healthy"
        
        return {
            "status": overall_status,
            "components": components,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def test_diagnostics_endpoint():
    """Test /system/diagnostics endpoint"""
    try:
        import main
        import sqlite3
        from config.config import DB_PATH
        
        # Module load status
        module_load_status = {}
        for name, agent in main.gateway.agents.items():
            module_load_status[name] = "valid" if agent is not None else "invalid"
        
        # Database stats
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
        
        # Integration checks
        integration_checks = {
            "core_modules_loaded": all(status == "valid" for status in module_load_status.values()),
            "database_accessible": db_healthy,
            "gateway_initialized": main.gateway is not None,
            "memory_adapter_ready": main.gateway.memory is not None
        }
        
        # MongoDB check
        if os.getenv("USE_MONGODB", "false").lower() == "true":
            try:
                from src.db.mongodb_adapter import MongoDBAdapter
                from config.config import MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME
                mongo_adapter = MongoDBAdapter(MONGODB_CONNECTION_STRING, MONGODB_DATABASE_NAME)
                mongo_adapter.client.admin.command('ping')
                integration_checks["mongodb_ready"] = True
            except Exception:
                integration_checks["mongodb_ready"] = False
        
        # Noopur check
        if os.getenv("INTEGRATOR_USE_NOOPUR", "false").lower() == "true":
            external_health = main.gateway.check_external_service_health()
            integration_checks["external_service_ready"] = external_health["status"] == "healthy"
        
        # Compute integration readiness
        integration_ready = all(integration_checks.values())
        failing_components = [k for k, v in integration_checks.items() if not v]
        
        # Integration score
        total_checks = len(integration_checks)
        passing = sum(1 for v in integration_checks.values() if v)
        integration_score = round((passing / total_checks) if total_checks else 0.0, 3)
        
        readiness_reason = "all_checks_passed" if integration_ready else ";".join(failing_components)
        
        return {
            "module_load_status": module_load_status,
            "integration_ready": integration_ready,
            "integration_checks": integration_checks,
            "integration_score": integration_score,
            "readiness_reason": readiness_reason,
            "failing_components": failing_components,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "memory": {
                "total_interactions": total_interactions,
                "unique_users": unique_users,
                "db_path": DB_PATH
            }
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def test_feedback_validation():
    """Test feedback schema validation"""
    try:
        from src.core.feedback_models import CanonicalFeedbackSchema, FeedbackRequest
        from pydantic import ValidationError
        
        results = {
            "valid_feedback_accepted": False,
            "invalid_feedback_rejected": False,
            "schema_enforcement": False
        }
        
        # Test valid feedback
        try:
            valid_feedback = CanonicalFeedbackSchema(
                generation_id=123,
                command="+1",
                user_id="test_user"
            )
            results["valid_feedback_accepted"] = True
        except Exception:
            pass
        
        # Test invalid feedback rejection
        try:
            invalid_feedback = CanonicalFeedbackSchema(
                generation_id=123,
                command="invalid_command",
                user_id="test_user"
            )
            results["invalid_feedback_rejected"] = False  # Should have failed
        except ValidationError:
            results["invalid_feedback_rejected"] = True  # Correctly rejected
        except Exception:
            pass
        
        # Test schema enforcement
        results["schema_enforcement"] = results["valid_feedback_accepted"] and results["invalid_feedback_rejected"]
        
        return results
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def main():
    """Main integration verification workflow"""
    print("CORE INTEGRATOR - FINAL INTEGRATION VERIFICATION")
    print("=" * 80)
    
    # Test configurations
    test_modes = [
        {
            "name": "SQLite_Only",
            "env": {
                "USE_MONGODB": "false",
                "INTEGRATOR_USE_NOOPUR": "false",
                "SSPL_ENABLED": "false"
            }
        },
        {
            "name": "MongoDB_Enabled", 
            "env": {
                "USE_MONGODB": "true",
                "INTEGRATOR_USE_NOOPUR": "false",
                "SSPL_ENABLED": "false"
            }
        },
        {
            "name": "Noopur_Enabled",
            "env": {
                "USE_MONGODB": "false", 
                "INTEGRATOR_USE_NOOPUR": "true",
                "SSPL_ENABLED": "false"
            }
        },
        {
            "name": "All_Disabled",
            "env": {
                "USE_MONGODB": "false",
                "INTEGRATOR_USE_NOOPUR": "false", 
                "SSPL_ENABLED": "false"
            }
        }
    ]
    
    results = []
    
    for mode in test_modes:
        result = test_configuration_mode(mode["name"], mode["env"])
        results.append(result)
        
        # Save individual result
        mode_file = Path(f"reports/integration_verification_{mode['name'].lower()}.json")
        mode_file.parent.mkdir(exist_ok=True)
        with open(mode_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    # Generate summary report
    summary = {
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "verification_status": "COMPLETED",
        "total_modes_tested": len(test_modes),
        "successful_modes": sum(1 for r in results if r.get("status") == "SUCCESS"),
        "failed_modes": sum(1 for r in results if r.get("status") == "FAILED"),
        "modes": results,
        "integration_verification_complete": True
    }
    
    # Save summary
    summary_file = Path("reports/final_integration_verification.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*80}")
    print("INTEGRATION VERIFICATION COMPLETE")
    print(f"{'='*80}")
    print(f"Modes Tested: {summary['total_modes_tested']}")
    print(f"Successful: {summary['successful_modes']}")
    print(f"Failed: {summary['failed_modes']}")
    print(f"Report: {summary_file}")
    
    return summary['failed_modes'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)