#!/usr/bin/env python3
"""
Comprehensive NTP Synchronization System
Advanced time synchronization and monitoring for AI Trading Bot
"""

import os
import sys
import time
import json
import yaml
import logging
import asyncio
import subprocess
import socket
import struct
import ntplib
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import statistics
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeStatus(Enum):
    """NTP time synchronization status."""
    SYNCHRONIZED = "synchronized"
    DRIFT_WARNING = "drift_warning"
    DRIFT_CRITICAL = "drift_critical"
    UNREACHABLE = "unreachable"
    ERROR = "error"
    UNKNOWN = "unknown"

class NTPServerTier(Enum):
    """NTP server tier classification."""
    STRATUM_1 = 1    # Primary reference clocks
    STRATUM_2 = 2    # Secondary servers (most common)
    STRATUM_3 = 3    # Tertiary servers
    STRATUM_4 = 4    # Local reference

@dataclass
class NTPServer:
    """NTP server configuration."""
    hostname: str
    tier: NTPServerTier
    location: str
    description: str
    priority: int = 1
    timeout: float = 10.0
    enabled: bool = True

@dataclass
class TimeSync:
    """Time synchronization result."""
    server: str
    offset: float
    delay: float
    jitter: float
    stratum: int
    reference_id: str
    timestamp: datetime
    status: TimeStatus

@dataclass
class TimeDriftAlert:
    """Time drift alert details."""
    drift_ms: float
    threshold_ms: float
    server: str
    severity: str
    timestamp: datetime
    description: str
    recommended_action: str

@dataclass
class NTPHealthReport:
    """NTP system health report."""
    system_time: datetime
    synchronized: bool
    primary_server: Optional[str]
    active_servers: List[str]
    failed_servers: List[str]
    average_offset: float
    max_drift: float
    sync_quality: str
    last_sync: Optional[datetime]
    uptime_percentage: float
    recommendations: List[str]

