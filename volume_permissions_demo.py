#!/usr/bin/env python3
"""
Volume Permissions Security System - Practical Demonstration
Real scanning and fixing of Docker volume permission issues
"""

import os
import asyncio
import json
import shutil
from datetime import datetime
from volume_permissions_security_system import (
    VolumePermissionsSecuritySystem,
    VolumePermission, VolumeType, SecurityLevel
)

async def main():
    """Demonstrate comprehensive volume permissions security."""
    print("🔒 Docker Volume Permissions Security - Live Demo")
    print("=" * 70)
    
    # Initialize the security system
    security_system = VolumePermissionsSecuritySystem()
    
    print(f"\n🎯 Creating realistic volume permission scenarios...")
    
    # Create realistic AI Trading Bot volume structure
    volume_scenarios = {
        "./demo_volumes/trading_data": {
            "files": [
                ("trading_history.db", 0o644, "Database with trading history"),
                ("positions.json", 0o666, "INSECURE: World-writable positions file"),
                ("market_data.csv", 0o755, "ISSUE: Executable data file"),
                ("cache.tmp", 0o777, "CRITICAL: World-writable cache")
            ],
            "type": VolumeType.DATA,
            "security": SecurityLevel.HIGH
        },
        "./demo_volumes/config": {
            "files": [
                ("app_config.yaml", 0o644, "Application configuration"),
                ("trading_params.json", 0o640, "Trading parameters"),
                ("exchange_settings.conf", 0o777, "CRITICAL: World-writable config"),
                ("logging.ini", 0o644, "Logging configuration")
            ],
            "type": VolumeType.CONFIG,
            "security": SecurityLevel.HIGH
        },
        "./demo_volumes/secrets": {
            "files": [
                ("api_keys.env", 0o777, "CRITICAL: World-readable API keys"),
                ("private_keys.pem", 0o644, "CRITICAL: World-readable private keys"),
                ("certificates.crt", 0o600, "Secure certificate storage"),
                ("oauth_tokens.json", 0o666, "CRITICAL: World-writable tokens")
            ],
            "type": VolumeType.SECRETS,
            "security": SecurityLevel.MAXIMUM
        },
        "./demo_volumes/logs": {
            "files": [
                ("trading.log", 0o644, "Trading activity logs"),
                ("error.log", 0o640, "Error logs"),
                ("audit.log", 0o777, "ISSUE: World-writable audit log"),
                ("debug.log", 0o755, "ISSUE: Executable log file")
            ],
            "type": VolumeType.LOGS,
            "security": SecurityLevel.HIGH
        }
    }
    
    # Create the volume scenarios
    for volume_path, scenario in volume_scenarios.items():
        os.makedirs(volume_path, exist_ok=True)
        
        for filename, mode, description in scenario["files"]:
            file_path = os.path.join(volume_path, filename)
            
            # Create realistic content based on file type
            content = generate_realistic_content(filename, description)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Set the permission (some are intentionally insecure)
            os.chmod(file_path, mode)
            
            print(f"   📄 Created {filename} (mode: {oct(mode)}) - {description}")
    
    print(f"\n🔍 Starting comprehensive volume security scans...")
    
    scan_summary = {
        "total_volumes": len(volume_scenarios),
        "total_violations": 0,
        "critical_violations": 0,
        "auto_fixable": 0,
        "overall_score": 0
    }
    
    # Scan each volume
    for volume_path, scenario in volume_scenarios.items():
        print(f"\n📂 Scanning: {volume_path}")
        print("-" * 50)
        
        try:
            # Create custom policy for this volume
            policy = VolumePermission(
                path=volume_path,
                volume_type=scenario["type"],
                security_level=scenario["security"],
                owner_uid=1001,  # Non-root trading bot user
                owner_gid=1001,
                directory_mode=0o750 if scenario["security"] == SecurityLevel.HIGH else 0o700,
                file_mode=0o640 if scenario["security"] == SecurityLevel.HIGH else 0o600
            )
            
            # Perform security scan
            scan_result = await security_system.scan_volume_permissions(volume_path, policy)
            
            # Update summary statistics
            scan_summary["total_violations"] += len(scan_result.violations)
            scan_summary["critical_violations"] += sum(1 for v in scan_result.violations if v.severity == "CRITICAL")
            scan_summary["auto_fixable"] += sum(1 for v in scan_result.violations if v.auto_fixable)
            scan_summary["overall_score"] += scan_result.security_score
            
            # Display scan results
            print(f"   🎯 Security Score: {scan_result.security_score:.1f}/100")
            print(f"   ⚠️  Risk Level: {scan_result.risk_level}")
            print(f"   🚨 Violations Found: {len(scan_result.violations)}")
            
            # Show critical violations
            critical_violations = [v for v in scan_result.violations if v.severity == "CRITICAL"]
            if critical_violations:
                print(f"   ⛔ CRITICAL ISSUES:")
                for violation in critical_violations[:3]:  # Show top 3
                    print(f"      • {violation.path}: {violation.description}")
                    print(f"        Fix: {violation.recommendation}")
            
            # Generate security reports
            reports = security_system.save_security_reports(volume_path)
            print(f"   📊 Reports saved: {os.path.basename(reports['html'])}")
            
            # Demonstrate permission fixing (dry run first)
            if scan_result.violations:
                print(f"\n   🔧 Simulating permission fixes...")
                fix_result = await security_system.fix_volume_permissions(volume_path, dry_run=True)
                
                print(f"      💡 Available fixes: {len(fix_result['fixes_applied'])}")
                if fix_result['fixes_applied']:
                    print(f"      🛠️  Sample fixes:")
                    for fix in fix_result['fixes_applied'][:3]:
                        print(f"         → {fix['command']}")
                
                # Prompt for actual fixes
                print(f"\n   ❓ Apply fixes to {volume_path}? (y/N): ", end="")
                # In demo mode, we'll apply fixes to show improvement
                apply_fixes = True  # Auto-apply for demo
                
                if apply_fixes:
                    print("y")
                    print(f"   🔧 Applying permission fixes...")
                    
                    actual_fix_result = await security_system.fix_volume_permissions(volume_path, dry_run=False)
                    
                    print(f"      ✅ Fixes applied: {len(actual_fix_result['fixes_applied'])}")
                    print(f"      ❌ Failed fixes: {len(actual_fix_result['fixes_failed'])}")
                    
                    if actual_fix_result.get("verification"):
                        verification = actual_fix_result["verification"]
                        print(f"      📈 Security improvement: {verification['security_score_after'] - verification['security_score_before']:.1f} points")
                        print(f"      🎯 Violations reduced: {verification['improvement']}")
                else:
                    print("N")
                    print(f"   ⏭️  Skipping fixes for {volume_path}")
            
        except Exception as e:
            print(f"   ❌ Error scanning {volume_path}: {e}")
    
    # Calculate overall statistics
    scan_summary["overall_score"] = scan_summary["overall_score"] / len(volume_scenarios)
    
    print(f"\n📊 OVERALL SECURITY SUMMARY")
    print("=" * 70)
    print(f"Volumes Scanned: {scan_summary['total_volumes']}")
    print(f"Total Violations: {scan_summary['total_violations']}")
    print(f"Critical Issues: {scan_summary['critical_violations']}")
    print(f"Auto-fixable: {scan_summary['auto_fixable']}")
    print(f"Average Security Score: {scan_summary['overall_score']:.1f}/100")
    
    # Risk assessment
    if scan_summary['critical_violations'] > 0:
        risk_level = "🚨 CRITICAL"
        recommendation = "Immediate action required - Fix critical violations now!"
    elif scan_summary['total_violations'] > 10:
        risk_level = "⚠️ HIGH"
        recommendation = "High priority - Address violations within 24 hours"
    elif scan_summary['total_violations'] > 0:
        risk_level = "💛 MEDIUM"
        recommendation = "Monitor and fix violations during next maintenance window"
    else:
        risk_level = "✅ LOW"
        recommendation = "Excellent security posture - maintain current practices"
    
    print(f"Overall Risk Level: {risk_level}")
    print(f"Recommendation: {recommendation}")
    
    # Generate secure Docker Compose configuration
    print(f"\n🐳 Generating secure Docker Compose configuration...")
    compose_config = security_system.generate_docker_compose_volumes()
    
    # Save secure compose configuration
    with open("volume_security/docker-compose.secure-volumes.yml", 'w') as f:
        f.write("""# Secure Docker Compose Configuration for AI Trading Bot
# Generated by Volume Permissions Security System

version: '3.8'

services:
  ai-trading-bot:
    image: ai-trading-bot:secure
    user: "1001:1001"  # Non-root user
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    volumes:
""")
        for mount in compose_config["service_volumes"]:
            f.write(f"      - {mount}\n")
        
        f.write(f"\nvolumes:\n")
        for name, config in compose_config["volumes"].items():
            f.write(f"  {name}:\n")
            f.write(f"    driver: {config['driver']}\n")
            if "driver_opts" in config:
                f.write(f"    driver_opts:\n")
                for opt, value in config["driver_opts"].items():
                    f.write(f"      {opt}: \"{value}\"\n")
    
    print(f"✅ Secure Docker Compose saved: volume_security/docker-compose.secure-volumes.yml")
    
    # Generate best practices guide
    print(f"\n📚 Generating Volume Security Best Practices...")
    
    best_practices = generate_best_practices_guide(scan_summary, volume_scenarios)
    
    with open("volume_security/VOLUME_SECURITY_BEST_PRACTICES.md", 'w') as f:
        f.write(best_practices)
    
    print(f"✅ Best practices guide saved: volume_security/VOLUME_SECURITY_BEST_PRACTICES.md")
    
    print(f"\n🎉 Volume Permissions Security Demo Completed!")
    print(f"📄 Check volume_security/reports/ for detailed security reports")
    print(f"🔧 Review and apply recommended fixes for production deployment")

