#!/usr/bin/env python3
"""
Docker Image Vulnerability Scanning Demo
Practical demonstration of vulnerability scanning with real results
"""

import os
import json
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path

class ImageScannerDemo:
    """Simple demonstration of Docker image vulnerability scanning."""
    
    def __init__(self):
        """Initialize the scanner demo."""
        self.trivy_path = os.path.expanduser("~/.local/bin/trivy")
        self.ensure_trivy_available()
    
    def ensure_trivy_available(self):
        """Ensure Trivy is available in PATH."""
        if not os.path.exists(self.trivy_path):
            print("❌ Trivy not found. Please install it first.")
            print("💡 Run: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b ~/.local/bin")
            exit(1)
        
        # Add to PATH for this session
        current_path = os.environ.get('PATH', '')
        local_bin = os.path.expanduser('~/.local/bin')
        if local_bin not in current_path:
            os.environ['PATH'] = f"{local_bin}:{current_path}"
    
    def scan_image_with_trivy(self, image_name):
        """Scan an image with Trivy and return results."""
        print(f"🔍 Scanning {image_name} with Trivy...")
        
        try:
            # Run Trivy scan
            result = subprocess.run([
                self.trivy_path, "image",
                "--format", "json",
                "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
                "--no-progress",
                image_name
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 or result.returncode == 1:  # Trivy returns 1 if vulns found
                # Parse JSON output
                scan_data = json.loads(result.stdout)
                return self.parse_trivy_results(scan_data, image_name)
            else:
                return {
                    "image": image_name,
                    "error": f"Trivy scan failed: {result.stderr}",
                    "vulnerabilities": []
                }
                
        except subprocess.TimeoutExpired:
            return {
                "image": image_name,
                "error": "Scan timed out",
                "vulnerabilities": []
            }
        except json.JSONDecodeError:
            return {
                "image": image_name,
                "error": "Failed to parse scan results",
                "vulnerabilities": []
            }
        except Exception as e:
            return {
                "image": image_name,
                "error": f"Scan error: {e}",
                "vulnerabilities": []
            }
    
    def parse_trivy_results(self, scan_data, image_name):
        """Parse Trivy JSON results into a standardized format."""
        vulnerabilities = []
        
        # Extract vulnerabilities from Trivy results
        if "Results" in scan_data:
            for result in scan_data["Results"]:
                if "Vulnerabilities" in result:
                    for vuln in result["Vulnerabilities"]:
                        vulnerability = {
                            "id": vuln.get("VulnerabilityID", ""),
                            "severity": vuln.get("Severity", "UNKNOWN"),
                            "package": vuln.get("PkgName", ""),
                            "installed_version": vuln.get("InstalledVersion", ""),
                            "fixed_version": vuln.get("FixedVersion", "Not Available"),
                            "title": vuln.get("Title", ""),
                            "description": vuln.get("Description", "")[:200] + "..." if vuln.get("Description", "") else "",
                            "cvss_score": self.extract_cvss_score(vuln)
                        }
                        vulnerabilities.append(vulnerability)
        
        # Count vulnerabilities by severity
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for vuln in vulnerabilities:
            severity = vuln["severity"]
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            "image": image_name,
            "scan_time": datetime.now().isoformat(),
            "total_vulnerabilities": len(vulnerabilities),
            "severity_counts": severity_counts,
            "vulnerabilities": vulnerabilities,
            "risk_assessment": self.assess_risk(severity_counts)
        }
    
    def extract_cvss_score(self, vuln_data):
        """Extract CVSS score from vulnerability data."""
        if "CVSS" in vuln_data:
            cvss = vuln_data["CVSS"]
            if isinstance(cvss, dict):
                for source in ["nvd", "redhat", "ubuntu"]:
                    if source in cvss and "V3Score" in cvss[source]:
                        return cvss[source]["V3Score"]
        return None
    
    def assess_risk(self, severity_counts):
        """Assess overall risk based on vulnerability counts."""
        critical = severity_counts.get("CRITICAL", 0)
        high = severity_counts.get("HIGH", 0)
        medium = severity_counts.get("MEDIUM", 0)
        
        if critical > 0:
            return {
                "level": "CRITICAL",
                "score": min(100, critical * 20 + high * 10 + medium * 5),
                "recommendation": "🚨 DO NOT DEPLOY - Critical vulnerabilities must be fixed immediately"
            }
        elif high > 5:
            return {
                "level": "HIGH", 
                "score": min(80, high * 10 + medium * 5),
                "recommendation": "⚠️ HIGH RISK - Multiple high-severity vulnerabilities detected"
            }
        elif high > 0:
            return {
                "level": "MEDIUM",
                "score": min(60, high * 10 + medium * 5),
                "recommendation": "📋 MODERATE RISK - High-severity vulnerabilities found"
            }
        elif medium > 10:
            return {
                "level": "MEDIUM",
                "score": min(40, medium * 5),
                "recommendation": "📋 MODERATE RISK - Many medium-severity vulnerabilities"
            }
        else:
            return {
                "level": "LOW",
                "score": medium * 2,
                "recommendation": "✅ LOW RISK - Few or no significant vulnerabilities"
            }
    
    def display_scan_results(self, results):
        """Display scan results in a formatted way."""
        if "error" in results:
            print(f"   ❌ Scan failed: {results['error']}")
            return
        
        counts = results["severity_counts"]
        risk = results["risk_assessment"]
        
        print(f"   ✅ Scan completed:")
        print(f"      Total vulnerabilities: {results['total_vulnerabilities']}")
        print(f"      Critical: {counts['CRITICAL']} | High: {counts['HIGH']} | Medium: {counts['MEDIUM']} | Low: {counts['LOW']}")
        print(f"      Risk Level: {risk['level']} (Score: {risk['score']}/100)")
        print(f"      Recommendation: {risk['recommendation']}")
        
        # Show top 5 most severe vulnerabilities
        if results["vulnerabilities"]:
            print(f"\n   🔍 Top Critical/High Vulnerabilities:")
            severe_vulns = [v for v in results["vulnerabilities"] if v["severity"] in ["CRITICAL", "HIGH"]][:5]
            
            if severe_vulns:
                for i, vuln in enumerate(severe_vulns, 1):
                    severity_emoji = "🚨" if vuln["severity"] == "CRITICAL" else "⚠️"
                    fixed_info = f" (Fix: {vuln['fixed_version']})" if vuln["fixed_version"] != "Not Available" else " (No fix available)"
                    print(f"      {i}. {severity_emoji} {vuln['id']} - {vuln['package']} {vuln['installed_version']}{fixed_info}")
            else:
                print("      No critical or high vulnerabilities found! 🎉")
    
    def save_detailed_report(self, results, output_dir="vulnerability_reports"):
        """Save detailed vulnerability report."""
        if "error" in results:
            return None
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate report filename
        image_safe = results["image"].replace(":", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/scan_report_{image_safe}_{timestamp}.json"
        
        # Save detailed JSON report
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate HTML summary
        html_filename = filename.replace(".json", ".html")
        self.generate_html_report(results, html_filename)
        
        print(f"   📄 Detailed reports saved:")
        print(f"      JSON: {filename}")
        print(f"      HTML: {html_filename}")
        
        return filename
    
    def generate_html_report(self, results, filename):
        """Generate HTML vulnerability report."""
        risk = results["risk_assessment"]
        counts = results["severity_counts"]
        
        # Risk level colors
        risk_colors = {
            "CRITICAL": "#dc3545",
            "HIGH": "#fd7e14", 
            "MEDIUM": "#ffc107",
            "LOW": "#28a745"
        }
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Vulnerability Scan Report - {results['image']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
        .critical {{ border-left-color: #dc3545; }}
        .high {{ border-left-color: #fd7e14; }}
        .medium {{ border-left-color: #ffc107; }}
        .low {{ border-left-color: #28a745; }}
        .risk-card {{ background: {risk_colors.get(risk['level'], '#6c757d')}; color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
        .risk-score {{ font-size: 36px; font-weight: bold; }}
        .vuln-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .vuln-table th, .vuln-table td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        .vuln-table th {{ background: #f8f9fa; font-weight: bold; }}
        .severity-critical {{ background-color: #f8d7da; }}
        .severity-high {{ background-color: #fff3cd; }}
        .severity-medium {{ background-color: #d1ecf1; }}
        .severity-low {{ background-color: #d4edda; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Docker Image Vulnerability Report</h1>
            <h2>{results['image']}</h2>
            <p><strong>Scan Time:</strong> {results['scan_time']}</p>
            <p><strong>Scanner:</strong> Trivy</p>
        </div>
        
        <div class="summary">
            <div class="summary-card critical">
                <h3>Critical</h3>
                <div style="font-size: 32px; font-weight: bold; color: #dc3545;">{counts['CRITICAL']}</div>
            </div>
            <div class="summary-card high">
                <h3>High</h3>
                <div style="font-size: 32px; font-weight: bold; color: #fd7e14;">{counts['HIGH']}</div>
            </div>
            <div class="summary-card medium">
                <h3>Medium</h3>
                <div style="font-size: 32px; font-weight: bold; color: #ffc107;">{counts['MEDIUM']}</div>
            </div>
            <div class="summary-card low">
                <h3>Low</h3>
                <div style="font-size: 32px; font-weight: bold; color: #28a745;">{counts['LOW']}</div>
            </div>
        </div>
        
        <div class="risk-card">
            <h3>🎯 Risk Assessment</h3>
            <div style="display: flex; align-items: center; gap: 20px;">
                <div class="risk-score">{risk['score']}/100</div>
                <div>
                    <div style="font-size: 24px; font-weight: bold;">{risk['level']} RISK</div>
                    <div>{risk['recommendation']}</div>
                </div>
            </div>
        </div>
        
        <h2>📋 Vulnerability Details</h2>
        <table class="vuln-table">
            <tr>
                <th>CVE ID</th>
                <th>Severity</th>
                <th>Package</th>
                <th>Installed Version</th>
                <th>Fixed Version</th>
                <th>CVSS Score</th>
                <th>Title</th>
            </tr>
"""
        
        # Add vulnerability rows (limit to top 50 for readability)
        vulnerabilities = sorted(results["vulnerabilities"], 
                               key=lambda x: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(x["severity"], 0), 
                               reverse=True)[:50]
        
        for vuln in vulnerabilities:
            severity_class = f"severity-{vuln['severity'].lower()}"
            cvss_score = vuln.get("cvss_score", "N/A")
            html_content += f"""
            <tr class="{severity_class}">
                <td>{vuln['id']}</td>
                <td>{vuln['severity']}</td>
                <td>{vuln['package']}</td>
                <td>{vuln['installed_version']}</td>
                <td>{vuln['fixed_version']}</td>
                <td>{cvss_score}</td>
                <td>{vuln['title'][:100]}...</td>
            </tr>
"""
        
        html_content += """
        </table>
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>📈 Next Steps</h3>
            <ul>
                <li><strong>Critical/High vulnerabilities:</strong> Update packages to fixed versions immediately</li>
                <li><strong>Medium vulnerabilities:</strong> Plan updates in next maintenance window</li>
                <li><strong>Low vulnerabilities:</strong> Monitor and update when convenient</li>
                <li><strong>No fix available:</strong> Consider alternative packages or accept risk with mitigation</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, "w") as f:
            f.write(html_content)

def main():
    """Demonstrate image vulnerability scanning."""
    print("🔍 Docker Image Vulnerability Scanning Demo")
    print("=" * 60)
    
    scanner = ImageScannerDemo()
    
    # Test images to scan (including some public images with known vulnerabilities)
    test_images = [
        "python:3.11-alpine",  # Generally secure base image
        "ubuntu:20.04",        # May have some vulnerabilities
        "node:14",             # Older version, likely has vulnerabilities
        "redis:7-alpine",      # Generally secure
    ]
    
    print(f"\n🎯 Scanning {len(test_images)} test images...")
    
    for image in test_images:
        print(f"\n🔍 Scanning {image}...")
        
        # Scan the image
        results = scanner.scan_image_with_trivy(image)
        
        # Display results
        scanner.display_scan_results(results)
        
        # Save detailed report
        if "error" not in results:
            scanner.save_detailed_report(results)
    
    print(f"\n✅ Vulnerability scanning demonstration complete!")
    print(f"📄 Detailed reports saved in vulnerability_reports/ directory")
    print(f"\n💡 Integration Tips:")
    print(f"   • Add to CI/CD pipeline to scan before deployment")
    print(f"   • Set up automated alerts for critical vulnerabilities")
    print(f"   • Use policy gates to block vulnerable images")
    print(f"   • Schedule regular scans of production images")

if __name__ == "__main__":
    main()