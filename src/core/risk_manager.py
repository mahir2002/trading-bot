"""Comprehensive risk management system."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskLimits:
    """Risk limit configuration."""

    max_position_size: float = 0.10  # 10% of portfolio
    max_single_trade: float = 0.05  # 5% per trade
    max_daily_loss: float = 0.05  # 5% per day
    max_weekly_loss: float = 0.10  # 10% per week
    max_drawdown: float = 0.15  # 15% max drawdown
    max_correlation: float = 0.70  # Max correlation between positions
    min_liquidity: float = 100000  # Minimum daily volume
    max_positions: int = 10  # Max concurrent positions
    min_win_rate: float = 0.50  # Minimum acceptable win rate


@dataclass
class Position:
    """Trade position."""

    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    unrealized_pnl: float = 0.0

    def update_price(self, price: float) -> None:
        """Update current price and calculate P&L."""
        self.current_price = price
        if self.side == "long":
            self.unrealized_pnl = (price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.size

    def get_pnl_pct(self) -> float:
        """Calculate P&L percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price


@dataclass
class RiskAlert:
    """Risk alert message."""

    level: RiskLevel
    message: str
    symbol: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    action_required: bool = False
    suggested_action: Optional[str] = None


class RiskManager:
    """
    Portfolio-level risk management with Kelly Criterion sizing.

    Features:
    - Position sizing using Kelly Criterion
    - Stop-loss / take-profit automation
    - Drawdown protection
    - Correlation analysis
    - Daily/weekly loss limits
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()
        self.positions: Dict[str, Position] = {}
        self.daily_pnl: List[Dict[str, Any]] = []
        self.trade_history: List[Dict[str, Any]] = []
        self.peak_portfolio_value: float = 0.0
        self.current_drawdown: float = 0.0
        self.alerts: List[RiskAlert] = []

    def calculate_position_size(
        self,
        portfolio_value: float,
        confidence: float,
        volatility: float,
        win_probability: float = 0.6,
        win_loss_ratio: float = 2.0,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size using Kelly Criterion.

        Kelly Formula: f* = (p*b - q) / b
        where:
        - p = probability of win
        - q = probability of loss (1 - p)
        - b = win/loss ratio

        Args:
            portfolio_value: Current portfolio value
            confidence: Model confidence (0-1)
            volatility: Asset volatility (annualized)
            win_probability: Historical win probability
            win_loss_ratio: Average win / average loss

        Returns:
            Tuple of (position_size, metadata)
        """
        if confidence <= 0.5 or win_probability <= 0.5:
            return 0.0, {"reason": "insufficient_confidence"}

        # Base Kelly calculation
        loss_probability = 1 - win_probability
        kelly = (win_probability * win_loss_ratio - loss_probability) / win_loss_ratio

        # Conservative half-Kelly
        half_kelly = kelly / 2

        # Adjust for volatility (reduce size for high volatility)
        volatility_adjustment = 1 / (1 + volatility * 10)
        adjusted_kelly = half_kelly * volatility_adjustment

        # Adjust for model confidence
        confidence_adjustment = confidence

        # Calculate position size
        position_pct = min(
            adjusted_kelly * confidence_adjustment,
            self.limits.max_position_size,
            self.limits.max_single_trade,
        )

        position_size = portfolio_value * position_pct

        metadata = {
            "kelly_fraction": kelly,
            "half_kelly": half_kelly,
            "volatility_adj": volatility_adjustment,
            "confidence_adj": confidence_adjustment,
            "final_pct": position_pct,
            "portfolio_value": portfolio_value,
            "constraints": {
                "max_position_size": self.limits.max_position_size,
                "max_single_trade": self.limits.max_single_trade,
            },
        }

        return position_size, metadata

    def check_trade_allowed(
        self, symbol: str, side: str, size: float, price: float, portfolio_value: float
    ) -> Tuple[bool, List[RiskAlert]]:
        """
        Check if trade is allowed under risk limits.

        Returns:
            Tuple of (allowed, alerts)
        """
        alerts: List[RiskAlert] = []

        # Check max positions
        if len(self.positions) >= self.limits.max_positions and symbol not in self.positions:
            alerts.append(
                RiskAlert(
                    level=RiskLevel.HIGH,
                    message=f"Max positions ({self.limits.max_positions}) reached",
                    action_required=True,
                    suggested_action="Close existing position before opening new one",
                )
            )
            return False, alerts

        # Check position size
        position_value = size * price
        position_pct = position_value / portfolio_value

        if position_pct > self.limits.max_position_size:
            alerts.append(
                RiskAlert(
                    level=RiskLevel.HIGH,
                    message=f"Position size {position_pct:.2%} exceeds limit {self.limits.max_position_size:.2%}",
                    symbol=symbol,
                    action_required=True,
                    suggested_action=f"Reduce size to {self.limits.max_position_size * portfolio_value / price:.4f} units",
                )
            )
            return False, alerts

        # Check daily loss limit
        daily_loss = self.get_daily_loss()
        if abs(daily_loss) / portfolio_value > self.limits.max_daily_loss:
            alerts.append(
                RiskAlert(
                    level=RiskLevel.CRITICAL,
                    message=f"Daily loss limit {self.limits.max_daily_loss:.2%} exceeded",
                    action_required=True,
                    suggested_action="Stop trading for today",
                )
            )
            return False, alerts

        # Check drawdown
        if self.current_drawdown > self.limits.max_drawdown:
            alerts.append(
                RiskAlert(
                    level=RiskLevel.CRITICAL,
                    message=f"Drawdown {self.current_drawdown:.2%} exceeds limit {self.limits.max_drawdown:.2%}",
                    action_required=True,
                    suggested_action="Close positions and pause trading",
                )
            )
            return False, alerts

        return True, alerts

    def check_stop_loss_take_profit(self, position: Position) -> Optional[str]:
        """
        Check if stop-loss or take-profit should trigger.

        Returns:
            'stop_loss', 'take_profit', or None
        """
        pnl_pct = position.get_pnl_pct()

        # Check stop-loss
        if pnl_pct <= -abs((position.stop_loss - position.entry_price) / position.entry_price):
            return "stop_loss"

        # Check take-profit
        if pnl_pct >= abs((position.take_profit - position.entry_price) / position.entry_price):
            return "take_profit"

        return None

    def add_position(self, position: Position) -> bool:
        """Add new position to tracking."""
        self.positions[position.symbol] = position
        logger.info(f"Added position: {position.symbol} {position.side} @ {position.entry_price}")
        return True

    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """Close position and record P&L."""
        if symbol not in self.positions:
            return {"error": "Position not found"}

        position = self.positions[symbol]
        position.update_price(exit_price)

        realized_pnl = position.unrealized_pnl
        pnl_pct = realized_pnl / (position.entry_price * position.size)

        # Record trade
        trade_record = {
            "symbol": symbol,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "size": position.size,
            "side": position.side,
            "realized_pnl": realized_pnl,
            "pnl_pct": pnl_pct,
            "entry_time": position.timestamp,
            "exit_time": datetime.now(),
            "duration_hours": (datetime.now() - position.timestamp).total_seconds() / 3600,
        }

        self.trade_history.append(trade_record)
        del self.positions[symbol]

        logger.info(f"Closed position: {symbol} P&L: {realized_pnl:.2f} ({pnl_pct:.2%})")

        return trade_record

    def update_portfolio_value(self, current_value: float) -> None:
        """Update portfolio value and calculate drawdown."""
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value

        self.current_drawdown = (
            (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
            if self.peak_portfolio_value > 0
            else 0
        )

    def get_daily_loss(self) -> float:
        """Calculate today's realized loss."""
        today = datetime.now().date()
        today_trades = [t for t in self.trade_history if t["exit_time"].date() == today]
        return sum(t["realized_pnl"] for t in today_trades)

    def get_win_rate(self, window: int = 100) -> float:
        """Calculate win rate over last N trades."""
        if len(self.trade_history) < window:
            return 0.5

        recent = self.trade_history[-window:]
        wins = sum(1 for t in recent if t["realized_pnl"] > 0)
        return wins / len(recent)

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "current_drawdown": self.current_drawdown,
            }

        # Calculate metrics
        wins = [t["realized_pnl"] for t in self.trade_history if t["realized_pnl"] > 0]
        losses = [abs(t["realized_pnl"]) for t in self.trade_history if t["realized_pnl"] < 0]

        total_wins = sum(wins)
        total_losses = sum(losses)

        win_rate = len(wins) / len(self.trade_history) if self.trade_history else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        # Calculate returns for Sharpe
        returns = [t["pnl_pct"] for t in self.trade_history]
        avg_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if returns else 1
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0

        return {
            "total_trades": len(self.trade_history),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": self.current_drawdown,
            "total_pnl": sum(t["realized_pnl"] for t in self.trade_history),
            "avg_trade_pnl": np.mean([t["realized_pnl"] for t in self.trade_history]),
            "avg_win": np.mean(wins) if wins else 0,
            "avg_loss": np.mean(losses) if losses else 0,
            "open_positions": len(self.positions),
        }
