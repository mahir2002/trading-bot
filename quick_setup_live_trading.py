#!/usr/bin/env python3
"""
Quick Setup for Live Trading
Interactive script to configure your AI trading bot for live trading
"""

import os
import sys
from pathlib import Path
from dotenv import set_key, load_dotenv

def print_banner():
    """Print setup banner"""
    print("🚀 AI Trading Bot - Live Trading Setup")
    print("=" * 50)
    print("⚠️  IMPORTANT: This sets up REAL trading with REAL money!")
    print("💡 Make sure you understand the risks before proceeding")
    print("=" * 50)

def check_requirements():
    """Check if all requirements are met"""
    print("\n📋 Checking Requirements...")
    
    requirements = {
        "Binance Account": False,
        "API Keys": False,
        "Funded Account": False,
        "Paper Trading Completed": False
    }
    
    # Check if config exists
    config_exists = os.path.exists('config.env')
    if config_exists:
        load_dotenv('config.env')
        if os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_SECRET_KEY'):
            requirements["API Keys"] = True
    
    print("\n📊 Requirements Status:")
    for req, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {req}")
    
    if not all(requirements.values()):
        print("\n⚠️  Some requirements are missing. Please complete them first:")
        print("   1. Create Binance account: https://binance.com")
        print("   2. Get API keys from Account → API Management")
        print("   3. Fund your account with trading balance")
        print("   4. Complete paper trading for 2+ weeks")
        
        continue_anyway = input("\nContinue setup anyway? (y/N): ").lower()
        if continue_anyway != 'y':
            print("Setup cancelled. Complete requirements first.")
            return False
    
    return True

