#!/usr/bin/env python3
"""
Performance Optimizer - Production-Ready Performance Optimization
Monitors, analyzes, and optimizes the unified trading platform
"""

import asyncio
import psutil
import time
import statistics
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
import threading
import gc
import tracemalloc

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_rss: int
    memory_vms: int
    events_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    active_connections: int
    queue_sizes: Dict[str, int]
    error_rate: float
    gc_collections: Dict[str, int]

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation."""
    category: str
    priority: str  # HIGH, MEDIUM, LOW
    title: str
    description: str
    impact: str
    implementation: str
    estimated_improvement: str

class PerformanceMonitor:
    """Real-time performance monitoring."""
    
    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.metrics_history: deque = deque(maxlen=3600)  # 1 hour of data
        self.latency_samples: deque = deque(maxlen=1000)
        self.event_counts: defaultdict = defaultdict(int)
        self.error_counts: defaultdict = defaultdict(int)
        self.is_monitoring = False
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'latency_warning': 100.0,  # ms
            'latency_critical': 500.0,  # ms
            'error_rate_warning': 0.05,  # 5%
            'error_rate_critical': 0.10  # 10%
        }
    
    async def start_monitoring(self):
        """Start performance monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.logger.info("Starting performance monitoring")
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        self.logger.info("Stopped performance monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Event metrics
        current_time = time.time()
        events_per_second = self._calculate_events_per_second()
        
        # Latency metrics
        avg_latency, p95_latency, p99_latency = self._calculate_latency_metrics()
        
        # Error rate
        error_rate = self._calculate_error_rate()
        
        # GC metrics
        gc_stats = self._get_gc_stats()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            memory_rss=process_memory.rss,
            memory_vms=process_memory.vms,
            events_per_second=events_per_second,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            active_connections=0,  # Would be populated by connection manager
            queue_sizes={},  # Would be populated by event bus
            error_rate=error_rate,
            gc_collections=gc_stats
        )
    
    def _calculate_events_per_second(self) -> float:
        """Calculate events per second."""
        current_time = time.time()
        
        # Count events in the last second
        recent_events = sum(
            count for timestamp, count in self.event_counts.items()
            if current_time - timestamp < 1.0
        )
        
        return float(recent_events)
    
    def _calculate_latency_metrics(self) -> Tuple[float, float, float]:
        """Calculate latency metrics."""
        if not self.latency_samples:
            return 0.0, 0.0, 0.0
        
        samples = list(self.latency_samples)
        avg_latency = statistics.mean(samples)
        
        if len(samples) >= 20:
            p95_latency = statistics.quantiles(samples, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(samples, n=100)[98] if len(samples) >= 100 else max(samples)
        else:
            p95_latency = max(samples)
            p99_latency = max(samples)
        
        return avg_latency, p95_latency, p99_latency
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate."""
        current_time = time.time()
        
        # Count errors and total events in the last minute
        total_events = 0
        total_errors = 0
        
        for timestamp, count in self.event_counts.items():
            if current_time - timestamp < 60.0:
                total_events += count
        
        for timestamp, count in self.error_counts.items():
            if current_time - timestamp < 60.0:
                total_errors += count
        
        return (total_errors / total_events) if total_events > 0 else 0.0
    
    def _get_gc_stats(self) -> Dict[str, int]:
        """Get garbage collection statistics."""
        return {
            f'generation_{i}': gc.get_count()[i] for i in range(3)
        }
    
    async def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts."""
        alerts = []
        
        # CPU alerts
        if metrics.cpu_usage >= self.thresholds['cpu_critical']:
            alerts.append(f"CRITICAL: CPU usage at {metrics.cpu_usage:.1f}%")
        elif metrics.cpu_usage >= self.thresholds['cpu_warning']:
            alerts.append(f"WARNING: CPU usage at {metrics.cpu_usage:.1f}%")
        
        # Memory alerts
        if metrics.memory_usage >= self.thresholds['memory_critical']:
            alerts.append(f"CRITICAL: Memory usage at {metrics.memory_usage:.1f}%")
        elif metrics.memory_usage >= self.thresholds['memory_warning']:
            alerts.append(f"WARNING: Memory usage at {metrics.memory_usage:.1f}%")
        
        # Latency alerts
        if metrics.p95_latency_ms >= self.thresholds['latency_critical']:
            alerts.append(f"CRITICAL: P95 latency at {metrics.p95_latency_ms:.1f}ms")
        elif metrics.p95_latency_ms >= self.thresholds['latency_warning']:
            alerts.append(f"WARNING: P95 latency at {metrics.p95_latency_ms:.1f}ms")
        
        # Error rate alerts
        if metrics.error_rate >= self.thresholds['error_rate_critical']:
            alerts.append(f"CRITICAL: Error rate at {metrics.error_rate:.2%}")
        elif metrics.error_rate >= self.thresholds['error_rate_warning']:
            alerts.append(f"WARNING: Error rate at {metrics.error_rate:.2%}")
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(alert)
    
    def record_event(self, event_type: str, latency_ms: float = None, is_error: bool = False):
        """Record an event for performance tracking."""
        current_time = time.time()
        
        # Record event count
        self.event_counts[current_time] += 1
        
        # Record latency
        if latency_ms is not None:
            self.latency_samples.append(latency_ms)
        
        # Record error
        if is_error:
            self.error_counts[current_time] += 1
        
        # Clean old data
        self._cleanup_old_data(current_time)
    
    def _cleanup_old_data(self, current_time: float):
        """Clean up old performance data."""
        cutoff_time = current_time - 300  # 5 minutes
        
        # Clean event counts
        old_keys = [k for k in self.event_counts.keys() if k < cutoff_time]
        for key in old_keys:
            del self.event_counts[key]
        
        # Clean error counts
        old_keys = [k for k in self.error_counts.keys() if k < cutoff_time]
        for key in old_keys:
            del self.error_counts[key]
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[PerformanceMetrics]:
        """Get metrics history for specified duration."""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

class PerformanceOptimizer:
    """Performance optimization engine."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        self.optimization_history = []
        
    def analyze_performance(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Analyze performance over specified duration."""
        metrics_history = self.monitor.get_metrics_history(duration_minutes)
        
        if not metrics_history:
            return {'error': 'No metrics available for analysis'}
        
        analysis = {
            'period': f'{duration_minutes} minutes',
            'sample_count': len(metrics_history),
            'cpu': self._analyze_cpu(metrics_history),
            'memory': self._analyze_memory(metrics_history),
            'latency': self._analyze_latency(metrics_history),
            'throughput': self._analyze_throughput(metrics_history),
            'errors': self._analyze_errors(metrics_history),
            'trends': self._analyze_trends(metrics_history)
        }
        
        return analysis
    
    def _analyze_cpu(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze CPU performance."""
        cpu_values = [m.cpu_usage for m in metrics]
        
        return {
            'average': statistics.mean(cpu_values),
            'median': statistics.median(cpu_values),
            'max': max(cpu_values),
            'min': min(cpu_values),
            'std_dev': statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
            'spikes_count': len([v for v in cpu_values if v > 80]),
            'utilization_score': self._calculate_utilization_score(cpu_values, 80)
        }
    
    def _analyze_memory(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze memory performance."""
        memory_values = [m.memory_usage for m in metrics]
        rss_values = [m.memory_rss for m in metrics]
        
        return {
            'average_percent': statistics.mean(memory_values),
            'max_percent': max(memory_values),
            'average_rss_mb': statistics.mean(rss_values) / (1024 * 1024),
            'max_rss_mb': max(rss_values) / (1024 * 1024),
            'memory_growth_mb': (rss_values[-1] - rss_values[0]) / (1024 * 1024) if len(rss_values) > 1 else 0,
            'leak_indicator': self._detect_memory_leak(rss_values)
        }
    
    def _analyze_latency(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze latency performance."""
        avg_latencies = [m.avg_latency_ms for m in metrics if m.avg_latency_ms > 0]
        p95_latencies = [m.p95_latency_ms for m in metrics if m.p95_latency_ms > 0]
        
        if not avg_latencies:
            return {'error': 'No latency data available'}
        
        return {
            'average_ms': statistics.mean(avg_latencies),
            'p95_average_ms': statistics.mean(p95_latencies),
            'max_avg_ms': max(avg_latencies),
            'max_p95_ms': max(p95_latencies),
            'latency_variance': statistics.variance(avg_latencies) if len(avg_latencies) > 1 else 0,
            'sla_violations': len([l for l in p95_latencies if l > 100])  # >100ms violations
        }
    
    def _analyze_throughput(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze throughput performance."""
        throughput_values = [m.events_per_second for m in metrics if m.events_per_second > 0]
        
        if not throughput_values:
            return {'error': 'No throughput data available'}
        
        return {
            'average_eps': statistics.mean(throughput_values),
            'max_eps': max(throughput_values),
            'min_eps': min(throughput_values),
            'throughput_stability': 1 - (statistics.stdev(throughput_values) / statistics.mean(throughput_values))
        }
    
    def _analyze_errors(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze error patterns."""
        error_rates = [m.error_rate for m in metrics]
        
        return {
            'average_error_rate': statistics.mean(error_rates),
            'max_error_rate': max(error_rates),
            'error_spikes': len([r for r in error_rates if r > 0.05]),
            'reliability_score': 1 - statistics.mean(error_rates)
        }
    
    def _analyze_trends(self, metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze performance trends."""
        if len(metrics) < 10:
            return {'error': 'Insufficient data for trend analysis'}
        
        # Simple trend analysis using linear regression
        cpu_trend = self._calculate_trend([m.cpu_usage for m in metrics])
        memory_trend = self._calculate_trend([m.memory_usage for m in metrics])
        latency_trend = self._calculate_trend([m.avg_latency_ms for m in metrics if m.avg_latency_ms > 0])
        
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'latency_trend': latency_trend,
            'overall_health': self._calculate_overall_health(metrics)
        }
    
    def _calculate_utilization_score(self, values: List[float], threshold: float) -> float:
        """Calculate utilization efficiency score."""
        if not values:
            return 0.0
        
        # Optimal utilization is around 60-70%
        optimal_range = (50, 70)
        score = 0.0
        
        for value in values:
            if optimal_range[0] <= value <= optimal_range[1]:
                score += 1.0
            elif value < optimal_range[0]:
                score += value / optimal_range[0]
            else:
                score += max(0, 1 - (value - optimal_range[1]) / (100 - optimal_range[1]))
        
        return score / len(values)
    
    def _detect_memory_leak(self, rss_values: List[int]) -> bool:
        """Detect potential memory leaks."""
        if len(rss_values) < 10:
            return False
        
        # Check if memory consistently increases
        increases = 0
        for i in range(1, len(rss_values)):
            if rss_values[i] > rss_values[i-1]:
                increases += 1
        
        # If memory increases in >70% of samples, potential leak
        return (increases / (len(rss_values) - 1)) > 0.7
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear trend
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_overall_health(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate overall system health score (0-1)."""
        if not metrics:
            return 0.0
        
        latest = metrics[-1]
        
        # Health factors
        cpu_health = max(0, 1 - latest.cpu_usage / 100)
        memory_health = max(0, 1 - latest.memory_usage / 100)
        latency_health = max(0, 1 - latest.p95_latency_ms / 1000)  # Normalize to 1 second
        error_health = max(0, 1 - latest.error_rate)
        
        # Weighted average
        weights = [0.25, 0.25, 0.25, 0.25]
        health_scores = [cpu_health, memory_health, latency_health, error_health]
        
        return sum(w * s for w, s in zip(weights, health_scores))
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # CPU recommendations
        if 'cpu' in analysis:
            cpu_data = analysis['cpu']
            if cpu_data['average'] > 80:
                recommendations.append(OptimizationRecommendation(
                    category='CPU',
                    priority='HIGH',
                    title='High CPU Usage',
                    description=f"Average CPU usage is {cpu_data['average']:.1f}%",
                    impact='Performance degradation, increased latency',
                    implementation='Scale horizontally, optimize algorithms, add caching',
                    estimated_improvement='20-40% latency reduction'
                ))
            elif cpu_data['spikes_count'] > 10:
                recommendations.append(OptimizationRecommendation(
                    category='CPU',
                    priority='MEDIUM',
                    title='CPU Spikes',
                    description=f"Detected {cpu_data['spikes_count']} CPU spikes",
                    impact='Intermittent performance issues',
                    implementation='Implement rate limiting, optimize hot paths',
                    estimated_improvement='Smoother performance'
                ))
        
        # Memory recommendations
        if 'memory' in analysis:
            memory_data = analysis['memory']
            if memory_data.get('leak_indicator', False):
                recommendations.append(OptimizationRecommendation(
                    category='Memory',
                    priority='HIGH',
                    title='Potential Memory Leak',
                    description='Memory usage consistently increasing',
                    impact='System instability, potential crashes',
                    implementation='Review object lifecycle, implement proper cleanup',
                    estimated_improvement='Stable memory usage'
                ))
            elif memory_data['average_percent'] > 80:
                recommendations.append(OptimizationRecommendation(
                    category='Memory',
                    priority='MEDIUM',
                    title='High Memory Usage',
                    description=f"Average memory usage is {memory_data['average_percent']:.1f}%",
                    impact='Risk of out-of-memory errors',
                    implementation='Optimize data structures, implement memory pooling',
                    estimated_improvement='30-50% memory reduction'
                ))
        
        # Latency recommendations
        if 'latency' in analysis and 'error' not in analysis['latency']:
            latency_data = analysis['latency']
            if latency_data['p95_average_ms'] > 100:
                recommendations.append(OptimizationRecommendation(
                    category='Latency',
                    priority='HIGH',
                    title='High Latency',
                    description=f"P95 latency is {latency_data['p95_average_ms']:.1f}ms",
                    impact='Poor user experience, SLA violations',
                    implementation='Add caching, optimize database queries, use async processing',
                    estimated_improvement='50-70% latency reduction'
                ))
        
        # Throughput recommendations
        if 'throughput' in analysis and 'error' not in analysis['throughput']:
            throughput_data = analysis['throughput']
            if throughput_data['throughput_stability'] < 0.8:
                recommendations.append(OptimizationRecommendation(
                    category='Throughput',
                    priority='MEDIUM',
                    title='Unstable Throughput',
                    description='Throughput varies significantly',
                    impact='Unpredictable performance',
                    implementation='Implement connection pooling, optimize event processing',
                    estimated_improvement='More consistent performance'
                ))
        
        return recommendations
    
    def apply_optimization(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Apply an optimization recommendation."""
        # This would contain actual optimization implementations
        # For now, we'll just log the recommendation
        
        self.logger.info(f"Applying optimization: {recommendation.title}")
        
        result = {
            'recommendation': recommendation.title,
            'status': 'applied',
            'timestamp': datetime.now().isoformat(),
            'details': 'Optimization logged for manual implementation'
        }
        
        self.optimization_history.append(result)
        return result

class PerformanceProfiler:
    """Advanced performance profiling."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profiling_active = False
        
    def start_memory_profiling(self):
        """Start memory profiling."""
        if not self.profiling_active:
            tracemalloc.start()
            self.profiling_active = True
            self.logger.info("Memory profiling started")
    
    def get_memory_snapshot(self) -> Dict[str, Any]:
        """Get current memory snapshot."""
        if not tracemalloc.is_tracing():
            return {'error': 'Memory profiling not active'}
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_memory_mb': sum(stat.size for stat in top_stats) / (1024 * 1024),
            'top_allocations': [
                {
                    'file': stat.traceback.format()[0],
                    'size_mb': stat.size / (1024 * 1024),
                    'count': stat.count
                } for stat in top_stats[:10]
            ]
        }
    
    def stop_memory_profiling(self):
        """Stop memory profiling."""
        if self.profiling_active:
            tracemalloc.stop()
            self.profiling_active = False
            self.logger.info("Memory profiling stopped")

def create_performance_system() -> Tuple[PerformanceMonitor, PerformanceOptimizer, PerformanceProfiler]:
    """Create complete performance monitoring system."""
    monitor = PerformanceMonitor(collection_interval=1.0)
    optimizer = PerformanceOptimizer(monitor)
    profiler = PerformanceProfiler()
    
    return monitor, optimizer, profiler

async def main():
    """Example usage of the performance system."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create performance system
    monitor, optimizer, profiler = create_performance_system()
    
    # Start monitoring
    await monitor.start_monitoring()
    
    # Start profiling
    profiler.start_memory_profiling()
    
    try:
        # Simulate some work
        for i in range(60):
            # Simulate event processing
            start_time = time.time()
            await asyncio.sleep(0.01)  # Simulate work
            latency = (time.time() - start_time) * 1000
            
            # Record event
            monitor.record_event('test_event', latency_ms=latency)
            
            await asyncio.sleep(1)
        
        # Analyze performance
        analysis = optimizer.analyze_performance(duration_minutes=1)
        print("Performance Analysis:")
        print(json.dumps(analysis, indent=2, default=str))
        
        # Generate recommendations
        recommendations = optimizer.generate_recommendations(analysis)
        print(f"\nGenerated {len(recommendations)} recommendations:")
        for rec in recommendations:
            print(f"- [{rec.priority}] {rec.title}: {rec.description}")
        
        # Get memory snapshot
        memory_snapshot = profiler.get_memory_snapshot()
        print(f"\nMemory usage: {memory_snapshot.get('total_memory_mb', 0):.2f} MB")
        
    finally:
        # Cleanup
        monitor.stop_monitoring()
        profiler.stop_memory_profiling()

if __name__ == '__main__':
    import json
    asyncio.run(main()) 