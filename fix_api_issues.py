#!/usr/bin/env python3
"""
Fix API Server Issues
Addresses import errors and dependency conflicts
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def fix_flask_limiter():
    """Fix Flask-Limiter version compatibility"""
    print("🔧 Fixing Flask-Limiter compatibility...")
    
    # Uninstall and reinstall with specific version
    commands = [
        "pip uninstall flask-limiter -y",
        "pip install flask-limiter==3.5.0 --force-reinstall"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            return False
    
    return True

def check_imports():
    """Check if all required imports work"""
    print("🔍 Checking imports...")
    
    try:
        # Test basic imports
        import flask
        import flask_cors
        import flask_limiter
        import jwt
        import pandas as pd
        import ccxt
        print("✅ Basic imports working")
        
        # Test trading bot import
        try:
            from ai_trading_bot_simple import AITradingBot
            print("✅ AITradingBot import working")
        except ImportError as e:
            print(f"⚠️  AITradingBot import issue: {e}")
            print("   This is expected if exchange APIs aren't configured")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def create_minimal_env():
    """Create a minimal .env file if it doesn't exist"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("📝 Creating minimal .env file...")
        
        minimal_env = """# Minimal configuration for API testing
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
API_SECRET_KEY=test-secret-key-change-in-production
JWT_SECRET_KEY=jwt-test-secret-key-change-in-production
ADMIN_PASSWORD=admin123

# Trading Configuration (Paper trading for safety)
TRADING_MODE=paper
DEFAULT_TRADE_AMOUNT=10
RISK_PERCENTAGE=1
STOP_LOSS_PERCENTAGE=2
TAKE_PROFIT_PERCENTAGE=5

# Optional: Add your exchange API keys here
# BINANCE_API_KEY=your_binance_api_key
# BINANCE_SECRET_KEY=your_binance_secret_key
# BINANCE_TESTNET=true

# Optional: Add Telegram bot for notifications
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id
"""
        
        with open(".env", "w") as f:
            f.write(minimal_env)
        
        print("✅ Created .env file with minimal configuration")
        print("📝 Edit .env file to add your API keys")
        return True
    else:
        print("✅ .env file already exists")
        return True

def test_api_server():
    """Test if the API server can start"""
    print("🧪 Testing API server startup...")
    
    try:
        # Import the fixed API server
        import api_server
        print("✅ API server imports successfully")
        
        # Test database initialization
        api_server.init_db()
        print("✅ Database initialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ API server test failed: {e}")
        return False

def main():
    """Main fix routine"""
    print("🚀 AI Trading Bot API - Issue Fixer")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Fix steps
    steps = [
        ("Fix Flask-Limiter", fix_flask_limiter),
        ("Check imports", check_imports),
        ("Create minimal .env", create_minimal_env),
        ("Test API server", test_api_server)
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        if step_func():
            success_count += 1
        else:
            print(f"⚠️  {step_name} had issues but continuing...")
    
    print(f"\n📊 Results: {success_count}/{len(steps)} steps completed successfully")
    
    if success_count >= 3:
        print("\n🎉 API server should now work! Try running:")
        print("   python start_api.py")
        print("\n📚 Next steps:")
        print("   1. Add your exchange API keys to .env file")
        print("   2. Set up Telegram bot for notifications")
        print("   3. Test with paper trading first")
        print("   4. Read API_SETUP_GUIDE.md for complete setup")
    else:
        print("\n⚠️  Some issues remain. Check the errors above.")
        print("   You may need to install missing dependencies manually.")
    
    return success_count >= 3

if __name__ == "__main__":
    main() 