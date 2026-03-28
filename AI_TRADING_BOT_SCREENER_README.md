# 🤖 AI Trading Bot + Crypto Screener

A comprehensive AI-powered cryptocurrency trading bot with an integrated crypto screener, similar to DexScreener, featuring real-time market analysis, technical indicators, and automated trading signals.

## 🎯 Features

### 🤖 AI Trading Capabilities
- **Random Forest AI Model** for price prediction
- **Real-time trading signals** with confidence scores
- **Risk management** with position sizing
- **Telegram notifications** for all trades
- **Automated trading cycles** every 60 seconds
- **Model retraining** capabilities

### 📊 Crypto Screener (60+ Coins)
- **Major Cryptocurrencies**: BTC, ETH, BNB, XRP, ADA, SOL, DOT, AVAX, MATIC, LINK
- **DeFi Tokens**: UNI, AAVE, COMP, MKR, SUSHI, CRV, 1INCH, YFI
- **Memecoins**: DOGE, SHIB, PEPE, FLOKI, BONK, WIF
- **Gaming & NFT**: AXS, SAND, MANA, ENJ, GALA
- **AI & Data**: FET, OCEAN, AGIX, RENDER
- **Layer 1 & 2**: NEAR, ATOM, ALGO, FTM, OP, ARB

### 📈 Professional Interface
- **TradingView-style charts** with candlesticks
- **Technical indicators**: EMA 20/50, RSI, MACD
- **Multiple timeframes**: 1m, 5m, 15m, 1h, 4h, 1d
- **Real-time price updates** every 5-10 seconds
- **Dark theme** with professional styling
- **Interactive market table** with sorting
- **Live trading status** monitoring

## 🚀 Quick Start

### 1. Start the System
```bash
# Option 1: Direct start
python ai_trading_bot_with_screener.py

# Option 2: Using launcher
python start_ai_trading_bot.py
```

### 2. Access Dashboard
Open your browser and go to: **http://localhost:8056**

### 3. Features Available
- **Left Sidebar**: Market overview, AI trading status, controls
- **Main Area**: Interactive charts, timeframe selection
- **Market Table**: All 60+ cryptocurrencies with live data
- **Real-time Updates**: Automatic refresh every 5-10 seconds

## 📊 Dashboard Overview

### Market Overview Cards
- Top 5 cryptocurrencies with live prices
- 24-hour price changes with color coding
- Click any card to view its chart

### AI Trading Status
- Current trading status (Running/Stopped)
- Number of active positions
- AI model training status
- Last update timestamp

### Interactive Controls
- **Start Trading**: Begin AI trading system
- **Stop Trading**: Halt all trading activities
- **Retrain AI**: Retrain the AI model with latest data

### Professional Charts
- **Candlestick charts** with TradingView styling
- **Technical indicators**: Moving averages, RSI
- **Multiple timeframes** with easy switching
- **Real-time updates** every 5 seconds

### Comprehensive Market Table
- **60+ cryptocurrencies** organized by category
- **Live prices** with 4 decimal precision
- **24-hour changes** with color coding (green/red)
- **Volume data** and category classification
- **Sortable columns** for easy analysis

## 🔧 Configuration

### Environment Variables (.env file)
```bash
# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Exchange API Keys (for live trading)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key

# Risk Management
MAX_POSITION_SIZE=0.1
DAILY_LOSS_LIMIT=0.05
MIN_CONFIDENCE_THRESHOLD=70
```

### Supported Exchanges
- **Binance** (Primary)
- **Binance Testnet** (For testing)
- Easily extensible to other exchanges

## 🧠 AI Trading Logic

### Signal Generation
1. **Data Collection**: Fetch OHLCV data for analysis
2. **Feature Engineering**: Calculate technical indicators
3. **AI Prediction**: Use Random Forest for price direction
4. **Signal Generation**: Buy/Sell/Hold based on confidence
5. **Risk Assessment**: Position sizing and risk checks
6. **Execution**: Place orders (simulated by default)

### Technical Indicators Used
- **SMA 20**: Simple Moving Average
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Price Action**: Change ratios and momentum

