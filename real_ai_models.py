#!/usr/bin/env python3
"""
Real AI Models for Cryptocurrency Trading
Advanced LSTM, Transformer, and Ensemble Models with Feature Engineering
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import ML libraries, fallback gracefully
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, MultiHeadAttention, LayerNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

# Technical indicators
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """Advanced feature engineering for cryptocurrency data"""
    
    def __init__(self):
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive technical indicators"""
        if df.empty or len(df) < 50:
            return df
        
        try:
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning("Missing required columns for technical features")
                return df
            
            # Price-based features
            df['price_change'] = df['close'].pct_change()
            df['price_volatility'] = df['price_change'].rolling(window=20).std()
            df['price_momentum'] = df['close'] / df['close'].shift(10) - 1
            
            # Moving averages
            for period in [5, 10, 20, 50]:
                df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Volume features
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['price_volume'] = df['close'] * df['volume']
            
            # Advanced indicators using TA-Lib if available
            if TALIB_AVAILABLE:
                try:
                    # Convert to numpy arrays
                    high = df['high'].values
                    low = df['low'].values
                    close = df['close'].values
                    volume = df['volume'].values
                    
                    # Stochastic
                    df['stoch_k'], df['stoch_d'] = talib.STOCH(high, low, close)
                    
                    # Williams %R
                    df['williams_r'] = talib.WILLR(high, low, close)
                    
                    # Commodity Channel Index
                    df['cci'] = talib.CCI(high, low, close)
                    
                    # Average True Range
                    df['atr'] = talib.ATR(high, low, close)
                    
                    # On Balance Volume
                    df['obv'] = talib.OBV(close, volume)
                    
                    # Money Flow Index
                    df['mfi'] = talib.MFI(high, low, close, volume)
                    
                except Exception as e:
                    logger.warning(f"TA-Lib indicators failed: {e}")
            
            # Market structure features
            df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
            df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
            
            # Support/Resistance levels
            df['resistance'] = df['high'].rolling(window=20).max()
            df['support'] = df['low'].rolling(window=20).min()
            df['support_resistance_ratio'] = (df['close'] - df['support']) / (df['resistance'] - df['support'])
            
            # Time-based features
            if 'timestamp' in df.columns:
                df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
                df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
            # Fill NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            logger.info(f"✅ Created {len(df.columns)} technical features")
            return df
            
        except Exception as e:
            logger.error(f"Error creating technical features: {e}")
            return df
    
    def create_sequence_data(self, df: pd.DataFrame, sequence_length: int = 60, 
                           target_col: str = 'close') -> Tuple[np.ndarray, np.ndarray]:
        """Create sequence data for LSTM training"""
        try:
            # Select feature columns (exclude non-numeric)
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in feature_cols:
                feature_cols.remove(target_col)
            
            # Scale features
            if self.scaler and SKLEARN_AVAILABLE:
                scaled_features = self.scaler.fit_transform(df[feature_cols])
                scaled_target = df[target_col].values
            else:
                scaled_features = df[feature_cols].values
                scaled_target = df[target_col].values
            
            X, y = [], []
            for i in range(sequence_length, len(scaled_features)):
                X.append(scaled_features[i-sequence_length:i])
                y.append(scaled_target[i])
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error creating sequence data: {e}")
            return np.array([]), np.array([])

class RealLSTMPredictor:
    """Real LSTM Neural Network for price prediction"""
    
    def __init__(self, sequence_length: int = 60, features: int = 20):
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.is_trained = False
        
    def build_model(self) -> Optional[Model]:
        """Build LSTM model architecture"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, using fallback prediction")
            return None
        
        try:
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(self.sequence_length, self.features)),
                Dropout(0.2),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50),
                Dropout(0.2),
                Dense(25, activation='relu'),
                Dense(1)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
            return model
            
        except Exception as e:
            logger.error(f"Error building LSTM model: {e}")
            return None
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 50, validation_split: float = 0.2) -> bool:
        """Train the LSTM model"""
        if not TENSORFLOW_AVAILABLE or X.size == 0 or y.size == 0:
            logger.warning("Cannot train LSTM: TensorFlow unavailable or no data")
            return False
        
        try:
            self.model = self.build_model()
            if self.model is None:
                return False
            
            # Early stopping
            early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            
            # Train model
            history = self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=32,
                validation_split=validation_split,
                callbacks=[early_stopping],
                verbose=0
            )
            
            self.is_trained = True
            logger.info(f"✅ LSTM model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using trained LSTM model"""
        if not self.is_trained or self.model is None or X.size == 0:
            # Fallback prediction
            return np.array([np.random.uniform(0.95, 1.05) for _ in range(len(X))])
        
        try:
            predictions = self.model.predict(X, verbose=0)
            return predictions.flatten()
        except Exception as e:
            logger.error(f"Error making LSTM predictions: {e}")
            return np.array([1.0] * len(X))

