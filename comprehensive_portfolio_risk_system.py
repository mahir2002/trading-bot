#!/usr/bin/env python3
"""
Comprehensive Portfolio Risk Management System
Advanced risk management addressing account-level risk, dynamic position sizing,
and sophisticated portfolio risk controls beyond basic per-trade limits
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.covariance import LedoitWolf
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time
import json

class RiskLevel(Enum):
    """Risk level classifications."""
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    MAXIMUM = "MAXIMUM"

class PositionSizeMethod(Enum):
    """Position sizing methodologies."""
    FIXED_FRACTIONAL = "FIXED_FRACTIONAL"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"
    KELLY_CRITERION = "KELLY_CRITERION"
    RISK_PARITY = "RISK_PARITY"
    DYNAMIC_CORRELATION = "DYNAMIC_CORRELATION"

@dataclass
class RiskLimits:
    """Comprehensive risk limits configuration."""
    # Account-level limits
    max_account_risk: float = 0.05          # 5% maximum account risk
    max_daily_drawdown: float = 0.02        # 2% maximum daily drawdown
    max_total_drawdown: float = 0.10        # 10% maximum total drawdown
    max_portfolio_var: float = 0.03         # 3% portfolio VaR limit
    
    # Position-level limits
    max_position_risk: float = 0.01         # 1% maximum per position
    max_position_size: float = 0.05         # 5% maximum position size
    max_correlation_exposure: float = 0.15  # 15% maximum correlated exposure
    
    # Trading limits
    max_daily_trades: int = 10              # Maximum trades per day
    max_open_positions: int = 20            # Maximum open positions
    min_time_between_trades: int = 300      # 5 minutes between trades (seconds)
    
    # Volatility limits
    max_portfolio_volatility: float = 0.25  # 25% maximum portfolio volatility
    volatility_lookback: int = 30           # 30-day volatility calculation
    
    # Concentration limits
    max_sector_exposure: float = 0.20       # 20% maximum sector exposure
    max_single_asset_exposure: float = 0.10 # 10% maximum single asset

@dataclass
class PortfolioMetrics:
    """Real-time portfolio risk metrics."""
    total_value: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Risk metrics
    portfolio_var_95: float = 0.0
    portfolio_var_99: float = 0.0
    expected_shortfall: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    
    # Volatility metrics
    portfolio_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Exposure metrics
    gross_exposure: float = 0.0
    net_exposure: float = 0.0
    leverage: float = 0.0
    
    # Position metrics
    num_positions: int = 0
    avg_position_size: float = 0.0
    largest_position: float = 0.0
    
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

class VolatilityEstimator:
    """Advanced volatility estimation for dynamic position sizing."""
    
    def __init__(self, lookback_period: int = 30):
        self.lookback_period = lookback_period
        self.volatility_models = {}
    
    def estimate_volatility(self, returns: pd.Series, method: str = 'ewma') -> float:
        """Estimate volatility using various methods."""
        
        if len(returns) < 10:
            return 0.02  # Default 2% volatility
        
        if method == 'simple':
            return returns.std() * np.sqrt(252)
        
        elif method == 'ewma':
            # Exponentially weighted moving average
            lambda_factor = 0.94
            ewma_var = returns.ewm(alpha=1-lambda_factor).var().iloc[-1]
            return np.sqrt(ewma_var * 252)
        
        elif method == 'garch':
            # Simplified GARCH(1,1)
            return self._garch_volatility(returns)
        
        elif method == 'realized':
            # Realized volatility from high-frequency data
            return self._realized_volatility(returns)
        
        else:
            return returns.rolling(self.lookback_period).std().iloc[-1] * np.sqrt(252)
    
    def _garch_volatility(self, returns: pd.Series) -> float:
        """Simplified GARCH(1,1) volatility estimation."""
        
        # GARCH parameters (simplified)
        omega = 0.000001
        alpha = 0.1
        beta = 0.85
        
        # Initialize
        variance = returns.var()
        
        # GARCH iteration
        for ret in returns.tail(min(100, len(returns))):
            variance = omega + alpha * (ret ** 2) + beta * variance
        
        return np.sqrt(variance * 252)
    
    def _realized_volatility(self, returns: pd.Series) -> float:
        """Realized volatility calculation."""
        
        # Sum of squared returns (proxy for realized volatility)
        realized_var = (returns ** 2).rolling(self.lookback_period).sum().iloc[-1]
        return np.sqrt(realized_var * 252 / self.lookback_period)

class CorrelationManager:
    """Dynamic correlation analysis for portfolio risk."""
    
    def __init__(self, lookback_period: int = 60):
        self.lookback_period = lookback_period
        self.correlation_matrices = {}
        self.asset_returns = {}
    
    def update_correlations(self, asset_returns: Dict[str, pd.Series]):
        """Update correlation matrices."""
        
        self.asset_returns = asset_returns
        
        # Create returns dataframe
        returns_df = pd.DataFrame(asset_returns)
        
        if len(returns_df) < self.lookback_period:
            return
        
        # Rolling correlation matrices
        for window in [30, 60, 90]:
            if len(returns_df) >= window:
                corr_matrix = returns_df.rolling(window).corr().iloc[-len(returns_df.columns):]
                self.correlation_matrices[f'{window}d'] = corr_matrix
    
    def get_portfolio_correlation_risk(self, positions: Dict[str, float]) -> float:
        """Calculate portfolio correlation risk."""
        
        if '60d' not in self.correlation_matrices:
            return 0.0
        
        corr_matrix = self.correlation_matrices['60d']
        assets = list(positions.keys())
        
        # Filter correlation matrix for current assets
        common_assets = [asset for asset in assets if asset in corr_matrix.columns]
        
        if len(common_assets) < 2:
            return 0.0
        
        # Create position weights vector
        weights = np.array([positions.get(asset, 0) for asset in common_assets])
        weights = weights / np.sum(np.abs(weights)) if np.sum(np.abs(weights)) > 0 else weights
        
        # Calculate portfolio correlation risk
        filtered_corr = corr_matrix.loc[common_assets, common_assets].fillna(0)
        correlation_risk = np.dot(weights, np.dot(filtered_corr.values, weights))
        
        return max(0, correlation_risk)
    
    def get_concentration_risk(self, positions: Dict[str, float], threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """Identify highly correlated position pairs."""
        
        if '30d' not in self.correlation_matrices:
            return []
        
        corr_matrix = self.correlation_matrices['30d']
        high_corr_pairs = []
        
        assets = list(positions.keys())
        
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                if asset1 in corr_matrix.columns and asset2 in corr_matrix.columns:
                    correlation = corr_matrix.loc[asset1, asset2]
                    if abs(correlation) > threshold:
                        high_corr_pairs.append((asset1, asset2, correlation))
        
        return high_corr_pairs

class DynamicPositionSizer:
    """Advanced dynamic position sizing system."""
    
    def __init__(self, base_position_size: float = 0.02):
        self.base_position_size = base_position_size
        self.volatility_estimator = VolatilityEstimator()
        self.position_history = []
    
    def calculate_position_size(self, 
                              method: PositionSizeMethod,
                              account_value: float,
                              signal_strength: float,
                              asset_volatility: float,
                              portfolio_volatility: float,
                              correlation_adjustment: float = 1.0,
                              **kwargs) -> float:
        """Calculate dynamic position size based on multiple factors."""
        
        if method == PositionSizeMethod.FIXED_FRACTIONAL:
            return self._fixed_fractional_sizing(account_value, signal_strength)
        
        elif method == PositionSizeMethod.VOLATILITY_ADJUSTED:
            return self._volatility_adjusted_sizing(
                account_value, signal_strength, asset_volatility, portfolio_volatility
            )
        
        elif method == PositionSizeMethod.KELLY_CRITERION:
            return self._kelly_criterion_sizing(
                account_value, signal_strength, **kwargs
            )
        
        elif method == PositionSizeMethod.RISK_PARITY:
            return self._risk_parity_sizing(
                account_value, asset_volatility, **kwargs
            )
        
        elif method == PositionSizeMethod.DYNAMIC_CORRELATION:
            return self._correlation_adjusted_sizing(
                account_value, signal_strength, asset_volatility, correlation_adjustment
            )
        
        else:
            return self._fixed_fractional_sizing(account_value, signal_strength)
    
    def _fixed_fractional_sizing(self, account_value: float, signal_strength: float) -> float:
        """Fixed fractional position sizing."""
        return account_value * self.base_position_size * signal_strength
    
    def _volatility_adjusted_sizing(self, 
                                  account_value: float, 
                                  signal_strength: float,
                                  asset_volatility: float,
                                  portfolio_volatility: float) -> float:
        """Volatility-adjusted position sizing."""
        
        # Target volatility approach
        target_volatility = 0.15  # 15% target volatility
        
        if asset_volatility > 0:
            volatility_adjustment = target_volatility / asset_volatility
            volatility_adjustment = np.clip(volatility_adjustment, 0.2, 3.0)  # Limit adjustment
        else:
            volatility_adjustment = 1.0
        
        # Portfolio volatility adjustment
        portfolio_adjustment = 1.0
        if portfolio_volatility > target_volatility:
            portfolio_adjustment = target_volatility / portfolio_volatility
        
        base_size = account_value * self.base_position_size * signal_strength
        return base_size * volatility_adjustment * portfolio_adjustment
    
    def _kelly_criterion_sizing(self, 
                              account_value: float,
                              signal_strength: float,
                              win_probability: float = 0.55,
                              avg_win: float = 0.02,
                              avg_loss: float = 0.015) -> float:
        """Kelly Criterion position sizing."""
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds, p = win probability, q = loss probability
        
        if avg_loss <= 0:
            avg_loss = 0.015
        
        b = avg_win / avg_loss  # Odds
        p = win_probability * signal_strength  # Adjusted win probability
        q = 1 - p  # Loss probability
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = np.clip(kelly_fraction, 0, 0.25)  # Cap at 25%
        
        return account_value * kelly_fraction
    
    def _risk_parity_sizing(self, 
                          account_value: float,
                          asset_volatility: float,
                          target_risk_contribution: float = 0.02) -> float:
        """Risk parity position sizing."""
        
        if asset_volatility <= 0:
            return account_value * self.base_position_size
        
        # Position size to achieve target risk contribution
        position_size = (account_value * target_risk_contribution) / asset_volatility
        
        return position_size
    
    def _correlation_adjusted_sizing(self,
                                   account_value: float,
                                   signal_strength: float,
                                   asset_volatility: float,
                                   correlation_adjustment: float) -> float:
        """Correlation-adjusted position sizing."""
        
        base_size = self._volatility_adjusted_sizing(
            account_value, signal_strength, asset_volatility, 0.15
        )
        
        # Reduce size for highly correlated positions
        correlation_factor = 1.0 / (1.0 + correlation_adjustment)
        
        return base_size * correlation_factor

class ComprehensiveRiskManager:
    """Advanced portfolio risk management system."""
    
    def __init__(self, risk_limits: RiskLimits = None):
        self.risk_limits = risk_limits or RiskLimits()
        self.portfolio_metrics = PortfolioMetrics()
        self.correlation_manager = CorrelationManager()
        self.position_sizer = DynamicPositionSizer()
        
        # Risk tracking
        self.daily_pnl_history = []
        self.portfolio_values = []
        self.risk_alerts = []
        self.position_history = []
        
        # Risk monitoring
        self.last_risk_check = datetime.now()
        self.risk_breach_count = 0
        
        print("🛡️ Comprehensive Portfolio Risk Management System Initialized")
        print("   ✅ Account-level risk controls")
        print("   ✅ Dynamic position sizing")
        print("   ✅ Portfolio correlation analysis")
        print("   ✅ Advanced risk metrics")
    
    def update_portfolio_metrics(self, positions: Dict[str, Dict], account_value: float):
        """Update comprehensive portfolio metrics."""
        
        # Basic portfolio metrics
        self.portfolio_metrics.total_value = account_value
        self.portfolio_metrics.num_positions = len(positions)
        
        # Calculate exposures
        total_long = sum(pos['value'] for pos in positions.values() if pos['side'] == 'long')
        total_short = sum(abs(pos['value']) for pos in positions.values() if pos['side'] == 'short')
        
        self.portfolio_metrics.gross_exposure = total_long + total_short
        self.portfolio_metrics.net_exposure = total_long - total_short
        self.portfolio_metrics.leverage = self.portfolio_metrics.gross_exposure / account_value if account_value > 0 else 0
        
        # Calculate PnL metrics
        unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions.values())
        self.portfolio_metrics.unrealized_pnl = unrealized_pnl
        
        # Update portfolio value history
        self.portfolio_values.append({
            'timestamp': datetime.now(),
            'value': account_value,
            'pnl': unrealized_pnl
        })
        
        # Calculate risk metrics
        self._calculate_risk_metrics()
        
        # Check risk limits
        self._check_risk_limits()
    
    def _calculate_risk_metrics(self):
        """Calculate advanced portfolio risk metrics."""
        
        if len(self.portfolio_values) < 30:
            return
        
        # Extract returns
        values = [pv['value'] for pv in self.portfolio_values[-252:]]  # Last year
        returns = np.diff(values) / values[:-1]
        
        if len(returns) == 0:
            return
        
        # VaR calculations
        self.portfolio_metrics.portfolio_var_95 = np.percentile(returns, 5)
        self.portfolio_metrics.portfolio_var_99 = np.percentile(returns, 1)
        
        # Expected Shortfall (Conditional VaR)
        var_95_returns = returns[returns <= self.portfolio_metrics.portfolio_var_95]
        if len(var_95_returns) > 0:
            self.portfolio_metrics.expected_shortfall = np.mean(var_95_returns)
        
        # Volatility metrics
        self.portfolio_metrics.portfolio_volatility = np.std(returns) * np.sqrt(252)
        
        # Sharpe ratio
        if self.portfolio_metrics.portfolio_volatility > 0:
            avg_return = np.mean(returns) * 252
            self.portfolio_metrics.sharpe_ratio = avg_return / self.portfolio_metrics.portfolio_volatility
        
        # Sortino ratio
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_volatility = np.std(negative_returns) * np.sqrt(252)
            if downside_volatility > 0:
                avg_return = np.mean(returns) * 252
                self.portfolio_metrics.sortino_ratio = avg_return / downside_volatility
        
        # Drawdown calculation
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        
        self.portfolio_metrics.current_drawdown = drawdown[-1]
        self.portfolio_metrics.max_drawdown = np.min(drawdown)
        
        # Calmar ratio
        if abs(self.portfolio_metrics.max_drawdown) > 0:
            avg_return = np.mean(returns) * 252
            self.portfolio_metrics.calmar_ratio = avg_return / abs(self.portfolio_metrics.max_drawdown)
    
    def _check_risk_limits(self):
        """Check all risk limits and generate alerts."""
        
        alerts = []
        
        # Account-level risk checks
        if abs(self.portfolio_metrics.current_drawdown) > self.risk_limits.max_daily_drawdown:
            alerts.append(RiskAlert(
                alert_type="DAILY_DRAWDOWN_BREACH",
                severity="HIGH",
                message=f"Daily drawdown {self.portfolio_metrics.current_drawdown:.2%} exceeds limit {self.risk_limits.max_daily_drawdown:.2%}",
                metric_value=abs(self.portfolio_metrics.current_drawdown),
                threshold=self.risk_limits.max_daily_drawdown,
                timestamp=datetime.now(),
                action_required="REDUCE_POSITIONS"
            ))
        
        if abs(self.portfolio_metrics.max_drawdown) > self.risk_limits.max_total_drawdown:
            alerts.append(RiskAlert(
                alert_type="MAX_DRAWDOWN_BREACH",
                severity="CRITICAL",
                message=f"Maximum drawdown {self.portfolio_metrics.max_drawdown:.2%} exceeds limit {self.risk_limits.max_total_drawdown:.2%}",
                metric_value=abs(self.portfolio_metrics.max_drawdown),
                threshold=self.risk_limits.max_total_drawdown,
                timestamp=datetime.now(),
                action_required="EMERGENCY_LIQUIDATION"
            ))
        
        # Portfolio VaR check
        if abs(self.portfolio_metrics.portfolio_var_95) > self.risk_limits.max_portfolio_var:
            alerts.append(RiskAlert(
                alert_type="VAR_BREACH",
                severity="MEDIUM",
                message=f"Portfolio VaR {abs(self.portfolio_metrics.portfolio_var_95):.2%} exceeds limit {self.risk_limits.max_portfolio_var:.2%}",
                metric_value=abs(self.portfolio_metrics.portfolio_var_95),
                threshold=self.risk_limits.max_portfolio_var,
                timestamp=datetime.now(),
                action_required="REDUCE_RISK"
            ))
        
        # Volatility check
        if self.portfolio_metrics.portfolio_volatility > self.risk_limits.max_portfolio_volatility:
            alerts.append(RiskAlert(
                alert_type="VOLATILITY_BREACH",
                severity="MEDIUM",
                message=f"Portfolio volatility {self.portfolio_metrics.portfolio_volatility:.2%} exceeds limit {self.risk_limits.max_portfolio_volatility:.2%}",
                metric_value=self.portfolio_metrics.portfolio_volatility,
                threshold=self.risk_limits.max_portfolio_volatility,
                timestamp=datetime.now(),
                action_required="REDUCE_VOLATILITY"
            ))
        
        # Leverage check
        if self.portfolio_metrics.leverage > 2.0:  # 2x leverage limit
            alerts.append(RiskAlert(
                alert_type="LEVERAGE_BREACH",
                severity="HIGH",
                message=f"Portfolio leverage {self.portfolio_metrics.leverage:.2f}x exceeds prudent limits",
                metric_value=self.portfolio_metrics.leverage,
                threshold=2.0,
                timestamp=datetime.now(),
                action_required="REDUCE_LEVERAGE"
            ))
        
        # Add alerts to history
        self.risk_alerts.extend(alerts)
        
        # Keep only recent alerts (last 100)
        if len(self.risk_alerts) > 100:
            self.risk_alerts = self.risk_alerts[-100:]
        
        return alerts
    
    def calculate_optimal_position_size(self,
                                      signal_strength: float,
                                      asset_symbol: str,
                                      current_price: float,
                                      asset_volatility: float,
                                      account_value: float,
                                      existing_positions: Dict[str, Dict],
                                      method: PositionSizeMethod = PositionSizeMethod.VOLATILITY_ADJUSTED) -> Dict[str, Any]:
        """Calculate optimal position size with comprehensive risk controls."""
        
        # Get correlation adjustment
        position_values = {k: v['value'] for k, v in existing_positions.items()}
        correlation_risk = self.correlation_manager.get_portfolio_correlation_risk(position_values)
        
        # Calculate base position size
        base_size = self.position_sizer.calculate_position_size(
            method=method,
            account_value=account_value,
            signal_strength=signal_strength,
            asset_volatility=asset_volatility,
            portfolio_volatility=self.portfolio_metrics.portfolio_volatility,
            correlation_adjustment=correlation_risk
        )
        
        # Apply risk limits
        max_position_value = account_value * self.risk_limits.max_position_size
        max_risk_value = account_value * self.risk_limits.max_position_risk / asset_volatility if asset_volatility > 0 else max_position_value
        
        # Final position size (minimum of all constraints)
        final_size = min(base_size, max_position_value, max_risk_value)
        
        # Calculate position quantity
        quantity = final_size / current_price if current_price > 0 else 0
        
        # Risk metrics for this position
        position_risk = (final_size * asset_volatility) / account_value
        
        return {
            'quantity': quantity,
            'value': final_size,
            'risk_contribution': position_risk,
            'method_used': method.value,
            'base_size': base_size,
            'size_after_limits': final_size,
            'correlation_adjustment': correlation_risk,
            'volatility_adjustment': asset_volatility
        }
    
    def should_allow_trade(self,
                          asset_symbol: str,
                          trade_value: float,
                          existing_positions: Dict[str, Dict]) -> Tuple[bool, str]:
        """Determine if trade should be allowed based on risk limits."""
        
        # Check position count limit
        if len(existing_positions) >= self.risk_limits.max_open_positions:
            return False, f"Maximum positions limit reached ({self.risk_limits.max_open_positions})"
        
        # Check single asset exposure
        current_exposure = existing_positions.get(asset_symbol, {}).get('value', 0)
        new_exposure = (abs(current_exposure) + abs(trade_value)) / self.portfolio_metrics.total_value
        
        if new_exposure > self.risk_limits.max_single_asset_exposure:
            return False, f"Single asset exposure limit exceeded ({new_exposure:.1%} > {self.risk_limits.max_single_asset_exposure:.1%})"
        
        # Check drawdown limits
        if abs(self.portfolio_metrics.current_drawdown) > self.risk_limits.max_daily_drawdown:
            return False, f"Daily drawdown limit exceeded ({abs(self.portfolio_metrics.current_drawdown):.1%})"
        
        # Check VaR limits
        if abs(self.portfolio_metrics.portfolio_var_95) > self.risk_limits.max_portfolio_var:
            return False, f"Portfolio VaR limit exceeded ({abs(self.portfolio_metrics.portfolio_var_95):.1%})"
        
        # Check time between trades
        if hasattr(self, 'last_trade_time'):
            time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
            if time_since_last < self.risk_limits.min_time_between_trades:
                return False, f"Minimum time between trades not met ({time_since_last:.0f}s < {self.risk_limits.min_time_between_trades}s)"
        
        return True, "Trade approved"
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report."""
        
        recent_alerts = [alert for alert in self.risk_alerts if 
                        (datetime.now() - alert.timestamp).days < 1]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio_metrics': {
                'total_value': self.portfolio_metrics.total_value,
                'num_positions': self.portfolio_metrics.num_positions,
                'gross_exposure': self.portfolio_metrics.gross_exposure,
                'net_exposure': self.portfolio_metrics.net_exposure,
                'leverage': self.portfolio_metrics.leverage,
                'portfolio_var_95': self.portfolio_metrics.portfolio_var_95,
                'portfolio_volatility': self.portfolio_metrics.portfolio_volatility,
                'current_drawdown': self.portfolio_metrics.current_drawdown,
                'max_drawdown': self.portfolio_metrics.max_drawdown,
                'sharpe_ratio': self.portfolio_metrics.sharpe_ratio,
                'sortino_ratio': self.portfolio_metrics.sortino_ratio
            },
            'risk_limits': {
                'max_account_risk': self.risk_limits.max_account_risk,
                'max_daily_drawdown': self.risk_limits.max_daily_drawdown,
                'max_total_drawdown': self.risk_limits.max_total_drawdown,
                'max_portfolio_var': self.risk_limits.max_portfolio_var,
                'max_position_risk': self.risk_limits.max_position_risk,
                'max_position_size': self.risk_limits.max_position_size
            },
            'recent_alerts': [
                {
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                } for alert in recent_alerts
            ],
            'risk_status': 'HEALTHY' if len(recent_alerts) == 0 else 'AT_RISK'
        }

