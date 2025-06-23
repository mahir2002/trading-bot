#!/usr/bin/env python3
"""
🧠 Advanced ML Models for Cryptocurrency Trading
Comprehensive implementation of LSTM, Transformer, ARIMA, GARCH models
with sentiment and news data integration
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Core ML libraries
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import xgboost as xgb
    import lightgbm as lgb
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Deep Learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (LSTM, GRU, Dense, Dropout, Input, 
                                       MultiHeadAttention, LayerNormalization,
                                       GlobalAveragePooling1D, Embedding, 
                                       Conv1D, MaxPooling1D, Flatten)
    from tensorflow.keras.optimizers import Adam, RMSprop
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# Statistical models
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    from arch import arch_model
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

# Technical indicators
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    try:
        import ta
        TA_AVAILABLE = True
    except ImportError:
        TA_AVAILABLE = False

# Sentiment analysis
try:
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    import feedparser
    import requests
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """Advanced feature engineering with sentiment and news integration"""
    
    def __init__(self):
        self.scaler = RobustScaler() if SKLEARN_AVAILABLE else None
        self.sentiment_analyzer = SentimentIntensityAnalyzer() if SENTIMENT_AVAILABLE else None
        self.feature_names = []
        
    def engineer_comprehensive_features(self, df: pd.DataFrame, 
                                      sentiment_data: Optional[Dict] = None,
                                      news_data: Optional[List] = None) -> pd.DataFrame:
        """Create comprehensive feature set including sentiment and news"""
        features = df.copy()
        
        # Technical features
        features = self._add_technical_features(features)
        
        # Market microstructure features
        features = self._add_microstructure_features(features)
        
        # Volatility modeling features
        features = self._add_volatility_features(features)
        
        # Regime detection features
        features = self._add_regime_features(features)
        
        # Sentiment features
        if sentiment_data:
            features = self._add_sentiment_features(features, sentiment_data)
        
        # News features
        if news_data:
            features = self._add_news_features(features, news_data)
        
        # Cross-asset features
        features = self._add_cross_asset_features(features)
        
        # Time-based features
        features = self._add_temporal_features(features)
        
        return features.dropna()
    
    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators"""
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['price_momentum'] = df['close'] / df['close'].shift(10) - 1
        df['price_acceleration'] = df['returns'].diff()
        
        # Moving averages (multiple timeframes)
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            df[f'price_above_sma_{period}'] = (df['close'] > df[f'sma_{period}']).astype(int)
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # RSI and momentum
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        df['macd_bullish'] = (df['macd'] > df['macd_signal']).astype(int)
        
        # Volume features
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['volume_price_trend'] = df['volume'] * df['returns']
        df['on_balance_volume'] = (df['volume'] * np.sign(df['returns'])).cumsum()
        
        return df
    
    def _add_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market microstructure features"""
        # Price impact measures
        df['price_impact'] = abs(df['returns']) / (df['volume'] / df['volume'].rolling(20).mean())
        
        # Bid-ask spread proxy
        df['spread_proxy'] = (df['high'] - df['low']) / df['close']
        
        # Market efficiency measures
        df['hurst_exponent'] = df['returns'].rolling(50).apply(self._calculate_hurst)
        
        # Liquidity measures
        df['amihud_illiquidity'] = abs(df['returns']) / df['volume']
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility modeling features"""
        # Historical volatility
        for window in [5, 10, 20, 50]:
            df[f'volatility_{window}'] = df['returns'].rolling(window=window).std()
        
        # GARCH-like volatility
        df['garch_vol'] = self._calculate_garch_volatility(df['returns'])
        
        # Volatility regime
        vol_threshold = df['volatility_20'].rolling(100).quantile(0.7)
        df['high_vol_regime'] = (df['volatility_20'] > vol_threshold).astype(int)
        
        # Volatility clustering
        df['vol_clustering'] = (df['volatility_20'] > df['volatility_20'].shift(1)).astype(int)
        
        return df
    
    def _add_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market regime detection features"""
        # Trend regime
        df['trend_strength'] = abs(df['close'].rolling(20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
        ))
        trend_threshold = df['trend_strength'].rolling(100).quantile(0.7)
        df['strong_trend_regime'] = (df['trend_strength'] > trend_threshold).astype(int)
        
        # Market stress indicator
        df['market_stress'] = (
            (df['rsi'] < 30).astype(int) + 
            (df['rsi'] > 70).astype(int) + 
            df['high_vol_regime']
        )
        
        return df
    
    def _add_sentiment_features(self, df: pd.DataFrame, sentiment_data: Dict) -> pd.DataFrame:
        """Add sentiment-based features"""
        # Overall sentiment score
        df['sentiment_score'] = sentiment_data.get('overall_sentiment', 0.0)
        
        # Fear & Greed Index
        df['fear_greed_index'] = sentiment_data.get('fear_greed_index', 50)
        df['extreme_fear'] = (df['fear_greed_index'] < 25).astype(int)
        df['extreme_greed'] = (df['fear_greed_index'] > 75).astype(int)
        
        # Social media sentiment
        df['twitter_sentiment'] = sentiment_data.get('twitter_sentiment', 0.0)
        df['reddit_sentiment'] = sentiment_data.get('reddit_sentiment', 0.0)
        df['social_volume'] = sentiment_data.get('social_volume', 0)
        
        # Sentiment momentum
        df['sentiment_momentum'] = df['sentiment_score'].diff()
        df['sentiment_volatility'] = df['sentiment_score'].rolling(10).std()
        
        return df
    
    def _add_news_features(self, df: pd.DataFrame, news_data: List) -> pd.DataFrame:
        """Add news-based features"""
        # News sentiment aggregation
        news_sentiments = []
        for article in news_data:
            if self.sentiment_analyzer:
                sentiment = self.sentiment_analyzer.polarity_scores(article.get('title', ''))
                news_sentiments.append(sentiment['compound'])
        
        avg_news_sentiment = np.mean(news_sentiments) if news_sentiments else 0.0
        df['news_sentiment'] = avg_news_sentiment
        df['news_volume'] = len(news_data)
        
        # News impact score
        df['news_impact'] = abs(avg_news_sentiment) * np.log(1 + len(news_data))
        
        return df
    
    def _add_cross_asset_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cross-asset correlation features"""
        # Auto-correlation
        df['auto_correlation'] = df['returns'].rolling(20).apply(
            lambda x: x.autocorr(lag=1) if len(x) > 1 else 0
        )
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_market_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 16)).astype(int)
        
        return df
    
    def _calculate_hurst(self, series):
        """Calculate Hurst exponent for market efficiency"""
        try:
            if len(series) < 10:
                return 0.5
            
            lags = range(2, min(20, len(series)//2))
            tau = [np.sqrt(np.std(np.subtract(series[lag:], series[:-lag]))) for lag in lags]
            poly = np.polyfit(np.log(lags), np.log(tau), 1)
            return poly[0] * 2.0
        except:
            return 0.5
    
    def _calculate_garch_volatility(self, returns: pd.Series, window: int = 20) -> pd.Series:
        """Calculate GARCH-like volatility"""
        alpha, beta = 0.1, 0.85
        vol = returns.rolling(window).std()
        garch_vol = vol.copy()
        
        for i in range(1, len(returns)):
            if not pd.isna(vol.iloc[i-1]):
                garch_vol.iloc[i] = np.sqrt(
                    alpha * returns.iloc[i-1]**2 + 
                    beta * garch_vol.iloc[i-1]**2
                )
        
        return garch_vol

class LSTMPredictor:
    """Advanced LSTM model for time series prediction"""
    
    def __init__(self, sequence_length: int = 60, features: int = 50):
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.scaler = MinMaxScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        
    def build_model(self) -> Optional[Model]:
        """Build advanced LSTM architecture"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available")
            return None
        
        try:
            model = Sequential([
                # First LSTM layer
                LSTM(128, return_sequences=True, input_shape=(self.sequence_length, self.features)),
                Dropout(0.2),
                
                # Second LSTM layer
                LSTM(64, return_sequences=True),
                Dropout(0.2),
                
                # Third LSTM layer
                LSTM(32, return_sequences=False),
                Dropout(0.2),
                
                # Dense layers
                Dense(50, activation='relu'),
                Dropout(0.1),
                Dense(25, activation='relu'),
                Dense(1, activation='linear')
            ])
            
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error building LSTM model: {e}")
            return None
    
    def train(self, X: np.ndarray, y: np.ndarray, validation_split: float = 0.2) -> bool:
        """Train the LSTM model"""
        if not TENSORFLOW_AVAILABLE or X.size == 0:
            return False
        
        try:
            self.model = self.build_model()
            if self.model is None:
                return False
            
            # Callbacks
            early_stopping = EarlyStopping(
                monitor='val_loss', 
                patience=15, 
                restore_best_weights=True
            )
            reduce_lr = ReduceLROnPlateau(
                monitor='val_loss', 
                factor=0.5, 
                patience=10, 
                min_lr=0.0001
            )
            
            # Train model
            history = self.model.fit(
                X, y,
                epochs=100,
                batch_size=32,
                validation_split=validation_split,
                callbacks=[early_stopping, reduce_lr],
                verbose=0
            )
            
            self.is_trained = True
            logger.info("✅ LSTM model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training LSTM: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained or self.model is None:
            return np.array([])
        
        try:
            predictions = self.model.predict(X, verbose=0)
            return predictions.flatten()
        except Exception as e:
            logger.error(f"Error making LSTM predictions: {e}")
            return np.array([])

class TransformerPredictor:
    """Transformer model for time series prediction"""
    
    def __init__(self, sequence_length: int = 60, features: int = 50):
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.is_trained = False
        
    def build_model(self) -> Optional[Model]:
        """Build Transformer architecture"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        try:
            inputs = Input(shape=(self.sequence_length, self.features))
            
            # Multi-head attention
            attention = MultiHeadAttention(
                num_heads=8, 
                key_dim=64
            )(inputs, inputs)
            
            # Add & Norm
            attention = tf.keras.layers.Add()([inputs, attention])
            attention = LayerNormalization()(attention)
            
            # Feed Forward Network
            ff = Dense(256, activation='relu')(attention)
            ff = Dropout(0.1)(ff)
            ff = Dense(self.features)(ff)
            
            # Add & Norm
            ff = tf.keras.layers.Add()([attention, ff])
            ff = LayerNormalization()(ff)
            
            # Global pooling and output
            pooled = GlobalAveragePooling1D()(ff)
            outputs = Dense(1, activation='linear')(pooled)
            
            model = Model(inputs=inputs, outputs=outputs)
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error building Transformer: {e}")
            return None
    
    def train(self, X: np.ndarray, y: np.ndarray, validation_split: float = 0.2) -> bool:
        """Train the Transformer model"""
        if not TENSORFLOW_AVAILABLE or X.size == 0:
            return False
        
        try:
            self.model = self.build_model()
            if self.model is None:
                return False
            
            # Callbacks
            early_stopping = EarlyStopping(
                monitor='val_loss', 
                patience=20, 
                restore_best_weights=True
            )
            
            # Train model
            history = self.model.fit(
                X, y,
                epochs=100,
                batch_size=32,
                validation_split=validation_split,
                callbacks=[early_stopping],
                verbose=0
            )
            
            self.is_trained = True
            logger.info("✅ Transformer model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training Transformer: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained or self.model is None:
            return np.array([])
        
        try:
            predictions = self.model.predict(X, verbose=0)
            return predictions.flatten()
        except Exception as e:
            logger.error(f"Error making Transformer predictions: {e}")
            return np.array([])

class ARIMAGARCHPredictor:
    """ARIMA-GARCH model for statistical time series prediction"""
    
    def __init__(self):
        self.arima_model = None
        self.garch_model = None
        self.is_trained = False
        
    def fit_arima(self, series: pd.Series, max_p: int = 5, max_d: int = 2, max_q: int = 5) -> bool:
        """Fit ARIMA model with automatic order selection"""
        if not STATSMODELS_AVAILABLE:
            logger.warning("Statsmodels not available")
            return False
        
        try:
            # Check stationarity
            adf_result = adfuller(series.dropna())
            is_stationary = adf_result[1] < 0.05
            
            if not is_stationary:
                # Difference the series
                series = series.diff().dropna()
            
            # Grid search for best ARIMA parameters
            best_aic = float('inf')
            best_order = None
            
            for p in range(max_p + 1):
                for d in range(max_d + 1):
                    for q in range(max_q + 1):
                        try:
                            model = ARIMA(series, order=(p, d, q))
                            fitted_model = model.fit()
                            
                            if fitted_model.aic < best_aic:
                                best_aic = fitted_model.aic
                                best_order = (p, d, q)
                                self.arima_model = fitted_model
                        except:
                            continue
            
            if self.arima_model:
                logger.info(f"✅ ARIMA{best_order} fitted with AIC: {best_aic:.2f}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error fitting ARIMA: {e}")
            return False
    
    def fit_garch(self, returns: pd.Series) -> bool:
        """Fit GARCH model for volatility prediction"""
        if not STATSMODELS_AVAILABLE:
            return False
        
        try:
            # Fit GARCH(1,1) model
            self.garch_model = arch_model(
                returns.dropna() * 100,  # Scale for numerical stability
                vol='Garch',
                p=1,
                q=1
            )
            
            garch_fitted = self.garch_model.fit(disp='off')
            self.garch_model = garch_fitted
            
            logger.info("✅ GARCH(1,1) model fitted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error fitting GARCH: {e}")
            return False
    
    def train(self, series: pd.Series) -> bool:
        """Train both ARIMA and GARCH models"""
        try:
            # Fit ARIMA for price prediction
            arima_success = self.fit_arima(series)
            
            # Fit GARCH for volatility prediction
            returns = series.pct_change().dropna()
            garch_success = self.fit_garch(returns)
            
            self.is_trained = arima_success or garch_success
            return self.is_trained
            
        except Exception as e:
            logger.error(f"Error training ARIMA-GARCH: {e}")
            return False
    
    def predict(self, steps: int = 1) -> Dict:
        """Make predictions using ARIMA-GARCH"""
        predictions = {}
        
        try:
            if self.arima_model:
                arima_forecast = self.arima_model.forecast(steps=steps)
                predictions['price_forecast'] = arima_forecast
            
            if self.garch_model:
                garch_forecast = self.garch_model.forecast(horizon=steps)
                predictions['volatility_forecast'] = garch_forecast.variance.iloc[-1].values
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making ARIMA-GARCH predictions: {e}")
            return {}

class AdvancedEnsemblePredictor:
    """Advanced ensemble combining all models with sentiment integration"""
    
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.feature_engineer = AdvancedFeatureEngineer()
        self.is_trained = False
        
    def initialize_models(self):
        """Initialize all models"""
        try:
            # Deep learning models
            self.models['lstm'] = LSTMPredictor()
            self.models['transformer'] = TransformerPredictor()
            
            # Statistical models
            self.models['arima_garch'] = ARIMAGARCHPredictor()
            
            # Traditional ML models
            if SKLEARN_AVAILABLE:
                self.models['xgboost'] = xgb.XGBRegressor(
                    n_estimators=1000,
                    max_depth=8,
                    learning_rate=0.01,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
                
                self.models['lightgbm'] = lgb.LGBMRegressor(
                    n_estimators=1000,
                    max_depth=8,
                    learning_rate=0.01,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42
                )
                
                self.models['random_forest'] = RandomForestRegressor(
                    n_estimators=500,
                    max_depth=15,
                    random_state=42
                )
            
            # Initialize equal weights
            num_models = len(self.models)
            for model_name in self.models:
                self.weights[model_name] = 1.0 / num_models
            
            logger.info(f"✅ Initialized {num_models} models in ensemble")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
    def train_ensemble(self, price_data: pd.DataFrame, 
                      sentiment_data: Optional[Dict] = None,
                      news_data: Optional[List] = None) -> bool:
        """Train all models in the ensemble"""
        try:
            if price_data.empty or len(price_data) < 200:
                logger.warning("Insufficient data for training")
                return False
            
            # Feature engineering with sentiment and news
            featured_data = self.feature_engineer.engineer_comprehensive_features(
                price_data, sentiment_data, news_data
            )
            
            # Prepare sequence data for deep learning
            X_seq, y_seq = self._create_sequence_data(featured_data)
            
            # Prepare traditional ML data
            feature_cols = featured_data.select_dtypes(include=[np.number]).columns.tolist()
            if 'close' in feature_cols:
                feature_cols.remove('close')
            
            X_ml = featured_data[feature_cols].iloc[60:].values
            y_ml = featured_data['close'].iloc[60:].values
            
            trained_models = 0
            
            # Train deep learning models
            if X_seq.size > 0:
                if 'lstm' in self.models:
                    if self.models['lstm'].train(X_seq, y_seq):
                        trained_models += 1
                
                if 'transformer' in self.models:
                    if self.models['transformer'].train(X_seq, y_seq):
                        trained_models += 1
            
            # Train statistical models
            if 'arima_garch' in self.models:
                if self.models['arima_garch'].train(featured_data['close']):
                    trained_models += 1
            
            # Train traditional ML models
            if SKLEARN_AVAILABLE and len(X_ml) > 0:
                try:
                    for model_name in ['xgboost', 'lightgbm', 'random_forest']:
                        if model_name in self.models:
                            self.models[model_name].fit(X_ml, y_ml)
                            trained_models += 1
                except Exception as e:
                    logger.warning(f"Error training ML models: {e}")
            
            self.is_trained = trained_models > 0
            logger.info(f"✅ Trained {trained_models} models successfully")
            return self.is_trained
            
        except Exception as e:
            logger.error(f"Error training ensemble: {e}")
            return False
    
    def predict_ensemble(self, current_data: pd.DataFrame,
                        sentiment_data: Optional[Dict] = None,
                        news_data: Optional[List] = None) -> Dict:
        """Make ensemble predictions with sentiment integration"""
        try:
            if not self.is_trained or current_data.empty:
                return self._fallback_prediction()
            
            # Feature engineering
            featured_data = self.feature_engineer.engineer_comprehensive_features(
                current_data, sentiment_data, news_data
            )
            
            predictions = {}
            confidences = {}
            
            # Deep learning predictions
            if len(featured_data) >= 60:
                X_seq, _ = self._create_sequence_data(featured_data)
                
                if X_seq.size > 0:
                    # LSTM prediction
                    if 'lstm' in self.models and self.models['lstm'].is_trained:
                        lstm_pred = self.models['lstm'].predict(X_seq[-1:])
                        if len(lstm_pred) > 0:
                            predictions['lstm'] = lstm_pred[0]
                            confidences['lstm'] = 0.85
                    
                    # Transformer prediction
                    if 'transformer' in self.models and self.models['transformer'].is_trained:
                        transformer_pred = self.models['transformer'].predict(X_seq[-1:])
                        if len(transformer_pred) > 0:
                            predictions['transformer'] = transformer_pred[0]
                            confidences['transformer'] = 0.88
            
            # Statistical model predictions
            if 'arima_garch' in self.models and self.models['arima_garch'].is_trained:
                stat_pred = self.models['arima_garch'].predict(steps=1)
                if 'price_forecast' in stat_pred:
                    predictions['arima_garch'] = stat_pred['price_forecast'][0]
                    confidences['arima_garch'] = 0.75
            
            # Traditional ML predictions
            if SKLEARN_AVAILABLE:
                feature_cols = featured_data.select_dtypes(include=[np.number]).columns.tolist()
                if 'close' in feature_cols:
                    feature_cols.remove('close')
                
                if len(feature_cols) > 0:
                    X_ml = featured_data[feature_cols].iloc[-1:].values
                    
                    for model_name in ['xgboost', 'lightgbm', 'random_forest']:
                        if model_name in self.models:
                            try:
                                pred = self.models[model_name].predict(X_ml)
                                predictions[model_name] = pred[0]
                                confidences[model_name] = 0.80
                            except Exception as e:
                                logger.warning(f"Error with {model_name} prediction: {e}")
            
            # Calculate ensemble prediction
            if predictions:
                ensemble_pred = self._calculate_weighted_prediction(predictions, confidences)
                overall_confidence = np.mean(list(confidences.values()))
                
                # Sentiment adjustment
                sentiment_adjustment = self._calculate_sentiment_adjustment(sentiment_data)
                adjusted_pred = ensemble_pred * (1 + sentiment_adjustment)
                
                return {
                    'ensemble_prediction': adjusted_pred,
                    'base_prediction': ensemble_pred,
                    'individual_predictions': predictions,
                    'confidences': confidences,
                    'overall_confidence': overall_confidence,
                    'sentiment_adjustment': sentiment_adjustment,
                    'models_used': list(predictions.keys())
                }
            
            return self._fallback_prediction()
            
        except Exception as e:
            logger.error(f"Error making ensemble prediction: {e}")
            return self._fallback_prediction()
    
    def _create_sequence_data(self, df: pd.DataFrame, sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequence data for deep learning models"""
        try:
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'close' in feature_cols:
                feature_cols.remove('close')
            
            if self.feature_engineer.scaler:
                scaled_features = self.feature_engineer.scaler.fit_transform(df[feature_cols])
            else:
                scaled_features = df[feature_cols].values
            
            scaled_target = df['close'].values
            
            X, y = [], []
            for i in range(sequence_length, len(scaled_features)):
                X.append(scaled_features[i-sequence_length:i])
                y.append(scaled_target[i])
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error creating sequence data: {e}")
            return np.array([]), np.array([])
    
    def _calculate_weighted_prediction(self, predictions: Dict, confidences: Dict) -> float:
        """Calculate weighted ensemble prediction"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 1.0) * confidences.get(model_name, 1.0)
            weighted_sum += pred * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_sentiment_adjustment(self, sentiment_data: Optional[Dict]) -> float:
        """Calculate sentiment-based adjustment factor"""
        if not sentiment_data:
            return 0.0
        
        try:
            # Overall sentiment impact
            overall_sentiment = sentiment_data.get('overall_sentiment', 0.0)
            
            # Fear & Greed adjustment
            fear_greed = sentiment_data.get('fear_greed_index', 50)
            fear_greed_adjustment = (fear_greed - 50) / 500  # Normalize to [-0.1, 0.1]
            
            # Social sentiment adjustment
            social_sentiment = sentiment_data.get('twitter_sentiment', 0.0)
            social_adjustment = social_sentiment * 0.05  # Max 5% adjustment
            
            # News sentiment adjustment
            news_sentiment = sentiment_data.get('news_sentiment', 0.0)
            news_adjustment = news_sentiment * 0.03  # Max 3% adjustment
            
            total_adjustment = (
                overall_sentiment * 0.02 +
                fear_greed_adjustment +
                social_adjustment +
                news_adjustment
            )
            
            # Cap adjustment at ±10%
            return max(-0.1, min(0.1, total_adjustment))
            
        except Exception as e:
            logger.warning(f"Error calculating sentiment adjustment: {e}")
            return 0.0
    
    def _fallback_prediction(self) -> Dict:
        """Fallback prediction when models fail"""
        return {
            'ensemble_prediction': 0.0,
            'base_prediction': 0.0,
            'individual_predictions': {},
            'confidences': {},
            'overall_confidence': 0.0,
            'sentiment_adjustment': 0.0,
            'models_used': []
        }

# Example usage and testing
if __name__ == "__main__":
    logger.info("🧠 Advanced ML Models System Initialized")
    
    # Initialize ensemble
    ensemble = AdvancedEnsemblePredictor()
    ensemble.initialize_models()
    
    # Example sentiment data
    sample_sentiment = {
        'overall_sentiment': 0.2,
        'fear_greed_index': 65,
        'twitter_sentiment': 0.15,
        'reddit_sentiment': 0.1,
        'news_sentiment': 0.05,
        'social_volume': 1000
    }
    
    # Example news data
    sample_news = [
        {'title': 'Bitcoin reaches new highs amid institutional adoption'},
        {'title': 'Cryptocurrency market shows strong momentum'}
    ]
    
    logger.info("✅ Advanced ML Models System Ready") 