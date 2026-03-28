#!/usr/bin/env python3
"""
Signal Generation Module - Advanced Trading Signal Generation
Consolidates multi-layer confirmation, market regime detection, and risk-adjusted signals
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

class SignalType(Enum):
    """Advanced trading signal types."""
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    WEAK_SELL = "WEAK_SELL"
    HOLD = "HOLD"
    WEAK_BUY = "WEAK_BUY"
    BUY = "BUY"
    STRONG_BUY = "STRONG_BUY"

class MarketRegime(Enum):
    """Market regime types."""
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    STABLE = "STABLE"

@dataclass
class TradingSignal:
    """Comprehensive trading signal."""
    symbol: str
    signal_type: SignalType
    confidence: float
    expected_return: float
    risk_score: float
    
    # Confirmations
    technical_confirmation: float
    volume_confirmation: float
    momentum_confirmation: float
    
    # Market conditions
    market_regime: MarketRegime
    regime_compatibility: bool
    volatility_forecast: float
    
    # Risk management
    stop_loss: float
    take_profit: float
    position_size_recommendation: float
    holding_period: int  # hours
    
    # AI prediction
    ai_prediction: float
    ai_confidence: float
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: str = ""

@dataclass
class SignalConfirmation:
    """Signal confirmation results."""
    technical_confirmation: float
    volume_confirmation: float
    momentum_confirmation: float
    volatility_confirmation: float
    overall_score: float

class MarketRegimeDetector:
    """Advanced market regime detection."""
    
    def __init__(self):
        self.regime_history = []
        
    def detect_regime(self, price_data: pd.Series, volume_data: pd.Series = None) -> MarketRegime:
        """Detect current market regime."""
        
        if len(price_data) < 50:
            return MarketRegime.STABLE
        
        # Calculate metrics
        returns = price_data.pct_change().dropna()
        
        # Trend detection
        sma_20 = price_data.rolling(20).mean()
        sma_50 = price_data.rolling(50).mean()
        
        current_price = price_data.iloc[-1]
        sma_20_current = sma_20.iloc[-1] if not sma_20.isna().iloc[-1] else current_price
        sma_50_current = sma_50.iloc[-1] if not sma_50.isna().iloc[-1] else current_price
        
        # Volatility
        volatility = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
        
        # Trend strength
        trend_strength = (current_price - sma_50_current) / sma_50_current if sma_50_current != 0 else 0
        
        # Determine regime
        if volatility > 0.4:  # High volatility threshold
            return MarketRegime.HIGH_VOLATILITY
        elif volatility < 0.15:  # Low volatility threshold
            return MarketRegime.LOW_VOLATILITY
        elif trend_strength > 0.05 and sma_20_current > sma_50_current:
            return MarketRegime.TRENDING_BULL
        elif trend_strength < -0.05 and sma_20_current < sma_50_current:
            return MarketRegime.TRENDING_BEAR
        else:
            return MarketRegime.RANGING

class SignalGenerationModule(BaseModule):
    """Signal Generation Module for the unified trading platform."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config or {})
        
        # Initialize signal generator
        self.regime_detector = MarketRegimeDetector()
        self.generated_signals = []
        
    async def initialize(self) -> bool:
        """Initialize the signal generation module."""
        try:
            self.logger.info("Initializing Signal Generation Module...")
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Signal Generation Module initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Signal Generation Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """Start the signal generation module."""
        try:
            self.logger.info("Starting Signal Generation Module...")
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Signal Generation Module started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Signal Generation Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the signal generation module."""
        try:
            self.logger.info("Stopping Signal Generation Module...")
            
            self.status = ModuleStatus.STOPPED
            self.logger.info("Signal Generation Module stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Signal Generation Module: {e}")
            return False
    
    async def handle_event(self, event: ModuleEvent) -> bool:
        """Process incoming events."""
        try:
            if event.event_type == "signal_request":
                await self._handle_signal_request(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            return False
    
    async def _handle_signal_request(self, event: ModuleEvent):
        """Handle signal requests."""
        data = event.data
        symbol = data.get('symbol', 'UNKNOWN')
        
        # Generate simple signal for now
        signal = TradingSignal(
            symbol=symbol,
            signal_type=SignalType.HOLD,
            confidence=0.5,
            expected_return=0.0,
            risk_score=0.02,
            technical_confirmation=0.5,
            volume_confirmation=0.5,
            momentum_confirmation=0.5,
            market_regime=MarketRegime.STABLE,
            regime_compatibility=True,
            volatility_forecast=0.02,
            stop_loss=0.05,
            take_profit=0.10,
            position_size_recommendation=0.05,
            holding_period=24,
            ai_prediction=0.0,
            ai_confidence=0.5,
            reasoning="Basic signal generation"
        )
        
        # Emit signal generated event
        await self.event_bus.emit(ModuleEvent(
            type="trading_signal_generated",
            data={
                "symbol": symbol,
                "signal": signal.__dict__,
                "timestamp": datetime.now().isoformat()
            },
            priority=ModulePriority.HIGH
        ))
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status."""
        return {
            **super().get_status(),
            "total_signals": len(self.generated_signals)
        } 

    def get_module_info(self) -> ModuleInfo:
        """Return module information and metadata."""
        return ModuleInfo(
            name="signal_generation",
            version="1.0.0",
            description="Signal Generation Module",
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
