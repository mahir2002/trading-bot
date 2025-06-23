#!/usr/bin/env python3
"""
🔧 SETUP SCRIPT FOR ULTIMATE UNIFIED AI TRADING BOT
==================================================

This script sets up ALL your API keys and configuration 
for the ONE unified trading bot.

No more multiple models - just ONE comprehensive system!
"""

import os
from dotenv import set_key

def setup_ultimate_bot():
    """Setup the ultimate unified AI trading bot"""
    
    print("🚀 ULTIMATE UNIFIED AI TRADING BOT SETUP")
    print("="*50)
    print("Setting up THE ONLY trading bot you'll ever need!")
    print("This combines ALL features from every system we built.")
    print("="*50)
    
    # Create/update config file
    config_file = "config.env.ultimate"
    
    print("\n🔑 SETTING UP API KEYS")
    print("(Press Enter to skip any you don't have)")
    
    # Exchange APIs
    print("\n📈 EXCHANGE API KEYS:")
    binance_api = input("Binance API Key: ").strip()
    binance_secret = input("Binance Secret Key: ").strip()
    
    coinbase_api = input("Coinbase API Key (optional): ").strip()
    coinbase_secret = input("Coinbase Secret Key (optional): ").strip()
    
    kraken_api = input("Kraken API Key (optional): ").strip()
    kraken_secret = input("Kraken Secret Key (optional): ").strip()
    
    # Social Media APIs
    print("\n📱 SOCIAL MEDIA APIs (for sentiment analysis):")
    twitter_token = input("Twitter Bearer Token (optional): ").strip()
    reddit_client = input("Reddit Client ID (optional): ").strip()
    reddit_secret = input("Reddit Client Secret (optional): ").strip()
    
    # Data APIs
    print("\n📊 DATA APIs:")
    coingecko_api = input("CoinGecko API Key (optional): ").strip()
    coinmarketcap_api = input("CoinMarketCap API Key (optional): ").strip()
    telegram_token = input("Telegram Bot Token (optional): ").strip()
    
    # Trading Settings
    print("\n⚙️ TRADING SETTINGS:")
    
    live_trading = input("Enable LIVE trading? (y/N): ").strip().lower()
    enable_live = live_trading in ['y', 'yes', '1', 'true']
    
    if enable_live:
        print("⚠️ WARNING: LIVE TRADING ENABLED!")
        print("   Real money will be used for trading!")
        confirm = input("Are you absolutely sure? (type 'YES'): ").strip()
        if confirm != 'YES':
            enable_live = False
            print("   Live trading disabled for safety.")
    
    balance = input("Portfolio Balance (default: 100000): ").strip()
    if not balance:
        balance = "100000"
    
    confidence = input("Confidence Threshold 0-1 (default: 0.65): ").strip()
    if not confidence:
        confidence = "0.65"
    
    max_positions = input("Max Positions (default: 10): ").strip()
    if not max_positions:
        max_positions = "10"
    
    # Write configuration
    print(f"\n💾 SAVING CONFIGURATION TO {config_file}...")
    
    # Exchange settings
    if binance_api:
        set_key(config_file, 'BINANCE_API_KEY', binance_api)
    if binance_secret:
        set_key(config_file, 'BINANCE_SECRET_KEY', binance_secret)
    if coinbase_api:
        set_key(config_file, 'COINBASE_API_KEY', coinbase_api)
    if coinbase_secret:
        set_key(config_file, 'COINBASE_SECRET_KEY', coinbase_secret)
    if kraken_api:
        set_key(config_file, 'KRAKEN_API_KEY', kraken_api)
    if kraken_secret:
        set_key(config_file, 'KRAKEN_SECRET_KEY', kraken_secret)
    
    # Social media settings
    if twitter_token:
        set_key(config_file, 'TWITTER_BEARER_TOKEN', twitter_token)
    if reddit_client:
        set_key(config_file, 'REDDIT_CLIENT_ID', reddit_client)
    if reddit_secret:
        set_key(config_file, 'REDDIT_CLIENT_SECRET', reddit_secret)
    
    # Data API settings
    if coingecko_api:
        set_key(config_file, 'COINGECKO_API_KEY', coingecko_api)
    if coinmarketcap_api:
        set_key(config_file, 'COINMARKETCAP_API_KEY', coinmarketcap_api)
    if telegram_token:
        set_key(config_file, 'TELEGRAM_TOKEN', telegram_token)
    
    # Trading settings
    set_key(config_file, 'ENABLE_LIVE_TRADING', str(enable_live).lower())
    set_key(config_file, 'PORTFOLIO_BALANCE', balance)
    set_key(config_file, 'CONFIDENCE_THRESHOLD', confidence)
    set_key(config_file, 'MAX_POSITIONS', max_positions)
    
    # Feature flags (ALL ENABLED by default)
    set_key(config_file, 'ENABLE_ALL_MODELS', 'true')
    set_key(config_file, 'ENABLE_SOCIAL_SENTIMENT', 'true')
    set_key(config_file, 'ENABLE_NEWS_ANALYSIS', 'true')
    set_key(config_file, 'ENABLE_MULTI_EXCHANGE', 'true')
    
    print("✅ Configuration saved!")
    
    # Create run script
    print("\n📝 CREATING RUN SCRIPT...")
    
    run_script = f"""#!/bin/bash
# Ultimate Unified AI Trading Bot Runner
echo "🚀 Starting ULTIMATE UNIFIED AI TRADING BOT"
echo "Loading configuration from {config_file}..."

# Load environment variables
export $(cat {config_file} | grep -v '^#' | xargs)

# Run the ultimate bot
python3 ultimate_unified_ai_trading_bot.py
"""
    
    with open('run_ultimate_bot.sh', 'w') as f:
        f.write(run_script)
    
    os.chmod('run_ultimate_bot.sh', 0o755)
    
    print("✅ Run script created: run_ultimate_bot.sh")
    
    print("\n🎯 SETUP COMPLETE!")
    print("="*50)
    print("Your ULTIMATE UNIFIED AI TRADING BOT is ready!")
    print("")
    print("📁 Files created:")
    print(f"   • {config_file} - Your configuration")
    print(f"   • ultimate_unified_ai_trading_bot.py - THE trading bot")
    print(f"   • run_ultimate_bot.sh - Easy run script")
    print("")
    print("🚀 TO RUN YOUR BOT:")
    print("   ./run_ultimate_bot.sh")
    print("   OR")
    print("   python3 ultimate_unified_ai_trading_bot.py")
    print("")
    print("✨ This is THE ONLY trading bot you need!")
    print("   All 15+ AI models combined into ONE system")
    print("   All features from every system we built")
    print("   One configuration, one bot, all the power!")
    print("="*50)

