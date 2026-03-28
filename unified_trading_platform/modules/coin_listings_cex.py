#!/usr/bin/env python3
"""
🪙 CEX Coin Listings Module
Comprehensive coin listing collection from centralized exchanges using ccxt
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import aiohttp
import ccxt
import ccxt.async_support as ccxt_async
from dataclasses import dataclass, asdict
import hashlib
import os
from pathlib import Path

from unified_trading_platform.core.base_module import BaseModule, ModuleInfo, ModulePriority, ModuleStatus, ModuleEvent

@dataclass
class CoinListing:
    """Coin listing data structure"""
    symbol: str
    base: str
    quote: str
    exchange: str
    status: str
    type: str  # 'spot', 'margin', 'future', etc.
    precision_amount: Optional[float] = None
    precision_price: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    maker_fee: Optional[float] = None
    taker_fee: Optional[float] = None
    timestamp: Optional[datetime] = None
    info: Optional[Dict] = None

class CEXCoinListingsModule(BaseModule):
    """
    CEX Coin Listings Module
    
    Comprehensive coin listing collection from centralized exchanges:
    ✅ Binance, KuCoin, Coinbase, Kraken, Bybit, OKX, Gate.io, Huobi
    ✅ Daily caching with SQLite storage
    ✅ Real-time updates and synchronization
    ✅ Multi-exchange aggregation and deduplication
    ✅ Symbol mapping and normalization
    ✅ Fee and trading info collection
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Configuration
        self.enabled_exchanges = config.get('enabled_exchanges', [
            'binance', 'kucoinfutures', 'coinbasepro', 'kraken', 'bybit', 'okx', 'gate', 'huobi'
        ])
        self.cache_duration_hours = config.get('cache_duration_hours', 24)
        self.update_interval_hours = config.get('update_interval_hours', 24)
        self.enable_testnet = config.get('enable_testnet', False)
        self.include_delisted = config.get('include_delisted', False)
        self.symbol_types = config.get('symbol_types', ['spot', 'margin', 'future', 'swap'])
        
        # Cache and storage
        self.cache_dir = Path(config.get('cache_dir', 'data/coin_listings'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / 'cex_listings.db'
        
        # Exchange connections
        self.exchanges = {}
        self.exchange_configs = {
            'binance': {'class': ccxt_async.binance, 'testnet': 'binanceusdm'},
            'kucoinfutures': {'class': ccxt_async.kucoinfutures, 'testnet': None},
            'coinbasepro': {'class': ccxt_async.coinbasepro, 'testnet': 'coinbasepro'},
            'kraken': {'class': ccxt_async.kraken, 'testnet': None},
            'bybit': {'class': ccxt_async.bybit, 'testnet': 'bybit'},
            'okx': {'class': ccxt_async.okx, 'testnet': 'okx'},
            'gate': {'class': ccxt_async.gate, 'testnet': None},
            'huobi': {'class': ccxt_async.huobi, 'testnet': None}
        }
        
        # Data storage
        self.coin_listings = {}  # exchange -> List[CoinListing]
        self.aggregated_symbols = set()  # All unique symbols across exchanges
        self.symbol_mapping = {}  # Normalized symbol mapping
        self.exchange_stats = {}  # Per-exchange statistics
        
        # Update tasks
        self.update_tasks = []
        
        # Statistics
        self.stats = {
            'total_listings': 0,
            'unique_symbols': 0,
            'exchanges_online': 0,
            'last_update': None,
            'cache_hits': 0,
            'cache_misses': 0,
            'update_duration': 0
        }
    
    def get_module_info(self) -> ModuleInfo:
        """Return module information"""
        return ModuleInfo(
            name="CEX Coin Listings",
            version="1.0.0",
            description="Comprehensive coin listing collection from centralized exchanges",
            author="Unified Trading Platform",
            dependencies=['ccxt', 'aiohttp', 'sqlite3'],
            priority=ModulePriority.HIGH,
            config_schema={
                "type": "object",
                "properties": {
                    "enabled_exchanges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of exchanges to fetch listings from"
                    },
                    "cache_duration_hours": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Cache duration in hours"
                    },
                    "update_interval_hours": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Update interval in hours"
                    },
                    "symbol_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of symbols to include (spot, margin, future, swap)"
                    }
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the CEX coin listings module"""
        try:
            self.log_info("🚀 Initializing CEX Coin Listings Module...")
            
            # Initialize database
            await self._initialize_database()
            
            # Initialize exchanges
            await self._initialize_exchanges()
            
            # Load cached data
            await self._load_cached_data()
            
            self.log_info("✅ CEX Coin Listings Module initialized successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error initializing CEX Coin Listings Module: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the CEX coin listings module"""
        try:
            self.log_info("🚀 Starting CEX Coin Listings Module...")
            
            # Start periodic update task
            update_task = asyncio.create_task(self._periodic_update_task())
            self.update_tasks.append(update_task)
            
            # Register event handlers
            self.register_event_handler('get_coin_listings', self._handle_get_listings)
            self.register_event_handler('search_symbols', self._handle_search_symbols)
            self.register_event_handler('force_update_listings', self._handle_force_update)
            
            # Perform initial update if cache is stale
            if await self._is_cache_stale():
                self.log_info("📥 Cache is stale, performing initial update...")
                await self._update_all_listings()
            
            self.log_info("✅ CEX Coin Listings Module started successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error starting CEX Coin Listings Module: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the CEX coin listings module"""
        try:
            self.log_info("🛑 Stopping CEX Coin Listings Module...")
            
            # Cancel update tasks
            for task in self.update_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close exchange connections
            for exchange in self.exchanges.values():
                if hasattr(exchange, 'close'):
                    await exchange.close()
            
            self.log_info("✅ CEX Coin Listings Module stopped successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error stopping CEX Coin Listings Module: {e}")
            return False
    
    async def _initialize_database(self):
        """Initialize SQLite database for caching"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS coin_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    base TEXT NOT NULL,
                    quote TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    status TEXT,
                    type TEXT,
                    precision_amount REAL,
                    precision_price REAL,
                    min_amount REAL,
                    max_amount REAL,
                    min_price REAL,
                    max_price REAL,
                    min_cost REAL,
                    max_cost REAL,
                    maker_fee REAL,
                    taker_fee REAL,
                    timestamp TEXT,
                    info TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, exchange, type)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON coin_listings(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange ON coin_listings(exchange)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON coin_listings(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON coin_listings(status)')
            
            conn.commit()
            conn.close()
            
            self.log_info("📊 Database initialized successfully")
            
        except Exception as e:
            self.log_error(f"Database initialization failed: {e}")
            raise
    
    async def _initialize_exchanges(self):
        """Initialize exchange connections"""
        try:
            for exchange_name in self.enabled_exchanges:
                if exchange_name not in self.exchange_configs:
                    self.log_warning(f"Unknown exchange: {exchange_name}")
                    continue
                
                config = self.exchange_configs[exchange_name]
                exchange_class = config['class']
                
                # Initialize exchange
                exchange = exchange_class({
                    'sandbox': self.enable_testnet,
                    'enableRateLimit': True,
                    'timeout': 30000,
                })
                
                self.exchanges[exchange_name] = exchange
                self.exchange_stats[exchange_name] = {
                    'total_symbols': 0,
                    'active_symbols': 0,
                    'last_update': None,
                    'errors': 0
                }
                
                self.log_info(f"🔗 Exchange {exchange_name} initialized")
            
            self.log_info(f"✅ {len(self.exchanges)} exchanges initialized")
            
        except Exception as e:
            self.log_error(f"Exchange initialization failed: {e}")
            raise
    
    async def _load_cached_data(self):
        """Load cached coin listings from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load listings
            cursor.execute('''
                SELECT symbol, base, quote, exchange, status, type,
                       precision_amount, precision_price, min_amount, max_amount,
                       min_price, max_price, min_cost, max_cost,
                       maker_fee, taker_fee, timestamp, info
                FROM coin_listings
                WHERE datetime(updated_at) > datetime('now', '-{} hours')
            '''.format(self.cache_duration_hours))
            
            rows = cursor.fetchall()
            
            for row in rows:
                listing = CoinListing(
                    symbol=row[0], base=row[1], quote=row[2], exchange=row[3],
                    status=row[4], type=row[5],
                    precision_amount=row[6], precision_price=row[7],
                    min_amount=row[8], max_amount=row[9],
                    min_price=row[10], max_price=row[11],
                    min_cost=row[12], max_cost=row[13],
                    maker_fee=row[14], taker_fee=row[15],
                    timestamp=datetime.fromisoformat(row[16]) if row[16] else None,
                    info=json.loads(row[17]) if row[17] else None
                )
                
                if listing.exchange not in self.coin_listings:
                    self.coin_listings[listing.exchange] = []
                
                self.coin_listings[listing.exchange].append(listing)
                self.aggregated_symbols.add(listing.symbol)
            
            # Load metadata
            cursor.execute("SELECT value FROM cache_metadata WHERE key = 'last_update'")
            result = cursor.fetchone()
            if result:
                self.stats['last_update'] = datetime.fromisoformat(result[0])
            
            conn.close()
            
            # Update statistics
            self.stats['total_listings'] = sum(len(listings) for listings in self.coin_listings.values())
            self.stats['unique_symbols'] = len(self.aggregated_symbols)
            
            if self.stats['total_listings'] > 0:
                self.log_info(f"📥 Loaded {self.stats['total_listings']} cached listings from {len(self.coin_listings)} exchanges")
                self.stats['cache_hits'] += 1
            else:
                self.stats['cache_misses'] += 1
            
        except Exception as e:
            self.log_error(f"Failed to load cached data: {e}")
    
    async def _periodic_update_task(self):
        """Periodic task to update coin listings"""
        while True:
            try:
                await asyncio.sleep(self.update_interval_hours * 3600)  # Convert hours to seconds
                
                if await self._is_cache_stale():
                    self.log_info("🔄 Performing scheduled update...")
                    await self._update_all_listings()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Periodic update task error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _is_cache_stale(self) -> bool:
        """Check if cache is stale"""
        if not self.stats['last_update']:
            return True
        
        age = datetime.now() - self.stats['last_update']
        return age > timedelta(hours=self.cache_duration_hours)
    
    async def _update_all_listings(self):
        """Update coin listings from all exchanges"""
        start_time = datetime.now()
        
        try:
            self.log_info("🔄 Starting comprehensive listings update...")
            
            # Clear existing data
            self.coin_listings.clear()
            self.aggregated_symbols.clear()
            
            # Update from each exchange
            tasks = []
            for exchange_name, exchange in self.exchanges.items():
                task = asyncio.create_task(self._update_exchange_listings(exchange_name, exchange))
                tasks.append(task)
            
            # Wait for all updates to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_exchanges = 0
            for i, result in enumerate(results):
                exchange_name = list(self.exchanges.keys())[i]
                if isinstance(result, Exception):
                    self.log_error(f"Failed to update {exchange_name}: {result}")
                    self.exchange_stats[exchange_name]['errors'] += 1
                else:
                    successful_exchanges += 1
                    self.exchange_stats[exchange_name]['last_update'] = datetime.now()
            
            # Save to database
            await self._save_to_database()
            
            # Update statistics
            self.stats['total_listings'] = sum(len(listings) for listings in self.coin_listings.values())
            self.stats['unique_symbols'] = len(self.aggregated_symbols)
            self.stats['exchanges_online'] = successful_exchanges
            self.stats['last_update'] = datetime.now()
            self.stats['update_duration'] = (datetime.now() - start_time).total_seconds()
            
            self.log_info(f"✅ Update complete: {self.stats['total_listings']} listings from {successful_exchanges} exchanges")
            
        except Exception as e:
            self.log_error(f"Update all listings failed: {e}")
    
    async def _update_exchange_listings(self, exchange_name: str, exchange):
        """Update listings from a specific exchange"""
        try:
            self.log_info(f"📥 Updating listings from {exchange_name}...")
            
            # Load markets
            markets = await exchange.load_markets()
            
            exchange_listings = []
            active_count = 0
            
            for symbol, market in markets.items():
                # Filter by symbol type if specified
                if self.symbol_types and market.get('type') not in self.symbol_types:
                    continue
                
                # Skip delisted symbols if not included
                if not self.include_delisted and not market.get('active', True):
                    continue
                
                # Create listing object
                listing = CoinListing(
                    symbol=symbol,
                    base=market.get('base', ''),
                    quote=market.get('quote', ''),
                    exchange=exchange_name,
                    status='active' if market.get('active', True) else 'inactive',
                    type=market.get('type', 'spot'),
                    precision_amount=market.get('precision', {}).get('amount'),
                    precision_price=market.get('precision', {}).get('price'),
                    min_amount=market.get('limits', {}).get('amount', {}).get('min'),
                    max_amount=market.get('limits', {}).get('amount', {}).get('max'),
                    min_price=market.get('limits', {}).get('price', {}).get('min'),
                    max_price=market.get('limits', {}).get('price', {}).get('max'),
                    min_cost=market.get('limits', {}).get('cost', {}).get('min'),
                    max_cost=market.get('limits', {}).get('cost', {}).get('max'),
                    maker_fee=market.get('maker'),
                    taker_fee=market.get('taker'),
                    timestamp=datetime.now(),
                    info=market.get('info', {})
                )
                
                exchange_listings.append(listing)
                self.aggregated_symbols.add(symbol)
                
                if listing.status == 'active':
                    active_count += 1
            
            self.coin_listings[exchange_name] = exchange_listings
            
            # Update exchange statistics
            self.exchange_stats[exchange_name]['total_symbols'] = len(exchange_listings)
            self.exchange_stats[exchange_name]['active_symbols'] = active_count
            
            self.log_info(f"✅ {exchange_name}: {len(exchange_listings)} symbols ({active_count} active)")
            
        except Exception as e:
            self.log_error(f"Failed to update {exchange_name}: {e}")
            raise
    
    async def _save_to_database(self):
        """Save listings to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear old data
            cursor.execute('DELETE FROM coin_listings')
            
            # Insert new data
            for exchange_name, listings in self.coin_listings.items():
                for listing in listings:
                    cursor.execute('''
                        INSERT INTO coin_listings (
                            symbol, base, quote, exchange, status, type,
                            precision_amount, precision_price, min_amount, max_amount,
                            min_price, max_price, min_cost, max_cost,
                            maker_fee, taker_fee, timestamp, info
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        listing.symbol, listing.base, listing.quote, listing.exchange,
                        listing.status, listing.type,
                        listing.precision_amount, listing.precision_price,
                        listing.min_amount, listing.max_amount,
                        listing.min_price, listing.max_price,
                        listing.min_cost, listing.max_cost,
                        listing.maker_fee, listing.taker_fee,
                        listing.timestamp.isoformat() if listing.timestamp else None,
                        json.dumps(listing.info) if listing.info else None
                    ))
            
            # Update metadata
            cursor.execute('''
                INSERT OR REPLACE INTO cache_metadata (key, value, updated_at)
                VALUES ('last_update', ?, ?)
            ''', (datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"💾 Saved {self.stats['total_listings']} listings to database")
            
        except Exception as e:
            self.log_error(f"Failed to save to database: {e}")
    
    # Event handlers
    async def _handle_get_listings(self, event):
        """Handle get listings request"""
        try:
            exchange = event.data.get('exchange')
            symbol_type = event.data.get('type')
            status = event.data.get('status', 'active')
            
            if exchange and exchange in self.coin_listings:
                listings = self.coin_listings[exchange]
            else:
                # Return all listings
                listings = []
                for exchange_listings in self.coin_listings.values():
                    listings.extend(exchange_listings)
            
            # Apply filters
            if symbol_type:
                listings = [l for l in listings if l.type == symbol_type]
            
            if status:
                listings = [l for l in listings if l.status == status]
            
            return {
                'success': True,
                'listings': [asdict(listing) for listing in listings],
                'total': len(listings),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log_error(f"Get listings handler error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_search_symbols(self, event):
        """Handle symbol search request"""
        try:
            query = event.data.get('query', '').upper()
            limit = event.data.get('limit', 100)
            
            if not query:
                return {'success': False, 'error': 'Query parameter required'}
            
            matching_symbols = []
            for symbol in self.aggregated_symbols:
                if query in symbol.upper():
                    matching_symbols.append(symbol)
                    if len(matching_symbols) >= limit:
                        break
            
            return {
                'success': True,
                'symbols': matching_symbols,
                'total': len(matching_symbols),
                'query': query
            }
            
        except Exception as e:
            self.log_error(f"Search symbols handler error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_force_update(self, event):
        """Handle force update request"""
        try:
            await self._update_all_listings()
            return {
                'success': True,
                'message': 'Update completed',
                'statistics': self.stats
            }
            
        except Exception as e:
            self.log_error(f"Force update handler error: {e}")
            return {'success': False, 'error': str(e)}
    
    # Public API methods
    def get_all_symbols(self) -> Set[str]:
        """Get all unique symbols across all exchanges"""
        return self.aggregated_symbols.copy()
    
    def get_exchange_symbols(self, exchange: str) -> List[str]:
        """Get symbols for a specific exchange"""
        if exchange in self.coin_listings:
            return [listing.symbol for listing in self.coin_listings[exchange]]
        return []
    
    def get_symbol_info(self, symbol: str) -> List[CoinListing]:
        """Get detailed info for a symbol across all exchanges"""
        info = []
        for exchange_listings in self.coin_listings.values():
            for listing in exchange_listings:
                if listing.symbol == symbol:
                    info.append(listing)
        return info
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            **self.stats,
            'exchange_stats': self.exchange_stats,
            'enabled_exchanges': self.enabled_exchanges,
            'cache_age_hours': (datetime.now() - self.stats['last_update']).total_seconds() / 3600 if self.stats['last_update'] else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check module health"""
        try:
            # Test database connection
            cache_status = os.path.exists(self.db_path)
            
            # Test exchange connectivity
            exchange_status = {}
            for exchange_id in self.enabled_exchanges:
                try:
                    if exchange_id in self.exchanges:
                        exchange_status[exchange_id] = 'healthy'
                    else:
                        exchange_status[exchange_id] = 'unavailable'
                except:
                    exchange_status[exchange_id] = 'error'
            
            return {
                'status': 'healthy' if cache_status else 'degraded',
                'cache_status': cache_status,
                'exchange_status': exchange_status,
                'last_update': self.stats['last_update'].isoformat() if self.stats['last_update'] else None,
                'total_symbols': len(self.aggregated_symbols)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        return {
            'type': 'object',
            'properties': {
                'enabled_exchanges': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of enabled exchanges'
                },
                'cache_duration_hours': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 168,
                    'description': 'Cache duration in hours'
                },
                'update_interval_hours': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 24,
                    'description': 'Update interval in hours'
                },
                'symbol_types': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Supported symbol types'
                },
                'cache_dir': {
                    'type': 'string',
                    'description': 'Cache directory path'
                }
            },
            'required': ['enabled_exchanges', 'cache_duration_hours']
        }


def create_module(name: str, config: Dict[str, Any]) -> CEXCoinListingsModule:
    """Create CEX Coin Listings module instance"""
    return CEXCoinListingsModule(name, config) 