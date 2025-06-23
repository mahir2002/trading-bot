#!/usr/bin/env python3
"""
🚀 Advanced Cache Manager
Multi-tier caching system: Memory → Redis → SQLite
"""

import asyncio
import logging
import json
import sqlite3
import hashlib
import time
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle
import zlib
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

@dataclass
class CacheEntry:
    key: str
    value: Any
    expires_at: Optional[datetime]
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    compressed: bool = False

class MultiTierCacheManager:
    """
    Advanced Multi-Tier Caching System
    
    Architecture:
    Level 1: Memory Cache (fastest, limited size)
    Level 2: Redis Cache (fast, shared across instances)  
    Level 3: SQLite Cache (persistent, disk-based)
    
    Features:
    ✅ Automatic cache tiering and promotion
    ✅ Intelligent compression for large values
    ✅ TTL-based expiration
    ✅ LRU eviction policies
    ✅ Cache warming strategies
    ✅ Performance metrics and monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Configuration
        self.memory_cache_size = config.get('memory_cache_size', 1000)
        self.enable_redis = config.get('enable_redis', REDIS_AVAILABLE)
        self.enable_sqlite = config.get('enable_sqlite', True)
        self.enable_compression = config.get('enable_compression', True)
        self.compression_threshold = config.get('compression_threshold', 1024)  # 1KB
        self.default_ttl = config.get('default_ttl_seconds', 3600)  # 1 hour
        
        # Redis configuration
        self.redis_host = config.get('redis_host', 'localhost')
        self.redis_port = config.get('redis_port', 6379)
        self.redis_db = config.get('redis_db', 0)
        self.redis_password = config.get('redis_password')
        
        # SQLite configuration
        cache_dir = Path(config.get('cache_dir', 'data/cache'))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = cache_dir / 'cache.db'
        
        # Storage layers
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        
        # Statistics
        self.stats = {
            'memory_hits': 0,
            'memory_misses': 0,
            'redis_hits': 0,
            'redis_misses': 0,
            'sqlite_hits': 0,
            'sqlite_misses': 0,
            'promotions': 0,
            'evictions': 0,
            'compressions': 0,
            'total_requests': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize all cache layers"""
        try:
            # Initialize SQLite
            if self.enable_sqlite:
                await self._init_sqlite()
            
            # Initialize Redis
            if self.enable_redis:
                await self._init_redis()
            
            self.logger.info("🚀 Multi-tier cache manager initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache manager: {e}")
            return False
    
    async def _init_sqlite(self):
        """Initialize SQLite cache"""
        self.sqlite_conn = sqlite3.connect(str(self.sqlite_path), check_same_thread=False)
        self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                expires_at TEXT,
                created_at TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                size_bytes INTEGER,
                compressed BOOLEAN DEFAULT 0
            )
        ''')
        self.sqlite_conn.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)')
        self.sqlite_conn.commit()
        
        self.logger.info("✅ SQLite cache initialized")
    
    async def _init_redis(self):
        """Initialize Redis cache"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=False
            )
            
            # Test connection
            await self.redis_client.ping()
            self.logger.info("✅ Redis cache initialized")
            
        except Exception as e:
            self.logger.warning(f"Redis not available, continuing without it: {e}")
            self.redis_client = None
            self.enable_redis = False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with automatic tier promotion"""
        self.stats['total_requests'] += 1
        
        # Try memory cache first
        value = await self._get_from_memory(key)
        if value is not None:
            self.stats['memory_hits'] += 1
            return value
        
        self.stats['memory_misses'] += 1
        
        # Try Redis cache
        if self.enable_redis:
            value = await self._get_from_redis(key)
            if value is not None:
                self.stats['redis_hits'] += 1
                # Promote to memory cache
                await self._set_memory(key, value)
                self.stats['promotions'] += 1
                return value
            
            self.stats['redis_misses'] += 1
        
        # Try SQLite cache
        if self.enable_sqlite:
            value = await self._get_from_sqlite(key)
            if value is not None:
                self.stats['sqlite_hits'] += 1
                # Promote to higher tiers
                if self.enable_redis:
                    await self._set_redis(key, value)
                await self._set_memory(key, value)
                self.stats['promotions'] += 1
                return value
            
            self.stats['sqlite_misses'] += 1
        
        return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache tiers"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        try:
            # Set in all tiers
            await self._set_memory(key, value, expires_at)
            
            if self.enable_redis:
                await self._set_redis(key, value, ttl)
            
            if self.enable_sqlite:
                await self._set_sqlite(key, value, expires_at)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def _get_from_memory(self, key: str) -> Any:
        """Get from memory cache"""
        if key not in self.memory_cache:
            return None
        
        entry = self.memory_cache[key]
        
        # Check expiration
        if entry.expires_at and datetime.now() > entry.expires_at:
            del self.memory_cache[key]
            return None
        
        # Update access stats
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        return entry.value
    
    async def _set_memory(self, key: str, value: Any, expires_at: Optional[datetime] = None):
        """Set in memory cache with LRU eviction"""
        # Check if we need to evict
        if len(self.memory_cache) >= self.memory_cache_size:
            await self._evict_memory_lru()
        
        # Calculate size (approximate)
        try:
            size_bytes = len(pickle.dumps(value))
        except:
            size_bytes = len(str(value))
        
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at,
            created_at=datetime.now(),
            size_bytes=size_bytes
        )
        
        self.memory_cache[key] = entry
    
    async def _evict_memory_lru(self):
        """Evict least recently used item from memory"""
        if not self.memory_cache:
            return
        
        # Find LRU item
        lru_key = min(
            self.memory_cache.keys(),
            key=lambda k: self.memory_cache[k].last_accessed or self.memory_cache[k].created_at
        )
        
        del self.memory_cache[lru_key]
        self.stats['evictions'] += 1
    
    async def _get_from_redis(self, key: str) -> Any:
        """Get from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(f"cache:{key}")
            if data is None:
                return None
            
            # Deserialize
            entry_data = pickle.loads(data)
            
            # Check if compressed
            if entry_data.get('compressed'):
                entry_data['value'] = pickle.loads(zlib.decompress(entry_data['value']))
            
            return entry_data['value']
            
        except Exception as e:
            self.logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def _set_redis(self, key: str, value: Any, ttl: int):
        """Set in Redis cache"""
        if not self.redis_client:
            return
        
        try:
            # Prepare data
            serialized_value = pickle.dumps(value)
            compressed = False
            
            # Compress large values
            if self.enable_compression and len(serialized_value) > self.compression_threshold:
                serialized_value = zlib.compress(serialized_value)
                compressed = True
                self.stats['compressions'] += 1
            
            entry_data = {
                'value': serialized_value,
                'compressed': compressed,
                'created_at': datetime.now().isoformat()
            }
            
            # Store in Redis
            await self.redis_client.setex(
                f"cache:{key}",
                ttl,
                pickle.dumps(entry_data)
            )
            
        except Exception as e:
            self.logger.error(f"Redis set error for key {key}: {e}")
    
    async def _get_from_sqlite(self, key: str) -> Any:
        """Get from SQLite cache"""
        if not self.sqlite_conn:
            return None
        
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                'SELECT value, expires_at, compressed FROM cache_entries WHERE key = ?',
                (key,)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
            
            value_blob, expires_at_str, compressed = row
            
            # Check expiration
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now() > expires_at:
                    # Clean up expired entry
                    cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                    self.sqlite_conn.commit()
                    return None
            
            # Update access stats
            cursor.execute(
                'UPDATE cache_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?',
                (datetime.now().isoformat(), key)
            )
            self.sqlite_conn.commit()
            
            # Deserialize value
            if compressed:
                value = pickle.loads(zlib.decompress(value_blob))
            else:
                value = pickle.loads(value_blob)
            
            return value
            
        except Exception as e:
            self.logger.error(f"SQLite get error for key {key}: {e}")
            return None
    
    async def _set_sqlite(self, key: str, value: Any, expires_at: datetime):
        """Set in SQLite cache"""
        if not self.sqlite_conn:
            return
        
        try:
            # Serialize value
            serialized_value = pickle.dumps(value)
            compressed = False
            
            # Compress large values
            if self.enable_compression and len(serialized_value) > self.compression_threshold:
                serialized_value = zlib.compress(serialized_value)
                compressed = True
                self.stats['compressions'] += 1
            
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, value, expires_at, created_at, size_bytes, compressed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                key,
                serialized_value,
                expires_at.isoformat(),
                datetime.now().isoformat(),
                len(serialized_value),
                compressed
            ))
            
            self.sqlite_conn.commit()
            
        except Exception as e:
            self.logger.error(f"SQLite set error for key {key}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache tiers"""
        try:
            # Delete from memory
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Delete from Redis
            if self.redis_client:
                await self.redis_client.delete(f"cache:{key}")
            
            # Delete from SQLite
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                self.sqlite_conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def clear(self):
        """Clear all cache tiers"""
        try:
            # Clear memory
            self.memory_cache.clear()
            
            # Clear Redis
            if self.redis_client:
                keys = await self.redis_client.keys("cache:*")
                if keys:
                    await self.redis_client.delete(*keys)
            
            # Clear SQLite
            if self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('DELETE FROM cache_entries')
                self.sqlite_conn.commit()
            
            self.logger.info("🗑️ All cache tiers cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    async def cleanup_expired(self):
        """Clean up expired entries from all tiers"""
        now = datetime.now()
        
        # Clean memory cache
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.expires_at and now > entry.expires_at
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Clean SQLite cache
        if self.sqlite_conn:
            cursor = self.sqlite_conn.cursor()
            cursor.execute('DELETE FROM cache_entries WHERE expires_at < ?', (now.isoformat(),))
            deleted = cursor.rowcount
            self.sqlite_conn.commit()
            
            if deleted > 0:
                self.logger.info(f"🧹 Cleaned {deleted} expired entries from SQLite cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        memory_size = len(self.memory_cache)
        memory_bytes = sum(entry.size_bytes for entry in self.memory_cache.values())
        
        # Calculate hit rates
        total_memory_requests = self.stats['memory_hits'] + self.stats['memory_misses']
        total_redis_requests = self.stats['redis_hits'] + self.stats['redis_misses']
        total_sqlite_requests = self.stats['sqlite_hits'] + self.stats['sqlite_misses']
        
        memory_hit_rate = (self.stats['memory_hits'] / total_memory_requests * 100) if total_memory_requests > 0 else 0
        redis_hit_rate = (self.stats['redis_hits'] / total_redis_requests * 100) if total_redis_requests > 0 else 0
        sqlite_hit_rate = (self.stats['sqlite_hits'] / total_sqlite_requests * 100) if total_sqlite_requests > 0 else 0
        
        return {
            'memory_cache': {
                'entries': memory_size,
                'size_bytes': memory_bytes,
                'hit_rate_percent': memory_hit_rate,
                'max_size': self.memory_cache_size
            },
            'redis_cache': {
                'enabled': self.enable_redis,
                'hit_rate_percent': redis_hit_rate
            },
            'sqlite_cache': {
                'enabled': self.enable_sqlite,
                'hit_rate_percent': sqlite_hit_rate
            },
            'overall_stats': self.stats,
            'config': {
                'compression_enabled': self.enable_compression,
                'compression_threshold': self.compression_threshold,
                'default_ttl': self.default_ttl
            }
        }
    
    async def warm_cache(self, warm_data: Dict[str, Any], ttl: Optional[int] = None):
        """Warm cache with pre-computed data"""
        self.logger.info(f"🔥 Warming cache with {len(warm_data)} entries")
        
        for key, value in warm_data.items():
            await self.set(key, value, ttl)
        
        self.logger.info("✅ Cache warming completed")
    
    async def close(self):
        """Close all cache connections"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.sqlite_conn:
                self.sqlite_conn.close()
            
            self.logger.info("🔒 Cache manager closed")
            
        except Exception as e:
            self.logger.error(f"Error closing cache manager: {e}")

# Global cache manager instance
_cache_manager = None

async def get_cache_manager(config: Dict[str, Any] = None) -> MultiTierCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MultiTierCacheManager(config or {})
        await _cache_manager.initialize()
    return _cache_manager

# Convenience functions
async def get_cached(key: str, default: Any = None) -> Any:
    """Get value from global cache"""
    cache = await get_cache_manager()
    return await cache.get(key, default)

async def set_cached(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in global cache"""
    cache = await get_cache_manager()
    return await cache.set(key, value, ttl)

async def delete_cached(key: str) -> bool:
    """Delete key from global cache"""
    cache = await get_cache_manager()
    return await cache.delete(key)

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = f"{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()

@asynccontextmanager
async def cached_result(key: str, ttl: Optional[int] = None):
    """Context manager for caching function results"""
    cache = await get_cache_manager()
    
    # Try to get cached result
    result = await cache.get(key)
    if result is not None:
        yield result
        return
    
    # Compute result and cache it
    class ResultCapture:
        def __init__(self):
            self.result = None
        
        def __call__(self, value):
            self.result = value
            return value
    
    capture = ResultCapture()
    yield capture
    
    if capture.result is not None:
        await cache.set(key, capture.result, ttl) 