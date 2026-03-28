#!/usr/bin/env python3
"""
🔑 Simple Binance API Key Update
Update your Binance API keys with regular input
"""

import os
import re
from pathlib import Path

def update_api_keys():
    """Update API keys with regular input"""
    print("🔑 Simple Binance API Key Update")
    print("=" * 40)
    print()
    print("📝 Please enter your Binance API credentials:")
    print("   (Keys will be shown as you type - make sure no one is looking)")
    print()
    
    # Get API keys with regular input
    api_key = input("🔑 Enter your Binance API Key: ").strip()
    print()
    secret_key = input("🔐 Enter your Binance Secret Key: ").strip()
    print()
    
    # Validate inputs
    if not api_key or not secret_key:
        print("❌ Both API key and secret key are required!")
        return False
    
    if len(api_key) < 30 or len(secret_key) < 30:
        print("❌ Keys seem too short. Please check your keys.")
        print(f"   API Key length: {len(api_key)} characters")
        print(f"   Secret Key length: {len(secret_key)} characters")
        return False
    
    # Show what we got
    print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"✅ Secret Key: {secret_key[:8]}...{secret_key[-8:]}")
    print(f"📏 API Key length: {len(api_key)} characters")
    print(f"📏 Secret Key length: {len(secret_key)} characters")
    
    # Ask for confirmation
    confirm = input("\n❓ Do these keys look correct? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled. Please try again.")
        return False
    
    # Ask about environment
    print("\n🏛️  Trading Environment:")
    print("   1. Testnet (Paper trading - RECOMMENDED for beginners)")
    print("   2. Mainnet (Real trading - Use only if experienced)")
    
    env_choice = input("\nEnter choice (1 or 2): ").strip()
    
    if env_choice == "1":
        use_testnet = True
        print("✅ Using Testnet (Paper trading)")
    elif env_choice == "2":
        use_testnet = False
        print("⚠️  Using Mainnet (Real trading)")
        print("⚠️  WARNING: This will use real money!")
    else:
        print("❌ Invalid choice. Using Testnet for safety.")
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
        
        # Update environment settings
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
        print(f"   API Key: {api_key[:8]}...{api_key[-8:]}")
        print(f"   Secret Key: {secret_key[:8]}...{secret_key[-8:]}")
        print(f"   Environment: {'Testnet' if use_testnet else 'Mainnet'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating config file: {e}")
        return False

def main():
    """Main function"""
    if update_api_keys():
        print("\n🎉 API keys updated successfully!")
        print("\n📋 Next steps:")
        print("   1. Test your connection: python test_api_keys.py")
        print("   2. Run the dashboard: python crypto_dashboard_gui.py")
    else:
        print("\n❌ Failed to update API keys")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 