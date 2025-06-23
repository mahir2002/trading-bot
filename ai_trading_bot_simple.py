#!/usr/bin/env python3
"""
AI Crypto Trading Bot - Simplified Version
Features: Basic AI prediction, Telegram alerts, Google Sheets integration, Web Dashboard
"""

import os
import sys
import time
import logging
import asyncio
import schedule
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import ccxt
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from telegram import Bot
from telegram.error import TelegramError
import requests
import json

# Import custom Binance client
try:
    from binance_testnet_client import BinanceTestnetClient
except ImportError:
    BinanceTestnetClient = None

# Suppress warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

class TradingLogger:
    """Enhanced logging system for the trading bot"""
    
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(log_level)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler for general logs
        file_handler = logging.FileHandler(f'logs/trading_bot_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def trade(self, message):
        self.logger.info(f"TRADE: {message}")

class NotificationManager:
    """Handles Telegram notifications"""
    
    def __init__(self, logger):
        self.logger = logger
        self.telegram_bot = None
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Initialize Telegram bot
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token:
            try:
                self.telegram_bot = Bot(token=telegram_token)
                self.logger.info("Telegram bot initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram bot: {e}")
    
    async def send_telegram_message(self, message: str):
        """Send message via Telegram"""
        if not self.telegram_bot or not self.telegram_chat_id:
            return False
        
        try:
            await self.telegram_bot.send_message(chat_id=self.telegram_chat_id, text=message)
            return True
        except TelegramError as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def notify_trade(self, trade_info: Dict):
        """Send trade notification via Telegram"""
        message = f"""
🤖 AI Trading Bot Alert

📊 Symbol: {trade_info['symbol']}
📈 Action: {trade_info['action'].upper()}
💰 Amount: {trade_info['amount']}
💵 Price: ${trade_info['price']:.4f}
📅 Time: {trade_info['timestamp']}
🎯 Confidence: {trade_info.get('confidence', 'N/A')}%
        """
        
        await self.send_telegram_message(message)

class AIPredictor:
    """AI model for price prediction using Random Forest"""
    
    def __init__(self, logger):
        self.logger = logger
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.last_training = None
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare technical indicators as features"""
        # Price-based indicators
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
        
        # Momentum indicators
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['stoch'] = ta.momentum.stoch(df['high'], df['low'], df['close'])
        
        # Volatility indicators
        df['bb_upper'] = ta.volatility.bollinger_hband(df['close'])
        df['bb_middle'] = ta.volatility.bollinger_mavg(df['close'])
        df['bb_lower'] = ta.volatility.bollinger_lband(df['close'])
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
        
        # Volume indicators (fixed)
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['mfi'] = ta.volume.money_flow_index(df['high'], df['low'], df['close'], df['volume'])
        
        # Price action features
        df['price_change'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        
        # Target variable (1 if price goes up, 0 if down)
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        return df
    
    def train_models(self, df: pd.DataFrame):
        """Train Random Forest model"""
        try:
            # Prepare features
            df_features = self.prepare_features(df.copy())
            df_features = df_features.dropna()
            
            if len(df_features) < 100:
                self.logger.warning("Insufficient data for training")
                return False
            
            # Feature columns (excluding target and OHLCV)
            feature_cols = [col for col in df_features.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'target']]
            
            X = df_features[feature_cols].values
            y = df_features['target'].values
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.rf_model.fit(X_train_scaled, y_train)
            rf_accuracy = accuracy_score(y_test, self.rf_model.predict(X_test_scaled))
            
            self.is_trained = True
            self.last_training = datetime.now()
            
            self.logger.info(f"Model trained successfully. RF Accuracy: {rf_accuracy:.4f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to train models: {e}")
            return False
    
    def predict(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Make prediction using Random Forest"""
        if not self.is_trained:
            return 0.5, 0.0
        
        try:
            # Prepare features for the latest data point
            df_features = self.prepare_features(df.copy())
            df_features = df_features.dropna()
            
            if len(df_features) == 0:
                return 0.5, 0.0
            
            feature_cols = [col for col in df_features.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'target']]
            latest_features = df_features[feature_cols].iloc[-1:].values
            
            # Scale features
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Random Forest prediction
            rf_prob = self.rf_model.predict_proba(latest_features_scaled)[0][1]
            confidence = abs(rf_prob - 0.5) * 200  # Convert to percentage
            
            return rf_prob, confidence
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return 0.5, 0.0

