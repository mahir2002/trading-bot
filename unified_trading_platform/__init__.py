#!/usr/bin/env python3
"""
🚀 Unified Trading Platform
A comprehensive, modular cryptocurrency trading platform
"""

__version__ = "1.0.0"
__author__ = "Unified Trading Platform Team"
__description__ = "Modular cryptocurrency trading platform with AI capabilities"

# Core imports
from .core.trading_engine import TradingEngine
from .core.base_module import BaseModule, ModuleStatus, ModulePriority
from .core.event_bus import EventBus
from .core.plugin_manager import PluginManager
from .core.config_manager import ConfigManager

# Export main components
__all__ = [
    'TradingEngine',
    'BaseModule',
    'ModuleStatus',
    'ModulePriority',
    'EventBus',
    'PluginManager',
    'ConfigManager',
    '__version__',
    '__author__',
    '__description__'
] 