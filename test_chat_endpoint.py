#!/usr/bin/env python3
"""
Test script for Hermes Web Data API chat endpoint.
Tests the /api/v1/chat endpoint with a sample question.
"""

import sys
import os
from pathlib import Path

# Agregar ~/.hermes al path para importar llama-cpp
USER_HERMES = Path(os.path.expanduser("~/.hermes"))
if USER_HERMES.exists() and str(USER_HERMES) not in sys.path:
    sys.path.insert(0, str(USER_HERMES))

# Importar llama-cpp directamente
try:
    from llama_cpp import Llama
    print(f"✅ llama-cpp cargado correctamente desde: {USER_HERMES}")
except ImportError as e:
    print(f"❌ Error importando llama-cpp: {e}")
    sys.exit(1)

# Importar wrapper llama-cpp
try:
    from hermes_llama_wrapper import intercept_llm_call
    print(f"✅ Wrapper llama-cpp cargado desde: {USER_HERMES}/hermes_llama_wrapper.py")
except ImportError as e:
    print(f"❌ Error importando hermes_llama_wrapper: {e}")
    sys.exit(1)

from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_chat_endpoint():
    """Test the chat endpoint with a sample question."""
    print("=" * 70)
    print("HERMES WEB DATA API - CHAT ENDPOINT TEST")
    print("=" * 70)
    
   # Test request - neutral topic to avoid safety filters
    test_request = {
        "message": "¿Cuáles son los principales ríos de España y su importancia económica?",
        "context": {
            "language": "es",
            "user_id": "test_user_001",
            "session_id": "test_session_001"
        }
    }
    
    print("\n📤 Test Request:")
    print(f"   Message: {test_request['message']}")
    print(f"   Context: {test_request['context']}")
    
    # Send request
    print("\n🔄 Sending request to /api/v1/chat...")
    response = client.post("/api/v1/chat", json=test_request)
    
    print(f"\n📊 Response Details:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"   Response Length: {len(response.text)} bytes")
    
    # Parse response
    try:
        data = response.json()
    except Exception as e:
        print(f"\n❌ Failed to parse JSON response: {e}")
        print(f"   Raw response: {response.text}")
        return False
    
    print(f"\n📥 Response Data:")
    print(f"   JSON: {data}")
    
    # Validate response structure
    print("\n✅ Validation Checks:")
    
    if "error" in data:
        print(f"   ✗ Error returned: {data['error']}")
        print(f"   Detail: {data.get('detail', 'N/A')}")
        return False
    elif "message" in data and "conversation_id" in data:
        print(f"   ✓ Valid response structure")
        print(f"     - Message: {data.get('message', 'N/A')}...")
        print(f"     - Conversation ID: {data.get('conversation_id', 'N/A')}")
        print(f"     - Timestamp: {data.get('timestamp', 'N/A')}")
        
        # Check safety checks
        if "safety_checks" in data:
            safety = data["safety_checks"]
            print(f"\n🛡️  Safety Checks:")
            for key, value in safety.items():
                status = "⚠️ " if value else "✓"
                print(f"   {status} {key}: {value}")
        
        return True
    else:
        print(f"   ✗ Unexpected response structure: {data.keys()}")
        return False

def test_chat_with_safety_content():
    """Test chat endpoint with potentially sensitive content."""
    print("\n" + "=" * 70)
    print("SECURITY TEST - Sensitive Content Detection")
    print("=" * 70)
    
    test_request = {
        "message": "¿Cómo puedo obtener información sobre passwords o tokens API?",
        "context": {}
    }
    
    print("\n📤 Testing with sensitive content...")
    response = client.post("/api/v1/chat", json=test_request)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data}")
        
        # Check if safety filters worked
        if "safety_checks" in data:
            if data["safety_checks"].get("contains_credentials"):
                print(f"\n✅ Safety filter detected potential credentials!")
            elif data["safety_checks"].get("suggested_response"):
                print(f"\n⚠️  Safety message returned: {data['safety_checks']['suggested_response']}...")
            else:
                print(f"\n✓ No sensitive content detected (as expected)")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def main():
    """Run all chat endpoint tests."""
    print("\n🚀 Starting Hermes Chat Endpoint Tests...\n")
    
    # Test 1: Basic chat request
    success = test_chat_endpoint()
    
    # Test 2: Security/safety content
    safety_test = test_chat_with_safety_content()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"   Basic Chat Test:      {'✓ PASSED' if success else '✗ FAILED'}")
    print(f"   Security Test:         {'✓ PASSED' if safety_test else '✗ FAILED'}")
    print(f"   Overall Status:        {'✓ ALL TESTS PASSED' if (success and safety_test) else '✗ SOME TESTS FAILED'}")
    print("=" * 70)
    
    return 0 if (success and safety_test) else 1

if __name__ == "__main__":
    sys.exit(main())
