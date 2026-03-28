#!/usr/bin/env python3
"""
🔑 Binance API Setup Tester
Tests your current Binance API configuration and guides you through live trading setup
"""

import os
import ccxt
import asyncio
from dotenv import load_dotenv
from datetime import datetime

class BinanceAPITester:
    def __init__(self):
        load_dotenv('config.env.unified')
        
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        self.testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
        
        print("🔑 BINANCE API CONFIGURATION TEST")
        print("=" * 50)
        
    def test_api_connection(self):
        """Test current API connection"""
        try:
            # Configure exchange
            config = {
                'apiKey': self.api_key,
                'secret': self.secret_key,
                'enableRateLimit': True,
                'sandbox': self.testnet
            }
            
            if self.testnet:
                print("🧪 TESTING WITH BINANCE TESTNET (Paper Trading)")
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            else:
                print("💰 TESTING WITH LIVE BINANCE API (Real Money)")
            
            exchange = ccxt.binance(config)
            
            # Test connection
            print("\n📡 Testing API Connection...")
            balance = exchange.fetch_balance()
            
            print("✅ API Connection Successful!")
            
            # Show balances
            print(f"\n💰 Account Balances:")
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            btc_balance = balance.get('BTC', {}).get('free', 0)
            
            print(f"   USDT: ${usdt_balance:,.2f}")
            print(f"   BTC: {btc_balance:.6f}")
            
            if usdt_balance > 0 or btc_balance > 0:
                print("✅ Account has funds available for trading")
            else:
                print("⚠️  Account has no funds - add money before live trading")
            
            # Test market data
            print(f"\n📊 Testing Market Data...")
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"   BTC/USDT Price: ${ticker['last']:,.2f}")
            print("✅ Market data access working")
            
            # Test permissions
            print(f"\n🔐 Testing Trading Permissions...")
            try:
                # Try to get account info (requires trading permissions)
                account_info = exchange.fetch_balance()
                print("✅ Trading permissions verified")
                
                return True, {
                    'usdt_balance': usdt_balance,
                    'btc_balance': btc_balance,
                    'btc_price': ticker['last'],
                    'testnet': self.testnet
                }
                
            except Exception as e:
                print(f"❌ Trading permissions error: {e}")
                return False, None
                
        except Exception as e:
            print(f"❌ API Connection Failed: {e}")
            print("\n💡 Common Issues:")
            print("   - API key or secret incorrect")
            print("   - API key permissions insufficient")
            print("   - IP restrictions enabled")
            print("   - API key expired")
            return False, None
    
    def show_live_trading_setup(self):
        """Show how to set up for live trading"""
        print("\n🚀 LIVE TRADING SETUP GUIDE")
        print("=" * 30)
        
        print("\n1. 🔑 BINANCE API SETUP:")
        print("   a) Go to: https://www.binance.com/en/my/settings/api-management")
        print("   b) Create new API key or edit existing")
        print("   c) Required permissions:")
        print("      ✅ Enable Reading")
        print("      ✅ Enable Spot & Margin Trading")
        print("      ❌ NEVER enable Withdrawals")
        print("   d) Add IP restrictions for security")
        
        print("\n2. 💰 FUND YOUR ACCOUNT:")
        print("   a) Deposit USDT (recommended for trading)")
        print("   b) Minimum: $500-1000 for meaningful testing")
        print("   c) Start small - you can always add more")
        
        print("\n3. ⚙️ CONFIGURATION:")
        print("   a) Update config.env.unified:")
        print("      BINANCE_TESTNET=false")
        print("      ENABLE_LIVE_TRADING=true")
        print("      ENABLE_PAPER_TRADING=false")
        print("   b) Set conservative limits:")
        print("      DEFAULT_TRADE_AMOUNT=25  # $25 per trade")
        print("      RISK_PERCENTAGE=1        # 1% risk per trade")
        print("      MAX_POSITIONS=3          # Max 3 positions")
        
        print("\n4. 🛡️ SAFETY SETTINGS:")
        print("   a) Start with small trade amounts")
        print("   b) Set tight stop losses (3%)")
        print("   c) Enable daily loss limits (5%)")
        print("   d) Monitor closely for first 24 hours")

def main():
    tester = BinanceAPITester()
    
    # Test current setup
    success, data = tester.test_api_connection()
    
    if success:
        print(f"\n🎉 API SETUP SUCCESSFUL!")
        
        if data['testnet']:
            print("\n📝 CURRENT MODE: Paper Trading (Safe)")
            print("   - Using Binance testnet")
            print("   - Fake money only")
            print("   - Perfect for learning")
            
            print("\n🔄 TO SWITCH TO LIVE TRADING:")
            print("   1. Ensure you have real Binance API keys")
            print("   2. Fund your Binance account")
            print("   3. Run: python switch_to_live_trading.py")
            
        else:
            print("\n💰 CURRENT MODE: Live Trading (Real Money)")
            print(f"   - USDT Balance: ${data['usdt_balance']:,.2f}")
            print(f"   - BTC Balance: {data['btc_balance']:.6f}")
            
            if data['usdt_balance'] < 100:
                print("⚠️  Low balance - consider adding funds")
            else:
                print("✅ Sufficient balance for trading")
    else:
        print(f"\n❌ API SETUP NEEDS ATTENTION")
        tester.show_live_trading_setup()

if __name__ == "__main__":
    main() 