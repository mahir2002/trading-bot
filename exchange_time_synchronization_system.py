#!/usr/bin/env python3
"""
Exchange Time Synchronization System
Synchronizes with exchange server times for accurate trading operations
"""

import os
import sys
import time
import json
import yaml
import logging
import asyncio
import aiohttp
import hashlib
import hmac
import base64
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
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

class ExchangeType(Enum):
    """Supported exchange types."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKEX = "okex"
    HUOBI = "huobi"
    KUCOIN = "kucoin"
    BITFINEX = "bitfinex"
    FTXUS = "ftxus"
    GEMINI = "gemini"

class TimeSyncStatus(Enum):
    """Exchange time synchronization status."""
    SYNCHRONIZED = "synchronized"
    DRIFT_WARNING = "drift_warning"
    DRIFT_CRITICAL = "drift_critical"
    UNREACHABLE = "unreachable"
    AUTH_ERROR = "auth_error"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

@dataclass
class ExchangeConfig:
    """Exchange configuration for time synchronization."""
    name: str
    exchange_type: ExchangeType
    base_url: str
    time_endpoint: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    timeout: float = 10.0
    rate_limit_per_minute: int = 60
    requires_auth: bool = False
    timestamp_format: str = "milliseconds"  # or "seconds"
    enabled: bool = True

@dataclass
class ExchangeTimeSync:
    """Exchange time synchronization result."""
    exchange: str
    server_time: int
    local_time: int
    offset_ms: float
    network_delay_ms: float
    timestamp: datetime
    status: TimeSyncStatus
    response_time_ms: float
    auth_required: bool = False

@dataclass
class TimestampValidation:
    """Timestamp validation result for signed requests."""
    exchange: str
    request_timestamp: int
    server_timestamp: int
    offset_ms: float
    within_window: bool
    window_ms: int
    recommended_timestamp: int
    status: str

class ExchangeTimeSynchronizationSystem:
    """
    Comprehensive exchange time synchronization system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the exchange time synchronization system."""
        self.config = self._load_config(config_path)
        self.exchanges = self._load_exchange_configs()
        self.sync_history: Dict[str, List[ExchangeTimeSync]] = {}
        self.time_offsets: Dict[str, float] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.monitoring_active = False
        
        # Create directories
        os.makedirs("exchange_time_sync/reports", exist_ok=True)
        os.makedirs("exchange_time_sync/logs", exist_ok=True)
        os.makedirs("exchange_time_sync/configs", exist_ok=True)
        
        logger.info("✅ Exchange Time Synchronization System initialized")
        logger.info(f"   Configured {len(self.exchanges)} exchanges")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load exchange time sync configuration."""
        default_config = {
            "synchronization": {
                "sync_interval": 300,          # 5 minutes
                "drift_check_interval": 60,    # 1 minute
                "max_offset_warning": 1000,    # 1 second
                "max_offset_critical": 5000,   # 5 seconds
                "timestamp_window_ms": 5000,   # 5 second window for signed requests
                "retry_attempts": 3,
                "concurrent_syncs": True
            },
            "monitoring": {
                "history_retention_hours": 24,
                "health_check_interval": 300,
                "report_generation_interval": 3600,
                "performance_metrics": True,
                "detailed_logging": True
            },
            "alerts": {
                "drift_warning_threshold": 1000,    # 1 second
                "drift_critical_threshold": 5000,   # 5 seconds
                "consecutive_failures_threshold": 3,
                "notification_cooldown": 1800        # 30 minutes
            },
            "api_security": {
                "validate_signatures": True,
                "log_auth_attempts": True,
                "rate_limit_monitoring": True,
                "secure_credential_storage": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                return {**default_config, **user_config}
        
        return default_config
    
    def _load_exchange_configs(self) -> List[ExchangeConfig]:
        """Load exchange configurations."""
        exchanges = [
            # Major cryptocurrency exchanges
            ExchangeConfig(
                name="Binance",
                exchange_type=ExchangeType.BINANCE,
                base_url="https://api.binance.com",
                time_endpoint="/api/v3/time",
                timeout=5.0,
                rate_limit_per_minute=1200,
                timestamp_format="milliseconds"
            ),
            ExchangeConfig(
                name="Binance US",
                exchange_type=ExchangeType.BINANCE,
                base_url="https://api.binance.us",
                time_endpoint="/api/v3/time",
                timeout=5.0,
                rate_limit_per_minute=1200,
                timestamp_format="milliseconds"
            ),
            ExchangeConfig(
                name="Coinbase Pro",
                exchange_type=ExchangeType.COINBASE,
                base_url="https://api.exchange.coinbase.com",
                time_endpoint="/time",
                timeout=5.0,
                rate_limit_per_minute=600,
                timestamp_format="seconds"
            ),
            ExchangeConfig(
                name="Kraken",
                exchange_type=ExchangeType.KRAKEN,
                base_url="https://api.kraken.com",
                time_endpoint="/0/public/Time",
                timeout=10.0,
                rate_limit_per_minute=300,
                timestamp_format="seconds"
            ),
            ExchangeConfig(
                name="Bybit",
                exchange_type=ExchangeType.BYBIT,
                base_url="https://api.bybit.com",
                time_endpoint="/v5/market/time",
                timeout=5.0,
                rate_limit_per_minute=600,
                timestamp_format="milliseconds"
            ),
            ExchangeConfig(
                name="OKEx",
                exchange_type=ExchangeType.OKEX,
                base_url="https://www.okx.com",
                time_endpoint="/api/v5/public/time",
                timeout=5.0,
                rate_limit_per_minute=600,
                timestamp_format="milliseconds"
            ),
            ExchangeConfig(
                name="KuCoin",
                exchange_type=ExchangeType.KUCOIN,
                base_url="https://api.kucoin.com",
                time_endpoint="/api/v1/timestamp",
                timeout=5.0,
                rate_limit_per_minute=300,
                timestamp_format="milliseconds"
            ),
            ExchangeConfig(
                name="Huobi",
                exchange_type=ExchangeType.HUOBI,
                base_url="https://api.huobi.pro",
                time_endpoint="/v1/common/timestamp",
                timeout=5.0,
                rate_limit_per_minute=300,
                timestamp_format="milliseconds"
            )
        ]
        
        return exchanges
    
    def _check_rate_limit(self, exchange_name: str) -> bool:
        """Check if exchange rate limit allows request."""
        now = datetime.now(timezone.utc)
        
        if exchange_name not in self.rate_limits:
            self.rate_limits[exchange_name] = []
        
        # Remove old requests (older than 1 minute)
        cutoff_time = now - timedelta(minutes=1)
        self.rate_limits[exchange_name] = [
            req_time for req_time in self.rate_limits[exchange_name]
            if req_time > cutoff_time
        ]
        
        # Find exchange config
        exchange_config = next((e for e in self.exchanges if e.name == exchange_name), None)
        if not exchange_config:
            return False
        
        # Check if under rate limit
        if len(self.rate_limits[exchange_name]) >= exchange_config.rate_limit_per_minute:
            return False
        
        # Add current request
        self.rate_limits[exchange_name].append(now)
        return True
    
    async def sync_with_exchange(self, exchange_config: ExchangeConfig) -> Optional[ExchangeTimeSync]:
        """Synchronize with a specific exchange server time."""
        if not exchange_config.enabled:
            return None
        
        # Check rate limit
        if not self._check_rate_limit(exchange_config.name):
            logger.warning(f"⚠️ Rate limit exceeded for {exchange_config.name}")
            return ExchangeTimeSync(
                exchange=exchange_config.name,
                server_time=0,
                local_time=int(time.time() * 1000),
                offset_ms=float('inf'),
                network_delay_ms=float('inf'),
                timestamp=datetime.now(timezone.utc),
                status=TimeSyncStatus.RATE_LIMITED,
                response_time_ms=0
            )
        
        start_time = time.time()
        local_time_before = int(time.time() * 1000)
        
        try:
            logger.debug(f"🕐 Syncing with exchange: {exchange_config.name}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=exchange_config.timeout)) as session:
                url = f"{exchange_config.base_url}{exchange_config.time_endpoint}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        local_time_after = int(time.time() * 1000)
                        response_time_ms = (time.time() - start_time) * 1000
                        
                        # Parse server time based on exchange
                        server_time = self._parse_server_time(exchange_config, data)
                        
                        if server_time is None:
                            raise ValueError(f"Could not parse server time from {exchange_config.name}")
                        
                        # Calculate network delay and offset
                        network_delay_ms = (local_time_after - local_time_before) / 2
                        local_time_adjusted = local_time_before + network_delay_ms
                        offset_ms = server_time - local_time_adjusted
                        
                        # Determine sync status
                        if abs(offset_ms) <= self.config["alerts"]["drift_warning_threshold"]:
                            status = TimeSyncStatus.SYNCHRONIZED
                        elif abs(offset_ms) <= self.config["alerts"]["drift_critical_threshold"]:
                            status = TimeSyncStatus.DRIFT_WARNING
                        else:
                            status = TimeSyncStatus.DRIFT_CRITICAL
                        
                        sync_result = ExchangeTimeSync(
                            exchange=exchange_config.name,
                            server_time=server_time,
                            local_time=int(local_time_adjusted),
                            offset_ms=offset_ms,
                            network_delay_ms=network_delay_ms,
                            timestamp=datetime.now(timezone.utc),
                            status=status,
                            response_time_ms=response_time_ms,
                            auth_required=exchange_config.requires_auth
                        )
                        
                        logger.info(f"✅ Exchange sync successful: {exchange_config.name}")
                        logger.info(f"   Offset: {offset_ms:.2f}ms, Delay: {network_delay_ms:.2f}ms")
                        
                        # Update time offset cache
                        self.time_offsets[exchange_config.name] = offset_ms
                        self.last_sync_times[exchange_config.name] = datetime.now(timezone.utc)
                        
                        return sync_result
                    
                    else:
                        logger.error(f"❌ HTTP error {response.status} for {exchange_config.name}")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
            
        except Exception as e:
            logger.error(f"❌ Exchange sync failed for {exchange_config.name}: {e}")
            
            return ExchangeTimeSync(
                exchange=exchange_config.name,
                server_time=0,
                local_time=int(time.time() * 1000),
                offset_ms=float('inf'),
                network_delay_ms=float('inf'),
                timestamp=datetime.now(timezone.utc),
                status=TimeSyncStatus.UNREACHABLE,
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def _parse_server_time(self, exchange_config: ExchangeConfig, data: Dict[str, Any]) -> Optional[int]:
        """Parse server time from exchange response."""
        try:
            if exchange_config.exchange_type == ExchangeType.BINANCE:
                # Binance: {"serverTime": 1640995200000}
                server_time = data.get("serverTime")
                return int(server_time) if server_time else None
            
            elif exchange_config.exchange_type == ExchangeType.COINBASE:
                # Coinbase: {"iso": "2021-12-31T12:00:00.000Z", "epoch": 1640995200.000}
                epoch = data.get("epoch")
                if epoch:
                    return int(float(epoch) * 1000)  # Convert seconds to milliseconds
                return None
            
            elif exchange_config.exchange_type == ExchangeType.KRAKEN:
                # Kraken: {"error": [], "result": {"unixtime": 1640995200, "rfc1123": "..."}}
                result = data.get("result", {})
                unixtime = result.get("unixtime")
                return int(unixtime * 1000) if unixtime else None  # Convert to milliseconds
            
            elif exchange_config.exchange_type == ExchangeType.BYBIT:
                # Bybit: {"retCode": 0, "retMsg": "OK", "result": {"timeSecond": "1640995200", "timeNano": "1640995200000000000"}}
                result = data.get("result", {})
                time_nano = result.get("timeNano")
                if time_nano:
                    return int(int(time_nano) / 1000000)  # Convert nanoseconds to milliseconds
                time_second = result.get("timeSecond")
                return int(time_second) * 1000 if time_second else None
            
            elif exchange_config.exchange_type == ExchangeType.OKEX:
                # OKEx: {"code": "0", "msg": "", "data": [{"ts": "1640995200000"}]}
                data_list = data.get("data", [])
                if data_list and len(data_list) > 0:
                    ts = data_list[0].get("ts")
                    return int(ts) if ts else None
                return None
            
            elif exchange_config.exchange_type == ExchangeType.KUCOIN:
                # KuCoin: {"code": "200000", "data": 1640995200000}
                server_time = data.get("data")
                return int(server_time) if server_time else None
            
            elif exchange_config.exchange_type == ExchangeType.HUOBI:
                # Huobi: {"status": "ok", "data": 1640995200000}
                server_time = data.get("data")
                return int(server_time) if server_time else None
            
            else:
                # Generic fallback - look for common timestamp fields
                for field in ["serverTime", "timestamp", "time", "ts", "data", "result"]:
                    if field in data:
                        value = data[field]
                        if isinstance(value, (int, float)):
                            # Assume milliseconds if > 1e12, otherwise seconds
                            if value > 1e12:
                                return int(value)
                            else:
                                return int(value * 1000)
                        elif isinstance(value, str) and value.isdigit():
                            num_value = int(value)
                            return num_value if num_value > 1e12 else num_value * 1000
                
                return None
        
        except Exception as e:
            logger.error(f"❌ Error parsing server time for {exchange_config.name}: {e}")
            return None
    
    async def sync_all_exchanges(self) -> Dict[str, ExchangeTimeSync]:
        """Synchronize with all configured exchanges."""
        logger.info("🌐 Starting multi-exchange time synchronization")
        
        # Filter enabled exchanges
        enabled_exchanges = [e for e in self.exchanges if e.enabled]
        
        if self.config["synchronization"]["concurrent_syncs"]:
            # Concurrent synchronization
            sync_tasks = [
                self.sync_with_exchange(exchange) 
                for exchange in enabled_exchanges
            ]
            
            sync_results = await asyncio.gather(*sync_tasks, return_exceptions=True)
        else:
            # Sequential synchronization
            sync_results = []
            for exchange in enabled_exchanges:
                result = await self.sync_with_exchange(exchange)
                sync_results.append(result)
        
        # Process results
        results = {}
        for result in sync_results:
            if isinstance(result, ExchangeTimeSync) and result:
                results[result.exchange] = result
                
                # Store in history
                if result.exchange not in self.sync_history:
                    self.sync_history[result.exchange] = []
                
                self.sync_history[result.exchange].append(result)
                
                # Cleanup old history
                cutoff_time = datetime.now(timezone.utc) - timedelta(
                    hours=self.config["monitoring"]["history_retention_hours"]
                )
                self.sync_history[result.exchange] = [
                    sync for sync in self.sync_history[result.exchange]
                    if sync.timestamp > cutoff_time
                ]
        
        logger.info(f"✅ Multi-exchange sync completed: {len(results)}/{len(enabled_exchanges)} exchanges")
        
        return results
    
    def get_exchange_timestamp(self, exchange_name: str, apply_offset: bool = True) -> int:
        """Get current timestamp adjusted for exchange time offset."""
        current_time_ms = int(time.time() * 1000)
        
        if apply_offset and exchange_name in self.time_offsets:
            # Apply known offset to get exchange-synchronized timestamp
            offset_ms = self.time_offsets[exchange_name]
            return int(current_time_ms + offset_ms)
        
        return current_time_ms
    
    def validate_timestamp_for_signed_request(self, exchange_name: str, 
                                            request_timestamp: int) -> TimestampValidation:
        """Validate timestamp for signed API requests."""
        server_timestamp = self.get_exchange_timestamp(exchange_name, apply_offset=True)
        offset_ms = abs(request_timestamp - server_timestamp)
        window_ms = self.config["synchronization"]["timestamp_window_ms"]
        
        within_window = offset_ms <= window_ms
        
        # Get recommended timestamp (current time with offset)
        recommended_timestamp = self.get_exchange_timestamp(exchange_name, apply_offset=True)
        
        if within_window:
            status = "VALID"
        elif offset_ms <= window_ms * 2:
            status = "WARNING"
        else:
            status = "REJECTED"
        
        return TimestampValidation(
            exchange=exchange_name,
            request_timestamp=request_timestamp,
            server_timestamp=server_timestamp,
            offset_ms=offset_ms,
            within_window=within_window,
            window_ms=window_ms,
            recommended_timestamp=recommended_timestamp,
            status=status
        )
    
    def generate_signed_request_timestamp(self, exchange_name: str) -> int:
        """Generate optimal timestamp for signed API requests."""
        return self.get_exchange_timestamp(exchange_name, apply_offset=True)
    
    def generate_exchange_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive exchange time sync health report."""
        now = datetime.now(timezone.utc)
        
        # Get recent sync results (last hour)
        recent_syncs = {}
        for exchange_name, history in self.sync_history.items():
            recent_syncs[exchange_name] = [
                sync for sync in history
                if now - sync.timestamp <= timedelta(hours=1)
            ]
        
        # Calculate metrics
        synchronized_exchanges = []
        failed_exchanges = []
        exchange_metrics = {}
        
        for exchange_name, syncs in recent_syncs.items():
            if syncs:
                latest_sync = syncs[-1]
                
                if latest_sync.status == TimeSyncStatus.SYNCHRONIZED:
                    synchronized_exchanges.append(exchange_name)
                elif latest_sync.status in [TimeSyncStatus.UNREACHABLE, TimeSyncStatus.ERROR]:
                    failed_exchanges.append(exchange_name)
                
                # Calculate metrics for this exchange
                offsets = [sync.offset_ms for sync in syncs if sync.status != TimeSyncStatus.UNREACHABLE]
                delays = [sync.network_delay_ms for sync in syncs if sync.status != TimeSyncStatus.UNREACHABLE]
                
                exchange_metrics[exchange_name] = {
                    "latest_offset_ms": latest_sync.offset_ms,
                    "average_offset_ms": statistics.mean(offsets) if offsets else float('inf'),
                    "max_offset_ms": max(abs(o) for o in offsets) if offsets else float('inf'),
                    "average_delay_ms": statistics.mean(delays) if delays else float('inf'),
                    "sync_count": len(syncs),
                    "success_rate": len([s for s in syncs if s.status == TimeSyncStatus.SYNCHRONIZED]) / len(syncs) * 100,
                    "status": latest_sync.status.value
                }
        
        # Overall health assessment
        total_exchanges = len(self.exchanges)
        active_exchanges = len(synchronized_exchanges)
        
        if active_exchanges >= total_exchanges * 0.8:
            overall_health = "EXCELLENT"
        elif active_exchanges >= total_exchanges * 0.6:
            overall_health = "GOOD"
        elif active_exchanges >= total_exchanges * 0.4:
            overall_health = "POOR"
        else:
            overall_health = "CRITICAL"
        
        return {
            "timestamp": now.isoformat(),
            "overall_health": overall_health,
            "total_exchanges": total_exchanges,
            "synchronized_exchanges": synchronized_exchanges,
            "failed_exchanges": failed_exchanges,
            "active_exchange_count": len(synchronized_exchanges),
            "failed_exchange_count": len(failed_exchanges),
            "exchange_metrics": exchange_metrics,
            "recommendations": self._generate_recommendations(exchange_metrics, overall_health)
        }
    
    def _generate_recommendations(self, exchange_metrics: Dict[str, Any], 
                                overall_health: str) -> List[str]:
        """Generate recommendations based on exchange sync health."""
        recommendations = []
        
        if overall_health == "CRITICAL":
            recommendations.append("🚨 CRITICAL: Multiple exchange sync failures - investigate network connectivity")
        elif overall_health == "POOR":
            recommendations.append("⚠️ HIGH: Exchange sync issues detected - monitor closely")
        
        # Check individual exchange issues
        for exchange_name, metrics in exchange_metrics.items():
            if metrics["success_rate"] < 80:
                recommendations.append(f"⚠️ MEDIUM: {exchange_name} sync reliability issues ({metrics['success_rate']:.1f}%)")
            
            if abs(metrics["latest_offset_ms"]) > 5000:
                recommendations.append(f"🚨 HIGH: {exchange_name} time drift critical ({metrics['latest_offset_ms']:.1f}ms)")
            elif abs(metrics["latest_offset_ms"]) > 1000:
                recommendations.append(f"⚠️ MEDIUM: {exchange_name} time drift warning ({metrics['latest_offset_ms']:.1f}ms)")
        
        # General recommendations
        if overall_health in ["EXCELLENT", "GOOD"]:
            recommendations.append("✅ EXCELLENT: Exchange time synchronization performing well")
        
        recommendations.extend([
            "🔍 MONITOR: Regular exchange time sync health checks",
            "📋 MAINTAIN: Keep exchange configurations updated",
            "🔧 OPTIMIZE: Adjust sync intervals based on trading activity"
        ])
        
        return recommendations
    
    def save_exchange_sync_reports(self):
        """Save comprehensive exchange sync reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate health report
        health_report = self.generate_exchange_health_report()
        
        # Save JSON report
        json_file = f"exchange_time_sync/reports/exchange_sync_health_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(health_report, f, indent=2)
        
        # Save HTML report
        html_file = f"exchange_time_sync/reports/exchange_sync_health_{timestamp}.html"
        self._generate_html_report(health_report, html_file)
        
        logger.info(f"📄 Exchange sync reports saved: {json_file}")
    
    def _generate_html_report(self, health_report: Dict[str, Any], filename: str):
        """Generate HTML exchange sync health report."""
        health_colors = {
            "EXCELLENT": "#28a745",
            "GOOD": "#ffc107",
            "POOR": "#fd7e14", 
            "CRITICAL": "#dc3545"
        }
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Exchange Time Sync Report - AI Trading Bot</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .status-card {{ background: {health_colors.get(health_report['overall_health'], '#6c757d')}; color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
        .exchange-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .exchange-table th, .exchange-table td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        .exchange-table th {{ background: #f8f9fa; font-weight: bold; }}
        .exchange-sync {{ background-color: #d4edda; }}
        .exchange-failed {{ background-color: #f8d7da; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕐 Exchange Time Synchronization Report</h1>
            <h2>AI Trading Bot - Exchange Server Time Sync</h2>
            <p><strong>Report Time:</strong> {health_report['timestamp']}</p>
        </div>
        
        <div class="status-card">
            <h3>🎯 Overall Sync Health</h3>
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="font-size: 36px; font-weight: bold;">{health_report['overall_health']}</div>
                <div>
                    <div style="font-size: 18px;">Active: {health_report['active_exchange_count']}/{health_report['total_exchanges']} exchanges</div>
                    <div>Failed: {health_report['failed_exchange_count']} exchanges</div>
                </div>
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>Synchronized</h3>
                <div style="font-size: 32px; font-weight: bold; color: #28a745;">{health_report['active_exchange_count']}</div>
            </div>
            <div class="metric-card">
                <h3>Failed</h3>
                <div style="font-size: 32px; font-weight: bold; color: #dc3545;">{health_report['failed_exchange_count']}</div>
            </div>
            <div class="metric-card">
                <h3>Success Rate</h3>
                <div style="font-size: 32px; font-weight: bold; color: #007bff;">{health_report['active_exchange_count']/health_report['total_exchanges']*100:.1f}%</div>
            </div>
        </div>
        
        <h2>📊 Exchange Status</h2>
        <table class="exchange-table">
            <tr>
                <th>Exchange</th>
                <th>Status</th>
                <th>Latest Offset (ms)</th>
                <th>Avg Delay (ms)</th>
                <th>Success Rate</th>
            </tr>
"""
        
        # Add exchange metrics
        for exchange_name, metrics in health_report['exchange_metrics'].items():
            status_class = "exchange-sync" if exchange_name in health_report['synchronized_exchanges'] else "exchange-failed"
            status_icon = "✅" if exchange_name in health_report['synchronized_exchanges'] else "❌"
            
            html_content += f"""
            <tr class="{status_class}">
                <td>{exchange_name}</td>
                <td>{status_icon} {metrics['status'].title()}</td>
                <td>{metrics['latest_offset_ms']:.1f}</td>
                <td>{metrics['average_delay_ms']:.1f}</td>
                <td>{metrics['success_rate']:.1f}%</td>
            </tr>
"""
        
        html_content += f"""
        </table>
        
        <div class="recommendations">
            <h3>📈 Recommendations</h3>
            <ul>
"""
        
        for recommendation in health_report['recommendations']:
            html_content += f"                <li>{recommendation}</li>\n"
        
        html_content += """
            </ul>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>🔧 Trading Integration</h3>
            <p><strong>Signed Request Timestamps:</strong> Use exchange-synchronized timestamps for API authentication</p>
            <p><strong>Order Timing:</strong> Leverage precise exchange time for optimal order execution</p>
            <p><strong>Rate Limiting:</strong> Coordinate API calls with exchange server time</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html_content)
    
    async def start_continuous_monitoring(self):
        """Start continuous exchange time monitoring."""
        logger.info("🚀 Starting continuous exchange time monitoring")
        self.monitoring_active = True
        
        # Start monitoring tasks
        sync_task = asyncio.create_task(self._sync_monitoring_loop())
        health_task = asyncio.create_task(self._health_monitoring_loop())
        report_task = asyncio.create_task(self._report_generation_loop())
        
        try:
            await asyncio.gather(sync_task, health_task, report_task)
        except Exception as e:
            logger.error(f"❌ Exchange monitoring error: {e}")
        finally:
            self.monitoring_active = False
    
    async def _sync_monitoring_loop(self):
        """Continuous synchronization monitoring loop."""
        while self.monitoring_active:
            try:
                # Perform multi-exchange sync
                sync_results = await self.sync_all_exchanges()
                
                # Log sync summary
                successful_syncs = len([r for r in sync_results.values() if r.status == TimeSyncStatus.SYNCHRONIZED])
                logger.info(f"📊 Exchange sync: {successful_syncs}/{len(sync_results)} successful")
                
                # Wait for next sync cycle
                await asyncio.sleep(self.config["synchronization"]["sync_interval"])
                
            except Exception as e:
                logger.error(f"❌ Exchange sync monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring loop."""
        while self.monitoring_active:
            try:
                # Generate health report
                health_report = self.generate_exchange_health_report()
                
                # Log health status
                logger.info(f"📊 Exchange Health: {health_report['overall_health']} "
                          f"({health_report['active_exchange_count']}/{health_report['total_exchanges']} active)")
                
                # Check for critical issues
                if health_report['overall_health'] in ["CRITICAL", "POOR"]:
                    logger.error("🚨 Exchange sync health critical - immediate attention required")
                
                # Wait for next health check
                await asyncio.sleep(self.config["monitoring"]["health_check_interval"])
                
            except Exception as e:
                logger.error(f"❌ Exchange health monitoring error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _report_generation_loop(self):
        """Continuous report generation loop."""
        while self.monitoring_active:
            try:
                # Generate and save reports
                self.save_exchange_sync_reports()
                
                # Wait for next report generation
                await asyncio.sleep(self.config["monitoring"]["report_generation_interval"])
                
            except Exception as e:
                logger.error(f"❌ Exchange report generation error: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes before retry
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        logger.info("🛑 Stopping exchange time monitoring")
        self.monitoring_active = False

async def main():
    """Demonstrate exchange time synchronization system."""
    print("🕐 Exchange Time Synchronization System - AI Trading Bot")
    print("=" * 80)
    
    # Initialize exchange sync system
    exchange_sync = ExchangeTimeSynchronizationSystem()
    
    print(f"\n🌐 Performing exchange time synchronization...")
    
    # Perform initial sync with all exchanges
    sync_results = await exchange_sync.sync_all_exchanges()
    
    print(f"✅ Synchronized with {len(sync_results)} exchanges")
    
    # Show sync results
    print(f"\n📊 Exchange Sync Results:")
    for exchange_name, sync_result in sync_results.items():
        if sync_result.status != TimeSyncStatus.UNREACHABLE:
            status_icon = "✅" if sync_result.status == TimeSyncStatus.SYNCHRONIZED else "⚠️"
            print(f"   {status_icon} {exchange_name}: {sync_result.offset_ms:.2f}ms offset, {sync_result.network_delay_ms:.2f}ms delay")
        else:
            print(f"   ❌ {exchange_name}: Unreachable")
    
    # Demonstrate signed request timestamp generation
    print(f"\n🔐 Signed Request Timestamp Examples:")
    for exchange_name in ["Binance", "Coinbase Pro", "Kraken"]:
        if exchange_name in sync_results:
            timestamp = exchange_sync.generate_signed_request_timestamp(exchange_name)
            validation = exchange_sync.validate_timestamp_for_signed_request(exchange_name, timestamp)
            print(f"   🎯 {exchange_name}: {timestamp} ({validation.status})")
    
    # Generate health report
    print(f"\n📊 Generating exchange health report...")
    health_report = exchange_sync.generate_exchange_health_report()
    
    print(f"✅ Exchange Health Summary:")
    print(f"   Overall Health: {health_report['overall_health']}")
    print(f"   Active Exchanges: {health_report['active_exchange_count']}/{health_report['total_exchanges']}")
    print(f"   Failed Exchanges: {health_report['failed_exchange_count']}")
    
    # Save reports
    exchange_sync.save_exchange_sync_reports()
    print(f"\n📄 Reports saved to exchange_time_sync/reports/")
    
    # Show recommendations
    if health_report['recommendations']:
        print(f"\n📋 Recommendations:")
        for rec in health_report['recommendations'][:3]:  # Show top 3
            print(f"   • {rec}")
    
    print(f"\n🎉 Exchange Time Synchronization System demonstration completed!")
    print(f"💡 For continuous monitoring, run: await exchange_sync.start_continuous_monitoring()")

if __name__ == "__main__":
    asyncio.run(main()) 