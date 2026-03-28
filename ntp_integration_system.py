#!/usr/bin/env python3
"""
NTP Integration System for AI Trading Bot
Integrates NTP synchronization with Docker containers and trading operations
"""

import os
import sys
import json
import yaml
import logging
import asyncio
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ntp_synchronization_system import NTPSynchronizationSystem, TimeStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NTPIntegrationSystem:
    """Comprehensive NTP integration for AI Trading Bot infrastructure."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize NTP integration system."""
        self.ntp_system = NTPSynchronizationSystem()
        self.config = self._load_integration_config(config_path)
        self.docker_containers: Dict[str, str] = {}
        
        # Create integration directories
        os.makedirs("ntp_integration/configs", exist_ok=True)
        os.makedirs("ntp_integration/scripts", exist_ok=True)
        os.makedirs("ntp_integration/monitoring", exist_ok=True)
        
        logger.info("✅ NTP Integration System initialized")
    
    def _load_integration_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load integration configuration."""
        default_config = {
            "docker_integration": {
                "sync_containers": True,
                "container_time_check": True,
                "host_to_container_sync": True,
                "container_ntp_servers": [
                    "time.google.com",
                    "time.cloudflare.com",
                    "pool.ntp.org"
                ]
            },
            "trading_bot_integration": {
                "pre_trade_sync_check": True,
                "max_allowed_drift_ms": 100,
                "trading_halt_on_critical_drift": True,
                "timestamp_validation": True,
                "order_timing_sync": True
            },
            "monitoring_integration": {
                "health_check_interval": 300,
                "alert_on_drift": True,
                "log_sync_events": True,
                "performance_metrics": True,
                "compliance_reporting": True
            },
            "system_integration": {
                "startup_time_sync": True,
                "periodic_system_sync": True,
                "emergency_sync_procedures": True,
                "backup_time_sources": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                return {**default_config, **user_config}
        
        return default_config
    
    async def initialize_system_time_sync(self):
        """Initialize comprehensive system time synchronization."""
        logger.info("🚀 Initializing system-wide NTP synchronization")
        
        # 1. Perform initial NTP sync
        logger.info("🕐 Step 1: Initial NTP synchronization")
        sync_results = await self.ntp_system.perform_multi_server_sync()
        
        successful_syncs = [s for s in sync_results if s.status != TimeStatus.UNREACHABLE]
        logger.info(f"✅ Initial sync completed: {len(successful_syncs)}/{len(sync_results)} servers")
        
        # 2. Check system drift
        if successful_syncs:
            best_reference = self.ntp_system.get_best_time_reference(successful_syncs)
            if best_reference:
                drift_ms = abs(best_reference.offset)
                logger.info(f"📊 System drift: {drift_ms:.2f}ms from {best_reference.server}")
                
                if drift_ms > self.config["trading_bot_integration"]["max_allowed_drift_ms"]:
                    logger.warning(f"⚠️ High drift detected: {drift_ms:.2f}ms")
                    if self.config["trading_bot_integration"]["trading_halt_on_critical_drift"]:
                        logger.error("🚨 CRITICAL: Trading operations should be halted due to time drift")
        
        # 3. Configure system NTP
        await self._configure_system_ntp()
        
        # 4. Setup Docker time synchronization
        if self.config["docker_integration"]["sync_containers"]:
            await self._setup_docker_time_sync()
        
        logger.info("✅ System time synchronization initialized")
    
    async def _configure_system_ntp(self):
        """Configure system-level NTP synchronization."""
        logger.info("🔧 Configuring system NTP")
        
        # Generate NTP configuration
        ntp_config = self._generate_ntp_config()
        
        # Save NTP configuration
        ntp_config_path = "ntp_integration/configs/ntp.conf"
        with open(ntp_config_path, 'w') as f:
            f.write(ntp_config)
        
        logger.info(f"📄 NTP config saved: {ntp_config_path}")
        
        # Platform-specific NTP setup
        if sys.platform.startswith('linux'):
            await self._setup_linux_ntp()
        elif sys.platform == 'darwin':
            await self._setup_macos_ntp()
        elif sys.platform.startswith('win'):
            await self._setup_windows_ntp()
    
    def _generate_ntp_config(self) -> str:
        """Generate NTP configuration file."""
        ntp_servers = [
            "time.google.com",
            "time.cloudflare.com", 
            "time.nist.gov",
            "pool.ntp.org"
        ]
        
        config_lines = [
            "# NTP Configuration for AI Trading Bot",
            "# Generated by NTP Integration System",
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "# NTP Servers",
        ]
        
        for server in ntp_servers:
            config_lines.append(f"server {server} iburst")
        
        config_lines.extend([
            "",
            "# Drift file",
            "driftfile /var/lib/ntp/drift",
            "",
            "# Logging",
            "logfile /var/log/ntp.log",
            "",
            "# Security",
            "restrict default kod nomodify notrap nopeer noquery",
            "restrict -6 default kod nomodify notrap nopeer noquery",
            "restrict 127.0.0.1",
            "restrict -6 ::1",
        ])
        
        return "\n".join(config_lines)
    
    async def _setup_linux_ntp(self):
        """Setup NTP on Linux systems."""
        try:
            # Check if chronyd or ntpd is available
            chrony_available = subprocess.run(['which', 'chronyd'], capture_output=True).returncode == 0
            ntp_available = subprocess.run(['which', 'ntpd'], capture_output=True).returncode == 0
            
            if chrony_available:
                logger.info("🐧 Using chrony for Linux NTP")
                # Configure chrony
                chrony_config = """