def show_current_models():
    """Show all the separate models that will be replaced"""
    print("\n📊 MODELS BEING REPLACED BY UNIFIED BOT:")
    print("="*50)
    
    separate_models = [
        "ai_trading_bot_simple.py",
        "advanced_ai_models_framework.py", 
        "advanced_time_series_forecasting.py",
        "comprehensive_backtesting_optimization_system.py",
        "comprehensive_portfolio_risk_system.py",
        "advanced_signal_generation_system.py",
        "dynamic_model_retraining_demo.py",
        "time_series_validation_demo.py",
        "multi_class_trading_classifier.py",
        "unified_master_trading_bot.py",
        "And 6+ more individual models..."
    ]
    
    for i, model in enumerate(separate_models, 1):
        print(f"   {i:2d}. {model}")
    
    print("="*50)
    print("🎯 ALL OF THESE → ONE ultimate_unified_ai_trading_bot.py")
    print("   No more confusion, no more multiple files!")
    print("   Everything you need in ONE place!")

if __name__ == "__main__":
    show_current_models()
    
    print("\n" + "="*60)
    print("🚀 CONSOLIDATING ALL MODELS INTO ONE ULTIMATE BOT")
    print("="*60)
    
    proceed = input("\nReady to set up your ULTIMATE unified bot? (Y/n): ").strip().lower()
    
    if proceed in ['', 'y', 'yes', '1', 'true']:
        setup_ultimate_bot()
    else:
        print("Setup cancelled.") 