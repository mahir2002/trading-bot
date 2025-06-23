#!/usr/bin/env python3
"""
Live Optimized AI Trading Bot - High Return Version
Ready for live trading with real API keys
"""

import os
import sys
import pandas as pd
import numpy as np
import ccxt
import ta
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from dotenv import load_dotenv

load_dotenv()

class LiveOptimizedBot:
    """Live optimized trading bot for maximum returns"""
    
    def __init__(self):
        # Setup logging
        self.setup_logging()
        
        # Trading parameters (optimized for higher returns)
        self.confidence_threshold = 55  # Lower threshold for more trades
        self.max_position_size = 0.25   # 25% max position size
        self.stop_loss = 0.08           # 8% stop loss
        self.take_profit = 0.15         # 15% take profit
        self.daily_loss_limit = 0.10    # 10% daily loss limit
        
        # Trading pairs (high volume, good for AI)
        self.trading_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        self.timeframe = '1h'
        
        # Initialize exchange
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'sandbox': False,  # Set to True for testnet
            'enableRateLimit': True,
        })
        
        # Trading state
        self.positions = {}
        self.daily_pnl = 0.0
        self.trade_history = []
        self.models = {}
        self.scalers = {}
        self.feature_cols = {}
        
        # Performance tracking
        self.start_balance = 0
        self.current_balance = 0
        
        self.logger.info("🚀 Live Optimized Trading Bot initialized")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        self.logger = logging.getLogger('LiveOptimizedBot')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(f'logs/live_optimized_bot_{datetime.now().strftime("%Y%m%d")}.log')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def get_market_data(self, symbol: str, limit: int = 1000) -> pd.DataFrame:
        """Fetch real market data from exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch data for {symbol}: {e}")
            return pd.DataFrame()
    
    def create_optimized_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create optimized features for predictions"""
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = ta.trend.sma_indicator(df['close'], window=window)
            df[f'ema_{window}'] = ta.trend.ema_indicator(df['close'], window=window)
            df[f'price_above_sma_{window}'] = (df['close'] > df[f'sma_{window}']).astype(int)
        
        # Momentum indicators
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['rsi_signal'] = np.where(df['rsi'] < 30, 1, np.where(df['rsi'] > 70, -1, 0))
        
        # MACD
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['macd_signal'] = ta.trend.macd_signal(df['close'])
        df['macd_bullish'] = (df['macd'] > df['macd_signal']).astype(int)
        
        # Bollinger Bands
        df['bb_upper'] = ta.volatility.bollinger_hband(df['close'])
        df['bb_lower'] = ta.volatility.bollinger_lband(df['close'])
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_squeeze'] = ((df['bb_upper'] - df['bb_lower']) / df['close'] < 0.1).astype(int)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['high_volume'] = (df['volume_ratio'] > 1.5).astype(int)
        
        # Price patterns
        df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['high_volatility'] = (df['volatility'] > df['volatility'].rolling(50).mean()).astype(int)
        
        # Momentum features
        for period in [3, 5, 10]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'momentum_{period}_signal'] = np.where(df[f'momentum_{period}'] > 0.02, 1, 
                                                      np.where(df[f'momentum_{period}'] < -0.02, -1, 0))
        
        # Support/Resistance
        df['resistance'] = df['high'].rolling(window=20).max()
        df['support'] = df['low'].rolling(window=20).min()
        df['near_resistance'] = (df['close'] >= df['resistance'] * 0.99).astype(int)
        df['near_support'] = (df['close'] <= df['support'] * 1.01).astype(int)
        
        # Create target for training
        future_returns = df['close'].shift(-1) / df['close'] - 1
        df['target'] = np.where(future_returns > 0.015, 2,  # Strong buy
                               np.where(future_returns > 0.005, 1,  # Buy
                               np.where(future_returns < -0.015, -2,  # Strong sell
                               np.where(future_returns < -0.005, -1, 0))))  # Sell, Hold
        
        return df
    
    def train_model_for_symbol(self, symbol: str) -> bool:
        """Train optimized model for specific symbol"""
        try:
            self.logger.info(f"Training model for {symbol}...")
            
            # Get historical data
            df = self.get_market_data(symbol, limit=2000)
            if df.empty:
                self.logger.error(f"No data available for {symbol}")
                return False
            
            # Create features
            df_features = self.create_optimized_features(df.copy())
            df_features = df_features.dropna()
            
            if len(df_features) < 200:
                self.logger.error(f"Insufficient data for {symbol}")
                return False
            
            # Select features
            feature_cols = [col for col in df_features.columns 
                           if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'target']
                           and not df_features[col].isna().all()]
            
            X = df_features[feature_cols].values
            y = df_features['target'].values
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train ensemble models
            rf_model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42)
            gb_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.15, random_state=42)
            
            rf_model.fit(X_train_scaled, y_train)
            gb_model.fit(X_train_scaled, y_train)
            
            # Calculate accuracies
            rf_acc = accuracy_score(y_test, rf_model.predict(X_test_scaled))
            gb_acc = accuracy_score(y_test, gb_model.predict(X_test_scaled))
            
            self.logger.info(f"{symbol} - RF Accuracy: {rf_acc:.3f}, GB Accuracy: {gb_acc:.3f}")
            
            # Store models
            self.models[symbol] = {'rf': rf_model, 'gb': gb_model}
            self.scalers[symbol] = scaler
            self.feature_cols[symbol] = feature_cols
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to train model for {symbol}: {e}")
            return False
    
    def get_prediction(self, symbol: str) -> Tuple[int, float]:
        """Get prediction for symbol"""
        try:
            if symbol not in self.models:
                return 0, 0  # Hold, no confidence
            
            # Get current data
            df = self.get_market_data(symbol, limit=200)
            if df.empty:
                return 0, 0
            
            # Create features
            df_features = self.create_optimized_features(df.copy())
            df_features = df_features.dropna()
            
            if len(df_features) == 0:
                return 0, 0
            
            # Get latest features
            latest_features = df_features[self.feature_cols[symbol]].iloc[-1:].values
            latest_features_scaled = self.scalers[symbol].transform(latest_features)
            
            # Get predictions
            rf_pred = self.models[symbol]['rf'].predict(latest_features_scaled)[0]
            gb_pred = self.models[symbol]['gb'].predict(latest_features_scaled)[0]
            
            rf_proba = self.models[symbol]['rf'].predict_proba(latest_features_scaled)[0]
            gb_proba = self.models[symbol]['gb'].predict_proba(latest_features_scaled)[0]
            
            # Ensemble prediction
            ensemble_pred = int(np.round((rf_pred + gb_pred) / 2))
            
            # Calculate confidence
            rf_conf = max(rf_proba)
            gb_conf = max(gb_proba)
            ensemble_conf = (rf_conf + gb_conf) / 2 * 100
            
            return ensemble_pred, ensemble_conf
            
        except Exception as e:
            self.logger.error(f"Prediction failed for {symbol}: {e}")
            return 0, 0
    
    def get_account_balance(self) -> float:
        """Get current account balance"""
        try:
            balance = self.exchange.fetch_balance()
            usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
            return float(usdt_balance)
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            return 0
    
    def calculate_position_size(self, signal: int, confidence: float, balance: float, price: float) -> float:
        """Calculate optimal position size"""
        
        # Base size from confidence
        base_size = min(confidence / 100 * self.max_position_size, self.max_position_size)
        
        # Adjust for signal strength
        if abs(signal) == 2:  # Strong signals
            base_size *= 1.2
        
        # Calculate trade value
        trade_value = balance * base_size
        
        # Convert to quantity
        quantity = trade_value / price
        
        return quantity
    
    def execute_trade(self, symbol: str, side: str, quantity: float, signal: int, confidence: float) -> bool:
        """Execute trade on exchange"""
        try:
            # Get current price
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Check minimum order size
            market = self.exchange.market(symbol)
            min_amount = market['limits']['amount']['min']
            
            if quantity < min_amount:
                self.logger.warning(f"Order size {quantity} below minimum {min_amount} for {symbol}")
                return False
            
            # Execute order
            order = self.exchange.create_market_order(symbol, side, quantity)
            
            # Log trade
            trade = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': current_price,
                'signal': signal,
                'confidence': confidence,
                'order_id': order['id']
            }
            
            self.trade_history.append(trade)
            
            self.logger.info(f"✅ Executed {side} {quantity:.6f} {symbol} @ ${current_price:.2f} "
                           f"(Signal: {signal}, Confidence: {confidence:.1f}%)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute trade for {symbol}: {e}")
            return False
    
    def check_risk_limits(self) -> bool:
        """Check if risk limits are exceeded"""
        
        # Check daily loss limit
        if self.daily_pnl < -self.daily_loss_limit * self.start_balance:
            self.logger.warning("Daily loss limit exceeded!")
            return False
        
        return True
    
    def analyze_and_trade(self, symbol: str):
        """Analyze symbol and execute trades if conditions are met"""
        try:
            # Get prediction
            signal, confidence = self.get_prediction(symbol)
            
            # Get current balance
            balance = self.get_account_balance()
            
            # Get current price
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Log analysis
            signal_names = {-2: 'Strong Sell', -1: 'Sell', 0: 'Hold', 1: 'Buy', 2: 'Strong Buy'}
            self.logger.info(f"{symbol}: {signal_names.get(signal, 'Unknown')} "
                           f"(Confidence: {confidence:.1f}%, Price: ${current_price:.2f})")
            
            # Check if we should trade
            if confidence > self.confidence_threshold and self.check_risk_limits():
                
                # Get current position
                positions = self.exchange.fetch_positions([symbol])
                current_position = 0
                for pos in positions:
                    if pos['symbol'] == symbol:
                        current_position = float(pos['size'])
                        break
                
                # Trading logic
                if signal >= 1 and balance > 50:  # Buy signals
                    quantity = self.calculate_position_size(signal, confidence, balance, current_price)
                    if quantity > 0:
                        self.execute_trade(symbol, 'buy', quantity, signal, confidence)
                
                elif signal <= -1 and current_position > 0:  # Sell signals
                    # Sell portion of position based on confidence
                    sell_ratio = min(confidence / 100, 0.8)  # Max 80% of position
                    quantity = current_position * sell_ratio
                    if quantity > 0:
                        self.execute_trade(symbol, 'sell', quantity, signal, confidence)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
    
    async def run_trading_loop(self):
        """Main trading loop"""
        self.logger.info("🚀 Starting live optimized trading loop...")
        
        # Initialize
        self.start_balance = self.get_account_balance()
        self.current_balance = self.start_balance
        
        self.logger.info(f"💰 Starting balance: ${self.start_balance:.2f}")
        
        # Train models for all symbols
        for symbol in self.trading_pairs:
            success = self.train_model_for_symbol(symbol)
            if not success:
                self.logger.warning(f"Failed to train model for {symbol}, removing from trading pairs")
                self.trading_pairs.remove(symbol)
        
        if not self.trading_pairs:
            self.logger.error("No trading pairs available!")
            return
        
        self.logger.info(f"✅ Models trained for {len(self.trading_pairs)} pairs: {self.trading_pairs}")
        
        # Main trading loop
        while True:
            try:
                # Update current balance
                self.current_balance = self.get_account_balance()
                
                # Calculate daily P&L
                self.daily_pnl = self.current_balance - self.start_balance
                
                # Log status
                pnl_pct = (self.daily_pnl / self.start_balance) * 100 if self.start_balance > 0 else 0
                self.logger.info(f"💼 Balance: ${self.current_balance:.2f} | "
                               f"P&L: ${self.daily_pnl:.2f} ({pnl_pct:+.2f}%) | "
                               f"Trades: {len(self.trade_history)}")
                
                # Analyze each trading pair
                for symbol in self.trading_pairs:
                    self.analyze_and_trade(symbol)
                    await asyncio.sleep(2)  # Rate limiting
                
                # Wait before next iteration (5 minutes)
                self.logger.info("⏰ Waiting 5 minutes before next analysis...")
                await asyncio.sleep(300)
                
            except KeyboardInterrupt:
                self.logger.info("👋 Trading stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        current_balance = self.get_account_balance()
        total_return = ((current_balance - self.start_balance) / self.start_balance) * 100 if self.start_balance > 0 else 0
        
        # Trade statistics
        total_trades = len(self.trade_history)
        buy_trades = len([t for t in self.trade_history if t['side'] == 'buy'])
        sell_trades = len([t for t in self.trade_history if t['side'] == 'sell'])
        
        avg_confidence = np.mean([t['confidence'] for t in self.trade_history]) if self.trade_history else 0
        
        return {
            'start_balance': self.start_balance,
            'current_balance': current_balance,
            'total_return': total_return,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'avg_confidence': avg_confidence,
            'trading_pairs': self.trading_pairs
        }

def main():
    """Main function"""
    print("🚀 Live Optimized AI Trading Bot")
    print("=" * 50)
    print("⚠️  WARNING: This bot trades with real money!")
    print("💡 Make sure you have:")
    print("   - Valid API keys in .env file")
    print("   - Sufficient balance")
    print("   - Risk management settings")
    print("=" * 50)
    
    # Confirm before starting
    confirm = input("Type 'START' to begin live trading: ")
    if confirm != 'START':
        print("❌ Trading cancelled")
        return
    
    # Initialize and run bot
    bot = LiveOptimizedBot()
    
    try:
        # Test API connection
        balance = bot.get_account_balance()
        print(f"✅ API connected. Balance: ${balance:.2f}")
        
        if balance < 100:
            print("⚠️  Warning: Low balance. Consider adding more funds.")
        
        # Run trading loop
        asyncio.run(bot.run_trading_loop())
        
    except KeyboardInterrupt:
        print("\n👋 Trading stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Show final summary
        summary = bot.get_performance_summary()
        print("\n📊 FINAL PERFORMANCE SUMMARY")
        print("=" * 40)
        for key, value in summary.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main() 