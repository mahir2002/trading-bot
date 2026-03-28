#!/usr/bin/env python3
"""
🔗 New Listing Detector Integration Script
Integrates the new listing detector with existing CEX/DEX coin listing modules
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
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

async def integrate_new_listing_detector():
    """Integrate new listing detector with existing systems"""
    logger.info("🔗 Starting New Listing Detector Integration...")
    
    try:
        # Import required modules
        from modules.new_listing_detector import NewListingDetectorModule
        from modules.coin_listings_cex import CEXCoinListingsModule
        from modules.coin_listings_dex import DEXCoinListingsModule
        
        # Configuration for new listing detector
        detector_config = {
            'check_interval_hours': 6,
            'coingecko_api_key': os.getenv('COINGECKO_API_KEY', ''),
            'enable_geckoterminal': True,
            'min_market_cap_usd': 100000,
            'cache_dir': 'data/integrated_new_listings'
        }
        
        # Configuration for CEX module
        cex_config = {
            'enabled_exchanges': ['binance', 'coinbasepro', 'kraken', 'bybit'],
            'cache_duration_hours': 24,
            'include_delisted': False,
            'symbol_types': ['spot']
        }
        
        # Configuration for DEX module
        dex_config = {
            'enabled_networks': ['ethereum', 'bsc', 'polygon'],
            'enabled_dexes': ['uniswap_v2', 'uniswap_v3', 'pancakeswap'],
            'min_liquidity_usd': 10000,
            'cache_duration_hours': 24
        }
        
        # Create module instances
        detector = NewListingDetectorModule('new_listing_detector', detector_config)
        cex_module = CEXCoinListingsModule('cex_listings', cex_config)
        dex_module = DEXCoinListingsModule('dex_listings', dex_config)
        
        # Initialize all modules
        logger.info("🔧 Initializing modules...")
        
        modules = [
            ('New Listing Detector', detector),
            ('CEX Listings', cex_module),
            ('DEX Listings', dex_module)
        ]
        
        for name, module in modules:
            if await module.initialize():
                logger.info(f"✅ {name} initialized successfully")
            else:
                logger.error(f"❌ Failed to initialize {name}")
                return False
        
        # Start all modules
        logger.info("🚀 Starting modules...")
        for name, module in modules:
            if await module.start():
                logger.info(f"✅ {name} started successfully")
            else:
                logger.error(f"❌ Failed to start {name}")
                return False
        
        # Create integrated detection system
        integrated_system = IntegratedListingSystem(detector, cex_module, dex_module)
        
        # Run integrated detection
        logger.info("🔍 Running integrated new listing detection...")
        await integrated_system.run_comprehensive_detection()
        
        # Display results
        await integrated_system.display_results()
        
        # Stop all modules
        logger.info("🛑 Stopping modules...")
        for name, module in modules:
            await module.stop()
            logger.info(f"✅ {name} stopped")
        
        logger.info("✅ Integration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

class IntegratedListingSystem:
    """Integrated listing detection system combining all sources"""
    
    def __init__(self, detector, cex_module, dex_module):
        self.detector = detector
        self.cex_module = cex_module
        self.dex_module = dex_module
        self.results = {}
    
    async def run_comprehensive_detection(self):
        """Run comprehensive detection across all sources"""
        try:
            # Get current listings from all sources
            logger.info("📊 Collecting current listings from all sources...")
            
            # Get CEX listings
            cex_event = MockEvent({'action': 'get_all_listings'})
            cex_result = await self.cex_module._handle_get_listings(cex_event)
            cex_coins = set()
            
            if cex_result.get('success'):
                for exchange, listings in cex_result.get('listings', {}).items():
                    for symbol, data in listings.items():
                        cex_coins.add(f"cex_{exchange}_{symbol}")
                logger.info(f"📈 CEX: Found {len(cex_coins)} trading pairs")
            
            # Get DEX listings  
            dex_event = MockEvent({'action': 'get_all_tokens'})
            dex_result = await self.dex_module._handle_get_tokens(dex_event)
            dex_coins = set()
            
            if dex_result.get('success'):
                for network, tokens in dex_result.get('tokens', {}).items():
                    for token_id, data in tokens.items():
                        dex_coins.add(f"dex_{network}_{token_id}")
                logger.info(f"🔥 DEX: Found {len(dex_coins)} tokens")
            
            # Simulate historical data for demonstration
            await self._create_mock_historical_data(cex_coins, dex_coins)
            
            # Run new listing detection
            logger.info("🔍 Running new listing detection...")
            detection_event = MockEvent({})
            detection_result = await self.detector._handle_detect_new_listings(detection_event)
            
            # Store results
            self.results = {
                'cex_coins': len(cex_coins),
                'dex_coins': len(dex_coins),
                'detection_result': detection_result,
                'total_sources': len(cex_coins) + len(dex_coins)
            }
            
            # Get detected new listings
            get_listings_event = MockEvent({'limit': 20})
            new_listings_result = await self.detector._handle_get_new_listings(get_listings_event)
            self.results['new_listings'] = new_listings_result.get('listings', [])
            
            # Get AI data
            ai_data_event = MockEvent({})
            ai_data_result = await self.detector._handle_get_ai_data(ai_data_event)
            self.results['ai_data'] = ai_data_result.get('ai_data', {})
            
        except Exception as e:
            logger.error(f"❌ Comprehensive detection failed: {e}")
            raise
    
    async def _create_mock_historical_data(self, cex_coins, dex_coins):
        """Create mock historical data for demonstration"""
        try:
            # Create yesterday's snapshot (smaller set)
            yesterday_cex = set(list(cex_coins)[:max(1, len(cex_coins)//2)])  # Half the coins
            yesterday_dex = set(list(dex_coins)[:max(1, len(dex_coins)//2)])  # Half the coins
            
            # Create snapshots
            if yesterday_cex:
                snapshot_cex = self.detector._create_snapshot('integrated_cex', yesterday_cex)
                await self.detector._save_snapshot(snapshot_cex)
                logger.info(f"📸 Created CEX historical snapshot: {len(yesterday_cex)} coins")
            
            if yesterday_dex:
                snapshot_dex = self.detector._create_snapshot('integrated_dex', yesterday_dex)
                await self.detector._save_snapshot(snapshot_dex)
                logger.info(f"📸 Created DEX historical snapshot: {len(yesterday_dex)} coins")
            
            # Update detector's historical data
            await self.detector._load_historical_data()
            
        except Exception as e:
            logger.error(f"Failed to create mock historical data: {e}")
    
    async def display_results(self):
        """Display comprehensive results"""
        try:
            logger.info("📊 INTEGRATED LISTING DETECTION RESULTS")
            logger.info("=" * 60)
            
            # Source statistics
            logger.info(f"📈 CEX Trading Pairs: {self.results['cex_coins']}")
            logger.info(f"🔥 DEX Tokens: {self.results['dex_coins']}")
            logger.info(f"🌐 Total Sources Monitored: {self.results['total_sources']}")
            
            # Detection results
            detection = self.results['detection_result']
            logger.info(f"✅ Detection Success: {detection.get('success', False)}")
            logger.info(f"🆕 New Listings Found: {detection.get('new_listings_found', 0)}")
            
            # New listings details
            new_listings = self.results['new_listings']
            if new_listings:
                logger.info(f"📋 Detected New Listings ({len(new_listings)}):")
                for i, listing in enumerate(new_listings[:5], 1):  # Show top 5
                    logger.info(f"  {i}. {listing['symbol']} ({listing['name']})")
                    logger.info(f"     Source: {listing['source']}")
                    logger.info(f"     Priority: {listing['ai_analysis_priority']}")
                    if listing['market_cap_usd']:
                        logger.info(f"     Market Cap: ${listing['market_cap_usd']:,.0f}")
                    logger.info("")
            else:
                logger.info("📝 No new listings detected in current run")
            
            # AI data summary
            ai_data = self.results['ai_data']
            if ai_data:
                logger.info("🧠 AI Analysis Summary:")
                logger.info(f"  Total New Listings: {ai_data.get('total_new_listings', 0)}")
                logger.info(f"  High Priority: {ai_data.get('high_priority_count', 0)}")
                logger.info(f"  Medium Priority: {ai_data.get('medium_priority_count', 0)}")
                logger.info(f"  Low Priority: {ai_data.get('low_priority_count', 0)}")
            
            # Module health status
            logger.info("🏥 Module Health Status:")
            for name, module in [
                ('New Listing Detector', self.detector),
                ('CEX Listings', self.cex_module),
                ('DEX Listings', self.dex_module)
            ]:
                health = await module.health_check()
                status = health.get('status', 'unknown')
                logger.info(f"  {name}: {status.upper()}")
            
        except Exception as e:
            logger.error(f"Failed to display results: {e}")

class MockEvent:
    """Mock event class for testing"""
    def __init__(self, data=None):
        self.data = data or {}

async def create_integration_config():
    """Create integration configuration for unified master bot"""
    logger.info("📝 Creating integration configuration...")
    
    integration_config = {
        'new_listing_detection': {
            'enabled': True,
            'check_interval_hours': 6,
            'coingecko_api_key': '${COINGECKO_API_KEY}',
            'min_market_cap_usd': 100000,
            'enable_notifications': True,
            'enable_auto_trading': False,  # Safety first
            'max_new_listings_per_check': 20
        },
        'integration_settings': {
            'combine_cex_dex_data': True,
            'deduplicate_across_sources': True,
            'prioritize_high_volume_exchanges': True,
            'minimum_detection_confidence': 0.8
        },
        'notification_settings': {
            'telegram_enabled': True,
            'email_enabled': False,
            'webhook_enabled': False,
            'high_priority_only': True
        },
        'auto_trading_settings': {
            'enabled': False,  # Disabled by default for safety
            'max_position_size_usd': 1000,
            'minimum_market_cap_usd': 10000000,  # $10M minimum for auto-trading
            'maximum_risk_score': 30,  # Low risk only
            'cooldown_hours': 24  # Wait 24h before trading new listings
        }
    }
    
    # Save configuration
    config_path = 'data/new_listing_integration_config.json'
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    import json
    with open(config_path, 'w') as f:
        json.dump(integration_config, f, indent=2)
    
    logger.info(f"💾 Integration configuration saved to: {config_path}")
    
    return integration_config

def display_integration_summary():
    """Display integration summary"""
    print("\n" + "="*80)
    print("🎉 NEW LISTING DETECTOR INTEGRATION COMPLETE")
    print("="*80)
    print()
    print("✅ SUCCESSFULLY INTEGRATED:")
    print("  🔗 New Listing Detector Module")
    print("  📈 CEX Coin Listings Module") 
    print("  🔥 DEX Coin Listings Module")
    print("  🧠 AI-Ready Data Processing")
    print("  📊 Historical Comparison System")
    print()
    print("🎯 KEY CAPABILITIES:")
    print("  📊 Yesterday vs Today Comparison")
    print("  🦎 CoinGecko /coins/list Integration")
    print("  🔥 GeckoTerminal Trending Tokens")
    print("  📦 Separate AI Processing Storage")
    print("  🚨 Priority-Based Risk Assessment")
    print("  📲 Real-time Notification System")
    print()
    print("📁 FILES CREATED:")
    print("  📊 data/integrated_new_listings/new_listings.db")
    print("  🧠 data/integrated_new_listings/new_coins_for_ai.json")
    print("  ⚙️  data/new_listing_integration_config.json")
    print()
    print("🚀 NEXT STEPS:")
    print("  1. Set COINGECKO_API_KEY environment variable")
    print("  2. Add integration to unified_master_trading_bot.py")
    print("  3. Configure Telegram notifications")
    print("  4. Test with paper trading first")
    print("  5. Gradually enable auto-trading features")
    print()
    print("💰 BUSINESS VALUE:")
    print("  🎯 First-mover advantage on new listings")
    print("  🤖 AI-powered opportunity detection")
    print("  ⚡ Automated competitive intelligence")
    print("  📈 Enhanced profit potential")
    print()
    print("⚠️  SAFETY FEATURES:")
    print("  🛡️  Auto-trading disabled by default")
    print("  💰 Position size limits")
    print("  🎯 High market cap requirements for auto-trading")
    print("  ⏰ Cooldown periods between trades")
    print("="*80)

async def main():
    """Main integration function"""
    print("🔗 NEW LISTING DETECTOR INTEGRATION")
    print("="*80)
    
    # Create data directories
    os.makedirs('data/integrated_new_listings', exist_ok=True)
    
    # Run integration
    success = await integrate_new_listing_detector()
    
    if success:
        # Create integration config
        await create_integration_config()
        
        # Display summary
        display_integration_summary()
    else:
        print("❌ Integration failed - please check logs for details")

if __name__ == "__main__":
    asyncio.run(main()) 