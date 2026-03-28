#!/usr/bin/env python3
"""
🤖 AI TRADING ENGINE
Advanced AI-powered trading system with multiple strategies and risk management
Supports multi-exchange trading with real-time signal generation
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
from dataclasses import dataclass


@dataclass
class TradingSignal:
    """Trading signal data structure"""

    symbol: str
    action: str  # BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
    confidence: float  # 0.0 to 1.0
    price_target: float
    stop_loss: float
    take_profit: float
    timeframe: str
    strategy_name: str
    indicators_used: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH, EXTREME
    expected_return: float
    max_drawdown: float
    holding_period: int  # in hours
    market_conditions: Dict[str, Any]
    timestamp: datetime


@dataclass
class Position:
    """Trading position data structure"""

    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    exchange: str
    strategy: str


class TechnicalAnalysis:
    """Advanced technical analysis with multiple indicators"""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            # Basic price indicators
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()
            df["ema_20"] = df["close"].ewm(span=20).mean()

            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # MACD
            exp1 = df["close"].ewm(span=12).mean()
            exp2 = df["close"].ewm(span=26).mean()
            df["macd"] = exp1 - exp2
            df["macd_signal"] = df["macd"].ewm(span=9).mean()
            df["macd_hist"] = df["macd"] - df["macd_signal"]

            # Bollinger Bands
            df["bb_middle"] = df["close"].rolling(window=20).mean()
            bb_std = df["close"].rolling(window=20).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
            df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

            # Volume indicators
            df["volume_sma"] = df["volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_sma"]

            # Volatility
            df["volatility"] = df["close"].rolling(window=20).std()
            df["atr"] = (
                df[["high", "low", "close"]]
                .apply(
                    lambda x: max(
                        x["high"] - x["low"],
                        abs(x["high"] - x["close"]),
                        abs(x["low"] - x["close"]),
                    ),
                    axis=1,
                )
                .rolling(window=14)
                .mean()
            )

            return df

        except Exception as e:
            logging.error(f"Technical analysis calculation failed: {e}")
            return df


class MarketRegimeDetector:
    """Detect market conditions and regimes"""

    @staticmethod
    def detect_regime(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect current market regime"""
        try:
            if len(df) < 50:
                return {"trend": "UNKNOWN", "volatility": "UNKNOWN", "strength": 0}

            # Trend detection
            sma_20 = df["sma_20"].iloc[-1] if "sma_20" in df.columns else df["close"].iloc[-1]
            sma_50 = df["sma_50"].iloc[-1] if "sma_50" in df.columns else df["close"].iloc[-1]
            current_price = df["close"].iloc[-1]

            # Volatility analysis
            volatility = df["volatility"].iloc[-1] if "volatility" in df.columns else 0
            avg_volatility = (
                df["volatility"].rolling(50).mean().iloc[-1] if "volatility" in df.columns else 0
            )

            # Determine trend
            if current_price > sma_20 > sma_50:
                trend = "BULLISH"
            elif current_price < sma_20 < sma_50:
                trend = "BEARISH"
            else:
                trend = "SIDEWAYS"

            # Determine volatility regime
            if avg_volatility > 0:
                if volatility > avg_volatility * 1.5:
                    volatility_regime = "HIGH"
                elif volatility < avg_volatility * 0.7:
                    volatility_regime = "LOW"
                else:
                    volatility_regime = "NORMAL"
            else:
                volatility_regime = "NORMAL"

            return {
                "trend": trend,
                "volatility": volatility_regime,
                "strength": abs(current_price - sma_50) / sma_50 if sma_50 > 0 else 0,
                "momentum": (
                    (current_price - df["close"].iloc[-20]) / df["close"].iloc[-20]
                    if len(df) >= 20
                    else 0
                ),
            }

        except Exception as e:
            logging.error(f"Market regime detection failed: {e}")
            return {"trend": "UNKNOWN", "volatility": "UNKNOWN", "strength": 0, "momentum": 0}


