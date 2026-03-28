#!/usr/bin/env python3
"""
Dynamic Model Retraining and Continuous Learning System
Addresses static model limitations with adaptive retraining and performance monitoring
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
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
import joblib

# Statistical Libraries
import scipy.stats as stats
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import json
import threading
import time
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RetrainingTrigger(Enum):
    """Triggers for model retraining."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    TIME_BASED = "time_based"
    DATA_DRIFT = "data_drift"
    MARKET_REGIME_CHANGE = "market_regime_change"
    MANUAL = "manual"

class ModelStatus(Enum):
    """Model status states."""
    ACTIVE = "active"
    TRAINING = "training"
    VALIDATING = "validating"
    DEPRECATED = "deprecated"
    FAILED = "failed"

@dataclass
class ModelPerformance:
    """Model performance metrics."""
    timestamp: datetime
    r2_score: float
    mse: float
    mae: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    predictions_count: int
    confidence_score: float

@dataclass
class RetrainingEvent:
    """Retraining event record."""
    timestamp: datetime
    trigger: RetrainingTrigger
    old_performance: ModelPerformance
    new_performance: ModelPerformance
    improvement: float
    data_size: int
    training_time: float
    success: bool
    notes: str = ""

@dataclass
class ModelVersion:
    """Model version information."""
    version: str
    timestamp: datetime
    model_path: str
    performance: ModelPerformance
    status: ModelStatus
    features: List[str]
    hyperparameters: Dict[str, Any]
    training_data_size: int