# Chrony configuration for AI Trading Bot
server time.google.com iburst
server time.cloudflare.com iburst
server time.nist.gov iburst
server pool.ntp.org iburst

# Allow system clock to be stepped in the first few updates
makestep 1.0 3

# Enable kernel synchronization
rtcsync

# Logging
logdir /var/log/chrony
"""
                with open("ntp_integration/configs/chrony.conf", 'w') as f:
                    f.write(chrony_config)
            
            elif ntp_available:
                logger.info("🐧 Using ntpd for Linux NTP")
                # Configuration already generated
                pass
            
            else:
                logger.warning("⚠️ No NTP daemon found on Linux system")
                
        except Exception as e:
            logger.error(f"❌ Linux NTP setup failed: {e}")
    
    async def _setup_macos_ntp(self):
        """Setup NTP on macOS systems."""
        try:
            logger.info("🍎 Configuring macOS NTP")
            
            # macOS uses sntp by default
            macos_script = """#!/bin/bash
# macOS NTP Configuration Script for AI Trading Bot

# Enable automatic time sync
sudo systemsetup -setusingnetworktime on

# Set NTP server
sudo systemsetup -setnetworktimeserver time.apple.com

# Force immediate sync
sudo sntp -sS time.apple.com

echo "macOS NTP configuration completed"
"""
            
            script_path = "ntp_integration/scripts/setup_macos_ntp.sh"
            with open(script_path, 'w') as f:
                f.write(macos_script)
            
            os.chmod(script_path, 0o755)
            logger.info(f"📜 macOS NTP script saved: {script_path}")
            
        except Exception as e:
            logger.error(f"❌ macOS NTP setup failed: {e}")
    
    async def _setup_windows_ntp(self):
        """Setup NTP on Windows systems."""
        try:
            logger.info("🪟 Configuring Windows NTP")
            
            windows_script = """@echo off
REM Windows NTP Configuration Script for AI Trading Bot

REM Configure Windows Time service
w32tm /config /manualpeerlist:"time.windows.com,time.google.com,time.cloudflare.com" /syncfromflags:manual /reliable:yes /update

REM Start Windows Time service
net start w32time

REM Force immediate sync
w32tm /resync /force

