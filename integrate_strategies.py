#!/usr/bin/env python3
"""
Integration Script for Advanced Trading Strategies
Connects the educational trading strategies with the existing AI trading bot
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional

# Import existing bot components
try:
    from ai_trading_bot_simple import AITradingBot
except ImportError:
    print("Warning: AITradingBot not available, using fallback")
    AITradingBot = None

try:
    from advanced_trading_strategies import AdvancedTradingStrategies, TradingSignal, RiskLevel
except ImportError as e:
    print(f"Error: Cannot import advanced strategies: {e}")
    sys.exit(1)

# Optional imports
try:
    from utils import calculate_technical_indicators, calculate_performance_metrics
except ImportError:
    print("Warning: utils module not fully available, using basic functionality")
    calculate_technical_indicators = None
    calculate_performance_metrics = None

class IntegratedTradingBot:
    """
    Enhanced AI Trading Bot with Advanced Strategies
    Combines the existing bot with educational trading strategies
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        if AITradingBot:
            self.ai_bot = AITradingBot()
        else:
            self.ai_bot = None
        self.strategies = AdvancedTradingStrategies(logger=self.logger)
        
        # Trading state
        self.portfolio_value = self.config.get('portfolio_value', 10000)
        self.daily_loss = 0.0
        self.open_positions = []
        self.trade_history = []
        
        # Strategy preferences
        self.enabled_strategies = self.config.get('enabled_strategies', [
            'moving_average_crossover',
            'rsi_oversold_overbought',
            'scalping',
            'memecoin_momentum'
        ])
        
        # Risk management
        self.max_daily_loss = self.config.get('max_daily_loss', 0.05)  # 5%
        self.max_positions = self.config.get('max_positions', 5)
        
    def get_market_data(self, symbols: List[str], timeframe: str = '1h', 
                       limit: int = 500) -> Dict[str, pd.DataFrame]:
        """
        Get market data for multiple symbols
        Uses the existing bot's data fetching capabilities
        """
        market_data = {}
        
        for symbol in symbols:
            try:
                # Use existing bot's data fetching method
                if self.ai_bot and hasattr(self.ai_bot, 'get_historical_data'):
                    df = self.ai_bot.get_historical_data(symbol, timeframe, limit)
                else:
                    # Fallback to demo data
                    df = self._create_demo_data(symbol, limit)
                
                if df is not None and len(df) > 0:
                    market_data[symbol] = df
                    
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {e}")
                # Create demo data as fallback
                market_data[symbol] = self._create_demo_data(symbol, limit)
        
        return market_data
    
    def _create_demo_data(self, symbol: str, periods: int = 500) -> pd.DataFrame:
        """Create demo market data for testing"""
        import random
        
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        
        # Different base prices for different assets
        if 'BTC' in symbol.upper():
            base_price = 45000
            volatility = 0.02
        elif 'ETH' in symbol.upper():
            base_price = 2800
            volatility = 0.03
        elif any(meme in symbol.lower() for meme in ['doge', 'shib', 'pepe']):
            base_price = 0.1
            volatility = 0.08
        else:
            base_price = 100
            volatility = 0.04
        
        prices = []
        volumes = []
        current_price = base_price
        
        for _ in range(periods):
            change = random.uniform(-volatility, volatility)
            current_price *= (1 + change)
            prices.append(current_price)
            volumes.append(random.uniform(1000, 50000))
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * random.uniform(1.0, 1.02) for p in prices],
            'low': [p * random.uniform(0.98, 1.0) for p in prices],
            'close': prices,
            'volume': volumes
        })
        
        return df
    
    def analyze_signals(self, symbols: List[str]) -> List[TradingSignal]:
        """
        Analyze trading signals using advanced strategies
        """
        # Get market data
        market_data = self.get_market_data(symbols)
        
        if not market_data:
            self.logger.warning("No market data available")
            return []
        
        # Generate signals using advanced strategies
        signals = self.strategies.get_trading_signals(
            market_data=market_data,
            portfolio_value=self.portfolio_value,
            daily_loss=self.daily_loss
        )
        
        # Filter signals based on enabled strategies
        filtered_signals = []
        for signal in signals:
            if signal.strategy.value in self.enabled_strategies:
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def execute_signal(self, signal: TradingSignal, dry_run: bool = True) -> Dict:
        """
        Execute a trading signal
        """
        result = {
            'success': False,
            'signal': signal,
            'message': '',
            'trade_id': None
        }
        
        try:
            # Calculate position size
            position_size = self._calculate_position_size(signal)
            
            if position_size <= 0:
                result['message'] = "Position size too small or risk limits exceeded"
                return result
            
            # Check if we can open new position
            if len(self.open_positions) >= self.max_positions:
                result['message'] = "Maximum positions limit reached"
                return result
            
            if dry_run:
                # Simulate trade execution
                trade_data = {
                    'trade_id': f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'symbol': signal.symbol,
                    'action': signal.action,
                    'quantity': position_size / signal.entry_price,
                    'price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit,
                    'strategy': signal.strategy.value,
                    'confidence': signal.confidence,
                    'risk_level': signal.risk_level.value,
                    'timestamp': datetime.now(),
                    'status': 'simulated'
                }
                
                result['success'] = True
                result['trade_id'] = trade_data['trade_id']
                result['message'] = f"Simulated {signal.action} order for {signal.symbol}"
                
                # Add to trade history
                self.trade_history.append(trade_data)
                
                if signal.action == 'buy':
                    self.open_positions.append(trade_data)
                
            else:
                # Real trade execution would go here
                # This would integrate with your exchange API
                result['message'] = "Real trading not implemented - use dry_run=True"
            
        except Exception as e:
            result['message'] = f"Error executing signal: {e}"
            self.logger.error(f"Error executing signal: {e}")
        
        return result
    
    def _calculate_position_size(self, signal: TradingSignal) -> float:
        """Calculate position size based on risk parameters"""
        risk_params = self.strategies.risk_params[signal.risk_level]
        
        # Base position size
        base_size = self.portfolio_value * risk_params.max_position_size
        
        # Adjust for confidence
        adjusted_size = base_size * signal.confidence
        
        # Ensure minimum position
        min_size = self.portfolio_value * 0.001  # 0.1% minimum
        
        return max(adjusted_size, min_size)
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_trades = len(self.trade_history)
        open_trades = len(self.open_positions)
        
        # Calculate basic stats
        if self.trade_history:
            strategies_used = list(set(trade['strategy'] for trade in self.trade_history))
            risk_levels = list(set(trade['risk_level'] for trade in self.trade_history))
        else:
            strategies_used = []
            risk_levels = []
        
        return {
            'portfolio_value': self.portfolio_value,
            'daily_loss': self.daily_loss,
            'total_trades': total_trades,
            'open_positions': open_trades,
            'max_positions': self.max_positions,
            'strategies_used': strategies_used,
            'risk_levels_traded': risk_levels,
            'enabled_strategies': self.enabled_strategies
        }
    
    def run_analysis(self, symbols: List[str], execute_trades: bool = False) -> Dict:
        """
        Run complete trading analysis
        """
        self.logger.info(f"Running analysis for {len(symbols)} symbols")
        
        # Analyze signals
        signals = self.analyze_signals(symbols)
        
        results = {
            'timestamp': datetime.now(),
            'symbols_analyzed': symbols,
            'signals_generated': len(signals),
            'signals': [],
            'executed_trades': [],
            'portfolio_summary': self.get_portfolio_summary()
        }
        
        # Process signals
        for signal in signals:
            signal_data = {
                'symbol': signal.symbol,
                'action': signal.action,
                'confidence': signal.confidence,
                'strategy': signal.strategy.value,
                'risk_level': signal.risk_level.value,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'reasoning': signal.reasoning
            }
            results['signals'].append(signal_data)
            
            # Execute if requested
            if execute_trades:
                execution_result = self.execute_signal(signal, dry_run=True)
                results['executed_trades'].append(execution_result)
        
        return results