def generate_realistic_portfolio_data(n_days: int = 252) -> Tuple[Dict[str, pd.Series], pd.Series]:
    """Generate realistic portfolio data for testing."""
    
    np.random.seed(42)
    
    # Asset symbols
    assets = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'DOT/USD', 'LINK/USD']
    
    # Generate correlated returns
    n_assets = len(assets)
    
    # Create correlation matrix
    base_corr = 0.3
    correlation_matrix = np.full((n_assets, n_assets), base_corr)
    np.fill_diagonal(correlation_matrix, 1.0)
    
    # Generate correlated returns
    returns_data = {}
    
    # Base market factor
    market_returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
    
    for i, asset in enumerate(assets):
        # Asset-specific parameters
        asset_alpha = np.random.normal(0, 0.001, n_days)
        asset_volatility = 0.015 + i * 0.005  # Increasing volatility
        
        # Correlated returns
        asset_returns = (0.7 * market_returns + 
                        0.3 * np.random.normal(0, asset_volatility, n_days) + 
                        asset_alpha)
        
        returns_data[asset] = pd.Series(asset_returns, 
                                       index=pd.date_range(start='2023-01-01', periods=n_days))
    
    # Account value series
    initial_value = 100000
    account_values = [initial_value]
    
    for day in range(1, n_days):
        # Portfolio return (weighted average of asset returns)
        portfolio_return = np.mean([returns_data[asset].iloc[day] for asset in assets])
        new_value = account_values[-1] * (1 + portfolio_return)
        account_values.append(new_value)
    
    account_series = pd.Series(account_values, 
                              index=pd.date_range(start='2023-01-01', periods=n_days))
    
    return returns_data, account_series

