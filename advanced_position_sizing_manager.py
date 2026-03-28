#!/usr/bin/env python3
"""
📊 Advanced Position Sizing Management System
Addresses: "Position Sizing: The confidence_multiplier is a good start, but more
advanced position sizing strategies (e.g., Kelly Criterion, fixed fractional)
could be explored."
Solution: Comprehensive position sizing with multiple advanced strategies and dynamic optimization
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
import scipy.optimize as optimize
from scipy.stats import norm

class PositionSizingMethod(Enum):
    """Position sizing strategy types"""
    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY_CRITERION = "kelly_criterion"
    OPTIMAL_F = "optimal_f"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    RISK_PARITY = "risk_parity"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    SHARPE_OPTIMIZED = "sharpe_optimized"
    VAR_BASED = "var_based"
    MONTE_CARLO = "monte_carlo"
    ADAPTIVE_KELLY = "adaptive_kelly"

class RiskLevel(Enum):
    """Risk level classifications"""
    ULTRA_LOW = ("ultra_low", 0.01)
    LOW = ("low", 0.02)
    MODERATE = ("moderate", 0.05)
    HIGH = ("high", 0.10)
    AGGRESSIVE = ("aggressive", 0.20)

class MarketRegime(Enum):
    """Market regime classifications"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"

