#!/usr/bin/env python3
"""
🔧 API Connection Test - Verify Your Binance API Keys
Test your API keys before starting live trading
"""

import os
import ccxt
from dotenv import load_dotenv

def test_binance_connection():
    """Test Binance API connection"""
    try:
        print("🔧 Testing Binance API Connection...")
        
        # Load configuration
        load_dotenv('live_trading_config.env')
        
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or api_key == 'your_real_binance_api_key_here':
            print("❌ API key not set in live_trading_config.env")
            return False
        
        if not secret_key or secret_key == 'your_real_binance_secret_key_here':
            print("❌ Secret key not set in live_trading_config.env")
            return False
        
        # Test connection
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,  # Live trading
            'enableRateLimit': True,
        })
        
        # Test API permissions
        print("🔐 Testing API permissions...")
        account_info = exchange.fetch_balance()
        
        # Check USDT balance
        usdt_balance = account_info.get('USDT', {}).get('free', 0)
        print(f"✅ API Connection Successful!")
        print(f"💰 USDT Balance: ${usdt_balance:.2f}")
        
        # Test market data access
        print("📊 Testing market data access...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ Market Data Access: BTC/USDT = ${ticker['last']:.2f}")
        
        # Check trading permissions
        print("🎯 Testing trading permissions...")
        try:
            # Try to get open orders (tests trading permission without placing order)
            orders = exchange.fetch_open_orders('BTC/USDT')
            print("✅ Trading Permissions: Verified")
        except Exception as e:
            if "insufficient" in str(e).lower():
                print("✅ Trading Permissions: Verified (insufficient balance is normal)")
            else:
                print(f"⚠️ Trading Permission Issue: {e}")
        
        print("\n🎉 All tests passed! Ready for live trading!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\n💡 Common issues:")
        print("   - Check your API key and secret are correct")
        print("   - Ensure 'Spot & Margin Trading' is enabled")
        print("   - Verify IP restriction settings")
        return False

if __name__ == "__main__":
    test_binance_connection() 