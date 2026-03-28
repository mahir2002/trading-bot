#!/usr/bin/env python3
"""
🏗️ Base Module Framework
Abstract base class for all trading platform modules
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

class ModuleStatus(Enum):
    """Module status enumeration"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing" 
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"

class ModulePriority(Enum):
    """Module execution priority"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class ModuleInfo:
    """Module information and metadata"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    priority: ModulePriority
    config_schema: Dict[str, Any]

@dataclass
class ModuleEvent:
    """Event structure for inter-module communication"""
    event_type: str
    source_module: str
    target_module: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    priority: ModulePriority = ModulePriority.NORMAL

class BaseModule(ABC):
    """
    Abstract base class for all trading platform modules
    
    All modules must inherit from this class and implement the required methods.
    This ensures consistent interface and behavior across all modules.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.status = ModuleStatus.INACTIVE
        self.logger = logging.getLogger(f"Module.{name}")
        self.event_handlers = {}
        self.dependencies_met = False
        self.last_error = None
        self.metrics = {
            'events_processed': 0,
            'events_sent': 0,
            'errors': 0,
            'uptime_start': None
        }
        
        # Module info - to be defined by each module
        self.module_info = None
        
        # Event bus reference - will be set by plugin manager
        self.event_bus = None
    
    @abstractmethod
    def get_module_info(self) -> ModuleInfo:
        """Return module information and metadata"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the module
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the module
        
        Returns:
            bool: True if start successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the module
        
        Returns:
            bool: True if stop successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check module health
        
        Returns:
            Dict containing health status and metrics
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return configuration schema for this module
        
        Returns:
            Dict describing expected configuration format
        """
        pass
    
    # Event handling methods
    def register_event_handler(self, event_type: str, handler_func):
        """Register handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler_func)
        self.logger.debug(f"Registered handler for event type: {event_type}")
    
    async def handle_event(self, event: ModuleEvent) -> bool:
        """
        Handle incoming event
        
        Args:
            event: ModuleEvent to handle
            
        Returns:
            bool: True if event was handled successfully
        """
        try:
            self.metrics['events_processed'] += 1
            
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    await handler(event)
                return True
            else:
                self.logger.debug(f"No handler for event type: {event.event_type}")
                return False
                
        except Exception as e:
            self.metrics['errors'] += 1
            self.last_error = str(e)
            self.logger.error(f"Error handling event {event.event_type}: {e}")
            return False
    
    async def send_event(self, event_type: str, data: Dict[str, Any], 
                        target_module: Optional[str] = None, 
                        priority: ModulePriority = ModulePriority.NORMAL):
        """
        Send event to other modules via event bus
        
        Args:
            event_type: Type of event
            data: Event data
            target_module: Specific target module (None for broadcast)
            priority: Event priority
        """
        if self.event_bus:
            event = ModuleEvent(
                event_type=event_type,
                source_module=self.name,
                target_module=target_module,
                data=data,
                timestamp=datetime.now(),
                priority=priority
            )
            
            await self.event_bus.send_event(event)
            self.metrics['events_sent'] += 1
            self.logger.debug(f"Sent event: {event_type}")
        else:
            self.logger.warning("Event bus not available - cannot send event")
    
    # Status management
    def set_status(self, status: ModuleStatus, error_msg: Optional[str] = None):
        """Set module status"""
        old_status = self.status
        self.status = status
        
        if error_msg:
            self.last_error = error_msg
            
        if status == ModuleStatus.ACTIVE and old_status != ModuleStatus.ACTIVE:
            self.metrics['uptime_start'] = datetime.now()
            
        self.logger.info(f"Status changed: {old_status.value} -> {status.value}")
    
    def is_active(self) -> bool:
        """Check if module is active"""
        return self.status == ModuleStatus.ACTIVE
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get module metrics"""
        metrics = self.metrics.copy()
        
        if metrics['uptime_start']:
            uptime = datetime.now() - metrics['uptime_start']
            metrics['uptime_seconds'] = uptime.total_seconds()
        else:
            metrics['uptime_seconds'] = 0
            
        metrics['status'] = self.status.value
        metrics['last_error'] = self.last_error
        
        return metrics
    
    # Configuration methods
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update module configuration
        
        Args:
            new_config: New configuration dictionary
            
        Returns:
            bool: True if update successful
        """
        try:
            # Validate against schema
            if self.validate_config(new_config):
                self.config.update(new_config)
                self.logger.info("Configuration updated successfully")
                return True
            else:
                self.logger.error("Configuration validation failed")
                return False
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if valid
        """
        # Basic validation - can be enhanced with jsonschema
        schema = self.get_config_schema()
        
        for required_key in schema.get('required', []):
            if required_key not in config:
                self.logger.error(f"Missing required config key: {required_key}")
                return False
                
        return True
    
    # Dependency management
    def check_dependencies(self, available_modules: List[str]) -> bool:
        """
        Check if module dependencies are met
        
        Args:
            available_modules: List of available module names
            
        Returns:
            bool: True if all dependencies are met
        """
        if not self.module_info:
            return True
            
        for dependency in self.module_info.dependencies:
            if dependency not in available_modules:
                self.logger.warning(f"Dependency not met: {dependency}")
                return False
                
        self.dependencies_met = True
        return True
    
    # Utility methods
    def log_info(self, message: str):
        """Log info message with module context"""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str):
        """Log error message with module context"""
        self.logger.error(f"[{self.name}] {message}")
        self.metrics['errors'] += 1
    
    def log_warning(self, message: str):
        """Log warning message with module context"""
        self.logger.warning(f"[{self.name}] {message}")
    
    def __str__(self):
        return f"Module({self.name}, {self.status.value})"
    
    def __repr__(self):
        return f"BaseModule(name='{self.name}', status='{self.status.value}')" 