# 🚨 Robust Alerting System Guide

## Overview

The **Robust Alerting System** provides enterprise-grade error alerting and notification capabilities for your AI trading bot. It ensures operators are immediately aware of critical issues through multiple channels including email, SMS, Slack, PagerDuty, and custom webhooks.

## 🎯 Key Features

### ✅ **Multi-Channel Notifications**
- **Email**: HTML-formatted alerts with detailed information
- **Slack**: Rich message formatting with severity indicators
- **PagerDuty**: Integration for critical incident management
- **Webhooks**: Custom integrations with external systems
- **Console**: Real-time console notifications and logging

### ✅ **Intelligent Alert Management**
- **Severity-Based Routing**: Route alerts based on severity levels
- **Alert Deduplication**: Prevent spam with intelligent filtering
- **Rate Limiting**: Configurable limits to prevent alert floods
- **Escalation Rules**: Automatic escalation for unacknowledged alerts
- **Alert Lifecycle**: Complete tracking from creation to resolution

### ✅ **Advanced Features**
- **Custom Alert Rules**: Flexible condition-based routing
- **Retry Logic**: Exponential backoff for failed deliveries
- **Statistics Tracking**: Comprehensive metrics and reporting
- **Database Storage**: Persistent alert history and analytics
- **Recovery Notifications**: Automatic recovery detection and alerts

## 🚀 Quick Start

### Basic Implementation

```python
from robust_alerting_system import RobustAlertingSystem, AlertSeverity, AlertChannel

# Initialize alerting system
alerting = RobustAlertingSystem()

# Configure email notifications
alerting.configure_channel(AlertChannel.EMAIL, {
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',
    'to_emails': ['admin@tradingbot.com']
})

# Send critical alert
alert_id = alerting.send_alert(
    title="Trading Engine Failure",
    message="Primary trading engine has stopped responding",
    severity=AlertSeverity.CRITICAL,
    source="trading_engine"
)
```

### Enhanced Integration

```python
from enhanced_alerting_integration_demo import EnhancedMonitoringBot

# Initialize enhanced monitoring bot
bot = EnhancedMonitoringBot()

# Monitor trading operations with automatic alerting
result = bot.monitor_trading_operation("place_order", "BTCUSDT")

# Monitor security validation with alerting
security_result = bot.monitor_security_validation(data)
```

## 📊 Alert Severity Levels

### **CRITICAL** 🚨
- **Response Time**: Immediate (0-5 minutes)
- **Channels**: Email + Slack + PagerDuty + Console
- **Examples**: System crashes, trading engine failures, security breaches
- **Escalation**: Automatic after 15 minutes

### **HIGH** ⚠️
- **Response Time**: Urgent (5-15 minutes)
- **Channels**: Email + Slack + Console
- **Examples**: Security violations, API failures, data corruption
- **Escalation**: Automatic after 30 minutes

### **MEDIUM** ⚡
- **Response Time**: Important (15-60 minutes)
- **Channels**: Email + Console
- **Examples**: Performance issues, trading errors, validation failures
- **Escalation**: Manual only

### **LOW** ℹ️
- **Response Time**: Normal (1-4 hours)
- **Channels**: Console
- **Examples**: Minor warnings, configuration changes
- **Escalation**: None

### **INFO** 📊
- **Response Time**: Informational
- **Channels**: Console
- **Examples**: Service recoveries, status updates
- **Escalation**: None

## 🔧 Channel Configuration

### Email Configuration

```python
alerting.configure_channel(AlertChannel.EMAIL, {
    'enabled': True,
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'trading-bot@company.com',
    'password': 'your-app-password',
    'from_email': 'alerts@company.com',
    'to_emails': [
        'admin@company.com',
        'devops@company.com',
        'trading-team@company.com'
    ],
    'retry_attempts': 3,
    'retry_delay': 2.0,
    'timeout': 30
})
```

### Slack Configuration

```python
alerting.configure_channel(AlertChannel.SLACK, {
    'enabled': True,
    'webhook_url': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
    'channel': '#trading-alerts',
    'username': 'TradingBot-Monitor',
    'retry_attempts': 3,
    'retry_delay': 1.0,
    'timeout': 30
})
```

