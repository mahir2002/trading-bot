#!/usr/bin/env python3
"""
🚨 Robust Time Series Cross-Validation Demonstration
Shows critical differences between naive split and proper time series CV
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

def generate_realistic_financial_data(n_samples=1000, n_features=10):
    """Generate realistic financial time series with temporal dependencies"""
    
    np.random.seed(42)
    
    # Create dates
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='1D')
    
    # Generate features with temporal correlation (like real financial data)
    X = np.random.randn(n_samples, n_features)
    
    # Add strong temporal dependencies
    for i in range(1, n_samples):
        X[i] = 0.6 * X[i-1] + 0.4 * X[i]  # Autoregressive structure
    
    # Create realistic price-like target with trend and volatility clustering
    returns = np.random.randn(n_samples) * 0.02  # Daily returns ~2% volatility
    
    # Add volatility clustering (GARCH-like behavior)
    volatility = np.ones(n_samples) * 0.02
    for i in range(1, n_samples):
        volatility[i] = 0.1 * volatility[i-1] + 0.9 * abs(returns[i-1])
        returns[i] = returns[i] * volatility[i]
    
    # Create price series
    prices = 100 * np.exp(np.cumsum(returns))
    
    # Target is next day's return (common prediction task)
    y = np.zeros(n_samples)
    y[:-1] = returns[1:]  # Next day's return
    y[-1] = returns[-1]   # Handle last observation
    
    # Add feature relationships
    y += (
        0.3 * X[:, 0] +                    # Technical indicator
        0.2 * X[:, 1] * X[:, 2] +          # Interaction
        0.1 * np.tanh(X[:, 3]) +           # Non-linear
        np.random.randn(n_samples) * 0.01  # Noise
    )
    
    return X, y, dates, prices

def naive_validation_wrong(X, y):
    """Naive train_test_split - WRONG for time series!"""
    
    print("🚨 NAIVE TRAIN_TEST_SPLIT (DANGEROUS FOR TIME SERIES)")
    print("=" * 65)
    
    # This shuffles data - mixing past and future!
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, shuffle=True  # SHUFFLE IS THE PROBLEM!
    )
    
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    print(f"   ❌ PROBLEM: Training set contains FUTURE data!")
    print(f"   ❌ PROBLEM: Test set contains PAST data!")
    
    # Train model
    model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    test_mse = mean_squared_error(y_test, test_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    
    print(f"   ❌ Train R²: {train_r2:.4f}")
    print(f"   ❌ Test R²: {test_r2:.4f}")
    print(f"   ❌ Test MSE: {test_mse:.6f}")
    print(f"   ❌ Test MAE: {test_mae:.6f}")
    
    return {
        'method': 'naive_split',
        'train_r2': train_r2,
        'test_r2': test_r2,
        'test_mse': test_mse,
        'test_mae': test_mae,
        'predictions': test_pred,
        'actuals': y_test
    }

def walk_forward_validation_correct(X, y, dates):
    """Walk-forward validation - CORRECT for time series"""
    
    print(f"\n✅ WALK-FORWARD VALIDATION (CORRECT FOR TIME SERIES)")
    print("=" * 65)
    
    n_samples = len(X)
    min_train_size = max(100, int(n_samples * 0.4))  # Minimum training size
    test_size = max(20, int(n_samples * 0.1))        # Test size
    step_size = max(10, int(n_samples * 0.05))       # Step size
    
    print(f"   Minimum training size: {min_train_size}")
    print(f"   Test size per fold: {test_size}")
    print(f"   Step size: {step_size}")
    
    fold_results = []
    all_predictions = []
    all_actuals = []
    
    fold = 0
    
    # Walk forward through time
    while True:
        # Training window (expanding)
        train_start = 0
        train_end = min_train_size + fold * step_size
        
        # Test window (always after training)
        test_start = train_end
        test_end = test_start + test_size
        
        # Check bounds
        if test_end > n_samples:
            break
        
        # Extract data (preserving temporal order)
        X_train = X[train_start:train_end]
        y_train = y[train_start:train_end]
        X_test = X[test_start:test_end]
        y_test = y[test_start:test_end]
        
        # Ensure we have enough data
        if len(X_train) < 10 or len(X_test) < 1:
            break
        
        # Train on PAST data only
        model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
        model.fit(X_train, y_train)
        
        # Predict FUTURE data
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        fold_r2 = r2_score(y_test, y_pred)
        fold_mse = mean_squared_error(y_test, y_pred)
        
        fold_results.append({
            'fold': fold + 1,
            'train_start': dates[train_start],
            'train_end': dates[train_end-1],
            'test_start': dates[test_start],
            'test_end': dates[test_end-1],
            'train_size': len(X_train),
            'test_size': len(X_test),
            'r2': fold_r2,
            'mse': fold_mse
        })
        
        # Store predictions
        all_predictions.extend(y_pred)
        all_actuals.extend(y_test)
        
        print(f"   Fold {fold+1}: Train {dates[train_start].strftime('%Y-%m-%d')} to {dates[train_end-1].strftime('%Y-%m-%d')}")
        print(f"           Test {dates[test_start].strftime('%Y-%m-%d')} to {dates[test_end-1].strftime('%Y-%m-%d')}")
        print(f"           R² = {fold_r2:.4f}, MSE = {fold_mse:.6f}")
        
        fold += 1
    
    # Calculate overall metrics
    overall_r2 = r2_score(all_actuals, all_predictions)
    overall_mse = mean_squared_error(all_actuals, all_predictions)
    overall_mae = mean_absolute_error(all_actuals, all_predictions)
    
    fold_r2_scores = [f['r2'] for f in fold_results]
    mean_r2 = np.mean(fold_r2_scores)
    std_r2 = np.std(fold_r2_scores)
    
    print(f"\n   ✅ Walk-Forward Summary:")
    print(f"   ✅ Number of folds: {len(fold_results)}")
    print(f"   ✅ Mean R²: {mean_r2:.4f} ± {std_r2:.4f}")
    print(f"   ✅ Overall R²: {overall_r2:.4f}")
    print(f"   ✅ Overall MSE: {overall_mse:.6f}")
    print(f"   ✅ Overall MAE: {overall_mae:.6f}")
    print(f"   ✅ ADVANTAGE: Never uses future data!")
    
    return {
        'method': 'walk_forward',
        'fold_results': fold_results,
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'overall_r2': overall_r2,
        'overall_mse': overall_mse,
        'overall_mae': overall_mae,
        'predictions': all_predictions,
        'actuals': all_actuals,
        'n_folds': len(fold_results)
    }

def time_series_split_validation(X, y, dates):
    """Simple time series split - also correct"""
    
    print(f"\n✅ SIMPLE TIME SERIES SPLIT")
    print("=" * 40)
    
    # Split at 70% point (train on first 70%, test on last 30%)
    split_point = int(0.7 * len(X))
    
    X_train = X[:split_point]
    y_train = y[:split_point]
    X_test = X[split_point:]
    y_test = y[split_point:]
    
    print(f"   Train period: {dates[0].strftime('%Y-%m-%d')} to {dates[split_point-1].strftime('%Y-%m-%d')}")
    print(f"   Test period: {dates[split_point].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    print(f"   Train samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    
    # Train model
    model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    test_mse = mean_squared_error(y_test, test_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    
    print(f"   ✅ Train R²: {train_r2:.4f}")
    print(f"   ✅ Test R²: {test_r2:.4f}")
    print(f"   ✅ Test MSE: {test_mse:.6f}")
    print(f"   ✅ Test MAE: {test_mae:.6f}")
    
    return {
        'method': 'time_series_split',
        'train_r2': train_r2,
        'test_r2': test_r2,
        'test_mse': test_mse,
        'test_mae': test_mae,
        'predictions': test_pred,
        'actuals': y_test
    }

def demonstrate_look_ahead_bias():
    """Show concrete example of look-ahead bias"""
    
    print(f"\n🔍 DEMONSTRATING LOOK-AHEAD BIAS WITH REGIME CHANGE")
    print("=" * 60)
    
    # Create data with clear regime change
    n_samples = 600
    X = np.random.randn(n_samples, 5)
    
    # Regime 1 (first 300): Strong positive relationship
    # Regime 2 (last 300): Strong negative relationship
    y = np.zeros(n_samples)
    y[:300] = 2 * X[:300, 0] + X[:300, 1] + np.random.randn(300) * 0.1  # Positive regime
    y[300:] = -2 * X[300:, 0] - X[300:, 1] + np.random.randn(300) * 0.1  # Negative regime
    
    print("   📊 Data structure:")
    print("      • First 300 samples: Positive relationship (y = 2*X₀ + X₁)")
    print("      • Last 300 samples: Negative relationship (y = -2*X₀ - X₁)")
    print("      • This simulates a market regime change")
    
    # Naive split (mixes both regimes)
    X_train_naive, X_test_naive, y_train_naive, y_test_naive = train_test_split(
        X, y, test_size=0.3, shuffle=True, random_state=42
    )
    
    model_naive = RandomForestRegressor(n_estimators=50, random_state=42)
    model_naive.fit(X_train_naive, y_train_naive)
    naive_score = model_naive.score(X_test_naive, y_test_naive)
    
    # Time series split (respects temporal order)
    split_point = int(0.7 * n_samples)  # Split at 420 (in regime 2)
    X_train_ts = X[:split_point]
    y_train_ts = y[:split_point]
    X_test_ts = X[split_point:]
    y_test_ts = y[split_point:]
    
    model_ts = RandomForestRegressor(n_estimators=50, random_state=42)
    model_ts.fit(X_train_ts, y_train_ts)
    ts_score = model_ts.score(X_test_ts, y_test_ts)
    
    print(f"\n   📊 Results:")
    print(f"      ❌ Naive split R² (with look-ahead): {naive_score:.4f}")
    print(f"      ✅ Time series split R² (realistic): {ts_score:.4f}")
    print(f"      🚨 Difference: {naive_score - ts_score:.4f}")
    
    if ts_score > 0:
        optimism_pct = ((naive_score / ts_score - 1) * 100)
        print(f"      🚨 Naive split is {optimism_pct:.1f}% more optimistic!")
    else:
        print(f"      🚨 Naive split gives false confidence in a failing model!")
    
    print(f"\n   🔍 Why this happens:")
    print("      • Naive split: Training set contains samples from BOTH regimes")
    print("      • Model learns BOTH positive and negative relationships")
    print("      • Test set also contains BOTH regimes, so model performs well")
    print("      • Time series split: Model trained only on regime 1")
    print("      • When regime changes, model fails (realistic scenario)")

def main():
    """Main demonstration"""
    
    print("🚨 TIME SERIES CROSS-VALIDATION: CRITICAL FOR FINANCIAL ML")
    print("=" * 70)
    print("Why train_test_split is DANGEROUS for financial time series data")
    print("=" * 70)
    
    # Generate realistic financial data
    X, y, dates, prices = generate_realistic_financial_data(n_samples=800)
    
    print(f"📊 Generated realistic financial dataset:")
    print(f"   • {len(X)} daily observations")
    print(f"   • {X.shape[1]} features (technical indicators)")
    print(f"   • Target: Next day's return")
    print(f"   • Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    print(f"   • Price range: ${prices.min():.2f} to ${prices.max():.2f}")
    
    # 1. Naive approach (WRONG)
    naive_results = naive_validation_wrong(X, y)
    
    # 2. Walk-forward validation (CORRECT)
    wf_results = walk_forward_validation_correct(X, y, dates)
    
    # 3. Simple time series split (ALSO CORRECT)
    ts_results = time_series_split_validation(X, y, dates)
    
    # 4. Demonstrate look-ahead bias
    demonstrate_look_ahead_bias()
    
    # Final comparison
    print(f"\n📊 FINAL PERFORMANCE COMPARISON")
    print("=" * 50)
    print(f"❌ Naive Split R²:           {naive_results['test_r2']:.4f}")
    print(f"✅ Walk-Forward Mean R²:     {wf_results['mean_r2']:.4f} ± {wf_results['std_r2']:.4f}")
    print(f"✅ Simple Time Series R²:   {ts_results['test_r2']:.4f}")
    
    # Calculate bias
    naive_score = naive_results['test_r2']
    realistic_score = wf_results['mean_r2']
    
    if realistic_score > 0:
        bias = naive_score - realistic_score
        bias_pct = (bias / abs(realistic_score)) * 100
        
        print(f"\n🚨 OPTIMISM BIAS ANALYSIS:")
        print(f"   • Naive split advantage: {bias:.4f} R² points")
        print(f"   • Relative bias: {bias_pct:.1f}%")
        
        if bias > 0.1:
            print(f"   • ⚠️ SEVERE BIAS: Naive split is dangerously optimistic!")
        elif bias > 0.05:
            print(f"   • ⚠️ MODERATE BIAS: Significant overestimation of performance")
        else:
            print(f"   • ✅ LOW BIAS: Results are reasonably consistent")
    
    print(f"\n⚠️ CRITICAL IMPLICATIONS FOR TRADING:")
    print("=" * 45)
    print("• Naive split creates FALSE CONFIDENCE in model performance")
    print("• Real trading results will be MUCH WORSE than expected")
    print("• Look-ahead bias leads to catastrophic overfitting")
    print("• Proper time series CV prevents costly trading mistakes")
    print("• Walk-forward validation simulates REAL retraining scenarios")
    
    print(f"\n✅ TIME SERIES CV BEST PRACTICES:")
    print("=" * 40)
    print("1. ❌ NEVER use train_test_split with shuffle=True")
    print("2. ✅ ALWAYS train on past, test on future")
    print("3. ✅ Use walk-forward or expanding window validation")
    print("4. ✅ Include gaps between train/test sets")
    print("5. ✅ Simulate realistic retraining frequency")
    print("6. ✅ Report performance variance over time")
    print("7. ✅ Test on multiple time periods")
    print("8. ✅ Consider regime changes and market conditions")
    
    print(f"\n🎯 CONCLUSION:")
    print("Time series cross-validation is MANDATORY for financial ML!")
    print("The difference between profit and loss in trading!")
    
    return {
        'naive': naive_results,
        'walk_forward': wf_results,
        'time_series': ts_results
    }

if __name__ == "__main__":
    results = main() 