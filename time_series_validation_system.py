#!/usr/bin/env python3
"""
Time-Series Cross-Validation and Feature Selection System
Proper validation techniques for financial time series without look-ahead bias
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Machine Learning Libraries
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.feature_selection import RFE, SelectFromModel, VarianceThreshold
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Statistical Libraries
import scipy.stats as stats
from scipy.stats import spearmanr, pearsonr
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
from itertools import combinations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationMethod(Enum):
    """Time-series validation methods."""
    WALK_FORWARD = "walk_forward"
    EXPANDING_WINDOW = "expanding_window"
    SLIDING_WINDOW = "sliding_window"
    PURGED_CROSS_VALIDATION = "purged_cv"
    BLOCKED_TIME_SERIES = "blocked_ts"

class FeatureSelectionMethod(Enum):
    """Feature selection methods."""
    CORRELATION_FILTER = "correlation_filter"
    MUTUAL_INFORMATION = "mutual_information"
    RECURSIVE_ELIMINATION = "recursive_elimination"
    L1_REGULARIZATION = "l1_regularization"
    TREE_IMPORTANCE = "tree_importance"
    STATISTICAL_TESTS = "statistical_tests"
    VARIANCE_THRESHOLD = "variance_threshold"
    PCA_REDUCTION = "pca_reduction"

@dataclass
class ValidationResult:
    """Results from time-series cross-validation."""
    method: ValidationMethod
    n_splits: int
    scores: List[float]
    mean_score: float
    std_score: float
    train_sizes: List[int]
    test_sizes: List[int]
    feature_importance: Dict[str, float]
    prediction_intervals: List[Tuple[float, float]]
    residual_analysis: Dict[str, Any]

@dataclass
class FeatureSelectionResult:
    """Results from feature selection process."""
    method: FeatureSelectionMethod
    selected_features: List[str]
    feature_scores: Dict[str, float]
    n_features_selected: int
    correlation_matrix: pd.DataFrame
    redundancy_analysis: Dict[str, Any]
    performance_improvement: float

class TimeSeriesValidator:
    """Advanced time-series cross-validation system."""
    
    def __init__(self, 
                 min_train_size: int = 252,  # 1 year of daily data
                 test_size: int = 63,        # 3 months of daily data
                 step_size: int = 21,        # 1 month step
                 purge_size: int = 5,        # 1 week purge
                 embargo_size: int = 2):     # 2 days embargo
        
        self.min_train_size = min_train_size
        self.test_size = test_size
        self.step_size = step_size
        self.purge_size = purge_size
        self.embargo_size = embargo_size
        
        # Validation results storage
        self.validation_results = {}
        self.feature_selection_results = {}
        
        print("📊 Time-Series Cross-Validation System Initialized")
        print(f"   Minimum Training Size: {min_train_size} periods")
        print(f"   Test Size: {test_size} periods")
        print(f"   Step Size: {step_size} periods")
        print(f"   Purge Size: {purge_size} periods")
        print(f"   Embargo Size: {embargo_size} periods")
    
    def walk_forward_validation(self, 
                              X: pd.DataFrame, 
                              y: pd.Series, 
                              model: Any,
                              n_splits: int = None) -> ValidationResult:
        """Implement walk-forward optimization validation."""
        
        print(f"🚶 Performing Walk-Forward Validation...")
        
        if n_splits is None:
            # Calculate maximum number of splits
            n_splits = (len(X) - self.min_train_size - self.test_size) // self.step_size + 1
        
        scores = []
        train_sizes = []
        test_sizes = []
        feature_importance_list = []
        predictions = []
        actuals = []
        
        for i in range(n_splits):
            # Calculate split indices
            train_start = 0
            train_end = self.min_train_size + i * self.step_size
            test_start = train_end + self.purge_size  # Add purge period
            test_end = min(test_start + self.test_size, len(X))
            
            if test_end <= test_start:
                break
            
            # Extract training and test sets
            X_train = X.iloc[train_start:train_end]
            y_train = y.iloc[train_start:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate score
            if hasattr(model, 'predict_proba'):  # Classification
                score = accuracy_score(y_test, y_pred)
            else:  # Regression
                score = r2_score(y_test, y_pred)
            
            scores.append(score)
            train_sizes.append(len(X_train))
            test_sizes.append(len(X_test))
            
            # Store predictions for analysis
            predictions.extend(y_pred)
            actuals.extend(y_test.values)
            
            # Feature importance (if available)
            if hasattr(model, 'feature_importances_'):
                importance = dict(zip(X.columns, model.feature_importances_))
                feature_importance_list.append(importance)
            
            print(f"   Split {i+1}/{n_splits}: Score = {score:.4f}, Train = {len(X_train)}, Test = {len(X_test)}")
        
        # Aggregate feature importance
        if feature_importance_list:
            feature_importance = {}
            for feature in X.columns:
                feature_importance[feature] = np.mean([imp.get(feature, 0) for imp in feature_importance_list])
        else:
            feature_importance = {}
        
        # Residual analysis
        residuals = np.array(actuals) - np.array(predictions)
        residual_analysis = self._analyze_residuals(residuals)
        
        # Prediction intervals (simplified)
        prediction_intervals = [(pred - 1.96 * np.std(residuals), pred + 1.96 * np.std(residuals)) 
                              for pred in predictions]
        
        result = ValidationResult(
            method=ValidationMethod.WALK_FORWARD,
            n_splits=len(scores),
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            train_sizes=train_sizes,
            test_sizes=test_sizes,
            feature_importance=feature_importance,
            prediction_intervals=prediction_intervals,
            residual_analysis=residual_analysis
        )
        
        print(f"   ✅ Walk-Forward Validation Complete: {result.mean_score:.4f} ± {result.std_score:.4f}")
        return result
    
    def expanding_window_validation(self, 
                                  X: pd.DataFrame, 
                                  y: pd.Series, 
                                  model: Any,
                                  n_splits: int = None) -> ValidationResult:
        """Implement expanding window validation."""
        
        print(f"📈 Performing Expanding Window Validation...")
        
        if n_splits is None:
            n_splits = (len(X) - self.min_train_size - self.test_size) // self.step_size + 1
        
        scores = []
        train_sizes = []
        test_sizes = []
        feature_importance_list = []
        predictions = []
        actuals = []
        
        for i in range(n_splits):
            # Calculate split indices (expanding training window)
            train_start = 0
            train_end = self.min_train_size + i * self.step_size
            test_start = train_end + self.purge_size
            test_end = min(test_start + self.test_size, len(X))
            
            if test_end <= test_start:
                break
            
            # Extract training and test sets
            X_train = X.iloc[train_start:train_end]
            y_train = y.iloc[train_start:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate score
            if hasattr(model, 'predict_proba'):  # Classification
                score = accuracy_score(y_test, y_pred)
            else:  # Regression
                score = r2_score(y_test, y_pred)
            
            scores.append(score)
            train_sizes.append(len(X_train))
            test_sizes.append(len(X_test))
            
            # Store predictions
            predictions.extend(y_pred)
            actuals.extend(y_test.values)
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                importance = dict(zip(X.columns, model.feature_importances_))
                feature_importance_list.append(importance)
        
        # Aggregate results
        if feature_importance_list:
            feature_importance = {}
            for feature in X.columns:
                feature_importance[feature] = np.mean([imp.get(feature, 0) for imp in feature_importance_list])
        else:
            feature_importance = {}
        
        residuals = np.array(actuals) - np.array(predictions)
        residual_analysis = self._analyze_residuals(residuals)
        prediction_intervals = [(pred - 1.96 * np.std(residuals), pred + 1.96 * np.std(residuals)) 
                              for pred in predictions]
        
        result = ValidationResult(
            method=ValidationMethod.EXPANDING_WINDOW,
            n_splits=len(scores),
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            train_sizes=train_sizes,
            test_sizes=test_sizes,
            feature_importance=feature_importance,
            prediction_intervals=prediction_intervals,
            residual_analysis=residual_analysis
        )
        
        print(f"   ✅ Expanding Window Validation Complete: {result.mean_score:.4f} ± {result.std_score:.4f}")
        return result
    
    def sliding_window_validation(self, 
                                X: pd.DataFrame, 
                                y: pd.Series, 
                                model: Any,
                                window_size: int = None,
                                n_splits: int = None) -> ValidationResult:
        """Implement sliding window validation."""
        
        print(f"🔄 Performing Sliding Window Validation...")
        
        if window_size is None:
            window_size = self.min_train_size
        
        if n_splits is None:
            n_splits = (len(X) - window_size - self.test_size) // self.step_size + 1
        
        scores = []
        train_sizes = []
        test_sizes = []
        feature_importance_list = []
        predictions = []
        actuals = []
        
        for i in range(n_splits):
            # Calculate split indices (sliding training window)
            train_start = i * self.step_size
            train_end = train_start + window_size
            test_start = train_end + self.purge_size
            test_end = min(test_start + self.test_size, len(X))
            
            if test_end <= test_start or train_end >= len(X):
                break
            
            # Extract training and test sets
            X_train = X.iloc[train_start:train_end]
            y_train = y.iloc[train_start:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate score
            if hasattr(model, 'predict_proba'):  # Classification
                score = accuracy_score(y_test, y_pred)
            else:  # Regression
                score = r2_score(y_test, y_pred)
            
            scores.append(score)
            train_sizes.append(len(X_train))
            test_sizes.append(len(X_test))
            
            # Store predictions
            predictions.extend(y_pred)
            actuals.extend(y_test.values)
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                importance = dict(zip(X.columns, model.feature_importances_))
                feature_importance_list.append(importance)
        
        # Aggregate results
        if feature_importance_list:
            feature_importance = {}
            for feature in X.columns:
                feature_importance[feature] = np.mean([imp.get(feature, 0) for imp in feature_importance_list])
        else:
            feature_importance = {}
        
        residuals = np.array(actuals) - np.array(predictions)
        residual_analysis = self._analyze_residuals(residuals)
        prediction_intervals = [(pred - 1.96 * np.std(residuals), pred + 1.96 * np.std(residuals)) 
                              for pred in predictions]
        
        result = ValidationResult(
            method=ValidationMethod.SLIDING_WINDOW,
            n_splits=len(scores),
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            train_sizes=train_sizes,
            test_sizes=test_sizes,
            feature_importance=feature_importance,
            prediction_intervals=prediction_intervals,
            residual_analysis=residual_analysis
        )
        
        print(f"   ✅ Sliding Window Validation Complete: {result.mean_score:.4f} ± {result.std_score:.4f}")
        return result
    
    def purged_cross_validation(self, 
                              X: pd.DataFrame, 
                              y: pd.Series, 
                              model: Any,
                              n_splits: int = 5) -> ValidationResult:
        """Implement purged cross-validation to prevent leakage."""
        
        print(f"🧹 Performing Purged Cross-Validation...")
        
        total_size = len(X)
        fold_size = total_size // n_splits
        
        scores = []
        train_sizes = []
        test_sizes = []
        feature_importance_list = []
        predictions = []
        actuals = []
        
        for i in range(n_splits):
            # Calculate test fold indices
            test_start = i * fold_size
            test_end = min((i + 1) * fold_size, total_size)
            
            # Calculate purge boundaries
            purge_start = max(0, test_start - self.purge_size)
            purge_end = min(total_size, test_end + self.purge_size)
            
            # Create training indices (excluding test and purge periods)
            train_indices = list(range(0, purge_start)) + list(range(purge_end, total_size))
            test_indices = list(range(test_start, test_end))
            
            if len(train_indices) < self.min_train_size:
                continue
            
            # Extract training and test sets
            X_train = X.iloc[train_indices]
            y_train = y.iloc[train_indices]
            X_test = X.iloc[test_indices]
            y_test = y.iloc[test_indices]
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate score
            if hasattr(model, 'predict_proba'):  # Classification
                score = accuracy_score(y_test, y_pred)
            else:  # Regression
                score = r2_score(y_test, y_pred)
            
            scores.append(score)
            train_sizes.append(len(X_train))
            test_sizes.append(len(X_test))
            
            # Store predictions
            predictions.extend(y_pred)
            actuals.extend(y_test.values)
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                importance = dict(zip(X.columns, model.feature_importances_))
                feature_importance_list.append(importance)
        
        # Aggregate results
        if feature_importance_list:
            feature_importance = {}
            for feature in X.columns:
                feature_importance[feature] = np.mean([imp.get(feature, 0) for imp in feature_importance_list])
        else:
            feature_importance = {}
        
        residuals = np.array(actuals) - np.array(predictions)
        residual_analysis = self._analyze_residuals(residuals)
        prediction_intervals = [(pred - 1.96 * np.std(residuals), pred + 1.96 * np.std(residuals)) 
                              for pred in predictions]
        
        result = ValidationResult(
            method=ValidationMethod.PURGED_CROSS_VALIDATION,
            n_splits=len(scores),
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            train_sizes=train_sizes,
            test_sizes=test_sizes,
            feature_importance=feature_importance,
            prediction_intervals=prediction_intervals,
            residual_analysis=residual_analysis
        )
        
        print(f"   ✅ Purged Cross-Validation Complete: {result.mean_score:.4f} ± {result.std_score:.4f}")
        return result
    
    def _analyze_residuals(self, residuals: np.ndarray) -> Dict[str, Any]:
        """Analyze residuals for model diagnostics."""
        
        analysis = {}
        
        # Basic statistics
        analysis['mean'] = np.mean(residuals)
        analysis['std'] = np.std(residuals)
        analysis['skewness'] = stats.skew(residuals)
        analysis['kurtosis'] = stats.kurtosis(residuals)
        
        # Normality tests
        _, analysis['shapiro_p'] = stats.shapiro(residuals[:min(5000, len(residuals))])
        _, analysis['jarque_bera_p'] = stats.jarque_bera(residuals)
        
        # Autocorrelation test
        try:
            analysis['ljung_box_p'] = acorr_ljungbox(residuals, lags=10, return_df=True)['lb_pvalue'].iloc[-1]
        except:
            analysis['ljung_box_p'] = np.nan
        
        # Heteroscedasticity (simplified)
        analysis['heteroscedasticity'] = np.corrcoef(np.abs(residuals[1:]), np.abs(residuals[:-1]))[0, 1]
        
        return analysis
    
    def compare_validation_methods(self, 
                                 X: pd.DataFrame, 
                                 y: pd.Series, 
                                 model: Any) -> Dict[str, ValidationResult]:
        """Compare different validation methods."""
        
        print(f"\n🔍 Comparing Time-Series Validation Methods...")
        
        results = {}
        
        # Walk-forward validation
        results['walk_forward'] = self.walk_forward_validation(X, y, model)
        
        # Expanding window validation
        results['expanding_window'] = self.expanding_window_validation(X, y, model)
        
        # Sliding window validation
        results['sliding_window'] = self.sliding_window_validation(X, y, model)
        
        # Purged cross-validation
        results['purged_cv'] = self.purged_cross_validation(X, y, model)
        
        # Summary comparison
        print(f"\n📊 Validation Method Comparison:")
        print("-" * 70)
        for method, result in results.items():
            print(f"{method:<20}: {result.mean_score:.4f} ± {result.std_score:.4f} ({result.n_splits} splits)")
        
        self.validation_results = results
        return results

class FeatureSelector:
    """Advanced feature selection system for time-series data."""
    
    def __init__(self, 
                 correlation_threshold: float = 0.95,
                 variance_threshold: float = 0.01,
                 max_features: int = None):
        
        self.correlation_threshold = correlation_threshold
        self.variance_threshold = variance_threshold
        self.max_features = max_features
        
        # Results storage
        self.selection_results = {}
        self.correlation_matrix = None
        
        print("🎯 Feature Selection System Initialized")
        print(f"   Correlation Threshold: {correlation_threshold}")
        print(f"   Variance Threshold: {variance_threshold}")
        print(f"   Max Features: {max_features if max_features else 'No limit'}")
    
    def correlation_filter(self, 
                          X: pd.DataFrame, 
                          y: pd.Series = None) -> FeatureSelectionResult:
        """Remove highly correlated features."""
        
        print(f"🔗 Applying Correlation Filter...")
        
        # Calculate correlation matrix
        corr_matrix = X.corr().abs()
        self.correlation_matrix = corr_matrix
        
        # Find highly correlated pairs
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Identify features to remove
        to_remove = set()
        redundancy_pairs = []
        
        for col in upper_triangle.columns:
            for idx in upper_triangle.index:
                if upper_triangle.loc[idx, col] > self.correlation_threshold:
                    # Remove the feature with lower correlation to target (if available)
                    if y is not None:
                        corr_with_target_col = abs(y.corr(X[col]))
                        corr_with_target_idx = abs(y.corr(X[idx]))
                        
                        if corr_with_target_col < corr_with_target_idx:
                            to_remove.add(col)
                        else:
                            to_remove.add(idx)
                    else:
                        # Remove the second feature by default
                        to_remove.add(col)
                    
                    redundancy_pairs.append((idx, col, upper_triangle.loc[idx, col]))
        
        # Selected features
        selected_features = [col for col in X.columns if col not in to_remove]
        
        # Feature scores (correlation with target if available)
        if y is not None:
            feature_scores = {col: abs(y.corr(X[col])) for col in selected_features}
        else:
            feature_scores = {col: 1.0 for col in selected_features}
        
        # Redundancy analysis
        redundancy_analysis = {
            'highly_correlated_pairs': redundancy_pairs,
            'removed_features': list(to_remove),
            'correlation_threshold': self.correlation_threshold
        }
        
        result = FeatureSelectionResult(
            method=FeatureSelectionMethod.CORRELATION_FILTER,
            selected_features=selected_features,
            feature_scores=feature_scores,
            n_features_selected=len(selected_features),
            correlation_matrix=corr_matrix,
            redundancy_analysis=redundancy_analysis,
            performance_improvement=0.0  # To be calculated later
        )
        
        print(f"   ✅ Correlation Filter Complete: {len(selected_features)}/{len(X.columns)} features selected")
        print(f"   Removed {len(to_remove)} highly correlated features")
        
        return result
    
    def mutual_information_selection(self, 
                                   X: pd.DataFrame, 
                                   y: pd.Series,
                                   k: int = None) -> FeatureSelectionResult:
        """Select features based on mutual information."""
        
        print(f"🧠 Applying Mutual Information Selection...")
        
        if k is None:
            k = min(self.max_features or len(X.columns), len(X.columns))
        
        # Calculate mutual information
        selector = SelectKBest(score_func=mutual_info_regression, k=k)
        X_selected = selector.fit_transform(X, y)
        
        # Get selected features
        selected_mask = selector.get_support()
        selected_features = X.columns[selected_mask].tolist()
        
        # Feature scores
        feature_scores = dict(zip(X.columns, selector.scores_))
        
        # Redundancy analysis
        redundancy_analysis = {
            'mutual_info_scores': feature_scores,
            'selection_threshold': sorted(selector.scores_, reverse=True)[k-1] if k < len(X.columns) else 0
        }
        
        result = FeatureSelectionResult(
            method=FeatureSelectionMethod.MUTUAL_INFORMATION,
            selected_features=selected_features,
            feature_scores=feature_scores,
            n_features_selected=len(selected_features),
            correlation_matrix=X[selected_features].corr(),
            redundancy_analysis=redundancy_analysis,
            performance_improvement=0.0
        )
        
        print(f"   ✅ Mutual Information Selection Complete: {len(selected_features)} features selected")
        
        return result
    
    def recursive_feature_elimination(self, 
                                    X: pd.DataFrame, 
                                    y: pd.Series,
                                    estimator: Any = None,
                                    n_features: int = None) -> FeatureSelectionResult:
        """Recursive feature elimination."""
        
        print(f"🔄 Applying Recursive Feature Elimination...")
        
        if estimator is None:
            estimator = RandomForestRegressor(n_estimators=50, random_state=42)
        
        if n_features is None:
            n_features = min(self.max_features or len(X.columns), len(X.columns) // 2)
        
        # Apply RFE
        selector = RFE(estimator=estimator, n_features_to_select=n_features)
        X_selected = selector.fit_transform(X, y)
        
        # Get selected features
        selected_mask = selector.get_support()
        selected_features = X.columns[selected_mask].tolist()
        
        # Feature rankings
        feature_scores = {}
        for i, feature in enumerate(X.columns):
            # Convert ranking to score (lower rank = higher score)
            feature_scores[feature] = 1.0 / selector.ranking_[i]
        
        # Redundancy analysis
        redundancy_analysis = {
            'feature_rankings': dict(zip(X.columns, selector.ranking_)),
            'eliminated_features': X.columns[~selected_mask].tolist()
        }
        
        result = FeatureSelectionResult(
            method=FeatureSelectionMethod.RECURSIVE_ELIMINATION,
            selected_features=selected_features,
            feature_scores=feature_scores,
            n_features_selected=len(selected_features),
            correlation_matrix=X[selected_features].corr(),
            redundancy_analysis=redundancy_analysis,
            performance_improvement=0.0
        )
        
        print(f"   ✅ Recursive Feature Elimination Complete: {len(selected_features)} features selected")
        
        return result
    
    def l1_regularization_selection(self, 
                                  X: pd.DataFrame, 
                                  y: pd.Series,
                                  alpha: float = 0.01) -> FeatureSelectionResult:
        """Feature selection using L1 regularization (Lasso)."""
        
        print(f"🎯 Applying L1 Regularization Selection...")
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)
        
        # Apply Lasso
        lasso = Lasso(alpha=alpha, random_state=42)
        lasso.fit(X_scaled, y)
        
        # Get selected features (non-zero coefficients)
        selected_mask = lasso.coef_ != 0
        selected_features = X.columns[selected_mask].tolist()
        
        # Feature scores (absolute coefficients)
        feature_scores = dict(zip(X.columns, np.abs(lasso.coef_)))
        
        # Redundancy analysis
        redundancy_analysis = {
            'lasso_coefficients': dict(zip(X.columns, lasso.coef_)),
            'alpha_parameter': alpha,
            'zero_coefficients': X.columns[~selected_mask].tolist()
        }
        
        result = FeatureSelectionResult(
            method=FeatureSelectionMethod.L1_REGULARIZATION,
            selected_features=selected_features,
            feature_scores=feature_scores,
            n_features_selected=len(selected_features),
            correlation_matrix=X[selected_features].corr() if selected_features else pd.DataFrame(),
            redundancy_analysis=redundancy_analysis,
            performance_improvement=0.0
        )
        
        print(f"   ✅ L1 Regularization Selection Complete: {len(selected_features)} features selected")
        
        return result
    
    def tree_importance_selection(self, 
                                X: pd.DataFrame, 
                                y: pd.Series,
                                threshold: float = 0.001) -> FeatureSelectionResult:
        """Feature selection based on tree-based feature importance."""
        
        print(f"🌳 Applying Tree-Based Feature Selection...")
        
        # Train random forest
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        # Get feature importance
        importances = rf.feature_importances_
        feature_scores = dict(zip(X.columns, importances))
        
        # Select features above threshold
        selected_features = [feature for feature, importance in feature_scores.items() 
                           if importance >= threshold]
        
        # If max_features is set, select top features
        if self.max_features and len(selected_features) > self.max_features:
            sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
            selected_features = [feature for feature, _ in sorted_features[:self.max_features]]
        
        # Redundancy analysis
        redundancy_analysis = {
            'importance_threshold': threshold,
            'below_threshold_features': [f for f in X.columns if feature_scores[f] < threshold]
        }
        
        result = FeatureSelectionResult(
            method=FeatureSelectionMethod.TREE_IMPORTANCE,
            selected_features=selected_features,
            feature_scores=feature_scores,
            n_features_selected=len(selected_features),
            correlation_matrix=X[selected_features].corr(),
            redundancy_analysis=redundancy_analysis,
            performance_improvement=0.0
        )
        
        print(f"   ✅ Tree-Based Selection Complete: {len(selected_features)} features selected")
        
        return result
    
    def variance_threshold_selection(self, 
                                   X: pd.DataFrame) -> FeatureSelectionResult:
        """Remove features with low variance."""
        
        print(f"📊 Applying Variance Threshold Selection...")
        
        # Apply variance threshold
        selector = VarianceThreshold(threshold=self.variance_threshold)
        X_selected = selector.fit_transform(X)
        
        # Get selected features
        selected_mask = selector.get_support()
        selected_features = X.columns[selected_mask].tolist()
        
        # Feature scores (variance)
        feature_scores = dict(zip(X.columns, selector.variances_))
        
        # Redundancy analysis
        redundancy_analysis = {
            'variance_threshold': self.variance_threshold,
            'low_variance_features': X.columns[~selected_mask].tolist(),
            'feature_variances': feature_scores
        }
        
        result = FeatureSelectionResult(
            method=FeatureSelectionMethod.VARIANCE_THRESHOLD,
            selected_features=selected_features,
            feature_scores=feature_scores,
            n_features_selected=len(selected_features),
            correlation_matrix=X[selected_features].corr(),
            redundancy_analysis=redundancy_analysis,
            performance_improvement=0.0
        )
        
        print(f"   ✅ Variance Threshold Selection Complete: {len(selected_features)} features selected")
        
        return result
    
    def comprehensive_feature_selection(self, 
                                      X: pd.DataFrame, 
                                      y: pd.Series,
                                      methods: List[FeatureSelectionMethod] = None) -> Dict[str, FeatureSelectionResult]:
        """Apply multiple feature selection methods and compare results."""
        
        print(f"\n🎯 Comprehensive Feature Selection Analysis...")
        
        if methods is None:
            methods = [
                FeatureSelectionMethod.VARIANCE_THRESHOLD,
                FeatureSelectionMethod.CORRELATION_FILTER,
                FeatureSelectionMethod.MUTUAL_INFORMATION,
                FeatureSelectionMethod.TREE_IMPORTANCE,
                FeatureSelectionMethod.L1_REGULARIZATION
            ]
        
        results = {}
        
        # Apply each method
        for method in methods:
            if method == FeatureSelectionMethod.VARIANCE_THRESHOLD:
                results['variance_threshold'] = self.variance_threshold_selection(X)
            elif method == FeatureSelectionMethod.CORRELATION_FILTER:
                results['correlation_filter'] = self.correlation_filter(X, y)
            elif method == FeatureSelectionMethod.MUTUAL_INFORMATION:
                results['mutual_information'] = self.mutual_information_selection(X, y)
            elif method == FeatureSelectionMethod.TREE_IMPORTANCE:
                results['tree_importance'] = self.tree_importance_selection(X, y)
            elif method == FeatureSelectionMethod.L1_REGULARIZATION:
                results['l1_regularization'] = self.l1_regularization_selection(X, y)
        
        # Summary comparison
        print(f"\n📊 Feature Selection Method Comparison:")
        print("-" * 70)
        for method, result in results.items():
            print(f"{method:<20}: {result.n_features_selected:>3} features selected")
        
        self.selection_results = results
        return results
    
    def consensus_feature_selection(self, 
                                   selection_results: Dict[str, FeatureSelectionResult],
                                   min_votes: int = 2) -> List[str]:
        """Select features based on consensus across multiple methods."""
        
        print(f"\n🗳️ Consensus Feature Selection (min votes: {min_votes})...")
        
        # Count votes for each feature
        feature_votes = {}
        for method, result in selection_results.items():
            for feature in result.selected_features:
                feature_votes[feature] = feature_votes.get(feature, 0) + 1
        
        # Select features with minimum votes
        consensus_features = [feature for feature, votes in feature_votes.items() 
                            if votes >= min_votes]
        
        print(f"   ✅ Consensus Selection Complete: {len(consensus_features)} features selected")
        print(f"   Features selected by {min_votes}+ methods: {len(consensus_features)}")
        
        return consensus_features 