#!/usr/bin/env python3
"""
⚙️ Configuration Manager
Centralized configuration management for the unified trading platform
"""

import yaml
import json
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import jsonschema
from jsonschema import validate
import copy

class ConfigManager:
    """
    Unified Configuration Manager
    
    Handles loading, validation, and management of all platform configurations
    """
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger("ConfigManager")
        
        # Configuration storage
        self.config = {}
        self.config_schema = self._get_base_schema()
        self.environment_configs = {}
        
        # Configuration history for rollback
        self.config_history = []
        self.max_history_size = 10
        
        # File watching
        self.last_modified = None
        
        self.logger.info(f"Configuration Manager initialized with path: {self.config_path}")
    
    def _get_base_schema(self) -> Dict[str, Any]:
        """Get the base configuration schema"""
        return {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "environment": {"type": "string", "enum": ["development", "staging", "production"]},
                        "debug": {"type": "boolean"},
                        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]}
                    },
                    "required": ["name", "version", "environment"]
                },
                "modules": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "priority": {"type": "integer", "minimum": 1, "maximum": 4},
                                "config": {"type": "object"}
                            },
                            "required": ["enabled"]
                        }
                    }
                },
                "critical_modules": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "restart_policy": {
                    "type": "string",
                    "enum": ["manual", "automatic"]
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "encryption_key": {"type": "string"},
                        "api_rate_limit": {"type": "integer"},
                        "max_concurrent_requests": {"type": "integer"}
                    }
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "pool_size": {"type": "integer"},
                        "timeout": {"type": "integer"}
                    }
                },
                "exchanges": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "api_key": {"type": "string"},
                                "api_secret": {"type": "string"},
                                "sandbox": {"type": "boolean"},
                                "rate_limit": {"type": "integer"}
                            },
                            "required": ["enabled"]
                        }
                    }
                },
                "trading": {
                    "type": "object",
                    "properties": {
                        "default_position_size": {"type": "number"},
                        "max_position_size": {"type": "number"},
                        "risk_percentage": {"type": "number"},
                        "stop_loss_percentage": {"type": "number"},
                        "take_profit_percentage": {"type": "number"}
                    }
                }
            },
            "required": ["platform", "modules"]
        }
    
    async def load_config(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not self.config_path.exists():
                self.logger.error(f"Configuration file not found: {self.config_path}")
                # Create default config
                await self._create_default_config()
                return await self.load_config()  # Retry after creating default
            
            # Check file modification time
            current_modified = self.config_path.stat().st_mtime
            if self.last_modified and current_modified == self.last_modified:
                self.logger.debug("Configuration file unchanged, skipping reload")
                return True
            
            # Load the configuration file
            with open(self.config_path, 'r') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    new_config = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == '.json':
                    new_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {self.config_path.suffix}")
            
            # Validate configuration
            if not self.validate_config(new_config):
                self.logger.error("Configuration validation failed")
                return False
            
            # Save current config to history before updating
            if self.config:
                self._save_to_history()
            
            # Load environment-specific overrides
            environment = new_config.get('platform', {}).get('environment', 'development')
            env_config = await self._load_environment_config(environment)
            
            # Merge configurations
            self.config = self._merge_configs(new_config, env_config)
            
            # Process configuration (expand variables, etc.)
            self.config = self._process_config(self.config)
            
            self.last_modified = current_modified
            
            self.logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    async def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "platform": {
                "name": "Unified Trading Platform",
                "version": "1.0.0",
                "environment": "development",
                "debug": True,
                "log_level": "INFO"
            },
            "modules": {
                "market_data": {
                    "enabled": True,
                    "priority": 1,
                    "config": {
                        "symbols": ["BTC/USDT", "ETH/USDT"],
                        "timeframes": ["1m", "5m", "1h"],
                        "update_interval": 1
                    }
                },
                "ai_models": {
                    "enabled": True,
                    "priority": 2,
                    "config": {
                        "model_type": "ensemble",
                        "retrain_interval": 3600,
                        "features": ["price", "volume", "technical", "sentiment"]
                    }
                },
                "signal_generator": {
                    "enabled": True,
                    "priority": 2,
                    "config": {
                        "confidence_threshold": 0.7,
                        "max_signals_per_hour": 10
                    }
                },
                "risk_manager": {
                    "enabled": True,
                    "priority": 1,
                    "config": {
                        "max_risk_per_trade": 0.02,
                        "max_portfolio_risk": 0.1,
                        "stop_loss": 0.05,
                        "take_profit": 0.1
                    }
                },
                "order_manager": {
                    "enabled": True,
                    "priority": 1,
                    "config": {
                        "execution_mode": "paper",
                        "slippage_tolerance": 0.001
                    }
                },
                "dashboard": {
                    "enabled": True,
                    "priority": 3,
                    "config": {
                        "port": 8080,
                        "host": "localhost",
                        "auto_refresh": 5
                    }
                }
            },
            "critical_modules": ["risk_manager", "order_manager"],
            "restart_policy": "automatic",
            "security": {
                "api_rate_limit": 1000,
                "max_concurrent_requests": 100
            },
            "database": {
                "url": "sqlite:///trading_platform.db",
                "pool_size": 5,
                "timeout": 30
            },
            "exchanges": {
                "binance": {
                    "enabled": False,
                    "sandbox": True,
                    "rate_limit": 1200
                }
            },
            "trading": {
                "default_position_size": 0.01,
                "max_position_size": 0.1,
                "risk_percentage": 0.02,
                "stop_loss_percentage": 0.05,
                "take_profit_percentage": 0.1
            }
        }
        
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save default configuration
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Created default configuration: {self.config_path}")
    
    async def _load_environment_config(self, environment: str) -> Dict[str, Any]:
        """Load environment-specific configuration overrides"""
        env_config_path = self.config_path.parent / f"config.{environment}.yaml"
        
        if env_config_path.exists():
            try:
                with open(env_config_path, 'r') as f:
                    env_config = yaml.safe_load(f)
                self.logger.info(f"Loaded environment config for: {environment}")
                return env_config or {}
            except Exception as e:
                self.logger.warning(f"Error loading environment config: {e}")
        
        return {}
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries"""
        def deep_merge(base, override):
            result = copy.deepcopy(base)
            
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            
            return result
        
        return deep_merge(base_config, override_config)
    
    def _process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process configuration (expand environment variables, etc.)"""
        def expand_value(value):
            if isinstance(value, str):
                # Expand environment variables
                if value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    default_value = None
                    
                    if ':' in env_var:
                        env_var, default_value = env_var.split(':', 1)
                    
                    return os.getenv(env_var, default_value)
                
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            
            elif isinstance(value, list):
                return [expand_value(item) for item in value]
            
            return value
        
        return expand_value(config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if valid
        """
        try:
            # Basic validation
            if not isinstance(config, dict):
                self.logger.error("Configuration must be a dictionary")
                return False
            
            # Check required sections
            required_sections = ['platform', 'modules']
            for section in required_sections:
                if section not in config:
                    self.logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate platform section
            platform = config.get('platform', {})
            required_platform_fields = ['name', 'version', 'environment']
            for field in required_platform_fields:
                if field not in platform:
                    self.logger.error(f"Missing required platform field: {field}")
                    return False
            
            # Validate modules section
            modules = config.get('modules', {})
            if not isinstance(modules, dict):
                self.logger.error("Modules section must be a dictionary")
                return False
            
            # Additional custom validations
            if not self._validate_module_dependencies(config):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}")
            return False
    
    def _validate_module_dependencies(self, config: Dict[str, Any]) -> bool:
        """Validate module dependencies"""
        modules = config.get('modules', {})
        enabled_modules = [name for name, conf in modules.items() if conf.get('enabled', False)]
        
        # Define module dependencies
        dependencies = {
            'signal_generator': ['market_data', 'ai_models'],
            'order_manager': ['signal_generator', 'risk_manager'],
            'dashboard': ['market_data']
        }
        
        for module_name, deps in dependencies.items():
            if module_name in enabled_modules:
                for dep in deps:
                    if dep not in enabled_modules:
                        self.logger.warning(f"Module {module_name} recommends {dep} to be enabled")
        
        return True
    
    def _save_to_history(self):
        """Save current configuration to history"""
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'config': copy.deepcopy(self.config)
        }
        
        self.config_history.append(history_entry)
        
        # Limit history size
        if len(self.config_history) > self.max_history_size:
            self.config_history.pop(0)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration"""
        return copy.deepcopy(self.config)
    
    def get_module_config(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific module"""
        modules = self.config.get('modules', {})
        if module_name in modules:
            return copy.deepcopy(modules[module_name])
        return None
    
    def get_platform_config(self) -> Dict[str, Any]:
        """Get platform-level configuration"""
        return copy.deepcopy(self.config.get('platform', {}))
    
    def get_exchange_config(self, exchange_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific exchange"""
        exchanges = self.config.get('exchanges', {})
        if exchange_name in exchanges:
            return copy.deepcopy(exchanges[exchange_name])
        return None
    
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update the entire configuration
        
        Args:
            new_config: New configuration dictionary
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Validate new configuration
            if not self.validate_config(new_config):
                return False
            
            # Save current config to history
            self._save_to_history()
            
            # Update configuration
            self.config = copy.deepcopy(new_config)
            
            # Save to file
            await self.save_config()
            
            self.logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    async def update_module_config(self, module_name: str, module_config: Dict[str, Any]) -> bool:
        """
        Update configuration for a specific module
        
        Args:
            module_name: Name of the module
            module_config: New module configuration
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Update the module config in the main config
            if 'modules' not in self.config:
                self.config['modules'] = {}
            
            self.config['modules'][module_name] = copy.deepcopy(module_config)
            
            # Validate the entire configuration
            if not self.validate_config(self.config):
                self.logger.error("Configuration validation failed after module update")
                return False
            
            # Save to file
            await self.save_config()
            
            self.logger.info(f"Module configuration updated: {module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating module configuration: {e}")
            return False
    
    async def save_config(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create backup
            backup_path = self.config_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml')
            if self.config_path.exists():
                backup_path.write_text(self.config_path.read_text())
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            # Update modification time
            self.last_modified = self.config_path.stat().st_mtime
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def rollback_config(self, steps: int = 1) -> bool:
        """
        Rollback configuration to a previous version
        
        Args:
            steps: Number of versions to rollback
            
        Returns:
            bool: True if rollback successful
        """
        try:
            if len(self.config_history) < steps:
                self.logger.error(f"Cannot rollback {steps} steps, only {len(self.config_history)} versions available")
                return False
            
            # Get the configuration to rollback to
            rollback_entry = self.config_history[-(steps)]
            rollback_config = rollback_entry['config']
            
            # Update current configuration
            self.config = copy.deepcopy(rollback_config)
            
            self.logger.info(f"Configuration rolled back {steps} version(s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during configuration rollback: {e}")
            return False
    
    def get_config_history(self) -> List[Dict[str, Any]]:
        """Get configuration history"""
        return copy.deepcopy(self.config_history)
    
    def export_config(self, export_path: str, format: str = 'yaml') -> bool:
        """
        Export configuration to a file
        
        Args:
            export_path: Path to export to
            format: Export format ('yaml' or 'json')
            
        Returns:
            bool: True if exported successfully
        """
        try:
            export_file = Path(export_path)
            
            with open(export_file, 'w') as f:
                if format.lower() == 'yaml':
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                elif format.lower() == 'json':
                    json.dump(self.config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Configuration exported to {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False 