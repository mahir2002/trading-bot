#!/usr/bin/env python3
"""
🛡️ Dynamic Risk Management System
Addresses: "Risk parameters are static. Dynamic risk adjustment based on market volatility,
bot performance, or overall portfolio risk could be implemented."
Solution: Intelligent risk adjustment that adapts to market conditions and performance
"""

import asyncio
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
from collections import deque
import statistics
import math

class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"

class MarketRegime(Enum):
    """Market regime classifications"""
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"

class RiskAdjustmentTrigger(Enum):
    """Triggers for risk adjustment"""
    VOLATILITY_SPIKE = "volatility_spike"
    DRAWDOWN_LIMIT = "drawdown_limit"
    PERFORMANCE_DECLINE = "performance_decline"
    MARKET_REGIME_CHANGE = "market_regime_change"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_CRISIS = "liquidity_crisis"

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    # Volatility metrics
    price_volatility: float = 0.0
    returns_volatility: float = 0.0
    volatility_percentile: float = 0.0
    
    # Performance metrics
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    # Portfolio metrics
    portfolio_value: float = 0.0
    total_exposure: float = 0.0
    concentration_risk: float = 0.0
    correlation_risk: float = 0.0
    
    # Market metrics
    market_regime: MarketRegime = MarketRegime.SIDEWAYS
    liquidity_score: float = 1.0
    market_stress_index: float = 0.0
    
    # Risk scores
    overall_risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MODERATE

@dataclass
class RiskParameters:
    """Dynamic risk parameters that adjust based on conditions"""
    # Position sizing
    max_position_size: float = 0.1  # % of portfolio
    max_total_exposure: float = 0.8  # % of portfolio
    max_single_asset_exposure: float = 0.3  # % of portfolio
    
    # Stop losses
    stop_loss_percentage: float = 0.02  # 2%
    trailing_stop_percentage: float = 0.015  # 1.5%
    
    # Take profits
    take_profit_percentage: float = 0.04  # 4%
    profit_scaling_levels: List[float] = field(default_factory=lambda: [0.02, 0.03, 0.04])
    
    # Leverage and margin
    max_leverage: float = 2.0
    margin_buffer: float = 0.3  # 30% buffer
    
    # Correlation limits
    max_correlation: float = 0.7
    correlation_lookback: int = 30  # days
    
    # Volatility adjustments
    volatility_multiplier: float = 1.0
    volatility_lookback: int = 20  # days
    
    # Performance thresholds
    max_daily_loss: float = 0.05  # 5%
    max_weekly_loss: float = 0.15  # 15%
    max_monthly_loss: float = 0.25  # 25%
    
    # Emergency controls
    circuit_breaker_loss: float = 0.10  # 10% daily loss triggers emergency stop
    recovery_threshold: float = 0.02  # 2% gain needed to resume normal operations

