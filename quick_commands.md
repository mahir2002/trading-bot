# 🚀 AI Trading Bot - Quick Commands

## Basic Usage
```bash
# Run the main trading bot (continuous)
python ai_trading_bot_simple.py

# Quick strategy analysis (one-time)
python integrate_strategies.py

# Start web API server
python start_api.py

# Start trading charts
python start_charts.py
```

## Testing & Setup
```bash
# Test Binance connection
python test_binance_connection.py

# Test Telegram notifications
python direct_telegram_test.py

# Test bot functionality
python test_bot_functionality.py
```

## Web Interfaces
- **API Dashboard**: http://localhost:5001
- **Trading Charts**: http://localhost:8050

## Current Settings
- **Mode**: Paper Trading (Safe)
- **Exchange**: Binance Testnet
- **Notifications**: Telegram ✅
- **Pairs**: BTC/USDT, ETH/USDT

## Safety Notes
- Currently in **PAPER TRADING** mode (no real money)
- All trades are simulated with testnet funds
- Change `BINANCE_TESTNET=false` for live trading
- Always test thoroughly before going live

## Controls
- **Stop Bot**: Press Ctrl+C
- **View Logs**: Check terminal output
- **Get Alerts**: Check Telegram messages 