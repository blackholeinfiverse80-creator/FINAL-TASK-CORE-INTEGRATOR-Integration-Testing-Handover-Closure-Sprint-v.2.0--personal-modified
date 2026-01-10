#!/usr/bin/env python3
"""
Quick Multi-Database Integration Test
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
        
        print("✅ SQLite Adapter: WORKING")
        return True
    except Exception as e:
        print(f"❌ SQLite Adapter: FAILED - {e}")
        return False

def test_mongodb_adapter():
    """Test MongoDB adapter (with mock if no real connection)"""
    print("Testing MongoDB Adapter...")
    try:
        from src.db.mongodb_adapter import MongoDBAdapter, PYMONGO_AVAILABLE
        
        if not PYMONGO_AVAILABLE:
            print("⚠️  MongoDB Adapter: pymongo not available")
            return False
            
        # Try with invalid connection to test error handling
        try:
            adapter = MongoDBAdapter("mongodb://invalid:27017", "test_db")
            print("❌ MongoDB Adapter: Should have failed with invalid connection")
            return False
        except Exception:
            print("✅ MongoDB Adapter: Properly handles connection errors")
            return True
            
    except Exception as e:
        print(f"❌ MongoDB Adapter: FAILED - {e}")
        return False

def test_noopur_adapter():
    """Test Noopur adapter"""
    print("Testing Noopur Adapter...")
    try:
        from src.db.memory_adapter import RemoteNoopurAdapter
        
        # Test with NOOPUR disabled
        os.environ["INTEGRATOR_USE_NOOPUR"] = "false"
        adapter = RemoteNoopurAdapter()
        
        # Should work but return empty results
        history = adapter.get_user_history("test_user")
        context = adapter.get_context("test_user")
        
        print("✅ Noopur Adapter: WORKING (disabled mode)")
        return True
    except Exception as e:
        print(f"❌ Noopur Adapter: FAILED - {e}")
        return False

def test_gateway_integration():
    """Test Gateway with different database configurations"""
    print("Testing Gateway Integration...")
    try:
        # Test with SQLite only
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
            print("✅ Gateway Integration: WORKING")
            return True
        else:
            print("❌ Gateway Integration: Invalid response format")
            return False
            
    except Exception as e:
        print(f"❌ Gateway Integration: FAILED - {e}")
        return False

def test_configuration_switching():
    """Test switching between database configurations"""
    print("Testing Configuration Switching...")
    
    configs = [
        {"USE_MONGODB": "false", "INTEGRATOR_USE_NOOPUR": "false"},
        {"USE_MONGODB": "false", "INTEGRATOR_USE_NOOPUR": "true"},
        {"USE_MONGODB": "true", "INTEGRATOR_USE_NOOPUR": "false"},
    ]
    
    results = []
    for i, config in enumerate(configs):
        try:
            # Update environment
            for key, value in config.items():
                os.environ[key] = value
            
            # Force reload of config module
            if 'config.config' in sys.modules:
                del sys.modules['config.config']
            if 'src.core.gateway' in sys.modules:
                del sys.modules['src.core.gateway']
                
            from src.core.gateway import Gateway
            gateway = Gateway()
            
            # Test that gateway initializes
            adapter_type = type(gateway.memory).__name__
            results.append(f"Config {i+1}: {adapter_type}")
            
        except Exception as e:
            results.append(f"Config {i+1}: FAILED - {str(e)[:50]}")
    
    print("Configuration switching results:")
    for result in results:
        print(f"  {result}")
    
    return len([r for r in results if "FAILED" not in r]) > 0

def main():
    """Run all integration tests"""
    print("=" * 50)
    print("MULTI-DATABASE INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("SQLite Adapter", test_sqlite_adapter),
        ("MongoDB Adapter", test_mongodb_adapter), 
        ("Noopur Adapter", test_noopur_adapter),
        ("Gateway Integration", test_gateway_integration),
        ("Configuration Switching", test_configuration_switching),
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
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Multi-database integration is READY for testing!")
    elif passed >= len(tests) - 1:
        print("⚠️  Multi-database integration is MOSTLY ready (minor issues)")
    else:
        print("❌ Multi-database integration needs work before testing")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)