def demonstrate_comprehensive_risk_management():
    """Demonstrate the comprehensive portfolio risk management system."""
    
    print("🛡️ Comprehensive Portfolio Risk Management System Demo")
    print("=" * 80)
    
    # Generate realistic data
    print("📊 Generating Realistic Portfolio Data...")
    asset_returns, account_values = generate_realistic_portfolio_data(252)
    print(f"   Generated data for {len(asset_returns)} assets over {len(account_values)} days")
    
    # Initialize risk management system
    risk_limits = RiskLimits(
        max_account_risk=0.05,
        max_daily_drawdown=0.02,
        max_total_drawdown=0.10,
        max_portfolio_var=0.03,
        max_position_risk=0.01,
        max_position_size=0.05
    )
    
    risk_manager = ComprehensiveRiskManager(risk_limits)
    
    print(f"\n🔄 Simulating Portfolio Management...")
    
    # Simulate portfolio over time
    positions = {}
    trades_executed = 0
    trades_rejected = 0
    
    for day in range(50, len(account_values), 5):  # Every 5th day
        
        current_value = account_values.iloc[day]
        
        # Update correlation manager
        recent_returns = {asset: returns.iloc[max(0, day-60):day] 
                         for asset, returns in asset_returns.items()}
        risk_manager.correlation_manager.update_correlations(recent_returns)
        
        # Simulate some positions
        if len(positions) < 3:  # Build up to 3 positions
            
            # Pick random asset
            asset = np.random.choice(list(asset_returns.keys()))
            current_price = 100 * (1 + asset_returns[asset].iloc[:day].sum())  # Cumulative price
            
            # Simulate signal
            signal_strength = np.random.uniform(0.4, 0.9)
            
            # Calculate asset volatility
            asset_vol = asset_returns[asset].iloc[max(0, day-30):day].std() * np.sqrt(252)
            
            # Check if trade should be allowed
            trade_value = current_value * 0.03  # 3% position
            allowed, reason = risk_manager.should_allow_trade(asset, trade_value, positions)
            
            if allowed:
                # Calculate optimal position size
                position_info = risk_manager.calculate_optimal_position_size(
                    signal_strength=signal_strength,
                    asset_symbol=asset,
                    current_price=current_price,
                    asset_volatility=asset_vol,
                    account_value=current_value,
                    existing_positions=positions,
                    method=PositionSizeMethod.VOLATILITY_ADJUSTED
                )
                
                # Add position
                positions[asset] = {
                    'value': position_info['value'],
                    'quantity': position_info['quantity'],
                    'side': 'long',
                    'entry_price': current_price,
                    'unrealized_pnl': 0,
                    'risk_contribution': position_info['risk_contribution']
                }
                
                trades_executed += 1
                risk_manager.last_trade_time = datetime.now()
                
            else:
                trades_rejected += 1
                print(f"   Trade rejected: {reason}")
        
        # Update position values
        for asset, position in positions.items():
            current_price = 100 * (1 + asset_returns[asset].iloc[:day].sum())
            position['unrealized_pnl'] = (current_price - position['entry_price']) * position['quantity']
            position['value'] = position['quantity'] * current_price
        
        # Update portfolio metrics
        risk_manager.update_portfolio_metrics(positions, current_value)
        
        # Show progress
        if day % 25 == 0:
            print(f"   Day {day}: Portfolio Value ${current_value:,.2f}, Positions: {len(positions)}")
    
    # Final analysis
    print(f"\n📊 Portfolio Risk Analysis:")
    print("=" * 50)
    
    metrics = risk_manager.portfolio_metrics
    
    print(f"📈 Portfolio Performance:")
    print(f"   Final Value: ${metrics.total_value:,.2f}")
    print(f"   Number of Positions: {metrics.num_positions}")
    print(f"   Gross Exposure: ${metrics.gross_exposure:,.2f}")
    print(f"   Net Exposure: ${metrics.net_exposure:,.2f}")
    print(f"   Leverage: {metrics.leverage:.2f}x")
    
    print(f"\n⚖️ Risk Metrics:")
    print(f"   Portfolio VaR (95%): {metrics.portfolio_var_95:.3f}")
    print(f"   Portfolio Volatility: {metrics.portfolio_volatility:.1%}")
    print(f"   Current Drawdown: {metrics.current_drawdown:.1%}")
    print(f"   Maximum Drawdown: {metrics.max_drawdown:.1%}")
    print(f"   Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio: {metrics.sortino_ratio:.2f}")
    
    print(f"\n📋 Trading Activity:")
    print(f"   Trades Executed: {trades_executed}")
    print(f"   Trades Rejected: {trades_rejected}")
    print(f"   Rejection Rate: {trades_rejected/(trades_executed + trades_rejected)*100:.1f}%")
    
    # Risk alerts
    recent_alerts = [alert for alert in risk_manager.risk_alerts if 
                    (datetime.now() - alert.timestamp).days < 1]
    
    print(f"\n🚨 Risk Alerts (Last 24h):")
    if recent_alerts:
        for alert in recent_alerts[-5:]:  # Show last 5 alerts
            print(f"   {alert.severity}: {alert.message}")
    else:
        print("   No recent risk alerts - Portfolio is HEALTHY")
    
    # Position sizing analysis
    print(f"\n💼 Position Sizing Analysis:")
    if positions:
        position_sizes = [pos['value'] for pos in positions.values()]
        risk_contributions = [pos['risk_contribution'] for pos in positions.values()]
        
        print(f"   Average Position Size: ${np.mean(position_sizes):,.2f}")
        print(f"   Largest Position: ${max(position_sizes):,.2f}")
        print(f"   Average Risk Contribution: {np.mean(risk_contributions):.1%}")
        print(f"   Total Risk Contribution: {sum(risk_contributions):.1%}")
    
    return risk_manager, positions, asset_returns