class PerformanceMonitor:
    """Real-time performance monitoring system."""
    
    def __init__(self, 
                 performance_window: int = 100,
                 degradation_threshold: float = 0.1,
                 min_predictions: int = 50):
        
        self.performance_window = performance_window
        self.degradation_threshold = degradation_threshold
        self.min_predictions = min_predictions
        
        # Performance tracking
        self.recent_predictions = []
        self.recent_actuals = []
        self.performance_history = []
        self.baseline_performance = None
        
        print("📊 Performance Monitor Initialized")
        print(f"   Performance Window: {performance_window} predictions")
        print(f"   Degradation Threshold: {degradation_threshold:.1%}")
        print(f"   Minimum Predictions: {min_predictions}")
    
    def update_performance(self, y_true: float, y_pred: float, confidence: float = 1.0):
        """Update performance with new prediction."""
        
        # Add to recent predictions
        self.recent_predictions.append(y_pred)
        self.recent_actuals.append(y_true)
        
        # Maintain window size
        if len(self.recent_predictions) > self.performance_window:
            self.recent_predictions.pop(0)
            self.recent_actuals.pop(0)
        
        # Calculate current performance if enough data
        if len(self.recent_predictions) >= self.min_predictions:
            current_performance = self._calculate_performance(confidence)
            self.performance_history.append(current_performance)
            
            # Set baseline if not set
            if self.baseline_performance is None:
                self.baseline_performance = current_performance
                print(f"📈 Baseline Performance Set: R² = {current_performance.r2_score:.4f}")
            
            return current_performance
        
        return None
    
    def _calculate_performance(self, confidence: float) -> ModelPerformance:
        """Calculate current performance metrics."""
        
        y_true = np.array(self.recent_actuals)
        y_pred = np.array(self.recent_predictions)
        
        # Basic metrics
        r2 = r2_score(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        
        # Trading-specific metrics
        returns = y_pred  # Assuming predictions are returns
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Calculate drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Win rate
        win_rate = np.mean(y_pred * y_true > 0) if len(y_true) > 0 else 0
        
        return ModelPerformance(
            timestamp=datetime.now(),
            r2_score=r2,
            mse=mse,
            mae=mae,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            predictions_count=len(self.recent_predictions),
            confidence_score=confidence
        )
    
    def check_degradation(self) -> bool:
        """Check if performance has degraded significantly."""
        
        if (self.baseline_performance is None or 
            len(self.performance_history) < 5):  # Need some history
            return False
        
        current_performance = self.performance_history[-1]
        
        # Check R² degradation
        r2_degradation = (self.baseline_performance.r2_score - current_performance.r2_score) / abs(self.baseline_performance.r2_score)
        
        # Check Sharpe ratio degradation
        sharpe_degradation = (self.baseline_performance.sharpe_ratio - current_performance.sharpe_ratio) / abs(self.baseline_performance.sharpe_ratio) if self.baseline_performance.sharpe_ratio != 0 else 0
        
        # Check win rate degradation
        win_rate_degradation = self.baseline_performance.win_rate - current_performance.win_rate
        
        degraded = (r2_degradation > self.degradation_threshold or
                   sharpe_degradation > self.degradation_threshold or
                   win_rate_degradation > self.degradation_threshold)
        
        if degraded:
            print(f"🚨 Performance Degradation Detected!")
            print(f"   R² Degradation: {r2_degradation:.2%}")
            print(f"   Sharpe Degradation: {sharpe_degradation:.2%}")
            print(f"   Win Rate Degradation: {win_rate_degradation:.2%}")
        
        return degraded

class DataDriftDetector:
    """Detect changes in data distribution."""
    
    def __init__(self, 
                 drift_threshold: float = 0.05,
                 window_size: int = 1000):
        
        self.drift_threshold = drift_threshold
        self.window_size = window_size
        
        # Reference distribution
        self.reference_data = None
        self.recent_data = []
        
        print("🔍 Data Drift Detector Initialized")
        print(f"   Drift Threshold: {drift_threshold}")
        print(f"   Window Size: {window_size}")
    
    def set_reference_distribution(self, X: pd.DataFrame):
        """Set reference distribution for drift detection."""
        self.reference_data = X.copy()
        print(f"📊 Reference Distribution Set: {len(X)} samples, {len(X.columns)} features")
    
    def update_recent_data(self, X: pd.DataFrame):
        """Update recent data window."""
        
        self.recent_data.append(X)
        
        # Maintain window size
        if len(self.recent_data) > self.window_size:
            self.recent_data.pop(0)
    
    def detect_drift(self) -> Tuple[bool, Dict[str, float]]:
        """Detect data drift using statistical tests."""
        
        if (self.reference_data is None or 
            len(self.recent_data) < 100):  # Need enough recent data
            return False, {}
        
        # Combine recent data
        recent_df = pd.concat(self.recent_data, ignore_index=True)
        
        drift_scores = {}
        significant_drift = False
        
        # Test each feature for drift
        for column in self.reference_data.columns:
            if column in recent_df.columns:
                # Kolmogorov-Smirnov test
                ref_values = self.reference_data[column].dropna()
                recent_values = recent_df[column].dropna()
                
                if len(ref_values) > 0 and len(recent_values) > 0:
                    ks_stat, p_value = stats.ks_2samp(ref_values, recent_values)
                    drift_scores[column] = p_value
                    
                    if p_value < self.drift_threshold:
                        significant_drift = True
        
        if significant_drift:
            print(f"🚨 Data Drift Detected!")
            drifted_features = [f for f, p in drift_scores.items() if p < self.drift_threshold]
            print(f"   Drifted Features: {len(drifted_features)}")
            print(f"   Most Significant: {min(drift_scores.items(), key=lambda x: x[1])}")
        
        return significant_drift, drift_scores

class MarketRegimeDetector:
    """Detect changes in market regime."""
    
    def __init__(self, 
                 volatility_threshold: float = 2.0,
                 trend_threshold: float = 0.1,
                 window_size: int = 252):
        
        self.volatility_threshold = volatility_threshold
        self.trend_threshold = trend_threshold
        self.window_size = window_size
        
        # Regime tracking
        self.current_regime = None
        self.regime_history = []
        self.price_history = []
        
        print("🌊 Market Regime Detector Initialized")
        print(f"   Volatility Threshold: {volatility_threshold}")
        print(f"   Trend Threshold: {trend_threshold}")
        print(f"   Window Size: {window_size}")
    
    def update_market_data(self, price: float, volume: float = None):
        """Update market data for regime detection."""
        
        self.price_history.append(price)
        
        # Maintain window size
        if len(self.price_history) > self.window_size:
            self.price_history.pop(0)
        
        # Detect regime if enough data
        if len(self.price_history) >= 50:  # Minimum for regime detection
            new_regime = self._detect_current_regime()
            
            if new_regime != self.current_regime:
                print(f"🌊 Market Regime Change: {self.current_regime} → {new_regime}")
                self.current_regime = new_regime
                self.regime_history.append({
                    'timestamp': datetime.now(),
                    'regime': new_regime,
                    'price': price
                })
                return True
        
        return False
    
    def _detect_current_regime(self) -> str:
        """Detect current market regime."""
        
        prices = np.array(self.price_history)
        returns = np.diff(prices) / prices[:-1]
        
        # Calculate metrics
        recent_volatility = np.std(returns[-50:]) if len(returns) >= 50 else np.std(returns)
        long_term_volatility = np.std(returns)
        recent_trend = np.mean(returns[-20:]) if len(returns) >= 20 else np.mean(returns)
        
        # Determine regime
        if recent_volatility > self.volatility_threshold * long_term_volatility:
            if recent_trend > self.trend_threshold:
                return "VOLATILE_BULL"
            elif recent_trend < -self.trend_threshold:
                return "VOLATILE_BEAR"
            else:
                return "HIGH_VOLATILITY"
        else:
            if recent_trend > self.trend_threshold:
                return "STABLE_BULL"
            elif recent_trend < -self.trend_threshold:
                return "STABLE_BEAR"
            else:
                return "SIDEWAYS"

class DynamicModelRetrainer:
    """Dynamic model retraining and continuous learning system."""
    
    def __init__(self,
                 model_class=RandomForestRegressor,
                 model_params: Dict[str, Any] = None,
                 retrain_frequency_hours: int = 24,
                 max_training_data_age_days: int = 365,
                 min_training_samples: int = 1000,
                 model_storage_path: str = "models/"):
        
        self.model_class = model_class
        self.model_params = model_params or {'n_estimators': 100, 'random_state': 42}
        self.retrain_frequency_hours = retrain_frequency_hours
        self.max_training_data_age_days = max_training_data_age_days
        self.min_training_samples = min_training_samples
        
        # Create model storage directory
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(exist_ok=True)
        
        # Components
        self.performance_monitor = PerformanceMonitor()
        self.drift_detector = DataDriftDetector()
        self.regime_detector = MarketRegimeDetector()
        
        # Model management
        self.current_model = None
        self.model_versions = []
        self.training_data = pd.DataFrame()
        self.target_data = pd.Series()
        self.last_retrain_time = None
        
        # Retraining events
        self.retraining_events = []
        self.is_training = False
        
        print("🔄 Dynamic Model Retrainer Initialized")
        print(f"   Model Class: {model_class.__name__}")
        print(f"   Retrain Frequency: {retrain_frequency_hours} hours")
        print(f"   Max Data Age: {max_training_data_age_days} days")
        print(f"   Min Training Samples: {min_training_samples}")
    
    def initialize_model(self, X: pd.DataFrame, y: pd.Series) -> bool:
        """Initialize the first model."""
        
        print("🚀 Initializing First Model...")
        
        if len(X) < self.min_training_samples:
            print(f"❌ Insufficient training data: {len(X)} < {self.min_training_samples}")
            return False
        
        # Store training data
        self.training_data = X.copy()
        self.target_data = y.copy()
        
        # Set reference distributions
        self.drift_detector.set_reference_distribution(X)
        
        # Train initial model
        success = self._train_model(X, y, is_initial=True)
        
        if success:
            self.last_retrain_time = datetime.now()
            print("✅ Initial Model Training Complete")
        
        return success
    
    def update_with_new_data(self, X_new: pd.DataFrame, y_new: pd.Series):
        """Update system with new data."""
        
        # Add to training data
        self.training_data = pd.concat([self.training_data, X_new], ignore_index=True)
        self.target_data = pd.concat([self.target_data, y_new], ignore_index=True)
        
        # Update drift detector
        self.drift_detector.update_recent_data(X_new)
        
        # Update market regime detector
        if 'close' in X_new.columns:
            for price in X_new['close']:
                regime_change = self.regime_detector.update_market_data(price)
                if regime_change:
                    self._trigger_retraining(RetrainingTrigger.MARKET_REGIME_CHANGE)
        
        # Trim old data
        self._trim_old_data()
        
        # Check for retraining triggers
        self._check_retraining_triggers()
    
    def make_prediction(self, X: pd.DataFrame) -> Tuple[np.ndarray, float]:
        """Make prediction and update performance monitoring."""
        
        if self.current_model is None:
            raise ValueError("No trained model available")
        
        # Make prediction
        prediction = self.current_model.predict(X)
        
        # Calculate confidence (simplified)
        if hasattr(self.current_model, 'predict_proba'):
            proba = self.current_model.predict_proba(X)
            confidence = np.max(proba, axis=1).mean()
        else:
            confidence = 0.8  # Default confidence for regression
        
        return prediction, confidence
    
    def update_performance(self, y_true: float, y_pred: float, confidence: float = 1.0):
        """Update performance monitoring with actual results."""
        
        current_performance = self.performance_monitor.update_performance(y_true, y_pred, confidence)
        
        # Check for performance degradation
        if (current_performance and 
            self.performance_monitor.check_degradation()):
            self._trigger_retraining(RetrainingTrigger.PERFORMANCE_DEGRADATION)
    
    def _check_retraining_triggers(self):
        """Check all retraining triggers."""
        
        if self.is_training:
            return
        
        # Time-based trigger
        if (self.last_retrain_time and 
            datetime.now() - self.last_retrain_time > timedelta(hours=self.retrain_frequency_hours)):
            self._trigger_retraining(RetrainingTrigger.TIME_BASED)
        
        # Data drift trigger
        drift_detected, drift_scores = self.drift_detector.detect_drift()
        if drift_detected:
            self._trigger_retraining(RetrainingTrigger.DATA_DRIFT)
    
    def _trigger_retraining(self, trigger: RetrainingTrigger):
        """Trigger model retraining."""
        
        if self.is_training:
            print(f"⏳ Retraining already in progress, skipping {trigger.value}")
            return
        
        print(f"🔄 Triggering Retraining: {trigger.value}")
        
        # Start retraining in background
        threading.Thread(target=self._retrain_model_async, args=(trigger,)).start()
    
    def _retrain_model_async(self, trigger: RetrainingTrigger):
        """Asynchronously retrain the model."""
        
        self.is_training = True
        start_time = time.time()
        
        try:
            # Get current performance
            old_performance = (self.performance_monitor.performance_history[-1] 
                             if self.performance_monitor.performance_history 
                             else None)
            
            # Train new model
            success = self._train_model(self.training_data, self.target_data)
            
            if success:
                # Evaluate new model performance
                new_performance = self._evaluate_model_performance()
                
                # Calculate improvement
                improvement = 0.0
                if old_performance:
                    improvement = (new_performance.r2_score - old_performance.r2_score) / abs(old_performance.r2_score) if old_performance.r2_score != 0 else 0
                
                # Record retraining event
                event = RetrainingEvent(
                    timestamp=datetime.now(),
                    trigger=trigger,
                    old_performance=old_performance,
                    new_performance=new_performance,
                    improvement=improvement,
                    data_size=len(self.training_data),
                    training_time=time.time() - start_time,
                    success=True,
                    notes=f"Triggered by {trigger.value}"
                )
                
                self.retraining_events.append(event)
                self.last_retrain_time = datetime.now()
                
                # Update baseline performance
                self.performance_monitor.baseline_performance = new_performance
                
                print(f"✅ Retraining Complete: {improvement:+.2%} improvement")
            
        except Exception as e:
            print(f"❌ Retraining Failed: {str(e)}")
            
            # Record failed event
            event = RetrainingEvent(
                timestamp=datetime.now(),
                trigger=trigger,
                old_performance=old_performance,
                new_performance=None,
                improvement=0.0,
                data_size=len(self.training_data),
                training_time=time.time() - start_time,
                success=False,
                notes=f"Failed: {str(e)}"
            )
            self.retraining_events.append(event)
        
        finally:
            self.is_training = False
    
    def _train_model(self, X: pd.DataFrame, y: pd.Series, is_initial: bool = False) -> bool:
        """Train a new model version."""
        
        try:
            print(f"🎯 Training Model: {len(X)} samples, {len(X.columns)} features")
            
            # Create and train model
            model = self.model_class(**self.model_params)
            model.fit(X, y)
            
            # Create model version
            version = f"v{len(self.model_versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_path = self.model_storage_path / f"model_{version}.joblib"
            
            # Save model
            joblib.dump(model, model_path)
            
            # Calculate performance
            performance = self._calculate_model_performance(model, X, y)
            
            # Create version record
            model_version = ModelVersion(
                version=version,
                timestamp=datetime.now(),
                model_path=str(model_path),
                performance=performance,
                status=ModelStatus.ACTIVE,
                features=list(X.columns),
                hyperparameters=self.model_params.copy(),
                training_data_size=len(X)
            )
            
            # Update current model
            if self.current_model is not None:
                # Mark previous model as deprecated
                if self.model_versions:
                    self.model_versions[-1].status = ModelStatus.DEPRECATED
            
            self.current_model = model
            self.model_versions.append(model_version)
            
            print(f"✅ Model Trained: {version}")
            print(f"   R² Score: {performance.r2_score:.4f}")
            print(f"   Sharpe Ratio: {performance.sharpe_ratio:.4f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model Training Failed: {str(e)}")
            return False
    
    def _calculate_model_performance(self, model, X: pd.DataFrame, y: pd.Series) -> ModelPerformance:
        """Calculate comprehensive model performance."""
        
        # Make predictions
        y_pred = model.predict(X)
        
        # Basic metrics
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        
        # Trading metrics
        returns = y_pred
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Drawdown calculation
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Win rate
        win_rate = np.mean(y_pred * y > 0) if len(y) > 0 else 0
        
        return ModelPerformance(
            timestamp=datetime.now(),
            r2_score=r2,
            mse=mse,
            mae=mae,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            predictions_count=len(y),
            confidence_score=0.8
        )
    
    def _evaluate_model_performance(self) -> ModelPerformance:
        """Evaluate current model performance on recent data."""
        
        if len(self.training_data) > 1000:
            # Use last 500 samples for evaluation
            X_eval = self.training_data.tail(500)
            y_eval = self.target_data.tail(500)
        else:
            X_eval = self.training_data
            y_eval = self.target_data
        
        return self._calculate_model_performance(self.current_model, X_eval, y_eval)
    
    def _trim_old_data(self):
        """Remove old training data beyond max age."""
        
        if len(self.training_data) == 0:
            return
        
        # Assume data has timestamp index or column
        cutoff_date = datetime.now() - timedelta(days=self.max_training_data_age_days)
        
        # For demo purposes, just keep last N samples
        max_samples = self.min_training_samples * 3
        if len(self.training_data) > max_samples:
            self.training_data = self.training_data.tail(max_samples)
            self.target_data = self.target_data.tail(max_samples)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        
        current_performance = (self.performance_monitor.performance_history[-1] 
                             if self.performance_monitor.performance_history 
                             else None)
        
        return {
            'current_model_version': self.model_versions[-1].version if self.model_versions else None,
            'model_status': self.model_versions[-1].status.value if self.model_versions else None,
            'training_data_size': len(self.training_data),
            'is_training': self.is_training,
            'last_retrain_time': self.last_retrain_time,
            'current_performance': current_performance,
            'total_retraining_events': len(self.retraining_events),
            'current_regime': self.regime_detector.current_regime,
            'performance_monitoring': {
                'baseline_r2': self.performance_monitor.baseline_performance.r2_score if self.performance_monitor.baseline_performance else None,
                'current_r2': current_performance.r2_score if current_performance else None,
                'predictions_tracked': len(self.performance_monitor.recent_predictions)
            }
        }
    
    def manual_retrain(self) -> bool:
        """Manually trigger model retraining."""
        print("🔧 Manual Retraining Triggered")
        self._trigger_retraining(RetrainingTrigger.MANUAL)
        return True

def generate_dynamic_market_data(n_samples: int = 2000) -> Tuple[pd.DataFrame, pd.Series]:
    """Generate dynamic market data with regime changes and drift."""
    
    np.random.seed(42)
    
    timestamps = pd.date_range(start='2020-01-01', periods=n_samples, freq='H')
    
    # Generate price with regime changes
    price = 100.0
    prices = [price]
    regime_changes = [500, 1000, 1500]  # Points where market regime changes
    
    for i in range(1, n_samples):
        # Different volatility regimes
        if i < regime_changes[0]:
            volatility = 0.01  # Low volatility
            drift = 0.0001
        elif i < regime_changes[1]:
            volatility = 0.03  # High volatility
            drift = -0.0002
        elif i < regime_changes[2]:
            volatility = 0.015  # Medium volatility
            drift = 0.0003
        else:
            volatility = 0.025  # High volatility again
            drift = -0.0001
        
        return_shock = np.random.normal(drift, volatility)
        price *= (1 + return_shock)
        prices.append(price)
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'close': prices
    })
    data.set_index('timestamp', inplace=True)
    
    # Generate features that drift over time
    features = pd.DataFrame(index=data.index)
    returns = data['close'].pct_change()
    
    # Base features
    features['returns'] = returns
    features['volatility_20'] = returns.rolling(20).std()
    features['sma_50'] = data['close'].rolling(50).mean()
    features['rsi'] = calculate_rsi(data['close'], 14)
    
    # Features that drift over time
    for i, idx in enumerate(data.index):
        # Add time-dependent drift to features
        time_factor = i / len(data)
        features.loc[idx, 'drifting_feature_1'] = np.random.normal(0.5 + time_factor, 0.1)
        features.loc[idx, 'drifting_feature_2'] = np.random.normal(1.0 - time_factor * 0.5, 0.2)
    
    # Add technical indicators
    features['macd'] = calculate_macd(data['close'])
    features['bollinger_position'] = calculate_bollinger_position(data['close'])
    
    # Target: future returns
    target = data['close'].shift(-24) / data['close'] - 1
    
    # Clean data
    valid_mask = ~(features.isnull().any(axis=1) | target.isnull())
    features_clean = features[valid_mask]
    target_clean = target[valid_mask]
    
    return features_clean, target_clean

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices: pd.Series) -> pd.Series:
    """Calculate MACD indicator."""
    ema_12 = prices.ewm(span=12).mean()
    ema_26 = prices.ewm(span=26).mean()
    return ema_12 - ema_26

