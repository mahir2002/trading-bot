#!/usr/bin/env python3
"""
🚨 LIVE TRADING LAUNCHER - REAL MONEY
⚠️ This script will trade with REAL MONEY - Use with extreme caution!

Safety Features:
- API key validation
- Balance verification
- Risk limit checks
- Emergency stop mechanisms
- Real-time monitoring
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
import ccxt
import requests
from dotenv import load_dotenv

class LiveTradingLauncher:
    """🚨 Safe Live Trading Launcher with Multiple Safety Checks"""
    
    def __init__(self):
        """Initialize the live trading launcher"""
        self.config = {}
        self.exchange = None
        self.account_balance = 0.0
        self.safety_checks_passed = False
        
        print("🚨 LIVE TRADING LAUNCHER - REAL MONEY")
        print("=" * 50)
        
    def load_configuration(self) -> bool:
        """Load and validate live trading configuration"""
        try:
            # Load live trading config
            if not os.path.exists('live_trading_config.env'):
                print("❌ live_trading_config.env not found!")
                print("💡 Please create this file with your API keys first")
                return False
            
            load_dotenv('live_trading_config.env')
            
            # Required API keys
            self.config = {
                'binance_api_key': os.getenv('BINANCE_API_KEY'),
                'binance_secret_key': os.getenv('BINANCE_SECRET_KEY'),
                'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'coingecko_api_key': os.getenv('COINGECKO_API_KEY'),
                'initial_balance': float(os.getenv('INITIAL_BALANCE', 1000)),
                'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS_PERCENT', 5)),
                'confidence_threshold': float(os.getenv('CONFIDENCE_THRESHOLD', 65)),
                'max_positions': int(os.getenv('MAX_POSITIONS', 5)),
                'position_size': float(os.getenv('POSITION_SIZE_PERCENT', 10)),
            }
            
            print("✅ Configuration loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return False
    
    def validate_api_keys(self) -> bool:
        """Validate API keys and exchange connection"""
        try:
            print("\n🔐 Validating API Keys...")
            
            # Check if API keys are set
            if not self.config['binance_api_key'] or self.config['binance_api_key'] == 'your_real_binance_api_key_here':
                print("❌ Binance API key not set!")
                print("💡 Please update live_trading_config.env with your real API keys")
                return False
            
            if not self.config['binance_secret_key'] or self.config['binance_secret_key'] == 'your_real_binance_secret_key_here':
                print("❌ Binance secret key not set!")
                return False
            
            # Test Binance connection
            self.exchange = ccxt.binance({
                'apiKey': self.config['binance_api_key'],
                'secret': self.config['binance_secret_key'],
                'sandbox': False,  # LIVE TRADING
                'enableRateLimit': True,
            })
            
            # Test API connection
            balance = self.exchange.fetch_balance()
            self.account_balance = balance['USDT']['free'] if 'USDT' in balance else 0.0
            
            print(f"✅ Binance API connection successful")
            print(f"💰 Account USDT Balance: ${self.account_balance:.2f}")
            
            # Test Telegram
            if self.config['telegram_token']:
                url = f"https://api.telegram.org/bot{self.config['telegram_token']}/getMe"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print("✅ Telegram bot connection successful")
                else:
                    print("⚠️ Telegram connection failed (notifications disabled)")
            
            return True
            
        except Exception as e:
            print(f"❌ API validation failed: {e}")
            return False
    
    def perform_safety_checks(self) -> bool:
        """Perform comprehensive safety checks"""
        try:
            print("\n🛡️ Performing Safety Checks...")
            
            # Check 1: Minimum balance
            min_balance = self.config['initial_balance']
            if self.account_balance < min_balance:
                print(f"❌ Insufficient balance: ${self.account_balance:.2f} < ${min_balance:.2f}")
                return False
            print(f"✅ Balance check passed: ${self.account_balance:.2f}")
            
            # Check 2: Risk limits
            max_risk = self.account_balance * (self.config['max_daily_loss'] / 100)
            print(f"✅ Maximum daily risk: ${max_risk:.2f} ({self.config['max_daily_loss']}%)")
            
            # Check 3: Position sizing
            position_value = self.account_balance * (self.config['position_size'] / 100)
            print(f"✅ Position size: ${position_value:.2f} ({self.config['position_size']}%)")
            
            # Check 4: Configuration validation
            if self.config['confidence_threshold'] < 60:
                print("⚠️ Warning: Confidence threshold is low for live trading")
                response = input("Continue anyway? (yes/no): ").lower()
                if response != 'yes':
                    return False
            
            print("✅ All safety checks passed")
            return True
            
        except Exception as e:
            print(f"❌ Safety check failed: {e}")
            return False
    
    def send_telegram_alert(self, message: str) -> None:
        """Send Telegram alert"""
        try:
            if self.config['telegram_token'] and self.config['telegram_chat_id']:
                url = f"https://api.telegram.org/bot{self.config['telegram_token']}/sendMessage"
                data = {
                    'chat_id': self.config['telegram_chat_id'],
                    'text': f"🚨 LIVE TRADING ALERT\n\n{message}",
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"⚠️ Telegram alert failed: {e}")
    
    def final_confirmation(self) -> bool:
        """Final confirmation before starting live trading"""
        print("\n" + "="*60)
        print("🚨 FINAL CONFIRMATION - LIVE TRADING WITH REAL MONEY")
        print("="*60)
        print(f"💰 Account Balance: ${self.account_balance:.2f}")
        print(f"🎯 Max Positions: {self.config['max_positions']}")
        print(f"💵 Position Size: {self.config['position_size']}% (${self.account_balance * self.config['position_size'] / 100:.2f})")
        print(f"🛡️ Daily Loss Limit: {self.config['max_daily_loss']}% (${self.account_balance * self.config['max_daily_loss'] / 100:.2f})")
        print(f"🎯 Confidence Threshold: {self.config['confidence_threshold']}%")
        print("="*60)
        
        print("\n⚠️ WARNING: This will trade with REAL MONEY!")
        print("⚠️ You could lose money if the bot makes bad trades!")
        print("⚠️ Only proceed if you understand the risks!")
        
        print("\nType 'START LIVE TRADING' to confirm (case sensitive):")
        confirmation = input("Confirmation: ")
        
        if confirmation == "START LIVE TRADING":
            print("✅ Live trading confirmed!")
            return True
        else:
            print("❌ Live trading cancelled")
            return False
    
    def start_live_trading(self) -> None:
        """Start the live trading bot"""
        try:
            print("\n🚀 Starting Live Trading Bot...")
            
            # Send startup notification
            startup_message = f"""
