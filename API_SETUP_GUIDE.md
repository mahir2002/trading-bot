# 🚀 AI Trading Bot - Complete API Setup Guide

## 🔧 **Current Issues & Fixes**

### Issue 1: TradingBot Import Error
**Error:** `cannot import name 'TradingBot' from 'ai_trading_bot_simple'`
**Fix:** The class is named `AITradingBot`, not `TradingBot`

### Issue 2: Rate Limiter Error
**Error:** `Limiter.__init__() got multiple values for argument 'key_func'`
**Fix:** Flask-Limiter version compatibility issue

## 🔑 **Required APIs for Full Functionality**

### 1. **Cryptocurrency Exchange APIs** (ESSENTIAL)

#### **Binance API** (Recommended - Most Liquid)
```bash
# 1. Sign up at: https://www.binance.com/
# 2. Go to: Account > API Management
# 3. Create API Key with permissions:
#    - Read Info ✅
#    - Enable Trading ✅ 
#    - Enable Futures ✅ (optional)
# 4. Whitelist your IP address
# 5. Use Testnet for testing: https://testnet.binance.vision/
```

**Environment Variables:**
```env
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true  # Use testnet for safe testing
```

#### **Coinbase Pro API** (Alternative)
```bash
# 1. Sign up at: https://pro.coinbase.com/
# 2. Go to: Settings > API
# 3. Create API Key with permissions:
#    - View ✅
#    - Trade ✅
# 4. Use Sandbox for testing: https://public.sandbox.pro.coinbase.com
```

**Environment Variables:**
```env
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_secret_key
COINBASE_PASSPHRASE=your_coinbase_passphrase
COINBASE_SANDBOX=true  # Use sandbox for testing
```

#### **Other Supported Exchanges:**
- **Kraken**: `KRAKEN_API_KEY`, `KRAKEN_SECRET_KEY`
- **KuCoin**: `KUCOIN_API_KEY`, `KUCOIN_SECRET_KEY`, `KUCOIN_PASSPHRASE`
- **Bybit**: `BYBIT_API_KEY`, `BYBIT_SECRET_KEY`

### 2. **AI/ML APIs** (For Advanced Features)

#### **OpenAI API** (For AI-powered analysis)
```bash
# 1. Sign up at: https://platform.openai.com/
# 2. Go to: API Keys
# 3. Create new secret key
# 4. Pricing: ~$0.002 per 1K tokens (GPT-3.5-turbo)
```

**Environment Variables:**
```env
OPENAI_API_KEY=sk-your_openai_key_here
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4 for better analysis
```

**Use Cases:**
- Market sentiment analysis from news
- Trading signal interpretation
- Risk assessment
- Portfolio optimization suggestions

#### **Alternative AI APIs:**
```env
# Anthropic Claude (Advanced reasoning)
ANTHROPIC_API_KEY=your_anthropic_key

# Google Gemini (Multimodal analysis)
GOOGLE_API_KEY=your_google_api_key

# Cohere (Text analysis)
COHERE_API_KEY=your_cohere_key
```

### 3. **Market Data APIs** (Enhanced Data)

#### **CoinGecko API** (Crypto market data)
```bash
# 1. Sign up at: https://www.coingecko.com/en/api
# 2. Free tier: 10,000 calls/month
# 3. Pro tier: $129/month for 50,000 calls
```

**Environment Variables:**
```env
COINGECKO_API_KEY=your_coingecko_key_here
```

**Features:**
- Historical price data
- Market cap rankings
- DeFi protocols data
- NFT market data

#### **Alpha Vantage** (Traditional markets + Crypto)
```bash
# 1. Sign up at: https://www.alphavantage.co/
# 2. Free tier: 5 calls/minute, 500 calls/day
# 3. Premium: $49.99/month for unlimited calls
```

**Environment Variables:**
```env
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
```

#### **Polygon.io** (High-quality financial data)
```bash
# 1. Sign up at: https://polygon.io/
# 2. Free tier: 5 calls/minute
# 3. Starter: $99/month for real-time data
```

**Environment Variables:**
```env
POLYGON_API_KEY=your_polygon_key
```

### 4. **News & Sentiment APIs**

#### **NewsAPI** (Global news)
```bash
# 1. Sign up at: https://newsapi.org/
# 2. Free tier: 1,000 requests/day
# 3. Business: $449/month for 1M requests
```

**Environment Variables:**
```env
NEWS_API_KEY=your_news_api_key
```

#### **Twitter API v2** (Social sentiment)
```bash
# 1. Apply at: https://developer.twitter.com/
# 2. Essential tier: Free (500K tweets/month)
# 3. Elevated tier: $100/month (2M tweets/month)
```

**Environment Variables:**
```env
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
```

#### **Reddit API** (Community sentiment)
```bash
# 1. Create app at: https://www.reddit.com/prefs/apps
# 2. Free tier: 60 requests/minute
```

**Environment Variables:**
```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name
```

### 5. **Notification APIs**

