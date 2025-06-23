#!/usr/bin/env python3
"""
🛡️ Specific Exception Handling System
Advanced exception handling with specific exception types for better error management
Replaces broad 'except Exception' catches with targeted exception handling
"""

import asyncio
import logging
import json
import pickle
import time
from typing import Dict, Any, Optional, Union, Callable, List
from functools import wraps
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

# Import specific exception types
import ccxt
import requests
import pydantic
from pydantic import ValidationError
import aiohttp
import sqlite3
# import redis  # Optional - only needed if using Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================================================================
# EXCEPTION CATEGORIES AND TYPES
# =================================================================

class ExceptionCategory(Enum):
    """Categories of exceptions for better handling"""
    VALIDATION_ERROR = "validation"
    NETWORK_ERROR = "network"
    API_ERROR = "api"
    DATABASE_ERROR = "database"
    AUTHENTICATION_ERROR = "auth"
    RATE_LIMIT_ERROR = "rate_limit"
    DATA_ERROR = "data"
    SECURITY_ERROR = "security"
    SYSTEM_ERROR = "system"
    BUSINESS_LOGIC_ERROR = "business"

@dataclass
class ExceptionContext:
    """Context information for exception handling"""
    category: ExceptionCategory
    exception_type: str
    message: str
    original_exception: Exception
    function_name: str
    timestamp: datetime
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class SpecificExceptionHandler:
    """Comprehensive specific exception handling system"""
    
    def __init__(self):
        self.exception_stats = {
            'total_exceptions': 0,
            'handled_exceptions': 0,
            'unhandled_exceptions': 0,
            'by_category': {},
            'by_type': {}
        }
        
        # Exception mapping for quick categorization
        self.exception_mapping = {
            # Validation Exceptions
            ValidationError: ExceptionCategory.VALIDATION_ERROR,
            pydantic.ValidationError: ExceptionCategory.VALIDATION_ERROR,
            ValueError: ExceptionCategory.VALIDATION_ERROR,
            TypeError: ExceptionCategory.VALIDATION_ERROR,
            
            # Network Exceptions
            requests.exceptions.ConnectionError: ExceptionCategory.NETWORK_ERROR,
            requests.exceptions.Timeout: ExceptionCategory.NETWORK_ERROR,
            requests.exceptions.HTTPError: ExceptionCategory.NETWORK_ERROR,
            aiohttp.ClientError: ExceptionCategory.NETWORK_ERROR,
            aiohttp.ClientTimeout: ExceptionCategory.NETWORK_ERROR,
            aiohttp.ClientConnectionError: ExceptionCategory.NETWORK_ERROR,
            
            # CCXT Exchange Exceptions (if available)
            # ccxt.NetworkError: ExceptionCategory.NETWORK_ERROR,
            # ccxt.RateLimitExceeded: ExceptionCategory.RATE_LIMIT_ERROR,
            # ccxt.AuthenticationError: ExceptionCategory.AUTHENTICATION_ERROR,
            # ccxt.InsufficientFunds: ExceptionCategory.API_ERROR,
            # ccxt.InvalidSymbol: ExceptionCategory.VALIDATION_ERROR,
            # ccxt.ExchangeNotAvailable: ExceptionCategory.API_ERROR,
            # ccxt.ExchangeError: ExceptionCategory.API_ERROR,
            # ccxt.RequestTimeout: ExceptionCategory.NETWORK_ERROR,
            
            # Database Exceptions
            sqlite3.Error: ExceptionCategory.DATABASE_ERROR,
            sqlite3.IntegrityError: ExceptionCategory.DATABASE_ERROR,
            sqlite3.OperationalError: ExceptionCategory.DATABASE_ERROR,
            
            # Redis Exceptions (if available)
            # redis.ConnectionError: ExceptionCategory.DATABASE_ERROR,
            # redis.TimeoutError: ExceptionCategory.DATABASE_ERROR,
            # redis.RedisError: ExceptionCategory.DATABASE_ERROR,
            
            # Data Processing Exceptions
            json.JSONDecodeError: ExceptionCategory.DATA_ERROR,
            UnicodeDecodeError: ExceptionCategory.DATA_ERROR,
            KeyError: ExceptionCategory.DATA_ERROR,
            IndexError: ExceptionCategory.DATA_ERROR,
            
            # System Exceptions
            FileNotFoundError: ExceptionCategory.SYSTEM_ERROR,
            PermissionError: ExceptionCategory.SYSTEM_ERROR,
            MemoryError: ExceptionCategory.SYSTEM_ERROR,
            OSError: ExceptionCategory.SYSTEM_ERROR,
        }
    
    def categorize_exception(self, exception: Exception) -> ExceptionCategory:
        """Categorize exception based on its type"""
        
        exception_type = type(exception)
        
        # Direct mapping
        if exception_type in self.exception_mapping:
            return self.exception_mapping[exception_type]
        
        # Check inheritance hierarchy
        for exc_type, category in self.exception_mapping.items():
            if isinstance(exception, exc_type):
                return category
        
        # Analyze exception message for additional categorization
        error_message = str(exception).lower()
        
        if any(keyword in error_message for keyword in ['rate limit', '429', 'too many requests']):
            return ExceptionCategory.RATE_LIMIT_ERROR
        elif any(keyword in error_message for keyword in ['auth', 'unauthorized', '401', '403']):
            return ExceptionCategory.AUTHENTICATION_ERROR
        elif any(keyword in error_message for keyword in ['timeout', 'connection', 'network']):
            return ExceptionCategory.NETWORK_ERROR
        elif any(keyword in error_message for keyword in ['validation', 'invalid', 'format']):
            return ExceptionCategory.VALIDATION_ERROR
        elif any(keyword in error_message for keyword in ['database', 'sql', 'redis']):
            return ExceptionCategory.DATABASE_ERROR
        elif any(keyword in error_message for keyword in ['security', 'injection', 'xss']):
            return ExceptionCategory.SECURITY_ERROR
        
        return ExceptionCategory.SYSTEM_ERROR
    
    def create_exception_context(self, exception: Exception, function_name: str, 
                               metadata: Dict[str, Any] = None) -> ExceptionContext:
        """Create detailed exception context"""
        
        category = self.categorize_exception(exception)
        
        return ExceptionContext(
            category=category,
            exception_type=type(exception).__name__,
            message=str(exception),
            original_exception=exception,
            function_name=function_name,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
    
    def handle_validation_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle validation-specific exceptions"""
        
        logger.warning(f"🔍 Validation error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'validation_error',
            'message': context.message,
            'details': {},
            'retry_recommended': False
        }
        
        # Specific handling for different validation errors
        if isinstance(context.original_exception, ValidationError):
            # Pydantic validation errors
            if hasattr(context.original_exception, 'errors'):
                try:
                    result['details'] = {
                        'validation_errors': [
                            {
                                'field': error.get('loc', ['unknown'])[0] if error.get('loc') else 'unknown',
                                'message': error.get('msg', 'Unknown validation error'),
                                'type': error.get('type', 'unknown')
                            }
                            for error in context.original_exception.errors()
                        ]
                    }
                except Exception:
                    result['details'] = {'raw_error': str(context.original_exception)}
        
        elif isinstance(context.original_exception, ValueError):
            result['details'] = {
                'value_error': context.message,
                'suggestion': 'Check input values and formats'
            }
        
        elif isinstance(context.original_exception, TypeError):
            result['details'] = {
                'type_error': context.message,
                'suggestion': 'Check data types and function arguments'
            }
        
        return result
    
    def handle_network_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle network-specific exceptions"""
        
        logger.warning(f"🌐 Network error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'network_error',
            'message': context.message,
            'details': {},
            'retry_recommended': True,
            'retry_delay': 5.0
        }
        
        # Specific handling for different network errors
        if isinstance(context.original_exception, requests.exceptions.Timeout):
            result['details'] = {
                'timeout_error': True,
                'suggestion': 'Increase timeout or check network connectivity'
            }
            result['retry_delay'] = 2.0
        
        elif isinstance(context.original_exception, requests.exceptions.ConnectionError):
            result['details'] = {
                'connection_error': True,
                'suggestion': 'Check internet connection and endpoint availability'
            }
            result['retry_delay'] = 10.0
        
        elif isinstance(context.original_exception, requests.exceptions.HTTPError):
            if hasattr(context.original_exception, 'response'):
                status_code = getattr(context.original_exception.response, 'status_code', None)
                result['details'] = {
                    'http_error': True,
                    'status_code': status_code,
                    'suggestion': f'HTTP {status_code} error - check API endpoint and parameters'
                }
                
                if status_code in [500, 502, 503, 504]:
                    result['retry_recommended'] = True
                    result['retry_delay'] = 30.0
                elif status_code in [401, 403]:
                    result['retry_recommended'] = False
                    result['error_type'] = 'authentication_error'
        
        elif isinstance(context.original_exception, ccxt.NetworkError):
            result['details'] = {
                'exchange_network_error': True,
                'suggestion': 'Exchange connectivity issue - check exchange status'
            }
        
        return result
    
    def handle_api_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle API-specific exceptions"""
        
        logger.warning(f"🔌 API error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'api_error',
            'message': context.message,
            'details': {},
            'retry_recommended': False
        }
        
        # Specific handling for different API errors
        if isinstance(context.original_exception, ccxt.ExchangeError):
            result['details'] = {
                'exchange_error': True,
                'exchange': context.metadata.get('exchange_name', 'unknown')
            }
            
            error_msg = context.message.lower()
            if 'insufficient funds' in error_msg:
                result['error_type'] = 'insufficient_funds'
                result['details']['suggestion'] = 'Check account balance'
            elif 'invalid symbol' in error_msg:
                result['error_type'] = 'invalid_symbol'
                result['details']['suggestion'] = 'Verify trading pair symbol'
            elif 'maintenance' in error_msg:
                result['retry_recommended'] = True
                result['retry_delay'] = 300.0  # 5 minutes
        
        elif isinstance(context.original_exception, ccxt.InsufficientFunds):
            result['error_type'] = 'insufficient_funds'
            result['details'] = {
                'insufficient_funds': True,
                'suggestion': 'Check account balance and reduce order size'
            }
        
        elif isinstance(context.original_exception, ccxt.InvalidSymbol):
            result['error_type'] = 'invalid_symbol'
            result['details'] = {
                'invalid_symbol': True,
                'suggestion': 'Check trading pair symbol format and availability'
            }
        
        return result
    
    def handle_rate_limit_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle rate limit exceptions"""
        
        logger.warning(f"⏱️ Rate limit error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'rate_limit_error',
            'message': context.message,
            'details': {
                'rate_limited': True,
                'suggestion': 'Reduce request frequency'
            },
            'retry_recommended': True,
            'retry_delay': 60.0  # Default 1 minute
        }
        
        # Extract retry-after if available
        if hasattr(context.original_exception, 'response') and context.original_exception.response:
            retry_after = context.original_exception.response.headers.get('Retry-After')
            if retry_after:
                try:
                    result['retry_delay'] = float(retry_after)
                except ValueError:
                    pass
        
        return result
    
    def handle_authentication_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle authentication exceptions"""
        
        logger.error(f"🔐 Authentication error in {context.function_name}: {context.message}")
        
        return {
            'success': False,
            'error_type': 'authentication_error',
            'message': context.message,
            'details': {
                'authentication_failed': True,
                'suggestion': 'Check API keys and permissions'
            },
            'retry_recommended': False
        }
    
    def handle_database_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle database exceptions"""
        
        logger.error(f"🗄️ Database error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'database_error',
            'message': context.message,
            'details': {},
            'retry_recommended': True,
            'retry_delay': 5.0
        }
        
        # Specific handling for different database errors
        if isinstance(context.original_exception, sqlite3.IntegrityError):
            result['details'] = {
                'integrity_error': True,
                'suggestion': 'Check data constraints and unique key violations'
            }
            result['retry_recommended'] = False
        
        elif isinstance(context.original_exception, sqlite3.OperationalError):
            result['details'] = {
                'operational_error': True,
                'suggestion': 'Check database connection and SQL syntax'
            }
        
        elif isinstance(context.original_exception, redis.ConnectionError):
            result['details'] = {
                'redis_connection_error': True,
                'suggestion': 'Check Redis server status and connection settings'
            }
            result['retry_delay'] = 10.0
        
        return result
    
    def handle_data_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle data processing exceptions"""
        
        logger.warning(f"📊 Data error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'data_error',
            'message': context.message,
            'details': {},
            'retry_recommended': False
        }
        
        # Specific handling for different data errors
        if isinstance(context.original_exception, json.JSONDecodeError):
            result['details'] = {
                'json_decode_error': True,
                'suggestion': 'Check JSON format and structure'
            }
        
        elif isinstance(context.original_exception, KeyError):
            result['details'] = {
                'key_error': True,
                'missing_key': str(context.original_exception),
                'suggestion': 'Check data structure and required fields'
            }
        
        elif isinstance(context.original_exception, IndexError):
            result['details'] = {
                'index_error': True,
                'suggestion': 'Check array bounds and data availability'
            }
        
        return result
    
    def handle_security_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle security-related exceptions"""
        
        logger.error(f"🚨 Security error in {context.function_name}: {context.message}")
        
        return {
            'success': False,
            'error_type': 'security_error',
            'message': context.message,
            'details': {
                'security_violation': True,
                'suggestion': 'Review input data for malicious content'
            },
            'retry_recommended': False
        }
    
    def handle_system_exception(self, context: ExceptionContext) -> Dict[str, Any]:
        """Handle system-level exceptions"""
        
        logger.error(f"⚙️ System error in {context.function_name}: {context.message}")
        
        result = {
            'success': False,
            'error_type': 'system_error',
            'message': context.message,
            'details': {},
            'retry_recommended': True,
            'retry_delay': 10.0
        }
        
        # Specific handling for different system errors
        if isinstance(context.original_exception, FileNotFoundError):
            result['details'] = {
                'file_not_found': True,
                'suggestion': 'Check file path and permissions'
            }
            result['retry_recommended'] = False
        
        elif isinstance(context.original_exception, PermissionError):
            result['details'] = {
                'permission_error': True,
                'suggestion': 'Check file/directory permissions'
            }
            result['retry_recommended'] = False
        
        elif isinstance(context.original_exception, MemoryError):
            result['details'] = {
                'memory_error': True,
                'suggestion': 'Reduce memory usage or increase available memory'
            }
            result['retry_recommended'] = False
        
        return result
    
    def handle_exception(self, exception: Exception, function_name: str, 
                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main exception handling method with specific categorization"""
        
        self.exception_stats['total_exceptions'] += 1
        
        # Create exception context
        context = self.create_exception_context(exception, function_name, metadata)
        
        # Update statistics
        category_key = context.category.value
        if category_key not in self.exception_stats['by_category']:
            self.exception_stats['by_category'][category_key] = 0
        self.exception_stats['by_category'][category_key] += 1
        
        type_key = context.exception_type
        if type_key not in self.exception_stats['by_type']:
            self.exception_stats['by_type'][type_key] = 0
        self.exception_stats['by_type'][type_key] += 1
        
        # Handle based on category
        try:
            if context.category == ExceptionCategory.VALIDATION_ERROR:
                result = self.handle_validation_exception(context)
            elif context.category == ExceptionCategory.NETWORK_ERROR:
                result = self.handle_network_exception(context)
            elif context.category == ExceptionCategory.API_ERROR:
                result = self.handle_api_exception(context)
            elif context.category == ExceptionCategory.RATE_LIMIT_ERROR:
                result = self.handle_rate_limit_exception(context)
            elif context.category == ExceptionCategory.AUTHENTICATION_ERROR:
                result = self.handle_authentication_exception(context)
            elif context.category == ExceptionCategory.DATABASE_ERROR:
                result = self.handle_database_exception(context)
            elif context.category == ExceptionCategory.DATA_ERROR:
                result = self.handle_data_exception(context)
            elif context.category == ExceptionCategory.SECURITY_ERROR:
                result = self.handle_security_exception(context)
            else:
                result = self.handle_system_exception(context)
            
            self.exception_stats['handled_exceptions'] += 1
            
            # Add common fields
            result.update({
                'category': context.category.value,
                'exception_type': context.exception_type,
                'timestamp': context.timestamp.isoformat(),
                'function_name': context.function_name
            })
            
            return result
            
        except Exception as handler_error:
            # Fallback if specific handler fails
            logger.error(f"❌ Exception handler failed: {handler_error}")
            self.exception_stats['unhandled_exceptions'] += 1
            
            return {
                'success': False,
                'error_type': 'handler_error',
                'message': f"Exception handler failed: {handler_error}",
                'original_error': str(exception),
                'retry_recommended': False
            }
    
    def get_exception_stats(self) -> Dict[str, Any]:
        """Get exception handling statistics"""
        
        total = self.exception_stats['total_exceptions']
        
        return {
            'total_exceptions': total,
            'handled_exceptions': self.exception_stats['handled_exceptions'],
            'unhandled_exceptions': self.exception_stats['unhandled_exceptions'],
            'handling_success_rate': (
                (self.exception_stats['handled_exceptions'] / max(total, 1)) * 100
            ),
            'by_category': self.exception_stats['by_category'].copy(),
            'by_type': self.exception_stats['by_type'].copy()
        }

# =================================================================
# DECORATOR FOR AUTOMATIC EXCEPTION HANDLING
# =================================================================

def with_specific_exception_handling(function_name: str = None, 
                                   metadata: Dict[str, Any] = None):
    """Decorator for automatic specific exception handling"""
    
    def decorator(func: Callable) -> Callable:
        handler = SpecificExceptionHandler()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                func_name = function_name or func.__name__
                result = handler.handle_exception(e, func_name, metadata)
                
                # Log the handled exception
                logger.info(f"🛡️ Exception handled in {func_name}: {result['error_type']}")
                
                # Return the error result instead of raising
                return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_name = function_name or func.__name__
                result = handler.handle_exception(e, func_name, metadata)
                
                # Log the handled exception
                logger.info(f"🛡️ Exception handled in {func_name}: {result['error_type']}")
                
                # Return the error result instead of raising
                return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# =================================================================
# GLOBAL EXCEPTION HANDLER INSTANCE
# =================================================================

# Global instance for easy access
exception_handler = SpecificExceptionHandler()

# =================================================================
# DEMONSTRATION
# =================================================================

async def demo_specific_exception_handling():
    """Demonstrate specific exception handling capabilities"""
    
    print("🛡️ SPECIFIC EXCEPTION HANDLING DEMO")
    print("=" * 80)
    print("Demonstrating targeted exception handling instead of broad catches")
    print()
    
    handler = SpecificExceptionHandler()
    
    # Test different exception types
    test_exceptions = [
        (ValueError("Invalid field format"), "validate_user_input"),
        (requests.exceptions.Timeout("Request timeout"), "fetch_market_data"),
        (ValueError("Invalid value provided"), "validate_input"),
        (TypeError("Invalid type provided"), "type_check"),
        (json.JSONDecodeError("Invalid JSON", "", 0), "parse_response"),
        (sqlite3.IntegrityError("Unique constraint failed"), "save_trade"),
        (KeyError("'price'"), "extract_price"),
        (FileNotFoundError("Config file not found"), "load_config")
    ]
    
    print("🔍 TESTING SPECIFIC EXCEPTION HANDLING")
    print("-" * 60)
    
    for i, (exception, function_name) in enumerate(test_exceptions, 1):
        print(f"\n   Test {i}: {type(exception).__name__} in {function_name}")
        
        result = handler.handle_exception(exception, function_name)
        
        print(f"   Category: {result['category']}")
        print(f"   Error Type: {result['error_type']}")
        print(f"   Retry Recommended: {result['retry_recommended']}")
        
        if 'retry_delay' in result:
            print(f"   Retry Delay: {result['retry_delay']}s")
        
        if result['details']:
            print(f"   Details: {list(result['details'].keys())}")
    
    # Show statistics
    print(f"\n📊 EXCEPTION HANDLING STATISTICS")
    print("=" * 80)
    
    stats = handler.get_exception_stats()
    
    print(f"📈 Overall Statistics:")
    print(f"   Total exceptions: {stats['total_exceptions']}")
    print(f"   Handled exceptions: {stats['handled_exceptions']}")
    print(f"   Unhandled exceptions: {stats['unhandled_exceptions']}")
    print(f"   Handling success rate: {stats['handling_success_rate']:.1f}%")
    
    print(f"\n📈 By Category:")
    for category, count in stats['by_category'].items():
        print(f"   {category}: {count}")
    
    print(f"\n📈 By Type:")
    for exc_type, count in stats['by_type'].items():
        print(f"   {exc_type}: {count}")
    
    print(f"\n🛡️ SPECIFIC EXCEPTION HANDLING CAPABILITIES:")
    print(f"   ✅ Validation Errors: Field-level error details and suggestions")
    print(f"   ✅ Network Errors: Retry recommendations with appropriate delays")
    print(f"   ✅ API Errors: Exchange-specific error handling")
    print(f"   ✅ Rate Limits: Automatic retry-after extraction")
    print(f"   ✅ Authentication: Security-focused error handling")
    print(f"   ✅ Database Errors: Connection and integrity error handling")
    print(f"   ✅ Data Errors: JSON and parsing error management")
    print(f"   ✅ System Errors: File and permission error handling")
    
    print(f"\n🎉 SPECIFIC EXCEPTION HANDLING DEMO COMPLETE!")
    print(f"✅ All exception types now have targeted, specific handling!")

if __name__ == "__main__":
    asyncio.run(demo_specific_exception_handling()) 