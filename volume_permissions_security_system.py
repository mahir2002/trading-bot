#!/usr/bin/env python3
"""
Comprehensive Docker Volume Permissions Security System
Advanced volume permission management and security enforcement
"""

import os
import stat
import json
import yaml
import logging
import subprocess
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union, Tuple
from enum import Enum
from pathlib import Path
import pwd
import grp
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VolumeType(Enum):
    """Volume types for security classification."""
    DATA = "data"                    # Application data volumes
    CONFIG = "config"                # Configuration files
    LOGS = "logs"                    # Log file volumes
    SECRETS = "secrets"              # Sensitive data (keys, certificates)
    CACHE = "cache"                  # Temporary/cache volumes
    BACKUP = "backup"                # Backup storage volumes
    SHARED = "shared"                # Shared between containers

class SecurityLevel(Enum):
    """Security levels for volume permissions."""
    MAXIMUM = "maximum"              # Ultra-secure (700/600 permissions)
    HIGH = "high"                    # High security (750/640 permissions)
    STANDARD = "standard"            # Standard security (755/644 permissions)
    PERMISSIVE = "permissive"        # Permissive (777/666 permissions)

class PermissionIssue(Enum):
    """Types of permission issues."""
    WORLD_WRITABLE = "world_writable"
    WORLD_READABLE = "world_readable"
    GROUP_WRITABLE = "group_writable"
    EXECUTABLE_DATA = "executable_data"
    MISSING_OWNER = "missing_owner"
    WRONG_OWNER = "wrong_owner"
    SETUID_BIT = "setuid_bit"
    STICKY_BIT_MISSING = "sticky_bit_missing"

@dataclass
class VolumePermission:
    """Volume permission configuration."""
    path: str
    volume_type: VolumeType
    security_level: SecurityLevel
    owner_uid: int
    owner_gid: int
    directory_mode: int
    file_mode: int
    enforce_owner: bool = True
    recursive: bool = True
    exclude_patterns: List[str] = field(default_factory=list)

@dataclass
class PermissionViolation:
    """Permission violation details."""
    path: str
    issue_type: PermissionIssue
    current_mode: int
    expected_mode: int
    current_owner: Tuple[int, int]
    expected_owner: Tuple[int, int]
    severity: str
    description: str
    recommendation: str
    auto_fixable: bool

@dataclass
class VolumeSecurityScan:
    """Volume security scan results."""
    volume_path: str
    scan_time: datetime
    total_files: int
    total_directories: int
    violations: List[PermissionViolation]
    security_score: float
    risk_level: str
    scan_duration: float

