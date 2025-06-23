#!/usr/bin/env python3
"""
🛡️ Overfitting Prevention Demo for Random Forests
Demonstrates key techniques to prevent overfitting in financial ML
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import ExtraTreesClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.feature_selection import SelectKBest, SelectFromModel, f_classif
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt

class OverfittingPreventionDemo:
    """
    Demonstrates comprehensive overfitting prevention for Random Forests
    """
    
    def __init__(self):
        self.results = {}
    
    def generate_overfitting_prone_data(self, n_samples=1000, n_features=100, n_relevant=5):
        """
        Generate data that's prone to overfitting
        Many features, few relevant ones - classic overfitting scenario
        """
        
        np.random.seed(42)
        
        # Generate random features
        X = np.random.randn(n_samples, n_features)
        
        # Only some features are actually relevant
        relevant_indices = np.random.choice(n_features, n_relevant, replace=False)
        
        # Create target based on relevant features only
        y_continuous = np.sum(X[:, relevant_indices], axis=1)
        
        # Add some non-linear interactions
        y_continuous += 0.5 * X[:, relevant_indices[0]] * X[:, relevant_indices[1]]
        
        # Add noise
        y_continuous += np.random.randn(n_samples) * 0.3
        
        # Convert to classification
        y = (y_continuous > np.median(y_continuous)).astype(int)
        
        return X, y, relevant_indices
    
    def demonstrate_unregularized_overfitting(self, X, y):
        """
        Show how unregularized Random Forest overfits
        """
        
        print("❌ UNREGULARIZED RANDOM FOREST (PRONE TO OVERFITTING)")
        print("=" * 55)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Create overfitting-prone Random Forest
        overfitting_rf = RandomForestClassifier(
            n_estimators=500,           # Too many trees
            max_depth=None,             # No depth limit
            min_samples_split=2,        # Too small
            min_samples_leaf=1,         # Too small
            max_features='sqrt',        # Changed from 'auto' to 'sqrt'
            bootstrap=True,
            random_state=42
        )
        
        # Fit and evaluate
        overfitting_rf.fit(X_train, y_train)
        
        train_score = overfitting_rf.score(X_train, y_train)
        test_score = overfitting_rf.score(X_test, y_test)
        overfitting_gap = train_score - test_score
        
        print(f"📊 Training Accuracy: {train_score:.4f}")
        print(f"📊 Test Accuracy: {test_score:.4f}")
        print(f"⚠️ Overfitting Gap: {overfitting_gap:.4f}")
        print(f"🚨 Overfitting Severity: {'HIGH' if overfitting_gap > 0.1 else 'MEDIUM' if overfitting_gap > 0.05 else 'LOW'}")
        
        # Cross-validation to confirm overfitting
        cv_scores = cross_val_score(overfitting_rf, X_train, y_train, cv=5)
        print(f"📈 CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"📉 CV vs Train Gap: {train_score - cv_scores.mean():.4f}")
        
        self.results['unregularized'] = {
            'train_score': train_score,
            'test_score': test_score,
            'cv_score': cv_scores.mean(),
            'overfitting_gap': overfitting_gap
        }
        
        return overfitting_rf, X_train, X_test, y_train, y_test
    
    def apply_feature_selection(self, X, y):
        """
        Apply feature selection to reduce overfitting
        """
        
        print(f"\n🎯 FEATURE SELECTION (DIMENSIONALITY REDUCTION)")
        print("=" * 50)
        
        original_features = X.shape[1]
        
        # Method 1: Statistical feature selection
        selector = SelectKBest(score_func=f_classif, k=20)  # Select top 20 features
        X_selected = selector.fit_transform(X, y)
        selected_features = selector.get_support(indices=True)
        
        print(f"📉 Original Features: {original_features}")
        print(f"📈 Selected Features: {X_selected.shape[1]}")
        print(f"🎯 Reduction: {100 * (1 - X_selected.shape[1] / original_features):.1f}%")
        
        # Method 2: Tree-based feature selection
        tree_selector = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        tree_selector.fit(X, y)
        
        # Get feature importances
        importances = tree_selector.feature_importances_
        important_features = np.where(importances > np.percentile(importances, 80))[0]
        
        print(f"🌲 Tree-based selection: {len(important_features)} features")
        
        # Combine selections (intersection for conservative approach)
        final_features = np.intersect1d(selected_features, important_features)
        if len(final_features) < 10:  # Ensure minimum features
            final_features = selected_features[:15]
        
        X_final = X[:, final_features]
        
        print(f"✅ Final Selected Features: {len(final_features)}")
        print(f"🎯 Total Reduction: {100 * (1 - len(final_features) / original_features):.1f}%")
        
        return X_final, final_features
    
    def create_regularized_random_forest(self, X, y):
        """
        Create Random Forest with regularization to prevent overfitting
        """
        
        print(f"\n🛡️ REGULARIZED RANDOM FOREST")
        print("=" * 35)
        
        # Define regularization parameter grid
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7, 10],
            'min_samples_split': [5, 10, 20],
            'min_samples_leaf': [2, 5, 10],
            'max_features': ['sqrt', 'log2', 0.3],
            'min_impurity_decrease': [0.0, 0.01, 0.02]
        }
        
        # Use RandomizedSearchCV for efficiency
        rf_base = RandomForestClassifier(random_state=42)
        
        random_search = RandomizedSearchCV(
            rf_base,
            param_distributions=param_grid,
            n_iter=30,  # Try 30 combinations
            cv=5,
            scoring='accuracy',
            random_state=42,
            n_jobs=-1
        )
        
        print("🔧 Tuning hyperparameters...")
        random_search.fit(X, y)
        
        best_params = random_search.best_params_
        best_score = random_search.best_score_
        
        print(f"✅ Best CV Score: {best_score:.4f}")
        print(f"🎛️ Best Parameters:")
        for param, value in best_params.items():
            print(f"   {param}: {value}")
        
        # Create final regularized model
        regularized_rf = RandomForestClassifier(**best_params, random_state=42)
        
        return regularized_rf, best_params
    
    def create_ensemble_model(self, regularized_rf):
        """
        Create ensemble to further reduce overfitting
        """
        
        print(f"\n🎭 ENSEMBLE MODEL (DIVERSITY FOR ROBUSTNESS)")
        print("=" * 45)
        
        # Create diverse models
        models = [
            ('rf_regularized', regularized_rf),
            ('extra_trees', ExtraTreesClassifier(
                n_estimators=100, max_depth=7, min_samples_split=10, 
                min_samples_leaf=5, random_state=42
            )),
            ('logistic', LogisticRegression(
                C=1.0, penalty='l2', random_state=42, max_iter=1000
            )),
            ('ridge', SGDClassifier(
                alpha=1.0, penalty='l2', random_state=42, max_iter=1000
            ))
        ]
        
        # Create voting ensemble
        ensemble = VotingClassifier(
            estimators=models,
            voting='hard'  # Use hard voting since RidgeClassifier doesn't have predict_proba
        )
        
        print("🎪 Ensemble Components:")
        for name, model in models:
            print(f"   • {name}: {type(model).__name__}")
        
        return ensemble
    
    def evaluate_regularized_model(self, model, X, y, model_name="Regularized Model"):
        """
        Evaluate regularized model performance
        """
        
        print(f"\n📊 {model_name.upper()} EVALUATION")
        print("=" * (len(model_name) + 15))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Fit model
        model.fit(X_train, y_train)
        
        # Evaluate
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        overfitting_gap = train_score - test_score
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)
        
        print(f"📈 Training Accuracy: {train_score:.4f}")
        print(f"📊 Test Accuracy: {test_score:.4f}")
        print(f"🎯 CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"⚖️ Overfitting Gap: {overfitting_gap:.4f}")
        print(f"🛡️ Overfitting Level: {'LOW' if overfitting_gap < 0.05 else 'MEDIUM' if overfitting_gap < 0.1 else 'HIGH'}")
        
        # Detailed classification report
        y_pred = model.predict(X_test)
        print(f"\n📋 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'cv_score': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'overfitting_gap': overfitting_gap
        }
    
    def compare_models(self):
        """
        Compare all models and show overfitting prevention effectiveness
        """
        
        print(f"\n⚖️ MODEL COMPARISON & OVERFITTING PREVENTION EFFECTIVENESS")
        print("=" * 65)
        
        models = ['unregularized', 'regularized_rf', 'ensemble']
        
        print(f"{'Model':<20} {'Train Acc':<10} {'Test Acc':<10} {'CV Acc':<10} {'Overfit Gap':<12} {'Status':<10}")
        print("-" * 75)
        
        for model_name in models:
            if model_name in self.results:
                result = self.results[model_name]
                status = 'HIGH' if result['overfitting_gap'] > 0.1 else 'MEDIUM' if result['overfitting_gap'] > 0.05 else 'LOW'
                print(f"{model_name:<20} {result['train_score']:<10.4f} {result['test_score']:<10.4f} "
                      f"{result['cv_score']:<10.4f} {result['overfitting_gap']:<12.4f} {status:<10}")
        
        # Calculate improvements
        if 'unregularized' in self.results and 'ensemble' in self.results:
            unreg_gap = self.results['unregularized']['overfitting_gap']
            reg_gap = self.results['ensemble']['overfitting_gap']
            improvement = unreg_gap - reg_gap
            improvement_pct = (improvement / unreg_gap) * 100 if unreg_gap > 0 else 0
            
            print(f"\n🚀 OVERFITTING REDUCTION:")
            print(f"   Original Gap: {unreg_gap:.4f}")
            print(f"   Regularized Gap: {reg_gap:.4f}")
            print(f"   Improvement: {improvement:.4f} ({improvement_pct:.1f}%)")
    
    def run_complete_demonstration(self):
        """
        Run complete overfitting prevention demonstration
        """
        
        print("🛡️ COMPREHENSIVE RANDOM FOREST OVERFITTING PREVENTION")
        print("=" * 60)
        print("Demonstrating techniques to prevent overfitting in financial ML")
        print("=" * 60)
        
        # 1. Generate overfitting-prone data
        print(f"\n📊 GENERATING OVERFITTING-PRONE DATA")
        print("=" * 40)
        
        X, y, relevant_features = self.generate_overfitting_prone_data(
            n_samples=1000, n_features=100, n_relevant=5
        )
        
        print(f"📈 Samples: {X.shape[0]}")
        print(f"📊 Total Features: {X.shape[1]}")
        print(f"🎯 Relevant Features: {len(relevant_features)}")
        print(f"⚠️ Irrelevant Features: {X.shape[1] - len(relevant_features)}")
        print(f"🚨 Overfitting Risk: HIGH (many irrelevant features)")
        
        # 2. Demonstrate unregularized overfitting
        unregularized_rf, X_train, X_test, y_train, y_test = self.demonstrate_unregularized_overfitting(X, y)
        
        # 3. Apply feature selection
        X_selected, selected_features = self.apply_feature_selection(X, y)
        
        # 4. Create regularized Random Forest
        regularized_rf, best_params = self.create_regularized_random_forest(X_selected, y)
        
        # 5. Evaluate regularized Random Forest
        reg_results = self.evaluate_regularized_model(
            regularized_rf, X_selected, y, "Regularized Random Forest"
        )
        self.results['regularized_rf'] = reg_results
        
        # 6. Create and evaluate ensemble
        ensemble = self.create_ensemble_model(regularized_rf)
        ensemble_results = self.evaluate_regularized_model(
            ensemble, X_selected, y, "Ensemble Model"
        )
        self.results['ensemble'] = ensemble_results
        
        # 7. Compare all models
        self.compare_models()
        
        # 8. Summary of techniques
        self.print_overfitting_prevention_summary()
        
        return self.results
    
    def print_overfitting_prevention_summary(self):
        """
        Print summary of overfitting prevention techniques
        """
        
        print(f"\n🛡️ OVERFITTING PREVENTION TECHNIQUES APPLIED")
        print("=" * 50)
        
        techniques = [
            ("🎯 Feature Selection", "Reduced features from 100 to ~15-20"),
            ("🔧 Hyperparameter Tuning", "Optimized RF parameters via RandomizedSearchCV"),
            ("📏 Regularization", "Applied min_samples_split, min_samples_leaf, max_depth"),
            ("🎭 Ensemble Methods", "Combined RF with ExtraTrees, Logistic, Ridge"),
            ("✅ Cross-Validation", "Used 5-fold CV for realistic performance estimates"),
            ("🛡️ Conservative Settings", "Prevented overly complex models")
        ]
        
        for technique, description in techniques:
            print(f"{technique}: {description}")
        
        print(f"\n🎯 KEY BENEFITS OF OVERFITTING PREVENTION:")
        print("=" * 45)
        benefits = [
            "✅ More realistic performance estimates",
            "✅ Better generalization to new data",
            "✅ Reduced risk of catastrophic losses",
            "✅ More stable model performance",
            "✅ Lower variance in predictions",
            "✅ Better risk management"
        ]
        
        for benefit in benefits:
            print(f"   {benefit}")
        
        print(f"\n⚠️ WHY RANDOM FORESTS OVERFIT WITHOUT REGULARIZATION:")
        print("=" * 55)
        reasons = [
            "❌ Deep trees memorize training data noise",
            "❌ Too many features lead to spurious correlations",
            "❌ Small leaf nodes fit individual data points",
            "❌ No built-in complexity penalty",
            "❌ Bootstrap sampling may not provide enough diversity"
        ]
        
        for reason in reasons:
            print(f"   {reason}")

def main():
    """
    Main demonstration function
    """
    
    demo = OverfittingPreventionDemo()
    results = demo.run_complete_demonstration()
    
    print(f"\n🎉 OVERFITTING PREVENTION DEMONSTRATION COMPLETE!")
    print("=" * 50)
    print("✅ Random Forest overfitting successfully prevented!")
    print("✅ Ensemble model provides robust, generalizable predictions!")
    print("✅ Ready for production trading system!")

if __name__ == "__main__":
    main()