def calculate_bollinger_position(prices: pd.Series, period: int = 20) -> pd.Series:
    """Calculate position within Bollinger Bands."""
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return (prices - lower) / (upper - lower)

def demonstrate_dynamic_retraining():
    """Demonstrate dynamic model retraining system."""
    
    print("🔄 Dynamic Model Retraining System Demonstration")
    print("=" * 80)
    
    # Generate market data with regime changes
    print("📊 Generating Dynamic Market Data...")
    X, y = generate_dynamic_market_data(2000)
    print(f"   Generated {len(X)} samples with {len(X.columns)} features")
    print(f"   Data includes regime changes and feature drift")
    
    # Initialize dynamic retrainer
    retrainer = DynamicModelRetrainer(
        model_class=RandomForestRegressor,
        model_params={'n_estimators': 50, 'random_state': 42},
        retrain_frequency_hours=168,  # Weekly retraining
        max_training_data_age_days=365,
        min_training_samples=500
    )
    
    # Split data for simulation
    initial_size = 800
    X_initial = X.iloc[:initial_size]
    y_initial = y.iloc[:initial_size]
    
    # Initialize model
    print(f"\n🚀 Initializing Model with {len(X_initial)} samples...")
    success = retrainer.initialize_model(X_initial, y_initial)
    
    if not success:
        print("❌ Failed to initialize model")
        return
    
    # Simulate live trading with new data
    print(f"\n📈 Simulating Live Trading with Dynamic Updates...")
    
    batch_size = 50
    prediction_results = []
    
    for i in range(initial_size, len(X), batch_size):
        end_idx = min(i + batch_size, len(X))
        X_batch = X.iloc[i:end_idx]
        y_batch = y.iloc[i:end_idx]
        
        print(f"\n📊 Processing Batch {i//batch_size + 1}: Samples {i}-{end_idx}")
        
        # Make predictions
        try:
            predictions, confidence = retrainer.make_prediction(X_batch)
            
            # Simulate actual results and update performance
            for j, (pred, actual) in enumerate(zip(predictions, y_batch.values)):
                retrainer.update_performance(actual, pred, confidence)
                prediction_results.append({
                    'sample': i + j,
                    'prediction': pred,
                    'actual': actual,
                    'confidence': confidence
                })
            
            # Update with new data (simulates real-time data ingestion)
            retrainer.update_with_new_data(X_batch, y_batch)
            
            # Show system status every few batches
            if (i // batch_size + 1) % 5 == 0:
                status = retrainer.get_system_status()
                print(f"   📊 System Status:")
                print(f"      Model Version: {status['current_model_version']}")
                print(f"      Training Data Size: {status['training_data_size']}")
                print(f"      Current Regime: {status['current_regime']}")
                print(f"      Retraining Events: {status['total_retraining_events']}")
                
                if status['current_performance']:
                    perf = status['current_performance']
                    print(f"      Current R²: {perf.r2_score:.4f}")
                    print(f"      Sharpe Ratio: {perf.sharpe_ratio:.4f}")
        
        except Exception as e:
            print(f"   ❌ Error processing batch: {str(e)}")
            continue
    
    # Final system analysis
    print(f"\n📊 Final System Analysis:")
    print("=" * 50)
    
    status = retrainer.get_system_status()
    print(f"📈 Final Model Status:")
    print(f"   Model Version: {status['current_model_version']}")
    print(f"   Total Training Data: {status['training_data_size']} samples")
    print(f"   Retraining Events: {status['total_retraining_events']}")
    print(f"   Current Market Regime: {status['current_regime']}")
    
    # Performance analysis
    if retrainer.performance_monitor.performance_history:
        performances = retrainer.performance_monitor.performance_history
        print(f"\n📊 Performance Evolution:")
        print(f"   Initial R²: {performances[0].r2_score:.4f}")
        print(f"   Final R²: {performances[-1].r2_score:.4f}")
        print(f"   Best R²: {max(p.r2_score for p in performances):.4f}")
        print(f"   Worst R²: {min(p.r2_score for p in performances):.4f}")
        
        # Sharpe ratio evolution
        print(f"   Initial Sharpe: {performances[0].sharpe_ratio:.4f}")
        print(f"   Final Sharpe: {performances[-1].sharpe_ratio:.4f}")
        print(f"   Best Sharpe: {max(p.sharpe_ratio for p in performances):.4f}")
    
    # Retraining events analysis
    if retrainer.retraining_events:
        print(f"\n🔄 Retraining Events Analysis:")
        for i, event in enumerate(retrainer.retraining_events):
            print(f"   Event {i+1}: {event.trigger.value}")
            print(f"      Timestamp: {event.timestamp}")
            print(f"      Improvement: {event.improvement:+.2%}")
            print(f"      Training Time: {event.training_time:.1f}s")
            print(f"      Success: {'✅' if event.success else '❌'}")
    
    # Model versions
    print(f"\n📦 Model Versions:")
    for version in retrainer.model_versions:
        status_emoji = "🟢" if version.status == ModelStatus.ACTIVE else "🔴"
        print(f"   {status_emoji} {version.version}: R² = {version.performance.r2_score:.4f}")
    
    return retrainer, prediction_results

def create_retraining_analysis_plot(retrainer, prediction_results):
    """Create comprehensive analysis plots."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Performance evolution over time
    ax1 = axes[0, 0]
    if retrainer.performance_monitor.performance_history:
        performances = retrainer.performance_monitor.performance_history
        timestamps = [p.timestamp for p in performances]
        r2_scores = [p.r2_score for p in performances]
        sharpe_ratios = [p.sharpe_ratio for p in performances]
        
        ax1.plot(timestamps, r2_scores, label='R² Score', color='blue', linewidth=2)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(timestamps, sharpe_ratios, label='Sharpe Ratio', color='red', linewidth=2)
        
        ax1.set_title('Model Performance Evolution')
        ax1.set_ylabel('R² Score', color='blue')
        ax1_twin.set_ylabel('Sharpe Ratio', color='red')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
    
    # Retraining events timeline
    ax2 = axes[0, 1]
    if retrainer.retraining_events:
        events = retrainer.retraining_events
        event_times = [e.timestamp for e in events]
        event_improvements = [e.improvement * 100 for e in events]
        event_colors = ['green' if e.success else 'red' for e in events]
        
        bars = ax2.bar(range(len(events)), event_improvements, color=event_colors, alpha=0.7)
        ax2.set_title('Retraining Event Improvements')
        ax2.set_ylabel('Performance Improvement (%)')
        ax2.set_xlabel('Retraining Event')
        ax2.grid(True, alpha=0.3)
        
        # Add trigger labels
        for i, event in enumerate(events):
            ax2.text(i, event_improvements[i], event.trigger.value.replace('_', '\n'), 
                    ha='center', va='bottom', fontsize=8, rotation=45)
    
    # Prediction accuracy over time
    ax3 = axes[1, 0]
    if prediction_results:
        samples = [r['sample'] for r in prediction_results[-500:]]  # Last 500 predictions
        predictions = [r['prediction'] for r in prediction_results[-500:]]
        actuals = [r['actual'] for r in prediction_results[-500:]]
        
        ax3.scatter(actuals, predictions, alpha=0.6, s=20)
        ax3.plot([min(actuals), max(actuals)], [min(actuals), max(actuals)], 'r--', linewidth=2)
        ax3.set_title('Prediction vs Actual (Recent 500)')
        ax3.set_xlabel('Actual Returns')
        ax3.set_ylabel('Predicted Returns')
        ax3.grid(True, alpha=0.3)
        
        # Calculate and display R²
        r2 = np.corrcoef(actuals, predictions)[0, 1] ** 2
        ax3.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax3.transAxes, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Model version performance comparison
    ax4 = axes[1, 1]
    if retrainer.model_versions:
        versions = [v.version for v in retrainer.model_versions]
        version_r2 = [v.performance.r2_score for v in retrainer.model_versions]
        version_sharpe = [v.performance.sharpe_ratio for v in retrainer.model_versions]
        
        x_pos = np.arange(len(versions))
        width = 0.35
        
        bars1 = ax4.bar(x_pos - width/2, version_r2, width, label='R² Score', alpha=0.7)
        bars2 = ax4.bar(x_pos + width/2, version_sharpe, width, label='Sharpe Ratio', alpha=0.7)
        
        ax4.set_title('Model Version Performance')
        ax4.set_ylabel('Score')
        ax4.set_xlabel('Model Version')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels([v.split('_')[0] for v in versions], rotation=45)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dynamic_model_retraining_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def main():
    """Run dynamic model retraining demonstration."""
    
    print("🔄 Dynamic Model Retraining and Continuous Learning System")
    print("=" * 80)
    print("Addressing Static Model Limitations with Adaptive Retraining")
    print("=" * 80)
    
    # Run demonstration
    retrainer, prediction_results = demonstrate_dynamic_retraining()
    
    # Create analysis visualization
    print(f"\n📈 Creating comprehensive analysis visualization...")
    create_retraining_analysis_plot(retrainer, prediction_results)
    
    # Summary and recommendations
    print(f"\n🎯 Key Findings and Recommendations:")
    print("=" * 60)
    print("✅ DYNAMIC Model Management:")
    print("   • Automatic retraining based on performance degradation")
    print("   • Data drift detection and regime change adaptation")
    print("   • Continuous performance monitoring and evaluation")
    print("   • Version control and model lifecycle management")
    
    print(f"\n✅ Adaptive Learning Features:")
    print("   • Real-time performance monitoring with degradation alerts")
    print("   • Statistical drift detection using KS tests")
    print("   • Market regime detection based on volatility and trends")
    print("   • Configurable retraining triggers and thresholds")
    
    print(f"\n📊 System Performance:")
    if retrainer.retraining_events:
        avg_improvement = np.mean([e.improvement for e in retrainer.retraining_events if e.success])
        print(f"   • Average Retraining Improvement: {avg_improvement:+.2%}")
        print(f"   • Total Retraining Events: {len(retrainer.retraining_events)}")
        print(f"   • Successful Retrainings: {sum(1 for e in retrainer.retraining_events if e.success)}")
    
    if retrainer.performance_monitor.performance_history:
        performances = retrainer.performance_monitor.performance_history
        print(f"   • Performance Tracking: {len(performances)} data points")
        print(f"   • R² Improvement: {performances[0].r2_score:.4f} → {performances[-1].r2_score:.4f}")
    
    print(f"\n🎉 Dynamic Model Retraining Demo Complete!")
    print("🚀 Your trading models now adapt automatically to changing market conditions!")

if __name__ == "__main__":
    main() 