class VolumePermissionsSecuritySystem:
    """
    Comprehensive Docker volume permissions security system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the volume permissions security system."""
        self.config = self._load_config(config_path)
        self.volume_policies = self._load_volume_policies()
        self.scan_results: Dict[str, VolumeSecurityScan] = {}
        
        # Create security directories
        os.makedirs("volume_security/reports", exist_ok=True)
        os.makedirs("volume_security/policies", exist_ok=True)
        os.makedirs("volume_security/fixes", exist_ok=True)
        
        logger.info("✅ Volume Permissions Security System initialized")
        logger.info(f"   Loaded {len(self.volume_policies)} volume policies")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load system configuration."""
        default_config = {
            "security_levels": {
                "maximum": {
                    "directory_mode": 0o700,
                    "file_mode": 0o600,
                    "description": "Ultra-secure - Owner only access"
                },
                "high": {
                    "directory_mode": 0o750,
                    "file_mode": 0o640,
                    "description": "High security - Owner and group read"
                },
                "standard": {
                    "directory_mode": 0o755,
                    "file_mode": 0o644,
                    "description": "Standard security - World readable"
                },
                "permissive": {
                    "directory_mode": 0o777,
                    "file_mode": 0o666,
                    "description": "Permissive - World writable (NOT RECOMMENDED)"
                }
            },
            "volume_types": {
                "secrets": {
                    "default_security": "maximum",
                    "enforce_owner": True,
                    "allow_group_access": False,
                    "scan_frequency": "daily"
                },
                "config": {
                    "default_security": "high",
                    "enforce_owner": True,
                    "allow_group_access": True,
                    "scan_frequency": "weekly"
                },
                "data": {
                    "default_security": "standard",
                    "enforce_owner": True,
                    "allow_group_access": True,
                    "scan_frequency": "weekly"
                },
                "logs": {
                    "default_security": "high",
                    "enforce_owner": True,
                    "allow_group_access": True,
                    "scan_frequency": "daily"
                }
            },
            "scanning": {
                "max_scan_depth": 10,
                "skip_system_dirs": True,
                "follow_symlinks": False,
                "parallel_scanning": True
            },
            "remediation": {
                "auto_fix_enabled": False,
                "backup_before_fix": True,
                "fix_verification": True,
                "rollback_on_failure": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                return {**default_config, **user_config}
        
        return default_config
    
    def _load_volume_policies(self) -> Dict[str, VolumePermission]:
        """Load volume security policies."""
        policies = {}
        
        # Default AI Trading Bot volume policies
        trading_bot_policies = {
            "/app/data": VolumePermission(
                path="/app/data",
                volume_type=VolumeType.DATA,
                security_level=SecurityLevel.HIGH,
                owner_uid=1001,  # Non-root trading bot user
                owner_gid=1001,
                directory_mode=0o750,
                file_mode=0o640,
                exclude_patterns=["*.tmp", "*.log"]
            ),
            "/app/config": VolumePermission(
                path="/app/config",
                volume_type=VolumeType.CONFIG,
                security_level=SecurityLevel.HIGH,
                owner_uid=1001,
                owner_gid=1001,
                directory_mode=0o750,
                file_mode=0o640
            ),
            "/app/secrets": VolumePermission(
                path="/app/secrets",
                volume_type=VolumeType.SECRETS,
                security_level=SecurityLevel.MAXIMUM,
                owner_uid=1001,
                owner_gid=1001,
                directory_mode=0o700,
                file_mode=0o600
            ),
            "/app/logs": VolumePermission(
                path="/app/logs",
                volume_type=VolumeType.LOGS,
                security_level=SecurityLevel.HIGH,
                owner_uid=1001,
                owner_gid=1001,
                directory_mode=0o750,
                file_mode=0o640
            ),
            "/app/backups": VolumePermission(
                path="/app/backups",
                volume_type=VolumeType.BACKUP,
                security_level=SecurityLevel.HIGH,
                owner_uid=1001,
                owner_gid=1001,
                directory_mode=0o750,
                file_mode=0o640
            )
        }
        
        policies.update(trading_bot_policies)
        return policies
    
    async def scan_volume_permissions(self, volume_path: str, 
                                    policy: Optional[VolumePermission] = None) -> VolumeSecurityScan:
        """Perform comprehensive volume permission security scan."""
        scan_start = datetime.now(timezone.utc)
        
        logger.info(f"🔍 Scanning volume permissions: {volume_path}")
        
        if not os.path.exists(volume_path):
            raise ValueError(f"Volume path does not exist: {volume_path}")
        
        # Use default policy if none provided
        if policy is None:
            policy = self._get_default_policy(volume_path)
        
        violations = []
        total_files = 0
        total_directories = 0
        
        # Scan directory tree
        for root, dirs, files in os.walk(volume_path):
            # Check if we should skip this directory
            if self._should_skip_directory(root):
                continue
            
            # Scan directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                total_directories += 1
                
                try:
                    violation = await self._check_path_permissions(dir_path, policy, is_directory=True)
                    if violation:
                        violations.append(violation)
                except (OSError, PermissionError) as e:
                    logger.warning(f"Cannot scan directory {dir_path}: {e}")
            
            # Scan files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                total_files += 1
                
                # Skip excluded patterns
                if self._matches_exclude_pattern(file_name, policy.exclude_patterns):
                    continue
                
                try:
                    violation = await self._check_path_permissions(file_path, policy, is_directory=False)
                    if violation:
                        violations.append(violation)
                except (OSError, PermissionError) as e:
                    logger.warning(f"Cannot scan file {file_path}: {e}")
        
        # Calculate security score
        security_score = self._calculate_security_score(violations, total_files + total_directories)
        risk_level = self._determine_risk_level(security_score, violations)
        
        scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
        
        scan_result = VolumeSecurityScan(
            volume_path=volume_path,
            scan_time=scan_start,
            total_files=total_files,
            total_directories=total_directories,
            violations=violations,
            security_score=security_score,
            risk_level=risk_level,
            scan_duration=scan_duration
        )
        
        # Store scan results
        self.scan_results[volume_path] = scan_result
        
        logger.info(f"✅ Volume scan completed:")
        logger.info(f"   Files: {total_files}, Directories: {total_directories}")
        logger.info(f"   Violations: {len(violations)}")
        logger.info(f"   Security Score: {security_score:.1f}/100")
        logger.info(f"   Risk Level: {risk_level}")
        
        return scan_result
    
    async def _check_path_permissions(self, path: str, policy: VolumePermission, 
                                    is_directory: bool) -> Optional[PermissionViolation]:
        """Check permissions for a specific path."""
        try:
            stat_info = os.stat(path)
            current_mode = stat_info.st_mode & 0o777
            current_owner = (stat_info.st_uid, stat_info.st_gid)
            
            expected_mode = policy.directory_mode if is_directory else policy.file_mode
            expected_owner = (policy.owner_uid, policy.owner_gid)
            
            # Check for various permission issues
            violations = []
            
            # World writable check
            if current_mode & 0o002:
                violations.append(PermissionIssue.WORLD_WRITABLE)
            
            # World readable check for sensitive volumes
            if policy.volume_type == VolumeType.SECRETS and current_mode & 0o004:
                violations.append(PermissionIssue.WORLD_READABLE)
            
            # Group writable check for maximum security
            if policy.security_level == SecurityLevel.MAXIMUM and current_mode & 0o020:
                violations.append(PermissionIssue.GROUP_WRITABLE)
            
            # Executable data files check
            if not is_directory and current_mode & 0o111 and not path.endswith(('.sh', '.py', '.pl')):
                violations.append(PermissionIssue.EXECUTABLE_DATA)
            
            # Owner check
            if policy.enforce_owner and current_owner != expected_owner:
                violations.append(PermissionIssue.WRONG_OWNER)
            
            # SETUID/SETGID bit check
            if stat_info.st_mode & (stat.S_ISUID | stat.S_ISGID):
                violations.append(PermissionIssue.SETUID_BIT)
            
            # Return the most severe violation
            if violations:
                most_severe = violations[0]  # Prioritize by enum order
                return PermissionViolation(
                    path=path,
                    issue_type=most_severe,
                    current_mode=current_mode,
                    expected_mode=expected_mode,
                    current_owner=current_owner,
                    expected_owner=expected_owner,
                    severity=self._get_violation_severity(most_severe, policy),
                    description=self._get_violation_description(most_severe, path, current_mode),
                    recommendation=self._get_violation_recommendation(most_severe, expected_mode, expected_owner),
                    auto_fixable=self._is_auto_fixable(most_severe)
                )
            
            return None
            
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot check permissions for {path}: {e}")
            return None
    
    def _get_default_policy(self, volume_path: str) -> VolumePermission:
        """Get default policy for a volume path."""
        # Try to match existing policies
        for policy_path, policy in self.volume_policies.items():
            if volume_path.startswith(policy_path):
                return policy
        
        # Return default policy
        return VolumePermission(
            path=volume_path,
            volume_type=VolumeType.DATA,
            security_level=SecurityLevel.STANDARD,
            owner_uid=1001,
            owner_gid=1001,
            directory_mode=0o755,
            file_mode=0o644
        )
    
    def _should_skip_directory(self, path: str) -> bool:
        """Check if directory should be skipped during scanning."""
        skip_dirs = {'/proc', '/sys', '/dev', '/tmp', '/.git', '/node_modules'}
        return any(path.startswith(skip_dir) for skip_dir in skip_dirs)
    
    def _matches_exclude_pattern(self, filename: str, patterns: List[str]) -> bool:
        """Check if filename matches any exclude pattern."""
        import fnmatch
        return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)
    
    def _calculate_security_score(self, violations: List[PermissionViolation], total_items: int) -> float:
        """Calculate overall security score (0-100)."""
        if total_items == 0:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {
            "CRITICAL": 10,
            "HIGH": 7,
            "MEDIUM": 4,
            "LOW": 1
        }
        
        total_penalty = sum(severity_weights.get(v.severity, 1) for v in violations)
        max_possible_penalty = total_items * 10  # All items with critical violations
        
        # Calculate score (higher is better)
        score = max(0, 100 - (total_penalty / max_possible_penalty * 100))
        return round(score, 1)
    
    def _determine_risk_level(self, security_score: float, violations: List[PermissionViolation]) -> str:
        """Determine overall risk level."""
        critical_violations = sum(1 for v in violations if v.severity == "CRITICAL")
        high_violations = sum(1 for v in violations if v.severity == "HIGH")
        
        if critical_violations > 0 or security_score < 40:
            return "CRITICAL"
        elif high_violations > 5 or security_score < 60:
            return "HIGH"
        elif security_score < 80:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_violation_severity(self, issue: PermissionIssue, policy: VolumePermission) -> str:
        """Get severity level for a permission violation."""
        if policy.volume_type == VolumeType.SECRETS:
            # Secrets are always critical
            if issue in [PermissionIssue.WORLD_WRITABLE, PermissionIssue.WORLD_READABLE, 
                        PermissionIssue.GROUP_WRITABLE]:
                return "CRITICAL"
        
        severity_map = {
            PermissionIssue.WORLD_WRITABLE: "CRITICAL",
            PermissionIssue.SETUID_BIT: "CRITICAL",
            PermissionIssue.WORLD_READABLE: "HIGH" if policy.volume_type == VolumeType.SECRETS else "MEDIUM",
            PermissionIssue.GROUP_WRITABLE: "HIGH" if policy.security_level == SecurityLevel.MAXIMUM else "MEDIUM",
            PermissionIssue.WRONG_OWNER: "HIGH" if policy.enforce_owner else "MEDIUM",
            PermissionIssue.EXECUTABLE_DATA: "MEDIUM",
            PermissionIssue.MISSING_OWNER: "LOW",
            PermissionIssue.STICKY_BIT_MISSING: "LOW"
        }
        
        return severity_map.get(issue, "MEDIUM")
    
    def _get_violation_description(self, issue: PermissionIssue, path: str, current_mode: int) -> str:
        """Get human-readable description of the violation."""
        descriptions = {
            PermissionIssue.WORLD_WRITABLE: f"File/directory is world-writable (mode: {oct(current_mode)})",
            PermissionIssue.WORLD_READABLE: f"Sensitive file is world-readable (mode: {oct(current_mode)})",
            PermissionIssue.GROUP_WRITABLE: f"File/directory is group-writable in maximum security context (mode: {oct(current_mode)})",
            PermissionIssue.EXECUTABLE_DATA: f"Data file has execute permissions (mode: {oct(current_mode)})",
            PermissionIssue.WRONG_OWNER: f"File/directory has incorrect owner/group",
            PermissionIssue.SETUID_BIT: f"File has SETUID/SETGID bit set (mode: {oct(current_mode)})",
            PermissionIssue.MISSING_OWNER: f"File/directory owner cannot be determined",
            PermissionIssue.STICKY_BIT_MISSING: f"Shared directory missing sticky bit (mode: {oct(current_mode)})"
        }
        
        return descriptions.get(issue, f"Permission issue detected in {path}")
    
    def _get_violation_recommendation(self, issue: PermissionIssue, expected_mode: int, 
                                    expected_owner: Tuple[int, int]) -> str:
        """Get recommendation for fixing the violation."""
        uid, gid = expected_owner
        
        recommendations = {
            PermissionIssue.WORLD_WRITABLE: f"Remove world-write permissions: chmod {oct(expected_mode)[-3:]}",
            PermissionIssue.WORLD_READABLE: f"Remove world-read permissions: chmod {oct(expected_mode)[-3:]}",
            PermissionIssue.GROUP_WRITABLE: f"Remove group-write permissions: chmod {oct(expected_mode)[-3:]}",
            PermissionIssue.EXECUTABLE_DATA: f"Remove execute permissions: chmod {oct(expected_mode)[-3:]}",
            PermissionIssue.WRONG_OWNER: f"Change ownership: chown {uid}:{gid}",
            PermissionIssue.SETUID_BIT: f"Remove SETUID/SETGID bits: chmod {oct(expected_mode)[-3:]}",
            PermissionIssue.MISSING_OWNER: f"Set correct ownership: chown {uid}:{gid}",
            PermissionIssue.STICKY_BIT_MISSING: f"Add sticky bit: chmod +t"
        }
        
        return recommendations.get(issue, "Review and correct permissions manually")
    
    def _is_auto_fixable(self, issue: PermissionIssue) -> bool:
        """Check if violation can be automatically fixed."""
        auto_fixable = {
            PermissionIssue.WORLD_WRITABLE: True,
            PermissionIssue.WORLD_READABLE: True,
            PermissionIssue.GROUP_WRITABLE: True,
            PermissionIssue.EXECUTABLE_DATA: True,
            PermissionIssue.WRONG_OWNER: True,
            PermissionIssue.SETUID_BIT: True,
            PermissionIssue.STICKY_BIT_MISSING: True,
            PermissionIssue.MISSING_OWNER: False  # Requires manual intervention
        }
        
        return auto_fixable.get(issue, False)
    
    async def fix_volume_permissions(self, volume_path: str, 
                                   dry_run: bool = True) -> Dict[str, Any]:
        """Fix volume permissions based on scan results."""
        logger.info(f"🔧 {'Simulating' if dry_run else 'Applying'} permission fixes for: {volume_path}")
        
        scan_result = self.scan_results.get(volume_path)
        if not scan_result:
            raise ValueError(f"No scan results found for {volume_path}. Run scan first.")
        
        fix_results = {
            "volume_path": volume_path,
            "dry_run": dry_run,
            "fixes_applied": [],
            "fixes_failed": [],
            "backup_created": False,
            "rollback_available": False
        }
        
        # Create backup if not dry run
        if not dry_run and self.config["remediation"]["backup_before_fix"]:
            backup_path = await self._create_permissions_backup(volume_path)
            fix_results["backup_created"] = True
            fix_results["backup_path"] = backup_path
        
        # Apply fixes for auto-fixable violations
        for violation in scan_result.violations:
            if not violation.auto_fixable:
                continue
            
            try:
                fix_command = self._generate_fix_command(violation)
                
                if dry_run:
                    fix_results["fixes_applied"].append({
                        "path": violation.path,
                        "issue": violation.issue_type.value,
                        "command": fix_command,
                        "simulated": True
                    })
                else:
                    # Apply the fix
                    await self._apply_permission_fix(violation)
                    fix_results["fixes_applied"].append({
                        "path": violation.path,
                        "issue": violation.issue_type.value,
                        "command": fix_command,
                        "applied": True
                    })
                    
            except Exception as e:
                fix_results["fixes_failed"].append({
                    "path": violation.path,
                    "issue": violation.issue_type.value,
                    "error": str(e)
                })
                logger.error(f"Failed to fix {violation.path}: {e}")
        
        # Verify fixes if not dry run
        if not dry_run and self.config["remediation"]["fix_verification"]:
            verification_result = await self._verify_fixes(volume_path)
            fix_results["verification"] = verification_result
        
        logger.info(f"✅ Permission fix {'simulation' if dry_run else 'application'} completed:")
        logger.info(f"   Fixes applied: {len(fix_results['fixes_applied'])}")
        logger.info(f"   Fixes failed: {len(fix_results['fixes_failed'])}")
        
        return fix_results
    
    def _generate_fix_command(self, violation: PermissionViolation) -> str:
        """Generate shell command to fix the violation."""
        if violation.issue_type == PermissionIssue.WRONG_OWNER:
            uid, gid = violation.expected_owner
            return f"chown {uid}:{gid} '{violation.path}'"
        else:
            mode = oct(violation.expected_mode)[-3:]
            return f"chmod {mode} '{violation.path}'"
    
    async def _apply_permission_fix(self, violation: PermissionViolation):
        """Apply permission fix for a violation."""
        if violation.issue_type == PermissionIssue.WRONG_OWNER:
            uid, gid = violation.expected_owner
            os.chown(violation.path, uid, gid)
        else:
            os.chmod(violation.path, violation.expected_mode)
    
    async def _create_permissions_backup(self, volume_path: str) -> str:
        """Create backup of current permissions."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"volume_security/fixes/permissions_backup_{timestamp}.json"
        
        permissions_data = {}
        
        for root, dirs, files in os.walk(volume_path):
            for item in dirs + files:
                item_path = os.path.join(root, item)
                try:
                    stat_info = os.stat(item_path)
                    permissions_data[item_path] = {
                        "mode": stat_info.st_mode & 0o777,
                        "uid": stat_info.st_uid,
                        "gid": stat_info.st_gid
                    }
                except (OSError, PermissionError):
                    continue
        
        with open(backup_file, 'w') as f:
            json.dump(permissions_data, f, indent=2)
        
        logger.info(f"📄 Permissions backup created: {backup_file}")
        return backup_file
    
    async def _verify_fixes(self, volume_path: str) -> Dict[str, Any]:
        """Verify that fixes were applied correctly."""
        logger.info(f"🔍 Verifying permission fixes for: {volume_path}")
        
        # Re-scan the volume
        policy = self._get_default_policy(volume_path)
        new_scan = await self.scan_volume_permissions(volume_path, policy)
        
        # Compare with previous scan
        old_violations = len(self.scan_results[volume_path].violations)
        new_violations = len(new_scan.violations)
        
        verification = {
            "success": new_violations < old_violations,
            "violations_before": old_violations,
            "violations_after": new_violations,
            "improvement": old_violations - new_violations,
            "security_score_before": self.scan_results[volume_path].security_score,
            "security_score_after": new_scan.security_score
        }
        
        logger.info(f"✅ Verification completed:")
        logger.info(f"   Violations reduced: {verification['improvement']}")
        logger.info(f"   Security score improved: {verification['security_score_after'] - verification['security_score_before']:.1f}")
        
        return verification
    
    def generate_volume_security_report(self, volume_path: str) -> Dict[str, Any]:
        """Generate comprehensive volume security report."""
        scan_result = self.scan_results.get(volume_path)
        if not scan_result:
            raise ValueError(f"No scan results found for {volume_path}")
        
        # Group violations by severity
        violations_by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        for violation in scan_result.violations:
            violations_by_severity[violation.severity].append(violation)
        
        # Generate summary statistics
        summary = {
            "volume_path": volume_path,
            "scan_time": scan_result.scan_time.isoformat(),
            "security_score": scan_result.security_score,
            "risk_level": scan_result.risk_level,
            "total_items": scan_result.total_files + scan_result.total_directories,
            "total_violations": len(scan_result.violations),
            "violations_by_severity": {
                severity: len(violations) 
                for severity, violations in violations_by_severity.items()
            },
            "auto_fixable_violations": sum(1 for v in scan_result.violations if v.auto_fixable),
            "scan_duration": scan_result.scan_duration
        }
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(scan_result)
        
        return {
            "summary": summary,
            "violations": [
                {
                    "path": v.path,
                    "issue_type": v.issue_type.value,
                    "severity": v.severity,
                    "current_mode": oct(v.current_mode),
                    "expected_mode": oct(v.expected_mode),
                    "description": v.description,
                    "recommendation": v.recommendation,
                    "auto_fixable": v.auto_fixable
                }
                for v in scan_result.violations
            ],
            "recommendations": recommendations
        }
    
    def _generate_security_recommendations(self, scan_result: VolumeSecurityScan) -> List[str]:
        """Generate actionable security recommendations."""
        recommendations = []
        
        critical_violations = sum(1 for v in scan_result.violations if v.severity == "CRITICAL")
        high_violations = sum(1 for v in scan_result.violations if v.severity == "HIGH")
        auto_fixable = sum(1 for v in scan_result.violations if v.auto_fixable)
        
        if critical_violations > 0:
            recommendations.append(f"🚨 URGENT: Fix {critical_violations} critical permission violations immediately")
        
        if high_violations > 0:
            recommendations.append(f"⚠️ HIGH PRIORITY: Address {high_violations} high-severity permission issues")
        
        if auto_fixable > 0:
            recommendations.append(f"🔧 AUTOMATION: {auto_fixable} violations can be automatically fixed")
        
        if scan_result.security_score < 60:
            recommendations.append("📈 IMPROVEMENT: Consider implementing stricter security policies")
        
        recommendations.extend([
            "🔍 MONITORING: Schedule regular permission scans",
            "📋 POLICY: Review and update volume security policies",
            "🎓 TRAINING: Educate team on secure volume practices"
        ])
        
        return recommendations
    
    def generate_docker_compose_volumes(self) -> Dict[str, Any]:
        """Generate secure Docker Compose volume configurations."""
        secure_volumes = {}
        
        for path, policy in self.volume_policies.items():
            volume_name = path.replace("/", "_").replace("app_", "")
            
            secure_volumes[volume_name] = {
                "driver": "local",
                "driver_opts": {
                    "type": "none",
                    "o": f"bind,uid={policy.owner_uid},gid={policy.owner_gid}",
                    "device": f"./volumes{path}"
                }
            }
        
        # Generate service volume mounts
        volume_mounts = []
        for path, policy in self.volume_policies.items():
            volume_name = path.replace("/", "_").replace("app_", "")
            volume_mounts.append(f"{volume_name}:{path}:rw")
        
        return {
            "volumes": secure_volumes,
            "service_volumes": volume_mounts,
            "security_notes": [
                "All volumes use specific UID/GID for security",
                "Volumes are mounted with explicit ownership",
                "No privileged or root access required",
                "Permissions are enforced at mount time"
            ]
        }
    
    def save_security_reports(self, volume_path: str):
        """Save comprehensive security reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        volume_safe = volume_path.replace("/", "_").replace(":", "_")
        
        # Generate report
        report = self.generate_volume_security_report(volume_path)
        
        # Save JSON report
        json_file = f"volume_security/reports/volume_security_{volume_safe}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save HTML report
        html_file = f"volume_security/reports/volume_security_{volume_safe}_{timestamp}.html"
        self._generate_html_report(report, html_file)
        
        logger.info(f"📄 Security reports saved:")
        logger.info(f"   JSON: {json_file}")
        logger.info(f"   HTML: {html_file}")
        
        return {"json": json_file, "html": html_file}
    
    def _generate_html_report(self, report: Dict[str, Any], filename: str):
        """Generate HTML security report."""
        summary = report["summary"]
        violations = report["violations"]
        recommendations = report["recommendations"]
        
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
    <title>Volume Security Report - {summary['volume_path']}</title>
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
        .risk-card {{ background: {risk_colors.get(summary['risk_level'], '#6c757d')}; color: white; padding: 25px; border-radius: 10px; margin: 20px 0; }}
        .violations-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .violations-table th, .violations-table td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        .violations-table th {{ background: #f8f9fa; font-weight: bold; }}
        .severity-critical {{ background-color: #f8d7da; }}
        .severity-high {{ background-color: #fff3cd; }}
        .severity-medium {{ background-color: #d1ecf1; }}
        .severity-low {{ background-color: #d4edda; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .recommendations ul {{ margin: 0; padding-left: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Volume Security Report</h1>
            <h2>{summary['volume_path']}</h2>
            <p><strong>Scan Time:</strong> {summary['scan_time']}</p>
            <p><strong>Security Score:</strong> {summary['security_score']}/100</p>
        </div>
        
        <div class="summary">
            <div class="summary-card critical">
                <h3>Critical</h3>
                <div style="font-size: 32px; font-weight: bold; color: #dc3545;">{summary['violations_by_severity']['CRITICAL']}</div>
            </div>
            <div class="summary-card high">
                <h3>High</h3>
                <div style="font-size: 32px; font-weight: bold; color: #fd7e14;">{summary['violations_by_severity']['HIGH']}</div>
            </div>
            <div class="summary-card medium">
                <h3>Medium</h3>
                <div style="font-size: 32px; font-weight: bold; color: #ffc107;">{summary['violations_by_severity']['MEDIUM']}</div>
            </div>
            <div class="summary-card low">
                <h3>Low</h3>
                <div style="font-size: 32px; font-weight: bold; color: #28a745;">{summary['violations_by_severity']['LOW']}</div>
            </div>
        </div>
        
        <div class="risk-card">
            <h3>🎯 Risk Assessment</h3>
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="font-size: 36px; font-weight: bold;">{summary['security_score']}/100</div>
                <div>
                    <div style="font-size: 24px; font-weight: bold;">{summary['risk_level']} RISK</div>
                    <div>Auto-fixable violations: {summary['auto_fixable_violations']}</div>
                </div>
            </div>
        </div>
        
        <h2>🚨 Permission Violations</h2>
        <table class="violations-table">
            <tr>
                <th>Path</th>
                <th>Issue Type</th>
                <th>Severity</th>
                <th>Current Mode</th>
                <th>Expected Mode</th>
                <th>Auto-Fixable</th>
                <th>Recommendation</th>
            </tr>
"""
        
        # Add violation rows
        for violation in violations[:50]:  # Limit to 50 for readability
            severity_class = f"severity-{violation['severity'].lower()}"
            auto_fix = "✅ Yes" if violation['auto_fixable'] else "❌ No"
            
            html_content += f"""
            <tr class="{severity_class}">
                <td>{violation['path'][:60]}...</td>
                <td>{violation['issue_type']}</td>
                <td>{violation['severity']}</td>
                <td>{violation['current_mode']}</td>
                <td>{violation['expected_mode']}</td>
                <td>{auto_fix}</td>
                <td>{violation['recommendation'][:80]}...</td>
            </tr>
"""
        
        html_content += f"""
        </table>
        
        <div class="recommendations">
            <h3>📈 Security Recommendations</h3>
            <ul>
"""
        
        for recommendation in recommendations:
            html_content += f"                <li>{recommendation}</li>\n"
        
        html_content += """
            </ul>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>🔧 Next Steps</h3>
            <ol>
                <li><strong>Critical/High violations:</strong> Fix immediately to prevent security breaches</li>
                <li><strong>Auto-fixable violations:</strong> Use automated fixing tools for efficiency</li>
                <li><strong>Manual review:</strong> Investigate violations that require manual intervention</li>
                <li><strong>Policy updates:</strong> Review and update security policies as needed</li>
                <li><strong>Regular monitoring:</strong> Schedule periodic security scans</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html_content)

async def main():
    """Demonstrate volume permissions security system."""
    print("🔒 Docker Volume Permissions Security System")
    print("=" * 70)
    
    # Initialize system
    security_system = VolumePermissionsSecuritySystem()
    
    # Create test volume directories for demonstration
    test_volumes = [
        "./test_volumes/data",
        "./test_volumes/config", 
        "./test_volumes/secrets",
        "./test_volumes/logs"
    ]
    
    print(f"\n🎯 Setting up test volumes...")
    
    # Create test volumes with various permission issues
    for volume_path in test_volumes:
        os.makedirs(volume_path, exist_ok=True)
        
        # Create some test files with different permission issues
        test_files = [
            ("config.json", 0o644),
            ("secret.key", 0o777),  # World writable - security issue!
            ("data.db", 0o755),     # Executable data file - issue!
            ("log.txt", 0o666)     # World writable - issue!
        ]
        
        for filename, mode in test_files:
            file_path = os.path.join(volume_path, filename)
            with open(file_path, 'w') as f:
                f.write(f"Test content for {filename}")
            os.chmod(file_path, mode)
    
    print(f"✅ Test volumes created with intentional permission issues")
    
    # Scan each volume
    for volume_path in test_volumes:
        print(f"\n🔍 Scanning {volume_path}...")
        
        try:
            scan_result = await security_system.scan_volume_permissions(volume_path)
            
            # Save security reports
            security_system.save_security_reports(volume_path)
            
            # Show summary
            print(f"   Security Score: {scan_result.security_score}/100")
            print(f"   Risk Level: {scan_result.risk_level}")
            print(f"   Violations: {len(scan_result.violations)}")
            
            # Demonstrate fix simulation
            if scan_result.violations:
                print(f"   🔧 Simulating fixes...")
                fix_result = await security_system.fix_volume_permissions(volume_path, dry_run=True)
                print(f"   Fixes available: {len(fix_result['fixes_applied'])}")
                
        except Exception as e:
            print(f"   ❌ Error scanning {volume_path}: {e}")
    
    # Generate secure Docker Compose configuration
    print(f"\n🐳 Generating secure Docker Compose configuration...")
    compose_config = security_system.generate_docker_compose_volumes()
    
    with open("volume_security/secure_docker_compose_volumes.yml", 'w') as f:
        yaml.dump(compose_config, f, indent=2)
    
    print(f"✅ Secure Docker Compose volumes configuration saved")
    print(f"\n📄 Security reports saved in volume_security/reports/")
    print(f"🔧 Review reports and apply recommended fixes")

if __name__ == "__main__":
    asyncio.run(main())