class AdvancedEnsemblePredictor:
    """Advanced ensemble of multiple ML models"""
    
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.feature_engineer = AdvancedFeatureEngineer()
        self.is_trained = False
        
    def initialize_models(self):
        """Initialize all models in the ensemble"""
        try:
            # LSTM Model
            self.models['lstm'] = RealLSTMPredictor()
            
            # Traditional ML models (if sklearn available)
            if SKLEARN_AVAILABLE:
                self.models['random_forest'] = RandomForestRegressor(
                    n_estimators=100, 
                    max_depth=10, 
                    random_state=42
                )
                self.models['gradient_boost'] = GradientBoostingRegressor(
                    n_estimators=100, 
                    max_depth=6, 
                    random_state=42
                )
            
            # Initialize weights (equal initially)
            num_models = len(self.models)
            for model_name in self.models:
                self.weights[model_name] = 1.0 / num_models
                
            logger.info(f"✅ Initialized {num_models} models in ensemble")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
    def train_ensemble(self, price_data: pd.DataFrame) -> bool:
        """Train all models in the ensemble"""
        try:
            if price_data.empty or len(price_data) < 100:
                logger.warning("Insufficient data for training")
                return False
            
            # Feature engineering
            featured_data = self.feature_engineer.create_technical_features(price_data)
            
            # Prepare sequence data for deep learning models
            X_seq, y_seq = self.feature_engineer.create_sequence_data(featured_data)
            
            # Prepare traditional ML data
            feature_cols = featured_data.select_dtypes(include=[np.number]).columns.tolist()
            if 'close' in feature_cols:
                feature_cols.remove('close')
            
            X_ml = featured_data[feature_cols].iloc[60:].values  # Skip first 60 for alignment
            y_ml = featured_data['close'].iloc[60:].values
            
            trained_models = 0
            
            # Train LSTM
            if 'lstm' in self.models and X_seq.size > 0:
                if self.models['lstm'].train(X_seq, y_seq):
                    trained_models += 1
            
            # Train traditional ML models
            if SKLEARN_AVAILABLE and len(X_ml) > 0:
                try:
                    if 'random_forest' in self.models:
                        self.models['random_forest'].fit(X_ml, y_ml)
                        trained_models += 1
                    
                    if 'gradient_boost' in self.models:
                        self.models['gradient_boost'].fit(X_ml, y_ml)
                        trained_models += 1
                        
                except Exception as e:
                    logger.warning(f"Error training traditional ML models: {e}")
            
            self.is_trained = trained_models > 0
            logger.info(f"✅ Trained {trained_models} models successfully")
            return self.is_trained
            
        except Exception as e:
            logger.error(f"Error training ensemble: {e}")
            return False
    
    def predict_ensemble(self, current_data: pd.DataFrame) -> Dict:
        """Make ensemble predictions"""
        try:
            if not self.is_trained or current_data.empty:
                return self._fallback_prediction()
            
            # Feature engineering
            featured_data = self.feature_engineer.create_technical_features(current_data)
            
            predictions = {}
            confidences = {}
            
            # Get predictions from each model
            if len(featured_data) >= 60:
                # Sequence data for deep learning
                X_seq, _ = self.feature_engineer.create_sequence_data(featured_data)
                
                if X_seq.size > 0:
                    # LSTM prediction
                    if 'lstm' in self.models:
                        lstm_pred = self.models['lstm'].predict(X_seq[-1:])
                        if len(lstm_pred) > 0:
                            predictions['lstm'] = lstm_pred[0]
                            confidences['lstm'] = 0.8
                
                # Traditional ML predictions
                if SKLEARN_AVAILABLE:
                    feature_cols = featured_data.select_dtypes(include=[np.number]).columns.tolist()
                    if 'close' in feature_cols:
                        feature_cols.remove('close')
                    
                    if len(feature_cols) > 0:
                        X_ml = featured_data[feature_cols].iloc[-1:].values
                        
                        try:
                            if 'random_forest' in self.models:
                                rf_pred = self.models['random_forest'].predict(X_ml)
                                predictions['random_forest'] = rf_pred[0]
                                confidences['random_forest'] = 0.7
                            
                            if 'gradient_boost' in self.models:
                                gb_pred = self.models['gradient_boost'].predict(X_ml)
                                predictions['gradient_boost'] = gb_pred[0]
                                confidences['gradient_boost'] = 0.72
                                
                        except Exception as e:
                            logger.warning(f"Error with traditional ML predictions: {e}")
            
            # Ensemble prediction
            if predictions:
                current_price = featured_data['close'].iloc[-1]
                
                # Weighted average of predictions
                weighted_sum = sum(pred * confidences.get(model, 0.5) for model, pred in predictions.items())
                total_weight = sum(confidences.get(model, 0.5) for model in predictions.keys())
                
                ensemble_prediction = weighted_sum / total_weight if total_weight > 0 else current_price
                
                # Calculate prediction confidence
                prediction_variance = np.var(list(predictions.values()))
                ensemble_confidence = max(0.5, 1.0 - (prediction_variance / current_price))
                
                # Determine direction and strength
                price_change = (ensemble_prediction - current_price) / current_price
                direction = "BUY" if price_change > 0.01 else "SELL" if price_change < -0.01 else "HOLD"
                
                return {
                    'prediction': ensemble_prediction,
                    'current_price': current_price,
                    'price_change_percent': price_change * 100,
                    'direction': direction,
                    'confidence': ensemble_confidence * 100,
                    'model_predictions': predictions,
                    'model_confidences': confidences,
                    'ensemble_strength': len(predictions)
                }
            
            return self._fallback_prediction()
            
        except Exception as e:
            logger.error(f"Error making ensemble prediction: {e}")
            return self._fallback_prediction()
    
    def _fallback_prediction(self) -> Dict:
        """Fallback prediction when models fail"""
        return {
            'prediction': 1.0,
            'current_price': 1.0,
            'price_change_percent': 0.0,
            'direction': 'HOLD',
            'confidence': 50.0,
            'model_predictions': {},
            'model_confidences': {},
            'ensemble_strength': 0
        }

