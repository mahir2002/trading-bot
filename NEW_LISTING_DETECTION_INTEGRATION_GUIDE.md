# 🔍 New Listing Detection System - Integration Guide

## Overview

The **New Listing Detection System** provides advanced detection of newly listed cryptocurrencies across multiple exchanges and platforms, with historical tracking, CoinGecko integration, and AI-ready data preparation.

## 🎯 Key Features

### ✅ Core Functionality
- **Historical Tracking**: Store yesterday's coin lists and compare with today's
- **Multi-Source Detection**: CEX, DEX, CoinGecko, GeckoTerminal integration
- **AI-Ready Data**: Separate storage optimized for AI processing
- **Priority Scoring**: Intelligent risk assessment and categorization
- **Real-time Notifications**: Alerts for high-priority new listings

### ✅ Enhanced Data Sources
- **CoinGecko API**: `/coins/list` endpoint for comprehensive coverage
- **GeckoTerminal**: Trending DeFi token detection
- **CEX Integration**: Connect with existing exchange listing modules
- **DEX Integration**: Link with DEX token discovery systems

## 🚀 Quick Start

### 1. Basic Integration

```python
from unified_trading_platform.modules.new_listing_detector import NewListingDetectorModule

# Configuration
config = {
    'check_interval_hours': 6,  # Check every 6 hours
    'coingecko_api_key': 'your_coingecko_api_key',  # Optional but recommended
    'enable_geckoterminal': True,
    'min_market_cap_usd': 100000,  # $100K minimum
    'max_new_listings_per_check': 50,
    'cache_dir': 'data/new_listings'
}

# Create and start
detector = NewListingDetectorModule('new_listing_detector', config)
await detector.initialize()
await detector.start()
```

### 2. Integration with Unified Master Bot

Add to `unified_master_trading_bot.py`:

```python
def setup_new_listing_detection(self):
    """Setup new listing detection system"""
    try:
        from unified_trading_platform.modules.new_listing_detector import NewListingDetectorModule
        
        config = {
            'check_interval_hours': self.config.get('new_listing_check_hours', 6),
            'coingecko_api_key': self.config.get('coingecko_api_key', ''),
            'enable_notifications': True,
            'min_market_cap_usd': self.config.get('min_new_listing_market_cap', 100000),
            'cache_dir': 'data/new_listings'
        }
        
        self.new_listing_detector = NewListingDetectorModule('new_listing_detector', config)
        asyncio.create_task(self.new_listing_detector.initialize())
        asyncio.create_task(self.new_listing_detector.start())
        
        logger.info("✅ New listing detection configured")
        
    except Exception as e:
        logger.error(f"Failed to setup new listing detection: {e}")
```

## 📊 Data Structure

### Historical Snapshots
```sql
CREATE TABLE historical_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    total_coins INTEGER,
    unique_symbols INTEGER,
    coin_list_hash TEXT,
    coin_list TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### New Listings
```sql
CREATE TABLE new_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT,
    source TEXT NOT NULL,
    exchange TEXT,
    network TEXT,
    contract_address TEXT,
    detected_at TEXT NOT NULL,
    market_cap_usd REAL,
    price_usd REAL,
    volume_24h_usd REAL,
    total_supply REAL,
    circulating_supply REAL,
    coingecko_id TEXT,
    description TEXT,
    homepage TEXT,
    image_url TEXT,
    categories TEXT,
    ai_analysis_priority TEXT,
    risk_score REAL,
    info TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### AI Data File Format
```json
{
  "timestamp": "2025-01-22T10:30:00",
  "total_new_listings": 15,
  "high_priority_count": 3,
  "medium_priority_count": 8,
  "low_priority_count": 4,
  "new_listings": [
    {
      "coin_id": "example-coin",
      "symbol": "EXAMPLE",
      "name": "Example Coin",
      "source": "coingecko",
      "market_cap_usd": 5000000,
      "price_usd": 0.25,
      "volume_24h_usd": 100000,
      "ai_analysis_priority": "high",
      "risk_score": 25,
      "categories": ["defi", "layer-1"],
      "detected_at": "2025-01-22T10:15:00",
      "contract_address": "0x...",
      "description": "Revolutionary DeFi protocol...",
      "homepage": "https://example.com"
    }
  ]
}
```

## 🔧 Configuration Options