🚀 <b>LIVE TRADING STARTED</b>
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 Balance: ${self.account_balance:.2f}
🎯 Max Positions: {self.config['max_positions']}
🛡️ Daily Loss Limit: {self.config['max_daily_loss']}%
📊 Confidence Threshold: {self.config['confidence_threshold']}%
"""
            self.send_telegram_alert(startup_message)
            
            # Start the unified bot in live mode
            cmd = [
                'python', 'unified_master_trading_bot.py',
                '--mode', 'live',
                '--config', 'live_trading_config.env',
                '--telegram',
                '--premium-data',
                '--verbose'
            ]
            
            print("🎯 Launching unified master trading bot...")
            print("📝 Command:", ' '.join(cmd))
            
            # Set environment variables for live trading
            env = os.environ.copy()
            env.update({
                'ENABLE_LIVE_TRADING': 'true',
                'BINANCE_API_KEY': self.config['binance_api_key'],
                'BINANCE_SECRET_KEY': self.config['binance_secret_key'],
                'BINANCE_TESTNET': 'false'
            })
            
            # Start the bot
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env
            )
            
            print(f"✅ Live trading bot started (PID: {process.pid})")
            print("📋 Monitoring output...")
            
            # Monitor the bot output
            for line in process.stdout:
                print(line.strip())
                
                # Check for critical errors
                if "EMERGENCY STOP" in line or "CRITICAL ERROR" in line:
                    self.send_telegram_alert(f"🚨 CRITICAL: {line.strip()}")
                    break
            
        except KeyboardInterrupt:
            print("\n🛑 Live trading stopped by user")
            self.send_telegram_alert("🛑 Live trading stopped by user")
        except Exception as e:
            error_msg = f"❌ Live trading error: {e}"
            print(error_msg)
            self.send_telegram_alert(error_msg)
    
    def run(self) -> None:
        """Main launcher execution"""
        try:
            print("🔧 Step 1: Loading configuration...")
            if not self.load_configuration():
                return
            
            print("🔧 Step 2: Validating API keys...")
            if not self.validate_api_keys():
                return
            
            print("🔧 Step 3: Performing safety checks...")
            if not self.perform_safety_checks():
                return
            
            print("🔧 Step 4: Final confirmation...")
            if not self.final_confirmation():
                return
            
            print("🔧 Step 5: Starting live trading...")
            self.start_live_trading()
            
        except Exception as e:
            print(f"❌ Launcher error: {e}")

def main():
    """Main entry point"""
    try:
        launcher = LiveTradingLauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n🛑 Launcher stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main() 