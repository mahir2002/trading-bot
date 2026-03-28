#!/usr/bin/env python3
"""
Advanced Trading Strategies for AI Trading Bot
Implements strategies from the educational document with proper risk management

This module includes:
- Moving Average Crossover (Golden Cross/Death Cross)
- RSI Oversold/Overbought Strategy
- Scalping Strategy
- Memecoin Momentum Strategy with extreme risk management
- Dollar Cost Averaging
- Hybrid Strategy combining multiple indicators
- Comprehensive risk management system
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

class StrategyType(Enum):
    """Trading strategy types"""
    MOVING_AVERAGE_CROSSOVER = "ma_crossover"
    RSI_OVERSOLD_OVERBOUGHT = "rsi_levels"
    EVENT_DRIVEN = "event_driven"
    SCALPING = "scalping"
    DOLLAR_COST_AVERAGING = "dca"
    MEMECOIN_MOMENTUM = "memecoin_momentum"
    HYBRID_STRATEGY = "hybrid"

class RiskLevel(Enum):
    """Risk levels for different assets"""
    LOW = "low"           # BTC, ETH
    MEDIUM = "medium"     # Top 20 altcoins
    HIGH = "high"         # Smaller altcoins
    EXTREME = "extreme"   # Memecoins

@dataclass
class TradingSignal:
    """Trading signal with confidence and risk assessment"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0.0 to 1.0
    strategy: StrategyType
    risk_level: RiskLevel
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 0.0
    reasoning: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RiskParameters:
    """Risk management parameters based on educational document"""
    max_position_size: float = 0.02  # 2% of portfolio per trade
    stop_loss_percentage: float = 0.05  # 5% stop loss
    take_profit_percentage: float = 0.10  # 10% take profit
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_open_positions: int = 5
    risk_reward_ratio: float = 2.0  # Minimum 2:1 risk/reward

