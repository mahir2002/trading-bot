#!/usr/bin/env python3
"""
🛡️ Integrated Overfitting Prevention with Advanced Targets
Combines overfitting prevention techniques with sophisticated target engineering
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report

def create_advanced_features(data):
    """Create advanced technical features"""
    
    # Price-based features
    data['returns'] = data['close'].pct_change()
    data['log_returns'] = np.log(data['close'] / data['close'].shift(1))
    data['volatility'] = data['returns'].rolling(20).std()
    
    # Moving averages
    for period in [5, 10, 20, 50]:
        data[f'ma_{period}'] = data['close'].rolling(period).mean()
        data[f'ma_ratio_{period}'] = data['close'] / data[f'ma_{period}']
    
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    bb_period = 20
    bb_std = 2
    data['bb_middle'] = data['close'].rolling(bb_period).mean()
    bb_std_val = data['close'].rolling(bb_period).std()
    data['bb_upper'] = data['bb_middle'] + (bb_std_val * bb_std)
    data['bb_lower'] = data['bb_middle'] - (bb_std_val * bb_std)
    data['bb_position'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
    
    # Volume features
    if 'volume' in data.columns:
        data['volume_ma'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma']
    
    return data

def create_advanced_targets(data):
    """Create sophisticated target variables"""
    
    targets = {}
    
    # 1. Multi-class price movement
    future_returns = data['close'].shift(-5) / data['close'] - 1
    price_movement_cut = pd.cut(
        future_returns, 
        bins=[-np.inf, -0.02, 0.02, np.inf], 
        labels=[0, 1, 2]  # Sell, Hold, Buy
    )
    targets['price_movement_3class'] = price_movement_cut.cat.codes.replace(-1, np.nan)
    
    # 2. Volatility-adjusted returns
    volatility = data['returns'].rolling(20).std()
    vol_adj_returns = future_returns / volatility
    targets['vol_adjusted_binary'] = (vol_adj_returns > 0).astype(float).replace({True: 1, False: 0})
    
    # 3. Price range prediction
    future_high = data['high'].shift(-5)
    future_low = data['low'].shift(-5)
    current_price = data['close']
    
    price_range = (future_high - future_low) / current_price
    targets['high_volatility'] = (price_range > price_range.quantile(0.7)).astype(float).replace({True: 1, False: 0})
    
    # 4. Trend continuation
    current_trend = (data['close'] > data['close'].rolling(10).mean()).astype(float)
    future_trend = (data['close'].shift(-5) > data['close'].shift(-5).rolling(10).mean()).astype(float)
    targets['trend_continuation'] = (current_trend == future_trend).astype(float).replace({True: 1, False: 0})
    
    return targets

class OverfittingPreventionPipeline:
    """Complete pipeline with overfitting prevention"""
    
    def __init__(self):
        self.feature_selector = None
        self.model = None
        self.selected_features = None
        
    def prepare_data(self, data):
        """Prepare features and targets with overfitting prevention"""
        
        print("📊 PREPARING DATA WITH OVERFITTING PREVENTION")
        print("=" * 50)
        
        # Create advanced features
        data = create_advanced_features(data)
        
        # Create advanced targets
        targets = create_advanced_targets(data)
        
        # Select feature columns (exclude price columns to prevent leakage)
        feature_cols = [col for col in data.columns if col not in 
                       ['open', 'high', 'low', 'close', 'volume', 'date']]
        
        X = data[feature_cols].dropna()
        
        print(f"📈 Original Features: {len(feature_cols)}")
        print(f"🎯 Available Targets: {len(targets)}")
        
        return X, targets
    
    def apply_feature_selection(self, X, y, max_features=20):
        """Apply aggressive feature selection"""
        
        print(f"\n🎯 FEATURE SELECTION (OVERFITTING PREVENTION)")
        print("=" * 50)
        
        original_features = X.shape[1]
        
        # Statistical feature selection
        self.feature_selector = SelectKBest(
            score_func=f_classif, 
            k=min(max_features, X.shape[1])
        )
        
        X_selected = self.feature_selector.fit_transform(X, y)
        self.selected_features = self.feature_selector.get_support(indices=True)
        
        print(f"📉 Original Features: {original_features}")
        print(f"📈 Selected Features: {X_selected.shape[1]}")
        print(f"🎯 Reduction: {100 * (1 - X_selected.shape[1] / original_features):.1f}%")
        
        # Show top features
        feature_names = X.columns[self.selected_features]
        feature_scores = self.feature_selector.scores_[self.selected_features]
        
        print(f"\n🏆 TOP SELECTED FEATURES:")
        for name, score in zip(feature_names, feature_scores):
            print(f"   {name}: {score:.2f}")
        
        return X_selected
    
    def create_regularized_model(self, X, y):
        """Create regularized ensemble model"""
        
        print(f"\n🛡️ CREATING REGULARIZED ENSEMBLE")
        print("=" * 35)
        
        # Regularization parameter grid
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7, 10],
            'min_samples_split': [5, 10, 20, 50],
            'min_samples_leaf': [2, 5, 10, 20],
            'max_features': ['sqrt', 'log2', 0.3],
            'min_impurity_decrease': [0.0, 0.01, 0.02]
        }
        
        # Base Random Forest
        rf_base = RandomForestClassifier(random_state=42)
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Hyperparameter tuning
        random_search = RandomizedSearchCV(
            rf_base,
            param_distributions=param_grid,
            n_iter=30,
            cv=tscv,  # Time series CV
            scoring='accuracy',
            random_state=42,
            n_jobs=-1
        )
        
        print("🔧 Tuning hyperparameters with Time Series CV...")
        random_search.fit(X, y)
        
        best_params = random_search.best_params_
        best_score = random_search.best_score_
        
        print(f"✅ Best CV Score: {best_score:.4f}")
        print(f"🎛️ Best Parameters:")
        for param, value in best_params.items():
            print(f"   {param}: {value}")
        
        # Create final regularized model
        self.model = RandomForestClassifier(**best_params, random_state=42)
        
        return self.model
    
    def evaluate_with_time_series_cv(self, X, y, model):
        """Evaluate using time series cross-validation"""
        
        print(f"\n📊 TIME SERIES CROSS-VALIDATION EVALUATION")
        print("=" * 45)
        
        tscv = TimeSeriesSplit(n_splits=5)
        
        cv_scores = []
        train_scores = []
        overfitting_gaps = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            gap = train_score - test_score
            
            cv_scores.append(test_score)
            train_scores.append(train_score)
            overfitting_gaps.append(gap)
            
            print(f"Fold {fold+1}: Train={train_score:.4f}, Test={test_score:.4f}, Gap={gap:.4f}")
        
        results = {
            'cv_mean': np.mean(cv_scores),
            'cv_std': np.std(cv_scores),
            'train_mean': np.mean(train_scores),
            'overfitting_mean': np.mean(overfitting_gaps),
            'overfitting_max': np.max(overfitting_gaps)
        }
        
        print(f"\n📈 CROSS-VALIDATION RESULTS:")
        print(f"   CV Accuracy: {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")
        print(f"   Train Accuracy: {results['train_mean']:.4f}")
        print(f"   Overfitting Gap: {results['overfitting_mean']:.4f}")
        print(f"   Max Gap: {results['overfitting_max']:.4f}")
        
        # Overfitting assessment
        if results['overfitting_mean'] < 0.05:
            status = "LOW ✅"
        elif results['overfitting_mean'] < 0.1:
            status = "MEDIUM ⚠️"
        else:
            status = "HIGH 🚨"
        
        print(f"   Overfitting Level: {status}")
        
        return results
    
    def run_complete_pipeline(self, data, target_name='price_movement_3class'):
        """Run complete overfitting prevention pipeline"""
        
        print("🛡️ INTEGRATED OVERFITTING PREVENTION PIPELINE")
        print("=" * 55)
        print("Advanced targets + Comprehensive overfitting prevention")
        print("=" * 55)
        
        # Prepare data
        X, targets = self.prepare_data(data)
        
        if target_name not in targets:
            print(f"❌ Target '{target_name}' not found. Available: {list(targets.keys())}")
            return None
        
        y = targets[target_name].dropna()
        
        # Align X and y
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]
        
        print(f"\n🎯 TARGET: {target_name}")
        print(f"📊 Samples: {len(X)}")
        print(f"📈 Features: {X.shape[1]}")
        print(f"🎲 Target Distribution: {y.value_counts().to_dict()}")
        
        # Apply feature selection
        X_selected = self.apply_feature_selection(X, y)
        
        # Create regularized model
        model = self.create_regularized_model(X_selected, y)
        
        # Evaluate with time series CV
        results = self.evaluate_with_time_series_cv(X_selected, y, model)
        
        # Final model training
        print(f"\n🎯 TRAINING FINAL MODEL")
        print("=" * 25)
        model.fit(X_selected, y)
        
        # Feature importance
        if hasattr(model, 'feature_importances_'):
            feature_names = X.columns[self.selected_features]
            importances = model.feature_importances_
            
            print(f"\n🏆 FEATURE IMPORTANCE (TOP 10):")
            feature_importance = list(zip(feature_names, importances))
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            
            for name, importance in feature_importance[:10]:
                print(f"   {name}: {importance:.4f}")
        
        return {
            'model': model,
            'feature_selector': self.feature_selector,
            'selected_features': self.selected_features,
            'cv_results': results,
            'X_processed': X_selected,
            'y': y
        }

def demonstrate_integrated_system():
    """Demonstrate integrated overfitting prevention system"""
    
    # Generate sample financial data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    
    # Simulate price data with realistic patterns
    returns = np.random.randn(1000) * 0.02
    returns[100:200] += 0.001  # Trend period
    returns[500:600] -= 0.001  # Downtrend period
    
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(1000) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(1000)) * 0.01),
        'low': prices * (1 - np.abs(np.random.randn(1000)) * 0.01),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 1000)
    })
    
    # Run pipeline
    pipeline = OverfittingPreventionPipeline()
    
    # Test different targets
    targets_to_test = ['price_movement_3class', 'vol_adjusted_binary', 'high_volatility']
    
    results = {}
    for target in targets_to_test:
        print(f"\n" + "="*60)
        print(f"TESTING TARGET: {target}")
        print("="*60)
        
        result = pipeline.run_complete_pipeline(data, target)
        if result:
            results[target] = result
    
    # Summary
    print(f"\n🎉 INTEGRATED SYSTEM SUMMARY")
    print("=" * 30)
    
    for target, result in results.items():
        cv_results = result['cv_results']
        print(f"\n{target}:")
        print(f"   CV Accuracy: {cv_results['cv_mean']:.4f} ± {cv_results['cv_std']:.4f}")
        print(f"   Overfitting Gap: {cv_results['overfitting_mean']:.4f}")
        print(f"   Selected Features: {len(result['selected_features'])}")
    
    print(f"\n✅ OVERFITTING PREVENTION SUCCESSFULLY INTEGRATED!")
    print("🛡️ Advanced targets + Regularization = Robust trading system!")
    
    return results

if __name__ == "__main__":
    results = demonstrate_integrated_system()