#!/usr/bin/env python3
"""
🚀 Complete Live Trading Setup
Safe transition from paper trading to live trading with real money
"""

import os
import sys
import time
from pathlib import Path
from dotenv import set_key, load_dotenv
import ccxt

class LiveTradingSetup:
    def __init__(self):
        self.config_file = 'config.env.unified'
        self.project_root = Path.cwd()
        
        print("🚀 COMPLETE LIVE TRADING SETUP")
        print("=" * 50)
        print("This will help you safely transition from paper trading to live trading")
        print("⚠️  WARNING: Live trading involves real money and risk!")
        print("=" * 50)
    
    def check_paper_trading_performance(self):
        """Check if paper trading has been running long enough"""
        print("\n📊 PAPER TRADING PERFORMANCE CHECK")
        print("-" * 40)
        
        # Check if logs exist
        logs_dir = self.project_root / 'logs'
        if not logs_dir.exists():
            print("❌ No trading logs found")
            print("   Run paper trading for at least 1-2 weeks first")
            return False
        
        # Check for recent activity
        log_files = list(logs_dir.glob('*.log'))
        if not log_files:
            print("❌ No log files found")
            print("   Run paper trading for at least 1-2 weeks first")
            return False
        
        print("✅ Paper trading logs found")
        
        # Ask user about performance
        print("\n📈 PAPER TRADING QUESTIONS:")
        print("Answer these questions about your paper trading experience:")
        
        duration = input("1. How long has paper trading been running? (days): ").strip()
        try:
            days = int(duration)
            if days < 7:
                print("⚠️  Recommendation: Run paper trading for at least 7-14 days")
                proceed = input("   Continue anyway? (y/N): ").lower()
                if proceed != 'y':
                    return False
        except ValueError:
            print("⚠️  Please run paper trading for at least 1-2 weeks")
            return False
        
        profitable = input("2. Is paper trading showing profits? (y/N): ").lower()
        if profitable != 'y':
            print("⚠️  Recommendation: Only go live when paper trading is profitable")
            proceed = input("   Continue anyway? (y/N): ").lower()
            if proceed != 'y':
                return False
        
        comfortable = input("3. Are you comfortable with the bot's behavior? (y/N): ").lower()
        if comfortable != 'y':
            print("⚠️  Get comfortable with paper trading first")
            return False
        
        print("✅ Paper trading performance check passed")
        return True
    
    def get_binance_api_keys(self):
        """Get real Binance API keys from user"""
        print("\n🔑 BINANCE API KEYS SETUP")
        print("-" * 30)
        
        print("STEP 1: Create Binance API Keys")
        print("1. Go to: https://www.binance.com/en/my/settings/api-management")
        print("2. Click 'Create API'")
        print("3. Name: 'AI Trading Bot Live'")
        print("4. IMPORTANT PERMISSIONS:")
        print("   ✅ Enable Reading")
        print("   ✅ Enable Spot & Margin Trading")
        print("   ❌ NEVER enable Withdrawals")
        print("   ❌ NEVER enable Futures")
        print("5. Set IP restrictions for security")
        print("6. Copy API Key and Secret Key")
        
        input("\nPress Enter when you have your API keys ready...")
        
        print("\nSTEP 2: Enter Your API Keys")
        api_key = input("Enter your Binance API Key: ").strip()
        if not api_key or len(api_key) < 20:
            print("❌ Invalid API key")
            return None, None
        
        secret_key = input("Enter your Binance Secret Key: ").strip()
        if not secret_key or len(secret_key) < 20:
            print("❌ Invalid secret key")
            return None, None
        
        return api_key, secret_key
    
    def test_api_keys(self, api_key, secret_key):
        """Test the provided API keys"""
        print("\n🧪 TESTING API KEYS...")
        
        try:
            exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'sandbox': False  # Live trading
            })
            
            # Test connection
            balance = exchange.fetch_balance()
            print("✅ API connection successful")
            
            # Check balances
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            btc_balance = balance.get('BTC', {}).get('free', 0)
            
            print(f"💰 Account Balances:")
            print(f"   USDT: ${usdt_balance:,.2f}")
            print(f"   BTC: {btc_balance:.6f}")
            
            total_usdt_value = usdt_balance + (btc_balance * 50000)  # Rough BTC value
            
            if total_usdt_value < 100:
                print("⚠️  Low balance - consider adding funds")
                print("   Recommended minimum: $500-1000")
                
                proceed = input("   Continue with low balance? (y/N): ").lower()
                if proceed != 'y':
                    return False
            else:
                print("✅ Sufficient balance for trading")
            
            return True
            
        except Exception as e:
            print(f"❌ API test failed: {e}")
            print("\n💡 Common issues:")
            print("   - Check API key permissions")
            print("   - Verify IP restrictions")
            print("   - Ensure 'Enable Reading' and 'Enable Spot Trading' are checked")
            return False
    
    def configure_live_trading(self, api_key, secret_key):
        """Configure the system for live trading"""
        print("\n⚙️ CONFIGURING LIVE TRADING...")
        
        # Get trading parameters
        print("\nTRADING PARAMETERS:")
        
        trade_amount = input("Trade amount per position ($25-100 recommended): $").strip()
        try:
            trade_amount = float(trade_amount)
            if trade_amount < 10:
                trade_amount = 25
            elif trade_amount > 500:
                print("⚠️  Large trade amount - starting with $100")
                trade_amount = 100
        except ValueError:
            trade_amount = 25
        
        max_positions = input("Max simultaneous positions (3-5 recommended): ").strip()
        try:
            max_positions = int(max_positions)
            if max_positions < 1:
                max_positions = 3
            elif max_positions > 10:
                print("⚠️  Too many positions - limiting to 5")
                max_positions = 5
        except ValueError:
            max_positions = 3
        
        # Update configuration
        print(f"\n💾 UPDATING CONFIGURATION...")
        
        # API Keys
        set_key(self.config_file, 'BINANCE_API_KEY', api_key)
        set_key(self.config_file, 'BINANCE_SECRET_KEY', secret_key)
        
        # Live Trading Mode
        set_key(self.config_file, 'BINANCE_TESTNET', 'false')
        set_key(self.config_file, 'ENABLE_LIVE_TRADING', 'true')
        set_key(self.config_file, 'ENABLE_PAPER_TRADING', 'false')
        
        # Conservative Trading Parameters
        set_key(self.config_file, 'POSITION_SIZE', str(trade_amount / 1000))  # Convert to percentage
        set_key(self.config_file, 'MAX_POSITIONS', str(max_positions))
        set_key(self.config_file, 'CONFIDENCE_THRESHOLD', '75')  # Higher threshold for live trading
        set_key(self.config_file, 'STOP_LOSS', '0.03')  # 3% stop loss
        set_key(self.config_file, 'TAKE_PROFIT', '0.06')  # 6% take profit
        set_key(self.config_file, 'MAX_DAILY_LOSS', '0.05')  # 5% daily loss limit
        set_key(self.config_file, 'RISK_PER_TRADE', '0.01')  # 1% risk per trade
        
        print("✅ Configuration updated for live trading")
        
        return {
            'trade_amount': trade_amount,
            'max_positions': max_positions
        }
    
    def show_final_instructions(self, config):
        """Show final instructions for live trading"""
        print("\n🎉 LIVE TRADING SETUP COMPLETE!")
        print("=" * 40)
        
        print(f"\n📊 CONFIGURATION SUMMARY:")
        print(f"   Trade Amount: ${config['trade_amount']:.2f} per position")
        print(f"   Max Positions: {config['max_positions']}")
        print(f"   Stop Loss: 3%")
        print(f"   Take Profit: 6%")
        print(f"   Daily Loss Limit: 5%")
        print(f"   Confidence Threshold: 75%")
        
        print(f"\n🚀 TO START LIVE TRADING:")
        print("1. Stop current paper trading bot (Ctrl+C)")
        print("2. Start live trading:")
        print("   python ultimate_all_in_one_trading_system.py web")
        print("3. Monitor dashboard: http://localhost:8200")
        print("4. Watch Telegram notifications closely")
        
        print(f"\n🛡️ SAFETY REMINDERS:")
        print("   • You are now trading with REAL money")
        print("   • Monitor the bot closely for first 24 hours")
        print("   • Emergency stop: Ctrl+C in terminal")
        print("   • Check dashboard frequently")
        print("   • Trust your risk management settings")
        
        print(f"\n📱 MONITORING:")
        print("   • Dashboard: http://localhost:8200")
        print("   • Telegram: Real-time trade notifications")
        print("   • Logs: Check logs/ directory for details")
        
        print(f"\n⚠️  IMPORTANT:")
        print("   • Start small and scale up gradually")
        print("   • Never risk more than you can afford to lose")
        print("   • Keep learning and adjusting")
        print("   • Consider taking profits regularly")

