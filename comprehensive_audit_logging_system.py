#!/usr/bin/env python3
"""
Comprehensive Audit Logging System
Maintains detailed audit trails of all significant actions for AI Trading Bot
"""

import os
import sys
import json
import time
import hashlib
import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
import traceback
from pathlib import Path
import gzip
import csv
from contextlib import contextmanager
import uuid
import inspect

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events."""
    # Trading Events
    TRADE_ORDER_PLACED = "trade_order_placed"
    TRADE_ORDER_EXECUTED = "trade_order_executed"
    TRADE_ORDER_CANCELLED = "trade_order_cancelled"
    TRADE_ORDER_FAILED = "trade_order_failed"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    PORTFOLIO_REBALANCED = "portfolio_rebalanced"
    
    # Financial Events
    DEPOSIT_INITIATED = "deposit_initiated"
    DEPOSIT_COMPLETED = "deposit_completed"
    WITHDRAWAL_INITIATED = "withdrawal_initiated"
    WITHDRAWAL_COMPLETED = "withdrawal_completed"
    BALANCE_CHANGED = "balance_changed"
    FEE_CHARGED = "fee_charged"
    
    # Configuration Events
    CONFIG_CHANGED = "config_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_UPDATED = "api_key_updated"
    API_KEY_DELETED = "api_key_deleted"
    STRATEGY_CHANGED = "strategy_changed"
    PARAMETER_CHANGED = "parameter_changed"
    
    # Access Control Events
    USER_LOGIN_SUCCESS = "user_login_success"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_LOGOUT = "user_logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    
    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_DETECTED = "data_breach_detected"
    
    # API Events
    API_REQUEST_MADE = "api_request_made"
    API_REQUEST_FAILED = "api_request_failed"
    API_RATE_LIMITED = "api_rate_limited"
    API_KEY_COMPROMISED = "api_key_compromised"

class AuditSeverity(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Comprehensive audit event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: AuditEventType = AuditEventType.SYSTEM_ERROR
    severity: AuditSeverity = AuditSeverity.MEDIUM
    
    # Actor Information
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Resource Information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    
    # Event Details
    action: str = ""
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Financial Information
    amount: Optional[float] = None
    currency: Optional[str] = None
    balance_before: Optional[float] = None
    balance_after: Optional[float] = None
    
    # Technical Information
    system_component: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Verification
    checksum: Optional[str] = field(default=None)
    
    def __post_init__(self):
        """Generate checksum for integrity verification."""
        if not self.checksum:
            self.checksum = self._generate_checksum()
    
    def _generate_checksum(self) -> str:
        """Generate SHA-256 checksum for event integrity."""
        event_data = {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'action': self.action,
            'details': json.dumps(self.details, sort_keys=True)
        }
        
        content = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify event integrity using checksum."""
        original_checksum = self.checksum
        self.checksum = None
        calculated_checksum = self._generate_checksum()
        self.checksum = original_checksum
        return original_checksum == calculated_checksum

