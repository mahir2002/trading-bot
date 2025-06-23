#!/usr/bin/env python3
"""
🚀 ENHANCED SCIKIT-LEARN TRADING CLASSIFIER 🚀
==============================================

Advanced machine learning classification system for the Ultimate Unified AI Trading Bot
using cutting-edge scikit-learn algorithms from official documentation.

Based on: https://scikit-learn.org/stable/auto_examples/classification/index.html
"""

import os
import sys
import numpy as np
import pandas as pd
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
import joblib

# Scikit-learn imports - Advanced Classification Algorithms
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier,
    VotingClassifier, BaggingClassifier, ExtraTreesClassifier
)
from sklearn.svm import SVC, NuSVC
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.linear_model import (
    LogisticRegression, SGDClassifier, RidgeClassifier, 
    PassiveAggressiveClassifier, Perceptron
)
from sklearn.tree import DecisionTreeClassifier, ExtraTreeClassifier
from sklearn.neighbors import KNeighborsClassifier, RadiusNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF, Matern, RationalQuadratic, ExpSineSquared

# Model Selection and Evaluation
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV,
    StratifiedKFold, cross_validate, validation_curve, learning_curve
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    classification_report, confusion_matrix, roc_curve, precision_recall_curve
)

# Preprocessing and Feature Engineering
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, QuantileTransformer,
    LabelEncoder, OneHotEncoder, PolynomialFeatures
)
from sklearn.feature_selection import (
    SelectKBest, f_classif, mutual_info_classif, RFE, RFECV,
    SelectFromModel, VarianceThreshold
)
from sklearn.decomposition import PCA, FastICA, TruncatedSVD
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.compose import ColumnTransformer

