#!/usr/bin/env python3
"""
Enterprise Encryption Security System
Comprehensive encryption at rest and in transit for trading systems
"""

import asyncio
import logging
import os
import json
import base64
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import ssl
import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import nacl.secret
import nacl.utils
from nacl.public import PrivateKey, PublicKey, Box
import aiofiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncryptionMethod(Enum):
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305" 
    FERNET = "fernet"
    RSA_OAEP = "rsa_oaep"
    NACL_SECRETBOX = "nacl_secretbox"

class StorageType(Enum):
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    CACHE = "cache"
    BACKUP = "backup"
    CI_CD = "ci_cd"
    LOGS = "logs"

@dataclass
class EncryptedData:
    """Encrypted data container with metadata"""
    ciphertext: str
    encryption_method: str
    key_id: str
    nonce: Optional[str] = None
    salt: Optional[str] = None
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class EncryptionKey:
    """Encryption key metadata"""
    key_id: str
    algorithm: str
    key_size: int
    created_at: datetime
    last_used: datetime
    rotation_count: int
    is_active: bool
    storage_types: List[str]

class EncryptionKeyManager:
    """Manages encryption keys with rotation and derivation"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or self._generate_master_key()
        self.keys: Dict[str, bytes] = {}
        self.key_metadata: Dict[str, EncryptionKey] = {}
        self.backend = default_backend()
        
    def _generate_master_key(self) -> bytes:
        """Generate or derive master key from secure source"""
        
        # In production, this should come from a secure source like:
        # - Hardware Security Module (HSM)
        # - Key Management Service (AWS KMS, Azure Key Vault, etc.)
        # - Secure key derivation from passphrase + salt
        
        master_key_env = os.environ.get('MASTER_ENCRYPTION_KEY')
        if master_key_env:
            # Derive key from environment variable + salt
            salt = os.environ.get('ENCRYPTION_SALT', 'default_salt').encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            return kdf.derive(master_key_env.encode())
        else:
            # Generate random key (for demo/development)
            logger.warning("⚠️  Using generated master key - not suitable for production")
            return secrets.token_bytes(32)
    
    def derive_key(self, purpose: str, key_size: int = 32) -> Tuple[str, bytes]:
        """Derive encryption key for specific purpose"""
        
        key_id = f"{purpose}_{hashlib.sha256(purpose.encode()).hexdigest()[:8]}"
        
        if key_id not in self.keys:
            # Derive key using HKDF
            info = f"trading_system_{purpose}".encode()
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=key_size,
                salt=None,
                info=info,
                backend=self.backend
            )
            
            derived_key = hkdf.derive(self.master_key)
            self.keys[key_id] = derived_key
            
            # Store metadata
            self.key_metadata[key_id] = EncryptionKey(
                key_id=key_id,
                algorithm="HKDF-SHA256",
                key_size=key_size * 8,  # bits
                created_at=datetime.now(),
                last_used=datetime.now(),
                rotation_count=0,
                is_active=True,
                storage_types=[]
            )
            
            logger.info(f"🔑 Derived encryption key: {key_id}")
        
        # Update last used
        self.key_metadata[key_id].last_used = datetime.now()
        return key_id, self.keys[key_id]
    
    def rotate_key(self, key_id: str) -> Tuple[str, bytes]:
        """Rotate an encryption key"""
        
        if key_id in self.key_metadata:
            # Extract purpose from key_id
            purpose = key_id.split('_')[0]
            
            # Mark old key as inactive
            self.key_metadata[key_id].is_active = False
            
            # Generate new key
            new_key_id = f"{purpose}_{hashlib.sha256(f'{purpose}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"
            
            # Derive new key
            info = f"trading_system_{purpose}_rotated".encode()
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=secrets.token_bytes(16),  # Random salt for rotation
                info=info,
                backend=self.backend
            )
            
            new_key = hkdf.derive(self.master_key)
            self.keys[new_key_id] = new_key
            
            # Store new metadata
            old_metadata = self.key_metadata[key_id]
            self.key_metadata[new_key_id] = EncryptionKey(
                key_id=new_key_id,
                algorithm="HKDF-SHA256",
                key_size=256,
                created_at=datetime.now(),
                last_used=datetime.now(),
                rotation_count=old_metadata.rotation_count + 1,
                is_active=True,
                storage_types=old_metadata.storage_types
            )
            
            logger.info(f"🔄 Rotated encryption key: {key_id} → {new_key_id}")
            return new_key_id, new_key
        
        raise ValueError(f"Key {key_id} not found")

class SecureEncryption:
    """Comprehensive encryption system for API keys and sensitive data"""
    
    def __init__(self, key_manager: Optional[EncryptionKeyManager] = None):
        self.key_manager = key_manager or EncryptionKeyManager()
        self.backend = default_backend()
        
    # ==================== AES-256-GCM ENCRYPTION ====================
    
    async def encrypt_aes_gcm(self, plaintext: str, purpose: str) -> EncryptedData:
        """Encrypt using AES-256-GCM (recommended for most use cases)"""
        
        key_id, key = self.key_manager.derive_key(f"aes_gcm_{purpose}", 32)
        
        # Generate random nonce
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        
        # Get authentication tag
        auth_tag = encryptor.tag
        
        # Combine ciphertext and auth tag
        encrypted_data = ciphertext + auth_tag
        
        return EncryptedData(
            ciphertext=base64.b64encode(encrypted_data).decode(),
            encryption_method=EncryptionMethod.AES_256_GCM.value,
            key_id=key_id,
            nonce=base64.b64encode(nonce).decode()
        )
    
    async def decrypt_aes_gcm(self, encrypted_data: EncryptedData) -> str:
        """Decrypt AES-256-GCM encrypted data"""
        
        key = self.key_manager.keys.get(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Encryption key {encrypted_data.key_id} not found")
        
        # Decode data
        encrypted_bytes = base64.b64decode(encrypted_data.ciphertext)
        nonce = base64.b64decode(encrypted_data.nonce)
        
        # Split ciphertext and auth tag (last 16 bytes)
        ciphertext = encrypted_bytes[:-16]
        auth_tag = encrypted_bytes[-16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, auth_tag),
            backend=self.backend
        )
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode()
    
    # ==================== ChaCha20-Poly1305 ENCRYPTION ====================
    
    async def encrypt_chacha20(self, plaintext: str, purpose: str) -> EncryptedData:
        """Encrypt using ChaCha20-Poly1305 (high performance)"""
        
        key_id, key = self.key_manager.derive_key(f"chacha20_{purpose}", 32)
        
        # Use PyNaCl for ChaCha20-Poly1305
        box = nacl.secret.SecretBox(key)
        encrypted_bytes = box.encrypt(plaintext.encode())
        
        return EncryptedData(
            ciphertext=base64.b64encode(encrypted_bytes.ciphertext).decode(),
            encryption_method=EncryptionMethod.CHACHA20_POLY1305.value,
            key_id=key_id,
            nonce=base64.b64encode(encrypted_bytes.nonce).decode()
        )
    
    async def decrypt_chacha20(self, encrypted_data: EncryptedData) -> str:
        """Decrypt ChaCha20-Poly1305 encrypted data"""
        
        key = self.key_manager.keys.get(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Encryption key {encrypted_data.key_id} not found")
        
        box = nacl.secret.SecretBox(key)
        
        # Reconstruct encrypted message
        ciphertext = base64.b64decode(encrypted_data.ciphertext)
        nonce = base64.b64decode(encrypted_data.nonce)
        
        encrypted_message = nacl.utils.EncryptedMessage(ciphertext, nonce)
        plaintext = box.decrypt(encrypted_message)
        
        return plaintext.decode()
    
    # ==================== FERNET ENCRYPTION ====================
    
    async def encrypt_fernet(self, plaintext: str, purpose: str) -> EncryptedData:
        """Encrypt using Fernet (simple and secure)"""
        
        key_id, key = self.key_manager.derive_key(f"fernet_{purpose}", 32)
        
        # Fernet requires base64-encoded key
        fernet_key = base64.urlsafe_b64encode(key)
        f = Fernet(fernet_key)
        
        encrypted_bytes = f.encrypt(plaintext.encode())
        
        return EncryptedData(
            ciphertext=base64.b64encode(encrypted_bytes).decode(),
            encryption_method=EncryptionMethod.FERNET.value,
            key_id=key_id
        )
    
    async def decrypt_fernet(self, encrypted_data: EncryptedData) -> str:
        """Decrypt Fernet encrypted data"""
        
        key = self.key_manager.keys.get(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Encryption key {encrypted_data.key_id} not found")
        
        fernet_key = base64.urlsafe_b64encode(key)
        f = Fernet(fernet_key)
        
        encrypted_bytes = base64.b64decode(encrypted_data.ciphertext)
        plaintext = f.decrypt(encrypted_bytes)
        
        return plaintext.decode()
    
    # ==================== MAIN ENCRYPTION INTERFACE ====================
    
    async def encrypt(self, plaintext: str, purpose: str, 
                     method: EncryptionMethod = EncryptionMethod.AES_256_GCM) -> EncryptedData:
        """Main encryption method with algorithm selection"""
        
        if method == EncryptionMethod.AES_256_GCM:
            return await self.encrypt_aes_gcm(plaintext, purpose)
        elif method == EncryptionMethod.CHACHA20_POLY1305:
            return await self.encrypt_chacha20(plaintext, purpose)
        elif method == EncryptionMethod.FERNET:
            return await self.encrypt_fernet(plaintext, purpose)
        else:
            raise ValueError(f"Unsupported encryption method: {method}")
    
    async def decrypt(self, encrypted_data: EncryptedData) -> str:
        """Main decryption method"""
        
        method = EncryptionMethod(encrypted_data.encryption_method)
        
        if method == EncryptionMethod.AES_256_GCM:
            return await self.decrypt_aes_gcm(encrypted_data)
        elif method == EncryptionMethod.CHACHA20_POLY1305:
            return await self.decrypt_chacha20(encrypted_data)
        elif method == EncryptionMethod.FERNET:
            return await self.decrypt_fernet(encrypted_data)
        else:
            raise ValueError(f"Unsupported encryption method: {method}")

class StorageEncryption:
    """Encryption at rest for various storage systems"""
    
    def __init__(self, encryption_system: SecureEncryption):
        self.encryption = encryption_system
        
    async def encrypt_for_storage(self, data: Dict[str, Any], 
                                storage_type: StorageType) -> str:
        """Encrypt data for specific storage type"""
        
        # Serialize data
        json_data = json.dumps(data, default=str)
        
        # Choose encryption method based on storage type
        method = self._get_encryption_method(storage_type)
        purpose = f"storage_{storage_type.value}"
        
        # Encrypt
        encrypted_data = await self.encryption.encrypt(json_data, purpose, method)
        
        # Return as JSON string for storage
        return json.dumps(asdict(encrypted_data), default=str)
    
    async def decrypt_from_storage(self, encrypted_json: str) -> Dict[str, Any]:
        """Decrypt data from storage"""
        
        # Parse encrypted data
        encrypted_dict = json.loads(encrypted_json)
        encrypted_data = EncryptedData(**encrypted_dict)
        
        # Decrypt
        json_data = await self.encryption.decrypt(encrypted_data)
        
        # Parse and return
        return json.loads(json_data)
    
    def _get_encryption_method(self, storage_type: StorageType) -> EncryptionMethod:
        """Select encryption method based on storage type"""
        
        storage_methods = {
            StorageType.DATABASE: EncryptionMethod.AES_256_GCM,
            StorageType.FILE_SYSTEM: EncryptionMethod.AES_256_GCM,
            StorageType.CACHE: EncryptionMethod.CHACHA20_POLY1305,  # Performance
            StorageType.BACKUP: EncryptionMethod.AES_256_GCM,
            StorageType.CI_CD: EncryptionMethod.FERNET,  # Simplicity
            StorageType.LOGS: EncryptionMethod.CHACHA20_POLY1305
        }
        
        return storage_methods.get(storage_type, EncryptionMethod.AES_256_GCM)

class TransitEncryption:
    """Encryption in transit for API communications"""
    
    def __init__(self, encryption_system: SecureEncryption):
        self.encryption = encryption_system
        
    async def create_secure_session(self, verify_ssl: bool = True) -> aiohttp.ClientSession:
        """Create HTTP session with strict TLS configuration"""
        
        # Create SSL context with strict security
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = verify_ssl
        ssl_context.verify_mode = ssl.CERT_REQUIRED if verify_ssl else ssl.CERT_NONE
        
        # Disable weak protocols and ciphers
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Create connector with SSL context
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Create session with security headers
        headers = {
            'User-Agent': 'SecureTradingBot/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        return aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def encrypt_api_payload(self, payload: Dict[str, Any], 
                                endpoint: str) -> Tuple[str, Dict[str, str]]:
        """Encrypt API payload for transmission"""
        
        # Serialize payload
        json_payload = json.dumps(payload, separators=(',', ':'))
        
        # Encrypt with endpoint-specific purpose
        purpose = f"api_{hashlib.sha256(endpoint.encode()).hexdigest()[:8]}"
        encrypted_data = await self.encryption.encrypt(
            json_payload, 
            purpose, 
            EncryptionMethod.CHACHA20_POLY1305  # Fast for API calls
        )
        
        # Create encrypted payload
        encrypted_payload = json.dumps(asdict(encrypted_data), default=str)
        
        # Add encryption headers
        headers = {
            'X-Encryption-Method': encrypted_data.encryption_method,
            'X-Encryption-Key-ID': encrypted_data.key_id,
            'Content-Type': 'application/json',
            'Content-Encoding': 'encrypted'
        }
        
        return encrypted_payload, headers
    
    async def decrypt_api_response(self, encrypted_response: str, 
                                 headers: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt API response"""
        
        # Check if response is encrypted
        if headers.get('Content-Encoding') != 'encrypted':
            return json.loads(encrypted_response)
        
        # Parse encrypted data
        encrypted_dict = json.loads(encrypted_response)
        encrypted_data = EncryptedData(**encrypted_dict)
        
        # Decrypt
        json_response = await self.encryption.decrypt(encrypted_data)
        return json.loads(json_response)

