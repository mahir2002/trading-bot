#!/usr/bin/env python3
"""
🔑 Update Binance API Keys
Securely update your Binance API keys in the configuration file
"""

import os
import re
import getpass
from pathlib import Path

def update_binance_keys():
    """Update Binance API keys in config file"""
    print("🔑 Binance API Key Update Tool")
    print("=" * 40)
    print()
    print("ℹ️  This tool will help you update your Binance API keys securely.")
    print("   Your keys will be stored in the config.env file.")
    print()
    
    # Get API keys from user
    print("📝 Please enter your Binance API credentials:")
    print("   (You can get these from: https://www.binance.com/en/my/settings/api-management)")
    print()
    
    api_key = input("🔑 Enter your Binance API Key: ").strip()
    secret_key = getpass.getpass("🔐 Enter your Binance Secret Key: ").strip()
    
    # Validate inputs
    if not api_key or not secret_key:
        print("❌ Both API key and secret key are required!")
        return False
    
    if len(api_key) < 30 or len(secret_key) < 30:
        print("❌ API keys seem too short. Please check your keys.")
        return False
    
    # Ask about trading environment
    print("\n🏛️  Which Binance environment do you want to use?")
    print("   1. Testnet (Paper trading with fake money - RECOMMENDED)")
    print("   2. Mainnet (Real trading with real money)")
    
    env_choice = input("\nEnter choice (1 or 2): ").strip()
    
    if env_choice == "1":
        use_testnet = True
        print("✅ Using Binance Testnet (Paper trading)")
    elif env_choice == "2":
        use_testnet = False
        print("⚠️  Using Binance Mainnet (Real trading)")
        confirm = input("⚠️  Are you sure you want to use real money? (type 'YES' to confirm): ")
        if confirm != "YES":
            print("❌ Cancelled. Using testnet instead.")
            use_testnet = True
    else:
        print("❌ Invalid choice. Using testnet for safety.")
        use_testnet = True
    
    # Update config file
    config_file = Path("config.env")
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False
    
    try:
        # Read current config
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Update API keys
        content = re.sub(r'BINANCE_API_KEY=.*', f'BINANCE_API_KEY={api_key}', content)
        content = re.sub(r'BINANCE_SECRET_KEY=.*', f'BINANCE_SECRET_KEY={secret_key}', content)
        
        # Update testnet setting
        if use_testnet:
            content = re.sub(r'BINANCE_TESTNET=.*', 'BINANCE_TESTNET=true', content)
            content = re.sub(r'TRADING_MODE=.*', 'TRADING_MODE=testnet', content)
        else:
            content = re.sub(r'BINANCE_TESTNET=.*', 'BINANCE_TESTNET=false', content)
            content = re.sub(r'TRADING_MODE=.*', 'TRADING_MODE=live', content)
        
        # Write updated config
        with open(config_file, 'w') as f:
            f.write(content)
        
        print(f"\n✅ Successfully updated {config_file}")
        print(f"   API Key: {api_key[:8]}...")
        print(f"   Secret Key: {secret_key[:8]}...")
        print(f"   Environment: {'Testnet' if use_testnet else 'Mainnet'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating config file: {e}")
        return False

def main():
    """Main function"""
    if update_binance_keys():
        print("\n🎉 API keys updated successfully!")
        print("   You can now test your connection by running:")
        print("   python test_api_keys.py")
    else:
        print("\n❌ Failed to update API keys")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 