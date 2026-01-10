#!/usr/bin/env python3
import json
import os
import sys
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime

class Day1Verifier:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.artifacts = {}
        
    def update_env(self, config):
        with open(".env", 'w') as f:
            f.write("# Day 1 Integration Verification\n")
            for k, v in config.items():
                f.write(f"{k}={v}\n")
                
    def start_server(self):
        return subprocess.Popen([sys.executable, "main.py"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    def wait_server(self):
        for _ in range(30):
            try:
                requests.get(f"{self.base_url}/", timeout=2)
                return True
            except:
                time.sleep(1)
        return False
        
    def test_config(self, name, config):
        print(f"Testing {name}...")
        self.update_env(config)
        
        server = self.start_server()
        try:
            if not self.wait_server():
                return {"error": "Server failed to start"}
                
            # Test endpoints
            health = requests.get(f"{self.base_url}/system/health").json()
            diagnostics = requests.get(f"{self.base_url}/system/diagnostics").json()
            
            # Test invalid feedback (should fail)
            feedback_resp = requests.post(f"{self.base_url}/feedback", 
                json={"user_id": "test", "generation_id": "invalid", "feedback_type": "bad"})
            
            return {
                "health": health,
                "diagnostics": diagnostics, 
                "feedback_rejection": feedback_resp.status_code >= 400,
                "integration_ready": diagnostics.get("integration_ready"),
                "integration_score": diagnostics.get("integration_score")
            }
        finally:
            server.terminate()
            server.wait()
            
    def run(self):
        configs = {
            "sqlite_only": {"USE_MONGODB": "false", "INTEGRATOR_USE_NOOPUR": "false"},
            "mongodb_enabled": {"USE_MONGODB": "true", "MONGODB_CONNECTION_STRING": "mongodb://localhost:27017", "INTEGRATOR_USE_NOOPUR": "false"},
            "noopur_enabled": {"USE_MONGODB": "false", "INTEGRATOR_USE_NOOPUR": "true", "NOOPUR_BASE_URL": "http://localhost:5001"},
            "noopur_disabled": {"USE_MONGODB": "false", "INTEGRATOR_USE_NOOPUR": "false"}
        }
        
        for name, config in configs.items():
            self.artifacts[name] = self.test_config(name, config)
            
        # Test determinism
        det1 = self.test_config("determinism_1", configs["sqlite_only"])
        det2 = self.test_config("determinism_2", configs["sqlite_only"])
        
        self.artifacts["determinism_test"] = {
            "run1_ready": det1.get("integration_ready"),
            "run2_ready": det2.get("integration_ready"),
            "deterministic": det1.get("integration_ready") == det2.get("integration_ready")
        }
        
        # Save artifacts
        Path("verification_artifacts").mkdir(exist_ok=True)
        with open("verification_artifacts/day1_results.json", 'w') as f:
            json.dump(self.artifacts, f, indent=2, default=str)
            
        print("Day 1 verification complete. Artifacts saved.")
        return self.artifacts

if __name__ == "__main__":
    verifier = Day1Verifier()
    verifier.run()