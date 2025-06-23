#!/usr/bin/env python3
"""
🎯 Integrated Time Series Cross-Validation Trading System
Replaces naive train_test_split with proper time series validation
Prevents look-ahead bias and provides realistic performance estimates
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

# Technical analysis
import talib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeSeriesCVTradingSystem:
    """
    Advanced trading system with proper time series cross-validation
    Eliminates look-ahead bias and provides realistic performance estimates
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.models = {}
        self.scalers = {}
        self.validation_results = {}
        self.feature_importance = {}
        
        logger.info("🎯 Time Series CV Trading System initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            # Time series CV settings
            'cv_method': 'walk_forward',     # walk_forward, expanding_window, rolling_window
            'initial_train_ratio': 0.5,     # Initial training set size
            'test_ratio': 0.1,              # Test set size per fold
            'step_ratio': 0.05,             # Step size for walk-forward
            'min_train_samples': 100,       # Minimum training samples
            'gap_ratio': 0.01,              # Gap between train/test (prevent leakage)
            
            # Model settings
            'models': {
                'random_forest': {
                    'class': RandomForestRegressor,
                    'params': {'n_estimators': 50, 'max_depth': 8, 'random_state': 42}
                },
                'gradient_boosting': {
                    'class': GradientBoostingRegressor,
                    'params': {'n_estimators': 50, 'max_depth': 4, 'random_state': 42}
                },
                'ridge': {
                    'class': Ridge,
                    'params': {'alpha': 1.0, 'random_state': 42}
                }
            },
            
            # Feature engineering
            'technical_indicators': [
                'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26',
                'RSI_14', 'MACD', 'MACD_signal',
                'BB_upper', 'BB_middle', 'BB_lower',
                'ATR_14', 'ADX_14',
                'STOCH_K', 'STOCH_D',
                'CCI_14', 'MFI_14'
            ],
            
            # Performance metrics
            'metrics': ['r2', 'mse', 'mae', 'directional_accuracy', 'sharpe_ratio'],
            'target_column': 'close',
            'prediction_horizon': 1,        # Predict 1 period ahead
            
            # Risk management
            'max_position_size': 0.1,       # 10% max position
            'stop_loss': 0.02,              # 2% stop loss
            'take_profit': 0.04,            # 4% take profit
            
            # System settings
            'scaler_type': 'robust',        # robust, standard
            'n_jobs': -1,
            'random_state': 42
        }
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare technical indicators and features"""
        
        logger.info("📊 Preparing technical features...")
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Create copy to avoid modifying original
        data = df.copy()
        
        # Price-based indicators
        data['SMA_10'] = talib.SMA(data['close'], timeperiod=10)
        data['SMA_20'] = talib.SMA(data['close'], timeperiod=20)
        data['SMA_50'] = talib.SMA(data['close'], timeperiod=50)
        
        data['EMA_12'] = talib.EMA(data['close'], timeperiod=12)
        data['EMA_26'] = talib.EMA(data['close'], timeperiod=26)
        
        # Momentum indicators
        data['RSI_14'] = talib.RSI(data['close'], timeperiod=14)
        data['MACD'], data['MACD_signal'], _ = talib.MACD(data['close'])
        
        # Bollinger Bands
        data['BB_upper'], data['BB_middle'], data['BB_lower'] = talib.BBANDS(data['close'])
        
        # Volatility indicators
        data['ATR_14'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
        data['ADX_14'] = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
        
        # Stochastic
        data['STOCH_K'], data['STOCH_D'] = talib.STOCH(data['high'], data['low'], data['close'])
        
        # Other indicators
        data['CCI_14'] = talib.CCI(data['high'], data['low'], data['close'], timeperiod=14)
        data['MFI_14'] = talib.MFI(data['high'], data['low'], data['close'], data['volume'], timeperiod=14)
        
        # Price-based features
        data['price_change'] = data['close'].pct_change()
        data['high_low_ratio'] = data['high'] / data['low']
        data['volume_sma_ratio'] = data['volume'] / talib.SMA(data['volume'], timeperiod=20)
        
        # Lagged features (important for time series)
        for lag in [1, 2, 3, 5]:
            data[f'close_lag_{lag}'] = data['close'].shift(lag)
            data[f'volume_lag_{lag}'] = data['volume'].shift(lag)
            data[f'price_change_lag_{lag}'] = data['price_change'].shift(lag)
        
        # Target variable (next period's return)
        data['target'] = data['close'].shift(-self.config['prediction_horizon']).pct_change()
        
        # Drop rows with NaN values
        data = data.dropna()
        
        logger.info(f"✅ Features prepared: {data.shape[1]} columns, {len(data)} samples")
        
        return data
    
    def walk_forward_validation(self, 
                              X: np.ndarray, 
                              y: np.ndarray, 
                              dates: pd.DatetimeIndex,
                              model_name: str) -> Dict[str, Any]:
        """
        Walk-forward validation for time series
        Most realistic validation for trading systems
        """
        
        logger.info(f"🚶 Walk-forward validation for {model_name}...")
        
        n_samples = len(X)
        initial_train_size = max(
            self.config['min_train_samples'],
            int(n_samples * self.config['initial_train_ratio'])
        )
        test_size = max(1, int(n_samples * self.config['test_ratio']))
        step_size = max(1, int(n_samples * self.config['step_ratio']))
        gap_size = max(0, int(n_samples * self.config['gap_ratio']))
        
        # Get model configuration
        model_config = self.config['models'][model_name]
        
        results = {
            'fold_results': [],
            'predictions': [],
            'actuals': [],
            'dates': [],
            'model_name': model_name
        }
        
        fold = 0
        
        while True:
            # Define training window (expanding)
            train_start = 0
            train_end = initial_train_size + fold * step_size
            
            # Add gap to prevent data leakage
            gap_end = train_end + gap_size
            
            # Define test window
            test_start = gap_end
            test_end = min(test_start + test_size, n_samples)
            
            # Check if we have enough data
            if test_end > n_samples or train_end - train_start < self.config['min_train_samples']:
                break
            
            # Extract data
            X_train = X[train_start:train_end]
            y_train = y[train_start:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            if len(X_test) == 0:
                break
            
            # Scale features
            scaler = self._get_scaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = model_config['class'](**model_config['params'])
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            fold_metrics = self._calculate_comprehensive_metrics(y_test, y_pred)
            
            # Store results
            fold_result = {
                'fold': fold + 1,
                'train_start': dates[train_start],
                'train_end': dates[train_end-1],
                'test_start': dates[test_start],
                'test_end': dates[test_end-1],
                'train_size': len(X_train),
                'test_size': len(X_test),
                'gap_size': gap_size,
                **fold_metrics
            }
            
            results['fold_results'].append(fold_result)
            results['predictions'].extend(y_pred.tolist())
            results['actuals'].extend(y_test.tolist())
            results['dates'].extend(dates[test_start:test_end])
            
            logger.info(f"   Fold {fold+1}: R² = {fold_metrics['r2']:.4f}, "
                       f"Directional Acc = {fold_metrics['directional_accuracy']:.3f}")
            
            fold += 1
        
        # Calculate overall metrics
        overall_metrics = self._calculate_comprehensive_metrics(
            np.array(results['actuals']), np.array(results['predictions'])
        )
        
        # Calculate fold statistics
        fold_r2_scores = [f['r2'] for f in results['fold_results']]
        fold_dir_acc = [f['directional_accuracy'] for f in results['fold_results']]
        
        results['summary'] = {
            'n_folds': len(results['fold_results']),
            'mean_r2': np.mean(fold_r2_scores),
            'std_r2': np.std(fold_r2_scores),
            'mean_directional_accuracy': np.mean(fold_dir_acc),
            'std_directional_accuracy': np.std(fold_dir_acc),
            'overall_metrics': overall_metrics,
            'stability_score': 1 / (1 + np.std(fold_r2_scores))  # Higher is more stable
        }
        
        logger.info(f"✅ Walk-forward validation complete: {len(results['fold_results'])} folds")
        logger.info(f"   Mean R²: {results['summary']['mean_r2']:.4f} ± {results['summary']['std_r2']:.4f}")
        logger.info(f"   Mean Directional Accuracy: {results['summary']['mean_directional_accuracy']:.3f}")
        
        return results
    
    def expanding_window_validation(self, 
                                  X: np.ndarray, 
                                  y: np.ndarray, 
                                  dates: pd.DatetimeIndex,
                                  model_name: str) -> Dict[str, Any]:
        """
        Expanding window validation
        Training set grows over time
        """
        
        logger.info(f"📈 Expanding window validation for {model_name}...")
        
        n_samples = len(X)
        min_train_size = max(
            self.config['min_train_samples'],
            int(n_samples * 0.3)
        )
        test_size = max(1, int(n_samples * self.config['test_ratio']))
        step_size = max(1, int(n_samples * 0.1))
        
        model_config = self.config['models'][model_name]
        
        results = {
            'fold_results': [],
            'predictions': [],
            'actuals': [],
            'dates': [],
            'model_name': model_name
        }
        
        fold = 0
        
        while True:
            # Expanding training window (always from start)
            train_end = min_train_size + fold * step_size
            
            # Test window
            test_start = train_end
            test_end = min(test_start + test_size, n_samples)
            
            if test_end > n_samples:
                break
            
            # Extract data
            X_train = X[0:train_end]  # Always from beginning
            y_train = y[0:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            # Scale and train
            scaler = self._get_scaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            model = model_config['class'](**model_config['params'])
            model.fit(X_train_scaled, y_train)
            
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            fold_metrics = self._calculate_comprehensive_metrics(y_test, y_pred)
            
            fold_result = {
                'fold': fold + 1,
                'train_size': len(X_train),
                'test_size': len(X_test),
                **fold_metrics
            }
            
            results['fold_results'].append(fold_result)
            results['predictions'].extend(y_pred.tolist())
            results['actuals'].extend(y_test.tolist())
            
            fold += 1
        
        # Calculate overall metrics
        overall_metrics = self._calculate_comprehensive_metrics(
            np.array(results['actuals']), np.array(results['predictions'])
        )
        
        # Calculate summary
        fold_r2_scores = [f['r2'] for f in results['fold_results']]
        results['summary'] = {
            'n_folds': len(results['fold_results']),
            'mean_r2': np.mean(fold_r2_scores),
            'std_r2': np.std(fold_r2_scores),
            'overall_metrics': overall_metrics
        }
        
        return results
    
    def compare_validation_methods(self, 
                                 X: np.ndarray, 
                                 y: np.ndarray, 
                                 dates: pd.DatetimeIndex) -> Dict[str, Any]:
        """
        Compare different validation methods across all models
        """
        
        logger.info("🔍 Comparing validation methods across models...")
        
        results = {
            'walk_forward': {},
            'expanding_window': {},
            'comparison_summary': {}
        }
        
        # Test each model with each validation method
        for model_name in self.config['models'].keys():
            logger.info(f"\n--- Testing {model_name.upper()} ---")
            
            # Walk-forward validation
            wf_results = self.walk_forward_validation(X, y, dates, model_name)
            results['walk_forward'][model_name] = wf_results
            
            # Expanding window validation
            ew_results = self.expanding_window_validation(X, y, dates, model_name)
            results['expanding_window'][model_name] = ew_results
        
        # Create comparison summary
        comparison = {}
        
        for model_name in self.config['models'].keys():
            wf_score = results['walk_forward'][model_name]['summary']['mean_r2']
            ew_score = results['expanding_window'][model_name]['summary']['mean_r2']
            
            wf_stability = results['walk_forward'][model_name]['summary']['stability_score']
            
            comparison[model_name] = {
                'walk_forward_r2': wf_score,
                'expanding_window_r2': ew_score,
                'stability_score': wf_stability,
                'recommended_method': 'walk_forward' if wf_score > ew_score else 'expanding_window'
            }
        
        # Find best model
        best_model = max(comparison.keys(), 
                        key=lambda x: comparison[x]['walk_forward_r2'])
        
        results['comparison_summary'] = {
            'model_comparison': comparison,
            'best_model': best_model,
            'best_score': comparison[best_model]['walk_forward_r2'],
            'recommendation': f"Use {best_model} with walk-forward validation"
        }
        
        logger.info(f"\n🏆 BEST MODEL: {best_model}")
        logger.info(f"   Walk-forward R²: {comparison[best_model]['walk_forward_r2']:.4f}")
        logger.info(f"   Stability score: {comparison[best_model]['stability_score']:.4f}")
        
        return results
    
    def _get_scaler(self):
        """Get appropriate scaler"""
        if self.config['scaler_type'] == 'robust':
            return RobustScaler()
        else:
            return StandardScaler()
    
    def _calculate_comprehensive_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        
        # Ensure inputs are numpy arrays
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        metrics = {}
        
        # Regression metrics
        metrics['r2'] = r2_score(y_true, y_pred)
        metrics['mse'] = mean_squared_error(y_true, y_pred)
        metrics['rmse'] = np.sqrt(metrics['mse'])
        metrics['mae'] = mean_absolute_error(y_true, y_pred)
        
        # Financial metrics
        # Directional accuracy (most important for trading)
        direction_true = np.sign(y_true)
        direction_pred = np.sign(y_pred)
        metrics['directional_accuracy'] = np.mean(direction_true == direction_pred)
        
        # Hit ratio (predictions within 1% of actual)
        relative_error = np.abs((y_pred - y_true) / (np.abs(y_true) + 1e-8))
        metrics['hit_ratio_1pct'] = np.mean(relative_error <= 0.01)
        
        # Sharpe-like ratio for predictions
        if np.std(y_pred) > 0:
            metrics['prediction_sharpe'] = np.mean(y_pred) / np.std(y_pred)
        else:
            metrics['prediction_sharpe'] = 0.0
        
        return metrics
    
    def generate_trading_signals(self, predictions: np.ndarray, threshold: float = 0.001) -> np.ndarray:
        """
        Generate trading signals from predictions
        """
        
        predictions = np.array(predictions)
        signals = np.zeros(len(predictions))
        
        # Buy signal: prediction > threshold
        signals[predictions > threshold] = 1
        
        # Sell signal: prediction < -threshold
        signals[predictions < -threshold] = -1
        
        # Hold signal: |prediction| <= threshold
        # signals already initialized to 0
        
        return signals
    
    def backtest_strategy(self, 
                         predictions: np.ndarray, 
                         actual_returns: np.ndarray,
                         dates: pd.DatetimeIndex) -> Dict[str, Any]:
        """
        Simple backtest of trading strategy
        """
        
        predictions = np.array(predictions)
        actual_returns = np.array(actual_returns)
        
        signals = self.generate_trading_signals(predictions)
        
        # Calculate strategy returns
        strategy_returns = signals[:-1] * actual_returns[1:]  # Shift to avoid look-ahead
        
        # Performance metrics
        total_return = np.prod(1 + strategy_returns) - 1
        annualized_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
        volatility = np.std(strategy_returns) * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = np.cumprod(1 + strategy_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Win rate
        winning_trades = strategy_returns[strategy_returns > 0]
        win_rate = len(winning_trades) / len(strategy_returns[strategy_returns != 0]) if len(strategy_returns[strategy_returns != 0]) > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': np.sum(signals != 0),
            'strategy_returns': strategy_returns,
            'signals': signals
        }
    
    def train_and_validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Main method to train and validate the trading system
        """
        
        logger.info("🎯 Starting comprehensive time series validation...")
        
        # Prepare features
        data = self.prepare_features(df)
        
        # Prepare feature matrix and target
        feature_cols = [col for col in data.columns 
                       if col not in ['target', 'open', 'high', 'low', 'close', 'volume']]
        
        X = data[feature_cols].values
        y = data['target'].values
        dates = data.index
        
        logger.info(f"📊 Dataset prepared: {X.shape[0]} samples, {X.shape[1]} features")
        
        # Compare validation methods
        validation_results = self.compare_validation_methods(X, y, dates)
        
        # Get best model results
        best_model = validation_results['comparison_summary']['best_model']
        best_results = validation_results['walk_forward'][best_model]
        
        # Backtest the best model
        backtest_results = self.backtest_strategy(
            np.array(best_results['predictions']),
            np.array(best_results['actuals']),
            pd.DatetimeIndex(best_results['dates'])
        )
        
        # Store results
        self.validation_results = validation_results
        
        final_results = {
            'validation_results': validation_results,
            'best_model': best_model,
            'backtest_results': backtest_results,
            'feature_columns': feature_cols,
            'data_shape': X.shape
        }
        
        # Print summary
        self._print_final_summary(final_results)
        
        return final_results
    
    def _print_final_summary(self, results: Dict[str, Any]):
        """Print comprehensive summary of results"""
        
        print(f"\n🎯 TIME SERIES CV TRADING SYSTEM RESULTS")
        print("=" * 60)
        
        best_model = results['best_model']
        validation = results['validation_results']
        backtest = results['backtest_results']
        
        print(f"📊 Dataset: {results['data_shape'][0]} samples, {results['data_shape'][1]} features")
        print(f"🏆 Best Model: {best_model}")
        
        # Validation performance
        wf_summary = validation['walk_forward'][best_model]['summary']
        print(f"\n✅ WALK-FORWARD VALIDATION PERFORMANCE:")
        print(f"   • Number of folds: {wf_summary['n_folds']}")
        print(f"   • Mean R²: {wf_summary['mean_r2']:.4f} ± {wf_summary['std_r2']:.4f}")
        print(f"   • Directional Accuracy: {wf_summary['mean_directional_accuracy']:.3f}")
        print(f"   • Stability Score: {wf_summary['stability_score']:.4f}")
        
        # Backtest performance
        print(f"\n💰 BACKTEST PERFORMANCE:")
        print(f"   • Total Return: {backtest['total_return']:.2%}")
        print(f"   • Annualized Return: {backtest['annualized_return']:.2%}")
        print(f"   • Volatility: {backtest['volatility']:.2%}")
        print(f"   • Sharpe Ratio: {backtest['sharpe_ratio']:.3f}")
        print(f"   • Maximum Drawdown: {backtest['max_drawdown']:.2%}")
        print(f"   • Win Rate: {backtest['win_rate']:.2%}")
        print(f"   • Total Trades: {backtest['total_trades']}")
        
        # Model comparison
        print(f"\n📈 MODEL COMPARISON:")
        comparison = validation['comparison_summary']['model_comparison']
        for model_name, metrics in comparison.items():
            print(f"   • {model_name}: R² = {metrics['walk_forward_r2']:.4f}, "
                  f"Stability = {metrics['stability_score']:.4f}")
        
        print(f"\n✅ ADVANTAGES OF TIME SERIES CV:")
        print("   • No look-ahead bias (never uses future data)")
        print("   • Realistic performance estimates")
        print("   • Simulates real trading conditions")
        print("   • Accounts for temporal dependencies")
        print("   • Provides stability metrics")
        print("   • Multiple validation methods compared")

