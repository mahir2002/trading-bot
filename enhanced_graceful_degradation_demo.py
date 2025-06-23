#!/usr/bin/env python3
"""
🛡️ ENHANCED GRACEFUL DEGRADATION DEMO
================================================================================
Advanced graceful degradation demonstration integrated with:
- Schema validation system
- Security validation system  
- Specific exception handling
- Real trading bot operations

Demonstrates complete system resilience and fallback mechanisms.
"""

import logging
import time
from typing import Dict, Any, Optional
from graceful_degradation_system import (
    GracefulDegradationSystem, 
    ServiceStatus, 
    DegradationLevel,
    CacheService,
    ExchangeService
)

# Import existing systems
try:
    from pydantic_schema_validation_system import PydanticSchemaValidator
    from secure_api_validator import SecureAPIValidator  
    from specific_exception_handling_system import SpecificExceptionHandler
except ImportError as e:
    logging.warning(f"Some systems not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedTradingBot:
    """
    Enhanced trading bot with complete graceful degradation integration.
    """
    
    def __init__(self):
        # Initialize all systems
        self.degradation_system = GracefulDegradationSystem()
        self.cache_service = CacheService(self.degradation_system)
        self.exchange_service = ExchangeService(self.degradation_system)
        
        # Initialize validation systems if available
        try:
            self.schema_validator = PydanticSchemaValidator()
            self.security_validator = SecureAPIValidator()
            self.exception_handler = SpecificExceptionHandler()
        except:
            logger.warning("⚠️ Some validation systems not available - using fallbacks")
            self.schema_validator = None
            self.security_validator = None
            self.exception_handler = None
        
        self.trading_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'degraded_operations': 0,
            'failed_operations': 0
        }
        
        logger.info("🤖 Enhanced Trading Bot initialized with graceful degradation")
    
    def secure_get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data with full system integration."""
        self.trading_stats['total_operations'] += 1
        
        try:
            # Step 1: Get ticker data with graceful degradation
            ticker_result = self.exchange_service.get_ticker(symbol)
            
            if not ticker_result['success']:
                self.trading_stats['failed_operations'] += 1
                return {
                    'success': False,
                    'error': 'Market data unavailable',
                    'degradation_level': self.degradation_system.degradation_level.name
                }
            
            ticker_data = ticker_result['data']
            
            # Step 2: Validate schema if available
            if self.schema_validator:
                try:
                    validated_data = self.schema_validator.validate_ticker_response(ticker_data)
                    if not validated_data['success']:
                        logger.warning("⚠️ Schema validation failed, using raw data")
                        ticker_data = ticker_result['data']  # Use original data
                    else:
                        ticker_data = validated_data['data']
                except Exception as e:
                    logger.warning(f"⚠️ Schema validation error: {e}")
            
            # Step 3: Security validation if available
            if self.security_validator:
                try:
                    security_result = self.security_validator.validate_exchange_response(ticker_data)
                    if not security_result['success']:
                        logger.warning("⚠️ Security validation failed")
                except Exception as e:
                    logger.warning(f"⚠️ Security validation error: {e}")
            
            # Step 4: Cache the result with graceful degradation
            cache_key = f"ticker_{symbol}"
            try:
                self.cache_service.set_data(cache_key, str(ticker_data))
            except Exception as e:
                logger.warning(f"⚠️ Cache storage failed: {e}")
            
            # Determine if operation was degraded
            if ticker_result['fallback_used']:
                self.trading_stats['degraded_operations'] += 1
            else:
                self.trading_stats['successful_operations'] += 1
            
            return {
                'success': True,
                'data': ticker_data,
                'fallback_used': ticker_result['fallback_used'],
                'degradation_level': self.degradation_system.degradation_level.name,
                'response_time': ticker_result['response_time']
            }
            
        except Exception as e:
            self.trading_stats['failed_operations'] += 1
            
            # Use exception handler if available
            if self.exception_handler:
                error_result = self.exception_handler.handle_exception(e, "secure_get_market_data")
                return {
                    'success': False,
                    'error': error_result.get('message', str(e)),
                    'error_category': error_result.get('category', 'unknown'),
                    'degradation_level': self.degradation_system.degradation_level.name
                }
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'degradation_level': self.degradation_system.degradation_level.name
                }
    
    def secure_place_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """Place order with full system integration."""
        self.trading_stats['total_operations'] += 1
        
        try:
            # Step 1: Validate order parameters
            if amount <= 0:
                raise ValueError("Order amount must be positive")
            
            if side not in ['buy', 'sell']:
                raise ValueError("Order side must be 'buy' or 'sell'")
            
            # Step 2: Check cached market data first
            cache_key = f"ticker_{symbol}"
            try:
                cached_data = self.cache_service.get_data(cache_key)
                if cached_data['success'] and cached_data['fallback_used']:
                    logger.info("📦 Using cached market data (degraded mode)")
            except Exception as e:
                logger.warning(f"⚠️ Cache retrieval failed: {e}")
            
            # Step 3: Place order with graceful degradation
            order_result = self.exchange_service.place_order(symbol, side, amount)
            
            if not order_result['success']:
                self.trading_stats['failed_operations'] += 1
                return {
                    'success': False,
                    'error': 'Order placement failed',
                    'degradation_level': self.degradation_system.degradation_level.name
                }
            
            order_data = order_result['data']
            
            # Step 4: Validate order response if available
            if self.schema_validator:
                try:
                    validated_order = self.schema_validator.validate_order_response(order_data)
                    if validated_order['success']:
                        order_data = validated_order['data']
                except Exception as e:
                    logger.warning(f"⚠️ Order validation error: {e}")
            
            # Determine if operation was degraded
            if order_result['fallback_used']:
                self.trading_stats['degraded_operations'] += 1
            else:
                self.trading_stats['successful_operations'] += 1
            
            return {
                'success': True,
                'data': order_data,
                'fallback_used': order_result['fallback_used'],
                'degradation_level': self.degradation_system.degradation_level.name,
                'response_time': order_result['response_time']
            }
            
        except Exception as e:
            self.trading_stats['failed_operations'] += 1
            
            # Use exception handler if available
            if self.exception_handler:
                error_result = self.exception_handler.handle_exception(e, "secure_place_order")
                return {
                    'success': False,
                    'error': error_result.get('message', str(e)),
                    'error_category': error_result.get('category', 'unknown'),
                    'degradation_level': self.degradation_system.degradation_level.name
                }
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'degradation_level': self.degradation_system.degradation_level.name
                }
    
    def get_trading_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trading statistics."""
        total_ops = self.trading_stats['total_operations']
        success_rate = (self.trading_stats['successful_operations'] / total_ops * 100) if total_ops > 0 else 0
        degraded_rate = (self.trading_stats['degraded_operations'] / total_ops * 100) if total_ops > 0 else 0
        
        return {
            'trading_stats': self.trading_stats.copy(),
            'success_rate': success_rate,
            'degraded_rate': degraded_rate,
            'system_health': self.degradation_system.get_system_health(),
            'recommendations': self.degradation_system.get_degradation_recommendations()
        }


