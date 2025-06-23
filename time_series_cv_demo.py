#!/usr/bin/env python3
"""
🚨 Time Series Cross-Validation vs Naive Split Demonstration
Shows why train_test_split is dangerous for financial data
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

def generate_financial_time_series(n_samples=2000, n_features=15):
    """Generate realistic financial time series with temporal dependencies"""
    
    np.random.seed(42)
    
    # Create dates
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='1H')
    
    # Generate features with strong temporal dependencies (like real financial data)
    X = np.random.randn(n_samples, n_features)
    
    # Add temporal correlation (autoregressive structure)
    for i in range(1, n_samples):
        X[i] = 0.7 * X[i-1] + 0.3 * X[i]  # Strong temporal correlation
    
    # Add trend and seasonality (common in financial data)
    trend = np.linspace(0, 5, n_samples)
    daily_seasonal = 2 * np.sin(2 * np.pi * np.arange(n_samples) / 24)
    weekly_seasonal = 1.5 * np.sin(2 * np.pi * np.arange(n_samples) / (24*7))
    
    # Generate target with complex dependencies
    y = (
        1.5 * X[:, 0] +                    # Linear relationship
        0.8 * X[:, 1] * X[:, 2] +          # Interaction term
        0.6 * np.sin(X[:, 3]) +            # Non-linear relationship
        0.4 * np.cumsum(X[:, 4]) / 100 +   # Cumulative effect
        trend +                            # Long-term trend
        daily_seasonal +                   # Daily pattern
        weekly_seasonal +                  # Weekly pattern
        np.random.randn(n_samples) * 0.3   # Noise
    )
    
    return X, y, dates

def naive_train_test_split_validation(X, y):
    """Standard train_test_split - WRONG for time series!"""
    
    print("🚨 NAIVE TRAIN_TEST_SPLIT (WRONG FOR TIME SERIES)")
    print("=" * 60)
    
    # This is what most people do - but it's WRONG for time series!
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True  # SHUFFLE=TRUE IS THE PROBLEM!
    )
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"❌ Train R²: {train_score:.4f}")
    print(f"❌ Test R²: {test_score:.4f}")
    print(f"❌ Test MSE: {mse:.4f}")
    print(f"❌ Test MAE: {mae:.4f}")
    print(f"❌ PROBLEM: Uses future data to predict past!")
    print(f"❌ PROBLEM: Overly optimistic performance estimates!")
    
    return {
        'train_score': train_score,
        'test_score': test_score,
        'mse': mse,
        'mae': mae,
        'predictions': y_pred,
        'actuals': y_test
    }

def walk_forward_validation(X, y, dates):
    """Walk-forward validation - CORRECT for time series"""
    
    print(f"\n✅ WALK-FORWARD VALIDATION (CORRECT FOR TIME SERIES)")
    print("=" * 60)
    
    n_samples = len(X)
    initial_train_size = int(n_samples * 0.6)  # Start with 60% for training
    step_size = int(n_samples * 0.05)          # Step forward by 5%
    test_size = int(n_samples * 0.1)           # Test on 10%
    
    all_predictions = []
    all_actuals = []
    fold_scores = []
    
    fold = 0
    train_start = 0
    
    while True:
        # Define training window (expanding)
        train_end = initial_train_size + fold * step_size
        
        # Define test window
        test_start = train_end
        test_end = min(test_start + test_size, n_samples)
        
        # Check if we have enough data
        if test_end > n_samples:
            break
        
        # Extract data (NO SHUFFLING - preserves temporal order)
        X_train = X[train_start:train_end]
        y_train = y[train_start:train_end]
        X_test = X[test_start:test_end]
        y_test = y[test_start:test_end]
        
        # Train model on past data only
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Predict future data
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        fold_score = r2_score(y_test, y_pred)
        fold_scores.append(fold_score)
        
        # Store results
        all_predictions.extend(y_pred)
        all_actuals.extend(y_test)
        
        print(f"   Fold {fold+1}: Train period {dates[train_start]} to {dates[train_end-1]}")
        print(f"            Test period {dates[test_start]} to {dates[test_end-1]}")
        print(f"            R² = {fold_score:.4f}")
        
        fold += 1
    
    # Overall metrics
    overall_r2 = r2_score(all_actuals, all_predictions)
    overall_mse = mean_squared_error(all_actuals, all_predictions)
    overall_mae = mean_absolute_error(all_actuals, all_predictions)
    
    print(f"\n✅ Overall Walk-Forward Results:")
    print(f"✅ Mean R²: {np.mean(fold_scores):.4f} ± {np.std(fold_scores):.4f}")
    print(f"✅ Overall R²: {overall_r2:.4f}")
    print(f"✅ Overall MSE: {overall_mse:.4f}")
    print(f"✅ Overall MAE: {overall_mae:.4f}")
    print(f"✅ Number of folds: {fold}")
    print(f"✅ ADVANTAGE: Never uses future data!")
    print(f"✅ ADVANTAGE: Realistic trading simulation!")
    
    return {
        'fold_scores': fold_scores,
        'mean_score': np.mean(fold_scores),
        'std_score': np.std(fold_scores),
        'overall_r2': overall_r2,
        'mse': overall_mse,
        'mae': overall_mae,
        'predictions': all_predictions,
        'actuals': all_actuals,
        'n_folds': fold
    }

def expanding_window_validation(X, y, dates):
    """Expanding window validation - Another correct approach"""
    
    print(f"\n✅ EXPANDING WINDOW VALIDATION")
    print("=" * 50)
    
    n_samples = len(X)
    min_train_size = int(n_samples * 0.3)  # Minimum 30% for training
    test_size = int(n_samples * 0.1)       # Test on 10%
    step_size = int(n_samples * 0.1)       # Expand by 10%
    
    fold_scores = []
    all_predictions = []
    all_actuals = []
    
    fold = 0
    
    while True:
        # Expanding training window (always starts from beginning)
        train_end = min_train_size + fold * step_size
        
        # Test window
        test_start = train_end
        test_end = min(test_start + test_size, n_samples)
        
        if test_end > n_samples:
            break
        
        # Extract data
        X_train = X[0:train_end]  # Always from beginning (expanding)
        y_train = y[0:train_end]
        X_test = X[test_start:test_end]
        y_test = y[test_start:test_end]
        
        # Train and predict
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Metrics
        fold_score = r2_score(y_test, y_pred)
        fold_scores.append(fold_score)
        
        all_predictions.extend(y_pred)
        all_actuals.extend(y_test)
        
        print(f"   Fold {fold+1}: Train size {train_end}, Test R² = {fold_score:.4f}")
        
        fold += 1
    
    overall_r2 = r2_score(all_actuals, all_predictions)
    
    print(f"✅ Expanding Window Mean R²: {np.mean(fold_scores):.4f} ± {np.std(fold_scores):.4f}")
    print(f"✅ Overall R²: {overall_r2:.4f}")
    
    return {
        'fold_scores': fold_scores,
        'mean_score': np.mean(fold_scores),
        'overall_r2': overall_r2,
        'n_folds': fold
    }

def demonstrate_look_ahead_bias():
    """Demonstrate why look-ahead bias is dangerous"""
    
    print(f"\n🔍 DEMONSTRATING LOOK-AHEAD BIAS")
    print("=" * 50)
    
    # Generate data with a clear trend break
    n_samples = 1000
    X = np.random.randn(n_samples, 5)
    
    # First half: upward trend
    # Second half: downward trend (regime change)
    y = np.zeros(n_samples)
    y[:500] = np.linspace(0, 10, 500) + X[:500, 0] + np.random.randn(500) * 0.1
    y[500:] = np.linspace(10, 0, 500) + X[500:, 0] + np.random.randn(500) * 0.1
    
    # Naive split (shuffles data - mixes both regimes)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True)
    
    model_naive = RandomForestRegressor(n_estimators=100, random_state=42)
    model_naive.fit(X_train, y_train)
    naive_score = model_naive.score(X_test, y_test)
    
    # Time series split (respects temporal order)
    split_point = int(0.7 * n_samples)
    X_train_ts = X[:split_point]
    y_train_ts = y[:split_point]
    X_test_ts = X[split_point:]
    y_test_ts = y[split_point:]
    
    model_ts = RandomForestRegressor(n_estimators=100, random_state=42)
    model_ts.fit(X_train_ts, y_train_ts)
    ts_score = model_ts.score(X_test_ts, y_test_ts)
    
    print(f"📊 Regime Change Example:")
    print(f"   Naive split R² (with look-ahead): {naive_score:.4f}")
    print(f"   Time series split R² (realistic): {ts_score:.4f}")
    print(f"   Difference: {naive_score - ts_score:.4f}")
    print(f"   🚨 Naive split is {((naive_score/ts_score - 1) * 100):.1f}% more optimistic!")

def plot_comparison_results(naive_results, wf_results):
    """Plot comparison between naive and walk-forward results"""
    
    try:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Naive Split vs Walk-Forward Validation Comparison', fontsize=16)
        
        # Plot 1: Score comparison
        methods = ['Naive Split\n(WRONG)', 'Walk-Forward\n(CORRECT)']
        scores = [naive_results['test_score'], wf_results['mean_score']]
        colors = ['red', 'green']
        
        bars = axes[0, 0].bar(methods, scores, color=colors, alpha=0.7)
        axes[0, 0].set_title('R² Score Comparison')
        axes[0, 0].set_ylabel('R² Score')
        
        # Add value labels on bars
        for bar, score in zip(bars, scores):
            axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                           f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: Walk-forward scores over time
        axes[0, 1].plot(wf_results['fold_scores'], 'o-', color='green', linewidth=2)
        axes[0, 1].axhline(y=wf_results['mean_score'], color='green', linestyle='--', alpha=0.7)
        axes[0, 1].axhline(y=naive_results['test_score'], color='red', linestyle='--', alpha=0.7, 
                          label=f'Naive Score ({naive_results["test_score"]:.3f})')
        axes[0, 1].set_title('Walk-Forward Performance Over Time')
        axes[0, 1].set_xlabel('Fold')
        axes[0, 1].set_ylabel('R² Score')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Predictions vs Actuals (Naive)
        axes[1, 0].scatter(naive_results['actuals'], naive_results['predictions'], 
                          alpha=0.6, color='red', s=20)
        min_val = min(min(naive_results['actuals']), min(naive_results['predictions']))
        max_val = max(max(naive_results['actuals']), max(naive_results['predictions']))
        axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.8)
        axes[1, 0].set_title('Naive Split: Predictions vs Actuals')
        axes[1, 0].set_xlabel('Actual Values')
        axes[1, 0].set_ylabel('Predicted Values')
        
        # Plot 4: Predictions vs Actuals (Walk-Forward)
        axes[1, 1].scatter(wf_results['actuals'], wf_results['predictions'], 
                          alpha=0.6, color='green', s=20)
        min_val = min(min(wf_results['actuals']), min(wf_results['predictions']))
        max_val = max(max(wf_results['actuals']), max(wf_results['predictions']))
        axes[1, 1].plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.8)
        axes[1, 1].set_title('Walk-Forward: Predictions vs Actuals')
        axes[1, 1].set_xlabel('Actual Values')
        axes[1, 1].set_ylabel('Predicted Values')
        
        plt.tight_layout()
        plt.savefig('time_series_cv_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    except ImportError:
        print("Matplotlib not available for plotting")

def main():
    """Main demonstration"""
    
    print("🚨 TIME SERIES CROSS-VALIDATION vs NAIVE SPLIT")
    print("=" * 70)
    print("Demonstrating why train_test_split is DANGEROUS for financial data")
    print("=" * 70)
    
    # Generate realistic financial time series
    X, y, dates = generate_financial_time_series()
    
    print(f"📊 Generated {len(X)} samples with {X.shape[1]} features")
    print(f"📅 Date range: {dates[0]} to {dates[-1]}")
    
    # 1. Naive approach (WRONG)
    naive_results = naive_train_test_split_validation(X, y)
    
    # 2. Walk-forward validation (CORRECT)
    wf_results = walk_forward_validation(X, y, dates)
    
    # 3. Expanding window validation (ALSO CORRECT)
    ew_results = expanding_window_validation(X, y, dates)
    
    # 4. Demonstrate look-ahead bias
    demonstrate_look_ahead_bias()
    
    # Summary comparison
    print(f"\n📊 FINAL COMPARISON SUMMARY")
    print("=" * 50)
    print(f"❌ Naive Split R²:        {naive_results['test_score']:.4f}")
    print(f"✅ Walk-Forward R²:       {wf_results['mean_score']:.4f} ± {wf_results['std_score']:.4f}")
    print(f"✅ Expanding Window R²:   {ew_results['mean_score']:.4f}")
    
    # Calculate optimism bias
    optimism_bias = naive_results['test_score'] - wf_results['mean_score']
    optimism_pct = (optimism_bias / wf_results['mean_score']) * 100
    
    print(f"\n🚨 OPTIMISM BIAS:")
    print(f"   Naive split is {optimism_bias:.4f} points higher")
    print(f"   That's {optimism_pct:.1f}% more optimistic than reality!")
    
    print(f"\n⚠️ WHY THIS MATTERS FOR TRADING:")
    print("=" * 40)
    print("• Naive split gives FALSE confidence in model performance")
    print("• Real trading performance will be MUCH WORSE than expected")
    print("• Look-ahead bias leads to overfitting to future information")
    print("• Walk-forward validation simulates REAL trading conditions")
    print("• Proper CV prevents costly trading mistakes")
    
    print(f"\n✅ CORRECT TIME SERIES CV PRINCIPLES:")
    print("=" * 45)
    print("1. NEVER shuffle time series data")
    print("2. Always train on PAST data, test on FUTURE data")
    print("3. Use walk-forward or expanding window validation")
    print("4. Include gaps between train/test to prevent leakage")
    print("5. Simulate real-world retraining frequency")
    print("6. Report performance variance across time periods")
    
    # Plot results
    plot_comparison_results(naive_results, wf_results)
    
    print(f"\n🎯 CONCLUSION:")
    print("Time series cross-validation is CRITICAL for financial ML!")
    print("Never use train_test_split with shuffle=True for time series!")

if __name__ == "__main__":
    main() 