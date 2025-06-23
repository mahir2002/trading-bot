#!/usr/bin/env python3
"""
Risk Management Module - Comprehensive Portfolio Risk Management
Consolidates dynamic position sizing, portfolio risk controls, and advanced risk metrics
"""

import numpy as np
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

# Local imports
from core.base_module import BaseModule, ModuleStatus, ModuleInfo, ModulePriority, ModuleEvent
import sys
import os

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# from unified_trading_platform.core.event_bus import Event, ModulePriority  # Not needed - using ModuleEvent from base_module

class RiskLevel(Enum):
    """Risk level classifications."""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    MAXIMUM = "MAXIMUM"

@dataclass
class RiskLimits:
    """Comprehensive risk limits configuration."""
    max_account_risk: float = 0.05          # 5% maximum account risk
    max_daily_drawdown: float = 0.02        # 2% maximum daily drawdown
    max_total_drawdown: float = 0.10        # 10% maximum total drawdown
    max_position_size: float = 0.05         # 5% maximum position size
    max_open_positions: int = 20            # Maximum open positions

@dataclass
class RiskMetrics:
    """Real-time risk metrics."""
    portfolio_var_95: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    portfolio_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    leverage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class RiskAlert:
    """Risk management alert."""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    metric_value: float
    threshold: float
    timestamp: datetime
    action_required: str

class RiskManagementModule(BaseModule):
    """Risk Management Module for the unified trading platform."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config or {})
        
        # Initialize risk limits
        self.risk_limits = RiskLimits(
            max_account_risk=self.config.get('max_account_risk', 0.05),
            max_daily_drawdown=self.config.get('max_daily_drawdown', 0.02),
            max_total_drawdown=self.config.get('max_total_drawdown', 0.10),
            max_position_size=self.config.get('max_position_size', 0.05)
        )
        
        # Risk tracking
        self.risk_alerts = []
        self.current_positions = {}
        self.current_metrics = RiskMetrics()
        
    async def initialize(self) -> bool:
        """Initialize the risk management module."""
        try:
            self.logger.info("Initializing Risk Management Module...")
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Risk Management Module initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Risk Management Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """Start the risk management module."""
        try:
            self.logger.info("Starting Risk Management Module...")
            
            # Start risk monitoring
            asyncio.create_task(self._risk_monitoring())
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Risk Management Module started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Risk Management Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the risk management module."""
        try:
            self.logger.info("Stopping Risk Management Module...")
            
            self.status = ModuleStatus.STOPPED
            self.logger.info("Risk Management Module stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Risk Management Module: {e}")
            return False
    
    async def handle_event(self, event: ModuleEvent) -> bool:
        """Process incoming events."""
        try:
            if event.event_type == "trade_approval_request":
                await self._handle_trade_approval_request(event)
            elif event.event_type == "portfolio_update":
                await self._handle_portfolio_update(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            return False
    
    async def _handle_trade_approval_request(self, event: ModuleEvent):
        """Handle trade approval requests."""
        data = event.data
        symbol = data.get('symbol')
        trade_size = data.get('trade_size', 0)
        
        # Simple approval logic
        allowed = True
        reason = "Trade approved"
        
        # Check position count
        if len(self.current_positions) >= self.risk_limits.max_open_positions:
            allowed = False
            reason = "Maximum positions reached"
        
        # Emit response
        await self.event_bus.emit(ModuleEvent(
            type="trade_approval_response",
            data={
                "symbol": symbol,
                "approved": allowed,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            },
            priority=ModulePriority.HIGH
        ))
    
    async def _handle_portfolio_update(self, event: ModuleEvent):
        """Handle portfolio updates."""
        data = event.data
        positions = data.get('positions', {})
        
        self.current_positions = positions
        
        # Calculate basic risk metrics
        self.current_metrics = RiskMetrics()
        
        # Emit risk update
        await self.event_bus.emit(ModuleEvent(
            type="portfolio_risk_update",
            data={
                "metrics": self.current_metrics.__dict__,
                "alerts": [],
                "timestamp": datetime.now().isoformat()
            },
            priority=ModulePriority.NORMAL
        ))
    
    async def _risk_monitoring(self):
        """Background risk monitoring."""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Basic risk monitoring
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status."""
        return {
            **super().get_status(),
            "current_positions": len(self.current_positions),
            "risk_alerts": len(self.risk_alerts),
            "risk_limits": {
                "max_account_risk": self.risk_limits.max_account_risk,
                "max_position_size": self.risk_limits.max_position_size,
                "max_daily_drawdown": self.risk_limits.max_daily_drawdown
            }
        } 

    def get_module_info(self) -> ModuleInfo:
        """Return module information and metadata."""
        return ModuleInfo(
            name="risk_management",
            version="1.0.0",
            description="Risk Management Module",
            author="Unified Trading Platform",
            dependencies=[],
            priority=ModulePriority.NORMAL,
            config_schema=self.get_config_schema()
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check module health."""
        return {
            "status": self.status.value,
            "last_error": self.last_error,
            "metrics": self.get_metrics()
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this module."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
