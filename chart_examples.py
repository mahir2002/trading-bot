#!/usr/bin/env python3
"""
AI Trading Bot - TradingView Charts Examples
Demonstrates all charting features and generates sample charts
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_charts import TradingViewChart, TradeAnnotation

def create_sample_trades():
    """Create comprehensive sample trades for demonstration"""
    trades = []
    
    # Generate realistic trading data over 60 days
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
    base_prices = {'BTC/USDT': 45000, 'ETH/USDT': 3000, 'ADA/USDT': 0.5, 'SOL/USDT': 100}
    
    for i in range(200):
        symbol = symbols[i % len(symbols)]
        timestamp = datetime.now() - timedelta(days=60) + timedelta(hours=i*7.2)
        
        # Simulate realistic price movements
        base_price = base_prices[symbol]
        trend = 1 + (i * 0.001)  # Slight upward trend
        volatility = 1 + ((-1)**i * 0.05)  # 5% volatility
        price = base_price * trend * volatility
        
        # Alternate between buy and sell with some randomness
        side = 'buy' if (i + hash(symbol)) % 3 != 0 else 'sell'
        
        # Simulate profit/loss based on market conditions
        if side == 'sell':
            profit_loss = (i % 20) * 10 - 50  # -50 to +150
        else:
            profit_loss = -(i % 15) * 5  # Small losses on buys
        
        trade = TradeAnnotation(
            timestamp=timestamp,
            price=round(price, 2),
            side=side,
            amount=round(0.001 + (i * 0.0001), 6),
            profit_loss=round(profit_loss, 2),
            symbol=symbol,
            trade_id=f'trade_{i+1}'
        )
        trades.append(trade)
    
    return trades

def save_trades_to_file(trades, filename='logs/trades.json'):
    """Save trades to JSON file"""
    Path(filename).parent.mkdir(exist_ok=True)
    
    trades_data = []
    for trade in trades:
        trades_data.append({
            'id': trade.trade_id,
            'timestamp': trade.timestamp.isoformat(),
            'symbol': trade.symbol,
            'side': trade.side,
            'price': trade.price,
            'amount': trade.amount,
            'profit_loss': trade.profit_loss
        })
    
    with open(filename, 'w') as f:
        json.dump(trades_data, f, indent=2)
    
    print(f"✅ Saved {len(trades)} trades to {filename}")

def generate_all_charts():
    """Generate all types of charts with different configurations"""
    
    # Create charts directory
    Path('charts').mkdir(exist_ok=True)
    
    # Initialize charting system
    chart = TradingViewChart()
    
    # Create sample trades
    print("📊 Creating sample trading data...")
    trades = create_sample_trades()
    save_trades_to_file(trades)
    
    print("\n🎨 Generating TradingView-like charts...")
    
    # 1. Basic candlestick chart with moving averages
    print("1. Basic Candlestick Chart with Moving Averages...")
    btc_trades = [t for t in trades if t.symbol == 'BTC/USDT']
    fig1 = chart.create_candlestick_chart(
        'BTC/USDT',
        timeframe='1h',
        indicators=['sma_20', 'sma_50'],
        trades=btc_trades[:10]  # Show first 10 trades
    )
    chart.save_chart_as_html(fig1, 'charts/btc_basic_chart.html')
    
    # 2. Advanced chart with all indicators
    print("2. Advanced Chart with All Indicators...")
    fig2 = chart.create_candlestick_chart(
        'BTC/USDT',
        timeframe='1h',
        indicators=[
            'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26',
            'bollinger_bands', 'support_resistance', 'fibonacci',
            'volume', 'rsi', 'macd', 'stoch_k', 'stoch_d'
        ],
        trades=btc_trades
    )
    chart.save_chart_as_html(fig2, 'charts/btc_advanced_chart.html')
    
    # 3. ETH chart with Bollinger Bands and RSI
    print("3. ETH Chart with Bollinger Bands and RSI...")
    eth_trades = [t for t in trades if t.symbol == 'ETH/USDT']
    fig3 = chart.create_candlestick_chart(
        'ETH/USDT',
        timeframe='4h',
        indicators=['sma_20', 'bollinger_bands', 'volume', 'rsi'],
        trades=eth_trades
    )
    chart.save_chart_as_html(fig3, 'charts/eth_bollinger_rsi.html')
    
    # 4. ADA chart with MACD and Stochastic
    print("4. ADA Chart with MACD and Stochastic...")
    ada_trades = [t for t in trades if t.symbol == 'ADA/USDT']
    fig4 = chart.create_candlestick_chart(
        'ADA/USDT',
        timeframe='1d',
        indicators=['ema_12', 'ema_26', 'macd', 'stoch_k', 'stoch_d', 'volume'],
        trades=ada_trades
    )
    chart.save_chart_as_html(fig4, 'charts/ada_macd_stoch.html')
    
    # 5. SOL chart with Support/Resistance and Fibonacci
    print("5. SOL Chart with Support/Resistance and Fibonacci...")
    sol_trades = [t for t in trades if t.symbol == 'SOL/USDT']
    fig5 = chart.create_candlestick_chart(
        'SOL/USDT',
        timeframe='1h',
        indicators=['sma_50', 'support_resistance', 'fibonacci', 'volume'],
        trades=sol_trades
    )
    chart.save_chart_as_html(fig5, 'charts/sol_support_fib.html')
    
    # 6. Performance analysis chart
    print("6. Trading Performance Analysis...")
    fig6 = chart.create_performance_chart(trades, initial_balance=10000)
    chart.save_chart_as_html(fig6, 'charts/performance_analysis.html')
    
    # 7. Trading heatmap
    print("7. Trading Performance Heatmap...")
    fig7 = chart.create_heatmap_analysis(trades)
    chart.save_chart_as_html(fig7, 'charts/trading_heatmap.html')
    
    # 8. Market overview
    print("8. Market Overview Dashboard...")
    fig8 = chart.get_market_overview(['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT'])
    chart.save_chart_as_html(fig8, 'charts/market_overview.html')
    
    # 9. Different timeframes comparison
    print("9. BTC Multiple Timeframes...")
    timeframes = ['1m', '15m', '1h', '4h']
    for tf in timeframes:
        fig = chart.create_candlestick_chart(
            'BTC/USDT',
            timeframe=tf,
            indicators=['sma_20', 'sma_50', 'volume', 'rsi'],
            trades=btc_trades[:5]
        )
        chart.save_chart_as_html(fig, f'charts/btc_{tf}_chart.html')
    
    print("\n✅ All charts generated successfully!")
    print("\n📁 Generated Charts:")
    print("   • charts/btc_basic_chart.html - Basic BTC chart with moving averages")
    print("   • charts/btc_advanced_chart.html - Advanced BTC chart with all indicators")
    print("   • charts/eth_bollinger_rsi.html - ETH with Bollinger Bands and RSI")
    print("   • charts/ada_macd_stoch.html - ADA with MACD and Stochastic")
    print("   • charts/sol_support_fib.html - SOL with Support/Resistance and Fibonacci")
    print("   • charts/performance_analysis.html - Trading performance analysis")
    print("   • charts/trading_heatmap.html - Trading performance heatmap")
    print("   • charts/market_overview.html - Multi-symbol market overview")
    print("   • charts/btc_*_chart.html - BTC charts in different timeframes")

def demonstrate_features():
    """Demonstrate key features of the charting system"""
    
    print("🎯 TradingView-like Charting Features Demo")
    print("=" * 50)
    
    chart = TradingViewChart()
    
    # Demonstrate data fetching
    print("\n📊 Data Fetching:")
    df = chart.fetch_ohlcv_data('BTC/USDT', '1h', 100)
    print(f"   • Fetched {len(df)} candles for BTC/USDT")
    print(f"   • Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    
    # Demonstrate technical indicators
    print("\n🔧 Technical Indicators:")
    indicators = chart.calculate_technical_indicators(df)
    print(f"   • Calculated {len(indicators)} indicators")
    print("   • Available indicators:")
    for indicator in indicators.keys():
        if hasattr(indicators[indicator], '__len__') and len(indicators[indicator]) > 0:
            if isinstance(indicators[indicator], dict):
                print(f"     - {indicator}: {len(indicators[indicator])} levels")
            else:
                print(f"     - {indicator}: Latest value = {indicators[indicator].iloc[-1]:.2f}")
    
    # Demonstrate chart types
    print("\n📈 Chart Types:")
    print("   • Candlestick Charts with Trade Overlays")
    print("   • Performance Analysis (P&L, Drawdown)")
    print("   • Trading Heatmaps (Time-based Analysis)")
    print("   • Market Overview (Multi-symbol)")
    
    # Demonstrate supported symbols
    print("\n💰 Supported Symbols:")
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'DOGE/USDT']
    for symbol in symbols:
        print(f"   • {symbol}")
    
    # Demonstrate timeframes
    print("\n⏰ Supported Timeframes:")
    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    for tf in timeframes:
        print(f"   • {tf}")
    
    print("\n🎮 Interactive Features:")
    print("   • Real-time data updates")
    print("   • Zoom and pan functionality")
    print("   • Indicator toggle on/off")
    print("   • Export to HTML")
    print("   • Responsive design")
    print("   • Dark theme (TradingView-like)")

def main():
    """Main function"""
    print("🚀 AI Trading Bot - TradingView Charts Examples")
    print("=" * 50)
    
    try:
        # Demonstrate features
        demonstrate_features()
        
        # Generate all example charts
        print("\n" + "=" * 50)
        generate_all_charts()
        
        print("\n" + "=" * 50)
        print("🎉 Examples completed successfully!")
        print("\n📖 Next Steps:")
        print("1. Open the generated HTML files in your browser")
        print("2. Run 'python start_charts.py' for the interactive dashboard")
        print("3. Run 'python chart_dashboard.py' directly")
        print("4. Integrate with your trading bot using the TradingViewChart class")
        
        print("\n💡 Usage Tips:")
        print("• Use different timeframes for different analysis types")
        print("• Combine multiple indicators for better insights")
        print("• Monitor the heatmap to find optimal trading times")
        print("• Use performance analysis to track your strategy")
        print("• Export charts for reports and documentation")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all dependencies are installed")
        print("2. Check if trading_charts.py exists")
        print("3. Ensure you have write permissions")
        print("4. Try running: pip install -r requirements.txt")

if __name__ == '__main__':
    main() 