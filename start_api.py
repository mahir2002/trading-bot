#!/usr/bin/env python3
"""
AI Trading Bot API Startup Script
This script starts the API server with proper configuration and error handling
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'flask_cors',
        'flask_limiter',
        'jwt',
        'redis',
        'sqlite3',
        'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'jwt':
                import jwt
            elif package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                'flask', 'flask-cors', 'flask-limiter', 'pyjwt', 'redis', 'werkzeug'
            ])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def setup_environment():
    """Setup environment variables and configuration"""
    # Load environment variables
    env_file = Path('.env')
    env_example_file = Path('config.env.example')
    
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Loaded configuration from .env")
    elif env_example_file.exists():
        load_dotenv(env_example_file)
        print("⚠️  Using example configuration. Create .env for production.")
    else:
        print("⚠️  No configuration file found. Using defaults.")
    
    # Set default values if not provided
    os.environ.setdefault('API_HOST', '0.0.0.0')
    os.environ.setdefault('API_PORT', '5001')
    os.environ.setdefault('API_DEBUG', 'False')
    os.environ.setdefault('API_SECRET_KEY', 'dev-secret-key-change-in-production')
    os.environ.setdefault('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    os.environ.setdefault('ADMIN_PASSWORD', 'admin123')
    
    return True

def check_redis_connection():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD') or None,
            socket_connect_timeout=5
        )
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   Rate limiting will use in-memory storage")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'data', 'models']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Created necessary directories")

def display_startup_info():
    """Display startup information"""
    host = os.getenv('API_HOST', '0.0.0.0')
    port = os.getenv('API_PORT', '5001')
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    print("\n" + "=" * 60)
    print("🚀 AI Trading Bot API Server")
    print("=" * 60)
    print(f"📡 Server URL: http://{host}:{port}")
    print(f"🏥 Health Check: http://{host}:{port}/api/health")
    print(f"📚 Documentation: http://{host}:{port}/api/docs")
    print(f"🔧 Debug Mode: {'Enabled' if debug else 'Disabled'}")
    print(f"👤 Default Admin: admin / {os.getenv('ADMIN_PASSWORD', 'admin123')}")
    print("=" * 60)
    print("\n📋 Available Endpoints:")
    print("   Authentication:")
    print("   - POST /api/auth/login")
    print("   - POST /api/auth/register")
    print("\n   Bot Control:")
    print("   - POST /api/bot/start")
    print("   - POST /api/bot/stop")
    print("   - GET  /api/bot/status")
    print("   - POST /api/bot/restart")
    print("\n   Trading Data:")
    print("   - GET  /api/trades")
    print("   - GET  /api/trades/stats")
    print("\n   Market Data:")
    print("   - GET  /api/market/price/<symbol>")
    print("   - GET  /api/market/ohlcv/<symbol>")
    print("   - GET  /api/market/indicators/<symbol>")
    print("\n   Portfolio:")
    print("   - GET  /api/portfolio/balance")
    print("   - GET  /api/portfolio/positions")
    print("\n   Configuration:")
    print("   - GET  /api/config")
    print("   - PUT  /api/config")
    print("\n   Logs & Monitoring:")
    print("   - GET  /api/logs")
    print("   - GET  /api/health")
    print("=" * 60)

def main():
    """Main startup function"""
    print("🤖 Starting AI Trading Bot API Server...")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Exiting.")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed. Exiting.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check Redis (optional)
    check_redis_connection()
    
    # Display startup info
    display_startup_info()
    
    # Import and start the API server
    try:
        print("\n🔄 Initializing API server...")
        
        # Import the API server module
        from api_server import app, init_db
        
        # Initialize database
        print("🗄️  Initializing database...")
        init_db()
        
        # Get configuration
        host = os.getenv('API_HOST', '0.0.0.0')
        port = int(os.getenv('API_PORT', 5001))
        debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
        
        print(f"\n✅ API server starting on {host}:{port}")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 60)
        
        # Start the Flask application
        app.run(host=host, port=port, debug=debug, threaded=True)
        
    except ImportError as e:
        print(f"❌ Failed to import API server: {e}")
        print("   Make sure api_server.py exists and dependencies are installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("🔧 Check the logs for more details")
        sys.exit(1)

if __name__ == '__main__':
    main() 