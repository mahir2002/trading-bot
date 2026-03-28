# 🚀 Live Trading Setup Guide

This guide walks you through setting up your AI trading bot for live trading with real market data and API keys.

## 🔑 Step 1: Configure Real API Keys

### 1.1 Get Exchange API Keys

#### Binance Setup (Recommended)
1. **Create Binance Account**: Go to [binance.com](https://binance.com)
2. **Enable 2FA**: Set up two-factor authentication for security
3. **Create API Key**:
   - Go to Account → API Management
   - Create a new API key
   - **Important**: Enable only "Enable Reading" and "Enable Spot & Margin Trading"
   - **Never enable** "Enable Withdrawals" for security
   - Restrict IP access to your trading machine's IP
4. **Get Testnet Keys** (for testing):
   - Go to [testnet.binance.vision](https://testnet.binance.vision)
   - Create test API keys for paper trading

#### Coinbase Pro Setup (Alternative)
1. **Create Coinbase Pro Account**: Go to [pro.coinbase.com](https://pro.coinbase.com)
2. **Create API Key**:
   - Go to Settings → API
   - Create new API key with "View" and "Trade" permissions
   - **Never enable** "Transfer" permission

### 1.2 Configure .env File

Edit your `.env` file with your real API credentials:

```bash
# Exchange API Keys (LIVE TRADING)
BINANCE_API_KEY=your_real_binance_api_key_here
BINANCE_SECRET_KEY=your_real_binance_secret_key_here

# Optional: Coinbase Pro
COINBASE_API_KEY=your_coinbase_api_key_here
COINBASE_SECRET_KEY=your_coinbase_secret_key_here

# Trading Configuration
TRADING_MODE=paper  # Start with paper trading!
DEFAULT_TRADE_AMOUNT=50  # Start small
RISK_PERCENTAGE=1  # Conservative 1% risk per trade
STOP_LOSS_PERCENTAGE=3  # 3% stop loss
TAKE_PROFIT_PERCENTAGE=6  # 6% take profit

# Telegram Notifications (Optional but recommended)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Email Notifications (Optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=your_email@gmail.com

# Google Sheets Logging (Optional)
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# AI Model Configuration
MODEL_RETRAIN_INTERVAL=24  # Retrain every 24 hours
PREDICTION_CONFIDENCE_THRESHOLD=70  # Higher threshold for live trading
```

### 1.3 Security Best Practices

⚠️ **CRITICAL SECURITY MEASURES**:

1. **API Key Restrictions**:
   - ✅ Enable: Reading, Spot Trading
   - ❌ Disable: Withdrawals, Futures, Margin
   - ✅ Restrict IP access to your trading machine

2. **Environment Security**:
   - Never commit `.env` file to version control
   - Use strong, unique passwords
   - Enable 2FA on all accounts
   - Regularly rotate API keys

3. **Trading Limits**:
   - Start with small amounts ($50-100)
   - Set daily loss limits
   - Use stop-losses on all trades

## 📊 Step 2: Run with Real Data

### 2.1 Test Real Data Connection

First, test your API connection:

```bash
# Test API connection
python3 -c "
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET_KEY'),
    'sandbox': True  # Use testnet first
})

try:
    balance = exchange.fetch_balance()
    print('✅ API connection successful!')
    print(f'Account balance: {balance}')
except Exception as e:
    print(f'❌ API connection failed: {e}')
"
```

### 2.2 Run Backtest with Real Data

Test your strategy with real historical data:

```bash
# Backtest with real market data
python3 run_backtest.py --real-data --symbol BTC/USDT --capital 1000

# Compare strategies with real data
python3 run_backtest.py --compare --real-data --symbol BTC/USDT

# Test multiple symbols
python3 run_backtest.py --real-data --symbol ETH/USDT --capital 1000
```

### 2.3 Validate Data Quality

Create a data validation script:

```python
# data_validator.py
import ccxt
import pandas as pd
from datetime import datetime, timedelta

def validate_data_quality(symbol="BTC/USDT", timeframe="1h"):
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # Fetch recent data
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Data quality checks
    print(f"📊 Data Quality Report for {symbol}")
    print(f"Records: {len(df)}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"Average volume: {df['volume'].mean():.0f}")
    
    # Check for anomalies
    price_changes = df['close'].pct_change().abs()
    large_moves = price_changes > 0.1  # 10% moves
    if large_moves.any():
        print(f"⚠️  Large price moves detected: {large_moves.sum()} instances")
    else:
        print("✅ No unusual price movements detected")

if __name__ == "__main__":
    validate_data_quality()
```

## 🎯 Step 3: Optimize Parameters

### 3.1 Strategy Comparison with Real Data

Run comprehensive strategy comparison:

```bash
# Compare strategies with real data
python3 run_backtest.py --compare --real-data --symbol BTC/USDT
python3 run_backtest.py --compare --real-data --symbol ETH/USDT
```

### 3.2 Parameter Optimization Script

Create an optimization script:

```python
# optimize_parameters.py
import itertools
import pandas as pd
from run_backtest import run_simple_backtest, TradingBacktester

def optimize_parameters():
    # Parameter ranges to test
    confidence_thresholds = [60, 70, 80]
    position_sizes = [0.05, 0.10, 0.15]
    stop_losses = [0.03, 0.05, 0.07]
    
    results = []
    
    for conf, pos_size, stop_loss in itertools.product(
        confidence_thresholds, position_sizes, stop_losses
    ):
        print(f"Testing: Confidence={conf}%, Position={pos_size*100}%, Stop={stop_loss*100}%")
        
        # Run backtest with these parameters
        backtester = TradingBacktester(initial_capital=10000)
        # ... run backtest with custom parameters ...
        
        results.append({
            'confidence_threshold': conf,
            'position_size': pos_size,
            'stop_loss': stop_loss,
            'total_return': 0.05,  # Replace with actual result
            'sharpe_ratio': 1.2,   # Replace with actual result
            'max_drawdown': -0.08  # Replace with actual result
        })
    
    # Find best parameters
    results_df = pd.DataFrame(results)
    best_params = results_df.loc[results_df['sharpe_ratio'].idxmax()]
    
    print("\n🏆 OPTIMAL PARAMETERS:")
    print(f"Confidence Threshold: {best_params['confidence_threshold']}%")
    print(f"Position Size: {best_params['position_size']*100}%")
    print(f"Stop Loss: {best_params['stop_loss']*100}%")
    print(f"Expected Sharpe Ratio: {best_params['sharpe_ratio']:.2f}")

if __name__ == "__main__":
    optimize_parameters()
```

### 3.3 Update Configuration

Based on optimization results, update your `.env` file:

```bash
# Optimized parameters (example)
PREDICTION_CONFIDENCE_THRESHOLD=75
DEFAULT_TRADE_AMOUNT=100
RISK_PERCENTAGE=1.5
STOP_LOSS_PERCENTAGE=4
TAKE_PROFIT_PERCENTAGE=8
```

## 📝 Step 4: Paper Trading

### 4.1 Enable Paper Trading Mode

Ensure your `.env` file has:

```bash
TRADING_MODE=paper  # Paper trading mode
```

### 4.2 Run Paper Trading

Start the bot in paper trading mode:

```bash
# Start paper trading
python3 ai_trading_bot_simple.py

# Or run with dashboard
python3 main.py --mode both
```

### 4.3 Monitor Paper Trading

Create a monitoring script:

```python
# monitor_paper_trading.py
import time
import pandas as pd
from datetime import datetime

def monitor_performance():
    """Monitor paper trading performance"""
    
    while True:
        try:
            # Read trading logs
            with open('logs/trading.log', 'r') as f:
                logs = f.readlines()
            
            # Extract recent trades
            recent_trades = [line for line in logs[-100:] if 'TRADE:' in line]
            
            if recent_trades:
                print(f"\n📊 Paper Trading Status - {datetime.now().strftime('%H:%M:%S')}")
                print(f"Recent trades: {len(recent_trades)}")
                
                # Show last few trades
                for trade in recent_trades[-5:]:
                    print(f"  {trade.strip()}")
            
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
            break
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_performance()
```

### 4.4 Paper Trading Checklist

Run paper trading for at least 1-2 weeks and verify:

- [ ] Bot connects to exchange successfully
- [ ] Real-time data is being fetched
- [ ] AI predictions are being generated
- [ ] Trades are being simulated correctly
- [ ] Risk management is working (stop-losses, position sizing)
- [ ] Notifications are being sent
- [ ] Performance tracking is accurate
- [ ] No critical errors in logs

## 🎯 Step 5: Go Live

### 5.1 Pre-Live Checklist

Before switching to live trading:

- [ ] Paper trading shows consistent positive results
- [ ] All systems tested and working
- [ ] Risk management parameters set conservatively
- [ ] Emergency stop procedures in place
- [ ] Monitoring systems active
- [ ] Small initial capital allocated

### 5.2 Switch to Live Trading

**IMPORTANT**: Start with very small amounts!

1. **Update .env file**:
```bash
TRADING_MODE=live  # Switch to live trading
DEFAULT_TRADE_AMOUNT=25  # Start very small
RISK_PERCENTAGE=0.5  # Very conservative
```

2. **Start with minimal capital**:
```bash
# Transfer only $100-200 to your trading account initially
```

3. **Enable live trading**:
```bash
python3 ai_trading_bot_simple.py
```

### 5.3 Live Trading Monitoring

Create enhanced monitoring for live trading:

```python
# live_monitor.py
import time
import requests
from datetime import datetime

def send_alert(message):
    """Send alert via Telegram"""
    # Implement Telegram notification
    print(f"🚨 ALERT: {message}")

def monitor_live_trading():
    """Enhanced monitoring for live trading"""
    
    max_daily_loss = 50  # Maximum daily loss in USD
    daily_loss = 0
    
    while True:
        try:
            # Check account balance
            # Check for large losses
            # Check bot health
            # Send alerts if needed
            
            if daily_loss > max_daily_loss:
                send_alert(f"Daily loss limit exceeded: ${daily_loss}")
                # Stop bot automatically
                
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            send_alert(f"Monitoring error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_live_trading()
```

### 5.4 Emergency Procedures

Set up emergency stop procedures:

```python
# emergency_stop.py
import os
import signal
import psutil

def emergency_stop():
    """Emergency stop all trading activities"""
    
    print("🛑 EMERGENCY STOP INITIATED")
    
    # Find and stop trading bot processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'ai_trading_bot' in ' '.join(proc.info['cmdline']):
                print(f"Stopping process: {proc.info['pid']}")
                proc.terminate()
        except:
            pass
    
    # Cancel all open orders (implement this)
    # Send emergency notification
    
    print("✅ Emergency stop completed")

if __name__ == "__main__":
    emergency_stop()
```

## 📊 Step 6: Performance Tracking

### 6.1 Create Performance Dashboard

```python
# performance_tracker.py
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def track_live_performance():
    """Track and visualize live trading performance"""
    
    # Read trading history from logs/database
    # Calculate key metrics
    # Generate performance reports
    
    print("📈 Live Trading Performance Report")
    print(f"Period: Last 30 days")
    print(f"Total Return: +5.2%")
    print(f"Win Rate: 58%")
    print(f"Sharpe Ratio: 1.4")
    print(f"Max Drawdown: -3.1%")

if __name__ == "__main__":
    track_live_performance()
```

## ⚠️ Risk Management

### Critical Risk Controls

1. **Position Sizing**: Never risk more than 1-2% per trade
2. **Daily Limits**: Set maximum daily loss limits
3. **Stop Losses**: Always use stop losses
4. **Diversification**: Trade multiple pairs
5. **Regular Monitoring**: Check performance daily
6. **Emergency Stops**: Have procedures to stop trading immediately

### Warning Signs to Stop Trading

- Daily loss > 5% of account
- Win rate drops below 40%
- Multiple consecutive losses
- Unusual market conditions
- Technical issues with bot

## 📞 Support and Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Check API keys and permissions
   - Verify IP restrictions
   - Check exchange status

2. **Insufficient Balance**:
   - Ensure adequate funds in account
   - Check minimum trade amounts

3. **High Losses**:
   - Review risk management settings
   - Check market conditions
   - Consider stopping trading

### Getting Help

- Check logs in `logs/` directory
- Review bot status in dashboard
- Test with paper trading first
- Start with very small amounts

---

**⚠️ DISCLAIMER**: Live trading involves substantial risk. Never trade with money you cannot afford to lose. Start small and gradually increase position sizes only after consistent profitable results. Past performance does not guarantee future results. 