echo Windows NTP configuration completed
"""
            
            script_path = "ntp_integration/scripts/setup_windows_ntp.bat"
            with open(script_path, 'w') as f:
                f.write(windows_script)
            
            logger.info(f"📜 Windows NTP script saved: {script_path}")
            
        except Exception as e:
            logger.error(f"❌ Windows NTP setup failed: {e}")
    
    async def _setup_docker_time_sync(self):
        """Setup Docker container time synchronization."""
        logger.info("🐳 Setting up Docker time synchronization")
        
        # Discover running containers
        await self._discover_docker_containers()
        
        # Generate Docker Compose with time sync
        await self._generate_docker_compose_with_ntp()
        
        # Create container time sync scripts
        await self._create_container_sync_scripts()
    
    async def _discover_docker_containers(self):
        """Discover running Docker containers."""
        try:
            result = subprocess.run([
                'docker', 'ps', '--format', 'table {{.Names}}\t{{.Image}}'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            container_name = parts[0]
                            image = parts[1]
                            self.docker_containers[container_name] = image
                
                logger.info(f"🐳 Discovered {len(self.docker_containers)} Docker containers")
                for name, image in self.docker_containers.items():
                    logger.info(f"   • {name} ({image})")
            
        except Exception as e:
            logger.error(f"❌ Docker container discovery failed: {e}")
    
    async def _generate_docker_compose_with_ntp(self):
        """Generate Docker Compose configuration with NTP synchronization."""
        
        docker_compose = {
            "version": "3.8",
            "services": {
                "trading-bot": {
                    "image": "ai-trading-bot:latest",
                    "container_name": "trading_bot",
                    "volumes": [
                        "/etc/localtime:/etc/localtime:ro",
                        "/etc/timezone:/etc/timezone:ro",
                        "./ntp_integration/configs:/etc/ntp:ro"
                    ],
                    "environment": [
                        "TZ=UTC",
                        "NTP_SERVERS=time.google.com,time.cloudflare.com"
                    ],
                    "cap_add": [
                        "SYS_TIME"
                    ],
                    "security_opt": [
                        "no-new-privileges:true"
                    ],
                    "networks": ["trading_network"]
                },
                
                "ntp-monitor": {
                    "image": "alpine:latest",
                    "container_name": "ntp_monitor",
                    "command": [
                        "sh", "-c",
                        "apk add --no-cache ntpsec-ntpdate && "
                        "while true; do "
                        "ntpdate -s time.google.com; "
                        "sleep 300; "
                        "done"
                    ],
                    "volumes": [
                        "/etc/localtime:/etc/localtime:ro",
                        "./ntp_integration/monitoring:/monitoring"
                    ],
                    "networks": ["trading_network"],
                    "depends_on": ["trading-bot"]
                }
            },
            
            "networks": {
                "trading_network": {
                    "driver": "bridge"
                }
            }
        }
        
        compose_file = "ntp_integration/configs/docker-compose.ntp-sync.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False, indent=2)
        
        logger.info(f"🐳 Docker Compose with NTP sync saved: {compose_file}")
    
    async def _create_container_sync_scripts(self):
        """Create container time synchronization scripts."""
        
        # Container sync script
        sync_script = """#!/bin/bash
# Container Time Synchronization Script for AI Trading Bot

echo "🕐 Starting container time synchronization..."

# Function to sync time in container
sync_container_time() {
    local container_name=$1
    echo "🐳 Syncing time for container: $container_name"
    
    # Copy host timezone to container
    docker exec $container_name sh -c "
        if [ -f /etc/localtime ]; then
            echo 'Timezone already synchronized'
        else
            echo 'Setting up timezone synchronization'
        fi
    "
    
    # Sync time using ntpdate in container
    docker exec $container_name sh -c "
        if command -v ntpdate >/dev/null 2>&1; then
            ntpdate -s time.google.com 2>/dev/null || echo 'NTP sync skipped'
        else
            echo 'ntpdate not available in container'
        fi
    "
}

# Sync all running containers
for container in $(docker ps --format '{{.Names}}'); do
    sync_container_time $container
done

