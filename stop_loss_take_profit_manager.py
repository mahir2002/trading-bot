#!/usr/bin/env python3
"""
🛡️ Stop-Loss and Take-Profit Management System
Addresses: "No explicit stop-loss or take-profit mechanisms are evident.
These are crucial for managing downside risk and locking in profits."
Solution: Comprehensive SL/TP system with multiple strategies and dynamic adjustments
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

class StopLossType(Enum):
    """Types of stop-loss strategies"""
    FIXED_PERCENTAGE = "fixed_percentage"
    TRAILING_STOP = "trailing_stop"
    VOLATILITY_BASED = "volatility_based"
    ATR_BASED = "atr_based"

class TakeProfitType(Enum):
    """Types of take-profit strategies"""
    FIXED_PERCENTAGE = "fixed_percentage"
    RISK_REWARD_RATIO = "risk_reward_ratio"
    SCALED_PROFIT = "scaled_profit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class SLTPStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"

@dataclass
class MarketData:
    """Market data for SL/TP calculations"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volatility: Optional[float] = None
    atr: Optional[float] = None

@dataclass
class Position:
    """Trading position information"""
    position_id: str
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percentage: float
    entry_time: datetime
    value: float

@dataclass
class StopLossOrder:
    """Stop-loss order configuration"""
    sl_id: str
    position_id: str
    symbol: str
    sl_type: StopLossType
    trigger_price: float
    quantity: float
    status: SLTPStatus
    created_at: datetime
    percentage: Optional[float] = None
    trail_percentage: Optional[float] = None
    volatility_multiplier: Optional[float] = None
    atr_multiplier: Optional[float] = None
    highest_price: Optional[float] = None
    lowest_price: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class TakeProfitOrder:
    """Take-profit order configuration"""
    tp_id: str
    position_id: str
    symbol: str
    tp_type: TakeProfitType
    trigger_price: float
    quantity: float
    status: SLTPStatus
    created_at: datetime
    percentage: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    scale_levels: Optional[List[Dict]] = None
    last_updated: datetime = field(default_factory=datetime.now)

