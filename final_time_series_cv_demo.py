#!/usr/bin/env python3
"""
🎯 Final Time Series Cross-Validation Demonstration
Complete replacement of naive train_test_split with proper time series validation
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

class TimeSeriesValidator:
    """
    Proper time series cross-validation system
    Replaces dangerous naive train_test_split
    """
    
    def __init__(self):
        self.results = {}
    
    def naive_split_wrong(self, X, y, test_size=0.3):
        """Naive approach - WRONG for time series!"""
        
        print("🚨 NAIVE TRAIN_TEST_SPLIT (DANGEROUS!)")
        print("=" * 50)
        
        # This shuffles data - WRONG for time series!
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=True, random_state=42
        )
        
        print(f"   ❌ Training samples: {len(X_train)}")
        print(f"   ❌ Test samples: {len(X_test)}")
        print(f"   ❌ PROBLEM: Uses FUTURE data to predict PAST!")
        
        # Train model
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        y_pred = model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        
        print(f"   ❌ Train R²: {train_score:.4f}")
        print(f"   ❌ Test R²: {test_score:.4f}")
        print(f"   ❌ Test MSE: {mse:.6f}")
        print(f"   ❌ WARNING: These results are MISLEADING!")
        
        return {
            'method': 'naive_split',
            'train_r2': train_score,
            'test_r2': test_score,
            'test_mse': mse,
            'predictions': y_pred,
            'actuals': y_test
        }
    
    def walk_forward_validation_correct(self, X, y, dates=None):
        """Walk-forward validation - CORRECT for time series"""
        
        print(f"\n✅ WALK-FORWARD VALIDATION (CORRECT!)")
        print("=" * 50)
        
        n_samples = len(X)
        min_train_size = max(50, int(n_samples * 0.4))  # Start with 40%
        test_size = max(10, int(n_samples * 0.1))       # Test on 10%
        step_size = max(5, int(n_samples * 0.05))       # Step by 5%
        
        print(f"   ✅ Total samples: {n_samples}")
        print(f"   ✅ Min training size: {min_train_size}")
        print(f"   ✅ Test size per fold: {test_size}")
        print(f"   ✅ Step size: {step_size}")
        
        fold_scores = []
        all_predictions = []
        all_actuals = []
        fold_details = []
        
        fold = 0
        
        while True:
            # Expanding training window
            train_start = 0
            train_end = min_train_size + fold * step_size
            
            # Test window (always after training)
            test_start = train_end
            test_end = min(test_start + test_size, n_samples)
            
            # Check bounds
            if test_end > n_samples or train_end >= n_samples:
                break
            
            if test_end - test_start < 5:  # Need at least 5 test samples
                break
            
            # Extract data (preserving temporal order)
            X_train = X[train_start:train_end]
            y_train = y[train_start:train_end]
            X_test = X[test_start:test_end]
            y_test = y[test_start:test_end]
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train on PAST data only
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Predict FUTURE data
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            fold_r2 = r2_score(y_test, y_pred)
            fold_mse = mean_squared_error(y_test, y_pred)
            
            # Directional accuracy
            direction_true = np.sign(y_test)
            direction_pred = np.sign(y_pred)
            directional_acc = np.mean(direction_true == direction_pred)
            
            fold_scores.append(fold_r2)
            all_predictions.extend(y_pred)
            all_actuals.extend(y_test)
            
            fold_info = {
                'fold': fold + 1,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'r2': fold_r2,
                'mse': fold_mse,
                'directional_accuracy': directional_acc
            }
            
            if dates is not None:
                fold_info.update({
                    'train_start': dates[train_start],
                    'train_end': dates[train_end-1],
                    'test_start': dates[test_start],
                    'test_end': dates[test_end-1]
                })
                print(f"   Fold {fold+1}: {dates[test_start].strftime('%Y-%m-%d')} to {dates[test_end-1].strftime('%Y-%m-%d')}")
            else:
                print(f"   Fold {fold+1}: Samples {test_start} to {test_end-1}")
            
            print(f"            R² = {fold_r2:.4f}, Dir Acc = {directional_acc:.3f}")
            
            fold_details.append(fold_info)
            fold += 1
        
        # Overall metrics
        overall_r2 = r2_score(all_actuals, all_predictions)
        overall_mse = mean_squared_error(all_actuals, all_predictions)
        mean_r2 = np.mean(fold_scores)
        std_r2 = np.std(fold_scores)
        
        print(f"\n   ✅ Walk-Forward Summary:")
        print(f"   ✅ Number of folds: {len(fold_scores)}")
        print(f"   ✅ Mean R²: {mean_r2:.4f} ± {std_r2:.4f}")
        print(f"   ✅ Overall R²: {overall_r2:.4f}")
        print(f"   ✅ Overall MSE: {overall_mse:.6f}")
        print(f"   ✅ ADVANTAGE: Never uses future data!")
        
        return {
            'method': 'walk_forward',
            'n_folds': len(fold_scores),
            'mean_r2': mean_r2,
            'std_r2': std_r2,
            'overall_r2': overall_r2,
            'overall_mse': overall_mse,
            'fold_scores': fold_scores,
            'fold_details': fold_details,
            'predictions': all_predictions,
            'actuals': all_actuals
        }
    
    def time_series_split_correct(self, X, y, dates=None, train_ratio=0.7):
        """Simple time series split - also correct"""
        
        print(f"\n✅ TIME SERIES SPLIT (ALSO CORRECT!)")
        print("=" * 45)
        
        split_point = int(len(X) * train_ratio)
        
        X_train = X[:split_point]
        y_train = y[:split_point]
        X_test = X[split_point:]
        y_test = y[split_point:]
        
        if dates is not None:
            print(f"   ✅ Train: {dates[0].strftime('%Y-%m-%d')} to {dates[split_point-1].strftime('%Y-%m-%d')}")
            print(f"   ✅ Test:  {dates[split_point].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
        
        print(f"   ✅ Train samples: {len(X_train)}")
        print(f"   ✅ Test samples: {len(X_test)}")
        
        # Scale and train
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_r2 = model.score(X_train_scaled, y_train)
        test_r2 = model.score(X_test_scaled, y_test)
        test_mse = mean_squared_error(y_test, model.predict(X_test_scaled))
        
        print(f"   ✅ Train R²: {train_r2:.4f}")
        print(f"   ✅ Test R²: {test_r2:.4f}")
        print(f"   ✅ Test MSE: {test_mse:.6f}")
        
        return {
            'method': 'time_series_split',
            'train_r2': train_r2,
            'test_r2': test_r2,
            'test_mse': test_mse
        }
    
    def compare_models_with_proper_cv(self, X, y, dates=None):
        """Compare multiple models using proper time series CV"""
        
        print(f"\n🏆 MODEL COMPARISON WITH PROPER TIME SERIES CV")
        print("=" * 60)
        
        models = {
            'Random Forest': RandomForestRegressor(n_estimators=50, random_state=42),
            'Gradient Boosting': GradientBoostingRegressor(n_estimators=50, random_state=42),
            'Ridge Regression': Ridge(alpha=1.0, random_state=42)
        }
        
        results = {}
        
        for model_name, model in models.items():
            print(f"\n--- {model_name} ---")
            
            # Walk-forward validation for each model
            n_samples = len(X)
            min_train_size = max(50, int(n_samples * 0.4))
            test_size = max(10, int(n_samples * 0.1))
            step_size = max(5, int(n_samples * 0.05))
            
            fold_scores = []
            fold = 0
            
            while True:
                train_end = min_train_size + fold * step_size
                test_start = train_end
                test_end = min(test_start + test_size, n_samples)
                
                if test_end > n_samples or test_end - test_start < 5:
                    break
                
                X_train = X[0:train_end]
                y_train = y[0:train_end]
                X_test = X[test_start:test_end]
                y_test = y[test_start:test_end]
                
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                
                fold_r2 = r2_score(y_test, y_pred)
                fold_scores.append(fold_r2)
                
                fold += 1
            
            mean_r2 = np.mean(fold_scores)
            std_r2 = np.std(fold_scores)
            
            results[model_name] = {
                'mean_r2': mean_r2,
                'std_r2': std_r2,
                'n_folds': len(fold_scores)
            }
            
            print(f"   Mean R²: {mean_r2:.4f} ± {std_r2:.4f} ({len(fold_scores)} folds)")
        
        # Find best model
        best_model = max(results.keys(), key=lambda x: results[x]['mean_r2'])
        
        print(f"\n🏆 BEST MODEL: {best_model}")
        print(f"   Performance: {results[best_model]['mean_r2']:.4f} ± {results[best_model]['std_r2']:.4f}")
        
        return results

def generate_financial_time_series(n_samples=600):
    """Generate realistic financial time series data"""
    
    np.random.seed(42)
    
    # Create dates
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='1D')
    
    # Generate features with temporal correlation
    n_features = 10
    X = np.random.randn(n_samples, n_features)
    
    # Add temporal dependencies (like real financial data)
    for i in range(1, n_samples):
        X[i] = 0.7 * X[i-1] + 0.3 * X[i]
    
    # Generate target with trend and regime changes
    y = np.zeros(n_samples)
    
    # Regime 1: First third - upward trend
    regime1_end = n_samples // 3
    y[:regime1_end] = (
        1.5 * X[:regime1_end, 0] + 
        0.8 * X[:regime1_end, 1] + 
        np.linspace(0, 2, regime1_end) +  # Upward trend
        np.random.randn(regime1_end) * 0.1
    )
    
    # Regime 2: Middle third - sideways with volatility
    regime2_start = regime1_end
    regime2_end = 2 * n_samples // 3
    regime2_length = regime2_end - regime2_start
    y[regime2_start:regime2_end] = (
        0.5 * X[regime2_start:regime2_end, 0] + 
        -0.3 * X[regime2_start:regime2_end, 1] + 
        np.sin(np.linspace(0, 4*np.pi, regime2_length)) +  # Cyclical
        np.random.randn(regime2_length) * 0.2
    )
    
    # Regime 3: Last third - downward trend
    regime3_start = regime2_end
    regime3_length = n_samples - regime3_start
    y[regime3_start:] = (
        -1.2 * X[regime3_start:, 0] + 
        -0.6 * X[regime3_start:, 1] + 
        np.linspace(2, -1, regime3_length) +  # Downward trend
        np.random.randn(regime3_length) * 0.15
    )
    
    return X, y, dates

def demonstrate_look_ahead_bias():
    """Demonstrate the danger of look-ahead bias"""
    
    print(f"\n🔍 DEMONSTRATING LOOK-AHEAD BIAS DANGER")
    print("=" * 50)
    
    # Create data with clear regime change
    n_samples = 400
    X = np.random.randn(n_samples, 5)
    
    # First half: positive relationship
    # Second half: negative relationship (market crash scenario)
    y = np.zeros(n_samples)
    y[:200] = 2 * X[:200, 0] + X[:200, 1] + np.random.randn(200) * 0.1
    y[200:] = -2 * X[200:, 0] - X[200:, 1] + np.random.randn(200) * 0.1
    
    print("   📊 Scenario: Market regime change at midpoint")
    print("      • First half: Bull market (positive relationships)")
    print("      • Second half: Bear market (negative relationships)")
    
    # Naive split (dangerous)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True)
    model_naive = RandomForestRegressor(n_estimators=50, random_state=42)
    model_naive.fit(X_train, y_train)
    naive_score = model_naive.score(X_test, y_test)
    
    # Time series split (realistic)
    split_point = int(0.7 * n_samples)
    X_train_ts = X[:split_point]
    y_train_ts = y[:split_point]
    X_test_ts = X[split_point:]
    y_test_ts = y[split_point:]
    
    model_ts = RandomForestRegressor(n_estimators=50, random_state=42)
    model_ts.fit(X_train_ts, y_train_ts)
    ts_score = model_ts.score(X_test_ts, y_test_ts)
    
    print(f"\n   📊 Results:")
    print(f"      ❌ Naive split R²: {naive_score:.4f} (MISLEADING)")
    print(f"      ✅ Time series R²: {ts_score:.4f} (REALISTIC)")
    print(f"      🚨 Difference: {naive_score - ts_score:.4f}")
    
    if ts_score != 0:
        bias_pct = ((naive_score / abs(ts_score) - 1) * 100)
        print(f"      🚨 Naive approach is {abs(bias_pct):.1f}% off from reality!")
    
    print(f"\n   💡 Why this matters:")
    print("      • Naive split: Model sees BOTH regimes during training")
    print("      • Time series: Model only sees bull market, fails in bear market")
    print("      • Real trading: You can't use future data to predict past!")

def main():
    """Main demonstration of time series cross-validation"""
    
    print("🚨 TIME SERIES CROSS-VALIDATION: CRITICAL FOR FINANCIAL ML")
    print("=" * 70)
    print("Replacing dangerous train_test_split with proper validation")
    print("=" * 70)
    
    # Generate realistic financial data
    X, y, dates = generate_financial_time_series(n_samples=500)
    
    print(f"📊 Generated realistic financial dataset:")
    print(f"   • {len(X)} daily observations")
    print(f"   • {X.shape[1]} features")
    print(f"   • 3 market regimes (bull → sideways → bear)")
    print(f"   • Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    
    # Initialize validator
    validator = TimeSeriesValidator()
    
    # 1. Show naive approach (WRONG)
    naive_results = validator.naive_split_wrong(X, y)
    
    # 2. Show walk-forward validation (CORRECT)
    wf_results = validator.walk_forward_validation_correct(X, y, dates)
    
    # 3. Show simple time series split (ALSO CORRECT)
    ts_results = validator.time_series_split_correct(X, y, dates)
    
    # 4. Compare multiple models with proper CV
    model_comparison = validator.compare_models_with_proper_cv(X, y, dates)
    
    # 5. Demonstrate look-ahead bias
    demonstrate_look_ahead_bias()
    
    # Final comparison
    print(f"\n📊 FINAL PERFORMANCE COMPARISON")
    print("=" * 50)
    print(f"❌ Naive Split R²:        {naive_results['test_r2']:.4f} (MISLEADING)")
    print(f"✅ Walk-Forward R²:       {wf_results['mean_r2']:.4f} ± {wf_results['std_r2']:.4f}")
    print(f"✅ Time Series Split R²:  {ts_results['test_r2']:.4f}")
    
    # Calculate bias
    naive_score = naive_results['test_r2']
    realistic_score = wf_results['mean_r2']
    bias = naive_score - realistic_score
    
    print(f"\n🚨 OPTIMISM BIAS:")
    print(f"   Naive split advantage: {bias:.4f} R² points")
    if realistic_score > 0:
        bias_pct = (bias / realistic_score) * 100
        print(f"   Relative bias: {bias_pct:.1f}%")
    
    print(f"\n⚠️ CRITICAL TRADING IMPLICATIONS:")
    print("=" * 40)
    print("• Naive split creates FALSE CONFIDENCE")
    print("• Real trading performance will be WORSE")
    print("• Look-ahead bias leads to catastrophic losses")
    print("• Proper CV prevents costly mistakes")
    print("• Walk-forward simulates real retraining")
    
    print(f"\n✅ TIME SERIES CV BEST PRACTICES:")
    print("=" * 40)
    print("1. ❌ NEVER use train_test_split with shuffle=True")
    print("2. ✅ ALWAYS train on past, test on future")
    print("3. ✅ Use walk-forward or expanding window validation")
    print("4. ✅ Include gaps between train/test periods")
    print("5. ✅ Test multiple models with proper CV")
    print("6. ✅ Report performance variance over time")
    print("7. ✅ Consider regime changes and market conditions")
    print("8. ✅ Validate on multiple time periods")
    
    print(f"\n🎯 CONCLUSION:")
    print("Time series cross-validation is MANDATORY for financial ML!")
    print("It's the difference between profit and catastrophic loss!")
    
    return {
        'naive': naive_results,
        'walk_forward': wf_results,
        'time_series': ts_results,
        'model_comparison': model_comparison
    }

if __name__ == "__main__":
    results = main() 