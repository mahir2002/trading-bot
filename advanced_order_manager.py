#!/usr/bin/env python3
"""
📋 Advanced Order Management System
Addresses: "Order Types: Currently, it's not clear what order types are used for actual trades.
Implementing more sophisticated order types and execution logic could improve trade execution."
Solution: Comprehensive order types with intelligent execution strategies
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from abc import ABC, abstractmethod
import math

class OrderType(Enum):
    """Comprehensive order types for advanced trading"""
    # Basic order types
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    
    # Advanced order types
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    ICEBERG = "iceberg"
    TWAP = "twap"  # Time Weighted Average Price
    VWAP = "vwap"  # Volume Weighted Average Price
    
    # Algorithmic order types
    BRACKET = "bracket"  # OCO with profit/loss
    OCO = "oco"  # One Cancels Other
    CONDITIONAL = "conditional"
    SCALED = "scaled"  # Scale in/out orders

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TimeInForce(Enum):
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    GTD = "gtd"  # Good Till Date
    DAY = "day"  # Good for day

class ExecutionStrategy(Enum):
    AGGRESSIVE = "aggressive"  # Market orders, immediate execution
    PASSIVE = "passive"       # Limit orders, better prices
    BALANCED = "balanced"     # Mix of market and limit
    STEALTH = "stealth"       # Hidden/iceberg orders
    OPTIMAL = "optimal"       # AI-driven execution

@dataclass
class OrderCondition:
    """Conditions for conditional orders"""
    symbol: str
    condition_type: str  # "price_above", "price_below", "volume_above", etc.
    threshold: float
    timeframe: Optional[str] = None

@dataclass
class OrderExecution:
    """Execution details for filled orders"""
    execution_id: str
    timestamp: datetime
    price: float
    quantity: float
    fee: float
    fee_currency: str
    trade_id: Optional[str] = None

@dataclass
class BaseOrder:
    """Base order structure with all common fields"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    
    # Optional fields
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    
    # Status and tracking
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Execution tracking
    filled_quantity: float = 0.0
    remaining_quantity: Optional[float] = None
    average_price: Optional[float] = None
    executions: List[OrderExecution] = field(default_factory=list)
    
    # Advanced features
    conditions: List[OrderCondition] = field(default_factory=list)
    parent_order_id: Optional[str] = None
    child_order_ids: List[str] = field(default_factory=list)
    
    # Metadata
    strategy_name: Optional[str] = None
    notes: Optional[str] = None
    client_order_id: Optional[str] = None
    
    def __post_init__(self):
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity
        if self.client_order_id is None:
            self.client_order_id = f"client_{uuid.uuid4().hex[:8]}"

@dataclass
class AdvancedOrder(BaseOrder):
    """Extended order class for sophisticated order types"""
    
    # Trailing stop parameters
    trail_amount: Optional[float] = None
    trail_percent: Optional[float] = None
    trail_price: Optional[float] = None
    
    # Iceberg parameters
    visible_quantity: Optional[float] = None
    
    # TWAP/VWAP parameters
    duration_minutes: Optional[int] = None
    slice_count: Optional[int] = None
    
    # Bracket order parameters
    profit_price: Optional[float] = None
    loss_price: Optional[float] = None
    
    # Scaling parameters
    scale_levels: Optional[List[Dict]] = None
    
    # Execution strategy
    execution_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED

class OrderExecutor(ABC):
    """Abstract base class for order execution strategies"""
    
    @abstractmethod
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        pass
    
    @abstractmethod
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        pass

class MarketOrderExecutor(OrderExecutor):
    """Executes market orders immediately at best available price"""
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        current_price = market_data.get('price', 0)
        
        # Simulate market order execution
        execution_price = current_price
        if order.side == OrderSide.BUY:
            execution_price *= 1.001  # Slight slippage
        else:
            execution_price *= 0.999
        
        return {
            'order_id': order.order_id,
            'status': 'filled',
            'filled_quantity': order.quantity,
            'average_price': execution_price,
            'timestamp': datetime.now()
        }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.MARKET

