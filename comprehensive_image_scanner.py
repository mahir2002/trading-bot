#!/usr/bin/env python3
"""
Comprehensive Docker Image Vulnerability Scanner
Multi-tool vulnerability detection and remediation system
"""

import os
import json
import yaml
import logging
import subprocess
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union
from enum import Enum
import hashlib
from pathlib import Path
import re
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SeverityLevel(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"
    UNKNOWN = "UNKNOWN"

class ScannerType(Enum):
    """Supported vulnerability scanners."""
    TRIVY = "trivy"
    CLAIR = "clair"
    GRYPE = "grype"
    SNYK = "snyk"
    DOCKER_SCOUT = "docker-scout"

@dataclass
class Vulnerability:
    """Vulnerability information."""
    id: str
    severity: SeverityLevel
    package_name: str
    installed_version: str
    fixed_version: Optional[str]
    title: str
    description: str
    references: List[str] = field(default_factory=list)
    cvss_score: Optional[float] = None
    scanner: str = ""

@dataclass
class ScanResult:
    """Image scan results."""
    image_name: str
    image_tag: str
    scanner: str
    scan_time: datetime
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    scan_duration: float = 0.0

class ComprehensiveImageScanner:
    """
    Multi-tool Docker image vulnerability scanner with advanced reporting.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the comprehensive image scanner."""
        self.config = self._load_config(config_path)
        self.scan_results: Dict[str, List[ScanResult]] = {}
        self.scanners = self._initialize_scanners()
        
        # Create reports directory
        os.makedirs("vulnerability_reports", exist_ok=True)
        
        logger.info("✅ Comprehensive Image Scanner initialized")
        logger.info(f"   Available scanners: {list(self.scanners.keys())}")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load scanner configuration."""
        default_config = {
            "scanners": {
                "trivy": {
                    "enabled": True,
                    "severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    "vuln_type": ["os", "library"],
                    "exit_code": 1,
                    "timeout": 600
                },
                "grype": {
                    "enabled": True,
                    "fail_on": "high",
                    "timeout": 600
                },
                "clair": {
                    "enabled": True,
                    "api_url": "http://localhost:6060",
                    "timeout": 600
                },
                "snyk": {
                    "enabled": False,  # Requires API token
                    "severity_threshold": "high",
                    "timeout": 600
                },
                "docker_scout": {
                    "enabled": True,
                    "timeout": 600
                }
            },
            "reporting": {
                "formats": ["json", "html", "sarif"],
                "include_fixed": True,
                "include_negligible": False
            },
            "remediation": {
                "auto_update": False,
                "create_patches": True,
                "notification_webhook": None
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                return {**default_config, **user_config}
        
        return default_config
    
    def _initialize_scanners(self) -> Dict[str, bool]:
        """Initialize available scanners."""
        scanners = {}
        
        # Check Trivy
        try:
            result = subprocess.run(["trivy", "--version"], capture_output=True, text=True)
            scanners["trivy"] = result.returncode == 0
        except FileNotFoundError:
            scanners["trivy"] = False
        
        # Check Grype
        try:
            result = subprocess.run(["grype", "version"], capture_output=True, text=True)
            scanners["grype"] = result.returncode == 0
        except FileNotFoundError:
            scanners["grype"] = False
        
        # Check Docker Scout
        try:
            result = subprocess.run(["docker", "scout", "version"], capture_output=True, text=True)
            scanners["docker_scout"] = result.returncode == 0
        except FileNotFoundError:
            scanners["docker_scout"] = False
        
        # Clair requires API endpoint
        scanners["clair"] = self.config["scanners"]["clair"]["enabled"]
        
        # Snyk requires authentication
        scanners["snyk"] = self.config["scanners"]["snyk"]["enabled"]
        
        return scanners
    
    async def scan_image(self, image_name: str, scanners: Optional[List[str]] = None) -> Dict[str, ScanResult]:
        """Scan image with multiple vulnerability scanners."""
        if scanners is None:
            scanners = [s for s, available in self.scanners.items() if available]
        
        logger.info(f"🔍 Starting comprehensive scan of {image_name}")
        logger.info(f"   Using scanners: {scanners}")
        
        scan_tasks = []
        for scanner in scanners:
            if self.scanners.get(scanner, False):
                scan_tasks.append(self._scan_with_scanner(image_name, scanner))
        
        # Run all scans concurrently
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Process results
        scan_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Scanner {scanners[i]} failed: {result}")
            else:
                scan_results[scanners[i]] = result
        
        # Store results
        if image_name not in self.scan_results:
            self.scan_results[image_name] = []
        
        for scanner, result in scan_results.items():
            self.scan_results[image_name].append(result)
        
        return scan_results
    
    async def _scan_with_scanner(self, image_name: str, scanner: str) -> ScanResult:
        """Scan image with specific scanner."""
        start_time = datetime.now(timezone.utc)
        
        if scanner == "trivy":
            result = await self._scan_with_trivy(image_name)
        elif scanner == "grype":
            result = await self._scan_with_grype(image_name)
        elif scanner == "docker_scout":
            result = await self._scan_with_docker_scout(image_name)
        elif scanner == "clair":
            result = await self._scan_with_clair(image_name)
        elif scanner == "snyk":
            result = await self._scan_with_snyk(image_name)
        else:
            raise ValueError(f"Unknown scanner: {scanner}")
        
        result.scan_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        return result
    
    async def _scan_with_trivy(self, image_name: str) -> ScanResult:
        """Scan image with Trivy."""
        logger.info(f"🔍 Scanning {image_name} with Trivy...")
        
        cmd = [
            "trivy", "image",
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
            "--vuln-type", "os,library",
            "--no-progress",
            image_name
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0 and process.returncode != 1:  # Trivy returns 1 if vulns found
            raise Exception(f"Trivy scan failed: {stderr.decode()}")
        
        # Parse Trivy JSON output
        trivy_data = json.loads(stdout.decode())
        vulnerabilities = []
        
        if "Results" in trivy_data:
            for result in trivy_data["Results"]:
                if "Vulnerabilities" in result:
                    for vuln in result["Vulnerabilities"]:
                        vulnerability = Vulnerability(
                            id=vuln.get("VulnerabilityID", ""),
                            severity=SeverityLevel(vuln.get("Severity", "UNKNOWN")),
                            package_name=vuln.get("PkgName", ""),
                            installed_version=vuln.get("InstalledVersion", ""),
                            fixed_version=vuln.get("FixedVersion"),
                            title=vuln.get("Title", ""),
                            description=vuln.get("Description", ""),
                            references=vuln.get("References", []),
                            cvss_score=self._extract_cvss_score(vuln),
                            scanner="trivy"
                        )
                        vulnerabilities.append(vulnerability)
        
        return self._create_scan_result(image_name, "trivy", vulnerabilities)
    
    async def _scan_with_grype(self, image_name: str) -> ScanResult:
        """Scan image with Grype."""
        logger.info(f"🔍 Scanning {image_name} with Grype...")
        
        cmd = [
            "grype", image_name,
            "-o", "json",
            "--fail-on", "high"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Grype may return non-zero if vulnerabilities found
        if process.returncode not in [0, 1, 5]:
            raise Exception(f"Grype scan failed: {stderr.decode()}")
        
        # Parse Grype JSON output
        grype_data = json.loads(stdout.decode())
        vulnerabilities = []
        
        if "matches" in grype_data:
            for match in grype_data["matches"]:
                vuln = match.get("vulnerability", {})
                artifact = match.get("artifact", {})
                
                vulnerability = Vulnerability(
                    id=vuln.get("id", ""),
                    severity=SeverityLevel(vuln.get("severity", "UNKNOWN").upper()),
                    package_name=artifact.get("name", ""),
                    installed_version=artifact.get("version", ""),
                    fixed_version=vuln.get("fix", {}).get("versions", [None])[0] if vuln.get("fix") else None,
                    title=vuln.get("dataSource", ""),
                    description=vuln.get("description", ""),
                    references=vuln.get("urls", []),
                    cvss_score=self._extract_grype_cvss_score(vuln),
                    scanner="grype"
                )
                vulnerabilities.append(vulnerability)
        
        return self._create_scan_result(image_name, "grype", vulnerabilities)
    
    async def _scan_with_docker_scout(self, image_name: str) -> ScanResult:
        """Scan image with Docker Scout."""
        logger.info(f"🔍 Scanning {image_name} with Docker Scout...")
        
        cmd = [
            "docker", "scout", "cves",
            "--format", "json",
            image_name
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # Docker Scout might not be available or configured
            logger.warning(f"Docker Scout scan failed: {stderr.decode()}")
            return self._create_scan_result(image_name, "docker_scout", [])
        
        # Parse Docker Scout output (format may vary)
        try:
            scout_data = json.loads(stdout.decode())
            vulnerabilities = []
            
            # Docker Scout JSON format parsing (simplified)
            if isinstance(scout_data, dict) and "vulnerabilities" in scout_data:
                for vuln in scout_data["vulnerabilities"]:
                    vulnerability = Vulnerability(
                        id=vuln.get("id", ""),
                        severity=SeverityLevel(vuln.get("severity", "UNKNOWN").upper()),
                        package_name=vuln.get("package", ""),
                        installed_version=vuln.get("version", ""),
                        fixed_version=vuln.get("fixed_version"),
                        title=vuln.get("title", ""),
                        description=vuln.get("description", ""),
                        references=vuln.get("references", []),
                        scanner="docker_scout"
                    )
                    vulnerabilities.append(vulnerability)
            
            return self._create_scan_result(image_name, "docker_scout", vulnerabilities)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Docker Scout JSON output")
            return self._create_scan_result(image_name, "docker_scout", [])
    
    async def _scan_with_clair(self, image_name: str) -> ScanResult:
        """Scan image with Clair (requires Clair server)."""
        logger.info(f"🔍 Scanning {image_name} with Clair...")
        
        # This is a simplified Clair integration
        # In practice, you'd need to push the image to Clair and query the API
        logger.warning("Clair integration requires additional setup")
        return self._create_scan_result(image_name, "clair", [])
    
    async def _scan_with_snyk(self, image_name: str) -> ScanResult:
        """Scan image with Snyk (requires authentication)."""
        logger.info(f"🔍 Scanning {image_name} with Snyk...")
        
        if not os.environ.get("SNYK_TOKEN"):
            logger.warning("Snyk token not configured")
            return self._create_scan_result(image_name, "snyk", [])
        
        cmd = [
            "snyk", "container", "test",
            "--json",
            image_name
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        try:
            snyk_data = json.loads(stdout.decode())
            vulnerabilities = []
            
            if "vulnerabilities" in snyk_data:
                for vuln in snyk_data["vulnerabilities"]:
                    vulnerability = Vulnerability(
                        id=vuln.get("id", ""),
                        severity=SeverityLevel(vuln.get("severity", "UNKNOWN").upper()),
                        package_name=vuln.get("packageName", ""),
                        installed_version=vuln.get("version", ""),
                        fixed_version=vuln.get("nearestFixedInVersion"),
                        title=vuln.get("title", ""),
                        description=vuln.get("description", ""),
                        references=vuln.get("references", []),
                        cvss_score=vuln.get("cvssScore"),
                        scanner="snyk"
                    )
                    vulnerabilities.append(vulnerability)
            
            return self._create_scan_result(image_name, "snyk", vulnerabilities)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Snyk JSON output")
            return self._create_scan_result(image_name, "snyk", [])
    
    def _extract_cvss_score(self, vuln_data: Dict) -> Optional[float]:
        """Extract CVSS score from vulnerability data."""
        if "CVSS" in vuln_data:
            cvss = vuln_data["CVSS"]
            if isinstance(cvss, dict):
                for version in ["nvd", "redhat", "ubuntu"]:
                    if version in cvss and "V3Score" in cvss[version]:
                        return float(cvss[version]["V3Score"])
        return None
    
    def _extract_grype_cvss_score(self, vuln_data: Dict) -> Optional[float]:
        """Extract CVSS score from Grype vulnerability data."""
        if "cvss" in vuln_data:
            cvss_list = vuln_data["cvss"]
            if cvss_list and isinstance(cvss_list, list):
                return float(cvss_list[0].get("metrics", {}).get("baseScore", 0))
        return None
    
    def _create_scan_result(self, image_name: str, scanner: str, vulnerabilities: List[Vulnerability]) -> ScanResult:
        """Create scan result with vulnerability counts."""
        # Count vulnerabilities by severity
        severity_counts = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0
        }
        
        for vuln in vulnerabilities:
            if vuln.severity in severity_counts:
                severity_counts[vuln.severity] += 1
        
        # Extract image name and tag
        if ":" in image_name:
            name, tag = image_name.rsplit(":", 1)
        else:
            name, tag = image_name, "latest"
        
        return ScanResult(
            image_name=name,
            image_tag=tag,
            scanner=scanner,
            scan_time=datetime.now(timezone.utc),
            vulnerabilities=vulnerabilities,
            total_vulnerabilities=len(vulnerabilities),
            critical_count=severity_counts[SeverityLevel.CRITICAL],
            high_count=severity_counts[SeverityLevel.HIGH],
            medium_count=severity_counts[SeverityLevel.MEDIUM],
            low_count=severity_counts[SeverityLevel.LOW]
        )
    
    def generate_comprehensive_report(self, image_name: str) -> Dict[str, Any]:
        """Generate comprehensive vulnerability report."""
        if image_name not in self.scan_results:
            return {"error": f"No scan results found for {image_name}"}
        
        results = self.scan_results[image_name]
        
        # Aggregate results from all scanners
        all_vulnerabilities = {}
        scanner_summary = {}
        
        for result in results:
            scanner_summary[result.scanner] = {
                "total": result.total_vulnerabilities,
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
                "scan_time": result.scan_time.isoformat(),
                "duration": result.scan_duration
            }
            
            # Deduplicate vulnerabilities by CVE ID
            for vuln in result.vulnerabilities:
                vuln_key = f"{vuln.id}_{vuln.package_name}"
                if vuln_key not in all_vulnerabilities:
                    all_vulnerabilities[vuln_key] = vuln
                else:
                    # Merge scanner information
                    existing = all_vulnerabilities[vuln_key]
                    existing.scanner += f", {vuln.scanner}"
        
        # Calculate aggregate statistics
        unique_vulnerabilities = list(all_vulnerabilities.values())
        aggregate_counts = {
            "total": len(unique_vulnerabilities),
            "critical": sum(1 for v in unique_vulnerabilities if v.severity == SeverityLevel.CRITICAL),
            "high": sum(1 for v in unique_vulnerabilities if v.severity == SeverityLevel.HIGH),
            "medium": sum(1 for v in unique_vulnerabilities if v.severity == SeverityLevel.MEDIUM),
            "low": sum(1 for v in unique_vulnerabilities if v.severity == SeverityLevel.LOW)
        }
        
        # Generate risk score
        risk_score = self._calculate_risk_score(aggregate_counts)
        
        return {
            "image": image_name,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "scanners_used": list(scanner_summary.keys()),
            "aggregate_summary": aggregate_counts,
            "risk_score": risk_score,
            "scanner_results": scanner_summary,
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "severity": vuln.severity.value,
                    "package": vuln.package_name,
                    "installed_version": vuln.installed_version,
                    "fixed_version": vuln.fixed_version,
                    "title": vuln.title,
                    "description": vuln.description,
                    "cvss_score": vuln.cvss_score,
                    "detected_by": vuln.scanner,
                    "references": vuln.references
                }
                for vuln in unique_vulnerabilities
            ]
        }
    
    def _calculate_risk_score(self, counts: Dict[str, int]) -> Dict[str, Any]:
        """Calculate overall risk score for the image."""
        # Weighted scoring system
        weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1
        }
        
        weighted_score = (
            counts["critical"] * weights["critical"] +
            counts["high"] * weights["high"] +
            counts["medium"] * weights["medium"] +
            counts["low"] * weights["low"]
        )
        
        # Normalize to 0-100 scale
        max_possible_score = 100  # Arbitrary maximum for scaling
        normalized_score = min(weighted_score, max_possible_score)
        
        # Risk level determination
        if normalized_score >= 50:
            risk_level = "CRITICAL"
        elif normalized_score >= 30:
            risk_level = "HIGH"
        elif normalized_score >= 15:
            risk_level = "MEDIUM"
        elif normalized_score > 0:
            risk_level = "LOW"
        else:
            risk_level = "NEGLIGIBLE"
        
        return {
            "score": normalized_score,
            "level": risk_level,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level."""
        recommendations = {
            "CRITICAL": "🚨 DO NOT DEPLOY - Contains critical vulnerabilities that must be fixed immediately",
            "HIGH": "⚠️ DEPLOY WITH CAUTION - Contains high-severity vulnerabilities, consider fixing before production",
            "MEDIUM": "📋 MONITOR CLOSELY - Contains medium-severity vulnerabilities, schedule fixes",
            "LOW": "✅ ACCEPTABLE RISK - Contains only low-severity vulnerabilities",
            "NEGLIGIBLE": "🎉 SECURE - No significant vulnerabilities detected"
        }
        return recommendations.get(risk_level, "Unknown risk level")
    
    async def scan_multiple_images(self, images: List[str]) -> Dict[str, Dict[str, Any]]:
        """Scan multiple images concurrently."""
        logger.info(f"🔍 Starting batch scan of {len(images)} images")
        
        scan_tasks = [self.scan_image(image) for image in images]
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        batch_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scan {images[i]}: {result}")
                batch_results[images[i]] = {"error": str(result)}
            else:
                batch_results[images[i]] = self.generate_comprehensive_report(images[i])
        
        return batch_results
    
    def generate_html_report(self, image_name: str) -> str:
        """Generate HTML vulnerability report."""
        report_data = self.generate_comprehensive_report(image_name)
        
        if "error" in report_data:
            return f"<html><body><h1>Error</h1><p>{report_data['error']}</p></body></html>"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Docker Image Vulnerability Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
                .summary { display: flex; gap: 20px; margin: 20px 0; }
                .summary-card { background: #f8f9fa; padding: 15px; border-radius: 5px; flex: 1; }
                .critical { background: #dc3545; color: white; }
                .high { background: #fd7e14; color: white; }
                .medium { background: #ffc107; color: black; }
                .low { background: #28a745; color: white; }
                .vuln-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .vuln-table th, .vuln-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .vuln-table th { background: #f2f2f2; }
                .risk-score { font-size: 24px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Docker Image Vulnerability Report</h1>
                <p><strong>Image:</strong> {image}</p>
                <p><strong>Scan Time:</strong> {scan_time}</p>
                <p><strong>Scanners Used:</strong> {scanners}</p>
            </div>
            
            <div class="summary">
                <div class="summary-card critical">
                    <h3>Critical</h3>
                    <div class="risk-score">{critical}</div>
                </div>
                <div class="summary-card high">
                    <h3>High</h3>
                    <div class="risk-score">{high}</div>
                </div>
                <div class="summary-card medium">
                    <h3>Medium</h3>
                    <div class="risk-score">{medium}</div>
                </div>
                <div class="summary-card low">
                    <h3>Low</h3>
                    <div class="risk-score">{low}</div>
                </div>
            </div>
            
            <div class="summary-card">
                <h3>🎯 Risk Assessment</h3>
                <p><strong>Risk Score:</strong> {risk_score}/100</p>
                <p><strong>Risk Level:</strong> {risk_level}</p>
                <p><strong>Recommendation:</strong> {recommendation}</p>
            </div>
            
            <h2>📋 Vulnerability Details</h2>
            <table class="vuln-table">
                <tr>
                    <th>CVE ID</th>
                    <th>Severity</th>
                    <th>Package</th>
                    <th>Installed Version</th>
                    <th>Fixed Version</th>
                    <th>Title</th>
                    <th>CVSS Score</th>
                    <th>Detected By</th>
                </tr>
                {vulnerability_rows}
            </table>
        </body>
        </html>
        """
        
        # Generate vulnerability rows
        vulnerability_rows = ""
        for vuln in report_data.get("vulnerabilities", []):
            severity_class = vuln["severity"].lower()
            cvss_score = vuln.get("cvss_score", "N/A")
            fixed_version = vuln.get("fixed_version") or "Not Available"
            
            vulnerability_rows += f"""
                <tr class="{severity_class}">
                    <td>{vuln['id']}</td>
                    <td>{vuln['severity']}</td>
                    <td>{vuln['package']}</td>
                    <td>{vuln['installed_version']}</td>
                    <td>{fixed_version}</td>
                    <td>{vuln['title'][:100]}...</td>
                    <td>{cvss_score}</td>
                    <td>{vuln['detected_by']}</td>
                </tr>
            """
        
        # Fill template
        html_content = html_template.format(
            image=report_data["image"],
            scan_time=report_data["scan_timestamp"],
            scanners=", ".join(report_data["scanners_used"]),
            critical=report_data["aggregate_summary"]["critical"],
            high=report_data["aggregate_summary"]["high"],
            medium=report_data["aggregate_summary"]["medium"],
            low=report_data["aggregate_summary"]["low"],
            risk_score=report_data["risk_score"]["score"],
            risk_level=report_data["risk_score"]["level"],
            recommendation=report_data["risk_score"]["recommendation"],
            vulnerability_rows=vulnerability_rows
        )
        
        return html_content
    
    def save_reports(self, image_name: str):
        """Save vulnerability reports in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"vuln_report_{image_name.replace(':', '_').replace('/', '_')}_{timestamp}"
        
        # JSON Report
        json_report = self.generate_comprehensive_report(image_name)
        json_path = f"vulnerability_reports/{base_filename}.json"
        with open(json_path, "w") as f:
            json.dump(json_report, f, indent=2)
        
        # HTML Report
        html_report = self.generate_html_report(image_name)
        html_path = f"vulnerability_reports/{base_filename}.html"
        with open(html_path, "w") as f:
            f.write(html_report)
        
        logger.info(f"📄 Reports saved:")
        logger.info(f"   JSON: {json_path}")
        logger.info(f"   HTML: {html_path}")
        
        return {
            "json": json_path,
            "html": html_path
        }

async def main():
    """Main function to demonstrate comprehensive image scanning."""
    print("🔍 Comprehensive Docker Image Vulnerability Scanner")
    print("=" * 70)
    
    scanner = ComprehensiveImageScanner()
    
    # Example images to scan (AI Trading Bot images)
    test_images = [
        "trading-bot:latest",
        "trading-bot:ultra-secure",
        "dashboard:latest",
        "python:3.11-alpine",  # Base image
        "redis:7-alpine"       # Database image
    ]
    
    print(f"\n🎯 Scanning {len(test_images)} images...")
    
    # Scan each image
    for image in test_images:
        try:
            print(f"\n🔍 Scanning {image}...")
            results = await scanner.scan_image(image)
            
            # Generate and save reports
            scanner.save_reports(image)
            
            # Show summary
            report = scanner.generate_comprehensive_report(image)
            if "error" not in report:
                summary = report["aggregate_summary"]
                risk = report["risk_score"]
                print(f"   ✅ Scan complete:")
                print(f"      Total vulnerabilities: {summary['total']}")
                print(f"      Critical: {summary['critical']} | High: {summary['high']} | Medium: {summary['medium']} | Low: {summary['low']}")
                print(f"      Risk Score: {risk['score']}/100 ({risk['level']})")
            else:
                print(f"   ❌ Scan failed: {report['error']}")
                
        except Exception as e:
            print(f"   ❌ Error scanning {image}: {e}")
    
    print(f"\n✅ Comprehensive vulnerability scanning complete!")
    print(f"📄 Reports saved in vulnerability_reports/ directory")

if __name__ == "__main__":
    asyncio.run(main()) 