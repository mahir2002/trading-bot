#!/usr/bin/env python3
"""
🔍 New Listing Detector Module
Advanced new coin listing detection with historical tracking and CoinGecko integration
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass, asdict
import hashlib
import os
from pathlib import Path
import time

from unified_trading_platform.core.base_module import BaseModule, ModuleInfo, ModulePriority, ModuleStatus, ModuleEvent

@dataclass
class NewListingEvent:
    """New listing event data structure"""
    coin_id: str
    symbol: str
    name: str
    source: str  # 'cex', 'dex', 'coingecko'
    exchange: Optional[str] = None
    network: Optional[str] = None
    contract_address: Optional[str] = None
    detected_at: Optional[datetime] = None
    market_cap_usd: Optional[float] = None
    price_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    coingecko_id: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    image_url: Optional[str] = None
    categories: Optional[List[str]] = None
    ai_analysis_priority: Optional[str] = None  # 'high', 'medium', 'low'
    risk_score: Optional[float] = None
    info: Optional[Dict] = None

@dataclass
class HistoricalSnapshot:
    """Historical coin listing snapshot"""
    snapshot_id: str
    date: datetime
    source: str
    total_coins: int
    unique_symbols: int
    coin_list_hash: str
    coin_list: Set[str]
    metadata: Optional[Dict] = None

class NewListingDetectorModule(BaseModule):
    """
    New Listing Detector Module
    
    Advanced new coin listing detection system:
    ✅ Historical tracking and comparison
    ✅ Multi-source detection (CEX, DEX, CoinGecko)
    ✅ CoinGecko API integration for enhanced data
    ✅ GeckoTerminal scraping for DeFi tokens
    ✅ AI-ready new coin prioritization
    ✅ Risk assessment and categorization
    ✅ Automatic notification system
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Configuration
        self.check_interval_hours = config.get('check_interval_hours', 6)
        self.coingecko_api_key = config.get('coingecko_api_key', '')
        self.enable_geckoterminal = config.get('enable_geckoterminal', True)
        self.enable_notifications = config.get('enable_notifications', True)
        self.min_market_cap_usd = config.get('min_market_cap_usd', 100000)
        self.max_new_listings_per_check = config.get('max_new_listings_per_check', 50)
        self.historical_retention_days = config.get('historical_retention_days', 30)
        
        # Cache and storage
        self.cache_dir = Path(config.get('cache_dir', 'data/new_listings'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / 'new_listings.db'
        self.ai_data_path = self.cache_dir / 'new_coins_for_ai.json'
        
        # API endpoints
        self.coingecko_base_url = 'https://api.coingecko.com/api/v3'
        self.geckoterminal_base_url = 'https://api.geckoterminal.com/api/v2'
        
        # Session management
        self.session = None
        self.rate_limiter = {
            'coingecko': {'last_call': 0, 'min_interval': 1.2},  # 50 calls/minute
            'geckoterminal': {'last_call': 0, 'min_interval': 0.1}  # More lenient
        }
        
        # Data storage
        self.historical_snapshots = {}  # date -> HistoricalSnapshot
        self.current_coins = set()
        self.new_listings_today = []
        self.coingecko_coins = {}  # id -> detailed info
        
        # Statistics
        self.stats = {
            'total_new_listings_detected': 0,
            'new_listings_today': 0,
            'last_check': None,
            'total_snapshots': 0,
            'coingecko_coins_tracked': 0,
            'high_priority_new_coins': 0,
            'api_calls_today': 0
        }
    
    def get_module_info(self) -> ModuleInfo:
        """Return module information"""
        return ModuleInfo(
            name="New Listing Detector",
            version="1.0.0",
            description="Advanced new coin listing detection with CoinGecko integration",
            author="Unified Trading Platform",
            dependencies=['aiohttp', 'sqlite3'],
            priority=ModulePriority.HIGH,
            config_schema=self.get_config_schema()
        )
    
    async def initialize(self) -> bool:
        """Initialize the new listing detector module"""
        try:
            self.log_info("🚀 Initializing New Listing Detector Module...")
            
            # Initialize database
            await self._initialize_database()
            
            # Initialize HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AI-Trading-Bot/1.0'}
            )
            
            # Load historical data
            await self._load_historical_data()
            
            # Test API connectivity
            await self._test_api_connectivity()
            
            self.log_info("✅ New Listing Detector Module initialized successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error initializing New Listing Detector Module: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the new listing detector module"""
        try:
            self.log_info("🚀 Starting New Listing Detector Module...")
            
            # Start periodic check task
            check_task = asyncio.create_task(self._periodic_check_task())
            
            # Register event handlers
            self.register_event_handler('detect_new_listings', self._handle_detect_new_listings)
            self.register_event_handler('get_new_listings', self._handle_get_new_listings)
            self.register_event_handler('get_ai_data', self._handle_get_ai_data)
            
            # Perform initial check
            await self._check_for_new_listings()
            
            self.log_info("✅ New Listing Detector Module started successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error starting New Listing Detector Module: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the new listing detector module"""
        try:
            self.log_info("🛑 Stopping New Listing Detector Module...")
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            self.log_info("✅ New Listing Detector Module stopped successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error stopping New Listing Detector Module: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check module health"""
        try:
            # Test database connection
            db_status = os.path.exists(self.db_path)
            
            # Test API connectivity
            api_status = {}
            if self.coingecko_api_key:
                api_status['coingecko'] = 'configured'
            else:
                api_status['coingecko'] = 'no_api_key'
            
            return {
                'status': 'healthy' if db_status else 'degraded',
                'db_status': db_status,
                'api_status': api_status,
                'last_check': self.stats['last_check'].isoformat() if self.stats['last_check'] else None,
                'new_listings_today': self.stats['new_listings_today']
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
                'check_interval_hours': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 24,
                    'description': 'Check interval in hours'
                },
                'coingecko_api_key': {
                    'type': 'string',
                    'description': 'CoinGecko Pro API key for enhanced data'
                },
                'enable_geckoterminal': {
                    'type': 'boolean',
                    'description': 'Enable GeckoTerminal integration'
                },
                'min_market_cap_usd': {
                    'type': 'number',
                    'minimum': 0,
                    'description': 'Minimum market cap for new listings'
                },
                'cache_dir': {
                    'type': 'string',
                    'description': 'Cache directory path'
                }
            }
        }
    
    async def _initialize_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Historical snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_snapshots (
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
            ''')
            
            # New listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS new_listings (
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
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_date ON historical_snapshots(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_detected_at ON new_listings(detected_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_priority ON new_listings(ai_analysis_priority)')
            
            conn.commit()
            conn.close()
            
            self.log_info("📊 Database initialized successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize database: {e}")
            raise
    
    async def _test_api_connectivity(self):
        """Test API connectivity"""
        try:
            # Test CoinGecko
            coingecko_status = await self._test_coingecko_api()
            
            # Test GeckoTerminal
            geckoterminal_status = False
            if self.enable_geckoterminal:
                geckoterminal_status = await self._test_geckoterminal_api()
            
            self.log_info(f"🌐 API Connectivity: CoinGecko={coingecko_status}, GeckoTerminal={geckoterminal_status}")
            
        except Exception as e:
            self.log_warning(f"API connectivity test failed: {e}")
    
    async def _test_coingecko_api(self) -> bool:
        """Test CoinGecko API connectivity"""
        try:
            url = f"{self.coingecko_base_url}/ping"
            headers = {}
            if self.coingecko_api_key:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return True
            return False
            
        except Exception:
            return False
    
    async def _test_geckoterminal_api(self) -> bool:
        """Test GeckoTerminal API connectivity"""
        try:
            url = f"{self.geckoterminal_base_url}/networks"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return True
            return False
            
        except Exception:
            return False
    
    async def _load_historical_data(self):
        """Load historical snapshots from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT snapshot_id, date, source, total_coins, unique_symbols, 
                       coin_list_hash, coin_list, metadata
                FROM historical_snapshots
                WHERE date >= ?
                ORDER BY date DESC
            ''', ((datetime.now() - timedelta(days=self.historical_retention_days)).isoformat(),))
            
            for row in cursor.fetchall():
                snapshot = HistoricalSnapshot(
                    snapshot_id=row[0],
                    date=datetime.fromisoformat(row[1]),
                    source=row[2],
                    total_coins=row[3],
                    unique_symbols=row[4],
                    coin_list_hash=row[5],
                    coin_list=set(json.loads(row[6])) if row[6] else set(),
                    metadata=json.loads(row[7]) if row[7] else None
                )
                
                date_key = snapshot.date.date().isoformat()
                if date_key not in self.historical_snapshots:
                    self.historical_snapshots[date_key] = {}
                self.historical_snapshots[date_key][snapshot.source] = snapshot
            
            conn.close()
            
            self.stats['total_snapshots'] = len(self.historical_snapshots)
            self.log_info(f"📚 Loaded {self.stats['total_snapshots']} historical snapshots")
            
        except Exception as e:
            self.log_error(f"Failed to load historical data: {e}")
    
    async def _periodic_check_task(self):
        """Periodic new listing check task"""
        while True:
            try:
                await asyncio.sleep(self.check_interval_hours * 3600)
                await self._check_for_new_listings()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Periodic check task error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _check_for_new_listings(self):
        """Main new listing detection logic"""
        try:
            self.log_info("🔍 Starting new listing detection...")
            
            # Get current date
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Collect current coin lists from all sources
            current_sources = await self._collect_current_coin_lists()
            
            # Create today's snapshots
            today_snapshots = {}
            for source, coin_list in current_sources.items():
                snapshot = self._create_snapshot(source, coin_list)
                today_snapshots[source] = snapshot
                await self._save_snapshot(snapshot)
            
            # Compare with yesterday's snapshots
            new_listings = []
            yesterday_key = yesterday.isoformat()
            
            if yesterday_key in self.historical_snapshots:
                for source, today_snapshot in today_snapshots.items():
                    if source in self.historical_snapshots[yesterday_key]:
                        yesterday_snapshot = self.historical_snapshots[yesterday_key][source]
                        
                        # Find new coins
                        new_coins = today_snapshot.coin_list - yesterday_snapshot.coin_list
                        
                        if new_coins:
                            self.log_info(f"🆕 Found {len(new_coins)} new listings in {source}")
                            
                            # Process new coins
                            for coin_id in new_coins:
                                new_listing = await self._process_new_coin(coin_id, source)
                                if new_listing:
                                    new_listings.append(new_listing)
            
            # Enhance with CoinGecko data
            enhanced_listings = await self._enhance_with_coingecko(new_listings)
            
            # Filter and prioritize
            prioritized_listings = await self._prioritize_new_listings(enhanced_listings)
            
            # Save to database and AI data file
            await self._save_new_listings(prioritized_listings)
            await self._update_ai_data_file(prioritized_listings)
            
            # Send notifications
            if self.enable_notifications and prioritized_listings:
                await self._send_new_listing_notifications(prioritized_listings)
            
            # Update statistics
            self.stats['new_listings_today'] = len(prioritized_listings)
            self.stats['total_new_listings_detected'] += len(prioritized_listings)
            self.stats['last_check'] = datetime.now()
            
            self.log_info(f"✅ New listing detection complete: {len(prioritized_listings)} new coins detected")
            
        except Exception as e:
            self.log_error(f"❌ New listing detection failed: {e}")
    
    async def _collect_current_coin_lists(self) -> Dict[str, Set[str]]:
        """Collect current coin lists from all sources"""
        coin_lists = {}
        
        try:
            # Get from CoinGecko
            coingecko_coins = await self._get_coingecko_coin_list()
            if coingecko_coins:
                coin_lists['coingecko'] = set(coingecko_coins.keys())
                self.coingecko_coins = coingecko_coins
                self.stats['coingecko_coins_tracked'] = len(coingecko_coins)
            
            # Get from GeckoTerminal
            if self.enable_geckoterminal:
                geckoterminal_coins = await self._get_geckoterminal_coins()
                if geckoterminal_coins:
                    coin_lists['geckoterminal'] = geckoterminal_coins
            
        except Exception as e:
            self.log_error(f"Failed to collect coin lists: {e}")
        
        return coin_lists
    
    async def _get_coingecko_coin_list(self) -> Dict[str, Dict]:
        """Get comprehensive coin list from CoinGecko"""
        try:
            await self._rate_limit('coingecko')
            
            url = f"{self.coingecko_base_url}/coins/list"
            headers = {}
            if self.coingecko_api_key:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
            params = {
                'include_platform': 'true'
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    coins_data = await response.json()
                    
                    # Convert to dict for easier processing
                    coins_dict = {}
                    for coin in coins_data:
                        coins_dict[coin['id']] = coin
                    
                    self.log_info(f"📈 CoinGecko: {len(coins_dict)} coins retrieved")
                    return coins_dict
                else:
                    self.log_warning(f"CoinGecko API error: {response.status}")
                    return {}
            
        except Exception as e:
            self.log_error(f"Failed to get CoinGecko coin list: {e}")
            return {}
    
    async def _get_geckoterminal_coins(self) -> Set[str]:
        """Get trending coins from GeckoTerminal"""
        try:
            await self._rate_limit('geckoterminal')
            
            # Get trending pools
            url = f"{self.geckoterminal_base_url}/tokens/trending"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    coins = set()
                    for token in data.get('data', []):
                        if 'attributes' in token:
                            symbol = token['attributes'].get('symbol')
                            address = token['attributes'].get('address')
                            if symbol and address:
                                coins.add(f"{symbol}_{address}")
                    
                    self.log_info(f"🔥 GeckoTerminal: {len(coins)} trending tokens retrieved")
                    return coins
                else:
                    self.log_warning(f"GeckoTerminal API error: {response.status}")
                    return set()
            
        except Exception as e:
            self.log_error(f"Failed to get GeckoTerminal coins: {e}")
            return set()
    
    def _create_snapshot(self, source: str, coin_list: Set[str]) -> HistoricalSnapshot:
        """Create a historical snapshot"""
        coin_list_json = json.dumps(sorted(list(coin_list)))
        coin_list_hash = hashlib.sha256(coin_list_json.encode()).hexdigest()
        
        snapshot = HistoricalSnapshot(
            snapshot_id=f"{source}_{datetime.now().date().isoformat()}_{coin_list_hash[:8]}",
            date=datetime.now(),
            source=source,
            total_coins=len(coin_list),
            unique_symbols=len(set(coin.split('_')[0] for coin in coin_list if '_' in coin)),
            coin_list_hash=coin_list_hash,
            coin_list=coin_list
        )
        
        return snapshot
    
    async def _save_snapshot(self, snapshot: HistoricalSnapshot):
        """Save snapshot to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO historical_snapshots (
                    snapshot_id, date, source, total_coins, unique_symbols,
                    coin_list_hash, coin_list, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.snapshot_id,
                snapshot.date.isoformat(),
                snapshot.source,
                snapshot.total_coins,
                snapshot.unique_symbols,
                snapshot.coin_list_hash,
                json.dumps(list(snapshot.coin_list)),
                json.dumps(snapshot.metadata) if snapshot.metadata else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_error(f"Failed to save snapshot: {e}")
    
    async def _process_new_coin(self, coin_id: str, source: str) -> Optional[NewListingEvent]:
        """Process a newly detected coin"""
        try:
            # Extract basic info
            if source == 'coingecko' and coin_id in self.coingecko_coins:
                coin_data = self.coingecko_coins[coin_id]
                
                new_listing = NewListingEvent(
                    coin_id=coin_id,
                    symbol=coin_data.get('symbol', '').upper(),
                    name=coin_data.get('name', ''),
                    source=source,
                    coingecko_id=coin_id,
                    detected_at=datetime.now()
                )
                
                # Add platform info if available
                platforms = coin_data.get('platforms', {})
                if platforms:
                    # Use first platform as primary
                    platform_name = list(platforms.keys())[0]
                    contract_address = platforms[platform_name]
                    new_listing.network = platform_name
                    new_listing.contract_address = contract_address
                
                return new_listing
            
            elif source == 'geckoterminal':
                # Parse GeckoTerminal format: SYMBOL_ADDRESS
                if '_' in coin_id:
                    symbol, address = coin_id.split('_', 1)
                    
                    new_listing = NewListingEvent(
                        coin_id=coin_id,
                        symbol=symbol.upper(),
                        name=symbol,
                        source=source,
                        contract_address=address,
                        detected_at=datetime.now()
                    )
                    
                    return new_listing
            
            return None
            
        except Exception as e:
            self.log_error(f"Failed to process new coin {coin_id}: {e}")
            return None
    
    async def _enhance_with_coingecko(self, new_listings: List[NewListingEvent]) -> List[NewListingEvent]:
        """Enhance new listings with detailed CoinGecko data"""
        enhanced_listings = []
        
        for listing in new_listings:
            try:
                if listing.coingecko_id:
                    # Get detailed data from CoinGecko
                    detailed_data = await self._get_coingecko_coin_details(listing.coingecko_id)
                    
                    if detailed_data:
                        # Update listing with detailed data
                        market_data = detailed_data.get('market_data', {})
                        
                        listing.market_cap_usd = market_data.get('market_cap', {}).get('usd')
                        listing.price_usd = market_data.get('current_price', {}).get('usd')
                        listing.volume_24h_usd = market_data.get('total_volume', {}).get('usd')
                        listing.total_supply = market_data.get('total_supply')
                        listing.circulating_supply = market_data.get('circulating_supply')
                        
                        listing.description = detailed_data.get('description', {}).get('en', '')[:500]
                        listing.homepage = detailed_data.get('links', {}).get('homepage', [None])[0]
                        listing.image_url = detailed_data.get('image', {}).get('small')
                        listing.categories = detailed_data.get('categories', [])
                
                enhanced_listings.append(listing)
                
            except Exception as e:
                self.log_error(f"Failed to enhance listing {listing.coin_id}: {e}")
                enhanced_listings.append(listing)  # Add anyway
        
        return enhanced_listings
    
    async def _get_coingecko_coin_details(self, coin_id: str) -> Optional[Dict]:
        """Get detailed coin data from CoinGecko"""
        try:
            await self._rate_limit('coingecko')
            
            url = f"{self.coingecko_base_url}/coins/{coin_id}"
            headers = {}
            if self.coingecko_api_key:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false'
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.log_warning(f"CoinGecko details error for {coin_id}: {response.status}")
                    return None
            
        except Exception as e:
            self.log_error(f"Failed to get CoinGecko details for {coin_id}: {e}")
            return None
    
    async def _prioritize_new_listings(self, new_listings: List[NewListingEvent]) -> List[NewListingEvent]:
        """Prioritize new listings for AI analysis"""
        prioritized = []
        
        for listing in new_listings:
            try:
                # Calculate AI analysis priority
                priority_score = 0
                risk_score = 50  # Default medium risk
                
                # Market cap factor
                if listing.market_cap_usd:
                    if listing.market_cap_usd >= 100_000_000:  # $100M+
                        priority_score += 30
                        risk_score -= 20
                    elif listing.market_cap_usd >= 10_000_000:  # $10M+
                        priority_score += 20
                        risk_score -= 10
                    elif listing.market_cap_usd >= 1_000_000:  # $1M+
                        priority_score += 10
                    else:
                        risk_score += 20  # Higher risk for low market cap
                
                # Volume factor
                if listing.volume_24h_usd:
                    if listing.volume_24h_usd >= 1_000_000:  # $1M+ daily volume
                        priority_score += 20
                        risk_score -= 10
                    elif listing.volume_24h_usd >= 100_000:  # $100K+ daily volume
                        priority_score += 10
                
                # Category factor
                if listing.categories:
                    high_interest_categories = [
                        'decentralized-finance-defi', 'layer-1', 'layer-2',
                        'artificial-intelligence', 'gaming', 'metaverse'
                    ]
                    if any(cat in high_interest_categories for cat in listing.categories):
                        priority_score += 15
                        risk_score -= 5
                
                # Contract verification factor
                if listing.contract_address and len(listing.contract_address) == 42:  # Ethereum address
                    priority_score += 5
                    risk_score -= 5
                
                # Determine priority level
                if priority_score >= 50:
                    listing.ai_analysis_priority = 'high'
                    self.stats['high_priority_new_coins'] += 1
                elif priority_score >= 25:
                    listing.ai_analysis_priority = 'medium'
                else:
                    listing.ai_analysis_priority = 'low'
                
                listing.risk_score = max(0, min(100, risk_score))
                
                # Filter by minimum market cap
                if (not listing.market_cap_usd or 
                    listing.market_cap_usd >= self.min_market_cap_usd):
                    prioritized.append(listing)
                
            except Exception as e:
                self.log_error(f"Failed to prioritize listing {listing.coin_id}: {e}")
                prioritized.append(listing)  # Add with default priority
        
        # Sort by priority and market cap
        prioritized.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}.get(x.ai_analysis_priority, 0),
            x.market_cap_usd or 0
        ), reverse=True)
        
        # Limit results
        return prioritized[:self.max_new_listings_per_check]
    
    async def _save_new_listings(self, new_listings: List[NewListingEvent]):
        """Save new listings to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for listing in new_listings:
                cursor.execute('''
                    INSERT INTO new_listings (
                        coin_id, symbol, name, source, exchange, network,
                        contract_address, detected_at, market_cap_usd, price_usd,
                        volume_24h_usd, total_supply, circulating_supply,
                        coingecko_id, description, homepage, image_url,
                        categories, ai_analysis_priority, risk_score, info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing.coin_id, listing.symbol, listing.name, listing.source,
                    listing.exchange, listing.network, listing.contract_address,
                    listing.detected_at.isoformat() if listing.detected_at else None,
                    listing.market_cap_usd, listing.price_usd, listing.volume_24h_usd,
                    listing.total_supply, listing.circulating_supply,
                    listing.coingecko_id, listing.description, listing.homepage,
                    listing.image_url, json.dumps(listing.categories) if listing.categories else None,
                    listing.ai_analysis_priority, listing.risk_score,
                    json.dumps(listing.info) if listing.info else None
                ))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"💾 Saved {len(new_listings)} new listings to database")
            
        except Exception as e:
            self.log_error(f"Failed to save new listings: {e}")
    
    async def _update_ai_data_file(self, new_listings: List[NewListingEvent]):
        """Update AI data file with new listings"""
        try:
            ai_data = {
                'timestamp': datetime.now().isoformat(),
                'total_new_listings': len(new_listings),
                'high_priority_count': len([l for l in new_listings if l.ai_analysis_priority == 'high']),
                'medium_priority_count': len([l for l in new_listings if l.ai_analysis_priority == 'medium']),
                'low_priority_count': len([l for l in new_listings if l.ai_analysis_priority == 'low']),
                'new_listings': []
            }
            
            # Convert new listings to dict format
            for listing in new_listings:
                listing_dict = asdict(listing)
                if listing_dict['detected_at']:
                    listing_dict['detected_at'] = listing_dict['detected_at'].isoformat()
                ai_data['new_listings'].append(listing_dict)
            
            # Save to AI data file
            with open(self.ai_data_path, 'w') as f:
                json.dump(ai_data, f, indent=2)
            
            self.log_info(f"🧠 AI data file updated with {len(new_listings)} new listings")
            
        except Exception as e:
            self.log_error(f"Failed to update AI data file: {e}")
    
    async def _send_new_listing_notifications(self, new_listings: List[NewListingEvent]):
        """Send notifications for new listings"""
        try:
            high_priority = [l for l in new_listings if l.ai_analysis_priority == 'high']
            
            if high_priority:
                # Convert to dict for event sending
                high_priority_dicts = []
                for listing in high_priority[:5]:  # Top 5
                    listing_dict = asdict(listing)
                    if listing_dict['detected_at']:
                        listing_dict['detected_at'] = listing_dict['detected_at'].isoformat()
                    high_priority_dicts.append(listing_dict)
                
                # Send event for high priority new listings
                await self.send_event('new_high_priority_listings', {
                    'count': len(high_priority),
                    'listings': high_priority_dicts
                })
                
                self.log_info(f"🚨 Sent notification for {len(high_priority)} high priority new listings")
            
        except Exception as e:
            self.log_error(f"Failed to send notifications: {e}")
    
    async def _rate_limit(self, api: str):
        """Rate limiting for API calls"""
        if api in self.rate_limiter:
            limiter = self.rate_limiter[api]
            elapsed = time.time() - limiter['last_call']
            
            if elapsed < limiter['min_interval']:
                wait_time = limiter['min_interval'] - elapsed
                await asyncio.sleep(wait_time)
            
            limiter['last_call'] = time.time()
            self.stats['api_calls_today'] += 1
    
    # Event handlers
    async def _handle_detect_new_listings(self, event):
        """Handle manual new listing detection request"""
        try:
            await self._check_for_new_listings()
            return {
                'success': True,
                'new_listings_found': self.stats['new_listings_today'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_get_new_listings(self, event):
        """Handle get new listings request"""
        try:
            limit = event.data.get('limit', 50)
            priority = event.data.get('priority')  # 'high', 'medium', 'low'
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM new_listings
                WHERE detected_at >= ?
            '''
            params = [(datetime.now() - timedelta(days=1)).isoformat()]
            
            if priority:
                query += ' AND ai_analysis_priority = ?'
                params.append(priority)
            
            query += ' ORDER BY detected_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dict format
            columns = [desc[0] for desc in cursor.description]
            listings = []
            for row in rows:
                listing_dict = dict(zip(columns, row))
                listings.append(listing_dict)
            
            conn.close()
            
            return {
                'success': True,
                'listings': listings,
                'total': len(listings)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_get_ai_data(self, event):
        """Handle get AI data request"""
        try:
            if os.path.exists(self.ai_data_path):
                with open(self.ai_data_path, 'r') as f:
                    ai_data = json.load(f)
                
                return {
                    'success': True,
                    'ai_data': ai_data,
                    'file_path': str(self.ai_data_path)
                }
            else:
                return {
                    'success': False,
                    'error': 'AI data file not found'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Public API methods
    def get_statistics(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            **self.stats,
            'check_interval_hours': self.check_interval_hours,
            'min_market_cap_usd': self.min_market_cap_usd,
            'coingecko_api_configured': bool(self.coingecko_api_key),
            'geckoterminal_enabled': self.enable_geckoterminal
        }


def create_module(name: str, config: Dict[str, Any]) -> NewListingDetectorModule:
    """Create New Listing Detector module instance"""
    return NewListingDetectorModule(name, config) 