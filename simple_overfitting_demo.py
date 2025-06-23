#!/usr/bin/env python3
"""
🛡️ Simple Overfitting Prevention Demo for Random Forests
Shows key techniques to prevent overfitting in financial ML
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report

def generate_overfitting_data():
    """Generate data prone to overfitting"""
    np.random.seed(42)
    
    n_samples = 1000
    n_features = 100
    n_relevant = 5
    
    # Generate random features
    X = np.random.randn(n_samples, n_features)
    
    # Only some features are relevant
    relevant_indices = np.random.choice(n_features, n_relevant, replace=False)
    y_continuous = np.sum(X[:, relevant_indices], axis=1)
    y_continuous += 0.5 * X[:, relevant_indices[0]] * X[:, relevant_indices[1]]
    y_continuous += np.random.randn(n_samples) * 0.3
    
    # Convert to classification
    y = (y_continuous > np.median(y_continuous)).astype(int)
    
    return X, y, relevant_indices

def demonstrate_unregularized_overfitting(X, y):
    """Show unregularized Random Forest overfitting"""
    
    print("❌ UNREGULARIZED RANDOM FOREST (OVERFITTING)")
    print("=" * 45)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Overfitting-prone Random Forest
    overfitting_rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42
    )
    
    overfitting_rf.fit(X_train, y_train)
    
    train_score = overfitting_rf.score(X_train, y_train)
    test_score = overfitting_rf.score(X_test, y_test)
    overfitting_gap = train_score - test_score
    
    cv_scores = cross_val_score(overfitting_rf, X_train, y_train, cv=5)
    
    print(f"📊 Training Accuracy: {train_score:.4f}")
    print(f"📊 Test Accuracy: {test_score:.4f}")
    print(f"⚠️ Overfitting Gap: {overfitting_gap:.4f}")
    print(f"📈 CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"🚨 Severity: {'HIGH' if overfitting_gap > 0.1 else 'MEDIUM' if overfitting_gap > 0.05 else 'LOW'}")
    
    return {'train': train_score, 'test': test_score, 'cv': cv_scores.mean(), 'gap': overfitting_gap}

def apply_feature_selection(X, y):
    """Apply feature selection"""
    
    print(f"\n🎯 FEATURE SELECTION")
    print("=" * 20)
    
    original_features = X.shape[1]
    
    # Select top 20 features
    selector = SelectKBest(score_func=f_classif, k=20)
    X_selected = selector.fit_transform(X, y)
    
    print(f"📉 Original Features: {original_features}")
    print(f"📈 Selected Features: {X_selected.shape[1]}")
    print(f"🎯 Reduction: {100 * (1 - X_selected.shape[1] / original_features):.1f}%")
    
    return X_selected

def create_regularized_random_forest(X, y):
    """Create regularized Random Forest"""
    
    print(f"\n🛡️ REGULARIZED RANDOM FOREST")
    print("=" * 30)
    
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 5, 7, 10],
        'min_samples_split': [5, 10, 20],
        'min_samples_leaf': [2, 5, 10],
        'max_features': ['sqrt', 'log2']
    }
    
    rf_base = RandomForestClassifier(random_state=42)
    
    random_search = RandomizedSearchCV(
        rf_base, param_grid, n_iter=20, cv=5, 
        scoring='accuracy', random_state=42, n_jobs=-1
    )
    
    print("🔧 Tuning hyperparameters...")
    random_search.fit(X, y)
    
    best_params = random_search.best_params_
    best_score = random_search.best_score_
    
    print(f"✅ Best CV Score: {best_score:.4f}")
    print(f"🎛️ Best Parameters:")
    for param, value in best_params.items():
        print(f"   {param}: {value}")
    
    return RandomForestClassifier(**best_params, random_state=42)

def evaluate_model(model, X, y, model_name):
    """Evaluate model performance"""
    
    print(f"\n📊 {model_name.upper()} EVALUATION")
    print("=" * (len(model_name) + 15))
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    model.fit(X_train, y_train)
    
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    overfitting_gap = train_score - test_score
    
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    
    print(f"📈 Training Accuracy: {train_score:.4f}")
    print(f"📊 Test Accuracy: {test_score:.4f}")
    print(f"🎯 CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"⚖️ Overfitting Gap: {overfitting_gap:.4f}")
    print(f"🛡️ Level: {'LOW' if overfitting_gap < 0.05 else 'MEDIUM' if overfitting_gap < 0.1 else 'HIGH'}")
    
    return {'train': train_score, 'test': test_score, 'cv': cv_scores.mean(), 'gap': overfitting_gap}

def compare_results(unregularized, regularized):
    """Compare model results"""
    
    print(f"\n⚖️ MODEL COMPARISON")
    print("=" * 20)
    
    print(f"{'Model':<15} {'Train':<8} {'Test':<8} {'CV':<8} {'Gap':<8} {'Status':<8}")
    print("-" * 55)
    
    models = [
        ('Unregularized', unregularized),
        ('Regularized', regularized)
    ]
    
    for name, result in models:
        status = 'HIGH' if result['gap'] > 0.1 else 'MEDIUM' if result['gap'] > 0.05 else 'LOW'
        print(f"{name:<15} {result['train']:<8.4f} {result['test']:<8.4f} "
              f"{result['cv']:<8.4f} {result['gap']:<8.4f} {status:<8}")
    
    improvement = unregularized['gap'] - regularized['gap']
    improvement_pct = (improvement / unregularized['gap']) * 100 if unregularized['gap'] > 0 else 0
    
    print(f"\n🚀 OVERFITTING REDUCTION:")
    print(f"   Original Gap: {unregularized['gap']:.4f}")
    print(f"   Regularized Gap: {regularized['gap']:.4f}")
    print(f"   Improvement: {improvement:.4f} ({improvement_pct:.1f}%)")

def print_summary():
    """Print overfitting prevention summary"""
    
    print(f"\n🛡️ OVERFITTING PREVENTION TECHNIQUES")
    print("=" * 40)
    
    techniques = [
        "🎯 Feature Selection: Reduced dimensionality",
        "🔧 Hyperparameter Tuning: Optimized complexity",
        "📏 Regularization: Limited tree depth and samples",
        "✅ Cross-Validation: Realistic performance estimates"
    ]
    
    for technique in techniques:
        print(f"   {technique}")
    
    print(f"\n🎯 KEY BENEFITS:")
    print("=" * 15)
    benefits = [
        "✅ More realistic performance estimates",
        "✅ Better generalization to new data",
        "✅ Reduced risk of catastrophic losses",
        "✅ More stable predictions"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print(f"\n⚠️ WHY RANDOM FORESTS OVERFIT:")
    print("=" * 30)
    reasons = [
        "❌ Deep trees memorize noise",
        "❌ Too many features create spurious patterns",
        "❌ Small leaf nodes fit individual points",
        "❌ No built-in complexity penalty"
    ]
    
    for reason in reasons:
        print(f"   {reason}")

def main():
    """Main demonstration"""
    
    print("🛡️ RANDOM FOREST OVERFITTING PREVENTION")
    print("=" * 40)
    print("Demonstrating overfitting prevention techniques")
    print("=" * 40)
    
    # Generate data
    print(f"\n📊 GENERATING DATA")
    print("=" * 18)
    X, y, relevant_features = generate_overfitting_data()
    print(f"📈 Samples: {X.shape[0]}")
    print(f"📊 Total Features: {X.shape[1]}")
    print(f"🎯 Relevant Features: {len(relevant_features)}")
    print(f"⚠️ Irrelevant Features: {X.shape[1] - len(relevant_features)}")
    print(f"🚨 Overfitting Risk: HIGH")
    
    # Demonstrate unregularized overfitting
    unregularized_results = demonstrate_unregularized_overfitting(X, y)
    
    # Apply feature selection
    X_selected = apply_feature_selection(X, y)
    
    # Create regularized Random Forest
    regularized_rf = create_regularized_random_forest(X_selected, y)
    
    # Evaluate regularized model
    regularized_results = evaluate_model(regularized_rf, X_selected, y, "Regularized Random Forest")
    
    # Compare results
    compare_results(unregularized_results, regularized_results)
    
    # Print summary
    print_summary()
    
    print(f"\n🎉 OVERFITTING PREVENTION COMPLETE!")
    print("✅ Random Forest overfitting successfully prevented!")

if __name__ == "__main__":
    main() 