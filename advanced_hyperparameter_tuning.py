#!/usr/bin/env python3
"""
🎯 Advanced Hyperparameter Tuning System
Comprehensive hyperparameter optimization for cryptocurrency trading models
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.model_selection import (
    GridSearchCV, RandomizedSearchCV, TimeSeriesSplit, 
    cross_val_score, validation_curve
)
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Advanced optimization libraries
try:
    from skopt import BayesSearchCV
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    from skopt import gp_minimize
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

try:
    import hyperopt
    from hyperopt import hp, fmin, tpe, Trials, STATUS_OK
    HYPEROPT_AVAILABLE = True
except ImportError:
    HYPEROPT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedHyperparameterTuner:
    """
    Advanced hyperparameter tuning system with multiple optimization strategies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.tuning_results = {}
        self.best_models = {}
        self.optimization_history = {}
        
        logger.info("🎯 Advanced Hyperparameter Tuner initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for hyperparameter tuning"""
        return {
            # Tuning strategies
            'strategies': ['grid_search', 'random_search', 'bayesian', 'optuna'],
            'primary_strategy': 'bayesian',
            
            # Cross-validation
            'cv_folds': 5,
            'cv_method': 'time_series',
            'test_size': 0.2,
            
            # Search parameters
            'n_iter_random': 100,
            'n_calls_bayesian': 50,
            'n_trials_optuna': 100,
            
            # Scoring
            'scoring': 'neg_mean_squared_error',
            'refit_metric': 'neg_mean_squared_error',
            
            # Performance
            'n_jobs': -1,
            'verbose': 1,
            'random_state': 42,
            
            # Early stopping
            'early_stopping': True,
            'patience': 10,
            'min_improvement': 0.001
        }
    
    def get_parameter_spaces(self) -> Dict[str, Dict]:
        """Get comprehensive parameter spaces for all models"""
        return {
            'random_forest': {
                'grid': {
                    'n_estimators': [100, 200, 300, 500],
                    'max_depth': [5, 10, 15, 20, None],
                    'min_samples_split': [2, 5, 10, 20],
                    'min_samples_leaf': [1, 2, 4, 8],
                    'max_features': ['sqrt', 'log2', 0.3, 0.5, 0.7],
                    'bootstrap': [True, False],
                    'max_samples': [0.7, 0.8, 0.9, None]
                },
                'random': {
                    'n_estimators': [50, 100, 200, 300, 500, 800],
                    'max_depth': [3, 5, 7, 10, 15, 20, 25, None],
                    'min_samples_split': [2, 5, 10, 15, 20, 25],
                    'min_samples_leaf': [1, 2, 4, 6, 8, 10],
                    'max_features': ['sqrt', 'log2', 0.2, 0.3, 0.5, 0.7, 0.9],
                    'bootstrap': [True, False],
                    'max_samples': [0.6, 0.7, 0.8, 0.9, None],
                    'criterion': ['squared_error', 'absolute_error', 'poisson']
                },
                'bayesian': [
                    Integer(50, 800, name='n_estimators'),
                    Integer(3, 30, name='max_depth'),
                    Integer(2, 25, name='min_samples_split'),
                    Integer(1, 10, name='min_samples_leaf'),
                    Categorical(['sqrt', 'log2', 0.3, 0.5, 0.7], name='max_features'),
                    Categorical([True, False], name='bootstrap'),
                    Categorical([0.7, 0.8, 0.9, None], name='max_samples')
                ]
            },
            
            'gradient_boosting': {
                'grid': {
                    'n_estimators': [100, 200, 300],
                    'learning_rate': [0.01, 0.05, 0.1, 0.2],
                    'max_depth': [3, 5, 7, 10],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'subsample': [0.8, 0.9, 1.0],
                    'max_features': ['sqrt', 'log2', None]
                },
                'random': {
                    'n_estimators': [50, 100, 200, 300, 500],
                    'learning_rate': [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.3],
                    'max_depth': [2, 3, 4, 5, 6, 7, 8, 10, 12],
                    'min_samples_split': [2, 5, 10, 15, 20],
                    'min_samples_leaf': [1, 2, 4, 6, 8],
                    'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
                    'max_features': ['sqrt', 'log2', 0.3, 0.5, 0.7, None],
                    'loss': ['squared_error', 'absolute_error', 'huber']
                },
                'bayesian': [
                    Integer(50, 500, name='n_estimators'),
                    Real(0.001, 0.3, name='learning_rate', prior='log-uniform'),
                    Integer(2, 12, name='max_depth'),
                    Integer(2, 20, name='min_samples_split'),
                    Integer(1, 8, name='min_samples_leaf'),
                    Real(0.6, 1.0, name='subsample'),
                    Categorical(['sqrt', 'log2', None], name='max_features')
                ]
            },
            
            'extra_trees': {
                'grid': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'max_features': ['sqrt', 'log2', 0.5]
                },
                'random': {
                    'n_estimators': [50, 100, 200, 300, 500],
                    'max_depth': [3, 5, 7, 10, 15, 20, None],
                    'min_samples_split': [2, 5, 10, 15, 20],
                    'min_samples_leaf': [1, 2, 4, 6, 8],
                    'max_features': ['sqrt', 'log2', 0.3, 0.5, 0.7, 0.9],
                    'bootstrap': [True, False]
                },
                'bayesian': [
                    Integer(50, 500, name='n_estimators'),
                    Integer(3, 25, name='max_depth'),
                    Integer(2, 20, name='min_samples_split'),
                    Integer(1, 8, name='min_samples_leaf'),
                    Categorical(['sqrt', 'log2', 0.5], name='max_features')
                ]
            },
            
            'ridge': {
                'grid': {
                    'alpha': [0.1, 1.0, 10.0, 100.0],
                    'solver': ['auto', 'svd', 'cholesky', 'lsqr']
                },
                'random': {
                    'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
                },
                'bayesian': [
                    Real(0.001, 1000.0, name='alpha', prior='log-uniform')
                ]
            },
            
            'lasso': {
                'grid': {
                    'alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
                    'max_iter': [1000, 2000, 5000]
                },
                'random': {
                    'alpha': [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
                    'max_iter': [500, 1000, 2000, 5000, 10000]
                },
                'bayesian': [
                    Real(0.0001, 100.0, name='alpha', prior='log-uniform'),
                    Integer(500, 10000, name='max_iter')
                ]
            },
            
            'elastic_net': {
                'grid': {
                    'alpha': [0.001, 0.01, 0.1, 1.0],
                    'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9],
                    'max_iter': [1000, 2000]
                },
                'random': {
                    'alpha': [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0],
                    'l1_ratio': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                    'max_iter': [500, 1000, 2000, 5000]
                },
                'bayesian': [
                    Real(0.0001, 10.0, name='alpha', prior='log-uniform'),
                    Real(0.1, 0.9, name='l1_ratio'),
                    Integer(500, 5000, name='max_iter')
                ]
            },
            
            'svr': {
                'grid': {
                    'C': [0.1, 1.0, 10.0, 100.0],
                    'epsilon': [0.01, 0.1, 0.2],
                    'kernel': ['rbf', 'linear', 'poly']
                },
                'random': {
                    'C': [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0],
                    'epsilon': [0.001, 0.01, 0.1, 0.2, 0.5],
                    'kernel': ['rbf', 'linear', 'poly', 'sigmoid'],
                    'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1.0]
                },
                'bayesian': [
                    Real(0.01, 1000.0, name='C', prior='log-uniform'),
                    Real(0.001, 0.5, name='epsilon'),
                    Categorical(['rbf', 'linear', 'poly'], name='kernel')
                ]
            },
            
            'knn': {
                'grid': {
                    'n_neighbors': [3, 5, 7, 9, 11],
                    'weights': ['uniform', 'distance'],
                    'algorithm': ['auto', 'ball_tree', 'kd_tree']
                },
                'random': {
                    'n_neighbors': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20],
                    'weights': ['uniform', 'distance'],
                    'algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute'],
                    'leaf_size': [10, 20, 30, 40, 50]
                },
                'bayesian': [
                    Integer(2, 20, name='n_neighbors'),
                    Categorical(['uniform', 'distance'], name='weights'),
                    Integer(10, 50, name='leaf_size')
                ]
            },
            
            'mlp': {
                'grid': {
                    'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
                    'activation': ['relu', 'tanh'],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate': ['constant', 'adaptive']
                },
                'random': {
                    'hidden_layer_sizes': [(50,), (100,), (150,), (50, 50), (100, 50), (100, 100), (150, 100, 50)],
                    'activation': ['relu', 'tanh', 'logistic'],
                    'alpha': [0.00001, 0.0001, 0.001, 0.01, 0.1],
                    'learning_rate': ['constant', 'invscaling', 'adaptive'],
                    'learning_rate_init': [0.001, 0.01, 0.1],
                    'max_iter': [200, 500, 1000]
                },
                'bayesian': [
                    Categorical([(50,), (100,), (150,), (50, 50), (100, 50)], name='hidden_layer_sizes'),
                    Categorical(['relu', 'tanh'], name='activation'),
                    Real(0.00001, 0.1, name='alpha', prior='log-uniform'),
                    Real(0.001, 0.1, name='learning_rate_init', prior='log-uniform')
                ]
            }
        }
    
    def get_model_instances(self) -> Dict[str, Any]:
        """Get model instances for tuning"""
        return {
            'random_forest': RandomForestRegressor(random_state=self.config['random_state']),
            'gradient_boosting': GradientBoostingRegressor(random_state=self.config['random_state']),
            'extra_trees': ExtraTreesRegressor(random_state=self.config['random_state']),
            'ridge': Ridge(),
            'lasso': Lasso(random_state=self.config['random_state']),
            'elastic_net': ElasticNet(random_state=self.config['random_state']),
            'svr': SVR(),
            'knn': KNeighborsRegressor(),
            'mlp': MLPRegressor(random_state=self.config['random_state'], max_iter=500)
        }
    
    def create_cv_strategy(self, X: np.ndarray, y: np.ndarray):
        """Create cross-validation strategy"""
        if self.config['cv_method'] == 'time_series':
            return TimeSeriesSplit(n_splits=self.config['cv_folds'])
        else:
            from sklearn.model_selection import KFold
            return KFold(n_splits=self.config['cv_folds'], shuffle=True, random_state=self.config['random_state'])
    
    def grid_search_tuning(self, 
                          model_name: str, 
                          X: np.ndarray, 
                          y: np.ndarray) -> Tuple[Any, Dict, float]:
        """Perform grid search hyperparameter tuning"""
        logger.info(f"🔍 Grid Search tuning for {model_name}...")
        
        model = self.get_model_instances()[model_name]
        param_grid = self.get_parameter_spaces()[model_name]['grid']
        cv = self.create_cv_strategy(X, y)
        
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=param_grid,
            cv=cv,
            scoring=self.config['scoring'],
            n_jobs=self.config['n_jobs'],
            verbose=self.config['verbose'],
            refit=True
        )
        
        grid_search.fit(X, y)
        
        logger.info(f"   Best score: {grid_search.best_score_:.4f}")
        logger.info(f"   Best params: {grid_search.best_params_}")
        
        return grid_search.best_estimator_, grid_search.best_params_, grid_search.best_score_
    
    def random_search_tuning(self, 
                           model_name: str, 
                           X: np.ndarray, 
                           y: np.ndarray) -> Tuple[Any, Dict, float]:
        """Perform randomized search hyperparameter tuning"""
        logger.info(f"🎲 Random Search tuning for {model_name}...")
        
        model = self.get_model_instances()[model_name]
        param_dist = self.get_parameter_spaces()[model_name]['random']
        cv = self.create_cv_strategy(X, y)
        
        random_search = RandomizedSearchCV(
            estimator=model,
            param_distributions=param_dist,
            n_iter=self.config['n_iter_random'],
            cv=cv,
            scoring=self.config['scoring'],
            n_jobs=self.config['n_jobs'],
            verbose=self.config['verbose'],
            random_state=self.config['random_state'],
            refit=True
        )
        
        random_search.fit(X, y)
        
        logger.info(f"   Best score: {random_search.best_score_:.4f}")
        logger.info(f"   Best params: {random_search.best_params_}")
        
        return random_search.best_estimator_, random_search.best_params_, random_search.best_score_
    
    def bayesian_optimization_tuning(self, 
                                   model_name: str, 
                                   X: np.ndarray, 
                                   y: np.ndarray) -> Tuple[Any, Dict, float]:
        """Perform Bayesian optimization hyperparameter tuning"""
        if not BAYESIAN_AVAILABLE:
            logger.warning("Bayesian optimization not available, falling back to random search")
            return self.random_search_tuning(model_name, X, y)
        
        logger.info(f"🧠 Bayesian Optimization tuning for {model_name}...")
        
        model = self.get_model_instances()[model_name]
        search_space = self.get_parameter_spaces()[model_name]['bayesian']
        cv = self.create_cv_strategy(X, y)
        
        bayes_search = BayesSearchCV(
            estimator=model,
            search_spaces=search_space,
            n_iter=self.config['n_calls_bayesian'],
            cv=cv,
            scoring=self.config['scoring'],
            n_jobs=self.config['n_jobs'],
            verbose=self.config['verbose'],
            random_state=self.config['random_state'],
            refit=True
        )
        
        bayes_search.fit(X, y)
        
        logger.info(f"   Best score: {bayes_search.best_score_:.4f}")
        logger.info(f"   Best params: {bayes_search.best_params_}")
        
        return bayes_search.best_estimator_, bayes_search.best_params_, bayes_search.best_score_
    
    def optuna_tuning(self, 
                     model_name: str, 
                     X: np.ndarray, 
                     y: np.ndarray) -> Tuple[Any, Dict, float]:
        """Perform Optuna hyperparameter tuning"""
        if not OPTUNA_AVAILABLE:
            logger.warning("Optuna not available, falling back to random search")
            return self.random_search_tuning(model_name, X, y)
        
        logger.info(f"⚡ Optuna tuning for {model_name}...")
        
        def objective(trial):
            # Define parameter suggestions based on model
            if model_name == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 800),
                    'max_depth': trial.suggest_int('max_depth', 3, 30),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 25),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                    'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', 0.3, 0.5, 0.7]),
                    'bootstrap': trial.suggest_categorical('bootstrap', [True, False])
                }
            elif model_name == 'gradient_boosting':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                    'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3, log=True),
                    'max_depth': trial.suggest_int('max_depth', 2, 12),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 8),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0)
                }
            else:
                # Fallback to random search for other models
                return self.random_search_tuning(model_name, X, y)
            
            model = self.get_model_instances()[model_name]
            model.set_params(**params)
            
            cv = self.create_cv_strategy(X, y)
            scores = cross_val_score(model, X, y, cv=cv, scoring=self.config['scoring'], n_jobs=1)
            return scores.mean()
        
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler())
        study.optimize(objective, n_trials=self.config['n_trials_optuna'], show_progress_bar=True)
        
        # Train best model
        best_params = study.best_params
        best_model = self.get_model_instances()[model_name]
        best_model.set_params(**best_params)
        best_model.fit(X, y)
        
        logger.info(f"   Best score: {study.best_value:.4f}")
        logger.info(f"   Best params: {best_params}")
        
        return best_model, best_params, study.best_value
    
    def comprehensive_model_tuning(self, 
                                 X: np.ndarray, 
                                 y: np.ndarray,
                                 models_to_tune: Optional[List[str]] = None) -> Dict[str, Dict]:
        """Perform comprehensive hyperparameter tuning for multiple models"""
        logger.info("🎯 Starting comprehensive model tuning...")
        
        if models_to_tune is None:
            models_to_tune = ['random_forest', 'gradient_boosting', 'extra_trees']
        
        results = {}
        
        for model_name in models_to_tune:
            logger.info(f"\n🔧 Tuning {model_name.upper()}...")
            
            model_results = {}
            
            # Try different tuning strategies
            strategies = self.config['strategies']
            if self.config['primary_strategy'] in strategies:
                # Prioritize primary strategy
                strategies = [self.config['primary_strategy']] + [s for s in strategies if s != self.config['primary_strategy']]
            
            best_score = float('-inf')
            best_model = None
            best_params = None
            best_strategy = None
            
            for strategy in strategies:
                try:
                    if strategy == 'grid_search':
                        model, params, score = self.grid_search_tuning(model_name, X, y)
                    elif strategy == 'random_search':
                        model, params, score = self.random_search_tuning(model_name, X, y)
                    elif strategy == 'bayesian':
                        model, params, score = self.bayesian_optimization_tuning(model_name, X, y)
                    elif strategy == 'optuna':
                        model, params, score = self.optuna_tuning(model_name, X, y)
                    else:
                        continue
                    
                    model_results[strategy] = {
                        'model': model,
                        'params': params,
                        'score': score
                    }
                    
                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_params = params
                        best_strategy = strategy
                    
                    logger.info(f"   {strategy}: {score:.4f}")
                    
                except Exception as e:
                    logger.error(f"   Error in {strategy}: {e}")
                    continue
            
            # Store best results
            results[model_name] = {
                'best_model': best_model,
                'best_params': best_params,
                'best_score': best_score,
                'best_strategy': best_strategy,
                'all_results': model_results
            }
            
            logger.info(f"✅ Best {model_name}: {best_score:.4f} ({best_strategy})")
        
        # Store results
        self.tuning_results = results
        
        # Find overall best model
        overall_best = max(results.items(), key=lambda x: x[1]['best_score'])
        logger.info(f"\n🏆 OVERALL BEST MODEL: {overall_best[0].upper()}")
        logger.info(f"   Score: {overall_best[1]['best_score']:.4f}")
        logger.info(f"   Strategy: {overall_best[1]['best_strategy']}")
        logger.info(f"   Params: {overall_best[1]['best_params']}")
        
        return results
    
    def validate_tuned_models(self, 
                            X: np.ndarray, 
                            y: np.ndarray,
                            test_size: float = 0.2) -> Dict[str, Dict]:
        """Validate tuned models on holdout test set"""
        logger.info("🧪 Validating tuned models...")
        
        # Split data
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        validation_results = {}
        
        for model_name, results in self.tuning_results.items():
            if 'best_model' not in results or results['best_model'] is None:
                continue
            
            model = results['best_model']
            
            # Retrain on training set
            model.fit(X_train, y_train)
            
            # Predict on test set
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            validation_results[model_name] = {
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'cv_score': results['best_score'],
                'params': results['best_params']
            }
            
            logger.info(f"   {model_name}: R² = {r2:.4f}, RMSE = {rmse:.4f}")
        
        return validation_results
    
    def learning_curve_analysis(self, 
                              model_name: str, 
                              X: np.ndarray, 
                              y: np.ndarray) -> Dict:
        """Analyze learning curves for the best model"""
        if model_name not in self.tuning_results:
            logger.error(f"Model {model_name} not found in tuning results")
            return {}
        
        logger.info(f"📈 Learning curve analysis for {model_name}...")
        
        from sklearn.model_selection import learning_curve
        
        best_model = self.tuning_results[model_name]['best_model']
        cv = self.create_cv_strategy(X, y)
        
        train_sizes = np.linspace(0.1, 1.0, 10)
        
        train_sizes_abs, train_scores, val_scores = learning_curve(
            best_model, X, y, 
            train_sizes=train_sizes,
            cv=cv,
            scoring=self.config['scoring'],
            n_jobs=self.config['n_jobs']
        )
        
        return {
            'train_sizes': train_sizes_abs,
            'train_scores_mean': np.mean(train_scores, axis=1),
            'train_scores_std': np.std(train_scores, axis=1),
            'val_scores_mean': np.mean(val_scores, axis=1),
            'val_scores_std': np.std(val_scores, axis=1)
        }
    
    def feature_importance_analysis(self, 
                                  model_name: str, 
                                  feature_names: List[str]) -> pd.DataFrame:
        """Analyze feature importance for tree-based models"""
        if model_name not in self.tuning_results:
            logger.error(f"Model {model_name} not found in tuning results")
            return pd.DataFrame()
        
        model = self.tuning_results[model_name]['best_model']
        
        if hasattr(model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info(f"📊 Top 10 features for {model_name}:")
            for _, row in importance_df.head(10).iterrows():
                logger.info(f"   {row['feature']}: {row['importance']:.4f}")
            
            return importance_df
        else:
            logger.warning(f"Model {model_name} does not have feature_importances_ attribute")
            return pd.DataFrame()
    
    def export_tuning_results(self, filepath: str):
        """Export tuning results to file"""
        import json
        
        # Prepare results for JSON serialization
        export_data = {}
        for model_name, results in self.tuning_results.items():
            export_data[model_name] = {
                'best_params': results['best_params'],
                'best_score': results['best_score'],
                'best_strategy': results['best_strategy']
            }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"📁 Tuning results exported to {filepath}")

