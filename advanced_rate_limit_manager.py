#!/usr/bin/env python3
"""
⚡ Advanced Rate Limit Manager
Addresses: "CCXT has rate limit handling, but explicit custom rate limit management 
for high-frequency trading or multiple concurrent requests might be beneficial"
Solution: Sophisticated rate limiting with burst handling, priority queues, and adaptive limits
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import logging
from datetime import datetime, timedelta
import json
import heapq
from contextlib import asynccontextmanager, contextmanager

class RequestPriority(Enum):
    """Priority levels for different types of requests"""
    CRITICAL = 1      # Emergency orders, stop losses
    HIGH = 2          # Regular trading orders
    MEDIUM = 3        # Market data updates
    LOW = 4           # Historical data, analytics
    BACKGROUND = 5    # Bulk operations, reports

class RateLimitType(Enum):
    """Different types of rate limits"""
    REQUESTS_PER_SECOND = "rps"
    REQUESTS_PER_MINUTE = "rpm"
    REQUESTS_PER_HOUR = "rph"
    WEIGHT_PER_MINUTE = "wpm"    # Binance-style weighted requests
    ORDER_RATE_LIMIT = "orl"     # Special limit for order placement

@dataclass
class RateLimitRule:
    """Configuration for a specific rate limit"""
    limit_type: RateLimitType
    max_requests: int
    time_window: int  # seconds
    weight_per_request: int = 1
    burst_allowance: int = 0  # Extra requests allowed in burst
    recovery_time: int = 60   # Time to recover burst allowance

@dataclass
class RequestMetrics:
    """Metrics for tracking request patterns"""
    total_requests: int = 0
    successful_requests: int = 0
    rate_limited_requests: int = 0
    avg_response_time: float = 0.0
    peak_rps: float = 0.0
    current_rps: float = 0.0
    burst_usage: int = 0
    queue_depth: int = 0

@dataclass
class QueuedRequest:
    """Represents a queued request with priority"""
    priority: RequestPriority
    func: Callable
    args: tuple
    kwargs: dict
    future: asyncio.Future
    timestamp: float
    weight: int = 1
    retry_count: int = 0
    
    def __lt__(self, other):
        # Lower priority value = higher priority in queue
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float, burst_capacity: int = 0):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.burst_capacity = burst_capacity
        self.tokens = capacity
        self.burst_tokens = burst_capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1, allow_burst: bool = True) -> bool:
        """Try to consume tokens from the bucket"""
        with self.lock:
            now = time.time()
            
            # Refill tokens based on time passed
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # Try to consume from regular tokens first
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            # Try to use burst tokens if allowed
            if allow_burst and self.burst_tokens >= tokens:
                self.burst_tokens -= tokens
                return True
            
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Calculate how long to wait for tokens to be available"""
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            
            needed_tokens = tokens - self.tokens
            return needed_tokens / self.refill_rate
    
    def refill_burst(self):
        """Gradually refill burst tokens"""
        with self.lock:
            if self.burst_tokens < self.burst_capacity:
                self.burst_tokens = min(self.burst_capacity, self.burst_tokens + 1)

