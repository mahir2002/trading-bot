#!/usr/bin/env python3
"""
Unified Trading Dashboard Launcher
Launches the comprehensive web dashboard for the unified trading platform
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))

from dashboard.app import app, socketio

async def main():
    """Launch the unified trading dashboard"""
    print("🚀 Starting Unified Trading Dashboard...")
    print("📊 This dashboard replaces all 25+ previous dashboards")
    print("🌐 Access at: http://localhost:8080")
    print("📱 Mobile responsive design included")
    print("⚡ Real-time updates via WebSocket")
    print("")
    print("🎯 CONSOLIDATION COMPLETE!")
    print("   ✅ 35+ trading bots → 1 unified platform")
    print("   ✅ 25+ dashboards → 1 comprehensive interface")
    print("   ✅ 40+ systems → 1 modular architecture")
    print("")
    
    try:
        # Run the dashboard with SocketIO
        socketio.run(
            app,
            host='0.0.0.0',
            port=8080,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 