@dataclass
class MarketData:
    """Market data for risk calculations"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    returns: List[float] = field(default_factory=list)
    volatility: float = 0.0
    liquidity_score: float = 1.0

class VolatilityCalculator:
    """Advanced volatility calculations"""
    
    @staticmethod
    def calculate_realized_volatility(returns: List[float], window: int = 20) -> float:
        """Calculate realized volatility using standard deviation"""
        if len(returns) < window:
            return 0.0
        
        recent_returns = returns[-window:]
        return np.std(recent_returns) * np.sqrt(252)  # Annualized
    
    @staticmethod
    def calculate_garch_volatility(returns: List[float]) -> float:
        """Simplified GARCH-like volatility calculation"""
        if len(returns) < 10:
            return 0.0
        
        # Simple EWMA volatility
        alpha = 0.06  # Decay factor
        variance = 0.0
        
        for i, ret in enumerate(returns[-20:]):
            weight = (1 - alpha) ** i
            variance += weight * (ret ** 2)
        
        return np.sqrt(variance * 252)  # Annualized
    
    @staticmethod
    def calculate_volatility_percentile(current_vol: float, historical_vols: List[float]) -> float:
        """Calculate percentile of current volatility vs historical"""
        if not historical_vols:
            return 50.0
        
        sorted_vols = sorted(historical_vols)
        position = sum(1 for vol in sorted_vols if vol <= current_vol)
        return (position / len(sorted_vols)) * 100

class PerformanceAnalyzer:
    """Analyze trading performance for risk adjustment"""
    
    def __init__(self):
        self.trade_history: List[Dict] = []
        self.equity_curve: List[float] = []
        self.daily_returns: List[float] = []
    
    def add_trade(self, trade: Dict):
        """Add trade to performance history"""
        self.trade_history.append({
            'timestamp': trade.get('timestamp', datetime.now()),
            'symbol': trade.get('symbol', ''),
            'side': trade.get('side', ''),
            'quantity': trade.get('quantity', 0),
            'entry_price': trade.get('entry_price', 0),
            'exit_price': trade.get('exit_price', 0),
            'pnl': trade.get('pnl', 0),
            'pnl_percentage': trade.get('pnl_percentage', 0)
        })
    
    def calculate_sharpe_ratio(self, lookback_days: int = 30) -> float:
        """Calculate Sharpe ratio"""
        if len(self.daily_returns) < lookback_days:
            return 0.0
        
        recent_returns = self.daily_returns[-lookback_days:]
        if not recent_returns:
            return 0.0
        
        mean_return = np.mean(recent_returns)
        std_return = np.std(recent_returns)
        
        if std_return == 0:
            return 0.0
        
        # Assuming 0% risk-free rate
        return (mean_return / std_return) * np.sqrt(252)
    
    def calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum and current drawdown"""
        if len(self.equity_curve) < 2:
            return 0.0, 0.0
        
        peak = self.equity_curve[0]
        max_drawdown = 0.0
        current_drawdown = 0.0
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Current drawdown
        current_peak = max(self.equity_curve)
        current_value = self.equity_curve[-1]
        current_drawdown = (current_peak - current_value) / current_peak
        
        return max_drawdown, current_drawdown
    
    def calculate_win_rate(self, lookback_trades: int = 50) -> float:
        """Calculate win rate"""
        if not self.trade_history:
            return 0.0
        
        recent_trades = self.trade_history[-lookback_trades:]
        winning_trades = sum(1 for trade in recent_trades if trade['pnl'] > 0)
        
        return winning_trades / len(recent_trades) if recent_trades else 0.0
    
    def calculate_profit_factor(self, lookback_trades: int = 50) -> float:
        """Calculate profit factor"""
        if not self.trade_history:
            return 0.0
        
        recent_trades = self.trade_history[-lookback_trades:]
        gross_profit = sum(trade['pnl'] for trade in recent_trades if trade['pnl'] > 0)
        gross_loss = abs(sum(trade['pnl'] for trade in recent_trades if trade['pnl'] < 0))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

class MarketRegimeDetector:
    """Detect market regimes for risk adjustment"""
    
    def __init__(self):
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[float]] = {}
    
    def update_data(self, symbol: str, price: float, volume: float):
        """Update market data"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.volume_history[symbol] = []
        
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)
        
        # Keep only recent data
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
            self.volume_history[symbol] = self.volume_history[symbol][-100:]
    
    def detect_regime(self, symbol: str) -> MarketRegime:
        """Detect current market regime"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return MarketRegime.SIDEWAYS
        
        prices = self.price_history[symbol]
        returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
        
        # Calculate metrics
        volatility = np.std(returns[-20:]) * np.sqrt(252)
        trend_strength = self._calculate_trend_strength(prices[-20:])
        
        # Regime classification
        if volatility > 0.4:  # 40% annualized volatility
            return MarketRegime.HIGH_VOLATILITY
        elif volatility < 0.1:  # 10% annualized volatility
            return MarketRegime.LOW_VOLATILITY
        elif trend_strength > 0.7:
            recent_return = prices[-1] / prices[-20] - 1
            return MarketRegime.BULL_TRENDING if recent_return > 0 else MarketRegime.BEAR_TRENDING
        else:
            return MarketRegime.SIDEWAYS
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """Calculate trend strength using linear regression R²"""
        if len(prices) < 5:
            return 0.0
        
        x = np.arange(len(prices))
        y = np.array(prices)
        
        # Linear regression
        correlation = np.corrcoef(x, y)[0, 1]
        return abs(correlation)
    
    def calculate_market_stress_index(self, symbols: List[str]) -> float:
        """Calculate overall market stress index"""
        stress_scores = []
        
        for symbol in symbols:
            if symbol in self.price_history and len(self.price_history[symbol]) >= 10:
                prices = self.price_history[symbol]
                returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
                
                # Stress indicators
                volatility = np.std(returns[-10:])
                negative_returns = sum(1 for r in returns[-10:] if r < -0.02)  # > 2% down days
                
                stress_score = volatility * 10 + negative_returns * 0.1
                stress_scores.append(stress_score)
        
        return np.mean(stress_scores) if stress_scores else 0.0