#### **Telegram Bot API** (Instant notifications)
```bash
# 1. Message @BotFather on Telegram
# 2. Create new bot: /newbot
# 3. Get your bot token
# 4. Get your chat ID: message your bot, then visit:
#    https://api.telegram.org/bot<YourBOTToken>/getUpdates
```

**Environment Variables:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

#### **Discord Webhook** (Server notifications)
```bash
# 1. Go to your Discord server
# 2. Server Settings > Integrations > Webhooks
# 3. Create webhook and copy URL
```

**Environment Variables:**
```env
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

#### **Email Notifications** (SMTP)
```env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Use App Password for Gmail
EMAIL_RECIPIENT=recipient@gmail.com
```

### 6. **Database & Storage APIs**

#### **Redis** (Caching & Session Storage)
```bash
# Option 1: Local Redis
docker run -d -p 6379:6379 redis:alpine

# Option 2: Redis Cloud (Free tier: 30MB)
# Sign up at: https://redis.com/try-free/
```

**Environment Variables:**
```env
REDIS_HOST=localhost  # or your Redis Cloud endpoint
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password  # if using Redis Cloud
REDIS_DB=0
```

#### **Google Sheets API** (Data logging)
```bash
# 1. Go to: https://console.developers.google.com/
# 2. Create project and enable Google Sheets API
# 3. Create service account and download JSON credentials
# 4. Share your spreadsheet with the service account email
```

**Environment Variables:**
```env
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

## 🛠️ **Quick Setup Instructions**

### Step 1: Copy Environment Template
```bash
cp config.env.example .env
```

### Step 2: Edit Your .env File
```bash
nano .env  # or use your preferred editor
```

### Step 3: Essential APIs to Start With
**Minimum viable setup:**
1. **Binance Testnet** (for trading)
2. **Telegram Bot** (for notifications)
3. **CoinGecko Free** (for market data)

### Step 4: Test Your Setup
```bash
python start_api.py
```

## 💰 **Cost Breakdown**

### **Free Tier (Testing)**
- Binance Testnet: Free
- Telegram Bot: Free
- CoinGecko: Free (10K calls/month)
- NewsAPI: Free (1K calls/day)
- **Total: $0/month**

### **Basic Production ($50-100/month)**
- Binance Live: Free (trading fees apply)
- CoinGecko Pro: $129/month
- OpenAI: ~$20/month (moderate usage)
- **Total: ~$149/month**

### **Professional Setup ($200-500/month)**
- All above APIs
- Alpha Vantage Premium: $49.99/month
- Twitter API Elevated: $100/month
- Polygon.io Starter: $99/month
- Redis Cloud: $7/month
- **Total: ~$385/month**

## 🔒 **Security Best Practices**

### API Key Security
```bash
# Never commit API keys to git
echo ".env" >> .gitignore

# Use environment variables in production
export BINANCE_API_KEY="your_key_here"

# Rotate keys regularly (monthly)
# Use IP whitelisting when available
# Enable 2FA on all accounts
```

### Trading Safety
```bash
# Always start with testnet/sandbox
BINANCE_TESTNET=true
COINBASE_SANDBOX=true

# Use small amounts initially
DEFAULT_TRADE_AMOUNT=10  # Start with $10

# Set strict risk limits
RISK_PERCENTAGE=1  # Risk only 1% per trade
STOP_LOSS_PERCENTAGE=2  # 2% stop loss
```

## 🚨 **Troubleshooting Common Issues**

### Issue: "Invalid API Key"
```bash
# Check if key is correctly set
echo $BINANCE_API_KEY

# Verify key permissions on exchange
# Check IP whitelist settings
# Ensure testnet keys for testnet endpoints
```

### Issue: "Rate Limit Exceeded"
```bash
# Implement exponential backoff
# Use multiple API keys for rotation
# Cache frequently requested data
# Optimize API call frequency
```

### Issue: "Insufficient Balance"
```bash
# Check account balance
# Verify trading permissions
# Ensure correct trading pair format (BTC/USDT not BTCUSDT)
```

## 📊 **API Usage Monitoring**

### Track Your Usage
```python
# Monitor API calls
import time
from collections import defaultdict

api_calls = defaultdict(int)

def track_api_call(api_name):
    api_calls[api_name] += 1
    print(f"{api_name}: {api_calls[api_name]} calls today")
```

### Set Up Alerts
```python
# Alert when approaching limits
if api_calls['coingecko'] > 9000:  # 90% of 10K limit
    send_telegram_message("⚠️ CoinGecko API limit warning!")
```

## 🎯 **Next Steps**

1. **Start with testnet** - Use sandbox/testnet APIs first
2. **Implement gradually** - Add one API at a time
3. **Monitor costs** - Track API usage and costs
4. **Scale up** - Move to production when confident
5. **Optimize** - Cache data and optimize API calls

## 📞 **Support & Resources**

- **Binance API Docs**: https://binance-docs.github.io/apidocs/
- **CCXT Library**: https://docs.ccxt.com/
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

**⚠️ Disclaimer**: Trading cryptocurrencies involves substantial risk. Never trade with money you can't afford to lose. Always test thoroughly with small amounts first. 