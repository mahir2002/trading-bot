#!/usr/bin/env python3
"""
📈 Historical Data Fetcher Module Demo
Demonstrates 30-day OHLCV data fetching for newly detected coins
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the historical data fetcher module
try:
    from unified_trading_platform.modules.historical_data_fetcher import HistoricalDataFetcherModule
    from unified_trading_platform.core.base_module import ModuleEvent
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Make sure you're running from the correct directory")
    exit(1)

async def demo_historical_data_fetcher():
    """
    Comprehensive Historical Data Fetcher Demo
    
    Shows:
    1. Module initialization and setup
    2. Processing new listing events
    3. Fetching OHLCV data from CoinGecko and exchanges
    4. SQLite database storage
    5. CSV export functionality
    6. AI-ready data preparation
    7. Data quality assessment
    """
    
    print("=" * 80)
    print("🚀 HISTORICAL DATA FETCHER MODULE DEMO")
    print("=" * 80)
    print()
    
    # ================================================================
    # 1. MODULE INITIALIZATION
    # ================================================================
    print("📋 STEP 1: MODULE INITIALIZATION")
    print("-" * 50)
    
    # Configuration for the historical data fetcher
    config = {
        'coingecko_api_key': '',  # Add your CoinGecko Pro API key if available
        'data_retention_days': 30,
        'enable_ccxt_fetching': True,
        'enable_csv_export': True,
        'data_quality_threshold': 0.8,
        'cache_dir': 'data/historical_data'
    }
    
    # Create and initialize the module
    fetcher = HistoricalDataFetcherModule("historical_data_fetcher", config)
    
    print(f"✅ Created Historical Data Fetcher Module")
    print(f"📊 Data retention: {config['data_retention_days']} days")
    print(f"💾 Cache directory: {config['cache_dir']}")
    print(f"📈 CCXT fetching: {'enabled' if config['enable_ccxt_fetching'] else 'disabled'}")
    print(f"📄 CSV export: {'enabled' if config['enable_csv_export'] else 'disabled'}")
    print()
    
    # Initialize module
    success = await fetcher.initialize()
    if not success:
        print("❌ Failed to initialize Historical Data Fetcher Module")
        return
    
    # Start module
    success = await fetcher.start()
    if not success:
        print("❌ Failed to start Historical Data Fetcher Module")
        return
    
    print("✅ Historical Data Fetcher Module initialized and started successfully")
    print()
    
    # ================================================================
    # 2. HEALTH CHECK AND STATUS
    # ================================================================
    print("📋 STEP 2: HEALTH CHECK AND STATUS")
    print("-" * 50)
    
    health = await fetcher.health_check()
    print(f"🏥 Health status: {health['status']}")
    print(f"💾 Database status: {health['db_status']}")
    print(f"🔗 API status: {json.dumps(health['api_status'], indent=2)}")
    print(f"📚 Datasets cached: {health['datasets_cached']}")
    print(f"⏳ Pending fetches: {health['pending_fetches']}")
    print()
    
    # ================================================================
    # 3. SIMULATE NEW LISTING EVENTS
    # ================================================================
    print("📋 STEP 3: SIMULATE NEW LISTING EVENTS")
    print("-" * 50)
    
    # Sample new listings that we'll process
    sample_new_listings = [
        {
            'coin_id': 'bitcoin',
            'symbol': 'BTC',
            'name': 'Bitcoin',
            'coingecko_id': 'bitcoin',
            'market_cap_usd': 800000000000,
            'priority': 'high'
        },
        {
            'coin_id': 'ethereum',
            'symbol': 'ETH', 
            'name': 'Ethereum',
            'coingecko_id': 'ethereum',
            'market_cap_usd': 300000000000,
            'priority': 'high'
        },
        {
            'coin_id': 'cardano',
            'symbol': 'ADA',
            'name': 'Cardano',
            'coingecko_id': 'cardano',
            'market_cap_usd': 15000000000,
            'priority': 'medium'
        },
        {
            'coin_id': 'solana',
            'symbol': 'SOL',
            'name': 'Solana',
            'coingecko_id': 'solana',
            'market_cap_usd': 25000000000,
            'priority': 'high'
        },
        {
            'coin_id': 'chainlink',
            'symbol': 'LINK',
            'name': 'Chainlink',
            'coingecko_id': 'chainlink',
            'market_cap_usd': 8000000000,
            'priority': 'medium'
        }
    ]
    
    print(f"🪙 Processing {len(sample_new_listings)} sample new listings:")
    print()
    
    results = []
    for i, listing in enumerate(sample_new_listings, 1):
        print(f"  {i}. {listing['symbol']} ({listing['name']})")
        print(f"     💰 Market Cap: ${listing['market_cap_usd']:,}")
        print(f"     🔥 Priority: {listing['priority']}")
        
        # Create event and process it
        event = ModuleEvent(
            event_type='process_new_listing',
            data=listing,
            timestamp=datetime.now()
        )
        
        result = await fetcher._handle_process_new_listing(event)
        results.append(result)
        
        if result['success']:
            print(f"     ✅ Queued for historical data fetch (position {result['queue_position']})")
        else:
            print(f"     ❌ Failed: {result.get('error', 'Unknown error')}")
        print()
    
    # ================================================================
    # 4. PROCESS PENDING FETCHES
    # ================================================================
    print("📋 STEP 4: PROCESS PENDING HISTORICAL DATA FETCHES")
    print("-" * 50)
    
    print(f"⏳ Processing {len(fetcher.pending_fetches)} pending historical data fetches...")
    print("This may take a few minutes depending on API rate limits...")
    print()
    
    # Process a batch manually for demo purposes
    if fetcher.pending_fetches:
        # Take first 3 for demo (to avoid long wait times)
        demo_batch = fetcher.pending_fetches[:3]
        fetcher.pending_fetches = fetcher.pending_fetches[3:]
        
        print(f"📦 Processing demo batch of {len(demo_batch)} coins:")
        print()
        
        for coin_info in demo_batch:
            print(f"📈 Fetching historical data for {coin_info['symbol']}...")
            
            try:
                dataset = await fetcher._fetch_coin_historical_data(coin_info)
                
                if dataset:
                    print(f"✅ Success: {dataset.data_points} data points from {len(dataset.sources)} sources")
                    print(f"   📊 Sources: {', '.join(dataset.sources)}")
                    print(f"   📅 Date range: {dataset.start_date.date()} to {dataset.end_date.date()}")
                    
                    # Calculate quality score
                    quality = await fetcher._calculate_data_quality(dataset)
                    print(f"   🏆 Data quality: {quality:.1%}")
                    print()
                else:
                    print(f"❌ Failed to fetch data for {coin_info['symbol']}")
                    print()
                
            except Exception as e:
                print(f"❌ Error fetching data for {coin_info['symbol']}: {e}")
                print()
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    # ================================================================
    # 5. DATABASE AND CSV EXPORTS
    # ================================================================
    print("📋 STEP 5: DATABASE AND CSV EXPORTS")
    print("-" * 50)
    
    # Check what data was saved
    stats = fetcher.get_statistics()
    print(f"📊 Historical Data Fetcher Statistics:")
    print(f"   💾 Total datasets created: {stats['total_datasets_created']}")
    print(f"   ✅ Successful fetches: {stats['successful_fetches']}")
    print(f"   ❌ Failed fetches: {stats['failed_fetches']}")
    print(f"   📈 Total data points: {stats['total_data_points']}")
    print(f"   📄 CSV files created: {stats['csv_files_created']}")
    print(f"   🔗 API calls today: {stats['api_calls_today']}")
    print(f"   🗄️ Datasets cached: {stats['datasets_cached']}")
    print(f"   ⏳ Pending fetches: {stats['pending_fetches']}")
    print()
    
    # Show CSV files created
    csv_dir = Path(config['cache_dir']) / 'csv_exports'
    if csv_dir.exists():
        csv_files = list(csv_dir.glob('*.csv'))
        ai_files = list(csv_dir.glob('*_ai_summary.json'))
        
        print(f"📄 CSV Export Files ({len(csv_files)} files):")
        for csv_file in csv_files:
            file_size = csv_file.stat().st_size
            print(f"   📊 {csv_file.name} ({file_size:,} bytes)")
        print()
        
        print(f"🧠 AI Summary Files ({len(ai_files)} files):")
        for ai_file in ai_files:
            file_size = ai_file.stat().st_size
            print(f"   🤖 {ai_file.name} ({file_size:,} bytes)")
        print()
    
    # ================================================================
    # 6. DEMONSTRATE CSV AND AI DATA STRUCTURE
    # ================================================================
    print("📋 STEP 6: DEMONSTRATE CSV AND AI DATA STRUCTURE")
    print("-" * 50)
    
    # Show sample of exported data if available
    if fetcher.historical_datasets:
        sample_coin_id = list(fetcher.historical_datasets.keys())[0]
        sample_dataset = fetcher.historical_datasets[sample_coin_id]
        
        print(f"📊 Sample Dataset: {sample_dataset.symbol} ({sample_dataset.name})")
        print(f"   🆔 Coin ID: {sample_dataset.coin_id}")
        print(f"   📈 Data points: {sample_dataset.data_points}")
        print(f"   🔗 Sources: {', '.join(sample_dataset.sources)}")
        print(f"   📅 Period: {sample_dataset.start_date.date()} to {sample_dataset.end_date.date()}")
        print()
        
        # Show sample OHLCV data
        if sample_dataset.ohlcv_data:
            print("📈 Sample OHLCV Data (first 3 entries):")
            for i, ohlcv in enumerate(sample_dataset.ohlcv_data[:3]):
                print(f"   {i+1}. Date: {ohlcv.date}")
                print(f"      Open: ${ohlcv.open:.6f}")
                print(f"      High: ${ohlcv.high:.6f}")
                print(f"      Low: ${ohlcv.low:.6f}")
                print(f"      Close: ${ohlcv.close:.6f}")
                print(f"      Volume: {ohlcv.volume:,.2f}")
                print(f"      Source: {ohlcv.source}")
                if ohlcv.exchange:
                    print(f"      Exchange: {ohlcv.exchange}")
                print()
        
        # Show AI summary if available
        ai_summary_path = csv_dir / f"{sample_dataset.symbol}_{sample_dataset.coin_id}_ai_summary.json"
        if ai_summary_path.exists():
            print("🧠 AI-Ready Data Summary:")
            with open(ai_summary_path, 'r') as f:
                ai_summary = json.load(f)
            
            price_stats = ai_summary.get('price_statistics', {})
            print(f"   💰 Price Change: {price_stats.get('price_change_pct', 0):.2f}%")
            print(f"   📊 Volatility: {price_stats.get('volatility', 0):.2f}%")
            print(f"   📈 Min Price: ${price_stats.get('min_price', 0):.6f}")
            print(f"   📈 Max Price: ${price_stats.get('max_price', 0):.6f}")
            
            ai_features = ai_summary.get('ai_features', {})
            print(f"   🔥 Trending Up: {ai_features.get('is_trending_up', False)}")
            print(f"   📊 High Volume: {ai_features.get('has_high_volume', False)}")
            print(f"   📈 Volatility Category: {ai_features.get('volatility_category', 'unknown')}")
            print(f"   🏆 Data Quality: {ai_features.get('data_quality_score', 0):.1%}")
            print()
    
    # ================================================================
    # 7. INTEGRATION WITH NEW LISTING DETECTOR
    # ================================================================
    print("📋 STEP 7: INTEGRATION WITH NEW LISTING DETECTOR")
    print("-" * 50)
    
    print("🔗 Integration Points:")
    print("   1. New Listing Detector emits 'process_new_listing' events")
    print("   2. Historical Data Fetcher automatically queues data fetching")
    print("   3. Background processing fetches OHLCV data from multiple sources")
    print("   4. Data is stored in SQLite database and exported to CSV")
    print("   5. AI-ready summaries are generated with technical indicators")
    print("   6. Quality scores ensure only reliable data is used")
    print()
    
    print("📊 Event Flow:")
    print("   New Coin Detected → Queue Historical Fetch → Fetch from CoinGecko")
    print("                                            → Fetch from Exchanges (CCXT)")
    print("                                            → Quality Assessment")
    print("                                            → SQLite Storage")
    print("                                            → CSV Export") 
    print("                                            → AI Summary Generation")
    print()
    
    # ================================================================
    # 8. PERFORMANCE AND EFFICIENCY
    # ================================================================
    print("📋 STEP 8: PERFORMANCE AND EFFICIENCY FEATURES")
    print("-" * 50)
    
    print("⚡ Performance Features:")
    print("   📊 Rate limiting: CoinGecko (50 calls/min), Exchanges (2 calls/sec)")
    print("   🔄 Background processing: Batch processing of pending fetches")
    print("   💾 Database caching: Avoid duplicate data fetching")
    print("   📈 Quality filtering: Only high-quality data (>80% complete)")
    print("   🧠 AI optimization: Pre-calculated indicators and features")
    print("   📄 Multiple formats: SQLite for queries, CSV for AI training")
    print()
    
    print("🛡️ Reliability Features:")
    print("   ❌ Error handling: Graceful failure with detailed logging")
    print("   🔄 Retry logic: Automatic retries for transient failures")
    print("   📊 Data validation: Completeness, consistency, timeliness checks")
    print("   🔍 Multi-source: CoinGecko + multiple exchanges for redundancy")
    print("   💾 Persistent storage: Data survives restarts and crashes")
    print()
    
    # ================================================================
    # 9. SHUTDOWN AND CLEANUP
    # ================================================================
    print("📋 STEP 9: SHUTDOWN AND CLEANUP")
    print("-" * 50)
    
    # Final statistics
    final_stats = fetcher.get_statistics()
    print("📊 Final Statistics:")
    for key, value in final_stats.items():
        if isinstance(value, (int, float)):
            print(f"   {key}: {value:,}")
        elif isinstance(value, list):
            print(f"   {key}: {', '.join(map(str, value))}")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Stop the module
    await fetcher.stop()
    print("✅ Historical Data Fetcher Module stopped successfully")
    print()
    
    # ================================================================
    # SUMMARY
    # ================================================================
    print("=" * 80)
    print("🎉 HISTORICAL DATA FETCHER DEMO COMPLETED")
    print("=" * 80)
    print()
    print("🏆 Demo Results:")
    print(f"   📊 Datasets created: {final_stats.get('total_datasets_created', 0)}")
    print(f"   ✅ Successful fetches: {final_stats.get('successful_fetches', 0)}")
    print(f"   📈 Total data points: {final_stats.get('total_data_points', 0)}")
    print(f"   📄 CSV files: {final_stats.get('csv_files_created', 0)}")
    print(f"   🔗 API calls: {final_stats.get('api_calls_today', 0)}")
    print()
    
    print("💡 Key Features Demonstrated:")
    print("   ✅ Automatic OHLCV data fetching for new listings")
    print("   ✅ Multi-source data collection (CoinGecko + Exchanges)")
    print("   ✅ SQLite database storage with full schema")
    print("   ✅ CSV export for AI/ML model training")
    print("   ✅ AI-ready data summaries with technical indicators")
    print("   ✅ Data quality assessment and filtering")
    print("   ✅ Rate limiting and error handling")
    print("   ✅ Background processing and queue management")
    print()
    
    print("🚀 Next Steps:")
    print("   1. Configure CoinGecko Pro API key for higher rate limits")
    print("   2. Integrate with main new listing detector module")
    print("   3. Connect to AI/ML pipeline for automated analysis")
    print("   4. Set up monitoring and alerting for data quality")
    print("   5. Scale to handle thousands of new listings per day")
    print()
    
    print("💾 Data Location:")
    print(f"   Database: {fetcher.db_path}")
    print(f"   CSV files: {fetcher.csv_dir}")
    print("   Ready for AI processing and backtesting!")
    print()

if __name__ == "__main__":
    print("Starting Historical Data Fetcher Module Demo...")
    print("This demo shows comprehensive OHLCV data fetching capabilities")
    print()
    
    try:
        asyncio.run(demo_historical_data_fetcher())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n�� Demo finished!") 