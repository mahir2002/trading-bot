#!/usr/bin/env python3
"""
Switch to Live Trading
Convert your current working configuration to live trading
"""

import os
from dotenv import set_key, load_dotenv

def switch_to_live_trading():
    """Switch current configuration to live trading"""
    print("🔄 Switching to Live Trading Configuration")
    print("=" * 50)
    
    config_file = 'config.env'
    
    # Load current config
    load_dotenv(config_file)
    
    print("\n📋 Current Status:")
    current_mode = os.getenv('TRADING_MODE', 'paper')
    current_testnet = os.getenv('BINANCE_TESTNET', 'true')
    print(f"   Trading Mode: {current_mode}")
    print(f"   Using Testnet: {current_testnet}")
    
    # Check if API keys are placeholder
    api_key = os.getenv('BINANCE_API_KEY', '')
    if 'your_binance_api_key_here' in api_key or len(api_key) < 20:
        print("\n🔑 STEP 1: Update API Keys")
        print("You need to replace the placeholder API keys with your REAL Binance API keys:")
        print("   1. Go to: https://binance.com → Account → API Management")
        print("   2. Create API key with 'Enable Reading' and 'Enable Spot Trading'")
        print("   3. NEVER enable 'Enable Withdrawals'")
        
        new_api_key = input("\nEnter your REAL Binance API Key: ").strip()
        new_secret_key = input("Enter your REAL Binance Secret Key: ").strip()
        
        if new_api_key and new_secret_key:
            set_key(config_file, 'BINANCE_API_KEY', new_api_key)
            set_key(config_file, 'BINANCE_SECRET_KEY', new_secret_key)
            print("✅ API keys updated")
        else:
            print("❌ API keys required for live trading")
            return False
    else:
        print("✅ API keys are already configured")
    
    print("\n⚙️ STEP 2: Switch Trading Mode")
    
    # Confirm live trading
    print("⚠️  WARNING: You are about to switch to LIVE TRADING with REAL money!")
    confirm = input("Type 'LIVE' to confirm live trading: ")
    if confirm != 'LIVE':
        print("❌ Live trading cancelled")
        return False
    
    # Update trading settings
    changes = {
        'TRADING_MODE': 'live',
        'BINANCE_TESTNET': 'false',
        'DEFAULT_TRADE_AMOUNT': '25',  # Start small
        'RISK_PERCENTAGE': '1.0',      # Conservative
        'PREDICTION_CONFIDENCE_THRESHOLD': '0.75',  # Higher threshold
        'ENABLE_PAPER_TRADING': 'false',
        'ENABLE_REAL_TRADING': 'true'
    }
    
    print("\n📝 Applying live trading configuration...")
    for key, value in changes.items():
        set_key(config_file, key, value)
        print(f"   {key} = {value}")
    
    print("\n🛡️ STEP 3: Risk Management Settings")
    
    # Additional safety settings
    safety_settings = {
        'MAX_DAILY_LOSS_PERCENT': '5',    # Stop at 5% daily loss
        'MAX_POSITIONS': '3',             # Limit positions
        'STOP_LOSS_PERCENT': '3',         # 3% stop loss
        'TAKE_PROFIT_PERCENT': '6'        # 6% take profit
    }
    
    for key, value in safety_settings.items():
        set_key(config_file, key, value)
        print(f"   {key} = {value}")
    
    print("\n✅ LIVE TRADING CONFIGURATION COMPLETE!")
    print("\n🚀 Next Steps:")
    print("   1. Stop your current bot (Ctrl+C)")
    print("   2. Restart: python ai_trading_bot_simple.py")
    print("   3. Monitor CLOSELY in dashboard: http://localhost:8050")
    print("   4. Watch Telegram notifications")
    
    print("\n⚠️  IMPORTANT REMINDERS:")
    print("   • You're now trading with REAL money")
    print("   • Start with small amounts ($25 per trade)")
    print("   • Monitor the bot closely for the first 24 hours")
    print("   • Have emergency stop procedures ready")
    
    return True

def test_live_config():
    """Test the live trading configuration"""
    print("\n🧪 Testing Live Trading Configuration...")
    
    try:
        import ccxt
        from dotenv import load_dotenv
        
        load_dotenv('config.env')
        
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        use_testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
        
        if not api_key or not secret_key:
            print("❌ API keys not found")
            return False
        
        # Test connection
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'sandbox': use_testnet
        })
        
        # Test API call
        balance = exchange.fetch_balance()
        print("✅ Live API connection successful!")
        
        if use_testnet:
            print("⚠️  Still using testnet - check BINANCE_TESTNET setting")
        else:
            print("✅ Connected to LIVE Binance API")
            
        # Show account info
        print(f"   Account has {len(balance['info']['balances'])} assets")
        
        # Show non-zero balances
        total_value = 0
        for asset in balance['info']['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            if free > 0 or locked > 0:
                print(f"   {asset['asset']}: {free} (free) + {locked} (locked)")
                if asset['asset'] == 'USDT':
                    total_value += free + locked
        
        if total_value > 0:
            print(f"   💰 Available USDT: ${total_value:.2f}")
        else:
            print("   ⚠️  No USDT balance found - you may need to deposit funds")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    if switch_to_live_trading():
        test_live_config() 