class ExchangeManager:
    """Manages exchange connections and trading operations"""
    
    def __init__(self, logger):
        self.logger = logger
        self.exchanges = {}
        self.active_exchange = None
        
        # Initialize exchanges
        self._init_exchanges()
    
    def _init_exchanges(self):
        """Initialize exchange connections"""
        # Try custom Binance client first
        if BinanceTestnetClient:
            try:
                self.binance_client = BinanceTestnetClient()
                # Test the connection
                if self.binance_client.test_connection():
                    self.active_exchange = 'binance_custom'
                    self.logger.info("✅ Custom Binance client initialized successfully")
                    return
                else:
                    self.logger.warning("Custom Binance client test failed")
            except Exception as e:
                self.logger.warning(f"Custom Binance client failed: {e}")
        
        # Fallback to CCXT if custom client fails
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if api_key and secret_key:
            try:
                # Configure for testnet or live
                binance_config = {
                    'apiKey': api_key,
                    'secret': secret_key,
                    'enableRateLimit': True,
                }
                
                # Set testnet URL if using testnet
                if use_testnet:
                    binance_config['sandbox'] = True
                    binance_config['urls'] = {
                        'api': {
                            'public': 'https://testnet.binance.vision/api',
                            'private': 'https://testnet.binance.vision/api',
                        },
                        'test': {
                            'public': 'https://testnet.binance.vision/api',
                            'private': 'https://testnet.binance.vision/api',
                        }
                    }
                    self.logger.info("Using Binance Testnet")
                else:
                    self.logger.info("Using Binance Live API")
                
                # Try authenticated connection first
                self.exchanges['binance'] = ccxt.binance(binance_config)
                
                # Test the connection
                test_exchange = self.exchanges['binance']
                test_exchange.fetch_ticker('BTC/USDT')  # Test with public endpoint
                
                self.active_exchange = 'binance'
                self.logger.info("Binance exchange initialized with authentication")
                
            except Exception as e:
                self.logger.warning(f"Authenticated Binance connection failed: {e}")
                self.logger.info("Falling back to public API for paper trading...")
                
                # Fall back to public API
                try:
                    self.exchanges['binance_public'] = ccxt.binance({
                        'enableRateLimit': True,
                    })
                    self.active_exchange = 'binance_public'
                    self.logger.info("Binance public API initialized for paper trading")
                except Exception as e2:
                    self.logger.error(f"Failed to initialize Binance public API: {e2}")
        else:
            # No API keys provided, use public API
            try:
                self.exchanges['binance_public'] = ccxt.binance({
                    'enableRateLimit': True,
                })
                self.active_exchange = 'binance_public'
                self.logger.info("Binance public API initialized (no credentials provided)")
            except Exception as e:
                self.logger.error(f"Failed to initialize Binance public API: {e}")
    
    def get_exchange(self, exchange_name: str = None):
        """Get exchange instance"""
        if exchange_name and exchange_name in self.exchanges:
            return self.exchanges[exchange_name]
        elif self.active_exchange:
            return self.exchanges[self.active_exchange]
        else:
            return None
    
    def get_balance(self, exchange_name: str = None) -> Dict:
        """Get account balance"""
        # Use custom Binance client if available
        if self.active_exchange == 'binance_custom' and self.binance_client:
            try:
                return self.binance_client.get_balance()
            except Exception as e:
                self.logger.error(f"Failed to fetch balance from custom client: {e}")
        
        # Fallback to CCXT
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return {}
        
        # Check if we're using public API (paper trading mode)
        if self.active_exchange and 'public' in self.active_exchange:
            # Return simulated balance for paper trading
            simulated_balance = {
                'free': {'USDT': 1000.0, 'BTC': 0.0, 'ETH': 0.0},
                'used': {'USDT': 0.0, 'BTC': 0.0, 'ETH': 0.0},
                'total': {'USDT': 1000.0, 'BTC': 0.0, 'ETH': 0.0}
            }
            return simulated_balance
        
        try:
            balance = exchange.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"Failed to fetch balance: {e}")
            # Fall back to simulated balance if real balance fails
            return {
                'free': {'USDT': 1000.0, 'BTC': 0.0, 'ETH': 0.0},
                'used': {'USDT': 0.0, 'BTC': 0.0, 'ETH': 0.0},
                'total': {'USDT': 1000.0, 'BTC': 0.0, 'ETH': 0.0}
            }
    
    def get_ticker(self, symbol: str, exchange_name: str = None) -> Dict:
        """Get ticker information"""
        # Use custom Binance client if available
        if self.active_exchange == 'binance_custom' and self.binance_client:
            try:
                price_data = self.binance_client.get_ticker_price(symbol.replace('/', ''))
                stats_24hr = self.binance_client.get_ticker_24hr(symbol.replace('/', ''))
                
                # Convert to CCXT format
                return {
                    'symbol': symbol,
                    'last': float(price_data['price']),
                    'bid': None,
                    'ask': None,
                    'high': float(stats_24hr['highPrice']),
                    'low': float(stats_24hr['lowPrice']),
                    'open': float(stats_24hr['openPrice']),
                    'close': float(price_data['price']),
                    'change': float(stats_24hr['priceChange']),
                    'percentage': float(stats_24hr['priceChangePercent']),
                    'volume': float(stats_24hr['volume']),
                    'timestamp': int(time.time() * 1000)
                }
            except Exception as e:
                self.logger.error(f"Failed to fetch ticker from custom client for {symbol}: {e}")
        
        # Fallback to CCXT
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return {}
        
        try:
            ticker = exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            return {}
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500, exchange_name: str = None) -> pd.DataFrame:
        """Get OHLCV data"""
        # Use custom Binance client if available
        if self.active_exchange == 'binance_custom' and self.binance_client:
            try:
                return self.binance_client.get_ohlcv_dataframe(symbol.replace('/', ''), timeframe, limit)
            except Exception as e:
                self.logger.error(f"Failed to fetch OHLCV from custom client for {symbol}: {e}")
        
        # Fallback to CCXT
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return pd.DataFrame()
        
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            return pd.DataFrame()

