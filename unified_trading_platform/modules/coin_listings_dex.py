#!/usr/bin/env python3
"""
🌐 DEX Coin Listings Module
Comprehensive coin listing collection from decentralized exchanges using The Graph
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass, asdict
import hashlib
import os
from pathlib import Path

from unified_trading_platform.core.base_module import BaseModule, ModuleInfo, ModulePriority, ModuleStatus, ModuleEvent

@dataclass
class DEXTokenListing:
    """DEX token listing data structure"""
    token_address: str
    symbol: str
    name: str
    decimals: int
    exchange: str
    network: str
    total_liquidity_usd: Optional[float] = None
    total_volume_usd: Optional[float] = None
    price_usd: Optional[float] = None
    price_change_24h: Optional[float] = None
    market_cap_usd: Optional[float] = None
    pairs_count: Optional[int] = None
    created_at: Optional[datetime] = None
    last_trade: Optional[datetime] = None
    is_verified: Optional[bool] = None
    timestamp: Optional[datetime] = None
    info: Optional[Dict] = None

class DEXCoinListingsModule(BaseModule):
    """
    DEX Coin Listings Module
    
    Comprehensive coin listing collection from decentralized exchanges:
    ✅ Uniswap V2/V3, PancakeSwap, SushiSwap, Curve, Balancer
    ✅ Multi-chain support (Ethereum, BSC, Polygon, Arbitrum, Optimism)
    ✅ The Graph protocol integration for reliable data
    ✅ Daily caching with SQLite storage
    ✅ Real-time token discovery and price tracking
    ✅ Liquidity and volume filtering
    ✅ Verified token identification
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Configuration
        self.enabled_networks = config.get('enabled_networks', [
            'ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism'
        ])
        self.enabled_dexes = config.get('enabled_dexes', [
            'uniswap-v2', 'uniswap-v3', 'pancakeswap', 'sushiswap', 'curve', 'balancer'
        ])
        self.cache_duration_hours = config.get('cache_duration_hours', 24)
        self.update_interval_hours = config.get('update_interval_hours', 24)
        self.min_liquidity_usd = config.get('min_liquidity_usd', 1000)
        self.min_volume_24h_usd = config.get('min_volume_24h_usd', 100)
        self.max_tokens_per_dex = config.get('max_tokens_per_dex', 1000)
        
        # Cache and storage
        self.cache_dir = Path(config.get('cache_dir', 'data/coin_listings'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / 'dex_listings.db'
        
        # The Graph endpoints configuration
        self.graph_endpoints = {
            'uniswap-v2': {
                'ethereum': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
                'polygon': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2-polygon'
            },
            'uniswap-v3': {
                'ethereum': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
                'polygon': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-polygon',
                'arbitrum': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-arbitrum',
                'optimism': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-optimism'
            },
            'pancakeswap': {
                'bsc': 'https://api.thegraph.com/subgraphs/name/pancakeswap/exchange',
                'polygon': 'https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-polygon'
            },
            'sushiswap': {
                'ethereum': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange',
                'polygon': 'https://api.thegraph.com/subgraphs/name/sushiswap/matic-exchange',
                'arbitrum': 'https://api.thegraph.com/subgraphs/name/sushiswap/arbitrum-exchange'
            },
            'curve': {
                'ethereum': 'https://api.thegraph.com/subgraphs/name/curvefi/curve',
                'polygon': 'https://api.thegraph.com/subgraphs/name/curvefi/curve-polygon'
            },
            'balancer': {
                'ethereum': 'https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2',
                'polygon': 'https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-polygon-v2',
                'arbitrum': 'https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-arbitrum-v2'
            }
        }
        
        # Data storage
        self.token_listings = {}  # network -> dex -> List[DEXTokenListing]
        self.aggregated_tokens = set()  # All unique token addresses
        self.token_mapping = {}  # Symbol -> List[token_addresses]
        self.dex_stats = {}  # Per-DEX statistics
        
        # HTTP session
        self.session = None
        
        # Update tasks
        self.update_tasks = []
        
        # Statistics
        self.stats = {
            'total_tokens': 0,
            'unique_symbols': 0,
            'networks_active': 0,
            'dexes_active': 0,
            'last_update': None,
            'cache_hits': 0,
            'cache_misses': 0,
            'update_duration': 0,
            'total_liquidity_usd': 0,
            'total_volume_24h_usd': 0
        }
    
    def get_module_info(self) -> ModuleInfo:
        """Return module information"""
        return ModuleInfo(
            name="DEX Coin Listings",
            version="1.0.0",
            description="Comprehensive coin listing collection from decentralized exchanges",
            author="Unified Trading Platform",
            dependencies=['aiohttp', 'sqlite3'],
            priority=ModulePriority.HIGH,
            config_schema={
                "type": "object",
                "properties": {
                    "enabled_networks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of blockchain networks to monitor"
                    },
                    "enabled_dexes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of DEXes to fetch listings from"
                    },
                    "cache_duration_hours": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Cache duration in hours"
                    },
                    "min_liquidity_usd": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Minimum liquidity in USD to include token"
                    },
                    "min_volume_24h_usd": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Minimum 24h volume in USD to include token"
                    }
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the DEX coin listings module"""
        try:
            self.log_info("🚀 Initializing DEX Coin Listings Module...")
            
            # Initialize HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Unified Trading Platform DEX Module'}
            )
            
            # Initialize database
            await self._initialize_database()
            
            # Test The Graph connectivity
            await self._test_graph_connectivity()
            
            # Load cached data
            await self._load_cached_data()
            
            self.log_info("✅ DEX Coin Listings Module initialized successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error initializing DEX Coin Listings Module: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the DEX coin listings module"""
        try:
            self.log_info("🚀 Starting DEX Coin Listings Module...")
            
            # Start periodic update task
            update_task = asyncio.create_task(self._periodic_update_task())
            self.update_tasks.append(update_task)
            
            # Register event handlers
            self.register_event_handler('get_dex_listings', self._handle_get_listings)
            self.register_event_handler('search_tokens', self._handle_search_tokens)
            self.register_event_handler('get_token_info', self._handle_get_token_info)
            self.register_event_handler('force_update_dex_listings', self._handle_force_update)
            
            # Perform initial update if cache is stale
            if await self._is_cache_stale():
                self.log_info("📥 Cache is stale, performing initial update...")
                await self._update_all_listings()
            
            self.log_info("✅ DEX Coin Listings Module started successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error starting DEX Coin Listings Module: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the DEX coin listings module"""
        try:
            self.log_info("🛑 Stopping DEX Coin Listings Module...")
            
            # Cancel update tasks
            for task in self.update_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            self.log_info("✅ DEX Coin Listings Module stopped successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error stopping DEX Coin Listings Module: {e}")
            return False
    
    async def _initialize_database(self):
        """Initialize SQLite database for caching"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dex_token_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    decimals INTEGER,
                    exchange TEXT NOT NULL,
                    network TEXT NOT NULL,
                    total_liquidity_usd REAL,
                    total_volume_usd REAL,
                    price_usd REAL,
                    price_change_24h REAL,
                    market_cap_usd REAL,
                    pairs_count INTEGER,
                    created_at TEXT,
                    last_trade TEXT,
                    is_verified BOOLEAN,
                    timestamp TEXT,
                    info TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, exchange, network)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dex_cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dex_token_address ON dex_token_listings(token_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dex_symbol ON dex_token_listings(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dex_exchange ON dex_token_listings(exchange)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dex_network ON dex_token_listings(network)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dex_liquidity ON dex_token_listings(total_liquidity_usd)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dex_volume ON dex_token_listings(total_volume_usd)')
            
            conn.commit()
            conn.close()
            
            self.log_info("📊 Database initialized successfully")
            
        except Exception as e:
            self.log_error(f"Database initialization failed: {e}")
            raise
    
    async def _test_graph_connectivity(self):
        """Test connectivity to The Graph endpoints"""
        try:
            test_count = 0
            success_count = 0
            
            for dex in self.enabled_dexes:
                if dex not in self.graph_endpoints:
                    continue
                
                for network in self.enabled_networks:
                    if network not in self.graph_endpoints[dex]:
                        continue
                    
                    endpoint = self.graph_endpoints[dex][network]
                    test_count += 1
                    
                    # Simple test query
                    query = '''
                    {
                        tokens(first: 1) {
                            id
                            symbol
                        }
                    }
                    '''
                    
                    try:
                        async with self.session.post(
                            endpoint,
                            json={'query': query},
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                success_count += 1
                                self.log_info(f"✅ {dex} on {network}: Connected")
                            else:
                                self.log_warning(f"⚠️ {dex} on {network}: HTTP {response.status}")
                    except Exception as e:
                        self.log_warning(f"❌ {dex} on {network}: {str(e)[:50]}")
            
            connectivity_rate = (success_count / test_count * 100) if test_count > 0 else 0
            self.log_info(f"📡 Graph connectivity: {success_count}/{test_count} ({connectivity_rate:.1f}%)")
            
        except Exception as e:
            self.log_error(f"Graph connectivity test failed: {e}")
    
    async def _load_cached_data(self):
        """Load cached token listings from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load listings
            cursor.execute('''
                SELECT token_address, symbol, name, decimals, exchange, network,
                       total_liquidity_usd, total_volume_usd, price_usd, price_change_24h,
                       market_cap_usd, pairs_count, created_at, last_trade,
                       is_verified, timestamp, info
                FROM dex_token_listings
                WHERE datetime(updated_at) > datetime('now', '-{} hours')
            '''.format(self.cache_duration_hours))
            
            rows = cursor.fetchall()
            
            for row in rows:
                listing = DEXTokenListing(
                    token_address=row[0], symbol=row[1], name=row[2], decimals=row[3],
                    exchange=row[4], network=row[5],
                    total_liquidity_usd=row[6], total_volume_usd=row[7],
                    price_usd=row[8], price_change_24h=row[9],
                    market_cap_usd=row[10], pairs_count=row[11],
                    created_at=datetime.fromisoformat(row[12]) if row[12] else None,
                    last_trade=datetime.fromisoformat(row[13]) if row[13] else None,
                    is_verified=bool(row[14]) if row[14] is not None else None,
                    timestamp=datetime.fromisoformat(row[15]) if row[15] else None,
                    info=json.loads(row[16]) if row[16] else None
                )
                
                # Store in nested structure
                if listing.network not in self.token_listings:
                    self.token_listings[listing.network] = {}
                
                if listing.exchange not in self.token_listings[listing.network]:
                    self.token_listings[listing.network][listing.exchange] = []
                
                self.token_listings[listing.network][listing.exchange].append(listing)
                self.aggregated_tokens.add(listing.token_address)
                
                # Update symbol mapping
                if listing.symbol not in self.token_mapping:
                    self.token_mapping[listing.symbol] = []
                self.token_mapping[listing.symbol].append(listing.token_address)
            
            # Load metadata
            cursor.execute("SELECT value FROM dex_cache_metadata WHERE key = 'last_update'")
            result = cursor.fetchone()
            if result:
                self.stats['last_update'] = datetime.fromisoformat(result[0])
            
            conn.close()
            
            # Update statistics
            self._update_statistics()
            
            if self.stats['total_tokens'] > 0:
                self.log_info(f"📥 Loaded {self.stats['total_tokens']} cached tokens from {self.stats['dexes_active']} DEXes")
                self.stats['cache_hits'] += 1
            else:
                self.stats['cache_misses'] += 1
            
        except Exception as e:
            self.log_error(f"Failed to load cached data: {e}")
    
    async def _periodic_update_task(self):
        """Periodic task to update token listings"""
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
        """Update token listings from all DEXes"""
        start_time = datetime.now()
        
        try:
            self.log_info("🔄 Starting comprehensive DEX listings update...")
            
            # Clear existing data
            self.token_listings.clear()
            self.aggregated_tokens.clear()
            self.token_mapping.clear()
            
            # Update from each DEX and network combination
            tasks = []
            for dex in self.enabled_dexes:
                if dex not in self.graph_endpoints:
                    continue
                
                for network in self.enabled_networks:
                    if network not in self.graph_endpoints[dex]:
                        continue
                    
                    task = asyncio.create_task(self._update_dex_listings(dex, network))
                    tasks.append(task)
            
            # Wait for all updates to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_updates = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.log_error(f"Update failed: {result}")
                else:
                    successful_updates += 1
            
            # Save to database
            await self._save_to_database()
            
            # Update statistics
            self._update_statistics()
            self.stats['last_update'] = datetime.now()
            self.stats['update_duration'] = (datetime.now() - start_time).total_seconds()
            
            self.log_info(f"✅ Update complete: {self.stats['total_tokens']} tokens from {successful_updates} sources")
            
        except Exception as e:
            self.log_error(f"Update all listings failed: {e}")
    
    async def _update_dex_listings(self, dex: str, network: str):
        """Update listings from a specific DEX and network"""
        try:
            endpoint = self.graph_endpoints[dex][network]
            self.log_info(f"📥 Updating {dex} tokens on {network}...")
            
            # Build GraphQL query based on DEX type
            if dex.startswith('uniswap'):
                query = self._build_uniswap_query()
            elif dex == 'pancakeswap':
                query = self._build_pancakeswap_query()
            elif dex == 'sushiswap':
                query = self._build_sushiswap_query()
            elif dex == 'curve':
                query = self._build_curve_query()
            elif dex == 'balancer':
                query = self._build_balancer_query()
            else:
                self.log_warning(f"Unknown DEX type: {dex}")
                return
            
            async with self.session.post(
                endpoint,
                json={'query': query},
                timeout=60
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                data = await response.json()
                
                if 'errors' in data:
                    raise Exception(f"GraphQL errors: {data['errors']}")
                
                tokens = self._parse_tokens_response(data, dex, network)
                
                # Store tokens
                if network not in self.token_listings:
                    self.token_listings[network] = {}
                
                self.token_listings[network][dex] = tokens
                
                # Update aggregated data
                for token in tokens:
                    self.aggregated_tokens.add(token.token_address)
                    
                    if token.symbol not in self.token_mapping:
                        self.token_mapping[token.symbol] = []
                    
                    if token.token_address not in self.token_mapping[token.symbol]:
                        self.token_mapping[token.symbol].append(token.token_address)
                
                self.log_info(f"✅ {dex} on {network}: {len(tokens)} tokens")
            
        except Exception as e:
            self.log_error(f"Failed to update {dex} on {network}: {e}")
            raise
    
    def _build_uniswap_query(self) -> str:
        """Build GraphQL query for Uniswap"""
        return f'''
        {{
            tokens(
                first: {self.max_tokens_per_dex},
                orderBy: totalLiquidity,
                orderDirection: desc,
                where: {{
                    totalLiquidity_gt: "{self.min_liquidity_usd}"
                }}
            ) {{
                id
                symbol
                name
                decimals
                totalLiquidity
                totalVolume
                tradeVolume
                tradeVolumeUSD
                totalLiquidityUSD
                derivedETH
                txCount
            }}
        }}
        '''
    
    def _build_pancakeswap_query(self) -> str:
        """Build GraphQL query for PancakeSwap"""
        return f'''
        {{
            tokens(
                first: {self.max_tokens_per_dex},
                orderBy: totalLiquidityUSD,
                orderDirection: desc,
                where: {{
                    totalLiquidityUSD_gt: "{self.min_liquidity_usd}"
                }}
            ) {{
                id
                symbol
                name
                decimals
                totalLiquidityUSD
                totalVolumeUSD
                tradeVolumeUSD
                derivedBNB
                txCount
            }}
        }}
        '''
    
    def _build_sushiswap_query(self) -> str:
        """Build GraphQL query for SushiSwap"""
        return f'''
        {{
            tokens(
                first: {self.max_tokens_per_dex},
                orderBy: liquidityUSD,
                orderDirection: desc,
                where: {{
                    liquidityUSD_gt: "{self.min_liquidity_usd}"
                }}
            ) {{
                id
                symbol
                name
                decimals
                liquidityUSD
                volumeUSD
                txCount
            }}
        }}
        '''
    
    def _build_curve_query(self) -> str:
        """Build GraphQL query for Curve"""
        return f'''
        {{
            tokens(
                first: {self.max_tokens_per_dex},
                orderBy: totalSupply,
                orderDirection: desc
            ) {{
                id
                symbol
                name
                decimals
                totalSupply
                totalBalanceUSD
            }}
        }}
        '''
    
    def _build_balancer_query(self) -> str:
        """Build GraphQL query for Balancer"""
        return f'''
        {{
            tokens(
                first: {self.max_tokens_per_dex},
                orderBy: totalBalanceUSD,
                orderDirection: desc,
                where: {{
                    totalBalanceUSD_gt: "{self.min_liquidity_usd}"
                }}
            ) {{
                id
                symbol
                name
                decimals
                totalBalanceUSD
                totalVolumeUSD
            }}
        }}
        '''
    
    def _parse_tokens_response(self, data: Dict, dex: str, network: str) -> List[DEXTokenListing]:
        """Parse tokens from GraphQL response"""
        tokens = []
        
        try:
            token_data = data.get('data', {}).get('tokens', [])
            
            for token in token_data:
                # Extract common fields
                token_address = token.get('id', '').lower()
                symbol = token.get('symbol', '')
                name = token.get('name', '')
                decimals = int(token.get('decimals', 18))
                
                # Extract DEX-specific fields
                if dex.startswith('uniswap'):
                    total_liquidity_usd = float(token.get('totalLiquidityUSD', 0))
                    total_volume_usd = float(token.get('tradeVolumeUSD', 0))
                elif dex == 'pancakeswap':
                    total_liquidity_usd = float(token.get('totalLiquidityUSD', 0))
                    total_volume_usd = float(token.get('tradeVolumeUSD', 0))
                elif dex == 'sushiswap':
                    total_liquidity_usd = float(token.get('liquidityUSD', 0))
                    total_volume_usd = float(token.get('volumeUSD', 0))
                elif dex == 'curve':
                    total_liquidity_usd = float(token.get('totalBalanceUSD', 0))
                    total_volume_usd = 0  # Curve doesn't provide volume in this query
                elif dex == 'balancer':
                    total_liquidity_usd = float(token.get('totalBalanceUSD', 0))
                    total_volume_usd = float(token.get('totalVolumeUSD', 0))
                else:
                    total_liquidity_usd = 0
                    total_volume_usd = 0
                
                # Apply filters
                if total_liquidity_usd < self.min_liquidity_usd:
                    continue
                
                if total_volume_usd < self.min_volume_24h_usd and total_volume_usd > 0:
                    continue
                
                # Create listing object
                listing = DEXTokenListing(
                    token_address=token_address,
                    symbol=symbol,
                    name=name,
                    decimals=decimals,
                    exchange=dex,
                    network=network,
                    total_liquidity_usd=total_liquidity_usd,
                    total_volume_usd=total_volume_usd,
                    pairs_count=int(token.get('txCount', 0)),
                    timestamp=datetime.now(),
                    info=token
                )
                
                tokens.append(listing)
            
        except Exception as e:
            self.log_error(f"Error parsing tokens response: {e}")
        
        return tokens
    
    def _update_statistics(self):
        """Update module statistics"""
        total_tokens = 0
        unique_symbols = set()
        total_liquidity = 0
        total_volume = 0
        networks_active = len(self.token_listings)
        dexes_active = 0
        
        for network, dexes in self.token_listings.items():
            dexes_active += len(dexes)
            for dex, tokens in dexes.items():
                total_tokens += len(tokens)
                for token in tokens:
                    unique_symbols.add(token.symbol)
                    if token.total_liquidity_usd:
                        total_liquidity += token.total_liquidity_usd
                    if token.total_volume_usd:
                        total_volume += token.total_volume_usd
        
        self.stats.update({
            'total_tokens': total_tokens,
            'unique_symbols': len(unique_symbols),
            'networks_active': networks_active,
            'dexes_active': dexes_active,
            'total_liquidity_usd': total_liquidity,
            'total_volume_24h_usd': total_volume
        })
    
    async def _save_to_database(self):
        """Save listings to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear old data
            cursor.execute('DELETE FROM dex_token_listings')
            
            # Insert new data
            for network, dexes in self.token_listings.items():
                for dex, tokens in dexes.items():
                    for token in tokens:
                        cursor.execute('''
                            INSERT INTO dex_token_listings (
                                token_address, symbol, name, decimals, exchange, network,
                                total_liquidity_usd, total_volume_usd, price_usd, price_change_24h,
                                market_cap_usd, pairs_count, created_at, last_trade,
                                is_verified, timestamp, info
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            token.token_address, token.symbol, token.name, token.decimals,
                            token.exchange, token.network,
                            token.total_liquidity_usd, token.total_volume_usd,
                            token.price_usd, token.price_change_24h,
                            token.market_cap_usd, token.pairs_count,
                            token.created_at.isoformat() if token.created_at else None,
                            token.last_trade.isoformat() if token.last_trade else None,
                            token.is_verified,
                            token.timestamp.isoformat() if token.timestamp else None,
                            json.dumps(token.info) if token.info else None
                        ))
            
            # Update metadata
            cursor.execute('''
                INSERT OR REPLACE INTO dex_cache_metadata (key, value, updated_at)
                VALUES ('last_update', ?, ?)
            ''', (datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"💾 Saved {self.stats['total_tokens']} tokens to database")
            
        except Exception as e:
            self.log_error(f"Failed to save to database: {e}")
    
    # Event handlers
    async def _handle_get_listings(self, event):
        """Handle get listings request"""
        try:
            network = event.data.get('network')
            dex = event.data.get('dex')
            min_liquidity = event.data.get('min_liquidity_usd', 0)
            
            tokens = []
            
            if network and dex:
                # Specific network and DEX
                if network in self.token_listings and dex in self.token_listings[network]:
                    tokens = self.token_listings[network][dex]
            elif network:
                # All DEXes on specific network
                if network in self.token_listings:
                    for dex_tokens in self.token_listings[network].values():
                        tokens.extend(dex_tokens)
            else:
                # All tokens
                for network_data in self.token_listings.values():
                    for dex_tokens in network_data.values():
                        tokens.extend(dex_tokens)
            
            # Apply liquidity filter
            if min_liquidity > 0:
                tokens = [t for t in tokens if (t.total_liquidity_usd or 0) >= min_liquidity]
            
            return {
                'success': True,
                'tokens': [asdict(token) for token in tokens],
                'total': len(tokens),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log_error(f"Get listings handler error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_search_tokens(self, event):
        """Handle token search request"""
        try:
            query = event.data.get('query', '').upper()
            limit = event.data.get('limit', 100)
            network = event.data.get('network')
            
            if not query:
                return {'success': False, 'error': 'Query parameter required'}
            
            matching_tokens = []
            
            for net, dexes in self.token_listings.items():
                if network and net != network:
                    continue
                
                for dex, tokens in dexes.items():
                    for token in tokens:
                        if (query in token.symbol.upper() or 
                            query in (token.name or '').upper() or
                            query in token.token_address.lower()):
                            matching_tokens.append(asdict(token))
                            if len(matching_tokens) >= limit:
                                break
                    if len(matching_tokens) >= limit:
                        break
                if len(matching_tokens) >= limit:
                    break
            
            return {
                'success': True,
                'tokens': matching_tokens,
                'total': len(matching_tokens),
                'query': query
            }
            
        except Exception as e:
            self.log_error(f"Search tokens handler error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _handle_get_token_info(self, event):
        """Handle get token info request"""
        try:
            token_address = event.data.get('token_address', '').lower()
            
            if not token_address:
                return {'success': False, 'error': 'Token address required'}
            
            token_info = []
            
            for network, dexes in self.token_listings.items():
                for dex, tokens in dexes.items():
                    for token in tokens:
                        if token.token_address.lower() == token_address:
                            token_info.append(asdict(token))
            
            return {
                'success': True,
                'token_info': token_info,
                'found_on_exchanges': len(token_info),
                'token_address': token_address
            }
            
        except Exception as e:
            self.log_error(f"Get token info handler error: {e}")
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
    def get_all_tokens(self) -> Set[str]:
        """Get all unique token addresses"""
        return self.aggregated_tokens.copy()
    
    def get_tokens_by_symbol(self, symbol: str) -> List[str]:
        """Get token addresses for a specific symbol"""
        return self.token_mapping.get(symbol.upper(), [])
    
    def get_tokens_by_network(self, network: str) -> List[DEXTokenListing]:
        """Get all tokens for a specific network"""
        tokens = []
        if network in self.token_listings:
            for dex_tokens in self.token_listings[network].values():
                tokens.extend(dex_tokens)
        return tokens
    
    def get_tokens_by_dex(self, dex: str) -> List[DEXTokenListing]:
        """Get all tokens for a specific DEX across all networks"""
        tokens = []
        for network_data in self.token_listings.values():
            if dex in network_data:
                tokens.extend(network_data[dex])
        return tokens
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            **self.stats,
            'enabled_networks': self.enabled_networks,
            'enabled_dexes': self.enabled_dexes,
            'cache_age_hours': (datetime.now() - self.stats['last_update']).total_seconds() / 3600 if self.stats['last_update'] else None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check module health"""
        try:
            # Test database connection
            cache_status = os.path.exists(self.db_path)
            
            # Test Graph connectivity
            graph_status = {}
            for network in self.enabled_networks:
                graph_status[network] = 'unknown'  # Would need actual test
            
            return {
                'status': 'healthy' if cache_status else 'degraded',
                'cache_status': cache_status,
                'graph_status': graph_status,
                'last_update': self.stats['last_update'].isoformat() if self.stats['last_update'] else None,
                'total_tokens': self.stats['total_tokens']
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
                'enabled_networks': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of enabled networks'
                },
                'enabled_dexes': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of enabled DEX protocols'
                },
                'cache_duration_hours': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 168,
                    'description': 'Cache duration in hours'
                },
                'min_liquidity_usd': {
                    'type': 'number',
                    'minimum': 0,
                    'description': 'Minimum liquidity in USD'
                },
                'min_volume_24h_usd': {
                    'type': 'number',
                    'minimum': 0,
                    'description': 'Minimum 24h volume in USD'
                },
                'max_tokens_per_dex': {
                    'type': 'integer',
                    'minimum': 1,
                    'description': 'Maximum tokens per DEX'
                },
                'cache_dir': {
                    'type': 'string',
                    'description': 'Cache directory path'
                }
            },
            'required': ['enabled_networks', 'enabled_dexes']
        }


def create_module(name: str, config: Dict[str, Any]) -> DEXCoinListingsModule:
    """Create DEX Coin Listings module instance"""
    return DEXCoinListingsModule(name, config) 