### Risk Management
- **Confidence Threshold**: Only trade signals >70% confidence
- **Position Sizing**: Dynamic based on account balance
- **Daily Limits**: Maximum trades and loss limits
- **Stop Losses**: Automatic risk management

## 📱 Telegram Integration

### Setup Telegram Notifications
1. Create a Telegram bot via @BotFather
2. Get your bot token
3. Get your chat ID
4. Add to your .env file

### Notification Types
- **Trade Alerts**: Buy/sell signals with details
- **AI Status**: Model training and system status
- **Risk Alerts**: Position limits and warnings

## 🎨 Interface Features

### Professional Styling
- **Dark Theme**: Easy on the eyes for long trading sessions
- **TradingView Colors**: Green/red candlesticks, professional palette
- **Responsive Design**: Works on desktop and mobile
- **Smooth Animations**: Real-time updates without flickering

### User Experience
- **One-Click Symbol Selection**: Click market cards to switch charts
- **Timeframe Buttons**: Easy switching between 1m to 1d
- **Live Indicators**: Real-time status updates
- **Color-Coded Data**: Green for gains, red for losses

## 📈 Market Categories

### Major Cryptocurrencies (10 coins)
Bitcoin, Ethereum, BNB, XRP, Cardano, Solana, Polkadot, Avalanche, Polygon, Chainlink

### DeFi Tokens (8 coins)
Uniswap, Aave, Compound, Maker, SushiSwap, Curve, 1inch, Yearn Finance

### Memecoins (6 coins)
Dogecoin, Shiba Inu, Pepe, Floki, Bonk, Dogwifhat

### Gaming & NFT (5 coins)
Axie Infinity, Sandbox, Decentraland, Enjin, Gala

### AI & Data (4 coins)
Fetch.ai, Ocean Protocol, SingularityNET, Render

### Layer 1 & 2 (6 coins)
NEAR Protocol, Cosmos, Algorand, Fantom, Optimism, Arbitrum

## 🔄 Real-Time Updates

### Update Frequencies
- **Market Data**: Every 10 seconds
- **Charts**: Every 5 seconds
- **AI Analysis**: Every 60 seconds
- **Trading Signals**: As generated

### Data Sources
- **Binance API**: Primary data source
- **Real-time WebSocket**: For live price feeds
- **Historical Data**: For AI training and backtesting

## 🛡️ Security & Safety

### Paper Trading Mode
- **Simulated Trading**: No real money at risk
- **Full Functionality**: All features work in simulation
- **Safe Testing**: Test strategies without financial risk

### Risk Controls
- **Position Limits**: Maximum position sizes
- **Daily Limits**: Trading frequency controls
- **Confidence Thresholds**: Only high-confidence trades
- **Stop Losses**: Automatic risk management

## 🚀 Advanced Features

### AI Model Management
- **Automatic Retraining**: Periodic model updates
- **Performance Monitoring**: Track prediction accuracy
- **Feature Engineering**: Advanced technical indicators
- **Backtesting**: Historical performance analysis

### Extensibility
- **Plugin Architecture**: Easy to add new features
- **Custom Indicators**: Add your own technical analysis
- **Multiple Exchanges**: Support for various trading platforms
- **API Integration**: Connect to external services

## 📊 Performance Monitoring

### Trading Metrics
- **Win Rate**: Percentage of profitable trades
- **Average Return**: Mean profit per trade
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest loss period

### System Metrics
- **Uptime**: System availability
- **Response Time**: API and UI performance
- **Error Rates**: System reliability
- **Resource Usage**: CPU and memory monitoring

## 🔧 Troubleshooting

### Common Issues
1. **Port Already in Use**: Change port in the code
2. **API Errors**: Check internet connection and API keys
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Telegram Not Working**: Verify bot token and chat ID

### Support
- Check logs in the `logs/` directory
- Verify environment variables in `.env`
- Test API connections with test scripts
- Monitor system resources

## 📝 License

This project is for educational purposes. Use at your own risk when trading with real money.

## 🤝 Contributing

Feel free to submit issues, feature requests, and pull requests to improve the system.

---

**⚠️ Disclaimer**: This software is for educational purposes only. Cryptocurrency trading involves substantial risk of loss. Never trade with money you cannot afford to lose. 