def demonstrate_integrated_system():
    """Demonstrate the integrated time series CV trading system"""
    
    # Generate sample cryptocurrency data
    np.random.seed(42)
    n_samples = 800
    
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='1H')
    
    # Generate realistic OHLCV data
    returns = np.random.randn(n_samples) * 0.02
    for i in range(1, n_samples):
        returns[i] = 0.1 * returns[i-1] + 0.9 * returns[i]  # Add persistence
    
    prices = 100 * np.exp(np.cumsum(returns))
    
    # Create OHLCV data
    df = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_samples) * 0.001),
        'high': prices * (1 + np.abs(np.random.randn(n_samples)) * 0.002),
        'low': prices * (1 - np.abs(np.random.randn(n_samples)) * 0.002),
        'close': prices,
        'volume': np.random.lognormal(10, 1, n_samples)
    }, index=dates)
    
    # Ensure OHLC consistency
    df['high'] = np.maximum.reduce([df['open'], df['high'], df['low'], df['close']])
    df['low'] = np.minimum.reduce([df['open'], df['high'], df['low'], df['close']])
    
    print("🎯 INTEGRATED TIME SERIES CV TRADING SYSTEM DEMO")
    print("=" * 60)
    print(f"📊 Generated {len(df)} samples of cryptocurrency data")
    print(f"📅 Date range: {df.index[0]} to {df.index[-1]}")
    print(f"💰 Price range: ${df['close'].min():.2f} to ${df['close'].max():.2f}")
    
    # Initialize and run system
    system = TimeSeriesCVTradingSystem()
    results = system.train_and_validate(df)
    
    return results

