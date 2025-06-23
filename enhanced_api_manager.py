#!/usr/bin/env python3
"""
Enhanced API Manager with Retry Logic, Caching, and Error Handling
Improves reliability and performance of API calls
"""

import time
import random
import json
import logging
import requests
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAPIManager:
    """Enhanced API manager with retry logic, caching, and rate limiting"""
    
    def __init__(self, cache_duration_minutes=5):
        self.cache = {}
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.rate_limits = {}
        self.last_requests = {}
        
    def _get_cache_key(self, url: str, params: Dict = None) -> str:
        """Generate cache key from URL and parameters"""
        cache_data = f"{url}_{json.dumps(params, sort_keys=True) if params else ''}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_duration
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for key: {cache_key[:8]}...")
            return self.cache[cache_key]['data']
        return None
    
    def _store_in_cache(self, cache_key: str, data: Any):
        """Store data in cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cached data for key: {cache_key[:8]}...")
    
    def _enforce_rate_limit(self, api_name: str, requests_per_second: float = 1.0):
        """Enforce rate limiting for API calls"""
        if api_name in self.last_requests:
            time_since_last = time.time() - self.last_requests[api_name]
            min_interval = 1.0 / requests_per_second
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logger.debug(f"Rate limiting {api_name}: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_requests[api_name] = time.time()
    
    def fetch_with_retry(self, 
                        func: Callable, 
                        max_retries: int = 3, 
                        base_delay: float = 1.0,
                        exponential_backoff: bool = True,
                        cache_key: str = None) -> Any:
        """
        Fetch data with retry logic and caching
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries
            exponential_backoff: Use exponential backoff
            cache_key: Cache key for storing results
        """
        
        # Check cache first
        if cache_key and self._is_cache_valid(cache_key):
            return self._get_from_cache(cache_key)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1}")
                result = func()
                
                # Store in cache if successful
                if cache_key:
                    self._store_in_cache(cache_key, result)
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries:
                    if exponential_backoff:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    else:
                        delay = base_delay + random.uniform(0, 0.5)
                    
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        # If we have cached data (even if expired), return it as fallback
        if cache_key and cache_key in self.cache:
            logger.warning("Using expired cache data as fallback")
            return self.cache[cache_key]['data']
        
        raise last_exception

class EnhancedCoinGeckoAPI:
    """Enhanced CoinGecko API client with improved reliability"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.pro_url = "https://pro-api.coingecko.com/api/v3"
        self.api_manager = EnhancedAPIManager(cache_duration_minutes=2)
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with enhanced error handling"""
        
        # Use Pro API if key is available
        base_url = self.pro_url if self.api_key else self.base_url
        url = f"{base_url}/{endpoint}"
        
        # Add API key to headers if available
        headers = {}
        if self.api_key:
            headers['x-cg-pro-api-key'] = self.api_key
        
        # Rate limiting
        api_name = "coingecko_pro" if self.api_key else "coingecko_free"
        rate_limit = 50 if self.api_key else 10  # requests per second
        self.api_manager._enforce_rate_limit(api_name, rate_limit)
        
        def make_request():
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        # Generate cache key
        cache_key = self.api_manager._get_cache_key(url, params)
        
        return self.api_manager.fetch_with_retry(
            func=make_request,
            max_retries=3,
            base_delay=1.0,
            cache_key=cache_key
        )
    
    def get_coins_markets(self, vs_currency='usd', per_page=250, page=1) -> Dict:
        """Get coins market data with enhanced reliability"""
        try:
            params = {
                'vs_currency': vs_currency,
                'order': 'market_cap_desc',
                'per_page': per_page,
                'page': page,
                'price_change_percentage': '1h,24h,7d,30d'
            }
            
            # Remove sparkline to avoid API errors
            # params['sparkline'] = False
            
            return self._make_request('coins/markets', params)
            
        except Exception as e:
            logger.error(f"Error fetching coins markets: {e}")
            return []
    
    def get_global_data(self) -> Dict:
        """Get global market data"""
        try:
            return self._make_request('global')
        except Exception as e:
            logger.error(f"Error fetching global data: {e}")
            return {}
    
    def get_trending(self) -> Dict:
        """Get trending coins"""
        try:
            return self._make_request('search/trending')
        except Exception as e:
            logger.error(f"Error fetching trending data: {e}")
            return {}
    
    def get_fear_greed_index(self) -> Dict:
        """Get Fear & Greed Index (alternative endpoint)"""
        try:
            # Using alternative API since CoinGecko doesn't have this
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching fear & greed index: {e}")
            return {'data': [{'value': 50, 'value_classification': 'Neutral'}]}

class EnhancedBinanceAPI:
    """Enhanced Binance API client"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.api_manager = EnhancedAPIManager(cache_duration_minutes=1)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make Binance API request"""
        url = f"{self.base_url}/{endpoint}"
        
        # Rate limiting for Binance
        self.api_manager._enforce_rate_limit("binance", 10)  # 10 requests per second
        
        def make_request():
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        
        cache_key = self.api_manager._get_cache_key(url, params)
        
        return self.api_manager.fetch_with_retry(
            func=make_request,
            max_retries=2,
            base_delay=0.5,
            cache_key=cache_key
        )
    
    def get_24hr_ticker(self) -> list:
        """Get 24hr ticker statistics"""
        try:
            return self._make_request('ticker/24hr')
        except Exception as e:
            logger.error(f"Error fetching Binance ticker: {e}")
            return []
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 500) -> list:
        """Get kline/candlestick data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            return self._make_request('klines', params)
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return []

class DataAggregator:
    """Aggregate data from multiple sources with fallbacks"""
    
    def __init__(self, coingecko_api_key: str = None):
        self.coingecko = EnhancedCoinGeckoAPI(coingecko_api_key)
        self.binance = EnhancedBinanceAPI()
        
    def get_comprehensive_market_data(self) -> Dict:
        """Get comprehensive market data with fallbacks"""
        logger.info("🚀 Fetching comprehensive market data...")
        
        market_data = {}
        
        try:
            # Primary: CoinGecko data
            logger.info("📡 Fetching CoinGecko data...")
            cg_data = self.coingecko.get_coins_markets(per_page=250)
            
            if cg_data:
                for coin in cg_data:
                    symbol = coin.get('symbol', '').upper()
                    if symbol:
                        market_data[symbol] = {
                            'name': coin.get('name', symbol),
                            'price': coin.get('current_price', 0),
                            'change_24h': coin.get('price_change_percentage_24h', 0),
                            'change_1h': coin.get('price_change_percentage_1h', 0),
                            'change_7d': coin.get('price_change_percentage_7d', 0),
                            'change_30d': coin.get('price_change_percentage_30d', 0),
                            'volume_24h': coin.get('total_volume', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'market_cap_rank': coin.get('market_cap_rank', 999),
                            'high_24h': coin.get('high_24h', 0),
                            'low_24h': coin.get('low_24h', 0),
                            'ath': coin.get('ath', 0),
                            'atl': coin.get('atl', 0),
                            'source': 'CoinGecko'
                        }
                
                logger.info(f"✅ CoinGecko: {len(market_data)} coins loaded")
            
        except Exception as e:
            logger.error(f"❌ CoinGecko fetch failed: {e}")
        
        try:
            # Fallback: Binance data
            logger.info("📡 Fetching Binance data as supplement...")
            binance_data = self.binance.get_24hr_ticker()
            
            binance_count = 0
            for ticker in binance_data:
                symbol = ticker.get('symbol', '').replace('USDT', '').replace('BUSD', '')
                
                if symbol and (symbol not in market_data or not market_data[symbol].get('price')):
                    market_data[symbol] = {
                        'name': symbol,
                        'price': float(ticker.get('lastPrice', 0)),
                        'change_24h': float(ticker.get('priceChangePercent', 0)),
                        'volume_24h': float(ticker.get('volume', 0)),
                        'high_24h': float(ticker.get('highPrice', 0)),
                        'low_24h': float(ticker.get('lowPrice', 0)),
                        'source': 'Binance'
                    }
                    binance_count += 1
            
            logger.info(f"✅ Binance: {binance_count} additional coins loaded")
            
        except Exception as e:
            logger.error(f"❌ Binance fetch failed: {e}")
        
        # Get global data
        try:
            global_data = self.coingecko.get_global_data()
            if global_data and 'data' in global_data:
                market_data['_global'] = global_data['data']
        except Exception as e:
            logger.error(f"❌ Global data fetch failed: {e}")
        
        logger.info(f"🎯 Total market data loaded: {len(market_data)} items")
        return market_data

# Usage example
if __name__ == "__main__":
    # Test the enhanced API manager
    import os
    
    api_key = os.getenv('COINGECKO_API_KEY')
    aggregator = DataAggregator(api_key)
    
    print("🚀 Testing Enhanced API Manager...")
    
    # Test data fetching
    data = aggregator.get_comprehensive_market_data()
    
    print(f"✅ Successfully loaded {len(data)} market data items")
    
    # Show some sample data
    sample_coins = list(data.keys())[:5]
    for coin in sample_coins:
        if coin != '_global':
            coin_data = data[coin]
            print(f"📊 {coin}: ${coin_data.get('price', 0):.6f} ({coin_data.get('change_24h', 0):+.2f}%)") 