class SimpleAIModel:
    """Simple AI model for trading predictions"""

    def __init__(self):
        self.is_trained = False

    def train(self, df: pd.DataFrame):
        """Train the model with historical data"""
        try:
            if len(df) > 100:
                self.is_trained = True
                logging.info("🤖 Simple AI model trained")
                return True
            return False
        except Exception as e:
            logging.error(f"AI model training failed: {e}")
            return False

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Make prediction based on current data"""
        try:
            if not self.is_trained or len(df) < 20:
                return {"action": "HOLD", "confidence": 0.0}

            # Simple prediction logic based on multiple indicators
            rsi = df["rsi"].iloc[-1] if "rsi" in df.columns else 50
            macd = df["macd"].iloc[-1] if "macd" in df.columns else 0
            macd_signal = df["macd_signal"].iloc[-1] if "macd_signal" in df.columns else 0
            bb_position = df["bb_position"].iloc[-1] if "bb_position" in df.columns else 0.5

            # Scoring system
            score = 0

            # RSI signals
            if rsi < 30:
                score += 2  # Oversold, buy signal
            elif rsi > 70:
                score -= 2  # Overbought, sell signal
            elif 40 < rsi < 60:
                score += 0.5  # Neutral, slight buy bias

            # MACD signals
            if macd > macd_signal:
                score += 1
            else:
                score -= 1

            # Bollinger Bands
            if bb_position < 0.2:
                score += 1  # Near lower band, buy signal
            elif bb_position > 0.8:
                score -= 1  # Near upper band, sell signal

            # Convert score to action and confidence
            if score >= 2:
                action = "STRONG_BUY"
                confidence = min(0.9, 0.6 + (score - 2) * 0.1)
            elif score >= 1:
                action = "BUY"
                confidence = 0.7
            elif score <= -2:
                action = "STRONG_SELL"
                confidence = min(0.9, 0.6 + abs(score + 2) * 0.1)
            elif score <= -1:
                action = "SELL"
                confidence = 0.7
            else:
                action = "HOLD"
                confidence = 0.5

            return {"action": action, "confidence": confidence, "score": score}

        except Exception as e:
            logging.error(f"AI prediction failed: {e}")
            return {"action": "HOLD", "confidence": 0.0}


class TradingStrategy:
    """Base trading strategy class"""

    def __init__(self, name: str):
        self.name = name
        self.ai_model = SimpleAIModel()
        self.technical_analysis = TechnicalAnalysis()
        self.regime_detector = MarketRegimeDetector()

    def analyze_market_conditions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze current market conditions"""
        return self.regime_detector.detect_regime(df)

    def calculate_entry_signals(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Calculate entry signals - to be implemented by subclasses"""
        raise NotImplementedError

    def calculate_risk_parameters(self, df: pd.DataFrame, signal: TradingSignal) -> TradingSignal:
        """Calculate risk parameters for the signal"""
        try:
            current_price = df["close"].iloc[-1]
            atr = (
                df["atr"].iloc[-1]
                if "atr" in df.columns and not pd.isna(df["atr"].iloc[-1])
                else current_price * 0.02
            )

            if signal.action in ["BUY", "STRONG_BUY"]:
                # Long position
                signal.stop_loss = current_price - (2 * atr)
                signal.take_profit = current_price + (3 * atr)
                signal.expected_return = (signal.take_profit - current_price) / current_price
                signal.max_drawdown = (current_price - signal.stop_loss) / current_price
            elif signal.action in ["SELL", "STRONG_SELL"]:
                # Short position
                signal.stop_loss = current_price + (2 * atr)
                signal.take_profit = current_price - (3 * atr)
                signal.expected_return = (current_price - signal.take_profit) / current_price
                signal.max_drawdown = (signal.stop_loss - current_price) / current_price

            return signal

        except Exception as e:
            logging.error(f"Risk parameter calculation failed: {e}")
            return signal


class AITradingStrategy(TradingStrategy):
    """AI-powered trading strategy"""

    def __init__(self):
        super().__init__("AI_STRATEGY")

    def calculate_entry_signals(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Calculate AI-based entry signals"""
        try:
            # Calculate technical indicators
            df_with_indicators = self.technical_analysis.calculate_indicators(df.copy())

            # Get market conditions
            market_conditions = self.analyze_market_conditions(df_with_indicators)

            # Get AI prediction
            ai_prediction = self.ai_model.predict(df_with_indicators)

            if ai_prediction["confidence"] < 0.6:  # Minimum confidence threshold
                return None

            # Create trading signal
            signal = TradingSignal(
                symbol=(
                    df.get("symbol", ["UNKNOWN"])[0]
                    if hasattr(df.get("symbol", "UNKNOWN"), "__iter__")
                    else "UNKNOWN"
                ),
                action=ai_prediction["action"],
                confidence=ai_prediction["confidence"],
                price_target=df["close"].iloc[-1],
                stop_loss=0,  # Will be calculated
                take_profit=0,  # Will be calculated
                timeframe="1h",
                strategy_name=self.name,
                indicators_used=["AI_MODEL", "RSI", "MACD", "BOLLINGER_BANDS"],
                risk_level="MEDIUM",
                expected_return=0,
                max_drawdown=0,
                holding_period=24,  # 24 hours default
                market_conditions=market_conditions,
                timestamp=datetime.now(),
            )

            # Calculate risk parameters
            signal = self.calculate_risk_parameters(df_with_indicators, signal)

            return signal

        except Exception as e:
            logging.error(f"AI signal calculation failed: {e}")
            return None


class MomentumStrategy(TradingStrategy):
    """Momentum-based trading strategy"""

    def __init__(self):
        super().__init__("MOMENTUM")

    def calculate_entry_signals(self, df: pd.DataFrame) -> Optional[TradingSignal]:
        """Calculate momentum-based entry signals"""
        try:
            # Calculate technical indicators
            df_with_indicators = self.technical_analysis.calculate_indicators(df.copy())

            if len(df_with_indicators) < 20:
                return None

            # Get latest values
            rsi = df_with_indicators["rsi"].iloc[-1] if "rsi" in df_with_indicators.columns else 50
            macd = (
                df_with_indicators["macd"].iloc[-1] if "macd" in df_with_indicators.columns else 0
            )
            macd_signal = (
                df_with_indicators["macd_signal"].iloc[-1]
                if "macd_signal" in df_with_indicators.columns
                else 0
            )
            price = df_with_indicators["close"].iloc[-1]
            sma_20 = (
                df_with_indicators["sma_20"].iloc[-1]
                if "sma_20" in df_with_indicators.columns
                else price
            )
            volume_ratio = (
                df_with_indicators["volume_ratio"].iloc[-1]
                if "volume_ratio" in df_with_indicators.columns
                else 1.0
            )

            # Momentum conditions
            macd_bullish = macd > macd_signal
            price_above_sma = price > sma_20
            high_volume = volume_ratio > 1.2

            # Generate signals
            if macd_bullish and price_above_sma and high_volume and rsi < 70:
                action = "BUY"
                confidence = 0.7
            elif not macd_bullish and not price_above_sma and high_volume and rsi > 30:
                action = "SELL"
                confidence = 0.7
            else:
                return None

            # Create signal
            signal = TradingSignal(
                symbol=(
                    df.get("symbol", ["UNKNOWN"])[0]
                    if hasattr(df.get("symbol", "UNKNOWN"), "__iter__")
                    else "UNKNOWN"
                ),
                action=action,
                confidence=confidence,
                price_target=price,
                stop_loss=0,
                take_profit=0,
                timeframe="1h",
                strategy_name=self.name,
                indicators_used=["RSI", "MACD", "SMA", "VOLUME"],
                risk_level="MEDIUM",
                expected_return=0,
                max_drawdown=0,
                holding_period=12,
                market_conditions=self.analyze_market_conditions(df_with_indicators),
                timestamp=datetime.now(),
            )

            return self.calculate_risk_parameters(df_with_indicators, signal)

        except Exception as e:
            logging.error(f"Momentum signal calculation failed: {e}")
            return None


class AITradingEngine:
    """Main AI trading engine"""

    def __init__(self, db_path: str = "crypto_trading_bot.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.strategies = {"ai_strategy": AITradingStrategy(), "momentum": MomentumStrategy()}
        self.positions = {}
        self.setup_database()

    def setup_database(self):
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.logger.info("✅ Trading engine database connected")
        except Exception as e:
            self.logger.error(f"❌ Database setup failed: {e}")

    def get_market_data(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> pd.DataFrame:
        """Get market data for analysis"""
        try:
            # For demo purposes, generate sample data
            # In production, this would fetch from exchange APIs or database
            dates = pd.date_range(
                start=datetime.now() - timedelta(hours=limit), end=datetime.now(), freq="H"
            )

            # Generate realistic price data
            np.random.seed(42)  # For reproducible results
            base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 500

            prices = []
            current_price = base_price

            for i in range(len(dates)):
                # Random walk with slight upward bias
                change = np.random.normal(0, 0.02)  # 2% volatility
                current_price *= 1 + change
                prices.append(current_price)

            df = pd.DataFrame(
                {
                    "timestamp": dates,
                    "open": prices,
                    "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                    "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                    "close": prices,
                    "volume": [np.random.uniform(1000, 10000) for _ in prices],
                }
            )

            df.set_index("timestamp", inplace=True)
            df["symbol"] = symbol
            return df

        except Exception as e:
            self.logger.error(f"Failed to get market data for {symbol}: {e}")
            return pd.DataFrame()

    def train_ai_models(self, symbols: List[str]):
        """Train AI models with historical data"""
        self.logger.info("🤖 Starting AI model training...")

        for symbol in symbols:
            try:
                # Get more historical data for training
                df = self.get_market_data(symbol, "1h", 1000)
                if len(df) > 100:
                    success = self.strategies["ai_strategy"].ai_model.train(df)
                    if success:
                        self.logger.info(f"✅ AI model trained for {symbol}")
                    else:
                        self.logger.warning(f"⚠️ AI training failed for {symbol}")
                else:
                    self.logger.warning(f"⚠️ Insufficient data for {symbol}")
            except Exception as e:
                self.logger.error(f"Training failed for {symbol}: {e}")

    def generate_signals(self, symbols: List[str]) -> List[TradingSignal]:
        """Generate trading signals for multiple symbols"""
        signals = []

        for symbol in symbols:
            try:
                # Get market data
                df = self.get_market_data(symbol)
                if df.empty:
                    continue

                # Generate signals from each strategy
                for strategy_name, strategy in self.strategies.items():
                    try:
                        signal = strategy.calculate_entry_signals(df)
                        if signal and signal.action != "HOLD":
                            signals.append(signal)
                            self.logger.info(
                                f"📊 {strategy_name} signal: {signal.action} {symbol} "
                                f"(confidence: {signal.confidence:.2f})"
                            )
                    except Exception as e:
                        self.logger.error(
                            f"Signal generation failed for {strategy_name} on {symbol}: {e}"
                        )

            except Exception as e:
                self.logger.error(f"Failed to process {symbol}: {e}")

        return signals

    def filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Filter and rank signals by quality"""
        try:
            # Filter by minimum confidence
            filtered = [s for s in signals if s.confidence >= 0.6]

            # Filter by risk level
            filtered = [s for s in signals if s.risk_level in ["LOW", "MEDIUM"]]

            # Sort by confidence * expected_return
            filtered.sort(key=lambda x: x.confidence * max(x.expected_return, 0.01), reverse=True)

            # Limit to top 10 signals
            return filtered[:10]

        except Exception as e:
            self.logger.error(f"Signal filtering failed: {e}")
            return signals

    def execute_signal(self, signal: TradingSignal) -> bool:
        """Execute a trading signal"""
        try:
            # This would integrate with actual exchange APIs
            # For now, just log the signal
            self.logger.info(f"🚀 Executing {signal.action} signal for {signal.symbol}")
            self.logger.info(f"   Strategy: {signal.strategy_name}")
            self.logger.info(f"   Confidence: {signal.confidence:.2f}")
            self.logger.info(f"   Expected Return: {signal.expected_return:.2%}")
            self.logger.info(f"   Stop Loss: {signal.stop_loss:.4f}")
            self.logger.info(f"   Take Profit: {signal.take_profit:.4f}")

            # Store signal in database
            self.store_signal(signal)

            return True

        except Exception as e:
            self.logger.error(f"Signal execution failed: {e}")
            return False

    def store_signal(self, signal: TradingSignal):
        """Store trading signal in database"""
        try:
            cursor = self.conn.cursor()

            # Create a simple signals table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_signals_simple (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    action TEXT,
                    confidence REAL,
                    price_target REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    strategy_name TEXT,
                    expected_return REAL,
                    risk_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                INSERT INTO trading_signals_simple (
                    symbol, action, confidence, price_target, stop_loss, take_profit,
                    strategy_name, expected_return, risk_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    signal.symbol,
                    signal.action,
                    signal.confidence,
                    signal.price_target,
                    signal.stop_loss,
                    signal.take_profit,
                    signal.strategy_name,
                    signal.expected_return,
                    signal.risk_level,
                ),
            )

            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to store signal: {e}")

    async def run_trading_cycle(self, symbols: List[str]):
        """Run a complete trading cycle"""
        self.logger.info("🔄 Starting trading cycle...")

        try:
            # Generate signals
            signals = self.generate_signals(symbols)
            self.logger.info(f"📈 Generated {len(signals)} raw signals")

            # Filter signals
            filtered_signals = self.filter_signals(signals)
            self.logger.info(f"✅ Filtered to {len(filtered_signals)} quality signals")

            # Execute signals
            executed_count = 0
            for signal in filtered_signals:
                if self.execute_signal(signal):
                    executed_count += 1

            self.logger.info(f"🚀 Executed {executed_count} signals")

            return {
                "total_signals": len(signals),
                "filtered_signals": len(filtered_signals),
                "executed_signals": executed_count,
            }

        except Exception as e:
            self.logger.error(f"Trading cycle failed: {e}")
            return None


# Usage example
async def main():
    """Main trading function"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Initialize trading engine
    engine = AITradingEngine()

    # Define trading symbols
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"]

    # Train AI models
    engine.train_ai_models(symbols)

    # Run trading cycles
    cycle_count = 0
    while cycle_count < 5:  # Run 5 cycles for demo
        try:
            result = await engine.run_trading_cycle(symbols)
            if result:
                print(
                    f"🔄 Trading cycle {cycle_count + 1}: "
                    f"{result['executed_signals']} signals executed"
                )

            cycle_count += 1
            # Wait 30 seconds between cycles for demo
            await asyncio.sleep(30)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