class AuditLogger:
    """Comprehensive audit logging system."""
    
    def __init__(self, db_path: str = "audit_logs/audit.db", 
                 log_dir: str = "audit_logs",
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 retention_days: int = 365):
        """Initialize the audit logging system."""
        self.db_path = db_path
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.retention_days = retention_days
        
        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance tracking
        self.events_logged = 0
        self.start_time = datetime.now(timezone.utc)
        
        # Current session tracking
        self.session_id = str(uuid.uuid4())
        
        logger.info("✅ Comprehensive Audit Logging System initialized")
        logger.info(f"   Database: {db_path}")
        logger.info(f"   Log Directory: {log_dir}")
        logger.info(f"   Session ID: {self.session_id}")
        
        # Log system startup
        self.log_system_event(
            AuditEventType.SYSTEM_STARTUP,
            "Audit logging system initialized",
            {
                'session_id': self.session_id,
                'database_path': db_path,
                'log_directory': str(log_dir)
            }
        )
    
    def _init_database(self):
        """Initialize SQLite database for audit logs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    resource_type TEXT,
                    resource_id TEXT,
                    exchange TEXT,
                    symbol TEXT,
                    action TEXT NOT NULL,
                    description TEXT,
                    details TEXT,
                    amount REAL,
                    currency TEXT,
                    balance_before REAL,
                    balance_after REAL,
                    system_component TEXT,
                    function_name TEXT,
                    line_number INTEGER,
                    error_code TEXT,
                    stack_trace TEXT,
                    checksum TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_exchange ON audit_events(exchange)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_severity ON audit_events(severity)')
            
            conn.commit()
    
    def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event to database and files."""
        try:
            with self._lock:
                # Store in database
                self._store_in_database(event)
                
                # Store in JSON log file
                self._store_in_file(event)
                
                # Update statistics
                self.events_logged += 1
                
                # Perform maintenance if needed
                if self.events_logged % 1000 == 0:
                    self._perform_maintenance()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {e}")
            return False
    
    def _store_in_database(self, event: AuditEvent):
        """Store audit event in SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO audit_events (
                    event_id, timestamp, event_type, severity,
                    user_id, session_id, ip_address, user_agent,
                    resource_type, resource_id, exchange, symbol,
                    action, description, details,
                    amount, currency, balance_before, balance_after,
                    system_component, function_name, line_number,
                    error_code, stack_trace, checksum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, event.timestamp.isoformat(), event.event_type.value, event.severity.value,
                event.user_id, event.session_id, event.ip_address, event.user_agent,
                event.resource_type, event.resource_id, event.exchange, event.symbol,
                event.action, event.description, json.dumps(event.details),
                event.amount, event.currency, event.balance_before, event.balance_after,
                event.system_component, event.function_name, event.line_number,
                event.error_code, event.stack_trace, event.checksum
            ))
            conn.commit()
    
    def _store_in_file(self, event: AuditEvent):
        """Store audit event in JSON log file."""
        date_str = event.timestamp.strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{date_str}.json"
        
        # Convert event to dictionary
        event_dict = asdict(event)
        event_dict['timestamp'] = event.timestamp.isoformat()
        event_dict['event_type'] = event.event_type.value
        event_dict['severity'] = event.severity.value
        
        # Append to file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_dict) + '\n')
    
    def _perform_maintenance(self):
        """Perform periodic maintenance tasks."""
        try:
            # Rotate large log files
            self._rotate_large_files()
            
            # Clean old log files
            self._cleanup_old_files()
            
            logger.debug(f"📊 Audit maintenance completed: {self.events_logged} events logged")
            
        except Exception as e:
            logger.error(f"❌ Audit maintenance error: {e}")
    
    def _rotate_large_files(self):
        """Rotate log files that exceed size limit."""
        for log_file in self.log_dir.glob("audit_*.json"):
            if log_file.stat().st_size > self.max_file_size:
                # Compress and archive
                timestamp = datetime.now().strftime("%H%M%S")
                archived_name = f"{log_file.stem}_{timestamp}.json.gz"
                archived_path = self.log_dir / archived_name
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(archived_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                # Clear original file
                log_file.unlink()
                
                logger.info(f"📦 Archived large log file: {archived_name}")
    
    def _cleanup_old_files(self):
        """Remove log files older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for log_file in self.log_dir.glob("audit_*.json*"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                logger.info(f"🗑️ Removed old log file: {log_file.name}")
    
    # Specialized logging methods for different event types
    
    def log_trade_event(self, event_type: AuditEventType, symbol: str, side: str,
                       quantity: float, price: float, exchange: str,
                       order_id: str = None, user_id: str = None,
                       details: Dict[str, Any] = None) -> bool:
        """Log trading-related events."""
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.HIGH if event_type == AuditEventType.TRADE_ORDER_FAILED else AuditSeverity.MEDIUM,
            user_id=user_id,
            session_id=self.session_id,
            resource_type="order",
            resource_id=order_id,
            exchange=exchange,
            symbol=symbol,
            action=f"{side.upper()} {quantity} {symbol} at {price}",
            description=f"Trade {event_type.value} for {symbol}",
            details={
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_id': order_id,
                **(details or {})
            },
            amount=quantity * price,
            currency=symbol.split('/')[-1] if '/' in symbol else 'USD',
            system_component='trading_engine'
        )
        
        return self.log_event(event)
    
    def log_financial_event(self, event_type: AuditEventType, amount: float,
                           currency: str, balance_before: float = None,
                           balance_after: float = None, transaction_id: str = None,
                           exchange: str = None, user_id: str = None,
                           details: Dict[str, Any] = None) -> bool:
        """Log financial events (deposits, withdrawals, balance changes)."""
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            session_id=self.session_id,
            resource_type="financial_transaction",
            resource_id=transaction_id,
            exchange=exchange,
            action=f"{event_type.value.replace('_', ' ').title()} {amount} {currency}",
            description=f"Financial transaction: {event_type.value}",
            details={
                'transaction_id': transaction_id,
                'exchange': exchange,
                **(details or {})
            },
            amount=amount,
            currency=currency,
            balance_before=balance_before,
            balance_after=balance_after,
            system_component='financial_manager'
        )
        
        return self.log_event(event)
    
    def log_config_change(self, config_type: str, old_value: Any, new_value: Any,
                         user_id: str = None, details: Dict[str, Any] = None) -> bool:
        """Log configuration changes."""
        event = AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGED,
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            session_id=self.session_id,
            resource_type="configuration",
            resource_id=config_type,
            action=f"Changed {config_type}",
            description=f"Configuration change: {config_type}",
            details={
                'config_type': config_type,
                'old_value': str(old_value),
                'new_value': str(new_value),
                **(details or {})
            },
            system_component='config_manager'
        )
        
        return self.log_event(event)
    
    def log_access_event(self, event_type: AuditEventType, user_id: str,
                        ip_address: str = None, user_agent: str = None,
                        resource: str = None, success: bool = True,
                        details: Dict[str, Any] = None) -> bool:
        """Log access control events."""
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM,
            user_id=user_id,
            session_id=self.session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="access_control",
            resource_id=resource,
            action=f"{'Successful' if success else 'Failed'} {event_type.value.replace('_', ' ')}",
            description=f"Access event: {event_type.value}",
            details={
                'success': success,
                'resource': resource,
                **(details or {})
            },
            system_component='access_control'
        )
        
        return self.log_event(event)
    
    def log_security_event(self, event_type: AuditEventType, description: str,
                          severity: AuditSeverity = AuditSeverity.HIGH,
                          user_id: str = None, ip_address: str = None,
                          details: Dict[str, Any] = None) -> bool:
        """Log security-related events."""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            session_id=self.session_id,
            ip_address=ip_address,
            resource_type="security",
            action=event_type.value.replace('_', ' ').title(),
            description=description,
            details=details or {},
            system_component='security_monitor'
        )
        
        return self.log_event(event)
    
    def log_system_event(self, event_type: AuditEventType, description: str,
                        details: Dict[str, Any] = None,
                        severity: AuditSeverity = AuditSeverity.LOW) -> bool:
        """Log system-related events."""
        # Get caller information
        caller_frame = inspect.currentframe().f_back
        function_name = caller_frame.f_code.co_name
        line_number = caller_frame.f_lineno
        
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            session_id=self.session_id,
            resource_type="system",
            action=event_type.value.replace('_', ' ').title(),
            description=description,
            details=details or {},
            system_component='system',
            function_name=function_name,
            line_number=line_number
        )
        
        return self.log_event(event)
    
    def log_error_event(self, error: Exception, context: str = "",
                       severity: AuditSeverity = AuditSeverity.HIGH,
                       user_id: str = None) -> bool:
        """Log error events with full stack trace."""
        stack_trace = traceback.format_exc()
        
        event = AuditEvent(
            event_type=AuditEventType.SYSTEM_ERROR,
            severity=severity,
            user_id=user_id,
            session_id=self.session_id,
            resource_type="error",
            action="System Error Occurred",
            description=f"Error in {context}: {str(error)}",
            details={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context
            },
            error_code=type(error).__name__,
            stack_trace=stack_trace,
            system_component='error_handler'
        )
        
        return self.log_event(event)
    
    def log_api_event(self, event_type: AuditEventType, endpoint: str,
                     method: str, status_code: int = None,
                     response_time: float = None, user_id: str = None,
                     details: Dict[str, Any] = None) -> bool:
        """Log API-related events."""
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.MEDIUM if status_code and status_code < 400 else AuditSeverity.HIGH,
            user_id=user_id,
            session_id=self.session_id,
            resource_type="api",
            resource_id=endpoint,
            action=f"{method} {endpoint}",
            description=f"API {event_type.value}: {method} {endpoint}",
            details={
                'method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'response_time_ms': response_time,
                **(details or {})
            },
            system_component='api_handler'
        )
        
        return self.log_event(event)
    
    # Query and analysis methods
    
    def query_events(self, start_date: datetime = None, end_date: datetime = None,
                    event_types: List[AuditEventType] = None,
                    user_id: str = None, exchange: str = None,
                    severity: AuditSeverity = None,
                    limit: int = 1000) -> List[Dict[str, Any]]:
        """Query audit events with filters."""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
            
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
            
        if event_types:
            placeholders = ','.join(['?' for _ in event_types])
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])
            
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if exchange:
            query += " AND exchange = ?"
            params.append(exchange)
            
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_event_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get audit event statistics."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT exchange) as exchanges_used,
                    event_type,
                    severity,
                    COUNT(*) as count
                FROM audit_events 
                WHERE timestamp >= ?
                GROUP BY event_type, severity
                ORDER BY count DESC
            ''', (start_date.isoformat(),))
            
            results = cursor.fetchall()
            
        # Aggregate statistics
        stats = {
            'period_days': days,
            'total_events': sum(row[5] for row in results),
            'unique_users': len(set(row[1] for row in results if row[1])),
            'exchanges_used': len(set(row[2] for row in results if row[2])),
            'events_by_type': {},
            'events_by_severity': {},
            'top_event_types': []
        }
        
        # Group by event type and severity
        for row in results:
            event_type, severity, count = row[3], row[4], row[5]
            
            if event_type not in stats['events_by_type']:
                stats['events_by_type'][event_type] = 0
            stats['events_by_type'][event_type] += count
            
            if severity not in stats['events_by_severity']:
                stats['events_by_severity'][severity] = 0
            stats['events_by_severity'][severity] += count
        
        # Top event types
        stats['top_event_types'] = sorted(
            stats['events_by_type'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats
    
    def export_events_csv(self, filename: str, start_date: datetime = None,
                         end_date: datetime = None, filters: Dict[str, Any] = None) -> bool:
        """Export audit events to CSV file."""
        try:
            events = self.query_events(
                start_date=start_date,
                end_date=end_date,
                **(filters or {})
            )
            
            if not events:
                logger.warning("No events found for export")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = events[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for event in events:
                    writer.writerow(event)
            
            logger.info(f"📄 Exported {len(events)} events to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export events to CSV: {e}")
            return False
    
    def verify_log_integrity(self, start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """Verify integrity of audit logs using checksums."""
        events = self.query_events(start_date=start_date, end_date=end_date)
        
        total_events = len(events)
        valid_events = 0
        corrupted_events = []
        
        for event_data in events:
            # Reconstruct AuditEvent object
            event = AuditEvent(
                event_id=event_data['event_id'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                event_type=AuditEventType(event_data['event_type']),
                severity=AuditSeverity(event_data['severity']),
                user_id=event_data['user_id'],
                session_id=event_data['session_id'],
                ip_address=event_data['ip_address'],
                user_agent=event_data['user_agent'],
                resource_type=event_data['resource_type'],
                resource_id=event_data['resource_id'],
                exchange=event_data['exchange'],
                symbol=event_data['symbol'],
                action=event_data['action'],
                description=event_data['description'],
                details=json.loads(event_data['details'] or '{}'),
                amount=event_data['amount'],
                currency=event_data['currency'],
                balance_before=event_data['balance_before'],
                balance_after=event_data['balance_after'],
                system_component=event_data['system_component'],
                function_name=event_data['function_name'],
                line_number=event_data['line_number'],
                error_code=event_data['error_code'],
                stack_trace=event_data['stack_trace'],
                checksum=event_data['checksum']
            )
            
            if event.verify_integrity():
                valid_events += 1
            else:
                corrupted_events.append(event_data['event_id'])
        
        integrity_result = {
            'total_events': total_events,
            'valid_events': valid_events,
            'corrupted_events': len(corrupted_events),
            'integrity_percentage': (valid_events / total_events * 100) if total_events > 0 else 0,
            'corrupted_event_ids': corrupted_events
        }
        
        return integrity_result
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get comprehensive audit system summary."""
        uptime = datetime.now(timezone.utc) - self.start_time
        
        stats = self.get_event_statistics(days=7)  # Last 7 days
        integrity = self.verify_log_integrity(
            start_date=datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        return {
            'system_info': {
                'session_id': self.session_id,
                'uptime_seconds': int(uptime.total_seconds()),
                'events_logged': self.events_logged,
                'database_path': self.db_path,
                'log_directory': str(self.log_dir)
            },
            'recent_statistics': stats,
            'integrity_check': integrity,
            'health_status': 'HEALTHY' if integrity['integrity_percentage'] > 99 else 'WARNING'
        }

# Context manager for audit logging
@contextmanager
def audit_context(audit_logger: AuditLogger, user_id: str = None,
                 ip_address: str = None, user_agent: str = None):
    """Context manager for automatic audit logging."""
    start_time = time.time()
    
    try:
        yield
        
        # Log successful operation
        duration = time.time() - start_time
        audit_logger.log_system_event(
            AuditEventType.SYSTEM_WARNING,
            "Operation completed successfully",
            {
                'duration_seconds': duration,
                'user_id': user_id,
                'ip_address': ip_address
            }
        )
        
    except Exception as e:
        # Log error
        audit_logger.log_error_event(e, "Context operation failed", user_id=user_id)
        raise

def main():
    """Demonstrate comprehensive audit logging system."""
    print("📋 Comprehensive Audit Logging System - AI Trading Bot")
    print("=" * 80)
    
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    print(f"\n📊 Demonstrating comprehensive audit logging capabilities...")
    
    # Demonstrate different types of audit events
    
    # 1. Trading Events
    print(f"\n1. 🔄 Trading Events:")
    audit_logger.log_trade_event(
        AuditEventType.TRADE_ORDER_PLACED,
        symbol="BTC/USDT",
        side="BUY",
        quantity=0.001,
        price=45000.00,
        exchange="Binance",
        order_id="order_123456",
        user_id="user_001",
        details={'strategy': 'momentum', 'confidence': 0.85}
    )
    
    audit_logger.log_trade_event(
        AuditEventType.TRADE_ORDER_EXECUTED,
        symbol="BTC/USDT",
        side="BUY",
        quantity=0.001,
        price=45050.00,
        exchange="Binance",
        order_id="order_123456",
        user_id="user_001"
    )
    print("   ✅ Logged trade order placement and execution")
    
    # 2. Financial Events
    print(f"\n2. 💰 Financial Events:")
    audit_logger.log_financial_event(
        AuditEventType.DEPOSIT_COMPLETED,
        amount=1000.00,
        currency="USDT",
        balance_before=5000.00,
        balance_after=6000.00,
        transaction_id="dep_789012",
        exchange="Binance",
        user_id="user_001"
    )
    print("   ✅ Logged deposit completion")
    
    # 3. Configuration Changes
    print(f"\n3. ⚙️ Configuration Changes:")
    audit_logger.log_config_change(
        config_type="trading_strategy",
        old_value="conservative",
        new_value="aggressive",
        user_id="admin_001",
        details={'reason': 'market_conditions_changed'}
    )
    print("   ✅ Logged configuration change")
    
    # 4. Access Events
    print(f"\n4. 🔐 Access Control Events:")
    audit_logger.log_access_event(
        AuditEventType.USER_LOGIN_SUCCESS,
        user_id="user_001",
        ip_address="192.168.1.100",
        user_agent="TradingBot/1.0",
        resource="dashboard",
        success=True
    )
    
    audit_logger.log_access_event(
        AuditEventType.USER_LOGIN_FAILED,
        user_id="unknown_user",
        ip_address="suspicious.ip.com",
        user_agent="AttackBot/2.0",
        resource="admin_panel",
        success=False,
        details={'attempt_count': 5, 'blocked': True}
    )
    print("   ✅ Logged successful and failed login attempts")
    
    # 5. Security Events
    print(f"\n5. 🛡️ Security Events:")
    audit_logger.log_security_event(
        AuditEventType.SUSPICIOUS_ACTIVITY,
        "Multiple failed login attempts from same IP",
        severity=AuditSeverity.HIGH,
        ip_address="suspicious.ip.com",
        details={
            'failed_attempts': 10,
            'time_window': '5 minutes',
            'action_taken': 'IP blocked'
        }
    )
    print("   ✅ Logged security incident")
    
    # 6. System Events
    print(f"\n6. 🖥️ System Events:")
    audit_logger.log_system_event(
        AuditEventType.SERVICE_STARTED,
        "Trading bot service started",
        details={'version': '2.1.0', 'config_file': 'production.yaml'}
    )
    print("   ✅ Logged system event")
    
    # 7. API Events
    print(f"\n7. 🌐 API Events:")
    audit_logger.log_api_event(
        AuditEventType.API_REQUEST_MADE,
        endpoint="/api/v1/orders",
        method="POST",
        status_code=201,
        response_time=150.5,
        user_id="user_001",
        details={'order_type': 'market', 'symbol': 'BTC/USDT'}
    )
    print("   ✅ Logged API request")
    
    # 8. Error Events
    print(f"\n8. ❌ Error Events:")
    try:
        # Simulate an error
        raise ValueError("Invalid trading parameter")
    except Exception as e:
        audit_logger.log_error_event(e, "Parameter validation", user_id="user_001")
    print("   ✅ Logged error event with stack trace")
    
    # Generate statistics and reports
    print(f"\n📊 Generating audit statistics...")
    stats = audit_logger.get_event_statistics(days=1)
    
    print(f"✅ Audit Statistics (Last 24 hours):")
    print(f"   Total Events: {stats['total_events']}")
    print(f"   Unique Users: {stats['unique_users']}")
    print(f"   Top Event Types:")
    for event_type, count in stats['top_event_types'][:5]:
        print(f"     • {event_type}: {count}")
    
    # Verify integrity
    print(f"\n🔍 Verifying log integrity...")
    integrity = audit_logger.verify_log_integrity()
    print(f"✅ Integrity Check:")
    print(f"   Total Events: {integrity['total_events']}")
    print(f"   Valid Events: {integrity['valid_events']}")
    print(f"   Integrity: {integrity['integrity_percentage']:.1f}%")
    
    # Export to CSV
    print(f"\n📄 Exporting audit logs...")
    csv_filename = f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    if audit_logger.export_events_csv(csv_filename):
        print(f"✅ Exported audit logs to {csv_filename}")
    
    # System summary
    print(f"\n📋 System Summary:")
    summary = audit_logger.get_audit_summary()
    print(f"   Health Status: {summary['health_status']}")
    print(f"   Events Logged: {summary['system_info']['events_logged']}")
    print(f"   Uptime: {summary['system_info']['uptime_seconds']} seconds")
    
    print(f"\n🎉 Comprehensive Audit Logging System demonstration completed!")
    print(f"📄 All significant actions have been logged with full traceability")

if __name__ == "__main__":
    main() 