class LimitOrderExecutor(OrderExecutor):
    """Executes limit orders when price conditions are met"""
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        current_price = market_data.get('price', 0)
        
        # Check if limit price is reached
        can_fill = False
        if order.side == OrderSide.BUY and current_price <= order.price:
            can_fill = True
        elif order.side == OrderSide.SELL and current_price >= order.price:
            can_fill = True
        
        if can_fill:
            return {
                'order_id': order.order_id,
                'status': 'filled',
                'filled_quantity': order.quantity,
                'average_price': order.price,
                'timestamp': datetime.now()
            }
        
        return {
            'order_id': order.order_id,
            'status': 'open',
            'message': f'Waiting for price to reach {order.price}'
        }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.LIMIT

class StopLossExecutor(OrderExecutor):
    """Executes stop loss orders when stop price is triggered"""
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        current_price = market_data.get('price', 0)
        
        # Check if stop price is triggered
        triggered = False
        if order.side == OrderSide.SELL and current_price <= order.stop_price:
            triggered = True
        elif order.side == OrderSide.BUY and current_price >= order.stop_price:
            triggered = True
        
        if triggered:
            # Convert to market order for immediate execution
            execution_price = current_price
            if order.side == OrderSide.SELL:
                execution_price *= 0.995  # Slippage on stop loss
            else:
                execution_price *= 1.005
            
            return {
                'order_id': order.order_id,
                'status': 'filled',
                'filled_quantity': order.quantity,
                'average_price': execution_price,
                'timestamp': datetime.now(),
                'trigger_price': order.stop_price
            }
        
        return {
            'order_id': order.order_id,
            'status': 'open',
            'message': f'Monitoring for stop price {order.stop_price}'
        }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.STOP_LOSS

class TrailingStopExecutor(OrderExecutor):
    """Executes trailing stop orders with dynamic stop price adjustment"""
    
    def __init__(self):
        self.best_prices = {}  # Track best prices for each order
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        current_price = market_data.get('price', 0)
        order_id = order.order_id
        
        # Initialize best price tracking
        if order_id not in self.best_prices:
            self.best_prices[order_id] = current_price
        
        # Update best price and trailing stop
        if order.side == OrderSide.SELL:
            # For sell orders, track highest price
            if current_price > self.best_prices[order_id]:
                self.best_prices[order_id] = current_price
                
                # Update trailing stop price
                if order.trail_percent:
                    order.trail_price = current_price * (1 - order.trail_percent / 100)
                elif order.trail_amount:
                    order.trail_price = current_price - order.trail_amount
            
            # Check if trailing stop is triggered
            if order.trail_price and current_price <= order.trail_price:
                execution_price = current_price * 0.995  # Slippage
                
                return {
                    'order_id': order.order_id,
                    'status': 'filled',
                    'filled_quantity': order.quantity,
                    'average_price': execution_price,
                    'timestamp': datetime.now(),
                    'trail_trigger': order.trail_price,
                    'best_price': self.best_prices[order_id]
                }
        
        else:  # BUY orders
            # For buy orders, track lowest price
            if current_price < self.best_prices[order_id]:
                self.best_prices[order_id] = current_price
                
                # Update trailing stop price
                if order.trail_percent:
                    order.trail_price = current_price * (1 + order.trail_percent / 100)
                elif order.trail_amount:
                    order.trail_price = current_price + order.trail_amount
            
            # Check if trailing stop is triggered
            if order.trail_price and current_price >= order.trail_price:
                execution_price = current_price * 1.005  # Slippage
                
                return {
                    'order_id': order.order_id,
                    'status': 'filled',
                    'filled_quantity': order.quantity,
                    'average_price': execution_price,
                    'timestamp': datetime.now(),
                    'trail_trigger': order.trail_price,
                    'best_price': self.best_prices[order_id]
                }
        
        trail_price_str = f"{order.trail_price:.4f}" if order.trail_price else "calculating..."
        return {
            'order_id': order.order_id,
            'status': 'open',
            'message': f'Trailing stop at {trail_price_str}, best price: {self.best_prices[order_id]:.4f}'
        }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.TRAILING_STOP

