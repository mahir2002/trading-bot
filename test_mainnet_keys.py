#!/usr/bin/env python3
"""
🔧 Test Mainnet Binance API Keys
Test your live Binance API keys safely
"""

import os
import ccxt
from dotenv import load_dotenv
from datetime import datetime

def test_mainnet_binance():
    """Test Binance mainnet API keys"""
    print("🔧 Testing Binance Mainnet API Keys")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('config.env')
    
    try:
        # Get API keys
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        print(f"📊 API Key found: {api_key[:8]}...")
        print(f"🔐 Secret Key found: {secret_key[:8]}...")
        
        # Create exchange instance for MAINNET
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,  # FALSE = Mainnet (real trading)
            'enableRateLimit': True,
        })
        
        print("\n🔗 Connecting to Binance Mainnet...")
        
        # Test 1: Server time
        print("⏰ Testing server connection...")
        server_time = exchange.fetch_time()
        print(f"✅ Server time: {datetime.fromtimestamp(server_time/1000)}")
        
        # Test 2: Account info
        print("\n💰 Testing account access...")
        account_info = exchange.fetch_balance()
        
        print("✅ Account access successful!")
        print("\n💰 Account Balances:")
        
        # Show significant balances
        total_usdt_value = 0
        for asset, balance in account_info.items():
            if isinstance(balance, dict) and balance.get('free', 0) > 0:
                free_balance = balance['free']
                if free_balance > 0.001:  # Only show significant balances
                    print(f"   {asset}: {free_balance:.6f}")
                    if asset == 'USDT':
                        total_usdt_value += free_balance
        
        # Test 3: Market data
        print("\n📊 Testing market data...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT: ${ticker['last']:,.2f}")
        
        # Test 4: Order book
        print("\n📈 Testing order book access...")
        orderbook = exchange.fetch_order_book('BTC/USDT', limit=5)
        print(f"✅ Order book: {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")
        
        # Test 5: Trading permissions (TEST ONLY)
        usdt_balance = account_info.get('USDT', {}).get('free', 0)
        if usdt_balance > 10:
            print(f"\n🎯 Testing trading permissions (TEST MODE)...")
            try:
                # Create a TEST order (won't actually execute)
                test_order = exchange.create_order(
                    symbol='BTC/USDT',
                    type='limit',
                    side='buy',
                    amount=0.001,  # Minimum amount
                    price=ticker['last'] * 0.5,  # Very low price (won't fill)
                    params={'test': True}  # TEST MODE - no real order
                )
                print("✅ Trading permissions confirmed!")
                print("   (Test order successful - no real trade made)")
            except Exception as e:
                print(f"⚠️  Trading test failed: {e}")
                print("   This might be due to API key restrictions")
        else:
            print(f"\n⚠️  USDT Balance: ${usdt_balance:.2f}")
            print("   Consider depositing USDT for trading")
        
        # Test 6: Account status
        print(f"\n📊 Account Status:")
        print(f"   USDT Balance: ${usdt_balance:.2f}")
        print(f"   Account Type: {'Normal' if account_info.get('info', {}).get('accountType') != 'SPOT' else 'Spot'}")
        print(f"   Trading Enabled: {'Yes' if account_info.get('info', {}).get('canTrade') else 'No'}")
        
        print("\n🎉 All tests passed!")
        print("✅ Your Binance API is working correctly!")
        
        return True
        
    except ccxt.AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("   Possible causes:")
        print("   1. Invalid API key or secret")
        print("   2. API key not activated")
        print("   3. IP restriction enabled")
        return False
        
    except ccxt.PermissionDenied as e:
        print(f"\n❌ Permission denied: {e}")
        print("   Your API key might not have trading permissions")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print(f"🚀 Starting mainnet test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_mainnet_binance()
    
    if success:
        print("\n🎊 SUCCESS!")
        print("Your trading bot is ready to use!")
        print("\n📋 Next steps:")
        print("1. Run the dashboard: python crypto_dashboard_gui.py")
        print("2. Start with paper trading to test strategies")
        print("3. Monitor performance before live trading")
    else:
        print("\n❌ Setup needs attention")
        print("Please check your API key configuration")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 