def get_api_credentials():
    """Get API credentials from user"""
    print("\n🔑 API Credentials Setup")
    print("Get your API keys from: https://binance.com → Account → API Management")
    print("\n⚠️  SECURITY REMINDERS:")
    print("   - Only enable 'Enable Reading' and 'Enable Spot Trading'")
    print("   - NEVER enable 'Enable Withdrawals'")
    print("   - Set IP restrictions to your current IP")
    
    api_key = input("\nEnter your Binance API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return None, None
    
    secret_key = input("Enter your Binance Secret Key: ").strip()
    if not secret_key:
        print("❌ Secret Key is required")
        return None, None
    
    # Basic validation
    if len(api_key) < 30 or len(secret_key) < 30:
        print("⚠️  Warning: API keys seem too short. Please verify.")
        confirm = input("Continue anyway? (y/N): ").lower()
        if confirm != 'y':
            return None, None
    
    return api_key, secret_key

def get_trading_configuration():
    """Get trading configuration from user"""
    print("\n⚙️ Trading Configuration")
    print("Configure your trading parameters carefully!")
    
    config = {}
    
    # Trading mode
    print("\n1. Trading Mode:")
    print("   paper = Simulated trading (recommended first)")
    print("   live = Real trading with real money")
    mode = input("Choose trading mode (paper/live) [paper]: ").strip().lower()
    config['TRADING_MODE'] = mode if mode in ['paper', 'live'] else 'paper'
    
    if config['TRADING_MODE'] == 'live':
        print("\n⚠️  LIVE TRADING SELECTED!")
        print("   You will trade with REAL money!")
        confirm = input("Are you sure? Type 'CONFIRM' to continue: ")
        if confirm != 'CONFIRM':
            print("Switching to paper trading for safety")
            config['TRADING_MODE'] = 'paper'
    
    # Trade amount
    print(f"\n2. Trade Amount (per trade in USD):")
    print("   Recommended: $25-50 for beginners")
    try:
        amount = float(input("Enter trade amount [50]: ") or "50")
        config['DEFAULT_TRADE_AMOUNT'] = max(10, min(amount, 1000))  # Limit between $10-1000
    except ValueError:
        config['DEFAULT_TRADE_AMOUNT'] = 50
    
    # Risk percentage
    print(f"\n3. Risk Percentage (% of account per trade):")
    print("   Recommended: 1-2% for conservative trading")
    try:
        risk = float(input("Enter risk percentage [1]: ") or "1")
        config['RISK_PERCENTAGE'] = max(0.5, min(risk, 5))  # Limit between 0.5-5%
    except ValueError:
        config['RISK_PERCENTAGE'] = 1
    
    # Stop loss
    print(f"\n4. Stop Loss Percentage:")
    print("   Recommended: 3-5% to limit losses")
    try:
        stop_loss = float(input("Enter stop loss percentage [3]: ") or "3")
        config['STOP_LOSS_PERCENTAGE'] = max(1, min(stop_loss, 10))  # Limit between 1-10%
    except ValueError:
        config['STOP_LOSS_PERCENTAGE'] = 3
    
    # Take profit
    print(f"\n5. Take Profit Percentage:")
    print("   Recommended: 6-10% to lock in profits")
    try:
        take_profit = float(input("Enter take profit percentage [6]: ") or "6")
        config['TAKE_PROFIT_PERCENTAGE'] = max(2, min(take_profit, 20))  # Limit between 2-20%
    except ValueError:
        config['TAKE_PROFIT_PERCENTAGE'] = 6
    
    return config

def get_notification_setup():
    """Setup notifications"""
    print("\n🔔 Notification Setup (Optional but Recommended)")
    
    setup_telegram = input("Setup Telegram notifications? (Y/n): ").lower()
    if setup_telegram != 'n':
        print("\nTelegram Bot Setup:")
        print("1. Message @BotFather on Telegram")
        print("2. Send: /newbot")
        print("3. Follow instructions to create bot")
        print("4. Save the bot token")
        print("5. Message your bot, then visit:")
        print("   https://api.telegram.org/bot<YourBOTToken>/getUpdates")
        print("6. Get your chat ID from the response")
        
        bot_token = input("\nEnter Telegram Bot Token (or press Enter to skip): ").strip()
        chat_id = input("Enter Telegram Chat ID (or press Enter to skip): ").strip()
        
        return bot_token, chat_id
    
    return "", ""

def create_config_file(api_key, secret_key, trading_config, telegram_config):
    """Create the config.env file"""
    print("\n📝 Creating Configuration File...")
    
    config_file = 'config.env'
    
    # Core configuration
    set_key(config_file, 'BINANCE_API_KEY', api_key)
    set_key(config_file, 'BINANCE_SECRET_KEY', secret_key)
    set_key(config_file, 'BINANCE_TESTNET', 'true' if trading_config['TRADING_MODE'] == 'paper' else 'false')
    
    # Trading configuration
    set_key(config_file, 'TRADING_MODE', trading_config['TRADING_MODE'])
    set_key(config_file, 'DEFAULT_TRADE_AMOUNT', str(trading_config['DEFAULT_TRADE_AMOUNT']))
    set_key(config_file, 'RISK_PERCENTAGE', str(trading_config['RISK_PERCENTAGE']))
    set_key(config_file, 'STOP_LOSS_PERCENTAGE', str(trading_config['STOP_LOSS_PERCENTAGE']))
    set_key(config_file, 'TAKE_PROFIT_PERCENTAGE', str(trading_config['TAKE_PROFIT_PERCENTAGE']))
    
    # Safety settings
    set_key(config_file, 'MAX_DAILY_LOSS_PERCENT', '5')
    set_key(config_file, 'MAX_POSITIONS', '3')
    set_key(config_file, 'POSITION_SIZE_PERCENT', '2')
    set_key(config_file, 'PREDICTION_CONFIDENCE_THRESHOLD', '0.75')
    
    # Telegram notifications
    if telegram_config[0] and telegram_config[1]:
        set_key(config_file, 'TELEGRAM_BOT_TOKEN', telegram_config[0])
        set_key(config_file, 'TELEGRAM_CHAT_ID', telegram_config[1])
        set_key(config_file, 'ENABLE_TELEGRAM_NOTIFICATIONS', 'true')
    
    # Dashboard settings
    set_key(config_file, 'DASHBOARD_HOST', '0.0.0.0')
    set_key(config_file, 'DASHBOARD_PORT', '8050')
    
    print(f"✅ Configuration saved to {config_file}")

def test_configuration():
    """Test the configuration"""
    print("\n🧪 Testing Configuration...")
    
    try:
        # Test API connection
        print("Testing API connection...")
        import ccxt
        from dotenv import load_dotenv
        
        load_dotenv('config.env')
        
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        # Configure exchange
        config = {
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        }
        
        if use_testnet:
            config['sandbox'] = True
            config['urls'] = {
                'api': {
                    'public': 'https://testnet.binance.vision/api',
                    'private': 'https://testnet.binance.vision/api',
                }
            }
        
        exchange = ccxt.binance(config)
        
        # Test connection
        balance = exchange.fetch_balance()
        print("✅ API connection successful!")
        
        if use_testnet:
            print("✅ Using testnet (paper trading)")
        else:
            print("⚠️  Using live API (real trading)")
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        print("\n💡 Common issues:")
        print("   - Check API keys are correct")
        print("   - Ensure API has proper permissions")
        print("   - Check internet connection")
        return False

def show_next_steps(trading_mode):
    """Show next steps"""
    print("\n🚀 Setup Complete! Next Steps:")
    print("=" * 40)
    
    if trading_mode == 'paper':
        print("📊 PAPER TRADING MODE (Recommended)")
        print("1. Start paper trading:")
        print("   python ai_trading_bot_simple.py")
        print("\n2. Monitor performance:")
        print("   python paper_trading_monitor.py")
        print("\n3. View dashboard:")
        print("   Open: http://localhost:8050")
        print("\n4. Run for 2+ weeks, then consider live trading")
        
    else:
        print("💰 LIVE TRADING MODE")
        print("⚠️  You are trading with REAL money!")
        print("\n1. Start with small amounts:")
        print("   python ai_trading_bot_simple.py")
        print("\n2. Monitor CLOSELY:")
        print("   python paper_trading_monitor.py")
        print("\n3. Emergency stop:")
        print("   Press Ctrl+C in bot terminal")
        print("\n4. Dashboard:")
        print("   Open: http://localhost:8050")
    
    print("\n🔒 Security Reminders:")
    print("   - Monitor bot performance daily")
    print("   - Never leave bot unattended for long periods")
    print("   - Have emergency stop procedures ready")
    print("   - Start small and scale up gradually")

def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        return
    
    # Get API credentials
    api_key, secret_key = get_api_credentials()
    if not api_key or not secret_key:
        print("❌ Setup cancelled - API credentials required")
        return
    
    # Get trading configuration
    trading_config = get_trading_configuration()
    
    # Get notification setup
    telegram_config = get_notification_setup()
    
    # Create configuration file
    create_config_file(api_key, secret_key, trading_config, telegram_config)
    
    # Test configuration
    if test_configuration():
        show_next_steps(trading_config['TRADING_MODE'])
        print("\n✅ Setup completed successfully!")
        print("📖 Read setup_live_trading_guide.md for detailed information")
    else:
        print("\n❌ Setup completed but configuration test failed")
        print("Please check your API keys and try again")

if __name__ == "__main__":
    main() 