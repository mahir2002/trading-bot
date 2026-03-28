#!/usr/bin/env python3
"""
Pipeline Scheduler - Automated 24-hour update pipeline
Orchestrates the complete data collection and AI processing pipeline

Author: Trading Bot System
Date: 2025-01-22
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
import os
import json
import time

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore

# Import our modules
from modules.coin_listings_cex import CoinListingsCEX
from modules.coin_listings_dex import CoinListingsDEX
from modules.new_listing_detector import NewListingDetector
from modules.historical_data_fetcher import HistoricalDataFetcher
from modules.social_sentiment_analyzer import SocialSentimentAnalyzer
from modules.ai_models import AIModelManager

class PipelineScheduler:
    """
    Comprehensive pipeline scheduler that manages the 24-hour update cycle
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the pipeline scheduler"""
        self.config_path = config_path or "unified_trading_platform/config/scheduler_config.json"
        self.config = self._load_config()
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            job_defaults={
                'coalesce': False,
                'max_instances': 1,
                'misfire_grace_time': 3600  # 1 hour grace period
            }
        )
        
        # Initialize modules
        self.cex_module = None
        self.dex_module = None
        self.detector_module = None
        self.historical_module = None
        self.sentiment_module = None
        self.ai_module = None
        
        # Pipeline state
        self.pipeline_running = False
        self.last_run_timestamp = None
        self.pipeline_stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'average_duration': 0,
            'last_error': None
        }
        
        self.logger.info("🚀 Pipeline Scheduler initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scheduler configuration"""
        default_config = {
            "schedule": {
                "enabled": True,
                "hour": 2,  # Run at 2 AM
                "minute": 0,
                "timezone": "UTC"
            },
            "pipeline": {
                "steps": {
                    "fetch_cex_coins": True,
                    "fetch_dex_coins": True,
                    "detect_new_listings": True,
                    "fetch_historical_data": True,
                    "analyze_sentiment": True,
                    "run_ai_models": True
                },
                "timeout_minutes": 120,  # 2 hours max
                "retry_attempts": 3,
                "retry_delay": 300  # 5 minutes
            },
            "logging": {
                "level": "INFO",
                "file": "logs/pipeline_scheduler.log",
                "max_size_mb": 100,
                "backup_count": 5
            },
            "notifications": {
                "success": True,
                "failure": True,
                "channels": ["file", "console"]
            }
        }
        
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                return {**default_config, **user_config}
            else:
                # Create default config file
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}")
        
        return default_config
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_config = self.config.get('logging', {})
        log_file = log_config.get('file', 'logs/pipeline_scheduler.log')
        
        # Create logs directory
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get('max_size_mb', 100) * 1024 * 1024,
            backupCount=log_config.get('backup_count', 5)
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
    
    async def initialize_modules(self):
        """Initialize all pipeline modules"""
        try:
            self.logger.info("🔧 Initializing pipeline modules...")
            
            # Initialize CEX module
            from modules.coin_listings_cex import CEXCoinListingsModule
            self.cex_module = CEXCoinListingsModule()
            self.logger.info("✅ CEX module initialized")
            
            # Initialize DEX module  
            from modules.coin_listings_dex import DEXCoinListingsModule
            self.dex_module = DEXCoinListingsModule()
            self.logger.info("✅ DEX module initialized")
            
            # Initialize new listing detector
            from modules.new_listing_detector import NewListingDetectorModule
            self.detector_module = NewListingDetectorModule()
            self.logger.info("✅ New listing detector initialized")
            
            # Initialize historical data fetcher
            from modules.historical_data_fetcher import HistoricalDataFetcherModule
            self.historical_module = HistoricalDataFetcherModule()
            self.logger.info("✅ Historical data fetcher initialized")
            
            # Initialize sentiment analyzer
            from modules.social_sentiment_analyzer import SocialSentimentAnalyzer
            self.sentiment_module = SocialSentimentAnalyzer()
            self.logger.info("✅ Social sentiment analyzer initialized")
            
            # Initialize AI models
            from modules.ai_models import AIModelManager
            self.ai_module = AIModelManager()
            self.logger.info("✅ AI model manager initialized")
            
            self.logger.info("🎉 All modules initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize modules: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def run_full_pipeline(self):
        """Execute the complete update pipeline"""
        if self.pipeline_running:
            self.logger.warning("⚠️ Pipeline already running, skipping this execution")
            return
        
        start_time = datetime.now()
        self.pipeline_running = True
        pipeline_data = {}
        
        try:
            self.logger.info("🚀 Starting full pipeline execution")
            self.logger.info(f"⏰ Pipeline started at {start_time}")
            
            steps = self.config.get('pipeline', {}).get('steps', {})
            
            # Step 1: Fetch CEX coins
            if steps.get('fetch_cex_coins', True):
                await self._execute_step(
                    "fetch_cex_coins",
                    "🏦 Fetching CEX coin listings",
                    self._fetch_cex_coins,
                    pipeline_data
                )
            
            # Step 2: Fetch DEX coins
            if steps.get('fetch_dex_coins', True):
                await self._execute_step(
                    "fetch_dex_coins", 
                    "🔄 Fetching DEX coin listings",
                    self._fetch_dex_coins,
                    pipeline_data
                )
            
            # Step 3: Detect new listings
            if steps.get('detect_new_listings', True):
                await self._execute_step(
                    "detect_new_listings",
                    "🔍 Detecting new coin listings",
                    self._detect_new_listings,
                    pipeline_data
                )
            
            # Step 4: Fetch historical data
            if steps.get('fetch_historical_data', True):
                await self._execute_step(
                    "fetch_historical_data",
                    "📊 Fetching historical data for new coins",
                    self._fetch_historical_data,
                    pipeline_data
                )
            
            # Step 5: Analyze sentiment
            if steps.get('analyze_sentiment', True):
                await self._execute_step(
                    "analyze_sentiment",
                    "💭 Analyzing social sentiment",
                    self._analyze_sentiment,
                    pipeline_data
                )
            
            # Step 6: Run AI models
            if steps.get('run_ai_models', True):
                await self._execute_step(
                    "run_ai_models",
                    "🤖 Running AI models",
                    self._run_ai_models,
                    pipeline_data
                )
            
            # Pipeline completed successfully
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.pipeline_stats['total_runs'] += 1
            self.pipeline_stats['successful_runs'] += 1
            self.pipeline_stats['average_duration'] = (
                (self.pipeline_stats['average_duration'] * (self.pipeline_stats['total_runs'] - 1) + duration) 
                / self.pipeline_stats['total_runs']
            )
            self.last_run_timestamp = end_time
            
            self.logger.info(f"🎉 Pipeline completed successfully!")
            self.logger.info(f"⏱️ Total duration: {duration:.2f} seconds")
            self.logger.info(f"📊 Pipeline summary: {json.dumps(pipeline_data, indent=2)}")
            
            # Save pipeline results
            await self._save_pipeline_results(pipeline_data, start_time, end_time)
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.pipeline_stats['total_runs'] += 1
            self.pipeline_stats['failed_runs'] += 1
            self.pipeline_stats['last_error'] = str(e)
            
            self.logger.error(f"❌ Pipeline failed after {duration:.2f} seconds")
            self.logger.error(f"Error: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Save error details
            await self._save_error_report(e, start_time, end_time, pipeline_data)
            
        finally:
            self.pipeline_running = False
    
    async def _execute_step(self, step_name: str, description: str, step_function, pipeline_data: dict):
        """Execute a single pipeline step with error handling"""
        step_start = time.time()
        
        try:
            self.logger.info(f"▶️ {description}")
            result = await step_function()
            
            step_duration = time.time() - step_start
            pipeline_data[step_name] = {
                'status': 'success',
                'duration_seconds': step_duration,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ {description} completed in {step_duration:.2f}s")
            if result:
                self.logger.info(f"📋 Result: {result.get('summary', 'No summary available')}")
            
        except Exception as e:
            step_duration = time.time() - step_start
            pipeline_data[step_name] = {
                'status': 'failed',
                'duration_seconds': step_duration,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.error(f"❌ {description} failed after {step_duration:.2f}s: {e}")
            
            # Continue with other steps even if one fails
            if self.config.get('pipeline', {}).get('stop_on_error', False):
                raise
    
    async def _fetch_cex_coins(self) -> Dict[str, Any]:
        """Fetch coins from centralized exchanges"""
        if not self.cex_module:
            raise Exception("CEX module not initialized")
        
        # Get all listings from CEX
        cex_results = await self.cex_module.get_all_listings()
        
        return {
            'summary': f"Fetched {len(cex_results)} CEX listings",
            'exchanges': list(cex_results.keys()) if isinstance(cex_results, dict) else [],
            'total_symbols': len(cex_results) if isinstance(cex_results, list) else sum(len(v) for v in cex_results.values())
        }
    
    async def _fetch_dex_coins(self) -> Dict[str, Any]:
        """Fetch coins from decentralized exchanges"""
        if not self.dex_module:
            raise Exception("DEX module not initialized")
        
        # Get all listings from DEX
        dex_results = await self.dex_module.get_all_listings()
        
        return {
            'summary': f"Fetched DEX listings from multiple networks",
            'networks': list(dex_results.keys()) if isinstance(dex_results, dict) else [],
            'total_pairs': len(dex_results) if isinstance(dex_results, list) else sum(len(v) for v in dex_results.values())
        }
    
    async def _detect_new_listings(self) -> Dict[str, Any]:
        """Detect new coin listings"""
        if not self.detector_module:
            raise Exception("New listing detector not initialized")
        
        # Run new listing detection
        new_listings = await self.detector_module.detect_new_listings()
        
        return {
            'summary': f"Detected {len(new_listings)} new listings",
            'new_coins': [coin.get('symbol', 'Unknown') for coin in new_listings[:10]],  # First 10
            'total_new': len(new_listings),
            'high_priority': len([c for c in new_listings if c.get('priority', 0) > 80])
        }
    
    async def _fetch_historical_data(self) -> Dict[str, Any]:
        """Fetch historical data for new coins"""
        if not self.historical_module:
            raise Exception("Historical data fetcher not initialized")
        
        # Get new coins that need historical data
        new_coins_file = "data/new_coins_for_ai.json"
        if not Path(new_coins_file).exists():
            return {'summary': 'No new coins file found, skipping historical data fetch'}
        
        with open(new_coins_file, 'r') as f:
            new_coins = json.load(f)
        
        if not new_coins:
            return {'summary': 'No new coins to process'}
        
        # Fetch historical data for each new coin
        processed_count = 0
        for coin in new_coins[:20]:  # Limit to first 20 to avoid timeout
            try:
                symbol = coin.get('symbol', '')
                if symbol:
                    await self.historical_module.fetch_historical_data(symbol, days=30)
                    processed_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to fetch historical data for {symbol}: {e}")
        
        return {
            'summary': f"Fetched historical data for {processed_count} new coins",
            'processed': processed_count,
            'total_new_coins': len(new_coins)
        }
    
    async def _analyze_sentiment(self) -> Dict[str, Any]:
        """Analyze social sentiment for new coins"""
        if not self.sentiment_module:
            raise Exception("Sentiment analyzer not initialized")
        
        # Get new coins for sentiment analysis
        new_coins_file = "data/new_coins_for_ai.json"
        if not Path(new_coins_file).exists():
            return {'summary': 'No new coins file found, skipping sentiment analysis'}
        
        with open(new_coins_file, 'r') as f:
            new_coins = json.load(f)
        
        if not new_coins:
            return {'summary': 'No new coins to analyze'}
        
        # Analyze sentiment for each new coin
        analyzed_count = 0
        for coin in new_coins[:10]:  # Limit to avoid API rate limits
            try:
                symbol = coin.get('symbol', '')
                if symbol:
                    sentiment_data = await self.sentiment_module.analyze_coin_sentiment(symbol)
                    analyzed_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to analyze sentiment for {symbol}: {e}")
        
        return {
            'summary': f"Analyzed sentiment for {analyzed_count} new coins",
            'analyzed': analyzed_count,
            'total_new_coins': len(new_coins)
        }
    
    async def _run_ai_models(self) -> Dict[str, Any]:
        """Run AI models on collected data"""
        if not self.ai_module:
            raise Exception("AI model manager not initialized")
        
        # Run AI models on new coin data
        try:
            ai_results = await self.ai_module.process_new_coins()
            
            return {
                'summary': f"AI models processed data successfully",
                'models_run': ai_results.get('models_run', 0),
                'predictions_made': ai_results.get('predictions_made', 0),
                'recommendations': ai_results.get('recommendations', [])[:5]  # First 5
            }
        except Exception as e:
            self.logger.warning(f"AI model processing failed: {e}")
            return {
                'summary': 'AI model processing failed',
                'error': str(e)
            }
    
    async def _save_pipeline_results(self, pipeline_data: dict, start_time: datetime, end_time: datetime):
        """Save pipeline results to file"""
        results_dir = Path("data/pipeline_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = results_dir / f"pipeline_result_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        full_results = {
            'pipeline_id': f"pipeline_{start_time.strftime('%Y%m%d_%H%M%S')}",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'status': 'success',
            'steps': pipeline_data,
            'stats': self.pipeline_stats
        }
        
        with open(results_file, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        self.logger.info(f"💾 Pipeline results saved to {results_file}")
    
    async def _save_error_report(self, error: Exception, start_time: datetime, end_time: datetime, pipeline_data: dict):
        """Save error report to file"""
        errors_dir = Path("data/pipeline_errors")
        errors_dir.mkdir(parents=True, exist_ok=True)
        
        error_file = errors_dir / f"pipeline_error_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        
        error_report = {
            'pipeline_id': f"pipeline_{start_time.strftime('%Y%m%d_%H%M%S')}",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'status': 'failed',
            'error': str(error),
            'traceback': traceback.format_exc(),
            'completed_steps': pipeline_data,
            'stats': self.pipeline_stats
        }
        
        with open(error_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        self.logger.error(f"💾 Error report saved to {error_file}")
    
    def start_scheduler(self):
        """Start the pipeline scheduler"""
        try:
            schedule_config = self.config.get('schedule', {})
            
            if not schedule_config.get('enabled', True):
                self.logger.info("📋 Scheduler is disabled in configuration")
                return
            
            # Add the main pipeline job
            self.scheduler.add_job(
                func=self.run_full_pipeline,
                trigger=CronTrigger(
                    hour=schedule_config.get('hour', 2),
                    minute=schedule_config.get('minute', 0),
                    timezone=schedule_config.get('timezone', 'UTC')
                ),
                id='full_pipeline',
                name='Full Update Pipeline',
                replace_existing=True
            )
            
            # Add a health check job every hour
            self.scheduler.add_job(
                func=self._health_check,
                trigger=IntervalTrigger(hours=1),
                id='health_check',
                name='Pipeline Health Check',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            
            next_run = self.scheduler.get_job('full_pipeline').next_run_time
            self.logger.info(f"📅 Pipeline scheduler started")
            self.logger.info(f"⏰ Next pipeline run: {next_run}")
            self.logger.info(f"🔄 Health checks every hour")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start scheduler: {e}")
            raise
    
    async def _health_check(self):
        """Perform health check on the pipeline system"""
        self.logger.info("🏥 Performing pipeline health check")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'scheduler_running': self.scheduler.running,
            'pipeline_running': self.pipeline_running,
            'last_run': self.last_run_timestamp.isoformat() if self.last_run_timestamp else None,
            'stats': self.pipeline_stats,
            'next_run': None
        }
        
        # Get next run time
        next_job = self.scheduler.get_job('full_pipeline')
        if next_job:
            health_status['next_run'] = next_job.next_run_time.isoformat()
        
        # Save health status
        health_dir = Path("data/health_checks")
        health_dir.mkdir(parents=True, exist_ok=True)
        
        health_file = health_dir / "pipeline_health.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)
        
        self.logger.info(f"💚 Health check completed - Status: {'HEALTHY' if self.scheduler.running else 'UNHEALTHY'}")
    
    def stop_scheduler(self):
        """Stop the pipeline scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("🛑 Pipeline scheduler stopped")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        next_run = None
        if self.scheduler.running:
            next_job = self.scheduler.get_job('full_pipeline')
            if next_job:
                next_run = next_job.next_run_time.isoformat()
        
        return {
            'scheduler_running': self.scheduler.running,
            'pipeline_running': self.pipeline_running,
            'last_run': self.last_run_timestamp.isoformat() if self.last_run_timestamp else None,
            'next_run': next_run,
            'stats': self.pipeline_stats,
            'config': self.config
        }
    
    async def run_pipeline_now(self):
        """Trigger pipeline execution immediately"""
        if self.pipeline_running:
            self.logger.warning("⚠️ Pipeline is already running")
            return False
        
        self.logger.info("🚀 Triggering immediate pipeline execution")
        asyncio.create_task(self.run_full_pipeline())
        return True


async def main():
    """Main function for testing the scheduler"""
    scheduler = PipelineScheduler()
    
    try:
        # Initialize modules
        await scheduler.initialize_modules()
        
        # Start scheduler
        scheduler.start_scheduler()
        
        # Keep running
        self.logger.info("✅ Pipeline scheduler is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logging.info("📋 Received shutdown signal")
    except Exception as e:
        logging.error(f"❌ Scheduler error: {e}")
    finally:
        scheduler.stop_scheduler()
        logging.info("👋 Pipeline scheduler shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 