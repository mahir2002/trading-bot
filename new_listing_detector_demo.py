#!/usr/bin/env python3
"""
🔍 New Listing Detector Demo
Comprehensive demonstration of the new coin listing detection system
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add paths
sys.path.append('.')
sys.path.append('unified_trading_platform')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_new_listing_detector():
    """Demonstrate the new listing detection system"""
    logger.info("🚀 Starting New Listing Detector Demo...")
    
    try:
        # Import the module
        from modules.new_listing_detector import NewListingDetectorModule
        
        # Configuration
        config = {
            'check_interval_hours': 1,  # Check every hour for demo
            'coingecko_api_key': os.getenv('COINGECKO_API_KEY', ''),  # Set your API key
            'enable_geckoterminal': True,
            'enable_notifications': True,
            'min_market_cap_usd': 50000,  # Lower threshold for demo
            'max_new_listings_per_check': 20,
            'historical_retention_days': 7,
            'cache_dir': 'data/new_listings_demo'
        }
        
        # Create module instance
        detector = NewListingDetectorModule('new_listing_detector', config)
        
        # Initialize
        logger.info("🔧 Initializing New Listing Detector...")
        if not await detector.initialize():
            logger.error("❌ Failed to initialize detector")
            return
        
        # Start the module
        logger.info("🚀 Starting New Listing Detector...")
        if not await detector.start():
            logger.error("❌ Failed to start detector")
            return
        
        # Health check
        logger.info("🏥 Performing health check...")
        health = await detector.health_check()
        logger.info(f"Health Status: {health}")
        
        # Demonstrate manual detection
        logger.info("🔍 Triggering manual new listing detection...")
        
        # Create mock event for manual detection
        class MockEvent:
            def __init__(self, data=None):
                self.data = data or {}
        
        detection_result = await detector._handle_detect_new_listings(MockEvent())
        logger.info(f"Detection Result: {detection_result}")
        
        # Wait a moment for processing
        await asyncio.sleep(5)
        
        # Get detected new listings
        logger.info("📋 Retrieving detected new listings...")
        get_listings_result = await detector._handle_get_new_listings(MockEvent({'limit': 10}))
        
        if get_listings_result['success']:
            listings = get_listings_result['listings']
            logger.info(f"📊 Retrieved {len(listings)} new listings")
            
            # Display top new listings
            if listings:
                logger.info("🆕 Top New Listings:")
                for i, listing in enumerate(listings[:5], 1):
                    logger.info(f"  {i}. {listing['symbol']} ({listing['name']})")
                    logger.info(f"     Source: {listing['source']}")
                    logger.info(f"     Priority: {listing['ai_analysis_priority']}")
                    logger.info(f"     Market Cap: ${listing['market_cap_usd']:,.2f}" if listing['market_cap_usd'] else "     Market Cap: N/A")
                    logger.info(f"     Risk Score: {listing['risk_score']}/100")
                    logger.info("")
            else:
                logger.info("📝 No new listings detected in this demo run")
        
        # Get AI data
        logger.info("🧠 Retrieving AI analysis data...")
        ai_data_result = await detector._handle_get_ai_data(MockEvent())
        
        if ai_data_result['success']:
            ai_data = ai_data_result['ai_data']
            logger.info("🧠 AI Data Summary:")
            logger.info(f"  Total New Listings: {ai_data['total_new_listings']}")
            logger.info(f"  High Priority: {ai_data['high_priority_count']}")
            logger.info(f"  Medium Priority: {ai_data['medium_priority_count']}")
            logger.info(f"  Low Priority: {ai_data['low_priority_count']}")
            logger.info(f"  Data File: {ai_data_result['file_path']}")
        
        # Show statistics
        logger.info("📊 Module Statistics:")
        stats = detector.get_statistics()
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        # Demonstrate historical snapshot functionality
        logger.info("📚 Demonstrating historical snapshot functionality...")
        await demonstrate_historical_tracking(detector)
        
        # Stop the module
        logger.info("🛑 Stopping New Listing Detector...")
        await detector.stop()
        
        logger.info("✅ New Listing Detector Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

async def demonstrate_historical_tracking(detector):
    """Demonstrate historical snapshot tracking"""
    try:
        logger.info("🔍 Testing historical snapshot creation...")
        
        # Create sample coin lists for different days
        sample_coins_day1 = {'bitcoin', 'ethereum', 'cardano', 'polkadot'}
        sample_coins_day2 = {'bitcoin', 'ethereum', 'cardano', 'polkadot', 'chainlink', 'uniswap'}  # 2 new coins
        
        # Create snapshots
        snapshot1 = detector._create_snapshot('sample_exchange', sample_coins_day1)
        snapshot2 = detector._create_snapshot('sample_exchange', sample_coins_day2)
        
        logger.info(f"📸 Snapshot 1: {snapshot1.total_coins} coins")
        logger.info(f"📸 Snapshot 2: {snapshot2.total_coins} coins")
        
        # Calculate new coins
        new_coins = snapshot2.coin_list - snapshot1.coin_list
        logger.info(f"🆕 New coins detected: {list(new_coins)}")
        
        # Save sample snapshots
        await detector._save_snapshot(snapshot1)
        await detector._save_snapshot(snapshot2)
        
        logger.info("✅ Historical tracking demonstration completed")
        
    except Exception as e:
        logger.error(f"❌ Historical tracking demo failed: {e}")

async def demonstrate_coingecko_integration():
    """Demonstrate CoinGecko API integration"""
    logger.info("🦎 Demonstrating CoinGecko Integration...")
    
    try:
        from modules.new_listing_detector import NewListingDetectorModule
        
        config = {
            'coingecko_api_key': os.getenv('COINGECKO_API_KEY', ''),
            'cache_dir': 'data/new_listings_demo'
        }
        
        detector = NewListingDetectorModule('coingecko_demo', config)
        await detector.initialize()
        
        # Test CoinGecko API
        logger.info("🌐 Testing CoinGecko API connectivity...")
        coingecko_status = await detector._test_coingecko_api()
        logger.info(f"CoinGecko API Status: {'✅ Connected' if coingecko_status else '❌ Failed'}")
        
        if coingecko_status:
            # Get coin list sample
            logger.info("📋 Fetching CoinGecko coin list sample...")
            coin_list = await detector._get_coingecko_coin_list()
            
            if coin_list:
                logger.info(f"📊 Retrieved {len(coin_list)} coins from CoinGecko")
                
                # Show sample coins
                sample_coins = list(coin_list.items())[:5]
                logger.info("🪙 Sample coins:")
                for coin_id, coin_data in sample_coins:
                    logger.info(f"  - {coin_data['name']} ({coin_data['symbol'].upper()})")
                    logger.info(f"    ID: {coin_id}")
                    platforms = coin_data.get('platforms', {})
                    if platforms:
                        logger.info(f"    Platforms: {list(platforms.keys())}")
                    logger.info("")
        
        # Test GeckoTerminal API
        logger.info("🔥 Testing GeckoTerminal API...")
        geckoterminal_status = await detector._test_geckoterminal_api()
        logger.info(f"GeckoTerminal API Status: {'✅ Connected' if geckoterminal_status else '❌ Failed'}")
        
        if geckoterminal_status:
            # Get trending tokens
            trending_tokens = await detector._get_geckoterminal_coins()
            if trending_tokens:
                logger.info(f"🔥 Retrieved {len(trending_tokens)} trending tokens")
                
                # Show sample trending tokens
                sample_trending = list(trending_tokens)[:5]
                logger.info("🔥 Sample trending tokens:")
                for token in sample_trending:
                    logger.info(f"  - {token}")
        
        await detector.stop()
        
    except Exception as e:
        logger.error(f"❌ CoinGecko integration demo failed: {e}")

def display_demo_summary():
    """Display demo summary and next steps"""
    print("\n" + "="*80)
    print("🎉 NEW LISTING DETECTOR DEMO SUMMARY")
    print("="*80)
    print()
    print("✅ IMPLEMENTED FEATURES:")
    print("  📊 Historical coin listing tracking")
    print("  🔍 Automated new listing detection")
    print("  🦎 CoinGecko API integration (/coins/list)")
    print("  🔥 GeckoTerminal trending token tracking")
    print("  🧠 AI-ready data preparation")
    print("  📦 Separate storage for new coins")
    print("  🚨 Priority-based risk assessment")
    print("  📲 Notification system for high-priority listings")
    print()
    print("📁 DATA FILES CREATED:")
    print("  📊 data/new_listings_demo/new_listings.db - SQLite database")
    print("  🧠 data/new_listings_demo/new_coins_for_ai.json - AI analysis data")
    print()
    print("🔧 INTEGRATION OPTIONS:")
    print("  1. Add to unified_master_trading_bot.py")
    print("  2. Connect to existing CEX/DEX listing modules")
    print("  3. Set up automatic trading on new high-priority listings")
    print("  4. Implement Telegram notifications for new coins")
    print()
    print("💡 NEXT STEPS:")
    print("  1. Set COINGECKO_API_KEY environment variable for full functionality")
    print("  2. Configure check intervals (default: 6 hours)")
    print("  3. Adjust minimum market cap thresholds")
    print("  4. Integrate with your existing trading strategies")
    print()
    print("🚀 BUSINESS VALUE:")
    print("  💰 Early detection of profitable new listings")
    print("  🎯 AI-powered prioritization reduces noise")
    print("  ⚡ Automated competitive advantage")
    print("  📈 Enhanced market coverage and opportunities")
    print()
    print("="*80)

async def run_comprehensive_demo():
    """Run comprehensive demonstration"""
    print("🔍 NEW LISTING DETECTOR - COMPREHENSIVE DEMO")
    print("="*80)
    
    # Check for API key
    if not os.getenv('COINGECKO_API_KEY'):
        print("⚠️  WARNING: COINGECKO_API_KEY not set")
        print("   Some features will be limited without API key")
        print("   Get your free API key at: https://www.coingecko.com/en/api")
        print()
    
    # Run main demo
    await demo_new_listing_detector()
    
    print("\n" + "-"*80)
    
    # Run CoinGecko integration demo
    await demonstrate_coingecko_integration()
    
    # Display summary
    display_demo_summary()

if __name__ == "__main__":
    # Create data directory
    os.makedirs('data/new_listings_demo', exist_ok=True)
    
    # Run the demo
    asyncio.run(run_comprehensive_demo()) 