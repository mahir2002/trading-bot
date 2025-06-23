# 📌 DEPENDENCY PINNING SYSTEM GUIDE

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Pinning Strategies](#pinning-strategies)
5. [Multi-Environment Management](#multi-environment-management)
6. [Security Integration](#security-integration)
7. [Automated Pin Management](#automated-pin-management)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The Dependency Pinning System provides intelligent version pinning for reproducible builds while maintaining security and compatibility. It integrates with vulnerability scanning and dependency update systems to ensure your AI trading bot has stable, secure, and up-to-date dependencies.

### Key Features
- **Multi-Environment Support**: Different pinning strategies for dev, staging, and production
- **Security-Aware Pinning**: Automatic integration with vulnerability scanning
- **Intelligent Strategies**: Exact, compatible, patch-level, and minor-level pinning
- **Automated Maintenance**: Staleness monitoring and automated pin updates
- **Hash Verification**: SHA256 hashes for security verification
- **Lock File Generation**: Reproducible builds with exact versions

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DEPENDENCY PINNING SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      PIN STRATEGY ENGINE                                │ │
│  │                                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ │
│  │  │    EXACT    │  │ COMPATIBLE  │  │    PATCH    │  │    MINOR    │    │ │
│  │  │             │  │             │  │             │  │             │    │ │
│  │  │ pkg==1.2.3  │  │ pkg~=1.2.3  │  │ pkg>=1.2.3 │  │ pkg>=1.2.0 │    │ │
│  │  │             │  │             │  │ <1.3.0      │  │ <1.3.0      │    │ │
│  │  │ Production  │  │ Compatible  │  │ Patch Level │  │ Minor Level │    │ │
│  │  │ Critical    │  │ Stability   │  │ Updates     │  │ Features    │    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    MULTI-ENVIRONMENT MANAGEMENT                         │ │
│  │                                                                         │ │
│  │ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │ │
│  │ │   DEVELOPMENT   │  │     STAGING     │  │   PRODUCTION    │          │ │
│  │ │                 │  │                 │  │                 │          │ │
│  │ │ • Minor Level   │  │ • Patch Level   │  │ • Exact Pins    │          │ │
│  │ │ • 14 day max    │  │ • 30 day max    │  │ • 60 day max    │          │ │
│  │ │ • Auto Updates  │  │ • Auto Patches  │  │ • Manual Review │          │ │
│  │ │ • Dev Deps      │  │ • Testing       │  │ • Hash Verify   │          │ │
│  │ └─────────────────┘  └─────────────────┘  └─────────────────┘          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                     SECURITY INTEGRATION                                │ │
│  │                                                                         │ │
│  │ • Vulnerability Scanner Integration: Real-time security assessment      │ │
│  │ • Emergency Pin Updates: Immediate security vulnerability response      │ │
│  │ • Security-Aware Strategies: Critical package enhanced protection       │ │
│  │ • Advisory Monitoring: CVE, CWE, CVSS integration                      │ │
│  │ • Compliance Tracking: NIST, OWASP, PCI DSS pin requirements          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    AUTOMATED PIN MANAGEMENT                             │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │ │
│  │  │   STALENESS     │  │   SECURITY      │  │ COMPATIBILITY   │        │ │
│  │  │   MONITORING    │  │   UPDATES       │  │   TESTING       │        │ │
│  │  │                 │  │                 │  │                 │        │ │
│  │  │ • Age Tracking  │  │ • CVE Response  │  │ • Pre-Update    │        │ │
│  │  │ • Policy Check  │  │ • Auto Patches  │  │ • Rollback      │        │ │
│  │  │ • Update Alert  │  │ • Emergency     │  │ • Verification  │        │ │
│  │  │ • Maintenance   │  │ • Notification  │  │ • Test Suite    │        │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### Prerequisites

#### 1. Install Required Tools

```bash
# Install packaging tools
pip install packaging requests python-dateutil

# Install development tools (optional)
pip install pip-tools pipdeptree
```

#### 2. Basic Setup

```python
from dependency_pinning_system import DependencyPinningSystem

# Initialize with default configuration
pinning_system = DependencyPinningSystem()

# Analyze current dependencies
analysis = pinning_system.analyze_current_dependencies()
print(f"Found {analysis['summary']['total_packages']} packages")
```

### Configuration

Create `pinning_config.json`:

```json
{
  "pinning_policies": {
    "production": {
      "default_strategy": "exact",
      "security_override": true,
      "max_pin_age_days": 60,
      "auto_update_patches": false,
      "auto_update_security": true,
      "compatibility_check_required": true,
      "hash_verification": true,
      "exclude_packages": ["dev-tools", "test-framework"]
    },
    "staging": {
      "default_strategy": "patch",
      "security_override": true,
      "max_pin_age_days": 30,
      "auto_update_patches": true,
      "auto_update_security": true,
      "compatibility_check_required": true,
      "hash_verification": true
    },
    "development": {
      "default_strategy": "minor",
      "security_override": true,
      "max_pin_age_days": 14,
      "auto_update_patches": true,
      "auto_update_security": true,
      "compatibility_check_required": false,
      "hash_verification": false,
      "include_dev_dependencies": true
    }
  },
  "critical_packages": [
    "requests", "urllib3", "cryptography", "pyjwt", "pillow",
    "django", "flask", "sqlalchemy", "numpy", "pandas"
  ],
  "pin_files": {
    "production": "requirements-prod.txt",
    "staging": "requirements-staging.txt",
    "development": "requirements-dev.txt",
    "testing": "requirements-test.txt"
  }
}
```

## Pinning Strategies

### 1. Exact Pinning (`==`)

**Use Case**: Production environments, critical packages
**Format**: `package==1.2.3`
**Benefits**: Maximum reproducibility, no unexpected changes
**Drawbacks**: Manual updates required, potential security lag

```python
# Generate exact pins for production
pinning_system.generate_pinned_requirements(
    environment=EnvironmentType.PRODUCTION
)
```

**Example Output**:
```
# Production exact pins
django==4.2.7  # 🔒 Critical package
requests==2.31.0  # 🔒 Critical package
cryptography==41.0.7  # 🔒 Critical package
```

### 2. Compatible Pinning (`~=`)

**Use Case**: Stable environments with controlled updates
**Format**: `package~=1.2.3` (equivalent to `>=1.2.3, ==1.2.*`)
**Benefits**: Automatic patch updates, maintains compatibility
**Drawbacks**: May introduce minor changes

```python
# Configure compatible pinning
policy = PinningPolicy(
    environment=EnvironmentType.STAGING,
    default_strategy=PinStrategy.COMPATIBLE,
    auto_update_patches=True
)
```

**Example Output**:
```
# Staging compatible pins
django~=4.2.0    # Allows 4.2.x updates
requests~=2.31.0 # Allows 2.31.x updates
```

### 3. Patch Level Pinning (`>=x.y.z,<x.y+1.0`)

**Use Case**: Development environments, non-critical packages
**Format**: `package>=1.2.3,<1.3.0`
**Benefits**: Automatic patch updates, security fixes
**Drawbacks**: Potential for breaking changes in patches

```python
# Generate patch-level pins
analysis = pinning_system.analyze_current_dependencies(
    environment=EnvironmentType.DEVELOPMENT
)

for rec in analysis['pinning_recommendations']:
    if rec['recommended_strategy'] == 'patch':
        print(f"{rec['package']}: {rec['recommended_pin']}")
```

**Example Output**:
```
# Development patch-level pins
django>=4.2.7,<4.3.0     # Patch updates allowed
requests>=2.31.0,<2.32.0  # Patch updates allowed
```

### 4. Minor Level Pinning (`>=x.y.z,<x+1.0.0`)

**Use Case**: Development environments, experimental packages
**Format**: `package>=1.2.3,<2.0.0`
**Benefits**: Feature updates, latest improvements
**Drawbacks**: Higher risk of breaking changes

```python
# Configure minor-level pinning for development
dev_policy = {
    'default_strategy': 'minor',
    'max_pin_age_days': 14,
    'auto_update_patches': True,
    'include_dev_dependencies': True
}
```

## Multi-Environment Management

### Environment-Specific Strategies

#### Production Environment
```python
# Production: Maximum stability
production_config = {
    'strategy': PinStrategy.EXACT,
    'max_age_days': 60,
    'security_override': True,
    'hash_verification': True,
    'auto_updates': False,
    'manual_review_required': True
}
```

**Characteristics**:
- Exact version pins for all packages
- Manual review required for updates
- Hash verification enabled
- Extended pin lifetime (60 days)
- Critical package protection

#### Staging Environment
```python
# Staging: Controlled testing
staging_config = {
    'strategy': PinStrategy.PATCH_LEVEL,
    'max_age_days': 30,
    'security_override': True,
    'auto_patch_updates': True,
    'compatibility_testing': True
}
```

**Characteristics**:
- Patch-level pins for testing
- Automatic patch updates
- Compatibility testing enabled
- Medium pin lifetime (30 days)
- Security updates prioritized

#### Development Environment
```python
# Development: Latest features
development_config = {
    'strategy': PinStrategy.MINOR_LEVEL,
    'max_age_days': 14,
    'auto_updates': True,
    'dev_dependencies': True,
    'testing_optional': True
}
```

**Characteristics**:
- Minor-level pins for features
- Frequent automatic updates
- Development dependencies included
- Short pin lifetime (14 days)
- Minimal testing requirements

### Cross-Environment Synchronization

```python
def synchronize_critical_packages():
    """Synchronize critical package versions across environments."""
    
    critical_packages = ['django', 'requests', 'cryptography']
    
    # Get production versions as baseline
    prod_pins = pinning_system.get_environment_pins(EnvironmentType.PRODUCTION)
    
    for env in [EnvironmentType.STAGING, EnvironmentType.DEVELOPMENT]:
        for package in critical_packages:
            if package in prod_pins:
                # Pin to same version in other environments
                pinning_system.update_pin(
                    package=package,
                    environment=env,
                    target_version=prod_pins[package],
                    reason=PinReason.COMPATIBILITY
                )
```

### Environment Promotion Pipeline

```bash
#!/bin/bash
# promote_pins.sh - Promote pins through environments

echo "🚀 Promoting pins through environments..."

# Step 1: Test in development
python -c "
from dependency_pinning_system import DependencyPinningSystem
system = DependencyPinningSystem()
system.validate_pins(EnvironmentType.DEVELOPMENT)
system.generate_pinned_requirements(EnvironmentType.DEVELOPMENT)
"

# Step 2: Promote to staging
echo "📋 Promoting to staging..."
cp requirements-dev.txt requirements-staging.txt

# Run staging tests
python -m pytest tests/ --env=staging

# Step 3: Promote to production (manual approval)
echo "🔒 Ready for production promotion (manual approval required)"
```

## Security Integration

### Vulnerability-Driven Pin Updates

```python
def security_aware_pinning():
    """Implement security-aware pinning strategies."""
    
    # Integration with vulnerability scanner
    from vulnerability_scanner import VulnerabilityScanner
    
    scanner = VulnerabilityScanner()
    scan_results = scanner.scan_all()
    critical_vulns = scanner.get_critical_vulnerabilities(scan_results)
    
    for vuln in critical_vulns:
        if hasattr(vuln, 'package_name') and vuln.fixed_versions:
            # Emergency pin update for security
            for env in EnvironmentType:
                pinning_system.update_pins(
                    environment=env,
                    packages=[vuln.package_name],
                    security_only=True
                )
                
                logger.info(f"🚨 Emergency security update: {vuln.package_name}")
```

### Critical Package Protection

```python
# Enhanced protection for critical packages
critical_package_policy = {
    'packages': [
        'requests', 'urllib3', 'cryptography', 'pyjwt',
        'django', 'flask', 'sqlalchemy'
    ],
    'enhanced_monitoring': True,
    'immediate_security_updates': True,
    'compatibility_testing_required': True,
    'rollback_on_failure': True,
    'notification_on_updates': True
}

# Apply enhanced protection
for package in critical_package_policy['packages']:
    pinning_system.set_package_policy(
        package=package,
        policy=critical_package_policy
    )
```

### Security Advisory Integration

```python
def monitor_security_advisories():
    """Monitor security advisories for pinned packages."""
    
    advisory_sources = [
        'https://pypi.org/pypi/{package}/json',
        'https://api.github.com/repos/pypa/advisory-database',
        'https://nvd.nist.gov/vuln/search'
    ]
    
    for package_name, pin in pinning_system.pinned_dependencies.items():
        # Check each advisory source
        advisories = []
        
        for source in advisory_sources:
            try:
                advisories.extend(
                    check_package_advisories(package_name, pin.pinned_version, source)
                )
            except Exception as e:
                logger.warning(f"Failed to check {source} for {package_name}: {e}")
        
        # Update pin with advisory information
        pin.security_advisories = advisories
        
        # Trigger update if critical advisories found
        if any(adv.get('severity') == 'critical' for adv in advisories):
            trigger_emergency_update(package_name, pin)
```

## Automated Pin Management

### Staleness Monitoring

```python
def monitor_pin_staleness():
    """Monitor and alert on stale pins."""
    
    stale_pins = []
    
    for env in EnvironmentType:
        validation_results = pinning_system.validate_pins(env)
        policy = pinning_system.policies[env]
        
        for result in validation_results:
            if result.days_since_pin > policy.max_pin_age_days:
                stale_pins.append({
                    'package': result.package_name,
                    'environment': env.value,
                    'age_days': result.days_since_pin,
                    'max_age': policy.max_pin_age_days,
                    'staleness_ratio': result.days_since_pin / policy.max_pin_age_days
                })
    
    # Sort by staleness ratio (most stale first)
    stale_pins.sort(key=lambda x: x['staleness_ratio'], reverse=True)
    
    # Generate staleness report
    if stale_pins:
        generate_staleness_alert(stale_pins)
    
    return stale_pins
```

### Automated Update Workflows

```python
def automated_pin_maintenance():
    """Automated pin maintenance workflow."""
    
    maintenance_actions = []
    
    # Step 1: Security updates (immediate)
    security_updates = identify_security_updates()
    for update in security_updates:
        result = execute_security_update(update)
        maintenance_actions.append(result)
    
    # Step 2: Staleness updates (scheduled)
    stale_pins = monitor_pin_staleness()
    for pin in stale_pins:
        if pin['staleness_ratio'] > 2.0:  # Very stale
            result = schedule_staleness_update(pin)
            maintenance_actions.append(result)
    
    # Step 3: Compatibility updates (maintenance window)
    if is_maintenance_window():
        compatibility_updates = identify_compatibility_updates()
        for update in compatibility_updates:
            result = execute_compatibility_update(update)
            maintenance_actions.append(result)
    
    # Step 4: Generate reports
    generate_maintenance_report(maintenance_actions)
    
    return maintenance_actions
```

### Maintenance Windows

```python
def setup_maintenance_windows():
    """Configure maintenance windows for different environments."""
    
    maintenance_config = {
        'production': {
            'schedule': 'weekly',
            'day': 'sunday',
            'time': '02:00',
            'duration_hours': 4,
            'timezone': 'UTC',
            'actions': [
                'staleness_updates',
                'compatibility_updates',
                'lock_file_regeneration'
            ]
        },
        'staging': {
            'schedule': 'daily',
            'time': '01:00',
            'duration_hours': 2,
            'timezone': 'UTC',
            'actions': [
                'patch_updates',
                'testing_validation',
                'requirements_sync'
            ]
        },
        'development': {
            'schedule': 'continuous',
            'immediate_updates': True,
            'actions': [
                'minor_updates',
                'feature_updates',
                'dev_dependency_updates'
            ]
        }
    }
    
    # Schedule maintenance tasks
    for env, config in maintenance_config.items():
        schedule_maintenance_window(env, config)
```

## Best Practices

### 1. Pin Strategy Selection

```python
def select_pin_strategy(package_name: str, environment: EnvironmentType) -> PinStrategy:
    """Select appropriate pin strategy based on package and environment."""
    
    # Critical packages always get exact pins in production
    if (package_name in CRITICAL_PACKAGES and 
        environment == EnvironmentType.PRODUCTION):
        return PinStrategy.EXACT
    
    # Security-sensitive packages
    if is_security_sensitive(package_name):
        return PinStrategy.EXACT
    
    # Environment-based defaults
    strategy_map = {
        EnvironmentType.PRODUCTION: PinStrategy.EXACT,
        EnvironmentType.STAGING: PinStrategy.PATCH_LEVEL,
        EnvironmentType.DEVELOPMENT: PinStrategy.MINOR_LEVEL
    }
    
    return strategy_map.get(environment, PinStrategy.EXACT)
```

### 2. Pin Freshness Management

```python
def manage_pin_freshness():
    """Implement pin freshness management strategy."""
    
    freshness_policies = {
        'critical_packages': {
            'max_age_days': 30,
            'update_strategy': 'immediate',
            'testing_required': True
        },
        'security_packages': {
            'max_age_days': 14,
            'update_strategy': 'batch',
            'security_scan_required': True
        },
        'regular_packages': {
            'max_age_days': 90,
            'update_strategy': 'maintenance_window',
            'compatibility_testing': True
        }
    }
    
    # Apply policies based on package classification
    for package_name, pin in pinning_system.pinned_dependencies.items():
        policy = classify_package_policy(package_name, freshness_policies)
        apply_freshness_policy(pin, policy)
```

### 3. Compatibility Testing

```python
def implement_compatibility_testing():
    """Implement comprehensive compatibility testing."""
    
    test_suite = {
        'unit_tests': {
            'command': 'python -m pytest tests/unit/',
            'timeout': 300,
            'required': True
        },
        'integration_tests': {
            'command': 'python -m pytest tests/integration/',
            'timeout': 600,
            'required': True
        },
        'security_tests': {
            'command': 'bandit -r . -f json',
            'timeout': 120,
            'required': False
        },
        'performance_tests': {
            'command': 'python -m pytest tests/performance/',
            'timeout': 900,
            'required': False
        }
    }
    
    def test_pin_compatibility(package_name: str, target_version: str) -> bool:
        """Test compatibility of pin update."""
        
        # Create isolated test environment
        with create_test_environment() as test_env:
            # Install target version
            test_env.install(f"{package_name}=={target_version}")
            
            # Run test suite
            for test_name, test_config in test_suite.items():
                result = test_env.run_test(test_config)
                
                if test_config['required'] and not result.passed:
                    logger.error(f"Required test {test_name} failed for {package_name}=={target_version}")
                    return False
            
            return True
```

### 4. Lock File Management

```python
def advanced_lock_file_management():
    """Advanced lock file generation and management."""
    
    # Generate lock files with hashes
    def generate_secure_lock_file(environment: EnvironmentType):
        """Generate lock file with security hashes."""
        
        pins = pinning_system.get_environment_pins(environment)
        lock_content = []
        
        # Header
        lock_content.extend([
            f"# Secure lock file for {environment.value}",
            f"# Generated: {datetime.now(timezone.utc).isoformat()}",
            f"# Use: pip install -r requirements-{environment.value}.lock --require-hashes",
            ""
        ])
        
        # Add packages with hashes
        for package_name, version in pins.items():
            # Get package hash from PyPI
            package_hash = get_package_hash(package_name, version)
            
            if package_hash:
                lock_content.extend([
                    f"{package_name}=={version} \\",
                    f"    --hash=sha256:{package_hash}"
                ])
            else:
                lock_content.append(f"{package_name}=={version}")
                logger.warning(f"No hash available for {package_name}=={version}")
        
        # Write lock file
        lock_file = f"requirements-{environment.value}.lock"
        with open(lock_file, 'w') as f:
            f.write('\n'.join(lock_content))
        
        return lock_file
    
    # Generate for all environments
    lock_files = {}
    for env in EnvironmentType:
        try:
            lock_file = generate_secure_lock_file(env)
            lock_files[env.value] = lock_file
            logger.info(f"✅ Generated secure lock file: {lock_file}")
        except Exception as e:
            logger.error(f"❌ Failed to generate lock file for {env.value}: {e}")
    
    return lock_files
```

### 5. CI/CD Integration

#### GitHub Actions Workflow

```yaml
name: Dependency Pin Management

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  push:
    paths:
      - 'requirements*.txt'
      - 'pinning_config.json'
  workflow_dispatch:

jobs:
  pin-management:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [development, staging, production]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install packaging requests python-dateutil
    
    - name: Analyze dependencies
      run: |
        python -c "
        from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
        system = DependencyPinningSystem()
        env = EnvironmentType('${{ matrix.environment }}')
        analysis = system.analyze_current_dependencies(env)
        print(f'Environment: {env.value}')
        print(f'Total packages: {analysis[\"summary\"][\"total_packages\"]}')
        print(f'Critical packages: {analysis[\"summary\"][\"critical_packages\"]}')
        "
    
    - name: Validate pins
      run: |
        python -c "
        from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
        system = DependencyPinningSystem()
        env = EnvironmentType('${{ matrix.environment }}')
        results = system.validate_pins(env)
        failed = [r for r in results if not r.validation_passed]
        if failed:
            print(f'❌ {len(failed)} pin validations failed')
            for result in failed[:5]:
                print(f'  - {result.package_name}: {result.issues}')
            exit(1)
        else:
            print(f'✅ All {len(results)} pins validated successfully')
        "
    
    - name: Generate pinned requirements
      run: |
        python -c "
        from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
        system = DependencyPinningSystem()
        env = EnvironmentType('${{ matrix.environment }}')
        content = system.generate_pinned_requirements(env)
        print(f'Generated requirements for {env.value}')
        "
    
    - name: Generate lock file (production only)
      if: matrix.environment == 'production'
      run: |
        python -c "
        from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
        system = DependencyPinningSystem()
        lock_content = system.generate_lock_file(EnvironmentType.PRODUCTION)
        print('Generated secure lock file with hashes')
        "
    
    - name: Upload requirements artifacts
      uses: actions/upload-artifact@v3
      with:
        name: requirements-${{ matrix.environment }}
        path: |
          requirements-${{ matrix.environment }}.txt
          requirements-${{ matrix.environment }}.lock
```

#### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    triggers {
        cron('H 2 * * 0')  // Weekly on Sunday
    }
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['development', 'staging', 'production'],
            description: 'Environment to manage pins for'
        )
        booleanParam(
            name: 'FORCE_UPDATE',
            defaultValue: false,
            description: 'Force update stale pins'
        )
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    pip install packaging requests python-dateutil
                '''
            }
        }
        
        stage('Analyze Dependencies') {
            steps {
                script {
                    sh '''
                        . venv/bin/activate
                        python -c "
                        from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
                        system = DependencyPinningSystem()
                        env = EnvironmentType('${params.ENVIRONMENT}')
                        analysis = system.analyze_current_dependencies(env)
                        
                        # Save analysis results
                        import json
                        with open('dependency_analysis.json', 'w') as f:
                            json.dump(analysis, f, indent=2, default=str)
                        "
                    '''
                    
                    // Archive analysis results
                    archiveArtifacts artifacts: 'dependency_analysis.json'
                }
            }
        }
        
        stage('Validate Pins') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -c "
                    from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
                    system = DependencyPinningSystem()
                    env = EnvironmentType('${params.ENVIRONMENT}')
                    results = system.validate_pins(env)
                    
                    failed = [r for r in results if not r.validation_passed]
                    if failed:
                        print(f'❌ {len(failed)} validation failures:')
                        for result in failed:
                            print(f'  - {result.package_name}: {result.issues}')
                        
                        if '${params.FORCE_UPDATE}' != 'true':
                            exit(1)
                    else:
                        print(f'✅ All {len(results)} pins validated')
                    "
                '''
            }
        }
        
        stage('Update Pins') {
            when {
                anyOf {
                    params.FORCE_UPDATE == true
                    environment name: 'ENVIRONMENT', value: 'development'
                }
            }
            steps {
                sh '''
                    . venv/bin/activate
                    python -c "
                    from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
                    system = DependencyPinningSystem()
                    env = EnvironmentType('${params.ENVIRONMENT}')
                    
                    # Update stale pins
                    update_results = system.update_pins(env, security_only=False)
                    
                    successful = len(update_results.get('successful_updates', []))
                    failed = len(update_results.get('failed_updates', []))
                    
                    print(f'Pin updates: {successful} successful, {failed} failed')
                    "
                '''
            }
        }
        
        stage('Generate Requirements') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -c "
                    from dependency_pinning_system import DependencyPinningSystem, EnvironmentType
                    system = DependencyPinningSystem()
                    env = EnvironmentType('${params.ENVIRONMENT}')
                    
                    # Generate pinned requirements
                    content = system.generate_pinned_requirements(env)
                    print(f'Generated requirements for {env.value}')
                    
                    # Generate lock file for production
                    if env == EnvironmentType.PRODUCTION:
                        lock_content = system.generate_lock_file(env)
                        print('Generated secure lock file')
                    "
                '''
                
                // Archive generated files
                archiveArtifacts artifacts: 'requirements-*.txt,requirements-*.lock'
            }
        }
        
        stage('Test Updated Dependencies') {
            when {
                anyOf {
                    params.FORCE_UPDATE == true
                    environment name: 'ENVIRONMENT', value: 'development'
                }
            }
            steps {
                sh '''
                    . venv/bin/activate
                    
                    # Install updated dependencies
                    pip install -r requirements-${params.ENVIRONMENT}.txt
                    
                    # Run test suite
                    python -m pytest tests/ -v --tb=short
                '''
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh 'rm -rf venv'
        }
        
        success {
            // Notify on successful pin management
            emailext (
                subject: "✅ Pin Management Successful - ${params.ENVIRONMENT}",
                body: "Dependency pin management completed successfully for ${params.ENVIRONMENT} environment.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
        
        failure {
            // Notify on failures
            emailext (
                subject: "❌ Pin Management Failed - ${params.ENVIRONMENT}",
                body: "Dependency pin management failed for ${params.ENVIRONMENT} environment. Check build logs for details.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Pin Validation Failures

**Problem**: Pins fail validation due to staleness or security issues

**Solution**:
```python
# Diagnose validation failures
def diagnose_pin_failures():
    validation_results = pinning_system.validate_pins(EnvironmentType.PRODUCTION)
    
    for result in validation_results:
        if not result.validation_passed:
            print(f"❌ {result.package_name}:")
            print(f"   Current pin: {result.current_pin}")
            print(f"   Recommended: {result.recommended_pin}")
            print(f"   Issues: {result.issues}")
            print(f"   Security concerns: {result.security_concerns}")
            print(f"   Days since pin: {result.days_since_pin}")
            print()

# Fix validation failures
def fix_validation_failures():
    # Update stale pins
    update_results = pinning_system.update_pins(
        environment=EnvironmentType.PRODUCTION,
        security_only=False
    )
    
    print(f"Updated {len(update_results['successful_updates'])} packages")
```

#### 2. Hash Verification Errors

**Problem**: Package hashes cannot be retrieved or verified

**Solution**:
```python
# Debug hash verification issues
def debug_hash_verification():
    packages = pinning_system._get_installed_packages()
    
    for package_name, version in packages.items():
        hash_value = pinning_system._get_package_hash(package_name, version)
        
        if hash_value:
            print(f"✅ {package_name}=={version}: {hash_value[:16]}...")
        else:
            print(f"❌ {package_name}=={version}: No hash available")

# Generate lock file without hashes for problematic packages
def generate_partial_lock_file():
    # Disable hash verification temporarily
    policy = pinning_system.policies[EnvironmentType.PRODUCTION]
    original_hash_verification = policy.hash_verification
    
    try:
        policy.hash_verification = False
        lock_content = pinning_system.generate_lock_file(EnvironmentType.PRODUCTION)
        print("Generated lock file without hash verification")
    finally:
        policy.hash_verification = original_hash_verification
```

#### 3. Compatibility Test Failures

**Problem**: Pin updates fail compatibility testing

**Solution**:
```python
# Debug compatibility issues
def debug_compatibility_issues(package_name: str, target_version: str):
    print(f"🔍 Testing compatibility for {package_name}=={target_version}")
    
    # Create test environment
    test_env = create_isolated_environment()
    
    try:
        # Install target version
        test_env.install(f"{package_name}=={target_version}")
        
        # Run individual test categories
        test_results = {}
        
        test_commands = {
            'import_test': f'python -c "import {package_name}"',
            'unit_tests': 'python -m pytest tests/unit/ -x',
            'integration_tests': 'python -m pytest tests/integration/ -x'
        }
        
        for test_name, command in test_commands.items():
            result = test_env.run_command(command)
            test_results[test_name] = {
                'passed': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        
        # Analyze results
        for test_name, result in test_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {test_name}")
            
            if not result['passed']:
                print(f"   Error: {result['error']}")
        
    finally:
        test_env.cleanup()

# Rollback problematic updates
def rollback_pin_update(package_name: str, environment: EnvironmentType):
    pin_key = f"{package_name}_{environment.value}"
    
    if pin_key in pinning_system.pinned_dependencies:
        pin = pinning_system.pinned_dependencies[pin_key]
        
        # Find previous version from history
        previous_version = find_previous_pin_version(package_name, environment)
        
        if previous_version:
            # Rollback to previous version
            pin.pinned_version = previous_version
            pin.pinned_date = datetime.now(timezone.utc)
            pin.pin_reason = PinReason.COMPATIBILITY
            
            print(f"🔄 Rolled back {package_name} to {previous_version}")
```

#### 4. Environment Synchronization Issues

**Problem**: Pins become out of sync between environments

**Solution**:
```python
# Synchronize pins across environments
def synchronize_environments():
    print("🔄 Synchronizing pins across environments...")
    
    # Get production pins as baseline
    prod_pins = {}
    for pin_key, pin in pinning_system.pinned_dependencies.items():
        if pin.environment == EnvironmentType.PRODUCTION:
            prod_pins[pin.name] = pin.pinned_version
    
    # Update staging and development
    for env in [EnvironmentType.STAGING, EnvironmentType.DEVELOPMENT]:
        env_policy = pinning_system.policies[env]
        
        for package_name, prod_version in prod_pins.items():
            # Check if package should be synchronized
            if package_name in pinning_system.config['critical_packages']:
                # Synchronize critical packages exactly
                target_pin = f"{package_name}=={prod_version}"
            else:
                # Use environment-appropriate strategy
                target_pin = pinning_system._generate_pin_spec(
                    package_name, prod_version, env_policy.default_strategy
                )
            
            # Update pin
            pinning_system.update_pins(
                environment=env,
                packages=[package_name]
            )
            
            print(f"📌 Synchronized {package_name} in {env.value}: {target_pin}")

# Detect synchronization drift
def detect_sync_drift():
    drift_report = []
    
    # Compare critical packages across environments
    critical_packages = pinning_system.config['critical_packages']
    
    for package in critical_packages:
        versions = {}
        
        for env in EnvironmentType:
            pin_key = f"{package}_{env.value}"
            if pin_key in pinning_system.pinned_dependencies:
                pin = pinning_system.pinned_dependencies[pin_key]
                versions[env.value] = pin.pinned_version
        
        # Check for version differences
        unique_versions = set(versions.values())
        if len(unique_versions) > 1:
            drift_report.append({
                'package': package,
                'versions': versions,
                'drift_detected': True
            })
    
    return drift_report
```

---

## Summary

The Dependency Pinning System provides comprehensive version management with:

✅ **Multi-Environment Support**: Different strategies for dev, staging, production
✅ **Security Integration**: Automatic vulnerability-driven pin updates
✅ **Intelligent Strategies**: Exact, compatible, patch, and minor-level pinning
✅ **Automated Maintenance**: Staleness monitoring and scheduled updates
✅ **Hash Verification**: SHA256 security verification for reproducible builds
✅ **Lock File Generation**: Secure, reproducible dependency specifications
✅ **CI/CD Integration**: Seamless integration with development workflows
✅ **Compatibility Testing**: Automated testing before pin updates
✅ **Cross-Environment Sync**: Coordinated pin management across environments
✅ **Comprehensive Monitoring**: Pin freshness and security advisory tracking

The system ensures your AI trading bot has stable, secure, and reproducible builds while maintaining the flexibility to adopt security updates and compatible improvements automatically. 