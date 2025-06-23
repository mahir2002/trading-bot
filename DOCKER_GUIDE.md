# 🐳 Docker Deployment Guide for AI Crypto Trading Bot

This guide explains how to deploy and run the AI Crypto Trading Bot using Docker and Docker Compose with Redis caching.

## 📋 Prerequisites

1. **Docker** installed on your system
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Verify installation: `docker --version`

2. **Docker Compose** (included with Docker Desktop)
   - Verify installation: `docker-compose --version`

3. **Configuration file** (`.env`)
   - Copy `config.env.example` to `.env`
   - Configure your API keys and settings

4. **Google Credentials** (optional)
   - Place `google-credentials.json` in the project root for Google Sheets integration

## 🚀 Quick Start

### 1. Clone and Setup
```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd ai-trading-bot

# Copy configuration template
cp config.env.example .env

# Edit configuration with your settings
nano .env  # or use your preferred editor

# Optional: Add Google Sheets credentials
# Place google-credentials.json in the project root
```

### 2. Build and Run

#### Option A: Complete Suite (Recommended)
```bash
# Build and start complete suite with Redis
docker-compose up -d redis trading-suite

# Access dashboard at http://localhost:8050
# Bot API available at http://localhost:5001
# Redis available at localhost:6379
```

#### Option B: Main Trading Bot with Redis
```bash
# Build and start trading bot with Redis
docker-compose up -d redis trading-bot

# View logs
docker-compose logs -f trading-bot
```

#### Option C: Dashboard Only
```bash
# Build and start dashboard with Redis
docker-compose up -d redis dashboard

# Access dashboard at http://localhost:8050
```

#### Option D: Alternative Bot (without Redis)
```bash
# Run simplified bot without Redis
docker-compose --profile alternative up -d ai-trading-bot
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Trading Configuration
TRADING_MODE=paper                    # paper or live
RISK_PERCENTAGE=2                     # Risk per trade (%)
PREDICTION_CONFIDENCE_THRESHOLD=0.7   # AI confidence threshold

# Exchange API Keys (at least one required)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key

# Optional: Coinbase Pro
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_secret_key

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Optional: Telegram Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: Email Notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@gmail.com

# Optional: Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS_FILE=google-credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8050
DASHBOARD_DEBUG=false

# Docker Configuration
TZ=UTC
LOG_LEVEL=INFO
```

## 📊 Available Services

### 1. Redis Cache (`redis`)
- **Purpose**: Data caching and session storage
- **Port**: 6379
- **Features**: Price data caching, prediction caching, trade history

### 2. Main Trading Bot (`trading-bot`)
- **Purpose**: AI trading algorithm with Redis integration
- **Port**: 5001 (API endpoint)
- **Features**: Enhanced caching, better performance, data persistence

### 3. Dashboard (`dashboard`)
- **Purpose**: Web-based monitoring interface
- **Port**: 8050
- **Features**: Real-time charts, bot controls, performance tracking

### 4. Trading Suite (`trading-suite`)
- **Purpose**: Combined bot + dashboard + Redis
- **Ports**: 8050 (dashboard), 5001 (bot API)
- **Recommended**: Best for most users

### 5. Alternative Bot (`ai-trading-bot`)
- **Purpose**: Simplified bot without Redis
- **Profile**: `alternative`
- **Use case**: Testing or minimal deployments

## 🛠️ Docker Commands

### Basic Operations
```bash
# Build images
docker-compose build

# Start complete suite
docker-compose up -d redis trading-suite

# Start specific services
docker-compose up -d redis trading-bot dashboard

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f trading-bot
docker-compose logs -f redis
```

### Management Commands
```bash
# Restart services
docker-compose restart

# Update and restart
docker-compose pull
docker-compose up -d

# Remove everything (including volumes)
docker-compose down -v

# Shell access to containers
docker-compose exec trading-bot bash
docker-compose exec redis redis-cli
```

### Redis Operations
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Check Redis status
docker-compose exec redis redis-cli ping

# View Redis info
docker-compose exec redis redis-cli info

# Clear Redis cache
docker-compose exec redis redis-cli flushdb
```

### Monitoring
```bash
# View running containers
docker ps

# Monitor resource usage
docker stats

# System status
docker-compose ps

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## 📁 Volume Mounts

The Docker setup includes persistent volumes for:

- **`./logs`** → `/app/logs` - Trading logs and activity
- **`./data`** → `/app/data` - Performance data and cache
- **`./.env`** → `/app/.env` - Configuration file
- **`./google-credentials.json`** → `/app/google-credentials.json` - Google API credentials
- **`redis_data`** - Redis data persistence