class IcebergExecutor(OrderExecutor):
    """Executes iceberg orders by showing only small portions"""
    
    def __init__(self):
        self.iceberg_state = {}  # Track iceberg execution state
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        order_id = order.order_id
        
        # Initialize iceberg state
        if order_id not in self.iceberg_state:
            self.iceberg_state[order_id] = {
                'total_quantity': order.quantity,
                'visible_quantity': order.visible_quantity or min(order.quantity * 0.1, 100),
                'executed_quantity': 0,
                'current_slice': 0
            }
        
        state = self.iceberg_state[order_id]
        current_price = market_data.get('price', 0)
        
        # Check if current visible slice can be filled
        visible_qty = min(state['visible_quantity'], 
                         state['total_quantity'] - state['executed_quantity'])
        
        if visible_qty <= 0:
            return {
                'order_id': order.order_id,
                'status': 'filled',
                'filled_quantity': state['total_quantity'],
                'average_price': order.price,
                'timestamp': datetime.now(),
                'iceberg_slices': state['current_slice']
            }
        
        # Simulate partial fill of visible quantity
        if order.side == OrderSide.BUY and current_price <= order.price:
            fill_qty = visible_qty
        elif order.side == OrderSide.SELL and current_price >= order.price:
            fill_qty = visible_qty
        else:
            return {
                'order_id': order.order_id,
                'status': 'open',
                'message': f'Iceberg slice {state["current_slice"]}: {visible_qty} visible'
            }
        
        # Update state
        state['executed_quantity'] += fill_qty
        state['current_slice'] += 1
        
        if state['executed_quantity'] >= state['total_quantity']:
            status = 'filled'
        else:
            status = 'partially_filled'
        
        return {
            'order_id': order.order_id,
            'status': status,
            'filled_quantity': fill_qty,
            'total_filled': state['executed_quantity'],
            'average_price': order.price,
            'timestamp': datetime.now(),
            'iceberg_slice': state['current_slice']
        }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.ICEBERG

class TWAPExecutor(OrderExecutor):
    """Time Weighted Average Price execution"""
    
    def __init__(self):
        self.twap_state = {}
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        order_id = order.order_id
        
        # Initialize TWAP state
        if order_id not in self.twap_state:
            duration_minutes = order.duration_minutes or 60
            slice_count = order.slice_count or 10
            
            self.twap_state[order_id] = {
                'start_time': datetime.now(),
                'duration_minutes': duration_minutes,
                'slice_count': slice_count,
                'slice_size': order.quantity / slice_count,
                'executed_slices': 0,
                'total_executed': 0,
                'next_execution': datetime.now()
            }
        
        state = self.twap_state[order_id]
        now = datetime.now()
        
        # Check if it's time for next slice
        if now < state['next_execution']:
            return {
                'order_id': order.order_id,
                'status': 'open',
                'message': f'TWAP: {state["executed_slices"]}/{state["slice_count"]} slices executed'
            }
        
        # Execute next slice
        if state['executed_slices'] < state['slice_count']:
            slice_qty = state['slice_size']
            current_price = market_data.get('price', 0)
            
            # Execute slice at current market price
            state['executed_slices'] += 1
            state['total_executed'] += slice_qty
            
            # Schedule next execution
            interval_minutes = state['duration_minutes'] / state['slice_count']
            state['next_execution'] = now + timedelta(minutes=interval_minutes)
            
            if state['executed_slices'] >= state['slice_count']:
                status = 'filled'
            else:
                status = 'partially_filled'
            
            return {
                'order_id': order.order_id,
                'status': status,
                'filled_quantity': slice_qty,
                'total_filled': state['total_executed'],
                'average_price': current_price,
                'timestamp': now,
                'twap_slice': f"{state['executed_slices']}/{state['slice_count']}"
            }
        
        return {
            'order_id': order.order_id,
            'status': 'filled',
            'message': 'TWAP execution completed'
        }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.TWAP