### Core Settings
```python
config = {
    # Detection frequency
    'check_interval_hours': 6,  # How often to check for new listings
    
    # API keys
    'coingecko_api_key': '',  # CoinGecko Pro API key (optional)
    
    # Feature toggles
    'enable_geckoterminal': True,  # Enable GeckoTerminal integration
    'enable_notifications': True,  # Send notifications for new listings
    
    # Filtering
    'min_market_cap_usd': 100000,  # Minimum market cap threshold
    'max_new_listings_per_check': 50,  # Limit results per check
    
    # Storage
    'cache_dir': 'data/new_listings',  # Storage directory
    'historical_retention_days': 30,  # How long to keep historical data
}
```

### Priority Scoring Algorithm
```python
def calculate_priority(listing):
    priority_score = 0
    risk_score = 50  # Default medium risk
    
    # Market cap factor (0-30 points)
    if listing.market_cap_usd >= 100_000_000:  # $100M+
        priority_score += 30
        risk_score -= 20
    elif listing.market_cap_usd >= 10_000_000:  # $10M+
        priority_score += 20
        risk_score -= 10
    elif listing.market_cap_usd >= 1_000_000:  # $1M+
        priority_score += 10
    
    # Volume factor (0-20 points)
    if listing.volume_24h_usd >= 1_000_000:  # $1M+ daily volume
        priority_score += 20
        risk_score -= 10
    elif listing.volume_24h_usd >= 100_000:  # $100K+ daily volume
        priority_score += 10
    
    # Category factor (0-15 points)
    high_interest_categories = [
        'decentralized-finance-defi', 'layer-1', 'layer-2',
        'artificial-intelligence', 'gaming', 'metaverse'
    ]
    if any(cat in high_interest_categories for cat in listing.categories):
        priority_score += 15
        risk_score -= 5
    
    # Priority levels
    if priority_score >= 50:
        return 'high', risk_score
    elif priority_score >= 25:
        return 'medium', risk_score
    else:
        return 'low', risk_score
```

## 🎯 Event Handlers

### Manual Detection
```python
# Trigger manual new listing detection
result = await detector.send_event('detect_new_listings', {})
print(f"New listings found: {result['new_listings_found']}")
```

### Get New Listings
```python
# Get recent new listings
result = await detector.send_event('get_new_listings', {
    'limit': 20,
    'priority': 'high'  # Optional: filter by priority
})

for listing in result['listings']:
    print(f"{listing['symbol']}: {listing['ai_analysis_priority']} priority")
```

### Get AI Data
```python
# Get AI-ready data file
result = await detector.send_event('get_ai_data', {})
ai_data = result['ai_data']
print(f"AI data file: {result['file_path']}")
```

## 🔔 Notification Integration

### Telegram Integration
```python
async def handle_new_listings_notification(event):
    """Handle new listing notifications"""
    if event.type == 'new_high_priority_listings':
        count = event.data['count']
        listings = event.data['listings']
        
        message = f"🚨 {count} High Priority New Listings Detected!\n\n"
        
        for listing in listings[:3]:  # Top 3
            message += f"🪙 {listing['symbol']} ({listing['name']})\n"
            message += f"💰 Market Cap: ${listing['market_cap_usd']:,.0f}\n"
            message += f"⚡ Source: {listing['source']}\n"
            message += f"🎯 Risk Score: {listing['risk_score']}/100\n\n"
        
        # Send to Telegram
        await send_telegram_message(message)

# Register the handler
detector.register_event_handler('new_high_priority_listings', handle_new_listings_notification)
```

### Trading Bot Integration
```python
async def handle_new_listings_for_trading(event):
    """Handle new listings for automated trading"""
    if event.type == 'new_high_priority_listings':
        for listing in event.data['listings']:
            if (listing['ai_analysis_priority'] == 'high' and 
                listing['risk_score'] < 30 and  # Low risk
                listing['market_cap_usd'] > 10_000_000):  # $10M+ market cap
                
                # Add to trading pairs
                symbol = f"{listing['symbol']}/USDT"
                await add_trading_pair(symbol)
                
                # Set initial position size (conservative)
                position_size = calculate_new_listing_position_size(listing)
                await set_position_limits(symbol, position_size)
                
                logger.info(f"🎯 Added new high-priority listing to trading: {symbol}")

detector.register_event_handler('new_high_priority_listings', handle_new_listings_for_trading)
```

