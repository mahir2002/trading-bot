#!/usr/bin/env python3
"""
AI Models Module - Consolidated Advanced AI Trading Models
Integrates LSTM, GRU, Transformer, Ensemble, and Multi-Class Classification
"""

import numpy as np
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import joblib
import json

# Deep Learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, MultiHeadAttention, LayerNormalization
    from tensorflow.keras.optimizers import Adam
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

# Local imports
from core.base_module import BaseModule, ModuleStatus, ModuleInfo, ModulePriority, ModuleEvent, ModuleInfo, ModulePriority, ModuleEvent
import sys
import os

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class ModelType(Enum):
    """Advanced model types."""
    LSTM = "LSTM"
    GRU = "GRU"
    TRANSFORMER = "TRANSFORMER"
    RANDOM_FOREST = "RANDOM_FOREST"
    GRADIENT_BOOSTING = "GRADIENT_BOOSTING"
    ENSEMBLE = "ENSEMBLE"

class SignalType(Enum):
    """Multi-class trading signals."""
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    WEAK_SELL = "WEAK_SELL"
    HOLD = "HOLD"
    WEAK_BUY = "WEAK_BUY"
    BUY = "BUY"
    STRONG_BUY = "STRONG_BUY"

@dataclass
class ModelPrediction:
    """Model prediction result."""
    symbol: str
    prediction_class: SignalType
    confidence: float
    expected_return: float
    volatility_forecast: float
    model_type: ModelType
    features_used: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ModelConfig:
    """Model configuration."""
    sequence_length: int = 60
    prediction_horizon: int = 1
    
    # LSTM/GRU Configuration
    lstm_units: List[int] = field(default_factory=lambda: [128, 64, 32])
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    
    # Ensemble Configuration
    ensemble_weights: Dict[str, float] = field(default_factory=lambda: {
        'lstm': 0.4, 'random_forest': 0.3, 'gradient_boosting': 0.3
    })