class BracketOrderExecutor(OrderExecutor):
    """Executes bracket orders (entry + profit target + stop loss)"""
    
    def __init__(self):
        self.bracket_state = {}
    
    async def execute_order(self, order: AdvancedOrder, market_data: Dict) -> Dict:
        order_id = order.order_id
        current_price = market_data.get('price', 0)
        
        # Initialize bracket state
        if order_id not in self.bracket_state:
            self.bracket_state[order_id] = {
                'entry_filled': False,
                'profit_order_id': f"{order_id}_profit",
                'stop_order_id': f"{order_id}_stop"
            }
        
        state = self.bracket_state[order_id]
        
        # First, execute entry order
        if not state['entry_filled']:
            # Check if entry conditions are met
            entry_filled = False
            if order.order_type == OrderType.MARKET:
                entry_filled = True
            elif order.side == OrderSide.BUY and current_price <= order.price:
                entry_filled = True
            elif order.side == OrderSide.SELL and current_price >= order.price:
                entry_filled = True
            
            if entry_filled:
                state['entry_filled'] = True
                return {
                    'order_id': order.order_id,
                    'status': 'filled',
                    'filled_quantity': order.quantity,
                    'average_price': order.price or current_price,
                    'timestamp': datetime.now(),
                    'bracket_stage': 'entry_filled',
                    'profit_target': order.profit_price,
                    'stop_loss': order.loss_price
                }
            else:
                return {
                    'order_id': order.order_id,
                    'status': 'open',
                    'message': 'Bracket: Waiting for entry fill'
                }
        
        # Entry is filled, monitor profit/loss levels
        else:
            # Check profit target
            profit_hit = False
            stop_hit = False
            
            if order.side == OrderSide.BUY:
                if current_price >= order.profit_price:
                    profit_hit = True
                elif current_price <= order.loss_price:
                    stop_hit = True
            else:  # SELL
                if current_price <= order.profit_price:
                    profit_hit = True
                elif current_price >= order.loss_price:
                    stop_hit = True
            
            if profit_hit:
                return {
                    'order_id': order.order_id,
                    'status': 'filled',
                    'filled_quantity': order.quantity,
                    'average_price': order.profit_price,
                    'timestamp': datetime.now(),
                    'bracket_stage': 'profit_target_hit',
                    'exit_reason': 'profit_target'
                }
            elif stop_hit:
                return {
                    'order_id': order.order_id,
                    'status': 'filled',
                    'filled_quantity': order.quantity,
                    'average_price': order.loss_price,
                    'timestamp': datetime.now(),
                    'bracket_stage': 'stop_loss_hit',
                    'exit_reason': 'stop_loss'
                }
            else:
                return {
                    'order_id': order.order_id,
                    'status': 'open',
                    'message': f'Bracket: Monitoring P/L levels (current: {current_price})'
                }
    
    def can_execute(self, order: AdvancedOrder, market_data: Dict) -> bool:
        return order.order_type == OrderType.BRACKET

