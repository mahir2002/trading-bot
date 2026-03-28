#!/usr/bin/env python3
"""
🚀 Scalable Trading Data Optimization System
Comprehensive solution for handling large numbers of trading pairs and high-frequency updates
with optimized data fetching, caching, batch processing, and rendering.
Key Features:
- Replaces polling with WebSocket streaming
- Batch API requests for multiple trading pairs
- Multi-level caching with compression
- Priority-based data updates
- Connection pooling and request multiplexing
- Memory-efficient data structures
- Progressive data loading
- Optimized rendering for large datasets
"""

import asyncio
import aiohttp
import redis
import json
import gzip
import pickle
import time
import threading
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import numpy as np
from contextlib import asynccontextmanager
import weakref
import gc
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

# WebSocket and streaming imports
import websockets
from websockets.server import serve
from websockets.exceptions import ConnectionClosed

# Dashboard integration
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

@dataclass
class TradingPairMetrics:
    """Optimized trading pair data structure"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    priority: int = 1  # 1=high, 2=medium, 3=low
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'change_24h': self.change_24h,
            'volume_24h': self.volume_24h,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority
        }

@dataclass 
class DataSubscription:
    """Client subscription with filtering and frequency control"""
    client_id: str
    symbols: Set[str]
    update_frequency: float  # seconds
    priority_filter: Set[int]  # priority levels to receive
    last_update: datetime
    data_types: Set[str]  # 'price', 'volume', 'ohlcv', 'orderbook'
    compression_enabled: bool = True

class APIPermissionValidator:
    """Validates and enforces Principle of Least Privilege for trading API keys"""
    
    def __init__(self):
        self.required_permissions = {
            'SPOT_TRADING': {
                'required': True,
                'risk_level': 'MEDIUM',
                'justification': 'Execute buy/sell orders for trading strategy',
                'financial_impact': 'TRADING_CAPITAL_ONLY'
            },
            'USER_DATA_STREAM': {
                'required': True,
                'risk_level': 'LOW',
                'justification': 'Monitor account balance and order status',
                'financial_impact': 'READ_ONLY'
            },
            'MARKET_DATA': {
                'required': True,
                'risk_level': 'LOW',
                'justification': 'Fetch price data for trading decisions',
                'financial_impact': 'NONE'
            }
        }
        
        self.prohibited_permissions = {
            'WITHDRAW': {
                'risk_level': 'CRITICAL',
                'financial_impact': 'TOTAL_ACCOUNT_LOSS',
                'description': 'Can withdraw all funds - NEVER required for trading'
            },
            'SUB_ACCOUNT_TRANSFER': {
                'risk_level': 'HIGH',
                'financial_impact': 'FUNDS_MOVEMENT', 
                'description': 'Can move funds between accounts'
            },
            'UNIVERSAL_TRANSFER': {
                'risk_level': 'HIGH',
                'financial_impact': 'FUNDS_MOVEMENT',
                'description': 'Can transfer to external accounts'
            },
            'MARGIN_TRADING': {
                'risk_level': 'HIGH',
                'financial_impact': 'LEVERAGE_EXPOSURE',
                'description': 'Can trade with borrowed funds - high liquidation risk'
            },
            'FUTURES_TRADING': {
                'risk_level': 'HIGH', 
                'financial_impact': 'LEVERAGE_EXPOSURE',
                'description': 'Can trade futures with high leverage'
            },
            'VANILLA_OPTIONS': {
                'risk_level': 'HIGH',
                'financial_impact': 'COMPLEX_DERIVATIVES',
                'description': 'Can trade options - complex risk profile'
            }
        }
        
        self.ip_restrictions_required = True
        self.max_daily_trading_limit = None  # Set based on risk tolerance
        
    async def validate_api_permissions(self, api_session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Validate API key permissions against security requirements"""
        
        validation_result = {
            'is_secure': True,
            'warnings': [],
            'critical_issues': [],
            'recommendations': [],
            'permission_audit': {}
        }
        
        try:
            # Get current API key permissions
            permissions = await self._get_api_key_permissions(api_session)
            validation_result['permission_audit'] = permissions
            
            # Check for prohibited permissions
            for perm_name, perm_info in self.prohibited_permissions.items():
                if permissions.get(perm_name, False):
                    validation_result['critical_issues'].append({
                        'permission': perm_name,
                        'risk_level': perm_info['risk_level'],
                        'financial_impact': perm_info['financial_impact'],
                        'recommendation': f"IMMEDIATELY disable {perm_name} permission",
                        'description': perm_info['description']
                    })
                    validation_result['is_secure'] = False
            
            # Check for required permissions
            for perm_name, perm_info in self.required_permissions.items():
                if not permissions.get(perm_name, False):
                    validation_result['warnings'].append({
                        'permission': perm_name,
                        'issue': 'Missing required permission',
                        'impact': 'Bot functionality may be limited',
                        'justification': perm_info['justification']
                    })
            
            # Check IP restrictions
            if not permissions.get('ip_restricted', False):
                validation_result['critical_issues'].append({
                    'permission': 'IP_RESTRICTIONS',
                    'risk_level': 'HIGH',
                    'financial_impact': 'UNAUTHORIZED_ACCESS',
                    'recommendation': 'Enable IP restrictions to your server IPs only',
                    'description': 'API key can be used from any IP address'
                })
                validation_result['is_secure'] = False
            
            # Generate security recommendations
            validation_result['recommendations'] = self._generate_security_recommendations(permissions)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate API permissions: {e}")
            validation_result['critical_issues'].append({
                'permission': 'VALIDATION_ERROR',
                'risk_level': 'UNKNOWN',
                'description': f'Could not validate permissions: {e}',
                'recommendation': 'Manually verify API key permissions'
            })
            validation_result['is_secure'] = False
            return validation_result
    
    async def _get_api_key_permissions(self, api_session: aiohttp.ClientSession) -> Dict[str, bool]:
        """Get current API key permissions from exchange"""
        try:
            # Binance API endpoint for account information
            url = "https://api.binance.com/api/v3/account"
            
            async with api_session.get(url) as response:
                if response.status == 200:
                    account_info = await response.json()
                    
                    # Extract permissions from account info
                    permissions = {
                        'SPOT_TRADING': account_info.get('canTrade', False),
                        'USER_DATA_STREAM': True,  # If we can call account endpoint
                        'MARKET_DATA': True,  # Always available
                        'WITHDRAW': account_info.get('canWithdraw', False),
                        'MARGIN_TRADING': 'MARGIN' in account_info.get('accountType', ''),
                        'FUTURES_TRADING': 'FUTURES' in account_info.get('accountType', ''),
                        'ip_restricted': True  # Need to check via different endpoint
                    }
                    
                    return permissions
                else:
                    logger.error(f"Failed to get account info: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting API permissions: {e}")
            return {}
    
    def _generate_security_recommendations(self, permissions: Dict[str, bool]) -> List[str]:
        """Generate security recommendations based on current permissions"""
        recommendations = []
        
        # Basic security recommendations
        recommendations.extend([
            "🔒 Enable IP restrictions to your server IPs only",
            "🔒 Set daily trading limits on your account", 
            "🔒 Enable 2FA on your exchange account",
            "🔒 Regularly rotate API keys (monthly recommended)",
            "🔒 Monitor API key usage through exchange logs",
            "🔒 Use separate API keys for different trading strategies",
            "🔒 Never share API keys or store them in plain text"
        ])
        
        # Permission-specific recommendations
        if permissions.get('WITHDRAW', False):
            recommendations.insert(0, "🚨 CRITICAL: Disable withdrawal permissions immediately")
        
        if permissions.get('MARGIN_TRADING', False):
            recommendations.insert(0, "⚠️  Consider disabling margin trading unless specifically required")
        
        if permissions.get('FUTURES_TRADING', False):
            recommendations.insert(0, "⚠️  Consider disabling futures trading unless specifically required")
        
        return recommendations
    
    def get_minimal_permission_template(self, exchange: str = 'binance') -> Dict[str, Any]:
        """Get template for minimal required permissions"""
        if exchange.lower() == 'binance':
            return {
                'api_restrictions': {
                    'enable_reading': True,
                    'enable_spot_and_margin_trading': True,  # Spot only
                    'enable_withdrawals': False,  # NEVER enable
                    'enable_internal_transfer': False,  # NEVER enable
                    'permits_universal_transfer': False,  # NEVER enable
                    'enable_vanilla_options': False,  # Unless specifically needed
                    'enable_margin': False,  # Unless specifically needed
                    'ip_restrict_access': True  # ALWAYS enable
                },
                'recommended_daily_limits': {
                    'max_order_value_usdt': 10000,  # Adjust based on capital
                    'max_daily_trades': 1000,
                    'max_position_size_percent': 10  # 10% of account max
                },
                'security_settings': {
                    'whitelist_ips': ['YOUR_SERVER_IP'],
                    'api_key_expiry_days': 30,
                    'enable_order_rate_limit': True
                }
            }
        
        return {}

