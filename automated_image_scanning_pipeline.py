#!/usr/bin/env python3
"""
Automated Docker Image Scanning Pipeline
CI/CD integration for continuous vulnerability assessment
"""

import os
import json
import yaml
import logging
import asyncio
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

from comprehensive_image_scanner import ComprehensiveImageScanner, SeverityLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScanPolicy:
    """Image scanning policy configuration."""
    # Severity thresholds
    fail_on_critical: bool = True
    fail_on_high: bool = True
    fail_on_medium: bool = False
    max_critical: int = 0
    max_high: int = 5
    max_medium: int = 20
    
    # Scan requirements
    required_scanners: List[str] = field(default_factory=lambda: ["trivy"])
    scan_timeout: int = 1800  # 30 minutes
    
    # Compliance requirements
    require_base_image_scan: bool = True
    require_dependency_scan: bool = True
    max_image_age_days: int = 30

@dataclass
class NotificationConfig:
    """Notification configuration for scan results."""
    # Slack integration
    slack_webhook: Optional[str] = None
    slack_channel: str = "#security-alerts"
    
    # Email configuration
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)
    
    # Webhook notifications
    webhook_url: Optional[str] = None
    
    # GitHub/GitLab integration
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

class AutomatedImageScanningPipeline:
    """
    Automated pipeline for continuous Docker image vulnerability scanning.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the automated scanning pipeline."""
        self.config = self._load_pipeline_config(config_path)
        self.scanner = ComprehensiveImageScanner()
        self.scan_policy = ScanPolicy(**self.config.get("scan_policy", {}))
        self.notifications = NotificationConfig(**self.config.get("notifications", {}))
        
        # Create pipeline directories
        os.makedirs("scan_pipeline/reports", exist_ok=True)
        os.makedirs("scan_pipeline/policies", exist_ok=True)
        os.makedirs("scan_pipeline/artifacts", exist_ok=True)
        
        logger.info("✅ Automated Image Scanning Pipeline initialized")
    
    def _load_pipeline_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load pipeline configuration."""
        default_config = {
            "scan_policy": {
                "fail_on_critical": True,
                "fail_on_high": True,
                "max_critical": 0,
                "max_high": 5,
                "required_scanners": ["trivy", "grype"]
            },
            "notifications": {
                "slack_webhook": os.environ.get("SLACK_WEBHOOK_URL"),
                "email_from": os.environ.get("NOTIFICATION_EMAIL"),
                "webhook_url": os.environ.get("NOTIFICATION_WEBHOOK")
            },
            "ci_cd": {
                "github_actions": True,
                "gitlab_ci": True,
                "jenkins": True,
                "docker_registry": "docker.io"
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                return {**default_config, **user_config}
        
        return default_config
    
    async def scan_image_pipeline(self, image_name: str, build_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute complete image scanning pipeline."""
        pipeline_start = datetime.now(timezone.utc)
        build_id = build_id or f"scan_{int(pipeline_start.timestamp())}"
        
        logger.info(f"🚀 Starting image scanning pipeline for {image_name}")
        logger.info(f"   Build ID: {build_id}")
        
        pipeline_result = {
            "image": image_name,
            "build_id": build_id,
            "pipeline_start": pipeline_start.isoformat(),
            "status": "running",
            "stages": {}
        }
        
        try:
            # Stage 1: Pre-scan validation
            stage_result = await self._pre_scan_validation(image_name)
            pipeline_result["stages"]["pre_validation"] = stage_result
            
            if not stage_result["passed"]:
                pipeline_result["status"] = "failed"
                pipeline_result["failure_stage"] = "pre_validation"
                return pipeline_result
            
            # Stage 2: Vulnerability scanning
            stage_result = await self._vulnerability_scanning_stage(image_name)
            pipeline_result["stages"]["vulnerability_scan"] = stage_result
            
            # Stage 3: Policy enforcement
            stage_result = await self._policy_enforcement_stage(image_name, pipeline_result["stages"]["vulnerability_scan"])
            pipeline_result["stages"]["policy_enforcement"] = stage_result
            
            # Stage 4: Report generation
            stage_result = await self._report_generation_stage(image_name, build_id)
            pipeline_result["stages"]["report_generation"] = stage_result
            
            # Stage 5: Notification and alerts
            stage_result = await self._notification_stage(image_name, pipeline_result)
            pipeline_result["stages"]["notifications"] = stage_result
            
            # Determine overall pipeline status
            pipeline_result["status"] = "passed" if pipeline_result["stages"]["policy_enforcement"]["passed"] else "failed"
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            pipeline_result["status"] = "error"
            pipeline_result["error"] = str(e)
        
        pipeline_result["pipeline_end"] = datetime.now(timezone.utc).isoformat()
        pipeline_result["duration"] = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
        
        # Save pipeline results
        await self._save_pipeline_results(build_id, pipeline_result)
        
        return pipeline_result
    
    async def _pre_scan_validation(self, image_name: str) -> Dict[str, Any]:
        """Pre-scan validation stage."""
        logger.info("🔍 Stage 1: Pre-scan validation")
        
        validation_result = {
            "stage": "pre_validation",
            "passed": True,
            "checks": {},
            "start_time": datetime.now(timezone.utc).isoformat()
        }
        
        # Check 1: Image exists and is accessible
        try:
            result = subprocess.run(
                ["docker", "inspect", image_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            validation_result["checks"]["image_accessible"] = {
                "passed": result.returncode == 0,
                "message": "Image is accessible" if result.returncode == 0 else "Image not found or inaccessible"
            }
        except subprocess.TimeoutExpired:
            validation_result["checks"]["image_accessible"] = {
                "passed": False,
                "message": "Image inspection timed out"
            }
        
        # Check 2: Image age validation
        if self.scan_policy.max_image_age_days > 0:
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.Created}}", image_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    created_date = datetime.fromisoformat(result.stdout.strip().replace('Z', '+00:00'))
                    age_days = (datetime.now(timezone.utc) - created_date).days
                    
                    validation_result["checks"]["image_age"] = {
                        "passed": age_days <= self.scan_policy.max_image_age_days,
                        "message": f"Image is {age_days} days old (max: {self.scan_policy.max_image_age_days})",
                        "age_days": age_days
                    }
            except Exception as e:
                validation_result["checks"]["image_age"] = {
                    "passed": False,
                    "message": f"Failed to check image age: {e}"
                }
        
        # Check 3: Scanner availability
        scanner_check = {"passed": True, "available_scanners": []}
        for scanner in self.scan_policy.required_scanners:
            available = self.scanner.scanners.get(scanner, False)
            scanner_check["available_scanners"].append({
                "scanner": scanner,
                "available": available
            })
            if not available:
                scanner_check["passed"] = False
        
        validation_result["checks"]["scanner_availability"] = scanner_check
        
        # Overall validation result
        validation_result["passed"] = all(
            check["passed"] for check in validation_result["checks"].values()
        )
        
        validation_result["end_time"] = datetime.now(timezone.utc).isoformat()
        
        return validation_result
    
    async def _vulnerability_scanning_stage(self, image_name: str) -> Dict[str, Any]:
        """Vulnerability scanning stage."""
        logger.info("🔍 Stage 2: Vulnerability scanning")
        
        scan_start = datetime.now(timezone.utc)
        
        # Execute comprehensive scan
        scan_results = await self.scanner.scan_image(
            image_name,
            scanners=self.scan_policy.required_scanners
        )
        
        # Generate comprehensive report
        comprehensive_report = self.scanner.generate_comprehensive_report(image_name)
        
        stage_result = {
            "stage": "vulnerability_scan",
            "start_time": scan_start.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration": (datetime.now(timezone.utc) - scan_start).total_seconds(),
            "scanners_used": list(scan_results.keys()),
            "scan_summary": comprehensive_report.get("aggregate_summary", {}),
            "risk_score": comprehensive_report.get("risk_score", {}),
            "vulnerabilities_found": len(comprehensive_report.get("vulnerabilities", []))
        }
        
        return stage_result
    
    async def _policy_enforcement_stage(self, image_name: str, scan_stage: Dict[str, Any]) -> Dict[str, Any]:
        """Policy enforcement stage."""
        logger.info("🔍 Stage 3: Policy enforcement")
        
        policy_result = {
            "stage": "policy_enforcement",
            "passed": True,
            "violations": [],
            "start_time": datetime.now(timezone.utc).isoformat()
        }
        
        scan_summary = scan_stage.get("scan_summary", {})
        
        # Check critical vulnerabilities
        if self.scan_policy.fail_on_critical and scan_summary.get("critical", 0) > self.scan_policy.max_critical:
            policy_result["violations"].append({
                "type": "critical_vulnerabilities",
                "found": scan_summary.get("critical", 0),
                "allowed": self.scan_policy.max_critical,
                "message": f"Found {scan_summary.get('critical', 0)} critical vulnerabilities (max allowed: {self.scan_policy.max_critical})"
            })
            policy_result["passed"] = False
        
        # Check high vulnerabilities
        if self.scan_policy.fail_on_high and scan_summary.get("high", 0) > self.scan_policy.max_high:
            policy_result["violations"].append({
                "type": "high_vulnerabilities",
                "found": scan_summary.get("high", 0),
                "allowed": self.scan_policy.max_high,
                "message": f"Found {scan_summary.get('high', 0)} high vulnerabilities (max allowed: {self.scan_policy.max_high})"
            })
            policy_result["passed"] = False
        
        # Check medium vulnerabilities
        if self.scan_policy.fail_on_medium and scan_summary.get("medium", 0) > self.scan_policy.max_medium:
            policy_result["violations"].append({
                "type": "medium_vulnerabilities",
                "found": scan_summary.get("medium", 0),
                "allowed": self.scan_policy.max_medium,
                "message": f"Found {scan_summary.get('medium', 0)} medium vulnerabilities (max allowed: {self.scan_policy.max_medium})"
            })
            policy_result["passed"] = False
        
        policy_result["end_time"] = datetime.now(timezone.utc).isoformat()
        
        return policy_result
    
    async def _report_generation_stage(self, image_name: str, build_id: str) -> Dict[str, Any]:
        """Report generation stage."""
        logger.info("🔍 Stage 4: Report generation")
        
        report_start = datetime.now(timezone.utc)
        
        # Generate and save reports
        report_paths = self.scanner.save_reports(image_name)
        
        # Generate additional CI/CD artifacts
        sarif_report = await self._generate_sarif_report(image_name)
        junit_report = await self._generate_junit_report(image_name, build_id)
        
        stage_result = {
            "stage": "report_generation",
            "start_time": report_start.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "reports_generated": {
                "json": report_paths.get("json"),
                "html": report_paths.get("html"),
                "sarif": sarif_report,
                "junit": junit_report
            }
        }
        
        return stage_result
    
    async def _notification_stage(self, image_name: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Notification and alerting stage."""
        logger.info("🔍 Stage 5: Notifications")
        
        notification_start = datetime.now(timezone.utc)
        notifications_sent = []
        
        # Determine notification urgency
        scan_summary = pipeline_result["stages"]["vulnerability_scan"]["scan_summary"]
        policy_passed = pipeline_result["stages"]["policy_enforcement"]["passed"]
        
        urgency = "low"
        if scan_summary.get("critical", 0) > 0:
            urgency = "critical"
        elif scan_summary.get("high", 0) > 0:
            urgency = "high"
        elif not policy_passed:
            urgency = "medium"
        
        # Send Slack notification
        if self.notifications.slack_webhook and urgency in ["critical", "high"]:
            slack_result = await self._send_slack_notification(image_name, pipeline_result, urgency)
            notifications_sent.append(slack_result)
        
        # Send email notification
        if self.notifications.email_to and urgency in ["critical", "high"]:
            email_result = await self._send_email_notification(image_name, pipeline_result, urgency)
            notifications_sent.append(email_result)
        
        # Send webhook notification
        if self.notifications.webhook_url:
            webhook_result = await self._send_webhook_notification(image_name, pipeline_result)
            notifications_sent.append(webhook_result)
        
        stage_result = {
            "stage": "notifications",
            "start_time": notification_start.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "urgency": urgency,
            "notifications_sent": notifications_sent
        }
        
        return stage_result
    
    async def _generate_sarif_report(self, image_name: str) -> str:
        """Generate SARIF report for security tools integration."""
        comprehensive_report = self.scanner.generate_comprehensive_report(image_name)
        
        sarif_report = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "Comprehensive Image Scanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/your-org/image-scanner"
                    }
                },
                "results": []
            }]
        }
        
        # Convert vulnerabilities to SARIF format
        for vuln in comprehensive_report.get("vulnerabilities", []):
            sarif_result = {
                "ruleId": vuln["id"],
                "message": {
                    "text": f"{vuln['title']} in {vuln['package']} {vuln['installed_version']}"
                },
                "level": self._severity_to_sarif_level(vuln["severity"]),
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": f"docker://{image_name}"
                        }
                    }
                }],
                "properties": {
                    "package": vuln["package"],
                    "installedVersion": vuln["installed_version"],
                    "fixedVersion": vuln.get("fixed_version"),
                    "cvssScore": vuln.get("cvss_score"),
                    "detectedBy": vuln["detected_by"]
                }
            }
            sarif_report["runs"][0]["results"].append(sarif_result)
        
        # Save SARIF report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sarif_filename = f"scan_pipeline/reports/sarif_{image_name.replace(':', '_').replace('/', '_')}_{timestamp}.sarif"
        
        with open(sarif_filename, 'w') as f:
            json.dump(sarif_report, f, indent=2)
        
        return sarif_filename
    
    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert vulnerability severity to SARIF level."""
        mapping = {
            "CRITICAL": "error",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "note",
            "NEGLIGIBLE": "note"
        }
        return mapping.get(severity, "note")
    
    async def _generate_junit_report(self, image_name: str, build_id: str) -> str:
        """Generate JUnit XML report for CI/CD integration."""
        comprehensive_report = self.scanner.generate_comprehensive_report(image_name)
        scan_summary = comprehensive_report.get("aggregate_summary", {})
        
        # Simple JUnit XML structure
        junit_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="VulnerabilityScanning" tests="4" failures="{int(scan_summary.get('critical', 0) > 0) + int(scan_summary.get('high', 0) > 0)}" time="0">
    <testcase name="CriticalVulnerabilities" classname="SecurityScan">
        {'<failure message="Critical vulnerabilities found">' + str(scan_summary.get('critical', 0)) + ' critical vulnerabilities detected</failure>' if scan_summary.get('critical', 0) > 0 else ''}
    </testcase>
    <testcase name="HighVulnerabilities" classname="SecurityScan">
        {'<failure message="High vulnerabilities found">' + str(scan_summary.get('high', 0)) + ' high vulnerabilities detected</failure>' if scan_summary.get('high', 0) > 0 else ''}
    </testcase>
    <testcase name="MediumVulnerabilities" classname="SecurityScan"/>
    <testcase name="LowVulnerabilities" classname="SecurityScan"/>
</testsuite>"""
        
        # Save JUnit report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        junit_filename = f"scan_pipeline/reports/junit_{image_name.replace(':', '_').replace('/', '_')}_{timestamp}.xml"
        
        with open(junit_filename, 'w') as f:
            f.write(junit_xml)
        
        return junit_filename
    
    async def _send_slack_notification(self, image_name: str, pipeline_result: Dict[str, Any], urgency: str) -> Dict[str, Any]:
        """Send Slack notification."""
        if not self.notifications.slack_webhook:
            return {"type": "slack", "sent": False, "reason": "No webhook configured"}
        
        scan_summary = pipeline_result["stages"]["vulnerability_scan"]["scan_summary"]
        policy_passed = pipeline_result["stages"]["policy_enforcement"]["passed"]
        
        # Choose emoji and color based on urgency
        emoji_map = {"critical": "🚨", "high": "⚠️", "medium": "📋", "low": "ℹ️"}
        color_map = {"critical": "#FF0000", "high": "#FF6600", "medium": "#FFCC00", "low": "#00FF00"}
        
        emoji = emoji_map.get(urgency, "ℹ️")
        color = color_map.get(urgency, "#808080")
        
        status_emoji = "✅" if policy_passed else "❌"
        status_text = "PASSED" if policy_passed else "FAILED"
        
        slack_payload = {
            "channel": self.notifications.slack_channel,
            "username": "Security Scanner",
            "icon_emoji": ":shield:",
            "attachments": [{
                "color": color,
                "title": f"{emoji} Docker Image Security Scan - {status_text}",
                "title_link": "https://your-ci-system.com/build/" + pipeline_result.get("build_id", "unknown"),
                "fields": [
                    {"title": "Image", "value": image_name, "short": True},
                    {"title": "Status", "value": f"{status_emoji} {status_text}", "short": True},
                    {"title": "Critical", "value": str(scan_summary.get("critical", 0)), "short": True},
                    {"title": "High", "value": str(scan_summary.get("high", 0)), "short": True},
                    {"title": "Medium", "value": str(scan_summary.get("medium", 0)), "short": True},
                    {"title": "Low", "value": str(scan_summary.get("low", 0)), "short": True}
                ],
                "footer": "Comprehensive Image Scanner",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(
                self.notifications.slack_webhook,
                json=slack_payload,
                timeout=30
            )
            return {
                "type": "slack",
                "sent": response.status_code == 200,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "type": "slack",
                "sent": False,
                "error": str(e)
            }
    
    async def _send_email_notification(self, image_name: str, pipeline_result: Dict[str, Any], urgency: str) -> Dict[str, Any]:
        """Send email notification."""
        if not self.notifications.smtp_server or not self.notifications.email_to:
            return {"type": "email", "sent": False, "reason": "Email not configured"}
        
        # Email implementation would go here
        return {"type": "email", "sent": False, "reason": "Email implementation needed"}
    
    async def _send_webhook_notification(self, image_name: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send generic webhook notification."""
        if not self.notifications.webhook_url:
            return {"type": "webhook", "sent": False, "reason": "No webhook URL configured"}
        
        try:
            response = requests.post(
                self.notifications.webhook_url,
                json=pipeline_result,
                timeout=30
            )
            return {
                "type": "webhook",
                "sent": response.status_code in [200, 201, 202],
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "type": "webhook",
                "sent": False,
                "error": str(e)
            }
    
    async def _save_pipeline_results(self, build_id: str, pipeline_result: Dict[str, Any]):
        """Save pipeline results for audit and analysis."""
        results_file = f"scan_pipeline/artifacts/pipeline_{build_id}.json"
        
        with open(results_file, 'w') as f:
            json.dump(pipeline_result, f, indent=2)
        
        logger.info(f"📄 Pipeline results saved: {results_file}")
    
    def generate_ci_cd_configs(self):
        """Generate CI/CD configuration files for popular platforms."""
        
        # GitHub Actions workflow
        github_workflow = """
name: Docker Image Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install scanning tools
      run: |
        # Install Trivy
        sudo apt-get update
        sudo apt-get install wget apt-transport-https gnupg lsb-release
        wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
        echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
        sudo apt-get update
        sudo apt-get install trivy
        
        # Install Grype
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
    
    - name: Build Docker image
      run: docker build -t ${{ github.repository }}:${{ github.sha }} .
    
    - name: Install scanner dependencies
      run: pip install -r requirements.txt
    
    - name: Run comprehensive security scan
      run: python automated_image_scanning_pipeline.py --image ${{ github.repository }}:${{ github.sha }} --build-id ${{ github.run_id }}
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        NOTIFICATION_EMAIL: ${{ secrets.NOTIFICATION_EMAIL }}
    
    - name: Upload scan results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-scan-results
        path: |
          vulnerability_reports/
          scan_pipeline/reports/
    
    - name: Upload SARIF results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: scan_pipeline/reports/*.sarif
"""
        
        # GitLab CI configuration
        gitlab_ci = """
stages:
  - build
  - security-scan
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

security-scan:
  stage: security-scan
  image: python:3.11
  services:
    - docker:dind
  before_script:
    - apt-get update
    - apt-get install -y wget apt-transport-https gnupg lsb-release
    # Install Trivy
    - wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add -
    - echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | tee -a /etc/apt/sources.list.d/trivy.list
    - apt-get update
    - apt-get install -y trivy
    # Install Grype
    - curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
    - pip install -r requirements.txt
  script:
    - python automated_image_scanning_pipeline.py --image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA --build-id $CI_JOB_ID
  artifacts:
    reports:
      junit: scan_pipeline/reports/*.xml
      sast: scan_pipeline/reports/*.sarif
    paths:
      - vulnerability_reports/
      - scan_pipeline/reports/
    expire_in: 1 week
  allow_failure: false
"""
        
        # Jenkins pipeline
        jenkins_pipeline = """
pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "${env.JOB_NAME}:${env.BUILD_ID}"
        SLACK_WEBHOOK = credentials('slack-webhook-url')
    }
    
    stages {
        stage('Build') {
            steps {
                script {
                    docker.build(env.DOCKER_IMAGE)
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    # Install scanning tools
                    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
                    
                    # Install Python dependencies
                    pip3 install -r requirements.txt
                    
                    # Run comprehensive scan
                    python3 automated_image_scanning_pipeline.py --image ${DOCKER_IMAGE} --build-id ${BUILD_ID}
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'vulnerability_reports/*, scan_pipeline/reports/*', fingerprint: true
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'vulnerability_reports',
                        reportFiles: '*.html',
                        reportName: 'Security Scan Report'
                    ])
                }
            }
        }
    }
}
"""
        
        # Save configuration files
        os.makedirs("ci_cd_configs", exist_ok=True)
        
        with open("ci_cd_configs/github_actions.yml", "w") as f:
            f.write(github_workflow.strip())
        
        with open("ci_cd_configs/gitlab_ci.yml", "w") as f:
            f.write(gitlab_ci.strip())
        
        with open("ci_cd_configs/Jenkinsfile", "w") as f:
            f.write(jenkins_pipeline.strip())
        
        logger.info("📄 CI/CD configuration files generated:")
        logger.info("   - ci_cd_configs/github_actions.yml")
        logger.info("   - ci_cd_configs/gitlab_ci.yml")
        logger.info("   - ci_cd_configs/Jenkinsfile")

async def main():
    """Main function to demonstrate automated image scanning pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Docker Image Scanning Pipeline")
    parser.add_argument("--image", required=True, help="Docker image to scan")
    parser.add_argument("--build-id", help="Build ID for tracking")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--generate-configs", action="store_true", help="Generate CI/CD configuration files")
    
    args = parser.parse_args()
    
    pipeline = AutomatedImageScanningPipeline(args.config)
    
    if args.generate_configs:
        pipeline.generate_ci_cd_configs()
        return
    
    print("🚀 Automated Docker Image Scanning Pipeline")
    print("=" * 60)
    
    # Execute pipeline
    result = await pipeline.scan_image_pipeline(args.image, args.build_id)
    
    # Print results summary
    print(f"\n📊 Pipeline Results:")
    print(f"   Image: {result['image']}")
    print(f"   Status: {result['status'].upper()}")
    print(f"   Duration: {result.get('duration', 0):.2f} seconds")
    
    if 'stages' in result:
        for stage_name, stage_data in result['stages'].items():
            if isinstance(stage_data, dict):
                status = "✅ PASSED" if stage_data.get('passed', True) else "❌ FAILED"
                print(f"   {stage_name}: {status}")
    
    # Exit with appropriate code
    exit_code = 0 if result['status'] == 'passed' else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())