def main():
    """Main demonstration"""
    
    print("🚨 REPLACING NAIVE TRAIN_TEST_SPLIT WITH PROPER TIME SERIES CV")
    print("=" * 70)
    
    # Run demonstration
    results = demonstrate_integrated_system()
    
    print(f"\n🎯 CRITICAL IMPROVEMENTS OVER NAIVE APPROACH:")
    print("=" * 55)
    print("✅ Walk-Forward Validation: Simulates real trading retraining")
    print("✅ No Look-Ahead Bias: Never uses future data for training")
    print("✅ Multiple Models Tested: Comprehensive model comparison")
    print("✅ Stability Analysis: Performance variance across time")
    print("✅ Realistic Estimates: Performance closer to real trading")
    print("✅ Temporal Dependencies: Preserves time series structure")
    print("✅ Gap Implementation: Prevents data leakage")
    print("✅ Comprehensive Metrics: Beyond just R² score")
    
    print(f"\n⚠️ WHY NAIVE TRAIN_TEST_SPLIT FAILS:")
    print("=" * 40)
    print("❌ Look-Ahead Bias: Uses future to predict past")
    print("❌ Overly Optimistic: Unrealistic performance estimates")
    print("❌ Data Leakage: Information contamination")
    print("❌ Ignores Time Structure: Breaks temporal dependencies")
    print("❌ Single Split: No stability assessment")
    print("❌ Poor Generalization: Doesn't reflect real conditions")
    
    print(f"\n✅ SYSTEM SUCCESSFULLY UPGRADED!")
    print("Time series cross-validation is now the foundation!")

if __name__ == "__main__":
    main() 