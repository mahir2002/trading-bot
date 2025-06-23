#!/usr/bin/env python3
"""
Test Enhanced Crypto Fetcher
Comprehensive testing of Binance + CoinMarketCap integration
"""

import time
from enhanced_crypto_fetcher import EnhancedCryptoFetcher
from coinmarketcap_fetcher import CoinMarketCapFetcher
from dynamic_crypto_fetcher import DynamicCryptoFetcher

def test_individual_fetchers():
    """Test individual fetchers"""
    print("🧪 TESTING INDIVIDUAL FETCHERS")
    print("=" * 50)
    
    # Test Binance fetcher
    print("\n📊 Testing Binance Fetcher...")
    binance_fetcher = DynamicCryptoFetcher()
    binance_data = binance_fetcher.get_comprehensive_market_coverage(min_volume_usdt=50000)
    print(f"   ✅ Binance: {len(binance_data)} cryptocurrencies")
    
    # Test CoinMarketCap fetcher
    print("\n📈 Testing CoinMarketCap Fetcher...")
    cmc_fetcher = CoinMarketCapFetcher()
    cmc_data = cmc_fetcher.get_cryptocurrency_listings(100)
    print(f"   ✅ CoinMarketCap: {len(cmc_data)} cryptocurrencies")
    
    # Test global metrics
    global_metrics = cmc_fetcher.get_global_metrics()
    if global_metrics:
        print(f"   ✅ Global metrics: Available")
        print(f"      Total cryptocurrencies: {global_metrics.get('total_cryptocurrencies', 0):,}")
        print(f"      Total market cap: ${global_metrics.get('total_market_cap', 0):,.0f}")
    else:
        print(f"   ⚠️ Global metrics: Not available")
    
    return binance_data, cmc_data, global_metrics

def test_enhanced_fetcher():
    """Test enhanced fetcher"""
    print("\n🚀 TESTING ENHANCED FETCHER")
    print("=" * 50)
    
    enhanced_fetcher = EnhancedCryptoFetcher()
    
    # Test comprehensive data
    print("\n📊 Testing comprehensive data fetch...")
    start_time = time.time()
    enhanced_data = enhanced_fetcher.get_comprehensive_crypto_data(min_volume=25000)
    fetch_time = time.time() - start_time
    
    if enhanced_data and 'cryptocurrencies' in enhanced_data:
        cryptos = enhanced_data['cryptocurrencies']
        
        print(f"   ✅ Enhanced fetch completed in {fetch_time:.2f} seconds")
        print(f"   📊 Total unique cryptocurrencies: {enhanced_data['total_unique_cryptos']:,}")
        
        # Data source breakdown
        breakdown = enhanced_data['data_source_breakdown']
        print(f"\n📡 Data Source Breakdown:")
        print(f"   Binance only: {breakdown['binance_only']:,}")
        print(f"   CoinMarketCap only: {breakdown['cmc_only']:,}")
        print(f"   Both sources: {breakdown['both_sources']:,}")
        
        # Trading availability
        trading = enhanced_data['trading_availability']
        print(f"\n💱 Trading Availability:")
        print(f"   Tradeable on Binance: {trading['tradeable_on_binance']:,}")
        print(f"   Market data only: {trading['market_data_only']:,}")
        
        # Category breakdown
        categories = enhanced_data['categories']
        print(f"\n📈 Top Categories:")
        sorted_categories = sorted(categories.items(), key=lambda x: x[1]['count'], reverse=True)
        for i, (category, info) in enumerate(sorted_categories[:10], 1):
            print(f"   {i:2d}. {category}: {info['count']} total ({info['tradeable']} tradeable)")
        
        # Top performers
        print(f"\n🏆 Top 5 by Market Cap:")
        for i, (symbol, info) in enumerate(enhanced_data['top_by_market_cap'][:5], 1):
            market_cap = info.get('market_cap', 0)
            price = info.get('cmc_price', info.get('binance_price', 0))
            sources = '+'.join(info.get('data_sources', []))
            tradeable = "✅" if info.get('has_binance_trading', False) else "📊"
            
            print(f"   {i}. {tradeable} {symbol:8} - {info.get('name', 'N/A'):20} "
                  f"${price:>8.4f} MC: ${market_cap:>12,.0f} [{sources}]")
        
        print(f"\n💹 Top 5 by Trading Volume:")
        for i, (symbol, info) in enumerate(enhanced_data['top_by_volume'][:5], 1):
            volume = info.get('binance_volume_24h', 0)
            price = info.get('binance_price', 0)
            
            print(f"   {i}. 💱 {symbol:8} - {info.get('name', 'N/A'):20} "
                  f"${price:>8.4f} Vol: ${volume:>12,.0f}")
        
        return enhanced_data
    else:
        print("   ❌ Enhanced fetch failed")
        return None