@dataclass
class TradingSignal:
    """Enhanced trading signal with comprehensive data"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    expected_return: float
    expected_volatility: float
    win_probability: float
    avg_win: float
    avg_loss: float
    holding_period: int  # Expected holding period in days
    market_regime: MarketRegime
    risk_level: RiskLevel
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PositionSizingParameters:
    """Parameters for position sizing calculations"""
    # Basic parameters
    max_position_size: float = 0.20  # 20% max per position
    max_total_exposure: float = 0.80  # 80% max total exposure
    min_position_size: float = 0.01   # 1% minimum position
    
    # Kelly Criterion parameters
    kelly_safety_factor: float = 0.25  # Use 25% of Kelly
    kelly_max_fraction: float = 0.15   # Cap Kelly at 15%
    
    # Risk management
    max_correlation: float = 0.70      # Max correlation between positions
    volatility_lookback: int = 30      # Days for volatility calculation
    
    # Adaptive parameters
    confidence_threshold: float = 0.60  # Minimum confidence for trading
    regime_adjustments: Dict[MarketRegime, float] = field(default_factory=lambda: {
        MarketRegime.BULL: 1.2,
        MarketRegime.BEAR: 0.6,
        MarketRegime.SIDEWAYS: 1.0,
        MarketRegime.HIGH_VOLATILITY: 0.5,
        MarketRegime.LOW_VOLATILITY: 1.1,
        MarketRegime.CRISIS: 0.3
    })

@dataclass
class PositionSizingResult:
    """Result of position sizing calculation"""
    symbol: str
    method: PositionSizingMethod
    recommended_size: float
    max_size: float
    confidence: float
    expected_return: float
    risk_metrics: Dict[str, float]
    reasoning: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class PositionSizingStrategy(ABC):
    """Abstract base class for position sizing strategies"""
    
    @abstractmethod
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate optimal position size"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        pass

class FixedFractionalSizing(PositionSizingStrategy):
    """Fixed fractional position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size using fixed fractional method"""
        
        # Base fractional size
        base_fraction = parameters.max_position_size
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        
        # Adjust for risk level
        risk_factor = signal.risk_level.value[1] / 0.10  # Normalize to moderate risk
        
        # Adjust for market regime
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        
        # Calculate final fraction
        position_fraction = base_fraction * confidence_factor * risk_factor * regime_factor
        
        # Apply bounds
        position_fraction = max(parameters.min_position_size, 
                              min(position_fraction, parameters.max_position_size))
        
        return position_fraction
    
    def get_strategy_name(self) -> str:
        return "Fixed Fractional"

class KellyCriterionSizing(PositionSizingStrategy):
    """Kelly Criterion position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size using Kelly Criterion"""
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds received, p = win probability, q = loss probability
        
        if signal.avg_loss == 0 or signal.win_probability == 0:
            return parameters.min_position_size
        
        # Calculate odds ratio
        b = abs(signal.avg_win / signal.avg_loss)
        p = signal.win_probability
        q = 1 - p
        
        # Kelly fraction
        kelly_fraction = (b * p - q) / b
        
        # Apply safety factor
        safe_kelly = kelly_fraction * parameters.kelly_safety_factor
        
        # Cap at maximum Kelly fraction
        safe_kelly = min(safe_kelly, parameters.kelly_max_fraction)
        
        # Ensure positive and within bounds
        safe_kelly = max(0, min(safe_kelly, parameters.max_position_size))
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        final_size = safe_kelly * confidence_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        return max(parameters.min_position_size, final_size)
    
    def get_strategy_name(self) -> str:
        return "Kelly Criterion"

class OptimalFSizing(PositionSizingStrategy):
    """Optimal F position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size using Optimal F method"""
        
        # Simulate trade outcomes based on signal parameters
        num_simulations = 1000
        
        # Generate random trade outcomes
        outcomes = []
        for _ in range(num_simulations):
            if np.random.random() < signal.win_probability:
                outcome = signal.avg_win
            else:
                outcome = -signal.avg_loss
            outcomes.append(outcome)
        
        # Find optimal f that maximizes geometric mean
        def geometric_mean(f, outcomes):
            if f <= 0 or f >= 1:
                return -np.inf
            
            total = 1.0
            for outcome in outcomes:
                new_value = 1 + f * outcome
                if new_value <= 0:
                    return -np.inf
                total *= new_value
            
            return total ** (1.0 / len(outcomes))
        
        # Optimize f
        result = optimize.minimize_scalar(
            lambda f: -geometric_mean(f, outcomes),
            bounds=(0.001, 0.5),
            method='bounded'
        )
        
        optimal_f = result.x if result.success else 0.05
        
        # Apply safety factor and bounds
        safe_f = optimal_f * 0.5  # 50% of optimal for safety
        safe_f = max(parameters.min_position_size, 
                    min(safe_f, parameters.max_position_size))
        
        # Adjust for confidence and regime
        confidence_factor = signal.confidence / 100
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        
        final_size = safe_f * confidence_factor * regime_factor
        
        return max(parameters.min_position_size, final_size)
    
    def get_strategy_name(self) -> str:
        return "Optimal F"

class VolatilityAdjustedSizing(PositionSizingStrategy):
    """Volatility-adjusted position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size adjusted for volatility"""
        
        # Base position size
        base_size = parameters.max_position_size
        
        # Target volatility (e.g., 2% daily)
        target_volatility = 0.02
        
        # Adjust for actual volatility
        if signal.expected_volatility > 0:
            volatility_adjustment = target_volatility / signal.expected_volatility
            volatility_adjustment = max(0.2, min(volatility_adjustment, 2.0))  # Bound adjustment
        else:
            volatility_adjustment = 1.0
        
        # Apply volatility adjustment
        vol_adjusted_size = base_size * volatility_adjustment
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        
        # Adjust for expected return
        return_factor = max(0.5, min(2.0, 1 + signal.expected_return * 10))
        
        # Final calculation
        final_size = vol_adjusted_size * confidence_factor * return_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        # Apply bounds
        return max(parameters.min_position_size, 
                  min(final_size, parameters.max_position_size))
    
    def get_strategy_name(self) -> str:
        return "Volatility Adjusted"

class RiskParitySizing(PositionSizingStrategy):
    """Risk parity position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size using risk parity approach"""
        
        # Target risk contribution per position
        target_risk_per_position = 0.02  # 2% risk per position
        
        # Calculate position size based on volatility
        if signal.expected_volatility > 0:
            # Position size = Target Risk / Volatility
            risk_based_size = target_risk_per_position / signal.expected_volatility
        else:
            risk_based_size = parameters.max_position_size
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        
        # Adjust for win probability
        win_prob_factor = signal.win_probability if signal.win_probability > 0 else 0.5
        
        # Calculate final size
        final_size = risk_based_size * confidence_factor * win_prob_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        # Apply bounds
        return max(parameters.min_position_size, 
                  min(final_size, parameters.max_position_size))
    
    def get_strategy_name(self) -> str:
        return "Risk Parity"

class ConfidenceWeightedSizing(PositionSizingStrategy):
    """Enhanced confidence-weighted position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size with advanced confidence weighting"""
        
        # Base size from confidence (non-linear scaling)
        confidence_normalized = signal.confidence / 100
        
        # Use power function for non-linear confidence scaling
        confidence_power = 1.5  # Emphasize high confidence more
        confidence_factor = confidence_normalized ** confidence_power
        
        # Expected return factor
        return_factor = max(0.1, min(3.0, 1 + signal.expected_return * 5))
        
        # Win probability factor
        win_prob_factor = signal.win_probability if signal.win_probability > 0 else 0.5
        
        # Risk-adjusted factor
        if signal.avg_loss > 0:
            risk_reward = signal.avg_win / signal.avg_loss
            risk_factor = max(0.5, min(2.0, risk_reward / 2.0))
        else:
            risk_factor = 1.0
        
        # Combine factors
        base_size = parameters.max_position_size
        final_size = base_size * confidence_factor * return_factor * win_prob_factor * risk_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        # Apply bounds
        return max(parameters.min_position_size, 
                  min(final_size, parameters.max_position_size))
    
    def get_strategy_name(self) -> str:
        return "Confidence Weighted"

class SharpeOptimizedSizing(PositionSizingStrategy):
    """Sharpe ratio optimized position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size to optimize Sharpe ratio"""
        
        # Risk-free rate (assume 2% annually, convert to daily)
        risk_free_rate = 0.02 / 252
        
        # Expected excess return
        excess_return = signal.expected_return - risk_free_rate
        
        # Sharpe-optimal position size
        if signal.expected_volatility > 0 and excess_return > 0:
            # Optimal leverage = (excess return) / (variance)
            optimal_leverage = excess_return / (signal.expected_volatility ** 2)
            
            # Convert to position size (cap at reasonable levels)
            sharpe_size = min(optimal_leverage, parameters.max_position_size * 2)
        else:
            sharpe_size = parameters.min_position_size
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        
        # Adjust for win probability
        win_prob_factor = signal.win_probability if signal.win_probability > 0 else 0.5
        
        # Final calculation
        final_size = sharpe_size * confidence_factor * win_prob_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        # Apply bounds
        return max(parameters.min_position_size, 
                  min(final_size, parameters.max_position_size))
    
    def get_strategy_name(self) -> str:
        return "Sharpe Optimized"

class VaRBasedSizing(PositionSizingStrategy):
    """Value at Risk based position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size based on Value at Risk"""
        
        # Target VaR (e.g., 1% daily VaR)
        target_var = 0.01
        confidence_level = 0.05  # 95% confidence
        
        # Calculate VaR for this position
        if signal.expected_volatility > 0:
            # Assume normal distribution
            z_score = norm.ppf(confidence_level)
            position_var = abs(z_score * signal.expected_volatility)
            
            # Position size to achieve target VaR
            var_based_size = target_var / position_var if position_var > 0 else parameters.min_position_size
        else:
            var_based_size = parameters.max_position_size
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        
        # Adjust for expected return
        if signal.expected_return > 0:
            return_factor = min(2.0, 1 + signal.expected_return * 5)
        else:
            return_factor = 0.5
        
        # Final calculation
        final_size = var_based_size * confidence_factor * return_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        # Apply bounds
        return max(parameters.min_position_size, 
                  min(final_size, parameters.max_position_size))
    
    def get_strategy_name(self) -> str:
        return "VaR Based"

class MonteCarloSizing(PositionSizingStrategy):
    """Monte Carlo simulation based position sizing strategy"""
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size using Monte Carlo simulation"""
        
        num_simulations = 1000
        position_sizes = np.linspace(parameters.min_position_size, parameters.max_position_size, 20)
        
        best_size = parameters.min_position_size
        best_score = -np.inf
        
        for size in position_sizes:
            # Simulate outcomes for this position size
            final_values = []
            
            for _ in range(num_simulations):
                # Simulate trade outcome
                if np.random.random() < signal.win_probability:
                    return_pct = signal.avg_win
                else:
                    return_pct = -signal.avg_loss
                
                # Calculate portfolio impact
                position_value = portfolio_value * size
                pnl = position_value * return_pct
                final_value = portfolio_value + pnl
                final_values.append(final_value)
            
            # Calculate score (risk-adjusted return)
            mean_return = np.mean(final_values) - portfolio_value
            std_return = np.std(final_values)
            
            if std_return > 0:
                sharpe_score = mean_return / std_return
            else:
                sharpe_score = 0
            
            # Penalize for downside risk
            downside_risk = np.mean([min(0, fv - portfolio_value) for fv in final_values])
            adjusted_score = sharpe_score - abs(downside_risk) / portfolio_value * 10
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_size = size
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        final_size = best_size * confidence_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        # Apply bounds
        return max(parameters.min_position_size, 
                  min(final_size, parameters.max_position_size))
    
    def get_strategy_name(self) -> str:
        return "Monte Carlo"