class DynamicRiskManager:
    """
    Comprehensive dynamic risk management system that adjusts parameters
    based on market volatility, bot performance, and portfolio risk
    """
    
    def __init__(self, initial_capital: float = 100000, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Core components
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_parameters = RiskParameters()
        self.base_risk_parameters = RiskParameters()  # Baseline for adjustments
        
        # Analysis components
        self.volatility_calculator = VolatilityCalculator()
        self.performance_analyzer = PerformanceAnalyzer()
        self.regime_detector = MarketRegimeDetector()
        
        # Data storage
        self.market_data: Dict[str, MarketData] = {}
        self.risk_metrics_history: List[RiskMetrics] = []
        self.adjustment_history: List[Dict] = []
        
        # Risk monitoring
        self.current_risk_metrics = RiskMetrics()
        self.emergency_mode = False
        self.last_adjustment_time = datetime.now()
        
        # Configuration
        self.adjustment_frequency = timedelta(minutes=15)  # Adjust every 15 minutes
        self.volatility_lookback = 20  # days
        self.performance_lookback = 30  # days
        
        self.logger.info("🛡️ Dynamic Risk Manager initialized")
    
    def update_market_data(self, symbol: str, price: float, volume: float):
        """Update market data for risk calculations"""
        
        if symbol not in self.market_data:
            self.market_data[symbol] = MarketData(symbol, price, volume, datetime.now())
        
        market_data = self.market_data[symbol]
        
        # Calculate return
        if market_data.price > 0:
            return_pct = (price / market_data.price) - 1
            market_data.returns.append(return_pct)
            
            # Keep only recent returns
            if len(market_data.returns) > 100:
                market_data.returns = market_data.returns[-100:]
        
        # Update data
        market_data.price = price
        market_data.volume = volume
        market_data.timestamp = datetime.now()
        
        # Calculate volatility
        if len(market_data.returns) >= 10:
            market_data.volatility = self.volatility_calculator.calculate_realized_volatility(
                market_data.returns, min(20, len(market_data.returns))
            )
        
        # Update regime detector
        self.regime_detector.update_data(symbol, price, volume)
    
    def update_portfolio_value(self, new_value: float):
        """Update current portfolio value"""
        
        if self.current_capital > 0:
            daily_return = (new_value / self.current_capital) - 1
            self.performance_analyzer.daily_returns.append(daily_return)
            
            # Keep only recent returns
            if len(self.performance_analyzer.daily_returns) > 252:  # 1 year
                self.performance_analyzer.daily_returns = self.performance_analyzer.daily_returns[-252:]
        
        self.current_capital = new_value
        self.performance_analyzer.equity_curve.append(new_value)
        
        # Keep only recent equity curve
        if len(self.performance_analyzer.equity_curve) > 252:
            self.performance_analyzer.equity_curve = self.performance_analyzer.equity_curve[-252:]
    
    def add_trade(self, trade_data: Dict):
        """Add completed trade for performance analysis"""
        self.performance_analyzer.add_trade(trade_data)
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        
        metrics = RiskMetrics()
        
        # Portfolio metrics - use current_capital instead of 0
        metrics.portfolio_value = self.current_capital
        
        # Performance metrics
        metrics.sharpe_ratio = self.performance_analyzer.calculate_sharpe_ratio(self.performance_lookback)
        max_dd, current_dd = self.performance_analyzer.calculate_max_drawdown()
        metrics.max_drawdown = max_dd
        metrics.current_drawdown = current_dd
        metrics.win_rate = self.performance_analyzer.calculate_win_rate()
        metrics.profit_factor = self.performance_analyzer.calculate_profit_factor()
        
        # Market metrics
        if self.market_data:
            # Average volatility across all symbols
            volatilities = [data.volatility for data in self.market_data.values() if data.volatility > 0]
            if volatilities:
                metrics.price_volatility = np.mean(volatilities)
                
                # Calculate volatility percentile
                historical_vols = []
                for data in self.market_data.values():
                    if len(data.returns) >= 20:
                        for i in range(20, len(data.returns)):
                            hist_vol = self.volatility_calculator.calculate_realized_volatility(
                                data.returns[i-20:i], 20
                            )
                            historical_vols.append(hist_vol)
                
                if historical_vols:
                    metrics.volatility_percentile = self.volatility_calculator.calculate_volatility_percentile(
                        metrics.price_volatility, historical_vols
                    )
            
            # Market regime
            symbols = list(self.market_data.keys())
            if symbols:
                regimes = [self.regime_detector.detect_regime(symbol) for symbol in symbols]
                # Use most common regime
                regime_counts = {}
                for regime in regimes:
                    regime_counts[regime] = regime_counts.get(regime, 0) + 1
                metrics.market_regime = max(regime_counts, key=regime_counts.get)
                
                # Market stress index
                metrics.market_stress_index = self.regime_detector.calculate_market_stress_index(symbols)
        
        # Calculate overall risk score
        metrics.overall_risk_score = self._calculate_overall_risk_score(metrics)
        metrics.risk_level = self._classify_risk_level(metrics.overall_risk_score)
        
        return metrics
    
    def _calculate_overall_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate overall risk score (0-100)"""
        
        score = 0.0
        
        # Volatility component (0-30 points)
        vol_score = min(30, metrics.volatility_percentile * 0.3)
        score += vol_score
        
        # Drawdown component (0-25 points)
        dd_score = min(25, metrics.current_drawdown * 250)  # 10% DD = 25 points
        score += dd_score
        
        # Performance component (0-20 points)
        if metrics.sharpe_ratio < 0:
            perf_score = 20  # Negative Sharpe = max risk
        elif metrics.sharpe_ratio < 1:
            perf_score = 15 - (metrics.sharpe_ratio * 15)
        else:
            perf_score = max(0, 10 - metrics.sharpe_ratio * 2)
        score += perf_score
        
        # Market stress component (0-15 points)
        stress_score = min(15, metrics.market_stress_index * 15)
        score += stress_score
        
        # Win rate component (0-10 points)
        if metrics.win_rate < 0.4:
            winrate_score = 10
        elif metrics.win_rate > 0.6:
            winrate_score = 0
        else:
            winrate_score = (0.6 - metrics.win_rate) * 50
        score += winrate_score
        
        return min(100, score)
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify risk level based on score"""
        
        if risk_score >= 80:
            return RiskLevel.EXTREME
        elif risk_score >= 65:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 35:
            return RiskLevel.MODERATE
        elif risk_score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def adjust_risk_parameters(self) -> Dict[str, Any]:
        """Dynamically adjust risk parameters based on current conditions"""
        
        # Check if adjustment is needed
        now = datetime.now()
        if now - self.last_adjustment_time < self.adjustment_frequency:
            return {"status": "no_adjustment", "reason": "too_soon"}
        
        # Calculate current risk metrics
        self.current_risk_metrics = self.calculate_risk_metrics()
        
        # Store metrics history
        self.risk_metrics_history.append(self.current_risk_metrics)
        if len(self.risk_metrics_history) > 100:
            self.risk_metrics_history = self.risk_metrics_history[-100:]
        
        # Determine adjustments needed
        adjustments = self._determine_adjustments()
        
        # Apply adjustments
        if adjustments:
            self._apply_adjustments(adjustments)
            
            # Log adjustment
            adjustment_record = {
                'timestamp': now,
                'risk_score': self.current_risk_metrics.overall_risk_score,
                'risk_level': self.current_risk_metrics.risk_level.value,
                'adjustments': adjustments,
                'trigger': self._identify_adjustment_trigger()
            }
            
            self.adjustment_history.append(adjustment_record)
            self.last_adjustment_time = now
            
            self.logger.info(f"🔧 Risk parameters adjusted: {adjustments}")
            
            return {
                "status": "adjusted",
                "adjustments": adjustments,
                "risk_level": self.current_risk_metrics.risk_level.value,
                "risk_score": self.current_risk_metrics.overall_risk_score
            }
        
        return {"status": "no_adjustment", "reason": "no_changes_needed"}
    
    def _determine_adjustments(self) -> Dict[str, float]:
        """Determine what adjustments are needed"""
        
        adjustments = {}
        metrics = self.current_risk_metrics
        base = self.base_risk_parameters
        
        # Risk level based adjustments
        risk_multiplier = self._get_risk_multiplier(metrics.risk_level)
        
        # Position sizing adjustments
        new_max_position = base.max_position_size * risk_multiplier
        if abs(new_max_position - self.risk_parameters.max_position_size) > 0.005:  # 0.5% threshold
            adjustments['max_position_size'] = new_max_position
        
        # Stop loss adjustments based on volatility
        vol_multiplier = 1.0
        if metrics.price_volatility > 0:
            # Increase stops in high volatility
            vol_multiplier = max(0.5, min(2.0, metrics.price_volatility / 0.2))  # Base 20% vol
        
        new_stop_loss = base.stop_loss_percentage * vol_multiplier * risk_multiplier
        if abs(new_stop_loss - self.risk_parameters.stop_loss_percentage) > 0.002:  # 0.2% threshold
            adjustments['stop_loss_percentage'] = new_stop_loss
        
        # Leverage adjustments
        new_leverage = base.max_leverage / risk_multiplier
        if abs(new_leverage - self.risk_parameters.max_leverage) > 0.1:
            adjustments['max_leverage'] = new_leverage
        
        # Exposure adjustments
        new_exposure = base.max_total_exposure * risk_multiplier
        if abs(new_exposure - self.risk_parameters.max_total_exposure) > 0.05:
            adjustments['max_total_exposure'] = new_exposure
        
        # Emergency adjustments
        if metrics.current_drawdown > 0.15:  # 15% drawdown
            adjustments['emergency_mode'] = True
            adjustments['max_position_size'] = base.max_position_size * 0.3  # Reduce to 30%
            adjustments['max_leverage'] = 1.0  # No leverage
        
        return adjustments
    
    def _get_risk_multiplier(self, risk_level: RiskLevel) -> float:
        """Get risk multiplier based on risk level"""
        
        multipliers = {
            RiskLevel.VERY_LOW: 1.5,    # Increase risk when safe
            RiskLevel.LOW: 1.2,
            RiskLevel.MODERATE: 1.0,    # Baseline
            RiskLevel.HIGH: 0.7,        # Reduce risk
            RiskLevel.VERY_HIGH: 0.4,
            RiskLevel.EXTREME: 0.2      # Minimal risk
        }
        
        return multipliers.get(risk_level, 1.0)
    
    def _apply_adjustments(self, adjustments: Dict[str, float]):
        """Apply risk parameter adjustments"""
        
        for param, value in adjustments.items():
            if param == 'emergency_mode':
                self.emergency_mode = value
            elif hasattr(self.risk_parameters, param):
                setattr(self.risk_parameters, param, value)
    
    def _identify_adjustment_trigger(self) -> RiskAdjustmentTrigger:
        """Identify what triggered the risk adjustment"""
        
        metrics = self.current_risk_metrics
        
        if metrics.current_drawdown > 0.1:
            return RiskAdjustmentTrigger.DRAWDOWN_LIMIT
        elif metrics.volatility_percentile > 90:
            return RiskAdjustmentTrigger.VOLATILITY_SPIKE
        elif metrics.sharpe_ratio < -0.5:
            return RiskAdjustmentTrigger.PERFORMANCE_DECLINE
        elif metrics.market_stress_index > 0.7:
            return RiskAdjustmentTrigger.LIQUIDITY_CRISIS
        else:
            return RiskAdjustmentTrigger.MARKET_REGIME_CHANGE
    
    def get_position_size_recommendation(self, symbol: str, signal_strength: float = 1.0) -> float:
        """Get recommended position size for a trade"""
        
        base_size = self.risk_parameters.max_position_size
        
        # Adjust for signal strength
        size = base_size * signal_strength
        
        # Adjust for symbol-specific volatility
        if symbol in self.market_data:
            symbol_vol = self.market_data[symbol].volatility
            if symbol_vol > 0:
                # Reduce size for high volatility assets
                vol_adjustment = min(1.0, 0.2 / symbol_vol)  # Base 20% volatility
                size *= vol_adjustment
        
        # Emergency mode adjustment
        if self.emergency_mode:
            size *= 0.3
        
        return min(size, self.risk_parameters.max_position_size)
    
    def get_stop_loss_recommendation(self, symbol: str, entry_price: float, side: str) -> float:
        """Get recommended stop loss price"""
        
        base_stop_pct = self.risk_parameters.stop_loss_percentage
        
        # Adjust for symbol volatility
        if symbol in self.market_data:
            symbol_vol = self.market_data[symbol].volatility
            if symbol_vol > 0:
                # Wider stops for high volatility
                vol_multiplier = max(1.0, symbol_vol / 0.2)  # Base 20% volatility
                stop_pct = base_stop_pct * vol_multiplier
            else:
                stop_pct = base_stop_pct
        else:
            stop_pct = base_stop_pct
        
        # Calculate stop price
        if side.lower() == 'buy':
            return entry_price * (1 - stop_pct)
        else:
            return entry_price * (1 + stop_pct)
    
    def should_halt_trading(self) -> Tuple[bool, str]:
        """Determine if trading should be halted"""
        
        metrics = self.current_risk_metrics
        
        # Circuit breaker conditions
        if metrics.current_drawdown > self.risk_parameters.circuit_breaker_loss:
            return True, f"Circuit breaker: {metrics.current_drawdown:.1%} drawdown"
        
        # Emergency mode
        if self.emergency_mode:
            return True, "Emergency mode activated"
        
        # Market stress
        if metrics.market_stress_index > 1.0:
            return True, f"High market stress: {metrics.market_stress_index:.2f}"
        
        # Performance degradation
        if metrics.sharpe_ratio < -1.0 and len(self.performance_analyzer.daily_returns) > 30:
            return True, f"Poor performance: Sharpe {metrics.sharpe_ratio:.2f}"
        
        return False, "Trading conditions normal"
    
    def get_risk_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive risk dashboard"""
        
        metrics = self.current_risk_metrics
        halt_trading, halt_reason = self.should_halt_trading()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'risk_level': metrics.risk_level.value,
            'risk_score': metrics.overall_risk_score,
            'market_regime': metrics.market_regime.value,
            
            'portfolio': {
                'value': metrics.portfolio_value,
                'drawdown_current': f"{metrics.current_drawdown:.1%}",
                'drawdown_max': f"{metrics.max_drawdown:.1%}",
                'sharpe_ratio': f"{metrics.sharpe_ratio:.2f}"
            },
            
            'market': {
                'volatility': f"{metrics.price_volatility:.1%}",
                'volatility_percentile': f"{metrics.volatility_percentile:.0f}th",
                'stress_index': f"{metrics.market_stress_index:.2f}"
            },
            
            'risk_parameters': {
                'max_position_size': f"{self.risk_parameters.max_position_size:.1%}",
                'stop_loss': f"{self.risk_parameters.stop_loss_percentage:.1%}",
                'max_leverage': f"{self.risk_parameters.max_leverage:.1f}x",
                'max_exposure': f"{self.risk_parameters.max_total_exposure:.1%}"
            },
            
            'controls': {
                'emergency_mode': self.emergency_mode,
                'halt_trading': halt_trading,
                'halt_reason': halt_reason
            },
            
            'recent_adjustments': len(self.adjustment_history),
            'last_adjustment': self.adjustment_history[-1]['timestamp'].isoformat() if self.adjustment_history else None
        }

# Global instance for easy use
risk_manager = DynamicRiskManager()

async def demo_dynamic_risk_management():
    """Demonstrate dynamic risk management capabilities"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("🛡️ DYNAMIC RISK MANAGEMENT DEMO")
    print("=" * 40)
    
    # Initialize risk manager
    risk_mgr = DynamicRiskManager(initial_capital=100000, logger=logger)
    
    print(f"💰 Initial Capital: ${risk_mgr.initial_capital:,.2f}")
    print(f"🎯 Base Risk Parameters:")
    print(f"   Max Position Size: {risk_mgr.base_risk_parameters.max_position_size:.1%}")
    print(f"   Stop Loss: {risk_mgr.base_risk_parameters.stop_loss_percentage:.1%}")
    print(f"   Max Leverage: {risk_mgr.base_risk_parameters.max_leverage:.1f}x")
    print()
    
    # Simulate market conditions and trading
    print("🎬 Simulating market conditions and trading...")
    
    # Phase 1: Normal market conditions
    print("\n📊 Phase 1: Normal Market Conditions")
    for day in range(10):
        # Simulate market data
        btc_price = 50000 + np.random.normal(0, 1000)  # Low volatility
        eth_price = 3000 + np.random.normal(0, 100)
        
        risk_mgr.update_market_data("BTC/USDT", btc_price, 1000000)
        risk_mgr.update_market_data("ETH/USDT", eth_price, 500000)
        
        # Simulate portfolio performance
        portfolio_change = np.random.normal(0.001, 0.01)  # Small positive drift
        new_value = risk_mgr.current_capital * (1 + portfolio_change)
        risk_mgr.update_portfolio_value(new_value)
        
        # Simulate some trades
        if day % 3 == 0:
            trade = {
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'quantity': 0.01,
                'entry_price': btc_price,
                'exit_price': btc_price * (1 + np.random.normal(0.01, 0.02)),
                'pnl': np.random.normal(100, 200),
                'pnl_percentage': np.random.normal(0.01, 0.02)
            }
            risk_mgr.add_trade(trade)
    
    # Check risk adjustment
    adjustment_result = risk_mgr.adjust_risk_parameters()
    print(f"   Risk Adjustment: {adjustment_result['status']}")
    
    dashboard = risk_mgr.get_risk_dashboard()
    print(f"   Risk Level: {dashboard['risk_level']}")
    print(f"   Portfolio Value: ${dashboard['portfolio']['value']:,.2f}")
    print(f"   Current Drawdown: {dashboard['portfolio']['drawdown_current']}")
    
    # Phase 2: High volatility period
    print("\n⚡ Phase 2: High Volatility Period")
    for day in range(15):
        # Simulate high volatility
        btc_price = 50000 + np.random.normal(0, 3000)  # High volatility
        eth_price = 3000 + np.random.normal(0, 300)
        
        risk_mgr.update_market_data("BTC/USDT", btc_price, 2000000)
        risk_mgr.update_market_data("ETH/USDT", eth_price, 1000000)
        
        # Simulate more volatile performance
        portfolio_change = np.random.normal(-0.002, 0.03)  # Negative drift, high vol
        new_value = risk_mgr.current_capital * (1 + portfolio_change)
        risk_mgr.update_portfolio_value(new_value)
        
        # Simulate trades with mixed results
        if day % 2 == 0:
            trade = {
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'quantity': 0.01,
                'entry_price': btc_price,
                'exit_price': btc_price * (1 + np.random.normal(-0.01, 0.04)),
                'pnl': np.random.normal(-50, 400),
                'pnl_percentage': np.random.normal(-0.01, 0.04)
            }
            risk_mgr.add_trade(trade)
    
    # Check risk adjustment
    adjustment_result = risk_mgr.adjust_risk_parameters()
    print(f"   Risk Adjustment: {adjustment_result['status']}")
    if adjustment_result['status'] == 'adjusted':
        print(f"   Adjustments Made: {list(adjustment_result['adjustments'].keys())}")
    
    dashboard = risk_mgr.get_risk_dashboard()
    print(f"   Risk Level: {dashboard['risk_level']}")
    print(f"   Portfolio Value: ${dashboard['portfolio']['value']:,.2f}")
    print(f"   Volatility: {dashboard['market']['volatility']}")
    
    # Phase 3: Drawdown period
    print("\n📉 Phase 3: Significant Drawdown")
    for day in range(10):
        # Simulate market crash
        btc_price = 50000 * (0.95 ** day)  # Declining market
        eth_price = 3000 * (0.96 ** day)
        
        risk_mgr.update_market_data("BTC/USDT", btc_price, 3000000)
        risk_mgr.update_market_data("ETH/USDT", eth_price, 1500000)
        
        # Simulate losses
        portfolio_change = np.random.normal(-0.02, 0.01)  # Consistent losses
        new_value = risk_mgr.current_capital * (1 + portfolio_change)
        risk_mgr.update_portfolio_value(new_value)
        
        # Simulate losing trades
        trade = {
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'quantity': 0.01,
            'entry_price': btc_price * 1.02,
            'exit_price': btc_price,
            'pnl': np.random.normal(-300, 100),
            'pnl_percentage': np.random.normal(-0.03, 0.01)
        }
        risk_mgr.add_trade(trade)
    
    # Check risk adjustment
    adjustment_result = risk_mgr.adjust_risk_parameters()
    print(f"   Risk Adjustment: {adjustment_result['status']}")
    if adjustment_result['status'] == 'adjusted':
        print(f"   Adjustments Made: {list(adjustment_result['adjustments'].keys())}")
    
    dashboard = risk_mgr.get_risk_dashboard()
    print(f"   Risk Level: {dashboard['risk_level']}")
    print(f"   Portfolio Value: ${dashboard['portfolio']['value']:,.2f}")
    print(f"   Current Drawdown: {dashboard['portfolio']['drawdown_current']}")
    
    # Check if trading should be halted
    halt_trading, halt_reason = risk_mgr.should_halt_trading()
    if halt_trading:
        print(f"   🚨 TRADING HALTED: {halt_reason}")
    
    # Final dashboard
    print("\n📊 FINAL RISK DASHBOARD")
    print("=" * 30)
    
    final_dashboard = risk_mgr.get_risk_dashboard()
    
    print(f"🎯 Risk Assessment:")
    print(f"   Risk Level: {final_dashboard['risk_level'].upper()}")
    print(f"   Risk Score: {final_dashboard['risk_score']:.1f}/100")
    print(f"   Market Regime: {final_dashboard['market_regime']}")
    
    print(f"\n💰 Portfolio Status:")
    print(f"   Current Value: ${final_dashboard['portfolio']['value']:,.2f}")
    print(f"   Total Return: {(final_dashboard['portfolio']['value'] / risk_mgr.initial_capital - 1):.1%}")
    print(f"   Current Drawdown: {final_dashboard['portfolio']['drawdown_current']}")
    print(f"   Max Drawdown: {final_dashboard['portfolio']['drawdown_max']}")
    print(f"   Sharpe Ratio: {final_dashboard['portfolio']['sharpe_ratio']}")
    
    print(f"\n📈 Market Conditions:")
    print(f"   Volatility: {final_dashboard['market']['volatility']}")
    print(f"   Volatility Percentile: {final_dashboard['market']['volatility_percentile']}")
    print(f"   Market Stress: {final_dashboard['market']['stress_index']}")
    
    print(f"\n⚙️ Current Risk Parameters:")
    print(f"   Max Position Size: {final_dashboard['risk_parameters']['max_position_size']}")
    print(f"   Stop Loss: {final_dashboard['risk_parameters']['stop_loss']}")
    print(f"   Max Leverage: {final_dashboard['risk_parameters']['max_leverage']}")
    print(f"   Max Exposure: {final_dashboard['risk_parameters']['max_exposure']}")
    
    print(f"\n🚨 Risk Controls:")
    print(f"   Emergency Mode: {final_dashboard['controls']['emergency_mode']}")
    print(f"   Halt Trading: {final_dashboard['controls']['halt_trading']}")
    if final_dashboard['controls']['halt_trading']:
        print(f"   Halt Reason: {final_dashboard['controls']['halt_reason']}")
    
    print(f"\n📋 Adjustment History:")
    print(f"   Total Adjustments: {final_dashboard['recent_adjustments']}")
    if final_dashboard['last_adjustment']:
        print(f"   Last Adjustment: {final_dashboard['last_adjustment'][:19]}")
    
    # Demonstrate position sizing recommendations
    print(f"\n🎯 Position Sizing Recommendations:")
    for symbol in ['BTC/USDT', 'ETH/USDT']:
        recommended_size = risk_mgr.get_position_size_recommendation(symbol, signal_strength=0.8)
        print(f"   {symbol}: {recommended_size:.1%} of portfolio")
    
    # Demonstrate stop loss recommendations
    print(f"\n🛡️ Stop Loss Recommendations:")
    btc_price = list(risk_mgr.market_data['BTC/USDT'].returns)[-1] if 'BTC/USDT' in risk_mgr.market_data else 50000
    stop_price = risk_mgr.get_stop_loss_recommendation('BTC/USDT', btc_price, 'buy')
    print(f"   BTC/USDT Long: Stop at ${stop_price:,.2f} ({((stop_price/btc_price)-1):.1%})")
    
    print("\n🎉 DYNAMIC RISK MANAGEMENT DEMO COMPLETE!")
    print("=" * 45)
    print("✅ Market volatility monitoring")
    print("✅ Performance-based risk adjustment")
    print("✅ Dynamic position sizing")
    print("✅ Adaptive stop losses")
    print("✅ Emergency risk controls")
    print("✅ Real-time risk dashboard")
    print("✅ Automated parameter adjustment")

if __name__ == "__main__":
    asyncio.run(demo_dynamic_risk_management()) 