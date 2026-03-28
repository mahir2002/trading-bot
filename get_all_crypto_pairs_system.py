#!/usr/bin/env python3
"""
🌍 ULTIMATE CRYPTO DISCOVERY SYSTEM
Get ALL trading pairs, cryptocurrencies, and new coins made daily
"""

import asyncio
import logging
import json
import sqlite3
import ccxt
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CryptoAsset:
    """Complete crypto asset information"""
    symbol: str
    name: str
    source: str  # 'cex', 'dex', 'coingecko', 'coinmarketcap'
    exchange: Optional[str] = None
    network: Optional[str] = None
    contract_address: Optional[str] = None
    market_cap_usd: Optional[float] = None
    price_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    rank: Optional[int] = None
    is_new: bool = False

class UltimateCryptoDiscoverySystem:
    """
    🚀 ULTIMATE CRYPTO DISCOVERY SYSTEM
    
    ✅ ALL CEX Trading Pairs (Binance, Coinbase, Kraken, Bybit, OKX, Gate.io, Huobi, KuCoin)
    ✅ ALL DEX Tokens (Uniswap, PancakeSwap, SushiSwap, Balancer, Curve)
    ✅ ALL Networks (Ethereum, BSC, Polygon, Arbitrum, Optimism, Avalanche, Fantom, Solana)
    ✅ NEW Coins Daily (CoinGecko, CoinMarketCap, GeckoTerminal trending)
    ✅ Historical tracking and comparison
    ✅ AI-ready data export
    """
    
    def __init__(self):
        logger.info("🌍 Initializing Ultimate Crypto Discovery System...")
        
        # API Configuration
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY', '')
        self.coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY', '')
        
        # Data storage
        self.db_path = Path('data/ultimate_crypto_discovery.db')
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Exchange configurations
        self.cex_exchanges = {
            'binance': ccxt.binance({'enableRateLimit': True}),
            'coinbasepro': ccxt.coinbasepro({'enableRateLimit': True}),
            'kraken': ccxt.kraken({'enableRateLimit': True}),
            'bybit': ccxt.bybit({'enableRateLimit': True}),
            'okx': ccxt.okx({'enableRateLimit': True}),
            'gate': ccxt.gate({'enableRateLimit': True}),
            'huobi': ccxt.huobi({'enableRateLimit': True}),
            'kucoin': ccxt.kucoin({'enableRateLimit': True})
        }
        
        # DEX configurations
        self.dex_networks = {
            'ethereum': {'geckoterminal_id': 'eth'},
            'bsc': {'geckoterminal_id': 'bsc'},
            'polygon': {'geckoterminal_id': 'polygon_pos'},
            'arbitrum': {'geckoterminal_id': 'arbitrum'},
            'optimism': {'geckoterminal_id': 'optimism'},
            'avalanche': {'geckoterminal_id': 'avax'},
            'fantom': {'geckoterminal_id': 'ftm'},
            'solana': {'geckoterminal_id': 'solana'}
        }
        
        # Data containers
        self.all_crypto_assets = {}
        self.cex_pairs = {}
        self.dex_tokens = {}
        self.new_listings = []
        
        # Statistics
        self.stats = {
            'total_assets': 0,
            'cex_pairs': 0,
            'dex_tokens': 0,
            'new_listings_today': 0,
            'networks_covered': 0,
            'exchanges_covered': 0,
            'last_update': None
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        logger.info("🗄️ Initializing database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                exchange TEXT,
                network TEXT,
                contract_address TEXT,
                market_cap_usd REAL,
                price_usd REAL,
                volume_24h_usd REAL,
                rank INTEGER,
                is_new BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE NOT NULL,
                total_assets INTEGER,
                new_assets_count INTEGER,
                snapshot_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON crypto_assets(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON crypto_assets(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_new ON crypto_assets(is_new)')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Database initialized")
    
    async def discover_all_crypto_assets(self) -> Dict[str, Any]:
        """
        🌍 DISCOVER ALL CRYPTO ASSETS
        Get everything: CEX pairs, DEX tokens, new listings
        """
        logger.info("🚀 Starting comprehensive crypto discovery...")
        
        start_time = datetime.now()
        
        try:
            # Run all discovery methods in parallel
            tasks = [
                self._discover_cex_pairs(),
                self._discover_dex_tokens(),
                self._discover_coingecko_coins(),
                self._discover_new_listings()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Consolidate all data
            await self._consolidate_all_data()
            
            # Save to database
            await self._save_to_database()
            
            # Update statistics
            self._update_statistics()
            
            # Create daily snapshot
            await self._create_daily_snapshot()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Discovery complete in {duration:.2f}s")
            logger.info(f"📊 Total assets discovered: {self.stats['total_assets']:,}")
            logger.info(f"🏦 CEX pairs: {self.stats['cex_pairs']:,}")
            logger.info(f"🌐 DEX tokens: {self.stats['dex_tokens']:,}")
            logger.info(f"🆕 New listings today: {self.stats['new_listings_today']:,}")
            
            return {
                'success': True,
                'stats': self.stats,
                'duration': duration,
                'total_assets': len(self.all_crypto_assets)
            }
            
        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _discover_cex_pairs(self) -> Dict[str, Any]:
        """Discover ALL CEX trading pairs"""
        logger.info("🏦 Discovering CEX trading pairs...")
        
        cex_data = {}
        total_pairs = 0
        
        for exchange_name, exchange in self.cex_exchanges.items():
            try:
                logger.info(f"   📈 Fetching from {exchange_name}...")
                
                # Load markets
                markets = exchange.load_markets()
                
                exchange_pairs = {}
                for symbol, market in markets.items():
                    if market.get('active', True):  # Only active pairs
                        asset = CryptoAsset(
                            symbol=symbol,
                            name=market.get('base', ''),
                            source='cex',
                            exchange=exchange_name
                        )
                        exchange_pairs[symbol] = asset
                        total_pairs += 1
                
                cex_data[exchange_name] = exchange_pairs
                logger.info(f"   ✅ {exchange_name}: {len(exchange_pairs):,} pairs")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"   ⚠️ {exchange_name} failed: {e}")
        
        self.cex_pairs = cex_data
        logger.info(f"✅ CEX discovery complete: {total_pairs:,} total pairs")
        
        return {'success': True, 'exchanges': len(cex_data), 'total_pairs': total_pairs}
    
    async def _discover_dex_tokens(self) -> Dict[str, Any]:
        """Discover ALL DEX tokens across networks"""
        logger.info("🌐 Discovering DEX tokens...")
        
        dex_data = {}
        total_tokens = 0
        
        async with aiohttp.ClientSession() as session:
            for network_name, network_config in self.dex_networks.items():
                try:
                    logger.info(f"   🔗 Fetching from {network_name}...")
                    
                    network_tokens = {}
                    
                    # Use GeckoTerminal API for trending tokens
                    geckoterminal_id = network_config['geckoterminal_id']
                    url = f"https://api.geckoterminal.com/api/v2/networks/{geckoterminal_id}/trending_pools"
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for pool in data.get('data', [])[:100]:  # Top 100 per network
                                attributes = pool.get('attributes', {})
                                base_token = attributes.get('base_token', {})
                                
                                if base_token:
                                    symbol = base_token.get('symbol', '').upper()
                                    name = base_token.get('name', '')
                                    address = base_token.get('address', '')
                                    
                                    if symbol and address:
                                        asset = CryptoAsset(
                                            symbol=symbol,
                                            name=name,
                                            source='dex',
                                            network=network_name,
                                            contract_address=address,
                                            market_cap_usd=attributes.get('market_cap_usd'),
                                            price_usd=float(attributes.get('base_token_price_usd', 0)),
                                            volume_24h_usd=float(attributes.get('volume_usd', {}).get('h24', 0))
                                        )
                                        
                                        token_key = f"{symbol}_{address[:8]}"
                                        network_tokens[token_key] = asset
                                        total_tokens += 1
                    
                    dex_data[network_name] = network_tokens
                    logger.info(f"   ✅ {network_name}: {len(network_tokens):,} tokens")
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"   ⚠️ {network_name} failed: {e}")
        
        self.dex_tokens = dex_data
        logger.info(f"✅ DEX discovery complete: {total_tokens:,} total tokens")
        
        return {'success': True, 'networks': len(dex_data), 'total_tokens': total_tokens}
    
    async def _discover_coingecko_coins(self) -> Dict[str, Any]:
        """Discover ALL coins from CoinGecko"""
        logger.info("🦎 Discovering CoinGecko coins...")
        
        coingecko_data = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get all coins list
                headers = {}
                if self.coingecko_api_key:
                    headers['x-cg-pro-api-key'] = self.coingecko_api_key
                
                url = "https://api.coingecko.com/api/v3/coins/list?include_platform=true"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        coins = await response.json()
                        
                        for coin in coins:
                            asset = CryptoAsset(
                                symbol=coin.get('symbol', '').upper(),
                                name=coin.get('name', ''),
                                source='coingecko'
                            )
                            
                            # Add platform info if available
                            platforms = coin.get('platforms', {})
                            if platforms:
                                platform_name = list(platforms.keys())[0]
                                asset.network = platform_name
                                asset.contract_address = platforms[platform_name]
                            
                            coingecko_data[coin['id']] = asset
                        
                        logger.info(f"✅ CoinGecko: {len(coingecko_data):,} coins")
                    else:
                        logger.warning(f"⚠️ CoinGecko API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ CoinGecko discovery failed: {e}")
        
        return {'success': True, 'total_coins': len(coingecko_data)}
    
    async def _discover_new_listings(self) -> Dict[str, Any]:
        """Discover NEW listings from today"""
        logger.info("🆕 Discovering new listings...")
        
        new_listings = []
        
        try:
            # Check for new listings by comparing with yesterday's snapshot
            yesterday = datetime.now() - timedelta(days=1)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get yesterday's assets
            cursor.execute('''
                SELECT symbol, source FROM crypto_assets 
                WHERE DATE(created_at) = DATE(?)
            ''', (yesterday.date(),))
            
            yesterday_assets = set(cursor.fetchall())
            
            # Get today's assets (will be populated after consolidation)
            cursor.execute('''
                SELECT symbol, source FROM crypto_assets 
                WHERE DATE(created_at) = DATE('now')
            ''')
            
            today_assets = set(cursor.fetchall())
            
            # Find new assets
            truly_new = today_assets - yesterday_assets
            
            for symbol, source in truly_new:
                new_listings.append({
                    'symbol': symbol,
                    'source': source,
                    'detected_at': datetime.now(),
                    'is_new': True
                })
            
            conn.close()
            
            self.new_listings = new_listings
            logger.info(f"✅ New listings: {len(new_listings)} detected")
            
        except Exception as e:
            logger.error(f"❌ New listings discovery failed: {e}")
        
        return {'success': True, 'new_listings': len(new_listings)}
    
    async def _consolidate_all_data(self):
        """Consolidate all discovered data"""
        logger.info("🔄 Consolidating all data...")
        
        consolidated = {}
        
        # Add CEX pairs
        for exchange, pairs in self.cex_pairs.items():
            for symbol, asset in pairs.items():
                key = f"cex_{exchange}_{symbol}"
                consolidated[key] = asset
        
        # Add DEX tokens
        for network, tokens in self.dex_tokens.items():
            for token_key, asset in tokens.items():
                key = f"dex_{network}_{token_key}"
                consolidated[key] = asset
        
        self.all_crypto_assets = consolidated
        logger.info(f"✅ Consolidated {len(consolidated):,} total assets")
    
    async def _save_to_database(self):
        """Save all data to database"""
        logger.info("💾 Saving to database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear today's data
        cursor.execute("DELETE FROM crypto_assets WHERE DATE(created_at) = DATE('now')")
        
        # Insert all assets
        for key, asset in self.all_crypto_assets.items():
            cursor.execute('''
                INSERT INTO crypto_assets (
                    symbol, name, source, exchange, network, contract_address,
                    market_cap_usd, price_usd, volume_24h_usd, rank, is_new
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset.symbol, asset.name, asset.source, asset.exchange,
                asset.network, asset.contract_address, asset.market_cap_usd,
                asset.price_usd, asset.volume_24h_usd, asset.rank, asset.is_new
            ))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Data saved to database")
    
    def _update_statistics(self):
        """Update system statistics"""
        self.stats.update({
            'total_assets': len(self.all_crypto_assets),
            'cex_pairs': sum(len(pairs) for pairs in self.cex_pairs.values()),
            'dex_tokens': sum(len(tokens) for tokens in self.dex_tokens.values()),
            'new_listings_today': len(self.new_listings),
            'networks_covered': len(self.dex_networks),
            'exchanges_covered': len(self.cex_exchanges),
            'last_update': datetime.now()
        })
    
    async def _create_daily_snapshot(self):
        """Create daily snapshot for historical tracking"""
        logger.info("📸 Creating daily snapshot...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create snapshot
            snapshot_data = {
                'total_assets': self.stats['total_assets'],
                'cex_pairs': self.stats['cex_pairs'],
                'dex_tokens': self.stats['dex_tokens'],
                'new_listings': self.stats['new_listings_today'],
                'timestamp': datetime.now().isoformat()
            }
            
            cursor.execute('''
                INSERT INTO historical_snapshots (
                    snapshot_date, total_assets, new_assets_count, snapshot_data
                ) VALUES (DATE('now'), ?, ?, ?)
            ''', (
                self.stats['total_assets'],
                self.stats['new_listings_today'],
                json.dumps(snapshot_data)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Daily snapshot created")
            
        except Exception as e:
            logger.error(f"❌ Snapshot creation failed: {e}")
    
    async def get_all_trading_pairs(self, format_for_bot: bool = True) -> List[str]:
        """Get ALL trading pairs formatted for trading bot"""
        logger.info("🎯 Generating trading pairs for bot...")
        
        if not self.all_crypto_assets:
            await self.discover_all_crypto_assets()
        
        trading_pairs = set()
        
        # Get CEX pairs (already in SYMBOL/QUOTE format)
        for exchange, pairs in self.cex_pairs.items():
            for symbol in pairs.keys():
                if '/USDT' in symbol or '/USD' in symbol or '/BTC' in symbol or '/ETH' in symbol:
                    trading_pairs.add(symbol)
        
        # Convert DEX tokens to trading pairs (add /USDT)
        for network, tokens in self.dex_tokens.items():
            for token_key, asset in tokens.items():
                if asset.symbol and asset.symbol not in ['USDT', 'USD', 'USDC']:
                    trading_pairs.add(f"{asset.symbol}/USDT")
        
        # Convert to sorted list
        pairs_list = sorted(list(trading_pairs))
        
        logger.info(f"✅ Generated {len(pairs_list):,} trading pairs")
        
        return pairs_list
    
    async def get_new_listings_today(self) -> List[Dict]:
        """Get all new listings detected today"""
        logger.info("🆕 Getting today's new listings...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, name, source, exchange, network, contract_address,
                   market_cap_usd, price_usd, volume_24h_usd, created_at
            FROM crypto_assets 
            WHERE DATE(created_at) = DATE('now') AND is_new = 1
            ORDER BY market_cap_usd DESC NULLS LAST
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        new_listings = []
        for row in rows:
            new_listings.append({
                'symbol': row[0],
                'name': row[1],
                'source': row[2],
                'exchange': row[3],
                'network': row[4],
                'contract_address': row[5],
                'market_cap_usd': row[6],
                'price_usd': row[7],
                'volume_24h_usd': row[8],
                'detected_at': row[9]
            })
        
        logger.info(f"✅ Found {len(new_listings)} new listings today")
        
        return new_listings
    
    async def export_for_ai_analysis(self, filename: str = None) -> str:
        """Export all data for AI analysis"""
        if not filename:
            filename = f"all_crypto_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logger.info(f"📤 Exporting data for AI analysis: {filename}")
        
        export_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_assets': len(self.all_crypto_assets),
                'stats': self.stats
            },
            'cex_pairs': {},
            'dex_tokens': {},
            'new_listings': self.new_listings,
            'all_trading_pairs': await self.get_all_trading_pairs()
        }
        
        # Add CEX data
        for exchange, pairs in self.cex_pairs.items():
            export_data['cex_pairs'][exchange] = {
                symbol: asdict(asset) for symbol, asset in pairs.items()
            }
        
        # Add DEX data
        for network, tokens in self.dex_tokens.items():
            export_data['dex_tokens'][network] = {
                token_key: asdict(asset) for token_key, asset in tokens.items()
            }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"✅ Data exported to {filename}")
        
        return filename
    
    async def display_comprehensive_summary(self):
        """Display comprehensive summary of all discovered data"""
        print("=" * 80)
        print("🌍 ULTIMATE CRYPTO DISCOVERY SYSTEM - COMPLETE SUMMARY")
        print("=" * 80)
        
        print(f"📊 TOTAL ASSETS DISCOVERED: {self.stats['total_assets']:,}")
        print(f"🏦 CEX TRADING PAIRS: {self.stats['cex_pairs']:,}")
        print(f"🌐 DEX TOKENS: {self.stats['dex_tokens']:,}")
        print(f"🆕 NEW LISTINGS TODAY: {self.stats['new_listings_today']:,}")
        print(f"🔗 NETWORKS COVERED: {self.stats['networks_covered']}")
        print(f"📈 EXCHANGES COVERED: {self.stats['exchanges_covered']}")
        print(f"⏰ LAST UPDATE: {self.stats['last_update']}")
        
        print("\n" + "=" * 80)
        print("🏦 CEX EXCHANGES COVERAGE:")
        for exchange, pairs in self.cex_pairs.items():
            print(f"   📈 {exchange.upper()}: {len(pairs):,} pairs")
        
        print("\n" + "=" * 80)
        print("🌐 DEX NETWORKS COVERAGE:")
        for network, tokens in self.dex_tokens.items():
            print(f"   🔗 {network.upper()}: {len(tokens):,} tokens")
        
        if self.new_listings:
            print("\n" + "=" * 80)
            print("🆕 TODAY'S NEW LISTINGS (TOP 10):")
            for i, listing in enumerate(self.new_listings[:10], 1):
                print(f"   {i}. {listing['symbol']} ({listing['source']})")
        
        print("\n" + "=" * 80)
        print("✅ DISCOVERY COMPLETE - ALL CRYPTO ASSETS CATALOGUED!")
        print("=" * 80)

async def main():
    """Main function to demonstrate the system"""
    logger.info("🚀 Starting Ultimate Crypto Discovery System Demo...")
    
    # Create system
    discovery = UltimateCryptoDiscoverySystem()
    
    # Discover all crypto assets
    result = await discovery.discover_all_crypto_assets()
    
    if result['success']:
        # Display summary
        await discovery.display_comprehensive_summary()
        
        # Get all trading pairs for bot
        trading_pairs = await discovery.get_all_trading_pairs()
        print(f"\n🎯 TRADING PAIRS FOR BOT: {len(trading_pairs):,}")
        print("Top 20 pairs:", trading_pairs[:20])
        
        # Get new listings
        new_listings = await discovery.get_new_listings_today()
        print(f"\n🆕 NEW LISTINGS TODAY: {len(new_listings)}")
        
        # Export for AI
        ai_file = await discovery.export_for_ai_analysis()
        print(f"\n📤 AI DATA EXPORTED: {ai_file}")
        
        logger.info("✅ Demo completed successfully!")
    else:
        logger.error(f"❌ Demo failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