class AdaptiveKellySizing(PositionSizingStrategy):
    """Adaptive Kelly Criterion with dynamic parameter estimation"""
    
    def __init__(self):
        self.trade_history = []
        self.lookback_period = 50
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              current_positions: Dict, parameters: PositionSizingParameters) -> float:
        """Calculate position size using adaptive Kelly with historical data"""
        
        # Use historical data if available
        if len(self.trade_history) >= 10:
            recent_trades = self.trade_history[-self.lookback_period:]
            
            # Calculate empirical win rate and average returns
            wins = [t for t in recent_trades if t['return'] > 0]
            losses = [t for t in recent_trades if t['return'] <= 0]
            
            if len(wins) > 0 and len(losses) > 0:
                empirical_win_rate = len(wins) / len(recent_trades)
                empirical_avg_win = np.mean([t['return'] for t in wins])
                empirical_avg_loss = abs(np.mean([t['return'] for t in losses]))
                
                # Use empirical data for Kelly calculation
                if empirical_avg_loss > 0:
                    b = empirical_avg_win / empirical_avg_loss
                    p = empirical_win_rate
                    q = 1 - p
                    
                    kelly_fraction = (b * p - q) / b
                else:
                    kelly_fraction = 0.05
            else:
                # Fall back to signal data
                kelly_fraction = self._calculate_basic_kelly(signal)
        else:
            # Use signal data for Kelly calculation
            kelly_fraction = self._calculate_basic_kelly(signal)
        
        # Apply adaptive safety factor based on recent performance
        if len(self.trade_history) >= 5:
            recent_returns = [t['return'] for t in self.trade_history[-10:]]
            volatility = np.std(recent_returns) if len(recent_returns) > 1 else 0.1
            
            # Reduce Kelly fraction in high volatility periods
            safety_factor = max(0.1, min(0.5, 0.3 / max(volatility, 0.01)))
        else:
            safety_factor = parameters.kelly_safety_factor
        
        # Apply safety factor
        safe_kelly = kelly_fraction * safety_factor
        
        # Cap at maximum
        safe_kelly = min(safe_kelly, parameters.kelly_max_fraction)
        
        # Ensure positive and within bounds
        safe_kelly = max(0, min(safe_kelly, parameters.max_position_size))
        
        # Adjust for confidence
        confidence_factor = signal.confidence / 100
        final_size = safe_kelly * confidence_factor
        
        # Apply regime adjustment
        regime_factor = parameters.regime_adjustments.get(signal.market_regime, 1.0)
        final_size *= regime_factor
        
        return max(parameters.min_position_size, final_size)
    
    def _calculate_basic_kelly(self, signal: TradingSignal) -> float:
        """Calculate basic Kelly fraction from signal data"""
        if signal.avg_loss == 0 or signal.win_probability == 0:
            return 0.05
        
        b = abs(signal.avg_win / signal.avg_loss)
        p = signal.win_probability
        q = 1 - p
        
        return max(0, (b * p - q) / b)
    
    def add_trade_result(self, symbol: str, return_pct: float, holding_period: int):
        """Add trade result to history for adaptive learning"""
        self.trade_history.append({
            'symbol': symbol,
            'return': return_pct,
            'holding_period': holding_period,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.trade_history) > self.lookback_period * 2:
            self.trade_history = self.trade_history[-self.lookback_period:]
    
    def get_strategy_name(self) -> str:
        return "Adaptive Kelly"

class AdvancedPositionSizingManager:
    """Comprehensive position sizing management system"""
    
    def __init__(self, parameters: Optional[PositionSizingParameters] = None, 
                 logger: Optional[logging.Logger] = None):
        self.parameters = parameters or PositionSizingParameters()
        self.logger = logger or self._setup_logger()
        
        # Initialize strategies
        self.strategies = {
            PositionSizingMethod.FIXED_FRACTIONAL: FixedFractionalSizing(),
            PositionSizingMethod.KELLY_CRITERION: KellyCriterionSizing(),
            PositionSizingMethod.OPTIMAL_F: OptimalFSizing(),
            PositionSizingMethod.VOLATILITY_ADJUSTED: VolatilityAdjustedSizing(),
            PositionSizingMethod.RISK_PARITY: RiskParitySizing(),
            PositionSizingMethod.CONFIDENCE_WEIGHTED: ConfidenceWeightedSizing(),
            PositionSizingMethod.SHARPE_OPTIMIZED: SharpeOptimizedSizing(),
            PositionSizingMethod.VAR_BASED: VaRBasedSizing(),
            PositionSizingMethod.MONTE_CARLO: MonteCarloSizing(),
            PositionSizingMethod.ADAPTIVE_KELLY: AdaptiveKellySizing()
        }
        
        # Portfolio tracking
        self.current_positions = {}
        self.portfolio_value = 100000  # Default portfolio value
        self.position_history = []
        self.performance_metrics = {}
        
        self.logger.info("🎯 Advanced Position Sizing Manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for position sizing"""
        logger = logging.getLogger('PositionSizing')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def calculate_position_size(self, signal: TradingSignal, method: PositionSizingMethod,
                              portfolio_value: Optional[float] = None) -> PositionSizingResult:
        """Calculate position size using specified method"""
        
        portfolio_val = portfolio_value or self.portfolio_value
        
        # Get strategy
        strategy = self.strategies.get(method)
        if not strategy:
            raise ValueError(f"Unknown position sizing method: {method}")
        
        # Calculate base position size
        base_size = strategy.calculate_position_size(
            signal, portfolio_val, self.current_positions, self.parameters
        )
        
        # Apply portfolio-level constraints
        adjusted_size = self._apply_portfolio_constraints(signal, base_size, portfolio_val)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(signal, adjusted_size, portfolio_val)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(signal, method, base_size, adjusted_size, risk_metrics)
        
        result = PositionSizingResult(
            symbol=signal.symbol,
            method=method,
            recommended_size=adjusted_size,
            max_size=self.parameters.max_position_size,
            confidence=signal.confidence,
            expected_return=signal.expected_return,
            risk_metrics=risk_metrics,
            reasoning=reasoning
        )
        
        self.logger.info(f"📊 {signal.symbol} position sizing: {method.value} = {adjusted_size:.2%}")
        
        return result
    
    def _apply_portfolio_constraints(self, signal: TradingSignal, base_size: float, 
                                   portfolio_value: float) -> float:
        """Apply portfolio-level constraints to position size"""
        
        # Check total exposure
        current_exposure = sum(pos.get('size', 0) for pos in self.current_positions.values())
        available_exposure = self.parameters.max_total_exposure - current_exposure
        
        # Limit by available exposure
        max_allowed = min(base_size, available_exposure)
        
        # Check correlation constraints
        if signal.symbol in self.current_positions:
            # Existing position - allow adjustments
            adjusted_size = max_allowed
        else:
            # New position - check correlation limits
            adjusted_size = self._check_correlation_constraints(signal, max_allowed)
        
        # Apply absolute bounds
        adjusted_size = max(self.parameters.min_position_size, 
                          min(adjusted_size, self.parameters.max_position_size))
        
        return adjusted_size
    
    def _check_correlation_constraints(self, signal: TradingSignal, proposed_size: float) -> float:
        """Check correlation constraints for new positions"""
        
        # Simplified correlation check (in practice, would use actual correlation data)
        # For now, limit positions in same sector/category
        
        similar_positions = 0
        for symbol, position in self.current_positions.items():
            # Simple heuristic: symbols starting with same letter are "similar"
            if symbol[0] == signal.symbol[0]:
                similar_positions += 1
        
        # Reduce size if too many similar positions
        if similar_positions >= 3:
            correlation_factor = 0.5
        elif similar_positions >= 2:
            correlation_factor = 0.7
        else:
            correlation_factor = 1.0
        
        return proposed_size * correlation_factor
    
    def _calculate_risk_metrics(self, signal: TradingSignal, position_size: float, 
                              portfolio_value: float) -> Dict[str, float]:
        """Calculate risk metrics for the position"""
        
        position_value = portfolio_value * position_size
        
        # Value at Risk (95% confidence)
        if signal.expected_volatility > 0:
            daily_var = position_value * signal.expected_volatility * 1.645  # 95% VaR
        else:
            daily_var = position_value * 0.02  # Default 2% VaR
        
        # Maximum loss (worst case)
        max_loss = position_value * signal.avg_loss if signal.avg_loss > 0 else position_value * 0.1
        
        # Expected profit/loss
        expected_pnl = position_value * signal.expected_return
        
        # Risk-reward ratio
        risk_reward = abs(signal.avg_win / signal.avg_loss) if signal.avg_loss > 0 else 2.0
        
        # Portfolio impact
        portfolio_impact = position_size
        
        return {
            'position_value': position_value,
            'daily_var': daily_var,
            'max_loss': max_loss,
            'expected_pnl': expected_pnl,
            'risk_reward_ratio': risk_reward,
            'portfolio_impact': portfolio_impact,
            'volatility': signal.expected_volatility
        }
    
    def _generate_reasoning(self, signal: TradingSignal, method: PositionSizingMethod,
                          base_size: float, final_size: float, risk_metrics: Dict) -> List[str]:
        """Generate human-readable reasoning for position size"""
        
        reasoning = []
        
        # Method explanation
        strategy_name = self.strategies[method].get_strategy_name()
        reasoning.append(f"Using {strategy_name} method")
        
        # Base calculation
        reasoning.append(f"Base size calculated: {base_size:.2%}")
        
        # Confidence impact
        reasoning.append(f"Confidence level: {signal.confidence:.1f}%")
        
        # Risk level impact
        reasoning.append(f"Risk level: {signal.risk_level.value[0]}")
        
        # Market regime impact
        reasoning.append(f"Market regime: {signal.market_regime.value}")
        
        # Adjustments
        if abs(final_size - base_size) > 0.001:
            adjustment = (final_size - base_size) / base_size * 100
            reasoning.append(f"Portfolio constraints adjustment: {adjustment:+.1f}%")
        
        # Risk metrics
        reasoning.append(f"Expected return: {signal.expected_return:+.2%}")
        reasoning.append(f"Risk-reward ratio: {risk_metrics['risk_reward_ratio']:.2f}")
        reasoning.append(f"Portfolio impact: {risk_metrics['portfolio_impact']:.2%}")
        
        return reasoning
    
    def get_ensemble_recommendation(self, signal: TradingSignal, 
                                  methods: Optional[List[PositionSizingMethod]] = None,
                                  weights: Optional[Dict[PositionSizingMethod, float]] = None) -> PositionSizingResult:
        """Get ensemble recommendation from multiple methods"""
        
        if methods is None:
            methods = [
                PositionSizingMethod.KELLY_CRITERION,
                PositionSizingMethod.VOLATILITY_ADJUSTED,
                PositionSizingMethod.CONFIDENCE_WEIGHTED,
                PositionSizingMethod.RISK_PARITY
            ]
        
        if weights is None:
            # Equal weights
            weights = {method: 1.0 / len(methods) for method in methods}
        
        # Calculate individual recommendations
        individual_results = {}
        for method in methods:
            try:
                result = self.calculate_position_size(signal, method)
                individual_results[method] = result
            except Exception as e:
                self.logger.warning(f"Error calculating {method.value}: {e}")
                continue
        
        if not individual_results:
            # Fallback to fixed fractional
            return self.calculate_position_size(signal, PositionSizingMethod.FIXED_FRACTIONAL)
        
        # Calculate weighted average
        weighted_size = 0.0
        total_weight = 0.0
        
        for method, result in individual_results.items():
            weight = weights.get(method, 0.0)
            weighted_size += result.recommended_size * weight
            total_weight += weight
        
        if total_weight > 0:
            ensemble_size = weighted_size / total_weight
        else:
            ensemble_size = np.mean([r.recommended_size for r in individual_results.values()])
        
        # Apply final constraints
        ensemble_size = max(self.parameters.min_position_size,
                          min(ensemble_size, self.parameters.max_position_size))
        
        # Calculate ensemble risk metrics
        risk_metrics = self._calculate_risk_metrics(signal, ensemble_size, self.portfolio_value)
        
        # Generate ensemble reasoning
        reasoning = ["Ensemble recommendation from multiple methods:"]
        for method, result in individual_results.items():
            weight = weights.get(method, 0.0)
            reasoning.append(f"  {method.value}: {result.recommended_size:.2%} (weight: {weight:.2f})")
        reasoning.append(f"Weighted average: {ensemble_size:.2%}")
        
        return PositionSizingResult(
            symbol=signal.symbol,
            method=PositionSizingMethod.CONFIDENCE_WEIGHTED,  # Placeholder
            recommended_size=ensemble_size,
            max_size=self.parameters.max_position_size,
            confidence=signal.confidence,
            expected_return=signal.expected_return,
            risk_metrics=risk_metrics,
            reasoning=reasoning
        )
    
    def update_portfolio(self, positions: Dict[str, Dict], portfolio_value: float):
        """Update current portfolio state"""
        self.current_positions = positions
        self.portfolio_value = portfolio_value
        
        # Update adaptive strategies with new data
        if PositionSizingMethod.ADAPTIVE_KELLY in self.strategies:
            adaptive_kelly = self.strategies[PositionSizingMethod.ADAPTIVE_KELLY]
            # In practice, would update with actual trade results
    
    def get_position_sizing_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive position sizing dashboard"""
        
        current_exposure = sum(pos.get('size', 0) for pos in self.current_positions.values())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio': {
                'total_value': self.portfolio_value,
                'current_exposure': f"{current_exposure:.2%}",
                'available_exposure': f"{self.parameters.max_total_exposure - current_exposure:.2%}",
                'num_positions': len(self.current_positions)
            },
            'parameters': {
                'max_position_size': f"{self.parameters.max_position_size:.2%}",
                'max_total_exposure': f"{self.parameters.max_total_exposure:.2%}",
                'min_position_size': f"{self.parameters.min_position_size:.2%}",
                'kelly_safety_factor': f"{self.parameters.kelly_safety_factor:.2f}",
                'confidence_threshold': f"{self.parameters.confidence_threshold:.2%}"
            },
            'available_methods': [method.value for method in PositionSizingMethod],
            'current_positions': {
                symbol: {
                    'size': f"{pos.get('size', 0):.2%}",
                    'value': f"${pos.get('value', 0):,.2f}"
                }
                for symbol, pos in self.current_positions.items()
            }
        }

# Convenience functions for easy integration
def calculate_kelly_position_size(win_rate: float, avg_win: float, avg_loss: float,
                                confidence: float = 1.0, safety_factor: float = 0.25) -> float:
    """Quick Kelly Criterion calculation"""
    if avg_loss == 0 or win_rate == 0:
        return 0.01
    
    b = abs(avg_win / avg_loss)
    p = win_rate
    q = 1 - p
    
    kelly_fraction = (b * p - q) / b
    safe_kelly = kelly_fraction * safety_factor * confidence
    
    return max(0.01, min(safe_kelly, 0.20))

def calculate_volatility_adjusted_size(base_size: float, target_volatility: float,
                                     actual_volatility: float) -> float:
    """Quick volatility-adjusted position size"""
    if actual_volatility <= 0:
        return base_size
    
    adjustment = target_volatility / actual_volatility
    adjustment = max(0.2, min(adjustment, 2.0))
    
    return base_size * adjustment

def create_trading_signal(symbol: str, confidence: float, expected_return: float,
                        win_rate: float = 0.6, avg_win: float = 0.05, avg_loss: float = 0.03) -> TradingSignal:
    """Create a trading signal for position sizing"""
    
    # Determine action based on expected return
    if expected_return > 0.02:
        action = "BUY"
    elif expected_return < -0.02:
        action = "SELL"
    else:
        action = "HOLD"
    
    # Estimate volatility from win/loss data
    volatility = max(abs(avg_win), abs(avg_loss)) * 1.5
    
    # Determine risk level based on volatility
    if volatility < 0.02:
        risk_level = RiskLevel.LOW
    elif volatility < 0.05:
        risk_level = RiskLevel.MODERATE
    else:
        risk_level = RiskLevel.HIGH
    
    # Simple market regime detection (placeholder)
    if abs(expected_return) > 0.05:
        regime = MarketRegime.HIGH_VOLATILITY
    elif expected_return > 0.02:
        regime = MarketRegime.BULL
    elif expected_return < -0.02:
        regime = MarketRegime.BEAR
    else:
        regime = MarketRegime.SIDEWAYS
    
    return TradingSignal(
        symbol=symbol,
        action=action,
        confidence=confidence,
        expected_return=expected_return,
        expected_volatility=volatility,
        win_probability=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        holding_period=5,  # Default 5 days
        market_regime=regime,
        risk_level=risk_level
    )

if __name__ == "__main__":
    # Example usage and testing
    print("🎯 Advanced Position Sizing Manager - Testing")
    
    # Create manager
    manager = AdvancedPositionSizingManager()
    
    # Create test signal
    signal = create_trading_signal(
        symbol='BTC/USDT',
        confidence=75.0,
        expected_return=0.08,
        win_rate=0.65,
        avg_win=0.12,
        avg_loss=0.05
    )
    
    print(f"\n📊 Testing Position Sizing Methods for {signal.symbol}")
    print(f"   Confidence: {signal.confidence}%")
    print(f"   Expected Return: {signal.expected_return:+.2%}")
    print(f"   Win Rate: {signal.win_probability:.1%}")
    print(f"   Risk Level: {signal.risk_level.value[0]}")
    
    # Test all methods
    methods_to_test = [
        PositionSizingMethod.FIXED_FRACTIONAL,
        PositionSizingMethod.KELLY_CRITERION,
        PositionSizingMethod.VOLATILITY_ADJUSTED,
        PositionSizingMethod.RISK_PARITY,
        PositionSizingMethod.CONFIDENCE_WEIGHTED,
        PositionSizingMethod.SHARPE_OPTIMIZED,
        PositionSizingMethod.VAR_BASED
    ]
    
    results = {}
    
    print(f"\n🔍 Individual Method Results:")
    for method in methods_to_test:
        try:
            result = manager.calculate_position_size(signal, method)
            results[method] = result
            print(f"   {method.value:20}: {result.recommended_size:6.2%} "
                  f"(Risk-Reward: {result.risk_metrics['risk_reward_ratio']:.2f})")
        except Exception as e:
            print(f"   {method.value:20}: ERROR - {e}")
    
    # Test ensemble method
    print(f"\n🎯 Ensemble Recommendation:")
    ensemble_result = manager.get_ensemble_recommendation(signal)
    print(f"   Ensemble Size: {ensemble_result.recommended_size:.2%}")
    print(f"   Expected P&L: ${ensemble_result.risk_metrics['expected_pnl']:,.2f}")
    print(f"   Max Loss: ${ensemble_result.risk_metrics['max_loss']:,.2f}")
    print(f"   Daily VaR: ${ensemble_result.risk_metrics['daily_var']:,.2f}")
    
    # Show reasoning
    print(f"\n💡 Reasoning:")
    for reason in ensemble_result.reasoning[:5]:  # Show first 5 reasons
        print(f"   • {reason}")
    
    # Dashboard
    print(f"\n📊 Position Sizing Dashboard:")
    dashboard = manager.get_position_sizing_dashboard()
    
    print(f"   Portfolio Value: ${dashboard['portfolio']['total_value']:,.2f}")
    print(f"   Current Exposure: {dashboard['portfolio']['current_exposure']}")
    print(f"   Available Exposure: {dashboard['portfolio']['available_exposure']}")
    print(f"   Max Position Size: {dashboard['parameters']['max_position_size']}")
    print(f"   Kelly Safety Factor: {dashboard['parameters']['kelly_safety_factor']}")
    
    # Test quick functions
    print(f"\n⚡ Quick Function Tests:")
    kelly_size = calculate_kelly_position_size(0.65, 0.12, 0.05, 0.75)
    print(f"   Quick Kelly Size: {kelly_size:.2%}")
    
    vol_adjusted = calculate_volatility_adjusted_size(0.10, 0.02, 0.08)
    print(f"   Volatility Adjusted: {vol_adjusted:.2%}")
    
    print(f"\n✅ Advanced Position Sizing System Ready!")
    print(f"   Available Methods: {len(methods_to_test)}")
    print(f"   Ensemble Capability: ✅")
    print(f"   Risk Management: ✅")
    print(f"   Portfolio Constraints: ✅")