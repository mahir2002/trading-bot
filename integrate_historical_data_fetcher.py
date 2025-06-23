#!/usr/bin/env python3
"""
🔗 Historical Data Fetcher Integration
Integrates the Historical Data Fetcher with the New Listing Detector Module
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import required modules
from unified_trading_platform.modules.new_listing_detector import NewListingDetectorModule
from unified_trading_platform.modules.historical_data_fetcher import HistoricalDataFetcherModule
from unified_trading_platform.core.base_module import ModuleEvent

async def integrate_historical_data_fetcher():
    """
    Complete Integration Example
    
    Shows how to:
    1. Set up both modules
    2. Connect new listing events to historical data fetching
    3. Process the complete pipeline
    4. Demonstrate AI-ready output
    """
    
    print("=" * 80)
    print("🔗 HISTORICAL DATA FETCHER INTEGRATION")
    print("=" * 80)
    print()
    
    # ================================================================
    # 1. INITIALIZE BOTH MODULES
    # ================================================================
    print("📋 STEP 1: INITIALIZE MODULES")
    print("-" * 50)
    
    # New Listing Detector configuration
    detector_config = {
        'enable_cex_detection': True,
        'enable_dex_detection': True,
        'enable_coingecko_detection': True,
        'enable_geckoterminal_scraping': True,
        'cache_duration_hours': 24,
        'min_market_cap_usd': 100000,
        'max_new_listings_per_day': 50,
        'coingecko_api_key': '',  # Add your API key
        'cache_dir': 'data/new_listings'
    }
    
    # Historical Data Fetcher configuration  
    fetcher_config = {
        'coingecko_api_key': '',  # Same API key
        'data_retention_days': 30,
        'enable_ccxt_fetching': True,
        'enable_csv_export': True,
        'data_quality_threshold': 0.8,
        'cache_dir': 'data/historical_data'
    }
    
    # Create and initialize modules
    print("🔍 Initializing New Listing Detector...")
    detector = NewListingDetectorModule("new_listing_detector", detector_config)
    await detector.initialize()
    await detector.start()
    
    print("📈 Initializing Historical Data Fetcher...")
    fetcher = HistoricalDataFetcherModule("historical_data_fetcher", fetcher_config)
    await fetcher.initialize()
    await fetcher.start()
    
    print("✅ Both modules initialized successfully")
    print()
    
    # ================================================================
    # 2. SET UP EVENT ROUTING
    # ================================================================
    print("📋 STEP 2: SET UP EVENT ROUTING")
    print("-" * 50)
    
    async def route_new_listing_to_historical_fetcher(event_data):
        """Route new listing events to historical data fetcher"""
        try:
            # Create event for historical data fetcher
            historical_event = ModuleEvent(
                event_type='process_new_listing',
                data=event_data,
                timestamp=datetime.now()
            )
            
            # Process the event
            result = await fetcher._handle_process_new_listing(historical_event)
            
            print(f"📈 Routed {event_data.get('symbol', 'unknown')} to historical fetcher: {result['success']}")
            return result
            
        except Exception as e:
            print(f"❌ Error routing event: {e}")
            return {'success': False, 'error': str(e)}
    
    print("🔗 Event routing configured")
    print("   New Listing Detected → Historical Data Fetch Queued")
    print()
    
    # ================================================================
    # 3. SIMULATE COMPLETE PIPELINE
    # ================================================================
    print("📋 STEP 3: SIMULATE COMPLETE PIPELINE")
    print("-" * 50)
    
    # Create sample new listings (simulating detector output)
    sample_new_listings = [
        {
            'coin_id': 'ethereum',
            'symbol': 'ETH',
            'name': 'Ethereum', 
            'coingecko_id': 'ethereum',
            'market_cap_usd': 300000000000,
            'volume_24h_usd': 15000000000,
            'price_usd': 2500.0,
            'priority': 'high',
            'risk_score': 85,
            'detection_sources': ['coingecko', 'binance'],
            'detected_at': datetime.now().isoformat()
        },
        {
            'coin_id': 'cardano',
            'symbol': 'ADA',
            'name': 'Cardano',
            'coingecko_id': 'cardano', 
            'market_cap_usd': 15000000000,
            'volume_24h_usd': 800000000,
            'price_usd': 0.45,
            'priority': 'medium',
            'risk_score': 72,
            'detection_sources': ['coingecko', 'kraken'],
            'detected_at': datetime.now().isoformat()
        },
        {
            'coin_id': 'polygon',
            'symbol': 'MATIC',
            'name': 'Polygon',
            'coingecko_id': 'matic-network',
            'market_cap_usd': 8000000000,
            'volume_24h_usd': 500000000,
            'price_usd': 0.95,
            'priority': 'medium',
            'risk_score': 68,
            'detection_sources': ['coingecko', 'binance', 'coinbase'],
            'detected_at': datetime.now().isoformat()
        }
    ]
    
    print(f"🪙 Processing {len(sample_new_listings)} new listings through complete pipeline:")
    print()
    
    # Process each new listing
    routed_coins = []
    for i, listing in enumerate(sample_new_listings, 1):
        print(f"  {i}. Processing {listing['symbol']} ({listing['name']})")
        print(f"     💰 Market Cap: ${listing['market_cap_usd']:,}")
        print(f"     📊 Volume 24h: ${listing['volume_24h_usd']:,}")
        print(f"     💲 Price: ${listing['price_usd']}")
        print(f"     🔥 Priority: {listing['priority']}")
        print(f"     ⚠️ Risk Score: {listing['risk_score']}/100")
        
        # Route to historical data fetcher
        result = await route_new_listing_to_historical_fetcher(listing)
        
        if result['success']:
            print(f"     ✅ Queued for historical data fetch")
            routed_coins.append(listing)
        else:
            print(f"     ❌ Failed to queue: {result.get('error', 'Unknown')}")
        print()
    
    # ================================================================
    # 4. PROCESS HISTORICAL DATA FETCHES
    # ================================================================
    print("📋 STEP 4: PROCESS HISTORICAL DATA FETCHES")
    print("-" * 50)
    
    print(f"⏳ Processing {len(fetcher.pending_fetches)} queued historical data fetches...")
    print()
    
    # Process pending fetches (limiting to first 2 for demo)
    if fetcher.pending_fetches:
        demo_batch = fetcher.pending_fetches[:2]
        fetcher.pending_fetches = fetcher.pending_fetches[2:]
        
        for coin_info in demo_batch:
            print(f"📈 Fetching 30-day OHLCV data for {coin_info['symbol']}...")
            
            try:
                dataset = await fetcher._fetch_coin_historical_data(coin_info)
                
                if dataset:
                    quality = await fetcher._calculate_data_quality(dataset)
                    print(f"✅ Successfully fetched historical data:")
                    print(f"   📊 Data points: {dataset.data_points}")
                    print(f"   🔗 Sources: {', '.join(dataset.sources)}")
                    print(f"   📅 Period: {dataset.start_date.date()} to {dataset.end_date.date()}")
                    print(f"   🏆 Quality: {quality:.1%}")
                    
                    # Show CSV file created
                    csv_file = fetcher.csv_dir / f"{dataset.symbol}_{dataset.coin_id}_30d_ohlcv.csv"
                    if csv_file.exists():
                        file_size = csv_file.stat().st_size
                        print(f"   📄 CSV: {csv_file.name} ({file_size:,} bytes)")
                    
                    # Show AI summary
                    ai_file = fetcher.csv_dir / f"{dataset.symbol}_{dataset.coin_id}_ai_summary.json"
                    if ai_file.exists():
                        print(f"   🧠 AI Summary: Generated with technical indicators")
                        
                        # Load and show key AI features
                        with open(ai_file, 'r') as f:
                            ai_data = json.load(f)
                        
                        ai_features = ai_data.get('ai_features', {})
                        price_stats = ai_data.get('price_statistics', {})
                        
                        print(f"       💰 Price Change: {price_stats.get('price_change_pct', 0):.2f}%")
                        print(f"       📊 Volatility: {ai_features.get('volatility_category', 'unknown')}")
                        print(f"       🔥 Trending: {'Up' if ai_features.get('is_trending_up') else 'Down'}")
                        print(f"       📈 High Volume: {'Yes' if ai_features.get('has_high_volume') else 'No'}")
                    
                    print()
                else:
                    print(f"❌ Failed to fetch data for {coin_info['symbol']}")
                    print()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                print()
            
            # Delay between requests
            await asyncio.sleep(1)
    
    # ================================================================
    # 5. DEMONSTRATE INTEGRATED DATA FLOW
    # ================================================================
    print("📋 STEP 5: INTEGRATED DATA FLOW DEMONSTRATION")
    print("-" * 50)
    
    # Show combined statistics
    detector_stats = detector.get_statistics()
    fetcher_stats = fetcher.get_statistics()
    
    print("📊 New Listing Detector Stats:")
    print(f"   🔍 Total snapshots: {detector_stats.get('total_snapshots_created', 0)}")
    print(f"   🆕 New listings found: {detector_stats.get('total_new_listings', 0)}")
    print(f"   🔗 API calls: {detector_stats.get('api_calls_today', 0)}")
    print()
    
    print("📊 Historical Data Fetcher Stats:")
    print(f"   📈 Datasets created: {fetcher_stats.get('total_datasets_created', 0)}")
    print(f"   ✅ Successful fetches: {fetcher_stats.get('successful_fetches', 0)}")
    print(f"   📄 CSV files: {fetcher_stats.get('csv_files_created', 0)}")
    print(f"   🔗 API calls: {fetcher_stats.get('api_calls_today', 0)}")
    print()
    
    # ================================================================
    # 6. AI-READY DATA STRUCTURE
    # ================================================================
    print("📋 STEP 6: AI-READY DATA STRUCTURE")
    print("-" * 50)
    
    print("🧠 Complete AI Pipeline Output:")
    print()
    
    # Show structure of final AI data
    if fetcher.historical_datasets:
        sample_coin = list(fetcher.historical_datasets.keys())[0]
        dataset = fetcher.historical_datasets[sample_coin]
        
        print(f"📊 Example: {dataset.symbol} ({dataset.name})")
        print()
        
        print("🗄️ Database Schema:")
        print("   📊 historical_datasets table - metadata and summary")
        print("   📈 ohlcv_data table - timestamped price/volume data")
        print("   🏆 data_quality_metrics table - quality scores")
        print()
        
        print("📄 CSV Format (AI Training Ready):")
        print("   Columns: date, timestamp, open, high, low, close, volume, source, symbol, exchange")
        print("   📅 Time-ordered data for technical analysis")
        print("   🔗 Multi-source data for reliability")
        print()
        
        print("🧠 AI Summary Format:")
        print("   💰 Price statistics (change %, volatility, min/max)")
        print("   📊 Volume statistics (daily avg, total, peaks)")
        print("   📈 Technical indicators (SMA, RSI, momentum)")
        print("   🤖 AI features (trend direction, volume signals, volatility category)")
        print("   🏆 Data quality score (completeness, consistency, timeliness)")
        print()
    
    # ================================================================
    # 7. PRODUCTION DEPLOYMENT GUIDE
    # ================================================================
    print("📋 STEP 7: PRODUCTION DEPLOYMENT GUIDE")
    print("-" * 50)
    
    print("🚀 Production Integration Steps:")
    print()
    
    print("1. 🔧 Configuration:")
    print("   - Add CoinGecko Pro API key for higher rate limits")
    print("   - Configure database connection strings") 
    print("   - Set up monitoring and alerting")
    print("   - Configure rate limiting based on API plans")
    print()
    
    print("2. 🔗 Event System Integration:")
    print("   - Register historical fetcher as event listener")
    print("   - Set up event routing in main platform")
    print("   - Configure retry and error handling")
    print("   - Add circuit breakers for API failures")
    print()
    
    print("3. 📊 Data Pipeline:")
    print("   - Set up automated data quality monitoring")
    print("   - Configure AI model training triggers")
    print("   - Set up data archival and cleanup")
    print("   - Add real-time data streaming")
    print()
    
    print("4. 🔍 Monitoring:")
    print("   - API call rate monitoring")
    print("   - Data quality alerts")
    print("   - Processing latency tracking")
    print("   - Storage capacity monitoring")
    print()
    
    # ================================================================
    # 8. CLEANUP
    # ================================================================
    print("📋 STEP 8: CLEANUP")
    print("-" * 50)
    
    # Stop modules
    await detector.stop()
    await fetcher.stop()
    
    print("✅ All modules stopped successfully")
    print()
    
    # Show final data locations
    print("💾 Final Data Locations:")
    print(f"   🔍 New Listings DB: {detector.db_path}")
    print(f"   📈 Historical Data DB: {fetcher.db_path}")
    print(f"   📄 CSV Exports: {fetcher.csv_dir}")
    print(f"   🧠 AI Summaries: {fetcher.csv_dir}/*_ai_summary.json")
    print()
    
    # ================================================================
    # SUMMARY
    # ================================================================
    print("=" * 80)
    print("🎉 INTEGRATION DEMO COMPLETED")
    print("=" * 80)
    print()
    
    print("✅ Successfully Demonstrated:")
    print("   🔍 New listing detection and processing")
    print("   📈 Automatic historical data fetching")
    print("   💾 Multi-format data storage (SQLite + CSV)")
    print("   🧠 AI-ready data preparation")
    print("   🏆 Data quality assessment")
    print("   🔗 Complete event-driven pipeline")
    print()
    
    print("🚀 Ready for:")
    print("   🤖 AI/ML model training")
    print("   📊 Technical analysis")
    print("   💹 Backtesting strategies")
    print("   🔥 Real-time trading decisions")
    print()
    
    print("📈 Business Impact:")
    print("   💰 First-mover advantage on new listings")
    print("   🧠 AI-powered opportunity detection") 
    print("   📊 Comprehensive historical context")
    print("   🔍 Automated market intelligence")
    print()

async def create_unified_config():
    """Create a unified configuration file for both modules"""
    
    config = {
        'modules': {
            'new_listing_detector': {
                'enable_cex_detection': True,
                'enable_dex_detection': True,
                'enable_coingecko_detection': True,
                'enable_geckoterminal_scraping': True,
                'cache_duration_hours': 24,
                'min_market_cap_usd': 100000,
                'max_new_listings_per_day': 50,
                'coingecko_api_key': '${COINGECKO_API_KEY}',
                'cache_dir': 'data/new_listings'
            },
            'historical_data_fetcher': {
                'coingecko_api_key': '${COINGECKO_API_KEY}',
                'data_retention_days': 30,
                'enable_ccxt_fetching': True,
                'enable_csv_export': True,
                'data_quality_threshold': 0.8,
                'cache_dir': 'data/historical_data'
            }
        },
        'event_routing': {
            'new_listing_detected': ['historical_data_fetcher.process_new_listing'],
            'historical_data_ready': ['ai_processor.analyze_new_coin']
        },
        'rate_limits': {
            'coingecko_calls_per_minute': 50,
            'exchange_calls_per_second': 2,
            'max_concurrent_fetches': 5
        },
        'monitoring': {
            'enable_health_checks': True,
            'health_check_interval_seconds': 60,
            'enable_performance_metrics': True,
            'enable_alerting': True
        }
    }
    
    # Save configuration
    config_path = Path('integrated_historical_data_config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"📝 Created unified configuration: {config_path}")
    return config

if __name__ == "__main__":
    print("🔗 Starting Historical Data Fetcher Integration Demo...")
    print("This demonstrates the complete pipeline from new listing detection to AI-ready data")
    print()
    
    try:
        # Run the integration demo
        asyncio.run(integrate_historical_data_fetcher())
        
        # Create configuration file
        print("\n📝 Creating unified configuration file...")
        asyncio.run(create_unified_config())
        
    except KeyboardInterrupt:
        print("\n🛑 Integration demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Integration demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Integration demo finished!") 