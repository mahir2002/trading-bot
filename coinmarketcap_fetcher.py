#!/usr/bin/env python3
"""
CoinMarketCap API Fetcher
Fetches comprehensive cryptocurrency data from CoinMarketCap API
Expands coverage beyond just Binance pairs
"""

import requests
import json
from typing import Dict, List, Optional
import logging
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

class CoinMarketCapFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.sandbox_url = "https://sandbox-api.coinmarketcap.com/v1"
        
        # Use sandbox for testing if no API key
        if not self.api_key:
            self.logger.warning("⚠️ No CoinMarketCap API key found. Using sandbox mode for testing.")
            self.base_url = self.sandbox_url
            self.api_key = "b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c"  # Sandbox key
        
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to CoinMarketCap API"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"CMC API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error making CMC API request: {e}")
            return None
    
    def get_cryptocurrency_listings(self, limit: int = 5000) -> Dict[str, Dict]:
        """
        Get comprehensive cryptocurrency listings from CoinMarketCap
        Returns much more data than Binance including market cap, rankings, etc.
        """
        try:
            self.logger.info(f"📡 Fetching {limit} cryptocurrencies from CoinMarketCap...")
            
            params = {
                'start': 1,
                'limit': limit,
                'convert': 'USD',
                'sort': 'market_cap',
                'sort_dir': 'desc'
            }
            
            data = self._make_request('cryptocurrency/listings/latest', params)
            
            if not data or 'data' not in data:
                self.logger.error("Failed to fetch CMC listings")
                return {}
            
            cryptocurrencies = {}
            
            for crypto in data['data']:
                symbol = crypto['symbol']
                name = crypto['name']
                slug = crypto['slug']
                
                # Get quote data
                quote = crypto.get('quote', {}).get('USD', {})
                
                # Categorize the cryptocurrency
                category = self.categorize_crypto(name, symbol, crypto.get('tags', []))
                
                cryptocurrencies[symbol] = {
                    'id': crypto['id'],
                    'name': name,
                    'symbol': symbol,
                    'slug': slug,
                    'rank': crypto.get('cmc_rank', 0),
                    'price': quote.get('price', 0),
                    'volume_24h': quote.get('volume_24h', 0),
                    'volume_change_24h': quote.get('volume_change_24h', 0),
                    'percent_change_1h': quote.get('percent_change_1h', 0),
                    'percent_change_24h': quote.get('percent_change_24h', 0),
                    'percent_change_7d': quote.get('percent_change_7d', 0),
                    'percent_change_30d': quote.get('percent_change_30d', 0),
                    'market_cap': quote.get('market_cap', 0),
                    'market_cap_dominance': quote.get('market_cap_dominance', 0),
                    'fully_diluted_market_cap': quote.get('fully_diluted_market_cap', 0),
                    'circulating_supply': crypto.get('circulating_supply', 0),
                    'total_supply': crypto.get('total_supply', 0),
                    'max_supply': crypto.get('max_supply', 0),
                    'last_updated': quote.get('last_updated', ''),
                    'category': category,
                    'emoji': self.get_crypto_emoji(symbol),
                    'tags': crypto.get('tags', []),
                    'platform': crypto.get('platform', {}),
                    'date_added': crypto.get('date_added', ''),
                    'is_active': crypto.get('is_active', 1),
                    'is_fiat': crypto.get('is_fiat', 0)
                }
            
            self.logger.info(f"✅ Fetched {len(cryptocurrencies)} cryptocurrencies from CoinMarketCap")
            return cryptocurrencies
            
        except Exception as e:
            self.logger.error(f"Error fetching CMC listings: {e}")
            return {}
    
    def get_trending_cryptocurrencies(self) -> List[Dict]:
        """Get trending cryptocurrencies"""
        try:
            data = self._make_request('cryptocurrency/trending/latest')
            
            if not data or 'data' not in data:
                return []
            
            trending = []
            for crypto in data['data']:
                trending.append({
                    'id': crypto['id'],
                    'name': crypto['name'],
                    'symbol': crypto['symbol'],
                    'slug': crypto['slug'],
                    'rank': crypto.get('cmc_rank', 0),
                    'category': self.categorize_crypto(crypto['name'], crypto['symbol'], crypto.get('tags', [])),
                    'emoji': self.get_crypto_emoji(crypto['symbol'])
                })
            
            return trending
            
        except Exception as e:
            self.logger.error(f"Error fetching trending: {e}")
            return []
    
    def get_gainers_losers(self) -> Dict[str, List]:
        """Get top gainers and losers"""
        try:
            data = self._make_request('cryptocurrency/trending/gainers-losers')
            
            if not data or 'data' not in data:
                return {'gainers': [], 'losers': []}
            
            result = {'gainers': [], 'losers': []}
            
            for gainer in data['data'].get('gainers', []):
                result['gainers'].append({
                    'symbol': gainer['symbol'],
                    'name': gainer['name'],
                    'percent_change_24h': gainer.get('quote', {}).get('USD', {}).get('percent_change_24h', 0),
                    'price': gainer.get('quote', {}).get('USD', {}).get('price', 0),
                    'emoji': self.get_crypto_emoji(gainer['symbol'])
                })
            
            for loser in data['data'].get('losers', []):
                result['losers'].append({
                    'symbol': loser['symbol'],
                    'name': loser['name'],
                    'percent_change_24h': loser.get('quote', {}).get('USD', {}).get('percent_change_24h', 0),
                    'price': loser.get('quote', {}).get('USD', {}).get('price', 0),
                    'emoji': self.get_crypto_emoji(loser['symbol'])
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching gainers/losers: {e}")
            return {'gainers': [], 'losers': []}
    
    def get_global_metrics(self) -> Dict:
        """Get global cryptocurrency market metrics"""
        try:
            data = self._make_request('global-metrics/quotes/latest')
            
            if not data or 'data' not in data:
                return {}
            
            global_data = data['data']
            quote = global_data.get('quote', {}).get('USD', {})
            
            return {
                'total_cryptocurrencies': global_data.get('total_cryptocurrencies', 0),
                'total_market_cap': quote.get('total_market_cap', 0),
                'total_volume_24h': quote.get('total_volume_24h', 0),
                'total_volume_24h_reported': quote.get('total_volume_24h_reported', 0),
                'altcoin_volume_24h': quote.get('altcoin_volume_24h', 0),
                'altcoin_market_cap': quote.get('altcoin_market_cap', 0),
                'btc_dominance': global_data.get('btc_dominance', 0),
                'eth_dominance': global_data.get('eth_dominance', 0),
                'defi_volume_24h': quote.get('defi_volume_24h', 0),
                'defi_market_cap': quote.get('defi_market_cap', 0),
                'derivatives_volume_24h': quote.get('derivatives_volume_24h', 0),
                'stablecoin_volume_24h': quote.get('stablecoin_volume_24h', 0),
                'stablecoin_market_cap': quote.get('stablecoin_market_cap', 0),
                'last_updated': quote.get('last_updated', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching global metrics: {e}")
            return {}
    
    def categorize_crypto(self, name: str, symbol: str, tags: List[str]) -> str:
        """
        Categorize cryptocurrency based on name, symbol, and tags
        Enhanced categorization using CMC tags
        """
        name_lower = name.lower()
        symbol_upper = symbol.upper()
        tags_lower = [tag.lower() for tag in tags]
        
        # Use CMC tags for better categorization
        if any(tag in tags_lower for tag in ['defi', 'decentralized-exchange', 'yield-farming', 'lending-borrowing']):
            return 'DeFi'
        elif any(tag in tags_lower for tag in ['memes', 'meme', 'dog-themed']):
            return 'Meme'
        elif any(tag in tags_lower for tag in ['gaming', 'play-to-earn', 'nft', 'metaverse', 'virtual-reality']):
            return 'Gaming'
        elif any(tag in tags_lower for tag in ['ai-big-data', 'artificial-intelligence', 'machine-learning']):
            return 'AI'
        elif any(tag in tags_lower for tag in ['layer-1', 'smart-contracts', 'platform']):
            return 'Layer1'
        elif any(tag in tags_lower for tag in ['layer-2', 'scaling', 'ethereum-ecosystem']):
            return 'Layer2'
        elif any(tag in tags_lower for tag in ['privacy', 'privacy-coins']):
            return 'Privacy'
        elif any(tag in tags_lower for tag in ['stablecoin', 'stablecoins']):
            return 'Stablecoin'
        elif any(tag in tags_lower for tag in ['exchange-based-tokens', 'centralized-exchange']):
            return 'Exchange'
        elif any(tag in tags_lower for tag in ['storage', 'distributed-computing', 'filesharing']):
            return 'Storage'
        elif any(tag in tags_lower for tag in ['oracles', 'oracle']):
            return 'Oracle'
        elif any(tag in tags_lower for tag in ['social-money', 'content-creation', 'fan-token']):
            return 'Social'
        elif any(tag in tags_lower for tag in ['enterprise-solutions', 'supply-chain']):
            return 'Enterprise'
        elif any(tag in tags_lower for tag in ['wrapped-tokens', 'tokenized-btc']):
            return 'Wrapped'
        elif any(tag in tags_lower for tag in ['derivatives', 'prediction-markets']):
            return 'Derivatives'
        elif any(tag in tags_lower for tag in ['energy', 'carbon-credit']):
            return 'Energy'
        elif any(tag in tags_lower for tag in ['real-estate', 'commodities']):
            return 'RealWorld'
        
        # Fallback to symbol-based categorization
        major_coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'LTC', 'BCH', 'ETC', 'XLM', 'VET', 'TRX', 'FIL', 'EOS', 'THETA', 'AAVE']
        if symbol_upper in major_coins:
            return 'Major'
        
        return 'Other'
    
    def get_crypto_emoji(self, symbol: str) -> str:
        """Get emoji for cryptocurrency"""
        emoji_mapping = {
            # Major Cryptocurrencies
            'BTC': '₿', 'ETH': '⟠', 'BNB': '🟡', 'XRP': '💧', 'ADA': '🔵',
            'SOL': '🌞', 'DOT': '🔴', 'AVAX': '🔺', 'MATIC': '🟣', 'LINK': '🔗',
            'LTC': '🥈', 'BCH': '💚', 'ETC': '🟢', 'XLM': '⭐', 'VET': '✅',
            'TRX': '🔥', 'FIL': '📁', 'EOS': '⚫', 'THETA': '📺', 'AAVE': '👻',
            
            # DeFi
            'UNI': '🦄', 'SUSHI': '🍣', 'CAKE': '🥞', 'CRV': '📈', '1INCH': '📏',
            'YFI': '💰', 'COMP': '🏛️', 'MKR': '🏗️', 'SNX': '⚡', 'BAL': '⚖️',
            
            # Memecoins
            'DOGE': '🐕', 'SHIB': '🐕‍🦺', 'PEPE': '🐸', 'FLOKI': '🐕‍🦺',
            'BONK': '🔨', 'WIF': '🎩', 'ELON': '🚀', 'SAFEMOON': '🌙',
            
            # Gaming & NFT
            'AXS': '🎮', 'SAND': '🏖️', 'MANA': '🌐', 'ENJ': '💎', 'GALA': '🎪',
            'ILV': '⚔️', 'ALICE': '🐰', 'TLM': '👽', 'CHR': '🎨',
            
            # AI & Data
            'FET': '🤖', 'OCEAN': '🌊', 'AGIX': '🧠', 'RENDER': '🎨', 'GRT': '📊',
            'NMR': '🔢', 'CTXC': '🧠', 'AI': '🤖', 'GPT': '💬',
            
            # Layer 1 & 2
            'NEAR': '🔮', 'ATOM': '⚛️', 'ALGO': '🔷', 'FTM': '👻', 'ONE': '1️⃣',
            'HBAR': '♦️', 'EGLD': '⚡', 'LUNA': '🌙', 'ROSE': '🌹', 'OP': '🔴',
            'ARB': '🔵', 'METIS': '🌟', 'BOBA': '🧋',
            
            # Privacy
            'XMR': '🔒', 'ZEC': '🛡️', 'DASH': '💨', 'FIRO': '🔒', 'BEAM': '💡',
            
            # Stablecoins
            'USDT': '💵', 'USDC': '💵', 'BUSD': '💵', 'DAI': '💵', 'TUSD': '💵',
            
            # Exchange
            'CRO': '💎', 'FTT': '🔥', 'KCS': '💎', 'HT': '🔥', 'OKB': '⭕',
            
            # Storage
            'AR': '🗄️', 'STORJ': '☁️', 'SIA': '📁', 'BTT': '📁', 'HOT': '🔥',
            
            # Oracle
            'BAND': '📡', 'API3': '🔌', 'TRB': '📊', 'DIA': '💎',
            
            # Social
            'CHZ': '⚽', 'AUDIO': '🎵', 'RALLY': '📢', 'MASK': '🎭',
            
            # Others
            'USDT': '💵', 'USDC': '💵', 'BUSD': '💵', 'STETH': '⟠',
            'WBTC': '₿', 'LEO': '🦁', 'TON': '💎', 'ICP': '♾️'
        }
        
        return emoji_mapping.get(symbol.upper(), '💰')
    
    def get_comprehensive_data(self, limit: int = 2000) -> Dict:
        """
        Get comprehensive cryptocurrency data combining multiple endpoints
        """
        try:
            self.logger.info("🚀 Fetching comprehensive CoinMarketCap data...")
            
            # Get main listings
            listings = self.get_cryptocurrency_listings(limit)
            
            # Get global metrics
            global_metrics = self.get_global_metrics()
            
            # Get trending (if available)
            trending = self.get_trending_cryptocurrencies()
            
            # Get gainers/losers (if available)
            gainers_losers = self.get_gainers_losers()
            
            return {
                'cryptocurrencies': listings,
                'global_metrics': global_metrics,
                'trending': trending,
                'gainers': gainers_losers.get('gainers', []),
                'losers': gainers_losers.get('losers', []),
                'total_count': len(listings),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching comprehensive data: {e}")
            return {}

def main():
    """Test the CoinMarketCap fetcher"""
    fetcher = CoinMarketCapFetcher()
    
    print("🚀 COINMARKETCAP API INTEGRATION TEST")
    print("=" * 60)
    
    # Test comprehensive data fetch
    data = fetcher.get_comprehensive_data(100)  # Test with 100 coins
    
    if data and 'cryptocurrencies' in data:
        cryptos = data['cryptocurrencies']
        print(f"📊 Total cryptocurrencies fetched: {len(cryptos)}")
        
        # Show breakdown by category
        categories = {}
        for symbol, info in cryptos.items():
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(symbol)
        
        print(f"\n📈 Breakdown by category:")
        for category, symbols in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   {category}: {len(symbols)} coins")
            if len(symbols) > 0:
                examples = symbols[:3]
                example_names = [cryptos[s]['name'] for s in examples]
                print(f"      Examples: {', '.join(example_names)}")
        
        # Show top 10 by market cap
        print(f"\n🏆 Top 10 by Market Cap:")
        sorted_cryptos = sorted(cryptos.items(), key=lambda x: x[1]['market_cap'], reverse=True)
        for i, (symbol, info) in enumerate(sorted_cryptos[:10], 1):
            market_cap = info['market_cap']
            price = info['price']
            change_24h = info['percent_change_24h']
            print(f"   {i:2d}. {symbol:8} - {info['name']:20} ${price:>10.4f} ({change_24h:+6.2f}%) MC: ${market_cap:>15,.0f}")
        
        # Show global metrics
        if 'global_metrics' in data and data['global_metrics']:
            global_data = data['global_metrics']
            print(f"\n🌍 Global Market Metrics:")
            print(f"   Total Cryptocurrencies: {global_data.get('total_cryptocurrencies', 0):,}")
            print(f"   Total Market Cap: ${global_data.get('total_market_cap', 0):,.0f}")
            print(f"   24h Volume: ${global_data.get('total_volume_24h', 0):,.0f}")
            print(f"   BTC Dominance: {global_data.get('btc_dominance', 0):.2f}%")
            print(f"   ETH Dominance: {global_data.get('eth_dominance', 0):.2f}%")
        
        print(f"\n✅ COINMARKETCAP INTEGRATION SUCCESSFUL!")
        print(f"🎉 You now have access to comprehensive market data!")
        print(f"📊 Market cap rankings, global metrics, and much more!")
        
    else:
        print("❌ Failed to fetch data. Check your API key configuration.")
        print("💡 Add your CoinMarketCap API key to config.env:")
        print("   COINMARKETCAP_API_KEY=your_api_key_here")

if __name__ == "__main__":
    main() 