class AdvancedOrderManager:
    """
    Comprehensive order management system with sophisticated order types
    and intelligent execution strategies
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Order storage
        self.orders: Dict[str, AdvancedOrder] = {}
        self.order_history: List[AdvancedOrder] = []
        
        # Execution engines
        self.executors = {
            OrderType.MARKET: MarketOrderExecutor(),
            OrderType.LIMIT: LimitOrderExecutor(),
            OrderType.STOP_LOSS: StopLossExecutor(),
            OrderType.TRAILING_STOP: TrailingStopExecutor(),
            OrderType.ICEBERG: IcebergExecutor(),
            OrderType.TWAP: TWAPExecutor(),
            OrderType.BRACKET: BracketOrderExecutor(),
        }
        
        # Market data cache
        self.market_data: Dict[str, Dict] = {}
        
        # Performance metrics
        self.metrics = {
            'total_orders': 0,
            'filled_orders': 0,
            'cancelled_orders': 0,
            'average_fill_time': 0.0,
            'slippage_stats': [],
            'order_type_stats': {}
        }
        
        # Background tasks
        self.is_running = False
        self.background_tasks = []
        
        self.logger.info("📋 Advanced Order Manager initialized")
    
    def create_order(self, symbol: str, side: OrderSide, order_type: OrderType, 
                    quantity: float, **kwargs) -> AdvancedOrder:
        """Create a new advanced order"""
        
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        
        order = AdvancedOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            **kwargs
        )
        
        self.orders[order_id] = order
        self.metrics['total_orders'] += 1
        
        # Update order type statistics
        order_type_key = order_type.value
        if order_type_key not in self.metrics['order_type_stats']:
            self.metrics['order_type_stats'][order_type_key] = 0
        self.metrics['order_type_stats'][order_type_key] += 1
        
        self.logger.info(f"📝 Created {order_type.value} order: {order_id} - {side.value} {quantity} {symbol}")
        
        return order
    
    async def submit_order(self, order: AdvancedOrder) -> Dict:
        """Submit an order for execution"""
        
        if order.order_id not in self.orders:
            self.orders[order.order_id] = order
        
        order.status = OrderStatus.OPEN
        order.updated_at = datetime.now()
        
        self.logger.info(f"🚀 Submitted order: {order.order_id}")
        
        return {
            'order_id': order.order_id,
            'status': 'submitted',
            'message': 'Order submitted for execution'
        }
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an existing order"""
        
        if order_id not in self.orders:
            return {'error': 'Order not found'}
        
        order = self.orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return {'error': f'Cannot cancel order in {order.status.value} status'}
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        
        self.metrics['cancelled_orders'] += 1
        
        self.logger.info(f"❌ Cancelled order: {order_id}")
        
        return {
            'order_id': order_id,
            'status': 'cancelled',
            'message': 'Order cancelled successfully'
        }
    
    def update_market_data(self, symbol: str, data: Dict):
        """Update market data for order execution"""
        
        self.market_data[symbol] = {
            'price': data.get('price', 0),
            'bid': data.get('bid', 0),
            'ask': data.get('ask', 0),
            'volume': data.get('volume', 0),
            'timestamp': datetime.now(),
            **data
        }
    
    async def process_orders(self):
        """Process all active orders"""
        
        active_orders = [
            order for order in self.orders.values()
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        ]
        
        for order in active_orders:
            try:
                # Get market data for the symbol
                market_data = self.market_data.get(order.symbol, {})
                
                if not market_data:
                    continue
                
                # Find appropriate executor
                executor = self.executors.get(order.order_type)
                if not executor:
                    self.logger.warning(f"No executor found for order type: {order.order_type}")
                    continue
                
                # Execute order
                if executor.can_execute(order, market_data):
                    result = await executor.execute_order(order, market_data)
                    await self._handle_execution_result(order, result)
                
            except Exception as e:
                self.logger.error(f"Error processing order {order.order_id}: {e}")
                order.status = OrderStatus.REJECTED
    
    async def _handle_execution_result(self, order: AdvancedOrder, result: Dict):
        """Handle the result of order execution"""
        
        status = result.get('status')
        
        if status == 'filled':
            order.status = OrderStatus.FILLED
            order.filled_quantity = result.get('filled_quantity', order.quantity)
            order.average_price = result.get('average_price')
            order.updated_at = datetime.now()
            
            # Create execution record
            execution = OrderExecution(
                execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                timestamp=result.get('timestamp', datetime.now()),
                price=result.get('average_price', 0),
                quantity=result.get('filled_quantity', 0),
                fee=result.get('fee', 0),
                fee_currency=result.get('fee_currency', 'USDT')
            )
            order.executions.append(execution)
            
            # Move to history
            self.order_history.append(order)
            self.metrics['filled_orders'] += 1
            
            self.logger.info(f"✅ Order filled: {order.order_id} - {order.filled_quantity} @ {order.average_price}")
            
        elif status == 'partially_filled':
            order.status = OrderStatus.PARTIALLY_FILLED
            filled_qty = result.get('filled_quantity', 0)
            order.filled_quantity += filled_qty
            order.remaining_quantity -= filled_qty
            order.updated_at = datetime.now()
            
            self.logger.info(f"🔄 Partial fill: {order.order_id} - {filled_qty} filled, {order.remaining_quantity} remaining")
        
        elif status == 'open':
            # Order remains open, log status message if provided
            message = result.get('message')
            if message:
                self.logger.debug(f"📊 {order.order_id}: {message}")
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get detailed status of an order"""
        
        if order_id not in self.orders:
            return None
        
        order = self.orders[order_id]
        
        return {
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'order_type': order.order_type.value,
            'quantity': order.quantity,
            'price': order.price,
            'status': order.status.value,
            'filled_quantity': order.filled_quantity,
            'remaining_quantity': order.remaining_quantity,
            'average_price': order.average_price,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'executions': len(order.executions),
            'strategy_name': order.strategy_name
        }
    
    def get_orders_by_symbol(self, symbol: str) -> List[Dict]:
        """Get all orders for a specific symbol"""
        
        symbol_orders = [
            order for order in self.orders.values()
            if order.symbol == symbol
        ]
        
        return [self.get_order_status(order.order_id) for order in symbol_orders]
    
    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics"""
        
        # Calculate fill rate
        fill_rate = (self.metrics['filled_orders'] / max(1, self.metrics['total_orders'])) * 100
        
        # Calculate average slippage
        avg_slippage = 0
        if self.metrics['slippage_stats']:
            avg_slippage = sum(self.metrics['slippage_stats']) / len(self.metrics['slippage_stats'])
        
        return {
            'total_orders': self.metrics['total_orders'],
            'filled_orders': self.metrics['filled_orders'],
            'cancelled_orders': self.metrics['cancelled_orders'],
            'fill_rate': f"{fill_rate:.1f}%",
            'average_slippage': f"{avg_slippage:.4f}%",
            'order_type_distribution': self.metrics['order_type_stats'],
            'active_orders': len([o for o in self.orders.values() if o.status == OrderStatus.OPEN])
        }
    
    async def start_background_processing(self):
        """Start background order processing"""
        
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start order processing task
        processing_task = asyncio.create_task(self._background_order_processor())
        self.background_tasks.append(processing_task)
        
        self.logger.info("🚀 Background order processing started")
    
    async def stop_background_processing(self):
        """Stop background order processing"""
        
        self.is_running = False
        
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
        
        self.logger.info("⏹️ Background order processing stopped")
    
    async def _background_order_processor(self):
        """Background task to continuously process orders"""
        
        while self.is_running:
            try:
                await self.process_orders()
                await asyncio.sleep(0.1)  # Process every 100ms
                
            except Exception as e:
                self.logger.error(f"Error in background order processor: {e}")
                await asyncio.sleep(1)

