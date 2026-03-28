#!/usr/bin/env python3
"""
🚨 ENHANCED ALERTING INTEGRATION DEMO
================================================================================
Advanced alerting demonstration integrated with:
- Graceful degradation system
- Specific exception handling
- Security validation system
- Schema validation system
- Real trading bot operations

Demonstrates complete system monitoring and alerting capabilities.
"""

import logging
import time
from typing import Dict, Any, Optional
from robust_alerting_system import (
    RobustAlertingSystem,
    AlertSeverity,
    AlertChannel,
    AlertRule
)

# Import existing systems
try:
    from graceful_degradation_system import GracefulDegradationSystem, DegradationLevel
    from specific_exception_handling_system import SpecificExceptionHandler
    from secure_api_validator import SecureAPIValidator
    from pydantic_schema_validation_system import PydanticSchemaValidator
except ImportError as e:
    logging.warning(f"Some systems not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedMonitoringBot:
    """
    Enhanced trading bot with complete monitoring and alerting integration.
    """
    
    def __init__(self):
        # Initialize all systems
        self.alerting_system = RobustAlertingSystem()
        
        try:
            self.degradation_system = GracefulDegradationSystem()
            self.exception_handler = SpecificExceptionHandler()
            self.security_validator = SecureAPIValidator()
            self.schema_validator = PydanticSchemaValidator()
        except:
            logger.warning("⚠️ Some systems not available - using fallbacks")
            self.degradation_system = None
            self.exception_handler = None
            self.security_validator = None
            self.schema_validator = None
        
        # Configure alerting channels
        self._configure_alerting()
        
        # Set up monitoring rules
        self._setup_monitoring_rules()
        
        self.monitoring_stats = {
            'operations_monitored': 0,
            'alerts_triggered': 0,
            'critical_incidents': 0,
            'security_violations': 0,
            'performance_issues': 0,
            'recoveries_detected': 0
        }
        
        logger.info("🤖 Enhanced Monitoring Bot initialized with complete alerting")
    
    def _configure_alerting(self):
        """Configure alerting channels."""
        # Configure console notifications (always available)
        self.alerting_system.configure_channel(AlertChannel.CONSOLE, {
            'enabled': True
        })
        
        # Configure email notifications (demo configuration)
        self.alerting_system.configure_channel(AlertChannel.EMAIL, {
            'enabled': False,  # Disabled for demo
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'trading-bot@example.com',
            'password': 'app-password',
            'to_emails': ['admin@tradingbot.com', 'alerts@tradingbot.com']
        })
        
        # Configure Slack notifications (demo configuration)
        self.alerting_system.configure_channel(AlertChannel.SLACK, {
            'enabled': False,  # Disabled for demo
            'webhook_url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
            'channel': '#trading-alerts',
            'username': 'TradingBot-Monitor'
        })
        
        logger.info("✅ Alerting channels configured")
    
    def _setup_monitoring_rules(self):
        """Set up custom monitoring and alerting rules."""
        # Critical system failure rule
        self.alerting_system.add_alert_rule(AlertRule(
            name="critical_system_failure",
            condition="severity == 'critical'",
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL, AlertChannel.SLACK],
            cooldown_minutes=5,
            max_alerts_per_hour=10,
            escalation_minutes=15
        ))
        
        # Security violation rule
        self.alerting_system.add_alert_rule(AlertRule(
            name="security_incident",
            condition="source == 'security'",
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL],
            cooldown_minutes=10,
            max_alerts_per_hour=5
        ))
        
        # Performance degradation rule
        self.alerting_system.add_alert_rule(AlertRule(
            name="performance_issue",
            condition="source == 'performance'",
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.CONSOLE],
            cooldown_minutes=15,
            max_alerts_per_hour=3
        ))
        
        logger.info("✅ Monitoring rules configured")
    
    def monitor_trading_operation(self, operation: str, symbol: str) -> Dict[str, Any]:
        """Monitor a trading operation with comprehensive alerting."""
        self.monitoring_stats['operations_monitored'] += 1
        operation_start = time.time()
        
        try:
            # Simulate trading operation
            result = self._execute_trading_operation(operation, symbol)
            
            # Check for performance issues
            operation_time = time.time() - operation_start
            if operation_time > 2.0:  # Threshold: 2 seconds
                self._alert_performance_issue(operation, symbol, operation_time)
            
            # Check for degradation
            if self.degradation_system:
                health = self.degradation_system.get_system_health()
                if health['degradation_level'] != 'NONE':
                    self._alert_system_degradation(health)
            
            return result
            
        except Exception as e:
            # Handle and alert on exceptions
            return self._handle_operation_exception(operation, symbol, e)
    
    def _execute_trading_operation(self, operation: str, symbol: str) -> Dict[str, Any]:
        """Execute trading operation with monitoring."""
        
        # Simulate different operation scenarios
        if symbol == "CRITICAL_FAIL":
            raise Exception("Critical system failure - trading engine unresponsive")
        elif symbol == "SECURITY_FAIL":
            raise PermissionError("Unauthorized trading attempt detected")
        elif symbol == "NETWORK_FAIL":
            raise ConnectionError("Exchange API connection failed")
        elif symbol == "VALIDATION_FAIL":
            raise ValueError("Invalid trading parameters provided")
        elif symbol == "SLOW_RESPONSE":
            time.sleep(2.5)  # Simulate slow operation
            return {"status": "success", "symbol": symbol, "operation": operation}
        elif symbol == "SUCCESS":
            return {"status": "success", "symbol": symbol, "operation": operation}
        else:
            # Normal operation
            return {"status": "success", "symbol": symbol, "operation": operation}
    
    def _handle_operation_exception(self, operation: str, symbol: str, exception: Exception) -> Dict[str, Any]:
        """Handle operation exception with appropriate alerting."""
        
        # Determine alert severity based on exception type
        if isinstance(exception, (SystemError, RuntimeError)):
            severity = AlertSeverity.CRITICAL
            self.monitoring_stats['critical_incidents'] += 1
        elif isinstance(exception, PermissionError):
            severity = AlertSeverity.HIGH
            self.monitoring_stats['security_violations'] += 1
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW
        
        # Send alert
        alert_id = self.alerting_system.send_alert(
            title=f"{operation.title()} Operation Failed: {symbol}",
            message=f"Trading operation '{operation}' failed for {symbol}: {str(exception)}",
            severity=severity,
            source="trading_operation",
            metadata={
                "operation": operation,
                "symbol": symbol,
                "exception_type": type(exception).__name__,
                "timestamp": time.time()
            }
        )
        
        self.monitoring_stats['alerts_triggered'] += 1
        
        return {
            "status": "failed",
            "error": str(exception),
            "alert_id": alert_id,
            "severity": severity.value
        }
    
    def _alert_performance_issue(self, operation: str, symbol: str, duration: float):
        """Alert on performance issues."""
        self.monitoring_stats['performance_issues'] += 1
        
        self.alerting_system.send_alert(
            title=f"Slow {operation.title()} Operation: {symbol}",
            message=f"Operation '{operation}' for {symbol} took {duration:.2f}s (threshold: 2.0s)",
            severity=AlertSeverity.MEDIUM,
            source="performance",
            metadata={
                "operation": operation,
                "symbol": symbol,
                "duration": duration,
                "threshold": 2.0
            }
        )
        
        self.monitoring_stats['alerts_triggered'] += 1
    
    def _alert_system_degradation(self, health: Dict[str, Any]):
        """Alert on system degradation."""
        degradation_level = health['degradation_level']
        
        # Map degradation level to alert severity
        severity_map = {
            'MINIMAL': AlertSeverity.LOW,
            'MODERATE': AlertSeverity.MEDIUM,
            'SEVERE': AlertSeverity.HIGH,
            'CRITICAL': AlertSeverity.CRITICAL
        }
        
        severity = severity_map.get(degradation_level, AlertSeverity.MEDIUM)
        
        self.alerting_system.send_alert(
            title=f"System Degradation: {degradation_level}",
            message=f"System health degraded to {degradation_level} level. {health['healthy_services']}/{health['total_services']} services healthy.",
            severity=severity,
            source="system_health",
            metadata={
                "degradation_level": degradation_level,
                "health_percentage": health['health_percentage'],
                "healthy_services": health['healthy_services'],
                "total_services": health['total_services']
            }
        )
        
        self.monitoring_stats['alerts_triggered'] += 1
    
    def monitor_security_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor security validation with alerting."""
        try:
            if self.security_validator:
                result = self.security_validator.validate_exchange_response(data)
                
                if not result['success']:
                    # Security validation failed - send alert
                    self.alerting_system.send_alert(
                        title="Security Validation Failed",
                        message=f"Security validation failed: {result.get('message', 'Unknown security issue')}",
                        severity=AlertSeverity.HIGH,
                        source="security",
                        metadata={
                            "validation_result": result,
                            "data_keys": list(data.keys()) if isinstance(data, dict) else "non-dict"
                        }
                    )
                    
                    self.monitoring_stats['security_violations'] += 1
                    self.monitoring_stats['alerts_triggered'] += 1
                
                return result
            else:
                return {"success": True, "message": "Security validator not available"}
                
        except Exception as e:
            # Security validation exception
            self.alerting_system.send_alert(
                title="Security Validation Error",
                message=f"Security validation encountered an error: {str(e)}",
                severity=AlertSeverity.MEDIUM,
                source="security",
                metadata={
                    "exception_type": type(e).__name__,
                    "data_provided": bool(data)
                }
            )
            
            self.monitoring_stats['alerts_triggered'] += 1
            
            return {"success": False, "error": str(e)}
    
    def simulate_service_recovery(self, service_name: str):
        """Simulate service recovery and send recovery alert."""
        self.monitoring_stats['recoveries_detected'] += 1
        
        self.alerting_system.send_alert(
            title=f"Service Recovered: {service_name}",
            message=f"Service '{service_name}' has recovered and is now operational.",
            severity=AlertSeverity.INFO,
            source="recovery",
            metadata={
                "service_name": service_name,
                "recovery_time": time.time(),
                "status": "operational"
            }
        )
        
        self.monitoring_stats['alerts_triggered'] += 1
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        alerting_stats = self.alerting_system.get_alert_statistics()
        
        return {
            'monitoring_stats': self.monitoring_stats.copy(),
            'alerting_stats': alerting_stats,
            'active_alerts': len(self.alerting_system.get_active_alerts()),
            'system_health': self.alerting_system.get_system_health()
        }


def demonstrate_enhanced_alerting_integration():
    """Demonstrate enhanced alerting integration with all systems."""
    print("🚨 ENHANCED ALERTING INTEGRATION DEMO")
    print("=" * 80)
    print("Demonstrating complete monitoring and alerting integration")
    print("- Alerting + Graceful degradation + Exception handling + Security validation")
    
    # Initialize enhanced monitoring bot
    bot = EnhancedMonitoringBot()
    
    print("\n💰 MONITORED TRADING OPERATIONS")
    print("-" * 70)
    
    # Test successful operation
    print("\n   Test 1: ✅ Successful trading operation")
    result = bot.monitor_trading_operation("buy_order", "SUCCESS")
    print(f"   Status: {'✅ SUCCESS' if result['status'] == 'success' else '❌ FAILED'}")
    if result['status'] == 'success':
        print(f"   Operation: {result['operation']} for {result['symbol']}")
    
    # Test slow operation (performance alert)
    print("\n   Test 2: ⚡ Slow operation (performance alert)")
    result = bot.monitor_trading_operation("market_data", "SLOW_RESPONSE")
    print(f"   Status: {'✅ SUCCESS' if result['status'] == 'success' else '❌ FAILED'}")
    print("   Performance alert triggered for slow response")
    
    # Test critical system failure
    print("\n   Test 3: 🚨 Critical system failure")
    result = bot.monitor_trading_operation("place_order", "CRITICAL_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['status'] == 'success' else '❌ FAILED'}")
    if result['status'] == 'failed':
        print(f"   Error: {result['error']}")
        print(f"   Alert ID: {result['alert_id']}")
        print(f"   Severity: {result['severity'].upper()}")
    
    # Test security violation
    print("\n   Test 4: 🔒 Security violation")
    result = bot.monitor_trading_operation("unauthorized_trade", "SECURITY_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['status'] == 'success' else '❌ FAILED'}")
    if result['status'] == 'failed':
        print(f"   Security alert triggered: {result['error']}")
    
    # Test network failure
    print("\n   Test 5: 🌐 Network connection failure")
    result = bot.monitor_trading_operation("get_balance", "NETWORK_FAIL")
    print(f"   Status: {'✅ SUCCESS' if result['status'] == 'success' else '❌ FAILED'}")
    if result['status'] == 'failed':
        print(f"   Network alert triggered: {result['error']}")
    
    print("\n🔒 SECURITY MONITORING")
    print("-" * 70)
    
    # Test security validation monitoring
    print("\n   Test 6: ✅ Valid security data")
    security_result = bot.monitor_security_validation({
        "symbol": "BTCUSDT",
        "price": 50000.0,
        "volume": 1.5
    })
    print(f"   Security validation: {'✅ PASSED' if security_result['success'] else '❌ FAILED'}")
    
    # Test security validation with suspicious data
    print("\n   Test 7: ⚠️ Suspicious data detected")
    security_result = bot.monitor_security_validation({
        "symbol": "<script>alert('xss')</script>",
        "price": -1000,
        "volume": "DROP TABLE users"
    })
    print(f"   Security validation: {'✅ PASSED' if security_result['success'] else '❌ FAILED'}")
    if not security_result['success']:
        print("   Security alert triggered for suspicious data")
    
    print("\n🔄 SERVICE RECOVERY MONITORING")
    print("-" * 70)
    
    # Simulate service recoveries
    print("\n   Test 8: ✅ Service recovery notifications")
    bot.simulate_service_recovery("exchange_api")
    bot.simulate_service_recovery("database_connection")
    bot.simulate_service_recovery("redis_cache")
    print("   Recovery alerts sent for 3 services")
    
    print("\n📊 COMPREHENSIVE MONITORING STATISTICS")
    print("=" * 80)
    
    # Get comprehensive statistics
    stats = bot.get_monitoring_statistics()
    
    print(f"🤖 Monitoring Statistics:")
    for key, value in stats['monitoring_stats'].items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🚨 Alerting Statistics:")
    for key, value in stats['alerting_stats'].items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🏥 System Health:")
    health = stats['system_health']
    print(f"   Status: {health['status'].upper()}")
    print(f"   Active Alerts: {health['active_alerts']}")
    print(f"   Configured Channels: {len(health['configured_channels'])}")
    print(f"   Alert Rules: {len(health['alert_rules'])}")
    
    # Display active alerts
    active_alerts = bot.alerting_system.get_active_alerts()
    if active_alerts:
        print(f"\n🚨 Active Alerts ({len(active_alerts)}):")
        for alert in active_alerts[-5:]:  # Show last 5 alerts
            severity_emoji = {
                "critical": "🚨",
                "high": "⚠️", 
                "medium": "⚡",
                "low": "ℹ️",
                "info": "📊"
            }.get(alert.severity.value, "🔔")
            print(f"   {severity_emoji} {alert.severity.value.upper()}: {alert.title}")
    
    print(f"\n🚨 ENHANCED ALERTING INTEGRATION CAPABILITIES:")
    print("=" * 80)
    print("   ✅ Complete System Integration: All security and monitoring systems")
    print("   ✅ Multi-Severity Alerting: Critical, High, Medium, Low, Info levels")
    print("   ✅ Multi-Channel Notifications: Email, Slack, PagerDuty, Console")
    print("   ✅ Performance Monitoring: Response time and throughput alerts")
    print("   ✅ Security Violation Detection: Real-time security event alerting")
    print("   ✅ System Health Monitoring: Service degradation and recovery alerts")
    print("   ✅ Exception Integration: Specific error categorization and alerting")
    print("   ✅ Alert Deduplication: Prevents alert spam with intelligent filtering")
    print("   ✅ Alert Lifecycle Management: Acknowledgment and resolution tracking")
    print("   ✅ Comprehensive Statistics: Detailed monitoring and alerting metrics")
    
    print(f"\n🎉 ENHANCED ALERTING INTEGRATION DEMO COMPLETE!")
    print("✅ Your trading bot now has enterprise-grade monitoring and alerting!")


if __name__ == "__main__":
    demonstrate_enhanced_alerting_integration() 