### PagerDuty Configuration

```python
alerting.configure_channel(AlertChannel.PAGERDUTY, {
    'enabled': True,
    'integration_key': 'your-pagerduty-integration-key',
    'retry_attempts': 5,
    'retry_delay': 2.0,
    'timeout': 30
})
```

### Webhook Configuration

```python
alerting.configure_channel(AlertChannel.WEBHOOK, {
    'enabled': True,
    'urls': [
        'https://your-monitoring-system.com/webhook',
        'https://backup-webhook.com/alerts'
    ],
    'headers': {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer your-token'
    },
    'auth': ['username', 'password'],  # Optional basic auth
    'retry_attempts': 3,
    'retry_delay': 1.0,
    'timeout': 30
})
```

## 📋 Custom Alert Rules

### Rule Configuration

```python
from robust_alerting_system import AlertRule, AlertSeverity, AlertChannel

# Critical system failure rule
critical_rule = AlertRule(
    name="critical_system_failure",
    condition="severity == 'critical' and source in ['trading_engine', 'database']",
    severity=AlertSeverity.CRITICAL,
    channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.PAGERDUTY],
    cooldown_minutes=5,
    max_alerts_per_hour=10,
    escalation_minutes=15,
    auto_resolve=False
)

alerting.add_alert_rule(critical_rule)
```

### Rule Conditions

```python
# Condition examples
conditions = [
    "severity == 'critical'",
    "source == 'security' and severity in ['critical', 'high']",
    "source == 'trading' and 'balance' in message.lower()",
    "source == 'performance' and severity == 'medium'",
    "'timeout' in title.lower() or 'connection' in title.lower()"
]
```

### Advanced Rules

```python
# Trading error rule with custom routing
trading_rule = AlertRule(
    name="trading_errors",
    condition="source == 'trading' and severity in ['high', 'medium']",
    severity=AlertSeverity.MEDIUM,
    channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
    cooldown_minutes=15,
    max_alerts_per_hour=8,
    escalation_minutes=60,
    custom_message="Trading operation failed - immediate attention required"
)

# Security violation rule with immediate escalation
security_rule = AlertRule(
    name="security_violations",
    condition="source == 'security'",
    severity=AlertSeverity.HIGH,
    channels=[AlertChannel.EMAIL, AlertChannel.PAGERDUTY],
    cooldown_minutes=0,  # No cooldown for security
    max_alerts_per_hour=20,
    escalation_minutes=10  # Fast escalation
)
```

## 🔄 Alert Lifecycle Management

### Sending Alerts

```python
# Basic alert
alert_id = alerting.send_alert(
    title="Order Placement Failed",
    message="Failed to place buy order for BTCUSDT",
    severity=AlertSeverity.MEDIUM,
    source="trading"
)

# Alert with metadata
alert_id = alerting.send_alert(
    title="API Rate Limit Exceeded",
    message="Exchange API rate limit exceeded",
    severity=AlertSeverity.HIGH,
    source="exchange_api",
    metadata={
        "exchange": "binance",
        "rate_limit": "1200/minute",
        "current_rate": "1250/minute",
        "retry_after": 60
    },
    channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
)
```

### Acknowledging Alerts

```python
# Acknowledge alert
success = alerting.acknowledge_alert(alert_id, "admin@company.com")

if success:
    print("Alert acknowledged successfully")
else:
    print("Failed to acknowledge alert")
```

### Resolving Alerts

```python
# Resolve alert
success = alerting.resolve_alert(alert_id)

if success:
    print("Alert resolved successfully")
else:
    print("Failed to resolve alert")
```

### Querying Alerts

```python
# Get active alerts
active_alerts = alerting.get_active_alerts()
for alert in active_alerts:
    print(f"{alert.severity.value}: {alert.title}")

# Get alert statistics
stats = alerting.get_alert_statistics()
print(f"Total alerts: {stats['total_alerts']}")
print(f"Success rate: {(stats['alerts_sent'] / stats['total_alerts'] * 100):.1f}%")
```

## 📈 Monitoring and Analytics

### Alert Statistics

