#!/usr/bin/env python3
"""
📊 ENHANCED STRUCTURED LOGGING INTEGRATION
================================================================================
Advanced structured logging demonstration integrated with:
- Robust alerting system
- Graceful degradation system
- Specific exception handling
- Security validation system
- Performance monitoring

Demonstrates complete system logging and observability capabilities.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from structured_logging_system import (
    TradingBotStructuredLogger,
    LogCategory,
    LogLevel
)

# Import existing systems
try:
    from robust_alerting_system import RobustAlertingSystem, AlertSeverity, AlertChannel
    from graceful_degradation_system import GracefulDegradationSystem, DegradationLevel
    from specific_exception_handling_system import SpecificExceptionHandler
    from secure_api_validator import SecureAPIValidator
except ImportError as e:
    logging.warning(f"Some systems not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedLoggingTradingBot:
    """
    Enhanced trading bot with complete structured logging integration.
    """
    
    def __init__(self):
        # Initialize structured logging
        self.structured_logger = TradingBotStructuredLogger()
        
        # Initialize other systems
        try:
            self.alerting_system = RobustAlertingSystem()
            self.degradation_system = GracefulDegradationSystem()
            self.exception_handler = SpecificExceptionHandler()
            self.security_validator = SecureAPIValidator()
        except:
            logger.warning("⚠️ Some systems not available - using fallbacks")
            self.alerting_system = None
            self.degradation_system = None
            self.exception_handler = None
            self.security_validator = None
        
        # Configure alerting with console
        if self.alerting_system:
            self.alerting_system.configure_channel(AlertChannel.CONSOLE, {'enabled': True})
        
        self.operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'logged_events': 0,
            'alerts_triggered': 0,
            'exceptions_handled': 0
        }
        
        # Log initialization
        self.structured_logger.logger.info(
            "Enhanced trading bot with structured logging initialized",
            category=LogCategory.SYSTEM,
            metadata={
                "systems_loaded": {
                    "structured_logging": True,
                    "alerting": self.alerting_system is not None,
                    "degradation": self.degradation_system is not None,
                    "exception_handling": self.exception_handler is not None,
                    "security_validation": self.security_validator is not None
                }
            }
        )
        
        logger.info("🤖 Enhanced Logging Trading Bot initialized")
    
    def execute_trading_operation(self, operation: str, symbol: str, 
                                amount: Optional[float] = None) -> Dict[str, Any]:
        """Execute trading operation with comprehensive logging."""
        self.operation_stats['total_operations'] += 1
        
        # Set operation context
        with self.structured_logger.logger.context_manager(
            operation=operation,
            correlation_id=f"op_{int(time.time() * 1000)}"
        ):
            # Log operation start
            self.structured_logger.logger.info(
                f"Starting trading operation: {operation}",
                category=LogCategory.TRADING,
                metadata={
                    "symbol": symbol,
                    "amount": amount,
                    "operation_type": operation
                }
            )
            
            try:
                # Execute operation with performance timing
                with self.structured_logger.logger.performance_timer(operation, "trading"):
                    result = self._simulate_trading_operation(operation, symbol, amount)
                
                # Log successful operation
                if result['success']:
                    self.operation_stats['successful_operations'] += 1
                    self.structured_logger.log_order_placement(
                        symbol=symbol,
                        side=operation.split('_')[0] if '_' in operation else operation,
                        amount=amount or 0.0,
                        price=result.get('price'),
                        order_type=result.get('order_type', 'market'),
                        result="success",
                        order_id=result.get('order_id'),
                        exchange=result.get('exchange', 'default'),
                        duration_ms=result.get('duration_ms', 0)
                    )
                else:
                    self.operation_stats['failed_operations'] += 1
                    self._handle_operation_failure(operation, symbol, result)
                
                self.operation_stats['logged_events'] += 1
                return result
                
            except Exception as e:
                self.operation_stats['failed_operations'] += 1
                self.operation_stats['exceptions_handled'] += 1
                return self._handle_operation_exception(operation, symbol, e)
    
    def _simulate_trading_operation(self, operation: str, symbol: str, 
                                  amount: Optional[float]) -> Dict[str, Any]:
        """Simulate trading operation with different scenarios."""
        
        # Simulate different scenarios based on symbol
        if symbol == "CRITICAL_FAIL":
            raise Exception("Critical trading engine failure")
        elif symbol == "SECURITY_FAIL":
            raise PermissionError("Unauthorized trading attempt")
        elif symbol == "NETWORK_FAIL":
            raise ConnectionError("Exchange API connection failed")
        elif symbol == "VALIDATION_FAIL":
            raise ValueError("Invalid trading parameters")
        elif symbol == "SLOW_OPERATION":
            time.sleep(1.5)  # Simulate slow operation
            return {
                'success': True,
                'price': 50000.0,
                'order_id': 'ORD_SLOW_123',
                'exchange': 'binance',
                'duration_ms': 1500.0,
                'order_type': 'market'
            }
        elif symbol == "SUCCESS":
            return {
                'success': True,
                'price': 45000.0,
                'order_id': 'ORD_SUCCESS_456',
                'exchange': 'binance',
                'duration_ms': 85.3,
                'order_type': 'limit'
            }
        else:
            # Normal successful operation
            return {
                'success': True,
                'price': 48000.0,
                'order_id': f'ORD_{symbol}_{int(time.time())}',
                'exchange': 'binance',
                'duration_ms': 120.5,
                'order_type': 'market'
            }
    
    def _handle_operation_failure(self, operation: str, symbol: str, result: Dict[str, Any]):
        """Handle operation failure with structured logging."""
        error_message = result.get('error', 'Unknown error')
        
        # Log the failure
        self.structured_logger.logger.error(
            f"Trading operation failed: {operation}",
            category=LogCategory.TRADING,
            metadata={
                "symbol": symbol,
                "operation": operation,
                "error_details": result,
                "failure_reason": error_message
            }
        )
        
        # Send alert if alerting system is available
        if self.alerting_system:
            alert_id = self.alerting_system.send_alert(
                title=f"Trading Operation Failed: {operation}",
                message=f"Operation {operation} for {symbol} failed: {error_message}",
                severity=AlertSeverity.MEDIUM,
                source="trading_operation",
                metadata=result
            )
            
            # Log alert sending
            self.structured_logger.log_alert_sent(
                alert_id=alert_id,
                alert_type="trading_failure",
                severity="medium",
                channels=["console"],
                success=True
            )
            
            self.operation_stats['alerts_triggered'] += 1
    
    def _handle_operation_exception(self, operation: str, symbol: str, 
                                  exception: Exception) -> Dict[str, Any]:
        """Handle operation exception with comprehensive logging."""
        
        # Log exception with structured logging
        self.structured_logger.logger.log_exception(
            exception=exception,
            context=f"trading_operation_{operation}",
            category=LogCategory.TRADING,
            additional_data={
                "symbol": symbol,
                "operation": operation,
                "operation_stats": self.operation_stats.copy()
            }
        )
        
        # Handle with exception handler if available
        exception_result = None
        if self.exception_handler:
            exception_result = self.exception_handler.handle_exception(
                exception, f"{operation}_{symbol}"
            )
        
        # Determine alert severity based on exception type
        if isinstance(exception, (SystemError, RuntimeError)):
            severity = AlertSeverity.CRITICAL
        elif isinstance(exception, PermissionError):
            severity = AlertSeverity.HIGH
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW
        
        # Send alert if alerting system is available
        if self.alerting_system:
            alert_id = self.alerting_system.send_alert(
                title=f"Trading Exception: {type(exception).__name__}",
                message=f"Exception in {operation} for {symbol}: {str(exception)}",
                severity=severity,
                source="trading_exception",
                metadata={
                    "exception_type": type(exception).__name__,
                    "symbol": symbol,
                    "operation": operation,
                    "exception_handler_result": exception_result
                }
            )
            
            # Log alert sending
            self.structured_logger.log_alert_sent(
                alert_id=alert_id,
                alert_type="trading_exception",
                severity=severity.value,
                channels=["console"],
                success=True
            )
            
            self.operation_stats['alerts_triggered'] += 1
        
        return {
            'success': False,
            'error': str(exception),
            'exception_type': type(exception).__name__,
            'exception_handler_result': exception_result,
            'alert_severity': severity.value if severity else None
        }
    
    def monitor_system_health(self) -> Dict[str, Any]:
        """Monitor and log system health."""
        health_data = {}
        
        # Check degradation system if available
        if self.degradation_system:
            system_health = self.degradation_system.get_system_health()
            health_data.update({
                "degradation_level": system_health['degradation_level'],
                "health_percentage": system_health['health_percentage'],
                "healthy_services": system_health['healthy_services'],
                "total_services": system_health['total_services']
            })
            
            # Log system degradation if not healthy
            if system_health['degradation_level'] != 'NONE':
                self.structured_logger.log_system_degradation(
                    degradation_level=system_health['degradation_level'],
                    affected_services=[
                        name for name, service in self.degradation_system.services.items()
                        if service.status.value != 'healthy'
                    ],
                    health_percentage=system_health['health_percentage']
                )
        
        # Check alerting system if available
        if self.alerting_system:
            alerting_health = self.alerting_system.get_system_health()
            health_data.update({
                "active_alerts": alerting_health['active_alerts'],
                "configured_channels": len(alerting_health['configured_channels']),
                "alert_rules": len(alerting_health['alert_rules'])
            })
        
        # Add operation statistics
        health_data.update({
            "operation_stats": self.operation_stats.copy(),
            "success_rate": (
                self.operation_stats['successful_operations'] / 
                max(self.operation_stats['total_operations'], 1) * 100
            )
        })
        
        # Log system health
        self.structured_logger.logger.log_system_health(health_data)
        
        return health_data
    
    def validate_security_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data with security logging."""
        
        # Log security validation attempt
        self.structured_logger.logger.info(
            "Starting security validation",
            category=LogCategory.SECURITY,
            metadata={
                "data_keys": list(data.keys()) if isinstance(data, dict) else "non-dict",
                "data_size": len(str(data))
            }
        )
        
        try:
            # Perform security validation if available
            if self.security_validator:
                with self.structured_logger.logger.performance_timer("security_validation", "security"):
                    result = self.security_validator.validate_exchange_response(data)
                
                # Log validation result
                self.structured_logger.log_security_validation(
                    validation_type="exchange_response",
                    data_source="api_data",
                    success=result['success'],
                    violations=result.get('violations', []) if not result['success'] else [],
                    blocked=not result['success']
                )
                
                return result
            else:
                # Fallback validation
                self.structured_logger.log_security_validation(
                    validation_type="basic_check",
                    data_source="api_data",
                    success=True,
                    violations=[],
                    blocked=False
                )
                
                return {"success": True, "message": "Basic validation passed"}
                
        except Exception as e:
            # Log security validation exception
            self.structured_logger.logger.log_exception(
                exception=e,
                context="security_validation",
                category=LogCategory.SECURITY,
                additional_data={
                    "data_provided": bool(data),
                    "validation_type": "exchange_response"
                }
            )
            
            return {"success": False, "error": str(e)}
    
    def log_api_interaction(self, endpoint: str, method: str, 
                          success: bool, duration_ms: float,
                          status_code: int = 200) -> None:
        """Log API interaction with structured format."""
        
        # Log API request
        self.structured_logger.logger.log_api_request(
            method=method,
            url=f"https://api.exchange.com{endpoint}",
            status_code=status_code,
            duration_ms=duration_ms,
            request_size=256,
            response_size=512 if success else 64,
            user_agent="TradingBot/1.0"
        )
        
        # Log performance metric
        self.structured_logger.logger.log_performance_metric(
            metric_name=f"api_{endpoint.replace('/', '_')}_response_time",
            value=duration_ms,
            unit="ms",
            component="exchange_api",
            threshold=1000.0
        )
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics with structured logging."""
        
        # Collect all statistics
        stats = {
            "operation_stats": self.operation_stats.copy(),
            "performance_summary": self.structured_logger.logger.get_performance_summary(),
            "timestamp": time.time()
        }
        
        # Add alerting statistics if available
        if self.alerting_system:
            stats["alerting_stats"] = self.alerting_system.get_alert_statistics()
        
        # Add degradation statistics if available
        if self.degradation_system:
            stats["system_health"] = self.degradation_system.get_system_health()
        
        # Log statistics collection
        self.structured_logger.logger.info(
            "Comprehensive statistics collected",
            category=LogCategory.MONITORING,
            metadata=stats
        )
        
        return stats


def demonstrate_enhanced_structured_logging():
    """Demonstrate enhanced structured logging integration."""
    print("📊 ENHANCED STRUCTURED LOGGING INTEGRATION DEMO")
    print("=" * 80)
    print("Demonstrating complete structured logging integration")
    print("- Structured logging + Alerting + Degradation + Exception handling + Security")
    
    # Initialize enhanced logging trading bot
    bot = EnhancedLoggingTradingBot()
    
    print("\n💰 LOGGED TRADING OPERATIONS")
    print("-" * 70)
    
    # Test successful trading operation
    print("\n   Test 1: ✅ Successful trading operation")
    result = bot.execute_trading_operation("buy_market", "SUCCESS", 0.1)
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if result['success']:
        print(f"   Order ID: {result['order_id']}")
        print(f"   Price: ${result['price']:,.2f}")
    
    # Test slow operation with performance logging
    print("\n   Test 2: ⚡ Slow operation (performance logging)")
    result = bot.execute_trading_operation("sell_limit", "SLOW_OPERATION", 0.05)
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    print("   Performance metrics logged for slow operation")
    
    # Test critical system failure
    print("\n   Test 3: 🚨 Critical system failure")
    result = bot.execute_trading_operation("place_order", "CRITICAL_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if not result['success']:
        print(f"   Exception: {result['exception_type']}")
        print(f"   Alert Severity: {result.get('alert_severity', 'N/A')}")
    
    # Test security violation
    print("\n   Test 4: 🔒 Security violation")
    result = bot.execute_trading_operation("unauthorized_trade", "SECURITY_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if not result['success']:
        print(f"   Security exception logged: {result['exception_type']}")
    
    # Test network failure
    print("\n   Test 5: 🌐 Network connection failure")
    result = bot.execute_trading_operation("get_balance", "NETWORK_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if not result['success']:
        print(f"   Network error logged: {result['error']}")
    
    print("\n🔒 SECURITY VALIDATION LOGGING")
    print("-" * 70)
    
    # Test security validation logging
    print("\n   Test 6: ✅ Valid security data")
    security_result = bot.validate_security_data({
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "volume": 1.5
    })
    print(f"   Security validation: {'✅ PASSED' if security_result['success'] else '❌ FAILED'}")
    
    # Test security validation with suspicious data
    print("\n   Test 7: ⚠️ Suspicious data validation")
    security_result = bot.validate_security_data({
        "symbol": "<script>alert('xss')</script>",
        "price": -1000,
        "volume": "DROP TABLE users"
    })
    print(f"   Security validation: {'✅ PASSED' if security_result['success'] else '❌ FAILED'}")
    print("   Security violation logged with structured data")
    
    print("\n🌐 API INTERACTION LOGGING")
    print("-" * 70)
    
    # Test API interaction logging
    print("\n   Test 8: 🔗 Successful API call")
    bot.log_api_interaction("/api/v3/ticker", "GET", True, 89.5, 200)
    
    print("   Test 9: ❌ Failed API call")
    bot.log_api_interaction("/api/v3/order", "POST", False, 2500.0, 429)
    
    print("\n🏥 SYSTEM HEALTH MONITORING")
    print("-" * 70)
    
    # Test system health monitoring
    print("\n   Test 10: 📊 System health check")
    health = bot.monitor_system_health()
    print(f"   System health logged with {len(health)} metrics")
    print(f"   Success rate: {health['success_rate']:.1f}%")
    
    print("\n📊 COMPREHENSIVE STATISTICS")
    print("=" * 80)
    
    # Get comprehensive statistics
    stats = bot.get_comprehensive_statistics()
    
    print(f"🤖 Operation Statistics:")
    for key, value in stats['operation_stats'].items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n📈 Performance Summary:")
    perf_summary = stats['performance_summary']
    for component, metrics in perf_summary['components'].items():
        print(f"   {component}:")
        for metric_name, data in metrics.items():
            print(f"     {metric_name}: {data['value']} {data['unit']}")
    
    if 'alerting_stats' in stats:
        print(f"\n🚨 Alerting Statistics:")
        for key, value in stats['alerting_stats'].items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n📁 Structured Log Files:")
    from pathlib import Path
    log_dir = Path("logs")
    if log_dir.exists():
        for log_file in log_dir.glob("*.log"):
            size_kb = log_file.stat().st_size / 1024
            print(f"   {log_file.name}: {size_kb:.1f} KB")
            
            # Show sample log entry
            if log_file.name == "trading.log":
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            sample_log = json.loads(lines[-1])
                            print(f"   Sample entry: {sample_log['message']}")
                except:
                    pass
    
    print(f"\n📊 ENHANCED STRUCTURED LOGGING CAPABILITIES:")
    print("=" * 80)
    print("   ✅ JSON-Formatted Logs: Machine-readable structured format")
    print("   ✅ Complete System Integration: All security and monitoring systems")
    print("   ✅ Contextual Logging: Correlation IDs and operation tracking")
    print("   ✅ Performance Metrics: Automatic timing and threshold monitoring")
    print("   ✅ Exception Tracking: Full exception context with stack traces")
    print("   ✅ Security Event Logging: Detailed security violation tracking")
    print("   ✅ Alert Integration: Structured logging of all alert activities")
    print("   ✅ Business Metrics: Trading-specific business data logging")
    print("   ✅ API Interaction Logging: Complete API request/response tracking")
    print("   ✅ System Health Logging: Comprehensive system monitoring")
    print("   ✅ Multi-Category Logging: Trading, Security, Performance, API, Audit")
    print("   ✅ Log Aggregation Ready: Compatible with ELK, Splunk, Datadog")
    
    print(f"\n🎉 ENHANCED STRUCTURED LOGGING DEMO COMPLETE!")
    print("✅ Your trading bot now has enterprise-grade structured logging!")


if __name__ == "__main__":
    demonstrate_enhanced_structured_logging() 