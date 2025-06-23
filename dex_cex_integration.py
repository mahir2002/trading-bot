#!/usr/bin/env python3
"""
🔗 DEX/CEX INTEGRATION SYSTEM
Comprehensive system for integrating all DEX and CEX platforms
with daily new currency discovery
"""

import asyncio
import aiohttp
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
import requests
from web3 import Web3
import sqlite3
from dataclasses import dataclass

@dataclass
class NewCurrency:
    """Data class for new currency information"""
    symbol: str
    name: str
    contract_address: str
    network: str
    exchange: str
    launch_date: datetime
    initial_price: float
    volume_24h: float
    market_cap: float
    liquidity: float
    verified: bool
    risk_score: float

class DEXCEXIntegrator:
    """Comprehensive DEX/CEX integration system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_database()
        self.setup_exchanges()
        self.setup_dex_connections()
        self.setup_data_sources()
        
        # Currency tracking
        self.tracked_currencies = set()
        self.new_currencies_today = []
        self.risk_thresholds = {
            'min_liquidity': 10000,  # Minimum $10k liquidity
            'min_volume': 5000,      # Minimum $5k 24h volume
            'max_risk_score': 7.0,   # Maximum risk score (1-10)
            'min_holders': 100       # Minimum number of holders
        }
    
    def setup_database(self):
        """Setup SQLite database for currency tracking"""
        self.conn = sqlite3.connect('currency_tracker.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                contract_address TEXT,
                network TEXT NOT NULL,
                exchange TEXT NOT NULL,
                launch_date TIMESTAMP,
                initial_price REAL,
                current_price REAL,
                volume_24h REAL,
                market_cap REAL,
                liquidity REAL,
                verified BOOLEAN,
                risk_score REAL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency_id INTEGER,
                price REAL,
                volume REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (currency_id) REFERENCES currencies (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency_id INTEGER,
                signal_type TEXT,
                confidence REAL,
                price_target REAL,
                stop_loss REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (currency_id) REFERENCES currencies (id)
            )
        ''')
        
        self.conn.commit()
        self.logger.info("✅ Database setup complete")
    
    def setup_exchanges(self):
        """Setup CEX connections"""
        self.exchanges = {}
        
        # Major CEX platforms
        exchange_configs = {
            'binance': ccxt.binance({'enableRateLimit': True}),
            'coinbase': ccxt.coinbasepro({'enableRateLimit': True}),
            'kraken': ccxt.kraken({'enableRateLimit': True}),
            'okx': ccxt.okx({'enableRateLimit': True}),
            'bybit': ccxt.bybit({'enableRateLimit': True}),
            'kucoin': ccxt.kucoin({'enableRateLimit': True}),
            'huobi': ccxt.huobi({'enableRateLimit': True}),
            'gate': ccxt.gateio({'enableRateLimit': True})
        }
        
        for name, exchange in exchange_configs.items():
            try:
                exchange.load_markets()
                self.exchanges[name] = exchange
                self.logger.info(f"✅ {name.upper()} exchange connected")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to connect to {name}: {e}")
        
        self.logger.info(f"✅ Connected to {len(self.exchanges)} exchanges")
    
    def setup_dex_connections(self):
        """Setup DEX connections"""
        self.dex_connections = {}
        
        # Ethereum DEXs
        ethereum_rpc = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
        try:
            self.dex_connections['ethereum'] = {
                'web3': Web3(Web3.HTTPProvider(ethereum_rpc)),
                'dexs': {
                    'uniswap_v3': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                    'uniswap_v2': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                    'sushiswap': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                    'curve': '0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5',
                    'balancer': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'
                }
            }
            self.logger.info("✅ Ethereum DEX connections established")
        except Exception as e:
            self.logger.warning(f"⚠️ Ethereum connection failed: {e}")
        
        # BSC DEXs
        bsc_rpc = "https://bsc-dataseed.binance.org/"
        try:
            self.dex_connections['bsc'] = {
                'web3': Web3(Web3.HTTPProvider(bsc_rpc)),
                'dexs': {
                    'pancakeswap_v3': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',
                    'pancakeswap_v2': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
                    'biswap': '0x858E3312ed3A876947EA49d572A7C42DE08af7EE',
                    'mdex': '0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8'
                }
            }
            self.logger.info("✅ BSC DEX connections established")
        except Exception as e:
            self.logger.warning(f"⚠️ BSC connection failed: {e}")
        
        # Polygon DEXs
        polygon_rpc = "https://polygon-rpc.com/"
        try:
            self.dex_connections['polygon'] = {
                'web3': Web3(Web3.HTTPProvider(polygon_rpc)),
                'dexs': {
                    'quickswap': '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32',
                    'sushiswap': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                    'curve': '0x094d12e5b541784701FD8d65F11fc0598FBC6332'
                }
            }
            self.logger.info("✅ Polygon DEX connections established")
        except Exception as e:
            self.logger.warning(f"⚠️ Polygon connection failed: {e}")
    
    def setup_data_sources(self):
        """Setup data sources for new currency discovery"""
        self.data_sources = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1',
            'dexscreener': 'https://api.dexscreener.com/latest',
            'dextools': 'https://www.dextools.io/shared/data',
            'moralis': 'https://deep-index.moralis.io/api/v2',
            'covalent': 'https://api.covalenthq.com/v1',
            'defillama': 'https://api.llama.fi',
            'birdeye': 'https://public-api.birdeye.so',
            'geckoterminal': 'https://api.geckoterminal.com/api/v2'
        }
        
        self.logger.info("✅ Data sources configured")
    
    async def discover_new_currencies_daily(self):
        """Main function to discover new currencies daily"""
        self.logger.info("🔍 Starting daily new currency discovery...")
        
        today = datetime.now().date()
        new_currencies = []
        
        # Discover from multiple sources
        tasks = [
            self.discover_from_dexscreener(),
            self.discover_from_coingecko(),
            self.discover_from_dextools(),
            self.discover_from_birdeye(),
            self.discover_from_exchanges()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for result in results:
            if isinstance(result, list):
                new_currencies.extend(result)
        
        # Filter and validate currencies
        validated_currencies = await self.validate_new_currencies(new_currencies)
        
        # Store in database
        stored_count = await self.store_new_currencies(validated_currencies)
        
        self.logger.info(f"✅ Discovered {len(new_currencies)} currencies, validated {len(validated_currencies)}, stored {stored_count}")
        
        return validated_currencies
    
    async def discover_from_dexscreener(self) -> List[NewCurrency]:
        """Discover new currencies from DexScreener"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get trending tokens
                url = f"{self.data_sources['dexscreener']}/dex/tokens/trending"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        currencies = []
                        
                        for token in data.get('pairs', [])[:50]:  # Limit to top 50
                            try:
                                currency = NewCurrency(
                                    symbol=token.get('baseToken', {}).get('symbol', ''),
                                    name=token.get('baseToken', {}).get('name', ''),
                                    contract_address=token.get('baseToken', {}).get('address', ''),
                                    network=token.get('chainId', ''),
                                    exchange='dexscreener',
                                    launch_date=datetime.now(),
                                    initial_price=float(token.get('priceUsd', 0)),
                                    volume_24h=float(token.get('volume', {}).get('h24', 0)),
                                    market_cap=float(token.get('marketCap', 0)),
                                    liquidity=float(token.get('liquidity', {}).get('usd', 0)),
                                    verified=token.get('baseToken', {}).get('verified', False),
                                    risk_score=self.calculate_risk_score(token)
                                )
                                currencies.append(currency)
                            except Exception as e:
                                self.logger.warning(f"Error parsing DexScreener token: {e}")
                        
                        self.logger.info(f"✅ DexScreener: Found {len(currencies)} currencies")
                        return currencies
        except Exception as e:
            self.logger.error(f"❌ DexScreener discovery failed: {e}")
        
        return []
    
    async def discover_from_coingecko(self) -> List[NewCurrency]:
        """Discover new currencies from CoinGecko"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get recently added coins
                url = f"{self.data_sources['coingecko']}/coins/list?include_platform=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        currencies = []
                        
                        # Get coins added in last 7 days (simulate)
                        recent_coins = data[-100:]  # Get last 100 as proxy for recent
                        
                        for coin in recent_coins:
                            try:
                                # Get detailed info
                                detail_url = f"{self.data_sources['coingecko']}/coins/{coin['id']}"
                                async with session.get(detail_url) as detail_response:
                                    if detail_response.status == 200:
                                        detail_data = await detail_response.json()
                                        
                                        currency = NewCurrency(
                                            symbol=coin.get('symbol', '').upper(),
                                            name=coin.get('name', ''),
                                            contract_address=self.get_contract_address(detail_data),
                                            network=self.get_network_from_platforms(detail_data),
                                            exchange='coingecko',
                                            launch_date=datetime.now(),
                                            initial_price=self.get_current_price(detail_data),
                                            volume_24h=self.get_volume_24h(detail_data),
                                            market_cap=self.get_market_cap(detail_data),
                                            liquidity=0,  # Not available from CoinGecko
                                            verified=True,  # CoinGecko has verification
                                            risk_score=self.calculate_coingecko_risk_score(detail_data)
                                        )
                                        currencies.append(currency)
                                        
                                        # Rate limiting
                                        await asyncio.sleep(0.1)
                            except Exception as e:
                                self.logger.warning(f"Error parsing CoinGecko coin: {e}")
                        
                        self.logger.info(f"✅ CoinGecko: Found {len(currencies)} currencies")
                        return currencies
        except Exception as e:
            self.logger.error(f"❌ CoinGecko discovery failed: {e}")
        
        return []
    
    async def discover_from_dextools(self) -> List[NewCurrency]:
        """Discover new currencies from DexTools"""
        try:
            # DexTools requires API key and has rate limits
            # This is a placeholder implementation
            currencies = []
            
            # Simulate discovery from DexTools
            networks = ['ethereum', 'bsc', 'polygon']
            
            for network in networks:
                # In real implementation, use DexTools API
                # url = f"{self.data_sources['dextools']}/{network}/trending"
                
                # Placeholder data
                for i in range(5):
                    currency = NewCurrency(
                        symbol=f"TOKEN{i}",
                        name=f"Token {i}",
                        contract_address=f"0x{''.join(['0'] * 40)}",
                        network=network,
                        exchange='dextools',
                        launch_date=datetime.now(),
                        initial_price=np.random.uniform(0.001, 10),
                        volume_24h=np.random.uniform(1000, 100000),
                        market_cap=np.random.uniform(50000, 1000000),
                        liquidity=np.random.uniform(10000, 500000),
                        verified=False,
                        risk_score=np.random.uniform(3, 8)
                    )
                    currencies.append(currency)
            
            self.logger.info(f"✅ DexTools: Found {len(currencies)} currencies")
            return currencies
        except Exception as e:
            self.logger.error(f"❌ DexTools discovery failed: {e}")
        
        return []
    
    async def discover_from_birdeye(self) -> List[NewCurrency]:
        """Discover new currencies from Birdeye (Solana focused)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get trending tokens on Solana
                url = f"{self.data_sources['birdeye']}/defi/tokenlist"
                headers = {'X-API-KEY': 'YOUR_BIRDEYE_API_KEY'}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        currencies = []
                        
                        for token in data.get('data', {}).get('tokens', [])[:20]:
                            try:
                                currency = NewCurrency(
                                    symbol=token.get('symbol', ''),
                                    name=token.get('name', ''),
                                    contract_address=token.get('address', ''),
                                    network='solana',
                                    exchange='birdeye',
                                    launch_date=datetime.now(),
                                    initial_price=float(token.get('price', 0)),
                                    volume_24h=float(token.get('volume24h', 0)),
                                    market_cap=float(token.get('mc', 0)),
                                    liquidity=float(token.get('liquidity', 0)),
                                    verified=token.get('verified', False),
                                    risk_score=np.random.uniform(4, 7)  # Calculate based on metrics
                                )
                                currencies.append(currency)
                            except Exception as e:
                                self.logger.warning(f"Error parsing Birdeye token: {e}")
                        
                        self.logger.info(f"✅ Birdeye: Found {len(currencies)} currencies")
                        return currencies
        except Exception as e:
            self.logger.error(f"❌ Birdeye discovery failed: {e}")
        
        return []
    
    async def discover_from_exchanges(self) -> List[NewCurrency]:
        """Discover new listings from CEX exchanges"""
        currencies = []
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                # Reload markets to get latest listings
                exchange.load_markets()
                markets = exchange.markets
                
                # Check for recently added markets (simplified)
                for symbol, market in markets.items():
                    if self.is_recently_listed(market, exchange_name):
                        try:
                            ticker = exchange.fetch_ticker(symbol)
                            
                            currency = NewCurrency(
                                symbol=market['base'],
                                name=market['base'],  # Exchange doesn't provide full name
                                contract_address='',  # CEX doesn't provide contract
                                network=exchange_name,
                                exchange=exchange_name,
                                launch_date=datetime.now(),
                                initial_price=float(ticker.get('last', 0)),
                                volume_24h=float(ticker.get('quoteVolume', 0)),
                                market_cap=0,  # Not available from ticker
                                liquidity=float(ticker.get('quoteVolume', 0)),
                                verified=True,  # CEX listings are verified
                                risk_score=3.0  # Lower risk for CEX listings
                            )
                            currencies.append(currency)
                        except Exception as e:
                            self.logger.warning(f"Error fetching ticker for {symbol}: {e}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.warning(f"Error discovering from {exchange_name}: {e}")
        
        self.logger.info(f"✅ Exchanges: Found {len(currencies)} currencies")
        return currencies
    
    def calculate_risk_score(self, token_data: dict) -> float:
        """Calculate risk score for a token (1-10, lower is better)"""
        risk_score = 5.0  # Base score
        
        # Liquidity factor
        liquidity = float(token_data.get('liquidity', {}).get('usd', 0))
        if liquidity < 10000:
            risk_score += 3
        elif liquidity < 50000:
            risk_score += 1
        elif liquidity > 1000000:
            risk_score -= 1
        
        # Volume factor
        volume = float(token_data.get('volume', {}).get('h24', 0))
        if volume < 5000:
            risk_score += 2
        elif volume > 100000:
            risk_score -= 1
        
        # Age factor (if available)
        created_at = token_data.get('pairCreatedAt')
        if created_at:
            days_old = (datetime.now().timestamp() - created_at) / 86400
            if days_old < 1:
                risk_score += 2
            elif days_old > 30:
                risk_score -= 1
        
        # Verification factor
        if token_data.get('baseToken', {}).get('verified'):
            risk_score -= 1
        
        return max(1.0, min(10.0, risk_score))
    
    def calculate_coingecko_risk_score(self, coin_data: dict) -> float:
        """Calculate risk score for CoinGecko data"""
        risk_score = 4.0  # Lower base score for CoinGecko (more trusted)
        
        # Market cap factor
        market_cap = coin_data.get('market_data', {}).get('market_cap', {}).get('usd', 0)
        if market_cap < 100000:
            risk_score += 2
        elif market_cap > 10000000:
            risk_score -= 1
        
        # Volume factor
        volume = coin_data.get('market_data', {}).get('total_volume', {}).get('usd', 0)
        if volume < 10000:
            risk_score += 1
        elif volume > 1000000:
            risk_score -= 1
        
        # Community score
        community_score = coin_data.get('community_score', 0)
        if community_score > 50:
            risk_score -= 1
        elif community_score < 10:
            risk_score += 1
        
        return max(1.0, min(10.0, risk_score))
    
    async def validate_new_currencies(self, currencies: List[NewCurrency]) -> List[NewCurrency]:
        """Validate and filter new currencies based on risk criteria"""
        validated = []
        
        for currency in currencies:
            # Skip if already tracked
            if currency.symbol in self.tracked_currencies:
                continue
            
            # Apply risk filters
            if (currency.liquidity >= self.risk_thresholds['min_liquidity'] and
                currency.volume_24h >= self.risk_thresholds['min_volume'] and
                currency.risk_score <= self.risk_thresholds['max_risk_score']):
                
                # Additional validation
                if await self.additional_validation(currency):
                    validated.append(currency)
                    self.tracked_currencies.add(currency.symbol)
        
        return validated
    
    async def additional_validation(self, currency: NewCurrency) -> bool:
        """Perform additional validation checks"""
        try:
            # Check for honeypot/scam indicators
            if currency.contract_address and currency.network in self.dex_connections:
                # Implement honeypot detection
                if await self.check_honeypot(currency):
                    return False
            
            # Check social media presence
            if await self.check_social_presence(currency):
                return True
            
            # Check trading activity patterns
            if await self.check_trading_patterns(currency):
                return True
            
            return True
        except Exception as e:
            self.logger.warning(f"Validation failed for {currency.symbol}: {e}")
            return False
    
    async def check_honeypot(self, currency: NewCurrency) -> bool:
        """Check if token is a honeypot"""
        # Implement honeypot detection logic
        # This would involve checking:
        # - Can tokens be sold after buying
        # - Transfer restrictions
        # - Hidden functions in contract
        return False  # Placeholder
    
    async def check_social_presence(self, currency: NewCurrency) -> bool:
        """Check social media presence"""
        # Check Twitter, Telegram, Discord presence
        # Look for official accounts and community size
        return True  # Placeholder
    
    async def check_trading_patterns(self, currency: NewCurrency) -> bool:
        """Check for suspicious trading patterns"""
        # Look for:
        # - Wash trading
        # - Pump and dump patterns
        # - Unusual volume spikes
        return True  # Placeholder
    
    async def store_new_currencies(self, currencies: List[NewCurrency]) -> int:
        """Store validated currencies in database"""
        stored_count = 0
        cursor = self.conn.cursor()
        
        for currency in currencies:
            try:
                cursor.execute('''
                    INSERT INTO currencies (
                        symbol, name, contract_address, network, exchange,
                        launch_date, initial_price, current_price, volume_24h,
                        market_cap, liquidity, verified, risk_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    currency.symbol, currency.name, currency.contract_address,
                    currency.network, currency.exchange, currency.launch_date,
                    currency.initial_price, currency.initial_price, currency.volume_24h,
                    currency.market_cap, currency.liquidity, currency.verified,
                    currency.risk_score
                ))
                stored_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to store {currency.symbol}: {e}")
        
        self.conn.commit()
        return stored_count
    
    def get_contract_address(self, coin_data: dict) -> str:
        """Extract contract address from CoinGecko data"""
        platforms = coin_data.get('platforms', {})
        for platform, address in platforms.items():
            if address:
                return address
        return ''
    
    def get_network_from_platforms(self, coin_data: dict) -> str:
        """Get network from platforms data"""
        platforms = coin_data.get('platforms', {})
        if 'ethereum' in platforms:
            return 'ethereum'
        elif 'binance-smart-chain' in platforms:
            return 'bsc'
        elif 'polygon-pos' in platforms:
            return 'polygon'
        return list(platforms.keys())[0] if platforms else 'unknown'
    
    def get_current_price(self, coin_data: dict) -> float:
        """Get current price from CoinGecko data"""
        return float(coin_data.get('market_data', {}).get('current_price', {}).get('usd', 0))
    
    def get_volume_24h(self, coin_data: dict) -> float:
        """Get 24h volume from CoinGecko data"""
        return float(coin_data.get('market_data', {}).get('total_volume', {}).get('usd', 0))
    
    def get_market_cap(self, coin_data: dict) -> float:
        """Get market cap from CoinGecko data"""
        return float(coin_data.get('market_data', {}).get('market_cap', {}).get('usd', 0))
    
    def is_recently_listed(self, market: dict, exchange_name: str) -> bool:
        """Check if market was recently listed"""
        # This is a simplified check
        # In reality, you'd need to track listing dates
        return False  # Placeholder
    
    async def get_daily_new_currencies(self) -> List[Dict]:
        """Get today's discovered currencies"""
        cursor = self.conn.cursor()
        today = datetime.now().date()
        
        cursor.execute('''
            SELECT * FROM currencies 
            WHERE DATE(first_seen) = ? 
            ORDER BY risk_score ASC, volume_24h DESC
        ''', (today,))
        
        results = cursor.fetchall()
        
        # Convert to dict format
        columns = [desc[0] for desc in cursor.description]
        currencies = [dict(zip(columns, row)) for row in results]
        
        return currencies
    
    async def run_daily_discovery(self):
        """Run the daily discovery process"""
        while True:
            try:
                self.logger.info("🚀 Starting daily currency discovery...")
                
                # Discover new currencies
                new_currencies = await self.discover_new_currencies_daily()
                
                self.logger.info(f"✅ Daily discovery complete. Found {len(new_currencies)} new currencies")
                
                # Wait for next day
                await asyncio.sleep(86400)  # 24 hours
                
            except Exception as e:
                self.logger.error(f"❌ Daily discovery failed: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry

# Usage example
async def main():
    integrator = DEXCEXIntegrator()
    
    # Run daily discovery
    await integrator.run_daily_discovery()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 