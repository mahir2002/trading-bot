#!/usr/bin/env python3
"""
Production Pipeline Scheduler Launcher
Starts the automated 24-hour update pipeline scheduler

Author: Trading Bot System
Date: 2025-01-22
"""

import asyncio
import sys
import os
import signal
import logging
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_trading_platform.core.pipeline_scheduler import PipelineScheduler

class PipelineSchedulerLauncher:
    """Production launcher for the pipeline scheduler"""
    
    def __init__(self):
        self.scheduler = None
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n📋 Received signal {signum}, initiating graceful shutdown...")
            if self.scheduler:
                self.scheduler.stop_scheduler()
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_production_scheduler(self):
        """Start the production pipeline scheduler"""
        print("🚀 Starting Pipeline Scheduler - Production Mode")
        print("=" * 60)
        
        try:
            # Initialize scheduler
            print("🔧 Initializing pipeline scheduler...")
            self.scheduler = PipelineScheduler()
            
            # Display configuration
            config = self.scheduler.config
            print(f"\n📋 Configuration:")
            print(f"   📅 Schedule: Daily at {config['schedule']['hour']:02d}:{config['schedule']['minute']:02d} {config['schedule']['timezone']}")
            print(f"   ⏱️ Timeout: {config['pipeline']['timeout_minutes']} minutes")
            print(f"   🔄 Retry attempts: {config['pipeline']['retry_attempts']}")
            print(f"   📝 Log file: {config['logging']['file']}")
            print(f"   🛑 Stop on error: {config['pipeline'].get('stop_on_error', False)}")
            
            # Show enabled steps
            print(f"\n🔧 Pipeline Steps:")
            for step, enabled in config['pipeline']['steps'].items():
                status = "✅" if enabled else "❌"
                print(f"   {status} {step.replace('_', ' ').title()}")
            
            # Start the scheduler
            print(f"\n📅 Starting scheduler...")
            self.scheduler.start_scheduler()
            
            # Show status
            status = self.scheduler.get_pipeline_status()
            print(f"\n🔄 Scheduler Status:")
            print(f"   📡 Running: {status['scheduler_running']}")
            print(f"   ⏰ Next run: {status['next_run']}")
            print(f"   📅 Last run: {status['last_run'] or 'Never'}")
            
            # Check directories
            self._ensure_directories()
            
            print(f"\n✅ Pipeline scheduler is now running in production mode")
            print(f"   📊 Pipeline will run daily at {config['schedule']['hour']:02d}:{config['schedule']['minute']:02d} {config['schedule']['timezone']}")
            print(f"   🏥 Health checks every hour")
            print(f"   📝 All activities logged to: {config['logging']['file']}")
            print(f"   📁 Results saved to: data/pipeline_results/")
            print(f"   🚨 Errors logged to: data/pipeline_errors/")
            print(f"\n⚠️  Press Ctrl+C to stop the scheduler gracefully")
            
            # Keep running
            self.running = True
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
                # Periodic status update (every 6 hours)
                if self.running:
                    await self._periodic_status_update()
            
        except Exception as e:
            print(f"❌ Failed to start scheduler: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            "data/pipeline_results",
            "data/pipeline_errors", 
            "data/health_checks",
            "logs"
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Created/verified {len(dirs)} data directories")
    
    async def _periodic_status_update(self):
        """Provide periodic status updates"""
        try:
            if not self.scheduler:
                return
                
            status = self.scheduler.get_pipeline_status()
            stats = self.scheduler.pipeline_stats
            
            # Log status every 6 hours (360 minutes)
            # This is a simple check - in production you'd use a proper timer
            if hasattr(self, '_last_status_time'):
                from datetime import datetime, timedelta
                if datetime.now() - self._last_status_time < timedelta(hours=6):
                    return
            
            self._last_status_time = getattr(self, '_last_status_time', None) or datetime.now()
            
            logging.info("📊 Periodic Status Update:")
            logging.info(f"   📡 Scheduler running: {status['scheduler_running']}")
            logging.info(f"   🔄 Pipeline active: {status['pipeline_running']}")
            logging.info(f"   ⏰ Next run: {status['next_run']}")
            logging.info(f"   📈 Total runs: {stats['total_runs']}")
            logging.info(f"   ✅ Successful: {stats['successful_runs']}")
            logging.info(f"   ❌ Failed: {stats['failed_runs']}")
            
        except Exception as e:
            logging.error(f"Status update error: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        print("\n🛑 Stopping pipeline scheduler...")
        if self.scheduler:
            self.scheduler.stop_scheduler()
        self.running = False
        print("👋 Pipeline scheduler stopped")

async def main():
    """Main function"""
    launcher = PipelineSchedulerLauncher()
    
    try:
        success = await launcher.start_production_scheduler()
        if not success:
            return 1
    except KeyboardInterrupt:
        print("\n📋 Received shutdown signal")
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1
    finally:
        launcher.stop()
    
    return 0

if __name__ == "__main__":
    # Set up basic logging for the launcher
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scheduler_launcher.log'),
            logging.StreamHandler()
        ]
    )
    
    exit(asyncio.run(main())) 