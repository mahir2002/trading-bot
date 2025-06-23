#!/usr/bin/env python3
"""
🚀 Enhanced Trading System with Advanced ML Models
Integrates LSTM, Transformer, ARIMA, GARCH models with sentiment analysis
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import json

# Import our advanced models
try:
    from advanced_ml_models import AdvancedEnsemblePredictor, AdvancedFeatureEngineer
except ImportError:
    logger.warning("Advanced ML models not available, using fallback")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedTradingSignal:
    """Enhanced trading signal with comprehensive analysis"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    
    # Model predictions
    lstm_prediction: float = 0.0
    transformer_prediction: float = 0.0
    arima_prediction: float = 0.0
    ensemble_prediction: float = 0.0
    
    # Sentiment analysis
    overall_sentiment: float = 0.0
    twitter_sentiment: float = 0.0
    news_sentiment: float = 0.0
    fear_greed_index: int = 50
    
    # Technical analysis
    technical_score: float = 0.0
    volatility_forecast: float = 0.0
    trend_strength: float = 0.0
    
    # Risk metrics
    risk_score: float = 0.0
    max_drawdown_risk: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: str = ""

class EnhancedTradingSystem:
    """Enhanced trading system with advanced ML models and sentiment analysis"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        
        # Initialize advanced models
        try:
            self.ensemble_predictor = AdvancedEnsemblePredictor()
            self.ensemble_predictor.initialize_models()
            self.advanced_models_available = True
        except:
            self.advanced_models_available = False
            logger.warning("Advanced models not available, using simplified analysis")
        
        # Trading parameters
        self.max_position_size = 0.2  # Max 20% per position
        self.stop_loss_pct = 0.05     # 5% stop loss
        self.take_profit_pct = 0.15   # 15% take profit
        self.min_confidence = 0.7     # Minimum confidence for trades
        
        logger.info("🚀 Enhanced Trading System initialized")
    
    def analyze_symbol_comprehensive(self, symbol: str, price_data: pd.DataFrame) -> EnhancedTradingSignal:
        """Comprehensive analysis of a trading symbol"""
        try:
            logger.info(f"📊 Analyzing {symbol} with enhanced models...")
            
            # Simulate sentiment data (in real implementation, this would be collected from APIs)
            sentiment_data = self._simulate_sentiment_data(symbol)
            
            # Advanced model predictions
            if self.advanced_models_available:
                prediction_result = self._get_advanced_predictions(price_data, sentiment_data)
            else:
                prediction_result = self._get_fallback_predictions(price_data)
            
            # Technical analysis
            technical_analysis = self._calculate_comprehensive_technical_analysis(price_data)
            
            # Risk assessment
            risk_analysis = self._assess_comprehensive_risk(price_data, sentiment_data)
            
            # Generate enhanced signal
            signal = self._generate_enhanced_signal(
                symbol, price_data, prediction_result, 
                sentiment_data, technical_analysis, risk_analysis
            )
            
            logger.info(f"✅ Analysis complete for {symbol}: {signal.action} with {signal.confidence:.2f} confidence")
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return self._create_fallback_signal(symbol, price_data)
    
    def _simulate_sentiment_data(self, symbol: str) -> Dict:
        """Simulate comprehensive sentiment data"""
        return {
            'overall_sentiment': np.random.uniform(-0.3, 0.3),
            'fear_greed_index': np.random.randint(20, 80),
            'news_sentiment': np.random.uniform(-0.2, 0.2),
            'twitter_sentiment': np.random.uniform(-0.3, 0.3),
            'reddit_sentiment': np.random.uniform(-0.2, 0.2),
            'social_volume': np.random.randint(100, 1000),
            'news_articles': [
                {'title': f'{symbol} technical analysis shows bullish signals', 'sentiment': 0.2},
                {'title': f'Market outlook for {symbol} remains positive', 'sentiment': 0.1}
            ]
        }
    
    def _get_advanced_predictions(self, price_data: pd.DataFrame, sentiment_data: Dict) -> Dict:
        """Get predictions from advanced ML models"""
        try:
            # Train models if needed
            if not self.ensemble_predictor.is_trained:
                self.ensemble_predictor.train_ensemble(
                    price_data, sentiment_data, sentiment_data.get('news_articles', [])
                )
            
            # Get ensemble predictions
            return self.ensemble_predictor.predict_ensemble(
                price_data, sentiment_data, sentiment_data.get('news_articles', [])
            )
        except Exception as e:
            logger.warning(f"Advanced predictions failed: {e}")
            return self._get_fallback_predictions(price_data)
    
    def _get_fallback_predictions(self, price_data: pd.DataFrame) -> Dict:
        """Fallback predictions using simple models"""
        current_price = price_data['close'].iloc[-1]
        
        # Simple trend-following prediction
        sma_20 = price_data['close'].rolling(20).mean().iloc[-1]
        trend_prediction = current_price + (current_price - sma_20) * 0.1
        
        return {
            'ensemble_prediction': trend_prediction,
            'individual_predictions': {
                'trend_following': trend_prediction,
                'mean_reversion': (current_price + sma_20) / 2
            },
            'overall_confidence': 0.6,
            'models_used': ['trend_following', 'mean_reversion']
        }
    
    def _calculate_comprehensive_technical_analysis(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical analysis"""
        try:
            latest = df.iloc[-1]
            
            # Moving averages
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            sma_50 = df['close'].rolling(50).mean().iloc[-1]
            ema_12 = df['close'].ewm(span=12).mean().iloc[-1]
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            macd = (exp1 - exp2).iloc[-1]
            macd_signal = (exp1 - exp2).ewm(span=9).mean().iloc[-1]
            
            # Bollinger Bands
            bb_middle = df['close'].rolling(20).mean().iloc[-1]
            bb_std = df['close'].rolling(20).std().iloc[-1]
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_position = (latest['close'] - bb_lower) / (bb_upper - bb_lower)
            
            # Volume analysis
            volume_sma = df['volume'].rolling(20).mean().iloc[-1]
            volume_ratio = latest['volume'] / volume_sma
            
            # Technical score calculation
            technical_score = 0
            
            # Trend signals
            if latest['close'] > sma_20 > sma_50:
                technical_score += 25
            elif latest['close'] < sma_20 < sma_50:
                technical_score -= 25
            
            # RSI signals
            if rsi < 30:
                technical_score += 20  # Oversold
            elif rsi > 70:
                technical_score -= 20  # Overbought
            
            # MACD signals
            if macd > macd_signal:
                technical_score += 15
            else:
                technical_score -= 15
            
            # Volume confirmation
            if volume_ratio > 1.5:
                technical_score += 10
            
            # Bollinger Bands
            if bb_position < 0.2:
                technical_score += 15  # Near lower band
            elif bb_position > 0.8:
                technical_score -= 15  # Near upper band
            
            return {
                'technical_score': max(-100, min(100, technical_score)),
                'rsi': rsi,
                'macd': macd,
                'macd_signal': macd_signal,
                'bb_position': bb_position,
                'volume_ratio': volume_ratio,
                'trend_strength': abs((latest['close'] - df['close'].iloc[-20]) / df['close'].iloc[-20]),
                'price_above_sma20': latest['close'] > sma_20,
                'price_above_sma50': latest['close'] > sma_50
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return {'technical_score': 0}
    
    def _assess_comprehensive_risk(self, df: pd.DataFrame, sentiment_data: Dict) -> Dict:
        """Comprehensive risk assessment"""
        try:
            # Volatility risk
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Maximum drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # VaR (Value at Risk) - 95% confidence
            var_95 = np.percentile(returns, 5)
            
            # Sentiment risk
            sentiment_volatility = abs(sentiment_data.get('overall_sentiment', 0))
            fear_greed = sentiment_data.get('fear_greed_index', 50)
            
            # Market regime risk
            if fear_greed < 25 or fear_greed > 75:
                regime_risk = 0.3  # High risk in extreme conditions
            elif fear_greed < 40 or fear_greed > 60:
                regime_risk = 0.2  # Medium risk
            else:
                regime_risk = 0.1  # Low risk
            
            # Overall risk score (0-100)
            risk_score = (
                volatility * 30 +
                abs(max_drawdown) * 100 * 20 +
                abs(var_95) * 100 * 20 +
                sentiment_volatility * 100 * 15 +
                regime_risk * 100 * 15
            )
            
            return {
                'risk_score': min(100, risk_score),
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'var_95': var_95,
                'sentiment_risk': sentiment_volatility,
                'regime_risk': regime_risk
            }
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {'risk_score': 50}
    
    def _generate_enhanced_signal(self, symbol: str, df: pd.DataFrame, 
                                prediction_result: Dict, sentiment_data: Dict,
                                technical_analysis: Dict, risk_analysis: Dict) -> EnhancedTradingSignal:
        """Generate comprehensive trading signal"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Extract predictions
            ensemble_pred = prediction_result.get('ensemble_prediction', current_price)
            individual_preds = prediction_result.get('individual_predictions', {})
            overall_confidence = prediction_result.get('overall_confidence', 0.5)
            
            # Calculate expected return
            expected_return = (ensemble_pred - current_price) / current_price
            
            # Combine all signals
            technical_score = technical_analysis.get('technical_score', 0)
            sentiment_score = sentiment_data.get('overall_sentiment', 0) * 100
            
            # Overall signal strength
            signal_strength = (
                expected_return * 100 * 0.4 +  # Model prediction weight
                technical_score * 0.35 +       # Technical analysis weight
                sentiment_score * 0.25         # Sentiment weight
            )
            
            # Determine action
            if signal_strength > 25 and overall_confidence > self.min_confidence:
                action = 'BUY'
            elif signal_strength < -25 and overall_confidence > self.min_confidence:
                action = 'SELL'
            else:
                action = 'HOLD'
            
            # Position sizing based on confidence and risk
            risk_score = risk_analysis.get('risk_score', 50)
            position_size = self.max_position_size * overall_confidence * (1 - risk_score / 200)
            position_size = max(0.01, min(self.max_position_size, position_size))
            
            # Stop loss and take profit
            volatility = risk_analysis.get('volatility', 0.3)
            stop_loss_pct = max(self.stop_loss_pct, volatility * 0.5)
            take_profit_pct = max(self.take_profit_pct, volatility * 1.5)
            
            if action == 'BUY':
                stop_loss = current_price * (1 - stop_loss_pct)
                take_profit = current_price * (1 + take_profit_pct)
            elif action == 'SELL':
                stop_loss = current_price * (1 + stop_loss_pct)
                take_profit = current_price * (1 - take_profit_pct)
            else:
                stop_loss = current_price
                take_profit = current_price
            
            # Create detailed reasoning
            reasoning = f"""
🧠 ADVANCED ML ANALYSIS:
• Ensemble Prediction: ${ensemble_pred:.4f} (Expected Return: {expected_return:.2%})
• Model Confidence: {overall_confidence:.2f}
• Models Used: {', '.join(prediction_result.get('models_used', []))}

📊 TECHNICAL ANALYSIS:
• Technical Score: {technical_score:.1f}/100
• RSI: {technical_analysis.get('rsi', 0):.1f}
• MACD Signal: {'Bullish' if technical_analysis.get('macd', 0) > technical_analysis.get('macd_signal', 0) else 'Bearish'}
• Trend Strength: {technical_analysis.get('trend_strength', 0):.3f}
• Volume Ratio: {technical_analysis.get('volume_ratio', 1):.2f}x

💭 SENTIMENT ANALYSIS:
• Overall Sentiment: {sentiment_data.get('overall_sentiment', 0):.3f}
• Fear & Greed Index: {sentiment_data.get('fear_greed_index', 50)} ({'Extreme Fear' if sentiment_data.get('fear_greed_index', 50) < 25 else 'Extreme Greed' if sentiment_data.get('fear_greed_index', 50) > 75 else 'Neutral'})
• News Sentiment: {sentiment_data.get('news_sentiment', 0):.3f}
• Social Media Sentiment: {sentiment_data.get('twitter_sentiment', 0):.3f}

⚠️ RISK ASSESSMENT:
• Risk Score: {risk_score:.1f}/100
• Volatility: {risk_analysis.get('volatility', 0):.2%} (annualized)
• Max Drawdown Risk: {abs(risk_analysis.get('max_drawdown', 0)):.2%}
• VaR (95%): {abs(risk_analysis.get('var_95', 0)):.2%}

🎯 SIGNAL SUMMARY:
• Signal Strength: {signal_strength:.1f}
• Action Recommended: {action}
• Position Size: {position_size:.2%} of portfolio
            """.strip()
            
            return EnhancedTradingSignal(
                symbol=symbol,
                action=action,
                confidence=overall_confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                
                # Model predictions
                lstm_prediction=individual_preds.get('lstm', 0),
                transformer_prediction=individual_preds.get('transformer', 0),
                arima_prediction=individual_preds.get('arima_garch', 0),
                ensemble_prediction=ensemble_pred,
                
                # Sentiment
                overall_sentiment=sentiment_data.get('overall_sentiment', 0),
                twitter_sentiment=sentiment_data.get('twitter_sentiment', 0),
                news_sentiment=sentiment_data.get('news_sentiment', 0),
                fear_greed_index=sentiment_data.get('fear_greed_index', 50),
                
                # Technical
                technical_score=technical_score,
                volatility_forecast=risk_analysis.get('volatility', 0),
                trend_strength=technical_analysis.get('trend_strength', 0),
                
                # Risk
                risk_score=risk_score,
                max_drawdown_risk=abs(risk_analysis.get('max_drawdown', 0)),
                
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return self._create_fallback_signal(symbol, df)
    
    def _create_fallback_signal(self, symbol: str, df: pd.DataFrame) -> EnhancedTradingSignal:
        """Create fallback signal when analysis fails"""
        current_price = df['close'].iloc[-1]
        
        return EnhancedTradingSignal(
            symbol=symbol,
            action='HOLD',
            confidence=0.0,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit=current_price,
            position_size=0.0,
            reasoning="⚠️ Analysis failed - using fallback signal"
        )
    
    def execute_enhanced_strategy(self, symbols: List[str], 
                                market_data: Dict[str, pd.DataFrame]) -> List[EnhancedTradingSignal]:
        """Execute comprehensive trading strategy"""
        signals = []
        
        try:
            logger.info(f"🎯 Executing enhanced trading strategy for {len(symbols)} symbols")
            
            for symbol in symbols:
                if symbol in market_data and not market_data[symbol].empty:
                    signal = self.analyze_symbol_comprehensive(symbol, market_data[symbol])
                    signals.append(signal)
            
            # Sort by confidence
            signals.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"✅ Generated {len(signals)} enhanced trading signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error executing trading strategy: {e}")
            return signals
    
    def print_signal_summary(self, signal: EnhancedTradingSignal):
        """Print a comprehensive signal summary"""
        print(f"\n{'='*60}")
        print(f"🎯 ENHANCED TRADING SIGNAL: {signal.symbol}")
        print(f"{'='*60}")
        print(f"📈 ACTION: {signal.action}")
        print(f"🎲 CONFIDENCE: {signal.confidence:.2%}")
        print(f"💰 ENTRY PRICE: ${signal.entry_price:.4f}")
        print(f"🛑 STOP LOSS: ${signal.stop_loss:.4f} ({((signal.stop_loss/signal.entry_price-1)*100):+.1f}%)")
        print(f"🎯 TAKE PROFIT: ${signal.take_profit:.4f} ({((signal.take_profit/signal.entry_price-1)*100):+.1f}%)")
        print(f"📊 POSITION SIZE: {signal.position_size:.2%}")
        print(f"⚠️ RISK SCORE: {signal.risk_score:.1f}/100")
        
        print(f"\n🤖 MODEL PREDICTIONS:")
        if signal.lstm_prediction != 0:
            print(f"   LSTM: ${signal.lstm_prediction:.4f}")
        if signal.transformer_prediction != 0:
            print(f"   Transformer: ${signal.transformer_prediction:.4f}")
        if signal.arima_prediction != 0:
            print(f"   ARIMA-GARCH: ${signal.arima_prediction:.4f}")
        print(f"   Ensemble: ${signal.ensemble_prediction:.4f}")
        
        print(f"\n💭 SENTIMENT ANALYSIS:")
        print(f"   Overall: {signal.overall_sentiment:+.3f}")
        print(f"   Fear & Greed: {signal.fear_greed_index}/100")
        print(f"   News: {signal.news_sentiment:+.3f}")
        print(f"   Social: {signal.twitter_sentiment:+.3f}")
        
        print(f"\n📊 TECHNICAL INDICATORS:")
        print(f"   Technical Score: {signal.technical_score:.1f}/100")
        print(f"   Trend Strength: {signal.trend_strength:.3f}")
        print(f"   Volatility: {signal.volatility_forecast:.2%}")
        
        print(f"\n📝 DETAILED REASONING:")
        print(signal.reasoning)
        print(f"{'='*60}")

# Example usage
def main():
    """Example usage of the enhanced trading system"""
    
    # Initialize system
    trading_system = EnhancedTradingSystem(initial_capital=10000)
    
    # Sample data
    np.random.seed(42)  # For reproducible results
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=1000, freq='1H'),
        'open': np.random.randn(1000).cumsum() + 50000,
        'high': np.random.randn(1000).cumsum() + 50100,
        'low': np.random.randn(1000).cumsum() + 49900,
        'close': np.random.randn(1000).cumsum() + 50000,
        'volume': np.random.randint(1000, 10000, 1000)
    })
    
    # Ensure high > low and proper OHLC relationships
    sample_data['high'] = np.maximum(sample_data[['open', 'close']].max(axis=1), sample_data['high'])
    sample_data['low'] = np.minimum(sample_data[['open', 'close']].min(axis=1), sample_data['low'])
    
    # Analyze symbols
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    market_data = {symbol: sample_data.copy() for symbol in symbols}
    
    # Execute strategy
    signals = trading_system.execute_enhanced_strategy(symbols, market_data)
    
    # Display results
    for signal in signals[:2]:  # Show top 2 signals
        trading_system.print_signal_summary(signal)

if __name__ == "__main__":
    main() 