def main():
    """Demonstration of advanced hyperparameter tuning"""
    
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    n_features = 20
    
    # Create realistic financial time series features
    X = np.random.randn(n_samples, n_features)
    # Add some correlation structure
    for i in range(1, n_features):
        X[:, i] = 0.7 * X[:, i-1] + 0.3 * X[:, i]
    
    # Create target with some non-linear relationships
    y = (
        2 * X[:, 0] + 
        1.5 * X[:, 1] * X[:, 2] + 
        0.5 * np.sin(X[:, 3]) +
        0.3 * X[:, 4]**2 +
        np.random.randn(n_samples) * 0.1
    )
    
    # Initialize tuner
    tuner = AdvancedHyperparameterTuner()
    
    print("🎯 Advanced Hyperparameter Tuning Demonstration")
    print("=" * 60)
    
    # Comprehensive model tuning
    models_to_tune = ['random_forest', 'gradient_boosting', 'extra_trees']
    
    tuning_results = tuner.comprehensive_model_tuning(
        X, y, models_to_tune=models_to_tune
    )
    
    # Validate models
    print(f"\n🧪 MODEL VALIDATION RESULTS:")
    print("=" * 40)
    
    validation_results = tuner.validate_tuned_models(X, y)
    
    for model_name, metrics in validation_results.items():
        print(f"\n📊 {model_name.upper()}:")
        print(f"   R² Score: {metrics['r2']:.4f}")
        print(f"   RMSE: {metrics['rmse']:.4f}")
        print(f"   MAE: {metrics['mae']:.4f}")
        print(f"   CV Score: {metrics['cv_score']:.4f}")
    
    # Feature importance analysis
    feature_names = [f'feature_{i}' for i in range(n_features)]
    
    print(f"\n🔍 FEATURE IMPORTANCE ANALYSIS:")
    print("=" * 40)
    
    for model_name in ['random_forest', 'gradient_boosting']:
        if model_name in tuning_results:
            importance_df = tuner.feature_importance_analysis(model_name, feature_names)
    
    # Learning curve analysis
    print(f"\n📈 LEARNING CURVE ANALYSIS:")
    print("=" * 40)
    
    best_model_name = max(validation_results.items(), key=lambda x: x[1]['r2'])[0]
    learning_curves = tuner.learning_curve_analysis(best_model_name, X, y)
    
    if learning_curves:
        final_train_score = learning_curves['train_scores_mean'][-1]
        final_val_score = learning_curves['val_scores_mean'][-1]
        print(f"   Final Training Score: {final_train_score:.4f}")
        print(f"   Final Validation Score: {final_val_score:.4f}")
        print(f"   Overfitting Gap: {final_train_score - final_val_score:.4f}")
    
    # Export results
    tuner.export_tuning_results('hyperparameter_tuning_results.json')
    
    print(f"\n🎯 HYPERPARAMETER TUNING ADVANTAGES:")
    print("=" * 50)
    print("✅ Multiple Optimization Strategies: Grid, Random, Bayesian, Optuna")
    print("✅ Time Series Cross-Validation: Proper temporal validation")
    print("✅ Comprehensive Parameter Spaces: Extensive parameter coverage")
    print("✅ Model Comparison: Automatic best model selection")
    print("✅ Validation Framework: Holdout test set validation")
    print("✅ Learning Curve Analysis: Overfitting detection")
    print("✅ Feature Importance: Model interpretability")
    print("✅ Results Export: Reproducible configurations")
    
    print(f"\n📊 PERFORMANCE IMPROVEMENTS:")
    print("• Optimization Strategies: 4 advanced methods vs manual tuning")
    print("• Parameter Coverage: 100+ combinations vs default parameters")
    print("• Validation Rigor: Time series CV vs simple train/test split")
    print("• Model Selection: Automated best model vs single model")
    print("• Reproducibility: Exported configurations vs ad-hoc tuning")
    
    print(f"\n✅ Advanced hyperparameter tuning demonstration completed!")

if __name__ == "__main__":
    main() 