class AdvancedRateLimitManager:
    """
    Sophisticated rate limit manager for high-frequency trading
    Features: Priority queues, burst handling, adaptive limits, concurrent request management
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Rate limit configurations per exchange
        self.exchange_limits = self._initialize_exchange_limits()
        
        # Token buckets for each exchange and limit type
        self.token_buckets: Dict[str, Dict[str, TokenBucket]] = {}
        
        # Priority queues for requests
        self.request_queues: Dict[str, List[QueuedRequest]] = defaultdict(list)
        
        # Request metrics
        self.metrics: Dict[str, RequestMetrics] = defaultdict(RequestMetrics)
        
        # Active request tracking
        self.active_requests: Dict[str, int] = defaultdict(int)
        self.max_concurrent_requests: Dict[str, int] = defaultdict(lambda: 10)
        
        # Request history for adaptive limiting
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Background tasks
        self.background_tasks = []
        self.is_running = False
        
        # Initialize token buckets
        self._initialize_token_buckets()
        
        self.logger.info("⚡ Advanced Rate Limit Manager initialized")
    
    def _initialize_exchange_limits(self) -> Dict[str, List[RateLimitRule]]:
        """Initialize rate limit rules for different exchanges"""
        
        return {
            'binance': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 10, 1, burst_allowance=5),
                RateLimitRule(RateLimitType.WEIGHT_PER_MINUTE, 1200, 60, weight_per_request=1),
                RateLimitRule(RateLimitType.ORDER_RATE_LIMIT, 100, 10, weight_per_request=1),
            ],
            'coinbasepro': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 10, 1, burst_allowance=3),
                RateLimitRule(RateLimitType.REQUESTS_PER_MINUTE, 600, 60),
            ],
            'kraken': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 1, 1, burst_allowance=2),
                RateLimitRule(RateLimitType.REQUESTS_PER_MINUTE, 60, 60),
            ],
            'bybit': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 10, 1, burst_allowance=5),
                RateLimitRule(RateLimitType.REQUESTS_PER_MINUTE, 600, 60),
            ],
            'kucoin': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 30, 1, burst_allowance=10),
                RateLimitRule(RateLimitType.REQUESTS_PER_MINUTE, 1800, 60),
            ],
            'huobi': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 10, 1, burst_allowance=3),
                RateLimitRule(RateLimitType.REQUESTS_PER_MINUTE, 600, 60),
            ],
            'okx': [
                RateLimitRule(RateLimitType.REQUESTS_PER_SECOND, 10, 1, burst_allowance=5),
                RateLimitRule(RateLimitType.REQUESTS_PER_MINUTE, 600, 60),
            ]
        }
    
    def _initialize_token_buckets(self):
        """Initialize token buckets for all exchanges and limit types"""
        
        for exchange, rules in self.exchange_limits.items():
            self.token_buckets[exchange] = {}
            
            for rule in rules:
                bucket_key = f"{rule.limit_type.value}"
                refill_rate = rule.max_requests / rule.time_window
                
                self.token_buckets[exchange][bucket_key] = TokenBucket(
                    capacity=rule.max_requests,
                    refill_rate=refill_rate,
                    burst_capacity=rule.burst_allowance
                )
    
    def start_background_tasks(self):
        """Start background tasks for queue processing and metrics"""
        
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start queue processors for each exchange
        for exchange in self.exchange_limits.keys():
            task = asyncio.create_task(self._process_request_queue(exchange))
            self.background_tasks.append(task)
        
        # Start metrics collector
        metrics_task = asyncio.create_task(self._collect_metrics())
        self.background_tasks.append(metrics_task)
        
        # Start burst token refill
        refill_task = asyncio.create_task(self._refill_burst_tokens())
        self.background_tasks.append(refill_task)
        
        self.logger.info("🚀 Background rate limit tasks started")
    
    async def stop_background_tasks(self):
        """Stop all background tasks"""
        
        self.is_running = False
        
        for task in self.background_tasks:
            task.cancel()
        
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
        
        self.logger.info("⏹️ Background rate limit tasks stopped")
    
    def can_make_request(self, exchange: str, request_type: str = "general", 
                        weight: int = 1, priority: RequestPriority = RequestPriority.MEDIUM) -> bool:
        """Check if a request can be made immediately"""
        
        if exchange not in self.token_buckets:
            return True  # No limits configured
        
        # Check concurrent request limit
        if self.active_requests[exchange] >= self.max_concurrent_requests[exchange]:
            return False
        
        # Check all applicable rate limits
        for limit_type, bucket in self.token_buckets[exchange].items():
            if not bucket.consume(weight, allow_burst=(priority.value <= 2)):
                return False
        
        return True
    
    def get_wait_time(self, exchange: str, request_type: str = "general", 
                     weight: int = 1) -> float:
        """Calculate minimum wait time before request can be made"""
        
        if exchange not in self.token_buckets:
            return 0.0
        
        max_wait = 0.0
        
        # Check all applicable rate limits
        for limit_type, bucket in self.token_buckets[exchange].items():
            wait_time = bucket.get_wait_time(weight)
            max_wait = max(max_wait, wait_time)
        
        return max_wait
    
    async def execute_request(self, func: Callable, *args, 
                            exchange: str = "binance",
                            priority: RequestPriority = RequestPriority.MEDIUM,
                            weight: int = 1,
                            timeout: float = 30.0,
                            **kwargs) -> Any:
        """Execute a request with rate limiting and priority queuing"""
        
        # Try immediate execution if possible
        if self.can_make_request(exchange, weight=weight, priority=priority):
            return await self._execute_immediate(func, args, kwargs, exchange, weight)
        
        # Queue the request
        return await self._queue_request(func, args, kwargs, exchange, priority, weight, timeout)
    
    async def _execute_immediate(self, func: Callable, args: tuple, kwargs: dict,
                               exchange: str, weight: int) -> Any:
        """Execute request immediately"""
        
        start_time = time.time()
        self.active_requests[exchange] += 1
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_metrics(exchange, response_time, success=True)
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(exchange, response_time, success=False)
            raise
        
        finally:
            self.active_requests[exchange] -= 1
    
    async def _queue_request(self, func: Callable, args: tuple, kwargs: dict,
                           exchange: str, priority: RequestPriority, weight: int,
                           timeout: float) -> Any:
        """Queue a request for later execution"""
        
        future = asyncio.Future()
        
        request = QueuedRequest(
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs,
            future=future,
            timestamp=time.time(),
            weight=weight
        )
        
        # Add to priority queue
        heapq.heappush(self.request_queues[exchange], request)
        self.metrics[exchange].queue_depth = len(self.request_queues[exchange])
        
        self.logger.debug(f"📥 Queued {priority.name} priority request for {exchange}")
        
        # Wait for result with timeout
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Request timeout after {timeout}s for {exchange}")
            raise
    
    async def _process_request_queue(self, exchange: str):
        """Background task to process queued requests"""
        
        while self.is_running:
            try:
                if not self.request_queues[exchange]:
                    await asyncio.sleep(0.1)
                    continue
                
                # Get highest priority request
                request = heapq.heappop(self.request_queues[exchange])
                self.metrics[exchange].queue_depth = len(self.request_queues[exchange])
                
                # Check if we can execute it now
                if self.can_make_request(exchange, weight=request.weight, priority=request.priority):
                    # Execute the request
                    try:
                        result = await self._execute_immediate(
                            request.func, request.args, request.kwargs, exchange, request.weight
                        )
                        request.future.set_result(result)
                        
                    except Exception as e:
                        request.future.set_exception(e)
                
                else:
                    # Put it back in queue if we can't execute yet
                    heapq.heappush(self.request_queues[exchange], request)
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error processing queue for {exchange}: {e}")
                await asyncio.sleep(1)
    
    async def _collect_metrics(self):
        """Background task to collect and update metrics"""
        
        while self.is_running:
            try:
                current_time = time.time()
                
                for exchange in self.exchange_limits.keys():
                    # Calculate current RPS
                    recent_requests = [
                        req_time for req_time in self.request_history[exchange]
                        if current_time - req_time <= 1.0
                    ]
                    self.metrics[exchange].current_rps = len(recent_requests)
                    
                    # Update peak RPS
                    if self.metrics[exchange].current_rps > self.metrics[exchange].peak_rps:
                        self.metrics[exchange].peak_rps = self.metrics[exchange].current_rps
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)
    
    async def _refill_burst_tokens(self):
        """Background task to refill burst tokens"""
        
        while self.is_running:
            try:
                for exchange_buckets in self.token_buckets.values():
                    for bucket in exchange_buckets.values():
                        bucket.refill_burst()
                
                await asyncio.sleep(10)  # Refill every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error refilling burst tokens: {e}")
                await asyncio.sleep(10)
    
    def _update_metrics(self, exchange: str, response_time: float, success: bool):
        """Update request metrics"""
        
        metrics = self.metrics[exchange]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.rate_limited_requests += 1
        
        # Update average response time
        total_successful = metrics.successful_requests
        if total_successful > 0:
            metrics.avg_response_time = (
                (metrics.avg_response_time * (total_successful - 1) + response_time) / total_successful
            )
        
        # Add to request history
        self.request_history[exchange].append(time.time())
    
    @contextmanager
    def rate_limited_context(self, exchange: str, weight: int = 1):
        """Context manager for rate-limited operations"""
        
        # Wait if necessary
        wait_time = self.get_wait_time(exchange, weight=weight)
        if wait_time > 0:
            time.sleep(wait_time)
        
        # Consume tokens
        for bucket in self.token_buckets.get(exchange, {}).values():
            bucket.consume(weight)
        
        self.active_requests[exchange] += 1
        start_time = time.time()
        
        try:
            yield
            self._update_metrics(exchange, time.time() - start_time, success=True)
        except Exception as e:
            self._update_metrics(exchange, time.time() - start_time, success=False)
            raise
        finally:
            self.active_requests[exchange] -= 1
    
    @asynccontextmanager
    async def async_rate_limited_context(self, exchange: str, weight: int = 1):
        """Async context manager for rate-limited operations"""
        
        # Wait if necessary
        wait_time = self.get_wait_time(exchange, weight=weight)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        # Consume tokens
        for bucket in self.token_buckets.get(exchange, {}).values():
            bucket.consume(weight)
        
        self.active_requests[exchange] += 1
        start_time = time.time()
        
        try:
            yield
            self._update_metrics(exchange, time.time() - start_time, success=True)
        except Exception as e:
            self._update_metrics(exchange, time.time() - start_time, success=False)
            raise
        finally:
            self.active_requests[exchange] -= 1
    
    def get_rate_limit_status(self, exchange: str) -> Dict:
        """Get current rate limit status for an exchange"""
        
        if exchange not in self.token_buckets:
            return {"status": "no_limits", "message": "No rate limits configured"}
        
        status = {
            "exchange": exchange,
            "active_requests": self.active_requests[exchange],
            "max_concurrent": self.max_concurrent_requests[exchange],
            "queue_depth": len(self.request_queues[exchange]),
            "token_buckets": {},
            "metrics": {
                "total_requests": self.metrics[exchange].total_requests,
                "successful_requests": self.metrics[exchange].successful_requests,
                "rate_limited_requests": self.metrics[exchange].rate_limited_requests,
                "success_rate": (
                    self.metrics[exchange].successful_requests / 
                    max(1, self.metrics[exchange].total_requests) * 100
                ),
                "avg_response_time": self.metrics[exchange].avg_response_time,
                "current_rps": self.metrics[exchange].current_rps,
                "peak_rps": self.metrics[exchange].peak_rps
            }
        }
        
        # Add token bucket status
        for limit_type, bucket in self.token_buckets[exchange].items():
            with bucket.lock:
                status["token_buckets"][limit_type] = {
                    "available_tokens": bucket.tokens,
                    "capacity": bucket.capacity,
                    "burst_tokens": bucket.burst_tokens,
                    "burst_capacity": bucket.burst_capacity,
                    "utilization": (1 - bucket.tokens / bucket.capacity) * 100
                }
        
        return status
    
    def adjust_limits(self, exchange: str, multiplier: float):
        """Dynamically adjust rate limits based on performance"""
        
        if exchange not in self.token_buckets:
            return
        
        self.logger.info(f"🔧 Adjusting rate limits for {exchange} by {multiplier}x")
        
        # Adjust concurrent request limit
        current_limit = self.max_concurrent_requests[exchange]
        new_limit = max(1, int(current_limit * multiplier))
        self.max_concurrent_requests[exchange] = new_limit
        
        # Adjust token bucket capacities
        for bucket in self.token_buckets[exchange].values():
            with bucket.lock:
                bucket.capacity = max(1, int(bucket.capacity * multiplier))
                bucket.refill_rate *= multiplier
                bucket.tokens = min(bucket.tokens, bucket.capacity)
    
    def get_comprehensive_status(self) -> Dict:
        """Get comprehensive status of all exchanges"""
        
        return {
            "manager_status": {
                "is_running": self.is_running,
                "background_tasks": len(self.background_tasks),
                "total_exchanges": len(self.exchange_limits)
            },
            "exchanges": {
                exchange: self.get_rate_limit_status(exchange)
                for exchange in self.exchange_limits.keys()
            }
        }

# Global instance for easy use
rate_limit_manager = AdvancedRateLimitManager()

def with_rate_limiting(exchange: str = "binance", priority: RequestPriority = RequestPriority.MEDIUM, weight: int = 1):
    """Decorator for adding advanced rate limiting to functions"""
    
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                return await rate_limit_manager.execute_request(
                    func, *args, exchange=exchange, priority=priority, weight=weight, **kwargs
                )
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with rate_limit_manager.rate_limited_context(exchange, weight):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator

async def demo_advanced_rate_limiting():
    """Demonstrate advanced rate limiting capabilities"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("⚡ ADVANCED RATE LIMIT MANAGER DEMO")
    print("=" * 45)
    
    # Initialize manager
    manager = AdvancedRateLimitManager(logger)
    await manager.start_background_tasks()
    
    # Demo functions
    @with_rate_limiting(exchange='binance', priority=RequestPriority.HIGH, weight=1)
    async def fetch_ticker(symbol: str):
        """Simulate fetching ticker data"""
        await asyncio.sleep(0.1)  # Simulate API call
        return f"Ticker for {symbol}: $50000"
    
    @with_rate_limiting(exchange='binance', priority=RequestPriority.CRITICAL, weight=5)
    async def place_order(symbol: str, side: str, amount: float):
        """Simulate placing an order"""
        await asyncio.sleep(0.2)  # Simulate API call
        return f"Order placed: {side} {amount} {symbol}"
    
    @with_rate_limiting(exchange='binance', priority=RequestPriority.LOW, weight=1)
    async def fetch_history(symbol: str):
        """Simulate fetching historical data"""
        await asyncio.sleep(0.3)  # Simulate API call
        return f"Historical data for {symbol}"
    
    print("🧪 Testing concurrent requests with priority handling...")
    
    # Create a mix of requests with different priorities
    tasks = []
    
    # High-frequency ticker requests (medium priority)
    for i in range(20):
        tasks.append(fetch_ticker(f"BTC/USDT"))
    
    # Critical order requests (high priority)
    for i in range(5):
        tasks.append(place_order("BTC/USDT", "buy", 0.001))
    
    # Background data requests (low priority)
    for i in range(10):
        tasks.append(fetch_history("BTC/USDT"))
    
    print(f"📊 Executing {len(tasks)} concurrent requests...")
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    execution_time = time.time() - start_time
    
    successful = sum(1 for r in results if not isinstance(r, Exception))
    failed = len(results) - successful
    
    print(f"✅ Completed in {execution_time:.2f}s")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    # Show rate limit status
    print("\n📊 Rate Limit Status:")
    status = manager.get_rate_limit_status('binance')
    
    print(f"   Active requests: {status['active_requests']}/{status['max_concurrent']}")
    print(f"   Queue depth: {status['queue_depth']}")
    print(f"   Total requests: {status['metrics']['total_requests']}")
    print(f"   Success rate: {status['metrics']['success_rate']:.1f}%")
    print(f"   Avg response time: {status['metrics']['avg_response_time']:.3f}s")
    print(f"   Current RPS: {status['metrics']['current_rps']:.1f}")
    print(f"   Peak RPS: {status['metrics']['peak_rps']:.1f}")
    
    # Show token bucket status
    print("\n🪣 Token Bucket Status:")
    for limit_type, bucket_info in status['token_buckets'].items():
        utilization = bucket_info['utilization']
        print(f"   {limit_type}: {bucket_info['available_tokens']}/{bucket_info['capacity']} "
              f"tokens ({utilization:.1f}% used)")
        if bucket_info['burst_capacity'] > 0:
            print(f"     Burst: {bucket_info['burst_tokens']}/{bucket_info['burst_capacity']} tokens")
    
    # Test burst handling
    print("\n🚀 Testing burst handling...")
    burst_tasks = [fetch_ticker("ETH/USDT") for _ in range(15)]  # Exceed normal limit
    
    burst_start = time.time()
    burst_results = await asyncio.gather(*burst_tasks, return_exceptions=True)
    burst_time = time.time() - burst_start
    
    burst_successful = sum(1 for r in burst_results if not isinstance(r, Exception))
    print(f"   Burst requests: {burst_successful}/{len(burst_tasks)} successful in {burst_time:.2f}s")
    
    # Clean up
    await manager.stop_background_tasks()
    
    print("\n🎉 Advanced rate limiting demo complete!")
    print("✅ Priority-based request queuing")
    print("✅ Token bucket rate limiting")
    print("✅ Burst handling capabilities")
    print("✅ Concurrent request management")
    print("✅ Real-time metrics and monitoring")

if __name__ == "__main__":
    asyncio.run(demo_advanced_rate_limiting()) 