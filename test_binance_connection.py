#!/usr/bin/env python3
"""
Test Binance API Connection
This script tests your Binance API keys and connection
"""

import os
import sys
from dotenv import load_dotenv
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode

# Load environment variables
load_dotenv('config.env')

def test_binance_connection():
    """Test Binance API connection"""
    
    # Get API credentials
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    
    print("🔍 Testing Binance API Connection...")
    print(f"📍 Using Testnet: {use_testnet}")
    
    if not api_key or not secret_key:
        print("❌ ERROR: Binance API keys not found!")
        print("Please make sure you have:")
        print("- BINANCE_API_KEY=your_api_key")
        print("- BINANCE_SECRET_KEY=your_secret_key")
        print("- BINANCE_TESTNET=true")
        print("in your config.env file")
        return False
    
    # Set base URL
    if use_testnet:
        base_url = "https://testnet.binance.vision"
    else:
        base_url = "https://api.binance.com"
    
    print(f"🌐 Base URL: {base_url}")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-8:]}")
    
    # Test 1: Server Time (No authentication needed)
    print("\n📡 Test 1: Server Time...")
    try:
        response = requests.get(f"{base_url}/api/v3/time")
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            print(f"✅ Server Time: {server_time}")
        else:
            print(f"❌ Server Time Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server Time Exception: {e}")
        return False
    
    # Test 2: Exchange Info (No authentication needed)
    print("\n📊 Test 2: Exchange Info...")
    try:
        response = requests.get(f"{base_url}/api/v3/exchangeInfo")
        if response.status_code == 200:
            exchange_info = response.json()
            symbols_count = len(exchange_info['symbols'])
            print(f"✅ Exchange Info: {symbols_count} trading pairs available")
        else:
            print(f"❌ Exchange Info Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exchange Info Exception: {e}")
        return False
    
    # Test 3: Account Info (Authentication required)
    print("\n👤 Test 3: Account Info (Authentication)...")
    try:
        # Create signature
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
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            account_info = response.json()
            print(f"✅ Account Info Retrieved Successfully!")
            print(f"📈 Account Type: {account_info.get('accountType', 'Unknown')}")
            print(f"💰 Balances: {len(account_info.get('balances', []))} assets")
            
            # Show non-zero balances
            balances = account_info.get('balances', [])
            non_zero_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
            
            if non_zero_balances:
                print("\n💵 Non-zero Balances:")
                for balance in non_zero_balances[:5]:  # Show first 5
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    if free > 0 or locked > 0:
                        print(f"   {balance['asset']}: {free} (free) + {locked} (locked)")
            else:
                print("💡 No balances found (normal for new testnet accounts)")
                
        else:
            print(f"❌ Account Info Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Account Info Exception: {e}")
        return False
    
    # Test 4: Get Symbol Price (BTCUSDT)
    print("\n💲 Test 4: Symbol Price (BTCUSDT)...")
    try:
        response = requests.get(f"{base_url}/api/v3/ticker/price?symbol=BTCUSDT")
        if response.status_code == 200:
            price_data = response.json()
            print(f"✅ BTCUSDT Price: ${float(price_data['price']):,.2f}")
        else:
            print(f"❌ Price Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Price Exception: {e}")
    
    print("\n🎉 Binance API Connection Test Complete!")
    print("✅ Your API keys are working correctly!")
    
    if use_testnet:
        print("\n💡 Next Steps:")
        print("1. Your bot can now connect to Binance Testnet")
        print("2. You can start paper trading safely")
        print("3. Test your trading strategies with fake money")
        print("4. When ready, switch to live trading")
    
    return True

def create_config_file():
    """Create config.env file if it doesn't exist"""
    if not os.path.exists('config.env'):
        print("📝 Creating config.env file...")
        
        # Copy from example and prompt for keys
        with open('config.env.example', 'r') as f:
            content = f.read()
        
        print("\n🔑 Please enter your Binance API credentials:")
        api_key = input("Binance API Key: ").strip()
        secret_key = input("Binance Secret Key: ").strip()
        
        # Replace placeholders
        content = content.replace('your_binance_api_key', api_key)
        content = content.replace('your_binance_secret_key', secret_key)
        
        # Add testnet setting
        if 'BINANCE_TESTNET' not in content:
            content += "\n# Binance Configuration\nBINANCE_TESTNET=true\n"
        
        with open('config.env', 'w') as f:
            f.write(content)
        
        print("✅ config.env file created!")
        return True
    
    return False

if __name__ == "__main__":
    print("🚀 Binance API Connection Tester")
    print("=" * 50)
    
    # Check if config.env exists
    if not os.path.exists('config.env'):
        print("⚠️  config.env file not found!")
        create_config = input("Would you like to create it now? (y/n): ").lower().strip()
        if create_config == 'y':
            create_config_file()
        else:
            print("Please create config.env file with your API keys first.")
            sys.exit(1)
    
    # Test connection
    success = test_binance_connection()
    
    if success:
        print("\n🎯 Ready to start trading!")
        print("Run: python integrate_strategies.py")
    else:
        print("\n❌ Please fix the issues above and try again.") 