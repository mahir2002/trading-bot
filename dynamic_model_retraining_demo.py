#!/usr/bin/env python3
"""
Dynamic Model Retraining and Continuous Learning System Demo
Demonstrates how to address static model limitations with adaptive retraining
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import scipy.stats as stats
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time

class RetrainingTrigger(Enum):
    """Triggers for model retraining."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    TIME_BASED = "time_based"
    DATA_DRIFT = "data_drift"
    MARKET_REGIME_CHANGE = "market_regime_change"
    MANUAL = "manual"

@dataclass
class ModelPerformance:
    """Model performance metrics."""
    timestamp: datetime
    r2_score: float
    mse: float
    mae: float
    sharpe_ratio: float
    win_rate: float
    predictions_count: int

@dataclass
class RetrainingEvent:
    """Retraining event record."""
    timestamp: datetime
    trigger: RetrainingTrigger
    improvement: float
    training_time: float
    success: bool

class PerformanceMonitor:
    """Real-time performance monitoring system."""
    
    def __init__(self, window_size=100, degradation_threshold=0.15):
        self.window_size = window_size
        self.degradation_threshold = degradation_threshold
        
        self.recent_predictions = []
        self.recent_actuals = []
        self.performance_history = []
        self.baseline_performance = None
        
        print("📊 Performance Monitor Initialized")
        print(f"   Window Size: {window_size} predictions")
        print(f"   Degradation Threshold: {degradation_threshold:.1%}")
    
    def update_performance(self, y_true: float, y_pred: float):
        """Update performance with new prediction."""
        
        self.recent_predictions.append(y_pred)
        self.recent_actuals.append(y_true)
        
        # Maintain window size
        if len(self.recent_predictions) > self.window_size:
            self.recent_predictions.pop(0)
            self.recent_actuals.pop(0)
        
        # Calculate performance if enough data
        if len(self.recent_predictions) >= 50:
            current_performance = self._calculate_performance()
            self.performance_history.append(current_performance)
            
            if self.baseline_performance is None:
                self.baseline_performance = current_performance
                print(f"📈 Baseline Performance Set: R² = {current_performance.r2_score:.4f}")
            
            return current_performance
        
        return None
    
    def _calculate_performance(self) -> ModelPerformance:
        """Calculate current performance metrics."""
        
        y_true = np.array(self.recent_actuals)
        y_pred = np.array(self.recent_predictions)
        
        # Basic metrics
        r2 = r2_score(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        
        # Trading metrics
        returns = y_pred
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        win_rate = np.mean(y_pred * y_true > 0) if len(y_true) > 0 else 0
        
        return ModelPerformance(
            timestamp=datetime.now(),
            r2_score=r2,
            mse=mse,
            mae=mae,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            predictions_count=len(self.recent_predictions)
        )
    
    def check_degradation(self) -> bool:
        """Check if performance has degraded significantly."""
        
        if (self.baseline_performance is None or len(self.performance_history) < 5):
            return False
        
        current_performance = self.performance_history[-1]
        
        # Check R² degradation
        r2_degradation = (self.baseline_performance.r2_score - current_performance.r2_score) / abs(self.baseline_performance.r2_score)
        
        # Check Sharpe degradation
        sharpe_degradation = (self.baseline_performance.sharpe_ratio - current_performance.sharpe_ratio) / abs(self.baseline_performance.sharpe_ratio) if self.baseline_performance.sharpe_ratio != 0 else 0
        
        degraded = (r2_degradation > self.degradation_threshold or
                   sharpe_degradation > self.degradation_threshold)
        
        if degraded:
            print(f"🚨 Performance Degradation Detected!")
            print(f"   R² Degradation: {r2_degradation:.2%}")
            print(f"   Sharpe Degradation: {sharpe_degradation:.2%}")
        
        return degraded

class DataDriftDetector:
    """Detect changes in data distribution."""
    
    def __init__(self, drift_threshold=0.05):
        self.drift_threshold = drift_threshold
        self.reference_data = None
        self.recent_data = []
        
        print("🔍 Data Drift Detector Initialized")
        print(f"   Drift Threshold: {drift_threshold}")
    
    def set_reference_distribution(self, X: pd.DataFrame):
        """Set reference distribution for drift detection."""
        self.reference_data = X.copy()
        print(f"📊 Reference Distribution Set: {len(X)} samples")
    
    def update_recent_data(self, X: pd.DataFrame):
        """Update recent data window."""
        self.recent_data.append(X)
        
        # Keep last 500 batches
        if len(self.recent_data) > 500:
            self.recent_data.pop(0)
    
    def detect_drift(self) -> Tuple[bool, Dict[str, float]]:
        """Detect data drift using statistical tests."""
        
        if (self.reference_data is None or len(self.recent_data) < 10):
            return False, {}
        
        recent_df = pd.concat(self.recent_data, ignore_index=True)
        drift_scores = {}
        significant_drift = False
        
        # Test each feature for drift
        for column in self.reference_data.columns:
            if column in recent_df.columns:
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
        
        return significant_drift, drift_scores

class MarketRegimeDetector:
    """Detect changes in market regime."""
    
    def __init__(self, volatility_threshold=2.0):
        self.volatility_threshold = volatility_threshold
        self.current_regime = None
        self.price_history = []
        
        print("🌊 Market Regime Detector Initialized")
        print(f"   Volatility Threshold: {volatility_threshold}")
    
    def update_market_data(self, price: float):
        """Update market data for regime detection."""
        
        self.price_history.append(price)
        
        # Keep last 252 prices (roughly 1 year of daily data)
        if len(self.price_history) > 252:
            self.price_history.pop(0)
        
        if len(self.price_history) >= 50:
            new_regime = self._detect_current_regime()
            
            if new_regime != self.current_regime:
                print(f"🌊 Market Regime Change: {self.current_regime} → {new_regime}")
                self.current_regime = new_regime
                return True
        
        return False
    
    def _detect_current_regime(self) -> str:
        """Detect current market regime."""
        
        prices = np.array(self.price_history)
        returns = np.diff(prices) / prices[:-1]
        
        recent_volatility = np.std(returns[-50:]) if len(returns) >= 50 else np.std(returns)
        long_term_volatility = np.std(returns)
        recent_trend = np.mean(returns[-20:]) if len(returns) >= 20 else np.mean(returns)
        
        if recent_volatility > self.volatility_threshold * long_term_volatility:
            if recent_trend > 0.001:
                return "VOLATILE_BULL"
            elif recent_trend < -0.001:
                return "VOLATILE_BEAR"
            else:
                return "HIGH_VOLATILITY"
        else:
            if recent_trend > 0.001:
                return "STABLE_BULL"
            elif recent_trend < -0.001:
                return "STABLE_BEAR"
            else:
                return "SIDEWAYS"

class DynamicModelRetrainer:
    """Dynamic model retraining and continuous learning system."""
    
    def __init__(self,
                 model_class=RandomForestRegressor,
                 model_params=None,
                 min_training_samples=500):
        
        self.model_class = model_class
        self.model_params = model_params or {'n_estimators': 50, 'random_state': 42}
        self.min_training_samples = min_training_samples
        
        # Components
        self.performance_monitor = PerformanceMonitor()
        self.drift_detector = DataDriftDetector()
        self.regime_detector = MarketRegimeDetector()
        
        # Model management
        self.current_model = None
        self.training_data = pd.DataFrame()
        self.target_data = pd.Series()
        self.last_retrain_time = None
        
        # Events
        self.retraining_events = []
        self.is_training = False
        
        print("🔄 Dynamic Model Retrainer Initialized")
        print(f"   Model Class: {model_class.__name__}")
        print(f"   Min Training Samples: {min_training_samples}")
    
    def initialize_model(self, X: pd.DataFrame, y: pd.Series) -> bool:
        """Initialize the first model."""
        
        print("🚀 Initializing First Model...")
        
        if len(X) < self.min_training_samples:
            print(f"❌ Insufficient training data: {len(X)} < {self.min_training_samples}")
            return False
        
        self.training_data = X.copy()
        self.target_data = y.copy()
        
        self.drift_detector.set_reference_distribution(X)
        
        success = self._train_model(X, y)
        
        if success:
            self.last_retrain_time = datetime.now()
            print("✅ Initial Model Training Complete")
        
        return success
    
    def update_with_new_data(self, X_new: pd.DataFrame, y_new: pd.Series):
        """Update system with new data."""
        
        self.training_data = pd.concat([self.training_data, X_new], ignore_index=True)
        self.target_data = pd.concat([self.target_data, y_new], ignore_index=True)
        
        self.drift_detector.update_recent_data(X_new)
        
        # Update regime detector if price data available
        if 'close' in X_new.columns:
            for price in X_new['close']:
                regime_change = self.regime_detector.update_market_data(price)
                if regime_change:
                    self._trigger_retraining(RetrainingTrigger.MARKET_REGIME_CHANGE)
        
        # Trim old data (keep last 3000 samples)
        if len(self.training_data) > 3000:
            self.training_data = self.training_data.tail(3000)
            self.target_data = self.target_data.tail(3000)
        
        self._check_retraining_triggers()
    
    def make_prediction(self, X: pd.DataFrame) -> np.ndarray:
        """Make prediction with current model."""
        
        if self.current_model is None:
            raise ValueError("No trained model available")
        
        return self.current_model.predict(X)
    
    def update_performance(self, y_true: float, y_pred: float):
        """Update performance monitoring."""
        
        current_performance = self.performance_monitor.update_performance(y_true, y_pred)
        
        if (current_performance and self.performance_monitor.check_degradation()):
            self._trigger_retraining(RetrainingTrigger.PERFORMANCE_DEGRADATION)
    
    def _check_retraining_triggers(self):
        """Check all retraining triggers."""
        
        if self.is_training:
            return
        
        # Data drift trigger
        drift_detected, _ = self.drift_detector.detect_drift()
        if drift_detected:
            self._trigger_retraining(RetrainingTrigger.DATA_DRIFT)
    
    def _trigger_retraining(self, trigger: RetrainingTrigger):
        """Trigger model retraining."""
        
        if self.is_training:
            print(f"⏳ Retraining in progress, skipping {trigger.value}")
            return
        
        print(f"🔄 Triggering Retraining: {trigger.value}")
        self._retrain_model_sync(trigger)
    
    def _retrain_model_sync(self, trigger: RetrainingTrigger):
        """Synchronously retrain the model."""
        
        self.is_training = True
        start_time = time.time()
        
        try:
            old_performance = (self.performance_monitor.performance_history[-1].r2_score 
                             if self.performance_monitor.performance_history 
                             else 0.0)
            
            success = self._train_model(self.training_data, self.target_data)
            training_time = time.time() - start_time
            
            if success:
                new_performance = self._evaluate_model_performance()
                improvement = (new_performance - old_performance) / abs(old_performance) if old_performance != 0 else 0
                
                event = RetrainingEvent(
                    timestamp=datetime.now(),
                    trigger=trigger,
                    improvement=improvement,
                    training_time=training_time,
                    success=True
                )
                
                self.retraining_events.append(event)
                self.last_retrain_time = datetime.now()
                
                # Update baseline
                if self.performance_monitor.performance_history:
                    self.performance_monitor.baseline_performance = self.performance_monitor.performance_history[-1]
                
                print(f"✅ Retraining Complete: {improvement:+.2%} improvement")
            
        except Exception as e:
            print(f"❌ Retraining Failed: {str(e)}")
            
            event = RetrainingEvent(
                timestamp=datetime.now(),
                trigger=trigger,
                improvement=0.0,
                training_time=time.time() - start_time,
                success=False
            )
            self.retraining_events.append(event)
        
        finally:
            self.is_training = False
    
    def _train_model(self, X: pd.DataFrame, y: pd.Series) -> bool:
        """Train a new model."""
        
        try:
            print(f"🎯 Training Model: {len(X)} samples, {len(X.columns)} features")
            
            model = self.model_class(**self.model_params)
            model.fit(X, y)
            
            self.current_model = model
            
            performance = self._calculate_model_performance(model, X, y)
            print(f"✅ Model Trained - R²: {performance.r2_score:.4f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model Training Failed: {str(e)}")
            return False
    
    def _calculate_model_performance(self, model, X: pd.DataFrame, y: pd.Series) -> ModelPerformance:
        """Calculate model performance."""
        
        y_pred = model.predict(X)
        
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        
        returns = y_pred
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        win_rate = np.mean(y_pred * y > 0) if len(y) > 0 else 0
        
        return ModelPerformance(
            timestamp=datetime.now(),
            r2_score=r2,
            mse=mse,
            mae=mae,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            predictions_count=len(y)
        )
    
    def _evaluate_model_performance(self) -> float:
        """Evaluate current model performance."""
        
        if len(self.training_data) > 500:
            X_eval = self.training_data.tail(500)
            y_eval = self.target_data.tail(500)
        else:
            X_eval = self.training_data
            y_eval = self.target_data
        
        performance = self._calculate_model_performance(self.current_model, X_eval, y_eval)
        return performance.r2_score
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status."""
        
        current_performance = (self.performance_monitor.performance_history[-1] 
                             if self.performance_monitor.performance_history 
                             else None)
        
        return {
            'training_data_size': len(self.training_data),
            'is_training': self.is_training,
            'last_retrain_time': self.last_retrain_time,
            'current_performance': current_performance,
            'total_retraining_events': len(self.retraining_events),
            'current_regime': self.regime_detector.current_regime,
            'baseline_r2': self.performance_monitor.baseline_performance.r2_score if self.performance_monitor.baseline_performance else None,
            'current_r2': current_performance.r2_score if current_performance else None
        }

def generate_dynamic_market_data(n_samples=1500):
    """Generate market data with regime changes."""
    
    np.random.seed(42)
    
    timestamps = pd.date_range(start='2020-01-01', periods=n_samples, freq='H')
    
    # Generate price with regime changes
    price = 100.0
    prices = [price]
    regime_changes = [400, 800, 1200]
    
    for i in range(1, n_samples):
        # Different volatility regimes
        if i < regime_changes[0]:
            volatility = 0.01
            drift = 0.0001
        elif i < regime_changes[1]:
            volatility = 0.03
            drift = -0.0002
        elif i < regime_changes[2]:
            volatility = 0.015
            drift = 0.0003
        else:
            volatility = 0.025
            drift = -0.0001
        
        return_shock = np.random.normal(drift, volatility)
        price *= (1 + return_shock)
        prices.append(price)
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'close': prices
    })
    data.set_index('timestamp', inplace=True)
    
    # Generate features
    features = pd.DataFrame(index=data.index)
    returns = data['close'].pct_change()
    
    features['returns'] = returns
    features['volatility_20'] = returns.rolling(20).std()
    features['sma_50'] = data['close'].rolling(50).mean()
    features['close'] = data['close']  # For regime detection
    
    # Features that drift over time
    for i, idx in enumerate(data.index):
        time_factor = i / len(data)
        features.loc[idx, 'drifting_feature'] = np.random.normal(0.5 + time_factor, 0.1)
    
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = data['close'].ewm(span=12).mean()
    ema_26 = data['close'].ewm(span=26).mean()
    features['macd'] = ema_12 - ema_26
    
    # Target: future returns
    target = data['close'].shift(-24) / data['close'] - 1
    
    # Clean data
    valid_mask = ~(features.isnull().any(axis=1) | target.isnull())
    features_clean = features[valid_mask]
    target_clean = target[valid_mask]
    
    return features_clean, target_clean

def demonstrate_dynamic_retraining():
    """Demonstrate dynamic model retraining."""
    
    print("🔄 Dynamic Model Retraining System Demonstration")
    print("=" * 70)
    
    # Generate data
    print("📊 Generating Dynamic Market Data...")
    X, y = generate_dynamic_market_data(1500)
    print(f"   Generated {len(X)} samples with {len(X.columns)} features")
    print(f"   Data includes regime changes and feature drift")
    
    # Initialize retrainer
    retrainer = DynamicModelRetrainer(
        model_class=RandomForestRegressor,
        model_params={'n_estimators': 50, 'random_state': 42},
        min_training_samples=400
    )
    
    # Initial training
    initial_size = 600
    X_initial = X.iloc[:initial_size]
    y_initial = y.iloc[:initial_size]
    
    print(f"\n🚀 Initializing Model...")
    success = retrainer.initialize_model(X_initial, y_initial)
    
    if not success:
        print("❌ Failed to initialize model")
        return
    
    # Simulate live trading
    print(f"\n📈 Simulating Live Trading...")
    
    batch_size = 50
    prediction_results = []
    
    for i in range(initial_size, len(X), batch_size):
        end_idx = min(i + batch_size, len(X))
        X_batch = X.iloc[i:end_idx]
        y_batch = y.iloc[i:end_idx]
        
        print(f"\n📊 Batch {i//batch_size + 1}: Samples {i}-{end_idx}")
        
        try:
            # Make predictions
            predictions = retrainer.make_prediction(X_batch)
            
            # Update performance
            for pred, actual in zip(predictions, y_batch.values):
                retrainer.update_performance(actual, pred)
                prediction_results.append({
                    'prediction': pred,
                    'actual': actual
                })
            
            # Update with new data
            retrainer.update_with_new_data(X_batch, y_batch)
            
            # Show status
            if (i // batch_size + 1) % 4 == 0:
                status = retrainer.get_system_status()
                print(f"   📊 Status: Data={status['training_data_size']}, "
                      f"Events={status['total_retraining_events']}, "
                      f"Regime={status['current_regime']}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            continue
    
    # Final analysis
    print(f"\n📊 Final Analysis:")
    print("=" * 40)
    
    status = retrainer.get_system_status()
    print(f"📈 System Status:")
    print(f"   Training Data: {status['training_data_size']} samples")
    print(f"   Retraining Events: {status['total_retraining_events']}")
    print(f"   Current Regime: {status['current_regime']}")
    
    if retrainer.performance_monitor.performance_history:
        performances = retrainer.performance_monitor.performance_history
        print(f"\n📊 Performance Evolution:")
        print(f"   Initial R²: {performances[0].r2_score:.4f}")
        print(f"   Final R²: {performances[-1].r2_score:.4f}")
        print(f"   Best R²: {max(p.r2_score for p in performances):.4f}")
        print(f"   Performance Tracking Points: {len(performances)}")
    
    if retrainer.retraining_events:
        print(f"\n🔄 Retraining Events:")
        for i, event in enumerate(retrainer.retraining_events):
            print(f"   Event {i+1}: {event.trigger.value} "
                  f"({event.improvement:+.2%}, {event.training_time:.1f}s)")
    
    # Create simple visualization
    create_performance_plot(retrainer, prediction_results)
    
    return retrainer, prediction_results

def create_performance_plot(retrainer, prediction_results):
    """Create performance visualization."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Performance evolution
    ax1 = axes[0, 0]
    if retrainer.performance_monitor.performance_history:
        performances = retrainer.performance_monitor.performance_history
        r2_scores = [p.r2_score for p in performances]
        
        ax1.plot(r2_scores, linewidth=2, color='blue')
        ax1.set_title('Model Performance Evolution')
        ax1.set_ylabel('R² Score')
        ax1.set_xlabel('Performance Update')
        ax1.grid(True, alpha=0.3)
    
    # Retraining events
    ax2 = axes[0, 1]
    if retrainer.retraining_events:
        events = retrainer.retraining_events
        improvements = [e.improvement * 100 for e in events]
        colors = ['green' if e.success else 'red' for e in events]
        
        ax2.bar(range(len(events)), improvements, color=colors, alpha=0.7)
        ax2.set_title('Retraining Improvements')
        ax2.set_ylabel('Performance Improvement (%)')
        ax2.set_xlabel('Retraining Event')
        ax2.grid(True, alpha=0.3)
    
    # Prediction accuracy
    ax3 = axes[1, 0]
    if prediction_results:
        actuals = [r['actual'] for r in prediction_results[-300:]]
        predictions = [r['prediction'] for r in prediction_results[-300:]]
        
        ax3.scatter(actuals, predictions, alpha=0.6, s=20)
        ax3.plot([min(actuals), max(actuals)], [min(actuals), max(actuals)], 'r--')
        ax3.set_title('Prediction vs Actual (Recent 300)')
        ax3.set_xlabel('Actual Returns')
        ax3.set_ylabel('Predicted Returns')
        ax3.grid(True, alpha=0.3)
        
        r2 = np.corrcoef(actuals, predictions)[0, 1] ** 2
        ax3.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax3.transAxes,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Performance metrics over time
    ax4 = axes[1, 1]
    if retrainer.performance_monitor.performance_history:
        performances = retrainer.performance_monitor.performance_history
        sharpe_ratios = [p.sharpe_ratio for p in performances]
        win_rates = [p.win_rate for p in performances]
        
        ax4_twin = ax4.twinx()
        
        ax4.plot(sharpe_ratios, 'b-', label='Sharpe Ratio')
        ax4_twin.plot(win_rates, 'r-', label='Win Rate')
        
        ax4.set_title('Trading Metrics Evolution')
        ax4.set_ylabel('Sharpe Ratio', color='blue')
        ax4_twin.set_ylabel('Win Rate', color='red')
        ax4.set_xlabel('Performance Update')
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dynamic_model_retraining_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def main():
    """Run dynamic retraining demonstration."""
    
    print("🔄 Dynamic Model Retraining and Continuous Learning System")
    print("=" * 80)
    print("Addressing Static Model Limitations with Adaptive Retraining")
    print("=" * 80)
    
    # Run demonstration
    retrainer, prediction_results = demonstrate_dynamic_retraining()
    
    # Summary
    print(f"\n🎯 Key Achievements:")
    print("=" * 50)
    print("✅ DYNAMIC Model Management:")
    print("   • Automatic retraining based on performance degradation")
    print("   • Data drift detection and regime change adaptation")
    print("   • Real-time performance monitoring")
    print("   • Continuous model lifecycle management")
    
    print(f"\n📊 System Performance:")
    if retrainer.retraining_events:
        successful_events = [e for e in retrainer.retraining_events if e.success]
        if successful_events:
            avg_improvement = np.mean([e.improvement for e in successful_events])
            print(f"   • Average Improvement: {avg_improvement:+.2%}")
        print(f"   • Total Retraining Events: {len(retrainer.retraining_events)}")
        print(f"   • Successful Retrainings: {len(successful_events)}")
    
    print(f"\n🎉 Dynamic Model Retraining Demo Complete!")
    print("🚀 Your models now adapt automatically to changing markets!")

if __name__ == "__main__":
    main() 