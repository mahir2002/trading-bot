#!/usr/bin/env python3
"""
AI Trading Bot - Main Entry Point
Handles different startup modes for Docker deployment with Redis support
"""

import os
import sys
import argparse
import threading
import time
import signal
from datetime import datetime

def main():
    """Main entry point for the trading bot"""
    parser = argparse.ArgumentParser(description='AI Crypto Trading Bot')
    parser.add_argument('--mode', choices=['bot', 'dashboard', 'both'], 
                       default='both', help='Run mode')
    parser.add_argument('--config-check', action='store_true', 
                       help='Check configuration and exit')
    parser.add_argument('--redis-check', action='store_true',
                       help='Check Redis connection and exit')
    
    args = parser.parse_args()
    
    print("🤖 AI Crypto Trading Bot")
    print("=" * 50)
    print(f"Mode: {args.mode}")
    print(f"Time: {datetime.now()}")
    print(f"Timezone: {os.getenv('TZ', 'System Default')}")
    print("=" * 50)
    
    # Configuration check
    if args.config_check:
        return check_configuration()
    
    # Redis check
    if args.redis_check:
        return check_redis_connection()
    
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Import modules based on mode
    if args.mode in ['bot', 'both']:
        try:
            from ai_trading_bot_simple import AITradingBot
        except ImportError:
            print("❌ Failed to import trading bot")
            return 1
    
    if args.mode in ['dashboard', 'both']:
        try:
            from dashboard import run_dashboard
        except ImportError:
            print("❌ Failed to import dashboard")
            return 1
    
    # Check Redis connection before starting
    if not check_redis_connection():
        print("⚠️  Redis connection failed, continuing without cache...")
    
    # Run based on mode
    if args.mode == 'bot':
        return run_bot_only()
    elif args.mode == 'dashboard':
        return run_dashboard_only()
    elif args.mode == 'both':
        return run_both()
    
    return 0

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def check_redis_connection():
    """Check Redis connection"""
    try:
        import redis
        
        # Try to connect to Redis
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, 
                       socket_connect_timeout=5, socket_timeout=5)
        
        # Test connection
        r.ping()
        print(f"✅ Redis connection successful at {redis_host}:{redis_port}")
        return True
        
    except ImportError:
        print("⚠️  Redis package not installed, skipping Redis features")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def check_configuration():
    """Check if configuration is valid"""
    print("🔍 Checking configuration...")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("💡 Copy config.env.example to .env and configure your settings")
        return 1
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required variables
    required_vars = ['TRADING_MODE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return 1
    
    # Check API keys
    has_binance = os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_SECRET_KEY')
    has_coinbase = os.getenv('COINBASE_API_KEY') and os.getenv('COINBASE_SECRET_KEY')
    
    if not (has_binance or has_coinbase):
        print("⚠️  No exchange API keys configured")
        print("💡 Configure at least one exchange in .env file")
        return 1
    
    # Check Google credentials file
    google_creds = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'google-credentials.json')
    if os.path.exists(google_creds):
        print(f"✅ Google credentials found: {google_creds}")
    else:
        print(f"⚠️  Google credentials not found: {google_creds}")
    
    print("✅ Configuration looks good!")
    return 0

def run_bot_only():
    """Run only the trading bot"""
    print("🚀 Starting trading bot...")
    
    try:
        from ai_trading_bot_simple import main as bot_main
        bot_main()
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def run_dashboard_only():
    """Run only the dashboard"""
    print("🌐 Starting dashboard...")
    
    try:
        from dashboard import run_dashboard
        run_dashboard()
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def run_both():
    """Run both bot and dashboard"""
    print("🚀 Starting both bot and dashboard...")
    
    dashboard_thread = None
    
    try:
        # Start dashboard in a separate thread
        from dashboard import run_dashboard
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Give dashboard time to start
        time.sleep(5)
        print("✅ Dashboard started")
        
        # Start bot in main thread
        from ai_trading_bot_simple import main as bot_main
        bot_main()
        
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Services stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if dashboard_thread and dashboard_thread.is_alive():
            print("🛑 Stopping dashboard thread...")

def health_check():
    """Health check endpoint for container monitoring"""
    try:
        # Check if main components are working
        config_ok = check_configuration() == 0
        redis_ok = check_redis_connection()
        
        status = {
            'status': 'healthy' if config_ok else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'config': 'ok' if config_ok else 'error',
            'redis': 'ok' if redis_ok else 'unavailable',
            'timezone': os.getenv('TZ', 'system')
        }
        
        return status
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    sys.exit(main()) 