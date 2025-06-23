#!/usr/bin/env python3
"""
Exchange Time Synchronization System
Synchronizes with exchange server times for accurate trading operations
"""

import os
import time
import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExchangeType(Enum):
    """Supported exchange types."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKEX = "okex"

class TimeSyncStatus(Enum):
    """Exchange time synchronization status."""
    SYNCHRONIZED = "synchronized"
    DRIFT_WARNING = "drift_warning"
    DRIFT_CRITICAL = "drift_critical"
    UNREACHABLE = "unreachable"
    RATE_LIMITED = "rate_limited"

@dataclass
class ExchangeConfig:
    """Exchange configuration for time synchronization."""
    name: str
    exchange_type: ExchangeType
    base_url: str
    time_endpoint: str
    timeout: float = 10.0
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

class ExchangeTimeSynchronizationSystem:
    """Comprehensive exchange time synchronization system."""
    
    def __init__(self):
        """Initialize the exchange time synchronization system."""
        self.exchanges = self._load_exchange_configs()
        self.sync_history: Dict[str, List[ExchangeTimeSync]] = {}
        self.time_offsets: Dict[str, float] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        self.monitoring_active = False
        
        # Create directories
        os.makedirs("exchange_time_sync/reports", exist_ok=True)
        os.makedirs("exchange_time_sync/logs", exist_ok=True)
        
        logger.info("✅ Exchange Time Synchronization System initialized")
        logger.info(f"   Configured {len(self.exchanges)} exchanges")
    
    def _load_exchange_configs(self) -> List[ExchangeConfig]:
        """Load exchange configurations."""
        return [
            ExchangeConfig(
                name="Binance",
                exchange_type=ExchangeType.BINANCE,
                base_url="https://api.binance.com",
                time_endpoint="/api/v3/time",
                timeout=5.0
            ),
            ExchangeConfig(
                name="Binance US",
                exchange_type=ExchangeType.BINANCE,
                base_url="https://api.binance.us",
                time_endpoint="/api/v3/time",
                timeout=5.0
            ),
            ExchangeConfig(
                name="Coinbase Pro",
                exchange_type=ExchangeType.COINBASE,
                base_url="https://api.exchange.coinbase.com",
                time_endpoint="/time",
                timeout=5.0
            ),
            ExchangeConfig(
                name="Kraken",
                exchange_type=ExchangeType.KRAKEN,
                base_url="https://api.kraken.com",
                time_endpoint="/0/public/Time",
                timeout=10.0
            ),
            ExchangeConfig(
                name="Bybit",
                exchange_type=ExchangeType.BYBIT,
                base_url="https://api.bybit.com",
                time_endpoint="/v5/market/time",
                timeout=5.0
            ),
            ExchangeConfig(
                name="OKEx",
                exchange_type=ExchangeType.OKEX,
                base_url="https://www.okx.com",
                time_endpoint="/api/v5/public/time",
                timeout=5.0
            )
        ]
    
    async def sync_with_exchange(self, exchange_config: ExchangeConfig) -> Optional[ExchangeTimeSync]:
        """Synchronize with a specific exchange server time."""
        if not exchange_config.enabled:
            return None
        
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
                        
                        # Parse server time based on exchange
                        server_time = self._parse_server_time(exchange_config, data)
                        
                        if server_time is None:
                            raise ValueError(f"Could not parse server time from {exchange_config.name}")
                        
                        # Calculate network delay and offset
                        network_delay_ms = (local_time_after - local_time_before) / 2
                        local_time_adjusted = local_time_before + network_delay_ms
                        offset_ms = server_time - local_time_adjusted
                        
                        # Determine sync status
                        if abs(offset_ms) <= 1000:  # 1 second
                            status = TimeSyncStatus.SYNCHRONIZED
                        elif abs(offset_ms) <= 5000:  # 5 seconds
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
                            status=status
                        )
                        
                        logger.info(f"✅ Exchange sync successful: {exchange_config.name}")
                        logger.info(f"   Offset: {offset_ms:.2f}ms, Delay: {network_delay_ms:.2f}ms")
                        
                        # Update time offset cache
                        self.time_offsets[exchange_config.name] = offset_ms
                        self.last_sync_times[exchange_config.name] = datetime.now(timezone.utc)
                        
                        return sync_result
                    
                    else:
                        logger.error(f"❌ HTTP error {response.status} for {exchange_config.name}")
                        raise Exception(f"HTTP {response.status}")
            
        except Exception as e:
            logger.error(f"❌ Exchange sync failed for {exchange_config.name}: {e}")
            
            return ExchangeTimeSync(
                exchange=exchange_config.name,
                server_time=0,
                local_time=int(time.time() * 1000),
                offset_ms=float('inf'),
                network_delay_ms=float('inf'),
                timestamp=datetime.now(timezone.utc),
                status=TimeSyncStatus.UNREACHABLE
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
            
            else:
                # Generic fallback
                for field in ["serverTime", "timestamp", "time", "ts", "data"]:
                    if field in data:
                        value = data[field]
                        if isinstance(value, (int, float)):
                            return int(value * 1000) if value < 1e12 else int(value)
                return None
        
        except Exception as e:
            logger.error(f"❌ Error parsing server time for {exchange_config.name}: {e}")
            return None
    
    async def sync_all_exchanges(self) -> Dict[str, ExchangeTimeSync]:
        """Synchronize with all configured exchanges."""
        logger.info("🌐 Starting multi-exchange time synchronization")
        
        # Concurrent synchronization
        sync_tasks = [
            self.sync_with_exchange(exchange) 
            for exchange in self.exchanges if exchange.enabled
        ]
        
        sync_results = await asyncio.gather(*sync_tasks, return_exceptions=True)
        
        # Process results
        results = {}
        for result in sync_results:
            if isinstance(result, ExchangeTimeSync) and result:
                results[result.exchange] = result
                
                # Store in history
                if result.exchange not in self.sync_history:
                    self.sync_history[result.exchange] = []
                
                self.sync_history[result.exchange].append(result)
                
                # Cleanup old history (keep 24 hours)
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                self.sync_history[result.exchange] = [
                    sync for sync in self.sync_history[result.exchange]
                    if sync.timestamp > cutoff_time
                ]
        
        logger.info(f"✅ Multi-exchange sync completed: {len(results)} exchanges")
        return results
    
    def get_exchange_timestamp(self, exchange_name: str, apply_offset: bool = True) -> int:
        """Get current timestamp adjusted for exchange time offset."""
        current_time_ms = int(time.time() * 1000)
        
        if apply_offset and exchange_name in self.time_offsets:
            offset_ms = self.time_offsets[exchange_name]
            return int(current_time_ms + offset_ms)
        
        return current_time_ms
    
    def generate_signed_request_timestamp(self, exchange_name: str) -> int:
        """Generate optimal timestamp for signed API requests."""
        return self.get_exchange_timestamp(exchange_name, apply_offset=True)
    
    def validate_timestamp_window(self, exchange_name: str, request_timestamp: int, window_ms: int = 5000) -> bool:
        """Validate if timestamp is within acceptable window for signed requests."""
        server_timestamp = self.get_exchange_timestamp(exchange_name, apply_offset=True)
        offset_ms = abs(request_timestamp - server_timestamp)
        return offset_ms <= window_ms
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate exchange time sync health report."""
        now = datetime.now(timezone.utc)
        
        # Get recent sync results
        recent_syncs = {}
        for exchange_name, history in self.sync_history.items():
            recent_syncs[exchange_name] = [
                sync for sync in history
                if now - sync.timestamp <= timedelta(hours=1)
            ]
        
        # Calculate metrics
        synchronized_exchanges = []
        failed_exchanges = []
        
        for exchange_name, syncs in recent_syncs.items():
            if syncs:
                latest_sync = syncs[-1]
                if latest_sync.status == TimeSyncStatus.SYNCHRONIZED:
                    synchronized_exchanges.append(exchange_name)
                elif latest_sync.status == TimeSyncStatus.UNREACHABLE:
                    failed_exchanges.append(exchange_name)
        
        # Overall health
        total_exchanges = len(self.exchanges)
        active_exchanges = len(synchronized_exchanges)
        
        if active_exchanges >= total_exchanges * 0.8:
            overall_health = "EXCELLENT"
        elif active_exchanges >= total_exchanges * 0.6:
            overall_health = "GOOD"
        else:
            overall_health = "POOR"
        
        return {
            "timestamp": now.isoformat(),
            "overall_health": overall_health,
            "total_exchanges": total_exchanges,
            "synchronized_exchanges": synchronized_exchanges,
            "failed_exchanges": failed_exchanges,
            "active_exchange_count": len(synchronized_exchanges),
            "success_rate": (len(synchronized_exchanges) / total_exchanges * 100) if total_exchanges > 0 else 0
        }
    
    def save_reports(self):
        """Save exchange sync reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        health_report = self.generate_health_report()
        
        # Save JSON report
        json_file = f"exchange_time_sync/reports/exchange_sync_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(health_report, f, indent=2)
        
        logger.info(f"📄 Exchange sync report saved: {json_file}")
    
    async def start_monitoring(self):
        """Start continuous exchange time monitoring."""
        logger.info("🚀 Starting continuous exchange time monitoring")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                sync_results = await self.sync_all_exchanges()
                self.save_reports()
                await asyncio.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(60)

async def main():
    """Demonstrate exchange time synchronization system."""
    print("🕐 Exchange Time Synchronization System - AI Trading Bot")
    print("=" * 80)
    
    # Initialize exchange sync system
    exchange_sync = ExchangeTimeSynchronizationSystem()
    
    print(f"\n🌐 Performing exchange time synchronization...")
    
    # Sync with all exchanges
    sync_results = await exchange_sync.sync_all_exchanges()
    
    print(f"✅ Synchronized with {len(sync_results)} exchanges")
    
    # Show sync results
    print(f"\n📊 Exchange Sync Results:")
    for exchange_name, sync_result in sync_results.items():
        if sync_result.status != TimeSyncStatus.UNREACHABLE:
            status_icon = "✅" if sync_result.status == TimeSyncStatus.SYNCHRONIZED else "⚠️"
            print(f"   {status_icon} {exchange_name}: {sync_result.offset_ms:.2f}ms offset")
        else:
            print(f"   ❌ {exchange_name}: Unreachable")
    
    # Demonstrate signed request timestamps
    print(f"\n🔐 Signed Request Timestamp Examples:")
    for exchange_name in ["Binance", "Coinbase Pro", "Kraken"]:
        if exchange_name in sync_results:
            timestamp = exchange_sync.generate_signed_request_timestamp(exchange_name)
            is_valid = exchange_sync.validate_timestamp_window(exchange_name, timestamp)
            print(f"   🎯 {exchange_name}: {timestamp} ({'Valid' if is_valid else 'Invalid'})")
    
    # Generate health report
    health_report = exchange_sync.generate_health_report()
    print(f"\n📊 Exchange Health Summary:")
    print(f"   Overall Health: {health_report['overall_health']}")
    print(f"   Active Exchanges: {health_report['active_exchange_count']}/{health_report['total_exchanges']}")
    print(f"   Success Rate: {health_report['success_rate']:.1f}%")
    
    # Save reports
    exchange_sync.save_reports()
    print(f"\n📄 Reports saved to exchange_time_sync/reports/")
    
    print(f"\n🎉 Exchange Time Synchronization System demonstration completed!")

if __name__ == "__main__":
    asyncio.run(main()) 