class NTPSynchronizationSystem:
    """
    Comprehensive NTP synchronization and monitoring system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the NTP synchronization system."""
        self.config = self._load_config(config_path)
        self.ntp_servers = self._load_ntp_servers()
        self.sync_history: List[TimeSync] = []
        self.drift_alerts: List[TimeDriftAlert] = []
        self.monitoring_active = False
        self.last_sync_time: Optional[datetime] = None
        
        # Create NTP directories
        os.makedirs("ntp_monitoring/reports", exist_ok=True)
        os.makedirs("ntp_monitoring/logs", exist_ok=True)
        os.makedirs("ntp_monitoring/configs", exist_ok=True)
        
        logger.info("✅ NTP Synchronization System initialized")
        logger.info(f"   Configured {len(self.ntp_servers)} NTP servers")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load NTP system configuration."""
        default_config = {
            "synchronization": {
                "sync_interval": 300,          # 5 minutes
                "drift_check_interval": 60,    # 1 minute
                "max_offset_warning": 100,     # 100ms
                "max_offset_critical": 1000,   # 1 second
                "min_servers_required": 2,     # Minimum servers for reliability
                "sync_timeout": 30,            # Sync operation timeout
                "retry_attempts": 3,           # Retry failed syncs
                "quality_threshold": 0.5       # Sync quality threshold
            },
            "monitoring": {
                "history_retention_days": 30,
                "alert_retention_days": 7,
                "health_check_interval": 300,  # 5 minutes
                "report_generation_interval": 3600,  # 1 hour
                "performance_metrics": True,
                "detailed_logging": True
            },
            "alerts": {
                "drift_warning_threshold": 50,    # 50ms
                "drift_critical_threshold": 200,  # 200ms
                "server_failure_threshold": 3,    # Failed attempts
                "sync_failure_threshold": 5,      # Consecutive failures
                "notification_cooldown": 1800      # 30 minutes
            },
            "security": {
                "use_authenticated_ntp": False,
                "validate_certificates": True,
                "log_security_events": True,
                "restrict_server_access": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                return {**default_config, **user_config}
        
        return default_config
    
    def _load_ntp_servers(self) -> List[NTPServer]:
        """Load NTP server configurations."""
        # High-quality NTP servers for trading applications
        servers = [
            # Stratum 1 servers (Primary reference clocks)
            NTPServer(
                hostname="time.nist.gov",
                tier=NTPServerTier.STRATUM_1,
                location="USA",
                description="NIST (National Institute of Standards and Technology)",
                priority=1,
                timeout=5.0
            ),
            NTPServer(
                hostname="time.google.com",
                tier=NTPServerTier.STRATUM_1,
                location="Global",
                description="Google Public NTP",
                priority=1,
                timeout=5.0
            ),
            NTPServer(
                hostname="time.cloudflare.com",
                tier=NTPServerTier.STRATUM_1,
                location="Global",
                description="Cloudflare Public NTP",
                priority=1,
                timeout=5.0
            ),
            
            # Stratum 2 servers (Secondary servers)
            NTPServer(
                hostname="pool.ntp.org",
                tier=NTPServerTier.STRATUM_2,
                location="Global",
                description="NTP Pool Project",
                priority=2,
                timeout=10.0
            ),
            NTPServer(
                hostname="time.windows.com",
                tier=NTPServerTier.STRATUM_2,
                location="Global",
                description="Microsoft Windows Time",
                priority=2,
                timeout=10.0
            ),
            NTPServer(
                hostname="time.apple.com",
                tier=NTPServerTier.STRATUM_2,
                location="Global",
                description="Apple Time Service",
                priority=2,
                timeout=10.0
            ),
            
            # Regional Stratum 2 servers for redundancy
            NTPServer(
                hostname="north-america.pool.ntp.org",
                tier=NTPServerTier.STRATUM_2,
                location="North America",
                description="North America NTP Pool",
                priority=3,
                timeout=10.0
            ),
            NTPServer(
                hostname="europe.pool.ntp.org",
                tier=NTPServerTier.STRATUM_2,
                location="Europe",
                description="Europe NTP Pool",
                priority=3,
                timeout=10.0
            )
        ]
        
        return servers
    
    async def sync_with_ntp_server(self, server: NTPServer) -> Optional[TimeSync]:
        """Synchronize with a specific NTP server."""
        try:
            logger.debug(f"🕐 Syncing with NTP server: {server.hostname}")
            
            # Use ntplib for accurate NTP synchronization
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request(server.hostname, timeout=server.timeout)
            
            # Calculate offset and other metrics
            offset = response.offset * 1000  # Convert to milliseconds
            delay = response.delay * 1000
            jitter = getattr(response, 'root_dispersion', 0) * 1000
            
            # Determine sync status based on offset
            if abs(offset) <= self.config["alerts"]["drift_warning_threshold"]:
                status = TimeStatus.SYNCHRONIZED
            elif abs(offset) <= self.config["alerts"]["drift_critical_threshold"]:
                status = TimeStatus.DRIFT_WARNING
            else:
                status = TimeStatus.DRIFT_CRITICAL
            
            sync_result = TimeSync(
                server=server.hostname,
                offset=offset,
                delay=delay,
                jitter=jitter,
                stratum=response.stratum,
                reference_id=response.ref_id,
                timestamp=datetime.now(timezone.utc),
                status=status
            )
            
            logger.info(f"✅ NTP sync successful: {server.hostname}")
            logger.info(f"   Offset: {offset:.2f}ms, Delay: {delay:.2f}ms, Stratum: {response.stratum}")
            
            return sync_result
            
        except Exception as e:
            logger.error(f"❌ NTP sync failed for {server.hostname}: {e}")
            
            return TimeSync(
                server=server.hostname,
                offset=float('inf'),
                delay=float('inf'),
                jitter=float('inf'),
                stratum=16,  # Invalid stratum
                reference_id="NONE",
                timestamp=datetime.now(timezone.utc),
                status=TimeStatus.UNREACHABLE
            )
    
    async def perform_multi_server_sync(self) -> List[TimeSync]:
        """Perform synchronization with multiple NTP servers."""
        logger.info("🌐 Starting multi-server NTP synchronization")
        
        # Filter enabled servers and sort by priority
        enabled_servers = [s for s in self.ntp_servers if s.enabled]
        enabled_servers.sort(key=lambda x: (x.priority, x.tier.value))
        
        # Perform parallel synchronization
        sync_tasks = [
            self.sync_with_ntp_server(server) 
            for server in enabled_servers
        ]
        
        sync_results = await asyncio.gather(*sync_tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        valid_syncs = [
            result for result in sync_results 
            if isinstance(result, TimeSync) and result.status != TimeStatus.UNREACHABLE
        ]
        
        # Store sync history
        self.sync_history.extend(valid_syncs)
        self.last_sync_time = datetime.now(timezone.utc)
        
        # Cleanup old history
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            days=self.config["monitoring"]["history_retention_days"]
        )
        self.sync_history = [
            sync for sync in self.sync_history 
            if sync.timestamp > cutoff_time
        ]
        
        logger.info(f"✅ Multi-server sync completed: {len(valid_syncs)}/{len(enabled_servers)} servers")
        
        return valid_syncs
    
    def analyze_time_drift(self, sync_results: List[TimeSync]) -> List[TimeDriftAlert]:
        """Analyze time drift and generate alerts."""
        alerts = []
        
        for sync in sync_results:
            offset_abs = abs(sync.offset)
            
            # Check for drift warnings
            if offset_abs > self.config["alerts"]["drift_warning_threshold"]:
                severity = "WARNING" if offset_abs <= self.config["alerts"]["drift_critical_threshold"] else "CRITICAL"
                
                alert = TimeDriftAlert(
                    drift_ms=sync.offset,
                    threshold_ms=self.config["alerts"]["drift_warning_threshold"],
                    server=sync.server,
                    severity=severity,
                    timestamp=datetime.now(timezone.utc),
                    description=f"Time drift detected: {sync.offset:.2f}ms offset from {sync.server}",
                    recommended_action=self._get_drift_recommendation(offset_abs, severity)
                )
                
                alerts.append(alert)
                logger.warning(f"⚠️ Time drift alert: {alert.description}")
        
        # Store alerts
        self.drift_alerts.extend(alerts)
        
        # Cleanup old alerts
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            days=self.config["monitoring"]["alert_retention_days"]
        )
        self.drift_alerts = [
            alert for alert in self.drift_alerts 
            if alert.timestamp > cutoff_time
        ]
        
        return alerts
    
    def _get_drift_recommendation(self, offset_ms: float, severity: str) -> str:
        """Get recommendation for time drift remediation."""
        if severity == "CRITICAL":
            return "IMMEDIATE: Stop trading operations, force NTP sync, investigate system clock"
        elif offset_ms > 100:
            return "HIGH PRIORITY: Schedule NTP sync, monitor system performance"
        else:
            return "MONITOR: Increase sync frequency, check network connectivity"
    
    def get_best_time_reference(self, sync_results: List[TimeSync]) -> Optional[TimeSync]:
        """Get the best time reference from sync results."""
        if not sync_results:
            return None
        
        # Filter successful syncs
        successful_syncs = [
            sync for sync in sync_results 
            if sync.status in [TimeStatus.SYNCHRONIZED, TimeStatus.DRIFT_WARNING]
        ]
        
        if not successful_syncs:
            return None
        
        # Sort by quality (lower stratum, lower offset, lower delay)
        successful_syncs.sort(key=lambda x: (
            x.stratum,
            abs(x.offset),
            x.delay,
            x.jitter
        ))
        
        return successful_syncs[0]
    
    async def apply_time_correction(self, reference_sync: TimeSync) -> bool:
        """Apply time correction based on NTP reference."""
        try:
            # Calculate correction needed
            correction_seconds = reference_sync.offset / 1000.0
            
            logger.info(f"🔧 Applying time correction: {correction_seconds:.3f} seconds")
            
            # For safety, only apply corrections within reasonable bounds
            max_correction = self.config["synchronization"]["max_offset_critical"] / 1000.0
            
            if abs(correction_seconds) > max_correction:
                logger.error(f"❌ Time correction too large: {correction_seconds:.3f}s > {max_correction}s")
                return False
            
            # Apply system time correction (requires appropriate permissions)
            if sys.platform.startswith('linux') or sys.platform == 'darwin':
                # Use ntpdate or similar for Unix-like systems
                result = subprocess.run([
                    'sudo', 'ntpdate', '-s', reference_sync.server
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info(f"✅ System time synchronized with {reference_sync.server}")
                    return True
                else:
                    logger.error(f"❌ ntpdate failed: {result.stderr}")
                    return False
            
            elif sys.platform.startswith('win'):
                # Use w32time for Windows systems
                result = subprocess.run([
                    'w32tm', '/resync', '/force'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info("✅ Windows time service synchronized")
                    return True
                else:
                    logger.error(f"❌ w32tm failed: {result.stderr}")
                    return False
            
            else:
                logger.warning("⚠️ Unsupported platform for automatic time correction")
                return False
                
        except Exception as e:
            logger.error(f"❌ Time correction failed: {e}")
            return False
    
    def generate_ntp_health_report(self) -> NTPHealthReport:
        """Generate comprehensive NTP health report."""
        now = datetime.now(timezone.utc)
        
        # Get recent sync results (last hour)
        recent_syncs = [
            sync for sync in self.sync_history
            if now - sync.timestamp <= timedelta(hours=1)
        ]
        
        # Calculate metrics
        synchronized_servers = [
            sync.server for sync in recent_syncs
            if sync.status == TimeStatus.SYNCHRONIZED
        ]
        
        failed_servers = [
            sync.server for sync in recent_syncs
            if sync.status in [TimeStatus.UNREACHABLE, TimeStatus.ERROR]
        ]
        
        # Calculate average offset for synchronized servers
        sync_offsets = [
            sync.offset for sync in recent_syncs
            if sync.status in [TimeStatus.SYNCHRONIZED, TimeStatus.DRIFT_WARNING]
        ]
        
        average_offset = statistics.mean(sync_offsets) if sync_offsets else float('inf')
        max_drift = max(abs(offset) for offset in sync_offsets) if sync_offsets else float('inf')
        
        # Determine sync quality
        if len(synchronized_servers) >= self.config["synchronization"]["min_servers_required"]:
            if max_drift <= self.config["alerts"]["drift_warning_threshold"]:
                sync_quality = "EXCELLENT"
            elif max_drift <= self.config["alerts"]["drift_critical_threshold"]:
                sync_quality = "GOOD"
            else:
                sync_quality = "POOR"
        else:
            sync_quality = "CRITICAL"
        
        # Calculate uptime percentage (last 24 hours)
        day_ago = now - timedelta(hours=24)
        day_syncs = [sync for sync in self.sync_history if sync.timestamp > day_ago]
        successful_day_syncs = [
            sync for sync in day_syncs
            if sync.status in [TimeStatus.SYNCHRONIZED, TimeStatus.DRIFT_WARNING]
        ]
        
        uptime_percentage = (
            len(successful_day_syncs) / len(day_syncs) * 100 
            if day_syncs else 0
        )
        
        # Generate recommendations
        recommendations = self._generate_ntp_recommendations(
            synchronized_servers, failed_servers, max_drift, uptime_percentage
        )
        
        # Get primary server (best quality)
        primary_server = None
        if recent_syncs:
            best_sync = self.get_best_time_reference(recent_syncs)
            primary_server = best_sync.server if best_sync else None
        
        return NTPHealthReport(
            system_time=now,
            synchronized=len(synchronized_servers) > 0,
            primary_server=primary_server,
            active_servers=list(set(synchronized_servers)),
            failed_servers=list(set(failed_servers)),
            average_offset=average_offset,
            max_drift=max_drift,
            sync_quality=sync_quality,
            last_sync=self.last_sync_time,
            uptime_percentage=uptime_percentage,
            recommendations=recommendations
        )
    
    def _generate_ntp_recommendations(self, active_servers: List[str], 
                                    failed_servers: List[str], max_drift: float,
                                    uptime: float) -> List[str]:
        """Generate NTP system recommendations."""
        recommendations = []
        
        if len(active_servers) < self.config["synchronization"]["min_servers_required"]:
            recommendations.append("🚨 CRITICAL: Add more NTP servers for redundancy")
        
        if failed_servers:
            recommendations.append(f"⚠️ HIGH: Investigate {len(failed_servers)} failed NTP servers")
        
        if max_drift > self.config["alerts"]["drift_critical_threshold"]:
            recommendations.append("🚨 CRITICAL: Immediate time synchronization required")
        elif max_drift > self.config["alerts"]["drift_warning_threshold"]:
            recommendations.append("⚠️ MEDIUM: Monitor time drift closely")
        
        if uptime < 95.0:
            recommendations.append("⚠️ HIGH: Improve NTP service reliability")
        
        if uptime > 99.0 and max_drift < self.config["alerts"]["drift_warning_threshold"]:
            recommendations.append("✅ EXCELLENT: NTP synchronization performing well")
        
        recommendations.extend([
            "🔍 MONITOR: Regular NTP health checks",
            "📋 MAINTAIN: Keep NTP server list updated",
            "🔧 OPTIMIZE: Fine-tune sync intervals based on performance"
        ])
        
        return recommendations
    
    async def start_continuous_monitoring(self):
        """Start continuous NTP monitoring."""
        logger.info("🚀 Starting continuous NTP monitoring")
        self.monitoring_active = True
        
        # Start monitoring tasks
        sync_task = asyncio.create_task(self._sync_monitoring_loop())
        health_task = asyncio.create_task(self._health_monitoring_loop())
        report_task = asyncio.create_task(self._report_generation_loop())
        
        try:
            await asyncio.gather(sync_task, health_task, report_task)
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
        finally:
            self.monitoring_active = False
    
    async def _sync_monitoring_loop(self):
        """Continuous synchronization monitoring loop."""
        while self.monitoring_active:
            try:
                # Perform multi-server sync
                sync_results = await self.perform_multi_server_sync()
                
                # Analyze drift and generate alerts
                drift_alerts = self.analyze_time_drift(sync_results)
                
                # Apply corrections if needed
                if sync_results:
                    best_reference = self.get_best_time_reference(sync_results)
                    if best_reference and abs(best_reference.offset) > self.config["alerts"]["drift_critical_threshold"]:
                        logger.warning("🔧 Critical drift detected, attempting correction")
                        await self.apply_time_correction(best_reference)
                
                # Wait for next sync cycle
                await asyncio.sleep(self.config["synchronization"]["sync_interval"])
                
            except Exception as e:
                logger.error(f"❌ Sync monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring loop."""
        while self.monitoring_active:
            try:
                # Generate health report
                health_report = self.generate_ntp_health_report()
                
                # Log health status
                logger.info(f"📊 NTP Health: {health_report.sync_quality} "
                          f"({len(health_report.active_servers)} servers, "
                          f"{health_report.uptime_percentage:.1f}% uptime)")
                
                # Check for critical issues
                if health_report.sync_quality in ["CRITICAL", "POOR"]:
                    logger.error("🚨 NTP health critical - immediate attention required")
                
                # Wait for next health check
                await asyncio.sleep(self.config["monitoring"]["health_check_interval"])
                
            except Exception as e:
                logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _report_generation_loop(self):
        """Continuous report generation loop."""
        while self.monitoring_active:
            try:
                # Generate and save reports
                self.save_ntp_reports()
                
                # Wait for next report generation
                await asyncio.sleep(self.config["monitoring"]["report_generation_interval"])
                
            except Exception as e:
                logger.error(f"❌ Report generation error: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes before retry
    
    def save_ntp_reports(self):
        """Save comprehensive NTP reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate health report
        health_report = self.generate_ntp_health_report()
        
        # Save JSON report
        json_file = f"ntp_monitoring/reports/ntp_health_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "timestamp": health_report.system_time.isoformat(),
                "synchronized": health_report.synchronized,
                "primary_server": health_report.primary_server,
                "active_servers": health_report.active_servers,
                "failed_servers": health_report.failed_servers,
                "average_offset_ms": health_report.average_offset,
                "max_drift_ms": health_report.max_drift,
                "sync_quality": health_report.sync_quality,
                "uptime_percentage": health_report.uptime_percentage,
                "recommendations": health_report.recommendations,
                "recent_alerts": [
                    {
                        "drift_ms": alert.drift_ms,
                        "server": alert.server,
                        "severity": alert.severity,
                        "timestamp": alert.timestamp.isoformat(),
                        "description": alert.description
                    }
                    for alert in self.drift_alerts[-10:]  # Last 10 alerts
                ]
            }, indent=2)
        
        # Save HTML report
        html_file = f"ntp_monitoring/reports/ntp_health_{timestamp}.html"
        self._generate_html_report(health_report, html_file)
        
        logger.info(f"📄 NTP reports saved: {json_file}")
    
    def _generate_html_report(self, health_report: NTPHealthReport, filename: str):
        """Generate HTML NTP health report."""
        quality_colors = {
            "EXCELLENT": "#28a745",
            "GOOD": "#ffc107", 
            "POOR": "#fd7e14",
            "CRITICAL": "#dc3545"
        }
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NTP Health Report - AI Trading Bot</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .status-card {{ background: {quality_colors.get(health_report.sync_quality, '#6c757d')}; color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
        .servers-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .servers-table th, .servers-table td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        .servers-table th {{ background: #f8f9fa; font-weight: bold; }}
        .server-active {{ background-color: #d4edda; }}
        .server-failed {{ background-color: #f8d7da; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕐 NTP Health Report</h1>
            <h2>AI Trading Bot Time Synchronization</h2>
            <p><strong>Report Time:</strong> {health_report.system_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>Last Sync:</strong> {health_report.last_sync.strftime('%Y-%m-%d %H:%M:%S UTC') if health_report.last_sync else 'Never'}</p>
        </div>
        
        <div class="status-card">
            <h3>🎯 Overall Sync Status</h3>
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="font-size: 36px; font-weight: bold;">{health_report.sync_quality}</div>
                <div>
                    <div style="font-size: 18px;">{'✅ Synchronized' if health_report.synchronized else '❌ Not Synchronized'}</div>
                    <div>Primary Server: {health_report.primary_server or 'None'}</div>
                    <div>Uptime: {health_report.uptime_percentage:.1f}%</div>
                </div>
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>Active Servers</h3>
                <div style="font-size: 32px; font-weight: bold; color: #28a745;">{len(health_report.active_servers)}</div>
            </div>
            <div class="metric-card">
                <h3>Failed Servers</h3>
                <div style="font-size: 32px; font-weight: bold; color: #dc3545;">{len(health_report.failed_servers)}</div>
            </div>
            <div class="metric-card">
                <h3>Average Offset</h3>
                <div style="font-size: 32px; font-weight: bold; color: #007bff;">{health_report.average_offset:.1f}ms</div>
            </div>
            <div class="metric-card">
                <h3>Max Drift</h3>
                <div style="font-size: 32px; font-weight: bold; color: #fd7e14;">{health_report.max_drift:.1f}ms</div>
            </div>
        </div>
        
        <h2>📊 Server Status</h2>
        <table class="servers-table">
            <tr>
                <th>Server</th>
                <th>Status</th>
                <th>Location</th>
                <th>Tier</th>
            </tr>
"""
        
        # Add active servers
        for server_name in health_report.active_servers:
            server = next((s for s in self.ntp_servers if s.hostname == server_name), None)
            html_content += f"""
            <tr class="server-active">
                <td>{server_name}</td>
                <td>✅ Active</td>
                <td>{server.location if server else 'Unknown'}</td>
                <td>Stratum {server.tier.value if server else 'Unknown'}</td>
            </tr>
"""
        
        # Add failed servers
        for server_name in health_report.failed_servers:
            server = next((s for s in self.ntp_servers if s.hostname == server_name), None)
            html_content += f"""
            <tr class="server-failed">
                <td>{server_name}</td>
                <td>❌ Failed</td>
                <td>{server.location if server else 'Unknown'}</td>
                <td>Stratum {server.tier.value if server else 'Unknown'}</td>
            </tr>
"""
        
        html_content += f"""
        </table>
        
        <div class="recommendations">
            <h3>📈 Recommendations</h3>
            <ul>
"""
        
        for recommendation in health_report.recommendations:
            html_content += f"                <li>{recommendation}</li>\n"
        
        html_content += """
            </ul>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>🔧 Next Steps</h3>
            <ol>
                <li><strong>Monitor continuously:</strong> Keep NTP monitoring active</li>
                <li><strong>Address failures:</strong> Investigate and fix failed servers</li>
                <li><strong>Optimize performance:</strong> Fine-tune sync intervals</li>
                <li><strong>Review alerts:</strong> Respond to drift warnings promptly</li>
                <li><strong>Maintain redundancy:</strong> Ensure multiple reliable servers</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html_content)
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        logger.info("🛑 Stopping NTP monitoring")
        self.monitoring_active = False

async def main():
    """Demonstrate NTP synchronization system."""
    print("🕐 NTP Synchronization System - AI Trading Bot")
    print("=" * 70)
    
    # Initialize NTP system
    ntp_system = NTPSynchronizationSystem()
    
    print(f"\n🌐 Performing initial NTP synchronization...")
    
    # Perform initial sync
    sync_results = await ntp_system.perform_multi_server_sync()
    
    print(f"✅ Synchronized with {len(sync_results)} NTP servers")
    
    # Analyze results
    for sync in sync_results:
        status_icon = "✅" if sync.status == TimeStatus.SYNCHRONIZED else "⚠️" if sync.status == TimeStatus.DRIFT_WARNING else "❌"
        print(f"   {status_icon} {sync.server}: {sync.offset:.2f}ms offset, Stratum {sync.stratum}")
    
    # Check for drift alerts
    drift_alerts = ntp_system.analyze_time_drift(sync_results)
    if drift_alerts:
        print(f"\n⚠️ Time drift alerts:")
        for alert in drift_alerts:
            print(f"   {alert.severity}: {alert.description}")
    
    # Get best time reference
    best_reference = ntp_system.get_best_time_reference(sync_results)
    if best_reference:
        print(f"\n🎯 Best time reference: {best_reference.server}")
        print(f"   Offset: {best_reference.offset:.2f}ms")
        print(f"   Stratum: {best_reference.stratum}")
        print(f"   Quality: {best_reference.status.value}")
    
    # Generate health report
    print(f"\n📊 Generating NTP health report...")
    health_report = ntp_system.generate_ntp_health_report()
    
    print(f"✅ NTP Health Summary:")
    print(f"   Overall Quality: {health_report.sync_quality}")
    print(f"   Active Servers: {len(health_report.active_servers)}")
    print(f"   Failed Servers: {len(health_report.failed_servers)}")
    print(f"   Average Offset: {health_report.average_offset:.2f}ms")
    print(f"   Max Drift: {health_report.max_drift:.2f}ms")
    print(f"   Uptime: {health_report.uptime_percentage:.1f}%")
    
    # Save reports
    ntp_system.save_ntp_reports()
    print(f"\n📄 Reports saved to ntp_monitoring/reports/")
    
    # Show recommendations
    if health_report.recommendations:
        print(f"\n📋 Recommendations:")
        for rec in health_report.recommendations:
            print(f"   • {rec}")
    
    print(f"\n🎉 NTP Synchronization System demonstration completed!")
    print(f"💡 For continuous monitoring, run: ntp_system.start_continuous_monitoring()")

if __name__ == "__main__":
    asyncio.run(main()) 