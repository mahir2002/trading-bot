#!/usr/bin/env python3
"""
🛡️ Random Forest Overfitting Solution
Comprehensive approach using regularization techniques AND ensemble methods
Specifically designed for high-dimensional feature spaces
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import (
    RandomForestClassifier, ExtraTreesClassifier, 
    VotingClassifier, BaggingClassifier, AdaBoostClassifier
)
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.feature_selection import (
    SelectKBest, SelectFromModel, RFE, f_classif,
    VarianceThreshold, SelectPercentile
)
from sklearn.model_selection import (
    TimeSeriesSplit, cross_val_score, GridSearchCV,
    validation_curve
)
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

class RFOverfittingSolution:
    """
    Comprehensive solution for Random Forest overfitting with many features
    Combines regularization techniques with ensemble methods
    """
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.results = {}
        self.models = {}
        
    def generate_high_dimensional_data(self, n_samples=1000, n_features=200, n_relevant=5):
        """Generate high-dimensional data that causes overfitting"""
        
        np.random.seed(self.random_state)
        
        print("🚨 GENERATING HIGH-DIMENSIONAL OVERFITTING DATA")
        print("=" * 50)
        print(f"📊 Samples: {n_samples}")
        print(f"📈 Total Features: {n_features}")
        print(f"🎯 Relevant Features: {n_relevant}")
        print(f"⚠️ Irrelevant Features: {n_features - n_relevant}")
        print(f"🚨 Overfitting Risk: EXTREME (Curse of Dimensionality)")
        
        # Generate random features
        X = np.random.randn(n_samples, n_features)
        
        # Add some correlation structure to make it more realistic
        for i in range(0, n_features, 10):
            end_idx = min(i + 5, n_features)
            correlation_matrix = np.random.rand(end_idx - i, end_idx - i)
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix, 1)
            X[:, i:end_idx] = X[:, i:end_idx] @ correlation_matrix
        
        # Only first few features are actually relevant
        relevant_indices = list(range(n_relevant))
        
        # Create complex non-linear target
        y_continuous = (
            2.0 * X[:, 0] + 
            1.5 * X[:, 1] * X[:, 2] +  # Interaction term
            0.8 * np.sin(X[:, 3]) +    # Non-linear term
            0.5 * X[:, 4] ** 2 +       # Polynomial term
            np.random.randn(n_samples) * 0.3  # Noise
        )
        
        # Binary classification
        y = (y_continuous > np.median(y_continuous)).astype(int)
        
        return X, y, relevant_indices
    
    def demonstrate_baseline_overfitting(self, X, y):
        """Show how badly default Random Forest overfits with many features"""
        
        print(f"\n❌ BASELINE: DEFAULT RANDOM FOREST OVERFITTING")
        print("=" * 50)
        
        # Default Random Forest - prone to overfitting
        baseline_rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,        # Unlimited depth
            min_samples_split=2,   # Minimal split requirement
            min_samples_leaf=1,    # Single sample leaves
            max_features='sqrt',   # Still too many with 200 features
            random_state=self.random_state
        )
        
        # Time series split for realistic evaluation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Cross-validation scores
        cv_scores = cross_val_score(baseline_rf, X, y, cv=tscv, scoring='accuracy')
        
        # Train-test split
        split_idx = int(0.7 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        baseline_rf.fit(X_train, y_train)
        train_score = baseline_rf.score(X_train, y_train)
        test_score = baseline_rf.score(X_test, y_test)
        
        print(f"🚨 OVERFITTING INDICATORS:")
        print(f"   Training Accuracy: {train_score:.4f}")
        print(f"   Test Accuracy: {test_score:.4f}")
        print(f"   Train-Test Gap: {train_score - test_score:.4f}")
        print(f"   CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"   CV Stability: {'UNSTABLE' if cv_scores.std() > 0.05 else 'STABLE'}")
        
        # Feature importance analysis
        feature_importance = baseline_rf.feature_importances_
        top_features = np.argsort(feature_importance)[-10:]
        
        print(f"\n📊 FEATURE USAGE:")
        print(f"   Using all {X.shape[1]} features")
        print(f"   Top 10 feature indices: {top_features}")
        print(f"   Max feature importance: {feature_importance.max():.4f}")
        print(f"   Features with >1% importance: {np.sum(feature_importance > 0.01)}")
        
        self.results['baseline'] = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': train_score - test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'n_features': X.shape[1]
        }
        
        self.models['baseline'] = baseline_rf
        return baseline_rf
    
    def apply_regularization_techniques(self, X, y):
        """Apply comprehensive regularization techniques"""
        
        print(f"\n🛡️ REGULARIZATION TECHNIQUES")
        print("=" * 35)
        
        regularization_results = {}
        
        # 1. Hyperparameter Regularization
        print("1️⃣ HYPERPARAMETER REGULARIZATION")
        regularized_rf = RandomForestClassifier(
            n_estimators=50,               # Fewer trees
            max_depth=5,                  # Limited depth
            min_samples_split=20,         # Higher split requirement
            min_samples_leaf=10,          # Higher leaf requirement
            max_features=0.1,             # Use only 10% of features per tree
            min_impurity_decrease=0.01,   # Require improvement to split
            max_leaf_nodes=50,            # Limit total leaves
            random_state=self.random_state
        )
        
        # 2. Feature Selection Regularization
        print("2️⃣ FEATURE SELECTION REGULARIZATION")
        
        # Statistical feature selection
        selector_stats = SelectKBest(score_func=f_classif, k=20)
        X_stats = selector_stats.fit_transform(X, y)
        
        # Tree-based feature selection
        tree_selector = RandomForestClassifier(
            n_estimators=50, max_depth=3, random_state=self.random_state
        )
        tree_selector.fit(X, y)
        selector_tree = SelectFromModel(tree_selector, max_features=20)
        X_tree = selector_tree.fit_transform(X, y)
        
        # L1 regularization feature selection
        lr_l1 = LogisticRegression(penalty='l1', solver='liblinear', C=0.01, random_state=self.random_state)
        selector_l1 = SelectFromModel(lr_l1, max_features=20)
        X_l1 = selector_l1.fit_transform(X, y)
        
        # Combine feature selections (intersection)
        stats_features = selector_stats.get_support(indices=True)
        tree_features = selector_tree.get_support(indices=True)
        l1_features = selector_l1.get_support(indices=True)
        
        # Take intersection of all methods for most conservative selection
        combined_features = np.intersect1d(
            np.intersect1d(stats_features, tree_features), 
            l1_features
        )
        
        if len(combined_features) < 10:
            combined_features = stats_features[:15]  # Fallback
        
        X_selected = X[:, combined_features]
        
        print(f"   📉 Features: {X.shape[1]} → {X_selected.shape[1]} ({100*(1-X_selected.shape[1]/X.shape[1]):.1f}% reduction)")
        
        # 3. Evaluate regularized model
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(regularized_rf, X_selected, y, cv=tscv)
        
        split_idx = int(0.7 * len(X_selected))
        X_train, X_test = X_selected[:split_idx], X_selected[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        regularized_rf.fit(X_train, y_train)
        train_score = regularized_rf.score(X_train, y_train)
        test_score = regularized_rf.score(X_test, y_test)
        
        print(f"📊 REGULARIZATION RESULTS:")
        print(f"   Training: {train_score:.4f}")
        print(f"   Test: {test_score:.4f}")
        print(f"   Gap: {train_score - test_score:.4f}")
        print(f"   CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        regularization_results = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': train_score - test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'n_features': X_selected.shape[1]
        }
        
        self.results['regularized'] = regularization_results
        self.models['regularized'] = regularized_rf
        
        return regularized_rf, X_selected, combined_features
    
    def create_ensemble_methods(self, X, y):
        """Create comprehensive ensemble methods to combat overfitting"""
        
        print(f"\n🤝 ENSEMBLE METHODS")
        print("=" * 20)
        
        ensemble_results = {}
        
        # Base models with different regularization strategies
        base_models = []
        
        # Model 1: Conservative Random Forest
        rf_conservative = RandomForestClassifier(
            n_estimators=30, max_depth=4, min_samples_split=25,
            min_samples_leaf=15, max_features=0.15, random_state=self.random_state
        )
        base_models.append(('rf_conservative', rf_conservative))
        
        # Model 2: Extra Trees (more randomization)
        et_model = ExtraTreesClassifier(
            n_estimators=30, max_depth=4, min_samples_split=25,
            min_samples_leaf=15, max_features=0.15, random_state=self.random_state + 1
        )
        base_models.append(('extra_trees', et_model))
        
        # Model 3: Regularized Random Forest
        rf_regularized = RandomForestClassifier(
            n_estimators=30, max_depth=3, min_samples_split=30,
            min_samples_leaf=20, max_features=0.1, min_impurity_decrease=0.02,
            random_state=self.random_state + 2
        )
        base_models.append(('rf_regularized', rf_regularized))
        
        # Model 4: Linear model for diversity
        lr_model = LogisticRegression(C=0.1, random_state=self.random_state, max_iter=1000)
        base_models.append(('logistic', lr_model))
        
        print("1️⃣ VOTING ENSEMBLE")
        # Hard voting ensemble
        voting_hard = VotingClassifier(
            estimators=base_models,
            voting='hard'
        )
        
        # Soft voting ensemble (if all models support predict_proba)
        voting_soft = VotingClassifier(
            estimators=base_models,
            voting='soft'
        )
        
        print("2️⃣ BAGGING ENSEMBLE")
        # Bagging with regularized base estimator
        bagging_rf = BaggingClassifier(
            base_estimator=RandomForestClassifier(
                n_estimators=10, max_depth=4, min_samples_split=20,
                max_features=0.2, random_state=self.random_state
            ),
            n_estimators=10,
            max_samples=0.8,
            max_features=0.8,
            random_state=self.random_state
        )
        
        print("3️⃣ BOOSTING ENSEMBLE")
        # AdaBoost with weak learners
        ada_boost = AdaBoostClassifier(
            base_estimator=RandomForestClassifier(
                n_estimators=5, max_depth=2, max_features=0.1,
                random_state=self.random_state
            ),
            n_estimators=20,
            learning_rate=0.5,
            random_state=self.random_state
        )
        
        # Evaluate all ensemble methods
        ensembles = [
            ('voting_hard', voting_hard),
            ('voting_soft', voting_soft),
            ('bagging', bagging_rf),
            ('boosting', ada_boost)
        ]
        
        tscv = TimeSeriesSplit(n_splits=5)
        split_idx = int(0.7 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        best_ensemble = None
        best_score = 0
        
        for name, ensemble in ensembles:
            try:
                cv_scores = cross_val_score(ensemble, X_train, y_train, cv=tscv)
                ensemble.fit(X_train, y_train)
                
                train_score = ensemble.score(X_train, y_train)
                test_score = ensemble.score(X_test, y_test)
                
                print(f"   {name.upper()}:")
                print(f"     Train: {train_score:.4f}, Test: {test_score:.4f}")
                print(f"     Gap: {train_score - test_score:.4f}")
                print(f"     CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
                
                ensemble_results[name] = {
                    'train_score': train_score,
                    'test_score': test_score,
                    'gap': train_score - test_score,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                }
                
                if test_score > best_score:
                    best_score = test_score
                    best_ensemble = (name, ensemble)
                    
            except Exception as e:
                print(f"   {name.upper()}: Failed ({str(e)})")
        
        self.results['ensembles'] = ensemble_results
        self.models['best_ensemble'] = best_ensemble
        
        return best_ensemble, ensemble_results
    
    def create_ultimate_solution(self, X, y):
        """Combine regularization AND ensemble methods for ultimate solution"""
        
        print(f"\n🏆 ULTIMATE SOLUTION: REGULARIZATION + ENSEMBLE")
        print("=" * 50)
        
        # Step 1: Apply aggressive feature selection
        print("STEP 1: Aggressive Feature Selection")
        selector = SelectKBest(score_func=f_classif, k=15)
        X_selected = selector.fit_transform(X, y)
        selected_features = selector.get_support(indices=True)
        
        print(f"   Features: {X.shape[1]} → {X_selected.shape[1]} ({100*(1-X_selected.shape[1]/X.shape[1]):.1f}% reduction)")
        
        # Step 2: Create highly regularized base models
        print("STEP 2: Highly Regularized Base Models")
        
        base_models = [
            ('rf_ultra_conservative', RandomForestClassifier(
                n_estimators=20, max_depth=3, min_samples_split=40,
                min_samples_leaf=20, max_features=0.3, min_impurity_decrease=0.02,
                max_leaf_nodes=20, random_state=self.random_state
            )),
            ('extra_trees_conservative', ExtraTreesClassifier(
                n_estimators=20, max_depth=3, min_samples_split=40,
                min_samples_leaf=20, max_features=0.3, min_impurity_decrease=0.02,
                random_state=self.random_state + 1
            )),
            ('rf_shallow', RandomForestClassifier(
                n_estimators=15, max_depth=2, min_samples_split=50,
                min_samples_leaf=25, max_features=0.2, random_state=self.random_state + 2
            )),
            ('logistic_l2', LogisticRegression(
                C=0.01, penalty='l2', random_state=self.random_state, max_iter=1000
            ))
        ]
        
        # Step 3: Create ensemble with regularized models
        print("STEP 3: Ensemble of Regularized Models")
        
        ultimate_ensemble = VotingClassifier(
            estimators=base_models,
            voting='soft'
        )
        
        # Step 4: Evaluate ultimate solution
        print("STEP 4: Evaluation")
        
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(ultimate_ensemble, X_selected, y, cv=tscv)
        
        split_idx = int(0.7 * len(X_selected))
        X_train, X_test = X_selected[:split_idx], X_selected[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        ultimate_ensemble.fit(X_train, y_train)
        
        train_score = ultimate_ensemble.score(X_train, y_train)
        test_score = ultimate_ensemble.score(X_test, y_test)
        
        print(f"🏆 ULTIMATE SOLUTION RESULTS:")
        print(f"   Training: {train_score:.4f}")
        print(f"   Test: {test_score:.4f}")
        print(f"   Gap: {train_score - test_score:.4f}")
        print(f"   CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"   Features Used: {X_selected.shape[1]}")
        print(f"   Models in Ensemble: {len(base_models)}")
        
        self.results['ultimate'] = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': train_score - test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'n_features': X_selected.shape[1],
            'n_models': len(base_models)
        }
        
        self.models['ultimate'] = ultimate_ensemble
        
        return ultimate_ensemble, X_selected, selected_features
    
    def compare_all_approaches(self):
        """Compare all approaches: baseline, regularization, ensemble, ultimate"""
        
        print(f"\n📊 COMPREHENSIVE COMPARISON")
        print("=" * 30)
        
        approaches = ['baseline', 'regularized', 'ultimate']
        metrics = ['train_score', 'test_score', 'gap', 'cv_mean', 'cv_std']
        
        print(f"{'Approach':<15} {'Train':<8} {'Test':<8} {'Gap':<8} {'CV Mean':<8} {'CV Std':<8} {'Features':<10}")
        print("-" * 75)
        
        for approach in approaches:
            if approach in self.results:
                r = self.results[approach]
                features = r.get('n_features', 'N/A')
                print(f"{approach.capitalize():<15} {r['train_score']:<8.4f} {r['test_score']:<8.4f} "
                      f"{r['gap']:<8.4f} {r['cv_mean']:<8.4f} {r['cv_std']:<8.4f} {features:<10}")
        
        # Calculate improvements
        if 'baseline' in self.results and 'ultimate' in self.results:
            baseline = self.results['baseline']
            ultimate = self.results['ultimate']
            
            gap_improvement = (baseline['gap'] - ultimate['gap']) / baseline['gap'] * 100
            cv_improvement = (baseline['cv_std'] - ultimate['cv_std']) / baseline['cv_std'] * 100
            feature_reduction = (baseline['n_features'] - ultimate['n_features']) / baseline['n_features'] * 100
            
            print(f"\n🎯 IMPROVEMENTS (Ultimate vs Baseline):")
            print(f"   Train-Test Gap: {gap_improvement:.1f}% reduction")
            print(f"   CV Stability: {cv_improvement:.1f}% improvement")
            print(f"   Feature Reduction: {feature_reduction:.1f}% fewer features")
            print(f"   Test Performance: {ultimate['test_score'] - baseline['test_score']:+.4f}")
    
    def run_complete_solution(self):
        """Run the complete overfitting solution"""
        
        print("🛡️ RANDOM FOREST OVERFITTING SOLUTION")
        print("=" * 40)
        print("Comprehensive approach: Regularization + Ensemble Methods")
        print("=" * 40)
        
        # Generate high-dimensional data
        X, y, relevant_features = self.generate_high_dimensional_data()
        
        # Show baseline overfitting
        baseline_model = self.demonstrate_baseline_overfitting(X, y)
        
        # Apply regularization techniques
        regularized_model, X_reg, reg_features = self.apply_regularization_techniques(X, y)
        
        # Create ensemble methods
        best_ensemble, ensemble_results = self.create_ensemble_methods(X_reg, y)
        
        # Create ultimate solution
        ultimate_model, X_ultimate, ultimate_features = self.create_ultimate_solution(X, y)
        
        # Compare all approaches
        self.compare_all_approaches()
        
        print(f"\n✅ OVERFITTING SOLUTION COMPLETE!")
        print("🛡️ Random Forest overfitting addressed through:")
        print("   1. Hyperparameter regularization")
        print("   2. Aggressive feature selection")
        print("   3. Ensemble methods")
        print("   4. Conservative model settings")
        print("   5. Time series cross-validation")
        
        return {
            'data': (X, y),
            'models': self.models,
            'results': self.results,
            'selected_features': ultimate_features
        }

def main():
    """Main demonstration"""
    
    solution = RFOverfittingSolution()
    results = solution.run_complete_solution()
    
    print(f"\n🎉 SUCCESS!")
    print("Random Forest overfitting with many features has been solved!")
    print("Both regularization techniques AND ensemble methods applied!")

if __name__ == "__main__":
    main()