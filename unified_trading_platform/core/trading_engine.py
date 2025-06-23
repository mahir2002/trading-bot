#!/usr/bin/env python3
"""
🚀 Unified Trading Engine
Main orchestrator for the unified trading platform
"""

import asyncio
import logging
import signal
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json
from datetime import datetime
import sys

from .base_module import ModuleStatus, ModulePriority
from .event_bus import EventBus
from .plugin_manager import PluginManager
from .config_manager import ConfigManager

class TradingEngine:
    """
    Main Trading Engine for the Unified Platform
    
    Orchestrates all modules and provides central control
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger("TradingEngine")
        
        # Core components
        self.event_bus = EventBus()
        self.config_manager = ConfigManager(config_path)
        self.plugin_manager = PluginManager("modules", self.event_bus)
        
        # State management
        self.running = False
        self.startup_time = None
        self.shutdown_requested = False
        
        # Performance tracking
        self.performance_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'uptime_seconds': 0
        }
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        self.logger.info("Trading Engine initialized")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.shutdown_requested = True
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """
        Initialize the trading engine and all components
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info("Initializing Trading Engine...")
            
            # Load configuration
            if not await self.config_manager.load_config():
                self.logger.error("Failed to load configuration")
                return False
            
            config = self.config_manager.get_config()
            
            # Start event bus
            await self.event_bus.start()
            
            # Discover available modules
            discovered_modules = await self.plugin_manager.discover_modules()
            self.logger.info(f"Discovered modules: {discovered_modules}")
            
            # Load enabled modules based on configuration
            enabled_modules = config.get('modules', {})
            if not enabled_modules:
                self.logger.warning("No modules enabled in configuration")
                return False
            
            # Load modules
            load_results = await self.plugin_manager.load_modules(enabled_modules)
            
            failed_loads = [name for name, result in load_results.items() if not result.success]
            if failed_loads:
                self.logger.error(f"Failed to load modules: {failed_loads}")
                
                # Check if critical modules failed
                critical_modules = config.get('critical_modules', [])
                failed_critical = [name for name in failed_loads if name in critical_modules]
                
                if failed_critical:
                    self.logger.error(f"Critical modules failed to load: {failed_critical}")
                    return False
            
            # Start loaded modules
            start_results = await self.plugin_manager.start_modules()
            
            failed_starts = [name for name, success in start_results.items() if not success]
            if failed_starts:
                self.logger.error(f"Failed to start modules: {failed_starts}")
                
                # Check if critical modules failed to start
                critical_modules = config.get('critical_modules', [])
                failed_critical = [name for name in failed_starts if name in critical_modules]
                
                if failed_critical:
                    self.logger.error(f"Critical modules failed to start: {failed_critical}")
                    return False
            
            # Register for system events
            self.register_system_events()
            
            self.logger.info("Trading Engine initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            return False
    
    def register_system_events(self):
        """Register handlers for system-level events"""
        # Subscribe to critical events
        self.event_bus.subscribe(
            "TradingEngine", 
            "emergency_stop", 
            self._handle_emergency_stop,
            ModulePriority.CRITICAL
        )
        
        self.event_bus.subscribe(
            "TradingEngine",
            "trade_executed",
            self._handle_trade_executed,
            ModulePriority.HIGH
        )
        
        self.event_bus.subscribe(
            "TradingEngine",
            "module_error",
            self._handle_module_error,
            ModulePriority.HIGH
        )
    
    async def _handle_emergency_stop(self, event):
        """Handle emergency stop events"""
        self.logger.critical(f"Emergency stop triggered by {event.source_module}: {event.data}")
        await self.emergency_shutdown()
    
    async def _handle_trade_executed(self, event):
        """Handle trade execution events"""
        trade_data = event.data
        self.performance_stats['total_trades'] += 1
        
        if trade_data.get('success', False):
            self.performance_stats['successful_trades'] += 1
            pnl = trade_data.get('pnl', 0)
            self.performance_stats['total_pnl'] += pnl
        else:
            self.performance_stats['failed_trades'] += 1
        
        self.logger.info(f"Trade executed: {trade_data}")
    
    async def _handle_module_error(self, event):
        """Handle module error events"""
        error_data = event.data
        module_name = event.source_module
        error_level = error_data.get('level', 'ERROR')
        
        self.logger.error(f"Module error in {module_name}: {error_data}")
        
        # Check if this is a critical error requiring shutdown
        if error_level == 'CRITICAL':
            critical_modules = self.config_manager.get_config().get('critical_modules', [])
            if module_name in critical_modules:
                self.logger.critical(f"Critical module {module_name} failed, initiating shutdown")
                await self.emergency_shutdown()
    
    async def start(self) -> bool:
        """
        Start the trading engine
        
        Returns:
            bool: True if started successfully
        """
        if self.running:
            self.logger.warning("Trading engine already running")
            return True
        
        try:
            # Initialize if not already done
            if not await self.initialize():
                return False
            
            self.running = True
            self.startup_time = datetime.now()
            
            # Send startup event
            from unified_trading_platform.core.base_module import ModuleEvent
            startup_event = ModuleEvent(
                event_type='system_startup',
                source_module='TradingEngine',
                target_module=None,
                data={
                    'startup_time': self.startup_time.isoformat(),
                    'active_modules': list(self.plugin_manager.get_all_modules().keys())
                },
                timestamp=datetime.now(),
                priority=ModulePriority.HIGH
            )
            await self.event_bus.send_event(startup_event)
            
            self.logger.info("🚀 Trading Engine started successfully!")
            
            # Start main event loop
            await self.run()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            self.running = False
            return False
    
    async def run(self):
        """Main execution loop"""
        try:
            while self.running and not self.shutdown_requested:
                # Update performance stats
                if self.startup_time:
                    self.performance_stats['uptime_seconds'] = (
                        datetime.now() - self.startup_time
                    ).total_seconds()
                
                # Health check all modules
                await self.health_check_modules()
                
                # Sleep briefly to prevent busy waiting
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("Trading engine run loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            if self.running:
                await self.shutdown()
    
    async def health_check_modules(self):
        """Perform health checks on all modules"""
        try:
            modules = self.plugin_manager.get_all_modules()
            unhealthy_modules = []
            
            for module_name, module in modules.items():
                if module.is_active():
                    try:
                        health_status = await module.health_check()
                        if not health_status.get('healthy', False):
                            unhealthy_modules.append(module_name)
                            self.logger.warning(f"Module {module_name} health check failed: {health_status}")
                    except Exception as e:
                        unhealthy_modules.append(module_name)
                        self.logger.error(f"Health check error for {module_name}: {e}")
            
            # Handle unhealthy modules
            if unhealthy_modules:
                await self._handle_unhealthy_modules(unhealthy_modules)
                
        except Exception as e:
            self.logger.error(f"Error during health checks: {e}")
    
    async def _handle_unhealthy_modules(self, unhealthy_modules: List[str]):
        """Handle modules that failed health checks"""
        config = self.config_manager.get_config()
        restart_policy = config.get('restart_policy', 'manual')
        
        for module_name in unhealthy_modules:
            if restart_policy == 'automatic':
                self.logger.info(f"Attempting to restart unhealthy module: {module_name}")
                
                # Stop and restart the module
                await self.plugin_manager.stop_modules([module_name])
                start_result = await self.plugin_manager.start_modules([module_name])
                
                if start_result.get(module_name, False):
                    self.logger.info(f"Successfully restarted module: {module_name}")
                else:
                    self.logger.error(f"Failed to restart module: {module_name}")
            else:
                self.logger.warning(f"Module {module_name} is unhealthy but automatic restart is disabled")
    
    async def shutdown(self):
        """Graceful shutdown of the trading engine"""
        if not self.running:
            return
        
        self.logger.info("Initiating graceful shutdown...")
        self.running = False
        
        try:
            # Send shutdown event
            await self.event_bus.send_event({
                'event_type': 'system_shutdown',
                'source_module': 'TradingEngine',
                'target_module': None,
                'data': {
                    'shutdown_time': datetime.now().isoformat(),
                    'uptime_seconds': self.performance_stats['uptime_seconds']
                },
                'timestamp': datetime.now(),
                'priority': ModulePriority.CRITICAL
            })
            
            # Give modules time to process shutdown event
            await asyncio.sleep(2)
            
            # Stop all modules
            await self.plugin_manager.stop_modules()
            
            # Stop event bus
            await self.event_bus.stop()
            
            # Save final state
            await self.save_state()
            
            self.logger.info("Trading Engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def emergency_shutdown(self):
        """Emergency shutdown - immediate stop"""
        self.logger.critical("EMERGENCY SHUTDOWN INITIATED")
        self.running = False
        
        try:
            # Immediate stop of all modules
            await self.plugin_manager.stop_modules()
            await self.event_bus.stop()
            
            self.logger.critical("Emergency shutdown complete")
            sys.exit(1)
            
        except Exception as e:
            self.logger.critical(f"Error during emergency shutdown: {e}")
            sys.exit(1)
    
    async def save_state(self):
        """Save current state for recovery"""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'performance_stats': self.performance_stats,
                'module_states': {},
                'platform_status': self.plugin_manager.get_platform_status()
            }
            
            # Get state from each module
            for module_name, module in self.plugin_manager.get_all_modules().items():
                try:
                    state['module_states'][module_name] = {
                        'status': module.status.value,
                        'metrics': module.get_metrics()
                    }
                except Exception as e:
                    self.logger.error(f"Error getting state from module {module_name}: {e}")
            
            # Save to file
            state_file = Path("platform_state.json")
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            
            self.logger.info(f"State saved to {state_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall platform status"""
        return {
            'running': self.running,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'uptime_seconds': self.performance_stats['uptime_seconds'],
            'performance_stats': self.performance_stats.copy(),
            'platform_status': self.plugin_manager.get_platform_status(),
            'event_bus_stats': self.event_bus.get_statistics()
        }
    
    def get_module_status(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific module"""
        return self.event_bus.get_module_stats(module_name)
    
    # Administrative methods
    async def reload_module(self, module_name: str) -> bool:
        """Reload a specific module"""
        try:
            # Get current config
            config = self.config_manager.get_config()
            module_config = config.get('modules', {}).get(module_name)
            
            if not module_config:
                self.logger.error(f"No configuration found for module: {module_name}")
                return False
            
            # Stop and unload
            await self.plugin_manager.stop_modules([module_name])
            await self.plugin_manager.unload_module(module_name)
            
            # Reload
            load_result = await self.plugin_manager.load_module(module_name, module_config)
            if not load_result.success:
                return False
            
            # Start
            start_result = await self.plugin_manager.start_modules([module_name])
            return start_result.get(module_name, False)
            
        except Exception as e:
            self.logger.error(f"Error reloading module {module_name}: {e}")
            return False
    
    async def update_module_config(self, module_name: str, new_config: Dict[str, Any]) -> bool:
        """Update configuration for a specific module"""
        try:
            module = self.plugin_manager.get_module(module_name)
            if not module:
                self.logger.error(f"Module not found: {module_name}")
                return False
            
            # Update configuration
            success = module.update_config(new_config)
            if success:
                # Update in config manager as well
                await self.config_manager.update_module_config(module_name, new_config)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating config for module {module_name}: {e}")
            return False

# Main entry point
async def main():
    """Main entry point for the trading engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Trading Platform")
    parser.add_argument("--config", default="config/platform_config.yaml", 
                       help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_platform.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create and start trading engine
    engine = TradingEngine(args.config)
    
    try:
        success = await engine.start()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 