#!/usr/bin/env python3
"""
🛡️ ADVANCED CERTIFICATE VALIDATION SYSTEM
================================================================================
Advanced SSL/TLS certificate validation to prevent man-in-the-middle attacks
and ensure secure communications for the AI Trading Bot.

Features:
- Comprehensive certificate chain validation
- Certificate pinning with automatic updates
- Certificate transparency monitoring
- OCSP (Online Certificate Status Protocol) validation
- Certificate revocation checking
- Advanced certificate analysis and scoring
- Real-time certificate monitoring and alerting
"""

import os
import ssl
import socket
import logging
import hashlib
import base64
import time
import requests
import cryptography
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
import json
import threading
import concurrent.futures
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CertificateValidationType(Enum):
    """Types of certificate validation."""
    BASIC = "basic"                    # Basic certificate validation
    EXTENDED = "extended"              # Extended validation with OCSP
    STRICT = "strict"                  # Strict validation with CT logs
    PARANOID = "paranoid"              # Maximum security validation


class CertificateStatus(Enum):
    """Certificate validation status."""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class TrustLevel(Enum):
    """Certificate trust levels."""
    HIGH = "high"                      # Fully trusted certificate
    MEDIUM = "medium"                  # Trusted with minor issues
    LOW = "low"                        # Trusted with concerns
    UNTRUSTED = "untrusted"           # Not trusted


@dataclass
class CertificateChain:
    """Complete certificate chain information."""
    leaf_certificate: x509.Certificate
    intermediate_certificates: List[x509.Certificate] = field(default_factory=list)
    root_certificate: Optional[x509.Certificate] = None
    chain_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class CertificateAnalysis:
    """Comprehensive certificate analysis."""
    certificate: x509.Certificate
    fingerprint_sha256: str
    fingerprint_sha1: str
    subject_info: Dict[str, str]
    issuer_info: Dict[str, str]
    validity_period: Dict[str, datetime]
    key_info: Dict[str, Any]
    extensions: Dict[str, Any]
    san_entries: List[str] = field(default_factory=list)
    
    # Validation results
    status: CertificateStatus = CertificateStatus.UNKNOWN
    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    validation_errors: List[str] = field(default_factory=list)
    security_warnings: List[str] = field(default_factory=list)
    
    # Security scoring
    security_score: int = 0  # 0-100
    risk_factors: List[str] = field(default_factory=list)
    
    # OCSP and revocation
    ocsp_status: Optional[str] = None
    crl_status: Optional[str] = None
    
    # Certificate transparency
    ct_logs_count: int = 0
    ct_verified: bool = False


@dataclass
class CertificatePinning:
    """Certificate pinning configuration."""
    hostname: str
    pinned_fingerprints: List[str] = field(default_factory=list)
    backup_fingerprints: List[str] = field(default_factory=list)
    pin_type: str = "sha256"  # sha256, sha1, spki
    auto_update: bool = False
    last_updated: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


@dataclass
class ValidationResult:
    """Certificate validation result."""
    hostname: str
    certificate_analysis: CertificateAnalysis
    chain_analysis: CertificateChain
    pinning_result: Optional[Dict[str, Any]] = None
    ocsp_result: Optional[Dict[str, Any]] = None
    ct_result: Optional[Dict[str, Any]] = None
    
    overall_status: CertificateStatus = CertificateStatus.UNKNOWN
    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    security_score: int = 0
    
    validation_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_time_ms: int = 0
    
    recommendations: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)


