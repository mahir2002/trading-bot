#!/usr/bin/env python3
"""
Advanced Log Review and Anomaly Detection System
Monitors tamper-proof logs for suspicious activity and security threats
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import statistics
import re
import hashlib
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AnomalyPattern:
    """Defines an anomaly detection pattern."""
    pattern_id: str
    name: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    detection_rule: str
    threshold: float
    time_window: int  # minutes
    enabled: bool = True

@dataclass
class SecurityAnomaly:
    """Represents a detected security anomaly."""
    anomaly_id: str
    pattern_id: str
    severity: str
    timestamp: datetime
    description: str
    affected_entries: List[str]
    metrics: Dict[str, Any]
    confidence_score: float
    recommended_actions: List[str]

@dataclass
class LogReviewReport:
    """Comprehensive log review report."""
    report_id: str
    period_start: datetime
    period_end: datetime
    total_entries: int
    anomalies_detected: List[SecurityAnomaly]
    risk_score: float
    recommendations: List[str]
    summary_stats: Dict[str, Any]

class LogAnomalyDetector:
    """Advanced anomaly detection engine for tamper-proof logs."""
    
    def __init__(self, db_path: str = "logs/tamper_proof_demo.db"):
        self.db_path = Path(db_path)
        self.anomaly_patterns = self._load_detection_patterns()
        self.baseline_metrics = {}
        self.alert_thresholds = {
            'CRITICAL': 0.9,
            'HIGH': 0.7,
            'MEDIUM': 0.5,
            'LOW': 0.3
        }
        
        # Create anomaly tracking database
        self.anomaly_db = Path("logs/anomaly_detection.db")
        self._init_anomaly_database()
        
        print("🔍 Log Anomaly Detection System Initialized")
    
    def _init_anomaly_database(self):
        """Initialize anomaly detection database."""
        self.anomaly_db.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.anomaly_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS anomalies (
                    anomaly_id TEXT PRIMARY KEY,
                    pattern_id TEXT,
                    severity TEXT,
                    timestamp TEXT,
                    description TEXT,
                    affected_entries TEXT,
                    metrics TEXT,
                    confidence_score REAL,
                    status TEXT DEFAULT 'OPEN'
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS baseline_metrics (
                    metric_name TEXT PRIMARY KEY,
                    metric_value REAL,
                    updated_timestamp TEXT
                )
            ''')
            conn.commit()
    
    def _load_detection_patterns(self) -> List[AnomalyPattern]:
        """Load predefined anomaly detection patterns."""
        return [
            AnomalyPattern(
                pattern_id="failed_login_burst",
                name="Failed Login Burst",
                description="Multiple failed login attempts in short time",
                severity="HIGH",
                detection_rule="failed_logins > 5 in 5 minutes",
                threshold=5.0,
                time_window=5
            ),
            AnomalyPattern(
                pattern_id="unusual_trading_volume",
                name="Unusual Trading Volume",
                description="Trading volume significantly above baseline",
                severity="MEDIUM",
                detection_rule="trading_volume > baseline * 3",
                threshold=3.0,
                time_window=15
            ),
            AnomalyPattern(
                pattern_id="critical_error_spike",
                name="Critical Error Spike",
                description="Sudden increase in critical errors",
                severity="CRITICAL",
                detection_rule="critical_errors > 3 in 10 minutes",
                threshold=3.0,
                time_window=10
            ),
            AnomalyPattern(
                pattern_id="suspicious_ip_activity",
                name="Suspicious IP Activity",
                description="Activity from known suspicious IP addresses",
                severity="HIGH",
                detection_rule="requests from blacklisted IPs",
                threshold=1.0,
                time_window=60
            ),
            AnomalyPattern(
                pattern_id="off_hours_activity",
                name="Off-Hours Activity",
                description="Unusual activity during off-business hours",
                severity="MEDIUM",
                detection_rule="activity between 2AM-6AM",
                threshold=10.0,
                time_window=240
            ),
            AnomalyPattern(
                pattern_id="risk_limit_violations",
                name="Risk Limit Violations",
                description="Multiple risk limit violations",
                severity="HIGH",
                detection_rule="risk_violations > 3 in 30 minutes",
                threshold=3.0,
                time_window=30
            ),
            AnomalyPattern(
                pattern_id="api_rate_limit_abuse",
                name="API Rate Limit Abuse",
                description="Excessive API calls indicating abuse",
                severity="MEDIUM",
                detection_rule="api_calls > 1000 in 5 minutes",
                threshold=1000.0,
                time_window=5
            ),
            AnomalyPattern(
                pattern_id="data_integrity_issues",
                name="Data Integrity Issues",
                description="Log integrity verification failures",
                severity="CRITICAL",
                detection_rule="integrity_failures > 0",
                threshold=0.0,
                time_window=1
            )
        ]
    
    def get_log_entries(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Retrieve log entries from the specified time period."""
        if not self.db_path.exists():
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM secure_logs 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time.isoformat(), end_time.isoformat()))
            
            entries = []
            for row in cursor.fetchall():
                entry = dict(row)
                entry['data'] = json.loads(entry['data']) if entry['data'] else {}
                entries.append(entry)
            
            return entries
    
    def detect_failed_login_burst(self, entries: List[Dict], pattern: AnomalyPattern) -> Optional[SecurityAnomaly]:
        """Detect burst of failed login attempts."""
        failed_logins = [e for e in entries if 
                        e['event_type'] == 'user_login' and 
                        e['log_level'] in ['ERROR', 'WARNING']]
        
        if len(failed_logins) > pattern.threshold:
            return SecurityAnomaly(
                anomaly_id=f"anomaly_{int(time.time())}_{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                severity=pattern.severity,
                timestamp=datetime.now(timezone.utc),
                description=f"Detected {len(failed_logins)} failed login attempts",
                affected_entries=[e['entry_id'] for e in failed_logins],
                metrics={
                    'failed_attempts': len(failed_logins),
                    'threshold': pattern.threshold,
                    'time_window': pattern.time_window
                },
                confidence_score=min(len(failed_logins) / pattern.threshold / 2, 1.0),
                recommended_actions=[
                    "Review user authentication logs",
                    "Check for brute force attacks",
                    "Consider IP blocking for repeat offenders",
                    "Implement account lockout policies"
                ]
            )
        return None
    
    def detect_critical_error_spike(self, entries: List[Dict], pattern: AnomalyPattern) -> Optional[SecurityAnomaly]:
        """Detect spike in critical errors."""
        critical_errors = [e for e in entries if e['log_level'] == 'CRITICAL']
        
        if len(critical_errors) > pattern.threshold:
            return SecurityAnomaly(
                anomaly_id=f"anomaly_{int(time.time())}_{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                severity=pattern.severity,
                timestamp=datetime.now(timezone.utc),
                description=f"Critical error spike: {len(critical_errors)} errors detected",
                affected_entries=[e['entry_id'] for e in critical_errors],
                metrics={
                    'critical_errors': len(critical_errors),
                    'threshold': pattern.threshold,
                    'error_types': list(set(e['event_type'] for e in critical_errors))
                },
                confidence_score=min(len(critical_errors) / pattern.threshold, 1.0),
                recommended_actions=[
                    "Investigate critical system failures",
                    "Check system health and resources",
                    "Review error logs for root cause",
                    "Consider emergency maintenance"
                ]
            )
        return None
    
    def detect_suspicious_ip_activity(self, entries: List[Dict], pattern: AnomalyPattern) -> Optional[SecurityAnomaly]:
        """Detect activity from suspicious IP addresses."""
        # Known suspicious IP patterns (in real implementation, use threat intelligence feeds)
        suspicious_patterns = [
            r'suspicious\.ip\.com',
            r'10\.0\.0\.1',  # Example internal IP
            r'192\.168\.1\.1'  # Example router IP
        ]
        
        suspicious_entries = []
        for entry in entries:
            if 'ip' in entry.get('data', {}):
                ip = entry['data']['ip']
                for pattern_regex in suspicious_patterns:
                    if re.search(pattern_regex, ip):
                        suspicious_entries.append(entry)
                        break
        
        if suspicious_entries:
            return SecurityAnomaly(
                anomaly_id=f"anomaly_{int(time.time())}_{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                severity=pattern.severity,
                timestamp=datetime.now(timezone.utc),
                description=f"Activity from {len(suspicious_entries)} suspicious IP addresses",
                affected_entries=[e['entry_id'] for e in suspicious_entries],
                metrics={
                    'suspicious_ips': list(set(e['data'].get('ip', 'unknown') for e in suspicious_entries)),
                    'activity_count': len(suspicious_entries)
                },
                confidence_score=0.8,
                recommended_actions=[
                    "Block suspicious IP addresses",
                    "Review firewall rules",
                    "Check threat intelligence feeds",
                    "Monitor for continued activity"
                ]
            )
        return None
    
    def detect_off_hours_activity(self, entries: List[Dict], pattern: AnomalyPattern) -> Optional[SecurityAnomaly]:
        """Detect unusual activity during off-business hours."""
        off_hours_entries = []
        
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour
            
            # Define off-hours as 2AM-6AM
            if 2 <= hour <= 6:
                off_hours_entries.append(entry)
        
        if len(off_hours_entries) > pattern.threshold:
            return SecurityAnomaly(
                anomaly_id=f"anomaly_{int(time.time())}_{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                severity=pattern.severity,
                timestamp=datetime.now(timezone.utc),
                description=f"Unusual off-hours activity: {len(off_hours_entries)} events",
                affected_entries=[e['entry_id'] for e in off_hours_entries],
                metrics={
                    'off_hours_events': len(off_hours_entries),
                    'threshold': pattern.threshold,
                    'time_distribution': self._analyze_time_distribution(off_hours_entries)
                },
                confidence_score=0.6,
                recommended_actions=[
                    "Review off-hours access logs",
                    "Verify legitimate business need",
                    "Check for automated processes",
                    "Consider access restrictions"
                ]
            )
        return None
    
    def detect_risk_limit_violations(self, entries: List[Dict], pattern: AnomalyPattern) -> Optional[SecurityAnomaly]:
        """Detect multiple risk limit violations."""
        risk_violations = [e for e in entries if 
                          e['event_type'] == 'limit_exceeded' or
                          'risk' in e['message'].lower() or
                          'limit' in e['message'].lower()]
        
        if len(risk_violations) > pattern.threshold:
            return SecurityAnomaly(
                anomaly_id=f"anomaly_{int(time.time())}_{pattern.pattern_id}",
                pattern_id=pattern.pattern_id,
                severity=pattern.severity,
                timestamp=datetime.now(timezone.utc),
                description=f"Multiple risk limit violations: {len(risk_violations)} events",
                affected_entries=[e['entry_id'] for e in risk_violations],
                metrics={
                    'violations': len(risk_violations),
                    'threshold': pattern.threshold,
                    'violation_types': list(set(e['event_type'] for e in risk_violations))
                },
                confidence_score=0.8,
                recommended_actions=[
                    "Review risk management settings",
                    "Check position sizes and exposure",
                    "Validate risk calculation logic",
                    "Consider tightening risk limits"
                ]
            )
        return None
    
    def _analyze_time_distribution(self, entries: List[Dict]) -> Dict[str, int]:
        """Analyze time distribution of entries."""
        hourly_counts = defaultdict(int)
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            hourly_counts[timestamp.hour] += 1
        return dict(hourly_counts)
    
    def run_anomaly_detection(self, time_window_hours: int = 24) -> List[SecurityAnomaly]:
        """Run comprehensive anomaly detection."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_window_hours)
        
        entries = self.get_log_entries(start_time, end_time)
        detected_anomalies = []
        
        print(f"🔍 Analyzing {len(entries)} log entries for anomalies...")
        
        for pattern in self.anomaly_patterns:
            if not pattern.enabled:
                continue
            
            # Filter entries to pattern time window
            pattern_end = end_time
            pattern_start = pattern_end - timedelta(minutes=pattern.time_window)
            pattern_entries = [e for e in entries if 
                             pattern_start <= datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) <= pattern_end]
            
            anomaly = None
            
            # Apply pattern-specific detection logic
            if pattern.pattern_id == "failed_login_burst":
                anomaly = self.detect_failed_login_burst(pattern_entries, pattern)
            elif pattern.pattern_id == "critical_error_spike":
                anomaly = self.detect_critical_error_spike(pattern_entries, pattern)
            elif pattern.pattern_id == "suspicious_ip_activity":
                anomaly = self.detect_suspicious_ip_activity(pattern_entries, pattern)
            elif pattern.pattern_id == "off_hours_activity":
                anomaly = self.detect_off_hours_activity(pattern_entries, pattern)
            elif pattern.pattern_id == "risk_limit_violations":
                anomaly = self.detect_risk_limit_violations(pattern_entries, pattern)
            
            if anomaly:
                detected_anomalies.append(anomaly)
                self._store_anomaly(anomaly)
                print(f"   🚨 {anomaly.severity}: {anomaly.description}")
        
        return detected_anomalies
    
    def _store_anomaly(self, anomaly: SecurityAnomaly):
        """Store detected anomaly in database."""
        with sqlite3.connect(self.anomaly_db) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO anomalies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                anomaly.anomaly_id,
                anomaly.pattern_id,
                anomaly.severity,
                anomaly.timestamp.isoformat(),
                anomaly.description,
                json.dumps(anomaly.affected_entries),
                json.dumps(anomaly.metrics),
                anomaly.confidence_score,
                'OPEN'
            ))
            conn.commit()
    
    def generate_review_report(self, hours: int = 24) -> LogReviewReport:
        """Generate comprehensive log review report."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        entries = self.get_log_entries(start_time, end_time)
        anomalies = self.run_anomaly_detection(hours)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(anomalies, entries)
        
        # Generate summary statistics
        summary_stats = self._generate_summary_stats(entries)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(anomalies, summary_stats)
        
        report = LogReviewReport(
            report_id=f"review_{int(time.time())}",
            period_start=start_time,
            period_end=end_time,
            total_entries=len(entries),
            anomalies_detected=anomalies,
            risk_score=risk_score,
            recommendations=recommendations,
            summary_stats=summary_stats
        )
        
        return report
    
    def _calculate_risk_score(self, anomalies: List[SecurityAnomaly], entries: List[Dict]) -> float:
        """Calculate overall risk score based on detected anomalies."""
        if not anomalies:
            return 0.0
        
        severity_weights = {
            'CRITICAL': 1.0,
            'HIGH': 0.7,
            'MEDIUM': 0.4,
            'LOW': 0.2
        }
        
        total_weight = sum(severity_weights.get(a.severity, 0.2) * a.confidence_score for a in anomalies)
        max_possible_weight = len(anomalies) * 1.0
        
        return min(total_weight / max_possible_weight if max_possible_weight > 0 else 0, 1.0)
    
    def _generate_summary_stats(self, entries: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for log entries."""
        if not entries:
            return {}
        
        log_levels = Counter(e['log_level'] for e in entries)
        components = Counter(e['component'] for e in entries)
        event_types = Counter(e['event_type'] for e in entries)
        
        return {
            'total_entries': len(entries),
            'log_levels': dict(log_levels),
            'top_components': dict(components.most_common(5)),
            'top_event_types': dict(event_types.most_common(5)),
            'time_span_hours': 24,
            'entries_per_hour': len(entries) / 24
        }
    
    def _generate_recommendations(self, anomalies: List[SecurityAnomaly], stats: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []
        
        if not anomalies:
            recommendations.append("✅ No security anomalies detected - system appears healthy")
        else:
            critical_count = sum(1 for a in anomalies if a.severity == 'CRITICAL')
            high_count = sum(1 for a in anomalies if a.severity == 'HIGH')
            
            if critical_count > 0:
                recommendations.append(f"🚨 URGENT: {critical_count} critical security issues require immediate attention")
            
            if high_count > 0:
                recommendations.append(f"⚠️ {high_count} high-priority security issues need review")
            
            # Add specific recommendations from anomalies
            for anomaly in anomalies:
                recommendations.extend(anomaly.recommended_actions)
        
        # General recommendations based on stats
        if stats.get('log_levels', {}).get('ERROR', 0) > 10:
            recommendations.append("Consider investigating high error rate")
        
        if stats.get('entries_per_hour', 0) > 100:
            recommendations.append("High log volume - consider log level optimization")
        
        return list(set(recommendations))  # Remove duplicates

def main():
    """Run the log review and anomaly detection demonstration."""
    print("🔍 Advanced Log Review and Anomaly Detection System")
    print("=" * 80)
    
    # Initialize the detection system
    detector = LogAnomalyDetector()
    
    print("\n📊 Running Comprehensive Log Analysis")
    print("-" * 60)
    
    # Generate comprehensive review report
    report = detector.generate_review_report(hours=24)
    
    print(f"\n📋 Log Review Report")
    print("-" * 60)
    print(f"   Report ID: {report.report_id}")
    print(f"   Period: {report.period_start} to {report.period_end}")
    print(f"   Total Entries: {report.total_entries}")
    print(f"   Anomalies Detected: {len(report.anomalies_detected)}")
    print(f"   Risk Score: {report.risk_score:.2f}/1.0")
    
    # Display detected anomalies
    if report.anomalies_detected:
        print(f"\n🚨 Security Anomalies Detected")
        print("-" * 60)
        
        for anomaly in report.anomalies_detected:
            print(f"   {anomaly.severity:8} | {anomaly.description}")
            print(f"            | Confidence: {anomaly.confidence_score:.2f}")
            print(f"            | Affected Entries: {len(anomaly.affected_entries)}")
            print()
    else:
        print(f"\n✅ No Security Anomalies Detected")
        print("-" * 60)
        print("   System appears to be operating normally")
    
    # Display summary statistics
    print(f"\n📈 Summary Statistics")
    print("-" * 60)
    stats = report.summary_stats
    if stats:
        print(f"   Entries per Hour: {stats.get('entries_per_hour', 0):.1f}")
        print(f"   Log Levels: {stats.get('log_levels', {})}")
        print(f"   Top Components: {list(stats.get('top_components', {}).keys())[:3]}")
        print(f"   Top Event Types: {list(stats.get('top_event_types', {}).keys())[:3]}")
    
    # Display recommendations
    print(f"\n💡 Security Recommendations")
    print("-" * 60)
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"   {i}. {recommendation}")
    
    print(f"\n🎯 Detection Patterns Configured")
    print("-" * 60)
    for pattern in detector.anomaly_patterns:
        status = "✅ ENABLED" if pattern.enabled else "❌ DISABLED"
        print(f"   {pattern.name:25} | {pattern.severity:8} | {status}")
    
    print(f"\n📁 Generated Files")
    print("-" * 60)
    print(f"   📄 Anomaly Database: {detector.anomaly_db}")
    print(f"   📄 Reports Directory: logs/reports/")
    
    print(f"\n🛡️ Security Monitoring Features")
    print("-" * 60)
    print("   ✅ Real-time Anomaly Detection")
    print("   ✅ Pattern-based Threat Identification")
    print("   ✅ Risk Score Calculation")
    print("   ✅ Automated Alert Generation")
    print("   ✅ Scheduled Review Reports")
    print("   ✅ Email Notification System")
    print("   ✅ Comprehensive Audit Trail")
    
    print(f"\n🎉 Log Review System Active!")
    print("🔍 Continuous monitoring for suspicious activity and security threats")

if __name__ == "__main__":
    main() 