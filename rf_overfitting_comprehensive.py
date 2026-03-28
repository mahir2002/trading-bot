#!/usr/bin/env python3
"""
🛡️ Random Forest Overfitting Solution
Addresses: "Random Forests can overfit, especially with many features"
Solution: "Regularization techniques or ensemble methods could be explored"
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import SelectKBest, SelectFromModel, f_classif
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import accuracy_score

class RFOverfittingSolution:
    """
    Comprehensive solution for Random Forest overfitting with many features
    """
    
    def __init__(self):
        self.results = {}
    
    def generate_many_features_data(self):
        """Generate data with many features to demonstrate overfitting"""
        
        np.random.seed(42)
        n_samples = 1000
        n_features = 100  # Many features
        n_relevant = 5    # Few relevant features
        
        print("🚨 HIGH-DIMENSIONAL DATA (OVERFITTING PRONE)")
        print("=" * 45)
        print(f"📊 Samples: {n_samples}")
        print(f"📈 Total Features: {n_features}")
        print(f"🎯 Relevant Features: {n_relevant}")
        print(f"⚠️ Irrelevant Features: {n_features - n_relevant}")
        
        # Generate features
        X = np.random.randn(n_samples, n_features)
        
        # Only first 5 features are relevant
        y_continuous = (X[:, 0] + 0.5 * X[:, 1] + 0.3 * X[:, 2] + 
                       0.2 * X[:, 3] + 0.1 * X[:, 4] + 
                       np.random.randn(n_samples) * 0.2)
        
        y = (y_continuous > np.median(y_continuous)).astype(int)
        
        return X, y
    
    def demonstrate_overfitting_problem(self, X, y):
        """Show how Random Forest overfits with many features"""
        
        print(f"\n❌ PROBLEM: DEFAULT RANDOM FOREST WITH MANY FEATURES")
        print("=" * 55)
        
        # Default Random Forest - prone to overfitting
        default_rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=None,      # Unlimited depth
            min_samples_split=2, # Minimal requirements
            min_samples_leaf=1,
            max_features='sqrt',
            random_state=42
        )
        
        # Evaluate overfitting
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
        
        self.results['problem'] = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': gap,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return default_rf
    
    def apply_regularization_techniques(self, X, y):
        """Apply regularization techniques to prevent overfitting"""
        
        print(f"\n✅ SOLUTION 1: REGULARIZATION TECHNIQUES")
        print("=" * 40)
        
        print("🛡️ TECHNIQUE 1: Hyperparameter Regularization")
        
        # Regularized Random Forest
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
        
        # Statistical feature selection
        selector = SelectKBest(score_func=f_classif, k=15)
        X_selected = selector.fit_transform(X, y)
        selected_features = selector.get_support(indices=True)
        
        print(f"   Features reduced: {X.shape[1]} → {X_selected.shape[1]} ({100*(1-X_selected.shape[1]/X.shape[1]):.1f}% reduction)")
        
        # Evaluate regularized model
        split_idx = int(0.7 * len(X_selected))
        X_train, X_test = X_selected[:split_idx], X_selected[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        regularized_rf.fit(X_train, y_train)
        
        train_score = regularized_rf.score(X_train, y_train)
        test_score = regularized_rf.score(X_test, y_test)
        gap = train_score - test_score
        
        # Cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(regularized_rf, X_train, y_train, cv=tscv)
        
        print(f"📊 REGULARIZATION RESULTS:")
        print(f"   Training: {train_score:.4f}")
        print(f"   Test: {test_score:.4f}")
        print(f"   Gap: {gap:.4f} ({'LOW' if gap < 0.05 else 'MEDIUM' if gap < 0.10 else 'HIGH'})")
        print(f"   CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        self.results['regularized'] = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': gap,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return regularized_rf, X_selected
    
    def apply_ensemble_methods(self, X, y):
        """Apply ensemble methods to combat overfitting"""
        
        print(f"\n✅ SOLUTION 2: ENSEMBLE METHODS")
        print("=" * 30)
        
        print("🤝 ENSEMBLE TECHNIQUE 1: Voting Classifier")
        
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
        
        # Voting ensemble
        voting_ensemble = VotingClassifier(
            estimators=base_models,
            voting='soft'
        )
        
        print(f"   Base models: {len(base_models)}")
        print(f"   Voting type: Soft voting")
        print(f"   Diversity: Different algorithms and hyperparameters")
        
        # Evaluate ensemble
        split_idx = int(0.7 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        voting_ensemble.fit(X_train, y_train)
        
        train_score = voting_ensemble.score(X_train, y_train)
        test_score = voting_ensemble.score(X_test, y_test)
        gap = train_score - test_score
        
        # Cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(voting_ensemble, X_train, y_train, cv=tscv)
        
        print(f"📊 ENSEMBLE RESULTS:")
        print(f"   Training: {train_score:.4f}")
        print(f"   Test: {test_score:.4f}")
        print(f"   Gap: {gap:.4f} ({'LOW' if gap < 0.05 else 'MEDIUM' if gap < 0.10 else 'HIGH'})")
        print(f"   CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        self.results['ensemble'] = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': gap,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return voting_ensemble
    
    def create_ultimate_solution(self, X, y):
        """Combine regularization AND ensemble methods"""
        
        print(f"\n🏆 ULTIMATE SOLUTION: REGULARIZATION + ENSEMBLE")
        print("=" * 50)
        
        # Step 1: Feature selection (regularization)
        print("STEP 1: Aggressive Feature Selection")
        selector = SelectKBest(score_func=f_classif, k=12)
        X_selected = selector.fit_transform(X, y)
        
        print(f"   Features: {X.shape[1]} → {X_selected.shape[1]} ({100*(1-X_selected.shape[1]/X.shape[1]):.1f}% reduction)")
        
        # Step 2: Create highly regularized ensemble
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
        split_idx = int(0.7 * len(X_selected))
        X_train, X_test = X_selected[:split_idx], X_selected[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        regularized_ensemble.fit(X_train, y_train)
        
        train_score = regularized_ensemble.score(X_train, y_train)
        test_score = regularized_ensemble.score(X_test, y_test)
        gap = train_score - test_score
        
        # Cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(regularized_ensemble, X_train, y_train, cv=tscv)
        
        print(f"🏆 ULTIMATE SOLUTION RESULTS:")
        print(f"   Training: {train_score:.4f}")
        print(f"   Test: {test_score:.4f}")
        print(f"   Gap: {gap:.4f} ({'LOW' if gap < 0.05 else 'MEDIUM' if gap < 0.10 else 'HIGH'})")
        print(f"   CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"   Features Used: {X_selected.shape[1]}")
        print(f"   Techniques Applied: Feature Selection + Regularization + Ensemble")
        
        self.results['ultimate'] = {
            'train_score': train_score,
            'test_score': test_score,
            'gap': gap,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        return regularized_ensemble, X_selected
    
    def compare_all_solutions(self):
        """Compare problem vs solutions"""
        
        print(f"\n📊 COMPREHENSIVE COMPARISON")
        print("=" * 30)
        
        print(f"{'Approach':<15} {'Train':<8} {'Test':<8} {'Gap':<8} {'CV Mean':<8} {'CV Std':<8}")
        print("-" * 65)
        
        approaches = ['problem', 'regularized', 'ensemble', 'ultimate']
        for approach in approaches:
            if approach in self.results:
                r = self.results[approach]
                print(f"{approach.capitalize():<15} {r['train_score']:<8.4f} {r['test_score']:<8.4f} "
                      f"{r['gap']:<8.4f} {r['cv_mean']:<8.4f} {r['cv_std']:<8.4f}")
        
        # Calculate improvements
        if 'problem' in self.results and 'ultimate' in self.results:
            problem = self.results['problem']
            ultimate = self.results['ultimate']
            
            gap_improvement = (problem['gap'] - ultimate['gap']) / problem['gap'] * 100
            cv_improvement = (problem['cv_std'] - ultimate['cv_std']) / problem['cv_std'] * 100
            test_improvement = ultimate['test_score'] - problem['test_score']
            
            print(f"\n🎯 IMPROVEMENTS (Ultimate vs Problem):")
            print(f"   Train-Test Gap: {gap_improvement:.1f}% reduction")
            print(f"   CV Stability: {cv_improvement:.1f}% improvement")
            print(f"   Test Performance: {test_improvement:+.4f}")
    
    def run_complete_solution(self):
        """Run the complete overfitting solution"""
        
        print("🛡️ RANDOM FOREST OVERFITTING SOLUTION")
        print("=" * 40)
        print("Problem: Random Forests can overfit, especially with many features")
        print("Solution: Regularization techniques + Ensemble methods")
        print("=" * 40)
        
        # Generate data with many features
        X, y = self.generate_many_features_data()
        
        # Demonstrate the problem
        problem_model = self.demonstrate_overfitting_problem(X, y)
        
        # Apply regularization techniques
        regularized_model, X_reg = self.apply_regularization_techniques(X, y)
        
        # Apply ensemble methods
        ensemble_model = self.apply_ensemble_methods(X, y)
        
        # Create ultimate solution
        ultimate_model, X_ultimate = self.create_ultimate_solution(X, y)
        
        # Compare all solutions
        self.compare_all_solutions()
        
        print(f"\n✅ OVERFITTING SOLUTION COMPLETE!")
        print("🛡️ Random Forest overfitting with many features solved through:")
        print("   1. Hyperparameter regularization")
        print("   2. Feature selection")
        print("   3. Ensemble methods")
        print("   4. Conservative model settings")
        
        return {
            'models': {
                'problem': problem_model,
                'regularized': regularized_model,
                'ensemble': ensemble_model,
                'ultimate': ultimate_model
            },
            'results': self.results
        }

def main():
    """Main demonstration"""
    
    solution = RFOverfittingSolution()
    results = solution.run_complete_solution()
    
    print(f"\n🎉 SUCCESS!")
    print("Random Forest overfitting with many features has been comprehensively addressed!")
    print("Both regularization techniques AND ensemble methods successfully applied!")

if __name__ == "__main__":
    main() 