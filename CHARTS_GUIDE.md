# 📊 TradingView-like Charts & Analysis Guide

## Overview

This AI Trading Bot now includes a comprehensive TradingView-like charting system that provides professional-grade technical analysis tools, interactive charts, and performance analytics. The system is built using Plotly and Dash for maximum interactivity and visual appeal.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install plotly dash ta kaleido pandas numpy ccxt
```

### 2. Start the Interactive Dashboard
```bash
python start_charts.py
```
Then open http://localhost:8050 in your browser.

### 3. Generate Example Charts
```bash
python chart_examples.py
```
This creates sample charts in the `charts/` directory.

## 📈 Features

### Interactive Candlestick Charts
- **Professional candlestick visualization** with green/red color coding
- **Trade overlays** showing buy/sell points with profit/loss information
- **Multiple timeframes**: 1m, 5m, 15m, 30m, 1h, 4h, 1d
- **Zoom and pan** functionality for detailed analysis
- **Dark theme** similar to TradingView

### Technical Indicators

#### Moving Averages
- **SMA (Simple Moving Average)**: 20, 50, 200 periods
- **EMA (Exponential Moving Average)**: 12, 26 periods
- Color-coded lines for easy identification

#### Trend Indicators
- **Bollinger Bands**: Upper, middle, lower bands with shaded area
- **MACD**: MACD line, signal line, and histogram
- **Support & Resistance**: Dynamic levels based on price action

#### Momentum Indicators
- **RSI (Relative Strength Index)**: 14-period with overbought/oversold levels
- **Stochastic Oscillator**: %K and %D lines

#### Volume Analysis
- **Volume bars** with color coding (green for up, red for down)
- **Volume SMA**: 20-period moving average
- **VWAP**: Volume Weighted Average Price

#### Advanced Tools
- **Fibonacci Retracements**: Automatic calculation of key levels
- **Support/Resistance Detection**: Dynamic level identification

### Performance Analytics

#### Portfolio Analysis
- **Cumulative P&L chart** showing portfolio growth over time
- **Individual trade P&L** with color-coded bars
- **Drawdown analysis** with maximum drawdown calculation
- **Performance metrics**: Total return, win rate, average win/loss

#### Trading Heatmap
- **Time-based performance analysis** by hour and day of week
- **Color-coded heatmap** showing profitable vs unprofitable periods
- **Optimal trading time identification**

#### Market Overview
- **Multi-symbol dashboard** with synchronized timeframes
- **Real-time price monitoring** for multiple cryptocurrencies
- **Comparative analysis** across different assets

## 🎮 Interactive Dashboard

### Control Panel
- **Symbol Selection**: Choose from BTC/USDT, ETH/USDT, ADA/USDT, SOL/USDT, DOGE/USDT
- **Timeframe Selection**: Switch between different chart timeframes
- **Indicator Toggle**: Enable/disable specific technical indicators
- **Auto-refresh**: Real-time data updates every 30 seconds
- **Manual Refresh**: Update charts on demand

### Tab Navigation
1. **Price Chart**: Main candlestick chart with indicators and trade overlays
2. **Performance Analysis**: Portfolio performance and trade analytics
3. **Trading Heatmap**: Time-based performance analysis
4. **Market Overview**: Multi-symbol market dashboard

### Statistics Cards
- **Current Price**: Real-time price display
- **24h Change**: Price change percentage with color coding
- **Total Trades**: Number of executed trades
- **Win Rate**: Percentage of profitable trades

## 🔧 Integration with Trading Bot

### Basic Usage
```python
from trading_charts import TradingViewChart, TradeAnnotation
from datetime import datetime

# Initialize charting system
chart = TradingViewChart()

# Create trade annotation
trade = TradeAnnotation(
    timestamp=datetime.now(),
    price=45000.0,
    side='buy',
    amount=0.001,
    profit_loss=50.0,
    symbol='BTC/USDT',
    trade_id='trade_1'
)

# Generate chart with indicators
fig = chart.create_candlestick_chart(
    symbol='BTC/USDT',
    timeframe='1h',
    indicators=['sma_20', 'sma_50', 'bollinger_bands', 'rsi', 'volume'],
    trades=[trade]
)

# Save chart
chart.save_chart_as_html(fig, 'my_chart.html')
```

### Advanced Integration
```python
# Load trades from your trading bot
trades = chart.load_trades_from_file('logs/trades.json')

# Create performance analysis
performance_fig = chart.create_performance_chart(trades, initial_balance=10000)

# Create trading heatmap
heatmap_fig = chart.create_heatmap_analysis(trades)

# Generate market overview
overview_fig = chart.get_market_overview(['BTC/USDT', 'ETH/USDT', 'ADA/USDT'])
```

## 📊 Chart Types & Examples

### 1. Basic Candlestick Chart
```python
fig = chart.create_candlestick_chart(
    'BTC/USDT',
    timeframe='1h',
    indicators=['sma_20', 'sma_50']
)
```

### 2. Advanced Technical Analysis
```python
fig = chart.create_candlestick_chart(
    'BTC/USDT',
    timeframe='1h',
    indicators=[
        'sma_20', 'sma_50', 'sma_200',
        'bollinger_bands', 'rsi', 'macd',
        'support_resistance', 'fibonacci'
    ]
)
```

### 3. Volume Analysis
```python
fig = chart.create_candlestick_chart(
    'BTC/USDT',
    timeframe='1h',
    indicators=['volume', 'volume_sma', 'vwap']
)
```

### 4. Performance Tracking
```python
# Analyze trading performance
performance_fig = chart.create_performance_chart(trades)

