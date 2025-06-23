#!/usr/bin/env python3
"""
📊 Performance Monitor Module
Real-time performance tracking and system optimization
"""

import asyncio
import logging
import psutil
import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import tracemalloc
from contextlib import contextmanager

@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str = "general"
    tags: Dict[str, str] = None

@dataclass
class SystemSnapshot:
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    timestamp: datetime

class PerformanceMonitor:
    """
    Advanced Performance Monitoring System
    
    Features:
    ✅ Real-time system resource monitoring
    ✅ Function-level performance profiling
    ✅ Memory usage tracking
    ✅ Bottleneck identification
    ✅ Automatic alerting
    ✅ Prometheus metrics export
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring_enabled = config.get('enable_monitoring', True)
        self.alert_thresholds = config.get('alert_thresholds', {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_ms': 1000.0
        })
        
        # Storage
        self.metrics_history = []
        self.system_snapshots = []
        self.function_profiles = {}
        self.alerts_sent = set()
        
        # State
        self.start_time = datetime.now()
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Statistics
        self.stats = {
            'total_metrics': 0,
            'alerts_triggered': 0,
            'peak_cpu': 0.0,
            'peak_memory': 0.0,
            'avg_response_time': 0.0
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize memory profiling
        try:
            tracemalloc.start()
        except RuntimeError:
            pass  # Already started
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_enabled and not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("🚀 Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("🛑 Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                snapshot = self._collect_system_snapshot()
                self.system_snapshots.append(snapshot)
                
                # Check for alerts
                self._check_alerts(snapshot)
                
                # Clean old data (keep last 1000 snapshots)
                if len(self.system_snapshots) > 1000:
                    self.system_snapshots = self.system_snapshots[-1000:]
                
                # Update stats
                self._update_stats()
                
                time.sleep(self.config.get('monitoring_interval', 5))
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(10)
    
    def _collect_system_snapshot(self) -> SystemSnapshot:
        """Collect current system state"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return SystemSnapshot(
                cpu_percent=cpu,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk.percent,
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Error collecting system snapshot: {e}")
            return SystemSnapshot(0, 0, 0, 0, datetime.now())
    
    @contextmanager
    def profile_function(self, function_name: str):
        """Profile function execution time and memory"""
        if not self.monitoring_enabled:
            yield
            return
        
        start_time = time.perf_counter()
        start_memory = 0
        
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            start_memory = current
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            
            memory_delta = 0
            if tracemalloc.is_tracing():
                current, _ = tracemalloc.get_traced_memory()
                memory_delta = (current - start_memory) / 1024 / 1024  # MB
            
            # Update function profile
            if function_name not in self.function_profiles:
                self.function_profiles[function_name] = {
                    'call_count': 0,
                    'total_time_ms': 0,
                    'avg_time_ms': 0,
                    'max_time_ms': 0,
                    'memory_peak_mb': 0
                }
            
            profile = self.function_profiles[function_name]
            profile['call_count'] += 1
            profile['total_time_ms'] += execution_time
            profile['avg_time_ms'] = profile['total_time_ms'] / profile['call_count']
            profile['max_time_ms'] = max(profile['max_time_ms'], execution_time)
            profile['memory_peak_mb'] = max(profile['memory_peak_mb'], memory_delta)
            
            # Add metric
            self.add_metric(f"function_{function_name}_time", execution_time, "ms", "performance")
    
    def add_metric(self, name: str, value: float, unit: str = "", category: str = "general", **tags):
        """Add performance metric"""
        if self.monitoring_enabled:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                category=category,
                tags=tags or {}
            )
            self.metrics_history.append(metric)
            self.stats['total_metrics'] += 1
            
            # Keep only recent metrics
            if len(self.metrics_history) > 10000:
                self.metrics_history = self.metrics_history[-10000:]
    
    def _check_alerts(self, snapshot: SystemSnapshot):
        """Check for performance alerts"""
        alerts = []
        
        if snapshot.cpu_percent > self.alert_thresholds.get('cpu_percent', 80):
            alerts.append(f"High CPU: {snapshot.cpu_percent:.1f}%")
        
        if snapshot.memory_percent > self.alert_thresholds.get('memory_percent', 85):
            alerts.append(f"High Memory: {snapshot.memory_percent:.1f}%")
        
        if snapshot.disk_usage_percent > 90:
            alerts.append(f"High Disk: {snapshot.disk_usage_percent:.1f}%")
        
        for alert in alerts:
            if alert not in self.alerts_sent:
                self.alerts_sent.add(alert)
                self.stats['alerts_triggered'] += 1
                self.logger.warning(f"🚨 ALERT: {alert}")
                
                # Clear alert after 5 minutes
                threading.Timer(300, lambda: self.alerts_sent.discard(alert)).start()
    
    def _update_stats(self):
        """Update performance statistics"""
        if self.system_snapshots:
            recent = self.system_snapshots[-20:]  # Last 20 snapshots
            self.stats['peak_cpu'] = max(s.cpu_percent for s in recent)
            self.stats['peak_memory'] = max(s.memory_percent for s in recent)
        
        if self.metrics_history:
            response_metrics = [m for m in self.metrics_history if 'response' in m.name]
            if response_metrics:
                self.stats['avg_response_time'] = sum(m.value for m in response_metrics) / len(response_metrics)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        current = self._collect_system_snapshot()
        
        # Top slow functions
        top_functions = sorted(
            [(name, data) for name, data in self.function_profiles.items()],
            key=lambda x: x[1]['avg_time_ms'],
            reverse=True
        )[:10]
        
        return {
            'uptime_seconds': uptime,
            'current_system': {
                'cpu_percent': current.cpu_percent,
                'memory_percent': current.memory_percent,
                'memory_used_mb': current.memory_used_mb,
                'disk_percent': current.disk_usage_percent
            },
            'statistics': self.stats,
            'top_slow_functions': [
                {'name': name, **data} for name, data in top_functions
            ],
            'bottlenecks': self._detect_bottlenecks(),
            'total_metrics': len(self.metrics_history),
            'total_snapshots': len(self.system_snapshots)
        }
    
    def _detect_bottlenecks(self) -> List[Dict[str, Any]]:
        """Detect performance bottlenecks"""
        bottlenecks = []
        
        # Slow functions (>1 second average)
        for name, profile in self.function_profiles.items():
            if profile['avg_time_ms'] > 1000:
                bottlenecks.append({
                    'type': 'slow_function',
                    'function': name,
                    'avg_time_ms': profile['avg_time_ms'],
                    'call_count': profile['call_count'],
                    'severity': 'high' if profile['avg_time_ms'] > 5000 else 'medium'
                })
        
        # High memory usage
        if self.system_snapshots:
            recent_memory = [s.memory_percent for s in self.system_snapshots[-10:]]
            avg_memory = sum(recent_memory) / len(recent_memory)
            if avg_memory > 80:
                bottlenecks.append({
                    'type': 'high_memory',
                    'avg_memory_percent': avg_memory,
                    'severity': 'high' if avg_memory > 90 else 'medium'
                })
        
        return bottlenecks
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics for Prometheus"""
        lines = []
        current = self._collect_system_snapshot()
        
        # System metrics
        lines.append(f'system_cpu_percent {current.cpu_percent}')
        lines.append(f'system_memory_percent {current.memory_percent}')
        lines.append(f'system_memory_used_mb {current.memory_used_mb}')
        lines.append(f'system_disk_percent {current.disk_usage_percent}')
        
        # Function metrics
        for name, profile in self.function_profiles.items():
            safe_name = name.replace('.', '_').replace('-', '_')
            lines.append(f'function_avg_time_ms{{function="{safe_name}"}} {profile["avg_time_ms"]}')
            lines.append(f'function_call_count{{function="{safe_name}"}} {profile["call_count"]}')
        
        # Statistics
        for key, value in self.stats.items():
            if isinstance(value, (int, float)):
                lines.append(f'performance_{key} {value}')
        
        return '\n'.join(lines)

# Global instance
_monitor = None

def get_monitor(config: Dict[str, Any] = None) -> PerformanceMonitor:
    """Get global performance monitor"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor(config or {})
    return _monitor

def profile(function_name: str):
    """Decorator for function profiling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with get_monitor().profile_function(function_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def start_monitoring(config: Dict[str, Any] = None):
    """Start global monitoring"""
    get_monitor(config).start_monitoring()

def stop_monitoring():
    """Stop global monitoring"""
    get_monitor().stop_monitoring()

def add_metric(name: str, value: float, unit: str = "", category: str = "general", **tags):
    """Add metric to global monitor"""
    get_monitor().add_metric(name, value, unit, category, **tags) 