def generate_realistic_content(filename: str, description: str) -> str:
    """Generate realistic content for demo files."""
    if "api_keys" in filename:
        return """# AI Trading Bot API Keys - KEEP SECURE!
BINANCE_API_KEY=ak_test_1234567890abcdef
BINANCE_SECRET_KEY=sk_test_abcdef1234567890
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
COINGECKO_API_KEY=CG-1234567890abcdef
"""
    
    elif "private_keys" in filename:
        return """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7...
[DEMO PRIVATE KEY - NOT FOR PRODUCTION USE]
-----END PRIVATE KEY-----
"""
    
    elif "oauth_tokens" in filename:
        return """{
    "access_token": "ya29.demo_token_1234567890",
    "refresh_token": "1//demo_refresh_token_abcdef",
    "expires_in": 3600,
    "token_type": "Bearer"
}
"""
    
    elif "trading_history" in filename:
        return """CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO trades (symbol, side, quantity, price) VALUES
('BTCUSDT', 'BUY', 0.001, 45000.0),
('ETHUSDT', 'SELL', 0.1, 3200.0);
"""
    
    elif "positions" in filename:
        return """{
    "BTCUSDT": {
        "quantity": 0.001,
        "entry_price": 45000.0,
        "current_price": 46000.0,
        "pnl": 1.0,
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
"""
    
    elif "config" in filename or "settings" in filename:
        return """# AI Trading Bot Configuration
DEBUG: false
LOG_LEVEL: INFO
MAX_POSITION_SIZE: 1000
RISK_PERCENTAGE: 2.0
STOP_LOSS_PERCENTAGE: 5.0
TAKE_PROFIT_PERCENTAGE: 10.0
"""
    
    elif "log" in filename:
        return f"""2024-01-15 10:30:00 - INFO - AI Trading Bot started
2024-01-15 10:31:00 - INFO - Connected to Binance API
2024-01-15 10:32:00 - INFO - Market data stream established
2024-01-15 10:33:00 - WARNING - High volatility detected for BTCUSDT
2024-01-15 10:34:00 - INFO - Placed BUY order for 0.001 BTC at $45000
"""
    
    else:
        return f"Demo content for {filename}\nGenerated: {datetime.now()}\nDescription: {description}"

