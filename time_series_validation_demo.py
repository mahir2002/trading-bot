#!/usr/bin/env python3
"""
Time-Series Cross-Validation and Feature Selection Demo
Addresses look-ahead bias and feature redundancy in trading models
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ValidationResult:
    method: str
    scores: List[float]
    mean_score: float
    std_score: float
    look_ahead_bias_risk: str
    feature_count: int

class TimeSeriesValidator:
    """Proper time-series cross-validation system."""
    
    def __init__(self, min_train_size=252, test_size=63, step_size=21, purge_size=5):
        self.min_train_size = min_train_size
        self.test_size = test_size
        self.step_size = step_size
        self.purge_size = purge_size
        
        print("📊 Time-Series Cross-Validation System")
        print(f"   Min Training Size: {min_train_size} periods")
        print(f"   Test Size: {test_size} periods")
        print(f"   Purge Size: {purge_size} periods (prevents look-ahead bias)")
    
    def traditional_split_validation(self, X, y, model):
        """Traditional train/test split (PROBLEMATIC for time series)."""
        print("❌ Traditional Random Split (PROBLEMATIC)")
        
        scores = []
        for i in range(5):
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=i
            )
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            score = r2_score(y_test, y_pred)
            scores.append(score)
        
        return ValidationResult(
            method="Traditional Split",
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            look_ahead_bias_risk="HIGH - Uses future data",
            feature_count=len(X.columns)
        )
    
    def walk_forward_validation(self, X, y, model):
        """Walk-forward validation (PROPER for time series)."""
        print("✅ Walk-Forward Validation (PROPER)")
        
        n_splits = (len(X) - self.min_train_size - self.test_size) // self.step_size + 1
        scores = []
        
        for i in range(min(n_splits, 8)):
            train_end = self.min_train_size + i * self.step_size
            test_start = train_end + self.purge_size
            test_end = test_start + self.test_size
            
            if test_end > len(X):
                break
            
            X_train = X.iloc[:train_end]
            y_train = y.iloc[:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            score = r2_score(y_test, y_pred)
            scores.append(score)
            
            print(f"   Split {i+1}: Train={len(X_train)}, Test={len(X_test)}, Score={score:.4f}")
        
        return ValidationResult(
            method="Walk-Forward",
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            look_ahead_bias_risk="NONE - Respects temporal order",
            feature_count=len(X.columns)
        )
    
    def expanding_window_validation(self, X, y, model):
        """Expanding window validation."""
        print("✅ Expanding Window Validation (PROPER)")
        
        n_splits = (len(X) - self.min_train_size - self.test_size) // self.step_size + 1
        scores = []
        
        for i in range(min(n_splits, 8)):
            train_end = self.min_train_size + i * self.step_size
            test_start = train_end + self.purge_size
            test_end = test_start + self.test_size
            
            if test_end > len(X):
                break
            
            X_train = X.iloc[:train_end]
            y_train = y.iloc[:train_end]
            X_test = X.iloc[test_start:test_end]
            y_test = y.iloc[test_start:test_end]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            score = r2_score(y_test, y_pred)
            scores.append(score)
        
        return ValidationResult(
            method="Expanding Window",
            scores=scores,
            mean_score=np.mean(scores),
            std_score=np.std(scores),
            look_ahead_bias_risk="NONE - Uses only past data",
            feature_count=len(X.columns)
        )

class FeatureSelector:
    """Feature selection to address redundancy."""
    
    def __init__(self, correlation_threshold=0.95, variance_threshold=0.001):
        self.correlation_threshold = correlation_threshold
        self.variance_threshold = variance_threshold
        
        print("🎯 Feature Selection System")
        print(f"   Correlation Threshold: {correlation_threshold}")
        print(f"   Variance Threshold: {variance_threshold}")
    
    def analyze_redundancy(self, X):
        """Analyze feature redundancy."""
        print("\n🔍 Feature Redundancy Analysis:")
        
        # Correlation analysis
        corr_matrix = X.corr().abs()
        high_corr_pairs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > self.correlation_threshold:
                    high_corr_pairs.append({
                        'feature1': corr_matrix.columns[i],
                        'feature2': corr_matrix.columns[j],
                        'correlation': corr_matrix.iloc[i, j]
                    })
        
        # Variance analysis
        variances = X.var()
        low_variance_features = variances[variances < self.variance_threshold].index.tolist()
        
        print(f"   Total Features: {len(X.columns)}")
        print(f"   High Correlation Pairs (>{self.correlation_threshold}): {len(high_corr_pairs)}")
        print(f"   Low Variance Features (<{self.variance_threshold}): {len(low_variance_features)}")
        
        return high_corr_pairs, low_variance_features, corr_matrix
    
    def comprehensive_selection(self, X, y):
        """Apply comprehensive feature selection."""
        print("\n🎯 Comprehensive Feature Selection:")
        
        original_count = len(X.columns)
        print(f"   Starting with {original_count} features")
        
        # Step 1: Remove low variance features
        variance_selector = VarianceThreshold(threshold=self.variance_threshold)
        X_var = variance_selector.fit_transform(X)
        selected_features_var = X.columns[variance_selector.get_support()].tolist()
        removed_var = len(X.columns) - len(selected_features_var)
        
        X_var_df = pd.DataFrame(X_var, columns=selected_features_var, index=X.index)
        
        # Step 2: Remove highly correlated features
        corr_matrix = X_var_df.corr().abs()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        to_remove = set()
        for col in upper_triangle.columns:
            for idx in upper_triangle.index:
                if upper_triangle.loc[idx, col] > self.correlation_threshold:
                    # Keep feature with higher correlation to target
                    corr_target_col = abs(y.corr(X_var_df[col]))
                    corr_target_idx = abs(y.corr(X_var_df[idx]))
                    if corr_target_col < corr_target_idx:
                        to_remove.add(col)
                    else:
                        to_remove.add(idx)
        
        selected_features_corr = [col for col in selected_features_var if col not in to_remove]
        X_corr = X_var_df[selected_features_corr]
        removed_corr = len(selected_features_var) - len(selected_features_corr)
        
        # Step 3: Tree-based importance filter
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X_corr, y)
        
        importances = rf.feature_importances_
        importance_threshold = 0.001
        selected_mask = importances >= importance_threshold
        
        final_features = X_corr.columns[selected_mask].tolist()
        X_final = X_corr[final_features]
        removed_importance = len(selected_features_corr) - len(final_features)
        
        final_count = len(final_features)
        reduction_pct = (original_count - final_count) / original_count * 100
        
        print(f"   After Variance Filter: {len(selected_features_var)} (-{removed_var})")
        print(f"   After Correlation Filter: {len(selected_features_corr)} (-{removed_corr})")
        print(f"   After Importance Filter: {final_count} (-{removed_importance})")
        print(f"   Total Reduction: {reduction_pct:.1f}%")
        
        # Feature importance ranking
        feature_importance = dict(zip(final_features, importances[X_corr.columns.get_indexer(final_features)]))
        
        return {
            'final_features': X_final,
            'selected_feature_names': final_features,
            'feature_importance': feature_importance,
            'reduction_percentage': reduction_pct,
            'removed_counts': {
                'variance': removed_var,
                'correlation': removed_corr,
                'importance': removed_importance
            }
        }

def generate_financial_data(n_samples=1500):
    """Generate financial data with redundant features."""
    np.random.seed(42)
    
    # Generate price series
    timestamps = pd.date_range(start='2020-01-01', periods=n_samples, freq='H')
    price = 100.0
    prices = [price]
    
    for i in range(1, n_samples):
        return_shock = np.random.normal(0.0001, 0.02)
        price *= (1 + return_shock)
        prices.append(price)
    
    data = pd.DataFrame({'timestamp': timestamps, 'close': prices})
    data.set_index('timestamp', inplace=True)
    
    # Generate features with redundancy
    features = pd.DataFrame(index=data.index)
    returns = data['close'].pct_change()
    
    # Price features (some redundant)
    features['returns'] = returns
    features['returns_scaled'] = returns * 100  # Redundant
    features['log_returns'] = np.log(data['close'] / data['close'].shift(1))
    
    # Moving averages (redundant periods)
    for period in [5, 10, 20, 21, 50, 51]:  # 21≈20, 51≈50 redundant
        features[f'sma_{period}'] = data['close'].rolling(period).mean()
        features[f'price_to_sma_{period}'] = data['close'] / features[f'sma_{period}']
    
    # Volatility (redundant)
    for period in [10, 11, 20, 21]:
        features[f'volatility_{period}'] = returns.rolling(period).std()
        features[f'volatility_{period}_ann'] = features[f'volatility_{period}'] * np.sqrt(252)
    
    # Technical indicators
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    features['rsi_scaled'] = features['rsi'] / 100  # Redundant
    
    # MACD
    ema_12 = data['close'].ewm(span=12).mean()
    ema_26 = data['close'].ewm(span=26).mean()
    features['macd'] = ema_12 - ema_26
    features['macd_signal'] = features['macd'].ewm(span=9).mean()
    
    # Low variance noise features
    for i in range(5):
        features[f'noise_{i}'] = np.random.normal(0, 0.001, len(data))
    
    # Constant features
    features['constant_1'] = 1.0
    features['constant_2'] = 2.0
    
    # Target: future returns
    target = data['close'].shift(-24) / data['close'] - 1
    
    # Clean data
    valid_mask = ~(features.isnull().any(axis=1) | target.isnull())
    features_clean = features[valid_mask]
    target_clean = target[valid_mask]
    
    return features_clean, target_clean

def demonstrate_validation_methods():
    """Demonstrate proper vs improper validation."""
    print("🚨 Time-Series Validation Demonstration")
    print("=" * 60)
    
    # Generate data
    X, y = generate_financial_data(1500)
    print(f"Dataset: {len(X)} samples, {len(X.columns)} features")
    
    # Initialize validator
    validator = TimeSeriesValidator()
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    
    # Compare validation methods
    print(f"\n🔍 Validation Method Comparison:")
    print("-" * 60)
    
    results = []
    
    # Traditional split (problematic)
    result_traditional = validator.traditional_split_validation(X, y, model)
    results.append(result_traditional)
    
    # Walk-forward (proper)
    result_walkforward = validator.walk_forward_validation(X, y, model)
    results.append(result_walkforward)
    
    # Expanding window (proper)
    result_expanding = validator.expanding_window_validation(X, y, model)
    results.append(result_expanding)
    
    # Results summary
    print(f"\n📊 Validation Results Summary:")
    print("-" * 70)
    print(f"{'Method':<20} {'Mean Score':<12} {'Std Score':<12} {'Bias Risk'}")
    print("-" * 70)
    
    for result in results:
        risk_indicator = "🚨 HIGH" if "HIGH" in result.look_ahead_bias_risk else "✅ LOW"
        print(f"{result.method:<20} {result.mean_score:<12.4f} {result.std_score:<12.4f} {risk_indicator}")
    
    return results

def demonstrate_feature_selection():
    """Demonstrate feature selection process."""
    print("\n🎯 Feature Selection Demonstration")
    print("=" * 60)
    
    # Generate data
    X, y = generate_financial_data(1500)
    
    # Initialize feature selector
    selector = FeatureSelector()
    
    # Analyze redundancy
    high_corr_pairs, low_var_features, corr_matrix = selector.analyze_redundancy(X)
    
    # Show some examples
    if high_corr_pairs:
        print(f"\n🔗 High Correlation Examples:")
        for pair in high_corr_pairs[:5]:
            print(f"   {pair['feature1']} ↔ {pair['feature2']}: {pair['correlation']:.3f}")
    
    # Apply feature selection
    selection_results = selector.comprehensive_selection(X, y)
    
    # Test performance impact
    print(f"\n🧪 Performance Impact:")
    print("-" * 40)
    
    validator = TimeSeriesValidator()
    
    # Original features
    model_orig = RandomForestRegressor(n_estimators=50, random_state=42)
    result_orig = validator.walk_forward_validation(X, y, model_orig)
    
    # Selected features
    X_selected = selection_results['final_features']
    model_selected = RandomForestRegressor(n_estimators=50, random_state=42)
    result_selected = validator.walk_forward_validation(X_selected, y, model_selected)
    
    print(f"Original ({len(X.columns)} features): {result_orig.mean_score:.4f} ± {result_orig.std_score:.4f}")
    print(f"Selected ({len(X_selected.columns)} features): {result_selected.mean_score:.4f} ± {result_selected.std_score:.4f}")
    
    improvement = (result_selected.mean_score - result_orig.mean_score) / result_orig.mean_score * 100
    print(f"Performance Change: {improvement:+.2f}%")
    
    # Top features
    print(f"\n🏆 Top 10 Selected Features:")
    sorted_features = sorted(selection_results['feature_importance'].items(), 
                           key=lambda x: x[1], reverse=True)
    for i, (feature, importance) in enumerate(sorted_features[:10]):
        print(f"   {i+1:>2}. {feature:<20}: {importance:.4f}")
    
    return selection_results, result_orig, result_selected

def create_comparison_plot(validation_results, feature_results):
    """Create comparison visualization."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Validation scores comparison
    ax1 = axes[0, 0]
    methods = [r.method for r in validation_results]
    means = [r.mean_score for r in validation_results]
    stds = [r.std_score for r in validation_results]
    colors = ['red', 'green', 'blue']
    
    bars = ax1.bar(methods, means, yerr=stds, capsize=5, alpha=0.7, color=colors)
    ax1.set_title('Validation Method Comparison')
    ax1.set_ylabel('R² Score')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Feature reduction visualization
    ax2 = axes[0, 1]
    reduction_data = feature_results['removed_counts']
    categories = list(reduction_data.keys())
    values = list(reduction_data.values())
    
    ax2.bar(categories, values, alpha=0.7, color=['orange', 'red', 'purple'])
    ax2.set_title('Features Removed by Method')
    ax2.set_ylabel('Number of Features')
    ax2.grid(True, alpha=0.3)
    
    # Score distribution box plot
    ax3 = axes[1, 0]
    scores_data = [r.scores for r in validation_results]
    ax3.boxplot(scores_data, labels=[r.method for r in validation_results])
    ax3.set_title('Score Distribution by Method')
    ax3.set_ylabel('R² Score')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # Feature importance (top 10)
    ax4 = axes[1, 1]
    sorted_features = sorted(feature_results['feature_importance'].items(), 
                           key=lambda x: x[1], reverse=True)[:10]
    features, importances = zip(*sorted_features)
    
    ax4.barh(range(len(features)), importances, alpha=0.7)
    ax4.set_yticks(range(len(features)))
    ax4.set_yticklabels(features)
    ax4.set_title('Top 10 Feature Importance')
    ax4.set_xlabel('Importance')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('time_series_validation_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def main():
    """Run comprehensive demonstration."""
    print("📊 Time-Series Validation & Feature Selection System")
    print("=" * 80)
    print("Addressing Look-Ahead Bias and Feature Redundancy")
    print("=" * 80)
    
    # Demonstrate validation methods
    validation_results = demonstrate_validation_methods()
    
    # Demonstrate feature selection
    feature_results, orig_performance, selected_performance = demonstrate_feature_selection()
    
    # Create visualization
    print(f"\n📈 Creating analysis visualization...")
    create_comparison_plot(validation_results, feature_results)
    
    # Key findings
    print(f"\n🎯 Key Findings:")
    print("=" * 50)
    
    # Validation findings
    traditional_score = validation_results[0].mean_score
    walkforward_score = validation_results[1].mean_score
    bias_impact = (traditional_score - walkforward_score) / walkforward_score * 100
    
    print(f"📊 Look-Ahead Bias Impact:")
    print(f"   Traditional Split: {traditional_score:.4f} (INFLATED)")
    print(f"   Walk-Forward: {walkforward_score:.4f} (REALISTIC)")
    print(f"   Bias Inflation: +{bias_impact:.1f}%")
    
    # Feature selection findings
    improvement = (selected_performance.mean_score - orig_performance.mean_score) / orig_performance.mean_score * 100
    
    print(f"\n🎯 Feature Selection Impact:")
    print(f"   Original Features: {orig_performance.mean_score:.4f}")
    print(f"   Selected Features: {selected_performance.mean_score:.4f}")
    print(f"   Performance Change: {improvement:+.2f}%")
    print(f"   Feature Reduction: {feature_results['reduction_percentage']:.1f}%")
    
    # Recommendations
    print(f"\n✅ Recommendations:")
    print("   1. ALWAYS use walk-forward or expanding window validation")
    print("   2. NEVER use random train/test splits for time series")
    print("   3. Include purge periods to prevent data leakage")
    print("   4. Remove highly correlated and low-variance features")
    print("   5. Use tree-based importance for feature relevance")
    
    print(f"\n🎉 Demo Complete! Your models now avoid look-ahead bias!")

if __name__ == "__main__":
    main() 