#!/usr/bin/env python3
"""
Pipeline Scheduler Demo
Demonstrates the automated pipeline scheduler functionality

Author: Trading Bot System
Date: 2025-01-22
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_trading_platform.core.pipeline_scheduler import PipelineScheduler

async def demo_scheduler():
    """Demonstrate the pipeline scheduler functionality"""
    print("🚀 Pipeline Scheduler Demo")
    print("=" * 50)
    
    # Initialize scheduler
    scheduler = PipelineScheduler()
    
    try:
        print("\n📋 Scheduler Configuration:")
        config = scheduler.config
        print(f"   📅 Schedule: Daily at {config['schedule']['hour']:02d}:{config['schedule']['minute']:02d} {config['schedule']['timezone']}")
        print(f"   ⏱️ Timeout: {config['pipeline']['timeout_minutes']} minutes")
        print(f"   🔄 Retry attempts: {config['pipeline']['retry_attempts']}")
        print(f"   📝 Log file: {config['logging']['file']}")
        
        print("\n🔧 Pipeline Steps Enabled:")
        for step, enabled in config['pipeline']['steps'].items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {step.replace('_', ' ').title()}")
        
        print("\n🎯 Testing Pipeline Execution...")
        print("   Note: This will run the full pipeline once for demonstration")
        
        # Run pipeline once
        await scheduler.run_full_pipeline()
        
        print("\n📊 Pipeline Statistics:")
        stats = scheduler.pipeline_stats
        print(f"   📈 Total runs: {stats['total_runs']}")
        print(f"   ✅ Successful runs: {stats['successful_runs']}")
        print(f"   ❌ Failed runs: {stats['failed_runs']}")
        print(f"   ⏱️ Average duration: {stats['average_duration']:.2f} seconds")
        if stats['last_error']:
            print(f"   🚨 Last error: {stats['last_error']}")
        
        print("\n📅 Starting Scheduler (Demo Mode)...")
        print("   The scheduler is now running and will execute the pipeline daily")
        print("   Press Ctrl+C to stop the demo")
        
        # Start the scheduler
        scheduler.start_scheduler()
        
        # Show status
        status = scheduler.get_pipeline_status()
        print(f"\n🔄 Scheduler Status:")
        print(f"   📡 Running: {status['scheduler_running']}")
        print(f"   🔄 Pipeline active: {status['pipeline_running']}")
        print(f"   ⏰ Next run: {status['next_run']}")
        print(f"   📅 Last run: {status['last_run'] or 'Never'}")
        
        # Wait for a bit to show it's running
        print("\n⏳ Scheduler is running... (waiting 30 seconds for demo)")
        await asyncio.sleep(30)
        
        # Test immediate execution
        print("\n🚀 Testing immediate pipeline execution...")
        triggered = await scheduler.run_pipeline_now()
        if triggered:
            print("   ✅ Pipeline execution triggered successfully")
            print("   ⏳ Waiting for execution to complete...")
            
            # Wait for pipeline to complete
            while scheduler.pipeline_running:
                await asyncio.sleep(5)
                print("   🔄 Pipeline still running...")
            
            print("   🎉 Pipeline execution completed!")
        else:
            print("   ⚠️ Pipeline was already running")
        
        print("\n📊 Final Statistics:")
        final_stats = scheduler.pipeline_stats
        print(f"   📈 Total runs: {final_stats['total_runs']}")
        print(f"   ✅ Successful runs: {final_stats['successful_runs']}")
        print(f"   ❌ Failed runs: {final_stats['failed_runs']}")
        print(f"   ⏱️ Average duration: {final_stats['average_duration']:.2f} seconds")
        
        print("\n💾 Checking Generated Files:")
        
        # Check for pipeline results
        results_dir = Path("data/pipeline_results")
        if results_dir.exists():
            result_files = list(results_dir.glob("*.json"))
            print(f"   📊 Pipeline results: {len(result_files)} files")
            if result_files:
                latest = max(result_files, key=lambda f: f.stat().st_mtime)
                print(f"   📄 Latest result: {latest.name}")
        
        # Check for error reports
        errors_dir = Path("data/pipeline_errors")
        if errors_dir.exists():
            error_files = list(errors_dir.glob("*.json"))
            print(f"   🚨 Error reports: {len(error_files)} files")
        
        # Check for health checks
        health_dir = Path("data/health_checks")
        if health_dir.exists():
            health_file = health_dir / "pipeline_health.json"
            if health_file.exists():
                print(f"   💚 Health status: Available")
        
        # Check log file
        log_file = Path(scheduler.config['logging']['file'])
        if log_file.exists():
            print(f"   📝 Log file: {log_file} ({log_file.stat().st_size / 1024:.1f} KB)")
        
        print("\n🎉 Demo completed successfully!")
        print("   The scheduler would continue running in production mode")
        print("   All pipeline steps were tested and logged")
        
    except KeyboardInterrupt:
        print("\n📋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the scheduler
        scheduler.stop_scheduler()
        print("\n👋 Pipeline scheduler stopped")

def main():
    """Main function"""
    try:
        asyncio.run(demo_scheduler())
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 