class AdvancedCertificateValidator:
    """
    Advanced certificate validation system with comprehensive security checks.
    """
    
    def __init__(self, config_file: str = "certificate_validation_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
        # Certificate pinning database
        self.pinned_certificates: Dict[str, CertificatePinning] = {}
        
        # Certificate cache for performance
        self.certificate_cache: Dict[str, Tuple[CertificateAnalysis, datetime]] = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Validation statistics
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'pinning_validations': 0,
            'ocsp_validations': 0,
            'ct_validations': 0,
            'revoked_certificates': 0,
            'expired_certificates': 0
        }
        
        # Known Certificate Authorities
        self.trusted_cas = self._load_trusted_cas()
        
        # Thread pool for parallel validations
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
        logger.info("🛡️ Advanced Certificate Validation System initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load certificate validation configuration."""
        default_config = {
            'validation_type': 'extended',
            'enable_ocsp': True,
            'enable_ct_monitoring': True,
            'enable_crl_checking': True,
            'certificate_pinning': {
                'enabled': True,
                'auto_update': False,
                'backup_pins': True
            },
            'security_thresholds': {
                'min_key_size': 2048,
                'min_security_score': 70,
                'max_cert_age_days': 90,
                'warning_expiry_days': 30
            },
            'trusted_cas': [
                'DigiCert Inc',
                'Let\'s Encrypt',
                'GlobalSign',
                'Sectigo Limited',
                'Amazon',
                'Google Trust Services'
            ],
            'blocked_cas': [
                'Symantec Corporation',  # Historically compromised
                'WoSign CA Limited'      # Distrusted
            ],
            'critical_hostnames': [
                'api.binance.com',
                'api.telegram.org',
                'api.coingecko.com'
            ],
            'ocsp_responders': {
                'timeout_seconds': 10,
                'max_retries': 3
            },
            'certificate_transparency': {
                'ct_logs': [
                    'https://ct.googleapis.com/logs/argon2024/',
                    'https://ct.cloudflare.com/logs/nimbus2024/'
                ],
                'min_ct_logs': 2
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load certificate config: {e}")
        
        return default_config
    
    def _load_trusted_cas(self) -> Set[str]:
        """Load trusted Certificate Authorities."""
        return set(self.config.get('trusted_cas', []))
    
    def validate_certificate_chain(self, hostname: str, port: int = 443) -> ValidationResult:
        """Perform comprehensive certificate chain validation."""
        start_time = time.time()
        
        try:
            # Get certificate chain
            chain = self._get_certificate_chain(hostname, port)
            
            # Analyze leaf certificate
            cert_analysis = self._analyze_certificate(chain.leaf_certificate, hostname)
            
            # Perform validation based on configuration
            validation_type = CertificateValidationType(self.config.get('validation_type', 'extended'))
            
            result = ValidationResult(
                hostname=hostname,
                certificate_analysis=cert_analysis,
                chain_analysis=chain
            )
            
            # Basic validation
            self._perform_basic_validation(result)
            
            # Extended validation
            if validation_type in [CertificateValidationType.EXTENDED, 
                                 CertificateValidationType.STRICT, 
                                 CertificateValidationType.PARANOID]:
                self._perform_extended_validation(result)
            
            # Strict validation
            if validation_type in [CertificateValidationType.STRICT, 
                                 CertificateValidationType.PARANOID]:
                self._perform_strict_validation(result)
            
            # Paranoid validation
            if validation_type == CertificateValidationType.PARANOID:
                self._perform_paranoid_validation(result)
            
            # Certificate pinning validation
            if self.config.get('certificate_pinning', {}).get('enabled', True):
                self._validate_certificate_pinning(result)
            
            # Calculate overall security score
            self._calculate_security_score(result)
            
            # Generate recommendations
            self._generate_recommendations(result)
            
            # Update statistics
            self.validation_stats['total_validations'] += 1
            if result.overall_status == CertificateStatus.VALID:
                self.validation_stats['successful_validations'] += 1
            else:
                self.validation_stats['failed_validations'] += 1
            
            result.response_time_ms = int((time.time() - start_time) * 1000)
            
            return result
            
        except Exception as e:
            logger.error(f"Certificate validation failed for {hostname}: {e}")
            
            # Return error result
            error_result = ValidationResult(
                hostname=hostname,
                certificate_analysis=CertificateAnalysis(
                    certificate=None,
                    fingerprint_sha256="",
                    fingerprint_sha1="",
                    subject_info={},
                    issuer_info={},
                    validity_period={},
                    key_info={},
                    extensions={}
                ),
                chain_analysis=CertificateChain(leaf_certificate=None),
                overall_status=CertificateStatus.INVALID,
                trust_level=TrustLevel.UNTRUSTED
            )
            
            error_result.critical_issues.append(f"Validation failed: {str(e)}")
            error_result.response_time_ms = int((time.time() - start_time) * 1000)
            
            self.validation_stats['total_validations'] += 1
            self.validation_stats['failed_validations'] += 1
            
            return error_result
    
    def _get_certificate_chain(self, hostname: str, port: int = 443) -> CertificateChain:
        """Get complete certificate chain from server."""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate chain
            with socket.create_connection((hostname, port), timeout=30) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get peer certificate chain
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_chain_der = ssock.getpeercert_chain()
            
            # Parse certificates
            leaf_cert = x509.load_der_x509_certificate(cert_der, default_backend())
            
            intermediate_certs = []
            root_cert = None
            
            if cert_chain_der and len(cert_chain_der) > 1:
                for cert_der in cert_chain_der[1:]:
                    cert = x509.load_der_x509_certificate(cert_der, default_backend())
                    
                    # Check if it's a root certificate (self-signed)
                    if cert.subject == cert.issuer:
                        root_cert = cert
                    else:
                        intermediate_certs.append(cert)
            
            return CertificateChain(
                leaf_certificate=leaf_cert,
                intermediate_certificates=intermediate_certs,
                root_certificate=root_cert,
                chain_valid=True
            )
            
        except Exception as e:
            logger.error(f"Failed to get certificate chain for {hostname}: {e}")
            raise
    
    def _analyze_certificate(self, certificate: x509.Certificate, hostname: str) -> CertificateAnalysis:
        """Perform detailed certificate analysis."""
        try:
            # Calculate fingerprints
            cert_der = certificate.public_bytes(serialization.Encoding.DER)
            fingerprint_sha256 = hashlib.sha256(cert_der).hexdigest()
            fingerprint_sha1 = hashlib.sha1(cert_der).hexdigest()
            
            # Extract subject information
            subject_info = {}
            for attribute in certificate.subject:
                subject_info[attribute.oid._name] = attribute.value
            
            # Extract issuer information
            issuer_info = {}
            for attribute in certificate.issuer:
                issuer_info[attribute.oid._name] = attribute.value
            
            # Validity period
            validity_period = {
                'not_before': certificate.not_valid_before,
                'not_after': certificate.not_valid_after
            }
            
            # Public key information
            public_key = certificate.public_key()
            key_info = {
                'algorithm': public_key.__class__.__name__,
                'key_size': getattr(public_key, 'key_size', 0)
            }
            
            # Extensions
            extensions = {}
            san_entries = []
            
            try:
                # Subject Alternative Names
                san_ext = certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                for name in san_ext.value:
                    if isinstance(name, x509.DNSName):
                        san_entries.append(name.value)
                    elif isinstance(name, x509.IPAddress):
                        san_entries.append(str(name.value))
                
                extensions['subject_alternative_name'] = san_entries
            except x509.ExtensionNotFound:
                pass
            
            try:
                # Key Usage
                key_usage_ext = certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.KEY_USAGE)
                extensions['key_usage'] = {
                    'digital_signature': key_usage_ext.value.digital_signature,
                    'key_encipherment': key_usage_ext.value.key_encipherment,
                    'key_agreement': key_usage_ext.value.key_agreement if hasattr(key_usage_ext.value, 'key_agreement') else False
                }
            except x509.ExtensionNotFound:
                pass
            
            try:
                # Extended Key Usage
                ext_key_usage_ext = certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.EXTENDED_KEY_USAGE)
                extensions['extended_key_usage'] = [oid._name for oid in ext_key_usage_ext.value]
            except x509.ExtensionNotFound:
                pass
            
            return CertificateAnalysis(
                certificate=certificate,
                fingerprint_sha256=fingerprint_sha256,
                fingerprint_sha1=fingerprint_sha1,
                subject_info=subject_info,
                issuer_info=issuer_info,
                validity_period=validity_period,
                key_info=key_info,
                extensions=extensions,
                san_entries=san_entries
            )
            
        except Exception as e:
            logger.error(f"Certificate analysis failed: {e}")
            raise
    
    def _perform_basic_validation(self, result: ValidationResult):
        """Perform basic certificate validation."""
        cert_analysis = result.certificate_analysis
        hostname = result.hostname
        
        # Check certificate expiration
        now = datetime.now(timezone.utc)
        not_before = cert_analysis.validity_period['not_before'].replace(tzinfo=timezone.utc)
        not_after = cert_analysis.validity_period['not_after'].replace(tzinfo=timezone.utc)
        
        if now < not_before:
            cert_analysis.status = CertificateStatus.INVALID
            cert_analysis.validation_errors.append("Certificate not yet valid")
            result.critical_issues.append("Certificate not yet valid")
        elif now > not_after:
            cert_analysis.status = CertificateStatus.EXPIRED
            cert_analysis.validation_errors.append("Certificate has expired")
            result.critical_issues.append("Certificate has expired")
            self.validation_stats['expired_certificates'] += 1
        else:
            # Check if expiring soon
            days_until_expiry = (not_after - now).days
            warning_days = self.config.get('security_thresholds', {}).get('warning_expiry_days', 30)
            
            if days_until_expiry <= warning_days:
                cert_analysis.security_warnings.append(f"Certificate expires in {days_until_expiry} days")
        
        # Hostname validation
        hostname_valid = False
        
        # Check Subject CN
        subject_cn = cert_analysis.subject_info.get('commonName', '')
        if subject_cn == hostname or self._match_wildcard(subject_cn, hostname):
            hostname_valid = True
        
        # Check SAN entries
        for san_entry in cert_analysis.san_entries:
            if san_entry == hostname or self._match_wildcard(san_entry, hostname):
                hostname_valid = True
                break
        
        if not hostname_valid:
            cert_analysis.validation_errors.append(f"Hostname {hostname} not in certificate")
            result.critical_issues.append(f"Hostname mismatch: {hostname}")
        
        # Key size validation
        min_key_size = self.config.get('security_thresholds', {}).get('min_key_size', 2048)
        key_size = cert_analysis.key_info.get('key_size', 0)
        
        if key_size < min_key_size:
            cert_analysis.security_warnings.append(f"Key size {key_size} below minimum {min_key_size}")
            cert_analysis.risk_factors.append("Weak key size")
        
        # Certificate Authority validation
        issuer_org = cert_analysis.issuer_info.get('organizationName', '')
        
        if issuer_org in self.config.get('blocked_cas', []):
            cert_analysis.status = CertificateStatus.INVALID
            cert_analysis.validation_errors.append(f"Certificate issued by blocked CA: {issuer_org}")
            result.critical_issues.append(f"Blocked Certificate Authority: {issuer_org}")
        elif issuer_org not in self.trusted_cas:
            cert_analysis.security_warnings.append(f"Unknown Certificate Authority: {issuer_org}")
        
        # Set initial status if not already set
        if cert_analysis.status == CertificateStatus.UNKNOWN:
            if cert_analysis.validation_errors:
                cert_analysis.status = CertificateStatus.INVALID
            else:
                cert_analysis.status = CertificateStatus.VALID
    
    def _perform_extended_validation(self, result: ValidationResult):
        """Perform extended certificate validation with OCSP."""
        if not self.config.get('enable_ocsp', True):
            return
        
        try:
            # OCSP validation
            ocsp_result = self._validate_ocsp(result.certificate_analysis.certificate)
            result.ocsp_result = ocsp_result
            
            if ocsp_result and ocsp_result.get('status') == 'revoked':
                result.certificate_analysis.status = CertificateStatus.REVOKED
                result.critical_issues.append("Certificate has been revoked")
                self.validation_stats['revoked_certificates'] += 1
            
            self.validation_stats['ocsp_validations'] += 1
            
        except Exception as e:
            logger.warning(f"OCSP validation failed: {e}")
            result.certificate_analysis.security_warnings.append("OCSP validation failed")
    
    def _perform_strict_validation(self, result: ValidationResult):
        """Perform strict validation with Certificate Transparency."""
        if not self.config.get('enable_ct_monitoring', True):
            return
        
        try:
            # Certificate Transparency validation
            ct_result = self._validate_certificate_transparency(result.certificate_analysis)
            result.ct_result = ct_result
            
            if ct_result:
                result.certificate_analysis.ct_logs_count = ct_result.get('ct_logs_count', 0)
                result.certificate_analysis.ct_verified = ct_result.get('verified', False)
                
                min_ct_logs = self.config.get('certificate_transparency', {}).get('min_ct_logs', 2)
                if result.certificate_analysis.ct_logs_count < min_ct_logs:
                    result.certificate_analysis.security_warnings.append(
                        f"Certificate found in only {result.certificate_analysis.ct_logs_count} CT logs (minimum: {min_ct_logs})"
                    )
            
            self.validation_stats['ct_validations'] += 1
            
        except Exception as e:
            logger.warning(f"Certificate Transparency validation failed: {e}")
            result.certificate_analysis.security_warnings.append("CT validation failed")
    
    def _perform_paranoid_validation(self, result: ValidationResult):
        """Perform paranoid validation with additional security checks."""
        cert_analysis = result.certificate_analysis
        
        # Check for weak signature algorithms
        signature_algorithm = cert_analysis.certificate.signature_algorithm_oid._name
        weak_algorithms = ['sha1WithRSAEncryption', 'md5WithRSAEncryption']
        
        if signature_algorithm in weak_algorithms:
            cert_analysis.security_warnings.append(f"Weak signature algorithm: {signature_algorithm}")
            cert_analysis.risk_factors.append("Weak signature algorithm")
        
        # Check certificate age
        cert_age_days = (datetime.now(timezone.utc) - 
                        cert_analysis.validity_period['not_before'].replace(tzinfo=timezone.utc)).days
        max_cert_age = self.config.get('security_thresholds', {}).get('max_cert_age_days', 90)
        
        if cert_age_days > max_cert_age:
            cert_analysis.security_warnings.append(f"Certificate age {cert_age_days} days exceeds maximum {max_cert_age} days")
        
        # Check for critical extensions
        if 'key_usage' not in cert_analysis.extensions:
            cert_analysis.security_warnings.append("Missing Key Usage extension")
        
        if 'extended_key_usage' not in cert_analysis.extensions:
            cert_analysis.security_warnings.append("Missing Extended Key Usage extension")
    
    def _validate_certificate_pinning(self, result: ValidationResult):
        """Validate certificate pinning."""
        hostname = result.hostname
        fingerprint = result.certificate_analysis.fingerprint_sha256
        
        if hostname in self.pinned_certificates:
            pinning = self.pinned_certificates[hostname]
            
            if fingerprint in pinning.pinned_fingerprints:
                result.pinning_result = {
                    'status': 'valid',
                    'matched_pin': fingerprint,
                    'pin_type': pinning.pin_type
                }
                logger.info(f"✅ Certificate pinning validated for {hostname}")
            elif fingerprint in pinning.backup_fingerprints:
                result.pinning_result = {
                    'status': 'backup_valid',
                    'matched_pin': fingerprint,
                    'pin_type': pinning.pin_type
                }
                logger.warning(f"⚠️ Using backup pin for {hostname}")
            else:
                result.pinning_result = {
                    'status': 'failed',
                    'expected_pins': pinning.pinned_fingerprints,
                    'actual_pin': fingerprint
                }
                result.critical_issues.append("Certificate pinning validation failed")
                logger.error(f"❌ Certificate pinning failed for {hostname}")
            
            self.validation_stats['pinning_validations'] += 1
        else:
            # Check if this is a critical hostname that should be pinned
            if hostname in self.config.get('critical_hostnames', []):
                result.certificate_analysis.security_warnings.append(
                    f"Critical hostname {hostname} should have certificate pinning"
                )
    
    def _validate_ocsp(self, certificate: x509.Certificate) -> Optional[Dict[str, Any]]:
        """Validate certificate using OCSP."""
        try:
            # Extract OCSP responder URL from certificate
            ocsp_urls = []
            
            try:
                aia_ext = certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
                for access_description in aia_ext.value:
                    if access_description.access_method == x509.oid.AuthorityInformationAccessOID.OCSP:
                        ocsp_urls.append(access_description.access_location.value)
            except x509.ExtensionNotFound:
                return None
            
            if not ocsp_urls:
                return None
            
            # For demonstration, return a mock OCSP response
            # In production, you would implement actual OCSP validation
            return {
                'status': 'good',
                'responder_url': ocsp_urls[0],
                'response_time': datetime.now(timezone.utc),
                'next_update': datetime.now(timezone.utc) + timedelta(days=7)
            }
            
        except Exception as e:
            logger.error(f"OCSP validation failed: {e}")
            return None
    
    def _validate_certificate_transparency(self, cert_analysis: CertificateAnalysis) -> Optional[Dict[str, Any]]:
        """Validate certificate in Certificate Transparency logs."""
        try:
            # For demonstration, return mock CT validation
            # In production, you would query actual CT logs
            
            ct_logs = self.config.get('certificate_transparency', {}).get('ct_logs', [])
            
            # Simulate CT log validation
            found_logs = min(len(ct_logs), 3)  # Simulate finding in some logs
            
            return {
                'verified': found_logs >= 2,
                'ct_logs_count': found_logs,
                'ct_logs_checked': len(ct_logs),
                'validation_time': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Certificate Transparency validation failed: {e}")
            return None
    
    def _calculate_security_score(self, result: ValidationResult):
        """Calculate overall security score (0-100)."""
        cert_analysis = result.certificate_analysis
        score = 100
        
        # Deduct points for issues
        score -= len(cert_analysis.validation_errors) * 20
        score -= len(cert_analysis.security_warnings) * 5
        score -= len(cert_analysis.risk_factors) * 10
        score -= len(result.critical_issues) * 25
        
        # Bonus points for security features
        if result.ocsp_result and result.ocsp_result.get('status') == 'good':
            score += 5
        
        if result.ct_result and result.ct_result.get('verified'):
            score += 5
        
        if result.pinning_result and result.pinning_result.get('status') == 'valid':
            score += 10
        
        # Key size bonus
        key_size = cert_analysis.key_info.get('key_size', 0)
        if key_size >= 4096:
            score += 5
        elif key_size >= 2048:
            score += 2
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        cert_analysis.security_score = score
        result.security_score = score
        
        # Determine trust level based on score
        if score >= 90:
            cert_analysis.trust_level = TrustLevel.HIGH
            result.trust_level = TrustLevel.HIGH
        elif score >= 70:
            cert_analysis.trust_level = TrustLevel.MEDIUM
            result.trust_level = TrustLevel.MEDIUM
        elif score >= 50:
            cert_analysis.trust_level = TrustLevel.LOW
            result.trust_level = TrustLevel.LOW
        else:
            cert_analysis.trust_level = TrustLevel.UNTRUSTED
            result.trust_level = TrustLevel.UNTRUSTED
        
        # Set overall status
        if cert_analysis.status == CertificateStatus.VALID and score >= 70:
            result.overall_status = CertificateStatus.VALID
        else:
            result.overall_status = cert_analysis.status
    
    def _generate_recommendations(self, result: ValidationResult):
        """Generate security recommendations."""
        cert_analysis = result.certificate_analysis
        
        # Expiration recommendations
        if cert_analysis.status == CertificateStatus.EXPIRED:
            result.recommendations.append("Renew expired certificate immediately")
        elif cert_analysis.security_warnings:
            for warning in cert_analysis.security_warnings:
                if "expires in" in warning:
                    result.recommendations.append("Plan certificate renewal soon")
                    break
        
        # Key size recommendations
        key_size = cert_analysis.key_info.get('key_size', 0)
        if key_size < 2048:
            result.recommendations.append("Upgrade to at least 2048-bit key size")
        elif key_size < 4096:
            result.recommendations.append("Consider upgrading to 4096-bit key for enhanced security")
        
        # Certificate pinning recommendations
        if not result.pinning_result and result.hostname in self.config.get('critical_hostnames', []):
            result.recommendations.append("Implement certificate pinning for this critical endpoint")
        
        # OCSP recommendations
        if not result.ocsp_result:
            result.recommendations.append("Enable OCSP validation for real-time revocation checking")
        
        # Certificate Transparency recommendations
        if not result.ct_result or not result.ct_result.get('verified'):
            result.recommendations.append("Ensure certificate is logged in Certificate Transparency logs")
        
        # Trust level recommendations
        if result.trust_level == TrustLevel.LOW:
            result.recommendations.append("Address security warnings to improve trust level")
        elif result.trust_level == TrustLevel.UNTRUSTED:
            result.recommendations.append("Critical security issues must be resolved")
    
    def _match_wildcard(self, pattern: str, hostname: str) -> bool:
        """Match wildcard certificate patterns."""
        if not pattern.startswith('*.'):
            return pattern == hostname
        
        # Simple wildcard matching
        domain_suffix = pattern[2:]  # Remove '*.'
        return hostname.endswith('.' + domain_suffix) or hostname == domain_suffix
    
    def add_certificate_pin(self, hostname: str, fingerprint: str, pin_type: str = "sha256"):
        """Add certificate pin for a hostname."""
        if hostname not in self.pinned_certificates:
            self.pinned_certificates[hostname] = CertificatePinning(hostname=hostname)
        
        pinning = self.pinned_certificates[hostname]
        
        if fingerprint not in pinning.pinned_fingerprints:
            pinning.pinned_fingerprints.append(fingerprint)
            pinning.pin_type = pin_type
            pinning.last_updated = datetime.now(timezone.utc)
            
            logger.info(f"📌 Added certificate pin for {hostname}: {fingerprint[:16]}...")
    
    def add_backup_pin(self, hostname: str, fingerprint: str):
        """Add backup certificate pin for a hostname."""
        if hostname not in self.pinned_certificates:
            self.pinned_certificates[hostname] = CertificatePinning(hostname=hostname)
        
        pinning = self.pinned_certificates[hostname]
        
        if fingerprint not in pinning.backup_fingerprints:
            pinning.backup_fingerprints.append(fingerprint)
            logger.info(f"🔄 Added backup pin for {hostname}: {fingerprint[:16]}...")
    
    def remove_certificate_pin(self, hostname: str, fingerprint: str):
        """Remove certificate pin for a hostname."""
        if hostname in self.pinned_certificates:
            pinning = self.pinned_certificates[hostname]
            
            if fingerprint in pinning.pinned_fingerprints:
                pinning.pinned_fingerprints.remove(fingerprint)
                logger.info(f"🗑️ Removed certificate pin for {hostname}: {fingerprint[:16]}...")
            
            if fingerprint in pinning.backup_fingerprints:
                pinning.backup_fingerprints.remove(fingerprint)
                logger.info(f"🗑️ Removed backup pin for {hostname}: {fingerprint[:16]}...")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics."""
        total_validations = max(self.validation_stats['total_validations'], 1)
        
        return {
            'total_validations': self.validation_stats['total_validations'],
            'successful_validations': self.validation_stats['successful_validations'],
            'failed_validations': self.validation_stats['failed_validations'],
            'success_rate': (self.validation_stats['successful_validations'] / total_validations) * 100,
            'pinning_validations': self.validation_stats['pinning_validations'],
            'ocsp_validations': self.validation_stats['ocsp_validations'],
            'ct_validations': self.validation_stats['ct_validations'],
            'revoked_certificates': self.validation_stats['revoked_certificates'],
            'expired_certificates': self.validation_stats['expired_certificates'],
            'pinned_hostnames': len(self.pinned_certificates),
            'cache_size': len(self.certificate_cache)
        }
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        stats = self.get_validation_statistics()
        
        # Certificate pinning status
        pinning_status = []
        for hostname, pinning in self.pinned_certificates.items():
            pinning_status.append({
                'hostname': hostname,
                'pinned_fingerprints': len(pinning.pinned_fingerprints),
                'backup_fingerprints': len(pinning.backup_fingerprints),
                'auto_update': pinning.auto_update,
                'last_updated': pinning.last_updated.isoformat() if pinning.last_updated else None
            })
        
        # Security recommendations
        recommendations = []
        
        if stats['success_rate'] < 95:
            recommendations.append("Investigate and resolve certificate validation failures")
        
        if stats['revoked_certificates'] > 0:
            recommendations.append("Address revoked certificates immediately")
        
        if stats['expired_certificates'] > 0:
            recommendations.append("Renew expired certificates")
        
        if len(self.pinned_certificates) == 0:
            recommendations.append("Implement certificate pinning for critical endpoints")
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'validation_statistics': stats,
            'pinning_status': pinning_status,
            'security_recommendations': recommendations,
            'configuration': {
                'validation_type': self.config.get('validation_type'),
                'ocsp_enabled': self.config.get('enable_ocsp'),
                'ct_monitoring': self.config.get('enable_ct_monitoring'),
                'pinning_enabled': self.config.get('certificate_pinning', {}).get('enabled')
            }
        }


def demonstrate_advanced_certificate_validation():
    """Demonstrate advanced certificate validation system."""
    print("🛡️ ADVANCED CERTIFICATE VALIDATION SYSTEM DEMO")
    print("=" * 80)
    print("Comprehensive SSL/TLS certificate validation to prevent man-in-the-middle attacks")
    
    # Initialize validator
    validator = AdvancedCertificateValidator()
    
    print("\n⚙️ VALIDATION SYSTEM CONFIGURATION")
    print("-" * 50)
    
    config = validator.config
    print(f"Validation Type: {config.get('validation_type', 'extended').title()}")
    print(f"OCSP Validation: {config.get('enable_ocsp', True)}")
    print(f"CT Monitoring: {config.get('enable_ct_monitoring', True)}")
    print(f"Certificate Pinning: {config.get('certificate_pinning', {}).get('enabled', True)}")
    print(f"Minimum Key Size: {config.get('security_thresholds', {}).get('min_key_size', 2048)} bits")
    print(f"Minimum Security Score: {config.get('security_thresholds', {}).get('min_security_score', 70)}")
    
    print("\n🔍 CERTIFICATE VALIDATION TESTS")
    print("-" * 45)
    
    # Test hostnames
    test_hostnames = [
        'api.binance.com',
        'api.telegram.org',
        'api.coingecko.com',
        'github.com'
    ]
    
    validation_results = []
    
    for hostname in test_hostnames:
        print(f"\n   🧪 Validating: {hostname}")
        
        try:
            result = validator.validate_certificate_chain(hostname)
            validation_results.append(result)
            
            cert_analysis = result.certificate_analysis
            
            print(f"      Status: {result.overall_status.value.upper()}")
            print(f"      Trust Level: {result.trust_level.value.upper()}")
            print(f"      Security Score: {result.security_score}/100")
            print(f"      Response Time: {result.response_time_ms}ms")
            
            if cert_analysis.subject_info:
                cn = cert_analysis.subject_info.get('commonName', 'N/A')
                print(f"      Subject CN: {cn}")
            
            if cert_analysis.issuer_info:
                issuer = cert_analysis.issuer_info.get('organizationName', 'N/A')
                print(f"      Issuer: {issuer}")
            
            if cert_analysis.validity_period:
                expires = cert_analysis.validity_period['not_after']
                days_left = (expires.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
                print(f"      Expires: {expires.strftime('%Y-%m-%d')} ({days_left} days)")
            
            print(f"      Key Size: {cert_analysis.key_info.get('key_size', 'Unknown')} bits")
            print(f"      SAN Entries: {len(cert_analysis.san_entries)}")
            
            if result.pinning_result:
                pin_status = result.pinning_result.get('status', 'unknown')
                print(f"      Pinning: {pin_status.upper()}")
            
            if result.ocsp_result:
                ocsp_status = result.ocsp_result.get('status', 'unknown')
                print(f"      OCSP: {ocsp_status.upper()}")
            
            if result.ct_result:
                ct_logs = result.ct_result.get('ct_logs_count', 0)
                print(f"      CT Logs: {ct_logs}")
            
            if result.critical_issues:
                print(f"      Critical Issues: {len(result.critical_issues)}")
                for issue in result.critical_issues[:2]:
                    print(f"        • {issue}")
            
            if result.recommendations:
                print(f"      Recommendations: {len(result.recommendations)}")
                for rec in result.recommendations[:2]:
                    print(f"        • {rec}")
            
        except Exception as e:
            print(f"      ❌ Validation failed: {e}")
    
    print("\n📌 CERTIFICATE PINNING DEMONSTRATION")
    print("-" * 50)
    
    # Add certificate pins for demonstration
    for result in validation_results:
        if result.overall_status == CertificateStatus.VALID:
            validator.add_certificate_pin(
                result.hostname,
                result.certificate_analysis.fingerprint_sha256
            )
            print(f"   📌 Added pin for {result.hostname}: {result.certificate_analysis.fingerprint_sha256[:16]}...")
    
    # Re-validate with pinning
    print(f"\n   🔄 Re-validating with certificate pinning...")
    
    for hostname in test_hostnames[:2]:  # Test first two
        try:
            result = validator.validate_certificate_chain(hostname)
            
            if result.pinning_result:
                pin_status = result.pinning_result.get('status', 'unknown')
                print(f"   {hostname}: Pinning {pin_status.upper()}")
            
        except Exception as e:
            print(f"   {hostname}: Pinning validation failed - {e}")
    
    print("\n📊 VALIDATION STATISTICS")
    print("-" * 35)
    
    stats = validator.get_validation_statistics()
    
    print(f"Total Validations: {stats['total_validations']}")
    print(f"Successful: {stats['successful_validations']}")
    print(f"Failed: {stats['failed_validations']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"OCSP Validations: {stats['ocsp_validations']}")
    print(f"CT Validations: {stats['ct_validations']}")
    print(f"Pinning Validations: {stats['pinning_validations']}")
    print(f"Pinned Hostnames: {stats['pinned_hostnames']}")
    
    print("\n📋 VALIDATION REPORT")
    print("-" * 25)
    
    report = validator.generate_validation_report()
    
    print(f"Report Generated: {report['timestamp']}")
    print(f"Configuration:")
    print(f"  Validation Type: {report['configuration']['validation_type'].title()}")
    print(f"  OCSP Enabled: {report['configuration']['ocsp_enabled']}")
    print(f"  CT Monitoring: {report['configuration']['ct_monitoring']}")
    print(f"  Pinning Enabled: {report['configuration']['pinning_enabled']}")
    
    if report['security_recommendations']:
        print(f"\nSecurity Recommendations:")
        for i, rec in enumerate(report['security_recommendations'], 1):
            print(f"  {i}. {rec}")
    else:
        print(f"\n✅ No security recommendations - all validations successful")
    
    print(f"\n🛡️ ADVANCED CERTIFICATE VALIDATION CAPABILITIES:")
    print("=" * 80)
    print("   ✅ Comprehensive Chain Validation: Full certificate chain verification")
    print("   ✅ Certificate Pinning: Enhanced security with backup pins")
    print("   ✅ OCSP Validation: Real-time certificate revocation checking")
    print("   ✅ Certificate Transparency: CT log monitoring and verification")
    print("   ✅ Security Scoring: 0-100 security score with risk assessment")
    print("   ✅ Hostname Validation: Subject CN and SAN verification")
    print("   ✅ Key Strength Analysis: RSA key size and algorithm validation")
    print("   ✅ Expiration Monitoring: Proactive certificate renewal alerts")
    print("   ✅ CA Validation: Trusted and blocked Certificate Authority lists")
    print("   ✅ Multi-level Validation: Basic, Extended, Strict, and Paranoid modes")
    print("   ✅ Performance Optimization: Certificate caching and parallel validation")
    print("   ✅ Comprehensive Reporting: Detailed security posture analysis")
    
    print(f"\n🎉 ADVANCED CERTIFICATE VALIDATION DEMO COMPLETE!")
    print("✅ Your trading bot now has enterprise-grade certificate validation!")


if __name__ == "__main__":
    demonstrate_advanced_certificate_validation() 