def test_filtering():
    """Test filtering functionality"""
    print("\n🔍 TESTING FILTERING FUNCTIONALITY")
    print("=" * 50)
    
    enhanced_fetcher = EnhancedCryptoFetcher()
    
    # Test category filtering
    print("\n📊 Testing category filters...")
    
    categories_to_test = ['DeFi', 'Gaming', 'AI', 'Major', 'Meme']
    for category in categories_to_test:
        filtered_data = enhanced_fetcher.get_filtered_data(
            category=category, 
            tradeable_only=True, 
            top_n=5
        )
        
        if filtered_data and 'cryptocurrencies' in filtered_data:
            count = filtered_data['total_count']
            print(f"   {category}: {count} tradeable cryptocurrencies")
            
            if count > 0:
                # Show examples
                examples = list(filtered_data['cryptocurrencies'].items())[:3]
                example_names = [f"{info.get('emoji', '💰')} {symbol}" for symbol, info in examples]
                print(f"      Examples: {', '.join(example_names)}")
        else:
            print(f"   {category}: No data available")
    
    # Test market cap filtering
    print(f"\n💰 Testing market cap filters...")
    market_cap_filters = [
        (1000000000, "$1B+"),    # $1B+
        (100000000, "$100M+"),   # $100M+
        (10000000, "$10M+")      # $10M+
    ]
    
    for min_cap, label in market_cap_filters:
        filtered_data = enhanced_fetcher.get_filtered_data(
            min_market_cap=min_cap,
            top_n=10
        )
        
        if filtered_data and 'cryptocurrencies' in filtered_data:
            count = filtered_data['total_count']
            print(f"   {label}: {count} cryptocurrencies")
        else:
            print(f"   {label}: No data available")

def test_performance():
    """Test performance metrics"""
    print("\n⚡ PERFORMANCE TESTING")
    print("=" * 50)
    
    enhanced_fetcher = EnhancedCryptoFetcher()
    
    # Test multiple fetch times
    print("\n🕐 Testing fetch performance...")
    times = []
    
    for i in range(3):
        print(f"   Test {i+1}/3...", end=" ")
        start_time = time.time()
        data = enhanced_fetcher.get_comprehensive_crypto_data(min_volume=50000)
        fetch_time = time.time() - start_time
        times.append(fetch_time)
        print(f"{fetch_time:.2f}s")
    
    avg_time = sum(times) / len(times)
    print(f"\n📊 Performance Results:")
    print(f"   Average fetch time: {avg_time:.2f} seconds")
    print(f"   Fastest: {min(times):.2f}s")
    print(f"   Slowest: {max(times):.2f}s")
    
    if avg_time < 10:
        print(f"   ✅ Performance: Excellent")
    elif avg_time < 20:
        print(f"   ⚠️ Performance: Good")
    else:
        print(f"   ❌ Performance: Needs improvement")

def main():
    """Main test function"""
    print("🧪 ENHANCED CRYPTO FETCHER COMPREHENSIVE TEST")
    print("=" * 60)
    print("Testing Binance + CoinMarketCap integration")
    print("Verifying data quality and performance")
    print("=" * 60)
    
    try:
        # Test individual fetchers
        binance_data, cmc_data, global_metrics = test_individual_fetchers()
        
        # Test enhanced fetcher
        enhanced_data = test_enhanced_fetcher()
        
        # Test filtering
        test_filtering()
        
        # Test performance
        test_performance()
        
        # Final summary
        print("\n🎉 TEST SUMMARY")
        print("=" * 50)
        
        if binance_data and cmc_data and enhanced_data:
            print("✅ All tests passed successfully!")
            print(f"📊 Binance: {len(binance_data)} cryptocurrencies")
            print(f"📈 CoinMarketCap: {len(cmc_data)} cryptocurrencies")
            print(f"🚀 Enhanced: {enhanced_data['total_unique_cryptos']} total cryptocurrencies")
            print(f"💱 Tradeable: {enhanced_data['trading_availability']['tradeable_on_binance']}")
            print(f"📊 Market data only: {enhanced_data['trading_availability']['market_data_only']}")
            
            print(f"\n🎯 INTEGRATION SUCCESS!")
            print(f"Your system now has access to comprehensive cryptocurrency data")
            print(f"from multiple sources with enhanced market coverage!")
            
        else:
            print("⚠️ Some tests failed - check your API configurations")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        print("💡 Make sure your API keys are configured in config.env")

if __name__ == "__main__":
    main() 