#!/usr/bin/env python3
"""
Integration Test for Coin Listings with Unified Master Trading Bot
Tests the integration of CEX and DEX coin listing modules with the main trading bot
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add paths
sys.path.append('.')
sys.path.append('unified_trading_platform')

from modules.coin_listings_cex import CEXCoinListingsModule
from modules.coin_listings_dex import DEXCoinListingsModule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration_test.log')
    ]
)
logger = logging.getLogger(__name__)

class CoinListingsIntegrationTest:
    """Integration test for coin listings modules"""
    
    def __init__(self):
        logger.info("🧪 Initializing Coin Listings Integration Test...")
        
        # CEX Configuration
        self.cex_config = {
            'enabled_exchanges': ['binance', 'coinbasepro', 'kraken'],
            'cache_duration_hours': 24,
            'update_interval_hours': 24,
            'enable_testnet': False,
            'include_delisted': False,
            'symbol_types': ['spot', 'margin'],
            'cache_dir': 'data/test_coin_listings'
        }
        
        # DEX Configuration
        self.dex_config = {
            'enabled_networks': ['ethereum', 'bsc'],
            'enabled_dexes': ['uniswap-v2', 'uniswap-v3', 'pancakeswap'],
            'cache_duration_hours': 24,
            'update_interval_hours': 24,
            'min_liquidity_usd': 5000,
            'min_volume_24h_usd': 500,
            'max_tokens_per_dex': 100,
            'cache_dir': 'data/test_coin_listings'
        }
        
        # Initialize modules
        self.cex_listings = None
        self.dex_listings = None
        
        # Test data
        self.test_results = {
            'cex_tests': {},
            'dex_tests': {},
            'integration_tests': {}
        }
    
    async def setup_modules(self):
        """Setup coin listing modules"""
        try:
            logger.info("🔧 Setting up coin listing modules...")
            
            # Initialize CEX module
            self.cex_listings = CEXCoinListingsModule('test_cex', self.cex_config)
            logger.info("✅ CEX module initialized")
            
            # Initialize DEX module
            self.dex_listings = DEXCoinListingsModule('test_dex', self.dex_config)
            logger.info("✅ DEX module initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Module setup failed: {e}")
            return False
    
    async def test_cex_functionality(self):
        """Test CEX listing functionality"""
        logger.info("🧪 Testing CEX functionality...")
        
        try:
            # Test 1: Get all listings
            logger.info("   📋 Test 1: Getting all CEX listings...")
            listings_result = await self.cex_listings.handle_get_listings({})
            
            if listings_result and 'exchanges' in listings_result:
                exchange_count = len(listings_result['exchanges'])
                total_symbols = sum(len(data['symbols']) for data in listings_result['exchanges'].values())
                
                self.test_results['cex_tests']['get_listings'] = {
                    'status': 'PASS',
                    'exchanges': exchange_count,
                    'total_symbols': total_symbols
                }
                logger.info(f"   ✅ Found {total_symbols} symbols across {exchange_count} exchanges")
            else:
                self.test_results['cex_tests']['get_listings'] = {'status': 'FAIL', 'error': 'No data returned'}
                logger.warning("   ⚠️ No CEX listings data returned")
            
            # Test 2: Search for USDT pairs
            logger.info("   🔍 Test 2: Searching for USDT pairs...")
            search_result = await self.cex_listings.handle_search_symbols({
                'query': 'USDT',
                'exchange': 'binance',
                'limit': 20
            })
            
            if search_result and 'symbols' in search_result:
                usdt_count = len(search_result['symbols'])
                self.test_results['cex_tests']['search_usdt'] = {
                    'status': 'PASS',
                    'found_symbols': usdt_count
                }
                logger.info(f"   ✅ Found {usdt_count} USDT pairs")
                
                # Show some examples
                examples = [s['symbol'] for s in search_result['symbols'][:5]]
                logger.info(f"   📊 Examples: {', '.join(examples)}")
            else:
                self.test_results['cex_tests']['search_usdt'] = {'status': 'FAIL', 'error': 'No symbols found'}
                logger.warning("   ⚠️ No USDT pairs found")
            
            # Test 3: Get statistics
            logger.info("   📊 Test 3: Getting CEX statistics...")
            stats_result = await self.cex_listings.handle_get_statistics({})
            
            if stats_result:
                self.test_results['cex_tests']['statistics'] = {
                    'status': 'PASS',
                    'stats': stats_result
                }
                logger.info(f"   ✅ CEX Statistics: {stats_result}")
            else:
                self.test_results['cex_tests']['statistics'] = {'status': 'FAIL'}
                logger.warning("   ⚠️ No CEX statistics returned")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ CEX functionality test failed: {e}")
            self.test_results['cex_tests']['error'] = str(e)
            return False
    
    async def test_dex_functionality(self):
        """Test DEX listing functionality"""
        logger.info("🧪 Testing DEX functionality...")
        
        try:
            # Test 1: Get all DEX listings
            logger.info("   📋 Test 1: Getting all DEX listings...")
            listings_result = await self.dex_listings.handle_get_listings({})
            
            if listings_result and 'networks' in listings_result:
                network_count = len(listings_result['networks'])
                total_tokens = sum(
                    sum(len(dex_data['tokens']) for dex_data in network_data['dexes'].values())
                    for network_data in listings_result['networks'].values()
                )
                
                self.test_results['dex_tests']['get_listings'] = {
                    'status': 'PASS',
                    'networks': network_count,
                    'total_tokens': total_tokens
                }
                logger.info(f"   ✅ Found {total_tokens} tokens across {network_count} networks")
            else:
                self.test_results['dex_tests']['get_listings'] = {'status': 'FAIL', 'error': 'No data returned'}
                logger.warning("   ⚠️ No DEX listings data returned")
            
            # Test 2: Search tokens by network
            logger.info("   🔍 Test 2: Searching Ethereum tokens...")
            search_result = await self.dex_listings.handle_search_tokens({
                'network': 'ethereum',
                'min_liquidity_usd': 10000,
                'limit': 10
            })
            
            if search_result and 'tokens' in search_result:
                token_count = len(search_result['tokens'])
                self.test_results['dex_tests']['search_tokens'] = {
                    'status': 'PASS',
                    'found_tokens': token_count
                }
                logger.info(f"   ✅ Found {token_count} high-liquidity Ethereum tokens")
                
                # Show some examples
                examples = [t['symbol'] for t in search_result['tokens'][:5]]
                logger.info(f"   📊 Examples: {', '.join(examples)}")
            else:
                self.test_results['dex_tests']['search_tokens'] = {'status': 'FAIL', 'error': 'No tokens found'}
                logger.warning("   ⚠️ No high-liquidity tokens found")
            
            # Test 3: Get statistics
            logger.info("   📊 Test 3: Getting DEX statistics...")
            stats_result = await self.dex_listings.handle_get_statistics({})
            
            if stats_result:
                self.test_results['dex_tests']['statistics'] = {
                    'status': 'PASS',
                    'stats': stats_result
                }
                logger.info(f"   ✅ DEX Statistics: {stats_result}")
            else:
                self.test_results['dex_tests']['statistics'] = {'status': 'FAIL'}
                logger.warning("   ⚠️ No DEX statistics returned")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ DEX functionality test failed: {e}")
            self.test_results['dex_tests']['error'] = str(e)
            return False
    
    async def test_trading_pair_generation(self):
        """Test generating trading pairs for the unified bot"""
        logger.info("🧪 Testing trading pair generation...")
        
        try:
            # Get top CEX symbols
            cex_symbols = []
            if self.cex_listings:
                binance_symbols = await self.cex_listings.handle_search_symbols({
                    'query': 'USDT',
                    'exchange': 'binance',
                    'limit': 30
                })
                if binance_symbols and 'symbols' in binance_symbols:
                    cex_symbols = [s['symbol'] for s in binance_symbols['symbols']]
            
            # Get top DEX tokens
            dex_symbols = []
            if self.dex_listings:
                for network in ['ethereum', 'bsc']:
                    network_tokens = await self.dex_listings.handle_search_tokens({
                        'network': network,
                        'min_liquidity_usd': 20000,
                        'limit': 10
                    })
                    if network_tokens and 'tokens' in network_tokens:
                        for token in network_tokens['tokens']:
                            symbol = f"{token['symbol']}/USDT"
                            if symbol not in dex_symbols:
                                dex_symbols.append(symbol)
            
            # Generate unified trading pairs
            major_pairs = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'
            ]
            
            unified_pairs = major_pairs.copy()
            
            # Add CEX pairs
            for symbol in cex_symbols[:15]:
                if symbol not in unified_pairs and symbol.endswith('/USDT'):
                    unified_pairs.append(symbol)
            
            # Add DEX pairs
            for symbol in dex_symbols[:10]:
                if symbol not in unified_pairs:
                    unified_pairs.append(symbol)
            
            # Limit to 40 pairs
            unified_pairs = unified_pairs[:40]
            
            self.test_results['integration_tests']['trading_pairs'] = {
                'status': 'PASS',
                'cex_symbols': len(cex_symbols),
                'dex_symbols': len(dex_symbols),
                'unified_pairs': len(unified_pairs),
                'pairs': unified_pairs
            }
            
            logger.info(f"   ✅ Generated {len(unified_pairs)} unified trading pairs")
            logger.info(f"   📊 CEX sources: {len(cex_symbols)}, DEX sources: {len(dex_symbols)}")
            logger.info(f"   🎯 Top 10 pairs: {', '.join(unified_pairs[:10])}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Trading pair generation test failed: {e}")
            self.test_results['integration_tests']['trading_pairs'] = {'status': 'FAIL', 'error': str(e)}
            return False
    
    async def test_cache_performance(self):
        """Test caching performance"""
        logger.info("🧪 Testing cache performance...")
        
        try:
            # Test CEX caching
            start_time = datetime.now()
            await self.cex_listings.handle_get_listings({})
            first_call_time = (datetime.now() - start_time).total_seconds()
            
            start_time = datetime.now()
            await self.cex_listings.handle_get_listings({})
            cached_call_time = (datetime.now() - start_time).total_seconds()
            
            # Test DEX caching
            start_time = datetime.now()
            await self.dex_listings.handle_get_listings({})
            dex_first_call_time = (datetime.now() - start_time).total_seconds()
            
            start_time = datetime.now()
            await self.dex_listings.handle_get_listings({})
            dex_cached_call_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results['integration_tests']['cache_performance'] = {
                'status': 'PASS',
                'cex_first_call': first_call_time,
                'cex_cached_call': cached_call_time,
                'cex_speedup': first_call_time / cached_call_time if cached_call_time > 0 else 0,
                'dex_first_call': dex_first_call_time,
                'dex_cached_call': dex_cached_call_time,
                'dex_speedup': dex_first_call_time / dex_cached_call_time if dex_cached_call_time > 0 else 0
            }
            
            logger.info(f"   ✅ CEX: {first_call_time:.2f}s → {cached_call_time:.2f}s ({first_call_time/cached_call_time:.1f}x speedup)")
            logger.info(f"   ✅ DEX: {dex_first_call_time:.2f}s → {dex_cached_call_time:.2f}s ({dex_first_call_time/dex_cached_call_time:.1f}x speedup)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache performance test failed: {e}")
            self.test_results['integration_tests']['cache_performance'] = {'status': 'FAIL', 'error': str(e)}
            return False
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🧪 COIN LISTINGS INTEGRATION TEST SUMMARY")
        print("="*80)
        
        # CEX Tests
        print("\n📈 CEX MODULE TESTS:")
        for test_name, result in self.test_results['cex_tests'].items():
            if isinstance(result, dict) and 'status' in result:
                status = "✅ PASS" if result['status'] == 'PASS' else "❌ FAIL"
                print(f"   {status} {test_name}")
                if result['status'] == 'PASS':
                    if 'total_symbols' in result:
                        print(f"      Symbols: {result['total_symbols']}")
                    if 'found_symbols' in result:
                        print(f"      Found: {result['found_symbols']}")
        
        # DEX Tests
        print("\n🔄 DEX MODULE TESTS:")
        for test_name, result in self.test_results['dex_tests'].items():
            if isinstance(result, dict) and 'status' in result:
                status = "✅ PASS" if result['status'] == 'PASS' else "❌ FAIL"
                print(f"   {status} {test_name}")
                if result['status'] == 'PASS':
                    if 'total_tokens' in result:
                        print(f"      Tokens: {result['total_tokens']}")
                    if 'found_tokens' in result:
                        print(f"      Found: {result['found_tokens']}")
        
        # Integration Tests
        print("\n🔗 INTEGRATION TESTS:")
        for test_name, result in self.test_results['integration_tests'].items():
            if isinstance(result, dict) and 'status' in result:
                status = "✅ PASS" if result['status'] == 'PASS' else "❌ FAIL"
                print(f"   {status} {test_name}")
                if result['status'] == 'PASS':
                    if test_name == 'trading_pairs':
                        print(f"      Unified pairs: {result['unified_pairs']}")
                        print(f"      CEX sources: {result['cex_symbols']}")
                        print(f"      DEX sources: {result['dex_symbols']}")
                    elif test_name == 'cache_performance':
                        print(f"      CEX speedup: {result['cex_speedup']:.1f}x")
                        print(f"      DEX speedup: {result['dex_speedup']:.1f}x")
        
        # Overall Status
        all_tests = []
        for category in self.test_results.values():
            for test_result in category.values():
                if isinstance(test_result, dict) and 'status' in test_result:
                    all_tests.append(test_result['status'])
        
        passed = all_tests.count('PASS')
        total = len(all_tests)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 Integration test SUCCESSFUL - Ready for production!")
        elif success_rate >= 60:
            print("⚠️ Integration test PARTIAL - Some issues need attention")
        else:
            print("❌ Integration test FAILED - Major issues detected")
        
        print("="*80 + "\n")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting comprehensive integration tests...")
        
        # Setup
        if not await self.setup_modules():
            logger.error("❌ Module setup failed - aborting tests")
            return False
        
        # Run tests
        tests = [
            ("CEX Functionality", self.test_cex_functionality),
            ("DEX Functionality", self.test_dex_functionality),
            ("Trading Pair Generation", self.test_trading_pair_generation),
            ("Cache Performance", self.test_cache_performance)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"🔄 Running {test_name} test...")
            try:
                await test_func()
                logger.info(f"✅ {test_name} test completed")
            except Exception as e:
                logger.error(f"❌ {test_name} test failed: {e}")
        
        # Print summary
        self.print_test_summary()
        
        return True

async def main():
    """Main test execution"""
    try:
        # Create test instance
        test = CoinListingsIntegrationTest()
        
        # Run all tests
        await test.run_all_tests()
        
        logger.info("🏁 Integration test completed")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal test error: {e}")

if __name__ == "__main__":
    # Create data directory
    os.makedirs('data/test_coin_listings', exist_ok=True)
    
    # Run tests
    asyncio.run(main()) 