# Time-based analysis
heatmap_fig = chart.create_heatmap_analysis(trades)
```

## 🎨 Customization Options

### Indicator Configuration
```python
# Custom indicator combinations
scalping_indicators = ['ema_12', 'ema_26', 'rsi', 'volume']
swing_indicators = ['sma_20', 'sma_50', 'bollinger_bands', 'macd']
position_indicators = ['sma_50', 'sma_200', 'support_resistance']
```

### Chart Styling
- **Dark theme** (TradingView-like) by default
- **Color-coded elements**: Green for bullish, red for bearish
- **Professional typography** and spacing
- **Responsive design** for different screen sizes

### Export Options
```python
# Save as interactive HTML
chart.save_chart_as_html(fig, 'chart.html')

# Charts can also be exported as PNG, PDF, SVG using Plotly's built-in features
```

## 📁 File Structure

```
charts/                     # Generated chart files
├── btc_basic_chart.html    # Basic BTC analysis
├── btc_advanced_chart.html # Advanced BTC analysis
├── performance_analysis.html # Trading performance
├── trading_heatmap.html    # Time-based analysis
└── market_overview.html    # Multi-symbol overview

logs/
└── trades.json            # Trading data storage

trading_charts.py          # Core charting library
chart_dashboard.py         # Interactive web dashboard
chart_examples.py          # Example usage and demos
start_charts.py           # Dashboard startup script
```

## 🔍 Technical Indicators Explained

### Moving Averages
- **SMA 20**: Short-term trend (20 periods)
- **SMA 50**: Medium-term trend (50 periods)
- **SMA 200**: Long-term trend (200 periods)
- **EMA 12/26**: Fast/slow exponential moving averages for MACD

### Oscillators
- **RSI**: Momentum oscillator (0-100 scale)
  - Above 70: Overbought
  - Below 30: Oversold
- **Stochastic**: Momentum indicator comparing closing price to price range

### Trend Indicators
- **Bollinger Bands**: Volatility bands around moving average
- **MACD**: Trend-following momentum indicator
- **Support/Resistance**: Key price levels

### Volume Indicators
- **Volume Bars**: Trading volume with directional color coding
- **Volume SMA**: Smoothed volume trend
- **VWAP**: Volume-weighted average price

## 🎯 Trading Strategies

### Scalping (1m-5m charts)
```python
scalping_chart = chart.create_candlestick_chart(
    'BTC/USDT',
    timeframe='1m',
    indicators=['ema_12', 'ema_26', 'rsi', 'volume']
)
```

### Day Trading (15m-1h charts)
```python
day_trading_chart = chart.create_candlestick_chart(
    'BTC/USDT',
    timeframe='15m',
    indicators=['sma_20', 'bollinger_bands', 'rsi', 'macd']
)
```

### Swing Trading (4h-1d charts)
```python
swing_trading_chart = chart.create_candlestick_chart(
    'BTC/USDT',
    timeframe='4h',
    indicators=['sma_50', 'sma_200', 'support_resistance', 'fibonacci']
)
```

## 🚨 Troubleshooting

### Common Issues

1. **Charts not loading**
   - Check if all dependencies are installed
   - Ensure port 8050 is available
   - Verify file permissions

2. **No data displayed**
   - Check internet connection
   - Verify exchange API configuration
   - System will use demo data if exchange is unavailable

3. **Indicators not showing**
   - Ensure sufficient data points (minimum 200 candles recommended)
   - Check indicator names in the indicators list

4. **Performance issues**
   - Reduce the number of indicators
   - Use shorter timeframes for faster loading
   - Clear browser cache

### Error Messages
- **"Invalid Api-Key ID"**: Exchange API not configured (demo data will be used)
- **"Module not found"**: Install missing dependencies with pip
- **"Port already in use"**: Change port in dashboard configuration

## 🔮 Advanced Features

### Real-time Updates
The dashboard automatically refreshes every 30 seconds when auto-refresh is enabled.

### Data Caching
The system caches market data for 1 minute to improve performance and reduce API calls.

### Multi-timeframe Analysis
Compare the same symbol across different timeframes for comprehensive analysis.

### Trade Overlay
Visualize your actual trades on the charts with profit/loss information.

### Export Capabilities
Save charts as interactive HTML files for sharing and documentation.

## 📚 API Reference

### TradingViewChart Class
```python
class TradingViewChart:
    def __init__(self, exchange_id='binance')
    def fetch_ohlcv_data(symbol, timeframe, limit, start_date=None)
    def calculate_technical_indicators(df)
    def create_candlestick_chart(symbol, timeframe, indicators, trades)
    def create_performance_chart(trades, initial_balance)
    def create_heatmap_analysis(trades)
    def get_market_overview(symbols)
    def save_chart_as_html(fig, filename)
```

### TradeAnnotation Class
```python
@dataclass
class TradeAnnotation:
    timestamp: datetime
    price: float
    side: str  # 'buy' or 'sell'
    amount: float
    profit_loss: float = 0.0
    symbol: str = ""
    trade_id: str = ""
```

## 🎉 Conclusion

This TradingView-like charting system provides professional-grade technical analysis tools for your AI trading bot. With interactive charts, comprehensive indicators, and performance analytics, you can:

- **Analyze market trends** with professional charting tools
- **Monitor trading performance** with detailed analytics
- **Identify optimal trading times** using heatmap analysis
- **Track multiple cryptocurrencies** simultaneously
- **Export and share** your analysis

The system is designed to be both powerful for advanced users and accessible for beginners, with extensive documentation and examples to get you started quickly.

Happy trading! 📈🚀 