class ProductionSecretManager:
    """Production-grade secret management for trading bot"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.secrets_cache = {}
        self.permission_validator = APIPermissionValidator()
        self.rotation_system = None  # Will be initialized when needed
        self.encryption_system = None  # Will be initialized when needed
        
    async def get_secret(self, secret_name: str) -> str:
        """Get secret with multiple fallback methods for different deployment scenarios"""
        
        # Cache check (encrypted cache)
        if secret_name in self.secrets_cache:
            return await self._decrypt_cached_secret(secret_name)
            
        secret_value = None
        
        try:
            if self.environment == "production":
                # 1. Try Docker Secrets first (Docker Swarm)
                secret_value = self._read_docker_secret(secret_name)
                
                if not secret_value:
                    # 2. Try Kubernetes Secrets (injected as env vars)
                    secret_value = os.environ.get(secret_name.upper())
                
                if not secret_value:
                    # 3. Try AWS Secrets Manager
                    secret_value = await self._get_aws_secret(secret_name)
                    
                if not secret_value:
                    # 4. Try environment variables as last resort
                    secret_value = os.environ.get(secret_name.upper())
                    
            elif self.environment == "staging":
                # Staging: Kubernetes secrets or environment variables
                secret_value = os.environ.get(secret_name.upper())
                
            else:  # development
                # Development: .env file (for local development only)
                from dotenv import load_dotenv
                load_dotenv()
                secret_value = os.environ.get(secret_name.upper())
            
            if not secret_value:
                raise ValueError(f"Secret '{secret_name}' not found in any configured source")
                
            # Cache the secret (encrypted)
            await self._cache_encrypted_secret(secret_name, secret_value)
            return secret_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            raise
    
    def _read_docker_secret(self, secret_name: str) -> Optional[str]:
        """Read Docker secret from /run/secrets/"""
        try:
            secret_path = Path(f'/run/secrets/{secret_name}')
            if secret_path.exists():
                return secret_path.read_text().strip()
        except Exception as e:
            logger.debug(f"Docker secret not found for {secret_name}: {e}")
        return None
    
    async def _get_aws_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            session = boto3.Session()
            client = session.client('secretsmanager')
            response = client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except ClientError as e:
            logger.debug(f"AWS secret not found for {secret_name}: {e}")
        except Exception as e:
            logger.debug(f"AWS Secrets Manager error: {e}")
        
        return None
    
    async def _initialize_encryption_system(self):
        """Initialize encryption system for secure secret handling"""
        try:
            if self.encryption_system is None:
                from encryption_security_system import SecureAPIKeyManager
                self.encryption_system = SecureAPIKeyManager()
                logger.info("🔐 Encryption system initialized for secret management")
        except ImportError:
            logger.warning("⚠️  Encryption system not available - using plaintext cache")
        except Exception as e:
            logger.error(f"Failed to initialize encryption system: {e}")
    
    async def _cache_encrypted_secret(self, secret_name: str, secret_value: str):
        """Cache secret with encryption"""
        try:
            await self._initialize_encryption_system()
            
            if self.encryption_system:
                from encryption_security_system import StorageType
                # Encrypt secret for cache storage
                encrypted_data = await self.encryption_system.store_api_key(
                    "cache", secret_name, secret_value, StorageType.CACHE
                )
                self.secrets_cache[secret_name] = encrypted_data
            else:
                # Fallback to plaintext cache (development only)
                self.secrets_cache[secret_name] = secret_value
                logger.warning(f"⚠️  Storing {secret_name} in plaintext cache")
        except Exception as e:
            logger.error(f"Failed to encrypt secret for cache: {e}")
            # Fallback to plaintext
            self.secrets_cache[secret_name] = secret_value
    
    async def _decrypt_cached_secret(self, secret_name: str) -> str:
        """Decrypt secret from cache"""
        try:
            await self._initialize_encryption_system()
            
            cached_data = self.secrets_cache[secret_name]
            
            if self.encryption_system and isinstance(cached_data, str) and cached_data.startswith('{'):
                # Decrypt encrypted cache entry
                key_data = await self.encryption_system.retrieve_api_key(cached_data)
                return key_data['api_secret']  # Return the secret value
            else:
                # Return plaintext cache entry
                return cached_data
        except Exception as e:
            logger.error(f"Failed to decrypt cached secret: {e}")
            # Return cached value as-is
            return self.secrets_cache[secret_name]
    
    async def validate_security_setup(self, api_session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Comprehensive security validation"""
        
        security_report = {
            'environment': self.environment,
            'timestamp': time.time(),
            'security_score': 0,
            'max_security_score': 100,
            'validation_results': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Validate API permissions
        permission_results = await self.permission_validator.validate_api_permissions(api_session)
        security_report['validation_results']['api_permissions'] = permission_results
        
        # Check API key rotation status
        rotation_status = await self._check_rotation_status()
        security_report['validation_results']['key_rotation'] = rotation_status
        
        # Calculate security score
        score = 100
        
        # Deduct points for critical issues
        critical_issues = len(permission_results.get('critical_issues', []))
        score -= critical_issues * 30  # 30 points per critical issue
        
        # Deduct points for warnings
        warnings = len(permission_results.get('warnings', []))
        score -= warnings * 10  # 10 points per warning
        
        # Bonus points for production environment
        if self.environment == 'production':
            score += 10
        
        security_report['security_score'] = max(0, score)
        
        # Determine overall status
        if score >= 90:
            security_report['overall_status'] = 'EXCELLENT'
        elif score >= 75:
            security_report['overall_status'] = 'GOOD'
        elif score >= 50:
            security_report['overall_status'] = 'ACCEPTABLE'
        else:
            security_report['overall_status'] = 'UNSAFE'
        
        return security_report
    
    async def _check_rotation_status(self) -> Dict[str, Any]:
        """Check API key rotation status"""
        
        rotation_status = {
            'rotation_overdue': False,
            'days_since_last_rotation': 0,
            'rotation_policy_days': 30,
            'next_scheduled_rotation': None,
            'recommendations': []
        }
        
        try:
            # Check last rotation date from environment or secret metadata
            last_rotation_env = os.environ.get('LAST_API_KEY_ROTATION', '')
            rotation_policy_days = int(os.environ.get('API_KEY_ROTATION_DAYS', 30))
            
            if last_rotation_env:
                try:
                    from datetime import datetime
                    last_rotation = datetime.fromisoformat(last_rotation_env)
                    days_since = (datetime.now() - last_rotation).days
                    
                    rotation_status.update({
                        'days_since_last_rotation': days_since,
                        'rotation_policy_days': rotation_policy_days,
                        'rotation_overdue': days_since >= rotation_policy_days
                    })
                    
                    # Calculate next rotation date
                    from datetime import timedelta
                    next_rotation = last_rotation + timedelta(days=rotation_policy_days)
                    rotation_status['next_scheduled_rotation'] = next_rotation.isoformat()
                    
                    # Generate recommendations
                    if days_since >= rotation_policy_days:
                        rotation_status['recommendations'].append(
                            f"🚨 API key rotation is {days_since - rotation_policy_days} days overdue"
                        )
                    elif days_since >= rotation_policy_days - 5:
                        rotation_status['recommendations'].append(
                            f"⚠️  API key rotation due in {rotation_policy_days - days_since} days"
                        )
                    else:
                        rotation_status['recommendations'].append(
                            f"✅ API key rotation is up to date"
                        )
                        
                except ValueError:
                    rotation_status['recommendations'].append(
                        "⚠️  Invalid last rotation date format"
                    )
            else:
                rotation_status['recommendations'].append(
                    "⚠️  No API key rotation history found - consider setting up rotation schedule"
                )
                rotation_status['rotation_overdue'] = True
            
        except Exception as e:
            logger.error(f"Failed to check rotation status: {e}")
            rotation_status['recommendations'].append(
                f"❌ Failed to check rotation status: {e}"
            )
        
        return rotation_status
    
    async def initialize_rotation_system(self):
        """Initialize API key rotation system"""
        try:
            # Only import and initialize if not already done
            if self.rotation_system is None:
                from api_key_rotation_system import APIKeyRotationSystem
                self.rotation_system = APIKeyRotationSystem(environment=self.environment)
                logger.info("🔄 API key rotation system initialized")
        except ImportError:
            logger.warning("⚠️  API key rotation system not available")
        except Exception as e:
            logger.error(f"Failed to initialize rotation system: {e}")
    
    async def schedule_key_rotation(self, exchange: str = "binance", 
                                  trigger: str = "scheduled") -> Optional[str]:
        """Schedule API key rotation"""
        
        try:
            await self.initialize_rotation_system()
            
            if self.rotation_system:
                from api_key_rotation_system import RotationTrigger
                trigger_enum = RotationTrigger(trigger)
                
                rotation_id = await self.rotation_system.schedule_rotation(
                    exchange, trigger_enum
                )
                
                logger.info(f"🔄 Scheduled rotation {rotation_id} for {exchange}")
                return rotation_id
            else:
                logger.warning("⚠️  Rotation system not available")
                return None
                
        except Exception as e:
            logger.error(f"Failed to schedule rotation: {e}")
            return None

class ScalableDataOptimizer:
    """Advanced data optimization system with production-grade secret management"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.secret_manager = ProductionSecretManager(environment)
        
        # Configuration
        self.config = {
            'websocket_port': int(os.environ.get('WEBSOCKET_PORT', 8766)),
            'batch_size': int(os.environ.get('BATCH_SIZE', 100)),
            'max_concurrent_requests': int(os.environ.get('MAX_CONCURRENT_REQUESTS', 5)),
            'cache_ttl': int(os.environ.get('CACHE_TTL', 300)),
            'rate_limit_per_second': int(os.environ.get('RATE_LIMIT_PER_SECOND', 10)),
            'redis_host': os.environ.get('REDIS_HOST', 'localhost'),
            'redis_port': int(os.environ.get('REDIS_PORT', 6379)),
            'redis_db': int(os.environ.get('REDIS_DB', 0)),
        }
        
        # Initialize components
        self.api_session = None
        self.redis_client = None
        self.websocket_server = None
        self.connected_clients = set()
        self.data_cache = {}
        self.last_api_call = {}
        self.rate_limiter = asyncio.Semaphore(self.config['rate_limit_per_second'])
        
        # Performance metrics
        self.metrics = {
            'total_api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'websocket_messages_sent': 0,
            'average_response_time': 0.0,
            'active_connections': 0
        }
        
        # Priority-based update intervals (seconds)
        self.update_intervals = {
            'critical': float(os.environ.get('UPDATE_INTERVAL_CRITICAL', 0.1)),
            'high': float(os.environ.get('UPDATE_INTERVAL_HIGH', 0.5)),
            'medium': float(os.environ.get('UPDATE_INTERVAL_MEDIUM', 1.0)),
            'low': float(os.environ.get('UPDATE_INTERVAL_LOW', 5.0))
        }
        
    async def initialize(self):
        """Initialize all components with secure configuration"""
        try:
            # Get secrets securely
            api_key = await self.secret_manager.get_secret('binance_api_key')
            api_secret = await self.secret_manager.get_secret('binance_secret')
            redis_password = await self.secret_manager.get_secret('redis_password')
            
            # Initialize HTTP session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection limit
                limit_per_host=20,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            
            # Headers for API authentication
            headers = {
                'X-MBX-APIKEY': api_key,
                'User-Agent': 'ScalableDataOptimizer/1.0'
            }
            
            self.api_session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Initialize Redis connection
            redis_url = f"redis://:{redis_password}@{self.config['redis_host']}:{self.config['redis_port']}/{self.config['redis_db']}"
            self.redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            
            # Perform security validation
            await self.validate_security_setup()
            
            logger.info(f"Scalable Data Optimizer initialized in {self.environment} mode")
            logger.info(f"Configuration: {self.config}")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def validate_security_setup(self):
        """Validate security configuration and API permissions"""
        try:
            logger.info("🔍 Performing security validation...")
            
            # Run comprehensive security check
            security_report = await self.secret_manager.validate_security_setup(self.api_session)
            
            # Log security status
            logger.info(f"🔒 Security Score: {security_report['security_score']}/100")
            logger.info(f"🔒 Security Status: {security_report['overall_status']}")
            
            # Handle critical security issues
            critical_issues = security_report['validation_results']['api_permissions'].get('critical_issues', [])
            if critical_issues:
                logger.error("🚨 CRITICAL SECURITY ISSUES DETECTED:")
                for issue in critical_issues:
                    logger.error(f"   • {issue['permission']}: {issue['description']}")
                    logger.error(f"     Risk: {issue['risk_level']}, Impact: {issue['financial_impact']}")
                    logger.error(f"     Action: {issue['recommendation']}")
                
                if self.environment == 'production':
                    raise SecurityError("Critical security issues detected in production environment")
            
            # Log warnings
            warnings = security_report['validation_results']['api_permissions'].get('warnings', [])
            if warnings:
                logger.warning("⚠️  Security warnings:")
                for warning in warnings:
                    logger.warning(f"   • {warning['permission']}: {warning['issue']}")
            
            # Log recommendations
            recommendations = security_report['validation_results']['api_permissions'].get('recommendations', [])
            if recommendations:
                logger.info("💡 Security recommendations:")
                for rec in recommendations[:5]:  # Show top 5
                    logger.info(f"   {rec}")
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            if self.environment == 'production':
                raise
    
    def _setup_logger(self) -> logging.Logger:
        """Setup optimized logger"""
        logger = logging.getLogger('ScalableDataOptimizer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start_optimization_system(self):
        """Start the complete optimization system"""
        self.logger.info("🎯 Starting Scalable Data Optimization System")
        
        # Start background tasks
        tasks = [
            self._batch_data_fetcher(),
            self._cache_maintenance(),
            self._performance_monitor(),
            self._websocket_server(),
            self._priority_data_processor()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # ==================== BATCH DATA FETCHING ====================
    
    async def _batch_data_fetcher(self):
        """Optimized batch data fetching for multiple trading pairs"""
        while True:
            try:
                await self._fetch_all_trading_pairs_optimized()
                await asyncio.sleep(5)  # Configurable interval
            except Exception as e:
                self.logger.error(f"Batch fetching error: {e}")
                await asyncio.sleep(10)
    
    async def _fetch_all_trading_pairs_optimized(self):
        """Fetch data for all trading pairs using optimized batching"""
        
        # Get all symbols that need updates
        symbols_to_update = await self._get_symbols_requiring_updates()
        
        if not symbols_to_update:
            return
        
        # Create batches for parallel processing
        batches = [symbols_to_update[i:i + self.config['batch_size']] 
                  for i in range(0, len(symbols_to_update), self.config['batch_size'])]
        
        # Process batches concurrently with limit
        semaphore = asyncio.Semaphore(self.config['max_concurrent_requests'])
        
        async def process_batch(batch):
            async with semaphore:
                return await self._fetch_batch_data(batch)
        
        # Execute batches and collect results
        results = await asyncio.gather(
            *[process_batch(batch) for batch in batches],
            return_exceptions=True
        )
        
        # Process results and update cache
        total_updated = 0
        for result in results:
            if isinstance(result, list):
                total_updated += len(result)
                await self._update_cached_data(result)
        
        self.logger.info(f"📊 Updated {total_updated} trading pairs in {len(batches)} batches")
    
    async def _fetch_batch_data(self, symbols: List[str]) -> List[TradingPairMetrics]:
        """Fetch data for a batch of symbols"""
        
        try:
            # Use Binance 24hr ticker endpoint for batch data
            url = "https://api.binance.com/api/v3/ticker/24hr"
            
            # Check rate limiting
            await self._enforce_rate_limit()
            
            async with self.api_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter for requested symbols
                    symbol_set = set(symbols)
                    filtered_data = [ticker for ticker in data if ticker['symbol'] in symbol_set]
                    
                    # Convert to metrics objects
                    metrics = []
                    for ticker in filtered_data:
                        metric = TradingPairMetrics(
                            symbol=ticker['symbol'],
                            price=float(ticker['lastPrice']),
                            change_24h=float(ticker['priceChangePercent']),
                            volume_24h=float(ticker['volume']),
                            high_24h=float(ticker['highPrice']),
                            low_24h=float(ticker['lowPrice']),
                            timestamp=datetime.now(),
                            priority=self._get_symbol_priority(ticker['symbol'])
                        )
                        metrics.append(metric)
                    
                    return metrics
                else:
                    self.logger.error(f"API error: {response.status}")
                    return []
        
        except Exception as e:
            self.logger.error(f"Error fetching batch data: {e}")
            return []
    
    # ==================== INTELLIGENT CACHING ====================
    
    async def _update_cached_data(self, metrics: List[TradingPairMetrics]):
        """Update multi-level cache with compression"""
        
        for metric in metrics:
            # Update memory cache
            self.data_cache[metric.symbol] = metric
            
            # Update Redis cache with compression
            cache_key = f"trading_pair:{metric.symbol}"
            data = pickle.dumps(metric)
            
            if len(data) > 1024:  # 1KB threshold
                data = gzip.compress(data)
                cache_key += ":compressed"
            
            # Set with expiration
            await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                lambda: self.redis_client.setex(cache_key, self.config['cache_ttl'], data)
            )
            
            # Broadcast to WebSocket clients
            await self._broadcast_update(metric)
    
    async def get_cached_data(self, symbol: str) -> Optional[TradingPairMetrics]:
        """Get data from multi-level cache"""
        
        # Check memory cache first
        if symbol in self.data_cache:
            self.metrics['cache_hits'] += 1
            return self.data_cache[symbol]
        
        # Check Redis cache
        cache_key = f"trading_pair:{symbol}"
        compressed_key = f"{cache_key}:compressed"
        
        try:
            # Try compressed first
            data = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                lambda: self.redis_client.get(compressed_key)
            )
            
            if data:
                data = gzip.decompress(data)
                metric = pickle.loads(data)
                self.data_cache[symbol] = metric  # Update memory cache
                self.metrics['cache_hits'] += 1
                return metric
            
            # Try uncompressed
            data = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                lambda: self.redis_client.get(cache_key)
            )
            
            if data:
                metric = pickle.loads(data)
                self.data_cache[symbol] = metric  # Update memory cache
                self.metrics['cache_hits'] += 1
                return metric
        
        except Exception as e:
            self.logger.error(f"Cache retrieval error for {symbol}: {e}")
        
        self.metrics['cache_misses'] += 1
        return None
    
    async def _cache_maintenance(self):
        """Background cache maintenance and optimization"""
        while True:
            try:
                # Clean expired data from memory cache
                current_time = datetime.now()
                expired_symbols = []
                
                for symbol, metric in self.data_cache.items():
                    if (current_time - metric.timestamp).total_seconds() > self.config['cache_ttl']:  # Cache TTL
                        expired_symbols.append(symbol)
                
                for symbol in expired_symbols:
                    del self.data_cache[symbol]
                
                # Update cache statistics
                self.metrics['cache_size'] = len(self.data_cache)
                
                if self.metrics['cache_hits'] + self.metrics['cache_misses'] > 0:
                    self.metrics['cache_hit_ratio'] = (
                        self.metrics['cache_hits'] / 
                        (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                    )
                
                # Force garbage collection periodically
                if len(self.data_cache) > 1000:
                    gc.collect()
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                self.logger.error(f"Cache maintenance error: {e}")
                await asyncio.sleep(60)
    
    # ==================== WEBSOCKET REAL-TIME STREAMING ====================
    
    async def _websocket_server(self):
        """Start WebSocket server for real-time updates"""
        try:
            self.websocket_server = await serve(
                self._handle_websocket_client,
                "localhost",
                self.config['websocket_port'],
                ping_interval=20,
                ping_timeout=10
            )
            self.logger.info("🔗 WebSocket server started on port 8766")
            await self.websocket_server.wait_closed()
        except Exception as e:
            self.logger.error(f"WebSocket server error: {e}")
    
    async def _handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        client_id = f"client_{int(time.time() * 1000)}"
        self.connected_clients.add(websocket)
        
        try:
            self.logger.info(f"🔗 WebSocket client connected: {client_id}")
            
            # Send initial data
            await self._send_initial_data(websocket)
            
            # Handle client messages
            async for message in websocket:
                await self._handle_client_message(client_id, message, websocket)
                
        except ConnectionClosed:
            self.logger.info(f"🔌 WebSocket client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
    
    async def _broadcast_update(self, metric: TradingPairMetrics):
        """Broadcast updates to WebSocket clients"""
        if not self.connected_clients:
            return
        
        message = {
            'type': 'price_update',
            'data': metric.to_dict()
        }
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"Broadcast error: {e}")
                disconnected_clients.add(client)
        
        # Clean up disconnected clients
        self.connected_clients -= disconnected_clients
    
    # ==================== PRIORITY-BASED DATA PROCESSING ====================
    
    def _get_symbol_priority(self, symbol: str) -> int:
        """Determine symbol priority based on volume and popularity"""
        
        # High priority symbols (most liquid/popular)
        high_priority = {
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
        }
        
        # Medium priority symbols
        medium_priority = {
            'UNIUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT', 'FILUSDT',
            'TRXUSDT', 'ETCUSDT', 'XLMUSDT', 'EOSUSDT', 'XMRUSDT'
        }
        
        if symbol in high_priority:
            return 1
        elif symbol in medium_priority:
            return 2
        else:
            return 3
    
    async def _priority_data_processor(self):
        """Process data updates based on priority"""
        while True:
            try:
                # Process high priority first
                for priority in [1, 2, 3]:
                    queue = self.priority_queues[priority]
                    
                    # Process up to 50 items per priority level
                    for _ in range(min(50, len(queue))):
                        if queue:
                            symbol = queue.popleft()
                            await self._process_priority_update(symbol, priority)
                
                await asyncio.sleep(0.1)  # High frequency processing
                
            except Exception as e:
                self.logger.error(f"Priority processor error: {e}")
                await asyncio.sleep(1)
    
    async def _process_priority_update(self, symbol: str, priority: int):
        """Process individual priority update"""
        try:
            # Fetch latest data for this symbol
            metric = await self.get_cached_data(symbol)
            if metric and (datetime.now() - metric.timestamp).total_seconds() > (priority * 2):
                # Data is stale, fetch new data
                new_data = await self._fetch_single_symbol(symbol)
                if new_data:
                    await self._update_cached_data([new_data])
        except Exception as e:
            self.logger.error(f"Priority update error for {symbol}: {e}")
    
    # ==================== PERFORMANCE OPTIMIZATION ====================
    
    async def _get_symbols_requiring_updates(self) -> List[str]:
        """Get symbols that need data updates based on staleness and priority"""
        
        current_time = datetime.now()
        symbols_to_update = []
        
        # Get all subscribed symbols
        all_symbols = set()
        for subscription in self.subscriptions.values():
            all_symbols.update(subscription.symbols)
        
        for symbol in all_symbols:
            metric = self.data_cache.get(symbol)
            
            if not metric:
                # No data exists, needs update
                symbols_to_update.append(symbol)
                continue
            
            # Check if data is stale based on priority
            priority = self._get_symbol_priority(symbol)
            staleness_threshold = priority * 5  # 5s for high, 10s for medium, 15s for low
            
            if (current_time - metric.timestamp).total_seconds() > staleness_threshold:
                symbols_to_update.append(symbol)
        
        return symbols_to_update
    
    async def _enforce_rate_limit(self):
        """Enforce API rate limiting"""
        current_time = time.time()
        self.last_api_call.append(current_time)
        
        # Check if we're exceeding rate limit
        recent_calls = [t for t in self.last_api_call if current_time - t < 1.0]
        
        if len(recent_calls) >= self.config['rate_limit_per_second']:
            wait_time = 1.0 - (current_time - recent_calls[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
    
    async def _performance_monitor(self):
        """Monitor and log performance metrics"""
        while True:
            try:
                # Calculate performance metrics
                current_time = time.time()
                recent_calls = [t for t in self.last_api_call if current_time - t < 60]
                
                self.metrics.update({
                    'total_api_calls': len([t for t in recent_calls if current_time - t < 1]),
                    'cache_hit_ratio': self.metrics.get('cache_hit_ratio', 0),
                    'active_connections': len(self.connected_clients),
                    'memory_usage_mb': len(self.data_cache) * 0.001,  # Rough estimate
                    'active_websocket_clients': len(self.connected_clients)
                })
                
                # Log metrics every 30 seconds
                self.logger.info(
                    f"📊 Performance: "
                    f"API calls/s: {self.metrics['total_api_calls']}, "
                    f"Cache hit ratio: {self.metrics['cache_hit_ratio']:.2f}, "
                    f"Active subs: {self.metrics['active_connections']}, "
                    f"Memory: {self.metrics['memory_usage_mb']:.1f}MB, "
                    f"WS clients: {self.metrics['active_websocket_clients']}"
                )
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    # ==================== CLIENT SUBSCRIPTION MANAGEMENT ====================
    
    async def subscribe_client(self, client_id: str, symbols: List[str], 
                             update_frequency: float = 1.0, 
                             data_types: List[str] = None) -> bool:
        """Subscribe client to specific symbols with frequency control"""
        
        try:
            if data_types is None:
                data_types = ['price']
            
            subscription = DataSubscription(
                client_id=client_id,
                symbols=set(symbols),
                update_frequency=update_frequency,
                priority_filter={1, 2, 3},  # All priorities by default
                last_update=datetime.now(),
                data_types=set(data_types),
                compression_enabled=True
            )
            
            self.subscriptions[client_id] = subscription
            
            # Queue symbols for priority updates
            for symbol in symbols:
                priority = self._get_symbol_priority(symbol)
                self.priority_queues[priority].append(symbol)
            
            self.logger.info(f"✅ Client {client_id} subscribed to {len(symbols)} symbols")
            return True
            
        except Exception as e:
            self.logger.error(f"Subscription error for {client_id}: {e}")
            return False
    
    async def unsubscribe_client(self, client_id: str) -> bool:
        """Unsubscribe client from all data"""
        try:
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
                self.logger.info(f"✅ Client {client_id} unsubscribed")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Unsubscription error for {client_id}: {e}")
            return False
    
    # ==================== HELPER METHODS ====================
    
    async def _send_initial_data(self, websocket):
        """Send initial data to new WebSocket client"""
        try:
            # Send top 20 most popular pairs
            popular_symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
                'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT',
                'UNIUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT', 'FILUSDT',
                'TRXUSDT', 'ETCUSDT', 'XLMUSDT', 'EOSUSDT', 'XMRUSDT'
            ]
            
            initial_data = []
            for symbol in popular_symbols:
                metric = await self.get_cached_data(symbol)
                if metric:
                    initial_data.append(metric.to_dict())
            
            message = {
                'type': 'initial_data',
                'data': initial_data
            }
            
            await websocket.send(json.dumps(message))
            
        except Exception as e:
            self.logger.error(f"Error sending initial data: {e}")
    
    async def _handle_client_message(self, client_id: str, message: str, websocket):
        """Handle messages from WebSocket clients"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                symbols = data.get('symbols', [])
                frequency = data.get('frequency', 1.0)
                await self.subscribe_client(client_id, symbols, frequency)
                
                # Send confirmation
                await websocket.send(json.dumps({
                    'type': 'subscription_confirmed',
                    'symbols': symbols
                }))
                
            elif message_type == 'unsubscribe':
                await self.unsubscribe_client(client_id)
                
        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")
    
    async def _fetch_single_symbol(self, symbol: str) -> Optional[TradingPairMetrics]:
        """Fetch data for a single symbol"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            
            await self._enforce_rate_limit()
            
            async with self.api_session.get(url) as response:
                if response.status == 200:
                    ticker = await response.json()
                    
                    return TradingPairMetrics(
                        symbol=ticker['symbol'],
                        price=float(ticker['lastPrice']),
                        change_24h=float(ticker['priceChangePercent']),
                        volume_24h=float(ticker['volume']),
                        high_24h=float(ticker['highPrice']),
                        low_24h=float(ticker['lowPrice']),
                        timestamp=datetime.now(),
                        priority=self._get_symbol_priority(ticker['symbol'])
                    )
        except Exception as e:
            self.logger.error(f"Error fetching {symbol}: {e}")
            return None
    
    async def get_performance_stats(self) -> Dict:
        """Get current performance statistics"""
        return self.metrics.copy()
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.api_session.close()
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            self.logger.info("🧹 Cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

# ==================== DASH INTEGRATION ====================

class ScalableDashboardIntegration:
    """Integration with Dash for scalable dashboard updates"""
    
    def __init__(self, optimizer: ScalableDataOptimizer, app: dash.Dash):
        self.optimizer = optimizer
        self.app = app
        self.websocket_client = None
        self.latest_data = {}
        
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup optimized Dash callbacks"""
        
        # Replace interval-based updates with WebSocket store updates
        @self.app.callback(
            Output('trading-data-store', 'data'),
            [Input('websocket-trigger', 'data')]
        )
        def update_trading_data(websocket_data):
            """Update trading data from WebSocket"""
            if websocket_data:
                return websocket_data
            return self.latest_data
        
        # Optimized market overview with data virtualization
        @self.app.callback(
            Output('market-overview-table', 'data'),
            [Input('trading-data-store', 'data'),
             Input('table-pagination', 'active_page'),
             Input('symbol-filter', 'value')]
        )
        def update_market_table(trading_data, page, symbol_filter):
            """Update market table with pagination and filtering"""
            
            if not trading_data:
                return []
            
            # Filter data
            filtered_data = trading_data
            if symbol_filter:
                filtered_data = [d for d in trading_data if symbol_filter.upper() in d['symbol']]
            
            # Implement pagination (show 50 items per page)
            page_size = 50
            start_idx = (page - 1) * page_size if page else 0
            end_idx = start_idx + page_size
            
            return filtered_data[start_idx:end_idx]
        
        # Optimized chart updates with data decimation
        @self.app.callback(
            Output('price-chart', 'figure'),
            [Input('trading-data-store', 'data'),
             Input('selected-symbol', 'value')]
        )
        def update_price_chart(trading_data, selected_symbol):
            """Update price chart with optimized rendering"""
            
            if not trading_data or not selected_symbol:
                return go.Figure()
            
            # Find data for selected symbol
            symbol_data = next((d for d in trading_data if d['symbol'] == selected_symbol), None)
            
            if not symbol_data:
                return go.Figure()
            
            # Create optimized chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=[datetime.now()],
                y=[symbol_data['price']],
                mode='lines+markers',
                name=selected_symbol,
                line=dict(width=2)
            ))
            
            fig.update_layout(
                title=f"{selected_symbol} Price",
                xaxis_title="Time",
                yaxis_title="Price (USDT)",
                height=400,
                showlegend=False
            )
            
            return fig