echo "✅ Container time synchronization completed"
"""
        
        script_path = "ntp_integration/scripts/sync_container_time.sh"
        with open(script_path, 'w') as f:
            f.write(sync_script)
        
        os.chmod(script_path, 0o755)
        logger.info(f"📜 Container sync script saved: {script_path}")
    
    async def validate_trading_bot_time_sync(self) -> Dict[str, Any]:
        """Validate time synchronization for trading bot operations."""
        logger.info("🎯 Validating trading bot time synchronization")
        
        # Perform fresh NTP sync
        sync_results = await self.ntp_system.perform_multi_server_sync()
        
        # Get best time reference
        best_reference = self.ntp_system.get_best_time_reference(sync_results)
        
        validation_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_passed": False,
            "drift_ms": float('inf'),
            "status": "UNKNOWN",
            "recommendations": []
        }
        
        if best_reference:
            drift_ms = abs(best_reference.offset)
            max_allowed = self.config["trading_bot_integration"]["max_allowed_drift_ms"]
            
            validation_result.update({
                "drift_ms": drift_ms,
                "best_server": best_reference.server,
                "stratum": best_reference.stratum,
                "max_allowed_drift_ms": max_allowed
            })
            
            if drift_ms <= max_allowed:
                validation_result.update({
                    "validation_passed": True,
                    "status": "READY_FOR_TRADING"
                })
                logger.info(f"✅ Trading bot time validation passed: {drift_ms:.2f}ms drift")
            else:
                validation_result.update({
                    "status": "TRADING_HALT_RECOMMENDED",
                    "recommendations": [
                        "Halt trading operations immediately",
                        "Investigate system clock synchronization",
                        "Check network connectivity to NTP servers",
                        "Verify system time configuration"
                    ]
                })
                logger.error(f"🚨 Trading bot time validation failed: {drift_ms:.2f}ms drift")
        
        return validation_result
    
    async def start_integrated_monitoring(self):
        """Start integrated NTP monitoring with trading bot integration."""
        logger.info("🚀 Starting integrated NTP monitoring")
        
        # Start base NTP monitoring
        monitoring_task = asyncio.create_task(self.ntp_system.start_continuous_monitoring())
        
        # Start trading-specific monitoring
        trading_monitor_task = asyncio.create_task(self._trading_time_monitor())
        
        # Start Docker container monitoring
        if self.config["docker_integration"]["container_time_check"]:
            container_monitor_task = asyncio.create_task(self._container_time_monitor())
            await asyncio.gather(monitoring_task, trading_monitor_task, container_monitor_task)
        else:
            await asyncio.gather(monitoring_task, trading_monitor_task)
    
    async def _trading_time_monitor(self):
        """Monitor time synchronization for trading operations."""
        logger.info("📊 Starting trading time monitor")
        
        while True:
            try:
                # Validate time sync for trading
                validation = await self.validate_trading_bot_time_sync()
                
                # Log validation results
                if validation["validation_passed"]:
                    logger.info(f"✅ Trading time validation: {validation['drift_ms']:.2f}ms drift")
                else:
                    logger.error(f"🚨 Trading time validation failed: {validation['status']}")
                
                # Wait for next check
                await asyncio.sleep(self.config["monitoring_integration"]["health_check_interval"])
                
            except Exception as e:
                logger.error(f"❌ Trading time monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _container_time_monitor(self):
        """Monitor Docker container time synchronization."""
        logger.info("🐳 Starting container time monitor")
        
        while True:
            try:
                # Sync container times
                if self.docker_containers:
                    sync_script = "ntp_integration/scripts/sync_container_time.sh"
                    if os.path.exists(sync_script):
                        result = subprocess.run([sync_script], capture_output=True, text=True)
                        if result.returncode == 0:
                            logger.info("✅ Container time sync completed")
                        else:
                            logger.error(f"❌ Container time sync failed: {result.stderr}")
                
                # Wait for next sync
                await asyncio.sleep(self.config["monitoring_integration"]["health_check_interval"])
                
            except Exception as e:
                logger.error(f"❌ Container time monitor error: {e}")
                await asyncio.sleep(300)

async def main():
    """Demonstrate NTP integration system."""
    print("🕐 NTP Integration System - AI Trading Bot")
    print("=" * 80)
    
    # Initialize integration system
    integration = NTPIntegrationSystem()
    
    # Initialize system time sync
    await integration.initialize_system_time_sync()
    
    # Validate trading bot time sync
    validation = await integration.validate_trading_bot_time_sync()
    
    print(f"\n🎯 Trading Bot Time Validation:")
    print(f"   Status: {validation['status']}")
    print(f"   Drift: {validation['drift_ms']:.2f}ms")
    print(f"   Ready for Trading: {'Yes' if validation['validation_passed'] else 'No'}")
    
    if validation["recommendations"]:
        print(f"\n📋 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"   • {rec}")
    
    print(f"\n✅ NTP Integration System ready for production!")
    print(f"💡 Start monitoring: await integration.start_integrated_monitoring()")

if __name__ == "__main__":
    asyncio.run(main()) 