## 🧠 AI Processing Integration

### Data Preparation
```python
def prepare_ai_training_data():
    """Prepare new listing data for AI training"""
    import json
    import pandas as pd
    
    # Load AI data file
    with open('data/new_listings/new_coins_for_ai.json', 'r') as f:
        ai_data = json.load(f)
    
    # Convert to DataFrame
    listings_df = pd.DataFrame(ai_data['new_listings'])
    
    # Feature engineering
    listings_df['market_cap_log'] = np.log10(listings_df['market_cap_usd'].fillna(1))
    listings_df['volume_to_mcap_ratio'] = (
        listings_df['volume_24h_usd'] / listings_df['market_cap_usd']
    ).fillna(0)
    
    # Category encoding
    category_features = encode_categories(listings_df['categories'])
    listings_df = pd.concat([listings_df, category_features], axis=1)
    
    return listings_df

def train_new_listing_predictor(listings_df):
    """Train ML model to predict new listing success"""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    
    # Features for prediction
    features = [
        'market_cap_log', 'volume_to_mcap_ratio', 'risk_score',
        'has_defi_category', 'has_layer1_category', 'has_ai_category'
    ]
    
    # Target: success metric (you would define this based on price performance)
    # This is an example - you'd need historical performance data
    X = listings_df[features].fillna(0)
    y = calculate_listing_success_labels(listings_df)  # Your success metric
    
    # Train model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    accuracy = model.score(X_test, y_test)
    print(f"New listing prediction accuracy: {accuracy:.2%}")
    
    return model
```

## 📈 Performance Monitoring

### Health Checks
```python
async def monitor_detector_health():
    """Monitor detector health and performance"""
    health = await detector.health_check()
    
    if health['status'] != 'healthy':
        logger.warning(f"Detector health issue: {health}")
        # Send alert
        await send_health_alert(health)
    
    # Check API rate limits
    stats = detector.get_statistics()
    if stats['api_calls_today'] > 1000:  # Near rate limit
        logger.warning("Approaching API rate limits")

# Run health checks periodically
asyncio.create_task(periodic_health_check())
```

### Statistics Dashboard
```python
def create_statistics_dashboard():
    """Create statistics dashboard for new listing detection"""
    stats = detector.get_statistics()
    
    dashboard_data = {
        'detection_stats': {
            'total_new_listings_detected': stats['total_new_listings_detected'],
            'new_listings_today': stats['new_listings_today'],
            'high_priority_new_coins': stats['high_priority_new_coins'],
            'last_check': stats['last_check']
        },
        'api_stats': {
            'coingecko_coins_tracked': stats['coingecko_coins_tracked'],
            'api_calls_today': stats['api_calls_today'],
            'coingecko_api_configured': stats['coingecko_api_configured']
        },
        'performance_stats': {
            'check_interval_hours': stats['check_interval_hours'],
            'total_snapshots': stats['total_snapshots']
        }
    }
    
    return dashboard_data
```

## 🔒 Security Considerations

### API Key Management
```python
# Use environment variables for API keys
import os
config['coingecko_api_key'] = os.getenv('COINGECKO_API_KEY', '')

# Rotate API keys regularly
# Monitor API usage and rate limits
# Use different keys for different environments (dev/staging/prod)
```

### Data Validation
```python
def validate_new_listing_data(listing):
    """Validate new listing data before processing"""
    required_fields = ['coin_id', 'symbol', 'name', 'source']
    
    for field in required_fields:
        if not listing.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate market cap (prevent manipulation)
    if listing.get('market_cap_usd', 0) > 1_000_000_000_000:  # $1T limit
        logger.warning(f"Suspicious market cap for {listing['symbol']}: ${listing['market_cap_usd']:,.0f}")
    
    # Validate symbol format
    if not re.match(r'^[A-Z0-9]{2,10}$', listing['symbol']):
        logger.warning(f"Unusual symbol format: {listing['symbol']}")
    
    return True
```

## 🚀 Deployment Guide

### Production Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  new-listing-detector:
    build: .
    environment:
      - COINGECKO_API_KEY=${COINGECKO_API_KEY}
      - CHECK_INTERVAL_HOURS=6
      - MIN_MARKET_CAP_USD=100000
    volumes:
      - ./data/new_listings:/app/data/new_listings
    restart: unless-stopped
