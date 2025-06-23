# 🔑 Ultimate Trading System - API Keys Setup Guide

This guide will help you add your real API keys to the Ultimate All-in-One Trading System.

## 📋 Current Status

✅ **System Integration Complete**
- All API key loading implemented
- Configuration management active
- 10 exchanges supported
- 5 data sources integrated
- Telegram & Email notifications ready

⚠️ **API Keys Status**
- Currently using placeholder values
- System running in demo mode
- Real API keys needed for live trading

## 🔧 How to Add Your API Keys

### 1. Edit Configuration File

Open your `config.env.unified` file and replace the placeholder values with your real API keys:

```bash
# Edit the configuration file
nano config.env.unified
# or
code config.env.unified
```

### 2. Exchange API Keys

#### Binance (Primary Exchange)
```env
BINANCE_API_KEY=your_actual_binance_api_key_here
BINANCE_SECRET_KEY=your_actual_binance_secret_key_here
BINANCE_TESTNET=true  # Set to false for live trading
```

#### Coinbase Pro/Advanced Trade
```env
COINBASE_API_KEY=your_actual_coinbase_api_key_here
COINBASE_SECRET_KEY=your_actual_coinbase_secret_key_here
COINBASE_PASSPHRASE=your_actual_coinbase_passphrase_here
COINBASE_SANDBOX=true  # Set to false for live trading
```

#### Other Exchanges (Optional)
```env
# Kraken
KRAKEN_API_KEY=your_actual_kraken_api_key_here
KRAKEN_SECRET_KEY=your_actual_kraken_secret_key_here

# Bybit
BYBIT_API_KEY=your_actual_bybit_api_key_here
BYBIT_SECRET_KEY=your_actual_bybit_secret_key_here

# OKX
OKX_API_KEY=your_actual_okx_api_key_here
OKX_SECRET_KEY=your_actual_okx_secret_key_here
OKX_PASSPHRASE=your_actual_okx_passphrase_here
```

### 3. Data Source API Keys

#### CoinGecko (Recommended)
```env
COINGECKO_API_KEY=your_actual_coingecko_api_key_here
```

#### CoinMarketCap
```env
COINMARKETCAP_API_KEY=your_actual_coinmarketcap_api_key_here
```

### 4. Telegram Notifications

```env
TELEGRAM_BOT_TOKEN=your_actual_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_actual_telegram_chat_id_here
```

### 5. Email Notifications

```env
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here  # Use App Password, not regular password
```

## 🔐 How to Get API Keys

### Binance API Keys
1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create new API key
3. Enable "Spot & Margin Trading" (for trading)
4. Enable "Futures Trading" (optional)
5. Set IP restrictions for security
6. Copy API Key and Secret Key

### Coinbase API Keys
1. Go to [Coinbase Advanced Trade API](https://www.coinbase.com/settings/api)
2. Create new API key
3. Set permissions (view, trade)
4. Copy API Key, Secret, and Passphrase

### CoinGecko API Key
1. Go to [CoinGecko API](https://www.coingecko.com/en/api)
2. Sign up for free account
3. Get your API key from dashboard

### Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create new bot with `/newbot`
3. Get bot token
4. Start conversation with your bot
5. Get your chat ID from [this bot](https://t.me/userinfobot)

## 🧪 Testing Your API Keys

After adding your API keys, test them:

```bash
# Test all APIs
python test_api_keys.py

# Test only exchanges
python test_api_keys.py --exchanges

# Test only notifications
python test_api_keys.py --notifications
```

## 🚀 Restart System with Real API Keys

After adding your API keys:

```bash
# Stop current system
pkill -f ultimate_all_in_one_trading_system.py

# Start with real API keys
python ultimate_all_in_one_trading_system.py web
```

## 🛡️ Security Best Practices

### API Key Permissions
- **Binance**: Enable only "Spot Trading" initially
- **Never enable withdrawals** for trading bots
- Use **testnet/sandbox** first
- Set **IP restrictions** when possible

### File Security
- Keep `config.env.unified` private
- Never commit API keys to version control
- Use environment variables in production
- Regularly rotate API keys

### Trading Safety
- Start with **paper trading** (`ENABLE_PAPER_TRADING=true`)
- Use **small position sizes** initially
- Set **strict risk limits**
- Monitor system closely

## 📊 Expected Results After Setup

### With Valid API Keys
```
📊 SUMMARY:
   • Total APIs Tested: 21
   • Active APIs: 15-20
   • Success Rate: 75-95%
   • System Status: 🟢 EXCELLENT
```

### System Capabilities
- ✅ Real-time market data
- ✅ Live trading execution
- ✅ Portfolio tracking
- ✅ Risk management
- ✅ Notifications
- ✅ Multi-exchange support

## 🔧 Troubleshooting

### Common Issues

#### "Invalid API Key" Error
- Check API key format (no extra spaces)
- Verify permissions on exchange
- Check IP restrictions
- Ensure testnet/sandbox settings match

#### SSL Certificate Errors
- Normal in development environments
- APIs will still work for data fetching
- Consider using VPN if persistent

#### Rate Limiting
- System has built-in rate limiting
- Reduce trading frequency if needed
- Upgrade to higher API tier if available

### Getting Help

1. **Test API keys first**: `python test_api_keys.py`
2. **Check logs**: Look in `logs/` directory
3. **Verify configuration**: Double-check `config.env.unified`
4. **Start with one exchange**: Add Binance keys first

## 🎯 Next Steps

1. **Add Binance API keys** (most important)
2. **Test with paper trading**
3. **Add Telegram notifications**
4. **Add other exchanges gradually**
5. **Monitor and optimize**

## 📞 Support

If you need help:
- Check the logs in `logs/` directory
- Run `python test_api_keys.py` for diagnostics
- Verify API key permissions on exchanges
- Start with testnet/sandbox mode first

---

**⚠️ Important**: Always start with paper trading and testnet/sandbox modes before using real funds! 