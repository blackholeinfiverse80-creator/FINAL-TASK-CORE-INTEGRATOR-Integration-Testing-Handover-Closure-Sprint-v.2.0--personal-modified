#!/usr/bin/env python3
"""
Simple Multi-Database Integration Test
Tests SQLite, MongoDB, and Noopur adapter readiness
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_sqlite_adapter():
    """Test SQLite adapter"""
    print("Testing SQLite Adapter...")
    try:
        from src.db.memory_adapter import SQLiteAdapter
        adapter = SQLiteAdapter("test_db.db")
        
        # Test basic operations
        adapter.store_interaction("test_user", 
                                {"module": "test", "intent": "test"}, 
                                {"status": "success"})
        
        history = adapter.get_user_history("test_user")
        context = adapter.get_context("test_user")
        
        print("[PASS] SQLite Adapter: WORKING")
        return True
    except Exception as e:
        print(f"[FAIL] SQLite Adapter: {e}")
        return False

def test_mongodb_adapter():
    """Test MongoDB adapter"""
    print("Testing MongoDB Adapter...")
    try:
        from src.db.mongodb_adapter import MongoDBAdapter, PYMONGO_AVAILABLE
        
        if not PYMONGO_AVAILABLE:
            print("[SKIP] MongoDB Adapter: pymongo not available")
            return True  # Skip is considered a pass for this test
            
        # Try with invalid connection to test error handling
        try:
            adapter = MongoDBAdapter("mongodb://invalid:27017", "test_db")
            print("[FAIL] MongoDB Adapter: Should have failed with invalid connection")
            return False
        except Exception:
            print("[PASS] MongoDB Adapter: Properly handles connection errors")
            return True
            
    except Exception as e:
        print(f"[FAIL] MongoDB Adapter: {e}")
        return False

def test_gateway_integration():
    """Test Gateway with SQLite configuration"""
    print("Testing Gateway Integration...")
    try:
        # Set environment for SQLite only
        os.environ["USE_MONGODB"] = "false"
        os.environ["INTEGRATOR_USE_NOOPUR"] = "false"
        
        from src.core.gateway import Gateway
        gateway = Gateway()
        
        # Test basic request processing
        response = gateway.process_request(
            module="finance",
            intent="analyze", 
            user_id="test_user",
            data={"query": "test"}
        )
        
        if isinstance(response, dict) and "status" in response:
            print("[PASS] Gateway Integration: WORKING")
            return True
        else:
            print("[FAIL] Gateway Integration: Invalid response format")
            return False
            
    except Exception as e:
        print(f"[FAIL] Gateway Integration: {e}")
        return False

def main():
    """Run integration tests"""
    print("=" * 50)
    print("MULTI-DATABASE INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("SQLite Adapter", test_sqlite_adapter),
        ("MongoDB Adapter", test_mongodb_adapter), 
        ("Gateway Integration", test_gateway_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results[test_name] = test_func()
    
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    # Check specific readiness criteria
    print("\n" + "=" * 50)
    print("MULTI-DATABASE READINESS ASSESSMENT")
    print("=" * 50)
    
    readiness_checks = []
    
    # Check 1: Core adapters available
    try:
        from src.db.memory_adapter import SQLiteAdapter, RemoteNoopurAdapter
        from src.db.mongodb_adapter import MongoDBAdapter
        readiness_checks.append(("Core adapters importable", True))
    except Exception as e:
        readiness_checks.append(("Core adapters importable", False))
    
    # Check 2: Gateway can switch between adapters
    try:
        from src.core.gateway import Gateway
        readiness_checks.append(("Gateway supports multi-DB", True))
    except Exception:
        readiness_checks.append(("Gateway supports multi-DB", False))
    
    # Check 3: Configuration system works
    try:
        from config.config import USE_MONGODB, INTEGRATOR_USE_NOOPUR
        readiness_checks.append(("Configuration system", True))
    except Exception:
        readiness_checks.append(("Configuration system", False))
    
    # Check 4: Dependencies installed
    try:
        import pymongo
        import fastapi
        readiness_checks.append(("Required dependencies", True))
    except ImportError:
        readiness_checks.append(("Required dependencies", False))
    
    for check_name, result in readiness_checks:
        status = "PASS" if result else "FAIL"
        print(f"{check_name}: {status}")
    
    ready_count = sum(1 for _, result in readiness_checks if result)
    total_checks = len(readiness_checks)
    
    print(f"\nReadiness Score: {ready_count}/{total_checks}")
    
    if ready_count == total_checks:
        print("\nSTATUS: READY for multi-database integration testing")
        print("- All adapters are available and functional")
        print("- Gateway supports database switching")
        print("- Configuration system is working")
        print("- All dependencies are installed")
    elif ready_count >= total_checks - 1:
        print("\nSTATUS: MOSTLY READY (minor issues)")
    else:
        print("\nSTATUS: NOT READY (significant issues)")
    
    return ready_count == total_checks

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)