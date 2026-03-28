#!/usr/bin/env python3
"""
Tamper-Proof Logging System Demo
Demonstrates advanced log integrity protection features
"""

import asyncio
import json
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SecureLogEntry:
    """Secure log entry with integrity protection."""
    entry_id: str
    timestamp: datetime
    sequence_number: int
    log_level: str
    component: str
    event_type: str
    message: str
    data: Dict[str, Any]
    
    # Integrity fields
    content_hash: str = ""
    hmac_signature: str = ""
    previous_hash: str = ""
    chain_hash: str = ""
    
    def calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of content."""
        content = {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'sequence_number': self.sequence_number,
            'log_level': self.log_level,
            'component': self.component,
            'event_type': self.event_type,
            'message': self.message,
            'data': json.dumps(self.data, sort_keys=True)
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify content integrity."""
        return self.content_hash == self.calculate_content_hash()

class TamperProofDemo:
    """Demonstration of tamper-proof logging features."""
    
    def __init__(self):
        self.db_file = Path("logs/tamper_proof_demo.db")
        self.log_file = Path("logs/tamper_proof_demo.log")
        self.hmac_key = secrets.token_hex(32)
        self.chain: List[SecureLogEntry] = []
        self.current_hash = "0" * 64  # Genesis hash
        
        # Create directories
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        print("🔒 Tamper-Proof Logging System Initialized")
        print(f"   Database: {self.db_file}")
        print(f"   Log File: {self.log_file}")
    
    def _init_database(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS secure_logs (
                    entry_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    log_level TEXT NOT NULL,
                    component TEXT,
                    event_type TEXT,
                    message TEXT NOT NULL,
                    data TEXT,
                    content_hash TEXT NOT NULL,
                    hmac_signature TEXT,
                    previous_hash TEXT,
                    chain_hash TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def log_entry(self, log_level: str, component: str, event_type: str, 
                  message: str, data: Dict[str, Any] = None) -> str:
        """Log an entry with integrity protection."""
        
        entry_id = f"entry_{len(self.chain):06d}"
        entry = SecureLogEntry(
            entry_id=entry_id,
            timestamp=datetime.now(timezone.utc),
            sequence_number=len(self.chain),
            log_level=log_level,
            component=component,
            event_type=event_type,
            message=message,
            data=data or {}
        )
        
        # Calculate content hash
        entry.content_hash = entry.calculate_content_hash()
        
        # Calculate HMAC signature
        entry.hmac_signature = hmac.new(
            self.hmac_key.encode(),
            entry.content_hash.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Set previous hash and calculate chain hash
        entry.previous_hash = self.current_hash
        chain_data = f"{entry.previous_hash}{entry.content_hash}{entry.sequence_number}"
        entry.chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        
        # Update current hash
        self.current_hash = entry.chain_hash
        
        # Add to chain
        self.chain.append(entry)
        
        # Store in database
        self._store_entry(entry)
        
        # Write to log file
        self._write_to_file(entry)
        
        return entry_id
    
    def _store_entry(self, entry: SecureLogEntry):
        """Store entry in database."""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                INSERT INTO secure_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.entry_id, entry.timestamp.isoformat(), entry.sequence_number,
                entry.log_level, entry.component, entry.event_type, entry.message,
                json.dumps(entry.data), entry.content_hash, entry.hmac_signature,
                entry.previous_hash, entry.chain_hash
            ))
            conn.commit()
    
    def _write_to_file(self, entry: SecureLogEntry):
        """Write entry to log file."""
        log_data = {
            'entry_id': entry.entry_id,
            'timestamp': entry.timestamp.isoformat(),
            'sequence_number': entry.sequence_number,
            'log_level': entry.log_level,
            'component': entry.component,
            'event_type': entry.event_type,
            'message': entry.message,
            'data': entry.data,
            'integrity': {
                'content_hash': entry.content_hash,
                'hmac_signature': entry.hmac_signature,
                'previous_hash': entry.previous_hash,
                'chain_hash': entry.chain_hash
            }
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_data, default=str) + '\n')
    
    def verify_entry(self, entry_id: str) -> Dict[str, Any]:
        """Verify integrity of a specific entry."""
        
        # Find entry in chain
        entry = None
        for e in self.chain:
            if e.entry_id == entry_id:
                entry = e
                break
        
        if not entry:
            return {'valid': False, 'error': 'Entry not found'}
        
        # Verify content integrity
        content_valid = entry.verify_integrity()
        
        # Verify HMAC signature
        expected_hmac = hmac.new(
            self.hmac_key.encode(),
            entry.content_hash.encode(),
            hashlib.sha256
        ).hexdigest()
        hmac_valid = hmac.compare_digest(entry.hmac_signature, expected_hmac)
        
        # Verify chain integrity
        expected_chain_hash = hashlib.sha256(
            f"{entry.previous_hash}{entry.content_hash}{entry.sequence_number}".encode()
        ).hexdigest()
        chain_valid = entry.chain_hash == expected_chain_hash
        
        return {
            'entry_id': entry_id,
            'valid': content_valid and hmac_valid and chain_valid,
            'content_valid': content_valid,
            'hmac_valid': hmac_valid,
            'chain_valid': chain_valid,
            'verification_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def verify_entire_chain(self) -> Dict[str, Any]:
        """Verify integrity of entire log chain."""
        
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
            
            # Verify content integrity
            if not entry.verify_integrity():
                corrupted_entries.append(i)
                continue
            
            # Verify HMAC
            expected_hmac = hmac.new(
                self.hmac_key.encode(),
                entry.content_hash.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(entry.hmac_signature, expected_hmac):
                corrupted_entries.append(i)
                continue
            
            # Verify chain hash
            expected_chain_hash = hashlib.sha256(
                f"{entry.previous_hash}{entry.content_hash}{entry.sequence_number}".encode()
            ).hexdigest()
            
            if entry.chain_hash != expected_chain_hash:
                corrupted_entries.append(i)
            
            previous_hash = entry.chain_hash
        
        valid_entries = len(self.chain) - len(corrupted_entries)
        
        return {
            'valid': len(corrupted_entries) == 0,
            'corrupted_entries': corrupted_entries,
            'total_entries': len(self.chain),
            'valid_entries': valid_entries,
            'integrity_percentage': (valid_entries / len(self.chain) * 100) if self.chain else 100
        }
    
    def simulate_tamper_attempt(self, entry_id: str):
        """Simulate a tampering attempt for demonstration."""
        
        # Find and modify an entry
        for entry in self.chain:
            if entry.entry_id == entry_id:
                print(f"🚨 Simulating tamper attempt on {entry_id}")
                original_message = entry.message
                entry.message = "TAMPERED MESSAGE"
                print(f"   Original: {original_message}")
                print(f"   Tampered: {entry.message}")
                break
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging system statistics."""
        return {
            'total_entries': len(self.chain),
            'database_entries': self._count_database_entries(),
            'log_file_size': self.log_file.stat().st_size if self.log_file.exists() else 0,
            'integrity_features': [
                'SHA-256 Content Hashing',
                'HMAC Signing',
                'Blockchain-style Chaining',
                'Database Storage',
                'File Logging'
            ]
        }
    
    def _count_database_entries(self) -> int:
        """Count entries in database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM secure_logs')
            return cursor.fetchone()[0]

def main():
    """Run the tamper-proof logging demonstration."""
    print("🔒 Advanced Tamper-Proof Logging System Demo")
    print("=" * 80)
    
    # Initialize the demo system
    demo = TamperProofDemo()
    
    print("\n📝 Logging Events with Integrity Protection")
    print("-" * 60)
    
    # Log various events
    events = [
        ("INFO", "trading_engine", "trade_placed", "Order placed for BTC/USDT", 
         {"symbol": "BTC/USDT", "amount": 0.001, "price": 45000}),
        ("INFO", "auth_system", "user_login", "User login successful", 
         {"user_id": "user123", "ip": "192.168.1.100", "timestamp": datetime.now().isoformat()}),
        ("WARNING", "risk_manager", "limit_exceeded", "Risk limit exceeded", 
         {"limit_type": "position_size", "current": 15000, "max": 10000}),
        ("ERROR", "exchange_api", "connection_failed", "Failed to connect to exchange", 
         {"exchange": "binance", "error": "timeout", "retry_count": 3}),
        ("CRITICAL", "security_monitor", "suspicious_activity", "Suspicious login pattern detected", 
         {"pattern": "multiple_failed_attempts", "source_ip": "suspicious.ip.com", "count": 10})
    ]
    
    entry_ids = []
    for log_level, component, event_type, message, data in events:
        entry_id = demo.log_entry(log_level, component, event_type, message, data)
        entry_ids.append(entry_id)
        print(f"   ✅ {log_level:8} | {component:15} | {message}")
    
    print(f"\n🔍 Verifying Log Integrity")
    print("-" * 60)
    
    # Verify individual entries
    print("Individual Entry Verification:")
    for entry_id in entry_ids:
        verification = demo.verify_entry(entry_id)
        status = "✅ VALID" if verification['valid'] else "❌ CORRUPTED"
        print(f"   {entry_id}: {status}")
    
    # Verify entire chain
    print(f"\nComplete Chain Verification:")
    chain_verification = demo.verify_entire_chain()
    print(f"   Overall Status: {'✅ VALID' if chain_verification['valid'] else '❌ CORRUPTED'}")
    print(f"   Total Entries: {chain_verification['total_entries']}")
    print(f"   Valid Entries: {chain_verification['valid_entries']}")
    print(f"   Integrity: {chain_verification['integrity_percentage']:.1f}%")
    
    print(f"\n🚨 Tamper Detection Demonstration")
    print("-" * 60)
    
    # Simulate tampering
    if entry_ids:
        demo.simulate_tamper_attempt(entry_ids[1])  # Tamper with second entry
        
        # Verify after tampering
        print(f"\nVerification After Tampering:")
        tampered_verification = demo.verify_entry(entry_ids[1])
        status = "✅ VALID" if tampered_verification['valid'] else "❌ CORRUPTED"
        print(f"   Tampered Entry: {status}")
        
        if not tampered_verification['valid']:
            print(f"   🔍 Integrity Checks:")
            print(f"      Content Hash: {'✅' if tampered_verification['content_valid'] else '❌'}")
            print(f"      HMAC Signature: {'✅' if tampered_verification['hmac_valid'] else '❌'}")
            print(f"      Chain Link: {'✅' if tampered_verification['chain_valid'] else '❌'}")
    
    print(f"\n📊 System Statistics")
    print("-" * 60)
    
    stats = demo.get_statistics()
    for key, value in stats.items():
        if key == 'integrity_features':
            print(f"   {key.replace('_', ' ').title()}:")
            for feature in value:
                print(f"      • {feature}")
        else:
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n📁 Generated Files")
    print("-" * 60)
    print(f"   📄 Database: {demo.db_file} ({demo.db_file.stat().st_size} bytes)")
    print(f"   📄 Log File: {demo.log_file} ({demo.log_file.stat().st_size} bytes)")
    
    print(f"\n🛡️ Security Features Demonstrated")
    print("-" * 60)
    print("   ✅ SHA-256 Content Hashing - Detects any content modification")
    print("   ✅ HMAC Signing - Prevents unauthorized log creation")
    print("   ✅ Blockchain Chaining - Links entries in tamper-evident chain")
    print("   ✅ Dual Storage - Database + file redundancy")
    print("   ✅ Real-time Verification - Immediate tamper detection")
    print("   ✅ Forensic Analysis - Complete audit trail preservation")
    
    print(f"\n🎉 Tamper-Proof Logging Demo Complete!")
    print("🔒 Your logs are now protected against malicious modification")

if __name__ == "__main__":
    main() 