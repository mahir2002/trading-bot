#!/usr/bin/env python3
"""
🚀 Live Trading Setup Assistant
Helps configure your trading bot for live trading
"""

import os
import sys
from pathlib import Path

def print_header():
    print("🚀 LIVE TRADING SETUP ASSISTANT")
    print("=" * 50)
    print("This script will help you configure your trading bot for live trading.")
    print("⚠️  WARNING: Live trading involves real money and risk!")
    print("=" * 50)

def check_current_config():
    """Check current configuration status"""
    print("\n📋 CURRENT CONFIGURATION STATUS:")
    print("-" * 30)
    
    config_file = Path("config.env")
    if not config_file.exists():
        print("❌ config.env file not found!")
        return False
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Check API keys
    has_binance = "your_binance_api_key_here" not in content
    has_coingecko = "your_coingecko_api_key_here" not in content
    
    print(f"🔑 Binance API Key: {'✅ Configured' if has_binance else '❌ Not configured'}")
    print(f"🦎 CoinGecko API Key: {'✅ Configured' if has_coingecko else '❌ Not configured'}")
    
    # Check trading mode
    if "ENABLE_REAL_TRADING=true" in content:
        print("⚠️  LIVE TRADING: ENABLED")
    elif "ENABLE_PAPER_TRADING=true" in content:
        print("✅ PAPER TRADING: ENABLED (Safe)")
    
    return True

def show_requirements():
    """Show what's needed for live trading"""
    print("\n🎯 REQUIREMENTS FOR LIVE TRADING:")
    print("-" * 35)
    
    requirements = [
        "🔑 Exchange API Keys (Binance recommended)",
        "💰 Trading capital (start small!)",
        "📱 Notification setup (Telegram)",
        "🛡️ Risk management settings",
        "📊 Strategy backtesting results",
        "🧠 Understanding of trading risks"
    ]
    
    for req in requirements:
        print(f"  {req}")

def show_api_setup():
    """Show how to get API keys"""
    print("\n🔑 HOW TO GET API KEYS:")
    print("-" * 25)
    
    print("\n📈 BINANCE API SETUP:")
    print("1. Go to https://www.binance.com/")
    print("2. Create account and complete verification")
    print("3. Go to Account → API Management")
    print("4. Create new API key with these permissions:")
    print("   ✅ Enable Reading")
    print("   ✅ Enable Spot & Margin Trading")
    print("   ❌ Enable Futures (not needed)")
    print("   ❌ Enable Withdrawals (not recommended)")
    print("5. Copy API Key and Secret Key")
    print("6. Add to config.env file")
    
    print("\n🧪 TESTNET FIRST (RECOMMENDED):")
    print("1. Go to https://testnet.binance.vision/")
    print("2. Login with GitHub")
    print("3. Generate testnet API keys")
    print("4. Test with fake money first!")

def show_config_example():
    """Show configuration example"""
    print("\n⚙️  CONFIGURATION EXAMPLE:")
    print("-" * 25)
    
    config_example = """
# Exchange API Keys (REAL KEYS - KEEP SECURE!)
BINANCE_API_KEY=your_real_api_key_here
BINANCE_SECRET_KEY=your_real_secret_key_here

# Trading Mode
ENABLE_PAPER_TRADING=false    # Disable paper trading
ENABLE_REAL_TRADING=true      # Enable live trading
BINANCE_TESTNET=false         # Use real Binance (not testnet)

# Risk Management (IMPORTANT!)
INITIAL_BALANCE=1000          # Start small!
MAX_POSITIONS=5               # Limit positions
POSITION_SIZE_PERCENT=2       # Only 2% per trade
STOP_LOSS_PERCENT=3           # 3% stop loss
MAX_DAILY_LOSS_PERCENT=5      # Max 5% daily loss

# Notifications
ENABLE_TELEGRAM_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
"""
    
    print(config_example)

def show_safety_checklist():
    """Show safety checklist"""
    print("\n🛡️  SAFETY CHECKLIST:")
    print("-" * 20)
    
    checklist = [
        "✅ Start with testnet/paper trading",
        "✅ Use small amounts initially",
        "✅ Set strict stop losses",
        "✅ Monitor trades closely",
        "✅ Have notifications enabled",
        "✅ Understand the risks",
        "✅ Never invest more than you can lose",
        "✅ Test strategies thoroughly",
        "✅ Keep API keys secure",
        "✅ Regular monitoring and adjustments"
    ]
    
    for item in checklist:
        print(f"  {item}")

def show_next_steps():
    """Show next steps"""
    print("\n🚀 NEXT STEPS:")
    print("-" * 15)
    
    steps = [
        "1. 🧪 Test with paper trading first",
        "2. 🔑 Get Binance testnet API keys",
        "3. ⚙️  Update config.env with testnet keys",
        "4. 🎯 Run bot in testnet mode",
        "5. 📊 Monitor performance for 1-2 weeks",
        "6. 🔑 Get real API keys when confident",
        "7. 💰 Start with small real money amounts",
        "8. 📈 Scale up gradually as you gain confidence"
    ]
    
    for step in steps:
        print(f"  {step}")

def main():
    """Main setup assistant"""
    print_header()
    
    if not check_current_config():
        return
    
    show_requirements()
    show_api_setup()
    show_config_example()
    show_safety_checklist()
    show_next_steps()
    
    print("\n" + "=" * 50)
    print("🎯 REMEMBER: Start small, test thoroughly, manage risk!")
    print("💡 Your current setup is perfect for learning and testing.")
    print("🚀 When ready, follow the steps above for live trading.")
    print("=" * 50)

if __name__ == "__main__":
    main() 