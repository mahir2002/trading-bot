#!/usr/bin/env python3
"""
Unified Trading Platform Startup Script
Launches the complete trading platform with all modules and services
"""

import asyncio
import signal
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
import json
import subprocess
import time
from datetime import datetime

# Add the platform to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import platform components
from core.trading_engine import TradingEngine
from core.config_manager import ConfigManager
from modules.market_data import MarketDataModule
from modules.ai_models import AIModelsModule
from modules.signal_generation import SignalGenerationModule
from modules.risk_management import RiskManagementModule
from modules.order_execution import OrderExecutionModule
from modules.portfolio import PortfolioModule
from performance.optimizer import create_performance_system
from dashboard.app import app as dashboard_app, socketio, dashboard_event_handler

class UnifiedTradingPlatform:
    """Main platform orchestrator."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/production.yaml"
        self.trading_engine = None
        self.dashboard_process = None
        self.performance_monitor = None
        self.performance_optimizer = None
        self.performance_profiler = None
        self.logger = self._setup_logging()
        self.shutdown_event = asyncio.Event()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up comprehensive logging."""
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"logs/platform_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    async def start(self):
        """Start the unified trading platform."""
        try:
            self.logger.info("🚀 Starting Unified Trading Platform...")
            
            # Step 1: Load configuration
            await self._load_configuration()
            
            # Step 2: Initialize performance monitoring
            await self._initialize_performance_monitoring()
            
            # Step 3: Initialize trading engine
            await self._initialize_trading_engine()
            
            # Step 4: Register all modules
            await self._register_modules()
            
            # Step 5: Start trading engine
            await self._start_trading_engine()
            
            # Step 6: Start dashboard
            await self._start_dashboard()
            
            # Step 7: Setup signal handlers
            self._setup_signal_handlers()
            
            self.logger.info("✅ Unified Trading Platform started successfully!")
            self._print_startup_summary()
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start platform: {e}")
            raise
    
    async def _load_configuration(self):
        """Load platform configuration."""
        self.logger.info("📋 Loading configuration...")
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_path):
            await self._create_default_config()
        
        self.config_manager = ConfigManager(self.config_path)
        self.config = self.config_manager.get_config()
        
        self.logger.info(f"Configuration loaded from: {self.config_path}")
    
    async def _create_default_config(self):
        """Create default configuration file."""
        self.logger.info("Creating default configuration...")
        
        default_config = {
            'trading_engine': {
                'max_events_per_second': 1000,
                'health_check_interval': 30,
                'graceful_shutdown_timeout': 30,
                'emergency_stop_enabled': True
            },
            'market_data': {
                'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT'],
                'update_interval': 1,
                'data_sources': ['binance', 'coingecko'],
                'websocket_enabled': True,
                'historical_data_days': 30
            },
            'ai_models': {
                'model_types': ['LSTM', 'ENSEMBLE'],
                'prediction_interval': 300,  # 5 minutes
                'retrain_interval': 86400,   # 24 hours
                'feature_engineering': True,
                'ensemble_weights': {
                    'lstm': 0.4,
                    'random_forest': 0.3,
                    'gradient_boosting': 0.3
                }
            },
            'signal_generation': {
                'confirmation_threshold': 0.7,
                'regime_detection': True,
                'multi_timeframe_analysis': True,
                'risk_adjusted_sizing': True
            },
            'risk_management': {
                'max_account_risk': 0.02,      # 2%
                'max_daily_drawdown': 0.03,    # 3%
                'max_total_drawdown': 0.10,    # 10%
                'max_position_size': 0.05,     # 5%
                'max_open_positions': 20,
                'stop_loss_enabled': True,
                'take_profit_enabled': True
            },
            'order_execution': {
                'default_exchange': 'BINANCE',
                'execution_timeout': 30,
                'max_slippage': 0.001,         # 0.1%
                'order_retry_attempts': 3,
                'smart_routing': True
            },
            'portfolio': {
                'initial_capital': 100000.0,
                'base_currency': 'USDT',
                'rebalancing_enabled': True,
                'performance_tracking': True
            },
            'dashboard': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'real_time_updates': True,
                'authentication_required': False
            },
            'performance': {
                'monitoring_enabled': True,
                'profiling_enabled': False,
                'metrics_retention_hours': 24,
                'optimization_auto_apply': False
            },
            'logging': {
                'level': 'INFO',
                'file_rotation': True,
                'max_file_size_mb': 100,
                'backup_count': 10
            },
            'security': {
                'api_key_encryption': True,
                'secure_connections_only': True,
                'rate_limiting': True
            }
        }
        
        # Create config directory
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save default config
        import yaml
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Default configuration created at: {self.config_path}")
    
    async def _initialize_performance_monitoring(self):
        """Initialize performance monitoring system."""
        if not self.config.get('performance', {}).get('monitoring_enabled', True):
            return
        
        self.logger.info("📊 Initializing performance monitoring...")
        
        self.performance_monitor, self.performance_optimizer, self.performance_profiler = create_performance_system()
        
        # Start monitoring
        await self.performance_monitor.start_monitoring()
        
        # Start profiling if enabled
        if self.config.get('performance', {}).get('profiling_enabled', False):
            self.performance_profiler.start_memory_profiling()
        
        self.logger.info("Performance monitoring initialized")
    
    async def _initialize_trading_engine(self):
        """Initialize the trading engine."""
        self.logger.info("🔧 Initializing trading engine...")
        
        engine_config = self.config.get('trading_engine', {})
        self.trading_engine = TradingEngine(engine_config)
        
        # Connect performance monitoring to trading engine
        if self.performance_monitor:
            # This would be implemented in the trading engine to record events
            pass
        
        self.logger.info("Trading engine initialized")
    
    async def _register_modules(self):
        """Register all trading modules."""
        self.logger.info("🔌 Registering trading modules...")
        
        modules = [
            ('market_data', MarketDataModule(self.config.get('market_data', {}))),
            ('ai_models', AIModelsModule(self.config.get('ai_models', {}))),
            ('signal_generation', SignalGenerationModule(self.config.get('signal_generation', {}))),
            ('risk_management', RiskManagementModule(self.config.get('risk_management', {}))),
            ('order_execution', OrderExecutionModule(self.config.get('order_execution', {}))),
            ('portfolio', PortfolioModule(self.config.get('portfolio', {})))
        ]
        
        for name, module in modules:
            try:
                self.trading_engine.register_module(module)
                self.logger.info(f"✅ Registered module: {name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to register module {name}: {e}")
                raise
        
        self.logger.info(f"All {len(modules)} modules registered successfully")
    
    async def _start_trading_engine(self):
        """Start the trading engine."""
        self.logger.info("🚀 Starting trading engine...")
        
        success = await self.trading_engine.start()
        if not success:
            raise RuntimeError("Failed to start trading engine")
        
        self.logger.info("Trading engine started successfully")
    
    async def _start_dashboard(self):
        """Start the web dashboard."""
        dashboard_config = self.config.get('dashboard', {})
        
        if not dashboard_config.get('enabled', True):
            self.logger.info("Dashboard disabled in configuration")
            return
        
        self.logger.info("🌐 Starting web dashboard...")
        
        # Connect dashboard to trading engine events
        if hasattr(self.trading_engine, 'event_bus'):
            # This would be implemented to forward events to dashboard
            pass
        
        # Start dashboard in background
        host = dashboard_config.get('host', '0.0.0.0')
        port = dashboard_config.get('port', 5000)
        debug = dashboard_config.get('debug', False)
        
        def run_dashboard():
            socketio.run(dashboard_app, host=host, port=port, debug=debug, use_reloader=False)
        
        import threading
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Wait a moment for dashboard to start
        await asyncio.sleep(2)
        
        self.logger.info(f"Web dashboard started at: http://{host}:{port}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _print_startup_summary(self):
        """Print startup summary."""
        dashboard_config = self.config.get('dashboard', {})
        host = dashboard_config.get('host', '0.0.0.0')
        port = dashboard_config.get('port', 5000)
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🚀 UNIFIED TRADING PLATFORM                          ║
║                              Successfully Started                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📊 Dashboard:     http://{host}:{port:<10}                                   ║
║  📈 Modules:       6 trading modules active                                 ║
║  💹 Symbols:       {len(self.config.get('market_data', {}).get('symbols', []))} trading pairs monitored                           ║
║  🧠 AI Models:     {len(self.config.get('ai_models', {}).get('model_types', []))} AI models loaded                                ║
║  ⚡ Performance:   Real-time monitoring active                              ║
║  🛡️  Risk Mgmt:    Advanced risk controls enabled                           ║
║                                                                              ║
║  🎯 Platform Status: OPERATIONAL                                            ║
║  📅 Started:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔗 Quick Links:
   • Dashboard:     http://{host}:{port}
   • API Docs:      http://{host}:{port}/api/docs
   • System Status: http://{host}:{port}/api/system-status
   • Logs:          ./logs/

⚡ Key Features Active:
   ✅ Real-time market data streaming
   ✅ AI-powered signal generation
   ✅ Advanced risk management
   ✅ Multi-exchange order execution
   ✅ Portfolio tracking & analytics
   ✅ Performance monitoring
   ✅ Web dashboard interface

🛑 To stop the platform: Ctrl+C or send SIGTERM
"""
        print(summary)
    
    async def shutdown(self):
        """Gracefully shutdown the platform."""
        self.logger.info("🛑 Initiating platform shutdown...")
        
        try:
            # Stop trading engine
            if self.trading_engine:
                await self.trading_engine.stop()
                self.logger.info("Trading engine stopped")
            
            # Stop performance monitoring
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
                self.logger.info("Performance monitoring stopped")
            
            if self.performance_profiler:
                self.performance_profiler.stop_memory_profiling()
                self.logger.info("Performance profiling stopped")
            
            # Generate final performance report
            if self.performance_optimizer:
                analysis = self.performance_optimizer.analyze_performance(duration_minutes=60)
                report_file = f"logs/final_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(analysis, f, indent=2, default=str)
                self.logger.info(f"Final performance report saved: {report_file}")
            
            self.logger.info("✅ Platform shutdown completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            self.shutdown_event.set()

def run_tests():
    """Run the test suite."""
    print("🧪 Running test suite...")
    
    try:
        # Run integration tests
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def migrate_bots(search_paths: List[str]):
    """Run bot migration tool."""
    print("🔄 Running bot migration...")
    
    try:
        from tools.bot_migration_tool import MigrationOrchestrator
        
        platform_path = str(Path(__file__).parent)
        orchestrator = MigrationOrchestrator(platform_path)
        
        migration_config = {
            'skip_hard_migrations': False,
            'min_trading_score': 3,
            'supported_languages': ['python']
        }
        
        report = orchestrator.run_migration(search_paths, migration_config)
        
        print(f"✅ Migration completed:")
        print(f"   • Total bots discovered: {report['summary']['total_discovered']}")
        print(f"   • Successful migrations: {report['summary']['successful_migrations']}")
        print(f"   • Failed migrations: {report['summary']['failed_migrations']}")
        
        # Save detailed report
        report_file = f"logs/migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"   • Detailed report: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Unified Trading Platform')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--test', action='store_true', help='Run tests before starting')
    parser.add_argument('--migrate', nargs='+', help='Migrate bots from specified paths')
    parser.add_argument('--dry-run', action='store_true', help='Validate configuration without starting')
    
    args = parser.parse_args()
    
    # Run tests if requested
    if args.test:
        if not run_tests():
            print("❌ Tests failed, aborting startup")
            sys.exit(1)
    
    # Run migration if requested
    if args.migrate:
        if not migrate_bots(args.migrate):
            print("❌ Migration failed, aborting startup")
            sys.exit(1)
    
    # Create platform instance
    platform = UnifiedTradingPlatform(config_path=args.config)
    
    # Dry run - just validate configuration
    if args.dry_run:
        try:
            await platform._load_configuration()
            print("✅ Configuration is valid")
            return
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            sys.exit(1)
    
    # Start the platform
    try:
        await platform.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Platform error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Run the platform
    asyncio.run(main()) 