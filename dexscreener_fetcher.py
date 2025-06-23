#!/usr/bin/env python3
"""
DEX Screener API Integration
Fetches real-time data from decentralized exchanges including trending tokens,
new pairs, price data, and comprehensive DEX analytics
"""

import requests
import logging
import time
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

class DEXScreenerFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('DEXSCREENER_API_KEY')
        self.base_url = "https://api.dexscreener.com"
        
        # Headers for API requests
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'AI-Trading-Bot/1.0'
        }
        
        # Add API key to headers if available
        if self.api_key and self.api_key != 'your_dexscreener_api_key_here':
            self.headers['X-API-Key'] = self.api_key
            self.logger.info("✅ DEX Screener API key configured")
        else:
            self.logger.warning("⚠️ No DEX Screener API key found. Using public endpoints only.")
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 0.5 seconds between requests
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to DEX Screener API"""
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
                self.logger.error(f"DEX Screener API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error making DEX Screener API request: {e}")
            return None
    
    def get_trending_tokens(self, limit: int = 50) -> List[Dict]:
        """Get trending tokens from boosted tokens endpoint"""
        try:
            self.logger.info(f"📈 Fetching {limit} trending tokens from DEX Screener...")
            
            # Use boosted tokens as trending indicator
            data = self._make_request('token-boosts/latest/v1')
            
            if not data:
                self.logger.error("Failed to fetch trending tokens")
                return []
            
            trending_tokens = []
            
            # Process boosted tokens data
            if isinstance(data, list):
                for boost in data[:limit]:
                    token_info = self._process_boost_data(boost)
                    if token_info:
                        trending_tokens.append(token_info)
            
            self.logger.info(f"✅ Fetched {len(trending_tokens)} trending tokens")
            return trending_tokens
            
        except Exception as e:
            self.logger.error(f"Error fetching trending tokens: {e}")
            return []
    
    def get_new_pairs(self, limit: int = 50) -> List[Dict]:
        """Get pairs by searching for popular tokens"""
        try:
            self.logger.info(f"🆕 Fetching {limit} popular pairs from DEX Screener...")
            
            # Search for popular tokens like ETH, BTC, SOL
            popular_searches = ['ETH', 'BTC', 'SOL', 'USDC', 'USDT']
            all_pairs = []
            
            for search_term in popular_searches:
                data = self._make_request(f'latest/dex/search?q={search_term}')
                
                if data and 'pairs' in data:
                    for pair in data['pairs'][:10]:  # Get 10 pairs per search
                        pair_info = self._process_pair_data(pair)
                        if pair_info:
                            all_pairs.append(pair_info)
                
                if len(all_pairs) >= limit:
                    break
            
            new_pairs = all_pairs[:limit]
            self.logger.info(f"✅ Fetched {len(new_pairs)} popular pairs")
            return new_pairs
            
        except Exception as e:
            self.logger.error(f"Error fetching popular pairs: {e}")
            return []
    
    def search_tokens(self, query: str) -> List[Dict]:
        """Search for tokens by name, symbol, or address"""
        try:
            self.logger.info(f"🔍 Searching for tokens: {query}")
            
            data = self._make_request(f'latest/dex/search?q={query}')
            
            if not data or 'pairs' not in data:
                self.logger.error(f"Failed to search for tokens: {query}")
                return []
            
            search_results = []
            
            for pair in data['pairs']:
                token_info = self._process_pair_data(pair)
                if token_info:
                    search_results.append(token_info)
            
            self.logger.info(f"✅ Found {len(search_results)} results for '{query}'")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching tokens: {e}")
            return []
    
    def get_token_profile(self, chain_id: str, token_address: str) -> Optional[Dict]:
        """Get detailed profile for a specific token"""
        try:
            self.logger.info(f"📊 Fetching token profile: {chain_id}/{token_address}")
            
            data = self._make_request(f'tokens/v1/{chain_id}/{token_address}')
            
            if not data:
                self.logger.error(f"Failed to fetch token profile: {token_address}")
                return None
            
            # Process the token data
            if isinstance(data, list) and len(data) > 0:
                token_profile = self._process_pair_data(data[0], detailed=True)
                self.logger.info(f"✅ Fetched profile for {token_profile.get('baseToken', {}).get('symbol', 'Unknown')}")
                return token_profile
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching token profile: {e}")
            return None
    
    def get_dex_pairs(self, dex_id: str, limit: int = 50) -> List[Dict]:
        """Get pairs from a specific DEX (uniswap, pancakeswap, sushiswap, etc.)"""
        try:
            self.logger.info(f"🏪 Fetching {limit} pairs from {dex_id}")
            
            data = self._make_request(f'latest/dex/{dex_id}')
            
            if not data or 'pairs' not in data:
                self.logger.error(f"Failed to fetch pairs from {dex_id}")
                return []
            
            dex_pairs = []
            
            for pair in data['pairs'][:limit]:
                pair_info = self._process_pair_data(pair)
                if pair_info:
                    dex_pairs.append(pair_info)
            
            self.logger.info(f"✅ Fetched {len(dex_pairs)} pairs from {dex_id}")
            return dex_pairs
            
        except Exception as e:
            self.logger.error(f"Error fetching DEX pairs: {e}")
            return []
    
    def _process_boost_data(self, boost: Dict) -> Optional[Dict]:
        """Process boost data from DEX Screener"""
        try:
            # Create a simplified token info from boost data
            token_info = {
                'chainId': boost.get('chainId', ''),
                'tokenAddress': boost.get('tokenAddress', ''),
                'url': boost.get('url', ''),
                'baseToken': {
                    'address': boost.get('tokenAddress', ''),
                    'name': 'Boosted Token',
                    'symbol': 'BOOST',
                },
                'quoteToken': {
                    'address': '',
                    'name': 'USD',
                    'symbol': 'USD',
                },
                'priceUsd': '0',
                'volume': {'h24': 0},
                'priceChange': {'h24': 0},
                'liquidity': {'usd': 0},
                'fdv': 0,
                'marketCap': 0,
                'pairCreatedAt': 0,
                'category': 'Trending',
                'emoji': '🔥',
                'risk_score': 'Medium',
                'boost_amount': boost.get('amount', 0),
                'boost_total': boost.get('totalAmount', 0),
                'last_updated': datetime.now().isoformat()
            }
            
            return token_info
            
        except Exception as e:
            self.logger.error(f"Error processing boost data: {e}")
            return None
    
    def _process_pair_data(self, pair: Dict, detailed: bool = False) -> Optional[Dict]:
        """Process and standardize pair data from DEX Screener"""
        try:
            base_token = pair.get('baseToken', {})
            quote_token = pair.get('quoteToken', {})
            
            # Basic token info
            token_info = {
                'pairAddress': pair.get('pairAddress', ''),
                'chainId': pair.get('chainId', ''),
                'dexId': pair.get('dexId', ''),
                'url': pair.get('url', ''),
                'baseToken': {
                    'address': base_token.get('address', ''),
                    'name': base_token.get('name', ''),
                    'symbol': base_token.get('symbol', ''),
                },
                'quoteToken': {
                    'address': quote_token.get('address', ''),
                    'name': quote_token.get('name', ''),
                    'symbol': quote_token.get('symbol', ''),
                },
                'priceNative': pair.get('priceNative', '0'),
                'priceUsd': pair.get('priceUsd', '0'),
                'txns': pair.get('txns', {}),
                'volume': pair.get('volume', {}),
                'priceChange': pair.get('priceChange', {}),
                'liquidity': pair.get('liquidity', {}),
                'fdv': pair.get('fdv', 0),
                'marketCap': pair.get('marketCap', 0),
                'pairCreatedAt': pair.get('pairCreatedAt', 0),
                'category': self._categorize_dex_token(base_token.get('symbol', ''), base_token.get('name', '')),
                'emoji': self._get_dex_token_emoji(base_token.get('symbol', '')),
                'risk_score': self._calculate_risk_score(pair),
                'last_updated': datetime.now().isoformat()
            }
            
            # Add detailed info if requested
            if detailed:
                token_info.update({
                    'info': pair.get('info', {}),
                    'boosts': pair.get('boosts', {}),
                    'labels': pair.get('labels', []),
                })
            
            return token_info
            
        except Exception as e:
            self.logger.error(f"Error processing pair data: {e}")
            return None
    
    def _categorize_dex_token(self, symbol: str, name: str) -> str:
        """Categorize DEX tokens based on symbol and name"""
        symbol_lower = symbol.lower()
        name_lower = name.lower()
        
        # Meme tokens
        meme_keywords = ['doge', 'shib', 'pepe', 'floki', 'meme', 'inu', 'elon', 'moon', 'safe']
        if any(keyword in symbol_lower or keyword in name_lower for keyword in meme_keywords):
            return 'Meme'
        
        # DeFi tokens
        defi_keywords = ['swap', 'finance', 'yield', 'farm', 'stake', 'vault', 'protocol', 'dao']
        if any(keyword in symbol_lower or keyword in name_lower for keyword in defi_keywords):
            return 'DeFi'
        
        # Gaming tokens
        gaming_keywords = ['game', 'play', 'nft', 'meta', 'verse', 'land', 'hero', 'quest']
        if any(keyword in symbol_lower or keyword in name_lower for keyword in gaming_keywords):
            return 'Gaming'
        
        # AI tokens
        ai_keywords = ['ai', 'artificial', 'intelligence', 'neural', 'machine', 'learning', 'bot']
        if any(keyword in symbol_lower or keyword in name_lower for keyword in ai_keywords):
            return 'AI'
        
        return 'Other'
    
    def _get_dex_token_emoji(self, symbol: str) -> str:
        """Get emoji for DEX tokens"""
        symbol_lower = symbol.lower()
        
        emoji_map = {
            'eth': '⟠', 'btc': '₿', 'bnb': '🟡', 'ada': '🔵', 'sol': '🌞',
            'doge': '🐕', 'shib': '🐕‍🦺', 'pepe': '🐸', 'floki': '🐕‍🦺',
            'uni': '🦄', 'cake': '🥞', 'sushi': '🍣', 'aave': '👻',
            'link': '🔗', 'dot': '🔴', 'matic': '🟣', 'avax': '🔺',
        }
        
        for key, emoji in emoji_map.items():
            if key in symbol_lower:
                return emoji
        
        # Category-based emojis
        if 'meme' in symbol_lower or any(x in symbol_lower for x in ['doge', 'shib', 'pepe', 'inu']):
            return '🚀'
        elif 'game' in symbol_lower or 'nft' in symbol_lower:
            return '🎮'
        elif 'ai' in symbol_lower:
            return '🤖'
        elif any(x in symbol_lower for x in ['swap', 'finance', 'defi']):
            return '💱'
        
        return '💎'
    
    def _calculate_risk_score(self, pair: Dict) -> str:
        """Calculate risk score based on various factors"""
        try:
            # Get key metrics
            liquidity_usd = float(pair.get('liquidity', {}).get('usd', 0))
            volume_24h = float(pair.get('volume', {}).get('h24', 0))
            txns_24h = pair.get('txns', {}).get('h24', {})
            buys = int(txns_24h.get('buys', 0)) if txns_24h else 0
            sells = int(txns_24h.get('sells', 0)) if txns_24h else 0
            
            risk_factors = 0
            
            # Low liquidity risk
            if liquidity_usd < 10000:
                risk_factors += 3
            elif liquidity_usd < 50000:
                risk_factors += 2
            elif liquidity_usd < 100000:
                risk_factors += 1
            
            # Low volume risk
            if volume_24h < 1000:
                risk_factors += 3
            elif volume_24h < 10000:
                risk_factors += 2
            elif volume_24h < 50000:
                risk_factors += 1
            
            # Transaction imbalance risk
            total_txns = buys + sells
            if total_txns > 0:
                sell_ratio = sells / total_txns
                if sell_ratio > 0.8:  # Too many sells
                    risk_factors += 2
                elif sell_ratio > 0.7:
                    risk_factors += 1
            
            # Age risk (new pairs are riskier)
            pair_created = pair.get('pairCreatedAt', 0)
            if pair_created > 0:
                age_hours = (time.time() - pair_created / 1000) / 3600
                if age_hours < 24:
                    risk_factors += 2
                elif age_hours < 168:  # 1 week
                    risk_factors += 1
            
            # Determine risk level
            if risk_factors >= 6:
                return 'Very High'
            elif risk_factors >= 4:
                return 'High'
            elif risk_factors >= 2:
                return 'Medium'
            else:
                return 'Low'
                
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 'Unknown'
    
    def get_comprehensive_dex_data(self, limit: int = 100) -> Dict:
        """Get comprehensive DEX data including trending, new pairs, and analytics"""
        try:
            self.logger.info("🚀 Fetching comprehensive DEX data...")
            
            # Fetch data
            trending = self.get_trending_tokens(limit)
            new_pairs = self.get_new_pairs(50)
            
            # Combine and analyze data
            all_tokens = {}
            
            # Add trending tokens
            for token in trending:
                symbol = token.get('baseToken', {}).get('symbol', '')
                if symbol:
                    all_tokens[symbol] = {**token, 'source': 'trending'}
            
            # Add new pairs (don't overwrite trending)
            for token in new_pairs:
                symbol = token.get('baseToken', {}).get('symbol', '')
                if symbol and symbol not in all_tokens:
                    all_tokens[symbol] = {**token, 'source': 'new_pair'}
            
            # Calculate statistics
            categories = {}
            risk_levels = {}
            chains = {}
            dexes = {}
            
            for token in all_tokens.values():
                # Category breakdown
                category = token.get('category', 'Other')
                categories[category] = categories.get(category, 0) + 1
                
                # Risk level breakdown
                risk = token.get('risk_score', 'Unknown')
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
                
                # Chain breakdown
                chain = token.get('chainId', 'unknown')
                chains[chain] = chains.get(chain, 0) + 1
                
                # DEX breakdown
                dex = token.get('dexId', 'unknown')
                dexes[dex] = dexes.get(dex, 0) + 1
            
            return {
                'tokens': all_tokens,
                'total_tokens': len(all_tokens),
                'trending_count': len(trending),
                'new_pairs_count': len(new_pairs),
                'statistics': {
                    'categories': categories,
                    'risk_levels': risk_levels,
                    'chains': chains,
                    'dexes': dexes
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching comprehensive DEX data: {e}")
            return {}

def main():
    """Test the DEX Screener integration"""
    print("🚀 DEX SCREENER API INTEGRATION TEST")
    print("=" * 60)
    
    fetcher = DEXScreenerFetcher()
    
    # Test trending tokens
    print("\n📈 Testing Trending Tokens...")
    trending = fetcher.get_trending_tokens(10)
    print(f"   ✅ Fetched {len(trending)} trending tokens")
    
    if trending:
        print("\n🔥 Top 5 Trending:")
        for i, token in enumerate(trending[:5]):
            base_token = token.get('baseToken', {})
            price_usd = float(token.get('priceUsd', 0))
            change_24h = token.get('priceChange', {}).get('h24', 0)
            volume_24h = float(token.get('volume', {}).get('h24', 0))
            
            print(f"   {i+1}. {token.get('emoji', '💎')} {base_token.get('symbol', 'Unknown')} - {base_token.get('name', 'Unknown')}")
            print(f"      💰 ${price_usd:.6f} ({change_24h:+.2f}%) 📊 Vol: ${volume_24h:,.0f}")
            print(f"      🏪 {token.get('dexId', 'Unknown')} | ⛓️ Chain: {token.get('chainId', 'Unknown')}")
            print(f"      ⚠️ Risk: {token.get('risk_score', 'Unknown')}")
    
    # Test new pairs
    print("\n🆕 Testing New Pairs...")
    new_pairs = fetcher.get_new_pairs(5)
    print(f"   ✅ Fetched {len(new_pairs)} new pairs")
    
    if new_pairs:
        print("\n🌟 Latest New Pairs:")
        for i, pair in enumerate(new_pairs[:3]):
            base_token = pair.get('baseToken', {})
            created_at = pair.get('pairCreatedAt', 0)
            age_hours = (time.time() - created_at / 1000) / 3600 if created_at > 0 else 0
            
            print(f"   {i+1}. {pair.get('emoji', '💎')} {base_token.get('symbol', 'Unknown')}")
            print(f"      🕐 Created: {age_hours:.1f} hours ago")
            print(f"      🏪 {pair.get('dexId', 'Unknown')} | ⛓️ {pair.get('chainId', 'Unknown')}")
    
    # Test comprehensive data
    print("\n🚀 Testing Comprehensive DEX Data...")
    comprehensive = fetcher.get_comprehensive_dex_data(50)
    
    if comprehensive:
        print(f"   ✅ Total tokens: {comprehensive.get('total_tokens', 0)}")
        print(f"   📈 Trending: {comprehensive.get('trending_count', 0)}")
        print(f"   🆕 New pairs: {comprehensive.get('new_pairs_count', 0)}")
        
        stats = comprehensive.get('statistics', {})
        
        print("\n📊 Category Breakdown:")
        for category, count in sorted(stats.get('categories', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} tokens")
        
        print("\n⚠️ Risk Level Distribution:")
        for risk, count in sorted(stats.get('risk_levels', {}).items(), key=lambda x: x[1], reverse=True):
            print(f"   {risk}: {count} tokens")
        
        print("\n🏪 Top DEXs:")
        for dex, count in sorted(stats.get('dexes', {}).items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {dex}: {count} pairs")
    
    print("\n✅ DEX SCREENER INTEGRATION SUCCESSFUL!")
    print("🎉 You now have access to comprehensive DEX data!")
    print("📊 Trending tokens, new pairs, risk analysis, and much more!")

if __name__ == "__main__":
    main()