```python
# Get comprehensive statistics
stats = alerting.get_alert_statistics()

print(f"Alert Statistics:")
print(f"  Total Alerts: {stats['total_alerts']}")
print(f"  Alerts Sent: {stats['alerts_sent']}")
print(f"  Alerts Failed: {stats['alerts_failed']}")
print(f"  Alerts Suppressed: {stats['alerts_suppressed']}")
print(f"  Alerts Acknowledged: {stats['alerts_acknowledged']}")
print(f"  Alerts Resolved: {stats['alerts_resolved']}")
print(f"  Active Alerts: {stats['active_alerts']}")
```

### System Health

```python
# Get system health
health = alerting.get_system_health()

print(f"System Health:")
print(f"  Status: {health['status']}")
print(f"  Active Alerts: {health['active_alerts']}")
print(f"  Configured Channels: {health['configured_channels']}")
print(f"  Enabled Channels: {health['enabled_channels']}")
print(f"  Alert Rules: {health['alert_rules']}")
```

### Database Queries

```python
# Custom database queries for analytics
import sqlite3

with sqlite3.connect("alerts.db") as conn:
    # Get alerts by severity
    cursor = conn.execute("""
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        WHERE timestamp > datetime('now', '-24 hours')
        GROUP BY severity
    """)
    
    for row in cursor:
        print(f"{row[0]}: {row[1]} alerts")
    
    # Get top alert sources
    cursor = conn.execute("""
        SELECT source, COUNT(*) as count 
        FROM alerts 
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY source 
        ORDER BY count DESC 
        LIMIT 10
    """)
    
    for row in cursor:
        print(f"{row[0]}: {row[1]} alerts")
```

## 🔗 Integration Examples

### Integration with Exception Handling

```python
from specific_exception_handling_system import SpecificExceptionHandler

class AlertingExceptionHandler(SpecificExceptionHandler):
    def __init__(self, alerting_system):
        super().__init__()
        self.alerting = alerting_system
    
    def handle_exception(self, exception, context):
        # Handle exception with base handler
        result = super().handle_exception(exception, context)
        
        # Send alert based on exception category
        severity_map = {
            'validation': AlertSeverity.MEDIUM,
            'network': AlertSeverity.HIGH,
            'security': AlertSeverity.CRITICAL,
            'database': AlertSeverity.HIGH
        }
        
        severity = severity_map.get(result['category'], AlertSeverity.MEDIUM)
        
        self.alerting.send_alert(
            title=f"Exception in {context}",
            message=result['message'],
            severity=severity,
            source="exception_handler",
            metadata={
                "exception_type": result['error_type'],
                "category": result['category'],
                "context": context,
                "retry_recommended": result.get('retry_recommended', False)
            }
        )
        
        return result
```

### Integration with Graceful Degradation

```python
from graceful_degradation_system import GracefulDegradationSystem

class AlertingDegradationSystem(GracefulDegradationSystem):
    def __init__(self, alerting_system):
        super().__init__()
        self.alerting = alerting_system
    
    def _update_degradation_level(self):
        previous_level = self.degradation_level
        super()._update_degradation_level()
        
        # Alert on degradation level changes
        if previous_level != self.degradation_level:
            severity_map = {
                'MINIMAL': AlertSeverity.LOW,
                'MODERATE': AlertSeverity.MEDIUM,
                'SEVERE': AlertSeverity.HIGH,
                'CRITICAL': AlertSeverity.CRITICAL
            }
            
            severity = severity_map.get(self.degradation_level.name, AlertSeverity.INFO)
            
            self.alerting.send_alert(
                title=f"System Degradation: {self.degradation_level.name}",
                message=f"System degradation level changed from {previous_level.name} to {self.degradation_level.name}",
                severity=severity,
                source="system_health",
                metadata={
                    "previous_level": previous_level.name,
                    "current_level": self.degradation_level.name,
                    "health_percentage": self._calculate_health_percentage()
                }
            )
```

### Integration with Security Validation

