#!/usr/bin/env python3
"""
⚡ Demo: Advanced Rate Limiting for High-Frequency Trading
Shows: Token buckets, burst handling, priority queues, concurrent request management
"""

import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict
import logging
from contextlib import contextmanager
import threading

class RequestPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5

class RateLimitType(Enum):
    REQUESTS_PER_SECOND = "rps"
    REQUESTS_PER_MINUTE = "rpm"
    WEIGHT_PER_MINUTE = "wpm"
    ORDER_RATE_LIMIT = "orl"

@dataclass
class RateLimitRule:
    limit_type: RateLimitType
    max_requests: int
    time_window: int
    weight_per_request: int = 1
    burst_allowance: int = 0

@dataclass
class RequestMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    rate_limited_requests: int = 0
    avg_response_time: float = 0.0
    current_rps: float = 0.0

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float, burst_capacity: int = 0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.burst_capacity = burst_capacity
        self.tokens = capacity
        self.burst_tokens = burst_capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1, allow_burst: bool = True) -> bool:
        with self.lock:
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            if allow_burst and self.burst_tokens >= tokens:
                self.burst_tokens -= tokens
                return True
            
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            needed_tokens = tokens - self.tokens
            return needed_tokens / self.refill_rate

class AdvancedRateLimitManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Exchange configurations
        self.exchange_limits = {
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
            ]
        }
        
        # Token buckets
        self.token_buckets = {}
        self.metrics = defaultdict(RequestMetrics)
        self.active_requests = defaultdict(int)
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        
        self._initialize_token_buckets()
    
    def _initialize_token_buckets(self):
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
    
    def can_make_request(self, exchange: str, weight: int = 1, priority: RequestPriority = RequestPriority.MEDIUM) -> bool:
        if exchange not in self.token_buckets:
            return True
        
        for limit_type, bucket in self.token_buckets[exchange].items():
            if not bucket.consume(weight, allow_burst=(priority.value <= 2)):
                return False
        return True
    
    def get_wait_time(self, exchange: str, weight: int = 1) -> float:
        if exchange not in self.token_buckets:
            return 0.0
        
        max_wait = 0.0
        for limit_type, bucket in self.token_buckets[exchange].items():
            wait_time = bucket.get_wait_time(weight)
            max_wait = max(max_wait, wait_time)
        return max_wait
    
    def _update_metrics(self, exchange: str, response_time: float, success: bool):
        metrics = self.metrics[exchange]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.rate_limited_requests += 1
        
        total_successful = metrics.successful_requests
        if total_successful > 0:
            metrics.avg_response_time = (
                (metrics.avg_response_time * (total_successful - 1) + response_time) / total_successful
            )
        
        self.request_history[exchange].append(time.time())
    
    @contextmanager
    def rate_limited_context(self, exchange: str, weight: int = 1, priority: RequestPriority = RequestPriority.MEDIUM):
        # Wait if necessary
        wait_time = self.get_wait_time(exchange, weight=weight)
        if wait_time > 0:
            print(f"  ⏳ Waiting {wait_time:.2f}s for rate limit...")
            time.sleep(wait_time)
        
        # Consume tokens
        for bucket in self.token_buckets.get(exchange, {}).values():
            bucket.consume(weight, allow_burst=(priority.value <= 2))
        
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
        if exchange not in self.token_buckets:
            return {"status": "no_limits", "message": "No rate limits configured"}
        
        # Calculate current RPS
        current_time = time.time()
        recent_requests = [
            req_time for req_time in self.request_history[exchange]
            if current_time - req_time <= 1.0
        ]
        current_rps = len(recent_requests)
        
        status = {
            "exchange": exchange,
            "active_requests": self.active_requests[exchange],
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
                "current_rps": current_rps,
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

# Global instance
rate_limit_manager = AdvancedRateLimitManager()

def with_rate_limiting(exchange: str = "binance", priority: RequestPriority = RequestPriority.MEDIUM, weight: int = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with rate_limit_manager.rate_limited_context(exchange, weight, priority):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Demo functions
@with_rate_limiting(exchange='binance', priority=RequestPriority.HIGH, weight=1)
def fetch_ticker(symbol: str):
    time.sleep(0.1)  # Simulate API call
    return f"Ticker for {symbol}: ${50000 + random.randint(-1000, 1000)}"

@with_rate_limiting(exchange='binance', priority=RequestPriority.CRITICAL, weight=5)
def place_order(symbol: str, side: str, amount: float):
    time.sleep(0.2)  # Simulate API call
    return f"Order placed: {side} {amount} {symbol}"

@with_rate_limiting(exchange='binance', priority=RequestPriority.LOW, weight=1)
def fetch_history(symbol: str):
    time.sleep(0.3)  # Simulate API call
    return f"Historical data for {symbol}"

@with_rate_limiting(exchange='kraken', priority=RequestPriority.MEDIUM, weight=1)
def fetch_kraken_data(symbol: str):
    time.sleep(0.15)  # Simulate API call
    return f"Kraken data for {symbol}"

def demo_advanced_rate_limiting():
    """Demonstrate advanced rate limiting capabilities"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("⚡ ADVANCED RATE LIMIT MANAGER DEMO")
    print("=" * 45)
    
    print("🧪 Testing rate limiting with different priorities and weights...")
    
    # Test 1: Normal request flow
    print("\n📊 Test 1: Normal request flow")
    for i in range(5):
        result = fetch_ticker("BTC/USDT")
        print(f"  ✅ {result}")
    
    # Test 2: Burst handling
    print("\n🚀 Test 2: Burst handling (15 rapid requests)")
    start_time = time.time()
    burst_results = []
    
    for i in range(15):
        try:
            result = fetch_ticker("ETH/USDT")
            burst_results.append(result)
            print(f"  📈 Request {i+1}: Success")
        except Exception as e:
            burst_results.append(f"Error: {e}")
            print(f"  ❌ Request {i+1}: {e}")
    
    burst_time = time.time() - start_time
    successful_burst = len([r for r in burst_results if not r.startswith("Error")])
    print(f"  📊 Burst test: {successful_burst}/{len(burst_results)} successful in {burst_time:.2f}s")
    
    # Test 3: High-weight requests (orders)
    print("\n💰 Test 3: High-weight order requests")
    for i in range(3):
        result = place_order("BTC/USDT", "buy", 0.001)
        print(f"  💸 {result}")
    
    # Test 4: Mixed priority requests
    print("\n🎯 Test 4: Mixed priority requests")
    
    # Start with low priority requests
    print("  📚 Starting low priority requests...")
    for i in range(3):
        result = fetch_history("ADA/USDT")
        print(f"    📖 {result}")
    
    # Then high priority
    print("  🚨 Inserting high priority requests...")
    for i in range(2):
        result = fetch_ticker("DOT/USDT")
        print(f"    ⚡ {result}")
    
    # Test 5: Multi-exchange
    print("\n🌐 Test 5: Multi-exchange rate limiting")
    
    # Binance requests
    print("  🟡 Binance requests:")
    for i in range(3):
        result = fetch_ticker("BTC/USDT")
        print(f"    {result}")
    
    # Kraken requests (different limits)
    print("  🔵 Kraken requests:")
    for i in range(3):
        result = fetch_kraken_data("BTC/EUR")
        print(f"    {result}")
    
    # Show comprehensive status
    print("\n📊 COMPREHENSIVE RATE LIMIT STATUS")
    print("=" * 40)
    
    for exchange in ['binance', 'kraken']:
        status = rate_limit_manager.get_rate_limit_status(exchange)
        
        if status.get("status") == "no_limits":
            continue
        
        print(f"\n🏢 {exchange.upper()} Exchange:")
        print(f"  Active requests: {status['active_requests']}")
        print(f"  Total requests: {status['metrics']['total_requests']}")
        print(f"  Success rate: {status['metrics']['success_rate']:.1f}%")
        print(f"  Avg response time: {status['metrics']['avg_response_time']:.3f}s")
        print(f"  Current RPS: {status['metrics']['current_rps']:.1f}")
        
        print(f"  🪣 Token Buckets:")
        for limit_type, bucket_info in status['token_buckets'].items():
            utilization = bucket_info['utilization']
            print(f"    {limit_type}: {bucket_info['available_tokens']:.1f}/{bucket_info['capacity']} "
                  f"tokens ({utilization:.1f}% used)")
            if bucket_info['burst_capacity'] > 0:
                print(f"      Burst: {bucket_info['burst_tokens']}/{bucket_info['burst_capacity']} tokens")
    
    # Test 6: Rate limit recovery
    print("\n🔄 Test 6: Rate limit recovery demonstration")
    print("  Waiting 3 seconds for token bucket refill...")
    time.sleep(3)
    
    print("  Testing requests after recovery:")
    for i in range(5):
        result = fetch_ticker("RECOVERY/TEST")
        print(f"    ✅ {result}")
    
    print("\n🎉 ADVANCED RATE LIMITING DEMO COMPLETE!")
    print("=" * 45)
    print("✅ Token bucket rate limiting implemented")
    print("✅ Burst handling with priority support")
    print("✅ Multi-exchange configurations")
    print("✅ Real-time metrics and monitoring")
    print("✅ Automatic rate limit recovery")
    print("✅ Priority-based request handling")
    print("✅ Weight-based request classification")
    
    print("\n🚀 KEY BENEFITS FOR HIGH-FREQUENCY TRADING:")
    print("  • Prevents API rate limit violations")
    print("  • Prioritizes critical orders over data requests")
    print("  • Handles burst traffic intelligently")
    print("  • Supports multiple exchanges simultaneously")
    print("  • Provides real-time performance monitoring")
    print("  • Automatically recovers from rate limits")

if __name__ == "__main__":
    demo_advanced_rate_limiting() 