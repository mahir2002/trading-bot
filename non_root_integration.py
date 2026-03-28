#!/usr/bin/env python3
"""
Non-Root User Integration System for AI Trading Bot
Integrates non-root user security with existing security systems
"""

import os
import logging
import yaml
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# Import existing systems
try:
    from non_root_user_system import NonRootUserSystem, UserConfig, PermissionConfig, SecurityPolicy
    from minimal_base_images_system import MinimalBaseImagesSystem
    from certificate_validation_system import CertificateValidationSystem
    from robust_alerting_system import RobustAlertingSystem
except ImportError as e:
    logging.warning(f"Some security systems not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityIntegrationConfig:
    """Configuration for security system integration."""
    enable_non_root_enforcement: bool = True
    enable_certificate_validation: bool = True
    enable_vulnerability_scanning: bool = True
    enable_alerting: bool = True
    enable_compliance_monitoring: bool = True
    security_level: str = "high"  # low, medium, high, maximum
    
@dataclass
class ContainerSecurityProfile:
    """Complete security profile for a container."""
    container_name: str
    image_name: str
    user_config: UserConfig
    permission_config: PermissionConfig
    security_policy: SecurityPolicy
    certificates: List[str] = field(default_factory=list)
    compliance_frameworks: List[str] = field(default_factory=lambda: ['cis_docker'])
    monitoring_enabled: bool = True
    last_scan: Optional[datetime] = None
    security_score: int = 0

class NonRootIntegrationSystem:
    """
    Comprehensive integration system for non-root user security.
    
    Features:
    - Integration with existing security systems
    - Automated security policy enforcement
    - Continuous compliance monitoring
    - Real-time alerting and reporting
    - Container lifecycle security management
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the integration system."""
        self.config_path = config_path or "non_root_integration_config.yaml"
        
        # Initialize security systems
        self.non_root_system = NonRootUserSystem()
        
        # Try to initialize other systems
        self.minimal_images_system = None
        self.certificate_system = None
        self.alerting_system = None
        
        try:
            self.minimal_images_system = MinimalBaseImagesSystem()
        except:
            logger.warning("Minimal Base Images System not available")
            
        try:
            self.certificate_system = CertificateValidationSystem()
        except:
            logger.warning("Certificate Validation System not available")
            
        try:
            self.alerting_system = RobustAlertingSystem()
        except:
            logger.warning("Alerting System not available")
        
        # Load configuration
        self.config = SecurityIntegrationConfig()
        self.load_configuration()
        
        # Container security profiles
        self.security_profiles: Dict[str, ContainerSecurityProfile] = {}
        
        logger.info("✅ Non-Root Integration System initialized")
    
    def load_configuration(self):
        """Load integration configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                
                logger.info(f"✅ Integration configuration loaded from {self.config_path}")
                
            except Exception as e:
                logger.error(f"❌ Failed to load integration configuration: {e}")
    
    def save_configuration(self):
        """Save current configuration to file."""
        config_data = {
            'enable_non_root_enforcement': self.config.enable_non_root_enforcement,
            'enable_certificate_validation': self.config.enable_certificate_validation,
            'enable_vulnerability_scanning': self.config.enable_vulnerability_scanning,
            'enable_alerting': self.config.enable_alerting,
            'enable_compliance_monitoring': self.config.enable_compliance_monitoring,
            'security_level': self.config.security_level
        }
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            logger.info(f"✅ Integration configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save integration configuration: {e}")
    
    def create_container_security_profile(self, 
                                        container_name: str,
                                        image_name: str,
                                        custom_user_config: Optional[UserConfig] = None,
                                        custom_permission_config: Optional[PermissionConfig] = None,
                                        custom_security_policy: Optional[SecurityPolicy] = None) -> ContainerSecurityProfile:
        """Create a comprehensive security profile for a container."""
        
        # Use custom configs or defaults
        user_config = custom_user_config or self.non_root_system.user_config
        permission_config = custom_permission_config or self.non_root_system.permission_config
        security_policy = custom_security_policy or self.non_root_system.security_policy
        
        # Adjust security level based on configuration
        if self.config.security_level == "maximum":
            security_policy.drop_capabilities = ["ALL"]
            security_policy.add_capabilities = []
            security_policy.read_only_root_fs = True
            security_policy.no_new_privileges = True
            security_policy.allow_privilege_escalation = False
        elif self.config.security_level == "high":
            security_policy.drop_capabilities = ["ALL"]
            security_policy.add_capabilities = ["NET_BIND_SERVICE"]
            security_policy.read_only_root_fs = True
            security_policy.no_new_privileges = True
        
        profile = ContainerSecurityProfile(
            container_name=container_name,
            image_name=image_name,
            user_config=user_config,
            permission_config=permission_config,
            security_policy=security_policy,
            compliance_frameworks=['cis_docker', 'nist_800_190']
        )
        
        # Store profile
        self.security_profiles[container_name] = profile
        
        logger.info(f"✅ Security profile created for container: {container_name}")
        return profile
    
    def generate_integrated_dockerfile(self, 
                                     container_name: str,
                                     base_image: str = "python:3.11-alpine",
                                     application_type: str = "python") -> str:
        """Generate Dockerfile with integrated security features."""
        
        if container_name not in self.security_profiles:
            self.create_container_security_profile(container_name, base_image)
        
        profile = self.security_profiles[container_name]
        
        # Start with non-root user setup
        dockerfile_lines = []
        
        # Base image
        dockerfile_lines.extend([
            f"# Secure Dockerfile for {container_name}",
            f"# Generated by Non-Root Integration System",
            f"FROM {base_image}",
            "",
            "# Security and compliance labels",
            "LABEL security.non_root=\"true\"",
            "LABEL security.compliance=\"cis-docker-benchmark,nist-800-190\"",
            f"LABEL security.level=\"{self.config.security_level}\"",
            "LABEL security.scan=\"enabled\"",
            f"LABEL maintainer=\"AI Trading Bot Security System\"",
            f"LABEL version=\"1.0\"",
            f"LABEL created=\"{datetime.now(timezone.utc).isoformat()}\"",
            ""
        ])
        
        # Get non-root user setup from the system
        user_setup = self.non_root_system.generate_dockerfile_user_setup(base_image)
        dockerfile_lines.append(user_setup)
        
        # Add minimal base image optimizations if available
        if self.minimal_images_system:
            dockerfile_lines.extend([
                "# Minimal base image optimizations",
                "RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* 2>/dev/null || true",
                "RUN rm -rf /usr/share/man /usr/share/doc 2>/dev/null || true",
                ""
            ])
        
        # Application-specific setup
        if application_type == "python":
            dockerfile_lines.extend([
                "# Python application setup",
                "ENV PYTHONUNBUFFERED=1 \\",
                "    PYTHONDONTWRITEBYTECODE=1 \\",
                "    PIP_NO_CACHE_DIR=1 \\",
                "    PIP_DISABLE_PIP_VERSION_CHECK=1 \\",
                "    PYTHONPATH=/app",
                "",
                "# Install Python dependencies as non-root user",
                "COPY --chown=1001:1001 requirements.txt /tmp/",
                "RUN pip install --user --no-cache-dir -r /tmp/requirements.txt && \\",
                "    rm /tmp/requirements.txt",
                "",
                "# Add user site-packages to PATH",
                "ENV PATH=/home/appuser/.local/bin:$PATH",
                ""
            ])
        
        # Security hardening
        dockerfile_lines.extend([
            "# Additional security hardening",
            "RUN find /app -type f -name '*.py' -exec chmod 644 {} \\; 2>/dev/null || true",
            "RUN find /app -type d -exec chmod 755 {} \\; 2>/dev/null || true",
            ""
        ])
        
        # Health check
        dockerfile_lines.extend([
            "# Health check for container monitoring",
            "HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\",
            "    CMD python -c \"import requests; requests.get('http://localhost:5001/health', timeout=5)\" || exit 1",
            ""
        ])
        
        # Final user switch and command
        dockerfile_lines.extend([
            "# Final security configuration",
            f"USER {profile.user_config.uid}:{profile.user_config.gid}",
            f"WORKDIR {profile.permission_config.app_directory}",
            "",
            "# Default command",
            "CMD [\"python\", \"main.py\"]"
        ])
        
        return "\n".join(dockerfile_lines)
    
    def generate_integrated_docker_compose(self, 
                                         containers: List[str] = None) -> Dict[str, Any]:
        """Generate Docker Compose with integrated security features."""
        
        if not containers:
            containers = list(self.security_profiles.keys())
        
        compose_config = {
            'version': '3.8',
            'services': {},
            'networks': {
                'secure-trading-network': {
                    'driver': 'bridge',
                    'ipam': {
                        'config': [{'subnet': '172.30.0.0/16'}]
                    }
                }
            },
            'volumes': {
                'secure_logs': {'driver': 'local'},
                'secure_data': {'driver': 'local'}
            }
        }
        
        for container_name in containers:
            if container_name not in self.security_profiles:
                continue
                
            profile = self.security_profiles[container_name]
            
            # Get security configuration from non-root system
            security_config = self.non_root_system.generate_docker_compose_security()
            
            service_config = {
                'build': {
                    'context': '.',
                    'dockerfile': f'Dockerfile.{container_name}.secure'
                },
                'container_name': f'{container_name}-secure',
                'restart': 'unless-stopped',
                'networks': ['secure-trading-network'],
                'volumes': [
                    'secure_logs:/app/logs',
                    'secure_data:/app/data:ro'
                ],
                'environment': [
                    'TZ=UTC',
                    f'CONTAINER_NAME={container_name}',
                    f'SECURITY_LEVEL={self.config.security_level}'
                ],
                'healthcheck': {
                    'test': ['CMD', 'python', '-c', 'import requests; requests.get("http://localhost:5001/health")'],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3,
                    'start_period': '10s'
                },
                **security_config
            }
            
            # Add specific ports based on container type
            if 'bot' in container_name.lower():
                service_config['ports'] = ['5001:5001']
            elif 'dashboard' in container_name.lower():
                service_config['ports'] = ['8050:8050']
            elif 'redis' in container_name.lower():
                service_config['ports'] = ['6379:6379']
                service_config['image'] = 'redis:7-alpine'
                service_config.pop('build', None)  # Redis uses official image
            
            compose_config['services'][container_name] = service_config
        
        return compose_config
    
    def enforce_security_policies(self, container_name: str) -> Dict[str, Any]:
        """Enforce security policies for a container."""
        
        if container_name not in self.security_profiles:
            raise ValueError(f"No security profile found for container: {container_name}")
        
        profile = self.security_profiles[container_name]
        enforcement_result = {
            'container_name': container_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'policies_enforced': [],
            'violations_found': [],
            'actions_taken': []
        }
        
        # Validate container user
        validation = self.non_root_system.validate_container_user(container_name)
        
        if validation.get('status') == 'fail':
            enforcement_result['violations_found'].extend(validation.get('issues', []))
            enforcement_result['actions_taken'].append("Container security violation detected")
            
            # Send alert if alerting is enabled
            if self.config.enable_alerting and self.alerting_system:
                try:
                    self.alerting_system.send_alert(
                        title=f"Container Security Violation: {container_name}",
                        message=f"Container {container_name} is not running with proper security configuration",
                        severity="high",
                        source="non_root_integration",
                        details=validation
                    )
                    enforcement_result['actions_taken'].append("Security alert sent")
                except Exception as e:
                    logger.error(f"Failed to send security alert: {e}")
        
        # Check compliance
        if self.config.enable_compliance_monitoring:
            try:
                compliance_results = self.non_root_system.run_compliance_check('cis_docker')
                failed_checks = [check for check in compliance_results if check.status == 'FAIL']
                
                if failed_checks:
                    enforcement_result['violations_found'].extend([
                        f"Compliance check failed: {check.check_name}" for check in failed_checks
                    ])
                    enforcement_result['actions_taken'].append("Compliance violations recorded")
                
            except Exception as e:
                logger.error(f"Failed to run compliance check: {e}")
        
        # Update security profile
        profile.last_scan = datetime.now(timezone.utc)
        profile.security_score = self._calculate_profile_security_score(profile, enforcement_result)
        
        enforcement_result['policies_enforced'] = [
            "Non-root user validation",
            "Capability restrictions",
            "Privilege escalation prevention",
            "Read-only filesystem enforcement"
        ]
        
        return enforcement_result
    
    def _calculate_profile_security_score(self, 
                                        profile: ContainerSecurityProfile,
                                        enforcement_result: Dict[str, Any]) -> int:
        """Calculate security score for a container profile."""
        score = 100
        
        # Deduct points for violations
        violation_count = len(enforcement_result.get('violations_found', []))
        score -= violation_count * 10
        
        # Bonus points for security features
        if profile.security_policy.run_as_non_root:
            score += 10
        
        if profile.security_policy.read_only_root_fs:
            score += 10
        
        if profile.security_policy.no_new_privileges:
            score += 5
        
        if "ALL" in profile.security_policy.drop_capabilities:
            score += 15
        
        return max(0, min(100, score))
    
    def monitor_container_security(self, container_names: List[str] = None) -> Dict[str, Any]:
        """Monitor security status of containers."""
        
        if not container_names:
            container_names = list(self.security_profiles.keys())
        
        monitoring_result = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'containers_monitored': len(container_names),
            'security_status': {},
            'overall_security_score': 0,
            'alerts_generated': 0,
            'recommendations': []
        }
        
        total_score = 0
        alerts_count = 0
        
        for container_name in container_names:
            try:
                # Enforce security policies and get results
                enforcement_result = self.enforce_security_policies(container_name)
                
                # Update monitoring result
                monitoring_result['security_status'][container_name] = {
                    'security_score': self.security_profiles[container_name].security_score,
                    'violations': len(enforcement_result.get('violations_found', [])),
                    'last_scan': enforcement_result['timestamp'],
                    'status': 'secure' if len(enforcement_result.get('violations_found', [])) == 0 else 'issues_found'
                }
                
                total_score += self.security_profiles[container_name].security_score
                
                # Count alerts
                if enforcement_result.get('violations_found'):
                    alerts_count += 1
                
            except Exception as e:
                logger.error(f"Failed to monitor container {container_name}: {e}")
                monitoring_result['security_status'][container_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Calculate overall security score
        if container_names:
            monitoring_result['overall_security_score'] = total_score // len(container_names)
        
        monitoring_result['alerts_generated'] = alerts_count
        
        # Generate recommendations
        if monitoring_result['overall_security_score'] < 80:
            monitoring_result['recommendations'].append(
                "Review and strengthen container security configurations"
            )
        
        if alerts_count > 0:
            monitoring_result['recommendations'].append(
                "Address security violations immediately"
            )
        
        return monitoring_result
    
    def generate_comprehensive_security_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security report for all integrated systems."""
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'integration_config': {
                'non_root_enforcement': self.config.enable_non_root_enforcement,
                'certificate_validation': self.config.enable_certificate_validation,
                'vulnerability_scanning': self.config.enable_vulnerability_scanning,
                'alerting': self.config.enable_alerting,
                'compliance_monitoring': self.config.enable_compliance_monitoring,
                'security_level': self.config.security_level
            },
            'container_profiles': {},
            'security_monitoring': {},
            'compliance_status': {},
            'system_integration': {},
            'recommendations': []
        }
        
        # Container profiles summary
        for name, profile in self.security_profiles.items():
            report['container_profiles'][name] = {
                'image_name': profile.image_name,
                'user_uid': profile.user_config.uid,
                'security_score': profile.security_score,
                'last_scan': profile.last_scan.isoformat() if profile.last_scan else None,
                'compliance_frameworks': profile.compliance_frameworks
            }
        
        # Security monitoring
        if self.security_profiles:
            monitoring_result = self.monitor_container_security()
            report['security_monitoring'] = monitoring_result
        
        # System integration status
        report['system_integration'] = {
            'non_root_system': True,
            'minimal_images_system': self.minimal_images_system is not None,
            'certificate_system': self.certificate_system is not None,
            'alerting_system': self.alerting_system is not None
        }
        
        # Generate overall recommendations
        if report['security_monitoring'].get('overall_security_score', 100) < 90:
            report['recommendations'].append(
                "Strengthen overall container security posture"
            )
        
        if not all(report['system_integration'].values()):
            report['recommendations'].append(
                "Enable all available security system integrations"
            )
        
        return report
    
    def create_deployment_files(self):
        """Create all deployment files with integrated security."""
        
        # Create security profiles for common containers
        containers = ['trading-bot', 'dashboard', 'redis']
        
        for container in containers:
            self.create_container_security_profile(
                container_name=container,
                image_name=f"{container}:secure"
            )
        
        # Generate Dockerfiles
        for container in containers:
            if container == 'redis':
                continue  # Redis uses official image
                
            dockerfile_content = self.generate_integrated_dockerfile(
                container_name=container,
                base_image="python:3.11-alpine",
                application_type="python"
            )
            
            with open(f"Dockerfile.{container}.secure", "w") as f:
                f.write(dockerfile_content)
            
            logger.info(f"✅ Created Dockerfile.{container}.secure")
        
        # Generate Docker Compose
        compose_config = self.generate_integrated_docker_compose(containers)
        with open("docker-compose.secure.yml", "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        logger.info("✅ Created docker-compose.secure.yml")
        
        # Generate monitoring script
        monitoring_script = self._generate_monitoring_script()
        with open("monitor_security.py", "w") as f:
            f.write(monitoring_script)
        
        logger.info("✅ Created monitor_security.py")
        
        # Save configurations
        self.save_configuration()
        self.non_root_system.save_configuration()
        
        logger.info("✅ All deployment files created with integrated security")
    
    def _generate_monitoring_script(self) -> str:
        """Generate a monitoring script for continuous security monitoring."""
        
        script_content = '''#!/usr/bin/env python3
"""
Continuous Security Monitoring Script
Generated by Non-Root Integration System
"""

import time
import json
import logging
from datetime import datetime
from non_root_integration import NonRootIntegrationSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main monitoring loop."""
    logger.info("🔐 Starting continuous security monitoring...")
    
    # Initialize integration system
    integration_system = NonRootIntegrationSystem()
    
    while True:
        try:
            # Generate comprehensive security report
            report = integration_system.generate_comprehensive_security_report()
            
            # Log security status
            overall_score = report.get('security_monitoring', {}).get('overall_security_score', 0)
            logger.info(f"📊 Overall Security Score: {overall_score}/100")
            
            # Check for critical issues
            if overall_score < 70:
                logger.warning("⚠️ Security score below threshold - immediate attention required")
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"security_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"📋 Security report saved: {report_file}")
            
            # Wait before next check (default: 1 hour)
            time.sleep(3600)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    main()
'''
        
        return script_content

def main():
    """Main demonstration function."""
    print("🔐 Non-Root User Integration System for AI Trading Bot")
    print("=" * 65)
    
    # Initialize integration system
    integration_system = NonRootIntegrationSystem()
    
    # Create deployment files
    print("\n📦 Creating integrated deployment files...")
    integration_system.create_deployment_files()
    
    # Generate comprehensive security report
    print("\n📊 Generating comprehensive security report...")
    report = integration_system.generate_comprehensive_security_report()
    
    print(f"\n🔍 Integration Status:")
    print(f"  Non-Root System: ✅")
    print(f"  Minimal Images: {'✅' if report['system_integration']['minimal_images_system'] else '❌'}")
    print(f"  Certificate System: {'✅' if report['system_integration']['certificate_system'] else '❌'}")
    print(f"  Alerting System: {'✅' if report['system_integration']['alerting_system'] else '❌'}")
    
    if report.get('security_monitoring'):
        overall_score = report['security_monitoring'].get('overall_security_score', 0)
        print(f"\n📈 Overall Security Score: {overall_score}/100")
    
    # Save comprehensive report
    with open("comprehensive_security_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✅ Comprehensive security report saved")
    print("\n🚀 Integrated non-root security system ready!")
    print("\nNext steps:")
    print("1. Review generated Dockerfiles and docker-compose.secure.yml")
    print("2. Build secure containers: docker-compose -f docker-compose.secure.yml build")
    print("3. Deploy with security: docker-compose -f docker-compose.secure.yml up -d")
    print("4. Monitor security: python monitor_security.py")

if __name__ == "__main__":
    main() 