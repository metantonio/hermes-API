#!/usr/bin/env python3
"""Simple test for Hermes Web Data API"""

import urllib.request
import json
import sys

# Add venv to path
sys.path.insert(0, '/home/antonio/hermes/api/venv')

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("=== Hermes Web Data API - OpenAI-Compatible Format Test ===\n")
    
    # Test 1: Health endpoint
    print("Test 1: Health endpoint (/health)")
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/health", timeout=10)
        response = json.loads(req.read().decode())
        print(f"  ✓ Status: {response.get('status')}")
        print(f"  ✓ Timestamp: {response.get('timestamp')}\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False
    
    # Test 2: Chat endpoint with OpenAI format
    print("Test 2: Chat endpoint (/api/v1/chat)")
    try:
        url = f"{BASE_URL}/api/v1/chat"
        data = json.dumps({
            "model": "hermes-agent",
            "messages": [
                {"role": "system", "content": "You are a Python expert."},
                {"role": "user", "content": "Write a fibonacci function"}
            ],
            "stream": False
        }).encode('utf-8')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-hermes-webdata-api-key-2026"
        }
        
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST"
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode())
        
        print(f"  ✓ Response ID: {result.get('id')}")
        print(f"  ✓ Object type: {result.get('object')}")
        print(f"  ✓ Model: {result.get('model')}")
        print(f"  ✓ Choices count: {len(result.get('choices', []))}")
        print(f"  ✓ Usage: {result.get('usage')}")
        
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"\n  Assistant response (first 100 chars):")
        print(f"  '{content[:100]}'\n")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
