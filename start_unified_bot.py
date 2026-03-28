#!/usr/bin/env python3
"""
🚀 UNIFIED MASTER TRADING BOT STARTUP SCRIPT
Comprehensive launcher for the ultimate trading bot system
"""

import os
import sys
import argparse
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('startup.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger = logging.getLogger(__name__)
    
    required_packages = [
        'ccxt', 'pandas', 'numpy', 'ta', 'sklearn', 
        'requests', 'dotenv', 'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} - MISSING")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    logger.info("✅ All dependencies satisfied")
    return True

def check_config_files():
    """Check if configuration files exist"""
    logger = logging.getLogger(__name__)
    
    config_files = [
        'config.env.unified',
        'unified_master_trading_bot.py'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            logger.info(f"✅ {config_file} - Found")
        else:
            logger.error(f"❌ {config_file} - Missing")
            return False
    
    logger.info("✅ All configuration files found")
    return True

def create_directories():
    """Create necessary directories"""
    logger = logging.getLogger(__name__)
    
    directories = [
        'models',
        'logs',
        'data',
        'backtest_results',
        'reports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"✅ Directory created/verified: {directory}")

def display_banner():
    """Display startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║          🚀 UNIFIED MASTER AI TRADING BOT 🚀                 ║
    ║                                                              ║
    ║              The Ultimate Trading Bot System                 ║
    ║          Combining ALL 20+ Bots Into One Platform           ║
    ║                                                              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  Features:                                                   ║
    ║  • 50+ Trading Pairs                                         ║
    ║  • Multi-Exchange Support                                    ║
    ║  • Advanced AI Predictions                                   ║
    ║  • Comprehensive Risk Management                             ║
    ║  • Real-time Telegram Notifications                         ║
    ║  • Portfolio Optimization                                    ║
    ║  • Sentiment Analysis                                        ║
    ║  • DEX Trading Support                                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description='Unified Master Trading Bot Launcher')
    parser.add_argument('--mode', choices=['live', 'paper', 'backtest'], 
                       default='paper', help='Trading mode')
    parser.add_argument('--config', default='config.env.unified', 
                       help='Configuration file path')
    parser.add_argument('--check-only', action='store_true', 
                       help='Only check dependencies and configuration')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Display banner
    display_banner()
    
    logger.info("🔄 Starting Unified Master Trading Bot...")
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Config: {args.config}")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        sys.exit(1)
    
    # Check configuration files
    if not check_config_files():
        logger.error("❌ Configuration check failed")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    if args.check_only:
        logger.info("✅ All checks passed - System ready!")
        return
    
    # Set environment variables
    os.environ['TRADING_MODE'] = args.mode
    os.environ['CONFIG_FILE'] = args.config
    
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Import and run the bot
    try:
        logger.info("🚀 Launching Unified Master Trading Bot...")
        
        # Import the bot
        from unified_master_trading_bot import main as bot_main
        
        # Run the bot
        import asyncio
        asyncio.run(bot_main())
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 