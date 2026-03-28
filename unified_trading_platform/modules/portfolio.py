#!/usr/bin/env python3
"""
Portfolio Module - Comprehensive Portfolio Management and Analytics
Tracks positions, calculates P&L, manages portfolio metrics, and provides analytics
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

@dataclass
class Position:
    """Portfolio position."""
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    
    # Position details
    first_trade_time: datetime
    last_trade_time: datetime
    trade_count: int
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_profit: float = 0.0
    
    @property
    def pnl_percentage(self) -> float:
        """Calculate P&L percentage."""
        cost_basis = abs(self.quantity) * self.average_price
        return (self.unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0

@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    total_value: float
    total_pnl: float
    total_pnl_percentage: float
    unrealized_pnl: float
    realized_pnl: float
    
    # Risk metrics
    daily_var_95: float
    max_drawdown: float
    current_drawdown: float
    volatility: float
    sharpe_ratio: float
    
    # Performance metrics
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    
    # Position metrics
    long_positions: int
    short_positions: int
    total_positions: int
    
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Trade:
    """Individual trade record."""
    trade_id: str
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    
    # P&L (calculated when position is closed)
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None

class PortfolioModule(BaseModule):
    """Portfolio Module for the unified trading platform."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config or {})
        
        # Portfolio data
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.portfolio_history: List[PortfolioMetrics] = []
        
        # Portfolio settings
        self.initial_capital = self.config.get('initial_capital', 100000.0)
        self.current_capital = self.initial_capital
        self.cash_balance = self.initial_capital
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        
        # Current prices (from market data)
        self.current_prices: Dict[str, float] = {}
        
    async def initialize(self) -> bool:
        """Initialize the portfolio module."""
        try:
            self.logger.info("Initializing Portfolio Module...")
            
            # Initialize portfolio tracking
            await self._initialize_portfolio()
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Portfolio Module initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Portfolio Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """Start the portfolio module."""
        try:
            self.logger.info("Starting Portfolio Module...")
            
            # Start portfolio monitoring
            asyncio.create_task(self._portfolio_monitoring())
            asyncio.create_task(self._metrics_calculation())
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Portfolio Module started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Portfolio Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the portfolio module."""
        try:
            self.logger.info("Stopping Portfolio Module...")
            
            # Save portfolio state
            await self._save_portfolio_state()
            
            self.status = ModuleStatus.STOPPED
            self.logger.info("Portfolio Module stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Portfolio Module: {e}")
            return False
    
    async def handle_event(self, event: ModuleEvent) -> bool:
        """Process incoming events."""
        try:
            if event.event_type == "order_filled":
                await self._handle_order_filled(event)
            elif event.event_type == "market_data_update":
                await self._handle_market_data_update(event)
            elif event.event_type == "portfolio_request":
                await self._handle_portfolio_request(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            return False
    
    async def _handle_order_filled(self, event: ModuleEvent):
        """Handle filled orders to update positions."""
        try:
            data = event.data
            
            # Create trade record
            trade = Trade(
                trade_id=f"T_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                symbol=data['symbol'],
                side=data['side'],
                quantity=data['executed_quantity'],
                price=data['executed_price'],
                commission=data['commission'],
                timestamp=datetime.fromisoformat(data['timestamp'])
            )
            
            self.trades.append(trade)
            
            # Update position
            await self._update_position(trade)
            
            # Update cash balance
            trade_value = trade.quantity * trade.price
            if trade.side == 'BUY':
                self.cash_balance -= (trade_value + trade.commission)
            else:
                self.cash_balance += (trade_value - trade.commission)
            
            # Emit portfolio update
            await self._emit_portfolio_update()
            
        except Exception as e:
            self.logger.error(f"Error handling order filled: {e}")
    
    async def _handle_market_data_update(self, event: ModuleEvent):
        """Handle market data updates to update position values."""
        try:
            data = event.data
            symbol = data['symbol']
            price = data['price']
            
            # Update current price
            self.current_prices[symbol] = price
            
            # Update position if exists
            if symbol in self.positions:
                position = self.positions[symbol]
                old_market_value = position.market_value
                
                # Update position values
                position.current_price = price
                position.market_value = position.quantity * price
                position.unrealized_pnl = position.market_value - (position.quantity * position.average_price)
                position.total_pnl = position.realized_pnl + position.unrealized_pnl
                
                # Update max profit/drawdown
                if position.unrealized_pnl > position.max_profit:
                    position.max_profit = position.unrealized_pnl
                
                if position.unrealized_pnl < position.max_drawdown:
                    position.max_drawdown = position.unrealized_pnl
            
        except Exception as e:
            self.logger.error(f"Error handling market data update: {e}")
    
    async def _handle_portfolio_request(self, event: ModuleEvent):
        """Handle portfolio information requests."""
        try:
            # Calculate current metrics
            metrics = await self._calculate_portfolio_metrics()
            
            # Emit portfolio response
            await self.event_bus.emit(ModuleEvent(
                type="portfolio_response",
                data={
                    "metrics": metrics.__dict__,
                    "positions": {symbol: {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "average_price": pos.average_price,
                        "current_price": pos.current_price,
                        "market_value": pos.market_value,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "pnl_percentage": pos.pnl_percentage
                    } for symbol, pos in self.positions.items()},
                    "cash_balance": self.cash_balance,
                    "total_trades": len(self.trades)
                },
                priority=ModulePriority.NORMAL
            ))
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio request: {e}")
    
    async def _update_position(self, trade: Trade):
        """Update position based on trade."""
        try:
            symbol = trade.symbol
            
            if symbol not in self.positions:
                # Create new position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=0.0,
                    average_price=0.0,
                    current_price=trade.price,
                    market_value=0.0,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    total_pnl=0.0,
                    first_trade_time=trade.timestamp,
                    last_trade_time=trade.timestamp,
                    trade_count=0
                )
            
            position = self.positions[symbol]
            
            # Update position based on trade side
            if trade.side == 'BUY':
                # Calculate new average price
                if position.quantity >= 0:
                    # Adding to long position
                    total_cost = (position.quantity * position.average_price) + (trade.quantity * trade.price)
                    total_quantity = position.quantity + trade.quantity
                    position.average_price = total_cost / total_quantity if total_quantity > 0 else 0
                    position.quantity = total_quantity
                else:
                    # Covering short position
                    if abs(position.quantity) >= trade.quantity:
                        # Partial or full cover
                        realized_pnl = (position.average_price - trade.price) * trade.quantity
                        position.realized_pnl += realized_pnl
                        position.quantity += trade.quantity
                    else:
                        # Cover short and go long
                        cover_quantity = abs(position.quantity)
                        long_quantity = trade.quantity - cover_quantity
                        
                        # Realize P&L from covering short
                        realized_pnl = (position.average_price - trade.price) * cover_quantity
                        position.realized_pnl += realized_pnl
                        
                        # Set new long position
                        position.quantity = long_quantity
                        position.average_price = trade.price
            
            else:  # SELL
                if position.quantity > 0:
                    # Selling long position
                    if position.quantity >= trade.quantity:
                        # Partial or full sale
                        realized_pnl = (trade.price - position.average_price) * trade.quantity
                        position.realized_pnl += realized_pnl
                        position.quantity -= trade.quantity
                    else:
                        # Sell long and go short
                        sell_quantity = position.quantity
                        short_quantity = trade.quantity - sell_quantity
                        
                        # Realize P&L from selling long
                        realized_pnl = (trade.price - position.average_price) * sell_quantity
                        position.realized_pnl += realized_pnl
                        
                        # Set new short position
                        position.quantity = -short_quantity
                        position.average_price = trade.price
                else:
                    # Adding to short position
                    if position.quantity <= 0:
                        total_cost = (abs(position.quantity) * position.average_price) + (trade.quantity * trade.price)
                        total_quantity = abs(position.quantity) + trade.quantity
                        position.average_price = total_cost / total_quantity if total_quantity > 0 else 0
                        position.quantity = -total_quantity
            
            # Update position metadata
            position.last_trade_time = trade.timestamp
            position.trade_count += 1
            position.current_price = trade.price
            position.market_value = position.quantity * position.current_price
            position.unrealized_pnl = position.market_value - (position.quantity * position.average_price)
            position.total_pnl = position.realized_pnl + position.unrealized_pnl
            
            # Remove position if quantity is zero
            if abs(position.quantity) < 1e-8:
                del self.positions[symbol]
            
        except Exception as e:
            self.logger.error(f"Error updating position: {e}")
    
    async def _calculate_portfolio_metrics(self) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        try:
            # Calculate total values
            total_market_value = sum(pos.market_value for pos in self.positions.values())
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
            total_pnl = total_realized_pnl + total_unrealized_pnl
            
            total_value = self.cash_balance + total_market_value
            total_pnl_percentage = (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0
            
            # Calculate position counts
            long_positions = sum(1 for pos in self.positions.values() if pos.quantity > 0)
            short_positions = sum(1 for pos in self.positions.values() if pos.quantity < 0)
            total_positions = len(self.positions)
            
            # Calculate trade statistics
            closed_trades = [t for t in self.trades if t.pnl is not None]
            winning_trades = [t for t in closed_trades if t.pnl > 0]
            losing_trades = [t for t in closed_trades if t.pnl < 0]
            
            win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
            average_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            average_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
            
            gross_profit = sum(t.pnl for t in winning_trades)
            gross_loss = abs(sum(t.pnl for t in losing_trades))
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
            
            # Calculate risk metrics (simplified)
            daily_returns = self.daily_returns[-252:] if len(self.daily_returns) >= 252 else self.daily_returns
            volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
            
            # Calculate Sharpe ratio (assuming 0% risk-free rate)
            mean_return = np.mean(daily_returns) if daily_returns else 0
            sharpe_ratio = (mean_return * 252 / volatility) if volatility > 0 else 0
            
            # Calculate drawdown
            equity_values = [eq[1] for eq in self.equity_curve]
            if equity_values:
                peak = max(equity_values)
                current_value = equity_values[-1]
                current_drawdown = (peak - current_value) / peak if peak > 0 else 0
                
                # Calculate max drawdown
                max_drawdown = 0
                running_max = 0
                for value in equity_values:
                    if value > running_max:
                        running_max = value
                    drawdown = (running_max - value) / running_max if running_max > 0 else 0
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
            else:
                current_drawdown = 0
                max_drawdown = 0
            
            # Simple VaR calculation (95% confidence)
            daily_var_95 = np.percentile(daily_returns, 5) if len(daily_returns) > 20 else 0
            
            return PortfolioMetrics(
                total_value=total_value,
                total_pnl=total_pnl,
                total_pnl_percentage=total_pnl_percentage,
                unrealized_pnl=total_unrealized_pnl,
                realized_pnl=total_realized_pnl,
                daily_var_95=daily_var_95,
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                profit_factor=profit_factor,
                average_win=average_win,
                average_loss=average_loss,
                long_positions=long_positions,
                short_positions=short_positions,
                total_positions=total_positions
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {e}")
            return PortfolioMetrics(
                total_value=self.cash_balance,
                total_pnl=0, total_pnl_percentage=0,
                unrealized_pnl=0, realized_pnl=0,
                daily_var_95=0, max_drawdown=0, current_drawdown=0,
                volatility=0, sharpe_ratio=0,
                win_rate=0, profit_factor=0, average_win=0, average_loss=0,
                long_positions=0, short_positions=0, total_positions=0
            )
    
    async def _portfolio_monitoring(self):
        """Monitor portfolio and update metrics."""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Calculate current portfolio value
                total_market_value = sum(pos.market_value for pos in self.positions.values())
                current_value = self.cash_balance + total_market_value
                
                # Update equity curve
                self.equity_curve.append((datetime.now(), current_value))
                
                # Calculate daily return
                if len(self.equity_curve) > 1:
                    previous_value = self.equity_curve[-2][1]
                    daily_return = (current_value - previous_value) / previous_value if previous_value > 0 else 0
                    self.daily_returns.append(daily_return)
                
                # Limit history size
                if len(self.equity_curve) > 10000:
                    self.equity_curve = self.equity_curve[-5000:]
                if len(self.daily_returns) > 1000:
                    self.daily_returns = self.daily_returns[-500:]
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in portfolio monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _metrics_calculation(self):
        """Periodic metrics calculation and storage."""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Calculate and store metrics
                metrics = await self._calculate_portfolio_metrics()
                self.portfolio_history.append(metrics)
                
                # Limit history size
                if len(self.portfolio_history) > 1000:
                    self.portfolio_history = self.portfolio_history[-500:]
                
                # Emit metrics update
                await self.send_event(event_type="portfolio_metrics_update", data=metrics.__dict__, priority=ModulePriority.LOW
                )
                
                await asyncio.sleep(3600)  # Update every hour
                
            except Exception as e:
                self.logger.error(f"Error in metrics calculation: {e}")
                await asyncio.sleep(3600)
    
    async def _initialize_portfolio(self):
        """Initialize portfolio tracking."""
        try:
            # Load existing portfolio state if available
            # For now, start with clean slate
            self.logger.info(f"Initialized portfolio with {self.initial_capital} capital")
            
        except Exception as e:
            self.logger.error(f"Error initializing portfolio: {e}")
    
    async def _save_portfolio_state(self):
        """Save current portfolio state."""
        try:
            # Save portfolio state to file/database
            portfolio_state = {
                "positions": {symbol: {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "realized_pnl": pos.realized_pnl
                } for symbol, pos in self.positions.items()},
                "cash_balance": self.cash_balance,
                "total_trades": len(self.trades),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info("Portfolio state saved")
            
        except Exception as e:
            self.logger.error(f"Error saving portfolio state: {e}")
    
    async def _emit_portfolio_update(self):
        """Emit portfolio update event."""
        try:
            await self.event_bus.emit(ModuleEvent(
                type="portfolio_update",
                data={
                    "positions": {symbol: {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "market_value": pos.market_value,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "pnl_percentage": pos.pnl_percentage
                    } for symbol, pos in self.positions.items()},
                    "cash_balance": self.cash_balance,
                    "timestamp": datetime.now().isoformat()
                },
                priority=ModulePriority.NORMAL
            ))
            
        except Exception as e:
            self.logger.error(f"Error emitting portfolio update: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status."""
        total_value = self.cash_balance + sum(pos.market_value for pos in self.positions.values())
        total_pnl = sum(pos.total_pnl for pos in self.positions.values())
        
        return {
            **super().get_status(),
            "total_value": total_value,
            "total_pnl": total_pnl,
            "cash_balance": self.cash_balance,
            "positions": len(self.positions),
            "trades": len(self.trades)
        } 

    def get_module_info(self) -> ModuleInfo:
        """Return module information and metadata."""
        return ModuleInfo(
            name="portfolio",
            version="1.0.0",
            description="Portfolio Module",
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