## 🔒 Security Considerations

### 1. API Keys Protection
- Never commit `.env` file to version control
- Use read-only API keys when possible
- Enable IP restrictions on exchange APIs

### 2. Container Security
- Runs as non-root user (`trader`)
- Minimal base image (Python slim)
- No unnecessary packages installed
- Isolated Docker network

### 3. Redis Security
- Redis runs in isolated network
- No external Redis access by default
- Data encrypted in transit within Docker network

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Errors
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

#### 2. API Key Errors
```bash
# Check logs for API errors
docker-compose logs trading-bot | grep "Invalid Api-Key"

# Verify .env file
cat .env | grep API_KEY
```

#### 3. Port Conflicts
```bash
# Change ports in docker-compose.yml
ports:
  - "8051:8050"  # Use different host port
  - "6380:6379"  # Use different Redis port
```

#### 4. Google Credentials Issues
```bash
# Check if credentials file exists
ls -la google-credentials.json

# Check container access
docker-compose exec trading-bot ls -la /app/google-credentials.json
```

### Debugging Commands
```bash
# Check container health
docker-compose ps

# Inspect containers
docker inspect trading-bot
docker inspect redis-cache

# Execute commands in containers
docker-compose exec trading-bot python main.py --config-check
docker-compose exec trading-bot python main.py --redis-check

# View detailed logs
docker-compose logs --details trading-bot
```

## 📈 Monitoring and Maintenance

### 1. Log Monitoring
```bash
# Monitor logs in real-time
docker-compose logs -f

# Search for specific events
docker-compose logs | grep "TRADE:"
docker-compose logs | grep "ERROR"
docker-compose logs | grep "Redis"
```

### 2. Performance Monitoring
```bash
# Check resource usage
docker stats

# Monitor Redis performance
docker-compose exec redis redis-cli info stats

# Check cache hit rates
docker-compose exec redis redis-cli info keyspace
```

### 3. Cache Management
```bash
# View cached data
docker-compose exec redis redis-cli keys "*"

# Clear specific cache
docker-compose exec redis redis-cli del "price:BTC/USDT:1h"

# Clear all cache
docker-compose exec redis redis-cli flushdb
```

## 🔄 Backup and Recovery

### 1. Backup Data
```bash
# Create complete backup
tar -czf backup_$(date +%Y%m%d).tar.gz logs data .env google-credentials.json

# Backup Redis data
docker-compose exec redis redis-cli save
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./redis_backup.rdb
```

### 2. Restore Data
```bash
# Extract backup
tar -xzf backup_20231201.tar.gz

# Restore Redis data
docker cp ./redis_backup.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

## 🌐 Production Deployment

### 1. Environment-Specific Configurations
```bash
# Production environment
cp .env .env.production
# Edit production-specific settings

# Staging environment
cp .env .env.staging
# Edit staging-specific settings
```

### 2. Scaling with Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml trading-bot

# Scale services
docker service scale trading-bot_trading-bot=3
```

### 3. Cloud Deployment
- **AWS ECS**: Use the provided Dockerfile with Redis ElastiCache
- **Google Cloud Run**: Deploy with Cloud Memorystore for Redis
- **Azure Container Instances**: Use Azure Cache for Redis

## 📞 Support

If you encounter issues:

1. **Check the logs**: `docker-compose logs`
2. **Verify configuration**: `cat .env`
3. **Test Redis**: `docker-compose exec redis redis-cli ping`
4. **Check connectivity**: `docker-compose exec trading-bot python main.py --redis-check`
5. **Review this guide** for common solutions

## 🎯 Next Steps

1. **Configure API Keys**: Set up exchange API access
2. **Test Redis Connection**: Verify caching is working
3. **Monitor Performance**: Use dashboard and Redis monitoring
4. **Optimize Cache Settings**: Adjust TTL values based on usage
5. **Scale Up**: Consider live trading once comfortable

---

**⚠️ Important**: Always start with paper trading mode to test your configuration before risking real money!

## 🔧 Redis Benefits

### Performance Improvements
- **Faster Data Access**: Cached price data and predictions
- **Reduced API Calls**: Less strain on exchange APIs
- **Better Responsiveness**: Dashboard loads faster with cached data

### Enhanced Features
- **Trade History**: Persistent trade logging
- **Session Management**: Bot state persistence
- **Real-time Updates**: Live data sharing between components
- **Scalability**: Support for multiple bot instances 