def main():
    """Main function to demonstrate the integrated trading bot"""
    print("🤖 Integrated AI Trading Bot with Advanced Strategies")
    print("=" * 60)
    
    # Configuration
    config = {
        'portfolio_value': 10000,
        'max_daily_loss': 0.05,
        'max_positions': 5,
        'enabled_strategies': [
            'moving_average_crossover',
            'rsi_oversold_overbought',
            'scalping',
            'memecoin_momentum'
        ]
    }
    
    # Initialize integrated bot
    bot = IntegratedTradingBot(config)
    
    # Test symbols (mix of different risk levels)
    test_symbols = [
        'BTC/USDT',    # Low risk
        'ETH/USDT',    # Low risk
        'ADA/USDT',    # Medium risk
        'SOL/USDT',    # Medium risk
        'DOGE/USDT',   # Extreme risk (memecoin)
        'SHIB/USDT'    # Extreme risk (memecoin)
    ]
    
    # Run analysis
    results = bot.run_analysis(test_symbols, execute_trades=True)
    
    # Display results
    print(f"\n📊 Analysis Results:")
    print(f"Symbols Analyzed: {len(results['symbols_analyzed'])}")
    print(f"Signals Generated: {results['signals_generated']}")
    print(f"Trades Executed: {len(results['executed_trades'])}")
    
    print(f"\n💼 Portfolio Summary:")
    portfolio = results['portfolio_summary']
    print(f"Portfolio Value: ${portfolio['portfolio_value']:,.2f}")
    print(f"Open Positions: {portfolio['open_positions']}/{portfolio['max_positions']}")
    print(f"Total Trades: {portfolio['total_trades']}")
    print(f"Strategies Used: {', '.join(portfolio['strategies_used'])}")
    
    if results['signals']:
        print(f"\n🎯 Top Trading Signals:")
        print("-" * 40)
        
        for i, signal in enumerate(results['signals'][:5], 1):
            risk_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'extreme': '🔴'
            }
            
            print(f"{i}. {signal['symbol']}: {signal['action'].upper()} {risk_emoji.get(signal['risk_level'], '⚪')}")
            print(f"   Strategy: {signal['strategy']}")
            print(f"   Confidence: {signal['confidence']:.1%}")
            print(f"   Risk: {signal['risk_level']}")
            print(f"   Entry: ${signal['entry_price']:.4f}")
            if signal['stop_loss']:
                print(f"   Stop Loss: ${signal['stop_loss']:.4f}")
            if signal['take_profit']:
                print(f"   Take Profit: ${signal['take_profit']:.4f}")
            print(f"   Reasoning: {signal['reasoning']}")
            print()
    
    if results['executed_trades']:
        print(f"\n💰 Executed Trades:")
        print("-" * 40)
        
        for trade in results['executed_trades']:
            if trade['success']:
                print(f"✅ {trade['trade_id']}: {trade['message']}")
            else:
                print(f"❌ Failed: {trade['message']}")
    
    print(f"\n⚠️  EDUCATIONAL DISCLAIMER:")
    print("This implementation is based on the educational trading document.")
    print("All trades shown are simulated. Never invest more than you can afford to lose!")
    print("Memecoins carry extreme risk and are highly speculative!")

if __name__ == "__main__":
    main() 