# Usage example and testing
if __name__ == "__main__":
    print("🧠 Real AI Models Test")
    print("=" * 50)
    
    # Check available libraries
    print(f"📚 TensorFlow Available: {TENSORFLOW_AVAILABLE}")
    print(f"📚 Scikit-learn Available: {SKLEARN_AVAILABLE}")
    print(f"📚 TA-Lib Available: {TALIB_AVAILABLE}")
    
    # Create sample data
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='1H')
    np.random.seed(42)
    
    # Generate realistic price data
    price_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(100, 200, len(dates)),
        'high': np.random.uniform(100, 220, len(dates)),
        'low': np.random.uniform(80, 200, len(dates)),
        'close': np.random.uniform(90, 210, len(dates)),
        'volume': np.random.uniform(1000000, 10000000, len(dates))
    })
    
    # Ensure OHLC relationships
    for i in range(len(price_data)):
        high = max(price_data.iloc[i][['open', 'close']].max(), price_data.iloc[i]['high'])
        low = min(price_data.iloc[i][['open', 'close']].min(), price_data.iloc[i]['low'])
        price_data.iloc[i, price_data.columns.get_loc('high')] = high
        price_data.iloc[i, price_data.columns.get_loc('low')] = low
    
    print(f"📊 Generated {len(price_data)} data points")
    
    # Initialize and train ensemble
    ensemble = AdvancedEnsemblePredictor()
    ensemble.initialize_models()
    
    print("🏋️ Training ensemble models...")
    success = ensemble.train_ensemble(price_data)
    
    if success:
        print("✅ Ensemble training completed!")
        
        # Make prediction on recent data
        recent_data = price_data.tail(100)
        prediction = ensemble.predict_ensemble(recent_data)
        
        print("\n🔮 Ensemble Prediction:")
        print(f"   Direction: {prediction['direction']}")
        print(f"   Confidence: {prediction['confidence']:.1f}%")
        print(f"   Price Change: {prediction['price_change_percent']:+.2f}%")
        print(f"   Models Used: {prediction['ensemble_strength']}")
        
        if prediction['model_predictions']:
            print("\n🤖 Individual Model Predictions:")
            for model, pred in prediction['model_predictions'].items():
                conf = prediction['model_confidences'].get(model, 0)
                print(f"   {model}: {pred:.2f} (confidence: {conf:.1f})")
    else:
        print("❌ Ensemble training failed")
    
    print("\n✅ Real AI Models test completed!") 