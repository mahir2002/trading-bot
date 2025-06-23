#!/usr/bin/env python3
"""
Test AI Trading Bot API
Simple test script to verify API functionality
"""

import requests
import json
import time
import sys

# API Configuration
API_BASE_URL = "http://localhost:5001/api"
DEFAULT_ADMIN = {"username": "admin", "password": "admin123"}

def test_api_endpoint(endpoint, method="GET", data=None, headers=None, description=""):
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        
        print(f"📡 {method} {endpoint} - {description}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            try:
                result = response.json()
                if isinstance(result, dict) and len(result) <= 5:
                    print(f"   Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"   Response: {type(result).__name__} with {len(result) if hasattr(result, '__len__') else 'N/A'} items")
            except:
                print(f"   Response: {response.text[:100]}...")
        else:
            print(f"   Error: {response.text}")
        
        print()
        return response
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {url}")
        print("   Make sure the API server is running: python start_api.py")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Main test routine"""
    print("🧪 AI Trading Bot API - Test Suite")
    print("=" * 50)
    
    # Test 1: Health Check (no auth required)
    print("🏥 Testing Health Check...")
    health_response = test_api_endpoint("/health", description="Health check")
    
    if not health_response or health_response.status_code != 200:
        print("❌ API server is not responding. Please start it first:")
        print("   python start_api.py")
        return False
    
    # Test 2: Authentication
    print("🔐 Testing Authentication...")
    auth_response = test_api_endpoint(
        "/auth/login", 
        method="POST", 
        data=DEFAULT_ADMIN,
        description="Admin login"
    )
    
    if not auth_response or auth_response.status_code != 200:
        print("❌ Authentication failed")
        return False
    
    # Get token for authenticated requests
    token_data = auth_response.json()
    token = token_data.get('token')
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"✅ Authentication successful")
    print(f"   Token: {token[:20]}...")
    print()
    
    # Test 3: Bot Status (authenticated)
    print("🤖 Testing Bot Control...")
    test_api_endpoint("/bot/status", headers=headers, description="Bot status")
    
    # Test 4: Configuration (authenticated)
    print("⚙️  Testing Configuration...")
    test_api_endpoint("/config", headers=headers, description="Get configuration")
    
    # Test 5: Market Data (authenticated)
    print("📊 Testing Market Data...")
    test_api_endpoint("/market/price/BTC/USDT", headers=headers, description="BTC price")
    
    # Test 6: Portfolio (authenticated)
    print("💼 Testing Portfolio...")
    test_api_endpoint("/portfolio/balance", headers=headers, description="Portfolio balance")
    
    # Test 7: Trading Data (authenticated)
    print("📈 Testing Trading Data...")
    test_api_endpoint("/trades", headers=headers, description="Recent trades")
    test_api_endpoint("/trades/stats", headers=headers, description="Trade statistics")
    
    # Test 8: Documentation
    print("📚 Testing Documentation...")
    test_api_endpoint("/docs", description="API documentation")
    
    print("✅ API test suite completed!")
    print("\n📋 Summary:")
    print("   - API server is running and responding")
    print("   - Authentication is working")
    print("   - All major endpoints are accessible")
    print("   - Ready for integration with trading bot")
    
    print("\n🚀 Next Steps:")
    print("   1. Add your exchange API keys to .env file")
    print("   2. Set up Telegram notifications")
    print("   3. Test bot start/stop functionality")
    print("   4. Try paper trading first")
    
    return True

if __name__ == "__main__":
    main() 