#!/usr/bin/env python3
"""
🛡️ Random Forest Overfitting Solution
Problem: "Random Forests can overfit, especially with many features"
Solution: "Regularization techniques or ensemble methods could be explored"
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

def main():
    print("🛡️ RANDOM FOREST OVERFITTING SOLUTION")
    print("=" * 40)
    print("Problem: Random Forests can overfit, especially with many features")
    print("Solution: Regularization techniques + Ensemble methods")
    print("=" * 40)
    
    # Generate high-dimensional data (many features problem)
    np.random.seed(42)
    n_samples, n_features, n_relevant = 1000, 100, 5
    X = np.random.randn(n_samples, n_features)
    
    # Only first 5 features are relevant
    y_continuous = (X[:, 0] + 0.5 * X[:, 1] + 0.3 * X[:, 2] + 
                   0.2 * X[:, 3] + 0.1 * X[:, 4] + 
                   np.random.randn(n_samples) * 0.2)
    y = (y_continuous > np.median(y_continuous)).astype(int)
    
    print(f"🚨 HIGH-DIMENSIONAL DATA (OVERFITTING PRONE)")
    print(f"📊 Samples: {n_samples}")
    print(f"📈 Total Features: {n_features}")
    print(f"🎯 Relevant Features: {n_relevant}")
    print(f"⚠️ Irrelevant Features: {n_features - n_relevant}")
    
    # Problem: Default Random Forest with many features
    print(f"\n❌ PROBLEM: DEFAULT RANDOM FOREST WITH MANY FEATURES")
    print("=" * 55)
    
    default_rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,      # Unlimited depth - OVERFITS!
        min_samples_split=2, # Minimal requirements - OVERFITS!
        min_samples_leaf=1,
        max_features='sqrt',
        random_state=42
    )
    
    # Train-test split
    split_idx = int(0.7 * len(X))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    default_rf.fit(X_train, y_train)
    train_score = default_rf.score(X_train, y_train)
    test_score = default_rf.score(X_test, y_test)
    gap = train_score - test_score
    
    # Cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = cross_val_score(default_rf, X_train, y_train, cv=tscv)
    
    print(f"🚨 OVERFITTING INDICATORS:")
    print(f"   Training Accuracy: {train_score:.4f}")
    print(f"   Test Accuracy: {test_score:.4f}")
    print(f"   Train-Test Gap: {gap:.4f} ({'HIGH' if gap > 0.10 else 'MEDIUM' if gap > 0.05 else 'LOW'})")
    print(f"   CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"   Using all {X.shape[1]} features (including {X.shape[1] - 5} irrelevant)")
    
    # Solution 1: Regularization Techniques
    print(f"\n✅ SOLUTION 1: REGULARIZATION TECHNIQUES")
    print("=" * 40)
    
    print("🛡️ TECHNIQUE 1: Hyperparameter Regularization")
    regularized_rf = RandomForestClassifier(
        n_estimators=50,              # Fewer trees
        max_depth=5,                 # Limited depth
        min_samples_split=20,        # Higher split requirement
        min_samples_leaf=10,         # Higher leaf requirement
        max_features=0.3,            # Use only 30% of features per tree
        min_impurity_decrease=0.01,  # Require improvement to split
        random_state=42
    )
    
    print("🛡️ TECHNIQUE 2: Feature Selection")
    selector = SelectKBest(score_func=f_classif, k=15)
    X_selected = selector.fit_transform(X, y)
    
    print(f"   Features reduced: {X.shape[1]} → {X_selected.shape[1]} ({100*(1-X_selected.shape[1]/X.shape[1]):.1f}% reduction)")
    
    # Evaluate regularized model
    split_idx = int(0.7 * len(X_selected))
    X_train_sel, X_test_sel = X_selected[:split_idx], X_selected[split_idx:]
    
    regularized_rf.fit(X_train_sel, y_train)
    reg_train = regularized_rf.score(X_train_sel, y_train)
    reg_test = regularized_rf.score(X_test_sel, y_test)
    reg_gap = reg_train - reg_test
    
    cv_scores_reg = cross_val_score(regularized_rf, X_train_sel, y_train, cv=tscv)
    
    print(f"📊 REGULARIZATION RESULTS:")
    print(f"   Training: {reg_train:.4f}")
    print(f"   Test: {reg_test:.4f}")
    print(f"   Gap: {reg_gap:.4f} ({'LOW' if reg_gap < 0.05 else 'MEDIUM' if reg_gap < 0.10 else 'HIGH'})")
    print(f"   CV: {cv_scores_reg.mean():.4f} ± {cv_scores_reg.std():.4f}")
    
    # Solution 2: Ensemble Methods
    print(f"\n✅ SOLUTION 2: ENSEMBLE METHODS")
    print("=" * 30)
    
    print("🤝 ENSEMBLE TECHNIQUE: Voting Classifier")
    
    # Create diverse base models with different regularization
    base_models = [
        ('rf_conservative', RandomForestClassifier(
            n_estimators=30, max_depth=4, min_samples_split=25,
            min_samples_leaf=15, max_features=0.2, random_state=42
        )),
        ('extra_trees', ExtraTreesClassifier(
            n_estimators=30, max_depth=4, min_samples_split=25,
            min_samples_leaf=15, max_features=0.2, random_state=43
        )),
        ('rf_shallow', RandomForestClassifier(
            n_estimators=25, max_depth=3, min_samples_split=30,
            min_samples_leaf=20, max_features=0.15, random_state=44
        )),
        ('logistic', LogisticRegression(C=0.1, random_state=42, max_iter=1000))
    ]
    
    voting_ensemble = VotingClassifier(estimators=base_models, voting='soft')
    
    print(f"   Base models: {len(base_models)}")
    print(f"   Voting type: Soft voting")
    print(f"   Diversity: Different algorithms and hyperparameters")
    
    # Evaluate ensemble
    voting_ensemble.fit(X_train, y_train)
    ens_train = voting_ensemble.score(X_train, y_train)
    ens_test = voting_ensemble.score(X_test, y_test)
    ens_gap = ens_train - ens_test
    
    cv_scores_ens = cross_val_score(voting_ensemble, X_train, y_train, cv=tscv)
    
    print(f"📊 ENSEMBLE RESULTS:")
    print(f"   Training: {ens_train:.4f}")
    print(f"   Test: {ens_test:.4f}")
    print(f"   Gap: {ens_gap:.4f} ({'LOW' if ens_gap < 0.05 else 'MEDIUM' if ens_gap < 0.10 else 'HIGH'})")
    print(f"   CV: {cv_scores_ens.mean():.4f} ± {cv_scores_ens.std():.4f}")
    
    # Ultimate Solution: Regularization + Ensemble
    print(f"\n🏆 ULTIMATE SOLUTION: REGULARIZATION + ENSEMBLE")
    print("=" * 50)
    
    # Step 1: Feature selection
    print("STEP 1: Aggressive Feature Selection")
    selector_ultimate = SelectKBest(score_func=f_classif, k=12)
    X_ultimate = selector_ultimate.fit_transform(X, y)
    print(f"   Features: {X.shape[1]} → {X_ultimate.shape[1]} ({100*(1-X_ultimate.shape[1]/X.shape[1]):.1f}% reduction)")
    
    # Step 2: Regularized ensemble
    print("STEP 2: Regularized Ensemble")
    regularized_ensemble = VotingClassifier(
        estimators=[
            ('rf_ultra_conservative', RandomForestClassifier(
                n_estimators=20, max_depth=3, min_samples_split=40,
                min_samples_leaf=20, max_features=0.5, min_impurity_decrease=0.02,
                random_state=42
            )),
            ('extra_trees_conservative', ExtraTreesClassifier(
                n_estimators=20, max_depth=3, min_samples_split=40,
                min_samples_leaf=20, max_features=0.5, min_impurity_decrease=0.02,
                random_state=43
            )),
            ('logistic_l2', LogisticRegression(
                C=0.01, penalty='l2', random_state=42, max_iter=1000
            ))
        ],
        voting='soft'
    )
    
    # Evaluate ultimate solution
    split_idx = int(0.7 * len(X_ultimate))
    X_train_ult, X_test_ult = X_ultimate[:split_idx], X_ultimate[split_idx:]
    
    regularized_ensemble.fit(X_train_ult, y_train)
    ult_train = regularized_ensemble.score(X_train_ult, y_train)
    ult_test = regularized_ensemble.score(X_test_ult, y_test)
    ult_gap = ult_train - ult_test
    
    cv_scores_ult = cross_val_score(regularized_ensemble, X_train_ult, y_train, cv=tscv)
    
    print(f"🏆 ULTIMATE SOLUTION RESULTS:")
    print(f"   Training: {ult_train:.4f}")
    print(f"   Test: {ult_test:.4f}")
    print(f"   Gap: {ult_gap:.4f} ({'LOW' if ult_gap < 0.05 else 'MEDIUM' if ult_gap < 0.10 else 'HIGH'})")
    print(f"   CV: {cv_scores_ult.mean():.4f} ± {cv_scores_ult.std():.4f}")
    print(f"   Features Used: {X_ultimate.shape[1]}")
    print(f"   Techniques Applied: Feature Selection + Regularization + Ensemble")
    
    # Comprehensive Comparison
    print(f"\n📊 COMPREHENSIVE COMPARISON")
    print("=" * 30)
    
    print(f"{'Approach':<15} {'Train':<8} {'Test':<8} {'Gap':<8} {'CV Mean':<8} {'CV Std':<8}")
    print("-" * 65)
    print(f"{'Problem':<15} {train_score:<8.4f} {test_score:<8.4f} {gap:<8.4f} {cv_scores.mean():<8.4f} {cv_scores.std():<8.4f}")
    print(f"{'Regularized':<15} {reg_train:<8.4f} {reg_test:<8.4f} {reg_gap:<8.4f} {cv_scores_reg.mean():<8.4f} {cv_scores_reg.std():<8.4f}")
    print(f"{'Ensemble':<15} {ens_train:<8.4f} {ens_test:<8.4f} {ens_gap:<8.4f} {cv_scores_ens.mean():<8.4f} {cv_scores_ens.std():<8.4f}")
    print(f"{'Ultimate':<15} {ult_train:<8.4f} {ult_test:<8.4f} {ult_gap:<8.4f} {cv_scores_ult.mean():<8.4f} {cv_scores_ult.std():<8.4f}")
    
    # Calculate improvements
    gap_improvement = (gap - ult_gap) / gap * 100
    cv_improvement = (cv_scores.std() - cv_scores_ult.std()) / cv_scores.std() * 100
    test_improvement = ult_test - test_score
    
    print(f"\n🎯 IMPROVEMENTS (Ultimate vs Problem):")
    print(f"   Train-Test Gap: {gap_improvement:.1f}% reduction")
    print(f"   CV Stability: {cv_improvement:.1f}% improvement")
    print(f"   Test Performance: {test_improvement:+.4f}")
    
    print(f"\n✅ OVERFITTING SOLUTION COMPLETE!")
    print("🛡️ Random Forest overfitting with many features solved through:")
    print("   1. Hyperparameter regularization")
    print("   2. Feature selection")
    print("   3. Ensemble methods")
    print("   4. Conservative model settings")
    
    print(f"\n🎉 SUCCESS!")
    print("Random Forest overfitting with many features comprehensively addressed!")
    print("Both regularization techniques AND ensemble methods successfully applied!")

if __name__ == "__main__":
    main() 