#!/usr/bin/env python3
"""
Advanced Tamper-Proof Logging System
Ensures log integrity through multiple security mechanisms to prevent malicious modification
"""

import os
import json
import time
import hashlib
import hmac
import sqlite3
import threading
import asyncio
import aiofiles
import aiohttp
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
import traceback
from pathlib import Path
import uuid
import inspect
import secrets
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrityLevel(Enum):
    """Integrity protection levels."""
    BASIC = "basic"           # SHA-256 checksums only
    ENHANCED = "enhanced"     # Checksums + HMAC signing
    MAXIMUM = "maximum"       # Full cryptographic signing + blockchain chaining
    PARANOID = "paranoid"     # All protections + remote backup + real-time verification

class LogEvent(Enum):
    """Log event types for integrity monitoring."""
    LOG_CREATED = "log_created"
    LOG_VERIFIED = "log_verified"
    LOG_CORRUPTED = "log_corrupted"
    LOG_BACKED_UP = "log_backed_up"
    INTEGRITY_CHECK = "integrity_check"
    TAMPER_DETECTED = "tamper_detected"

@dataclass
class IntegrityMetadata:
    """Metadata for log integrity verification."""
    sequence_number: int
    timestamp: datetime
    checksum: str
    hmac_signature: Optional[str] = None
    digital_signature: Optional[str] = None
    previous_hash: Optional[str] = None
    merkle_root: Optional[str] = None
    backup_locations: List[str] = field(default_factory=list)
    verification_count: int = 0
    last_verified: Optional[datetime] = None