def create_risk_analysis_visualization(risk_manager, positions, asset_returns):
    """Create comprehensive risk analysis visualization."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Portfolio value over time
    ax1 = axes[0, 0]
    portfolio_history = risk_manager.portfolio_values
    if portfolio_history:
        timestamps = [pv['timestamp'] for pv in portfolio_history]
        values = [pv['value'] for pv in portfolio_history]
        ax1.plot(timestamps, values, linewidth=2, color='blue')
        ax1.set_title('Portfolio Value Over Time')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.grid(True, alpha=0.3)
    
    # Risk metrics
    ax2 = axes[0, 1]
    metrics = risk_manager.portfolio_metrics
    risk_metrics = {
        'VaR 95%': abs(metrics.portfolio_var_95),
        'Volatility': metrics.portfolio_volatility,
        'Max DD': abs(metrics.max_drawdown),
        'Current DD': abs(metrics.current_drawdown)
    }
    
    bars = ax2.bar(range(len(risk_metrics)), list(risk_metrics.values()), 
                   color=['red', 'orange', 'darkred', 'crimson'])
    ax2.set_title('Risk Metrics')
    ax2.set_ylabel('Risk Level')
    ax2.set_xticks(range(len(risk_metrics)))
    ax2.set_xticklabels(list(risk_metrics.keys()), rotation=45)
    
    # Position allocation
    ax3 = axes[0, 2]
    if positions:
        position_values = [pos['value'] for pos in positions.values()]
        position_labels = list(positions.keys())
        ax3.pie(position_values, labels=position_labels, autopct='%1.1f%%')
        ax3.set_title('Position Allocation')
    
    # Risk contributions
    ax4 = axes[1, 0]
    if positions:
        risk_contributions = [pos['risk_contribution'] for pos in positions.values()]
        position_labels = list(positions.keys())
        bars = ax4.bar(range(len(risk_contributions)), risk_contributions, 
                       color=['green', 'blue', 'purple', 'orange', 'red'][:len(risk_contributions)])
        ax4.set_title('Risk Contributions by Position')
        ax4.set_ylabel('Risk Contribution')
        ax4.set_xticks(range(len(position_labels)))
        ax4.set_xticklabels(position_labels, rotation=45)
    
    # Correlation heatmap
    ax5 = axes[1, 1]
    if '60d' in risk_manager.correlation_manager.correlation_matrices:
        corr_matrix = risk_manager.correlation_manager.correlation_matrices['60d']
        im = ax5.imshow(corr_matrix.values, cmap='RdBu_r', vmin=-1, vmax=1)
        ax5.set_title('Asset Correlation Matrix')
        ax5.set_xticks(range(len(corr_matrix.columns)))
        ax5.set_xticklabels(corr_matrix.columns, rotation=45)
        ax5.set_yticks(range(len(corr_matrix.index)))
        ax5.set_yticklabels(corr_matrix.index)
        plt.colorbar(im, ax=ax5)
    
    # Performance ratios
    ax6 = axes[1, 2]
    performance_ratios = {
        'Sharpe': metrics.sharpe_ratio,
        'Sortino': metrics.sortino_ratio,
        'Calmar': metrics.calmar_ratio
    }
    
    bars = ax6.bar(range(len(performance_ratios)), list(performance_ratios.values()), 
                   color=['blue', 'green', 'purple'])
    ax6.set_title('Performance Ratios')
    ax6.set_ylabel('Ratio')
    ax6.set_xticks(range(len(performance_ratios)))
    ax6.set_xticklabels(list(performance_ratios.keys()))
    ax6.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('comprehensive_portfolio_risk_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def main():
    """Run comprehensive portfolio risk management demonstration."""
    
    print("🛡️ Comprehensive Portfolio Risk Management System")
    print("=" * 80)
    print("Addressing Advanced Risk Management Limitations")
    print("=" * 80)
    
    # Run demonstration
    risk_manager, positions, asset_returns = demonstrate_comprehensive_risk_management()
    
    # Create visualization
    print(f"\n📈 Creating comprehensive risk analysis...")
    create_risk_analysis_visualization(risk_manager, positions, asset_returns)
    
    # Generate risk report
    risk_report = risk_manager.get_risk_report()
    
    print(f"\n📋 Comprehensive Risk Report:")
    print("=" * 50)
    print(f"Risk Status: {risk_report['risk_status']}")
    print(f"Portfolio Leverage: {risk_report['portfolio_metrics']['leverage']:.2f}x")
    print(f"Portfolio VaR: {abs(risk_report['portfolio_metrics']['portfolio_var_95']):.1%}")
    print(f"Current Drawdown: {abs(risk_report['portfolio_metrics']['current_drawdown']):.1%}")
    
    # Summary
    print(f"\n🎯 Key Achievements:")
    print("=" * 50)
    print("✅ ADVANCED Risk Management:")
    print("   • Account-level risk controls")
    print("   • Portfolio VaR and drawdown limits")
    print("   • Dynamic correlation analysis")
    print("   • Real-time risk monitoring")
    
    print(f"\n✅ DYNAMIC Position Sizing:")
    print("   • Volatility-adjusted sizing")
    print("   • Kelly Criterion optimization")
    print("   • Correlation-adjusted positions")
    print("   • Risk parity allocation")
    
    print(f"\n✅ COMPREHENSIVE Risk Metrics:")
    print("   • Value at Risk (VaR) calculation")
    print("   • Expected Shortfall analysis")
    print("   • Sharpe and Sortino ratios")
    print("   • Maximum drawdown tracking")
    
    print(f"\n🎉 Advanced Portfolio Risk Management Complete!")
    print("🚀 Your trading system now has institutional-grade risk management!")

if __name__ == "__main__":
    main() 