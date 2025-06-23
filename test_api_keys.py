#!/usr/bin/env python3
"""
🔍 Ultimate Trading System - API Key Validator
============================================

Comprehensive API key testing and validation script.
Tests all API keys from your config.env.unified file.

Usage:
    python test_api_keys.py                    # Test all APIs
    python test_api_keys.py --exchanges        # Test only exchanges
    python test_api_keys.py --data             # Test only data sources
    python test_api_keys.py --notifications    # Test only notifications
"""

import asyncio
import argparse
import sys
from datetime import datetime
import logging

# Import the ultimate system
from ultimate_all_in_one_trading_system import UltimateAllInOneTradingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print API testing banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║            🔍 ULTIMATE TRADING SYSTEM - API KEY VALIDATOR 🔍                 ║
║                                                                              ║
║                    Test All API Keys and Connectivity                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🔄 Exchange APIs: Binance, Coinbase, Kraken, Bybit, OKX, etc.             ║
║  📊 Data Sources: CoinGecko, CoinMarketCap, DexScreener, etc.              ║
║  📱 Social Media: Twitter, Reddit APIs                                     ║
║  📰 News Sources: NewsAPI, CryptoPanic, Benzinga                           ║
║  🔔 Notifications: Telegram, Email                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

async def test_all_apis():
    """Test all API keys"""
    print("🚀 Initializing Ultimate Trading System...")
    
    # Initialize the system
    system = UltimateAllInOneTradingSystem()
    
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n⏳ Testing API connectivity...")
    
    # Run comprehensive API validation
    results = await system.validate_api_keys()
    
    return results

async def test_exchanges_only():
    """Test only exchange APIs"""
    print("🔄 Testing Exchange APIs only...")
    
    system = UltimateAllInOneTradingSystem()
    
    results = {'exchanges': {}}
    
    for name, exchange in system.exchanges.items():
        try:
            if hasattr(exchange, 'fetch_balance') and system.exchange_config[name]['enabled']:
                # Test with a simple API call
                await asyncio.sleep(0.1)  # Rate limiting
                balance = exchange.fetch_balance()
                results['exchanges'][name] = {
                    'status': 'active',
                    'message': 'API key valid and active'
                }
                logger.info(f"✅ {name.title()} API key validated")
            else:
                results['exchanges'][name] = {
                    'status': 'demo',
                    'message': 'Running in demo mode'
                }
                logger.info(f"⚠️ {name.title()} running in demo mode")
        except Exception as e:
            results['exchanges'][name] = {
                'status': 'error',
                'message': str(e)
            }
            logger.warning(f"❌ {name.title()} API validation failed: {e}")
    
    return results

async def test_data_sources_only():
    """Test only data source APIs"""
    print("📊 Testing Data Source APIs only...")
    
    system = UltimateAllInOneTradingSystem()
    
    results = {'data_sources': {}}
    
    for source, config in system.data_config.items():
        if config['enabled']:
            try:
                results['data_sources'][source] = await system._test_data_api(source, config)
                logger.info(f"✅ {source.title()} API tested")
            except Exception as e:
                results['data_sources'][source] = {
                    'status': 'error',
                    'message': str(e)
                }
                logger.warning(f"❌ {source.title()} API test failed: {e}")
    
    return results

async def test_notifications_only():
    """Test only notification APIs"""
    print("🔔 Testing Notification APIs only...")
    
    system = UltimateAllInOneTradingSystem()
    
    results = {'notifications': {}}
    
    # Test Telegram
    if system.telegram_config['active']:
        try:
            await system._send_telegram_notification("🔍 API validation test - Ultimate Trading System")
            results['notifications']['telegram'] = {
                'status': 'active',
                'message': 'Test message sent successfully'
            }
            logger.info("✅ Telegram API validated")
        except Exception as e:
            results['notifications']['telegram'] = {
                'status': 'error',
                'message': str(e)
            }
            logger.warning(f"❌ Telegram validation failed: {e}")
    
    # Test Email
    if system.email_config['active']:
        try:
            await system._send_email_notification(
                "API Validation Test", 
                "🔍 API validation test - Ultimate Trading System"
            )
            results['notifications']['email'] = {
                'status': 'active',
                'message': 'Test email sent successfully'
            }
            logger.info("✅ Email API validated")
        except Exception as e:
            results['notifications']['email'] = {
                'status': 'error',
                'message': str(e)
            }
            logger.warning(f"❌ Email validation failed: {e}")
    
    return results

def print_results(results: dict):
    """Print formatted test results"""
    print("\n" + "="*80)
    print("🔍 API VALIDATION RESULTS")
    print("="*80)
    
    total_apis = 0
    active_apis = 0
    
    for category, apis in results.items():
        if apis:
            print(f"\n📋 {category.replace('_', ' ').title()}:")
            for name, result in apis.items():
                status_icon = "✅" if result['status'] == 'active' else "⚠️" if result['status'] == 'demo' else "❌"
                print(f"   {status_icon} {name.title()}: {result['message']}")
                total_apis += 1
                if result['status'] == 'active':
                    active_apis += 1
    
    success_rate = (active_apis / total_apis * 100) if total_apis > 0 else 0
    
    print(f"\n📊 SUMMARY:")
    print(f"   • Total APIs Tested: {total_apis}")
    print(f"   • Active APIs: {active_apis}")
    print(f"   • Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        status = "🟢 EXCELLENT"
    elif success_rate >= 50:
        status = "🟡 GOOD"
    elif success_rate >= 25:
        status = "🟠 LIMITED"
    else:
        status = "🔴 DEMO MODE"
    
    print(f"   • System Status: {status}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if success_rate < 100:
        print("   • Add missing API keys to config.env.unified")
        print("   • Verify API key permissions and quotas")
        print("   • Check network connectivity")
    else:
        print("   • All APIs are working perfectly!")
        print("   • System ready for live trading")

def main():
    """Main API testing function"""
    parser = argparse.ArgumentParser(description='Test Ultimate Trading System API Keys')
    parser.add_argument('--exchanges', action='store_true', help='Test only exchange APIs')
    parser.add_argument('--data', action='store_true', help='Test only data source APIs')
    parser.add_argument('--notifications', action='store_true', help='Test only notification APIs')
    parser.add_argument('--social', action='store_true', help='Test only social media APIs')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Determine test scope
    if args.exchanges:
        print("🔄 Testing Exchange APIs Only")
        results = asyncio.run(test_exchanges_only())
    elif args.data:
        print("📊 Testing Data Source APIs Only")
        results = asyncio.run(test_data_sources_only())
    elif args.notifications:
        print("🔔 Testing Notification APIs Only")
        results = asyncio.run(test_notifications_only())
    else:
        # Test all APIs
        print("🔍 Testing All APIs")
        results = asyncio.run(test_all_apis())
    
    # Print results
    print_results(results)
    
    # Determine exit code
    total_apis = sum(len(apis) for apis in results.values())
    active_apis = sum(
        1 for apis in results.values() 
        for result in apis.values() 
        if result['status'] == 'active'
    )
    
    if total_apis == 0:
        print("\n⚠️ No APIs configured or tested")
        sys.exit(1)
    elif active_apis == 0:
        print("\n❌ No APIs are working - running in demo mode")
        sys.exit(2)
    elif active_apis < total_apis:
        print(f"\n⚠️ Some APIs are not working ({active_apis}/{total_apis})")
        sys.exit(0)  # Partial success
    else:
        print("\n🎉 All APIs are working perfectly!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 API testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1) 