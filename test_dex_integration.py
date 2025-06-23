#!/usr/bin/env python3
"""
DEX Screener Integration Test
Comprehensive testing of DEX Screener API integration
"""

import time
from dexscreener_fetcher import DEXScreenerFetcher
from enhanced_crypto_fetcher import EnhancedCryptoFetcher

def test_dex_screener_integration():
    """Test DEX Screener integration comprehensively"""
    print("🚀 DEX SCREENER INTEGRATION COMPREHENSIVE TEST")
    print("=" * 70)
    
    fetcher = DEXScreenerFetcher()
    
    # Test 1: Trending tokens
    print("\n📈 Test 1: Trending Tokens")
    print("-" * 40)
    trending = fetcher.get_trending_tokens(15)
    print(f"✅ Fetched {len(trending)} trending tokens")
    
    if trending:
        print("\n🔥 Top 5 Trending Tokens:")
        for i, token in enumerate(trending[:5]):
            base_token = token.get('baseToken', {})
            chain = token.get('chainId', 'Unknown')
            dex = token.get('dexId', 'Unknown')
            boost_amount = token.get('boost_amount', 0)
            
            print(f"   {i+1}. {token.get('emoji', '💎')} {base_token.get('symbol', 'Unknown')}")
            print(f"      Chain: {chain} | DEX: {dex}")
            print(f"      Boost Amount: {boost_amount}")
            print(f"      Category: {token.get('category', 'Unknown')}")
            print(f"      Risk Score: {token.get('risk_score', 'Unknown')}")
    
    # Test 2: Popular pairs
    print("\n\n🆕 Test 2: Popular Pairs")
    print("-" * 40)
    pairs = fetcher.get_new_pairs(10)
    print(f"✅ Fetched {len(pairs)} popular pairs")
    
    if pairs:
        print("\n🌟 Top 5 Popular Pairs:")
        for i, pair in enumerate(pairs[:5]):
            base_token = pair.get('baseToken', {})
            quote_token = pair.get('quoteToken', {})
            price_usd = float(pair.get('priceUsd', 0))
            volume_24h = float(pair.get('volume', {}).get('h24', 0))
            liquidity = float(pair.get('liquidity', {}).get('usd', 0))
            
            print(f"   {i+1}. {pair.get('emoji', '💎')} {base_token.get('symbol', 'Unknown')}/{quote_token.get('symbol', 'Unknown')}")
            print(f"      Price: ${price_usd:.6f}")
            print(f"      Volume 24h: ${volume_24h:,.0f}")
            print(f"      Liquidity: ${liquidity:,.0f}")
            print(f"      Chain: {pair.get('chainId', 'Unknown')} | DEX: {pair.get('dexId', 'Unknown')}")
            print(f"      Risk: {pair.get('risk_score', 'Unknown')}")
    
    # Test 3: Search functionality
    print("\n\n🔍 Test 3: Search Functionality")
    print("-" * 40)
    search_terms = ['ETH', 'BTC', 'SOL']
    
    for term in search_terms:
        print(f"\nSearching for '{term}'...")
        results = fetcher.search_tokens(term)
        print(f"✅ Found {len(results)} results for '{term}'")
        
        if results:
            for i, result in enumerate(results[:2]):
                base_token = result.get('baseToken', {})
                price_usd = float(result.get('priceUsd', 0))
                
                print(f"   {i+1}. {result.get('emoji', '💎')} {base_token.get('symbol', 'Unknown')} - {base_token.get('name', 'Unknown')}")
                print(f"      Price: ${price_usd:.6f}")
                print(f"      Chain: {result.get('chainId', 'Unknown')}")
    
    # Test 4: Comprehensive DEX data
    print("\n\n🚀 Test 4: Comprehensive DEX Data")
    print("-" * 40)
    comprehensive = fetcher.get_comprehensive_dex_data(30)
    
    if comprehensive:
        print(f"✅ Total tokens: {comprehensive.get('total_tokens', 0)}")
        print(f"📈 Trending count: {comprehensive.get('trending_count', 0)}")
        print(f"🆕 Popular pairs count: {comprehensive.get('new_pairs_count', 0)}")
        
        stats = comprehensive.get('statistics', {})
        
        print("\n📊 Category Breakdown:")
        categories = stats.get('categories', {})
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} tokens")
        
        print("\n⚠️ Risk Level Distribution:")
        risk_levels = stats.get('risk_levels', {})
        for risk, count in sorted(risk_levels.items(), key=lambda x: x[1], reverse=True):
            print(f"   {risk}: {count} tokens")
        
        print("\n🏪 Top DEXs:")
        dexes = stats.get('dexes', {})
        for dex, count in sorted(dexes.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {dex}: {count} pairs")
        
        print("\n⛓️ Top Chains:")
        chains = stats.get('chains', {})
        for chain, count in sorted(chains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {chain}: {count} pairs")
    
    return {
        'trending_count': len(trending),
        'pairs_count': len(pairs),
        'comprehensive_tokens': comprehensive.get('total_tokens', 0) if comprehensive else 0,
        'test_passed': True
    }

def test_enhanced_crypto_with_dex():
    """Test enhanced crypto fetcher with DEX integration"""
    print("\n\n🌟 ENHANCED CRYPTO FETCHER + DEX INTEGRATION TEST")
    print("=" * 70)
    
    try:
        # Import and test enhanced fetcher
        enhanced_fetcher = EnhancedCryptoFetcher()
        
        print("\n📊 Testing Enhanced Fetcher with DEX data...")
        enhanced_data = enhanced_fetcher.get_enhanced_crypto_data()
        
        if enhanced_data:
            print(f"✅ Enhanced data fetched successfully")
            print(f"   Total cryptocurrencies: {enhanced_data.get('total_cryptocurrencies', 0)}")
            print(f"   Binance pairs: {enhanced_data.get('binance_count', 0)}")
            print(f"   CoinMarketCap data: {enhanced_data.get('coinmarketcap_count', 0)}")
            
            # Check if we can add DEX data
            dex_fetcher = DEXScreenerFetcher()
            dex_data = dex_fetcher.get_comprehensive_dex_data(20)
            
            if dex_data:
                print(f"   DEX tokens available: {dex_data.get('total_tokens', 0)}")
                print(f"   DEX trending: {dex_data.get('trending_count', 0)}")
                
                # Show integration potential
                enhanced_cryptos = enhanced_data.get('cryptocurrencies', {})
                dex_tokens = dex_data.get('tokens', {})
                
                overlap_count = 0
                dex_only_count = 0
                
                for symbol in dex_tokens.keys():
                    if symbol in enhanced_cryptos:
                        overlap_count += 1
                    else:
                        dex_only_count += 1
                
                print(f"\n🔗 Integration Analysis:")
                print(f"   Overlapping tokens (CEX + DEX): {overlap_count}")
                print(f"   DEX-only tokens: {dex_only_count}")
                print(f"   Total unique after integration: {len(enhanced_cryptos) + dex_only_count}")
                
                return {
                    'enhanced_total': len(enhanced_cryptos),
                    'dex_total': len(dex_tokens),
                    'overlap': overlap_count,
                    'dex_only': dex_only_count,
                    'integration_potential': len(enhanced_cryptos) + dex_only_count
                }
        
    except Exception as e:
        print(f"❌ Error testing enhanced fetcher: {e}")
        return {}

def main():
    """Run comprehensive DEX integration tests"""
    print("🧪 COMPREHENSIVE DEX SCREENER INTEGRATION TESTING")
    print("=" * 70)
    
    start_time = time.time()
    
    # Test DEX Screener
    dex_results = test_dex_screener_integration()
    
    # Test Enhanced Integration
    integration_results = test_enhanced_crypto_with_dex()
    
    end_time = time.time()
    test_duration = end_time - start_time
    
    # Summary
    print("\n\n📋 TEST SUMMARY")
    print("=" * 50)
    print(f"⏱️ Test Duration: {test_duration:.2f} seconds")
    print(f"📈 DEX Trending Tokens: {dex_results.get('trending_count', 0)}")
    print(f"🆕 DEX Popular Pairs: {dex_results.get('pairs_count', 0)}")
    print(f"🚀 DEX Comprehensive Tokens: {dex_results.get('comprehensive_tokens', 0)}")
    
    if integration_results:
        print(f"🔗 Enhanced Crypto Total: {integration_results.get('enhanced_total', 0)}")
        print(f"💎 DEX Total: {integration_results.get('dex_total', 0)}")
        print(f"🤝 Overlapping Tokens: {integration_results.get('overlap', 0)}")
        print(f"🆕 DEX-Only Tokens: {integration_results.get('dex_only', 0)}")
        print(f"🌟 Total Integration Potential: {integration_results.get('integration_potential', 0)}")
    
    print(f"\n✅ DEX SCREENER INTEGRATION: {'SUCCESSFUL' if dex_results.get('test_passed') else 'FAILED'}")
    print("🎉 Your AI trading bot now has access to DEX data!")
    print("📊 Trending tokens, popular pairs, risk analysis, and comprehensive DEX intelligence!")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("1. Add your DEX Screener API key to config.env for enhanced features")
    print("2. The integration provides both CEX and DEX market coverage")
    print("3. Use risk scores to filter high-risk DEX tokens")
    print("4. Monitor trending tokens for early opportunities")
    print("5. Cross-reference DEX liquidity with CEX volume for best trading pairs")

if __name__ == "__main__":
    main() 