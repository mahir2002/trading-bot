# 🔐 API Security Configuration Guide
## Principle of Least Privilege for Trading Bots

### 🚨 **CRITICAL**: Why This Matters

**Real-World Risk Examples:**
- **$1M+ Losses**: Bots with withdrawal permissions compromised
- **Liquidation Events**: Unauthorized margin/futures trading
- **Fund Draining**: Universal transfer permissions exploited
- **Regulatory Issues**: Unauthorized trading activities

---

## 🔍 **Permission Risk Assessment**

### **NEVER Grant These Permissions**
```yaml
PROHIBITED_PERMISSIONS:
  WITHDRAW: 
    risk: "TOTAL_ACCOUNT_LOSS"
    description: "Can withdraw all funds to external addresses"
    required_for_trading: false
    
  SUB_ACCOUNT_TRANSFER:
    risk: "FUNDS_MOVEMENT"
    description: "Can move funds between sub-accounts"
    required_for_trading: false
    
  UNIVERSAL_TRANSFER:
    risk: "EXTERNAL_TRANSFERS"
    description: "Can transfer to any external account"
    required_for_trading: false
    
  MARGIN_TRADING:
    risk: "LEVERAGE_LIQUIDATION"
    description: "Can trade with borrowed funds (2-10x leverage)"
    required_for_trading: false  # Unless specifically margin bot
    
  FUTURES_TRADING:
    risk: "HIGH_LEVERAGE_EXPOSURE"
    description: "Can trade futures (up to 125x leverage)"
    required_for_trading: false  # Unless specifically futures bot
```

### **Required Minimum Permissions**
```yaml
REQUIRED_PERMISSIONS:
  SPOT_TRADING:
    risk: "TRADING_CAPITAL_ONLY"
    description: "Buy/sell spot assets with existing balance"
    justification: "Core trading functionality"
    
  USER_DATA_STREAM:
    risk: "READ_ONLY"
    description: "Read account balance and order status"
    justification: "Monitor positions and portfolio"
    
  MARKET_DATA:
    risk: "NONE"
    description: "Read public market data"
    justification: "Price data for trading decisions"
```

---

## 🏗️ **Exchange-Specific Configuration**

### **Binance API Key Setup**

#### Step 1: Create API Key
1. Log in to Binance → Account → API Management
2. Click "Create API" → "System generated"
3. **Name**: `TradingBot-Production-YYYY-MM-DD`
4. **IMPORTANT**: Note the API Key and Secret immediately

#### Step 2: Configure Minimal Permissions
```yaml
# ✅ ENABLE THESE ONLY:
API_Restrictions:
  - Enable Reading: ✅ YES
  - Enable Spot & Margin Trading: ✅ YES (Spot only)
  - Enable Withdrawals: ❌ NO
  - Enable Internal Transfer: ❌ NO
  - Permits Universal Transfer: ❌ NO
  - Enable Vanilla Options: ❌ NO
  - Enable Margin: ❌ NO (unless margin bot)
  - Enable Futures: ❌ NO (unless futures bot)
```

#### Step 3: IP Restrictions (CRITICAL)
```yaml
IP_Access_Restrictions:
  status: ✅ ENABLED
  allowed_ips:
    - "YOUR_SERVER_IP"        # Your VPS/server IP
    - "YOUR_BACKUP_SERVER_IP" # Backup server only
  # Never allow: 0.0.0.0/0 or unrestricted access
```

#### Step 4: Additional Security Settings
```yaml
Security_Settings:
  daily_withdrawal_limit: 0  # Disable withdrawals
  api_key_expiry: 30_days   # Rotate monthly
  spot_trading_enabled: true
  margin_trading_enabled: false
  futures_trading_enabled: false
  
Rate_Limits:
  orders_per_second: 10
  orders_per_day: 200000
  requests_per_minute: 1200
```

### **Coinbase Pro API Configuration**
```yaml
Permissions:
  - view: ✅ YES        # Read account data
  - trade: ✅ YES       # Place/cancel orders
  - transfer: ❌ NO     # Move funds
  - withdraw: ❌ NO     # Withdraw funds
  
Restrictions:
  - Enable portfolio access: ✅ YES
  - Enable trading: ✅ YES  
  - Enable transfers: ❌ NO
  - Enable withdrawals: ❌ NO
```

### **Kraken API Configuration**
```yaml
Permissions:
  - Query Funds: ✅ YES
  - Query Open Orders: ✅ YES
  - Query Closed Orders: ✅ YES
  - Query Trades History: ✅ YES
  - Create & Modify Orders: ✅ YES
  - Cancel Orders: ✅ YES
  - Transfer Funds: ❌ NO
  - Withdraw Funds: ❌ NO
  - Create Staking Transactions: ❌ NO
```

---

## 🛡️ **Security Validation Script**

