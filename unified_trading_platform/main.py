#!/usr/bin/env python3
"""
🚀 Unified Trading Platform - Main Entry Point
"""

import asyncio
import logging
import argparse
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unified_trading_platform.core.trading_engine import TradingEngine

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler('unified_trading_platform.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

async def create_default_config():
    """Create default configuration directory and files"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Create main config file if it doesn't exist
    config_file = config_dir / "platform_config.yaml"
    if not config_file.exists():
        print(f"Creating default configuration at: {config_file}")
        from unified_trading_platform.core.config_manager import ConfigManager
        config_manager = ConfigManager(str(config_file))
        await config_manager._create_default_config()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified Trading Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m unified_trading_platform.main --config config/platform_config.yaml
  python -m unified_trading_platform.main --log-level DEBUG
  python -m unified_trading_platform.main --create-config
        """
    )
    
    parser.add_argument(
        "--config", 
        default="config/platform_config.yaml",
        help="Configuration file path (default: config/platform_config.yaml)"
    )
    
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create default configuration and exit"
    )
    
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="List available modules and exit"
    )
    
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (background process)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger("Main")
    
    try:
        # Handle special commands
        if args.create_config:
            await create_default_config()
            logger.info("Default configuration created. Please edit config/platform_config.yaml and run again.")
            return 0
        
        if args.validate_config:
            from unified_trading_platform.core.config_manager import ConfigManager
            config_manager = ConfigManager(args.config)
            if await config_manager.load_config():
                logger.info("✅ Configuration is valid")
                return 0
            else:
                logger.error("❌ Configuration validation failed")
                return 1
        
        if args.list_modules:
            from unified_trading_platform.core.plugin_manager import PluginManager
            from unified_trading_platform.core.event_bus import EventBus
            
            event_bus = EventBus()
            plugin_manager = PluginManager("modules", event_bus)
            
            modules = await plugin_manager.discover_modules()
            logger.info(f"Available modules ({len(modules)}):")
            for module in modules:
                logger.info(f"  • {module}")
            return 0
        
        # Ensure config directory exists
        await create_default_config()
        
        # Create and start trading engine
        logger.info("🚀 Starting Unified Trading Platform...")
        logger.info(f"📁 Configuration: {args.config}")
        logger.info(f"📝 Log Level: {args.log_level}")
        
        engine = TradingEngine(args.config)
        
        if args.daemon:
            logger.info("🔄 Running in daemon mode...")
            # In a real implementation, you'd use proper daemon libraries
            # For now, we'll just run normally
        
        success = await engine.start()
        
        if success:
            logger.info("✅ Trading Platform started successfully!")
            return 0
        else:
            logger.error("❌ Failed to start Trading Platform")
            return 1
    
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received - shutting down gracefully...")
        return 0
    
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 