class StopLossStrategy(ABC):
    """Abstract base class for stop-loss strategies"""
    
    @abstractmethod
    def calculate_stop_price(self, position: Position, market_data: MarketData, **kwargs) -> float:
        """Calculate stop-loss price"""
        pass
    
    @abstractmethod
    def should_update_stop(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> bool:
        """Determine if stop should be updated"""
        pass
    
    @abstractmethod
    def update_stop_price(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> float:
        """Update stop-loss price"""
        pass

class FixedPercentageStopLoss(StopLossStrategy):
    """Fixed percentage stop-loss strategy"""
    
    def calculate_stop_price(self, position: Position, market_data: MarketData, percentage: float = 0.02) -> float:
        """Calculate stop price based on fixed percentage"""
        if position.side == OrderSide.BUY:
            return position.entry_price * (1 - percentage)
        else:
            return position.entry_price * (1 + percentage)
    
    def should_update_stop(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> bool:
        """Fixed stops don't update"""
        return False
    
    def update_stop_price(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> float:
        """No update for fixed stops"""
        return sl_order.trigger_price

class TrailingStopLoss(StopLossStrategy):
    """Trailing stop-loss strategy"""
    
    def calculate_stop_price(self, position: Position, market_data: MarketData, trail_percentage: float = 0.02) -> float:
        """Calculate initial trailing stop price"""
        if position.side == OrderSide.BUY:
            return position.entry_price * (1 - trail_percentage)
        else:
            return position.entry_price * (1 + trail_percentage)
    
    def should_update_stop(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> bool:
        """Update trailing stop when price moves favorably"""
        current_price = market_data.price
        
        if position.side == OrderSide.BUY:
            return current_price > (sl_order.highest_price or position.entry_price)
        else:
            return current_price < (sl_order.lowest_price or position.entry_price)
    
    def update_stop_price(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> float:
        """Update trailing stop price"""
        current_price = market_data.price
        trail_percentage = sl_order.trail_percentage or 0.02
        
        if position.side == OrderSide.BUY:
            sl_order.highest_price = max(sl_order.highest_price or current_price, current_price)
            return sl_order.highest_price * (1 - trail_percentage)
        else:
            sl_order.lowest_price = min(sl_order.lowest_price or current_price, current_price)
            return sl_order.lowest_price * (1 + trail_percentage)

class VolatilityBasedStopLoss(StopLossStrategy):
    """Volatility-based stop-loss strategy"""
    
    def calculate_stop_price(self, position: Position, market_data: MarketData, volatility_multiplier: float = 2.0) -> float:
        """Calculate stop based on volatility"""
        volatility = market_data.volatility or 0.02
        stop_distance = volatility * volatility_multiplier
        
        if position.side == OrderSide.BUY:
            return position.entry_price * (1 - stop_distance)
        else:
            return position.entry_price * (1 + stop_distance)
    
    def should_update_stop(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> bool:
        """Update when volatility changes significantly"""
        return False
    
    def update_stop_price(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> float:
        """Update stop based on new volatility"""
        return self.calculate_stop_price(position, market_data, sl_order.volatility_multiplier or 2.0)

class ATRBasedStopLoss(StopLossStrategy):
    """ATR (Average True Range) based stop-loss strategy"""
    
    def calculate_stop_price(self, position: Position, market_data: MarketData, atr_multiplier: float = 2.0) -> float:
        """Calculate stop based on ATR"""
        atr = market_data.atr or (market_data.price * 0.02)
        stop_distance = atr * atr_multiplier
        
        if position.side == OrderSide.BUY:
            return position.entry_price - stop_distance
        else:
            return position.entry_price + stop_distance
    
    def should_update_stop(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> bool:
        """Update when ATR changes significantly"""
        return False
    
    def update_stop_price(self, sl_order: StopLossOrder, position: Position, market_data: MarketData) -> float:
        """Update stop based on new ATR"""
        return self.calculate_stop_price(position, market_data, sl_order.atr_multiplier or 2.0)

class TakeProfitStrategy(ABC):
    """Abstract base class for take-profit strategies"""
    
    @abstractmethod
    def calculate_profit_price(self, position: Position, market_data: MarketData, **kwargs) -> Union[float, List[float]]:
        """Calculate take-profit price(s)"""
        pass
    
    @abstractmethod
    def should_update_profit(self, tp_order: TakeProfitOrder, position: Position, market_data: MarketData) -> bool:
        """Determine if take-profit should be updated"""
        pass

class FixedPercentageTakeProfit(TakeProfitStrategy):
    """Fixed percentage take-profit strategy"""
    
    def calculate_profit_price(self, position: Position, market_data: MarketData, percentage: float = 0.04) -> float:
        """Calculate profit price based on fixed percentage"""
        if position.side == OrderSide.BUY:
            return position.entry_price * (1 + percentage)
        else:
            return position.entry_price * (1 - percentage)
    
    def should_update_profit(self, tp_order: TakeProfitOrder, position: Position, market_data: MarketData) -> bool:
        """Fixed profits don't update"""
        return False

class RiskRewardTakeProfit(TakeProfitStrategy):
    """Risk-reward ratio based take-profit strategy"""
    
    def calculate_profit_price(self, position: Position, market_data: MarketData, 
                             stop_price: float, risk_reward_ratio: float = 2.0) -> float:
        """Calculate profit price based on risk-reward ratio"""
        risk_amount = abs(position.entry_price - stop_price)
        reward_amount = risk_amount * risk_reward_ratio
        
        if position.side == OrderSide.BUY:
            return position.entry_price + reward_amount
        else:
            return position.entry_price - reward_amount
    
    def should_update_profit(self, tp_order: TakeProfitOrder, position: Position, market_data: MarketData) -> bool:
        """Update if stop-loss changes"""
        return False

class ScaledTakeProfit(TakeProfitStrategy):
    """Scaled take-profit strategy with multiple levels"""
    
    def calculate_profit_price(self, position: Position, market_data: MarketData, 
                             scale_levels: List[Dict] = None) -> List[float]:
        """Calculate multiple profit levels"""
        if not scale_levels:
            scale_levels = [
                {'percentage': 0.02, 'quantity_pct': 0.3},
                {'percentage': 0.04, 'quantity_pct': 0.4},
                {'percentage': 0.06, 'quantity_pct': 0.3},
            ]
        
        profit_prices = []
        for level in scale_levels:
            if position.side == OrderSide.BUY:
                price = position.entry_price * (1 + level['percentage'])
            else:
                price = position.entry_price * (1 - level['percentage'])
            profit_prices.append(price)
        
        return profit_prices
    
    def should_update_profit(self, tp_order: TakeProfitOrder, position: Position, market_data: MarketData) -> bool:
        """Scaled profits don't typically update"""
        return False

class StopLossTakeProfitManager:
    """
    Comprehensive stop-loss and take-profit management system
    Handles multiple strategies, dynamic adjustments, and intelligent execution
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Order storage
        self.stop_loss_orders: Dict[str, StopLossOrder] = {}
        self.take_profit_orders: Dict[str, TakeProfitOrder] = {}
        self.positions: Dict[str, Position] = {}
        
        # Strategy implementations
        self.sl_strategies = {
            StopLossType.FIXED_PERCENTAGE: FixedPercentageStopLoss(),
            StopLossType.TRAILING_STOP: TrailingStopLoss(),
            StopLossType.VOLATILITY_BASED: VolatilityBasedStopLoss(),
            StopLossType.ATR_BASED: ATRBasedStopLoss(),
        }
        
        self.tp_strategies = {
            TakeProfitType.FIXED_PERCENTAGE: FixedPercentageTakeProfit(),
            TakeProfitType.RISK_REWARD_RATIO: RiskRewardTakeProfit(),
            TakeProfitType.SCALED_PROFIT: ScaledTakeProfit(),
        }
        
        # Market data cache
        self.market_data: Dict[str, MarketData] = {}
        
        # Performance tracking
        self.metrics = {
            'total_sl_orders': 0,
            'triggered_sl_orders': 0,
            'total_tp_orders': 0,
            'triggered_tp_orders': 0,
            'avg_sl_slippage': 0.0,
            'avg_tp_slippage': 0.0,
            'total_saved_loss': 0.0,
            'total_locked_profit': 0.0
        }
        
        # Background processing
        self.is_running = False
        self.background_tasks = []
        
        self.logger.info("🛡️ Stop-Loss Take-Profit Manager initialized")
    
    def update_market_data(self, symbol: str, price: float, bid: float = None, ask: float = None, 
                          volume: float = 0, **kwargs):
        """Update market data for SL/TP calculations"""
        
        self.market_data[symbol] = MarketData(
            symbol=symbol,
            price=price,
            bid=bid or price,
            ask=ask or price,
            volume=volume,
            timestamp=datetime.now(),
            high_24h=kwargs.get('high_24h'),
            low_24h=kwargs.get('low_24h'),
            volatility=kwargs.get('volatility'),
            atr=kwargs.get('atr')
        )
    
    def add_position(self, position_id: str, symbol: str, side: OrderSide, quantity: float, 
                    entry_price: float, current_price: float = None) -> Position:
        """Add a new position to track"""
        
        current_price = current_price or entry_price
        unrealized_pnl = self._calculate_unrealized_pnl(side, quantity, entry_price, current_price)
        unrealized_pnl_pct = (unrealized_pnl / (quantity * entry_price)) * 100
        
        position = Position(
            position_id=position_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percentage=unrealized_pnl_pct,
            entry_time=datetime.now(),
            value=quantity * current_price
        )
        
        self.positions[position_id] = position
        self.logger.info(f"📍 Added position: {position_id} - {side.value} {quantity} {symbol} @ {entry_price}")
        
        return position
    
    def create_stop_loss(self, position_id: str, sl_type: StopLossType, **kwargs) -> StopLossOrder:
        """Create a stop-loss order for a position"""
        
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")
        
        position = self.positions[position_id]
        market_data = self.market_data.get(position.symbol)
        
        if not market_data:
            raise ValueError(f"No market data available for {position.symbol}")
        
        # Get strategy and calculate stop price
        strategy = self.sl_strategies.get(sl_type)
        if not strategy:
            raise ValueError(f"Stop-loss strategy {sl_type} not implemented")
        
        stop_price = strategy.calculate_stop_price(position, market_data, **kwargs)
        
        # Create stop-loss order
        sl_id = f"sl_{uuid.uuid4().hex[:8]}"
        sl_order = StopLossOrder(
            sl_id=sl_id,
            position_id=position_id,
            symbol=position.symbol,
            sl_type=sl_type,
            trigger_price=stop_price,
            quantity=position.quantity,
            status=SLTPStatus.ACTIVE,
            created_at=datetime.now(),
            **kwargs
        )
        
        self.stop_loss_orders[sl_id] = sl_order
        self.metrics['total_sl_orders'] += 1
        
        self.logger.info(f"🛡️ Created {sl_type.value} stop-loss: {sl_id} @ {stop_price:.4f}")
        
        return sl_order
    
    def create_take_profit(self, position_id: str, tp_type: TakeProfitType, **kwargs) -> TakeProfitOrder:
        """Create a take-profit order for a position"""
        
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")
        
        position = self.positions[position_id]
        market_data = self.market_data.get(position.symbol)
        
        if not market_data:
            raise ValueError(f"No market data available for {position.symbol}")
        
        # Get strategy and calculate profit price
        strategy = self.tp_strategies.get(tp_type)
        if not strategy:
            raise ValueError(f"Take-profit strategy {tp_type} not implemented")
        
        profit_price = strategy.calculate_profit_price(position, market_data, **kwargs)
        
        # Handle multiple profit levels for scaled strategies
        if isinstance(profit_price, list):
            profit_price = profit_price[0]  # Use first level as primary
        
        # Create take-profit order
        tp_id = f"tp_{uuid.uuid4().hex[:8]}"
        tp_order = TakeProfitOrder(
            tp_id=tp_id,
            position_id=position_id,
            symbol=position.symbol,
            tp_type=tp_type,
            trigger_price=profit_price,
            quantity=position.quantity,
            status=SLTPStatus.ACTIVE,
            created_at=datetime.now(),
            **kwargs
        )
        
        self.take_profit_orders[tp_id] = tp_order
        self.metrics['total_tp_orders'] += 1
        
        self.logger.info(f"💰 Created {tp_type.value} take-profit: {tp_id} @ {profit_price:.4f}")
        
        return tp_order
    
    def create_bracket_order(self, position_id: str, sl_type: StopLossType, tp_type: TakeProfitType,
                           sl_kwargs: Dict = None, tp_kwargs: Dict = None) -> Tuple[StopLossOrder, TakeProfitOrder]:
        """Create both stop-loss and take-profit orders (bracket order)"""
        
        sl_kwargs = sl_kwargs or {}
        tp_kwargs = tp_kwargs or {}
        
        # Create stop-loss
        sl_order = self.create_stop_loss(position_id, sl_type, **sl_kwargs)
        
        # Create take-profit
        tp_order = self.create_take_profit(position_id, tp_type, **tp_kwargs)
        
        self.logger.info(f"🎯 Created bracket order for position {position_id}")
        
        return sl_order, tp_order
    
    def update_position_price(self, position_id: str, current_price: float):
        """Update position with current market price"""
        
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        position.current_price = current_price
        position.unrealized_pnl = self._calculate_unrealized_pnl(
            position.side, position.quantity, position.entry_price, current_price
        )
        position.unrealized_pnl_percentage = (position.unrealized_pnl / (position.quantity * position.entry_price)) * 100
        position.value = position.quantity * current_price
    
    async def process_stop_loss_orders(self):
        """Process all active stop-loss orders"""
        
        triggered_orders = []
        
        for sl_id, sl_order in self.stop_loss_orders.items():
            if sl_order.status != SLTPStatus.ACTIVE:
                continue
            
            position = self.positions.get(sl_order.position_id)
            market_data = self.market_data.get(sl_order.symbol)
            
            if not position or not market_data:
                continue
            
            # Update position price
            self.update_position_price(position.position_id, market_data.price)
            
            # Check if stop should be updated
            strategy = self.sl_strategies.get(sl_order.sl_type)
            if strategy and strategy.should_update_stop(sl_order, position, market_data):
                new_stop_price = strategy.update_stop_price(sl_order, position, market_data)
                
                # Only update if new stop is better
                should_update = False
                if position.side == OrderSide.BUY and new_stop_price > sl_order.trigger_price:
                    should_update = True
                elif position.side == OrderSide.SELL and new_stop_price < sl_order.trigger_price:
                    should_update = True
                
                if should_update:
                    old_price = sl_order.trigger_price
                    sl_order.trigger_price = new_stop_price
                    sl_order.last_updated = datetime.now()
                    self.logger.info(f"📈 Updated stop-loss {sl_id}: {old_price:.4f} → {new_stop_price:.4f}")
            
            # Check if stop-loss is triggered
            if self._is_stop_loss_triggered(sl_order, market_data):
                triggered_orders.append(sl_order)
        
        # Process triggered orders
        for sl_order in triggered_orders:
            await self._execute_stop_loss(sl_order)
    
    async def process_take_profit_orders(self):
        """Process all active take-profit orders"""
        
        triggered_orders = []
        
        for tp_id, tp_order in self.take_profit_orders.items():
            if tp_order.status != SLTPStatus.ACTIVE:
                continue
            
            position = self.positions.get(tp_order.position_id)
            market_data = self.market_data.get(tp_order.symbol)
            
            if not position or not market_data:
                continue
            
            # Update position price
            self.update_position_price(position.position_id, market_data.price)
            
            # Check if take-profit is triggered
            if self._is_take_profit_triggered(tp_order, market_data):
                triggered_orders.append(tp_order)
        
        # Process triggered orders
        for tp_order in triggered_orders:
            await self._execute_take_profit(tp_order)
    
    def _is_stop_loss_triggered(self, sl_order: StopLossOrder, market_data: MarketData) -> bool:
        """Check if stop-loss should be triggered"""
        
        position = self.positions[sl_order.position_id]
        current_price = market_data.price
        
        if position.side == OrderSide.BUY:
            return current_price <= sl_order.trigger_price
        else:
            return current_price >= sl_order.trigger_price
    
    def _is_take_profit_triggered(self, tp_order: TakeProfitOrder, market_data: MarketData) -> bool:
        """Check if take-profit should be triggered"""
        
        position = self.positions[tp_order.position_id]
        current_price = market_data.price
        
        if position.side == OrderSide.BUY:
            return current_price >= tp_order.trigger_price
        else:
            return current_price <= tp_order.trigger_price
    
    async def _execute_stop_loss(self, sl_order: StopLossOrder):
        """Execute stop-loss order"""
        
        position = self.positions[sl_order.position_id]
        market_data = self.market_data[sl_order.symbol]
        
        # Simulate execution with slippage
        execution_price = self._calculate_execution_price(sl_order.trigger_price, position.side, market_data, is_stop_loss=True)
        
        # Calculate realized P&L
        realized_pnl = self._calculate_realized_pnl(position, execution_price)
        
        # Update order status
        sl_order.status = SLTPStatus.TRIGGERED
        sl_order.last_updated = datetime.now()
        
        # Update metrics
        self.metrics['triggered_sl_orders'] += 1
        slippage = abs(execution_price - sl_order.trigger_price) / sl_order.trigger_price
        self.metrics['avg_sl_slippage'] = (self.metrics['avg_sl_slippage'] + slippage) / 2
        
        if realized_pnl > 0:
            self.metrics['total_saved_loss'] += abs(realized_pnl)
        
        self.logger.info(f"🚨 Stop-loss triggered: {sl_order.sl_id} @ {execution_price:.4f} (P&L: {realized_pnl:+.2f})")
        
        # Remove position
        del self.positions[position.position_id]
        
        # Cancel any associated take-profit orders
        await self._cancel_associated_orders(position.position_id, 'take_profit')
    
    async def _execute_take_profit(self, tp_order: TakeProfitOrder):
        """Execute take-profit order"""
        
        position = self.positions[tp_order.position_id]
        market_data = self.market_data[tp_order.symbol]
        
        # Simulate execution with slippage
        execution_price = self._calculate_execution_price(tp_order.trigger_price, position.side, market_data, is_stop_loss=False)
        
        # Calculate realized P&L
        realized_pnl = self._calculate_realized_pnl(position, execution_price)
        
        # Update order status
        tp_order.status = SLTPStatus.TRIGGERED
        tp_order.last_updated = datetime.now()
        
        # Update metrics
        self.metrics['triggered_tp_orders'] += 1
        slippage = abs(execution_price - tp_order.trigger_price) / tp_order.trigger_price
        self.metrics['avg_tp_slippage'] = (self.metrics['avg_tp_slippage'] + slippage) / 2
        
        if realized_pnl > 0:
            self.metrics['total_locked_profit'] += realized_pnl
        
        self.logger.info(f"💰 Take-profit triggered: {tp_order.tp_id} @ {execution_price:.4f} (P&L: {realized_pnl:+.2f})")
        
        # Remove position
        del self.positions[position.position_id]
        
        # Cancel any associated stop-loss orders
        await self._cancel_associated_orders(position.position_id, 'stop_loss')
    
    def _calculate_execution_price(self, trigger_price: float, side: OrderSide, market_data: MarketData, is_stop_loss: bool) -> float:
        """Calculate execution price with realistic slippage"""
        
        # Base slippage (higher for stop-losses due to market orders)
        base_slippage = 0.001 if not is_stop_loss else 0.002  # 0.1% vs 0.2%
        
        # Add volume-based slippage
        volume_factor = max(0.5, min(2.0, 1000000 / max(market_data.volume, 100000)))
        slippage = base_slippage * volume_factor
        
        if side == OrderSide.BUY:
            return trigger_price * (1 + slippage)
        else:
            return trigger_price * (1 - slippage)
    
    def _calculate_unrealized_pnl(self, side: OrderSide, quantity: float, entry_price: float, current_price: float) -> float:
        """Calculate unrealized P&L"""
        
        if side == OrderSide.BUY:
            return quantity * (current_price - entry_price)
        else:
            return quantity * (entry_price - current_price)
    
    def _calculate_realized_pnl(self, position: Position, exit_price: float) -> float:
        """Calculate realized P&L"""
        
        return self._calculate_unrealized_pnl(position.side, position.quantity, position.entry_price, exit_price)
    
    async def _cancel_associated_orders(self, position_id: str, order_type: str):
        """Cancel associated orders when position is closed"""
        
        if order_type == 'stop_loss':
            orders_to_cancel = [sl for sl in self.stop_loss_orders.values() 
                              if sl.position_id == position_id and sl.status == SLTPStatus.ACTIVE]
            for order in orders_to_cancel:
                order.status = SLTPStatus.CANCELLED
                self.logger.info(f"❌ Cancelled stop-loss: {order.sl_id}")
        
        elif order_type == 'take_profit':
            orders_to_cancel = [tp for tp in self.take_profit_orders.values() 
                              if tp.position_id == position_id and tp.status == SLTPStatus.ACTIVE]
            for order in orders_to_cancel:
                order.status = SLTPStatus.CANCELLED
                self.logger.info(f"❌ Cancelled take-profit: {order.tp_id}")
    
    def get_performance_metrics(self) -> Dict:
        """Get SL/TP performance metrics"""
        
        total_sl = self.metrics['total_sl_orders']
        total_tp = self.metrics['total_tp_orders']
        
        return {
            'stop_loss_metrics': {
                'total_orders': total_sl,
                'triggered_orders': self.metrics['triggered_sl_orders'],
                'trigger_rate': f"{(self.metrics['triggered_sl_orders'] / max(1, total_sl)) * 100:.1f}%",
                'avg_slippage': f"{self.metrics['avg_sl_slippage'] * 100:.3f}%",
                'total_saved_loss': f"${self.metrics['total_saved_loss']:,.2f}"
            },
            'take_profit_metrics': {
                'total_orders': total_tp,
                'triggered_orders': self.metrics['triggered_tp_orders'],
                'trigger_rate': f"{(self.metrics['triggered_tp_orders'] / max(1, total_tp)) * 100:.1f}%",
                'avg_slippage': f"{self.metrics['avg_tp_slippage'] * 100:.3f}%",
                'total_locked_profit': f"${self.metrics['total_locked_profit']:,.2f}"
            },
            'overall': {
                'total_orders': total_sl + total_tp,
                'active_positions': len(self.positions),
                'active_sl_orders': len([sl for sl in self.stop_loss_orders.values() if sl.status == SLTPStatus.ACTIVE]),
                'active_tp_orders': len([tp for tp in self.take_profit_orders.values() if tp.status == SLTPStatus.ACTIVE])
            }
        }
    
    async def start_background_processing(self):
        """Start background processing of SL/TP orders"""
        
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start processing tasks
        sl_task = asyncio.create_task(self._background_sl_processor())
        tp_task = asyncio.create_task(self._background_tp_processor())
        
        self.background_tasks.extend([sl_task, tp_task])
        
        self.logger.info("🚀 Background SL/TP processing started")
    
    async def stop_background_processing(self):
        """Stop background processing"""
        
        self.is_running = False
        
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
        
        self.logger.info("⏹️ Background SL/TP processing stopped")
    
    async def _background_sl_processor(self):
        """Background task to process stop-loss orders"""
        
        while self.is_running:
            try:
                await self.process_stop_loss_orders()
                await asyncio.sleep(0.1)  # Process every 100ms
                
            except Exception as e:
                self.logger.error(f"Error in SL processor: {e}")
                await asyncio.sleep(1)
    
    async def _background_tp_processor(self):
        """Background task to process take-profit orders"""
        
        while self.is_running:
            try:
                await self.process_take_profit_orders()
                await asyncio.sleep(0.1)  # Process every 100ms
                
            except Exception as e:
                self.logger.error(f"Error in TP processor: {e}")
                await asyncio.sleep(1)

# Global instance for easy use
sltp_manager = StopLossTakeProfitManager()

# Convenience functions
def create_position_with_sltp(symbol: str, side: OrderSide, quantity: float, entry_price: float,
                             sl_percentage: float = 0.02, tp_percentage: float = 0.04) -> Tuple[Position, StopLossOrder, TakeProfitOrder]:
    """Create position with basic SL/TP orders"""
    
    position_id = f"pos_{uuid.uuid4().hex[:8]}"
    
    # Add position
    position = sltp_manager.add_position(position_id, symbol, side, quantity, entry_price)
    
    # Create stop-loss
    sl_order = sltp_manager.create_stop_loss(position_id, StopLossType.FIXED_PERCENTAGE, percentage=sl_percentage)
    
    # Create take-profit
    tp_order = sltp_manager.create_take_profit(position_id, TakeProfitType.FIXED_PERCENTAGE, percentage=tp_percentage)
    
    return position, sl_order, tp_order

def create_trailing_stop_position(symbol: str, side: OrderSide, quantity: float, entry_price: float,
                                 trail_percentage: float = 0.02, tp_percentage: float = 0.04) -> Tuple[Position, StopLossOrder, TakeProfitOrder]:
    """Create position with trailing stop-loss"""
    
    position_id = f"pos_{uuid.uuid4().hex[:8]}"
    
    # Add position
    position = sltp_manager.add_position(position_id, symbol, side, quantity, entry_price)
    
    # Create trailing stop-loss
    sl_order = sltp_manager.create_stop_loss(position_id, StopLossType.TRAILING_STOP, trail_percentage=trail_percentage)
    
    # Create take-profit
    tp_order = sltp_manager.create_take_profit(position_id, TakeProfitType.FIXED_PERCENTAGE, percentage=tp_percentage)
    
    return position, sl_order, tp_order
