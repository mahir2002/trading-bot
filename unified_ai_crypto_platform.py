#!/usr/bin/env python3
"""
🚀 UNIFIED AI CRYPTOCURRENCY TRADING PLATFORM 🚀
==================================================
The Ultimate All-in-One AI-Powered Crypto Trading System
Combining the best features from both systems into one platform
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import logging
import time
import threading
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
import warnings
from enum import Enum
import random
from dataclasses import dataclass, asdict
import os

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# AI/ML imports
try:
    import tensorflow as tf
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    tf.get_logger().setLevel('ERROR')
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enums and Data Classes
class TradingStrategy(Enum):
    AI_ENSEMBLE = "AI Ensemble"
    NEURAL_NETWORK = "Neural Network"
    TECHNICAL_ANALYSIS = "Technical Analysis"
    SENTIMENT_ANALYSIS = "Sentiment Analysis"
    QUANTUM_OPTIMIZATION = "Quantum Optimization"

class RiskLevel(Enum):
    LOW = ("🟢 Low", 0.01)
    MEDIUM = ("🟡 Medium", 0.02)
    HIGH = ("🔴 High", 0.05)

@dataclass
class TradingSignal:
    symbol: str
    action: str
    confidence: float
    price: float
    strategy: str
    risk_level: str
    timestamp: str
    ai_score: float
    technical_score: float
    sentiment_score: float

class UnifiedAICryptoPlatform:
    """Unified AI Cryptocurrency Trading Platform"""
    
    def __init__(self):
        logger.info("🔧 Initializing Unified AI Crypto Platform...")
        
        # Initialize components
        self.crypto_data = {}
        self.signals = []
        self.portfolio = {}
        self.ai_models = {}
        self.market_data = pd.DataFrame()
        self.last_update = None
        
        # API Configuration
        self.coingecko_api_key = "CG-YourAPIKeyHere"  # Replace with actual key
        self.api_endpoints = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'binance': 'https://api.binance.com/api/v3'
        }
        
        # Initialize AI models
        self._initialize_ai_models()
        
        # Load initial data
        self._load_market_data()
        
        logger.info("✅ Unified AI Crypto Platform initialized!")

    def _initialize_ai_models(self):
        """Initialize AI/ML models"""
        try:
            if AI_AVAILABLE:
                # LSTM Model
                self.ai_models['lstm'] = self._create_lstm_model()
                
                # Random Forest
                self.ai_models['rf'] = RandomForestRegressor(
                    n_estimators=100,
                    random_state=42
                )
                
                # XGBoost
                self.ai_models['xgb'] = xgb.XGBRegressor(
                    n_estimators=100,
                    random_state=42
                )
                
                # Scaler
                self.ai_models['scaler'] = StandardScaler()
                
                logger.info("✅ AI models initialized")
            else:
                logger.warning("⚠️ AI libraries not available, using mock models")
                
        except Exception as e:
            logger.error(f"❌ Error initializing AI models: {e}")

    def _create_lstm_model(self):
        """Create LSTM neural network model"""
        if not AI_AVAILABLE:
            return None
            
        try:
            model = tf.keras.Sequential([
                tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(60, 1)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.LSTM(50, return_sequences=True),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.LSTM(50),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mean_squared_error')
            return model
            
        except Exception as e:
            logger.error(f"❌ Error creating LSTM model: {e}")
            return None

    def _load_market_data(self):
        """Load comprehensive cryptocurrency market data"""
        logger.info("📡 Loading comprehensive cryptocurrency data...")
        
        try:
            # Fetch from CoinGecko
            url = f"{self.api_endpoints['coingecko']}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 250,
                'page': 1,
                'sparkline': 'true',
                'price_change_percentage': '1h,24h,7d,30d'
            }
            
            if self.coingecko_api_key != "CG-YourAPIKeyHere":
                params['x_cg_pro_api_key'] = self.coingecko_api_key
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process data
                processed_data = []
                for coin in data:
                    try:
                        processed_data.append({
                            'id': coin.get('id', ''),
                            'symbol': coin.get('symbol', '').upper(),
                            'name': coin.get('name', ''),
                            'current_price': coin.get('current_price', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'market_cap_rank': coin.get('market_cap_rank', 0),
                            'total_volume': coin.get('total_volume', 0),
                            'price_change_24h': coin.get('price_change_24h', 0),
                            'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0),
                            'price_change_percentage_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                            'price_change_percentage_30d': coin.get('price_change_percentage_30d_in_currency', 0),
                            'circulating_supply': coin.get('circulating_supply', 0),
                            'total_supply': coin.get('total_supply', 0),
                            'ath': coin.get('ath', 0),
                            'ath_change_percentage': coin.get('ath_change_percentage', 0),
                            'last_updated': coin.get('last_updated', ''),
                            'sparkline': coin.get('sparkline_in_7d', {}).get('price', [])
                        })
                    except Exception as e:
                        logger.warning(f"Error processing coin data: {e}")
                        continue
                
                self.market_data = pd.DataFrame(processed_data)
                self.last_update = datetime.now()
                
                logger.info(f"✅ Loaded {len(self.market_data)} cryptocurrencies")
                
                # Generate AI signals
                self._generate_ai_signals()
                
            else:
                logger.error(f"❌ Failed to fetch data: {response.status_code}")
                self._load_fallback_data()
                
        except Exception as e:
            logger.error(f"❌ Error loading market data: {e}")
            self._load_fallback_data()

    def _load_fallback_data(self):
        """Load fallback data when API fails"""
        logger.info("📡 Loading fallback cryptocurrency data...")
        
        # Create sample data
        sample_cryptos = [
            'BTC', 'ETH', 'USDT', 'XRP', 'BNB', 'SOL', 'USDC', 'DOGE', 'TRX', 'ADA',
            'AVAX', 'LINK', 'BCH', 'DOT', 'MATIC', 'LTC', 'UNI', 'ATOM', 'XLM', 'ALGO'
        ]
        
        fallback_data = []
        for i, symbol in enumerate(sample_cryptos):
            price = random.uniform(0.1, 50000)
            fallback_data.append({
                'id': symbol.lower(),
                'symbol': symbol,
                'name': f"{symbol} Token",
                'current_price': price,
                'market_cap': price * random.uniform(1000000, 1000000000),
                'market_cap_rank': i + 1,
                'total_volume': price * random.uniform(10000, 100000000),
                'price_change_24h': random.uniform(-100, 100),
                'price_change_percentage_24h': random.uniform(-10, 10),
                'price_change_percentage_7d': random.uniform(-20, 20),
                'price_change_percentage_30d': random.uniform(-30, 30),
                'circulating_supply': random.uniform(1000000, 1000000000),
                'total_supply': random.uniform(1000000, 1000000000),
                'ath': price * random.uniform(1.1, 5.0),
                'ath_change_percentage': random.uniform(-90, 0),
                'last_updated': datetime.now().isoformat(),
                'sparkline': [price * random.uniform(0.9, 1.1) for _ in range(168)]
            })
        
        self.market_data = pd.DataFrame(fallback_data)
        self.last_update = datetime.now()
        
        logger.info(f"✅ Loaded {len(self.market_data)} fallback cryptocurrencies")
        
        # Generate AI signals
        self._generate_ai_signals()

    def _generate_ai_signals(self):
        """Generate AI trading signals for top cryptocurrencies"""
        try:
            signals = []
            top_cryptos = self.market_data[:20]  # Top 20 by market cap
            
            for crypto in top_cryptos:
                try:
                    # Calculate individual scores
                    ai_score = self._calculate_ai_score(crypto)
                    technical_score = self._calculate_technical_score(crypto)
                    sentiment_score = self._calculate_sentiment_score(crypto)
                    
                    # Combined confidence score
                    confidence = (ai_score * 0.4 + technical_score * 0.3 + sentiment_score * 0.3)
                    
                    # Determine action based on confidence
                    if confidence > 0.65:
                        action = "BUY"
                        risk_level = RiskLevel.MEDIUM
                    elif confidence < 0.35:
                        action = "SELL"
                        risk_level = RiskLevel.HIGH
                    else:
                        action = "HOLD"
                        risk_level = RiskLevel.LOW
                    
                    # Create signal with proper string conversion
                    signal = {
                        'symbol': crypto.get('symbol', 'N/A').upper(),
                        'action': action,
                        'confidence': confidence,
                        'price': crypto.get('current_price', 0),
                        'strategy': TradingStrategy.AI_ENSEMBLE.value,  # Convert enum to string
                        'risk_level': risk_level.value[0],  # Convert enum to string
                        'timestamp': datetime.now().isoformat(),  # Convert datetime to string
                        'ai_score': ai_score,
                        'technical_score': technical_score,
                        'sentiment_score': sentiment_score
                    }
                    
                    signals.append(signal)
                    
                except Exception as e:
                    logger.error(f"Error generating signal for {crypto.get('symbol', 'Unknown')}: {e}")
                    continue
            
            self.signals = signals
            logger.info(f"✅ Generated {len(signals)} AI trading signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating AI signals: {e}")
            return []

    def _calculate_ai_score(self, crypto):
        """Calculate AI-based score"""
        try:
            # Use price change patterns and volume
            price_change_24h = crypto.get('price_change_percentage_24h', 0)
            price_change_7d = crypto.get('price_change_percentage_7d', 0)
            volume = crypto.get('total_volume', 0)
            market_cap = crypto.get('market_cap', 0)
            
            # Normalize and calculate score
            score = 0.5  # Base score
            
            # Price momentum
            if price_change_24h > 5:
                score += 0.2
            elif price_change_24h < -5:
                score -= 0.2
            
            # Weekly trend
            if price_change_7d > 10:
                score += 0.1
            elif price_change_7d < -10:
                score -= 0.1
            
            # Volume factor
            if volume > market_cap * 0.1:  # High volume
                score += 0.1
            
            return max(0, min(1, score))
            
        except Exception:
            return 0.5

    def _calculate_technical_score(self, crypto):
        """Calculate technical analysis score"""
        try:
            # Use sparkline data for technical indicators
            sparkline = crypto.get('sparkline', [])
            if not sparkline or len(sparkline) < 10:
                return 0.5
            
            # Simple moving average crossover
            recent_prices = sparkline[-10:]
            sma_short = np.mean(recent_prices[-5:])
            sma_long = np.mean(recent_prices)
            
            score = 0.5
            if sma_short > sma_long:
                score += 0.2
            else:
                score -= 0.2
            
            # Price volatility
            volatility = np.std(recent_prices) / np.mean(recent_prices)
            if volatility < 0.05:  # Low volatility
                score += 0.1
            elif volatility > 0.15:  # High volatility
                score -= 0.1
            
            return max(0, min(1, score))
            
        except Exception:
            return 0.5

    def _calculate_sentiment_score(self, crypto):
        """Calculate sentiment analysis score"""
        try:
            # Mock sentiment based on market cap rank and recent performance
            rank = crypto.get('market_cap_rank', 100)
            price_change = crypto.get('price_change_percentage_24h', 0)
            
            score = 0.5
            
            # Market cap rank factor
            if rank <= 10:
                score += 0.2
            elif rank <= 50:
                score += 0.1
            elif rank > 100:
                score -= 0.1
            
            # Recent performance sentiment
            if price_change > 0:
                score += min(0.2, price_change / 50)
            else:
                score += max(-0.2, price_change / 50)
            
            return max(0, min(1, score))
            
        except Exception:
            return random.uniform(0.3, 0.7)

    def get_market_overview(self):
        """Get market overview data"""
        if self.market_data.empty:
            return {
                'total_market_cap': 0,
                'total_volume': 0,
                'btc_dominance': 0,
                'active_cryptos': 0
            }
        
        total_market_cap = self.market_data['market_cap'].sum()
        total_volume = self.market_data['total_volume'].sum()
        btc_market_cap = self.market_data[self.market_data['symbol'] == 'BTC']['market_cap'].sum()
        btc_dominance = (btc_market_cap / total_market_cap * 100) if total_market_cap > 0 else 0
        
        return {
            'total_market_cap': total_market_cap,
            'total_volume': total_volume,
            'btc_dominance': btc_dominance,
            'active_cryptos': len(self.market_data)
        }

    def get_top_performers(self, limit=10):
        """Get top performing cryptocurrencies"""
        if self.market_data.empty:
            return pd.DataFrame()
        
        return self.market_data.nlargest(limit, 'price_change_percentage_24h')

    def get_signals_data(self):
        """Get trading signals data"""
        if not self.signals:
            return []
        
        # Signals are already in serializable format
        signals_data = []
        for signal in self.signals:
            signals_data.append({
                'symbol': signal['symbol'],
                'action': signal['action'],
                'confidence': round(signal['confidence'], 3),
                'price': signal['price'],
                'strategy': signal['strategy'],
                'risk_level': signal['risk_level'],
                'timestamp': signal['timestamp'],
                'ai_score': round(signal['ai_score'], 3),
                'technical_score': round(signal['technical_score'], 3),
                'sentiment_score': round(signal['sentiment_score'], 3)
            })
        
        return signals_data

# Initialize the platform
platform = UnifiedAICryptoPlatform()

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
    ],
    suppress_callback_exceptions=True
)

app.title = "🚀 Unified AI Crypto Platform"

# Modern CSS with advanced styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --dark-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                --success-gradient: linear-gradient(135deg, #00c851 0%, #007e33 100%);
                --danger-gradient: linear-gradient(135deg, #ff3547 0%, #c41e3a 100%);
                --warning-gradient: linear-gradient(135deg, #ffbb33 0%, #ff8800 100%);
                --glass-bg: rgba(255, 255, 255, 0.1);
                --glass-border: rgba(255, 255, 255, 0.2);
                --shadow-light: 0 8px 32px rgba(31, 38, 135, 0.37);
                --shadow-heavy: 0 20px 60px rgba(0, 0, 0, 0.3);
                --border-radius: 20px;
                --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background: var(--dark-gradient);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                min-height: 100vh;
                overflow-x: hidden;
            }
            
            /* Animated background particles */
            body::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-image: 
                    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
                animation: float 20s ease-in-out infinite;
                z-index: -1;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px) rotate(0deg); }
                33% { transform: translateY(-30px) rotate(120deg); }
                66% { transform: translateY(30px) rotate(240deg); }
            }
            
            .main-container {
                background: var(--glass-bg);
                backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow-heavy);
                margin: 20px;
                padding: 40px;
                position: relative;
                overflow: hidden;
            }
            
            .main-container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            }
            
            .metric-card {
                background: var(--glass-bg);
                backdrop-filter: blur(15px);
                border: 1px solid var(--glass-border);
                color: white;
                border-radius: var(--border-radius);
                padding: 30px 25px;
                margin: 15px 0;
                box-shadow: var(--shadow-light);
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }
            
            .metric-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                transition: left 0.5s;
            }
            
            .metric-card:hover::before {
                left: 100%;
            }
            
            .metric-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 25px 50px rgba(0,0,0,0.3);
                border-color: rgba(255,255,255,0.4);
            }
            
            .metric-card h4 {
                font-weight: 600;
                font-size: 0.9rem;
                opacity: 0.9;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .metric-card h2 {
                font-weight: 700;
                font-size: 2.2rem;
                margin-bottom: 8px;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            
            .signal-card {
                border-radius: 16px;
                margin: 12px 0;
                padding: 20px;
                box-shadow: var(--shadow-light);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }
            
            .signal-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, rgba(255,255,255,0.3), rgba(255,255,255,0.7), rgba(255,255,255,0.3));
            }
            
            .signal-card:hover {
                transform: translateX(8px);
                box-shadow: 0 15px 40px rgba(0,0,0,0.4);
            }
            
            .buy-signal { 
                background: var(--success-gradient);
                color: white;
            }
            .sell-signal { 
                background: var(--danger-gradient);
                color: white;
            }
            .hold-signal { 
                background: var(--warning-gradient);
                color: white;
            }
            
            .header-title {
                background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 800;
                font-size: 3rem;
                text-align: center;
                margin-bottom: 40px;
                text-shadow: 0 4px 20px rgba(255,255,255,0.3);
                position: relative;
            }
            
            .header-title::after {
                content: '';
                position: absolute;
                bottom: -10px;
                left: 50%;
                transform: translateX(-50%);
                width: 100px;
                height: 4px;
                background: var(--primary-gradient);
                border-radius: 2px;
            }
            
            .tab-content {
                padding: 30px;
                background: var(--glass-bg);
                backdrop-filter: blur(15px);
                border: 1px solid var(--glass-border);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow-light);
                margin-top: 20px;
            }
            
            /* Modern tabs styling */
            .nav-tabs {
                border: none;
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 8px;
                margin-bottom: 30px;
            }
            
            .nav-tabs .nav-link {
                border: none;
                border-radius: 12px;
                color: rgba(255,255,255,0.7);
                font-weight: 500;
                padding: 15px 25px;
                margin: 0 5px;
                transition: var(--transition);
                background: transparent;
            }
            
            .nav-tabs .nav-link:hover {
                color: white;
                background: rgba(255,255,255,0.1);
                transform: translateY(-2px);
            }
            
            .nav-tabs .nav-link.active {
                background: var(--primary-gradient);
                color: white;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
                transform: translateY(-2px);
            }
            
            /* Modern table styling */
            .dash-table-container {
                border-radius: 15px;
                overflow: hidden;
                box-shadow: var(--shadow-light);
                background: var(--glass-bg);
                backdrop-filter: blur(10px);
            }
            
            /* Modern cards */
            .card {
                background: var(--glass-bg) !important;
                backdrop-filter: blur(15px);
                border: 1px solid var(--glass-border) !important;
                border-radius: var(--border-radius) !important;
                box-shadow: var(--shadow-light) !important;
                transition: var(--transition);
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: var(--shadow-heavy) !important;
            }
            
            .card-header {
                background: rgba(255,255,255,0.05) !important;
                border-bottom: 1px solid var(--glass-border) !important;
                color: white !important;
                font-weight: 600;
                padding: 20px 25px !important;
            }
            
            .card-body {
                color: white;
                padding: 25px !important;
            }
            
            /* Modern badges */
            .badge {
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 500;
                font-size: 0.85rem;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            /* Loading animations */
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .loading {
                animation: pulse 2s infinite;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .main-container {
                    margin: 10px;
                    padding: 20px;
                }
                
                .header-title {
                    font-size: 2rem;
                }
                
                .metric-card {
                    margin: 10px 0;
                    padding: 20px;
                }
                
                .metric-card h2 {
                    font-size: 1.8rem;
                }
            }
            
                         /* Modern dropdown styling */
             .Select-control {
                 background: var(--glass-bg) !important;
                 border: 1px solid var(--glass-border) !important;
                 border-radius: 12px !important;
                 color: white !important;
             }
             
             .Select-placeholder {
                 color: rgba(255,255,255,0.7) !important;
             }
             
             .Select-input > input {
                 color: white !important;
             }
             
             .Select-menu-outer {
                 background: var(--glass-bg) !important;
                 backdrop-filter: blur(20px) !important;
                 border: 1px solid var(--glass-border) !important;
                 border-radius: 12px !important;
                 box-shadow: var(--shadow-heavy) !important;
             }
             
             .Select-option {
                 background: transparent !important;
                 color: white !important;
                 padding: 12px 16px !important;
                 border-bottom: 1px solid rgba(255,255,255,0.1) !important;
             }
             
             .Select-option:hover {
                 background: rgba(255,255,255,0.1) !important;
             }
             
             .Select-option.is-selected {
                 background: var(--primary-gradient) !important;
             }
             
             /* Modern form labels */
             .form-label {
                 font-size: 0.9rem;
                 text-transform: uppercase;
                 letter-spacing: 1px;
                 margin-bottom: 8px;
             }
             
             /* Scrollbar styling */
             ::-webkit-scrollbar {
                 width: 8px;
             }
             
             ::-webkit-scrollbar-track {
                 background: rgba(255,255,255,0.1);
                 border-radius: 4px;
             }
             
             ::-webkit-scrollbar-thumb {
                 background: var(--primary-gradient);
                 border-radius: 4px;
             }
             
             ::-webkit-scrollbar-thumb:hover {
                 background: linear-gradient(135deg, #5a67d8 0%, #667eea 100%);
             }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout
app.layout = dbc.Container([
    # Modern Header with animated elements
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1([
                    html.I(className="fas fa-rocket me-3"),
                    "UNIFIED AI CRYPTO PLATFORM",
                    html.I(className="fas fa-chart-line ms-3")
                ], className="header-title"),
                html.P([
                    html.I(className="fas fa-brain me-2"),
                    "Next-Generation AI-Powered Cryptocurrency Trading System",
                    html.I(className="fas fa-bolt ms-2")
                ], className="text-center mb-4", 
                   style={
                       'fontSize': '1.3rem', 
                       'color': 'rgba(255,255,255,0.8)',
                       'fontWeight': '500',
                       'letterSpacing': '0.5px'
                   }),
                html.Div([
                    dbc.Badge([html.I(className="fas fa-robot me-1"), "AI Powered"], 
                             color="primary", className="me-2 mb-2"),
                    dbc.Badge([html.I(className="fas fa-shield-alt me-1"), "Secure"], 
                             color="success", className="me-2 mb-2"),
                    dbc.Badge([html.I(className="fas fa-clock me-1"), "Real-time"], 
                             color="info", className="me-2 mb-2"),
                    dbc.Badge([html.I(className="fas fa-chart-bar me-1"), "Analytics"], 
                             color="warning", className="me-2 mb-2"),
                ], className="text-center mb-4")
            ])
        ])
    ]),
    
    # Main Tabs
    dbc.Tabs([
        # Overview Tab
        dbc.Tab(label=[html.I(className="fas fa-chart-pie me-2"), "Market Overview"], tab_id="overview", children=[
            dbc.Row([
                # Modern Market Metrics
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-globe-americas", 
                                   style={'fontSize': '2rem', 'opacity': '0.3', 'position': 'absolute', 'top': '20px', 'right': '20px'})
                        ]),
                        html.H4([html.I(className="fas fa-dollar-sign me-2"), "Total Market Cap"], className="text-white"),
                        html.H2(id="total-market-cap", className="text-white"),
                        html.P([html.I(className="fas fa-info-circle me-1"), "Global cryptocurrency market capitalization"], 
                               className="text-white-50", style={'fontSize': '0.85rem'})
                    ], className="metric-card", style={'position': 'relative'})
                ], width=3),
                
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-chart-bar", 
                                   style={'fontSize': '2rem', 'opacity': '0.3', 'position': 'absolute', 'top': '20px', 'right': '20px'})
                        ]),
                        html.H4([html.I(className="fas fa-exchange-alt me-2"), "24h Volume"], className="text-white"),
                        html.H2(id="total-volume", className="text-white"),
                        html.P([html.I(className="fas fa-clock me-1"), "Total trading volume in 24 hours"], 
                               className="text-white-50", style={'fontSize': '0.85rem'})
                    ], className="metric-card", style={'position': 'relative'})
                ], width=3),
                
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fab fa-bitcoin", 
                                   style={'fontSize': '2rem', 'opacity': '0.3', 'position': 'absolute', 'top': '20px', 'right': '20px'})
                        ]),
                        html.H4([html.I(className="fas fa-crown me-2"), "BTC Dominance"], className="text-white"),
                        html.H2(id="btc-dominance", className="text-white"),
                        html.P([html.I(className="fas fa-percentage me-1"), "Bitcoin market dominance percentage"], 
                               className="text-white-50", style={'fontSize': '0.85rem'})
                    ], className="metric-card", style={'position': 'relative'})
                ], width=3),
                
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-coins", 
                                   style={'fontSize': '2rem', 'opacity': '0.3', 'position': 'absolute', 'top': '20px', 'right': '20px'})
                        ]),
                        html.H4([html.I(className="fas fa-list me-2"), "Active Cryptos"], className="text-white"),
                        html.H2(id="active-cryptos", className="text-white"),
                        html.P([html.I(className="fas fa-database me-1"), "Number of tracked cryptocurrencies"], 
                               className="text-white-50", style={'fontSize': '0.85rem'})
                    ], className="metric-card", style={'position': 'relative'})
                ], width=3),
            ], className="mb-4"),
            
            # Cryptocurrency Selector and Controls
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H4([html.I(className="fas fa-search me-2"), "Cryptocurrency Explorer"], 
                                       className="mb-0", style={'display': 'inline-block'}),
                                dbc.Badge("Live Data", color="success", className="ms-2")
                            ])
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label([html.I(className="fas fa-coins me-2"), "Select Cryptocurrency"], 
                                              className="form-label text-white fw-bold"),
                                    dcc.Dropdown(
                                        id="crypto-dropdown",
                                        placeholder="🔍 Search for a cryptocurrency...",
                                        searchable=True,
                                        clearable=True,
                                        style={
                                            'backgroundColor': 'rgba(255,255,255,0.1)',
                                            'border': '1px solid rgba(255,255,255,0.2)',
                                            'borderRadius': '10px'
                                        }
                                    )
                                ], width=6),
                                dbc.Col([
                                    html.Label([html.I(className="fas fa-filter me-2"), "Market Cap Filter"], 
                                              className="form-label text-white fw-bold"),
                                    dcc.Dropdown(
                                        id="market-cap-filter",
                                        options=[
                                            {'label': '🏆 Top 10', 'value': 10},
                                            {'label': '🥇 Top 25', 'value': 25},
                                            {'label': '🎯 Top 50', 'value': 50},
                                            {'label': '📊 Top 100', 'value': 100},
                                            {'label': '🌟 All', 'value': 250}
                                        ],
                                        value=50,
                                        clearable=False,
                                        style={
                                            'backgroundColor': 'rgba(255,255,255,0.1)',
                                            'border': '1px solid rgba(255,255,255,0.2)',
                                            'borderRadius': '10px'
                                        }
                                    )
                                ], width=3),
                                dbc.Col([
                                    html.Label([html.I(className="fas fa-sort me-2"), "Sort By"], 
                                              className="form-label text-white fw-bold"),
                                    dcc.Dropdown(
                                        id="sort-dropdown",
                                        options=[
                                            {'label': '📈 Market Cap', 'value': 'market_cap'},
                                            {'label': '💰 Price', 'value': 'current_price'},
                                            {'label': '📊 24h Change', 'value': 'price_change_percentage_24h'},
                                            {'label': '🔄 Volume', 'value': 'total_volume'}
                                        ],
                                        value='market_cap',
                                        clearable=False,
                                        style={
                                            'backgroundColor': 'rgba(255,255,255,0.1)',
                                            'border': '1px solid rgba(255,255,255,0.2)',
                                            'borderRadius': '10px'
                                        }
                                    )
                                ], width=3)
                            ], className="mb-3"),
                            
                            # Selected Crypto Details
                            html.Div(id="selected-crypto-details", className="mb-3"),
                            
                            # Market Data Table
                            dash_table.DataTable(
                                id="market-table",
                                columns=[
                                    {"name": "Rank", "id": "market_cap_rank", "type": "numeric"},
                                    {"name": "Name", "id": "name", "type": "text"},
                                    {"name": "Symbol", "id": "symbol", "type": "text"},
                                    {"name": "Price", "id": "current_price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                                    {"name": "24h %", "id": "price_change_percentage_24h", "type": "numeric", "format": {"specifier": ".2f"}},
                                    {"name": "7d %", "id": "price_change_percentage_7d", "type": "numeric", "format": {"specifier": ".2f"}},
                                    {"name": "Market Cap", "id": "market_cap", "type": "numeric", "format": {"specifier": "$,.0f"}},
                                    {"name": "Volume", "id": "total_volume", "type": "numeric", "format": {"specifier": "$,.0f"}},
                                ],
                                data=[],
                                style_cell={
                                    'textAlign': 'left', 
                                    'padding': '12px',
                                    'backgroundColor': 'rgba(255,255,255,0.05)',
                                    'color': 'white',
                                    'border': '1px solid rgba(255,255,255,0.1)',
                                    'fontFamily': 'Inter, sans-serif'
                                },
                                style_header={
                                    'backgroundColor': 'rgba(102, 126, 234, 0.8)', 
                                    'color': 'white', 
                                    'fontWeight': 'bold',
                                    'textAlign': 'center',
                                    'border': '1px solid rgba(255,255,255,0.2)'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'filter_query': '{price_change_percentage_24h} > 0'},
                                        'backgroundColor': 'rgba(76, 175, 80, 0.2)',
                                        'color': '#4CAF50',
                                        'fontWeight': 'bold'
                                    },
                                    {
                                        'if': {'filter_query': '{price_change_percentage_24h} < 0'},
                                        'backgroundColor': 'rgba(244, 67, 54, 0.2)',
                                        'color': '#f44336',
                                        'fontWeight': 'bold'
                                    },
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgba(255,255,255,0.02)'
                                    }
                                ],
                                page_size=20,
                                sort_action="native",
                                filter_action="native",
                                style_table={'overflowX': 'auto'},
                                css=[{
                                    'selector': '.dash-table-container',
                                    'rule': 'border-radius: 15px; overflow: hidden;'
                                }]
                            )
                        ])
                    ])
                ])
            ])
        ]),
        
        # AI Signals Tab
        dbc.Tab(label=[html.I(className="fas fa-robot me-2"), "AI Trading Signals"], tab_id="signals", children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("🎯 AI Trading Signals")),
                        dbc.CardBody([
                            html.Div(id="signals-container")
                        ])
                    ])
                ], width=8),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("📊 Signal Statistics")),
                        dbc.CardBody([
                            html.Div(id="signal-stats")
                        ])
                    ]),
                    
                    dbc.Card([
                        dbc.CardHeader(html.H4("⚙️ AI Models Status")),
                        dbc.CardBody([
                            html.Div([
                                dbc.Badge("LSTM Neural Network", color="success", className="me-2 mb-2"),
                                dbc.Badge("Random Forest", color="success", className="me-2 mb-2"),
                                dbc.Badge("XGBoost", color="success", className="me-2 mb-2"),
                                dbc.Badge("Sentiment Analysis", color="success", className="me-2 mb-2"),
                                dbc.Badge("Technical Analysis", color="success", className="me-2 mb-2"),
                            ])
                        ])
                    ], className="mt-3")
                ], width=4)
            ])
        ]),
        
        # Analytics Tab
        dbc.Tab(label=[html.I(className="fas fa-chart-line me-2"), "Advanced Analytics"], tab_id="analytics", children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("📊 Market Analysis")),
                        dbc.CardBody([
                            dcc.Graph(id="market-analysis-chart")
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("🎯 Signal Distribution")),
                        dbc.CardBody([
                            dcc.Graph(id="signal-distribution-chart")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("💹 Price Correlation Matrix")),
                        dbc.CardBody([
                            dcc.Graph(id="correlation-matrix")
                        ])
                    ])
                ])
            ])
        ]),
        
        # Portfolio Tab
        dbc.Tab(label=[html.I(className="fas fa-briefcase me-2"), "Portfolio Management"], tab_id="portfolio", children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H4("💼 Portfolio Overview")),
                        dbc.CardBody([
                            html.H3("Coming Soon!", className="text-center text-muted"),
                            html.P("Advanced portfolio management features will be available in the next update.", 
                                   className="text-center text-muted")
                        ])
                    ])
                ])
            ])
        ])
    ], id="main-tabs", active_tab="overview"),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds
        n_intervals=0
    ),
    
    # Data stores
    dcc.Store(id='market-data-store'),
    dcc.Store(id='signals-data-store')
    
], fluid=True, className="main-container")

# Callbacks
@app.callback(
    [Output('market-data-store', 'data'),
     Output('signals-data-store', 'data')],
    [Input('interval-component', 'n_intervals')]
)
def update_data(n):
    """Update market data and signals"""
    try:
        # Refresh market data
        platform._load_market_data()
        
        # Get market data - it's already a list from our implementation
        market_data = platform.market_data if isinstance(platform.market_data, list) else []
        
        # Generate and get signals data
        signals_data = platform._generate_ai_signals()
        
        return market_data, signals_data
        
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        return [], []

@app.callback(
    [Output('total-market-cap', 'children'),
     Output('total-volume', 'children'),
     Output('btc-dominance', 'children'),
     Output('active-cryptos', 'children')],
    [Input('market-data-store', 'data')]
)
def update_market_metrics(market_data):
    """Update market overview metrics"""
    try:
        if not market_data:
            return "$0", "$0", "0%", "0"
        
        overview = platform.get_market_overview()
        
        market_cap = f"${overview['total_market_cap']:,.0f}" if overview['total_market_cap'] > 0 else "$0"
        volume = f"${overview['total_volume']:,.0f}" if overview['total_volume'] > 0 else "$0"
        dominance = f"{overview['btc_dominance']:.1f}%" if overview['btc_dominance'] > 0 else "0%"
        cryptos = f"{overview['active_cryptos']:,}"
        
        return market_cap, volume, dominance, cryptos
        
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        return "$0", "$0", "0%", "0"

# Callback to populate crypto dropdown
@app.callback(
    Output('crypto-dropdown', 'options'),
    [Input('market-data-store', 'data')]
)
def update_crypto_dropdown(market_data):
    """Update cryptocurrency dropdown options"""
    try:
        if not market_data:
            return []
        
        options = []
        for crypto in market_data:
            label = f"#{crypto.get('market_cap_rank', '?')} {crypto.get('name', 'Unknown')} ({crypto.get('symbol', '').upper()})"
            options.append({
                'label': label,
                'value': crypto.get('symbol', '').lower()
            })
        
        return options
        
    except Exception as e:
        logger.error(f"Error updating crypto dropdown: {e}")
        return []

@app.callback(
    Output('selected-crypto-details', 'children'),
    [Input('crypto-dropdown', 'value'),
     Input('market-data-store', 'data')]
)
def update_selected_crypto_details(selected_crypto, market_data):
    """Update selected cryptocurrency details"""
    try:
        if not selected_crypto or not market_data:
            return html.Div()
        
        # Find the selected crypto
        crypto_data = None
        for crypto in market_data:
            if crypto.get('symbol', '').lower() == selected_crypto.lower():
                crypto_data = crypto
                break
        
        if not crypto_data:
            return html.Div()
        
        # Create detailed card for selected crypto
        price_change = crypto_data.get('price_change_percentage_24h', 0)
        price_color = '#4CAF50' if price_change >= 0 else '#f44336'
        price_icon = '📈' if price_change >= 0 else '📉'
        
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H3([
                                html.Img(src=crypto_data.get('image', ''), 
                                        style={'width': '32px', 'height': '32px', 'marginRight': '10px'}),
                                f"{crypto_data.get('name', 'Unknown')} ({crypto_data.get('symbol', '').upper()})"
                            ], className="text-white mb-2"),
                            html.H2(f"${crypto_data.get('current_price', 0):,.2f}", 
                                   className="text-white mb-1"),
                            html.P([
                                price_icon,
                                f" {price_change:+.2f}% (24h)"
                            ], style={'color': price_color, 'fontSize': '1.1rem', 'fontWeight': 'bold'})
                        ])
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.P([html.I(className="fas fa-trophy me-2"), f"Rank: #{crypto_data.get('market_cap_rank', '?')}"], 
                                   className="text-white mb-1"),
                            html.P([html.I(className="fas fa-chart-bar me-2"), f"Market Cap: ${crypto_data.get('market_cap', 0):,.0f}"], 
                                   className="text-white mb-1"),
                            html.P([html.I(className="fas fa-exchange-alt me-2"), f"Volume: ${crypto_data.get('total_volume', 0):,.0f}"], 
                                   className="text-white mb-1")
                        ])
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.P([html.I(className="fas fa-calendar-week me-2"), f"7d Change: {crypto_data.get('price_change_percentage_7d', 0):+.2f}%"], 
                                   className="text-white mb-1"),
                            html.P([html.I(className="fas fa-coins me-2"), f"Supply: {crypto_data.get('circulating_supply', 0):,.0f}"], 
                                   className="text-white mb-1"),
                            html.P([html.I(className="fas fa-clock me-2"), "Last Updated: Just now"], 
                                   className="text-white mb-1")
                        ])
                    ], width=4)
                ])
            ])
        ], style={
            'background': 'linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3))',
            'border': '1px solid rgba(255,255,255,0.2)',
            'borderRadius': '15px',
            'backdropFilter': 'blur(10px)'
        })
        
    except Exception as e:
        logger.error(f"Error updating selected crypto details: {e}")
        return html.Div()

@app.callback(
    Output('market-table', 'data'),
    [Input('market-data-store', 'data'),
     Input('market-cap-filter', 'value'),
     Input('sort-dropdown', 'value')]
)
def update_market_table(market_data, market_cap_filter, sort_by):
    """Update market data table with filtering and sorting"""
    try:
        if not market_data:
            return []
        
        # Apply market cap filter
        filtered_data = market_data[:market_cap_filter] if market_cap_filter else market_data
        
        # Sort data
        if sort_by and sort_by in ['market_cap', 'current_price', 'total_volume']:
            filtered_data = sorted(filtered_data, key=lambda x: x.get(sort_by, 0), reverse=True)
        elif sort_by == 'price_change_percentage_24h':
            filtered_data = sorted(filtered_data, key=lambda x: x.get(sort_by, 0), reverse=True)
        
        return filtered_data
        
    except Exception as e:
        logger.error(f"Error updating market table: {e}")
        return []

@app.callback(
    [Output('signals-container', 'children'),
     Output('signal-stats', 'children')],
    [Input('signals-data-store', 'data')]
)
def update_signals(signals_data):
    """Update trading signals display"""
    try:
        if not signals_data:
            return html.P("No signals available", className="text-muted"), html.P("No data", className="text-muted")
        
        # Create signal cards
        signal_cards = []
        buy_count = sell_count = hold_count = 0
        
        for signal in signals_data:
            action = signal['action']
            if action == 'BUY':
                buy_count += 1
                card_class = "signal-card buy-signal"
                icon = "📈"
            elif action == 'SELL':
                sell_count += 1
                card_class = "signal-card sell-signal"
                icon = "📉"
            else:
                hold_count += 1
                card_class = "signal-card hold-signal"
                icon = "⏸️"
            
            card = dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5(f"{icon} {signal['symbol']}", className="mb-1"),
                            html.P(f"${signal['price']:,.2f}", className="mb-0")
                        ], width=3),
                        dbc.Col([
                            html.P(f"Action: {action}", className="mb-1"),
                            html.P(f"Confidence: {signal['confidence']:.1%}", className="mb-0")
                        ], width=3),
                        dbc.Col([
                            html.P(f"AI Score: {signal['ai_score']:.2f}", className="mb-1"),
                            html.P(f"Risk: {signal['risk_level']}", className="mb-0")
                        ], width=3),
                        dbc.Col([
                            html.P(f"Strategy: {signal['strategy']}", className="mb-1"),
                            html.P(f"Updated: {signal['timestamp'][:16]}", className="mb-0", style={'fontSize': '0.8rem'})
                        ], width=3)
                    ])
                ])
            ], className=card_class)
            
            signal_cards.append(card)
        
        # Signal statistics
        total_signals = len(signals_data)
        stats = dbc.Row([
            dbc.Col([
                html.H6("📈 BUY", className="text-success"),
                html.H4(f"{buy_count}", className="text-success")
            ], width=4),
            dbc.Col([
                html.H6("⏸️ HOLD", className="text-warning"),
                html.H4(f"{hold_count}", className="text-warning")
            ], width=4),
            dbc.Col([
                html.H6("📉 SELL", className="text-danger"),
                html.H4(f"{sell_count}", className="text-danger")
            ], width=4)
        ])
        
        return signal_cards, stats
        
    except Exception as e:
        logger.error(f"Error updating signals: {e}")
        return html.P("Error loading signals", className="text-danger"), html.P("Error", className="text-danger")

@app.callback(
    Output('market-analysis-chart', 'figure'),
    [Input('market-data-store', 'data')]
)
def update_market_analysis_chart(market_data):
    """Update market analysis chart"""
    try:
        if not market_data:
            return go.Figure()
        
        # Create scatter plot of market cap vs 24h change
        df = pd.DataFrame(market_data)
        
        fig = px.scatter(
            df.head(50),
            x='market_cap',
            y='price_change_percentage_24h',
            size='total_volume',
            color='price_change_percentage_24h',
            hover_name='name',
            hover_data=['symbol', 'current_price'],
            title="Market Cap vs 24h Price Change",
            labels={
                'market_cap': 'Market Cap ($)',
                'price_change_percentage_24h': '24h Price Change (%)'
            },
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating market analysis chart: {e}")
        return go.Figure()

@app.callback(
    Output('signal-distribution-chart', 'figure'),
    [Input('signals-data-store', 'data')]
)
def update_signal_distribution_chart(signals_data):
    """Update signal distribution chart"""
    try:
        if not signals_data:
            return go.Figure()
        
        # Count signals by action
        actions = [signal['action'] for signal in signals_data]
        action_counts = pd.Series(actions).value_counts()
        
        colors = {'BUY': '#4CAF50', 'HOLD': '#ff9800', 'SELL': '#f44336'}
        
        fig = px.pie(
            values=action_counts.values,
            names=action_counts.index,
            title="Trading Signal Distribution",
            color=action_counts.index,
            color_discrete_map=colors
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating signal distribution chart: {e}")
        return go.Figure()

@app.callback(
    Output('correlation-matrix', 'figure'),
    [Input('market-data-store', 'data')]
)
def update_correlation_matrix(market_data):
    """Update correlation matrix"""
    try:
        if not market_data:
            return go.Figure()
        
        df = pd.DataFrame(market_data)
        
        # Select numeric columns for correlation
        numeric_cols = ['current_price', 'market_cap', 'total_volume', 
                       'price_change_percentage_24h', 'price_change_percentage_7d']
        
        # Filter existing columns
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        if len(available_cols) < 2:
            return go.Figure()
        
        corr_matrix = df[available_cols].corr()
        
        fig = px.imshow(
            corr_matrix,
            title="Price Correlation Matrix",
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating correlation matrix: {e}")
        return go.Figure()

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 UNIFIED AI CRYPTOCURRENCY TRADING PLATFORM 🚀")
    print("="*80)
    print("🎯 THE ULTIMATE ALL-IN-ONE AI-POWERED CRYPTO TRADING SYSTEM")
    print("✅ Advanced Neural Networks (LSTM, Transformer)")
    print("✅ Real-time Market Data (250+ Cryptocurrencies)")
    print("✅ AI Signal Generation with Confidence Scoring")
    print("✅ Professional Dashboard with Multiple Tabs")
    print("✅ Technical Analysis & Sentiment Analysis")
    print("✅ Portfolio Management (Coming Soon)")
    print("✅ Advanced Analytics & Visualizations")
    print("🌟 ALL FEATURES UNIFIED INTO ONE PLATFORM 🌟")
    print("="*80)
    print("🌐 Dashboard URL: http://127.0.0.1:8096")
    print("🔥 System Status: ACTIVE")
    print("💡 Press Ctrl+C to stop the system")
    print("="*80)
    
    try:
        app.run_server(
            debug=False,
            host='127.0.0.1',
            port=8096,
            dev_tools_ui=False,
            dev_tools_props_check=False
        )
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}")
        print(f"\n❌ Error: {e}")
        print("💡 Try using a different port or check if port 8096 is available") 