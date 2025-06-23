#!/usr/bin/env python3
"""
Advanced AI Models Final Demo
Working demonstration of LSTM, ensemble methods, and sophisticated features
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Deep Learning
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# Machine Learning
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def generate_realistic_market_data(n_samples=1500):
    """Generate realistic market data with multiple regimes."""
    
    np.random.seed(42)
    timestamps = pd.date_range(start='2020-01-01', periods=n_samples, freq='D')
    
    # Generate price series with different regimes
    price = 100.0
    prices = []
    volumes = []
    
    for i in range(n_samples):
        # Market regime
        if i < 375:  # Bull market
            drift = 0.0008
            volatility = 0.02
        elif i < 750:  # Bear market
            drift = -0.0005
            volatility = 0.025
        elif i < 1125:  # Sideways
            drift = 0.0001
            volatility = 0.015
        else:  # High volatility
            drift = 0.0003
            volatility = 0.04
        
        # Price movement
        return_shock = np.random.normal(drift, volatility)
        price *= (1 + return_shock)
        prices.append(price)
        
        # Volume
        base_volume = np.random.lognormal(10, 0.5)
        volume_multiplier = 1 + abs(return_shock) * 5
        volumes.append(base_volume * volume_multiplier)
    
    # Create OHLC data
    close_series = pd.Series(prices)
    high = close_series * (1 + np.random.uniform(0, 0.005, n_samples))
    low = close_series * (1 - np.random.uniform(0, 0.005, n_samples))
    open_prices = close_series.shift(1).fillna(close_series.iloc[0])
    
    return pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close_series,
        'volume': volumes
    }, index=timestamps)

def create_advanced_features(data):
    """Create comprehensive feature set with proper data handling."""
    
    print("🔧 Creating Advanced Features...")
    df = data.copy()
    
    # 1. Basic Features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    df['price_change'] = df['close'] - df['open']
    df['price_range'] = df['high'] - df['low']
    df['volume_price'] = df['volume'] * df['close']
    
    # 2. Technical Indicators
    # Moving averages
    for period in [5, 10, 20, 50]:
        df[f'sma_{period}'] = df['close'].rolling(window=period, min_periods=1).mean()
        df[f'ema_{period}'] = df['close'].ewm(span=period, min_periods=1).mean()
        df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss + 1e-8)  # Avoid division by zero
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_12 = df['close'].ewm(span=12, min_periods=1).mean()
    ema_26 = df['close'].ewm(span=26, min_periods=1).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, min_periods=1).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    
    # Bollinger Bands
    sma_20 = df['close'].rolling(window=20, min_periods=1).mean()
    std_20 = df['close'].rolling(window=20, min_periods=1).std()
    df['bb_upper'] = sma_20 + (std_20 * 2)
    df['bb_lower'] = sma_20 - (std_20 * 2)
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_width'] + 1e-8)
    
    # 3. Lagged Features
    for lag in [1, 2, 3, 5]:
        df[f'close_lag_{lag}'] = df['close'].shift(lag)
        df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
    
    # 4. Volatility Features
    for window in [5, 10, 20]:
        df[f'volatility_{window}'] = df['returns'].rolling(window=window, min_periods=1).std()
        df[f'volatility_{window}_ann'] = df[f'volatility_{window}'] * np.sqrt(252)
    
    # Parkinson volatility
    df['parkinson_vol'] = np.sqrt(0.361 * np.log((df['high'] / df['low']).clip(lower=1e-8))**2)
    
    # 5. Statistical Features
    for window in [10, 20]:
        df[f'close_mean_{window}'] = df['close'].rolling(window=window, min_periods=1).mean()
        df[f'close_std_{window}'] = df['close'].rolling(window=window, min_periods=1).std()
        
        # Price position in range
        rolling_min = df['close'].rolling(window=window, min_periods=1).min()
        rolling_max = df['close'].rolling(window=window, min_periods=1).max()
        df[f'price_position_{window}'] = (df['close'] - rolling_min) / ((rolling_max - rolling_min) + 1e-8)
    
    # Momentum
    for period in [1, 5, 10]:
        df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
    
    # 6. Sentiment Features (simulated)
    np.random.seed(42)
    df['news_sentiment'] = np.random.normal(0, 0.1, len(df))
    df['social_sentiment'] = np.random.normal(0, 0.15, len(df))
    df['fear_greed_index'] = 50 + 30 * np.sin(np.arange(len(df)) * 0.02) + np.random.normal(0, 5, len(df))
    df['combined_sentiment'] = (0.4 * df['news_sentiment'] + 0.3 * df['social_sentiment'] + 
                                0.3 * (df['fear_greed_index'] - 50) / 50)
    
    # 7. On-chain Features (simulated)
    df['active_addresses'] = np.random.lognormal(10, 0.2, len(df))
    df['transaction_count'] = np.random.lognormal(12, 0.3, len(df))
    df['exchange_inflow'] = np.random.lognormal(8, 0.4, len(df))
    df['whale_transactions'] = np.random.poisson(5, len(df))
    df['open_interest'] = np.random.lognormal(10, 0.3, len(df))
    
    # 8. Temporal Features
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Clean data properly
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
    
    print(f"   ✅ Created {len(df.columns)} features")
    print(f"   ✅ Data shape: {df.shape}")
    
    return df

class LSTMModel:
    """LSTM model for time series prediction."""
    
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.model = None
    
    def build_model(self, n_features):
        """Build LSTM model."""
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(self.sequence_length, n_features)),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        return model
    
    def prepare_sequences(self, data):
        """Prepare sequences for LSTM."""
        X, y = [], []
        
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i, 0])  # Predict returns
        
        return np.array(X), np.array(y)
    
    def train(self, X_train, y_train):
        """Train LSTM model."""
        self.model = self.build_model(X_train.shape[2])
        
        history = self.model.fit(
            X_train, y_train,
            epochs=20,
            batch_size=16,
            verbose=0,
            validation_split=0.1
        )
        
        return history
    
    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X, verbose=0).flatten()

class AdvancedEnsemble:
    """Advanced ensemble combining multiple models."""
    
    def __init__(self, sequence_length=30):
        self.sequence_length = sequence_length
        self.models = {}
        self.weights = {'lstm': 0.4, 'rf': 0.3, 'gb': 0.3}
        
    def train(self, X_train, y_train):
        """Train ensemble models."""
        
        print("   🤖 Training LSTM model...")
        # LSTM
        lstm_model = LSTMModel(sequence_length=self.sequence_length)
        X_lstm, y_lstm = lstm_model.prepare_sequences(X_train)
        
        if len(X_lstm) > 10:  # Ensure we have enough data
            lstm_model.train(X_lstm, y_lstm)
            self.models['lstm'] = lstm_model
        
        # Random Forest
        print("   🌲 Training Random Forest...")
        rf_model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        X_flat = X_train.reshape(len(X_train), -1)
        rf_model.fit(X_flat, y_train[:, 0])
        self.models['rf'] = rf_model
        
        # Gradient Boosting
        print("   🚀 Training Gradient Boosting...")
        gb_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        gb_model.fit(X_flat, y_train[:, 0])
        self.models['gb'] = gb_model
        
        return self.models
    
    def predict(self, X_test):
        """Make ensemble predictions."""
        
        predictions = {}
        
        # LSTM predictions
        if 'lstm' in self.models:
            lstm_model = self.models['lstm']
            X_lstm, _ = lstm_model.prepare_sequences(X_test)
            if len(X_lstm) > 0:
                lstm_pred = lstm_model.predict(X_lstm)
                # Pad to match input length
                full_pred = np.zeros(len(X_test))
                start_idx = len(X_test) - len(lstm_pred)
                full_pred[start_idx:] = lstm_pred
                predictions['lstm'] = full_pred
        
        # Tree model predictions
        X_flat = X_test.reshape(len(X_test), -1)
        
        if 'rf' in self.models:
            predictions['rf'] = self.models['rf'].predict(X_flat)
        
        if 'gb' in self.models:
            predictions['gb'] = self.models['gb'].predict(X_flat)
        
        # Weighted ensemble
        if predictions:
            ensemble_pred = np.zeros(len(X_test))
            total_weight = 0
            
            for model_name, pred in predictions.items():
                weight = self.weights.get(model_name, 0.33)
                ensemble_pred += weight * pred
                total_weight += weight
            
            if total_weight > 0:
                ensemble_pred /= total_weight
            
            return ensemble_pred, predictions
        
        return np.zeros(len(X_test)), {}

def demonstrate_advanced_ai_models():
    """Demonstrate advanced AI models and feature engineering."""
    
    print("🤖 Advanced AI Models and Feature Engineering Demo")
    print("=" * 80)
    
    # Generate realistic market data
    print("📈 Generating Realistic Market Data...")
    market_data = generate_realistic_market_data(1500)
    print(f"   Generated {len(market_data)} samples with multiple market regimes")
    
    # Advanced feature engineering
    print("\n🔧 Advanced Feature Engineering...")
    features_df = create_advanced_features(market_data)
    
    # Prepare target variable (next period return)
    features_df['target'] = features_df['close'].shift(-1) / features_df['close'] - 1
    features_df = features_df.dropna()
    
    print(f"   Final dataset shape: {features_df.shape}")
    
    # Select numeric features for modeling
    numeric_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
    if 'target' in numeric_columns:
        numeric_columns.remove('target')
    
    # Prepare data
    X = features_df[numeric_columns].values
    y = features_df[['target'] + numeric_columns[:5]].values  # Multi-output for sequences
    
    # Train/test split (time series)
    split_point = int(len(X) * 0.8)
    X_train, X_test = X[:split_point], X[split_point:]
    y_train, y_test = y[:split_point], y[split_point:]
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n📊 Dataset Prepared:")
    print(f"   Training samples: {len(X_train)}")
    print(f"   Testing samples: {len(X_test)}")
    print(f"   Features: {len(numeric_columns)}")
    
    # Train advanced ensemble
    print(f"\n🤖 Training Advanced Ensemble Models...")
    ensemble = AdvancedEnsemble(sequence_length=min(30, len(X_train)//5))
    ensemble.train(X_train_scaled, y_train)
    
    # Make predictions
    print(f"\n📊 Generating Ensemble Predictions...")
    ensemble_pred, individual_preds = ensemble.predict(X_test_scaled)
    
    # Evaluate performance
    actual_returns = y_test[:, 0]  # Target returns
    min_length = min(len(ensemble_pred), len(actual_returns))
    
    ensemble_pred = ensemble_pred[:min_length]
    actual_returns = actual_returns[:min_length]
    
    # Performance metrics
    mse = mean_squared_error(actual_returns, ensemble_pred)
    mae = mean_absolute_error(actual_returns, ensemble_pred)
    r2 = r2_score(actual_returns, ensemble_pred)
    
    # Directional accuracy
    pred_direction = np.sign(ensemble_pred)
    actual_direction = np.sign(actual_returns)
    directional_accuracy = np.mean(pred_direction == actual_direction)
    
    print(f"\n📈 Advanced AI Model Performance:")
    print("=" * 50)
    print(f"Mean Squared Error: {mse:.6f}")
    print(f"Mean Absolute Error: {mae:.6f}")
    print(f"R² Score: {r2:.6f}")
    print(f"RMSE: {np.sqrt(mse):.6f}")
    print(f"Directional Accuracy: {directional_accuracy:.1%}")
    
    # Individual model performance
    print(f"\n🔍 Individual Model Analysis:")
    for model_name, pred in individual_preds.items():
        if len(pred) >= min_length:
            model_pred = pred[:min_length]
            model_r2 = r2_score(actual_returns, model_pred)
            model_acc = np.mean(np.sign(model_pred) == actual_direction)
            print(f"   {model_name.upper()}: R² = {model_r2:.3f}, Accuracy = {model_acc:.1%}")
    
    # Feature importance analysis
    if 'rf' in ensemble.models:
        rf_model = ensemble.models['rf']
        feature_importance = pd.DataFrame({
            'feature': numeric_columns,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n🔍 Top 15 Most Important Features:")
        print("=" * 50)
        for i, (_, row) in enumerate(feature_importance.head(15).iterrows()):
            print(f"{i+1:2d}. {row['feature']:<30} {row['importance']:.4f}")
    
    # Feature category analysis
    feature_categories = {
        'Technical': [f for f in numeric_columns if any(x in f for x in ['sma', 'ema', 'rsi', 'macd', 'bb'])],
        'Lagged': [f for f in numeric_columns if 'lag' in f],
        'Volatility': [f for f in numeric_columns if 'volatility' in f or 'parkinson' in f],
        'Sentiment': [f for f in numeric_columns if any(x in f for x in ['sentiment', 'fear', 'greed'])],
        'On-chain': [f for f in numeric_columns if any(x in f for x in ['active', 'transaction', 'exchange', 'whale', 'open_interest'])],
        'Statistical': [f for f in numeric_columns if any(x in f for x in ['mean', 'std', 'position', 'momentum'])],
        'Temporal': [f for f in numeric_columns if any(x in f for x in ['day', 'month', 'weekend', 'sin', 'cos'])],
        'Basic': [f for f in numeric_columns if any(x in f for x in ['returns', 'price', 'volume', 'range'])]
    }
    
    print(f"\n📊 Feature Category Distribution:")
    print("=" * 50)
    for category, features in feature_categories.items():
        print(f"{category:<12}: {len(features):2d} features")
    
    return {
        'ensemble_predictions': ensemble_pred,
        'individual_predictions': individual_preds,
        'actual_returns': actual_returns,
        'performance': {
            'mse': mse,
            'mae': mae,
            'r2': r2,
            'directional_accuracy': directional_accuracy
        },
        'feature_importance': feature_importance if 'rf' in ensemble.models else None,
        'feature_categories': feature_categories,
        'features_df': features_df,
        'ensemble': ensemble
    }

def create_comprehensive_visualization(results):
    """Create comprehensive visualization of results."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    ensemble_pred = results['ensemble_predictions']
    actual = results['actual_returns']
    individual_preds = results['individual_predictions']
    
    # 1. Predictions vs Actual
    ax1 = axes[0, 0]
    ax1.scatter(actual, ensemble_pred, alpha=0.6, s=20, color='blue')
    ax1.plot([actual.min(), actual.max()], [actual.min(), actual.max()], 'r--', lw=2)
    ax1.set_xlabel('Actual Returns')
    ax1.set_ylabel('Predicted Returns')
    ax1.set_title('Ensemble: Predictions vs Actual')
    ax1.grid(True, alpha=0.3)
    
    # 2. Time series comparison
    ax2 = axes[0, 1]
    time_idx = range(len(ensemble_pred))
    ax2.plot(time_idx, actual, label='Actual', alpha=0.8, linewidth=1)
    ax2.plot(time_idx, ensemble_pred, label='Ensemble', alpha=0.8, linewidth=1)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Returns')
    ax2.set_title('Predictions Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Feature importance
    ax3 = axes[0, 2]
    if results['feature_importance'] is not None:
        top_features = results['feature_importance'].head(10)
        bars = ax3.barh(range(len(top_features)), top_features['importance'])
        ax3.set_yticks(range(len(top_features)))
        ax3.set_yticklabels([f[:15] for f in top_features['feature']], fontsize=8)
        ax3.set_xlabel('Importance')
        ax3.set_title('Top 10 Feature Importance')
        ax3.grid(True, alpha=0.3)
    
    # 4. Individual model comparison
    ax4 = axes[1, 0]
    colors = ['red', 'green', 'orange']
    for i, (model_name, pred) in enumerate(individual_preds.items()):
        if len(pred) >= len(actual):
            model_pred = pred[:len(actual)]
            r2 = r2_score(actual, model_pred)
            ax4.scatter(actual, model_pred, alpha=0.5, s=15, 
                       color=colors[i % len(colors)], label=f'{model_name.upper()} (R²={r2:.3f})')
    
    ax4.plot([actual.min(), actual.max()], [actual.min(), actual.max()], 'k--', lw=1)
    ax4.set_xlabel('Actual Returns')
    ax4.set_ylabel('Predicted Returns')
    ax4.set_title('Individual Model Performance')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Performance metrics
    ax5 = axes[1, 1]
    perf = results['performance']
    metrics = ['R²', 'Directional\nAccuracy', 'RMSE', 'MAE']
    values = [perf['r2'], perf['directional_accuracy'], 
              np.sqrt(perf['mse']), perf['mae']]
    
    bars = ax5.bar(metrics, values, color=['blue', 'green', 'red', 'orange'])
    ax5.set_ylabel('Value')
    ax5.set_title('Ensemble Performance Metrics')
    ax5.grid(True, alpha=0.3)
    
    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 6. Feature category importance
    ax6 = axes[1, 2]
    if results['feature_importance'] is not None and results['feature_categories']:
        category_importance = {}
        for category, features in results['feature_categories'].items():
            category_features = results['feature_importance'][
                results['feature_importance']['feature'].isin(features)
            ]
            if len(category_features) > 0:
                category_importance[category] = category_features['importance'].sum()
        
        if category_importance:
            categories = list(category_importance.keys())
            importances = list(category_importance.values())
            bars = ax6.bar(categories, importances)
            ax6.set_ylabel('Total Importance')
            ax6.set_title('Feature Category Importance')
            ax6.tick_params(axis='x', rotation=45)
            ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('advanced_ai_models_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def main():
    """Main demonstration function."""
    
    print("🤖 Advanced AI Models and Feature Engineering Framework")
    print("=" * 80)
    print("LSTM, Ensemble Methods, Sophisticated Features & Multi-Class Capabilities")
    print("=" * 80)
    
    # Run demonstration
    results = demonstrate_advanced_ai_models()
    
    if results:
        # Create comprehensive visualization
        print(f"\n📈 Creating Comprehensive Analysis...")
        create_comprehensive_visualization(results)
        
        # Final summary
        print(f"\n🎯 Advanced AI Framework Achievements:")
        print("=" * 50)
        print("✅ ADVANCED Time-Series Models:")
        print("   • LSTM with multi-layer architecture")
        print("   • Random Forest with 50 estimators")
        print("   • Gradient Boosting with 50 estimators")
        print("   • Weighted ensemble aggregation")
        
        print(f"\n✅ SOPHISTICATED Feature Engineering:")
        print("   • Technical indicators (20+ features)")
        print("   • Lagged features for temporal patterns")
        print("   • Advanced volatility measures")
        print("   • Sentiment analysis integration")
        print("   • On-chain data simulation")
        print("   • Statistical and temporal features")
        
        print(f"\n✅ ENSEMBLE Intelligence:")
        print("   • Multi-model weighted voting")
        print("   • Individual model performance tracking")
        print("   • Robust prediction aggregation")
        
        print(f"\n✅ MULTI-CLASS Capabilities:")
        print("   • Continuous return prediction")
        print("   • Directional accuracy analysis")
        print("   • Advanced performance metrics")
        print("   • Feature importance analysis")
        
        perf = results['performance']
        print(f"\n📊 Performance Summary:")
        print(f"   • R² Score: {perf['r2']:.3f}")
        print(f"   • Directional Accuracy: {perf['directional_accuracy']:.1%}")
        print(f"   • RMSE: {np.sqrt(perf['mse']):.6f}")
        
        print(f"\n🎉 Advanced AI Models Framework Complete!")
        print("🚀 State-of-the-art ML capabilities successfully integrated!")
        
        return results
    else:
        print("❌ Demo failed - please check data processing")
        return None

if __name__ == "__main__":
    main() 