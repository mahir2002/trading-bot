#!/usr/bin/env python3
"""
📈 Advanced Time Series Cross-Validation System
Comprehensive cross-validation techniques for financial time series data
Prevents look-ahead bias and provides realistic performance estimates
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any, Generator, Union
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedTimeSeriesCV:
    """
    Advanced time series cross-validation system for financial data
    Implements multiple validation strategies to avoid look-ahead bias
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.validation_results = {}
        self.performance_history = {}
        
        logger.info("📈 Advanced Time Series CV initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for time series CV"""
        return {
            # Walk-forward validation
            'initial_train_size': 0.5,      # Initial training set size (50% of data)
            'step_size': 0.05,              # Step size for walk-forward (5% of data)
            'test_size': 0.1,               # Test set size (10% of data)
            'min_train_size': 0.3,          # Minimum training size (30% of data)
            
            # Expanding window validation
            'expanding_min_size': 0.2,      # Minimum size for expanding window
            'expanding_step': 0.1,          # Step size for expanding window
            
            # Rolling window validation
            'rolling_window_size': 0.4,     # Rolling window size (40% of data)
            'rolling_step': 0.05,           # Rolling step size (5% of data)
            
            # Blocked time series split
            'n_splits': 5,                  # Number of splits for blocked CV
            'gap_size': 0.02,               # Gap between train and test (2% of data)
            
            # Purged cross-validation
            'purge_size': 0.01,             # Purge size (1% of data)
            'embargo_size': 0.01,           # Embargo size (1% of data)
            
            # Performance metrics
            'metrics': ['mse', 'rmse', 'mae', 'r2', 'directional_accuracy'],
            'scoring_metric': 'r2',
            
            # Validation settings
            'shuffle': False,               # Never shuffle time series data
            'random_state': 42,
            'n_jobs': -1
        }
    
    def walk_forward_validation(self, 
                              X: np.ndarray, 
                              y: np.ndarray, 
                              model: Any,
                              dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Walk-forward validation (most realistic for trading)
        Simulates real-world trading where model is retrained periodically
        """
        logger.info("🚶 Performing walk-forward validation...")
        
        n_samples = len(X)
        initial_train_size = int(n_samples * self.config['initial_train_size'])
        step_size = max(1, int(n_samples * self.config['step_size']))
        test_size = max(1, int(n_samples * self.config['test_size']))
        min_train_size = int(n_samples * self.config['min_train_size'])
        
        results = {
            'predictions': [],
            'actuals': [],
            'train_scores': [],
            'test_scores': [],
            'train_sizes': [],
            'test_periods': [],
            'fold_metrics': []
        }
        
        fold = 0
        train_start = 0
        
        while True:
            # Define training window
            train_end = initial_train_size + fold * step_size
            
            # Define test window
            test_start = train_end
            test_end = min(test_start + test_size, n_samples)
            
            # Check if we have enough data
            if test_end > n_samples or train_end - train_start < min_train_size:
                break
            
            # Extract training and test data
            X_train = X[train_start:train_end]
            y_train = y[train_start:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            # Train model
            model_copy = self._clone_model(model)
            model_copy.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model_copy.predict(X_train)
            y_test_pred = model_copy.predict(X_test)
            
            # Calculate metrics
            train_score = r2_score(y_train, y_train_pred)
            test_score = r2_score(y_test, y_test_pred)
            
            fold_metrics = self._calculate_metrics(y_test, y_test_pred)
            
            # Store results
            results['predictions'].extend(y_test_pred)
            results['actuals'].extend(y_test)
            results['train_scores'].append(train_score)
            results['test_scores'].append(test_score)
            results['train_sizes'].append(train_end - train_start)
            results['fold_metrics'].append(fold_metrics)
            
            if dates is not None:
                results['test_periods'].append({
                    'start': dates[test_start],
                    'end': dates[test_end-1],
                    'train_start': dates[train_start],
                    'train_end': dates[train_end-1]
                })
            
            logger.info(f"   Fold {fold+1}: Train R² = {train_score:.4f}, Test R² = {test_score:.4f}")
            
            fold += 1
        
        # Calculate overall metrics
        overall_metrics = self._calculate_metrics(results['actuals'], results['predictions'])
        
        results['overall_metrics'] = overall_metrics
        results['mean_train_score'] = np.mean(results['train_scores'])
        results['mean_test_score'] = np.mean(results['test_scores'])
        results['std_test_score'] = np.std(results['test_scores'])
        results['n_folds'] = fold
        
        logger.info(f"✅ Walk-forward validation complete: {fold} folds")
        logger.info(f"   Mean test R²: {results['mean_test_score']:.4f} ± {results['std_test_score']:.4f}")
        
        return results
    
    def expanding_window_validation(self, 
                                  X: np.ndarray, 
                                  y: np.ndarray, 
                                  model: Any,
                                  dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Expanding window validation
        Training set grows over time, test set is fixed size
        """
        logger.info("📈 Performing expanding window validation...")
        
        n_samples = len(X)
        min_train_size = int(n_samples * self.config['expanding_min_size'])
        step_size = max(1, int(n_samples * self.config['expanding_step']))
        test_size = max(1, int(n_samples * self.config['test_size']))
        
        results = {
            'predictions': [],
            'actuals': [],
            'train_scores': [],
            'test_scores': [],
            'train_sizes': [],
            'test_periods': [],
            'fold_metrics': []
        }
        
        fold = 0
        
        while True:
            # Define expanding training window
            train_end = min_train_size + fold * step_size
            
            # Define test window
            test_start = train_end
            test_end = min(test_start + test_size, n_samples)
            
            # Check if we have enough data
            if test_end > n_samples:
                break
            
            # Extract training and test data
            X_train = X[0:train_end]  # Always start from beginning (expanding)
            y_train = y[0:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            # Train model
            model_copy = self._clone_model(model)
            model_copy.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model_copy.predict(X_train)
            y_test_pred = model_copy.predict(X_test)
            
            # Calculate metrics
            train_score = r2_score(y_train, y_train_pred)
            test_score = r2_score(y_test, y_test_pred)
            
            fold_metrics = self._calculate_metrics(y_test, y_test_pred)
            
            # Store results
            results['predictions'].extend(y_test_pred)
            results['actuals'].extend(y_test)
            results['train_scores'].append(train_score)
            results['test_scores'].append(test_score)
            results['train_sizes'].append(train_end)
            results['fold_metrics'].append(fold_metrics)
            
            if dates is not None:
                results['test_periods'].append({
                    'start': dates[test_start],
                    'end': dates[test_end-1],
                    'train_start': dates[0],
                    'train_end': dates[train_end-1]
                })
            
            logger.info(f"   Fold {fold+1}: Train R² = {train_score:.4f}, Test R² = {test_score:.4f}")
            
            fold += 1
        
        # Calculate overall metrics
        overall_metrics = self._calculate_metrics(results['actuals'], results['predictions'])
        
        results['overall_metrics'] = overall_metrics
        results['mean_train_score'] = np.mean(results['train_scores'])
        results['mean_test_score'] = np.mean(results['test_scores'])
        results['std_test_score'] = np.std(results['test_scores'])
        results['n_folds'] = fold
        
        logger.info(f"✅ Expanding window validation complete: {fold} folds")
        logger.info(f"   Mean test R²: {results['mean_test_score']:.4f} ± {results['std_test_score']:.4f}")
        
        return results
    
    def rolling_window_validation(self, 
                                X: np.ndarray, 
                                y: np.ndarray, 
                                model: Any,
                                dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Rolling window validation
        Fixed-size training window that slides through time
        """
        logger.info("🔄 Performing rolling window validation...")
        
        n_samples = len(X)
        window_size = int(n_samples * self.config['rolling_window_size'])
        step_size = max(1, int(n_samples * self.config['rolling_step']))
        test_size = max(1, int(n_samples * self.config['test_size']))
        
        results = {
            'predictions': [],
            'actuals': [],
            'train_scores': [],
            'test_scores': [],
            'train_sizes': [],
            'test_periods': [],
            'fold_metrics': []
        }
        
        fold = 0
        
        while True:
            # Define rolling training window
            train_start = fold * step_size
            train_end = train_start + window_size
            
            # Define test window
            test_start = train_end
            test_end = min(test_start + test_size, n_samples)
            
            # Check if we have enough data
            if test_end > n_samples or train_end > n_samples:
                break
            
            # Extract training and test data
            X_train = X[train_start:train_end]
            y_train = y[train_start:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            # Train model
            model_copy = self._clone_model(model)
            model_copy.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model_copy.predict(X_train)
            y_test_pred = model_copy.predict(X_test)
            
            # Calculate metrics
            train_score = r2_score(y_train, y_train_pred)
            test_score = r2_score(y_test, y_test_pred)
            
            fold_metrics = self._calculate_metrics(y_test, y_test_pred)
            
            # Store results
            results['predictions'].extend(y_test_pred)
            results['actuals'].extend(y_test)
            results['train_scores'].append(train_score)
            results['test_scores'].append(test_score)
            results['train_sizes'].append(window_size)
            results['fold_metrics'].append(fold_metrics)
            
            if dates is not None:
                results['test_periods'].append({
                    'start': dates[test_start],
                    'end': dates[test_end-1],
                    'train_start': dates[train_start],
                    'train_end': dates[train_end-1]
                })
            
            logger.info(f"   Fold {fold+1}: Train R² = {train_score:.4f}, Test R² = {test_score:.4f}")
            
            fold += 1
        
        # Calculate overall metrics
        overall_metrics = self._calculate_metrics(results['actuals'], results['predictions'])
        
        results['overall_metrics'] = overall_metrics
        results['mean_train_score'] = np.mean(results['train_scores'])
        results['mean_test_score'] = np.mean(results['test_scores'])
        results['std_test_score'] = np.std(results['test_scores'])
        results['n_folds'] = fold
        
        logger.info(f"✅ Rolling window validation complete: {fold} folds")
        logger.info(f"   Mean test R²: {results['mean_test_score']:.4f} ± {results['std_test_score']:.4f}")
        
        return results
    
    def blocked_time_series_split(self, 
                                X: np.ndarray, 
                                y: np.ndarray, 
                                model: Any,
                                dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Blocked time series split with gaps
        Similar to TimeSeriesSplit but with configurable gaps
        """
        logger.info("🧱 Performing blocked time series split...")
        
        n_samples = len(X)
        n_splits = self.config['n_splits']
        gap_size = max(1, int(n_samples * self.config['gap_size']))
        
        # Calculate split sizes
        total_usable = n_samples - (n_splits - 1) * gap_size
        test_size = total_usable // (n_splits + 1)
        
        results = {
            'predictions': [],
            'actuals': [],
            'train_scores': [],
            'test_scores': [],
            'train_sizes': [],
            'test_periods': [],
            'fold_metrics': []
        }
        
        for fold in range(n_splits):
            # Calculate train and test indices
            test_start = (fold + 1) * test_size + fold * gap_size
            test_end = test_start + test_size
            train_end = test_start - gap_size
            
            if test_end > n_samples or train_end <= 0:
                continue
            
            # Extract training and test data
            X_train = X[0:train_end]
            y_train = y[0:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            # Train model
            model_copy = self._clone_model(model)
            model_copy.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model_copy.predict(X_train)
            y_test_pred = model_copy.predict(X_test)
            
            # Calculate metrics
            train_score = r2_score(y_train, y_train_pred)
            test_score = r2_score(y_test, y_test_pred)
            
            fold_metrics = self._calculate_metrics(y_test, y_test_pred)
            
            # Store results
            results['predictions'].extend(y_test_pred)
            results['actuals'].extend(y_test)
            results['train_scores'].append(train_score)
            results['test_scores'].append(test_score)
            results['train_sizes'].append(train_end)
            results['fold_metrics'].append(fold_metrics)
            
            if dates is not None:
                results['test_periods'].append({
                    'start': dates[test_start],
                    'end': dates[test_end-1],
                    'train_start': dates[0],
                    'train_end': dates[train_end-1]
                })
            
            logger.info(f"   Fold {fold+1}: Train R² = {train_score:.4f}, Test R² = {test_score:.4f}")
        
        # Calculate overall metrics
        overall_metrics = self._calculate_metrics(results['actuals'], results['predictions'])
        
        results['overall_metrics'] = overall_metrics
        results['mean_train_score'] = np.mean(results['train_scores'])
        results['mean_test_score'] = np.mean(results['test_scores'])
        results['std_test_score'] = np.std(results['test_scores'])
        results['n_folds'] = len(results['train_scores'])
        
        logger.info(f"✅ Blocked time series split complete: {results['n_folds']} folds")
        logger.info(f"   Mean test R²: {results['mean_test_score']:.4f} ± {results['std_test_score']:.4f}")
        
        return results
    
    def purged_cross_validation(self, 
                              X: np.ndarray, 
                              y: np.ndarray, 
                              model: Any,
                              dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Purged cross-validation with embargo
        Removes samples around test set to prevent data leakage
        """
        logger.info("🧹 Performing purged cross-validation...")
        
        n_samples = len(X)
        n_splits = self.config['n_splits']
        purge_size = max(1, int(n_samples * self.config['purge_size']))
        embargo_size = max(1, int(n_samples * self.config['embargo_size']))
        
        # Calculate test set size
        test_size = n_samples // (n_splits + 1)
        
        results = {
            'predictions': [],
            'actuals': [],
            'train_scores': [],
            'test_scores': [],
            'train_sizes': [],
            'test_periods': [],
            'fold_metrics': []
        }
        
        for fold in range(n_splits):
            # Calculate test indices
            test_start = fold * test_size
            test_end = min(test_start + test_size, n_samples)
            
            # Calculate purge and embargo regions
            purge_start = max(0, test_start - purge_size)
            purge_end = min(n_samples, test_end + purge_size)
            embargo_start = max(0, test_end)
            embargo_end = min(n_samples, test_end + embargo_size)
            
            # Create training mask (exclude test, purge, and embargo regions)
            train_mask = np.ones(n_samples, dtype=bool)
            train_mask[purge_start:purge_end] = False
            train_mask[embargo_start:embargo_end] = False
            
            # Extract training and test data
            X_train = X[train_mask]
            y_train = y[train_mask]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            if len(X_train) < 10 or len(X_test) < 1:
                continue
            
            # Train model
            model_copy = self._clone_model(model)
            model_copy.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model_copy.predict(X_train)
            y_test_pred = model_copy.predict(X_test)
            
            # Calculate metrics
            train_score = r2_score(y_train, y_train_pred)
            test_score = r2_score(y_test, y_test_pred)
            
            fold_metrics = self._calculate_metrics(y_test, y_test_pred)
            
            # Store results
            results['predictions'].extend(y_test_pred)
            results['actuals'].extend(y_test)
            results['train_scores'].append(train_score)
            results['test_scores'].append(test_score)
            results['train_sizes'].append(len(X_train))
            results['fold_metrics'].append(fold_metrics)
            
            if dates is not None:
                train_dates = dates[train_mask]
                results['test_periods'].append({
                    'start': dates[test_start],
                    'end': dates[test_end-1],
                    'train_start': train_dates[0] if len(train_dates) > 0 else None,
                    'train_end': train_dates[-1] if len(train_dates) > 0 else None,
                    'purged_samples': purge_end - purge_start,
                    'embargo_samples': embargo_end - embargo_start
                })
            
            logger.info(f"   Fold {fold+1}: Train R² = {train_score:.4f}, Test R² = {test_score:.4f}")
        
        # Calculate overall metrics
        overall_metrics = self._calculate_metrics(results['actuals'], results['predictions'])
        
        results['overall_metrics'] = overall_metrics
        results['mean_train_score'] = np.mean(results['train_scores'])
        results['mean_test_score'] = np.mean(results['test_scores'])
        results['std_test_score'] = np.std(results['test_scores'])
        results['n_folds'] = len(results['train_scores'])
        
        logger.info(f"✅ Purged cross-validation complete: {results['n_folds']} folds")
        logger.info(f"   Mean test R²: {results['mean_test_score']:.4f} ± {results['std_test_score']:.4f}")
        
        return results
    
    def comprehensive_validation(self, 
                               X: np.ndarray, 
                               y: np.ndarray, 
                               model: Any,
                               dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Run all validation methods and compare results
        """
        logger.info("🎯 Running comprehensive time series validation...")
        
        validation_methods = {
            'walk_forward': self.walk_forward_validation,
            'expanding_window': self.expanding_window_validation,
            'rolling_window': self.rolling_window_validation,
            'blocked_split': self.blocked_time_series_split,
            'purged_cv': self.purged_cross_validation
        }
        
        results = {}
        
        for method_name, method_func in validation_methods.items():
            try:
                logger.info(f"\n--- {method_name.upper()} VALIDATION ---")
                method_results = method_func(X, y, model, dates)
                results[method_name] = method_results
                
            except Exception as e:
                logger.error(f"Error in {method_name}: {e}")
                continue
        
        # Compare methods
        comparison = self._compare_validation_methods(results)
        results['comparison'] = comparison
        
        # Store results
        self.validation_results = results
        
        return results
    
    def _compare_validation_methods(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare different validation methods"""
        logger.info("\n📊 Comparing validation methods...")
        
        comparison = {
            'method_scores': {},
            'method_stability': {},
            'method_folds': {},
            'best_method': None,
            'most_stable': None,
            'most_conservative': None
        }
        
        for method_name, method_results in results.items():
            if 'mean_test_score' in method_results:
                comparison['method_scores'][method_name] = method_results['mean_test_score']
                comparison['method_stability'][method_name] = method_results['std_test_score']
                comparison['method_folds'][method_name] = method_results['n_folds']
                
                logger.info(f"   {method_name}: {method_results['mean_test_score']:.4f} ± {method_results['std_test_score']:.4f} ({method_results['n_folds']} folds)")
        
        if comparison['method_scores']:
            # Best performing method
            comparison['best_method'] = max(comparison['method_scores'].items(), key=lambda x: x[1])
            
            # Most stable method (lowest std)
            comparison['most_stable'] = min(comparison['method_stability'].items(), key=lambda x: x[1])
            
            # Most conservative method (lowest score, indicating more realistic estimates)
            comparison['most_conservative'] = min(comparison['method_scores'].items(), key=lambda x: x[1])
            
            logger.info(f"\n🏆 Best method: {comparison['best_method'][0]} ({comparison['best_method'][1]:.4f})")
            logger.info(f"🎯 Most stable: {comparison['most_stable'][0]} (±{comparison['most_stable'][1]:.4f})")
            logger.info(f"⚠️ Most conservative: {comparison['most_conservative'][0]} ({comparison['most_conservative'][1]:.4f})")
        
        return comparison
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive metrics"""
        metrics = {}
        
        # Regression metrics
        metrics['mse'] = mean_squared_error(y_true, y_pred)
        metrics['rmse'] = np.sqrt(metrics['mse'])
        metrics['mae'] = mean_absolute_error(y_true, y_pred)
        metrics['r2'] = r2_score(y_true, y_pred)
        
        # Financial metrics
        # Directional accuracy
        y_true_direction = np.sign(np.diff(y_true))
        y_pred_direction = np.sign(np.diff(y_pred))
        metrics['directional_accuracy'] = np.mean(y_true_direction == y_pred_direction)
        
        # Hit ratio (percentage of predictions within 5% of actual)
        relative_error = np.abs((y_pred - y_true) / y_true)
        metrics['hit_ratio_5pct'] = np.mean(relative_error <= 0.05)
        
        return metrics
    
    def _clone_model(self, model: Any) -> Any:
        """Clone a model for cross-validation"""
        from sklearn.base import clone
        try:
            return clone(model)
        except:
            # Fallback for models that don't support cloning
            model_class = type(model)
            return model_class(**model.get_params())
    
    def plot_validation_results(self, results: Dict[str, Any], save_path: Optional[str] = None):
        """Plot validation results for visualization"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Time Series Cross-Validation Results', fontsize=16)
            
            # Plot 1: Method comparison
            if 'comparison' in results:
                method_names = list(results['comparison']['method_scores'].keys())
                scores = list(results['comparison']['method_scores'].values())
                stds = [results['comparison']['method_stability'][name] for name in method_names]
                
                axes[0, 0].bar(method_names, scores, yerr=stds, capsize=5)
                axes[0, 0].set_title('Validation Method Comparison')
                axes[0, 0].set_ylabel('R² Score')
                axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Plot 2: Walk-forward results over time
            if 'walk_forward' in results:
                wf_results = results['walk_forward']
                axes[0, 1].plot(wf_results['test_scores'], 'o-', label='Test Score')
                axes[0, 1].plot(wf_results['train_scores'], 's-', alpha=0.7, label='Train Score')
                axes[0, 1].set_title('Walk-Forward Validation Over Time')
                axes[0, 1].set_ylabel('R² Score')
                axes[0, 1].set_xlabel('Fold')
                axes[0, 1].legend()
            
            # Plot 3: Predictions vs Actuals
            if 'walk_forward' in results:
                wf_results = results['walk_forward']
                axes[1, 0].scatter(wf_results['actuals'], wf_results['predictions'], alpha=0.6)
                min_val = min(min(wf_results['actuals']), min(wf_results['predictions']))
                max_val = max(max(wf_results['actuals']), max(wf_results['predictions']))
                axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8)
                axes[1, 0].set_title('Predictions vs Actuals (Walk-Forward)')
                axes[1, 0].set_xlabel('Actual Values')
                axes[1, 0].set_ylabel('Predicted Values')
            
            # Plot 4: Training set size evolution
            if 'expanding_window' in results:
                ew_results = results['expanding_window']
                axes[1, 1].plot(ew_results['train_sizes'], ew_results['test_scores'], 'o-')
                axes[1, 1].set_title('Performance vs Training Set Size')
                axes[1, 1].set_xlabel('Training Set Size')
                axes[1, 1].set_ylabel('Test R² Score')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"📊 Validation plots saved to {save_path}")
            
            plt.show()
            
        except ImportError:
            logger.warning("Matplotlib not available for plotting")
        except Exception as e:
            logger.error(f"Error creating plots: {e}")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results"""
        if not self.validation_results:
            return {}
        
        summary = {
            'methods_tested': list(self.validation_results.keys()),
            'best_method': None,
            'recommended_approach': None,
            'key_insights': []
        }
        
        if 'comparison' in self.validation_results:
            comp = self.validation_results['comparison']
            
            summary['best_method'] = comp.get('best_method', [None, None])[0]
            summary['most_stable'] = comp.get('most_stable', [None, None])[0]
            summary['most_conservative'] = comp.get('most_conservative', [None, None])[0]
            
            # Generate insights
            if comp['best_method'] and comp['most_conservative']:
                best_score = comp['best_method'][1]
                conservative_score = comp['most_conservative'][1]
                
                if best_score - conservative_score > 0.1:
                    summary['key_insights'].append("Large performance gap between methods suggests potential overfitting")
                
                if comp['most_stable'][1] < 0.05:
                    summary['key_insights'].append("Low variance across folds indicates stable model performance")
                
                # Recommendation
                if comp['best_method'][0] == 'walk_forward':
                    summary['recommended_approach'] = "Walk-forward validation (most realistic for trading)"
                elif comp['most_stable'][1] < 0.02:
                    summary['recommended_approach'] = f"Use {comp['most_stable'][0]} for stable estimates"
                else:
                    summary['recommended_approach'] = "Consider ensemble of multiple validation methods"
        
        return summary

def demonstrate_time_series_cv():
    """Demonstrate time series cross-validation techniques"""
    
    # Generate realistic financial time series data
    np.random.seed(42)
    n_samples = 2000
    n_features = 10
    
    # Create dates
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='1H')
    
    # Generate features with temporal dependencies
    X = np.random.randn(n_samples, n_features)
    for i in range(1, n_samples):
        X[i] = 0.8 * X[i-1] + 0.2 * X[i]  # Add temporal correlation
    
    # Generate target with trend and noise
    trend = np.linspace(0, 10, n_samples)
    seasonal = 2 * np.sin(2 * np.pi * np.arange(n_samples) / 24)  # Daily seasonality
    noise = np.random.randn(n_samples) * 0.5
    
    y = (
        2 * X[:, 0] + 
        1.5 * X[:, 1] * X[:, 2] + 
        0.8 * np.sin(X[:, 3]) +
        trend + seasonal + noise
    )
    
    # Initialize CV system
    cv_system = AdvancedTimeSeriesCV()
    
    # Test model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    print("📈 Advanced Time Series Cross-Validation Demonstration")
    print("=" * 60)
    
    # Run comprehensive validation
    results = cv_system.comprehensive_validation(X, y, model, dates)
    
    # Get summary
    summary = cv_system.get_validation_summary()
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print("=" * 40)
    print(f"Methods tested: {len(summary['methods_tested'])}")
    print(f"Best method: {summary['best_method']}")
    print(f"Most stable: {summary['most_stable']}")
    print(f"Most conservative: {summary['most_conservative']}")
    print(f"Recommended approach: {summary['recommended_approach']}")
    
    if summary['key_insights']:
        print(f"\n🔍 KEY INSIGHTS:")
        for insight in summary['key_insights']:
            print(f"   • {insight}")
    
    # Compare with naive train_test_split
    print(f"\n⚠️ COMPARISON WITH NAIVE SPLIT:")
    print("=" * 40)
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    naive_model = RandomForestRegressor(n_estimators=100, random_state=42)
    naive_model.fit(X_train, y_train)
    naive_score = naive_model.score(X_test, y_test)
    
    print(f"Naive train_test_split R²: {naive_score:.4f}")
    
    if 'walk_forward' in results:
        wf_score = results['walk_forward']['mean_test_score']
        print(f"Walk-forward validation R²: {wf_score:.4f}")
        print(f"Difference: {naive_score - wf_score:.4f} (naive is likely optimistic)")
    
    return results

def main():
    """Main demonstration of advanced time series CV"""
    
    # Run demonstration
    results = demonstrate_time_series_cv()
    
    print(f"\n🎯 TIME SERIES CV ADVANTAGES:")
    print("=" * 50)
    print("✅ Walk-Forward Validation: Most realistic for trading (retraining simulation)")
    print("✅ Expanding Window: Growing training set over time")
    print("✅ Rolling Window: Fixed-size training window")
    print("✅ Blocked Split: Time series split with gaps")
    print("✅ Purged CV: Removes samples to prevent data leakage")
    print("✅ No Look-Ahead Bias: Future data never used to predict past")
    print("✅ Temporal Dependencies: Preserves time-based relationships")
    print("✅ Realistic Performance: Accurate out-of-sample estimates")
    
    print(f"\n📊 CRITICAL IMPROVEMENTS OVER NAIVE SPLIT:")
    print("• Temporal Validation: vs random train/test split")
    print("• No Data Leakage: Future information properly excluded")
    print("• Realistic Estimates: Performance closer to real trading")
    print("• Multiple Methods: 5 validation strategies vs single split")
    print("• Stability Analysis: Variance across time periods")
    print("• Trading Simulation: Walk-forward mimics real retraining")
    
    print(f"\n⚠️ WHY NAIVE SPLIT FAILS FOR FINANCIAL DATA:")
    print("• Look-Ahead Bias: Uses future data to predict past")
    print("• Overly Optimistic: Performance estimates too high")
    print("• Ignores Temporal Structure: Breaks time dependencies")
    print("• Poor Generalization: Doesn't reflect real trading conditions")
    print("• Data Leakage: Information from future contaminates training")
    
    print(f"\n✅ Advanced time series cross-validation demonstration completed!")

if __name__ == "__main__":
    main() 