#!/usr/bin/env python3
"""
Container Privilege Limitation Monitor
Real-time validation of container security configurations
"""

import json
import subprocess
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class PrivilegeMonitor:
    """Monitor container privilege limitations and security configurations."""
    
    def __init__(self):
        """Initialize the privilege monitor."""
        self.containers = [
            "trading-bot-secure",
            "dashboard-secure", 
            "api-secure",
            "redis-secure"
        ]
        
        # Critical security checks
        self.security_checks = {
            "privileged_mode": {
                "description": "Container must NOT run in privileged mode",
                "weight": 30,
                "critical": True
            },
            "capabilities": {
                "description": "ALL capabilities must be dropped",
                "weight": 25,
                "critical": True
            },
            "user_privileges": {
                "description": "Container must run as non-root user",
                "weight": 20,
                "critical": True
            },
            "read_only_filesystem": {
                "description": "Root filesystem should be read-only",
                "weight": 15,
                "critical": False
            },
            "security_options": {
                "description": "Security options must be properly configured",
                "weight": 10,
                "critical": False
            }
        }
    
    def check_docker_availability(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def check_privileged_mode(self, container_name: str) -> Tuple[str, Dict[str, Any]]:
        """Check if container is running in privileged mode."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format", "{{.HostConfig.Privileged}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                is_privileged = result.stdout.strip().lower() == "true"
                return ("CRITICAL_FAIL" if is_privileged else "PASS", {
                    "privileged": is_privileged,
                    "message": "⚠️ CRITICAL: Container running in privileged mode!" if is_privileged 
                              else "✅ Container not running in privileged mode",
                    "risk_level": "CRITICAL" if is_privileged else "LOW"
                })
            else:
                return ("ERROR", {
                    "message": f"❌ Failed to check privileged mode: {result.stderr.strip()}",
                    "risk_level": "UNKNOWN"
                })
                
        except subprocess.TimeoutExpired:
            return ("ERROR", {
                "message": "❌ Timeout checking privileged mode",
                "risk_level": "UNKNOWN"
            })
        except Exception as e:
            return ("ERROR", {
                "message": f"❌ Error checking privileged mode: {e}",
                "risk_level": "UNKNOWN"
            })
    
    def check_capabilities(self, container_name: str) -> Tuple[str, Dict[str, Any]]:
        """Check container Linux capabilities."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                config = json.loads(result.stdout)[0]
                host_config = config.get("HostConfig", {})
                
                cap_drop = host_config.get("CapDrop", [])
                cap_add = host_config.get("CapAdd", [])
                
                # Check if ALL capabilities are dropped
                all_dropped = "ALL" in cap_drop
                has_additions = len(cap_add) > 0
                
                issues = []
                if not all_dropped:
                    issues.append("❌ Not all capabilities dropped")
                if has_additions:
                    issues.append(f"⚠️ Additional capabilities added: {cap_add}")
                
                status = "FAIL" if issues else "PASS"
                if not all_dropped:
                    status = "CRITICAL_FAIL"
                
                return (status, {
                    "cap_drop": cap_drop,
                    "cap_add": cap_add,
                    "all_dropped": all_dropped,
                    "additional_caps": has_additions,
                    "issues": issues,
                    "message": "✅ All capabilities properly dropped" if not issues 
                              else f"⚠️ Capability issues: {'; '.join(issues)}",
                    "risk_level": "CRITICAL" if not all_dropped else ("MEDIUM" if has_additions else "LOW")
                })
            else:
                return ("ERROR", {
                    "message": f"❌ Failed to inspect container: {result.stderr.strip()}",
                    "risk_level": "UNKNOWN"
                })
                
        except Exception as e:
            return ("ERROR", {
                "message": f"❌ Error checking capabilities: {e}",
                "risk_level": "UNKNOWN"
            })
    
    def check_user_privileges(self, container_name: str) -> Tuple[str, Dict[str, Any]]:
        """Check if container is running as non-root user."""
        try:
            # Check configured user
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format", "{{.Config.User}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                configured_user = result.stdout.strip()
                
                # Try to check actual running user
                exec_result = subprocess.run(
                    ["docker", "exec", container_name, "id"],
                    capture_output=True, text=True, timeout=5
                )
                
                if exec_result.returncode == 0:
                    user_info = exec_result.stdout.strip()
                    is_root = "uid=0(root)" in user_info
                    
                    return ("CRITICAL_FAIL" if is_root else "PASS", {
                        "configured_user": configured_user,
                        "actual_user": user_info,
                        "is_root": is_root,
                        "message": "⚠️ CRITICAL: Container running as root!" if is_root 
                                  else f"✅ Container running as non-root: {user_info}",
                        "risk_level": "CRITICAL" if is_root else "LOW"
                    })
                else:
                    # Container might not be running, check configuration only
                    is_root_config = configured_user in ["", "root", "0", "0:0"]
                    
                    return ("FAIL" if is_root_config else "PASS", {
                        "configured_user": configured_user,
                        "actual_user": "Container not running",
                        "is_root": is_root_config,
                        "message": f"⚠️ Configured to run as root: {configured_user}" if is_root_config 
                                  else f"✅ Configured to run as non-root: {configured_user}",
                        "risk_level": "HIGH" if is_root_config else "LOW"
                    })
            else:
                return ("ERROR", {
                    "message": f"❌ Failed to check user configuration: {result.stderr.strip()}",
                    "risk_level": "UNKNOWN"
                })
                
        except Exception as e:
            return ("ERROR", {
                "message": f"❌ Error checking user privileges: {e}",
                "risk_level": "UNKNOWN"
            })
    
    def check_read_only_filesystem(self, container_name: str) -> Tuple[str, Dict[str, Any]]:
        """Check if container has read-only root filesystem."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format", "{{.HostConfig.ReadonlyRootfs}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                is_readonly = result.stdout.strip().lower() == "true"
                
                return ("PASS" if is_readonly else "WARN", {
                    "read_only": is_readonly,
                    "message": "✅ Root filesystem is read-only" if is_readonly 
                              else "⚠️ Root filesystem is writable (security risk)",
                    "risk_level": "LOW" if is_readonly else "MEDIUM"
                })
            else:
                return ("ERROR", {
                    "message": f"❌ Failed to check read-only filesystem: {result.stderr.strip()}",
                    "risk_level": "UNKNOWN"
                })
                
        except Exception as e:
            return ("ERROR", {
                "message": f"❌ Error checking read-only filesystem: {e}",
                "risk_level": "UNKNOWN"
            })
    
    def check_security_options(self, container_name: str) -> Tuple[str, Dict[str, Any]]:
        """Check container security options."""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_name, "--format", "{{.HostConfig.SecurityOpt}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                security_opts = result.stdout.strip()
                
                # Check for important security options
                has_no_new_privs = "no-new-privileges:true" in security_opts
                
                issues = []
                if not has_no_new_privs:
                    issues.append("❌ no-new-privileges not enabled")
                
                return ("PASS" if not issues else "WARN", {
                    "security_options": security_opts,
                    "no_new_privileges": has_no_new_privs,
                    "issues": issues,
                    "message": "✅ Security options properly configured" if not issues 
                              else f"⚠️ Security option issues: {'; '.join(issues)}",
                    "risk_level": "LOW" if not issues else "MEDIUM"
                })
            else:
                return ("ERROR", {
                    "message": f"❌ Failed to check security options: {result.stderr.strip()}",
                    "risk_level": "UNKNOWN"
                })
                
        except Exception as e:
            return ("ERROR", {
                "message": f"❌ Error checking security options: {e}",
                "risk_level": "UNKNOWN"
            })
    
    def monitor_container(self, container_name: str) -> Dict[str, Any]:
        """Monitor a single container for privilege limitations."""
        
        logger.info(f"🔍 Monitoring container: {container_name}")
        
        container_result = {
            "container_name": container_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall_status": "UNKNOWN",
            "security_score": 0,
            "critical_issues": 0,
            "total_issues": 0,
            "risk_level": "UNKNOWN"
        }
        
        # Perform all security checks
        checks = {
            "privileged_mode": self.check_privileged_mode(container_name),
            "capabilities": self.check_capabilities(container_name),
            "user_privileges": self.check_user_privileges(container_name),
            "read_only_filesystem": self.check_read_only_filesystem(container_name),
            "security_options": self.check_security_options(container_name)
        }
        
        total_score = 0
        max_score = 0
        critical_issues = 0
        total_issues = 0
        highest_risk = "LOW"
        
        for check_name, (status, details) in checks.items():
            check_config = self.security_checks[check_name]
            weight = check_config["weight"]
            is_critical = check_config["critical"]
            
            # Calculate score for this check
            if status == "PASS":
                check_score = weight
            elif status == "WARN":
                check_score = weight * 0.5
            elif status == "FAIL":
                check_score = weight * 0.2
                total_issues += 1
            elif status == "CRITICAL_FAIL":
                check_score = 0
                total_issues += 1
                if is_critical:
                    critical_issues += 1
            else:  # ERROR
                check_score = 0
                total_issues += 1
            
            total_score += check_score
            max_score += weight
            
            # Track highest risk level
            risk_level = details.get("risk_level", "LOW")
            if risk_level == "CRITICAL":
                highest_risk = "CRITICAL"
            elif risk_level == "HIGH" and highest_risk != "CRITICAL":
                highest_risk = "HIGH"
            elif risk_level == "MEDIUM" and highest_risk not in ["CRITICAL", "HIGH"]:
                highest_risk = "MEDIUM"
            
            container_result["checks"][check_name] = {
                "status": status,
                "details": details,
                "weight": weight,
                "score": check_score,
                "critical": is_critical
            }
            
            # Log individual check results
            if status == "PASS":
                logger.info(f"   ✅ {check_config['description']}")
            elif status == "WARN":
                logger.warning(f"   ⚠️ {check_config['description']}: {details.get('message', 'Warning')}")
            elif status in ["FAIL", "CRITICAL_FAIL"]:
                logger.error(f"   ❌ {check_config['description']}: {details.get('message', 'Failed')}")
            elif status == "ERROR":
                logger.error(f"   💥 {check_config['description']}: {details.get('message', 'Error')}")
        
        # Calculate overall results
        container_result["security_score"] = int((total_score / max_score) * 100) if max_score > 0 else 0
        container_result["critical_issues"] = critical_issues
        container_result["total_issues"] = total_issues
        container_result["risk_level"] = highest_risk
        
        # Determine overall status
        if critical_issues > 0:
            container_result["overall_status"] = "CRITICAL_FAIL"
            logger.error(f"   🚨 {container_name}: CRITICAL SECURITY ISSUES DETECTED!")
        elif container_result["security_score"] >= 90:
            container_result["overall_status"] = "PASS"
            logger.info(f"   ✅ {container_name}: Security checks passed ({container_result['security_score']}%)")
        elif container_result["security_score"] >= 70:
            container_result["overall_status"] = "WARN"
            logger.warning(f"   ⚠️ {container_name}: Security warnings ({container_result['security_score']}%)")
        else:
            container_result["overall_status"] = "FAIL"
            logger.error(f"   ❌ {container_name}: Security failures ({container_result['security_score']}%)")
        
        return container_result
    
    def monitor_all_containers(self) -> Dict[str, Any]:
        """Monitor all containers for privilege limitations."""
        
        logger.info("🔐 Container Privilege Limitation Monitor")
        logger.info("=" * 50)
        
        monitoring_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "containers_monitored": len(self.containers),
            "container_results": {},
            "overall_status": "UNKNOWN",
            "overall_security_score": 0,
            "total_critical_issues": 0,
            "total_issues": 0,
            "highest_risk_level": "LOW"
        }
        
        total_score = 0
        containers_checked = 0
        total_critical_issues = 0
        total_issues = 0
        highest_risk = "LOW"
        
        for container in self.containers:
            try:
                container_result = self.monitor_container(container)
                monitoring_result["container_results"][container] = container_result
                
                total_score += container_result["security_score"]
                containers_checked += 1
                total_critical_issues += container_result["critical_issues"]
                total_issues += container_result["total_issues"]
                
                # Track highest risk level
                risk_level = container_result["risk_level"]
                if risk_level == "CRITICAL":
                    highest_risk = "CRITICAL"
                elif risk_level == "HIGH" and highest_risk != "CRITICAL":
                    highest_risk = "HIGH"
                elif risk_level == "MEDIUM" and highest_risk not in ["CRITICAL", "HIGH"]:
                    highest_risk = "MEDIUM"
                    
            except Exception as e:
                logger.error(f"💥 Failed to monitor {container}: {e}")
                monitoring_result["container_results"][container] = {
                    "error": str(e),
                    "overall_status": "ERROR"
                }
        
        # Calculate overall results
        monitoring_result["overall_security_score"] = int(total_score / containers_checked) if containers_checked > 0 else 0
        monitoring_result["total_critical_issues"] = total_critical_issues
        monitoring_result["total_issues"] = total_issues
        monitoring_result["highest_risk_level"] = highest_risk
        
        # Determine overall status
        if total_critical_issues > 0:
            monitoring_result["overall_status"] = "CRITICAL_FAIL"
        elif monitoring_result["overall_security_score"] >= 90:
            monitoring_result["overall_status"] = "PASS"
        elif monitoring_result["overall_security_score"] >= 70:
            monitoring_result["overall_status"] = "WARN"
        else:
            monitoring_result["overall_status"] = "FAIL"
        
        return monitoring_result
    
    def generate_report(self, monitoring_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive privilege limitation monitoring report."""
        
        report = {
            "report_type": "privilege_limitation_monitoring",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "monitoring_result": monitoring_result,
            "summary": {
                "containers_monitored": monitoring_result["containers_monitored"],
                "overall_security_score": monitoring_result["overall_security_score"],
                "overall_status": monitoring_result["overall_status"],
                "total_critical_issues": monitoring_result["total_critical_issues"],
                "total_issues": monitoring_result["total_issues"],
                "highest_risk_level": monitoring_result["highest_risk_level"]
            },
            "recommendations": [],
            "next_actions": []
        }
        
        # Generate recommendations
        if monitoring_result["total_critical_issues"] > 0:
            report["recommendations"].append("🚨 IMMEDIATE ACTION REQUIRED: Critical security issues detected")
            report["next_actions"].append("Stop containers with critical issues immediately")
            report["next_actions"].append("Review and fix privileged mode and capability configurations")
        
        if monitoring_result["overall_security_score"] < 70:
            report["recommendations"].append("⚠️ Security configuration needs improvement")
            report["next_actions"].append("Review Docker Compose security settings")
        
        if monitoring_result["overall_status"] == "PASS":
            report["recommendations"].append("✅ Continue regular monitoring to maintain security")
            report["next_actions"].append("Schedule weekly privilege limitation checks")
        
        # Add specific recommendations based on common issues
        report["recommendations"].extend([
            "Ensure all containers use 'privileged: false'",
            "Drop ALL capabilities with 'cap_drop: [ALL]'",
            "Use non-root users (1001:1001 for apps, 999:999 for Redis)",
            "Enable read-only root filesystem where possible",
            "Configure security options: no-new-privileges:true"
        ])
        
        return report

def main():
    """Main monitoring function."""
    monitor = PrivilegeMonitor()
    
    # Check if Docker is available
    if not monitor.check_docker_availability():
        logger.error("❌ Docker not available. Please ensure Docker is installed and running.")
        sys.exit(1)
    
    try:
        # Monitor all containers
        monitoring_result = monitor.monitor_all_containers()
        
        # Generate comprehensive report
        report = monitor.generate_report(monitoring_result)
        
        # Save detailed report
        report_file = f"privilege_monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 PRIVILEGE LIMITATION MONITORING SUMMARY")
        logger.info("=" * 50)
        logger.info(f"🎯 Overall Security Score: {monitoring_result['overall_security_score']}/100")
        logger.info(f"🔍 Containers Monitored: {monitoring_result['containers_monitored']}")
        logger.info(f"🚨 Critical Issues: {monitoring_result['total_critical_issues']}")
        logger.info(f"⚠️ Total Issues: {monitoring_result['total_issues']}")
        logger.info(f"📈 Risk Level: {monitoring_result['highest_risk_level']}")
        logger.info(f"📋 Report Saved: {report_file}")
        
        # Final status
        if monitoring_result["overall_status"] == "CRITICAL_FAIL":
            logger.error("\n🚨 CRITICAL SECURITY ISSUES DETECTED - IMMEDIATE ACTION REQUIRED!")
            sys.exit(2)
        elif monitoring_result["overall_status"] == "FAIL":
            logger.error("\n❌ Security failures detected - review required")
            sys.exit(1)
        elif monitoring_result["overall_status"] == "WARN":
            logger.warning("\n⚠️ Security warnings - improvements recommended")
        else:
            logger.info("\n✅ All privilege limitation checks passed!")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Monitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n💥 Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()