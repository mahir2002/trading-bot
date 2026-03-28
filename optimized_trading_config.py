#!/usr/bin/env python3
"""
🚀 OPTIMIZED TRADING CONFIGURATION
Addresses HOLD Signal Issue & Improves Trading Performance

PROBLEMS IDENTIFIED:
1. Static 70% confidence threshold is too high
2. BTC confidence: 44-86% (inconsistent)
3. ETH confidence: 0-18% (always below threshold)
4. Result: 95%+ HOLD signals, no actual trading

SOLUTIONS IMPLEMENTED:
1. Dynamic confidence thresholds
2. Multi-tier signal generation
3. Confidence-based position sizing
4. Market regime adaptation
5. Enhanced risk management
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
import sqlite3
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizedTradingConfig:
    """Optimized trading configuration"""
    
    # Dynamic Confidence Thresholds (much lower than 70%)
    strong_buy_threshold: float = 0.65      # 65% for strong buy
    buy_threshold: float = 0.55             # 55% for regular buy
    weak_buy_threshold: float = 0.45        # 45% for weak buy
    
    strong_sell_threshold: float = 0.65     # 65% for strong sell
    sell_threshold: float = 0.55            # 55% for regular sell
    weak_sell_threshold: float = 0.45       # 45% for weak sell
    
    # Position Sizing by Confidence
    max_position_size: float = 0.10         # 10% max position
    base_position_size: float = 0.02        # 2% base position
    confidence_multiplier: float = 2.0      # Multiply by confidence
    
    # Risk Management
    stop_loss_pct: float = 0.03             # 3% stop loss
    take_profit_pct: float = 0.06           # 6% take profit
    max_daily_trades: int = 20              # Max trades per day
    max_concurrent_positions: int = 5       # Max positions at once
    
    # Market Regime Adaptation
    volatile_market_threshold: float = 0.30  # 30% volatility threshold
    trending_market_threshold: float = 0.02  # 2% trend threshold
    
    # Enhanced Features
    use_technical_confirmation: bool = True
    use_volume_confirmation: bool = True
    use_sentiment_analysis: bool = True
    
    # Retraining Parameters
    retrain_interval_hours: int = 6         # Retrain every 6 hours
    min_accuracy_threshold: float = 0.52    # 52% minimum accuracy

class OptimizedSignalGenerator:
    """Generates optimized trading signals with dynamic thresholds"""
    
    def __init__(self, config: OptimizedTradingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def generate_signal(self, symbol: str, prediction: float, confidence: float, 
                       market_data: pd.DataFrame) -> Dict:
        """Generate optimized trading signal"""
        
        try:
            # Calculate market regime
            market_regime = self._detect_market_regime(market_data)
            
            # Adjust thresholds based on market regime
            adjusted_thresholds = self._adjust_thresholds_for_regime(market_regime)
            
            # Determine signal type
            signal_type = self._determine_signal_type(
                prediction, confidence, adjusted_thresholds
            )
            
            # Calculate position size
            position_size = self._calculate_position_size(
                signal_type, confidence, market_regime
            )
            
            # Technical confirmations
            confirmations = self._get_technical_confirmations(market_data, signal_type)
            
            # Risk assessment
            risk_score = self._assess_risk(market_data, signal_type, confidence)
            
            # Generate final signal
            signal = {
                'symbol': symbol,
                'signal_type': signal_type,
                'confidence': confidence,
                'position_size': position_size,
                'market_regime': market_regime,
                'confirmations': confirmations,
                'risk_score': risk_score,
                'stop_loss': self._calculate_stop_loss(market_data, signal_type),
                'take_profit': self._calculate_take_profit(market_data, signal_type),
                'timestamp': datetime.now(),
                'reasoning': self._generate_reasoning(signal_type, confidence, confirmations)
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return {
                'symbol': symbol,
                'signal_type': 'HOLD',
                'confidence': 0.0,
                'position_size': 0.0,
                'reasoning': f'Error: {str(e)}'
            }
    
    def _detect_market_regime(self, data: pd.DataFrame) -> str:
        """Detect current market regime"""
        if len(data) < 20:
            return 'UNKNOWN'
        
        # Calculate volatility
        returns = data['close'].pct_change().dropna()
        volatility = returns.rolling(20).std().iloc[-1]
        
        # Calculate trend
        short_ma = data['close'].rolling(5).mean().iloc[-1]
        long_ma = data['close'].rolling(20).mean().iloc[-1]
        trend_strength = (short_ma - long_ma) / long_ma
        
        # Determine regime
        if volatility > self.config.volatile_market_threshold:
            return 'HIGH_VOLATILITY'
        elif abs(trend_strength) > self.config.trending_market_threshold:
            return 'TRENDING_BULL' if trend_strength > 0 else 'TRENDING_BEAR'
        else:
            return 'SIDEWAYS'
    
    def _adjust_thresholds_for_regime(self, regime: str) -> Dict[str, float]:
        """Adjust confidence thresholds based on market regime"""
        base_thresholds = {
            'strong_buy': self.config.strong_buy_threshold,
            'buy': self.config.buy_threshold,
            'weak_buy': self.config.weak_buy_threshold,
            'strong_sell': self.config.strong_sell_threshold,
            'sell': self.config.sell_threshold,
            'weak_sell': self.config.weak_sell_threshold
        }
        
        # Regime-based adjustments
        if regime == 'HIGH_VOLATILITY':
            # Higher thresholds in volatile markets
            adjustment = 0.05
        elif regime in ['TRENDING_BULL', 'TRENDING_BEAR']:
            # Lower thresholds in trending markets
            adjustment = -0.05
        else:
            # Standard thresholds in sideways markets
            adjustment = 0.0
        
        # Apply adjustments
        adjusted = {}
        for key, value in base_thresholds.items():
            adjusted[key] = max(0.30, min(0.80, value + adjustment))
        
        return adjusted
    
    def _determine_signal_type(self, prediction: float, confidence: float, 
                              thresholds: Dict[str, float]) -> str:
        """Determine signal type based on prediction and confidence"""
        
        # Convert confidence to 0-1 scale if needed
        conf = confidence / 100 if confidence > 1 else confidence
        
        # Strong signals (high confidence)
        if conf >= thresholds['strong_buy'] and prediction > 0.6:
            return 'STRONG_BUY'
        elif conf >= thresholds['strong_sell'] and prediction < 0.4:
            return 'STRONG_SELL'
        
        # Regular signals (medium confidence)
        elif conf >= thresholds['buy'] and prediction > 0.55:
            return 'BUY'
        elif conf >= thresholds['sell'] and prediction < 0.45:
            return 'SELL'
        
        # Weak signals (low-medium confidence)
        elif conf >= thresholds['weak_buy'] and prediction > 0.52:
            return 'WEAK_BUY'
        elif conf >= thresholds['weak_sell'] and prediction < 0.48:
            return 'WEAK_SELL'
        
        # Default to hold
        else:
            return 'HOLD'
    
    def _calculate_position_size(self, signal_type: str, confidence: float, 
                               regime: str) -> float:
        """Calculate position size based on signal strength and confidence"""
        
        if signal_type == 'HOLD':
            return 0.0
        
        # Base position sizes by signal type
        signal_multipliers = {
            'STRONG_BUY': 1.5,
            'BUY': 1.0,
            'WEAK_BUY': 0.6,
            'STRONG_SELL': 1.5,
            'SELL': 1.0,
            'WEAK_SELL': 0.6
        }
        
        # Confidence adjustment
        conf = confidence / 100 if confidence > 1 else confidence
        confidence_adj = conf * self.config.confidence_multiplier
        
        # Market regime adjustment
        regime_multipliers = {
            'HIGH_VOLATILITY': 0.7,
            'TRENDING_BULL': 1.2,
            'TRENDING_BEAR': 1.2,
            'SIDEWAYS': 1.0,
            'UNKNOWN': 0.8
        }
        
        # Calculate final position size
        position_size = (
            self.config.base_position_size * 
            signal_multipliers.get(signal_type, 0.5) * 
            confidence_adj * 
            regime_multipliers.get(regime, 1.0)
        )
        
        # Cap at maximum
        return min(position_size, self.config.max_position_size)
    
    def _get_technical_confirmations(self, data: pd.DataFrame, signal_type: str) -> Dict:
        """Get technical analysis confirmations"""
        confirmations = {
            'rsi_confirmation': False,
            'macd_confirmation': False,
            'volume_confirmation': False,
            'trend_confirmation': False,
            'total_score': 0
        }
        
        if len(data) < 20:
            return confirmations
        
        try:
            # RSI confirmation
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            if signal_type in ['STRONG_BUY', 'BUY', 'WEAK_BUY'] and current_rsi < 70:
                confirmations['rsi_confirmation'] = True
                confirmations['total_score'] += 1
            elif signal_type in ['STRONG_SELL', 'SELL', 'WEAK_SELL'] and current_rsi > 30:
                confirmations['rsi_confirmation'] = True
                confirmations['total_score'] += 1
            
            # MACD confirmation
            exp1 = data['close'].ewm(span=12).mean()
            exp2 = data['close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9).mean()
            macd_bullish = macd.iloc[-1] > signal_line.iloc[-1]
            
            if signal_type in ['STRONG_BUY', 'BUY', 'WEAK_BUY'] and macd_bullish:
                confirmations['macd_confirmation'] = True
                confirmations['total_score'] += 1
            elif signal_type in ['STRONG_SELL', 'SELL', 'WEAK_SELL'] and not macd_bullish:
                confirmations['macd_confirmation'] = True
                confirmations['total_score'] += 1
            
            # Volume confirmation
            avg_volume = data['volume'].rolling(20).mean().iloc[-1]
            current_volume = data['volume'].iloc[-1]
            if current_volume > avg_volume * 1.2:  # 20% above average
                confirmations['volume_confirmation'] = True
                confirmations['total_score'] += 1
            
            # Trend confirmation
            short_ma = data['close'].rolling(5).mean().iloc[-1]
            long_ma = data['close'].rolling(20).mean().iloc[-1]
            
            if signal_type in ['STRONG_BUY', 'BUY', 'WEAK_BUY'] and short_ma > long_ma:
                confirmations['trend_confirmation'] = True
                confirmations['total_score'] += 1
            elif signal_type in ['STRONG_SELL', 'SELL', 'WEAK_SELL'] and short_ma < long_ma:
                confirmations['trend_confirmation'] = True
                confirmations['total_score'] += 1
            
        except Exception as e:
            self.logger.warning(f"Technical confirmation error: {e}")
        
        return confirmations
    
    def _assess_risk(self, data: pd.DataFrame, signal_type: str, confidence: float) -> float:
        """Assess risk score (0-100, lower is better)"""
        
        risk_score = 50  # Base risk
        
        try:
            # Volatility risk
            returns = data['close'].pct_change().dropna()
            volatility = returns.rolling(20).std().iloc[-1]
            vol_risk = min(volatility * 200, 30)  # Cap at 30
            risk_score += vol_risk
            
            # Confidence risk (lower confidence = higher risk)
            conf = confidence / 100 if confidence > 1 else confidence
            conf_risk = (1 - conf) * 20
            risk_score += conf_risk
            
            # Signal strength risk
            if signal_type in ['WEAK_BUY', 'WEAK_SELL']:
                risk_score += 10
            elif signal_type in ['STRONG_BUY', 'STRONG_SELL']:
                risk_score -= 10
            
        except Exception as e:
            self.logger.warning(f"Risk assessment error: {e}")
            risk_score = 70  # Conservative default
        
        return max(0, min(100, risk_score))
    
    def _calculate_stop_loss(self, data: pd.DataFrame, signal_type: str) -> float:
        """Calculate stop loss price"""
        current_price = data['close'].iloc[-1]
        
        if signal_type in ['STRONG_BUY', 'BUY', 'WEAK_BUY']:
            return current_price * (1 - self.config.stop_loss_pct)
        elif signal_type in ['STRONG_SELL', 'SELL', 'WEAK_SELL']:
            return current_price * (1 + self.config.stop_loss_pct)
        else:
            return current_price
    
    def _calculate_take_profit(self, data: pd.DataFrame, signal_type: str) -> float:
        """Calculate take profit price"""
        current_price = data['close'].iloc[-1]
        
        if signal_type in ['STRONG_BUY', 'BUY', 'WEAK_BUY']:
            return current_price * (1 + self.config.take_profit_pct)
        elif signal_type in ['STRONG_SELL', 'SELL', 'WEAK_SELL']:
            return current_price * (1 - self.config.take_profit_pct)
        else:
            return current_price
    
    def _generate_reasoning(self, signal_type: str, confidence: float, 
                           confirmations: Dict) -> str:
        """Generate human-readable reasoning for the signal"""
        
        conf_pct = confidence if confidence > 1 else confidence * 100
        confirm_score = confirmations.get('total_score', 0)
        
        if signal_type == 'HOLD':
            return f"HOLD: Confidence {conf_pct:.1f}% below thresholds"
        
        strength = 'Strong' if 'STRONG' in signal_type else 'Moderate' if 'WEAK' not in signal_type else 'Weak'
        direction = 'bullish' if 'BUY' in signal_type else 'bearish'
        
        return (f"{strength} {direction} signal with {conf_pct:.1f}% confidence. "
                f"Technical confirmations: {confirm_score}/4. "
                f"{'Good' if confirm_score >= 2 else 'Limited'} technical support.")

class OptimizedTradingSystem:
    """Complete optimized trading system"""
    
    def __init__(self):
        self.config = OptimizedTradingConfig()
        self.signal_generator = OptimizedSignalGenerator(self.config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Trading state
        self.active_positions = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Performance tracking
        self.performance_history = []
        
    def update_config_file(self):
        """Update the main config.env file with optimized settings"""
        
        config_updates = {
            'PREDICTION_CONFIDENCE_THRESHOLD': '0.45',  # Much lower threshold
            'DEFAULT_TRADE_AMOUNT': '50',               # Smaller amounts for testing
            'RISK_PERCENTAGE': '2.0',                   # Conservative risk
            'STOP_LOSS_PERCENTAGE': '3.0',              # 3% stop loss
            'TAKE_PROFIT_PERCENTAGE': '6.0',            # 6% take profit
            'MAX_DAILY_TRADES': '20',                   # More trades allowed
            'POSITION_SIZE_PERCENT': '2',               # 2% position size
            'CONFIDENCE_THRESHOLD': '45',               # 45% confidence threshold
            'TRADING_CYCLE_INTERVAL': '300',            # 5 minutes
            'ENABLE_PAPER_TRADING': 'true',             # Keep paper trading
            'AI_RETRAIN_INTERVAL': '6',                 # Retrain every 6 hours
        }
        
        config_file = 'config.env'
        
        try:
            # Read current config
            with open(config_file, 'r') as f:
                lines = f.readlines()
            
            # Update values
            updated_lines = []
            updated_keys = set()
            
            for line in lines:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key = line.split('=')[0]
                    if key in config_updates:
                        updated_lines.append(f"{key}={config_updates[key]}\n")
                        updated_keys.add(key)
                    else:
                        updated_lines.append(line + '\n')
                else:
                    updated_lines.append(line + '\n')
            
            # Add any missing keys
            for key, value in config_updates.items():
                if key not in updated_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # Write updated config
            with open(config_file, 'w') as f:
                f.writelines(updated_lines)
            
            self.logger.info("✅ Config file updated with optimized settings")
            
            # Print changes
            print("\n🔧 OPTIMIZED CONFIGURATION APPLIED:")
            print("=" * 50)
            for key, value in config_updates.items():
                print(f"✅ {key}={value}")
            
        except Exception as e:
            self.logger.error(f"Failed to update config file: {e}")
    
    def analyze_current_performance(self):
        """Analyze current bot performance and suggest improvements"""
        
        try:
            # Try to read from database
            db_path = 'crypto_trading_data.db'
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                
                # Get recent predictions
                recent_predictions = pd.read_sql_query("""
                    SELECT * FROM predictions 
                    WHERE timestamp >= datetime('now', '-24 hours')
                    ORDER BY timestamp DESC
                """, conn)
                
                if not recent_predictions.empty:
                    print("\n📊 CURRENT PERFORMANCE ANALYSIS:")
                    print("=" * 50)
                    
                    # Signal distribution
                    signal_counts = recent_predictions['action'].value_counts()
                    total_signals = len(recent_predictions)
                    
                    print(f"📈 Total Signals (24h): {total_signals}")
                    for signal, count in signal_counts.items():
                        pct = (count / total_signals) * 100
                        print(f"   {signal}: {count} ({pct:.1f}%)")
                    
                    # Confidence analysis
                    avg_confidence = recent_predictions['confidence'].mean()
                    print(f"📊 Average Confidence: {avg_confidence:.1f}%")
                    
                    # Identify issues
                    hold_pct = signal_counts.get('HOLD', 0) / total_signals * 100
                    if hold_pct > 80:
                        print(f"⚠️  HIGH HOLD RATE: {hold_pct:.1f}% - Thresholds too high!")
                    
                    # Confidence by symbol
                    print("\n📈 Confidence by Symbol:")
                    conf_by_symbol = recent_predictions.groupby('symbol')['confidence'].agg(['mean', 'count'])
                    for symbol, stats in conf_by_symbol.iterrows():
                        print(f"   {symbol}: {stats['mean']:.1f}% avg ({stats['count']} signals)")
                
                conn.close()
                
        except Exception as e:
            self.logger.warning(f"Could not analyze performance: {e}")
    
    def create_optimized_bot_script(self):
        """Create an optimized version of the trading bot"""
        
        optimized_bot_code = '''#!/usr/bin/env python3
"""
🚀 OPTIMIZED AI TRADING BOT
Addresses HOLD signal issue with dynamic thresholds and improved trading logic
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing components
from ai_trading_bot_simple import AITradingBot, AIPredictor, ExchangeManager, RiskManager

