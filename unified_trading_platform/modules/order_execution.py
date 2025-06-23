#!/usr/bin/env python3
"""
Order Execution Module - Advanced Trade Execution and Order Management
Handles multi-exchange order execution, order routing, and execution optimization
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

# Local imports
from core.base_module import BaseModule, ModuleStatus, ModuleInfo, ModulePriority, ModuleEvent
import sys
import os

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# from unified_trading_platform.core.event_bus import Event, ModulePriority  # Not needed - using ModuleEvent from base_module

class OrderType(Enum):
    """Order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

class OrderSide(Enum):
    """Order sides."""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Order status."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class Exchange(Enum):
    """Supported exchanges."""
    BINANCE = "BINANCE"
    COINBASE = "COINBASE"
    KRAKEN = "KRAKEN"
    BYBIT = "BYBIT"

@dataclass
class Order:
    """Order data structure."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"
    exchange: Exchange = Exchange.BINANCE
    
    # Status tracking
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    commission: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Metadata
    client_order_id: str = ""
    exchange_order_id: str = ""
    error_message: str = ""

@dataclass
class ExecutionReport:
    """Trade execution report."""
    order_id: str
    symbol: str
    side: OrderSide
    executed_quantity: float
    executed_price: float
    commission: float
    timestamp: datetime
    exchange: Exchange
    
class OrderExecutionModule(BaseModule):
    """Order Execution Module for the unified trading platform."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config or {})
        
        # Order management
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.execution_reports: List[ExecutionReport] = []
        
        # Exchange configurations
        self.exchange_configs = self.config.get('exchanges', {})
        self.default_exchange = Exchange(self.config.get('default_exchange', 'BINANCE'))
        
        # Execution settings
        self.max_slippage = self.config.get('max_slippage', 0.001)  # 0.1%
        self.execution_timeout = self.config.get('execution_timeout', 30)  # seconds
        
    async def initialize(self) -> bool:
        """Initialize the order execution module."""
        try:
            self.logger.info("Initializing Order Execution Module...")
            
            # Initialize exchange connections
            await self._initialize_exchanges()
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Order Execution Module initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Order Execution Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """Start the order execution module."""
        try:
            self.logger.info("Starting Order Execution Module...")
            
            # Start order monitoring
            asyncio.create_task(self._order_monitoring())
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Order Execution Module started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Order Execution Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the order execution module."""
        try:
            self.logger.info("Stopping Order Execution Module...")
            
            # Cancel all active orders
            await self._cancel_all_orders()
            
            self.status = ModuleStatus.STOPPED
            self.logger.info("Order Execution Module stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Order Execution Module: {e}")
            return False
    
    async def handle_event(self, event: ModuleEvent) -> bool:
        """Process incoming events."""
        try:
            if event.event_type == "place_order":
                await self._handle_place_order(event)
            elif event.event_type == "cancel_order":
                await self._handle_cancel_order(event)
            elif event.event_type == "modify_order":
                await self._handle_modify_order(event)
            elif event.event_type == "execution_signal":
                await self._handle_execution_signal(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            return False
    
    async def _handle_place_order(self, event: ModuleEvent):
        """Handle order placement requests."""
        try:
            data = event.data
            
            # Create order
            order = Order(
                order_id=self._generate_order_id(),
                symbol=data['symbol'],
                side=OrderSide(data['side']),
                order_type=OrderType(data['order_type']),
                quantity=data['quantity'],
                price=data.get('price'),
                stop_price=data.get('stop_price'),
                exchange=Exchange(data.get('exchange', self.default_exchange.value))
            )
            
            # Validate order
            if not await self._validate_order(order):
                await self._emit_order_rejected(order, "Order validation failed")
                return
            
            # Submit order
            success = await self._submit_order(order)
            
            if success:
                self.active_orders[order.order_id] = order
                await self._emit_order_submitted(order)
            else:
                await self._emit_order_rejected(order, "Order submission failed")
                
        except Exception as e:
            self.logger.error(f"Error handling place order: {e}")
    
    async def _handle_cancel_order(self, event: ModuleEvent):
        """Handle order cancellation requests."""
        try:
            data = event.data
            order_id = data['order_id']
            
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                success = await self._cancel_order(order)
                
                if success:
                    order.status = OrderStatus.CANCELLED
                    del self.active_orders[order_id]
                    self.order_history.append(order)
                    await self._emit_order_cancelled(order)
                    
        except Exception as e:
            self.logger.error(f"Error handling cancel order: {e}")
    
    async def _handle_execution_signal(self, event: ModuleEvent):
        """Handle execution signals from trading strategies."""
        try:
            data = event.data
            
            # Convert signal to order
            order_data = {
                'symbol': data['symbol'],
                'side': data['side'],
                'order_type': data.get('order_type', 'MARKET'),
                'quantity': data['quantity'],
                'price': data.get('price'),
                'exchange': data.get('exchange', self.default_exchange.value)
            }
            
            # Place order
            place_order_event = ModuleEvent(
                type="place_order",
                data=order_data,
                priority=ModulePriority.HIGH
            )
            
            await self.process_event(place_order_event)
            
        except Exception as e:
            self.logger.error(f"Error handling execution signal: {e}")
    
    async def _validate_order(self, order: Order) -> bool:
        """Validate order before submission."""
        try:
            # Basic validation
            if order.quantity <= 0:
                self.logger.warning(f"Invalid quantity: {order.quantity}")
                return False
            
            if order.order_type == OrderType.LIMIT and order.price is None:
                self.logger.warning("Limit order requires price")
                return False
            
            # Check minimum order size (exchange-specific)
            min_order_size = self._get_min_order_size(order.symbol, order.exchange)
            if order.quantity < min_order_size:
                self.logger.warning(f"Order size {order.quantity} below minimum {min_order_size}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating order: {e}")
            return False
    
    async def _submit_order(self, order: Order) -> bool:
        """Submit order to exchange."""
        try:
            # Simulate order submission
            order.status = OrderStatus.SUBMITTED
            order.submitted_at = datetime.now()
            order.exchange_order_id = f"EX_{order.order_id}"
            
            self.logger.info(f"Order {order.order_id} submitted to {order.exchange.value}")
            
            # Simulate execution for market orders
            if order.order_type == OrderType.MARKET:
                asyncio.create_task(self._simulate_execution(order))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return False
    
    async def _simulate_execution(self, order: Order):
        """Simulate order execution (for testing)."""
        try:
            # Simulate execution delay
            await asyncio.sleep(1)
            
            # Simulate execution
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_price = order.price or 50000  # Mock price
            order.filled_at = datetime.now()
            order.commission = order.quantity * order.average_price * 0.001  # 0.1% commission
            
            # Move to history
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]
            self.order_history.append(order)
            
            # Create execution report
            execution_report = ExecutionReport(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                executed_quantity=order.filled_quantity,
                executed_price=order.average_price,
                commission=order.commission,
                timestamp=order.filled_at,
                exchange=order.exchange
            )
            
            self.execution_reports.append(execution_report)
            
            # Emit execution event
            await self._emit_order_filled(order, execution_report)
            
        except Exception as e:
            self.logger.error(f"Error simulating execution: {e}")
    
    async def _cancel_order(self, order: Order) -> bool:
        """Cancel order on exchange."""
        try:
            # Simulate cancellation
            self.logger.info(f"Cancelling order {order.order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    async def _cancel_all_orders(self):
        """Cancel all active orders."""
        try:
            for order_id in list(self.active_orders.keys()):
                order = self.active_orders[order_id]
                await self._cancel_order(order)
                order.status = OrderStatus.CANCELLED
                del self.active_orders[order_id]
                self.order_history.append(order)
                
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
    
    async def _order_monitoring(self):
        """Monitor active orders."""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Check for order updates
                for order_id, order in list(self.active_orders.items()):
                    # Check for timeouts
                    if order.submitted_at:
                        elapsed = (datetime.now() - order.submitted_at).total_seconds()
                        if elapsed > self.execution_timeout:
                            self.logger.warning(f"Order {order_id} timed out")
                            await self._cancel_order(order)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in order monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _initialize_exchanges(self):
        """Initialize exchange connections."""
        try:
            # Mock exchange initialization
            self.logger.info("Initializing exchange connections...")
            
            for exchange in Exchange:
                self.logger.info(f"Connected to {exchange.value}")
                
        except Exception as e:
            self.logger.error(f"Error initializing exchanges: {e}")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"ORD_{timestamp}"
    
    def _get_min_order_size(self, symbol: str, exchange: Exchange) -> float:
        """Get minimum order size for symbol on exchange."""
        # Mock minimum order sizes
        min_sizes = {
            'BTCUSDT': 0.001,
            'ETHUSDT': 0.01,
            'ADAUSDT': 10.0
        }
        return min_sizes.get(symbol, 0.001)
    
    async def _emit_order_submitted(self, order: Order):
        """Emit order submitted event."""
        await self.event_bus.emit(ModuleEvent(
            type="order_submitted",
            data={
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": order.quantity,
                "status": order.status.value,
                "timestamp": order.submitted_at.isoformat() if order.submitted_at else None
            },
            priority=ModulePriority.HIGH
        ))
    
    async def _emit_order_filled(self, order: Order, execution_report: ExecutionReport):
        """Emit order filled event."""
        await self.event_bus.emit(ModuleEvent(
            type="order_filled",
            data={
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "executed_quantity": execution_report.executed_quantity,
                "executed_price": execution_report.executed_price,
                "commission": execution_report.commission,
                "timestamp": execution_report.timestamp.isoformat()
            },
            priority=ModulePriority.HIGH
        ))
    
    async def _emit_order_cancelled(self, order: Order):
        """Emit order cancelled event."""
        await self.event_bus.emit(ModuleEvent(
            type="order_cancelled",
            data={
                "order_id": order.order_id,
                "symbol": order.symbol,
                "status": order.status.value,
                "timestamp": datetime.now().isoformat()
            },
            priority=ModulePriority.NORMAL
        ))
    
    async def _emit_order_rejected(self, order: Order, reason: str):
        """Emit order rejected event."""
        await self.event_bus.emit(ModuleEvent(
            type="order_rejected",
            data={
                "order_id": order.order_id,
                "symbol": order.symbol,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            },
            priority=ModulePriority.HIGH
        ))
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status."""
        return {
            **super().get_status(),
            "active_orders": len(self.active_orders),
            "total_orders": len(self.order_history) + len(self.active_orders),
            "execution_reports": len(self.execution_reports),
            "exchanges": [e.value for e in Exchange]
        } 

    def get_module_info(self) -> ModuleInfo:
        """Return module information and metadata."""
        return ModuleInfo(
            name="order_execution",
            version="1.0.0",
            description="Order Execution Module",
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
