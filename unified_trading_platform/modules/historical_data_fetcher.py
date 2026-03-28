#!/usr/bin/env python3
"""
📈 Historical Data Fetcher Module
Fetches 30-day OHLCV historical data for newly detected coins from multiple sources
"""

import asyncio
import logging
import json
import sqlite3
import csv
import ccxt.async_support as ccxt
import aiohttp
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import os
from pathlib import Path
from dataclasses import dataclass, asdict
import numpy as np

from unified_trading_platform.core.base_module import BaseModule, ModuleInfo, ModulePriority, ModuleStatus, ModuleEvent

@dataclass
class OHLCVData:
    """OHLCV data structure"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    symbol: str
    exchange: Optional[str] = None
    date: Optional[str] = None

@dataclass
class HistoricalDataset:
    """Complete historical dataset for a coin"""
    coin_id: str
    symbol: str
    name: str
    start_date: datetime
    end_date: datetime
    data_points: int
    sources: List[str]
    ohlcv_data: List[OHLCVData]
    metadata: Dict[str, Any]
    created_at: datetime

class HistoricalDataFetcherModule(BaseModule):
    """
    Historical Data Fetcher Module
    
    Comprehensive historical data collection system:
    ✅ 30-day OHLCV data fetching
    ✅ CoinGecko API integration
    ✅ CCXT multi-exchange support
    ✅ SQLite and CSV storage
    ✅ Data quality validation
    ✅ Rate limiting and error handling
    ✅ AI-ready data preparation
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Configuration
        self.coingecko_api_key = config.get('coingecko_api_key', '')
        self.data_retention_days = config.get('data_retention_days', 30)
        self.enable_ccxt_fetching = config.get('enable_ccxt_fetching', True)
        self.enable_csv_export = config.get('enable_csv_export', True)
        self.data_quality_threshold = config.get('data_quality_threshold', 0.8)  # 80% data completeness
        
        # Storage configuration
        self.cache_dir = Path(config.get('cache_dir', 'data/historical_data'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / 'historical_data.db'
        self.csv_dir = self.cache_dir / 'csv_exports'
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        # API endpoints
        self.coingecko_base_url = 'https://api.coingecko.com/api/v3'
        
        # Exchange configurations
        self.supported_exchanges = {
            'binance': {'class': ccxt.binance, 'timeframes': ['1d'], 'limit': 30},
            'coinbasepro': {'class': ccxt.coinbasepro, 'timeframes': ['1d'], 'limit': 30},
            'kraken': {'class': ccxt.kraken, 'timeframes': ['1d'], 'limit': 30},
            'bybit': {'class': ccxt.bybit, 'timeframes': ['1d'], 'limit': 30},
            'okx': {'class': ccxt.okx, 'timeframes': ['1d'], 'limit': 30}
        }
        
        # Session management
        self.session = None
        self.exchanges = {}  # Exchange instances
        self.rate_limiter = {
            'coingecko': {'last_call': 0, 'min_interval': 1.2},  # 50 calls/minute
            'exchange': {'last_call': 0, 'min_interval': 0.5}    # 2 calls/second
        }
        
        # Data storage
        self.historical_datasets = {}  # coin_id -> HistoricalDataset
        self.pending_fetches = []  # Queue of coins to fetch data for
        
        # Statistics
        self.stats = {
            'total_datasets_created': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'total_data_points': 0,
            'csv_files_created': 0,
            'api_calls_today': 0,
            'data_quality_average': 0.0,
            'last_fetch': None
        }
    
    def get_module_info(self) -> ModuleInfo:
        """Return module information"""
        return ModuleInfo(
            name="Historical Data Fetcher",
            version="1.0.0",
            description="Fetches 30-day OHLCV historical data for newly detected coins",
            author="Unified Trading Platform",
            dependencies=['aiohttp', 'ccxt', 'pandas', 'sqlite3'],
            priority=ModulePriority.HIGH,
            config_schema=self.get_config_schema()
        )
    
    async def initialize(self) -> bool:
        """Initialize the historical data fetcher module"""
        try:
            self.log_info("🚀 Initializing Historical Data Fetcher Module...")
            
            # Initialize database
            await self._initialize_database()
            
            # Initialize HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={'User-Agent': 'AI-Trading-Bot-Historical/1.0'}
            )
            
            # Initialize exchanges
            if self.enable_ccxt_fetching:
                await self._initialize_exchanges()
            
            # Load existing datasets
            await self._load_existing_datasets()
            
            self.log_info("✅ Historical Data Fetcher Module initialized successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error initializing Historical Data Fetcher Module: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the historical data fetcher module"""
        try:
            self.log_info("🚀 Starting Historical Data Fetcher Module...")
            
            # Register event handlers
            self.register_event_handler('fetch_historical_data', self._handle_fetch_historical_data)
            self.register_event_handler('get_historical_data', self._handle_get_historical_data)
            self.register_event_handler('export_to_csv', self._handle_export_to_csv)
            self.register_event_handler('process_new_listing', self._handle_process_new_listing)
            
            # Start background processing task
            asyncio.create_task(self._background_processing_task())
            
            self.log_info("✅ Historical Data Fetcher Module started successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error starting Historical Data Fetcher Module: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the historical data fetcher module"""
        try:
            self.log_info("🛑 Stopping Historical Data Fetcher Module...")
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            # Close exchange connections
            for exchange in self.exchanges.values():
                if hasattr(exchange, 'close'):
                    await exchange.close()
            
            self.log_info("✅ Historical Data Fetcher Module stopped successfully")
            return True
            
        except Exception as e:
            self.log_error(f"❌ Error stopping Historical Data Fetcher Module: {e}")
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
            
            # Test exchange connectivity
            api_status['exchanges'] = len(self.exchanges)
            
            return {
                'status': 'healthy' if db_status else 'degraded',
                'db_status': db_status,
                'api_status': api_status,
                'datasets_cached': len(self.historical_datasets),
                'pending_fetches': len(self.pending_fetches),
                'last_fetch': self.stats['last_fetch'].isoformat() if self.stats['last_fetch'] else None
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
                'coingecko_api_key': {
                    'type': 'string',
                    'description': 'CoinGecko Pro API key for historical data'
                },
                'data_retention_days': {
                    'type': 'integer',
                    'minimum': 7,
                    'maximum': 365,
                    'description': 'Number of days of historical data to fetch'
                },
                'enable_ccxt_fetching': {
                    'type': 'boolean',
                    'description': 'Enable exchange data fetching via CCXT'
                },
                'enable_csv_export': {
                    'type': 'boolean',
                    'description': 'Enable CSV export functionality'
                },
                'cache_dir': {
                    'type': 'string',
                    'description': 'Directory for storing historical data'
                }
            }
        }

    async def _initialize_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Historical datasets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_datasets (
                    coin_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    data_points INTEGER,
                    sources TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # OHLCV data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ohlcv_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coin_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT,
                    date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(coin_id, timestamp, source, exchange)
                )
            ''')
            
            # Data quality metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_quality_metrics (
                    coin_id TEXT PRIMARY KEY,
                    completeness_score REAL,
                    consistency_score REAL,
                    timeliness_score REAL,
                    overall_score REAL,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasets_symbol ON historical_datasets(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ohlcv_coin_timestamp ON ohlcv_data(coin_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ohlcv_source ON ohlcv_data(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ohlcv_date ON ohlcv_data(date)')
            
            conn.commit()
            conn.close()
            
            self.log_info("📊 Historical data database initialized successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize database: {e}")
            raise

    async def _initialize_exchanges(self):
        """Initialize CCXT exchange connections"""
        try:
            for exchange_name, config in self.supported_exchanges.items():
                try:
                    exchange_class = config['class']
                    exchange = exchange_class({
                        'apiKey': '',  # Public data only
                        'secret': '',
                        'timeout': 30000,
                        'enableRateLimit': True,
                        'sandbox': False
                    })
                    
                    # Test connection
                    await exchange.load_markets()
                    self.exchanges[exchange_name] = exchange
                    self.log_info(f"✅ Exchange {exchange_name} initialized successfully")
                    
                except Exception as e:
                    self.log_warning(f"⚠️ Failed to initialize exchange {exchange_name}: {e}")
            
            self.log_info(f"📈 Initialized {len(self.exchanges)} exchanges for historical data fetching")
            
        except Exception as e:
            self.log_error(f"Failed to initialize exchanges: {e}")

    async def _load_existing_datasets(self):
        """Load existing historical datasets from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT coin_id, symbol, name, start_date, end_date, 
                       data_points, sources, metadata
                FROM historical_datasets
                ORDER BY created_at DESC
            ''')
            
            for row in cursor.fetchall():
                dataset = HistoricalDataset(
                    coin_id=row[0],
                    symbol=row[1],
                    name=row[2],
                    start_date=datetime.fromisoformat(row[3]),
                    end_date=datetime.fromisoformat(row[4]),
                    data_points=row[5],
                    sources=json.loads(row[6]) if row[6] else [],
                    ohlcv_data=[],  # Loaded on demand
                    metadata=json.loads(row[7]) if row[7] else {},
                    created_at=datetime.now()
                )
                
                self.historical_datasets[row[0]] = dataset
            
            conn.close()
            
            self.log_info(f"📚 Loaded {len(self.historical_datasets)} existing historical datasets")
            
        except Exception as e:
            self.log_error(f"Failed to load existing datasets: {e}")

    async def _background_processing_task(self):
        """Background task to process pending fetches"""
        while True:
            try:
                if self.pending_fetches:
                    # Process up to 5 pending fetches at a time
                    batch = self.pending_fetches[:5]
                    self.pending_fetches = self.pending_fetches[5:]
                    
                    # Process batch
                    await self._process_fetch_batch(batch)
                
                # Wait before next batch
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_error(f"Background processing task error: {e}")
                await asyncio.sleep(30)

    async def _process_fetch_batch(self, batch: List[Dict]):
        """Process a batch of historical data fetches"""
        try:
            for coin_info in batch:
                try:
                    await self._fetch_coin_historical_data(coin_info)
                    await asyncio.sleep(2)  # Rate limiting between coins
                    
                except Exception as e:
                    self.log_error(f"Failed to fetch data for {coin_info.get('symbol', 'unknown')}: {e}")
                    self.stats['failed_fetches'] += 1
            
        except Exception as e:
            self.log_error(f"Batch processing failed: {e}")

    async def _fetch_coin_historical_data(self, coin_info: Dict) -> Optional[HistoricalDataset]:
        """Fetch comprehensive historical data for a single coin"""
        try:
            coin_id = coin_info['coin_id']
            symbol = coin_info['symbol']
            name = coin_info.get('name', symbol)
            
            self.log_info(f"📈 Fetching 30-day historical data for {symbol} ({coin_id})")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.data_retention_days)
            
            all_ohlcv_data = []
            sources_used = []
            
            # 1. Try CoinGecko first (most comprehensive)
            coingecko_data = await self._fetch_coingecko_historical_data(coin_id, start_date, end_date)
            if coingecko_data:
                all_ohlcv_data.extend(coingecko_data)
                sources_used.append('coingecko')
                self.log_info(f"📊 CoinGecko: {len(coingecko_data)} data points for {symbol}")
            
            # 2. Try exchanges via CCXT (if available and enabled)
            if self.enable_ccxt_fetching:
                exchange_data = await self._fetch_exchange_historical_data(symbol, start_date, end_date)
                if exchange_data:
                    all_ohlcv_data.extend(exchange_data)
                    sources_used.extend([f"exchange_{d.exchange}" for d in exchange_data])
                    self.log_info(f"📈 Exchanges: {len(exchange_data)} additional data points for {symbol}")
            
            if not all_ohlcv_data:
                self.log_warning(f"⚠️ No historical data found for {symbol}")
                self.stats['failed_fetches'] += 1
                return None
            
            # Create historical dataset
            dataset = HistoricalDataset(
                coin_id=coin_id,
                symbol=symbol,
                name=name,
                start_date=start_date,
                end_date=end_date,
                data_points=len(all_ohlcv_data),
                sources=list(set(sources_used)),
                ohlcv_data=all_ohlcv_data,
                metadata={
                    'coingecko_id': coin_info.get('coingecko_id'),
                    'contract_address': coin_info.get('contract_address'),
                    'network': coin_info.get('network'),
                    'market_cap_usd': coin_info.get('market_cap_usd'),
                    'fetch_timestamp': datetime.now().isoformat()
                },
                created_at=datetime.now()
            )
            
            # Calculate data quality score
            quality_score = await self._calculate_data_quality(dataset)
            
            if quality_score >= self.data_quality_threshold:
                # Save to database
                await self._save_historical_dataset(dataset, quality_score)
                
                # Export to CSV if enabled
                if self.enable_csv_export:
                    await self._export_dataset_to_csv(dataset)
                
                # Store in memory
                self.historical_datasets[coin_id] = dataset
                
                # Update statistics
                self.stats['successful_fetches'] += 1
                self.stats['total_data_points'] += len(all_ohlcv_data)
                self.stats['total_datasets_created'] += 1
                self.stats['last_fetch'] = datetime.now()
                
                self.log_info(f"✅ Successfully fetched historical data for {symbol}: {len(all_ohlcv_data)} points, quality: {quality_score:.2%}")
                
                return dataset
            else:
                self.log_warning(f"⚠️ Data quality too low for {symbol}: {quality_score:.2%} < {self.data_quality_threshold:.2%}")
                self.stats['failed_fetches'] += 1
                return None
                
        except Exception as e:
            self.log_error(f"Failed to fetch historical data for {coin_info.get('symbol', 'unknown')}: {e}")
            self.stats['failed_fetches'] += 1
            return None

    async def _fetch_coingecko_historical_data(self, coin_id: str, start_date: datetime, end_date: datetime) -> List[OHLCVData]:
        """Fetch historical data from CoinGecko"""
        try:
            await self._rate_limit('coingecko')
            
            # Convert dates to Unix timestamps
            from_timestamp = int(start_date.timestamp())
            to_timestamp = int(end_date.timestamp())
            
            url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart/range"
            headers = {}
            if self.coingecko_api_key:
                headers['x-cg-pro-api-key'] = self.coingecko_api_key
            
            params = {
                'vs_currency': 'usd',
                'from': from_timestamp,
                'to': to_timestamp
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse CoinGecko format
                    prices = data.get('prices', [])
                    volumes = data.get('total_volumes', [])
                    
                    if not prices:
                        return []
                    
                    # Convert to OHLCV format (CoinGecko only provides price and volume)
                    ohlcv_data = []
                    for i, (timestamp, price) in enumerate(prices):
                        # Find corresponding volume
                        volume = 0
                        for vol_timestamp, vol_value in volumes:
                            if abs(vol_timestamp - timestamp) < 3600000:  # Within 1 hour
                                volume = vol_value
                                break
                        
                        # Create OHLCV entry (using price as OHLC since we only have close prices)
                        ohlcv_entry = OHLCVData(
                            timestamp=int(timestamp),
                            open=price,    # Approximation
                            high=price,    # Approximation  
                            low=price,     # Approximation
                            close=price,   # Actual close price
                            volume=volume,
                            source='coingecko',
                            symbol=coin_id,
                            date=datetime.fromtimestamp(timestamp/1000).date().isoformat()
                        )
                        ohlcv_data.append(ohlcv_entry)
                    
                    self.stats['api_calls_today'] += 1
                    return ohlcv_data
                    
                else:
                    self.log_warning(f"CoinGecko API error for {coin_id}: {response.status}")
                    return []
            
        except Exception as e:
            self.log_error(f"Failed to fetch CoinGecko data for {coin_id}: {e}")
            return []

    async def _fetch_exchange_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[OHLCVData]:
        """Fetch historical data from exchanges via CCXT"""
        all_exchange_data = []
        
        try:
            # Try to find the symbol on various exchanges
            for exchange_name, exchange in self.exchanges.items():
                try:
                    await self._rate_limit('exchange')
                    
                    # Find matching symbol on exchange
                    markets = await exchange.load_markets()
                    
                    # Try various symbol formats
                    possible_symbols = [
                        f"{symbol}/USDT",
                        f"{symbol}/BUSD", 
                        f"{symbol}/USD",
                        f"{symbol}/BTC",
                        f"{symbol}/ETH"
                    ]
                    
                    exchange_symbol = None
                    for possible_symbol in possible_symbols:
                        if possible_symbol in markets:
                            exchange_symbol = possible_symbol
                            break
                    
                    if not exchange_symbol:
                        continue
                    
                    # Fetch OHLCV data
                    since = exchange.parse8601(start_date.isoformat())
                    limit = 30  # 30 days
                    
                    ohlcv = await exchange.fetch_ohlcv(
                        exchange_symbol, 
                        timeframe='1d',
                        since=since,
                        limit=limit
                    )
                    
                    if ohlcv:
                        # Convert to our format
                        for candle in ohlcv:
                            timestamp, open_price, high, low, close, volume = candle
                            
                            ohlcv_entry = OHLCVData(
                                timestamp=int(timestamp),
                                open=open_price,
                                high=high,
                                low=low,
                                close=close,
                                volume=volume,
                                source='exchange',
                                symbol=exchange_symbol,
                                exchange=exchange_name,
                                date=datetime.fromtimestamp(timestamp/1000).date().isoformat()
                            )
                            all_exchange_data.append(ohlcv_entry)
                        
                        self.log_info(f"📈 {exchange_name}: {len(ohlcv)} OHLCV points for {exchange_symbol}")
                
                except Exception as e:
                    self.log_debug(f"Exchange {exchange_name} failed for {symbol}: {e}")
                    continue
            
            return all_exchange_data
            
        except Exception as e:
            self.log_error(f"Failed to fetch exchange data for {symbol}: {e}")
            return []

    async def _calculate_data_quality(self, dataset: HistoricalDataset) -> float:
        """Calculate data quality score for a dataset"""
        try:
            if not dataset.ohlcv_data:
                return 0.0
            
            # Completeness score (0-1)
            expected_days = self.data_retention_days
            actual_days = len(set(d.date for d in dataset.ohlcv_data if d.date))
            completeness = min(actual_days / expected_days, 1.0)
            
            # Consistency score (0-1) - check for reasonable price ranges
            prices = [d.close for d in dataset.ohlcv_data if d.close > 0]
            if prices:
                price_std = np.std(prices)
                price_mean = np.mean(prices)
                cv = price_std / price_mean if price_mean > 0 else 0
                consistency = max(0, 1.0 - min(cv / 2.0, 1.0))  # Cap at 200% CV
            else:
                consistency = 0.0
            
            # Timeliness score (0-1) - how recent is the data
            latest_date = max(d.timestamp for d in dataset.ohlcv_data)
            hours_ago = (datetime.now().timestamp() - latest_date/1000) / 3600
            timeliness = max(0, 1.0 - min(hours_ago / 48.0, 1.0))  # Degrade over 48 hours
            
            # Overall score (weighted average)
            overall_score = (
                completeness * 0.5 +    # 50% weight on completeness
                consistency * 0.3 +     # 30% weight on consistency  
                timeliness * 0.2        # 20% weight on timeliness
            )
            
            return overall_score
            
        except Exception as e:
            self.log_error(f"Failed to calculate data quality: {e}")
            return 0.0

    async def _save_historical_dataset(self, dataset: HistoricalDataset, quality_score: float):
        """Save historical dataset to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save dataset metadata
            cursor.execute('''
                INSERT OR REPLACE INTO historical_datasets (
                    coin_id, symbol, name, start_date, end_date, 
                    data_points, sources, metadata, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset.coin_id,
                dataset.symbol,
                dataset.name,
                dataset.start_date.isoformat(),
                dataset.end_date.isoformat(),
                dataset.data_points,
                json.dumps(dataset.sources),
                json.dumps(dataset.metadata),
                datetime.now().isoformat()
            ))
            
            # Save OHLCV data
            for ohlcv in dataset.ohlcv_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO ohlcv_data (
                        coin_id, timestamp, open, high, low, close, volume,
                        source, symbol, exchange, date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dataset.coin_id,
                    ohlcv.timestamp,
                    ohlcv.open,
                    ohlcv.high, 
                    ohlcv.low,
                    ohlcv.close,
                    ohlcv.volume,
                    ohlcv.source,
                    ohlcv.symbol,
                    ohlcv.exchange,
                    ohlcv.date
                ))
            
            # Save quality metrics
            completeness = len(set(d.date for d in dataset.ohlcv_data)) / self.data_retention_days
            cursor.execute('''
                INSERT OR REPLACE INTO data_quality_metrics (
                    coin_id, completeness_score, consistency_score, 
                    timeliness_score, overall_score
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                dataset.coin_id,
                completeness,
                0.8,  # Placeholder
                0.9,  # Placeholder  
                quality_score
            ))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"💾 Saved historical dataset for {dataset.symbol} to database")
            
        except Exception as e:
            self.log_error(f"Failed to save dataset to database: {e}")

    async def _export_dataset_to_csv(self, dataset: HistoricalDataset):
        """Export dataset to CSV file"""
        try:
            # Create CSV filename
            csv_filename = f"{dataset.symbol}_{dataset.coin_id}_30d_ohlcv.csv"
            csv_path = self.csv_dir / csv_filename
            
            # Prepare data for CSV
            csv_data = []
            for ohlcv in sorted(dataset.ohlcv_data, key=lambda x: x.timestamp):
                csv_data.append({
                    'date': ohlcv.date,
                    'timestamp': ohlcv.timestamp,
                    'open': ohlcv.open,
                    'high': ohlcv.high,
                    'low': ohlcv.low,
                    'close': ohlcv.close,
                    'volume': ohlcv.volume,
                    'source': ohlcv.source,
                    'symbol': ohlcv.symbol,
                    'exchange': ohlcv.exchange or ''
                })
            
            # Write to CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(csv_path, index=False)
                
                self.stats['csv_files_created'] += 1
                self.log_info(f"📄 Exported {dataset.symbol} historical data to {csv_path}")
                
                # Also create AI-ready summary file
                await self._create_ai_summary_file(dataset, csv_path)
            
        except Exception as e:
            self.log_error(f"Failed to export dataset to CSV: {e}")

    async def _create_ai_summary_file(self, dataset: HistoricalDataset, csv_path: Path):
        """Create AI-ready summary file"""
        try:
            # Calculate technical indicators and summary stats
            ohlcv_data = sorted(dataset.ohlcv_data, key=lambda x: x.timestamp)
            if len(ohlcv_data) < 2:
                return
            
            prices = [d.close for d in ohlcv_data]
            volumes = [d.volume for d in ohlcv_data]
            
            summary = {
                'coin_id': dataset.coin_id,
                'symbol': dataset.symbol,
                'name': dataset.name,
                'data_period': {
                    'start_date': dataset.start_date.isoformat(),
                    'end_date': dataset.end_date.isoformat(),
                    'data_points': dataset.data_points
                },
                'price_statistics': {
                    'first_price': prices[0],
                    'last_price': prices[-1],
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'mean_price': np.mean(prices),
                    'price_change_pct': ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0,
                    'volatility': np.std(prices) / np.mean(prices) * 100 if np.mean(prices) > 0 else 0
                },
                'volume_statistics': {
                    'total_volume': sum(volumes),
                    'avg_daily_volume': np.mean(volumes),
                    'max_daily_volume': max(volumes),
                    'min_daily_volume': min(volumes)
                },
                'technical_indicators': {
                    'sma_7': np.mean(prices[-7:]) if len(prices) >= 7 else np.mean(prices),
                    'sma_14': np.mean(prices[-14:]) if len(prices) >= 14 else np.mean(prices),
                    'rsi_approx': self._calculate_simple_rsi(prices),
                    'price_momentum': (prices[-1] / prices[-7] - 1) * 100 if len(prices) >= 7 and prices[-7] > 0 else 0
                },
                'data_sources': dataset.sources,
                'csv_file': str(csv_path),
                'metadata': dataset.metadata,
                'ai_features': {
                    'is_trending_up': prices[-1] > prices[-7] if len(prices) >= 7 else False,
                    'has_high_volume': volumes[-1] > np.mean(volumes) * 1.5 if volumes else False,
                    'volatility_category': 'high' if (np.std(prices) / np.mean(prices) * 100) > 10 else 'low',
                    'data_quality_score': await self._calculate_data_quality(dataset)
                }
            }
            
            # Save AI summary
            ai_summary_path = self.csv_dir / f"{dataset.symbol}_{dataset.coin_id}_ai_summary.json"
            with open(ai_summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.log_info(f"🧠 Created AI summary file for {dataset.symbol}")
            
        except Exception as e:
            self.log_error(f"Failed to create AI summary file: {e}")

    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate simplified RSI"""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas[-period:]]
            losses = [-d if d < 0 else 0 for d in deltas[-period:]]
            
            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return 50.0

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
    async def _handle_fetch_historical_data(self, event):
        """Handle manual historical data fetch request"""
        try:
            coin_info = event.data
            dataset = await self._fetch_coin_historical_data(coin_info)
            
            if dataset:
                return {
                    'success': True,
                    'coin_id': dataset.coin_id,
                    'data_points': dataset.data_points,
                    'sources': dataset.sources,
                    'quality_score': await self._calculate_data_quality(dataset)
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to fetch historical data'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_get_historical_data(self, event):
        """Handle get historical data request"""
        try:
            coin_id = event.data.get('coin_id')
            
            if coin_id in self.historical_datasets:
                dataset = self.historical_datasets[coin_id]
                return {
                    'success': True,
                    'dataset': asdict(dataset)
                }
            else:
                return {
                    'success': False,
                    'error': 'Dataset not found'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_export_to_csv(self, event):
        """Handle CSV export request"""
        try:
            coin_id = event.data.get('coin_id')
            
            if coin_id in self.historical_datasets:
                dataset = self.historical_datasets[coin_id]
                await self._export_dataset_to_csv(dataset)
                return {
                    'success': True,
                    'csv_path': str(self.csv_dir / f"{dataset.symbol}_{coin_id}_30d_ohlcv.csv")
                }
            else:
                return {
                    'success': False,
                    'error': 'Dataset not found'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_process_new_listing(self, event):
        """Handle new listing detected from the new listing detector"""
        try:
            new_listing = event.data
            
            # Add to pending fetches queue
            coin_info = {
                'coin_id': new_listing.get('coin_id'),
                'symbol': new_listing.get('symbol'),
                'name': new_listing.get('name'),
                'coingecko_id': new_listing.get('coingecko_id'),
                'contract_address': new_listing.get('contract_address'),
                'network': new_listing.get('network'),
                'market_cap_usd': new_listing.get('market_cap_usd')
            }
            
            self.pending_fetches.append(coin_info)
            
            self.log_info(f"📈 Queued historical data fetch for new listing: {coin_info['symbol']}")
            
            return {
                'success': True,
                'message': f"Queued historical data fetch for {coin_info['symbol']}",
                'queue_position': len(self.pending_fetches)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            **self.stats,
            'datasets_cached': len(self.historical_datasets),
            'pending_fetches': len(self.pending_fetches),
            'supported_exchanges': list(self.supported_exchanges.keys()),
            'active_exchanges': list(self.exchanges.keys()),
            'data_retention_days': self.data_retention_days,
            'csv_export_enabled': self.enable_csv_export
        }


def create_module(name: str, config: Dict[str, Any]) -> HistoricalDataFetcherModule:
    """Create Historical Data Fetcher module instance"""
    return HistoricalDataFetcherModule(name, config)
