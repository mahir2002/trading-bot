#!/usr/bin/env python3
"""
Simple Backtest Example - Estimate returns of the AI trading bot via backtesting
Simplified backtest using predicted signals and market returns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

def fetch_data(symbol="BTC/USDT", timeframe="1h", limit=1000):
    """Fetch or generate sample data"""
    # For demo purposes, generate synthetic data
    # In practice, you'd fetch real data from your exchange
    
    np.random.seed(42)  # For reproducible results
    dates = pd.date_range(start='2023-01-01', periods=limit, freq='H')
    
    # Generate realistic price movements
    returns = np.random.normal(0.0001, 0.02, limit)
    prices = [100]  # Starting price
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Create OHLCV data
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.uniform(1000, 10000, limit)
    })
    df.set_index('timestamp', inplace=True)
    
    return df

def create_features(df):
    """Create technical analysis features"""
    # Simple moving averages
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # Exponential moving average
    df['ema_12'] = df['close'].ewm(span=12).mean()
    
    # Price-based features
    df['price_change'] = df['close'].pct_change()
    df['volatility'] = df['price_change'].rolling(window=20).std()
    
    # Relative strength index (simplified)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD (simplified)
    ema_12 = df['close'].ewm(span=12).mean()
    ema_26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema_12 - ema_26
    
    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    
    # Additional features
    df['high_low_ratio'] = df['high'] / df['low']
    df['close_open_ratio'] = df['close'] / df['open']
    
    return df

def generate_labels(df):
    """Generate target labels for prediction"""
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    
    # Generate target: 1 if next period price goes up, 0 if down
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    return df

def train_model(df):
    """Train a simple AI model"""
    # Select features for training
    features = ['sma_20', 'sma_50', 'ema_12', 'volatility', 'rsi', 'macd', 
               'high_low_ratio', 'close_open_ratio']
    
    # Prepare data
    df_clean = df.dropna()
    X = df_clean[features]
    y = df_clean['target']
    
    # Split data (80% train, 20% test)
    split_idx = int(len(df_clean) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Save model and scaler
    joblib.dump(model, 'model.joblib')
    joblib.dump(scaler, 'scaler.joblib')
    
    print(f"✅ Model trained on {len(X_train)} samples")
    print(f"📊 Training accuracy: {model.score(X_train_scaled, y_train):.3f}")
    print(f"📊 Test accuracy: {model.score(X_test_scaled, y_test):.3f}")
    
    return model, scaler

def run_backtest(symbol="BTC/USDT", timeframe="1h", initial_capital=10000):
    """Run the complete backtest"""
    
    print(f"🚀 Starting backtest for {symbol} ({timeframe})")
    print(f"💰 Initial Capital: ${initial_capital:,.2f}")
    print("="*50)
    
    # Load data and model predictions
    print("📊 Fetching data...")
    df = fetch_data(symbol, timeframe)
    
    print("🔧 Creating features...")
    df = create_features(df)
    df = generate_labels(df)
    
    # Train model if not exists, otherwise load
    try:
        model = joblib.load('model.joblib')
        scaler = joblib.load('scaler.joblib')
        print("✅ Loaded existing model")
    except FileNotFoundError:
        print("🤖 Training new model...")
        model, scaler = train_model(df)
    
    # Add predicted signal to dataframe
    features = ['sma_20', 'sma_50', 'ema_12', 'volatility', 'rsi', 'macd', 
               'high_low_ratio', 'close_open_ratio']
    
    df_clean = df.dropna()
    X = df_clean[features]
    X_scaled = scaler.transform(X)
    
    # Get predictions and probabilities
    df_clean['predicted'] = model.predict(X_scaled)
    df_clean['predicted_prob'] = model.predict_proba(X_scaled)[:, 1]
    
    # Calculate confidence (distance from 0.5)
    df_clean['confidence'] = abs(df_clean['predicted_prob'] - 0.5) * 200
    
    # Simulate strategy returns (buy=1, sell/hold=0)
    # Only trade when confidence is above threshold
    confidence_threshold = 60
    df_clean['signal'] = np.where(df_clean['confidence'] > confidence_threshold, 
                                 df_clean['predicted'], 0)
    
    # Strategy returns: buy when signal=1, hold when signal=0
    # Convert signal to position: 1 for long, 0 for cash
    df_clean['position'] = df_clean['signal'].shift(1)  # Use previous signal
    df_clean['strategy_return'] = df_clean['returns'] * df_clean['position']
    
    # Cumulative returns
    df_clean['market_cum_return'] = (1 + df_clean['returns']).cumprod()
    df_clean['strategy_cum_return'] = (1 + df_clean['strategy_return']).cumprod()
    
    # Calculate portfolio value
    df_clean['portfolio_value'] = initial_capital * df_clean['strategy_cum_return']
    
    # Print metrics
    print("\n" + "="*50)
    print("📊 BACKTEST RESULTS")
    print("="*50)
    
    # Model accuracy
    valid_predictions = df_clean.dropna(subset=['target', 'predicted'])
    if len(valid_predictions) > 0:
        accuracy = accuracy_score(valid_predictions['target'], valid_predictions['predicted'])
        print(f"🤖 Model accuracy: {accuracy:.2%}")
    
    # Returns
    final_market_return = df_clean['market_cum_return'].iloc[-1]
    final_strategy_return = df_clean['strategy_cum_return'].iloc[-1]
    final_portfolio_value = df_clean['portfolio_value'].iloc[-1]
    
    print(f"📈 Final market return: {final_market_return:.2f}x ({(final_market_return-1)*100:.1f}%)")
    print(f"🎯 Final strategy return: {final_strategy_return:.2f}x ({(final_strategy_return-1)*100:.1f}%)")
    print(f"💰 Final portfolio value: ${final_portfolio_value:,.2f}")
    print(f"💵 Total profit/loss: ${final_portfolio_value - initial_capital:,.2f}")
    
    # Risk metrics
    strategy_returns = df_clean['strategy_return'].dropna()
    market_returns = df_clean['returns'].dropna()
    
    if len(strategy_returns) > 0:
        strategy_volatility = strategy_returns.std() * np.sqrt(252 * 24)  # Annualized
        market_volatility = market_returns.std() * np.sqrt(252 * 24)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252 * 24) if strategy_returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = df_clean['strategy_cum_return']
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        print(f"📊 Strategy volatility: {strategy_volatility:.2%}")
        print(f"📊 Market volatility: {market_volatility:.2%}")
        print(f"📊 Sharpe ratio: {sharpe_ratio:.2f}")
        print(f"📊 Maximum drawdown: {max_drawdown:.2%}")
    
    # Trading statistics
    trades = df_clean[df_clean['position'] == 1]
    total_trades = len(trades)
    winning_trades = len(trades[trades['strategy_return'] > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    print(f"💼 Total signals: {total_trades}")
    print(f"💼 Win rate: {win_rate:.2%}")
    print(f"💼 Average confidence: {df_clean[df_clean['signal']==1]['confidence'].mean():.1f}%")
    
    # Plot results
    plt.figure(figsize=(15, 10))
    
    # Cumulative returns comparison
    plt.subplot(2, 2, 1)
    plt.plot(df_clean.index, df_clean['market_cum_return'], label='Buy & Hold', linewidth=2)
    plt.plot(df_clean.index, df_clean['strategy_cum_return'], label='AI Strategy', linewidth=2)
    plt.title('Cumulative Returns Comparison')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Portfolio value
    plt.subplot(2, 2, 2)
    plt.plot(df_clean.index, df_clean['portfolio_value'], color='green', linewidth=2)
    plt.axhline(y=initial_capital, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
    plt.title('Portfolio Value Over Time')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Drawdown
    plt.subplot(2, 2, 3)
    cumulative_returns = df_clean['strategy_cum_return']
    rolling_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    plt.fill_between(df_clean.index, drawdown, 0, alpha=0.3, color='red')
    plt.plot(df_clean.index, drawdown, color='red', linewidth=1)
    plt.title('Strategy Drawdown')
    plt.ylabel('Drawdown')
    plt.grid(True, alpha=0.3)
    
    # Prediction confidence distribution
    plt.subplot(2, 2, 4)
    plt.hist(df_clean['confidence'], bins=30, alpha=0.7, edgecolor='black')
    plt.axvline(x=confidence_threshold, color='red', linestyle='--', alpha=0.7, label=f'Threshold ({confidence_threshold}%)')
    plt.title('Prediction Confidence Distribution')
    plt.xlabel('Confidence (%)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('simple_backtest_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\n📁 Results saved to 'simple_backtest_results.png'")
    
    # Performance rating
    score = 0
    if final_strategy_return > final_market_return: score += 1
    if final_strategy_return > 1.1: score += 1  # 10% return
    if sharpe_ratio > 1: score += 1
    if max_drawdown > -0.2: score += 1  # Less than 20% drawdown
    if win_rate > 0.5: score += 1
    
    # Ensure score is within bounds
    score = min(score, 4)  # Maximum index is 4
    rating = ["Poor", "Below Average", "Average", "Good", "Excellent"][score]
    print(f"\n⭐ OVERALL RATING: {rating} ({score}/5)")
    
    return df_clean

if __name__ == "__main__":
    # Run the backtest
    results = run_backtest(
        symbol="BTC/USDT",
        timeframe="1h",
        initial_capital=10000
    )
    
    print("\n✅ Backtest completed successfully!")
    print("💡 This is a simplified example. For production use:")
    print("   - Use real market data")
    print("   - Implement proper risk management")
    print("   - Consider transaction costs")
    print("   - Test on multiple time periods")
    print("   - Validate with out-of-sample data") 