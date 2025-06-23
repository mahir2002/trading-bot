#!/usr/bin/env python3
"""
Debug Binance API Connection
More detailed testing to identify the exact issue
"""

import os
import ccxt
from dotenv import load_dotenv
import requests
import hmac
import hashlib
import time

# Load environment variables
load_dotenv('config.env')

def test_ccxt_binance():
    """Test CCXT Binance connection"""
    print("🔍 Testing CCXT Binance Connection...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    
    print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"Secret Key: {secret_key[:8]}...{secret_key[-8:]}")
    print(f"Using Testnet: {use_testnet}")
    
    try:
        # Configure for testnet
        binance_config = {
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'verbose': True,  # Enable verbose logging
        }
        
        if use_testnet:
            binance_config['urls'] = {
                'api': {
                    'public': 'https://testnet.binance.vision/api',
                    'private': 'https://testnet.binance.vision/api',
                }
            }
            print("✅ Configured for testnet")
        
        # Create exchange instance
        exchange = ccxt.binance(binance_config)
        
        print("📡 Testing public endpoint...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT Price: ${ticker['last']}")
        
        print("🔐 Testing authenticated endpoint...")
        balance = exchange.fetch_balance()
        print(f"✅ Account balance retrieved: {len(balance['info']['balances'])} assets")
        
        # Show non-zero balances
        for asset in balance['info']['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            if free > 0 or locked > 0:
                print(f"   {asset['asset']}: {free} (free) + {locked} (locked)")
        
        return True
        
    except Exception as e:
        print(f"❌ CCXT Error: {e}")
        print(f"Error type: {type(e)}")
        return False

def test_direct_api():
    """Test direct API calls"""
    print("\n🔍 Testing Direct API Calls...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    base_url = "https://testnet.binance.vision"
    
    try:
        # Test account endpoint with proper signature
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        
        signature = hmac.new(
            secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-MBX-APIKEY': api_key
        }
        
        url = f"{base_url}/api/v3/account?{query_string}&signature={signature}"
        
        print(f"Request URL: {base_url}/api/v3/account")
        print(f"Query string: {query_string}")
        print(f"Signature: {signature[:16]}...")
        
        response = requests.get(url, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Direct API success: {data.get('accountType', 'Unknown')} account")
            return True
        else:
            print(f"❌ Direct API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API exception: {e}")
        return False

def check_api_key_format():
    """Check API key format"""
    print("\n🔍 Checking API Key Format...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    print(f"API Key length: {len(api_key)}")
    print(f"Secret Key length: {len(secret_key)}")
    print(f"API Key starts with: {api_key[:4]}")
    print(f"Secret Key starts with: {secret_key[:4]}")
    
    # Check for common issues
    if ' ' in api_key or ' ' in secret_key:
        print("⚠️  WARNING: API keys contain spaces!")
    
    if '\n' in api_key or '\n' in secret_key:
        print("⚠️  WARNING: API keys contain newlines!")
    
    # Check if keys are alphanumeric
    import string
    valid_chars = string.ascii_letters + string.digits
    
    if not all(c in valid_chars for c in api_key):
        print("⚠️  WARNING: API key contains invalid characters!")
    
    if not all(c in valid_chars for c in secret_key):
        print("⚠️  WARNING: Secret key contains invalid characters!")

if __name__ == "__main__":
    print("🚀 Binance API Debug Tool")
    print("=" * 50)
    
    # Check API key format
    check_api_key_format()
    
    # Test direct API
    direct_success = test_direct_api()
    
    # Test CCXT
    ccxt_success = test_ccxt_binance()
    
    print("\n📊 Summary:")
    print(f"Direct API: {'✅ Success' if direct_success else '❌ Failed'}")
    print(f"CCXT API: {'✅ Success' if ccxt_success else '❌ Failed'}")
    
    if not direct_success and not ccxt_success:
        print("\n🔧 Troubleshooting:")
        print("1. Verify your API keys are correct")
        print("2. Check if API keys have proper permissions")
        print("3. Make sure you're using testnet keys for testnet")
        print("4. Try regenerating your API keys") 