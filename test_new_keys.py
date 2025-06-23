#!/usr/bin/env python3
"""
🔧 Test New API Keys Directly
Direct test of your updated API keys
"""

import os
import ccxt
from dotenv import load_dotenv
from datetime import datetime

def test_new_api_keys():
    """Test the new API keys directly"""
    print("🔧 Testing Your New Binance API Keys")
    print("=" * 50)
    
    # Force reload of config.env
    load_dotenv('config.env', override=True)
    
    # Get API keys
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    print(f"📊 Current API Key: {api_key[:8]}...{api_key[-8:] if api_key and len(api_key) > 16 else ''}")
    print(f"🔐 Current Secret: {secret_key[:8]}...{secret_key[-8:] if secret_key and len(secret_key) > 16 else ''}")
    print(f"📏 API Key length: {len(api_key) if api_key else 0}")
    print(f"📏 Secret length: {len(secret_key) if secret_key else 0}")
    
    # Verify these are the new keys
    if api_key and api_key.startswith('plbTwvXB'):
        print("✅ Found new API key (starts with plbTwvXB)")
    else:
        print("❌ Not using new API key!")
        return False
    
    if secret_key and secret_key.startswith('V16KGf9r'):
        print("✅ Found new secret key (starts with V16KGf9r)")
    else:
        print("❌ Not using new secret key!")
        return False
    
    try:
        # Create exchange instance
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,  # Mainnet
            'enableRateLimit': True,
        })
        
        print("\n🔗 Testing connection...")
        
        # Test 1: Server time
        server_time = exchange.fetch_time()
        print(f"✅ Server connection: {datetime.fromtimestamp(server_time/1000)}")
        
        # Test 2: Account info
        print("\n💰 Testing account access...")
        account_info = exchange.fetch_balance()
        
        print("🎉 SUCCESS! Account access working!")
        print("\n💰 Account Summary:")
        
        # Show balances
        for asset, balance in account_info.items():
            if isinstance(balance, dict) and balance.get('free', 0) > 0:
                free_balance = balance['free']
                if free_balance > 0.001:
                    print(f"   {asset}: {free_balance:.6f}")
        
        # Test market data
        print("\n📊 Testing market data...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT: ${ticker['last']:,.2f}")
        
        # Check account status
        account_info_detail = account_info.get('info', {})
        print(f"\n📊 Account Details:")
        print(f"   Can Trade: {account_info_detail.get('canTrade', 'Unknown')}")
        print(f"   Account Type: {account_info_detail.get('accountType', 'Unknown')}")
        
        return True
        
    except ccxt.AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("\n🔍 This means:")
        print("   1. API key or secret is incorrect")
        print("   2. IP restrictions are blocking you")
        print("   3. API key doesn't have required permissions")
        print(f"\n🌐 Your IP: 95.146.191.155 (from previous check)")
        print("   Make sure this IP is whitelisted on Binance")
        return False
        
    except ccxt.PermissionDenied as e:
        print(f"\n❌ Permission Error: {e}")
        print("   Your API key needs 'Enable Reading' and 'Enable Spot Trading' permissions")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

def main():
    """Main function"""
    print(f"🚀 Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_new_api_keys()
    
    if success:
        print("\n🎊 EXCELLENT! Your API keys are working!")
        print("\n📋 You're ready to:")
        print("   1. Run the trading dashboard")
        print("   2. Start with paper trading")
        print("   3. Monitor your bot's performance")
    else:
        print("\n⚠️  API keys need attention - check Binance settings")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 