# Advanced Techniques
from sklearn.calibration import CalibratedClassifierCV
from sklearn.multiclass import OneVsRestClassifier, OneVsOneClassifier
from sklearn.semi_supervised import LabelPropagation, LabelSpreading

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedSklearnTradingClassifier:
    """
    🚀 ENHANCED SCIKIT-LEARN TRADING CLASSIFIER 🚀
    
    Advanced machine learning classification system using cutting-edge
    scikit-learn algorithms for cryptocurrency trading predictions.
    
    Features:
    - 15+ Advanced Classification Algorithms
    - Ensemble Methods with Voting
    - Hyperparameter Optimization
    - Feature Engineering Pipeline
    - Model Calibration
    - Cross-Validation
    - Performance Analytics
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the enhanced classifier system"""
        self.config = config or {}
        self.models = {}
        self.ensemble_model = None
        self.feature_pipeline = None
        self.scalers = {}
        self.feature_selectors = {}
        self.performance_metrics = {}
        
        # Initialize all classification algorithms
        self._init_classification_algorithms()
        self._init_feature_engineering_pipeline()
        
        logger.info("🚀 Enhanced Scikit-learn Trading Classifier initialized")
        logger.info(f"   📊 {len(self.models)} classification algorithms ready")
    
    def _init_classification_algorithms(self):
        """Initialize all advanced classification algorithms from scikit-learn"""
        
        # 1. Ensemble Methods (Most Powerful)
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_split=5,
            min_samples_leaf=2, max_features='sqrt', random_state=42, n_jobs=-1
        )
        
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.1, max_depth=8,
            min_samples_split=5, min_samples_leaf=2, random_state=42
        )
        
        self.models['extra_trees'] = ExtraTreesClassifier(
            n_estimators=200, max_depth=15, min_samples_split=5,
            min_samples_leaf=2, random_state=42, n_jobs=-1
        )
        
        self.models['ada_boost'] = AdaBoostClassifier(
            n_estimators=100, learning_rate=1.0, random_state=42
        )
        
        self.models['bagging'] = BaggingClassifier(
            n_estimators=100, max_samples=0.8, max_features=0.8,
            random_state=42, n_jobs=-1
        )
        
        # 2. Support Vector Machines
        self.models['svm_rbf'] = SVC(
            kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42
        )
        
        self.models['svm_poly'] = SVC(
            kernel='poly', degree=3, C=1.0, probability=True, random_state=42
        )
        
        self.models['nu_svm'] = NuSVC(
            nu=0.5, kernel='rbf', probability=True, random_state=42
        )
        
        # 3. Neural Networks
        self.models['mlp_classifier'] = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25), activation='relu',
            solver='adam', alpha=0.001, learning_rate='adaptive',
            max_iter=500, random_state=42
        )
        
        # 4. Linear Models
        self.models['logistic_regression'] = LogisticRegression(
            C=1.0, solver='liblinear', multi_class='ovr', random_state=42
        )
        
        self.models['sgd_classifier'] = SGDClassifier(
            loss='hinge', alpha=0.01, random_state=42, max_iter=1000
        )
        
        self.models['ridge_classifier'] = RidgeClassifier(
            alpha=1.0, random_state=42
        )
        
        # 5. Naive Bayes
        self.models['gaussian_nb'] = GaussianNB()
        self.models['multinomial_nb'] = MultinomialNB()
        self.models['bernoulli_nb'] = BernoulliNB()
        
        # 6. Tree-based Models
        self.models['decision_tree'] = DecisionTreeClassifier(
            max_depth=15, min_samples_split=5, min_samples_leaf=2, random_state=42
        )
        
        # 7. Nearest Neighbors
        self.models['knn'] = KNeighborsClassifier(
            n_neighbors=5, weights='distance', algorithm='auto'
        )
        
        # 8. Discriminant Analysis
        self.models['lda'] = LinearDiscriminantAnalysis()
        self.models['qda'] = QuadraticDiscriminantAnalysis()
        
        # 9. Gaussian Process (Advanced)
        self.models['gaussian_process'] = GaussianProcessClassifier(
            kernel=1.0 * RBF(1.0), random_state=42
        )
        
        logger.info(f"✅ Initialized {len(self.models)} classification algorithms")
    
    def _init_feature_engineering_pipeline(self):
        """Initialize advanced feature engineering pipeline"""
        
        # Feature scaling options
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler(),
            'quantile': QuantileTransformer(output_distribution='uniform')
        }
        
        # Feature selection methods
        self.feature_selectors = {
            'k_best': SelectKBest(f_classif, k=20),
            'mutual_info': SelectKBest(mutual_info_classif, k=20),
            'variance': VarianceThreshold(threshold=0.01),
            'rfe': RFE(RandomForestClassifier(n_estimators=50, random_state=42), n_features_to_select=20)
        }
        
        logger.info("✅ Feature engineering pipeline initialized")
    
    def create_ensemble_model(self):
        """Create advanced ensemble model with voting"""
        
        # Select best performing models for ensemble
        ensemble_models = [
            ('rf', self.models['random_forest']),
            ('gb', self.models['gradient_boosting']),
            ('et', self.models['extra_trees']),
            ('svm', self.models['svm_rbf']),
            ('mlp', self.models['mlp_classifier']),
            ('lr', self.models['logistic_regression'])
        ]
        
        # Create voting classifier with soft voting for probability estimates
        self.ensemble_model = VotingClassifier(
            estimators=ensemble_models,
            voting='soft',
            n_jobs=-1
        )
        
        logger.info("✅ Advanced ensemble model created with 6 algorithms")
        return self.ensemble_model
    
    def prepare_features(self, data: pd.DataFrame, target_column: str = 'target') -> Tuple[np.ndarray, np.ndarray]:
        """Advanced feature preparation and engineering"""
        
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Separate features and target
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Create polynomial features for non-linear relationships
        poly_features = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
        X_poly = poly_features.fit_transform(X)
        
        # Feature selection
        selector = self.feature_selectors['k_best']
        X_selected = selector.fit_transform(X_poly, y)
        
        # Feature scaling
        scaler = self.scalers['standard']
        X_scaled = scaler.fit_transform(X_selected)
        
        # Store preprocessing objects
        self.poly_features = poly_features
        self.feature_selector = selector
        self.feature_scaler = scaler
        
        logger.info(f"✅ Features prepared: {X_scaled.shape[1]} features from {X.shape[1]} original")
        
        return X_scaled, y.values
    
    def train_all_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Dict]:
        """Train all classification models with cross-validation"""
        
        results = {}
        cv_folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        logger.info("🚀 Training all classification models...")
        
        for model_name, model in self.models.items():
            try:
                logger.info(f"   🔄 Training {model_name}...")
                
                # Cross-validation scores
                cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='accuracy', n_jobs=-1)
                
                # Train on full dataset
                model.fit(X, y)
                
                # Store results
                results[model_name] = {
                    'model': model,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'cv_scores': cv_scores
                }
                
                logger.info(f"   ✅ {model_name}: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
                
            except Exception as e:
                logger.error(f"   ❌ {model_name} training failed: {e}")
                continue
        
        # Train ensemble model
        if len(results) >= 3:
            logger.info("   🔄 Training ensemble model...")
            ensemble = self.create_ensemble_model()
            cv_scores = cross_val_score(ensemble, X, y, cv=cv_folds, scoring='accuracy', n_jobs=-1)
            ensemble.fit(X, y)
            
            results['ensemble'] = {
                'model': ensemble,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'cv_scores': cv_scores
            }
            
            logger.info(f"   ✅ ensemble: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        self.performance_metrics = results
        logger.info(f"✅ Trained {len(results)} models successfully")
        
        return results
    
    def hyperparameter_optimization(self, X: np.ndarray, y: np.ndarray, model_name: str = 'random_forest'):
        """Perform hyperparameter optimization using GridSearchCV"""
        
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        logger.info(f"🔧 Optimizing hyperparameters for {model_name}...")
        
        # Define parameter grids for different models
        param_grids = {
            'random_forest': {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 15, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            'gradient_boosting': {
                'n_estimators': [100, 150, 200],
                'learning_rate': [0.05, 0.1, 0.2],
                'max_depth': [6, 8, 10],
                'min_samples_split': [2, 5, 10]
            },
            'svm_rbf': {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1]
            },
            'logistic_regression': {
                'C': [0.01, 0.1, 1, 10, 100],
                'solver': ['liblinear', 'lbfgs'],
                'penalty': ['l1', 'l2']
            }
        }
        
        if model_name not in param_grids:
            logger.warning(f"No parameter grid defined for {model_name}")
            return None
        
        # Perform grid search
        grid_search = GridSearchCV(
            self.models[model_name],
            param_grids[model_name],
            cv=5,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # Update model with best parameters
        self.models[model_name] = grid_search.best_estimator_
        
        logger.info(f"✅ Best parameters for {model_name}: {grid_search.best_params_}")
        logger.info(f"✅ Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def get_feature_importance(self, model_name: str = 'random_forest') -> Dict[str, float]:
        """Get feature importance from tree-based models"""
        
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        model = self.models[model_name]
        
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_names = [f'feature_{i}' for i in range(len(importances))]
            
            importance_dict = dict(zip(feature_names, importances))
            sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            
            logger.info(f"✅ Feature importance extracted from {model_name}")
            return sorted_importance
        else:
            logger.warning(f"Model '{model_name}' does not support feature importance")
            return {}
    
    def predict_with_confidence(self, X: np.ndarray, model_name: str = 'ensemble') -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions with confidence scores"""
        
        if model_name == 'ensemble' and self.ensemble_model is not None:
            model = self.ensemble_model
        elif model_name in self.models:
            model = self.models[model_name]
        else:
            raise ValueError(f"Model '{model_name}' not found")
        
        # Make predictions
        predictions = model.predict(X)
        
        # Get prediction probabilities for confidence
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(X)
            confidence = np.max(probabilities, axis=1)
        else:
            confidence = np.ones(len(predictions)) * 0.5  # Default confidence
        
        return predictions, confidence
    
    def evaluate_model_performance(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Dict]:
        """Comprehensive model evaluation"""
        
        evaluation_results = {}
        
        for model_name, model_info in self.performance_metrics.items():
            model = model_info['model']
            
            try:
                # Make predictions
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                
                # ROC AUC for binary classification
                try:
                    if hasattr(model, 'predict_proba') and len(np.unique(y_test)) == 2:
                        y_proba = model.predict_proba(X_test)[:, 1]
                        roc_auc = roc_auc_score(y_test, y_proba)
                    else:
                        roc_auc = None
                except:
                    roc_auc = None
                
                evaluation_results[model_name] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'roc_auc': roc_auc,
                    'cv_mean': model_info['cv_mean'],
                    'cv_std': model_info['cv_std']
                }
                
            except Exception as e:
                logger.error(f"Evaluation failed for {model_name}: {e}")
                continue
        
        return evaluation_results
    
    def save_models(self, directory: str = "enhanced_sklearn_models"):
        """Save all trained models"""
        
        os.makedirs(directory, exist_ok=True)
        
        # Save individual models
        for model_name, model_info in self.performance_metrics.items():
            model_path = os.path.join(directory, f"{model_name}_model.joblib")
            joblib.dump(model_info['model'], model_path)
        
        # Save preprocessing objects
        if hasattr(self, 'feature_scaler'):
            joblib.dump(self.feature_scaler, os.path.join(directory, "feature_scaler.joblib"))
        if hasattr(self, 'feature_selector'):
            joblib.dump(self.feature_selector, os.path.join(directory, "feature_selector.joblib"))
        if hasattr(self, 'poly_features'):
            joblib.dump(self.poly_features, os.path.join(directory, "poly_features.joblib"))
        
        logger.info(f"✅ All models saved to {directory}")
    
    def load_models(self, directory: str = "enhanced_sklearn_models"):
        """Load saved models"""
        
        if not os.path.exists(directory):
            raise ValueError(f"Directory '{directory}' not found")
        
        # Load preprocessing objects
        scaler_path = os.path.join(directory, "feature_scaler.joblib")
        if os.path.exists(scaler_path):
            self.feature_scaler = joblib.load(scaler_path)
        
        selector_path = os.path.join(directory, "feature_selector.joblib")
        if os.path.exists(selector_path):
            self.feature_selector = joblib.load(selector_path)
        
        poly_path = os.path.join(directory, "poly_features.joblib")
        if os.path.exists(poly_path):
            self.poly_features = joblib.load(poly_path)
        
        # Load models
        for model_name in self.models.keys():
            model_path = os.path.join(directory, f"{model_name}_model.joblib")
            if os.path.exists(model_path):
                self.models[model_name] = joblib.load(model_path)
        
        # Load ensemble model
        ensemble_path = os.path.join(directory, "ensemble_model.joblib")
        if os.path.exists(ensemble_path):
            self.ensemble_model = joblib.load(ensemble_path)
        
        logger.info(f"✅ Models loaded from {directory}")
    
    def generate_trading_signals(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals using the ensemble of classifiers"""
        
        if self.ensemble_model is None:
            logger.warning("Ensemble model not trained. Using Random Forest.")
            model = self.models['random_forest']
        else:
            model = self.ensemble_model
        
        # Prepare features
        X = market_data.values
        
        # Apply preprocessing if available
        if hasattr(self, 'poly_features'):
            X = self.poly_features.transform(X)
        if hasattr(self, 'feature_selector'):
            X = self.feature_selector.transform(X)
        if hasattr(self, 'feature_scaler'):
            X = self.feature_scaler.transform(X)
        
        # Make predictions
        predictions, confidence = self.predict_with_confidence(X, 'ensemble' if self.ensemble_model else 'random_forest')
        
        # Convert predictions to trading signals
        signal_mapping = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
        signals = [signal_mapping.get(pred, 'HOLD') for pred in predictions]
        
        return {
            'signals': signals,
            'confidence': confidence,
            'predictions': predictions,
            'model_used': 'ensemble' if self.ensemble_model else 'random_forest'
        }

def generate_demo_trading_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate realistic demo trading data for testing"""
    
    np.random.seed(42)
    
    # Generate base features
    data = {
        'price': np.random.uniform(100, 1000, n_samples),
        'volume': np.random.uniform(1000000, 10000000, n_samples),
        'rsi': np.random.uniform(20, 80, n_samples),
        'macd': np.random.normal(0, 0.1, n_samples),
        'bollinger_position': np.random.uniform(0, 1, n_samples),
        'sma_20': np.random.uniform(95, 105, n_samples),
        'ema_12': np.random.uniform(95, 105, n_samples),
        'volatility': np.random.uniform(0.01, 0.1, n_samples),
        'returns_1d': np.random.normal(0, 0.02, n_samples),
        'returns_5d': np.random.normal(0, 0.05, n_samples),
        'sentiment_score': np.random.uniform(-1, 1, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Generate target based on features (realistic trading logic)
    df['target'] = 0  # Default HOLD
    
    # BUY conditions
    buy_condition = (
        (df['rsi'] < 30) & 
        (df['macd'] > 0) & 
        (df['sentiment_score'] > 0.2) &
        (df['returns_1d'] > 0)
    )
    df.loc[buy_condition, 'target'] = 2
    
    # SELL conditions
    sell_condition = (
        (df['rsi'] > 70) & 
        (df['macd'] < 0) & 
        (df['sentiment_score'] < -0.2) &
        (df['returns_1d'] < 0)
    )
    df.loc[sell_condition, 'target'] = 0
    
    # Everything else is HOLD (1)
    df.loc[(~buy_condition) & (~sell_condition), 'target'] = 1
    
    return df

def main():
    """Demo of the Enhanced Scikit-learn Trading Classifier"""
    
    print("🚀 ENHANCED SCIKIT-LEARN TRADING CLASSIFIER DEMO")
    print("=" * 60)
    print("Advanced machine learning for cryptocurrency trading")
    print("Based on: https://scikit-learn.org/stable/auto_examples/classification/index.html")
    print()
    
    # Initialize classifier
    classifier = EnhancedSklearnTradingClassifier()
    
    # Generate demo data
    print("📊 Generating demo trading data...")
    data = generate_demo_trading_data(2000)
    print(f"✅ Generated {len(data)} samples with {data.shape[1]-1} features")
    print(f"   Target distribution: {data['target'].value_counts().to_dict()}")
    print()
    
    # Prepare features
    print("🔧 Preparing features...")
    X, y = classifier.prepare_features(data)
    print(f"✅ Features prepared: {X.shape}")
    print()
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train all models
    print("🚀 Training all classification models...")
    results = classifier.train_all_models(X_train, y_train)
    print()
    
    # Hyperparameter optimization for best model
    best_model = max(results.items(), key=lambda x: x[1]['cv_mean'])
    print(f"🔧 Optimizing hyperparameters for best model: {best_model[0]}")
    classifier.hyperparameter_optimization(X_train, y_train, best_model[0])
    print()
    
    # Evaluate models
    print("📊 Evaluating model performance...")
    evaluation = classifier.evaluate_model_performance(X_test, y_test)
    
    print("\n🏆 MODEL PERFORMANCE RESULTS:")
    print("-" * 60)
    for model_name, metrics in evaluation.items():
        print(f"{model_name:20s} | Accuracy: {metrics['accuracy']:.4f} | "
              f"F1: {metrics['f1_score']:.4f} | CV: {metrics['cv_mean']:.4f}")
    
    # Feature importance
    print("\n🔍 FEATURE IMPORTANCE (Random Forest):")
    print("-" * 40)
    importance = classifier.get_feature_importance('random_forest')
    for feature, score in list(importance.items())[:10]:
        print(f"{feature:15s} | {score:.4f}")
    
    # Save models
    print("\n💾 Saving models...")
    classifier.save_models()
    
    # Generate trading signals demo
    print("\n📈 TRADING SIGNALS DEMO:")
    print("-" * 30)
    demo_data = data[['price', 'volume', 'rsi', 'macd', 'bollinger_position', 
                     'sma_20', 'ema_12', 'volatility', 'returns_1d', 'returns_5d', 'sentiment_score']].head(10)
    
    signals = classifier.generate_trading_signals(demo_data)
    
    for i, (signal, conf) in enumerate(zip(signals['signals'], signals['confidence'])):
        print(f"Sample {i+1:2d} | Signal: {signal:4s} | Confidence: {conf:.3f}")
    
    print("\n🎉 ENHANCED SCIKIT-LEARN CLASSIFIER DEMO COMPLETE!")
    print(f"✅ {len(results)} models trained and evaluated")
    print(f"✅ Best model: {best_model[0]} (CV: {best_model[1]['cv_mean']:.4f})")
    print("✅ Ready for integration with Ultimate Unified AI Trading Bot!")

if __name__ == "__main__":
    main() 