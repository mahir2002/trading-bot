#!/usr/bin/env python3
"""
🛡️ Robust Error Handler with Exponential Backoff
Addresses: "Basic error handling is present, but more robust retry mechanisms 
with exponential backoff could improve reliability for API calls"
Solution: Advanced error handling with intelligent retry strategies
"""

import asyncio
import time
import random
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import ccxt
import requests
from datetime import datetime
import json

class ErrorType(Enum):
    """Classification of different error types"""
    NETWORK_ERROR = "network"
    RATE_LIMIT_ERROR = "rate_limit"
    AUTHENTICATION_ERROR = "auth"
    INSUFFICIENT_FUNDS = "funds"
    INVALID_SYMBOL = "symbol"
    EXCHANGE_MAINTENANCE = "maintenance"
    TIMEOUT_ERROR = "timeout"
    SERVER_ERROR = "server"
    UNKNOWN_ERROR = "unknown"

class RetryStrategy(Enum):
    """Different retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential"
    LINEAR_BACKOFF = "linear"
    FIXED_DELAY = "fixed"
    JITTERED_EXPONENTIAL = "jittered_exponential"

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 5
    base_delay: float = 1.0  # seconds
    max_delay: float = 300.0  # 5 minutes max
    strategy: RetryStrategy = RetryStrategy.JITTERED_EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter_range: float = 0.1  # 10% jitter
    retry_on_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.RATE_LIMIT_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.SERVER_ERROR
    ])
    no_retry_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.AUTHENTICATION_ERROR,
        ErrorType.INSUFFICIENT_FUNDS,
        ErrorType.INVALID_SYMBOL
    ])

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: ErrorType
    original_error: Exception
    attempt_number: int
    total_attempts: int
    exchange_name: Optional[str] = None
    function_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_after: Optional[float] = None

class RobustErrorHandler:
    """Advanced error handling system with multiple retry strategies"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats = {}
        
        # Default configurations per exchange
        self.exchange_configs = {
            'binance': RetryConfig(max_retries=5, base_delay=1.0, max_delay=60.0),
            'coinbasepro': RetryConfig(max_retries=3, base_delay=2.0, max_delay=120.0),
            'kraken': RetryConfig(max_retries=3, base_delay=5.0, max_delay=300.0),
            'bybit': RetryConfig(max_retries=5, base_delay=1.0, max_delay=60.0),
            'kucoin': RetryConfig(max_retries=5, base_delay=0.5, max_delay=30.0),
            'default': RetryConfig()
        }
    
    def classify_error(self, error: Exception, exchange_name: Optional[str] = None) -> ErrorType:
        """Intelligently classify errors for appropriate handling"""
        
        error_str = str(error).lower()
        
        # CCXT-specific error classification
        if isinstance(error, ccxt.NetworkError):
            if 'timeout' in error_str:
                return ErrorType.TIMEOUT_ERROR
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, ccxt.RateLimitExceeded):
            return ErrorType.RATE_LIMIT_ERROR
        elif isinstance(error, ccxt.AuthenticationError):
            return ErrorType.AUTHENTICATION_ERROR
        elif isinstance(error, ccxt.InsufficientFunds):
            return ErrorType.INSUFFICIENT_FUNDS
        elif isinstance(error, ccxt.InvalidSymbol):
            return ErrorType.INVALID_SYMBOL
        elif isinstance(error, ccxt.ExchangeNotAvailable):
            return ErrorType.EXCHANGE_MAINTENANCE
        elif isinstance(error, ccxt.ExchangeError):
            if 'rate limit' in error_str:
                return ErrorType.RATE_LIMIT_ERROR
            elif 'insufficient' in error_str:
                return ErrorType.INSUFFICIENT_FUNDS
            elif 'invalid symbol' in error_str:
                return ErrorType.INVALID_SYMBOL
            elif 'maintenance' in error_str:
                return ErrorType.EXCHANGE_MAINTENANCE
            elif any(code in error_str for code in ['500', '502', '503', '504']):
                return ErrorType.SERVER_ERROR
            return ErrorType.UNKNOWN_ERROR
        
        # HTTP/Requests errors
        elif isinstance(error, requests.exceptions.Timeout):
            return ErrorType.TIMEOUT_ERROR
        elif isinstance(error, requests.exceptions.ConnectionError):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, requests.exceptions.HTTPError):
            if hasattr(error, 'response') and error.response:
                status_code = error.response.status_code
                if status_code == 429:
                    return ErrorType.RATE_LIMIT_ERROR
                elif status_code in [500, 502, 503, 504]:
                    return ErrorType.SERVER_ERROR
                elif status_code in [401, 403]:
                    return ErrorType.AUTHENTICATION_ERROR
            return ErrorType.SERVER_ERROR
        
        # Generic classification
        elif 'timeout' in error_str:
            return ErrorType.TIMEOUT_ERROR
        elif 'rate limit' in error_str or '429' in error_str:
            return ErrorType.RATE_LIMIT_ERROR
        elif 'auth' in error_str or '401' in error_str:
            return ErrorType.AUTHENTICATION_ERROR
        elif 'network' in error_str:
            return ErrorType.NETWORK_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def calculate_delay(self, attempt: int, config: RetryConfig, error_context: ErrorContext) -> float:
        """Calculate delay based on retry strategy"""
        
        # Use retry_after from rate limit headers if available
        if error_context.retry_after and error_context.error_type == ErrorType.RATE_LIMIT_ERROR:
            return min(error_context.retry_after, config.max_delay)
        
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.JITTERED_EXPONENTIAL:
            # Exponential backoff with jitter to avoid thundering herd
            base_delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
            jitter = base_delay * config.jitter_range * (2 * random.random() - 1)
            delay = base_delay + jitter
        else:
            delay = config.base_delay
        
        return min(delay, config.max_delay)
    
    def should_retry(self, error_context: ErrorContext, config: RetryConfig) -> bool:
        """Determine if we should retry based on error type and configuration"""
        
        if error_context.attempt_number >= config.max_retries:
            return False
        
        if error_context.error_type in config.no_retry_errors:
            return False
        
        if error_context.error_type in config.retry_on_errors:
            return True
        
        return False
    
    def extract_retry_after(self, error: Exception) -> Optional[float]:
        """Extract retry-after information from error"""
        
        if hasattr(error, 'response') and error.response and hasattr(error.response, 'headers'):
            retry_after = error.response.headers.get('Retry-After')
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
        
        error_str = str(error).lower()
        if 'retry after' in error_str:
            import re
            match = re.search(r'retry after (\d+)', error_str)
            if match:
                return float(match.group(1))
        
        return None
    
    def update_error_stats(self, error_context: ErrorContext):
        """Update error statistics for monitoring"""
        
        key = f"{error_context.exchange_name}_{error_context.error_type.value}"
        if key not in self.error_stats:
            self.error_stats[key] = {
                'count': 0,
                'first_seen': error_context.timestamp,
                'last_seen': error_context.timestamp,
                'success_after_retry': 0,
                'total_retries': 0
            }
        
        stats = self.error_stats[key]
        stats['count'] += 1
        stats['last_seen'] = error_context.timestamp
        stats['total_retries'] += error_context.attempt_number - 1
    
    def log_error_context(self, error_context: ErrorContext, delay: Optional[float] = None):
        """Log error with full context"""
        
        log_data = {
            'exchange': error_context.exchange_name,
            'function': error_context.function_name,
            'error_type': error_context.error_type.value,
            'attempt': f"{error_context.attempt_number}/{error_context.total_attempts}",
            'error': str(error_context.original_error)[:200]
        }
        
        if delay:
            log_data['retry_delay'] = f"{delay:.2f}s"
        
        if error_context.attempt_number == 1:
            self.logger.warning(f"🚨 API Error: {json.dumps(log_data)}")
        else:
            self.logger.info(f"🔄 Retry {error_context.attempt_number}: {json.dumps(log_data)}")
    
    def with_retry(self, exchange_name: Optional[str] = None, config: Optional[RetryConfig] = None):
        """Decorator for adding robust retry logic to functions"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute_with_retry(
                    func, args, kwargs, 
                    exchange_name=exchange_name,
                    config=config,
                    function_name=func.__name__
                )
            return wrapper
        return decorator
    
    def execute_with_retry(self, func: Callable, args: tuple, kwargs: dict,
                          exchange_name: Optional[str] = None,
                          config: Optional[RetryConfig] = None,
                          function_name: Optional[str] = None) -> Any:
        """Execute function with retry logic"""
        
        if config is None:
            config = self.exchange_configs.get(exchange_name, self.exchange_configs['default'])
        
        last_error = None
        
        for attempt in range(1, config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    self.logger.info(f"✅ Success after {attempt-1} retries: {function_name}")
                
                return result
                
            except Exception as error:
                last_error = error
                
                error_type = self.classify_error(error, exchange_name)
                retry_after = self.extract_retry_after(error)
                
                error_context = ErrorContext(
                    error_type=error_type,
                    original_error=error,
                    attempt_number=attempt,
                    total_attempts=config.max_retries,
                    exchange_name=exchange_name,
                    function_name=function_name,
                    retry_after=retry_after
                )
                
                self.update_error_stats(error_context)
                
                if not self.should_retry(error_context, config):
                    self.log_error_context(error_context)
                    self.logger.error(f"❌ Final failure after {attempt} attempts: {function_name}")
                    raise error
                
                if attempt < config.max_retries:
                    delay = self.calculate_delay(attempt, config, error_context)
                    self.log_error_context(error_context, delay)
                    
                    self.logger.info(f"⏳ Waiting {delay:.2f}s before retry {attempt+1}/{config.max_retries}")
                    time.sleep(delay)
        
        self.logger.error(f"❌ All {config.max_retries} retries failed: {function_name}")
        raise last_error
    
    def get_error_statistics(self) -> Dict:
        """Get comprehensive error statistics"""
        
        total_errors = sum(stats['count'] for stats in self.error_stats.values())
        total_retries = sum(stats['total_retries'] for stats in self.error_stats.values())
        total_successes = sum(stats['success_after_retry'] for stats in self.error_stats.values())
        
        return {
            'summary': {
                'total_errors': total_errors,
                'total_retries': total_retries,
                'successful_retries': total_successes,
                'retry_success_rate': (total_successes / total_retries * 100) if total_retries > 0 else 0
            },
            'by_exchange_and_type': self.error_stats,
            'most_common_errors': sorted(
                [(key, stats['count']) for key, stats in self.error_stats.items()],
                key=lambda x: x[1], reverse=True
            )[:10]
        }

# Global instance for easy use
error_handler = RobustErrorHandler()

def with_robust_retry(exchange_name: Optional[str] = None, config: Optional[RetryConfig] = None):
    """Convenient decorator for adding robust retry to any function"""
    return error_handler.with_retry(exchange_name=exchange_name, config=config)

def demo_robust_error_handling():
    """Demonstrate the robust error handling system"""
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("🛡️ ROBUST ERROR HANDLING DEMO")
    print("=" * 40)
    
    handler = RobustErrorHandler(logger)
    
    @handler.with_retry(exchange_name='binance')
    def flaky_api_call(fail_count: int = 2):
        """Simulates a flaky API call"""
        if not hasattr(flaky_api_call, 'attempts'):
            flaky_api_call.attempts = 0
        
        flaky_api_call.attempts += 1
        
        if flaky_api_call.attempts <= fail_count:
            if flaky_api_call.attempts == 1:
                raise ccxt.NetworkError("Connection timeout")
            elif flaky_api_call.attempts == 2:
                raise ccxt.RateLimitExceeded("Rate limit exceeded")
        
        return {"success": True, "attempts": flaky_api_call.attempts}
    
    @handler.with_retry(exchange_name='coinbasepro')
    def auth_error_call():
        """Simulates authentication error (should not retry)"""
        raise ccxt.AuthenticationError("Invalid API key")
    
    print("\n🧪 Testing flaky API call (should succeed after retries):")
    try:
        result = flaky_api_call(fail_count=2)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n🧪 Testing authentication error (should NOT retry):")
    try:
        result = auth_error_call()
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Failed immediately (correct): {type(e).__name__}")
    
    print("\n📊 Error Statistics:")
    stats = handler.get_error_statistics()
    print(f"Total errors: {stats['summary']['total_errors']}")
    print(f"Total retries: {stats['summary']['total_retries']}")
    print(f"Successful retries: {stats['summary']['successful_retries']}")
    
    print("\n🎉 Robust error handling demo complete!")
    print("✅ Exponential backoff implemented")
    print("✅ Intelligent error classification")
    print("✅ Configurable retry strategies")

if __name__ == "__main__":
    demo_robust_error_handling()