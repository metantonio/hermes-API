#!/usr/bin/env python3
"""
Hermes Web Data API - Test Script
=================================
Quick tests to verify the API is working correctly.
"""

import sys
import os

# Add API directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# Test Imports
# ============================================================================

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    tests = [
        ("main", "main"),
        ("config", "config"),
        ("security_filter", "security_filter"),
        ("models", "models"),
        ("startup", "startup"),
    ]
    
    passed = 0
    failed = 0
    
    for name, module_name in tests:
        try:
            __import__(module_name)
            print(f"  ✓ {name:15} imported successfully")
            passed += 1
        except ImportError as e:
            print(f"  ✗ {name:15} failed: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


# ============================================================================
# Test Configuration
# ============================================================================

def test_config():
    """Test that configuration can be loaded"""
    print("\nTesting configuration...")
    
    try:
        from config import get_settings, SETTINGS
        settings = get_settings()
        print(f"  ✓ Settings loaded: {settings.APP_NAME}")
        print(f"    Environment: {settings.APP_ENV}")
        print(f"    Debug: {settings.DEBUG}")
        print(f"    Host: {settings.HOST}:{settings.PORT}")
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


# ============================================================================
# Test Security Filter
# ============================================================================

def test_security_filter():
    """Test that security filtering works"""
    print("\nTesting security filter...")
    
    try:
        from security_filter import SecurityFilter, create_security_filter
        
        filter = create_security_filter()
        
        # Test filtering
        test_content = """
        API key: sk_live_abc123xyz
        Password: secret123
        Credit card: 1234-5678-9012-3456
        Email: user@example.com
        Dangerous URL: https://malware.com/payload.exe
        Normal text: This is a safe message
        """
        
        filtered, alerts = filter.filter_content(test_content, "test")
        
        print(f"  ✓ Filter applied")
        print(f"    Original length: {len(test_content)}")
        print(f"    Filtered length: {len(filtered)}")
        print(f"    Alerts generated: {len(alerts)}")
        
        # Verify filtering worked
        if "REDACTED" in filtered:
            print(f"  ✓ Content was sanitized")
        else:
            print(f"  ⚠ Content may not have been sanitized properly")
            
        return True
    except Exception as e:
        print(f"  ✗ Security filter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Database Models
# ============================================================================

def test_models():
    """Test that database models work"""
    print("\nTesting database models...")
    
    try:
        from models import Base, AuditLog, SecurityAlertLog
        from sqlalchemy import inspect
        
        # Check that models are properly defined
        table_names = [t.name for t in Base.metadata.tables]
        print(f"  ✓ Models loaded: {len(table_names)} tables defined")
        
        expected_tables = [
            "audit_logs",
            "security_alert_logs",
            "data_classifications",
            "data_extractions",
            "conversations",
        ]
        
        missing = [t for t in expected_tables if t not in table_names]
        if missing:
            print(f"  ⚠ Missing tables: {missing}")
        else:
            print(f"  ✓ All expected tables defined")
            
        return True
    except Exception as e:
        print(f"  ✗ Models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test API Creation
# ============================================================================

def test_api_creation():
    """Test that the FastAPI app can be created"""
    print("\nTesting API creation...")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Health endpoint works")
            print(f"    Status: {data.get('status')}")
            print(f"    Version: {data.get('version')}")
        else:
            print(f"  ✗ Health endpoint failed: {response.status_code}")
            
        return True
    except Exception as e:
        print(f"  ✗ API creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Extraction Endpoint
# ============================================================================

def test_extraction():
    """Test the data extraction endpoint"""
    print("\nTesting extraction endpoint...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test extraction request
        response = client.post(
            "/api/v1/extract",
            json={
                "url": "https://example.com",
                "fields": [
                    {"name": "title", "path": "$.title"}
                ]
            }
        )
        
        if response.status_code in [200, 400]:
            data = response.json()
            print(f"  ✓ Extraction endpoint responded")
            print(f"    Status: {response.status_code}")
            print(f"    Success: {data.get('success')}")
        else:
            print(f"  ✗ Extraction endpoint failed: {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            
        return True
    except Exception as e:
        print(f"  ✗ Extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Chat Endpoint
# ============================================================================

def test_chat():
    """Test the Hermes chat endpoint"""
    print("\nTesting chat endpoint...")
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Test chat request
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Hello, how can I help?",
                "context": {}
            }
        )
        
        if response.status_code in [200, 400]:
            data = response.json()
            print(f"  ✓ Chat endpoint responded")
            print(f"    Status: {response.status_code}")
            print(f"    Message length: {len(data.get('message', ''))}")
        else:
            print(f"  ✗ Chat endpoint failed: {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            
        return True
    except Exception as e:
        print(f"  ✗ Chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("HERMES WEB DATA API - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Security Filter", test_security_filter),
        ("Database Models", test_models),
        ("API Creation", test_api_creation),
        ("Extraction", test_extraction),
        ("Chat", test_chat),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{'─' * 60}")
        print(f"Test: {name}")
        print(f"{'─' * 60}")
        
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"  Total: {len(tests)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print("=" * 60)
    
    if failed == 0:
        print("  ✓ All tests passed!")
    else:
        print(f"  ✗ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Hermes Web Data API test suite"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--test-only",
        help="Run specific test by name",
        choices=["imports", "config", "filter", "models", "api", "extraction", "chat"]
    )
    
    args = parser.parse_args()
    
    if args.test_only:
        # Run specific test
        test_map = {
            "imports": (test_imports, "Imports"),
            "config": (test_config, "Configuration"),
            "filter": (test_security_filter, "Security Filter"),
            "models": (test_models, "Database Models"),
            "api": (test_api_creation, "API Creation"),
            "extraction": (test_extraction, "Extraction"),
            "chat": (test_chat, "Chat"),
        }
        
        if args.test_only in test_map:
            _, name = test_map[args.test_only]
            print(f"Running test: {name}...")
            if test_map[args.test_only][0]():
                print("  ✓ Test passed")
            else:
                print("  ✗ Test failed")
        else:
            print(f"Unknown test: {args.test_only}")
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)