def generate_best_practices_guide(scan_summary: dict, volume_scenarios: dict) -> str:
    """Generate comprehensive volume security best practices guide."""
    return f"""# Docker Volume Security Best Practices
## AI Trading Bot - Security Implementation Guide

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔍 Security Assessment Summary

- **Volumes Analyzed**: {scan_summary['total_volumes']}
- **Total Violations Found**: {scan_summary['total_violations']}
- **Critical Security Issues**: {scan_summary['critical_violations']}
- **Auto-fixable Issues**: {scan_summary['auto_fixable']}
- **Average Security Score**: {scan_summary['overall_score']:.1f}/100

## 🔒 Essential Volume Security Principles

### 1. **Principle of Least Privilege**
```yaml
# ✅ GOOD: Specific user/group with minimal permissions
volumes:
  app_data:
    driver: local
    driver_opts:
      type: none
      o: bind,uid=1001,gid=1001
      device: ./volumes/data

# ❌ BAD: Root ownership or world-writable
volumes:
  app_data:
    driver: local  # Uses root by default
```

### 2. **Volume Type Security Levels**

| Volume Type | Recommended Permissions | User Access | Group Access | World Access |
|-------------|------------------------|-----------  |-------------|-------------|
| **Secrets** | `700/600` | Read/Write | None | None |
| **Config**  | `750/640` | Read/Write | Read | None |
| **Data**    | `755/644` | Read/Write | Read | Read |
| **Logs**    | `750/640` | Read/Write | Read | None |
| **Cache**   | `750/660` | Read/Write | Read/Write | None |

### 3. **Critical Security Rules**

#### ⛔ **NEVER DO**
- World-writable permissions (`777`, `666`)
- Root user in containers
- Mounting system directories
- Sharing secrets between containers
- Using default permissions

#### ✅ **ALWAYS DO**
- Use specific UID/GID (non-root)
- Set explicit permissions
- Separate volume types
- Regular permission audits
- Backup before changes

## 🐳 Secure Docker Compose Configuration

### Basic Secure Setup
```yaml
version: '3.8'

services:
  ai-trading-bot:
    image: ai-trading-bot:latest
    user: "1001:1001"              # Non-root user
    read_only: true                # Read-only root filesystem
    security_opt:
      - no-new-privileges:true     # Prevent privilege escalation
    cap_drop:
      - ALL                        # Drop all capabilities
    volumes:
      - app_data:/app/data:rw
      - app_config:/app/config:ro   # Read-only config
      - app_secrets:/app/secrets:ro # Read-only secrets
      - app_logs:/app/logs:rw

volumes:
  app_data:
    driver: local
    driver_opts:
      type: none
      o: bind,uid=1001,gid=1001
      device: ./volumes/data
  
  app_config:
    driver: local
    driver_opts:
      type: none
      o: bind,uid=1001,gid=1001
      device: ./volumes/config
  
  app_secrets:
    driver: local
    driver_opts:
      type: none
      o: bind,uid=1001,gid=1001,mode=600
      device: ./volumes/secrets
  
  app_logs:
    driver: local
    driver_opts:
      type: none
      o: bind,uid=1001,gid=1001
      device: ./volumes/logs
```

### Advanced Security Configuration
```yaml
version: '3.8'

services:
  ai-trading-bot:
    image: ai-trading-bot:secure
    user: "1001:1001"
    read_only: true
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-trading-bot
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    volumes:
      - type: bind
        source: ./volumes/data
        target: /app/data
        bind:
          create_host_path: true
        read_only: false
      - type: bind
        source: ./volumes/secrets
        target: /app/secrets
        bind:
          create_host_path: true
        read_only: true
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔧 Automated Permission Management

### 1. **Pre-deployment Setup Script**
```bash
#!/bin/bash
# setup_secure_volumes.sh

# Create volume directories with secure permissions
mkdir -p ./volumes/{{data,config,secrets,logs,backups}}

# Set ownership (trading bot user)
chown -R 1001:1001 ./volumes/

# Set secure permissions
chmod 750 ./volumes/data ./volumes/config ./volumes/logs
chmod 700 ./volumes/secrets
chmod 755 ./volumes/backups

# Set file permissions
find ./volumes/data -type f -exec chmod 640 {{}} \\;
find ./volumes/config -type f -exec chmod 640 {{}} \\;
find ./volumes/secrets -type f -exec chmod 600 {{}} \\;
find ./volumes/logs -type f -exec chmod 640 {{}} \\;

echo "✅ Secure volume permissions configured"
```

### 2. **Regular Security Audit**
```bash
#!/bin/bash
# volume_security_audit.sh

# Run volume permissions scanner
python3 volume_permissions_security_system.py

# Check for world-writable files
echo "🔍 Checking for world-writable files..."
find ./volumes -type f -perm -002 -ls

# Check for SUID/SGID files
echo "🔍 Checking for SUID/SGID files..."
find ./volumes -type f \\( -perm -4000 -o -perm -2000 \\) -ls

# Verify ownership
echo "🔍 Verifying ownership..."
find ./volumes -not -user 1001 -ls
```

## 📋 Security Checklist

### Pre-deployment
- [ ] Non-root user configured (UID 1001)
- [ ] Volume permissions set correctly
- [ ] Secrets stored with 600/700 permissions
- [ ] No world-writable files
- [ ] No SUID/SGID bits set
- [ ] AppArmor/SELinux profiles configured

### Runtime
- [ ] Container runs as non-root
- [ ] Read-only root filesystem enabled
- [ ] Capabilities dropped
- [ ] Security options configured
- [ ] Health checks implemented

### Post-deployment
- [ ] Regular permission audits scheduled
- [ ] Security monitoring enabled
- [ ] Log analysis configured
- [ ] Incident response plan ready
- [ ] Backup and recovery tested

## 🚨 Common Vulnerabilities and Fixes

### 1. **World-Writable Files**
```bash
# Problem: Files with 777/666 permissions
find ./volumes -type f -perm -002

# Solution: Remove world-write permissions
find ./volumes -type f -perm -002 -exec chmod o-w {{}} \\;
```

### 2. **Incorrect Ownership**
```bash
# Problem: Files owned by root or wrong user
find ./volumes -not -user 1001

# Solution: Change ownership to trading bot user
chown -R 1001:1001 ./volumes/
```

### 3. **Executable Data Files**
```bash
# Problem: Data files with execute permissions
find ./volumes -name "*.json" -perm -111
find ./volumes -name "*.db" -perm -111

# Solution: Remove execute permissions from data files
find ./volumes -name "*.json" -exec chmod -x {{}} \\;
find ./volumes -name "*.db" -exec chmod -x {{}} \\;
```

### 4. **Secrets Exposure**
```bash
# Problem: Secrets readable by group/world
find ./volumes/secrets -type f -perm -044

# Solution: Restrict secrets to owner only
find ./volumes/secrets -type f -exec chmod 600 {{}} \\;
chmod 700 ./volumes/secrets
```

## 🔄 Continuous Security

### Automated Monitoring
```python
# monitor_volume_security.py
import os
import asyncio
from volume_permissions_security_system import VolumePermissionsSecuritySystem

async def continuous_monitoring():
    security_system = VolumePermissionsSecuritySystem()
    
    volumes_to_monitor = [
        './volumes/data',
        './volumes/config',
        './volumes/secrets',
        './volumes/logs'
    ]
    
    while True:
        for volume in volumes_to_monitor:
            scan_result = await security_system.scan_volume_permissions(volume)
            
            if scan_result.risk_level in ['CRITICAL', 'HIGH']:
                # Send alert
                print(f"🚨 Security Alert: {{volume}} - {{scan_result.risk_level}} risk")
                # Implement your alerting mechanism here
        
        # Check every 6 hours
        await asyncio.sleep(6 * 60 * 60)

if __name__ == "__main__":
    asyncio.run(continuous_monitoring())
```

### CI/CD Integration
```yaml
# .github/workflows/volume-security.yml
name: Volume Security Check

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  volume-security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install pyyaml
    
    - name: Run volume security scan
      run: |
        python3 volume_permissions_security_system.py
        
    - name: Check for critical vulnerabilities
      run: |
        # Fail if critical vulnerabilities found
        if grep -q "CRITICAL" volume_security/reports/*.json; then
          echo "❌ Critical volume security issues found!"
          exit 1
        fi
```

## 📞 Emergency Response

### Critical Vulnerability Response
1. **Immediate Actions**
   - Stop affected containers
   - Isolate compromised volumes
   - Fix permissions immediately
   - Audit access logs

2. **Recovery Steps**
   - Restore from secure backups
   - Apply security fixes
   - Re-scan all volumes
   - Update security policies

3. **Prevention**
   - Implement automated scanning
   - Regular security training
   - Update incident response plan
   - Improve monitoring

## 🎯 Production Deployment Recommendations

### High-Security Trading Bot Setup
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  ai-trading-bot:
    image: ai-trading-bot:v1.0.0
    user: "1001:1001"
    read_only: true
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-trading-bot-strict
      - seccomp:seccomp-trading-bot.json
    cap_drop:
      - ALL
    networks:
      - trading_internal
    volumes:
      - type: bind
        source: /opt/trading/data
        target: /app/data
        read_only: false
      - type: bind
        source: /opt/trading/secrets
        target: /app/secrets
        read_only: true
      - type: bind
        source: /opt/trading/logs
        target: /app/logs
        read_only: false
    tmpfs:
      - /tmp:noexec,nosuid,size=50m
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

networks:
  trading_internal:
    driver: bridge
    internal: true
```

## 📚 Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Container Security Guide](https://kubernetes.io/docs/concepts/security/)
- [NIST Container Security Guidelines](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)

---
*Generated by Volume Permissions Security System - Keep your containers secure! 🔒*
"""

if __name__ == "__main__":
    asyncio.run(main())