@dataclass
class TamperProofLogEntry:
    """Enhanced log entry with comprehensive integrity protection."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = 0
    log_level: str = "INFO"
    source_component: str = ""
    event_type: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Integrity fields
    content_hash: str = ""
    hmac_signature: str = ""
    digital_signature: str = ""
    previous_hash: str = ""
    chain_hash: str = ""
    
    # Metadata
    integrity_metadata: IntegrityMetadata = field(default_factory=lambda: IntegrityMetadata(0, datetime.now(timezone.utc), ""))
    
    def __post_init__(self):
        """Initialize integrity fields after creation."""
        if not self.content_hash:
            self.content_hash = self._calculate_content_hash()

    def _calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of log entry content."""
        content = {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'sequence_number': self.sequence_number,
            'log_level': self.log_level,
            'source_component': self.source_component,
            'event_type': self.event_type,
            'message': self.message,
            'data': json.dumps(self.data, sort_keys=True)
        }
        
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify the integrity of this log entry."""
        calculated_hash = self._calculate_content_hash()
        return calculated_hash == self.content_hash

class CryptographicSigner:
    """Handles cryptographic signing for log entries."""
    
    def __init__(self, key_size: int = 2048):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        self.public_key = self.private_key.public_key()
        
    def sign_data(self, data: str) -> str:
        """Sign data with private key."""
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verify signature with public key."""
        try:
            signature_bytes = base64.b64decode(signature.encode())
            self.public_key.verify(
                signature_bytes,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

class BlockchainChain:
    """Implements blockchain-like chaining for log entries."""
    
    def __init__(self):
        self.chain: List[TamperProofLogEntry] = []
        self.current_hash = "0" * 64  # Genesis hash
        
    def add_entry(self, entry: TamperProofLogEntry) -> str:
        """Add entry to the chain with proper linking."""
        entry.sequence_number = len(self.chain)
        entry.previous_hash = self.current_hash
        
        # Calculate chain hash
        chain_data = f"{entry.previous_hash}{entry.content_hash}{entry.sequence_number}"
        entry.chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        
        self.chain.append(entry)
        self.current_hash = entry.chain_hash
        
        return entry.chain_hash
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire chain."""
        if not self.chain:
            return {'valid': True, 'corrupted_entries': [], 'total_entries': 0}
        
        corrupted_entries = []
        previous_hash = "0" * 64
        
        for i, entry in enumerate(self.chain):
            # Verify sequence number
            if entry.sequence_number != i:
                corrupted_entries.append(i)
                continue
                
            # Verify previous hash link
            if entry.previous_hash != previous_hash:
                corrupted_entries.append(i)
                continue
                
            # Verify chain hash
            expected_chain_hash = hashlib.sha256(
                f"{entry.previous_hash}{entry.content_hash}{entry.sequence_number}".encode()
            ).hexdigest()
            
            if entry.chain_hash != expected_chain_hash:
                corrupted_entries.append(i)
                continue
                
            # Verify content integrity
            if not entry.verify_integrity():
                corrupted_entries.append(i)
                
            previous_hash = entry.chain_hash
        
        return {
            'valid': len(corrupted_entries) == 0,
            'corrupted_entries': corrupted_entries,
            'total_entries': len(self.chain),
            'integrity_percentage': ((len(self.chain) - len(corrupted_entries)) / len(self.chain) * 100) if self.chain else 100
        }

class RemoteBackupManager:
    """Manages remote backup of logs for additional integrity protection."""
    
    def __init__(self, backup_endpoints: List[str] = None):
        self.backup_endpoints = backup_endpoints or []
        self.backup_key = Fernet.generate_key()
        self.cipher = Fernet(self.backup_key)
        
    async def backup_entry(self, entry: TamperProofLogEntry) -> List[str]:
        """Backup log entry to remote locations."""
        successful_backups = []
        
        # Encrypt the entry before backup
        encrypted_data = self.cipher.encrypt(
            json.dumps(asdict(entry), default=str).encode()
        )
        
        for endpoint in self.backup_endpoints:
            try:
                success = await self._send_to_endpoint(endpoint, encrypted_data, entry.entry_id)
                if success:
                    successful_backups.append(endpoint)
            except Exception as e:
                logger.warning(f"Failed to backup to {endpoint}: {e}")
        
        return successful_backups
    
    async def _send_to_endpoint(self, endpoint: str, data: bytes, entry_id: str) -> bool:
        """Send encrypted data to backup endpoint."""
        # Simulate remote backup (in production, this would be actual HTTP/API calls)
        try:
            # For demo purposes, save to local backup directory
            backup_dir = Path("backup_logs") / endpoint.replace("://", "_").replace("/", "_")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"{entry_id}.encrypted"
            async with aiofiles.open(backup_file, 'wb') as f:
                await f.write(data)
            
            return True
        except Exception:
            return False
    
    async def verify_backup_integrity(self, entry_id: str) -> Dict[str, bool]:
        """Verify integrity of backed up entries."""
        verification_results = {}
        
        for endpoint in self.backup_endpoints:
            try:
                backup_dir = Path("backup_logs") / endpoint.replace("://", "_").replace("/", "_")
                backup_file = backup_dir / f"{entry_id}.encrypted"
                
                if backup_file.exists():
                    async with aiofiles.open(backup_file, 'rb') as f:
                        encrypted_data = await f.read()
                    
                    # Decrypt and verify
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    entry_data = json.loads(decrypted_data.decode())
                    
                    # Reconstruct entry and verify
                    verification_results[endpoint] = True  # Simplified verification
                else:
                    verification_results[endpoint] = False
                    
            except Exception as e:
                logger.error(f"Backup verification failed for {endpoint}: {e}")
                verification_results[endpoint] = False
        
        return verification_results

class TamperProofLogger:
    """Advanced tamper-proof logging system with multiple integrity protections."""
    
    def __init__(self, 
                 log_file: str = "tamper_proof.log",
                 db_file: str = "tamper_proof.db",
                 integrity_level: IntegrityLevel = IntegrityLevel.MAXIMUM,
                 backup_endpoints: List[str] = None,
                 hmac_key: str = None):
        
        self.log_file = Path(log_file)
        self.db_file = Path(db_file)
        self.integrity_level = integrity_level
        
        # Create directories
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.signer = CryptographicSigner() if integrity_level in [IntegrityLevel.MAXIMUM, IntegrityLevel.PARANOID] else None
        self.chain = BlockchainChain()
        self.backup_manager = RemoteBackupManager(backup_endpoints) if backup_endpoints else None
        
        # HMAC key for signing
        self.hmac_key = hmac_key or secrets.token_hex(32)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Statistics
        self.entries_logged = 0
        self.integrity_checks = 0
        self.tamper_attempts_detected = 0
        
        # Initialize database
        self._init_database()
        
        # Start background integrity monitoring if paranoid mode
        if integrity_level == IntegrityLevel.PARANOID:
            self._start_integrity_monitoring()
        
        logger.info(f"✅ Tamper-Proof Logging System initialized")
        logger.info(f"   Integrity Level: {integrity_level.value}")
        logger.info(f"   Log File: {log_file}")
        logger.info(f"   Database: {db_file}")
        
    def _init_database(self):
        """Initialize SQLite database for log storage."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tamper_proof_logs (
                    entry_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    log_level TEXT NOT NULL,
                    source_component TEXT,
                    event_type TEXT,
                    message TEXT NOT NULL,
                    data TEXT,
                    content_hash TEXT NOT NULL,
                    hmac_signature TEXT,
                    digital_signature TEXT,
                    previous_hash TEXT,
                    chain_hash TEXT NOT NULL,
                    backup_locations TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON tamper_proof_logs(timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sequence ON tamper_proof_logs(sequence_number)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_type ON tamper_proof_logs(event_type)
            ''')
            
            conn.commit()
    
    async def log_entry(self, 
                       log_level: str,
                       source_component: str,
                       event_type: str,
                       message: str,
                       data: Dict[str, Any] = None) -> str:
        """Log an entry with comprehensive integrity protection."""
        
        with self._lock:
            # Create log entry
            entry = TamperProofLogEntry(
                log_level=log_level,
                source_component=source_component,
                event_type=event_type,
                message=message,
                data=data or {}
            )
            
            # Apply integrity protections based on level
            await self._apply_integrity_protections(entry)
            
            # Add to blockchain chain
            chain_hash = self.chain.add_entry(entry)
            
            # Store in database
            await self._store_in_database(entry)
            
            # Write to log file
            await self._write_to_file(entry)
            
            # Backup if configured
            backup_locations = []
            if self.backup_manager and self.integrity_level in [IntegrityLevel.MAXIMUM, IntegrityLevel.PARANOID]:
                backup_locations = await self.backup_manager.backup_entry(entry)
                entry.integrity_metadata.backup_locations = backup_locations
            
            self.entries_logged += 1
            
            # Log the logging event itself (meta-logging)
            if event_type != LogEvent.LOG_CREATED.value:  # Prevent infinite recursion
                await self._log_integrity_event(
                    LogEvent.LOG_CREATED,
                    f"Log entry created: {entry.entry_id}",
                    {
                        'entry_id': entry.entry_id,
                        'integrity_level': self.integrity_level.value,
                        'backup_locations': backup_locations,
                        'chain_position': entry.sequence_number
                    }
                )
            
            return entry.entry_id
    
    async def _apply_integrity_protections(self, entry: TamperProofLogEntry):
        """Apply integrity protections based on configured level."""
        
        # Basic: SHA-256 checksum (already calculated in __post_init__)
        
        # Enhanced: Add HMAC signature
        if self.integrity_level in [IntegrityLevel.ENHANCED, IntegrityLevel.MAXIMUM, IntegrityLevel.PARANOID]:
            entry.hmac_signature = hmac.new(
                self.hmac_key.encode(),
                entry.content_hash.encode(),
                hashlib.sha256
            ).hexdigest()
        
        # Maximum/Paranoid: Add digital signature
        if self.integrity_level in [IntegrityLevel.MAXIMUM, IntegrityLevel.PARANOID] and self.signer:
            entry.digital_signature = self.signer.sign_data(entry.content_hash)
    
    async def _store_in_database(self, entry: TamperProofLogEntry):
        """Store log entry in SQLite database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                INSERT INTO tamper_proof_logs (
                    entry_id, timestamp, sequence_number, log_level,
                    source_component, event_type, message, data,
                    content_hash, hmac_signature, digital_signature,
                    previous_hash, chain_hash, backup_locations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.entry_id,
                entry.timestamp.isoformat(),
                entry.sequence_number,
                entry.log_level,
                entry.source_component,
                entry.event_type,
                entry.message,
                json.dumps(entry.data),
                entry.content_hash,
                entry.hmac_signature,
                entry.digital_signature,
                entry.previous_hash,
                entry.chain_hash,
                json.dumps(entry.integrity_metadata.backup_locations)
            ))
            conn.commit()
    
    async def _write_to_file(self, entry: TamperProofLogEntry):
        """Write log entry to file in JSON format."""
        log_data = {
            'entry_id': entry.entry_id,
            'timestamp': entry.timestamp.isoformat(),
            'sequence_number': entry.sequence_number,
            'log_level': entry.log_level,
            'source_component': entry.source_component,
            'event_type': entry.event_type,
            'message': entry.message,
            'data': entry.data,
            'integrity': {
                'content_hash': entry.content_hash,
                'hmac_signature': entry.hmac_signature,
                'digital_signature': entry.digital_signature,
                'previous_hash': entry.previous_hash,
                'chain_hash': entry.chain_hash
            }
        }
        
        async with aiofiles.open(self.log_file, 'a') as f:
            await f.write(json.dumps(log_data, default=str) + '\n')
    
    async def verify_log_integrity(self, entry_id: str = None) -> Dict[str, Any]:
        """Verify integrity of logs (specific entry or entire log)."""
        
        self.integrity_checks += 1
        
        if entry_id:
            return await self._verify_single_entry(entry_id)
        else:
            return await self._verify_all_logs()
    
    async def _verify_single_entry(self, entry_id: str) -> Dict[str, Any]:
        """Verify integrity of a single log entry."""
        
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM tamper_proof_logs WHERE entry_id = ?',
                (entry_id,)
            )
            row = cursor.fetchone()
        
        if not row:
            return {'valid': False, 'error': 'Entry not found'}
        
        # Reconstruct entry
        entry = TamperProofLogEntry(
            entry_id=row['entry_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            sequence_number=row['sequence_number'],
            log_level=row['log_level'],
            source_component=row['source_component'],
            event_type=row['event_type'],
            message=row['message'],
            data=json.loads(row['data']) if row['data'] else {},
            content_hash=row['content_hash'],
            hmac_signature=row['hmac_signature'] or '',
            digital_signature=row['digital_signature'] or '',
            previous_hash=row['previous_hash'] or '',
            chain_hash=row['chain_hash']
        )
        
        # Verify content integrity
        content_valid = entry.verify_integrity()
        
        # Verify HMAC if present
        hmac_valid = True
        if entry.hmac_signature and self.integrity_level in [IntegrityLevel.ENHANCED, IntegrityLevel.MAXIMUM, IntegrityLevel.PARANOID]:
            expected_hmac = hmac.new(
                self.hmac_key.encode(),
                entry.content_hash.encode(),
                hashlib.sha256
            ).hexdigest()
            hmac_valid = hmac.compare_digest(entry.hmac_signature, expected_hmac)
        
        # Verify digital signature if present
        signature_valid = True
        if entry.digital_signature and self.signer:
            signature_valid = self.signer.verify_signature(entry.content_hash, entry.digital_signature)
        
        # Verify backup integrity if configured
        backup_integrity = {}
        if self.backup_manager:
            backup_integrity = await self.backup_manager.verify_backup_integrity(entry_id)
        
        verification_result = {
            'entry_id': entry_id,
            'valid': content_valid and hmac_valid and signature_valid,
            'content_valid': content_valid,
            'hmac_valid': hmac_valid,
            'signature_valid': signature_valid,
            'backup_integrity': backup_integrity,
            'verification_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log verification event
        await self._log_integrity_event(
            LogEvent.LOG_VERIFIED if verification_result['valid'] else LogEvent.LOG_CORRUPTED,
            f"Log verification: {entry_id}",
            verification_result
        )
        
        if not verification_result['valid']:
            self.tamper_attempts_detected += 1
            await self._handle_tamper_detection(entry_id, verification_result)
        
        return verification_result
    
    async def _verify_all_logs(self) -> Dict[str, Any]:
        """Verify integrity of all logs."""
        
        # Verify blockchain chain integrity
        chain_verification = self.chain.verify_chain_integrity()
        
        # Verify individual entries
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('SELECT entry_id FROM tamper_proof_logs ORDER BY sequence_number')
            entry_ids = [row[0] for row in cursor.fetchall()]
        
        individual_verifications = []
        for entry_id in entry_ids:
            verification = await self._verify_single_entry(entry_id)
            individual_verifications.append(verification)
        
        valid_entries = sum(1 for v in individual_verifications if v['valid'])
        total_entries = len(individual_verifications)
        
        overall_result = {
            'overall_valid': chain_verification['valid'] and valid_entries == total_entries,
            'chain_integrity': chain_verification,
            'individual_verifications': individual_verifications,
            'summary': {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'corrupted_entries': total_entries - valid_entries,
                'integrity_percentage': (valid_entries / total_entries * 100) if total_entries > 0 else 100
            },
            'verification_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log overall verification
        await self._log_integrity_event(
            LogEvent.INTEGRITY_CHECK,
            "Complete log integrity verification",
            overall_result['summary']
        )
        
        return overall_result
    
    async def _log_integrity_event(self, event: LogEvent, message: str, data: Dict[str, Any]):
        """Log integrity-related events."""
        await self.log_entry(
            log_level="INFO" if event in [LogEvent.LOG_CREATED, LogEvent.LOG_VERIFIED, LogEvent.INTEGRITY_CHECK] else "WARNING",
            source_component="integrity_monitor",
            event_type=event.value,
            message=message,
            data=data
        )
    
    async def _handle_tamper_detection(self, entry_id: str, verification_result: Dict[str, Any]):
        """Handle detected tampering attempts."""
        
        # Log tamper detection
        await self._log_integrity_event(
            LogEvent.TAMPER_DETECTED,
            f"TAMPER DETECTED: {entry_id}",
            {
                'entry_id': entry_id,
                'verification_result': verification_result,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'severity': 'CRITICAL'
            }
        )
        
        # Additional security measures could be implemented here:
        # - Send alerts to security team
        # - Trigger incident response
        # - Lock down system
        # - Create forensic snapshots
        
        logger.critical(f"🚨 TAMPER DETECTED in log entry: {entry_id}")
    
    def _start_integrity_monitoring(self):
        """Start background integrity monitoring for paranoid mode."""
        def monitor():
            while True:
                try:
                    # Run integrity check every 5 minutes
                    asyncio.run(self.verify_log_integrity())
                    time.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Integrity monitoring error: {e}")
                    time.sleep(60)  # Retry in 1 minute
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("🔍 Background integrity monitoring started")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging system statistics."""
        return {
            'entries_logged': self.entries_logged,
            'integrity_checks': self.integrity_checks,
            'tamper_attempts_detected': self.tamper_attempts_detected,
            'integrity_level': self.integrity_level.value,
            'chain_length': len(self.chain.chain),
            'backup_endpoints': len(self.backup_manager.backup_endpoints) if self.backup_manager else 0
        }

# Convenience functions for different log levels
class TamperProofLoggerWrapper:
    """Wrapper class providing convenient logging methods."""
    
    def __init__(self, logger: TamperProofLogger, source_component: str):
        self.logger = logger
        self.source_component = source_component
    
    async def info(self, message: str, event_type: str = "info", data: Dict[str, Any] = None):
        return await self.logger.log_entry("INFO", self.source_component, event_type, message, data)
    
    async def warning(self, message: str, event_type: str = "warning", data: Dict[str, Any] = None):
        return await self.logger.log_entry("WARNING", self.source_component, event_type, message, data)
    
    async def error(self, message: str, event_type: str = "error", data: Dict[str, Any] = None):
        return await self.logger.log_entry("ERROR", self.source_component, event_type, message, data)
    
    async def critical(self, message: str, event_type: str = "critical", data: Dict[str, Any] = None):
        return await self.logger.log_entry("CRITICAL", self.source_component, event_type, message, data)

# Factory function
def create_tamper_proof_logger(
    log_file: str = "logs/tamper_proof.log",
    db_file: str = "logs/tamper_proof.db",
    integrity_level: IntegrityLevel = IntegrityLevel.MAXIMUM,
    backup_endpoints: List[str] = None,
    source_component: str = "trading_bot"
) -> TamperProofLoggerWrapper:
    """Factory function to create a tamper-proof logger."""
    
    # Default backup endpoints for demo
    if backup_endpoints is None:
        backup_endpoints = [
            "https://backup1.example.com/logs",
            "https://backup2.example.com/logs",
            "https://backup3.example.com/logs"
        ]
    
    logger_instance = TamperProofLogger(
        log_file=log_file,
        db_file=db_file,
        integrity_level=integrity_level,
        backup_endpoints=backup_endpoints
    )
    
    return TamperProofLoggerWrapper(logger_instance, source_component)

async def main():
    """Demonstrate the tamper-proof logging system."""
    print("🔒 Advanced Tamper-Proof Logging System Demo")
    print("=" * 80)
    
    # Create logger with maximum integrity protection
    logger = create_tamper_proof_logger(
        integrity_level=IntegrityLevel.MAXIMUM,
        source_component="demo_system"
    )
    
    print("📝 Logging various events with integrity protection...")
    
    # Log various types of events
    events = [
        ("Trading order placed", "trade_order", {"symbol": "BTC/USDT", "amount": 0.001, "price": 45000}),
        ("User login successful", "user_auth", {"user_id": "user123", "ip": "192.168.1.100"}),
        ("Configuration changed", "config_change", {"parameter": "risk_limit", "old_value": 10000, "new_value": 15000}),
        ("Security alert triggered", "security_alert", {"alert_type": "suspicious_activity", "severity": "high"}),
        ("System error occurred", "system_error", {"error": "Database connection timeout", "component": "trading_engine"})
    ]
    
    entry_ids = []
    for i, (message, event_type, data) in enumerate(events):
        entry_id = await logger.info(message, event_type, data)
        entry_ids.append(entry_id)
        print(f"   ✅ Logged: {message} (ID: {entry_id[:8]}...)")
    
    print(f"\n🔍 Verifying log integrity...")
    
    # Verify individual entries
    for entry_id in entry_ids[:3]:  # Verify first 3 entries
        verification = await logger.logger.verify_log_integrity(entry_id)
        status = "✅ VALID" if verification['valid'] else "❌ CORRUPTED"
        print(f"   Entry {entry_id[:8]}...: {status}")
    
    # Verify entire log
    print(f"\n📊 Complete integrity verification...")
    overall_verification = await logger.logger.verify_log_integrity()
    
    print(f"   Overall Status: {'✅ VALID' if overall_verification['overall_valid'] else '❌ CORRUPTED'}")
    print(f"   Total Entries: {overall_verification['summary']['total_entries']}")
    print(f"   Valid Entries: {overall_verification['summary']['valid_entries']}")
    print(f"   Integrity: {overall_verification['summary']['integrity_percentage']:.1f}%")
    
    # Show statistics
    print(f"\n📈 System Statistics:")
    stats = logger.logger.get_statistics()
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🎉 Tamper-Proof Logging System demonstration completed!")
    print(f"🔒 All logs are protected with cryptographic integrity verification")

if __name__ == "__main__":
    asyncio.run(main()) 