# ==================== DEMO AND TESTING ====================

async def demo_scalable_optimization():
    """Demonstration of the scalable optimization system"""
    
    print("🚀 SCALABLE TRADING DATA OPTIMIZATION SYSTEM")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = ScalableDataOptimizer()
    
    print("📊 System Configuration:")
    print(f"   • Batch Size: {optimizer.config['batch_size']} symbols")
    print(f"   • Max Concurrent Batches: {optimizer.config['max_concurrent_requests']}")
    print(f"   • Rate Limit: {optimizer.config['rate_limit_per_second']} requests/second")
    print(f"   • Connection Pool Size: 100 connections")
    print(f"   • Thread Pool Workers: 10")
    
    # Simulate subscribing to many trading pairs
    test_symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
        'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT',
        'UNIUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT', 'FILUSDT'
    ] * 10  # 150 symbols total
    
    print(f"\n🎯 Testing with {len(test_symbols)} trading pairs")
    
    # Subscribe test client
    await optimizer.subscribe_client("test_client", test_symbols, update_frequency=0.5)
    
    print("⏰ Running optimization system for 30 seconds...")
    
    # Start the system
    optimization_task = asyncio.create_task(optimizer.start_optimization_system())
    
    # Let it run for 30 seconds
    await asyncio.sleep(30)
    
    # Get performance stats
    stats = await optimizer.get_performance_stats()
    
    print("\n📊 Performance Results:")
    print(f"   • API Calls/Second: {stats['total_api_calls']}")
    print(f"   • Cache Hit Ratio: {stats['cache_hit_ratio']:.2%}")
    print(f"   • Active Subscriptions: {stats['active_connections']}")
    print(f"   • Memory Usage: {stats['memory_usage_mb']:.1f} MB")
    print(f"   • WebSocket Clients: {stats['active_websocket_clients']}")
    
    # Cleanup
    optimization_task.cancel()
    await optimizer.cleanup()
    
    print("\n✅ Scalable optimization demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_scalable_optimization()) 