```

### Environment Variables
```bash
# .env file
COINGECKO_API_KEY=your_coingecko_pro_api_key
GECKOTERMINAL_ENABLED=true
MIN_MARKET_CAP_USD=100000
CHECK_INTERVAL_HOURS=6
ENABLE_NOTIFICATIONS=true
```

### Monitoring Setup
```python
# monitoring.py
import asyncio
import logging
from datetime import datetime, timedelta

async def monitor_new_listing_detection():
    """Monitor new listing detection system"""
    while True:
        try:
            # Check last detection time
            stats = detector.get_statistics()
            last_check = datetime.fromisoformat(stats['last_check'])
            
            if datetime.now() - last_check > timedelta(hours=8):
                # Send alert - detection hasn't run in 8 hours
                await send_alert("New listing detection appears to be stuck")
            
            # Check database health
            health = await detector.health_check()
            if health['status'] != 'healthy':
                await send_alert(f"New listing detector health issue: {health}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            await asyncio.sleep(60)
```

## 📚 Best Practices

### 1. Rate Limit Management
```python
# Respect API rate limits
config['coingecko_rate_limit'] = 50  # calls per minute
config['geckoterminal_rate_limit'] = 300  # calls per minute

# Implement exponential backoff
async def api_call_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
```

### 2. Data Quality
```python
# Filter out obvious scams/test tokens
def filter_quality_listings(listings):
    filtered = []
    
    for listing in listings:
        # Skip obvious test tokens
        if any(word in listing['name'].lower() for word in ['test', 'fake', 'scam']):
            continue
            
        # Skip tokens with no real trading volume
        if listing.get('volume_24h_usd', 0) < 1000:
            continue
            
        # Skip tokens with suspicious market caps
        if listing.get('market_cap_usd', 0) > 100_000_000_000:  # $100B
            continue
            
        filtered.append(listing)
    
    return filtered
```

### 3. Error Handling
```python
# Comprehensive error handling
async def robust_detection_cycle():
    try:
        await detector._check_for_new_listings()
    except aiohttp.ClientError as e:
        logger.error(f"Network error during detection: {e}")
        # Continue operation, API might be temporarily down
    except sqlite3.Error as e:
        logger.error(f"Database error during detection: {e}")
        # Critical error - might need restart
        raise
    except Exception as e:
        logger.error(f"Unexpected error during detection: {e}")
        # Log full traceback for debugging
        import traceback
        traceback.print_exc()
```

## 🎉 Success Metrics

### Key Performance Indicators
- **Detection Accuracy**: % of legitimate new listings vs false positives
- **Detection Speed**: Time from listing to detection
- **API Efficiency**: API calls per successful detection
- **Priority Accuracy**: % of high-priority listings that perform well
- **Coverage**: % of actual new listings detected across all exchanges

### Business Value Tracking
```python
def calculate_business_value():
    """Calculate business value of new listing detection"""
    stats = detector.get_statistics()
    
    # Estimated value per high-priority detection
    value_per_detection = 5000  # $5K average profit opportunity
    
    total_value = stats['high_priority_new_coins'] * value_per_detection
    
    # ROI calculation
    monthly_cost = 100  # API costs + compute
    monthly_value = total_value * (30 / stats.get('days_active', 30))
    roi = (monthly_value - monthly_cost) / monthly_cost * 100
    
    return {
        'total_value_generated': total_value,
        'monthly_roi': roi,
        'cost_per_detection': monthly_cost / max(stats['high_priority_new_coins'], 1)
    }
```

---

## 🆘 Troubleshooting

### Common Issues

1. **CoinGecko API Rate Limits**
   - Solution: Get CoinGecko Pro API key
   - Implement proper rate limiting
   - Use caching to reduce API calls

2. **Database Lock Errors**
   - Solution: Implement connection pooling
   - Use WAL mode for SQLite
   - Add retry logic for database operations

3. **Memory Usage Growth**
   - Solution: Implement data cleanup
   - Limit historical retention
   - Clean up old snapshots regularly

4. **Missing New Listings**
   - Solution: Verify API connectivity
   - Check data source coverage
   - Review filtering criteria

### Debug Mode
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python new_listing_detector_demo.py
```

---

This comprehensive integration guide provides everything needed to implement and maintain the new listing detection system in your trading bot infrastructure. The system provides significant competitive advantages through early detection of profitable opportunities while maintaining robust risk management and data quality standards. 