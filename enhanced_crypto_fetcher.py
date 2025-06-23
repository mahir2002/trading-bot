#!/usr/bin/env python3
"""
Enhanced Crypto Fetcher
Combines Binance and CoinMarketCap data for maximum cryptocurrency coverage
Provides comprehensive market data with rankings, market caps, and trading pairs
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import concurrent.futures
from dynamic_crypto_fetcher import DynamicCryptoFetcher
from coinmarketcap_fetcher import CoinMarketCapFetcher

class EnhancedCryptoFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.binance_fetcher = DynamicCryptoFetcher()
        self.cmc_fetcher = CoinMarketCapFetcher()
        
    def get_comprehensive_crypto_data(self, min_volume: float = 10000) -> Dict:
        """
        Get comprehensive cryptocurrency data combining Binance and CoinMarketCap
        
        Args:
            min_volume: Minimum 24h volume filter for Binance pairs
            
        Returns:
            Dict containing combined data from both sources
        """
        try:
            self.logger.info("🚀 Fetching comprehensive cryptocurrency data from multiple sources...")
            
            # Fetch data from both sources concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks
                binance_future = executor.submit(self.binance_fetcher.get_comprehensive_market_coverage, min_volume_usdt=min_volume)
                cmc_future = executor.submit(self.cmc_fetcher.get_cryptocurrency_listings, 1000)
                
                # Get results
                binance_data = binance_future.result()
                cmc_data = cmc_future.result()
            
            # Get global metrics from CMC
            global_metrics = self.cmc_fetcher.get_global_metrics()
            
            # Merge and enhance the data
            enhanced_data = self._merge_data_sources(binance_data, cmc_data, global_metrics)
            
            self.logger.info(f"✅ Enhanced crypto data ready: {enhanced_data['total_unique_cryptos']} unique cryptocurrencies")
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Error fetching comprehensive data: {e}")
            return {}
    
    def _merge_data_sources(self, binance_data: Dict, cmc_data: Dict, global_metrics: Dict) -> Dict:
        """
        Merge data from Binance and CoinMarketCap sources
        
        Args:
            binance_data: Data from Binance API
            cmc_data: Data from CoinMarketCap API
            global_metrics: Global market metrics from CMC
            
        Returns:
            Enhanced merged dataset
        """
        try:
            enhanced_cryptos = {}
            
            # Start with Binance data (trading pairs with volume data)
            for symbol, binance_info in binance_data.items():
                enhanced_cryptos[symbol] = {
                    **binance_info,
                    'data_sources': ['binance'],
                    'has_binance_trading': True,
                    'binance_volume_24h': binance_info.get('volume', 0),
                    'binance_price': binance_info.get('price', 0),
                    'binance_change_24h': binance_info.get('priceChangePercent', 0)
                }
            
            # Enhance with CoinMarketCap data
            for symbol, cmc_info in cmc_data.items():
                if symbol in enhanced_cryptos:
                    # Merge data for existing symbols
                    enhanced_cryptos[symbol].update({
                        'cmc_rank': cmc_info.get('rank', 0),
                        'market_cap': cmc_info.get('market_cap', 0),
                        'market_cap_dominance': cmc_info.get('market_cap_dominance', 0),
                        'fully_diluted_market_cap': cmc_info.get('fully_diluted_market_cap', 0),
                        'circulating_supply': cmc_info.get('circulating_supply', 0),
                        'total_supply': cmc_info.get('total_supply', 0),
                        'max_supply': cmc_info.get('max_supply', 0),
                        'cmc_price': cmc_info.get('price', 0),
                        'cmc_volume_24h': cmc_info.get('volume_24h', 0),
                        'cmc_change_1h': cmc_info.get('percent_change_1h', 0),
                        'cmc_change_24h': cmc_info.get('percent_change_24h', 0),
                        'cmc_change_7d': cmc_info.get('percent_change_7d', 0),
                        'cmc_change_30d': cmc_info.get('percent_change_30d', 0),
                        'tags': cmc_info.get('tags', []),
                        'platform': cmc_info.get('platform', {}),
                        'date_added': cmc_info.get('date_added', ''),
                        'data_sources': enhanced_cryptos[symbol]['data_sources'] + ['coinmarketcap']
                    })
                    
                    # Use CMC category if available, otherwise keep Binance category
                    if cmc_info.get('category') and cmc_info['category'] != 'Other':
                        enhanced_cryptos[symbol]['category'] = cmc_info['category']
                        
                else:
                    # Add new symbols from CoinMarketCap (not available on Binance)
                    enhanced_cryptos[symbol] = {
                        **cmc_info,
                        'data_sources': ['coinmarketcap'],
                        'has_binance_trading': False,
                        'binance_volume_24h': 0,
                        'binance_price': 0,
                        'binance_change_24h': 0,
                        'cmc_rank': cmc_info.get('rank', 0),
                        'market_cap': cmc_info.get('market_cap', 0),
                        'cmc_price': cmc_info.get('price', 0),
                        'cmc_volume_24h': cmc_info.get('volume_24h', 0),
                        'cmc_change_24h': cmc_info.get('percent_change_24h', 0)
                    }
            
            # Calculate enhanced metrics
            binance_only = sum(1 for crypto in enhanced_cryptos.values() if crypto.get('data_sources', []) == ['binance'])
            cmc_only = sum(1 for crypto in enhanced_cryptos.values() if crypto.get('data_sources', []) == ['coinmarketcap'])
            both_sources = sum(1 for crypto in enhanced_cryptos.values() if len(crypto.get('data_sources', [])) == 2)
            
            # Categorize by data availability
            trading_available = {symbol: info for symbol, info in enhanced_cryptos.items() if info['has_binance_trading']}
            market_data_only = {symbol: info for symbol, info in enhanced_cryptos.items() if not info['has_binance_trading']}
            
            # Get top performers
            top_by_market_cap = sorted(
                [(symbol, info) for symbol, info in enhanced_cryptos.items() if info.get('market_cap', 0) > 0],
                key=lambda x: x[1]['market_cap'],
                reverse=True
            )[:50]
            
            top_by_volume = sorted(
                [(symbol, info) for symbol, info in enhanced_cryptos.items() if info.get('binance_volume_24h', 0) > 0],
                key=lambda x: x[1]['binance_volume_24h'],
                reverse=True
            )[:50]
            
            return {
                'cryptocurrencies': enhanced_cryptos,
                'total_unique_cryptos': len(enhanced_cryptos),
                'data_source_breakdown': {
                    'binance_only': binance_only,
                    'cmc_only': cmc_only,
                    'both_sources': both_sources
                },
                'trading_availability': {
                    'tradeable_on_binance': len(trading_available),
                    'market_data_only': len(market_data_only)
                },
                'top_by_market_cap': top_by_market_cap,
                'top_by_volume': top_by_volume,
                'global_metrics': global_metrics,
                'last_updated': datetime.now().isoformat(),
                'categories': self._get_category_breakdown(enhanced_cryptos)
            }
            
        except Exception as e:
            self.logger.error(f"Error merging data sources: {e}")
            return {}
    
    def _get_category_breakdown(self, cryptos: Dict) -> Dict:
        """Get breakdown of cryptocurrencies by category"""
        categories = {}
        for symbol, info in cryptos.items():
            category = info.get('category', 'Other')
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'tradeable': 0,
                    'market_data_only': 0,
                    'examples': []
                }
            
            categories[category]['count'] += 1
            if info.get('has_binance_trading', False):
                categories[category]['tradeable'] += 1
            else:
                categories[category]['market_data_only'] += 1
                
            if len(categories[category]['examples']) < 5:
                categories[category]['examples'].append({
                    'symbol': symbol,
                    'name': info.get('name', symbol),
                    'emoji': info.get('emoji', '💰')
                })
        
        return categories
    
    def get_filtered_data(self, 
                         category: Optional[str] = None,
                         min_market_cap: float = 0,
                         min_volume: float = 0,
                         tradeable_only: bool = False,
                         top_n: Optional[int] = None) -> Dict:
        """
        Get filtered cryptocurrency data based on various criteria
        
        Args:
            category: Filter by category (e.g., 'DeFi', 'Gaming', 'AI')
            min_market_cap: Minimum market cap filter
            min_volume: Minimum 24h volume filter
            tradeable_only: Only include cryptocurrencies tradeable on Binance
            top_n: Limit to top N results by market cap
            
        Returns:
            Filtered cryptocurrency data
        """
        try:
            # Get comprehensive data first
            all_data = self.get_comprehensive_crypto_data()
            
            if not all_data or 'cryptocurrencies' not in all_data:
                return {}
            
            cryptos = all_data['cryptocurrencies']
            filtered_cryptos = {}
            
            for symbol, info in cryptos.items():
                # Apply filters
                if category and info.get('category') != category:
                    continue
                    
                if min_market_cap > 0 and info.get('market_cap', 0) < min_market_cap:
                    continue
                    
                if min_volume > 0:
                    volume = max(info.get('binance_volume_24h', 0), info.get('cmc_volume_24h', 0))
                    if volume < min_volume:
                        continue
                
                if tradeable_only and not info.get('has_binance_trading', False):
                    continue
                
                filtered_cryptos[symbol] = info
            
            # Sort by market cap and limit if requested
            if top_n:
                sorted_items = sorted(
                    filtered_cryptos.items(),
                    key=lambda x: x[1].get('market_cap', 0),
                    reverse=True
                )[:top_n]
                filtered_cryptos = dict(sorted_items)
            
            return {
                'cryptocurrencies': filtered_cryptos,
                'total_count': len(filtered_cryptos),
                'filters_applied': {
                    'category': category,
                    'min_market_cap': min_market_cap,
                    'min_volume': min_volume,
                    'tradeable_only': tradeable_only,
                    'top_n': top_n
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error filtering data: {e}")
            return {}

def main():
    """Test the enhanced crypto fetcher"""
    fetcher = EnhancedCryptoFetcher()
    
    print("🚀 ENHANCED CRYPTO FETCHER TEST")
    print("=" * 60)
    print("Combining Binance + CoinMarketCap data for maximum coverage!")
    print()
    
    # Test comprehensive data
    data = fetcher.get_comprehensive_crypto_data(min_volume=25000)
    
    if data and 'cryptocurrencies' in data:
        print(f"📊 COMPREHENSIVE CRYPTOCURRENCY DATA")
        print(f"   Total Unique Cryptocurrencies: {data['total_unique_cryptos']:,}")
        print()
        
        # Data source breakdown
        breakdown = data['data_source_breakdown']
        print(f"📡 Data Source Breakdown:")
        print(f"   Binance Only: {breakdown['binance_only']:,} coins")
        print(f"   CoinMarketCap Only: {breakdown['cmc_only']:,} coins")
        print(f"   Both Sources: {breakdown['both_sources']:,} coins")
        print()
        
        # Trading availability
        trading = data['trading_availability']
        print(f"💱 Trading Availability:")
        print(f"   Tradeable on Binance: {trading['tradeable_on_binance']:,} coins")
        print(f"   Market Data Only: {trading['market_data_only']:,} coins")
        print()
        
        # Category breakdown
        categories = data['categories']
        print(f"📈 Category Breakdown:")
        for category, info in sorted(categories.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"   {category}: {info['count']} total ({info['tradeable']} tradeable)")
            if info['examples']:
                examples = [f"{ex['emoji']} {ex['symbol']}" for ex in info['examples'][:3]]
                print(f"      Examples: {', '.join(examples)}")
        print()
        
        # Top performers
        print(f"🏆 Top 10 by Market Cap:")
        for i, (symbol, info) in enumerate(data['top_by_market_cap'][:10], 1):
            market_cap = info.get('market_cap', 0)
            price = info.get('cmc_price', info.get('binance_price', 0))
            change_24h = info.get('cmc_change_24h', info.get('binance_change_24h', 0))
            sources = '+'.join(info['data_sources'])
            tradeable = "✅" if info['has_binance_trading'] else "📊"
            
            print(f"   {i:2d}. {tradeable} {symbol:8} - {info.get('name', 'N/A'):20} "
                  f"${price:>10.4f} ({change_24h:+6.2f}%) MC: ${market_cap:>15,.0f} [{sources}]")
        
        print(f"\n💹 Top 10 by Trading Volume:")
        for i, (symbol, info) in enumerate(data['top_by_volume'][:10], 1):
            volume = info.get('binance_volume_24h', 0)
            price = info.get('binance_price', 0)
            change_24h = info.get('binance_change_24h', 0)
            
            print(f"   {i:2d}. 💱 {symbol:8} - {info.get('name', 'N/A'):20} "
                  f"${price:>10.4f} ({change_24h:+6.2f}%) Vol: ${volume:>15,.0f}")
        
        # Global metrics
        if 'global_metrics' in data and data['global_metrics']:
            global_data = data['global_metrics']
            print(f"\n🌍 Global Market Metrics:")
            print(f"   Total Cryptocurrencies: {global_data.get('total_cryptocurrencies', 0):,}")
            print(f"   Total Market Cap: ${global_data.get('total_market_cap', 0):,.0f}")
            print(f"   24h Volume: ${global_data.get('total_volume_24h', 0):,.0f}")
            print(f"   BTC Dominance: {global_data.get('btc_dominance', 0):.2f}%")
            print(f"   ETH Dominance: {global_data.get('eth_dominance', 0):.2f}%")
        
        print(f"\n✅ ENHANCED CRYPTO FETCHER SUCCESS!")
        print(f"🎉 Maximum cryptocurrency coverage achieved!")
        print(f"📊 {data['total_unique_cryptos']:,} cryptocurrencies with comprehensive data!")
        
        # Test filtering
        print(f"\n🔍 Testing Filters...")
        
        # Test DeFi filter
        defi_data = fetcher.get_filtered_data(category='DeFi', tradeable_only=True, top_n=5)
        if defi_data and 'cryptocurrencies' in defi_data:
            print(f"   DeFi (Tradeable): {defi_data['total_count']} coins")
            
        # Test high market cap filter
        large_cap = fetcher.get_filtered_data(min_market_cap=1000000000, top_n=10)  # $1B+
        if large_cap and 'cryptocurrencies' in large_cap:
            print(f"   Large Cap ($1B+): {large_cap['total_count']} coins")
        
    else:
        print("❌ Failed to fetch enhanced data")
        print("💡 Check your API configurations")

if __name__ == "__main__":
    main() 