# Global instance for easy use
order_manager = AdvancedOrderManager()

# Convenience functions for creating different order types
def create_market_order(symbol: str, side: OrderSide, quantity: float, **kwargs) -> AdvancedOrder:
    """Create a market order"""
    return order_manager.create_order(symbol, side, OrderType.MARKET, quantity, **kwargs)

def create_limit_order(symbol: str, side: OrderSide, quantity: float, price: float, **kwargs) -> AdvancedOrder:
    """Create a limit order"""
    return order_manager.create_order(symbol, side, OrderType.LIMIT, quantity, price=price, **kwargs)

def create_stop_loss_order(symbol: str, side: OrderSide, quantity: float, stop_price: float, **kwargs) -> AdvancedOrder:
    """Create a stop loss order"""
    return order_manager.create_order(symbol, side, OrderType.STOP_LOSS, quantity, stop_price=stop_price, **kwargs)

def create_trailing_stop_order(symbol: str, side: OrderSide, quantity: float, trail_percent: float, **kwargs) -> AdvancedOrder:
    """Create a trailing stop order"""
    return order_manager.create_order(symbol, side, OrderType.TRAILING_STOP, quantity, trail_percent=trail_percent, **kwargs)

def create_iceberg_order(symbol: str, side: OrderSide, quantity: float, price: float, visible_quantity: float, **kwargs) -> AdvancedOrder:
    """Create an iceberg order"""
    return order_manager.create_order(symbol, side, OrderType.ICEBERG, quantity, price=price, visible_quantity=visible_quantity, **kwargs)

def create_twap_order(symbol: str, side: OrderSide, quantity: float, duration_minutes: int, **kwargs) -> AdvancedOrder:
    """Create a TWAP order"""
    return order_manager.create_order(symbol, side, OrderType.TWAP, quantity, duration_minutes=duration_minutes, **kwargs)

def create_bracket_order(symbol: str, side: OrderSide, quantity: float, entry_price: float, profit_price: float, loss_price: float, **kwargs) -> AdvancedOrder:
    """Create a bracket order"""
    return order_manager.create_order(symbol, side, OrderType.BRACKET, quantity, price=entry_price, profit_price=profit_price, loss_price=loss_price, **kwargs) 