class RiskManager:
    """Risk management system"""
    
    def __init__(self, logger):
        self.logger = logger
        self.max_risk_per_trade = float(os.getenv('RISK_PERCENTAGE', 2)) / 100
        self.max_daily_trades = 10
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
    
    def reset_daily_counters(self):
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_trade_count = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
            self.logger.info("Daily risk counters reset")
    
    def can_trade(self, balance: float) -> bool:
        """Check if trading is allowed based on risk rules"""
        self.reset_daily_counters()
        
        # Check daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            self.logger.warning("Daily trade limit reached")
            return False
        
        # Check if we have sufficient balance
        if balance < 10:  # Minimum balance threshold
            self.logger.warning("Insufficient balance for trading")
            return False
        
        return True
    
    def calculate_position_size(self, balance: float, price: float, confidence: float) -> float:
        """Calculate position size based on risk management"""
        # Base position size
        base_amount = balance * self.max_risk_per_trade
        
        # Adjust based on confidence
        confidence_multiplier = min(confidence / 100, 1.0)
        adjusted_amount = base_amount * confidence_multiplier
        
        # Calculate quantity
        quantity = adjusted_amount / price
        
        return max(quantity, 0.001)  # Minimum order size

class AITradingBot:
    """Main AI Trading Bot class - Simplified Version"""
    
    def __init__(self):
        # Initialize components
        self.logger = TradingLogger()
        self.notification_manager = NotificationManager(self.logger)
        self.ai_predictor = AIPredictor(self.logger)
        self.exchange_manager = ExchangeManager(self.logger)
        self.risk_manager = RiskManager(self.logger)
        
        # Configuration
        self.trading_pairs = ['BTC/USDT', 'ETH/USDT']
        self.timeframe = '1h'
        self.prediction_threshold = float(os.getenv('PREDICTION_CONFIDENCE_THRESHOLD', 0.7))
        self.is_running = False
        
        # Trading state
        self.positions = {}
        self.last_signals = {}
        
        self.logger.info("AI Trading Bot (Simplified) initialized successfully")
    
    async def initialize(self):
        """Initialize the bot and train models"""
        self.logger.info("Initializing AI Trading Bot...")
        
        # Train models with historical data
        for symbol in self.trading_pairs:
            try:
                df = self.exchange_manager.get_ohlcv(symbol, self.timeframe, limit=1000)
                if not df.empty:
                    self.ai_predictor.train_models(df)
                    break  # Train on first available symbol
            except Exception as e:
                self.logger.error(f"Failed to get data for {symbol}: {e}")
        
        self.logger.info("Bot initialization completed")
    
    async def analyze_market(self, symbol: str) -> Dict:
        """Analyze market for a specific symbol"""
        try:
            # Get market data
            df = self.exchange_manager.get_ohlcv(symbol, self.timeframe, limit=200)
            if df.empty:
                return {'signal': 'hold', 'confidence': 0}
            
            # Get AI prediction
            prediction, confidence = self.ai_predictor.predict(df)
            
            # Determine signal
            if prediction > 0.5 + (self.prediction_threshold - 0.5):
                signal = 'buy'
            elif prediction < 0.5 - (self.prediction_threshold - 0.5):
                signal = 'sell'
            else:
                signal = 'hold'
            
            # Get current price
            ticker = self.exchange_manager.get_ticker(symbol)
            current_price = ticker.get('last', 0) if ticker else 0
            
            return {
                'signal': signal,
                'confidence': confidence,
                'prediction': prediction,
                'current_price': current_price,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Market analysis failed for {symbol}: {e}")
            return {'signal': 'hold', 'confidence': 0}
    
    async def trading_loop(self):
        """Main trading loop"""
        self.logger.info("Starting trading loop...")
        
        while self.is_running:
            try:
                for symbol in self.trading_pairs:
                    # Analyze market
                    analysis = await self.analyze_market(symbol)
                    signal = analysis['signal']
                    confidence = analysis['confidence']
                    
                    self.logger.info(f"{symbol}: {signal.upper()} (Confidence: {confidence:.1f}%)")
                    
                    # Store last signal
                    self.last_signals[symbol] = analysis
                    
                    # Simulate trade notification for high confidence signals
                    if signal != 'hold' and confidence > 60:
                        trade_data = {
                            'symbol': symbol,
                            'action': signal,
                            'amount': 0.001,  # Simulated amount
                            'price': analysis['current_price'],
                            'timestamp': datetime.now().isoformat(),
                            'confidence': confidence
                        }
                        
                        self.logger.trade(f"SIMULATED {signal.upper()} {symbol} at ${analysis['current_price']:.4f}")
                        await self.notification_manager.notify_trade(trade_data)
                    
                    # Small delay between symbols
                    await asyncio.sleep(1)
                
                # Wait before next iteration
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def start(self):
        """Start the trading bot"""
        self.is_running = True
        self.logger.info("AI Trading Bot started")
        
        # Run the bot
        asyncio.run(self.run())
    
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        self.logger.info("AI Trading Bot stopped")
    
    async def run(self):
        """Main run method"""
        await self.initialize()
        await self.trading_loop()
    
    def get_status(self) -> Dict:
        """Get bot status for dashboard"""
        balance = self.exchange_manager.get_balance()
        
        return {
            'is_running': self.is_running,
            'balance': balance,
            'positions': self.positions,
            'last_signals': self.last_signals,
            'daily_trades': self.risk_manager.daily_trade_count,
            'daily_pnl': self.risk_manager.daily_pnl,
            'last_update': datetime.now().isoformat()
        }

def main():
    """Main function"""
    print("🤖 AI Crypto Trading Bot (Simplified)")
    print("=" * 50)
    
    # Create bot instance
    bot = AITradingBot()
    
    try:
        # Start the bot
        bot.start()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping bot...")
        bot.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        bot.logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main() 