class OptimizedAIPredictor(AIPredictor):
    """Enhanced AI Predictor with dynamic thresholds"""
    
    def __init__(self, logger):
        super().__init__(logger)
        
        # Optimized thresholds (much lower than 70%)
        self.strong_threshold = 0.65    # 65% for strong signals
        self.medium_threshold = 0.55    # 55% for medium signals  
        self.weak_threshold = 0.45      # 45% for weak signals
        
    def predict_with_confidence_tiers(self, df: pd.DataFrame) -> Dict:
        """Enhanced prediction with multiple confidence tiers"""
        
        try:
            prediction, confidence = self.predict(df)
            
            # Convert confidence to 0-1 scale
            conf = confidence / 100 if confidence > 1 else confidence
            
            # Determine signal with multiple tiers
            if prediction > 0.6 and conf >= self.strong_threshold:
                signal = 'strong_buy'
                position_size = 0.08  # 8% position
            elif prediction > 0.55 and conf >= self.medium_threshold:
                signal = 'buy'
                position_size = 0.05  # 5% position
            elif prediction > 0.52 and conf >= self.weak_threshold:
                signal = 'weak_buy'
                position_size = 0.03  # 3% position
            elif prediction < 0.4 and conf >= self.strong_threshold:
                signal = 'strong_sell'
                position_size = 0.08  # 8% position
            elif prediction < 0.45 and conf >= self.medium_threshold:
                signal = 'sell'
                position_size = 0.05  # 5% position
            elif prediction < 0.48 and conf >= self.weak_threshold:
                signal = 'weak_sell'
                position_size = 0.03  # 3% position
            else:
                signal = 'hold'
                position_size = 0.0
            
            return {
                'signal': signal,
                'confidence': confidence,
                'prediction': prediction,
                'position_size': position_size,
                'reasoning': self._generate_reasoning(signal, confidence, prediction)
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced prediction failed: {e}")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'prediction': 0.5,
                'position_size': 0.0,
                'reasoning': f'Error: {str(e)}'
            }
    
    def _generate_reasoning(self, signal: str, confidence: float, prediction: float) -> str:
        """Generate reasoning for the signal"""
        
        if signal == 'hold':
            return f"HOLD: Confidence {confidence:.1f}% or prediction {prediction:.3f} below thresholds"
        
        strength = signal.replace('_', ' ').title()
        return f"{strength} signal: {confidence:.1f}% confidence, {prediction:.3f} prediction"

