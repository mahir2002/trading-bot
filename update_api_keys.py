#!/usr/bin/env python3
"""
API Key Update Script
Safely update your Binance API keys in the .env file
"""

import os
import re

def update_env_file():
    """Update .env file with new API keys"""
    
    print("🔧 Binance API Key Update Tool")
    print("=" * 50)
    print("⚠️  SECURITY NOTICE:")
    print("   - Never share your API keys publicly")
    print("   - Use IP restrictions for security")
    print("   - Disable withdrawals unless needed")
    print("=" * 50)
    
    # Get current API keys
    print("\n📝 Enter your NEW Binance API keys:")
    print("(Get them from: https://www.binance.com/en/my/settings/api-management)")
    
    api_key = input("\n🔑 Binance API Key: ").strip()
    secret_key = input("🔐 Binance Secret Key: ").strip()
    
    if not api_key or not secret_key:
        print("❌ Both API key and secret key are required!")
        return False
    
    # Validate key format (basic check)
    if len(api_key) < 50 or len(secret_key) < 50:
        print("⚠️  Warning: API keys seem too short. Please double-check.")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            return False
    
    # Read current .env file
    try:
        with open('.env', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ .env file not found. Creating from template...")
        if os.path.exists('config.env.example'):
            with open('config.env.example', 'r') as f:
                content = f.read()
        else:
            print("❌ No template found. Please create .env file manually.")
            return False
    
    # Update API keys
    content = re.sub(r'BINANCE_API_KEY=.*', f'BINANCE_API_KEY={api_key}', content)
    content = re.sub(r'BINANCE_SECRET_KEY=.*', f'BINANCE_SECRET_KEY={secret_key}', content)
    
    # Optimize settings for higher returns
    optimizations = {
        'TRADING_MODE': 'paper',
        'DEFAULT_TRADE_AMOUNT': '100',
        'RISK_PERCENTAGE': '2',
        'PREDICTION_CONFIDENCE_THRESHOLD': '55',  # Lower for more trades
        'TRADING_PAIRS': 'BTC/USDT,ETH/USDT,BNB/USDT'
    }
    
    for key, value in optimizations.items():
        if key in content:
            content = re.sub(f'{key}=.*', f'{key}={value}', content)
        else:
            content += f'\n{key}={value}'
    
    # Write updated .env file
    try:
        with open('.env', 'w') as f:
            f.write(content)
        
        print("\n✅ .env file updated successfully!")
        print("\n📊 Optimized settings applied:")
        for key, value in optimizations.items():
            print(f"   {key}={value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        return False

def test_api_connection():
    """Test the API connection"""
    print("\n🧪 Testing API connection...")
    
    try:
        import ccxt
        from dotenv import load_dotenv
        
        # Load new environment variables
        load_dotenv()
        
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            print("❌ API keys not found in .env file")
            return False
        
        # Test connection
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,  # Use live API for testing
            'enableRateLimit': True,
        })
        
        # Test with a simple API call
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"✅ API connection successful!")
        print(f"   BTC/USDT Price: ${ticker['last']:.2f}")
        
        # Test account access
        try:
            balance = exchange.fetch_balance()
            print("✅ Account access successful!")
            
            # Show available balances
            for currency, amount in balance['free'].items():
                if amount > 0:
                    print(f"   {currency}: {amount}")
                    
        except Exception as e:
            print(f"⚠️  Account access limited: {e}")
            print("   This is normal for new API keys or restricted permissions")
        
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("\n💡 Common issues:")
        print("   - Check if API keys are correct")
        print("   - Ensure API key has 'Enable Reading' permission")
        print("   - Check if IP restrictions are set correctly")
        print("   - Wait a few minutes for new keys to activate")
        return False

def main():
    """Main function"""
    
    # Update API keys
    if update_env_file():
        
        # Test connection
        test_connection = input("\n🧪 Test API connection now? (y/n): ").lower()
        if test_connection == 'y':
            test_api_connection()
        
        print("\n🚀 Next steps:")
        print("   1. Test with paper trading: python3 ai_trading_bot_simple.py")
        print("   2. Run optimized backtest: python3 optimized_trading_bot.py")
        print("   3. When ready for live trading: Set TRADING_MODE=live in .env")
        
        print("\n⚠️  IMPORTANT:")
        print("   - Start with paper trading to test")
        print("   - Use small amounts when going live")
        print("   - Monitor performance closely")
    
    else:
        print("\n❌ Failed to update API keys. Please try again.")

if __name__ == "__main__":
    main() 