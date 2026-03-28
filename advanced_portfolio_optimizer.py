#!/usr/bin/env python3
"""
🎯 ADVANCED PORTFOLIO OPTIMIZER 🎯
Sophisticated portfolio optimization using:
- Modern Portfolio Theory (Markowitz)
- Black-Litterman Model
- Risk Parity
- Kelly Criterion
- CVaR Optimization
- Dynamic Rebalancing
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Optimization libraries
import cvxpy as cp
from scipy.optimize import minimize, differential_evolution
from scipy.stats import norm, multivariate_normal
import scipy.linalg as la

# ML libraries
from sklearn.covariance import LedoitWolf, OAS
from sklearn.preprocessing import StandardScaler
import numpy.linalg as npla

# Visualization
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationMethod(Enum):
    """Portfolio optimization methods"""
    MARKOWITZ = "markowitz"
    BLACK_LITTERMAN = "black_litterman"
    RISK_PARITY = "risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    CVAR_OPTIMIZATION = "cvar_optimization"
    HIERARCHICAL_RISK_PARITY = "hrp"

@dataclass
class PortfolioConstraints:
    """Portfolio optimization constraints"""
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_concentration: float = 0.3  # Max weight in single asset
    min_positions: int = 3
    max_positions: int = 20
    target_volatility: Optional[float] = None
    target_return: Optional[float] = None
    max_turnover: Optional[float] = None

@dataclass
class OptimizationResult:
    """Portfolio optimization result"""
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    method: OptimizationMethod
    rebalance_frequency: str
    constraints_satisfied: bool
    optimization_time: float

class AdvancedPortfolioOptimizer:
    """Advanced portfolio optimization engine"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize the portfolio optimizer"""
        self.risk_free_rate = risk_free_rate
        self.covariance_estimator = LedoitWolf()
        self.scaler = StandardScaler()
        
        # Market views for Black-Litterman
        self.market_views = {}
        self.view_confidence = {}
        
        logger.info("🎯 Advanced Portfolio Optimizer initialized")
    
    def prepare_data(self, price_data: Dict[str, pd.Series], 
                    lookback_days: int = 252) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare price data for optimization"""
        try:
            # Convert to DataFrame
            prices_df = pd.DataFrame(price_data)
            
            # Calculate returns
            returns_df = prices_df.pct_change().dropna()
            
            # Use only recent data
            if len(returns_df) > lookback_days:
                returns_df = returns_df.tail(lookback_days)
                prices_df = prices_df.tail(lookback_days + 1)
            
            # Remove assets with insufficient data
            min_observations = max(30, lookback_days // 4)
            valid_assets = returns_df.count() >= min_observations
            returns_df = returns_df.loc[:, valid_assets]
            prices_df = prices_df.loc[:, valid_assets]
            
            logger.info(f"📊 Prepared data: {len(returns_df.columns)} assets, {len(returns_df)} observations")
            
            return prices_df, returns_df
            
        except Exception as e:
            logger.error(f"Error preparing data: {e}")
            raise
    
    def estimate_parameters(self, returns_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Estimate expected returns and covariance matrix"""
        try:
            # Expected returns using multiple methods
            returns_mean = self._estimate_expected_returns(returns_df)
            
            # Covariance matrix with shrinkage
            returns_cov = self._estimate_covariance_matrix(returns_df)
            
            return returns_mean, returns_cov
            
        except Exception as e:
            logger.error(f"Error estimating parameters: {e}")
            raise
    
    def _estimate_expected_returns(self, returns_df: pd.DataFrame) -> np.ndarray:
        """Estimate expected returns using multiple methods"""
        methods = {}
        
        # Historical mean
        methods['historical'] = returns_df.mean().values
        
        # Exponentially weighted mean
        methods['ewm'] = returns_df.ewm(span=60).mean().iloc[-1].values
        
        # CAPM-based (simplified)
        market_return = returns_df.mean(axis=1)
        betas = []
        for col in returns_df.columns:
            beta = np.cov(returns_df[col], market_return)[0, 1] / np.var(market_return)
            expected_return = self.risk_free_rate + beta * (market_return.mean() - self.risk_free_rate)
            betas.append(expected_return)
        methods['capm'] = np.array(betas)
        
        # Ensemble approach
        weights = {'historical': 0.4, 'ewm': 0.4, 'capm': 0.2}
        expected_returns = sum(weights[method] * returns for method, returns in methods.items())
        
        return expected_returns
    
    def _estimate_covariance_matrix(self, returns_df: pd.DataFrame) -> np.ndarray:
        """Estimate covariance matrix with shrinkage"""
        try:
            # Ledoit-Wolf shrinkage
            cov_lw, _ = self.covariance_estimator.fit(returns_df).covariance_, self.covariance_estimator.shrinkage_
            
            # Ensure positive definite
            eigenvals, eigenvecs = npla.eigh(cov_lw)
            eigenvals = np.maximum(eigenvals, 1e-8)
            cov_matrix = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
            
            return cov_matrix
            
        except Exception as e:
            logger.error(f"Error estimating covariance: {e}")
            return np.cov(returns_df.T)
    
    def markowitz_optimization(self, expected_returns: np.ndarray, 
                             cov_matrix: np.ndarray,
                             constraints: PortfolioConstraints) -> np.ndarray:
        """Markowitz mean-variance optimization"""
        try:
            n_assets = len(expected_returns)
            weights = cp.Variable(n_assets)
            
            # Objective: maximize Sharpe ratio (equivalent to min variance for given return)
            portfolio_return = expected_returns.T @ weights
            portfolio_variance = cp.quad_form(weights, cov_matrix)
            
            # Constraints
            constraints_list = [
                cp.sum(weights) == 1,  # Fully invested
                weights >= constraints.min_weight,
                weights <= constraints.max_weight
            ]
            
            # Maximum concentration constraint
            if constraints.max_concentration < 1.0:
                constraints_list.append(weights <= constraints.max_concentration)
            
            # Target return constraint
            if constraints.target_return is not None:
                constraints_list.append(portfolio_return >= constraints.target_return)
            
            # Solve optimization
            if constraints.target_return is not None:
                # Minimize variance for target return
                objective = cp.Minimize(portfolio_variance)
            else:
                # Maximize Sharpe ratio
                objective = cp.Maximize(portfolio_return - 0.5 * portfolio_variance)
            
            problem = cp.Problem(objective, constraints_list)
            problem.solve(solver=cp.ECOS)
            
            if problem.status not in ["infeasible", "unbounded"]:
                return weights.value
            else:
                logger.warning("Markowitz optimization failed, using equal weights")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"Error in Markowitz optimization: {e}")
            return np.ones(len(expected_returns)) / len(expected_returns)
    
    def black_litterman_optimization(self, expected_returns: np.ndarray,
                                   cov_matrix: np.ndarray,
                                   market_caps: Optional[np.ndarray] = None) -> np.ndarray:
        """Black-Litterman optimization with market views"""
        try:
            n_assets = len(expected_returns)
            
            # Market capitalization weights (if not provided, use equal weights)
            if market_caps is None:
                w_market = np.ones(n_assets) / n_assets
            else:
                w_market = market_caps / np.sum(market_caps)
            
            # Risk aversion parameter
            risk_aversion = 3.0
            
            # Implied equilibrium returns
            pi = risk_aversion * cov_matrix @ w_market
            
            # Black-Litterman formula
            if self.market_views:
                # Views matrix P and views vector Q
                P, Q, omega = self._construct_views_matrices(n_assets)
                
                # Tau parameter (uncertainty in prior)
                tau = 1 / len(expected_returns)
                
                # Black-Litterman expected returns
                M1 = npla.inv(tau * cov_matrix)
                M2 = P.T @ npla.inv(omega) @ P
                M3 = npla.inv(tau * cov_matrix) @ pi
                M4 = P.T @ npla.inv(omega) @ Q
                
                mu_bl = npla.inv(M1 + M2) @ (M3 + M4)
                
                # Black-Litterman covariance
                cov_bl = npla.inv(M1 + M2)
            else:
                # No views, use equilibrium
                mu_bl = pi
                cov_bl = cov_matrix
            
            # Optimize with Black-Litterman parameters
            weights = cp.Variable(n_assets)
            portfolio_return = mu_bl.T @ weights
            portfolio_variance = cp.quad_form(weights, cov_bl)
            
            objective = cp.Maximize(portfolio_return - 0.5 * risk_aversion * portfolio_variance)
            constraints_list = [
                cp.sum(weights) == 1,
                weights >= 0
            ]
            
            problem = cp.Problem(objective, constraints_list)
            problem.solve()
            
            if problem.status not in ["infeasible", "unbounded"]:
                return weights.value
            else:
                return w_market
                
        except Exception as e:
            logger.error(f"Error in Black-Litterman optimization: {e}")
            return np.ones(len(expected_returns)) / len(expected_returns)
    
    def risk_parity_optimization(self, cov_matrix: np.ndarray,
                               target_risk_contributions: Optional[np.ndarray] = None) -> np.ndarray:
        """Risk parity optimization"""
        try:
            n_assets = len(cov_matrix)
            
            if target_risk_contributions is None:
                target_risk_contributions = np.ones(n_assets) / n_assets
            
            def risk_parity_objective(weights):
                """Risk parity objective function"""
                weights = np.array(weights)
                portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
                
                # Risk contributions
                marginal_contrib = cov_matrix @ weights
                risk_contrib = weights * marginal_contrib / portfolio_vol
                
                # Minimize squared deviations from target risk contributions
                return np.sum((risk_contrib - target_risk_contributions * portfolio_vol)**2)
            
            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Fully invested
            ]
            
            bounds = [(0.001, 0.5) for _ in range(n_assets)]  # Long-only with max 50% per asset
            
            # Initial guess
            x0 = np.ones(n_assets) / n_assets
            
            # Optimize
            result = minimize(
                risk_parity_objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )
            
            if result.success:
                return result.x
            else:
                logger.warning("Risk parity optimization failed, using equal weights")
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"Error in risk parity optimization: {e}")
            return np.ones(len(cov_matrix)) / len(cov_matrix)
    
    def kelly_criterion_optimization(self, expected_returns: np.ndarray,
                                   cov_matrix: np.ndarray,
                                   max_leverage: float = 1.0) -> np.ndarray:
        """Kelly Criterion optimization for maximum geometric growth"""
        try:
            n_assets = len(expected_returns)
            
            def kelly_objective(weights):
                """Kelly criterion objective (negative log growth rate)"""
                weights = np.array(weights)
                
                # Expected log return
                portfolio_return = weights.T @ expected_returns
                portfolio_variance = weights.T @ cov_matrix @ weights
                
                # Kelly approximation: E[log(1+r)] ≈ E[r] - 0.5*Var[r]
                log_growth = portfolio_return - 0.5 * portfolio_variance
                
                return -log_growth  # Minimize negative log growth
            
            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - max_leverage},
            ]
            
            bounds = [(-0.5, 1.0) for _ in range(n_assets)]  # Allow some shorting
            
            # Initial guess
            x0 = np.ones(n_assets) / n_assets * max_leverage
            
            # Optimize
            result = minimize(
                kelly_objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                return result.x
            else:
                return np.ones(n_assets) / n_assets * max_leverage
                
        except Exception as e:
            logger.error(f"Error in Kelly optimization: {e}")
            return np.ones(len(expected_returns)) / len(expected_returns)
    
    def cvar_optimization(self, returns_df: pd.DataFrame,
                         alpha: float = 0.05,
                         target_return: Optional[float] = None) -> np.ndarray:
        """Conditional Value at Risk (CVaR) optimization"""
        try:
            n_assets = len(returns_df.columns)
            n_scenarios = len(returns_df)
            
            # Decision variables
            weights = cp.Variable(n_assets)
            var = cp.Variable()
            u = cp.Variable(n_scenarios, nonneg=True)
            
            # Portfolio returns for each scenario
            portfolio_returns = returns_df.values @ weights
            
            # CVaR constraints
            constraints = [
                cp.sum(weights) == 1,  # Fully invested
                weights >= 0,  # Long-only
                u >= -(portfolio_returns - var)  # CVaR constraint
            ]
            
            # Target return constraint
            if target_return is not None:
                expected_return = cp.sum(cp.multiply(returns_df.mean().values, weights))
                constraints.append(expected_return >= target_return)
            
            # Objective: minimize CVaR
            cvar = var - (1/alpha) * cp.sum(u) / n_scenarios
            objective = cp.Minimize(-cvar)  # Maximize CVaR (minimize negative CVaR)
            
            problem = cp.Problem(objective, constraints)
            problem.solve()
            
            if problem.status not in ["infeasible", "unbounded"]:
                return weights.value
            else:
                return np.ones(n_assets) / n_assets
                
        except Exception as e:
            logger.error(f"Error in CVaR optimization: {e}")
            return np.ones(len(returns_df.columns)) / len(returns_df.columns)
    
    def hierarchical_risk_parity(self, cov_matrix: np.ndarray,
                                asset_names: List[str]) -> np.ndarray:
        """Hierarchical Risk Parity (HRP) optimization"""
        try:
            from scipy.cluster.hierarchy import linkage, dendrogram
            from scipy.spatial.distance import squareform
            
            # Convert covariance to correlation
            std_devs = np.sqrt(np.diag(cov_matrix))
            corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
            
            # Distance matrix
            distance_matrix = np.sqrt(0.5 * (1 - corr_matrix))
            
            # Hierarchical clustering
            condensed_distances = squareform(distance_matrix, checks=False)
            linkage_matrix = linkage(condensed_distances, method='ward')
            
            # Get clusters
            clusters = self._get_clusters(linkage_matrix, len(asset_names))
            
            # Allocate weights hierarchically
            weights = self._allocate_hrp_weights(cov_matrix, clusters)
            
            return weights
            
        except Exception as e:
            logger.error(f"Error in HRP optimization: {e}")
            return np.ones(len(cov_matrix)) / len(cov_matrix)
    
    def _get_clusters(self, linkage_matrix: np.ndarray, n_assets: int) -> List[List[int]]:
        """Get clusters from linkage matrix"""
        clusters = [[i] for i in range(n_assets)]
        
        for i in range(len(linkage_matrix)):
            cluster1_idx = int(linkage_matrix[i, 0])
            cluster2_idx = int(linkage_matrix[i, 1])
            
            # Merge clusters
            new_cluster = clusters[cluster1_idx] + clusters[cluster2_idx]
            clusters.append(new_cluster)
        
        return clusters[-1:]  # Return the final merged cluster structure
    
    def _allocate_hrp_weights(self, cov_matrix: np.ndarray, clusters: List[List[int]]) -> np.ndarray:
        """Allocate weights using HRP methodology"""
        n_assets = len(cov_matrix)
        weights = np.ones(n_assets)
        
        def _get_cluster_var(cluster_indices):
            """Get cluster variance"""
            cluster_cov = cov_matrix[np.ix_(cluster_indices, cluster_indices)]
            inv_diag = 1 / np.diag(cluster_cov)
            inv_diag /= inv_diag.sum()
            return inv_diag.T @ cluster_cov @ inv_diag
        
        # Recursive bisection
        def _recursive_bisection(cluster_indices):
            if len(cluster_indices) == 1:
                return
            
            # Split cluster in half
            mid = len(cluster_indices) // 2
            left_cluster = cluster_indices[:mid]
            right_cluster = cluster_indices[mid:]
            
            # Calculate cluster variances
            left_var = _get_cluster_var(left_cluster)
            right_var = _get_cluster_var(right_cluster)
            
            # Allocate weights inversely proportional to variance
            total_var = left_var + right_var
            left_weight = right_var / total_var
            right_weight = left_var / total_var
            
            # Update weights
            weights[left_cluster] *= left_weight
            weights[right_cluster] *= right_weight
            
            # Recurse
            _recursive_bisection(left_cluster)
            _recursive_bisection(right_cluster)
        
        _recursive_bisection(list(range(n_assets)))
        
        return weights / weights.sum()
    
    def _construct_views_matrices(self, n_assets: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Construct views matrices for Black-Litterman"""
        n_views = len(self.market_views)
        P = np.zeros((n_views, n_assets))
        Q = np.zeros(n_views)
        omega = np.eye(n_views)
        
        for i, (view_name, view_data) in enumerate(self.market_views.items()):
            # This would be implemented based on specific view structure
            pass
        
        return P, Q, omega
    
    def optimize_portfolio(self, price_data: Dict[str, pd.Series],
                         method: OptimizationMethod = OptimizationMethod.MARKOWITZ,
                         constraints: Optional[PortfolioConstraints] = None,
                         lookback_days: int = 252) -> OptimizationResult:
        """Main portfolio optimization function"""
        start_time = datetime.now()
        
        try:
            # Default constraints
            if constraints is None:
                constraints = PortfolioConstraints()
            
            # Prepare data
            prices_df, returns_df = self.prepare_data(price_data, lookback_days)
            
            # Estimate parameters
            expected_returns, cov_matrix = self.estimate_parameters(returns_df)
            
            # Optimize based on method
            if method == OptimizationMethod.MARKOWITZ:
                weights = self.markowitz_optimization(expected_returns, cov_matrix, constraints)
            elif method == OptimizationMethod.BLACK_LITTERMAN:
                weights = self.black_litterman_optimization(expected_returns, cov_matrix)
            elif method == OptimizationMethod.RISK_PARITY:
                weights = self.risk_parity_optimization(cov_matrix)
            elif method == OptimizationMethod.KELLY_CRITERION:
                weights = self.kelly_criterion_optimization(expected_returns, cov_matrix)
            elif method == OptimizationMethod.CVAR_OPTIMIZATION:
                weights = self.cvar_optimization(returns_df)
            elif method == OptimizationMethod.HIERARCHICAL_RISK_PARITY:
                weights = self.hierarchical_risk_parity(cov_matrix, list(returns_df.columns))
            else:
                weights = np.ones(len(expected_returns)) / len(expected_returns)
            
            # Calculate portfolio metrics
            portfolio_return = np.sum(weights * expected_returns) * 252  # Annualized
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(252)  # Annualized
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
            
            # Calculate VaR and CVaR
            portfolio_returns = returns_df.values @ weights
            var_95 = np.percentile(portfolio_returns, 5)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            # Calculate max drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # Create weights dictionary
            weights_dict = {asset: weight for asset, weight in zip(returns_df.columns, weights)}
            
            # Check constraints
            constraints_satisfied = self._check_constraints(weights, constraints)
            
            optimization_time = (datetime.now() - start_time).total_seconds()
            
            result = OptimizationResult(
                weights=weights_dict,
                expected_return=portfolio_return,
                expected_volatility=portfolio_vol,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                var_95=var_95,
                cvar_95=cvar_95,
                method=method,
                rebalance_frequency="monthly",
                constraints_satisfied=constraints_satisfied,
                optimization_time=optimization_time
            )
            
            logger.info(f"✅ Portfolio optimization completed: {method.value}")
            logger.info(f"   Expected Return: {portfolio_return:.2%}")
            logger.info(f"   Expected Volatility: {portfolio_vol:.2%}")
            logger.info(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            raise
    
    def _check_constraints(self, weights: np.ndarray, constraints: PortfolioConstraints) -> bool:
        """Check if portfolio satisfies constraints"""
        try:
            # Weight bounds
            if np.any(weights < constraints.min_weight) or np.any(weights > constraints.max_weight):
                return False
            
            # Concentration constraint
            if np.max(weights) > constraints.max_concentration:
                return False
            
            # Number of positions
            active_positions = np.sum(weights > 0.001)
            if active_positions < constraints.min_positions or active_positions > constraints.max_positions:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking constraints: {e}")
            return False
    
    def create_efficient_frontier(self, price_data: Dict[str, pd.Series],
                                n_portfolios: int = 100) -> pd.DataFrame:
        """Create efficient frontier"""
        try:
            prices_df, returns_df = self.prepare_data(price_data)
            expected_returns, cov_matrix = self.estimate_parameters(returns_df)
            
            # Range of target returns
            min_return = np.min(expected_returns)
            max_return = np.max(expected_returns)
            target_returns = np.linspace(min_return, max_return, n_portfolios)
            
            efficient_portfolios = []
            
            for target_return in target_returns:
                constraints = PortfolioConstraints(target_return=target_return)
                weights = self.markowitz_optimization(expected_returns, cov_matrix, constraints)
                
                portfolio_return = np.sum(weights * expected_returns) * 252
                portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(252)
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
                
                efficient_portfolios.append({
                    'return': portfolio_return,
                    'volatility': portfolio_vol,
                    'sharpe_ratio': sharpe_ratio,
                    'weights': weights
                })
            
            return pd.DataFrame(efficient_portfolios)
            
        except Exception as e:
            logger.error(f"Error creating efficient frontier: {e}")
            return pd.DataFrame()
    
    def visualize_portfolio(self, result: OptimizationResult) -> go.Figure:
        """Visualize portfolio allocation"""
        try:
            # Filter out very small weights
            significant_weights = {k: v for k, v in result.weights.items() if v > 0.01}
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(significant_weights.keys()),
                    values=list(significant_weights.values()),
                    hole=0.3,
                    textinfo='label+percent',
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title=f"Portfolio Allocation - {result.method.value.title()}",
                annotations=[dict(text=f'Sharpe: {result.sharpe_ratio:.2f}', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error visualizing portfolio: {e}")
            return go.Figure()

def main():
    """Example usage"""
    # Create sample data
    np.random.seed(42)
    n_assets = 10
    n_days = 500
    
    # Generate correlated returns
    correlation = 0.3
    cov_matrix = correlation * np.ones((n_assets, n_assets)) + (1 - correlation) * np.eye(n_assets)
    returns = np.random.multivariate_normal(np.zeros(n_assets), cov_matrix * 0.01, n_days)
    
    # Create price series
    prices = {}
    asset_names = [f"Asset_{i+1}" for i in range(n_assets)]
    
    for i, name in enumerate(asset_names):
        price_series = 100 * (1 + returns[:, i]).cumprod()
        prices[name] = pd.Series(price_series, index=pd.date_range('2022-01-01', periods=n_days))
    
    # Initialize optimizer
    optimizer = AdvancedPortfolioOptimizer()
    
    # Test different optimization methods
    methods = [
        OptimizationMethod.MARKOWITZ,
        OptimizationMethod.RISK_PARITY,
        OptimizationMethod.KELLY_CRITERION
    ]
    
    for method in methods:
        print(f"\n🎯 Testing {method.value.upper()} optimization:")
        result = optimizer.optimize_portfolio(prices, method=method)
        
        print(f"Expected Return: {result.expected_return:.2%}")
        print(f"Expected Volatility: {result.expected_volatility:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        
        # Show top 5 holdings
        sorted_weights = sorted(result.weights.items(), key=lambda x: x[1], reverse=True)
        print("Top 5 holdings:")
        for asset, weight in sorted_weights[:5]:
            print(f"  {asset}: {weight:.1%}")

if __name__ == "__main__":
    main()