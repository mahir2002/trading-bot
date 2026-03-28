#!/usr/bin/env python3
"""
🔐 Real API Keys Setup Script
Helps you add your actual Binance and other API keys to the Ultimate Trading System
"""

import os
import re
from pathlib import Path

def add_binance_keys():
    """Add real Binance API keys to the system"""
    print("\n🔐 BINANCE API KEYS SETUP")
    print("=" * 50)
    
    print("\n📝 Please provide your REAL Binance API keys:")
    print("   (You can find these in your Binance account > API Management)")
    print("   ⚠️  Make sure API has 'Enable Spot & Margin Trading' permission")
    
    api_key = input("\n🔑 Enter your Binance API Key: ").strip()
    secret_key = input("🔐 Enter your Binance Secret Key: ").strip()
    
    if not api_key or not secret_key:
        print("❌ API keys cannot be empty!")
        return False
    
    if len(api_key) < 20 or len(secret_key) < 20:
        print("❌ API keys seem too short. Please check and try again.")
        return False
    
    # Update config.env.unified
    config_file = "config.env.unified"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Replace Binance keys
        content = re.sub(r'BINANCE_API_KEY=.*', f'BINANCE_API_KEY={api_key}', content)
        content = re.sub(r'BINANCE_SECRET_KEY=.*', f'BINANCE_SECRET_KEY={secret_key}', content)
        
        with open(config_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {config_file}")
    
    # Update live_trading_config.env
    live_config = "live_trading_config.env"
    if os.path.exists(live_config):
        with open(live_config, 'r') as f:
            content = f.read()
        
        # Replace Binance keys
        content = re.sub(r'BINANCE_API_KEY=.*', f'BINANCE_API_KEY={api_key}', content)
        content = re.sub(r'BINANCE_SECRET_KEY=.*', f'BINANCE_SECRET_KEY={secret_key}', content)
        
        with open(live_config, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {live_config}")
    
    print("\n🎉 Binance API keys added successfully!")
    return True

def verify_existing_keys():
    """Check what API keys are already configured"""
    print("\n🔍 CHECKING EXISTING API KEYS")
    print("=" * 40)
    
    config_file = "config.env.unified"
    if not os.path.exists(config_file):
        print("❌ config.env.unified not found!")
        return
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Check various API keys
    keys_status = {
        'Binance API': 'BINANCE_API_KEY=',
        'Binance Secret': 'BINANCE_SECRET_KEY=',
        'CoinGecko': 'COINGECKO_API_KEY=',
        'CoinMarketCap': 'COINMARKETCAP_API_KEY=',
        'Telegram Bot': 'TELEGRAM_BOT_TOKEN=',
        'Telegram Chat': 'TELEGRAM_CHAT_ID='
    }
    
    for name, key_prefix in keys_status.items():
        lines = [line for line in content.split('\n') if line.startswith(key_prefix)]
        if lines:
            value = lines[0].split('=', 1)[1] if '=' in lines[0] else ''
            if value and not any(placeholder in value.lower() for placeholder in ['your_', 'placeholder', 'example']):
                if 'secret' in name.lower() or 'token' in name.lower():
                    masked_value = value[:8] + '*' * (len(value) - 16) + value[-8:] if len(value) > 16 else '*' * len(value)
                    print(f"✅ {name}: {masked_value}")
                else:
                    print(f"✅ {name}: {value}")
            else:
                print(f"❌ {name}: Not configured (placeholder)")
        else:
            print(f"❌ {name}: Not found")

def main():
    """Main function"""
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║            🔐 REAL API KEYS SETUP SCRIPT 🔐                                  ║")
    print("║                                                                              ║")
    print("║                Add Your Real Trading API Keys                               ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    while True:
        print("\n📋 MENU:")
        print("1. 🔍 Check existing API keys")
        print("2. 🔑 Add Binance API keys")
        print("3. 🧪 Test API keys")
        print("4. 🚀 Start trading system")
        print("5. ❌ Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            verify_existing_keys()
        elif choice == '2':
            if add_binance_keys():
                print("\n💡 TIP: Run option 3 to test your new API keys!")
        elif choice == '3':
            print("\n🧪 Testing API keys...")
            os.system("python test_api_keys.py --all")
        elif choice == '4':
            print("\n🚀 Starting Ultimate Trading System...")
            os.system("python ultimate_all_in_one_trading_system.py web")
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main() 