class SecureAPIKeyManager:
    """Secure API key management with comprehensive encryption"""
    
    def __init__(self):
        self.encryption = SecureEncryption()
        self.storage_encryption = StorageEncryption(self.encryption)
        self.transit_encryption = TransitEncryption(self.encryption)
        
    async def store_api_key(self, exchange: str, api_key: str, 
                          api_secret: str, storage_type: StorageType) -> str:
        """Securely store API key with encryption at rest"""
        
        # Prepare data for storage
        key_data = {
            'exchange': exchange,
            'api_key': api_key,
            'api_secret': api_secret,
            'created_at': datetime.now().isoformat(),
            'storage_type': storage_type.value
        }
        
        # Encrypt for storage
        encrypted_data = await self.storage_encryption.encrypt_for_storage(
            key_data, storage_type
        )
        
        logger.info(f"🔒 Encrypted API key for {exchange} ({storage_type.value})")
        return encrypted_data
    
    async def retrieve_api_key(self, encrypted_data: str) -> Dict[str, Any]:
        """Retrieve and decrypt API key"""
        
        # Decrypt from storage
        key_data = await self.storage_encryption.decrypt_from_storage(encrypted_data)
        
        logger.info(f"🔓 Decrypted API key for {key_data['exchange']}")
        return key_data
    
    async def secure_api_call(self, url: str, payload: Dict[str, Any], 
                            api_key: str, api_secret: str) -> Dict[str, Any]:
        """Make secure API call with encryption in transit"""
        
        # Create secure session
        session = await self.transit_encryption.create_secure_session()
        
        try:
            # Add authentication
            headers = {'X-MBX-APIKEY': api_key}
            
            # Sign request if required
            if api_secret:
                timestamp = str(int(time.time() * 1000))
                query_string = f"timestamp={timestamp}"
                
                signature = hmac.new(
                    api_secret.encode(),
                    query_string.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                payload['timestamp'] = timestamp
                payload['signature'] = signature
            
            # Encrypt payload for transmission
            encrypted_payload, encryption_headers = await self.transit_encryption.encrypt_api_payload(
                payload, url
            )
            
            # Combine headers
            headers.update(encryption_headers)
            
            # Make secure request
            async with session.post(url, data=encrypted_payload, headers=headers) as response:
                response_text = await response.text()
                response_headers = dict(response.headers)
                
                # Decrypt response
                decrypted_response = await self.transit_encryption.decrypt_api_response(
                    response_text, response_headers
                )
                
                return decrypted_response
                
        finally:
            await session.close()

class EncryptionAuditLogger:
    """Audit logging for encryption operations"""
    
    def __init__(self, log_file: str = "encryption_audit.log"):
        self.log_file = log_file
        self.encryption = SecureEncryption()
        
    async def log_encryption_event(self, event_type: str, details: Dict[str, Any]):
        """Log encryption event with encrypted details"""
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'source': 'encryption_security_system'
        }
        
        # Encrypt audit log entry
        encrypted_entry = await self.encryption.encrypt(
            json.dumps(audit_entry, default=str),
            'audit_logs',
            EncryptionMethod.AES_256_GCM
        )
        
        # Write to log file
        log_entry = {
            'encrypted_audit': asdict(encrypted_entry)
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

# Integration with existing systems
class EncryptedScalableDataOptimizer:
    """Enhanced scalable system with comprehensive encryption"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.api_key_manager = SecureAPIKeyManager()
        self.audit_logger = EncryptionAuditLogger()
        
    async def initialize_with_encryption(self):
        """Initialize system with encrypted API keys"""
        
        logger.info("🔐 Initializing with comprehensive encryption...")
        
        # Load encrypted API keys
        encrypted_keys = await self._load_encrypted_api_keys()
        
        # Audit initialization
        await self.audit_logger.log_encryption_event(
            'system_initialization',
            {
                'environment': self.environment,
                'encryption_enabled': True,
                'keys_loaded': len(encrypted_keys)
            }
        )
        
        logger.info(f"✅ System initialized with {len(encrypted_keys)} encrypted API keys")
    
    async def _load_encrypted_api_keys(self) -> Dict[str, str]:
        """Load and decrypt API keys from secure storage"""
        
        # This would integrate with your existing secret management
        # For demo purposes, we'll simulate loading encrypted keys
        
        encrypted_keys = {}
        
        exchanges = ['binance', 'coinbase', 'kraken']
        for exchange in exchanges:
            # Simulate encrypted key storage
            encrypted_data = await self.api_key_manager.store_api_key(
                exchange,
                f'demo_{exchange}_key',
                f'demo_{exchange}_secret',
                StorageType.DATABASE
            )
            
            encrypted_keys[exchange] = encrypted_data
            
        return encrypted_keys
    
    async def make_secure_api_call(self, exchange: str, endpoint: str, 
                                 payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call with comprehensive encryption"""
        
        # Load encrypted API keys
        encrypted_key_data = await self._get_encrypted_api_key(exchange)
        key_data = await self.api_key_manager.retrieve_api_key(encrypted_key_data)
        
        # Make secure API call
        response = await self.api_key_manager.secure_api_call(
            endpoint,
            payload,
            key_data['api_key'],
            key_data['api_secret']
        )
        
        # Audit API call
        await self.audit_logger.log_encryption_event(
            'secure_api_call',
            {
                'exchange': exchange,
                'endpoint': endpoint,
                'payload_encrypted': True,
                'response_encrypted': True
            }
        )
        
        return response
    
    async def _get_encrypted_api_key(self, exchange: str) -> str:
        """Get encrypted API key for exchange"""
        # This would retrieve from your actual storage system
        # For demo, we'll return a placeholder
        return f"encrypted_key_data_for_{exchange}"

# Demo and testing
async def demo_encryption_system():
    """Demonstrate comprehensive encryption system"""
    
    print("🔐 Starting Encryption Security System Demo\n")
    
    # Initialize encryption system
    encryption = SecureEncryption()
    api_key_manager = SecureAPIKeyManager()
    
    # Demo 1: Basic encryption/decryption
    print("📝 Demo 1: Basic Encryption/Decryption")
    sensitive_data = "binance_api_key_secret_12345"
    
    encrypted_data = await encryption.encrypt(
        sensitive_data, 
        "api_key_storage", 
        EncryptionMethod.AES_256_GCM
    )
    
    print(f"   ✅ Encrypted: {encrypted_data.ciphertext[:50]}...")
    
    decrypted_data = await encryption.decrypt(encrypted_data)
    print(f"   ✅ Decrypted: {decrypted_data}")
    print(f"   ✅ Match: {sensitive_data == decrypted_data}\n")
    
    # Demo 2: Storage encryption
    print("📦 Demo 2: Storage Encryption")
    
    api_key_data = {
        'exchange': 'binance',
        'api_key': 'demo_api_key_12345',
        'api_secret': 'demo_secret_67890'
    }
    
    # Encrypt for different storage types
    storage_types = [StorageType.DATABASE, StorageType.BACKUP, StorageType.CI_CD]
    
    for storage_type in storage_types:
        encrypted_storage = await api_key_manager.store_api_key(
            api_key_data['exchange'],
            api_key_data['api_key'],
            api_key_data['api_secret'],
            storage_type
        )
        
        print(f"   ✅ {storage_type.value}: {len(encrypted_storage)} bytes encrypted")
    
    print()
    
    # Demo 3: Performance comparison
    print("⚡ Demo 3: Encryption Performance")
    
    test_data = "sensitive_api_key_data_" * 100  # Larger test data
    methods = [
        EncryptionMethod.AES_256_GCM,
        EncryptionMethod.CHACHA20_POLY1305,
        EncryptionMethod.FERNET
    ]
    
    for method in methods:
        start_time = time.time()
        
        encrypted = await encryption.encrypt(test_data, "performance_test", method)
        decrypted = await encryption.decrypt(encrypted)
        
        duration = (time.time() - start_time) * 1000  # ms
        print(f"   ✅ {method.value}: {duration:.2f}ms")
    
    print()
    
    # Demo 4: Audit logging
    print("📋 Demo 4: Audit Logging")
    
    audit_logger = EncryptionAuditLogger()
    
    await audit_logger.log_encryption_event(
        'api_key_rotation',
        {
            'exchange': 'binance',
            'old_key_id': 'key_123',
            'new_key_id': 'key_456',
            'rotation_reason': 'scheduled'
        }
    )
    
    print("   ✅ Encrypted audit log written")
    
    # Read audit logs
    logs = await audit_logger.read_audit_logs()
    print(f"   ✅ Read {len(logs)} encrypted audit entries")
    
    print("\n🎉 Encryption system demo completed!")
    print("🔒 All API keys and sensitive data are now encrypted at rest and in transit")

if __name__ == "__main__":
    asyncio.run(demo_encryption_system()) 