```python
from secure_api_validator import SecureAPIValidator

class AlertingSecurityValidator(SecureAPIValidator):
    def __init__(self, alerting_system):
        super().__init__()
        self.alerting = alerting_system
    
    def validate_exchange_response(self, data):
        result = super().validate_exchange_response(data)
        
        # Alert on security validation failures
        if not result['success']:
            self.alerting.send_alert(
                title="Security Validation Failed",
                message=f"Security validation failed: {result['message']}",
                severity=AlertSeverity.HIGH,
                source="security",
                metadata={
                    "validation_type": "exchange_response",
                    "violation_details": result.get('details', {}),
                    "data_keys": list(data.keys()) if isinstance(data, dict) else "non-dict"
                }
            )
        
        return result
```

## 🛠️ Advanced Configuration

### Production Configuration

```python
# Production alerting configuration
production_config = {
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.company.com',
        'smtp_port': 587,
        'username': 'alerts@company.com',
        'password': 'secure-password',
        'to_emails': [
            'oncall@company.com',
            'devops@company.com',
            'trading-team@company.com'
        ],
        'retry_attempts': 5,
        'retry_delay': 2.0,
        'timeout': 30
    },
    'slack': {
        'enabled': True,
        'webhook_url': 'https://hooks.slack.com/services/PROD/WEBHOOK',
        'channel': '#critical-alerts',
        'username': 'TradingBot-Production',
        'retry_attempts': 3,
        'retry_delay': 1.0
    },
    'pagerduty': {
        'enabled': True,
        'integration_key': 'production-pagerduty-key',
        'retry_attempts': 5,
        'retry_delay': 3.0
    },
    'webhook': {
        'enabled': True,
        'urls': [
            'https://monitoring.company.com/webhook',
            'https://datadog.company.com/webhook'
        ],
        'headers': {
            'Authorization': 'Bearer prod-token'
        }
    }
}

# Apply production configuration
for channel, config in production_config.items():
    alerting.configure_channel(AlertChannel[channel.upper()], config)
```

### Development Configuration

```python
# Development alerting configuration
dev_config = {
    'console': {'enabled': True},
    'slack': {
        'enabled': True,
        'webhook_url': 'https://hooks.slack.com/services/DEV/WEBHOOK',
        'channel': '#dev-alerts',
        'username': 'TradingBot-Dev'
    },
    'email': {
        'enabled': False  # Disabled in development
    }
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Email Alerts Not Sending**
   ```python
   # Check SMTP configuration
   try:
       import smtplib
       server = smtplib.SMTP('smtp.gmail.com', 587)
       server.starttls()
       server.login('username', 'password')
       print("SMTP connection successful")
   except Exception as e:
       print(f"SMTP error: {e}")
   ```

2. **Slack Webhook Failures**
   ```python
   # Test Slack webhook
   import requests
   
   response = requests.post(webhook_url, json={
       "text": "Test message from trading bot"
   })
   print(f"Slack response: {response.status_code}")
   ```

3. **Alert Suppression Issues**
   ```python
   # Check deduplication settings
   for rule_name, rule in alerting.alert_rules.items():
       print(f"{rule_name}: cooldown={rule.cooldown_minutes}min, "
             f"max_per_hour={rule.max_alerts_per_hour}")
   ```

### Debug Commands

```python
# Debug alert system
print("Alert System Debug Info:")
print(f"Active alerts: {len(alerting.get_active_alerts())}")
print(f"Configured channels: {list(alerting.alert_configs.keys())}")
print(f"Alert rules: {list(alerting.alert_rules.keys())}")

# Check database
import sqlite3
with sqlite3.connect("alerts.db") as conn:
    cursor = conn.execute("SELECT COUNT(*) FROM alerts")
    count = cursor.fetchone()[0]
    print(f"Total alerts in database: {count}")
```

## 📊 Performance Optimization

### Alert Batching

```python
# Batch similar alerts to reduce noise
class BatchingAlertingSystem(RobustAlertingSystem):
    def __init__(self):
        super().__init__()
        self.alert_batch = defaultdict(list)
        self.batch_timer = None
    
    def batch_send_alert(self, title, message, severity, source, batch_key=None):
        batch_key = batch_key or f"{source}:{severity.value}"
        
        self.alert_batch[batch_key].append({
            'title': title,
            'message': message,
            'severity': severity,
            'source': source,
            'timestamp': datetime.now()
        })
        
        # Send batch after 5 minutes or 10 alerts
        if len(self.alert_batch[batch_key]) >= 10:
            self._send_batched_alerts(batch_key)
        elif not self.batch_timer:
            self.batch_timer = threading.Timer(300, self._send_all_batched_alerts)
            self.batch_timer.start()
