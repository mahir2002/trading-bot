#!/usr/bin/env python3
"""
Redis Utilities for AI Trading Bot
Provides caching and data management functionality
"""

import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class RedisManager:
    """Redis connection and utility manager"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.redis_client = None
        self.connected = False
        
        if REDIS_AVAILABLE:
            self._connect()
    
    def _connect(self):
        """Connect to Redis server"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'redis')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password if redis_password else None,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=False  # We'll handle encoding ourselves
            )
            
            # Test connection
            self.redis_client.ping()
            self.connected = True
            self.logger.info(f"Redis connected successfully at {redis_host}:{redis_port}")
            
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.connected or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            self.connected = False
            return False
    
    def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set a value in Redis with optional expiration"""
        if not self.is_connected():
            return False
        
        try:
            # Serialize the value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value).encode('utf-8')
            elif isinstance(value, str):
                serialized_value = value.encode('utf-8')
            else:
                serialized_value = pickle.dumps(value)
            
            # Set the value
            result = self.redis_client.set(key, serialized_value, ex=expire)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from Redis"""
        if not self.is_connected():
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                try:
                    return pickle.loads(value)
                except:
                    # Return as string if all else fails
                    return value.decode('utf-8', errors='ignore')
                    
        except Exception as e:
            self.logger.error(f"Redis GET error for key '{key}': {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        if not self.is_connected():
            return False
        
        try:
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            self.logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            self.logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in Redis"""
        if not self.is_connected():
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Redis INCREMENT error for key '{key}': {e}")
            return None
    
    def set_hash(self, key: str, mapping: Dict[str, Any], expire: int = None) -> bool:
        """Set a hash in Redis"""
        if not self.is_connected():
            return False
        
        try:
            # Serialize hash values
            serialized_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[field] = json.dumps(value)
                else:
                    serialized_mapping[field] = str(value)
            
            result = self.redis_client.hset(key, mapping=serialized_mapping)
            
            if expire:
                self.redis_client.expire(key, expire)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis HSET error for key '{key}': {e}")
            return False
    
    def get_hash(self, key: str) -> Dict[str, Any]:
        """Get a hash from Redis"""
        if not self.is_connected():
            return {}
        
        try:
            hash_data = self.redis_client.hgetall(key)
            
            # Deserialize hash values
            result = {}
            for field, value in hash_data.items():
                field_str = field.decode('utf-8') if isinstance(field, bytes) else field
                value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                
                # Try to parse as JSON
                try:
                    result[field_str] = json.loads(value_str)
                except json.JSONDecodeError:
                    result[field_str] = value_str
            
            return result
            
        except Exception as e:
            self.logger.error(f"Redis HGETALL error for key '{key}': {e}")
            return {}
    
    def add_to_list(self, key: str, value: Any, max_length: int = None) -> bool:
        """Add value to a Redis list"""
        if not self.is_connected():
            return False
        
        try:
            # Serialize the value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Add to list
            self.redis_client.lpush(key, serialized_value)
            
            # Trim list if max_length specified
            if max_length:
                self.redis_client.ltrim(key, 0, max_length - 1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis LPUSH error for key '{key}': {e}")
            return False
    
    def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get values from a Redis list"""
        if not self.is_connected():
            return []
        
        try:
            values = self.redis_client.lrange(key, start, end)
            
            # Deserialize values
            result = []
            for value in values:
                value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                
                # Try to parse as JSON
                try:
                    result.append(json.loads(value_str))
                except json.JSONDecodeError:
                    result.append(value_str)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Redis LRANGE error for key '{key}': {e}")
            return []
    
    def clear_cache(self, pattern: str = None) -> int:
        """Clear cache entries matching pattern"""
        if not self.is_connected():
            return 0
        
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                return self.redis_client.flushdb()
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Redis CLEAR error: {e}")
            return 0

class TradingCache:
    """High-level caching interface for trading bot"""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
        self.logger = redis_manager.logger
    
    def cache_price_data(self, symbol: str, timeframe: str, data: Dict, expire: int = 300):
        """Cache price data for a symbol"""
        key = f"price:{symbol}:{timeframe}"
        return self.redis.set(key, data, expire)
    
    def get_cached_price_data(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get cached price data"""
        key = f"price:{symbol}:{timeframe}"
        return self.redis.get(key)
    
    def cache_prediction(self, symbol: str, prediction: Dict, expire: int = 600):
        """Cache AI prediction"""
        key = f"prediction:{symbol}"
        prediction['timestamp'] = datetime.now().isoformat()
        return self.redis.set(key, prediction, expire)
    
    def get_cached_prediction(self, symbol: str) -> Optional[Dict]:
        """Get cached prediction"""
        key = f"prediction:{symbol}"
        return self.redis.get(key)
    
    def log_trade(self, trade_data: Dict):
        """Log trade to Redis list"""
        key = "trades:history"
        return self.redis.add_to_list(key, trade_data, max_length=1000)
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        key = "trades:history"
        return self.redis.get_list(key, 0, limit - 1)
    
    def update_bot_status(self, status: Dict):
        """Update bot status"""
        key = "bot:status"
        return self.redis.set_hash(key, status, expire=3600)
    
    def get_bot_status(self) -> Dict:
        """Get bot status"""
        key = "bot:status"
        return self.redis.get_hash(key)
    
    def increment_trade_counter(self, date: str = None) -> Optional[int]:
        """Increment daily trade counter"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        key = f"trades:count:{date}"
        return self.redis.increment(key)
    
    def get_trade_count(self, date: str = None) -> int:
        """Get daily trade count"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        key = f"trades:count:{date}"
        return self.redis.get(key, 0)

# Global Redis manager instance
redis_manager = None
trading_cache = None

def get_redis_manager(logger=None) -> RedisManager:
    """Get global Redis manager instance"""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager(logger)
    return redis_manager

def get_trading_cache(logger=None) -> TradingCache:
    """Get global trading cache instance"""
    global trading_cache
    if trading_cache is None:
        redis_mgr = get_redis_manager(logger)
        trading_cache = TradingCache(redis_mgr)
    return trading_cache 