#!/usr/bin/env python3
import requests
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import sqlite3
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("🚀 Starting Bot Training with Real Market Data")
print("=" * 60)

# Collect real BTC data from Binance
print("📊 Collecting real BTC market data...")
url = "https://api.binance.com/api/v3/klines"
params = {'symbol': 'BTCUSDT', 'interval': '1h', 'limit': 1000}

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # Convert data types
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    # Keep only OHLCV
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"✅ Collected {len(df)} real market records")
    print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"💰 Latest BTC price: ${df['close'].iloc[-1]:.2f}")
    
    # Create features
    print("🔧 Creating trading features...")
    df['price_change'] = df['close'].pct_change()
    df['price_change_5'] = df['close'].pct_change(5)
    df['sma_10'] = df['close'].rolling(10).mean()
    df['sma_20'] = df['close'].rolling(20).mean()
    df['price_to_sma10'] = df['close'] / df['sma_10']
    df['price_to_sma20'] = df['close'] / df['sma_20']
    df['volatility'] = df['close'].rolling(20).std()
    df['volume_sma'] = df['volume'].rolling(10).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # Create targets
    print("🎯 Creating trading targets...")
    df['future_price'] = df['close'].shift(-1)
    df['future_return'] = (df['future_price'] - df['close']) / df['close']
    df['target'] = (df['future_return'] > 0).astype(int)
    
    print(f"✅ Target distribution: {df['target'].value_counts().to_dict()}")
    
    # Train model
    print("🧠 Training AI model on real market data...")
    feature_cols = ['price_change', 'price_change_5', 'price_to_sma10', 'price_to_sma20', 'volatility', 'volume_ratio']
    
    df_clean = df.dropna()
    X = df_clean[feature_cols]
    y = df_clean['target']
    
    print(f"📊 Training data: {X.shape[0]} samples, {X.shape[1]} features")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    
    print(f"✅ Model trained successfully!")
    print(f"📈 Training accuracy: {train_acc:.1%}")
    print(f"📊 Test accuracy: {test_acc:.1%}")
    
    # Save to database
    print("💾 Saving results to database...")
    conn = sqlite3.connect("crypto_trading_data.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO model_performance 
        (model_type, accuracy, timestamp)
        VALUES (?, ?, ?)
    """, ('RealMarketData_RF', test_acc, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 TRAINING COMPLETE!")
    print(f"=" * 60)
    print(f"📊 Trained on {len(df_clean)} real market data points")
    print(f"🎯 Model accuracy: {test_acc:.1%}")
    print(f"💾 Results saved to database")
    print(f"\n🚀 Your bot now has REAL market intelligence!")
    print(f"🔥 Ready for improved trading performance!")
    
except Exception as e:
    print(f"❌ Training failed: {e}")
    print("Please check your internet connection and try again.")
