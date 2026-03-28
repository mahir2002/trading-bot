#!/usr/bin/env python3
"""
NTP Synchronization System Live Demo
Real-time time synchronization demonstration for AI Trading Bot
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from ntp_synchronization_system import (
    NTPSynchronizationSystem, 
    TimeStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NTPDemo:
    """Live demonstration of NTP synchronization capabilities."""
    
    def __init__(self):
        """Initialize the NTP demo."""
        self.ntp_system = NTPSynchronizationSystem()
        
    async def run_demo(self):
        """Run NTP synchronization demo."""
        print("🕐 NTP Synchronization System - Live Demo")
        print("=" * 80)
        
        # Initial sync
        print("\n🌐 Performing NTP synchronization...")
        sync_results = await self.ntp_system.perform_multi_server_sync()
        
        print(f"✅ Synchronized with {len(sync_results)} servers")
        
        # Show results
        for sync in sync_results:
            if sync.status != TimeStatus.UNREACHABLE:
                status = "✅" if sync.status == TimeStatus.SYNCHRONIZED else "⚠️"
                print(f"   {status} {sync.server}: {sync.offset:.2f}ms offset")
        
        # Health report
        health_report = self.ntp_system.generate_ntp_health_report()
        print(f"\n📊 Health Summary:")
        print(f"   Quality: {health_report.sync_quality}")
        print(f"   Active Servers: {len(health_report.active_servers)}")
        print(f"   Average Offset: {health_report.average_offset:.2f}ms")
        
        # Save reports
        self.ntp_system.save_ntp_reports()
        print(f"\n📄 Reports saved to ntp_monitoring/reports/")

async def main():
    """Run the NTP demo."""
    demo = NTPDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 