class AdvancedTradingStrategies:
    """
    Advanced trading strategies implementation based on educational document
    
    Implements:
    1. Moving Average Crossovers (Golden Cross/Death Cross)
    2. RSI Oversold/Overbought levels
    3. Scalping for short-term profits
    4. Memecoin momentum with extreme risk management
    5. Dollar Cost Averaging for long-term positions
    6. Hybrid strategies combining multiple indicators
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Risk parameters by asset class (from educational document)
        self.risk_params = {
            RiskLevel.LOW: RiskParameters(
                max_position_size=0.05,  # 5% for BTC/ETH
                stop_loss_percentage=0.03,  # Tighter stops for stable assets
                take_profit_percentage=0.08
            ),
            RiskLevel.MEDIUM: RiskParameters(
                max_position_size=0.03,  # 3% for top altcoins
                stop_loss_percentage=0.05,
                take_profit_percentage=0.12
            ),
            RiskLevel.HIGH: RiskParameters(
                max_position_size=0.02,  # 2% for smaller altcoins
                stop_loss_percentage=0.08,
                take_profit_percentage=0.15
            ),
            RiskLevel.EXTREME: RiskParameters(
                max_position_size=0.005,  # 0.5% for memecoins (extreme caution)
                stop_loss_percentage=0.15,  # Wide stops due to volatility
                take_profit_percentage=0.30  # Higher targets for high risk
            )
        }
        
        # Memecoin identifiers (as mentioned in educational document)
        self.memecoin_keywords = [
            'doge', 'shib', 'pepe', 'floki', 'safemoon', 'babydoge',
            'elon', 'moon', 'inu', 'meme', 'wojak', 'chad', 'bonk'
        ]
    
    def classify_asset_risk(self, symbol: str, market_cap: Optional[float] = None) -> RiskLevel:
        """
        Classify asset risk level based on symbol and market cap
        Following the risk assessment from the educational document
        """
        symbol_lower = symbol.lower()
        
        # Check if it's a memecoin (highest risk)
        if any(keyword in symbol_lower for keyword in self.memecoin_keywords):
            return RiskLevel.EXTREME
        
        # Major cryptocurrencies (lowest risk)
        major_cryptos = ['btc', 'eth', 'bitcoin', 'ethereum']
        if any(crypto in symbol_lower for crypto in major_cryptos):
            return RiskLevel.LOW
        
        # Top altcoins (medium risk)
        top_altcoins = ['ada', 'sol', 'dot', 'link', 'matic', 'avax', 'atom', 'near', 'uni', 'aave']
        if any(alt in symbol_lower for alt in top_altcoins):
            return RiskLevel.MEDIUM
        
        # Use market cap if available
        if market_cap:
            if market_cap > 10_000_000_000:  # > $10B
                return RiskLevel.LOW
            elif market_cap > 1_000_000_000:  # > $1B
                return RiskLevel.MEDIUM
            elif market_cap > 100_000_000:   # > $100M
                return RiskLevel.HIGH
            else:
                return RiskLevel.EXTREME
        
        # Default to high risk for unknown assets
        return RiskLevel.HIGH
    
    def moving_average_crossover(self, df: pd.DataFrame, symbol: str, 
                                short_window: int = 50, long_window: int = 200) -> Optional[TradingSignal]:
        """
        Moving Average Crossover Strategy
        
        Implements Golden Cross and Death Cross signals as described in educational document:
        - Golden Cross: Short MA crosses above Long MA (bullish signal)
        - Death Cross: Short MA crosses below Long MA (bearish signal)
        """
        if len(df) < long_window:
            return None
        
        # Calculate moving averages
        df['MA_short'] = df['close'].rolling(window=short_window).mean()
        df['MA_long'] = df['close'].rolling(window=long_window).mean()
        
        # Get latest values
        current_short = df['MA_short'].iloc[-1]
        current_long = df['MA_long'].iloc[-1]
        prev_short = df['MA_short'].iloc[-2]
        prev_long = df['MA_long'].iloc[-2]
        current_price = df['close'].iloc[-1]
        
        # Check for crossover
        golden_cross = (prev_short <= prev_long) and (current_short > current_long)
        death_cross = (prev_short >= prev_long) and (current_short < current_long)
        
        if golden_cross:
            risk_level = self.classify_asset_risk(symbol)
            risk_params = self.risk_params[risk_level]
            
            return TradingSignal(
                symbol=symbol,
                action='buy',
                confidence=0.7,
                strategy=StrategyType.MOVING_AVERAGE_CROSSOVER,
                risk_level=risk_level,
                entry_price=current_price,
                stop_loss=current_price * (1 - risk_params.stop_loss_percentage),
                take_profit=current_price * (1 + risk_params.take_profit_percentage),
                reasoning=f"Golden Cross: {short_window}MA crossed above {long_window}MA"
            )
        
        elif death_cross:
            return TradingSignal(
                symbol=symbol,
                action='sell',
                confidence=0.7,
                strategy=StrategyType.MOVING_AVERAGE_CROSSOVER,
                risk_level=self.classify_asset_risk(symbol),
                entry_price=current_price,
                reasoning=f"Death Cross: {short_window}MA crossed below {long_window}MA"
            )
        
        return None
    
    def rsi_oversold_overbought(self, df: pd.DataFrame, symbol: str,
                               rsi_period: int = 14, oversold: int = 30, 
                               overbought: int = 70) -> Optional[TradingSignal]:
        """
        RSI Oversold/Overbought Strategy
        
        As described in educational document:
        - RSI > 70: Overbought condition (potential sell)
        - RSI < 30: Oversold condition (potential buy)
        """
        if len(df) < rsi_period + 1:
            return None
        
        # Calculate RSI
        df['RSI'] = ta.momentum.rsi(df['close'], window=rsi_period)
        
        current_rsi = df['RSI'].iloc[-1]
        current_price = df['close'].iloc[-1]
        risk_level = self.classify_asset_risk(symbol)
        risk_params = self.risk_params[risk_level]
        
        # Oversold condition (potential buy)
        if current_rsi < oversold:
            # Higher confidence for more oversold conditions
            confidence = min(0.9, (oversold - current_rsi) / oversold + 0.5)
            
            return TradingSignal(
                symbol=symbol,
                action='buy',
                confidence=confidence,
                strategy=StrategyType.RSI_OVERSOLD_OVERBOUGHT,
                risk_level=risk_level,
                entry_price=current_price,
                stop_loss=current_price * (1 - risk_params.stop_loss_percentage),
                take_profit=current_price * (1 + risk_params.take_profit_percentage),
                reasoning=f"RSI oversold at {current_rsi:.2f}"
            )
        
        # Overbought condition (potential sell)
        elif current_rsi > overbought:
            confidence = min(0.9, (current_rsi - overbought) / (100 - overbought) + 0.5)
            
            return TradingSignal(
                symbol=symbol,
                action='sell',
                confidence=confidence,
                strategy=StrategyType.RSI_OVERSOLD_OVERBOUGHT,
                risk_level=risk_level,
                entry_price=current_price,
                reasoning=f"RSI overbought at {current_rsi:.2f}"
            )
        
        return None
    
    def scalping_strategy(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSignal]:
        """
        Scalping Strategy for short-term profits
        
        As described in educational document:
        - High-frequency trading for small price changes
        - Quick execution with tight risk management
        - Only for stable, liquid assets (not memecoins)
        """
        if len(df) < 20:
            return None
        
        # Calculate indicators for scalping
        df['EMA_fast'] = ta.trend.ema_indicator(df['close'], window=5)
        df['EMA_slow'] = ta.trend.ema_indicator(df['close'], window=10)
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        df['BB_upper'] = ta.volatility.bollinger_hband(df['close'])
        df['BB_lower'] = ta.volatility.bollinger_lband(df['close'])
        
        current_price = df['close'].iloc[-1]
        ema_fast = df['EMA_fast'].iloc[-1]
        ema_slow = df['EMA_slow'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        bb_upper = df['BB_upper'].iloc[-1]
        bb_lower = df['BB_lower'].iloc[-1]
        
        risk_level = self.classify_asset_risk(symbol)
        
        # Only scalp low to medium risk assets (avoid high volatility)
        if risk_level in [RiskLevel.EXTREME, RiskLevel.HIGH]:
            return None
        
        # Bullish scalping signal
        if (ema_fast > ema_slow and 
            rsi < 70 and 
            current_price > bb_lower and 
            current_price < (bb_upper + bb_lower) / 2):
            
            return TradingSignal(
                symbol=symbol,
                action='buy',
                confidence=0.6,
                strategy=StrategyType.SCALPING,
                risk_level=risk_level,
                entry_price=current_price,
                stop_loss=current_price * 0.995,  # Very tight 0.5% stop loss
                take_profit=current_price * 1.01,  # Quick 1% profit target
                reasoning="Scalping: EMA bullish, RSI not overbought, price in lower BB range"
            )
        
        # Bearish scalping signal
        elif (ema_fast < ema_slow and 
              rsi > 30 and 
              current_price < bb_upper and 
              current_price > (bb_upper + bb_lower) / 2):
            
            return TradingSignal(
                symbol=symbol,
                action='sell',
                confidence=0.6,
                strategy=StrategyType.SCALPING,
                risk_level=risk_level,
                entry_price=current_price,
                reasoning="Scalping: EMA bearish, RSI not oversold, price in upper BB range"
            )
        
        return None
    
    def memecoin_momentum_strategy(self, df: pd.DataFrame, symbol: str) -> Optional[TradingSignal]:
        """
        Memecoin-specific momentum strategy with EXTREME risk management
        
        As warned in educational document:
        - Memecoins are extremely volatile and speculative
        - Lack fundamental value
        - Prone to pump-and-dump schemes
        - Only trade with money you can afford to lose entirely
        """
        risk_level = self.classify_asset_risk(symbol)
        
        # Only apply to memecoins
        if risk_level != RiskLevel.EXTREME:
            return None
        
        if len(df) < 20:
            return None
        
        # Calculate momentum indicators
        df['price_change_1h'] = df['close'].pct_change(periods=1)
        df['price_change_4h'] = df['close'].pct_change(periods=4)
        df['volatility'] = df['close'].rolling(window=10).std()
        
        current_price = df['close'].iloc[-1]
        price_change_1h = df['price_change_1h'].iloc[-1]
        price_change_4h = df['price_change_4h'].iloc[-1]
        
        risk_params = self.risk_params[RiskLevel.EXTREME]
        
        # Extreme momentum buy signal (VERY RISKY)
        if (price_change_1h > 0.05 and  # 5% gain in 1 hour
            price_change_4h > 0.10):     # 10% gain in 4 hours
            
            return TradingSignal(
                symbol=symbol,
                action='buy',
                confidence=0.4,  # Low confidence due to extreme risk
                strategy=StrategyType.MEMECOIN_MOMENTUM,
                risk_level=RiskLevel.EXTREME,
                entry_price=current_price,
                stop_loss=current_price * (1 - risk_params.stop_loss_percentage),
                take_profit=current_price * (1 + risk_params.take_profit_percentage),
                reasoning=f"⚠️ EXTREME RISK: Memecoin momentum {price_change_1h:.1%} 1h, {price_change_4h:.1%} 4h"
            )
        
        # Rapid exit signal for memecoins (crash protection)
        elif price_change_1h < -0.10:  # 10% drop in 1 hour
            return TradingSignal(
                symbol=symbol,
                action='sell',
                confidence=0.8,
                strategy=StrategyType.MEMECOIN_MOMENTUM,
                risk_level=RiskLevel.EXTREME,
                entry_price=current_price,
                reasoning=f"🚨 Memecoin crash protection: {price_change_1h:.1%} drop in 1h"
            )
        
        return None
    
    def dollar_cost_averaging(self, symbol: str, current_price: float,
                             last_purchase_date: Optional[datetime] = None,
                             dca_interval_days: int = 7) -> Optional[TradingSignal]:
        """
        Dollar Cost Averaging Strategy
        
        As described in educational document:
        - Long-term investment strategy
        - Fixed amount invested at regular intervals
        - Reduces impact of market volatility
        - Only for stable assets (not memecoins)
        """
        risk_level = self.classify_asset_risk(symbol)
        
        # DCA only for low to medium risk assets
        if risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
            return None
        
        # Check if it's time for next DCA purchase
        if last_purchase_date:
            days_since_last = (datetime.now() - last_purchase_date).days
            if days_since_last < dca_interval_days:
                return None
        
        risk_params = self.risk_params[risk_level]
        
        return TradingSignal(
            symbol=symbol,
            action='buy',
            confidence=0.8,  # High confidence for DCA
            strategy=StrategyType.DOLLAR_COST_AVERAGING,
            risk_level=risk_level,
            entry_price=current_price,
            position_size=risk_params.max_position_size * 0.5,  # Smaller DCA positions
            reasoning=f"DCA purchase - regular {dca_interval_days}-day interval"
        )
    
    def validate_signal(self, signal: TradingSignal, portfolio_value: float,
                       daily_loss: float = 0.0) -> bool:
        """
        Validate trading signal against risk parameters
        Implements risk management principles from educational document
        """
        risk_params = self.risk_params[signal.risk_level]
        
        # Check daily loss limit
        if daily_loss >= risk_params.max_daily_loss:
            self.logger.warning(f"Daily loss limit reached: {daily_loss:.2%}")
            return False
        
        # Check minimum confidence thresholds
        min_confidence = {
            RiskLevel.LOW: 0.6,
            RiskLevel.MEDIUM: 0.65,
            RiskLevel.HIGH: 0.7,
            RiskLevel.EXTREME: 0.4  # Lower threshold for memecoins due to their nature
        }
        
        if signal.confidence < min_confidence[signal.risk_level]:
            return False
        
        # Check risk/reward ratio
        if signal.stop_loss and signal.take_profit and signal.action == 'buy':
            risk = signal.entry_price - signal.stop_loss
            reward = signal.take_profit - signal.entry_price
            
            if risk > 0 and reward / risk < risk_params.risk_reward_ratio:
                self.logger.warning(f"Poor risk/reward ratio: {reward/risk:.2f}")
                return False
        
        return True
    
    def get_trading_signals(self, market_data: Dict[str, pd.DataFrame],
                           portfolio_value: float = 10000,
                           daily_loss: float = 0.0) -> List[TradingSignal]:
        """
        Get trading signals for multiple symbols
        Implements all strategies from the educational document
        """
        signals = []
        
        for symbol, df in market_data.items():
            try:
                # Apply all strategies
                strategies = [
                    self.moving_average_crossover(df, symbol),
                    self.rsi_oversold_overbought(df, symbol),
                    self.scalping_strategy(df, symbol),
                    self.memecoin_momentum_strategy(df, symbol)
                ]
                
                # Filter valid signals and validate them
                for strategy_signal in strategies:
                    if (strategy_signal and 
                        self.validate_signal(strategy_signal, portfolio_value, daily_loss)):
                        signals.append(strategy_signal)
                
            except Exception as e:
                self.logger.error(f"Error generating signals for {symbol}: {e}")
        
        # Sort by confidence and risk level (prioritize high confidence, low risk)
        signals.sort(key=lambda x: (x.confidence, -list(RiskLevel).index(x.risk_level)), reverse=True)
        
        return signals

# Example usage and testing
if __name__ == "__main__":
    import random
    
    def create_sample_data(symbol: str, days: int = 100) -> pd.DataFrame:
        """Create sample OHLCV data for testing"""
        dates = pd.date_range(start='2024-01-01', periods=days, freq='1H')
        
        # Simulate price data with different volatility for different assets
        if 'BTC' in symbol:
            base_price = 50000
            volatility = 0.02  # 2% volatility for BTC
        elif 'ETH' in symbol:
            base_price = 3000
            volatility = 0.03  # 3% volatility for ETH
        elif any(meme in symbol.lower() for meme in ['doge', 'shib', 'pepe']):
            base_price = 0.1
            volatility = 0.10  # 10% volatility for memecoins
        else:
            base_price = 100
            volatility = 0.05  # 5% volatility for altcoins
        
        prices = []
        current_price = base_price
        
        for _ in range(days):
            change = random.uniform(-volatility, volatility)
            current_price *= (1 + change)
            prices.append(current_price)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * random.uniform(1.0, 1.02) for p in prices],
            'low': [p * random.uniform(0.98, 1.0) for p in prices],
            'close': prices,
            'volume': [random.uniform(1000, 10000) for _ in prices]
        })
        
        return df
    
    # Test the strategies
    print("🤖 Advanced Trading Strategies - Educational Implementation")
    print("=" * 60)
    
    strategies = AdvancedTradingStrategies()
    
    # Create sample data for different asset types
    test_data = {
        'BTC/USDT': create_sample_data('BTC', 250),
        'ETH/USDT': create_sample_data('ETH', 250),
        'ADA/USDT': create_sample_data('ADA', 250),
        'DOGE/USDT': create_sample_data('DOGE', 250),
        'PEPE/USDT': create_sample_data('PEPE', 250)
    }
    
    # Get trading signals
    signals = strategies.get_trading_signals(test_data, portfolio_value=10000)
    
    print(f"\n📊 Generated {len(signals)} trading signals:")
    print("-" * 60)
    
    for i, signal in enumerate(signals[:10], 1):  # Show top 10 signals
        risk_emoji = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡", 
            RiskLevel.HIGH: "🟠",
            RiskLevel.EXTREME: "🔴"
        }
        
        print(f"\n{i}. {signal.symbol}: {signal.action.upper()} {risk_emoji[signal.risk_level]}")
        print(f"   Strategy: {signal.strategy.value}")
        print(f"   Confidence: {signal.confidence:.1%}")
        print(f"   Risk Level: {signal.risk_level.value}")
        print(f"   Entry: ${signal.entry_price:.4f}")
        if signal.stop_loss:
            print(f"   Stop Loss: ${signal.stop_loss:.4f}")
        if signal.take_profit:
            print(f"   Take Profit: ${signal.take_profit:.4f}")
        print(f"   Reasoning: {signal.reasoning}")
    
    print(f"\n⚠️  DISCLAIMER: This is for educational purposes only.")
    print("   Never invest more than you can afford to lose!")
    print("   Memecoins are extremely risky and speculative!")