def main():
    setup = LiveTradingSetup()
    
    # Step 1: Check paper trading performance
    if not setup.check_paper_trading_performance():
        print("\n❌ Paper trading validation failed")
        print("   Continue with paper trading until you're ready")
        return
    
    # Step 2: Get API keys
    api_key, secret_key = setup.get_binance_api_keys()
    if not api_key or not secret_key:
        print("\n❌ API keys required for live trading")
        return
    
    # Step 3: Test API keys
    if not setup.test_api_keys(api_key, secret_key):
        print("\n❌ API key validation failed")
        return
    
    # Step 4: Configure live trading
    config = setup.configure_live_trading(api_key, secret_key)
    
    # Step 5: Final confirmation
    print("\n🚨 FINAL CONFIRMATION")
    print("=" * 25)
    print("⚠️  You are about to enable LIVE TRADING with REAL money!")
    print(f"   Trade amount: ${config['trade_amount']:.2f} per position")
    print(f"   Max positions: {config['max_positions']}")
    
    confirm = input("\nType 'START LIVE TRADING' to confirm (case sensitive): ")
    if confirm != 'START LIVE TRADING':
        print("❌ Live trading setup cancelled")
        return
    
    # Step 6: Show final instructions
    setup.show_final_instructions(config)
    
    print("\n🎯 READY TO START LIVE TRADING!")
    print("Run: python ultimate_all_in_one_trading_system.py web")

if __name__ == "__main__":
    main() 