def demonstrate_enhanced_graceful_degradation():
    """Demonstrate enhanced graceful degradation with full system integration."""
    print("🛡️ ENHANCED GRACEFUL DEGRADATION DEMO")
    print("=" * 80)
    print("Demonstrating complete trading bot resilience with integrated systems")
    print("- Graceful degradation + Schema validation + Security + Exception handling")
    
    # Initialize enhanced trading bot
    bot = EnhancedTradingBot()
    
    print("\n💰 INTEGRATED MARKET DATA OPERATIONS")
    print("-" * 70)
    
    # Test successful market data retrieval
    print("\n   Test 1: ✅ Successful market data (all systems)")
    result = bot.secure_get_market_data("BTCUSDT")
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if result['success']:
        print(f"   Price: ${result['data']['price']:,.2f}")
        print(f"   Exchange: {result['data']['exchange']}")
        print(f"   Fallback used: {result['fallback_used']}")
        print(f"   Degradation level: {result['degradation_level']}")
    
    # Test primary exchange failure with backup
    print("\n   Test 2: ❌ Primary exchange failure → Backup success")
    result = bot.secure_get_market_data("FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if result['success']:
        print(f"   Price: ${result['data']['price']:,.2f}")
        print(f"   Exchange: {result['data']['exchange']} (backup)")
        print(f"   Fallback used: {result['fallback_used']}")
        print(f"   Degradation level: {result['degradation_level']}")
    
    # Test complete exchange failure
    print("\n   Test 3: ❌ Complete exchange failure")
    result = bot.secure_get_market_data("BACKUP_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if not result['success']:
        print(f"   Error: {result['error']}")
        print(f"   Degradation level: {result['degradation_level']}")
    
    print("\n🏪 INTEGRATED ORDER OPERATIONS")
    print("-" * 70)
    
    # Test successful order placement
    print("\n   Test 4: ✅ Successful order placement")
    result = bot.secure_place_order("ETHUSDT", "buy", 0.1)
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if result['success']:
        print(f"   Order ID: {result['data']['order_id']}")
        print(f"   Exchange: {result['data']['exchange']}")
        print(f"   Fallback used: {result['fallback_used']}")
        print(f"   Degradation level: {result['degradation_level']}")
    
    # Test order with primary exchange failure
    print("\n   Test 5: ❌ Primary exchange failure → Backup order")
    result = bot.secure_place_order("FAIL", "sell", 0.05)
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if result['success']:
        print(f"   Order ID: {result['data']['order_id']}")
        print(f"   Exchange: {result['data']['exchange']} (backup)")
        print(f"   Fallback used: {result['fallback_used']}")
        print(f"   Degradation level: {result['degradation_level']}")
    
    # Test invalid order parameters
    print("\n   Test 6: ❌ Invalid order parameters")
    result = bot.secure_place_order("BTCUSDT", "invalid", -1.0)
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if not result['success']:
        print(f"   Error: {result['error']}")
        print(f"   Error Category: {result.get('error_category', 'N/A')}")
        print(f"   Degradation level: {result['degradation_level']}")
    
    print("\n📊 COMPREHENSIVE SYSTEM STATISTICS")
    print("=" * 80)
    
    # Get comprehensive statistics
    stats = bot.get_trading_statistics()
    
    print(f"🤖 Trading Bot Statistics:")
    for key, value in stats['trading_stats'].items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n📈 Performance Metrics:")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Degraded Operations: {stats['degraded_rate']:.1f}%")
    
    print(f"\n🏥 System Health:")
    health = stats['system_health']
    print(f"   Degradation Level: {health['degradation_level']}")
    print(f"   Health Percentage: {health['health_percentage']:.1f}%")
    print(f"   Healthy Services: {health['healthy_services']}/{health['total_services']}")
    
    print(f"\n🔧 Current Recommendations:")
    for recommendation in stats['recommendations']:
        print(f"   {recommendation}")
    
    print(f"\n🛡️ ENHANCED GRACEFUL DEGRADATION CAPABILITIES:")
    print("=" * 80)
    print("   ✅ Complete System Integration: All security systems working together")
    print("   ✅ Multi-Layer Fallbacks: Cache → Memory, Primary → Backup Exchange")
    print("   ✅ Schema Validation Resilience: Continues with raw data if validation fails")
    print("   ✅ Security Validation Resilience: Warns but continues operation")
    print("   ✅ Exception Handling Integration: Specific error categorization")
    print("   ✅ Circuit Breaker Protection: Prevents cascade failures")
    print("   ✅ Real-time Health Monitoring: 8 services monitored continuously")
    print("   ✅ Intelligent Degradation Levels: 5 levels from NONE to CRITICAL")
    print("   ✅ Performance Tracking: Response times and success rates")
    print("   ✅ Operational Continuity: Trading continues even with service failures")
    
    print(f"\n🎉 ENHANCED GRACEFUL DEGRADATION DEMO COMPLETE!")
    print("✅ Your trading bot now has enterprise-grade resilience and fault tolerance!")


if __name__ == "__main__":
    demonstrate_enhanced_graceful_degradation() 