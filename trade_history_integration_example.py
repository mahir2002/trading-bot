#!/usr/bin/env python3
"""
🔗 Trade History Integration Example
Shows how to integrate detailed trade history system with existing trading bots
for comprehensive trade tracking with entry/exit points, P&L, and reasoning.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Import our detailed trade history system
from detailed_trade_history_system import (
    DetailedTradeHistorySystem, TradingSignal, RiskMetrics, 
    TradeType, ExitReason, create_demo_detailed_trades
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    """Enhanced trading bot with detailed trade history integration"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_balance = initial_capital
        
        # Initialize detailed trade history system
        self.trade_history = DetailedTradeHistorySystem("enhanced_bot_trades.db")
        
        # Trading state
        self.open_positions = {}
        self.trading_active = True
        
        logger.info(f"🤖 Enhanced Trading Bot initialized with ${initial_capital:,.2f}")
    
    async def execute_buy_order(self, symbol: str, price: float, quantity: float,
                               strategy: str, reasoning: str, signal_data: Dict,
                               risk_data: Dict) -> Optional[str]:
        """Execute buy order with detailed tracking"""
        
        try:
            # Create trading signal
            signal = TradingSignal(
                signal_type=signal_data.get('type', 'unknown'),
                confidence=signal_data.get('confidence', 0.0),
                strength=signal_data.get('strength', 0.0),
                indicators=signal_data.get('indicators', {}),
                ai_prediction=signal_data.get('ai_prediction'),
                technical_score=signal_data.get('technical_score')
            )
            
            # Create risk metrics
            risk_metrics = RiskMetrics(
                position_size_pct=risk_data.get('position_size_pct', 1.0),
                risk_reward_ratio=risk_data.get('risk_reward_ratio', 1.0),
                max_risk_amount=risk_data.get('max_risk_amount', 100.0),
                volatility=risk_data.get('volatility', 0.02),
                correlation_risk=risk_data.get('correlation_risk', 0.0),
                portfolio_heat=risk_data.get('portfolio_heat', 0.0)
            )
            
            # Calculate stop loss and take profit
            stop_loss = price * 0.95  # 5% stop loss
            take_profit = price * 1.08  # 8% take profit
            
            # Market context
            market_context = {
                'timestamp': datetime.now().isoformat(),
                'market_conditions': signal_data.get('market_conditions', {}),
                'volatility': risk_data.get('volatility', 0.02),
                'volume': signal_data.get('volume', 0),
                'spread': signal_data.get('spread', 0)
            }
            
            # Create detailed trade record
            trade_id = self.trade_history.create_trade(
                symbol=symbol,
                side='buy',
                entry_price=price,
                quantity=quantity,
                strategy=strategy,
                reasoning=reasoning,
                signal=signal,
                risk_metrics=risk_metrics,
                stop_loss=stop_loss,
                take_profit=take_profit,
                order_type=TradeType.MARKET,
                market_context=market_context
            )
            
            # Update bot state
            self.open_positions[trade_id] = {
                'symbol': symbol,
                'side': 'buy',
                'entry_price': price,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'entry_time': datetime.now()
            }
            
            # Update balance (simulate)
            trade_value = price * quantity
            commission = trade_value * 0.001  # 0.1% commission
            self.current_balance -= (trade_value + commission)
            
            logger.info(f"✅ BUY ORDER EXECUTED: {trade_id}")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Price: ${price:.4f}")
            logger.info(f"   Quantity: {quantity:.6f}")
            logger.info(f"   Strategy: {strategy}")
            logger.info(f"   Confidence: {signal.confidence:.2%}")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"❌ Buy order failed: {e}")
            return None
    
    async def execute_sell_order(self, trade_id: str, exit_price: float, 
                                exit_reason: ExitReason, notes: str = "") -> bool:
        """Execute sell order with detailed tracking"""
        
        try:
            if trade_id not in self.open_positions:
                logger.warning(f"⚠️ Trade {trade_id} not found in open positions")
                return False
            
            position = self.open_positions[trade_id]
            
            # Close the detailed trade record
            success = self.trade_history.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                exit_reason=exit_reason,
                notes=notes
            )
            
            if success:
                # Calculate P&L
                entry_price = position['entry_price']
                quantity = position['quantity']
                
                if position['side'] == 'buy':
                    pnl = (exit_price - entry_price) * quantity
                else:
                    pnl = (entry_price - exit_price) * quantity
                
                # Update balance (simulate)
                trade_value = exit_price * quantity
                commission = trade_value * 0.001  # 0.1% commission
                self.current_balance += (trade_value - commission)
                
                # Remove from open positions
                del self.open_positions[trade_id]
                
                logger.info(f"✅ SELL ORDER EXECUTED: {trade_id}")
                logger.info(f"   Exit Price: ${exit_price:.4f}")
                logger.info(f"   P&L: ${pnl:+.2f}")
                logger.info(f"   Exit Reason: {exit_reason.value}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Sell order failed: {e}")
            return False
    
    async def monitor_positions(self):
        """Monitor open positions for stop loss/take profit"""
        
        while self.trading_active:
            try:
                for trade_id, position in list(self.open_positions.items()):
                    # Simulate current price (in real implementation, get from exchange)
                    current_price = position['entry_price'] * (1 + (hash(trade_id) % 21 - 10) / 1000)
                    
                    # Check stop loss
                    if current_price <= position['stop_loss']:
                        await self.execute_sell_order(
                            trade_id=trade_id,
                            exit_price=current_price,
                            exit_reason=ExitReason.STOP_LOSS,
                            notes="Stop loss triggered by price movement"
                        )
                    
                    # Check take profit
                    elif current_price >= position['take_profit']:
                        await self.execute_sell_order(
                            trade_id=trade_id,
                            exit_price=current_price,
                            exit_reason=ExitReason.TAKE_PROFIT,
                            notes="Take profit target reached"
                        )
                    
                    # Check time-based exit (example: 1 hour max holding)
                    elif datetime.now() - position['entry_time'] > timedelta(hours=1):
                        await self.execute_sell_order(
                            trade_id=trade_id,
                            exit_price=current_price,
                            exit_reason=ExitReason.TIME_LIMIT,
                            notes="Maximum holding period reached"
                        )
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Position monitoring error: {e}")
                await asyncio.sleep(30)
    
    def generate_trading_signal(self, symbol: str) -> Dict:
        """Generate trading signal with detailed analysis"""
        
        import random
        
        # Simulate technical analysis
        rsi = random.uniform(30, 70)
        macd = random.uniform(-0.5, 0.5)
        bb_position = random.uniform(0, 1)
        volume_ratio = random.uniform(0.5, 3.0)
        
        # Simulate AI prediction
        ai_prediction = random.uniform(0.3, 0.9)
        
        # Calculate confidence based on indicators
        confidence = 0.5
        if 40 < rsi < 60:  # Neutral RSI
            confidence += 0.1
        if abs(macd) > 0.1:  # Strong MACD
            confidence += 0.2
        if volume_ratio > 1.5:  # High volume
            confidence += 0.1
        if ai_prediction > 0.7:  # Strong AI signal
            confidence += 0.2
        
        # Generate reasoning
        reasoning_parts = []
        
        if ai_prediction > 0.7:
            reasoning_parts.append(f"Strong AI prediction signal ({ai_prediction:.2%})")
        
        if rsi < 40:
            reasoning_parts.append(f"RSI oversold at {rsi:.1f}")
        elif rsi > 60:
            reasoning_parts.append(f"RSI momentum at {rsi:.1f}")
        
        if macd > 0.1:
            reasoning_parts.append("MACD bullish crossover")
        elif macd < -0.1:
            reasoning_parts.append("MACD bearish signal")
        
        if volume_ratio > 2.0:
            reasoning_parts.append("High volume confirmation")
        
        reasoning = ". ".join(reasoning_parts) + "."
        
        return {
            'signal': 'buy' if ai_prediction > 0.6 else 'hold',
            'confidence': confidence,
            'reasoning': reasoning,
            'signal_data': {
                'type': 'ai_technical_combo',
                'confidence': confidence,
                'strength': ai_prediction,
                'indicators': {
                    'rsi': rsi,
                    'macd': macd,
                    'bb_position': bb_position,
                    'volume_ratio': volume_ratio
                },
                'ai_prediction': ai_prediction,
                'technical_score': (rsi/100 + (macd+1)/2 + bb_position) / 3
            },
            'risk_data': {
                'position_size_pct': min(confidence * 5, 3.0),  # Max 3% position
                'risk_reward_ratio': 1.6,
                'max_risk_amount': 200.0,
                'volatility': random.uniform(0.02, 0.06),
                'portfolio_heat': len(self.open_positions) * 2.5
            }
        }
    
    async def run_trading_session(self, duration_minutes: int = 60):
        """Run automated trading session with detailed tracking"""
        
        logger.info(f"🚀 Starting {duration_minutes}-minute trading session")
        
        # Start position monitoring
        monitor_task = asyncio.create_task(self.monitor_positions())
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT']
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        try:
            while datetime.now() < end_time and self.trading_active:
                for symbol in symbols:
                    # Generate trading signal
                    signal_analysis = self.generate_trading_signal(symbol)
                    
                    if signal_analysis['signal'] == 'buy' and signal_analysis['confidence'] > 0.7:
                        # Simulate current price
                        base_price = 45000 if 'BTC' in symbol else 3000
                        current_price = base_price * (1 + random.uniform(-0.05, 0.05))
                        
                        # Calculate position size
                        max_position_value = self.current_balance * 0.1  # Max 10% per trade
                        quantity = min(max_position_value / current_price, 0.01)
                        
                        if quantity > 0.001:  # Minimum trade size
                            await self.execute_buy_order(
                                symbol=symbol,
                                price=current_price,
                                quantity=quantity,
                                strategy='ai_technical_combo',
                                reasoning=signal_analysis['reasoning'],
                                signal_data=signal_analysis['signal_data'],
                                risk_data=signal_analysis['risk_data']
                            )
                
                await asyncio.sleep(30)  # Check every 30 seconds
        
        except KeyboardInterrupt:
            logger.info("🛑 Trading session interrupted by user")
        
        finally:
            # Stop monitoring and close remaining positions
            self.trading_active = False
            monitor_task.cancel()
            
            # Close any remaining positions
            for trade_id in list(self.open_positions.keys()):
                position = self.open_positions[trade_id]
                current_price = position['entry_price'] * 1.01  # Simulate small profit
                
                await self.execute_sell_order(
                    trade_id=trade_id,
                    exit_price=current_price,
                    exit_reason=ExitReason.MARKET_CLOSE,
                    notes="Session ended - closing all positions"
                )
            
            logger.info("✅ Trading session completed")
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        
        # Get detailed statistics from trade history system
        stats = self.trade_history.get_trade_statistics()
        
        # Calculate additional metrics
        total_return = (self.current_balance - self.initial_capital) / self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'current_balance': self.current_balance,
            'total_return': total_return,
            'total_trades': stats['total_trades'],
            'open_trades': stats['open_trades'],
            'win_rate': stats['win_rate'],
            'total_pnl': stats['total_pnl'],
            'profit_factor': stats['profit_factor'],
            'best_trade': stats['best_trade'],
            'worst_trade': stats['worst_trade'],
            'avg_holding_time': stats['avg_holding_time_hours'],
            'strategy_breakdown': stats['strategy_breakdown'],
            'exit_reasons': stats['exit_reasons']
        }
    
    def create_performance_report(self):
        """Create comprehensive performance report"""
        
        summary = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 ENHANCED TRADING BOT PERFORMANCE REPORT")
        print("="*60)
        
        print(f"\n💰 FINANCIAL SUMMARY:")
        print(f"   Initial Capital: ${summary['initial_capital']:,.2f}")
        print(f"   Current Balance: ${summary['current_balance']:,.2f}")
        print(f"   Total Return: {summary['total_return']:+.2%}")
        print(f"   Total P&L: ${summary['total_pnl']:+.2f}")
        
        print(f"\n📈 TRADING STATISTICS:")
        print(f"   Total Trades: {summary['total_trades']}")
        print(f"   Open Trades: {summary['open_trades']}")
        print(f"   Win Rate: {summary['win_rate']:.2%}")
        print(f"   Profit Factor: {summary['profit_factor']:.2f}")
        print(f"   Avg Holding Time: {summary['avg_holding_time']:.1f} hours")
        
        if summary['best_trade']:
            print(f"\n🏆 BEST TRADE:")
            print(f"   Trade ID: {summary['best_trade']['id']}")
            print(f"   P&L: ${summary['best_trade']['pnl']:+.2f}")
            print(f"   Symbol: {summary['best_trade']['symbol']}")
            print(f"   Strategy: {summary['best_trade']['strategy']}")
        
        if summary['worst_trade']:
            print(f"\n📉 WORST TRADE:")
            print(f"   Trade ID: {summary['worst_trade']['id']}")
            print(f"   P&L: ${summary['worst_trade']['pnl']:+.2f}")
            print(f"   Symbol: {summary['worst_trade']['symbol']}")
            print(f"   Strategy: {summary['worst_trade']['strategy']}")
        
        print(f"\n🎯 STRATEGY BREAKDOWN:")
        for strategy, data in summary['strategy_breakdown'].items():
            print(f"   {strategy.replace('_', ' ').title()}:")
            print(f"     Trades: {data['count']}")
            print(f"     Win Rate: {data['win_rate']:.2%}")
            print(f"     Total P&L: ${data['pnl']:+.2f}")
        
        print(f"\n🚪 EXIT ANALYSIS:")
        for reason, data in summary['exit_reasons'].items():
            avg_pnl = data['pnl'] / data['count'] if data['count'] > 0 else 0
            print(f"   {reason.replace('_', ' ').title()}:")
            print(f"     Count: {data['count']}")
            print(f"     Avg P&L: ${avg_pnl:+.2f}")
        
        print("\n" + "="*60)
    
    def export_detailed_history(self):
        """Export detailed trade history"""
        
        # Export trade data
        csv_file = self.trade_history.export_trade_history('csv', 'enhanced_bot_trades.csv')
        json_file = self.trade_history.export_trade_history('json', 'enhanced_bot_trades.json')
        
        # Create visualizations
        history_fig = self.trade_history.create_trade_history_visualization()
        history_fig.write_html("enhanced_bot_performance.html")
        
        table_fig = self.trade_history.create_detailed_trade_table()
        table_fig.write_html("enhanced_bot_trade_table.html")
        
        print(f"\n📁 EXPORTED FILES:")
        print(f"   • {csv_file}")
        print(f"   • {json_file}")
        print(f"   • enhanced_bot_performance.html")
        print(f"   • enhanced_bot_trade_table.html")

async def main():
    """Main demonstration function"""
    
    print("🤖 ENHANCED TRADING BOT WITH DETAILED TRADE HISTORY")
    print("="*70)
    
    # Initialize enhanced trading bot
    bot = EnhancedTradingBot(initial_capital=10000.0)
    
    # Run trading session
    print("\n🚀 Starting automated trading session...")
    await bot.run_trading_session(duration_minutes=5)  # 5-minute demo
    
    # Generate performance report
    bot.create_performance_report()
    
    # Export detailed history
    bot.export_detailed_history()
    
    print("\n✅ DEMO COMPLETED!")
    print("🌟 Enhanced trading bot with detailed trade history is ready!")

if __name__ == "__main__":
    import random
    random.seed(42)  # For reproducible demo
    
    # Run the demonstration
    asyncio.run(main()) 