```python
#!/usr/bin/env python3
"""
API Security Validation Script
Run this before deploying your trading bot
"""

import asyncio
import aiohttp
from scalable_data_optimization_system import ScalableDataOptimizer

async def validate_api_security():
    """Comprehensive API security validation"""
    
    print("🔍 Starting API Security Validation...")
    
    # Initialize optimizer with security validation
    optimizer = ScalableDataOptimizer(environment="production")
    
    try:
        # Initialize with security checks
        await optimizer.initialize()
        
        # Get detailed security report
        security_report = await optimizer.secret_manager.validate_security_setup(
            optimizer.api_session
        )
        
        # Display results
        print(f"\n📊 Security Assessment Results:")
        print(f"Environment: {security_report['environment']}")
        print(f"Security Score: {security_report['security_score']}/100")
        print(f"Overall Status: {security_report['overall_status']}")
        
        # Critical issues
        critical_issues = security_report['validation_results']['api_permissions'].get('critical_issues', [])
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}):")
            for issue in critical_issues:
                print(f"  • {issue['permission']}: {issue['description']}")
                print(f"    Action Required: {issue['recommendation']}")
        
        # Warnings
        warnings = security_report['validation_results']['api_permissions'].get('warnings', [])
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning['permission']}: {warning['issue']}")
        
        # Recommendations
        recommendations = security_report['validation_results']['api_permissions'].get('recommendations', [])
        if recommendations:
            print(f"\n💡 SECURITY RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:10], 1):
                print(f"  {i}. {rec}")
        
        # Final verdict
        if security_report['security_score'] >= 90:
            print(f"\n✅ SECURITY STATUS: EXCELLENT - Ready for production")
        elif security_report['security_score'] >= 75:
            print(f"\n✅ SECURITY STATUS: GOOD - Address warnings before production")
        elif security_report['security_score'] >= 50:
            print(f"\n⚠️  SECURITY STATUS: ACCEPTABLE - Address issues before production")
        else:
            print(f"\n🚨 SECURITY STATUS: UNSAFE - DO NOT DEPLOY TO PRODUCTION")
            
    except Exception as e:
        print(f"❌ Security validation failed: {e}")
        return False
    
    finally:
        await optimizer.cleanup()
    
    return security_report['security_score'] >= 75

if __name__ == "__main__":
    success = asyncio.run(validate_api_security())
    exit(0 if success else 1)
```

---

## 📋 **Pre-Production Security Checklist**

### **API Key Configuration**
- [ ] Created API key with descriptive name and date
- [ ] Enabled only required permissions (Spot Trading, Market Data, User Data)
- [ ] **DISABLED** withdrawal permissions
- [ ] **DISABLED** transfer permissions  
- [ ] **DISABLED** margin trading (unless specifically required)
- [ ] **DISABLED** futures trading (unless specifically required)
- [ ] Enabled IP restrictions to server IPs only
- [ ] Set reasonable daily trading limits
- [ ] Documented API key expiry date for rotation

### **Account Security**
- [ ] Enabled 2FA on exchange account
- [ ] Used unique, strong password
- [ ] Enabled email notifications for API key usage
- [ ] Reviewed and documented all API key permissions
- [ ] Set up monitoring for unusual API activity
- [ ] Created backup API keys with same restrictions

### **Infrastructure Security**
- [ ] Server IP whitelisted on exchange
- [ ] Firewall configured to allow only necessary ports
- [ ] API keys stored in secure secret management system
- [ ] SSL/TLS enabled for all API communications
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery plan documented

---

## 🔄 **API Key Rotation Schedule**

### **Monthly Rotation (Recommended)**
```python
# Automated API key rotation script
import datetime
from datetime import timedelta

def should_rotate_api_key(created_date: datetime.datetime) -> bool:
    """Check if API key should be rotated"""
    return datetime.datetime.now() - created_date > timedelta(days=30)

def rotate_api_key():
    """Automated API key rotation process"""
    # 1. Create new API key with same permissions
    # 2. Update secret management system
    # 3. Test new API key
    # 4. Switch production to new key
    # 5. Disable old API key
    # 6. Monitor for 24 hours
    # 7. Delete old API key
    pass
```

### **Emergency Rotation Triggers**
- Suspicious API activity detected
- Security breach at exchange
- Server compromise suspected
- Unusual trading patterns
- Failed authentication attempts

---

## 🚨 **Security Monitoring**

### **Real-Time Alerts**
```python
SECURITY_ALERTS = {
    'failed_api_calls': {
        'threshold': 5,
        'timeframe': '5_minutes',
        'action': 'disable_api_key'
    },
    'unusual_trading_volume': {
        'threshold': 10000,  # USD
        'timeframe': '1_hour',
        'action': 'pause_trading'
    },
    'rapid_order_changes': {
        'threshold': 50,
        'timeframe': '1_minute', 
        'action': 'pause_trading'
    },
    'unauthorized_ip_access': {
        'threshold': 1,
        'timeframe': 'immediate',
        'action': 'disable_api_key'
    }
}
```

### **Daily Security Review**
```bash
#!/bin/bash
# Daily security check script

echo "🔍 Daily Security Review - $(date)"

# Check API key permissions
python3 validate_api_security.py

# Review trading activity
python3 review_trading_activity.py

# Check for security alerts
python3 check_security_alerts.py

# Verify IP restrictions
python3 verify_ip_restrictions.py

echo "✅ Security review completed"
```

---

## 📞 **Emergency Response Plan**

### **If API Key Compromised**
1. **IMMEDIATE**: Disable API key on exchange
2. **IMMEDIATE**: Stop all trading bots
3. **IMMEDIATE**: Check account for unauthorized activity
4. **IMMEDIATE**: Change exchange account password
5. **IMMEDIATE**: Enable additional 2FA if available
6. **Within 1 hour**: Create new API key with proper restrictions
7. **Within 1 hour**: Update secret management system
8. **Within 2 hours**: Resume trading with new key
9. **Within 24 hours**: Audit all trades and account changes
10. **Within 48 hours**: Document incident and improve security

### **Contact Information**
```yaml
Emergency_Contacts:
  exchange_support: "support@binance.com"
  security_team: "your-security-team@company.com"
  system_admin: "admin@company.com"
  
Emergency_Procedures:
  api_key_disable: "Account → API Management → Disable"
  trading_halt: "Kill switch in bot dashboard"
  account_freeze: "Contact exchange support immediately"
```

---

**🎯 Remember: The goal is to give your trading bot EXACTLY the permissions it needs to trade, and nothing more. Every additional permission is a potential attack vector that could lead to total account loss.** 