# Pipeline Scheduler Guide

## 🚀 Automated 24-Hour Update Pipeline

The Pipeline Scheduler is a comprehensive system that orchestrates the complete data collection and AI processing pipeline every 24 hours. It ensures your trading bot stays updated with the latest market data, new coin listings, and AI-generated insights.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Pipeline Steps](#pipeline-steps)
7. [Logging & Monitoring](#logging--monitoring)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

## 🎯 Overview

The Pipeline Scheduler automates the following critical tasks:

1. **Fetch CEX Coins** - Collect listings from 8+ centralized exchanges
2. **Fetch DEX Coins** - Gather data from 5+ decentralized exchanges
3. **Detect New Listings** - Identify newly listed cryptocurrencies
4. **Fetch Historical Data** - Collect 30-day OHLCV data for new coins
5. **Analyze Sentiment** - Process social media sentiment for new coins
6. **Run AI Models** - Generate predictions and trading recommendations

## ✨ Features

### Core Features
- **24-Hour Scheduling** - Runs daily at configurable time (default: 2 AM UTC)
- **Comprehensive Logging** - All activities logged with rotation
- **Error Handling** - Resilient with retry mechanisms
- **Health Monitoring** - Hourly health checks and status reports
- **Flexible Configuration** - JSON-based configuration system
- **Graceful Shutdown** - Proper signal handling for production

### Advanced Features
- **Step-by-Step Execution** - Each pipeline step is independently tracked
- **Parallel Processing** - Optimized for performance
- **Data Persistence** - Results saved to JSON files
- **Error Reporting** - Detailed error logs and reports
- **Status Monitoring** - Real-time pipeline status tracking

## 🔧 Installation

### Prerequisites
- Python 3.8+
- All existing trading bot dependencies
- APScheduler library

### Install Dependencies
```bash
pip install -r requirements.txt
```

The scheduler requires:
- `apscheduler==3.10.4` - For scheduling functionality
- All existing modules (CEX, DEX, Detection, Historical, Sentiment, AI)

### Verify Installation
```python
from unified_trading_platform.core.pipeline_scheduler import PipelineScheduler
scheduler = PipelineScheduler()
print("✅ Pipeline Scheduler installed successfully")
```

## ⚙️ Configuration

### Configuration File
Location: `unified_trading_platform/config/scheduler_config.json`

```json
{
  "schedule": {
    "enabled": true,
    "hour": 2,
    "minute": 0,
    "timezone": "UTC"
  },
  "pipeline": {
    "steps": {
      "fetch_cex_coins": true,
      "fetch_dex_coins": true,
      "detect_new_listings": true,
      "fetch_historical_data": true,
      "analyze_sentiment": true,
      "run_ai_models": true
    },
    "timeout_minutes": 120,
    "retry_attempts": 3,
    "retry_delay": 300,
    "stop_on_error": false
  },
  "logging": {
    "level": "INFO",
    "file": "logs/pipeline_scheduler.log",
    "max_size_mb": 100,
    "backup_count": 5
  }
}
```

### Configuration Options

#### Schedule Settings
- `enabled`: Enable/disable the scheduler
- `hour`: Hour to run (0-23, UTC)
- `minute`: Minute to run (0-59)
- `timezone`: Timezone for scheduling

#### Pipeline Settings
- `steps`: Enable/disable individual pipeline steps
- `timeout_minutes`: Maximum pipeline execution time
- `retry_attempts`: Number of retry attempts for failed steps
- `retry_delay`: Delay between retries (seconds)
- `stop_on_error`: Stop pipeline on first error

#### Logging Settings
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `file`: Log file path
- `max_size_mb`: Max log file size before rotation
- `backup_count`: Number of backup log files

## 🚀 Usage

### Quick Start

#### 1. Demo Mode
```bash
python pipeline_scheduler_demo.py
```

#### 2. Production Mode
```bash
python launch_pipeline_scheduler.py
```

### Programmatic Usage

```python
import asyncio
from unified_trading_platform.core.pipeline_scheduler import PipelineScheduler

async def main():
    # Initialize scheduler
    scheduler = PipelineScheduler()
    
    # Start scheduler
    scheduler.start_scheduler()
    
    # Get status
    status = scheduler.get_pipeline_status()
    print(f"Next run: {status['next_run']}")
    
    # Run pipeline immediately (optional)
    await scheduler.run_pipeline_now()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop_scheduler()

asyncio.run(main())
```

## 📊 Pipeline Steps

### Step 1: Fetch CEX Coins
- **Purpose**: Collect coin listings from centralized exchanges
- **Exchanges**: Binance, KuCoin, Coinbase, Kraken, Bybit, OKX, Gate.io, Huobi
- **Output**: CEX listings with trading pairs and metadata

### Step 2: Fetch DEX Coins
- **Purpose**: Gather data from decentralized exchanges
- **Networks**: Ethereum, BSC, Polygon, Arbitrum, Optimism
- **Protocols**: Uniswap, PancakeSwap, SushiSwap, Curve, Balancer
- **Output**: DEX pairs with liquidity and volume data

### Step 3: Detect New Listings
- **Purpose**: Identify newly listed cryptocurrencies
- **Method**: Compare today's listings with yesterday's data
- **Sources**: CEX + DEX + CoinGecko + GeckoTerminal
- **Output**: `data/new_coins_for_ai.json` with priority scores

### Step 4: Fetch Historical Data
- **Purpose**: Collect 30-day OHLCV data for new coins
- **Sources**: CoinGecko API + Exchange APIs via CCXT
- **Data**: Open, High, Low, Close, Volume for each day
- **Output**: SQLite database + CSV files

### Step 5: Analyze Sentiment
- **Purpose**: Process social media sentiment for new coins
- **Sources**: Twitter API + Reddit scraping
- **Analysis**: TextBlob sentiment scoring
- **Output**: Sentiment scores and social metrics

### Step 6: Run AI Models
- **Purpose**: Generate predictions and trading recommendations
- **Models**: Multiple ML models for price prediction
- **Input**: Historical data + sentiment + market metrics
- **Output**: AI predictions and recommendations

## 📝 Logging & Monitoring

### Log Files
- **Scheduler Log**: `logs/pipeline_scheduler.log` (main operations)
- **Launcher Log**: `logs/scheduler_launcher.log` (startup/shutdown)
- **Module Logs**: Individual module logs (CEX, DEX, etc.)

### Log Levels
```python
DEBUG   # Detailed debug information
INFO    # General information messages
WARNING # Warning messages for non-critical issues
ERROR   # Error messages for failed operations
```

### Monitoring Files
- **Pipeline Results**: `data/pipeline_results/pipeline_result_YYYYMMDD_HHMMSS.json`
- **Error Reports**: `data/pipeline_errors/pipeline_error_YYYYMMDD_HHMMSS.json`
- **Health Status**: `data/health_checks/pipeline_health.json`

### Status Monitoring
```python
scheduler = PipelineScheduler()
status = scheduler.get_pipeline_status()

print(f"Scheduler running: {status['scheduler_running']}")
print(f"Pipeline active: {status['pipeline_running']}")
print(f"Next run: {status['next_run']}")
print(f"Last run: {status['last_run']}")
print(f"Total runs: {status['stats']['total_runs']}")
```

## 🏭 Production Deployment

### Systemd Service (Linux)
Create `/etc/systemd/system/pipeline-scheduler.service`:

```ini
[Unit]
Description=Trading Bot Pipeline Scheduler
After=network.target

[Service]
Type=simple
User=tradingbot
WorkingDirectory=/path/to/ai-trading-bot-23
ExecStart=/path/to/python launch_pipeline_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pipeline-scheduler
sudo systemctl start pipeline-scheduler
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "launch_pipeline_scheduler.py"]
```

### Cron Alternative
If you prefer cron over APScheduler:

```bash
# Edit crontab
crontab -e

# Add entry for 2 AM daily
0 2 * * * cd /path/to/ai-trading-bot-23 && python -c "
import asyncio
from unified_trading_platform.core.pipeline_scheduler import PipelineScheduler
scheduler = PipelineScheduler()
asyncio.run(scheduler.run_full_pipeline())
"
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Scheduler Won't Start
```bash
# Check logs
tail -f logs/pipeline_scheduler.log

# Verify configuration
python -c "
from unified_trading_platform.core.pipeline_scheduler import PipelineScheduler
scheduler = PipelineScheduler()
print('Config:', scheduler.config)
"
```

#### 2. Pipeline Steps Failing
```bash
# Check individual module logs
ls -la logs/

# Test individual modules
python -c "
from modules.coin_listings_cex import CoinListingsCEX
cex = CoinListingsCEX()
# Test module functionality
"
```

#### 3. High Memory Usage
- Increase system memory
- Reduce concurrent operations
- Enable garbage collection
- Monitor with `htop` or `top`

#### 4. API Rate Limits
- Check API keys and quotas
- Increase retry delays
- Reduce concurrent requests
- Monitor API usage

### Log Analysis
```bash
# View recent logs
tail -f logs/pipeline_scheduler.log

# Search for errors
grep -i error logs/pipeline_scheduler.log

# Monitor pipeline runs
grep -i "pipeline completed" logs/pipeline_scheduler.log
```

### Health Checks
```python
import json
from pathlib import Path

# Check health status
health_file = Path("data/health_checks/pipeline_health.json")
if health_file.exists():
    with open(health_file) as f:
        health = json.load(f)
    print(f"Health: {health}")
```

## 📚 API Reference

### PipelineScheduler Class

#### Constructor
```python
scheduler = PipelineScheduler(config_path="path/to/config.json")
```

#### Methods

##### start_scheduler()
Start the pipeline scheduler with configured timing.

```python
scheduler.start_scheduler()
```

##### stop_scheduler()
Stop the pipeline scheduler gracefully.

```python
scheduler.stop_scheduler()
```

##### run_full_pipeline()
Execute the complete pipeline once.

```python
await scheduler.run_full_pipeline()
```

##### run_pipeline_now()
Trigger immediate pipeline execution.

```python
success = await scheduler.run_pipeline_now()
```

##### get_pipeline_status()
Get current pipeline status and statistics.

```python
status = scheduler.get_pipeline_status()
```

#### Properties

##### pipeline_running
Check if pipeline is currently executing.

```python
is_running = scheduler.pipeline_running
```

##### pipeline_stats
Get pipeline execution statistics.

```python
stats = scheduler.pipeline_stats
# Returns: {
#   'total_runs': int,
#   'successful_runs': int,
#   'failed_runs': int,
#   'average_duration': float,
#   'last_error': str
# }
```

## 🎯 Best Practices

### 1. Configuration Management
- Keep configuration in version control
- Use environment-specific configs
- Document all configuration changes
- Test configuration changes in staging

### 2. Monitoring & Alerting
- Set up log monitoring
- Create alerts for failed pipelines
- Monitor system resources
- Track pipeline performance metrics

### 3. Error Handling
- Review error logs regularly
- Set up automated error notifications
- Have fallback procedures
- Document common issues and solutions

### 4. Performance Optimization
- Monitor execution times
- Optimize slow pipeline steps
- Use caching where appropriate
- Scale resources as needed

### 5. Security
- Secure API keys and credentials
- Use proper file permissions
- Implement access controls
- Regular security audits

## 🚨 Important Notes

- **Data Dependencies**: Ensure all required data directories exist
- **API Keys**: Verify all API keys are properly configured
- **System Resources**: Monitor CPU, memory, and disk usage
- **Network Connectivity**: Ensure stable internet connection
- **Backup Strategy**: Implement regular data backups

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review log files for errors
3. Test individual components
4. Verify configuration settings
5. Check system resources

## 🔄 Updates

To update the scheduler:

1. Pull latest code changes
2. Update configuration if needed
3. Restart the scheduler service
4. Monitor logs for issues
5. Verify pipeline execution

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-22  
**Status**: Production Ready ✅ 