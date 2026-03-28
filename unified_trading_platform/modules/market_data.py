#!/usr/bin/env python3
"""
📊 Market Data Module
Real-time market data collection and management
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import pandas as pd
from dataclasses import dataclass
import json

from core.base_module import BaseModule, ModuleInfo, ModulePriority, ModuleStatus, ModuleEvent
import sys
import os

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@dataclass
class MarketTick:
    """Market tick data structure"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    change_24h: Optional[float] = None

@dataclass
class OHLCVData:
    """OHLCV candlestick data structure"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketDataModule(BaseModule):
    """
    Market Data Module
    
    Handles real-time market data collection from multiple sources
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Configuration
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.timeframes = config.get('timeframes', ['1m', '5m', '1h'])
        self.update_interval = config.get('update_interval', 1)  # seconds
        self.data_sources = config.get('data_sources', ['binance', 'coingecko'])
        
        # Data storage
        self.current_prices = {}  # symbol -> MarketTick
        self.ohlcv_data = {}      # symbol -> timeframe -> List[OHLCVData]
        self.price_history = {}   # symbol -> List[MarketTick]
        
        # HTTP session for API calls
        self.session = None
        
        # Update tasks
        self.update_tasks = []
        
        # Data sources configuration
        self.data_source_configs = {
            'binance': {
                'base_url': 'https://api.binance.com/api/v3',
                'ticker_endpoint': '/ticker/24hr',
                'klines_endpoint': '/klines',
                'symbol_format': lambda s: s.replace('/', '').upper()
            },
            'coingecko': {
                'base_url': 'https://api.coingecko.com/api/v3',
                'price_endpoint': '/simple/price',
                'ohlc_endpoint': '/coins/{coin_id}/ohlc'
            }
        }
        
        # Statistics
        self.stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'last_update': None,
            'data_points': 0
        }
    
    def get_module_info(self) -> ModuleInfo:
        """Return module information"""
        return ModuleInfo(
            name="Market Data",
            version="1.0.0",
            description="Real-time market data collection and management",
            author="Unified Trading Platform",
            dependencies=[],
            priority=ModulePriority.CRITICAL,
            config_schema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Trading symbols to monitor"
                    },
                    "timeframes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Timeframes for OHLCV data"
                    },
                    "update_interval": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Update interval in seconds"
                    },
                    "data_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Data sources to use"
                    }
                },
                "required": ["symbols"]
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the market data module"""
        try:
            self.log_info("Initializing Market Data Module...")
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Initialize data storage
            for symbol in self.symbols:
                self.current_prices[symbol] = None
                self.price_history[symbol] = []
                self.ohlcv_data[symbol] = {}
                
                for timeframe in self.timeframes:
                    self.ohlcv_data[symbol][timeframe] = []
            
            # Test connectivity to data sources
            for source in self.data_sources:
                if await self._test_data_source(source):
                    self.log_info(f"Data source {source} is accessible")
                else:
                    self.log_warning(f"Data source {source} is not accessible")
            
            self.log_info("Market Data Module initialized successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Error initializing Market Data Module: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the market data module"""
        try:
            self.log_info("Starting Market Data Module...")
            
            # Start data update tasks
            for source in self.data_sources:
                if source == 'binance':
                    task = asyncio.create_task(self._update_binance_data())
                    self.update_tasks.append(task)
                elif source == 'coingecko':
                    task = asyncio.create_task(self._update_coingecko_data())
                    self.update_tasks.append(task)
            
            # Start price history task
            history_task = asyncio.create_task(self._update_price_history())
            self.update_tasks.append(history_task)
            
            # Register event handlers
            self.register_event_handler('request_market_data', self._handle_data_request)
            self.register_event_handler('subscribe_price_updates', self._handle_subscription)
            
            self.log_info("Market Data Module started successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Error starting Market Data Module: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the market data module"""
        try:
            self.log_info("Stopping Market Data Module...")
            
            # Cancel all update tasks
            for task in self.update_tasks:
                if not task.cancelled():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.update_tasks:
                await asyncio.gather(*self.update_tasks, return_exceptions=True)
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            self.log_info("Market Data Module stopped successfully")
            return True
            
        except Exception as e:
            self.log_error(f"Error stopping Market Data Module: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            health_status = {
                'healthy': True,
                'last_update': self.stats['last_update'],
                'total_updates': self.stats['total_updates'],
                'success_rate': 0,
                'data_freshness': 'unknown',
                'active_symbols': len([s for s in self.symbols if self.current_prices.get(s)]),
                'total_symbols': len(self.symbols)
            }
            
            # Calculate success rate
            total_updates = self.stats['total_updates']
            if total_updates > 0:
                health_status['success_rate'] = self.stats['successful_updates'] / total_updates
            
            # Check data freshness
            if self.stats['last_update']:
                last_update = datetime.fromisoformat(self.stats['last_update'])
                time_since_update = (datetime.now() - last_update).total_seconds()
                
                if time_since_update < 60:  # Less than 1 minute
                    health_status['data_freshness'] = 'fresh'
                elif time_since_update < 300:  # Less than 5 minutes
                    health_status['data_freshness'] = 'acceptable'
                else:
                    health_status['data_freshness'] = 'stale'
                    health_status['healthy'] = False
            
            # Check if we have data for all symbols
            if health_status['active_symbols'] < health_status['total_symbols']:
                health_status['healthy'] = False
            
            return health_status
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema"""
        return self.get_module_info().config_schema
    
    async def _test_data_source(self, source: str) -> bool:
        """Test connectivity to a data source"""
        try:
            if source == 'binance':
                url = f"{self.data_source_configs['binance']['base_url']}/ping"
                async with self.session.get(url) as response:
                    return response.status == 200
            elif source == 'coingecko':
                url = f"{self.data_source_configs['coingecko']['base_url']}/ping"
                async with self.session.get(url) as response:
                    return response.status == 200
            return False
            
        except Exception as e:
            self.log_error(f"Error testing data source {source}: {e}")
            return False
    
    async def _update_binance_data(self):
        """Update data from Binance API"""
        while self.is_active():
            try:
                # Get ticker data for all symbols
                config = self.data_source_configs['binance']
                url = f"{config['base_url']}{config['ticker_endpoint']}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data:
                            symbol_binance = item['symbol']
                            
                            # Convert Binance symbol format to our format
                            symbol = self._convert_binance_symbol(symbol_binance)
                            
                            if symbol in self.symbols:
                                tick = MarketTick(
                                    symbol=symbol,
                                    timestamp=datetime.now(),
                                    price=float(item['lastPrice']),
                                    volume=float(item['volume']),
                                    bid=float(item['bidPrice']),
                                    ask=float(item['askPrice']),
                                    high_24h=float(item['highPrice']),
                                    low_24h=float(item['lowPrice']),
                                    change_24h=float(item['priceChangePercent'])
                                )
                                
                                # Update current price
                                self.current_prices[symbol] = tick
                                
                                # Send price update event
                                await self.send_event(
                                    'price_update',
                                    {
                                        'symbol': symbol,
                                        'price': tick.price,
                                        'timestamp': tick.timestamp.isoformat(),
                                        'source': 'binance'
                                    },
                                    priority=ModulePriority.HIGH
                                )
                        
                        self.stats['successful_updates'] += 1
                        self.stats['last_update'] = datetime.now().isoformat()
                        
                    else:
                        self.log_error(f"Binance API error: {response.status}")
                        self.stats['failed_updates'] += 1
                
                self.stats['total_updates'] += 1
                
            except Exception as e:
                self.log_error(f"Error updating Binance data: {e}")
                self.stats['failed_updates'] += 1
            
            await asyncio.sleep(self.update_interval)
    
    async def _update_coingecko_data(self):
        """Update data from CoinGecko API"""
        while self.is_active():
            try:
                # CoinGecko has different rate limits, so update less frequently
                await asyncio.sleep(self.update_interval * 5)
                
                # Get price data
                config = self.data_source_configs['coingecko']
                
                # Convert symbols to CoinGecko format
                coin_ids = []
                for symbol in self.symbols:
                    coin_id = self._convert_to_coingecko_id(symbol)
                    if coin_id:
                        coin_ids.append(coin_id)
                
                if coin_ids:
                    url = f"{config['base_url']}{config['price_endpoint']}"
                    params = {
                        'ids': ','.join(coin_ids),
                        'vs_currencies': 'usd',
                        'include_24hr_change': 'true'
                    }
                    
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for coin_id, price_data in data.items():
                                symbol = self._convert_from_coingecko_id(coin_id)
                                
                                if symbol and symbol in self.symbols:
                                    # Only update if we don't have recent Binance data
                                    current_tick = self.current_prices.get(symbol)
                                    if not current_tick or (datetime.now() - current_tick.timestamp).seconds > 60:
                                        
                                        tick = MarketTick(
                                            symbol=symbol,
                                            timestamp=datetime.now(),
                                            price=float(price_data['usd']),
                                            volume=0,  # CoinGecko doesn't provide volume in this endpoint
                                            change_24h=price_data.get('usd_24h_change', 0)
                                        )
                                        
                                        self.current_prices[symbol] = tick
                                        
                                        # Send price update event
                                        await self.send_event(
                                            'price_update',
                                            {
                                                'symbol': symbol,
                                                'price': tick.price,
                                                'timestamp': tick.timestamp.isoformat(),
                                                'source': 'coingecko'
                                            },
                                            priority=ModulePriority.NORMAL
                                        )
                            
                            self.stats['successful_updates'] += 1
                            self.stats['last_update'] = datetime.now().isoformat()
                        else:
                            self.log_error(f"CoinGecko API error: {response.status}")
                            self.stats['failed_updates'] += 1
                
                self.stats['total_updates'] += 1
                
            except Exception as e:
                self.log_error(f"Error updating CoinGecko data: {e}")
                self.stats['failed_updates'] += 1
    
    async def _update_price_history(self):
        """Update price history for all symbols"""
        while self.is_active():
            try:
                for symbol in self.symbols:
                    current_tick = self.current_prices.get(symbol)
                    if current_tick:
                        # Add to history
                        self.price_history[symbol].append(current_tick)
                        
                        # Limit history size (keep last 1000 points)
                        if len(self.price_history[symbol]) > 1000:
                            self.price_history[symbol] = self.price_history[symbol][-1000:]
                        
                        self.stats['data_points'] += 1
                
                # Send periodic market summary
                await self.send_event(
                    'market_summary',
                    {
                        'timestamp': datetime.now().isoformat(),
                        'active_symbols': len([s for s in self.symbols if self.current_prices.get(s)]),
                        'total_data_points': self.stats['data_points']
                    },
                    priority=ModulePriority.LOW
                )
                
            except Exception as e:
                self.log_error(f"Error updating price history: {e}")
            
            await asyncio.sleep(60)  # Update history every minute
    
    def _convert_binance_symbol(self, binance_symbol: str) -> Optional[str]:
        """Convert Binance symbol format to standard format"""
        # Simple conversion for common pairs
        symbol_map = {
            'BTCUSDT': 'BTC/USDT',
            'ETHUSDT': 'ETH/USDT',
            'ADAUSDT': 'ADA/USDT',
            'BNBUSDT': 'BNB/USDT',
            'SOLUSDT': 'SOL/USDT'
        }
        
        return symbol_map.get(binance_symbol)
    
    def _convert_to_coingecko_id(self, symbol: str) -> Optional[str]:
        """Convert symbol to CoinGecko coin ID"""
        # Simple mapping for common coins
        coin_map = {
            'BTC/USDT': 'bitcoin',
            'ETH/USDT': 'ethereum',
            'ADA/USDT': 'cardano',
            'BNB/USDT': 'binancecoin',
            'SOL/USDT': 'solana'
        }
        
        return coin_map.get(symbol)
    
    def _convert_from_coingecko_id(self, coin_id: str) -> Optional[str]:
        """Convert CoinGecko coin ID to symbol"""
        id_map = {
            'bitcoin': 'BTC/USDT',
            'ethereum': 'ETH/USDT',
            'cardano': 'ADA/USDT',
            'binancecoin': 'BNB/USDT',
            'solana': 'SOL/USDT'
        }
        
        return id_map.get(coin_id)
    
    # Event handlers
    async def _handle_data_request(self, event):
        """Handle requests for market data"""
        try:
            request_data = event.data
            symbol = request_data.get('symbol')
            data_type = request_data.get('type', 'current_price')
            
            response_data = {'symbol': symbol, 'type': data_type}
            
            if data_type == 'current_price':
                if symbol in self.current_prices:
                    tick = self.current_prices[symbol]
                    if tick:
                        response_data.update({
                            'price': tick.price,
                            'timestamp': tick.timestamp.isoformat(),
                            'volume': tick.volume,
                            'change_24h': tick.change_24h
                        })
                    else:
                        response_data['error'] = 'No data available'
                else:
                    response_data['error'] = 'Symbol not found'
            
            elif data_type == 'price_history':
                if symbol in self.price_history:
                    history = self.price_history[symbol]
                    response_data['history'] = [
                        {
                            'timestamp': tick.timestamp.isoformat(),
                            'price': tick.price,
                            'volume': tick.volume
                        }
                        for tick in history[-100:]  # Last 100 points
                    ]
                else:
                    response_data['error'] = 'Symbol not found'
            
            # Send response
            await self.send_event(
                'market_data_response',
                response_data,
                target_module=event.source_module,
                priority=ModulePriority.HIGH
            )
            
        except Exception as e:
            self.log_error(f"Error handling data request: {e}")
    
    async def _handle_subscription(self, event):
        """Handle subscription requests for price updates"""
        try:
            subscription_data = event.data
            subscriber = event.source_module
            symbol = subscription_data.get('symbol')
            
            # For now, just acknowledge the subscription
            # In a more complex implementation, we'd maintain a subscriber list
            await self.send_event(
                'subscription_confirmed',
                {
                    'symbol': symbol,
                    'subscriber': subscriber,
                    'status': 'confirmed'
                },
                target_module=subscriber,
                priority=ModulePriority.NORMAL
            )
            
        except Exception as e:
            self.log_error(f"Error handling subscription: {e}")
    
    # Public API methods
    def get_current_price(self, symbol: str) -> Optional[MarketTick]:
        """Get current price for a symbol"""
        return self.current_prices.get(symbol)
    
    def get_price_history(self, symbol: str, limit: int = 100) -> List[MarketTick]:
        """Get price history for a symbol"""
        history = self.price_history.get(symbol, [])
        return history[-limit:] if history else []
    
    def get_all_prices(self) -> Dict[str, MarketTick]:
        """Get current prices for all symbols"""
        return {symbol: tick for symbol, tick in self.current_prices.items() if tick}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get module statistics"""
        return self.stats.copy()

# Module factory function
def create_module(name: str, config: Dict[str, Any]) -> MarketDataModule:
    """Create a MarketDataModule instance"""
    return MarketDataModule(name, config) 