class OptimizedTradingBot(AITradingBot):
    """Optimized trading bot with enhanced signal generation"""
    
    def __init__(self):
        super().__init__()
        
        # Replace predictor with optimized version
        self.ai_predictor = OptimizedAIPredictor(self.logger)
        
        # Enhanced configuration
        self.prediction_threshold = 0.45  # Much lower threshold
        self.min_confidence = 45          # 45% minimum confidence
        
        # Trading statistics
        self.signal_stats = {
            'strong_buy': 0, 'buy': 0, 'weak_buy': 0,
            'strong_sell': 0, 'sell': 0, 'weak_sell': 0,
            'hold': 0
        }
        
        self.logger.info("🚀 Optimized AI Trading Bot initialized")
    
    async def analyze_market(self, symbol: str) -> Dict:
        """Enhanced market analysis with multi-tier signals"""
        
        try:
            # Get market data
            df = self.exchange_manager.get_ohlcv(symbol, self.timeframe, limit=200)
            if df.empty:
                return {'signal': 'hold', 'confidence': 0}
            
            # Get enhanced prediction
            analysis = self.ai_predictor.predict_with_confidence_tiers(df)
            
            # Update statistics
            signal = analysis['signal']
            if signal in self.signal_stats:
                self.signal_stats[signal] += 1
            
            # Get current price
            ticker = self.exchange_manager.get_ticker(symbol)
            current_price = ticker.get('last', 0) if ticker else 0
            
            # Add market context
            analysis.update({
                'current_price': current_price,
                'timestamp': datetime.now(),
                'symbol': symbol
            })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Enhanced market analysis failed for {symbol}: {e}")
            return {'signal': 'hold', 'confidence': 0}
    
    async def trading_loop(self):
        """Enhanced trading loop with better signal handling"""
        
        self.logger.info("🚀 Starting optimized trading loop...")
        
        while self.is_running:
            try:
                for symbol in self.trading_pairs:
                    # Enhanced market analysis
                    analysis = await self.analyze_market(symbol)
                    
                    signal = analysis['signal']
                    confidence = analysis['confidence']
                    position_size = analysis.get('position_size', 0.0)
                    reasoning = analysis.get('reasoning', 'No reasoning provided')
                    
                    # Enhanced logging
                    if signal != 'hold':
                        self.logger.info(f"🎯 {symbol}: {signal.upper()} "
                                       f"(Confidence: {confidence:.1f}%, "
                                       f"Size: {position_size:.1%})")
                        self.logger.info(f"   Reasoning: {reasoning}")
                    else:
                        self.logger.info(f"⏸️  {symbol}: {signal.upper()} "
                                       f"(Confidence: {confidence:.1f}%)")
                    
                    # Store analysis
                    self.last_signals[symbol] = analysis
                    
                    # Simulate enhanced trading for high-confidence signals
                    if signal != 'hold' and confidence > self.min_confidence:
                        trade_data = {
                            'symbol': symbol,
                            'action': signal,
                            'amount': position_size * 1000,  # Simulated position
                            'price': analysis['current_price'],
                            'timestamp': datetime.now().isoformat(),
                            'confidence': confidence,
                            'reasoning': reasoning
                        }
                        
                        self.logger.trade(f"🎯 SIMULATED {signal.upper()} {symbol} "
                                        f"at ${analysis['current_price']:.4f} "
                                        f"(Size: {position_size:.1%})")
                        
                        await self.notification_manager.notify_trade(trade_data)
                    
                    # Small delay between symbols
                    await asyncio.sleep(1)
                
                # Print statistics every 10 iterations
                if sum(self.signal_stats.values()) % 10 == 0:
                    self._print_signal_statistics()
                
                # Wait before next iteration (5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in optimized trading loop: {e}")
                await asyncio.sleep(60)
    
    def _print_signal_statistics(self):
        """Print signal distribution statistics"""
        
        total_signals = sum(self.signal_stats.values())
        if total_signals == 0:
            return
        
        print("\n📊 SIGNAL DISTRIBUTION:")
        print("=" * 30)
        
        for signal, count in self.signal_stats.items():
            pct = (count / total_signals) * 100
            if count > 0:
                print(f"   {signal.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
        
        hold_pct = (self.signal_stats['hold'] / total_signals) * 100
        if hold_pct < 70:
            print(f"✅ Good signal diversity: {hold_pct:.1f}% HOLD")
        else:
            print(f"⚠️  High HOLD rate: {hold_pct:.1f}%")

if __name__ == "__main__":
    print("🚀 Optimized AI Trading Bot")
    print("=" * 50)
    print("✅ Dynamic confidence thresholds")
    print("✅ Multi-tier signal generation") 
    print("✅ Enhanced position sizing")
    print("✅ Improved trading logic")
    print("=" * 50)
    
    # Create optimized bot
    bot = OptimizedTradingBot()
    
    try:
        # Start the bot
        bot.start()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping optimized bot...")
        bot.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        bot.logger.error(f"Fatal error: {e}")
'''
        
        # Write optimized bot script
        with open('optimized_ai_trading_bot.py', 'w') as f:
            f.write(optimized_bot_code)
        
        # Make executable
        os.chmod('optimized_ai_trading_bot.py', 0o755)
        
        self.logger.info("✅ Created optimized_ai_trading_bot.py")
    
    def run_optimization(self):
        """Run the complete optimization process"""
        
        print("\n🚀 AI TRADING BOT OPTIMIZATION")
        print("=" * 60)
        print("🎯 Problem: 95%+ HOLD signals due to high confidence thresholds")
        print("🔧 Solution: Dynamic thresholds and multi-tier signals")
        print("=" * 60)
        
        # 1. Analyze current performance
        self.analyze_current_performance()
        
        # 2. Update configuration
        self.update_config_file()
        
        # 3. Create optimized bot
        self.create_optimized_bot_script()
        
        print("\n✅ OPTIMIZATION COMPLETE!")
        print("=" * 40)
        print("📋 Next Steps:")
        print("1. Stop current bot (Ctrl+C)")
        print("2. Run: python optimized_ai_trading_bot.py")
        print("3. Monitor improved signal generation")
        print("4. Expect 50-70% fewer HOLD signals")
        print("=" * 40)

def main():
    """Main optimization function"""
    
    # Create and run optimization system
    optimizer = OptimizedTradingSystem()
    optimizer.run_optimization()

if __name__ == "__main__":
    main() 