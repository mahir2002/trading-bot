#!/usr/bin/env python3
"""
Performance Monitor for AI Trading Bot
Tracks system performance, trading metrics, and provides optimization insights
"""

import time
import json
import logging
import psutil
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    api_calls_per_minute: int
    cache_hit_rate: float

@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_duration_minutes: float
    active_positions: int
    portfolio_value: float

@dataclass
class APIMetrics:
    """API performance metrics"""
    timestamp: datetime
    endpoint: str
    response_time_ms: float
    status_code: int
    success: bool
    cache_hit: bool
    retry_count: int

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, db_path: str = "performance_monitor.db"):
        self.db_path = db_path
        self.monitoring = False
        self.monitor_thread = None
        self.api_calls = []
        self.system_metrics = []
        self.trading_metrics = []
        
        # Initialize database
        self._init_database()
        
        # Performance tracking
        self.start_time = datetime.now()
        self.last_network_stats = psutil.net_io_counters()
        
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                memory_percent REAL,
                memory_used_mb REAL,
                disk_usage_percent REAL,
                network_sent_mb REAL,
                network_recv_mb REAL,
                active_threads INTEGER,
                api_calls_per_minute INTEGER,
                cache_hit_rate REAL
            )
        ''')
        
        # Trading metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                total_pnl REAL,
                daily_pnl REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                avg_trade_duration_minutes REAL,
                active_positions INTEGER,
                portfolio_value REAL
            )
        ''')
        
        # API metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                endpoint TEXT,
                response_time_ms REAL,
                status_code INTEGER,
                success BOOLEAN,
                cache_hit BOOLEAN,
                retry_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Performance monitor database initialized: {self.db_path}")
    
    def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous performance monitoring"""
        if self.monitoring:
            logger.warning("⚠️ Monitoring already active")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"🚀 Performance monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ Performance monitoring stopped")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self._store_system_metrics(system_metrics)
                
                # Clean old data (keep last 7 days)
                self._cleanup_old_data()
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(interval_seconds)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network stats
        network = psutil.net_io_counters()
        network_sent_mb = (network.bytes_sent - self.last_network_stats.bytes_sent) / 1024 / 1024
        network_recv_mb = (network.bytes_recv - self.last_network_stats.bytes_recv) / 1024 / 1024
        self.last_network_stats = network
        
        # Thread count
        active_threads = threading.active_count()
        
        # API calls per minute (from last minute)
        now = datetime.now()
        recent_calls = [call for call in self.api_calls 
                       if now - call['timestamp'] < timedelta(minutes=1)]
        api_calls_per_minute = len(recent_calls)
        
        # Cache hit rate
        cache_hits = sum(1 for call in recent_calls if call.get('cache_hit', False))
        cache_hit_rate = (cache_hits / len(recent_calls) * 100) if recent_calls else 0
        
        return SystemMetrics(
            timestamp=now,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_usage_percent=disk.percent,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_threads=active_threads,
            api_calls_per_minute=api_calls_per_minute,
            cache_hit_rate=cache_hit_rate
        )
    
    def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_metrics (
                timestamp, cpu_percent, memory_percent, memory_used_mb,
                disk_usage_percent, network_sent_mb, network_recv_mb,
                active_threads, api_calls_per_minute, cache_hit_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp.isoformat(),
            metrics.cpu_percent,
            metrics.memory_percent,
            metrics.memory_used_mb,
            metrics.disk_usage_percent,
            metrics.network_sent_mb,
            metrics.network_recv_mb,
            metrics.active_threads,
            metrics.api_calls_per_minute,
            metrics.cache_hit_rate
        ))
        
        conn.commit()
        conn.close()
    
    def record_api_call(self, endpoint: str, response_time_ms: float, 
                       status_code: int, success: bool, cache_hit: bool = False, 
                       retry_count: int = 0):
        """Record API call metrics"""
        api_metric = {
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'response_time_ms': response_time_ms,
            'status_code': status_code,
            'success': success,
            'cache_hit': cache_hit,
            'retry_count': retry_count
        }
        
        self.api_calls.append(api_metric)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_metrics (
                timestamp, endpoint, response_time_ms, status_code,
                success, cache_hit, retry_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            api_metric['timestamp'].isoformat(),
            endpoint,
            response_time_ms,
            status_code,
            success,
            cache_hit,
            retry_count
        ))
        
        conn.commit()
        conn.close()
        
        # Keep only recent API calls in memory
        cutoff = datetime.now() - timedelta(hours=1)
        self.api_calls = [call for call in self.api_calls if call['timestamp'] > cutoff]
    
    def record_trading_metrics(self, total_trades: int, winning_trades: int,
                             total_pnl: float, daily_pnl: float, max_drawdown: float,
                             sharpe_ratio: float, active_positions: int,
                             portfolio_value: float, avg_trade_duration_minutes: float = 0):
        """Record trading performance metrics"""
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        trading_metric = TradingMetrics(
            timestamp=datetime.now(),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            avg_trade_duration_minutes=avg_trade_duration_minutes,
            active_positions=active_positions,
            portfolio_value=portfolio_value
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trading_metrics (
                timestamp, total_trades, winning_trades, losing_trades,
                win_rate, total_pnl, daily_pnl, max_drawdown,
                sharpe_ratio, avg_trade_duration_minutes, active_positions,
                portfolio_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trading_metric.timestamp.isoformat(),
            total_trades, winning_trades, losing_trades, win_rate,
            total_pnl, daily_pnl, max_drawdown, sharpe_ratio,
            avg_trade_duration_minutes, active_positions, portfolio_value
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_summary(self, hours: int = 24) -> Dict:
        """Get performance summary for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # System metrics summary
        cursor.execute('''
            SELECT 
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(api_calls_per_minute) as avg_api_calls,
                AVG(cache_hit_rate) as avg_cache_hit_rate
            FROM system_metrics 
            WHERE timestamp > ?
        ''', (cutoff.isoformat(),))
        
        system_summary = cursor.fetchone()
        
        # API metrics summary
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                AVG(response_time_ms) as avg_response_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as cache_hits
            FROM api_metrics 
            WHERE timestamp > ?
        ''', (cutoff.isoformat(),))
        
        api_summary = cursor.fetchone()
        
        # Trading metrics summary (latest)
        cursor.execute('''
            SELECT * FROM trading_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        trading_summary = cursor.fetchone()
        
        conn.close()
        
        # Calculate uptime
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime_hours': uptime.total_seconds() / 3600,
            'system': {
                'avg_cpu_percent': system_summary[0] if system_summary[0] else 0,
                'max_cpu_percent': system_summary[1] if system_summary[1] else 0,
                'avg_memory_percent': system_summary[2] if system_summary[2] else 0,
                'max_memory_percent': system_summary[3] if system_summary[3] else 0,
                'avg_api_calls_per_minute': system_summary[4] if system_summary[4] else 0,
                'avg_cache_hit_rate': system_summary[5] if system_summary[5] else 0
            },
            'api': {
                'total_calls': api_summary[0] if api_summary[0] else 0,
                'avg_response_time_ms': api_summary[1] if api_summary[1] else 0,
                'successful_calls': api_summary[2] if api_summary[2] else 0,
                'cache_hits': api_summary[3] if api_summary[3] else 0,
                'success_rate': (api_summary[2] / api_summary[0] * 100) if api_summary[0] else 0,
                'cache_hit_rate': (api_summary[3] / api_summary[0] * 100) if api_summary[0] else 0
            },
            'trading': {
                'total_trades': trading_summary[2] if trading_summary else 0,
                'win_rate': trading_summary[5] if trading_summary else 0,
                'total_pnl': trading_summary[6] if trading_summary else 0,
                'daily_pnl': trading_summary[7] if trading_summary else 0,
                'max_drawdown': trading_summary[8] if trading_summary else 0,
                'sharpe_ratio': trading_summary[9] if trading_summary else 0,
                'active_positions': trading_summary[11] if trading_summary else 0,
                'portfolio_value': trading_summary[12] if trading_summary else 0
            }
        }
    
    def _cleanup_old_data(self):
        """Clean up old data (keep last 7 days)"""
        cutoff = datetime.now() - timedelta(days=7)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff.isoformat(),))
        cursor.execute('DELETE FROM api_metrics WHERE timestamp < ?', (cutoff.isoformat(),))
        cursor.execute('DELETE FROM trading_metrics WHERE timestamp < ?', (cutoff.isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        summary = self.get_performance_summary(hours=1)
        recommendations = []
        
        # CPU recommendations
        if summary['system']['avg_cpu_percent'] > 80:
            recommendations.append("🔥 High CPU usage detected. Consider reducing analysis frequency or optimizing algorithms.")
        
        # Memory recommendations
        if summary['system']['avg_memory_percent'] > 85:
            recommendations.append("💾 High memory usage detected. Consider implementing data cleanup or increasing cache limits.")
        
        # API recommendations
        if summary['api']['cache_hit_rate'] < 50:
            recommendations.append("📡 Low cache hit rate. Consider increasing cache duration or improving cache strategy.")
        
        if summary['api']['avg_response_time_ms'] > 2000:
            recommendations.append("⏱️ Slow API responses. Consider implementing connection pooling or using faster endpoints.")
        
        if summary['api']['success_rate'] < 95:
            recommendations.append("❌ Low API success rate. Check network connectivity and implement better error handling.")
        
        # Trading recommendations
        if summary['trading']['win_rate'] < 60:
            recommendations.append("📉 Low win rate detected. Consider adjusting trading strategy or confidence thresholds.")
        
        if summary['trading']['max_drawdown'] > 10:
            recommendations.append("🛡️ High drawdown detected. Consider implementing stricter risk management.")
        
        if not recommendations:
            recommendations.append("✅ System performance is optimal!")
        
        return recommendations
    
    def export_metrics(self, filename: str = None) -> str:
        """Export metrics to JSON file"""
        if not filename:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = self.get_performance_summary(hours=24)
        recommendations = self.get_optimization_recommendations()
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'summary': summary,
            'recommendations': recommendations
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"📊 Metrics exported to: {filename}")
        return filename

# Usage example and testing
if __name__ == "__main__":
    print("🚀 Performance Monitor Test")
    print("=" * 50)
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    
    # Start monitoring
    monitor.start_monitoring(interval_seconds=5)
    
    # Simulate some API calls
    print("📡 Simulating API calls...")
    for i in range(10):
        monitor.record_api_call(
            endpoint="coingecko/markets",
            response_time_ms=random.uniform(500, 2000),
            status_code=200,
            success=True,
            cache_hit=random.choice([True, False])
        )
        time.sleep(0.1)
    
    # Simulate trading metrics
    print("💰 Recording trading metrics...")
    monitor.record_trading_metrics(
        total_trades=25,
        winning_trades=18,
        total_pnl=1250.50,
        daily_pnl=85.25,
        max_drawdown=3.2,
        sharpe_ratio=1.8,
        active_positions=5,
        portfolio_value=11250.50
    )
    
    # Wait a bit for monitoring
    print("⏱️ Monitoring for 10 seconds...")
    time.sleep(10)
    
    # Get performance summary
    print("\n📊 Performance Summary:")
    summary = monitor.get_performance_summary(hours=1)
    
    print(f"⏰ Uptime: {summary['uptime_hours']:.2f} hours")
    print(f"🖥️ Avg CPU: {summary['system']['avg_cpu_percent']:.1f}%")
    print(f"💾 Avg Memory: {summary['system']['avg_memory_percent']:.1f}%")
    print(f"📡 API Calls: {summary['api']['total_calls']}")
    print(f"✅ API Success Rate: {summary['api']['success_rate']:.1f}%")
    print(f"💰 Win Rate: {summary['trading']['win_rate']:.1f}%")
    print(f"💵 Total P&L: ${summary['trading']['total_pnl']:.2f}")
    
    # Get recommendations
    print("\n🎯 Optimization Recommendations:")
    recommendations = monitor.get_optimization_recommendations()
    for rec in recommendations:
        print(f"  {rec}")
    
    # Export metrics
    export_file = monitor.export_metrics()
    print(f"\n📁 Metrics exported to: {export_file}")
    
    # Stop monitoring
    monitor.stop_monitoring()
    print("\n✅ Performance monitoring test completed!") 