```

### Memory Management

```python
# Cleanup old alerts to manage memory
def cleanup_old_alerts(self, days_to_keep=30):
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    with sqlite3.connect(self.db_path) as conn:
        conn.execute(
            "DELETE FROM alerts WHERE timestamp < ?",
            (cutoff_date.isoformat(),)
        )
    
    # Clean in-memory structures
    old_alert_ids = [
        alert_id for alert_id, alert in self.active_alerts.items()
        if alert.timestamp < cutoff_date
    ]
    
    for alert_id in old_alert_ids:
        del self.active_alerts[alert_id]
```

## 🎯 Best Practices

### 1. Alert Severity Guidelines

```python
# ✅ Good: Appropriate severity levels
AlertSeverity.CRITICAL  # System down, trading stopped
AlertSeverity.HIGH      # Security breach, API failures
AlertSeverity.MEDIUM    # Performance issues, trading errors
AlertSeverity.LOW       # Warnings, minor issues
AlertSeverity.INFO      # Status updates, recoveries

# ❌ Bad: Everything as critical
AlertSeverity.CRITICAL  # Minor validation error
```

### 2. Alert Message Quality

```python
# ✅ Good: Clear, actionable messages
alerting.send_alert(
    title="Trading Engine Failure - BTCUSDT",
    message="Primary trading engine stopped responding. Last heartbeat: 10:30 AM. Auto-failover initiated to backup engine.",
    severity=AlertSeverity.CRITICAL,
    source="trading_engine",
    metadata={
        "affected_pairs": ["BTCUSDT", "ETHUSDT"],
        "last_heartbeat": "2024-01-15T10:30:00Z",
        "failover_status": "in_progress"
    }
)

# ❌ Bad: Vague messages
alerting.send_alert(
    title="Error",
    message="Something went wrong",
    severity=AlertSeverity.HIGH,
    source="system"
)
```

### 3. Channel Configuration

```python
# ✅ Good: Severity-based routing
critical_channels = [AlertChannel.EMAIL, AlertChannel.PAGERDUTY, AlertChannel.SLACK]
medium_channels = [AlertChannel.EMAIL, AlertChannel.SLACK]
low_channels = [AlertChannel.CONSOLE]

# ❌ Bad: All alerts to all channels
all_channels = [AlertChannel.EMAIL, AlertChannel.PAGERDUTY, AlertChannel.SLACK]
```

## 🚀 Implementation Checklist

### ✅ **Basic Setup**
- [ ] Initialize RobustAlertingSystem
- [ ] Configure primary notification channels
- [ ] Set up default alert rules
- [ ] Test alert delivery

### ✅ **Channel Configuration**
- [ ] Email SMTP configuration
- [ ] Slack webhook setup
- [ ] PagerDuty integration key
- [ ] Custom webhook endpoints

### ✅ **Alert Rules**
- [ ] Critical system failure rules
- [ ] Security violation rules
- [ ] Performance degradation rules
- [ ] Recovery notification rules

### ✅ **Integration**
- [ ] Exception handling integration
- [ ] Graceful degradation integration
- [ ] Security validation integration
- [ ] Performance monitoring integration

### ✅ **Testing & Monitoring**
- [ ] Alert delivery testing
- [ ] Escalation procedure testing
- [ ] Performance impact assessment
- [ ] Alert analytics dashboard

## 🚀 Next Steps

1. **Implement Basic Alerting**
   ```bash
   python3 robust_alerting_system.py
   ```

2. **Test Enhanced Integration**
   ```bash
   python3 enhanced_alerting_integration_demo.py
   ```

3. **Configure Production Channels**
   - Set up email SMTP credentials
   - Configure Slack webhook URLs
   - Set up PagerDuty integration keys
   - Configure custom webhook endpoints

4. **Monitor and Optimize**
   - Review alert statistics regularly
   - Tune alert rules and thresholds
   - Optimize channel configurations
   - Implement alert analytics dashboard

Your AI trading bot now has enterprise-grade alerting and monitoring! 🚨 