class AdvancedFeatureEngineer:
    """Advanced feature engineering for financial time series."""
    
    def __init__(self):
        self.feature_names = []
        self.scaler = StandardScaler()
        
    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive feature set."""
        
        features_df = data.copy()
        
        # Technical indicators
        features_df = self._add_technical_features(features_df)
        
        # Lagged features
        features_df = self._add_lagged_features(features_df)
        
        # Volatility features
        features_df = self._add_volatility_features(features_df)
        
        # Statistical features
        features_df = self._add_statistical_features(features_df)
        
        # Clean features
        features_df = features_df.dropna()
        
        return features_df
    
    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators."""
        
        # Simple Moving Averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            if not df[f'sma_{period}'].isna().all():
                df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
        
        # Exponential Moving Averages
        for period in [12, 26]:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        band_width = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = np.where(band_width != 0, (df['close'] - df['bb_lower']) / band_width, 0.5)
        
        return df
    
    def _add_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged price features."""
        
        for lag in [1, 2, 3, 5, 10]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            df[f'return_lag_{lag}'] = df['close'].pct_change(lag)
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility features."""
        
        # Rolling volatility
        for window in [5, 10, 20, 30]:
            returns = df['close'].pct_change()
            df[f'volatility_{window}'] = returns.rolling(window).std()
            df[f'volatility_{window}_ann'] = df[f'volatility_{window}'] * np.sqrt(252)
        
        # Parkinson volatility estimator
        log_ratio = np.log(df['high'] / df['low'])
        df['parkinson_vol'] = np.sqrt(
            (1 / (4 * np.log(2))) * 
            (log_ratio ** 2).rolling(20).mean()
        ) * np.sqrt(252)
        
        return df
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add statistical features."""
        
        # Price momentum
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Price ranges
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        
        return df

class LSTMModel:
    """Advanced LSTM model for time series prediction."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.scaler = StandardScaler()
        
    def build_model(self, input_shape: Tuple[int, int]):
        """Build LSTM model architecture."""
        
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow not available. Install with: pip install tensorflow")
        
        model = Sequential([
            LSTM(self.config.lstm_units[0], return_sequences=True, input_shape=input_shape),
            Dropout(self.config.dropout_rate),
            LSTM(self.config.lstm_units[1], return_sequences=True),
            Dropout(self.config.dropout_rate),
            LSTM(self.config.lstm_units[2], return_sequences=False),
            Dropout(self.config.dropout_rate),
            Dense(50, activation='relu'),
            Dense(7, activation='softmax')  # 7 classes for multi-class classification
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=self.config.learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training."""
        
        X, y = [], []
        for i in range(self.config.sequence_length, len(data)):
            X.append(data[i-self.config.sequence_length:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Train LSTM model."""
        
        if not HAS_TENSORFLOW:
            return {'model_type': 'LSTM', 'error': 'TensorFlow not available'}
        
        # Build model
        self.model = self.build_model((X_train.shape[1], X_train.shape[2]))
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            batch_size=self.config.batch_size,
            epochs=self.config.epochs,
            verbose=0,
            validation_split=0.2
        )
        
        return {
            'model_type': 'LSTM',
            'final_loss': history.history['loss'][-1],
            'final_accuracy': history.history['accuracy'][-1],
            'epochs_trained': len(history.history['loss'])
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        return self.model.predict(X, verbose=0)

class EnsembleModel:
    """Advanced ensemble model combining multiple approaches."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.models = {}
        self.feature_engineer = AdvancedFeatureEngineer()
        
    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """Add model to ensemble."""
        self.models[name] = {'model': model, 'weight': weight}
    
    def train_ensemble(self, data: pd.DataFrame, target: pd.Series) -> Dict[str, Any]:
        """Train ensemble of models."""
        
        # Engineer features
        features_df = self.feature_engineer.engineer_features(data)
        
        # Prepare data for different model types
        results = {}
        
        # Random Forest
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        feature_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
        
        if 'close' in feature_columns:
            feature_columns.remove('close')
        
        X = features_df[feature_columns].values
        y = target.values
        
        # Remove NaN values
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X_clean = X[mask]
        y_clean = y[mask]
        
        if len(X_clean) > 0:
            rf_model.fit(X_clean, y_clean)
            self.add_model('random_forest', rf_model, self.config.ensemble_weights.get('random_forest', 0.3))
            results['random_forest'] = {'trained': True, 'samples': len(X_clean)}
        
        # Gradient Boosting
        gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        if len(X_clean) > 0:
            gb_model.fit(X_clean, y_clean)
            self.add_model('gradient_boosting', gb_model, self.config.ensemble_weights.get('gradient_boosting', 0.3))
            results['gradient_boosting'] = {'trained': True, 'samples': len(X_clean)}
        
        # LSTM (if TensorFlow available and enough data)
        if HAS_TENSORFLOW and len(X_clean) >= self.config.sequence_length * 2:
            lstm_model = LSTMModel(self.config)
            
            # Prepare sequences for LSTM
            X_lstm, y_lstm = lstm_model.prepare_sequences(X_clean)
            
            if len(X_lstm) > 0:
                lstm_results = lstm_model.train(X_lstm, y_lstm)
                self.add_model('lstm', lstm_model, self.config.ensemble_weights.get('lstm', 0.4))
                results['lstm'] = lstm_results
        
        return results
    
    def predict_ensemble(self, data: pd.DataFrame) -> ModelPrediction:
        """Generate ensemble prediction."""
        
        # Engineer features
        features_df = self.feature_engineer.engineer_features(data)
        
        if len(features_df) == 0:
            return ModelPrediction(
                symbol=data.get('symbol', ['UNKNOWN'])[0] if 'symbol' in data else 'UNKNOWN',
                prediction_class=SignalType.HOLD,
                confidence=0.0,
                expected_return=0.0,
                volatility_forecast=0.02,
                model_type=ModelType.ENSEMBLE,
                features_used=[]
            )
        
        # Prepare features
        feature_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
        if 'close' in feature_columns:
            feature_columns.remove('close')
        
        X = features_df[feature_columns].iloc[-1:].values
        
        # Get predictions from all models
        predictions = []
        weights = []
        
        for name, model_data in self.models.items():
            model = model_data['model']
            weight = model_data['weight']
            
            try:
                if name == 'lstm' and hasattr(model, 'predict'):
                    # For LSTM, we need sequence data
                    if len(X) >= self.config.sequence_length:
                        X_seq = X[-self.config.sequence_length:].reshape(1, self.config.sequence_length, -1)
                        pred = model.predict(X_seq)[0]
                        predictions.append(np.argmax(pred))
                        weights.append(weight)
                elif hasattr(model, 'predict'):
                    pred = model.predict(X)[0]
                    # Convert regression to classification
                    if pred > 0.02:
                        pred_class = 6  # STRONG_BUY
                    elif pred > 0.01:
                        pred_class = 5  # BUY
                    elif pred > 0.005:
                        pred_class = 4  # WEAK_BUY
                    elif pred < -0.02:
                        pred_class = 0  # STRONG_SELL
                    elif pred < -0.01:
                        pred_class = 1  # SELL
                    elif pred < -0.005:
                        pred_class = 2  # WEAK_SELL
                    else:
                        pred_class = 3  # HOLD
                    
                    predictions.append(pred_class)
                    weights.append(weight)
            except Exception as e:
                logging.warning(f"Model {name} prediction failed: {e}")
                continue
        
        # Ensemble prediction
        if predictions:
            # Weighted average of predictions
            weighted_pred = np.average(predictions, weights=weights)
            confidence = 1.0 - (np.std(predictions) / 3.0)  # Confidence based on agreement
            confidence = max(0.0, min(1.0, confidence))
            
            # Map to signal type
            signal_types = list(SignalType)
            pred_class = signal_types[int(round(weighted_pred))]
            
            # Estimate expected return
            expected_return = (weighted_pred - 3) * 0.01  # Scale to return
            
        else:
            pred_class = SignalType.HOLD
            confidence = 0.0
            expected_return = 0.0
        
        # Volatility forecast
        volatility_forecast = 0.02
        if len(features_df) > 20:
            returns = features_df['close'].pct_change().dropna()
            if len(returns) > 0:
                volatility_forecast = returns.std() * np.sqrt(252)
        
        return ModelPrediction(
            symbol=data.get('symbol', ['UNKNOWN'])[0] if 'symbol' in data else 'UNKNOWN',
            prediction_class=pred_class,
            confidence=confidence,
            expected_return=expected_return,
            volatility_forecast=volatility_forecast,
            model_type=ModelType.ENSEMBLE,
            features_used=feature_columns
        )

class AIModelsModule(BaseModule):
    """AI Models Module for the unified trading platform."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config or {})
        
        # Initialize components
        self.model_config = ModelConfig()
        self.ensemble_models = {}
        self.trained_symbols = set()
        
        # Performance tracking
        self.prediction_history = []
        self.accuracy_metrics = {}
        
    async def initialize(self) -> bool:
        """Initialize the AI models module."""
        try:
            self.logger.info("Initializing AI Models Module...")
            
            # Check TensorFlow availability
            if not HAS_TENSORFLOW:
                self.logger.warning("TensorFlow not available. LSTM models will be disabled.")
            
            # Load pre-trained models if available
            await self._load_pretrained_models()
            
            # Set up model retraining schedule
            await self._setup_retraining_schedule()
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("AI Models Module initialized successfully")
            
            # Send initialization event
            await self.send_event(
                event_type="ai_models_initialized",
                data={"module": self.name, "status": "initialized"},
                priority=ModulePriority.NORMAL
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Models Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """Start the AI models module."""
        try:
            self.logger.info("Starting AI Models Module...")
            
            # Start prediction service
            asyncio.create_task(self._prediction_service())
            
            # Start model monitoring
            asyncio.create_task(self._model_monitoring())
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("AI Models Module started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start AI Models Module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the AI models module."""
        try:
            self.logger.info("Stopping AI Models Module...")
            
            # Save models
            await self._save_models()
            
            self.status = ModuleStatus.STOPPED
            self.logger.info("AI Models Module stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop AI Models Module: {e}")
            return False
    
    async def handle_event(self, event: ModuleEvent) -> bool:
        """Process incoming events."""
        try:
            if event.event_type == "market_data_update":
                await self._handle_market_data_update(event)
            elif event.event_type == "prediction_request":
                await self._handle_prediction_request(event)
            elif event.event_type == "model_retrain_request":
                await self._handle_retrain_request(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            return False
    
    async def _handle_market_data_update(self, event: ModuleEvent):
        """Handle market data updates."""
        data = event.data
        symbol = data.get('symbol')
        
        if symbol and symbol in self.ensemble_models:
            # Update model with new data
            await self._update_model_data(symbol, data)
    
    async def _handle_prediction_request(self, event: ModuleEvent):
        """Handle prediction requests."""
        data = event.data
        symbol = data.get('symbol')
        market_data = data.get('market_data')
        
        if symbol and market_data is not None:
            prediction = await self._generate_prediction(symbol, market_data)
            
            # Send prediction event
            await self.send_event(
                event_type="ai_prediction_generated",
                data={
                    "symbol": symbol,
                    "prediction": prediction.__dict__,
                    "timestamp": datetime.now().isoformat()
                },
                priority=ModulePriority.HIGH
            )
    
    async def _generate_prediction(self, symbol: str, market_data: pd.DataFrame) -> ModelPrediction:
        """Generate AI prediction for symbol."""
        
        # Check if model exists for symbol
        if symbol not in self.ensemble_models:
            await self._train_model_for_symbol(symbol, market_data)
        
        # Generate prediction
        model = self.ensemble_models[symbol]
        prediction = model.predict_ensemble(market_data)
        
        # Store prediction for performance tracking
        self.prediction_history.append({
            'symbol': symbol,
            'prediction': prediction,
            'timestamp': datetime.now()
        })
        
        return prediction
    
    async def _train_model_for_symbol(self, symbol: str, market_data: pd.DataFrame):
        """Train ensemble model for a specific symbol."""
        try:
            self.logger.info(f"Training AI model for {symbol}...")
            
            # Create target variable (next period return)
            target = market_data['close'].shift(-1) / market_data['close'] - 1
            target = target.dropna()
            
            # Create ensemble model
            ensemble = EnsembleModel(self.model_config)
            
            # Train ensemble
            results = ensemble.train_ensemble(market_data, target)
            
            # Store model
            self.ensemble_models[symbol] = ensemble
            self.trained_symbols.add(symbol)
            
            self.logger.info(f"Model trained for {symbol}: {results}")
            
        except Exception as e:
            self.logger.error(f"Failed to train model for {symbol}: {e}")
    
    async def _prediction_service(self):
        """Background prediction service."""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Process prediction requests
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in prediction service: {e}")
                await asyncio.sleep(5)
    
    async def _model_monitoring(self):
        """Monitor model performance."""
        while self.status == ModuleStatus.RUNNING:
            try:
                # Check model performance
                await self._check_model_performance()
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in model monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_model_performance(self):
        """Check and log model performance."""
        if len(self.prediction_history) < 10:
            return
        
        # Calculate accuracy metrics
        recent_predictions = self.prediction_history[-100:]  # Last 100 predictions
        
        # Log performance metrics
        self.logger.info(f"Model Performance - Recent predictions: {len(recent_predictions)}")
        
        # Send performance event
        await self.send_event(
            event_type="ai_performance_update",
            data={
                "total_predictions": len(self.prediction_history),
                "recent_predictions": len(recent_predictions),
                "trained_symbols": len(self.trained_symbols)
            },
            priority=ModulePriority.LOW
        )
    
    async def _load_pretrained_models(self):
        """Load pre-trained models."""
        # Implementation for loading saved models
        pass
    
    async def _save_models(self):
        """Save trained models."""
        # Implementation for saving models
        pass
    
    async def _setup_retraining_schedule(self):
        """Set up automatic model retraining."""
        # Implementation for scheduled retraining
        pass
    
    async def _update_model_data(self, symbol: str, data: Dict[str, Any]):
        """Update model with new market data."""
        # Implementation for incremental learning
        pass
    
    async def _handle_retrain_request(self, event: ModuleEvent):
        """Handle model retraining requests."""
        data = event.data
        symbol = data.get('symbol')
        
        if symbol and symbol in self.ensemble_models:
            # Retrain model
            await self._train_model_for_symbol(symbol, data.get('market_data'))
    
    def get_module_info(self) -> ModuleInfo:
        """Return module information and metadata."""
        return ModuleInfo(
            name="ai_models",
            version="1.0.0",
            description="Advanced AI Models for Trading Predictions",
            author="Unified Trading Platform",
            dependencies=["market_data"],
            priority=ModulePriority.HIGH,
            config_schema=self.get_config_schema()
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check module health."""
        return {
            "status": self.status.value,
            "trained_models": len(self.ensemble_models),
            "tensorflow_available": HAS_TENSORFLOW,
            "last_error": self.last_error,
            "memory_usage": "N/A"  # Could implement actual memory tracking
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for this module."""
        return {
            "type": "object",
            "properties": {
                "model_type": {"type": "string", "enum": ["ensemble", "lstm", "random_forest"]},
                "retrain_interval": {"type": "integer", "minimum": 300},
                "features": {"type": "array", "items": {"type": "string"}},
                "sequence_length": {"type": "integer", "minimum": 10, "maximum": 1000},
                "prediction_horizon": {"type": "integer", "minimum": 1, "maximum": 100}
            },
            "required": ["model_type", "retrain_interval", "features"]
        } 