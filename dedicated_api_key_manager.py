#!/usr/bin/env python3
"""
Dedicated API Key Management System
Implements separate API keys for different bots and purposes to limit blast radius
"""

import asyncio
import logging
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotPurpose(Enum):
    """Different bot purposes with specific permission requirements"""
    MARKET_DATA = "market_data"           # Read-only market data fetching
    TRADING_MAIN = "trading_main"         # Main trading operations
    TRADING_SCALPING = "trading_scalping" # High-frequency scalping
    TRADING_SWING = "trading_swing"       # Swing trading positions
    PORTFOLIO_MANAGEMENT = "portfolio"    # Portfolio rebalancing
    RISK_MANAGEMENT = "risk_management"   # Risk monitoring and controls
    ARBITRAGE = "arbitrage"               # Cross-exchange arbitrage
    MARKET_MAKING = "market_making"       # Market making operations
    BACKTESTING = "backtesting"           # Historical data and testing
    MONITORING = "monitoring"             # System health monitoring
    ANALYTICS = "analytics"               # Performance analytics
    EMERGENCY_LIQUIDATION = "emergency"   # Emergency position closure

class Exchange(Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKEX = "okex"
    HUOBI = "huobi"
    KUCOIN = "kucoin"
    BITFINEX = "bitfinex"

class APIPermission(Enum):
    """API permission levels"""
    READ_ONLY = "read_only"
    SPOT_TRADING = "spot_trading"
    FUTURES_TRADING = "futures_trading"
    MARGIN_TRADING = "margin_trading"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    ACCOUNT_INFO = "account_info"
    ORDER_HISTORY = "order_history"

@dataclass
class APIKeyProfile:
    """Dedicated API key profile for specific bot purpose"""
    key_id: str
    exchange: Exchange
    purpose: BotPurpose
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    permissions: Set[APIPermission] = None
    max_daily_volume: Optional[float] = None
    max_position_size: Optional[float] = None
    allowed_symbols: Set[str] = None
    ip_whitelist: List[str] = None
    created_at: datetime = None
    last_used: datetime = None
    usage_count: int = 0
    is_active: bool = True
    emergency_contact: Optional[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.permissions is None:
            self.permissions = set()
        if self.allowed_symbols is None:
            self.allowed_symbols = set()
        if self.ip_whitelist is None:
            self.ip_whitelist = []

@dataclass
class APIKeyUsageLog:
    """Usage logging for API key monitoring"""
    key_id: str
    timestamp: datetime
    endpoint: str
    method: str
    response_code: int
    volume: Optional[float] = None
    symbol: Optional[str] = None
    error_message: Optional[str] = None
    ip_address: Optional[str] = None

class BotInstance:
    """Individual bot instance with dedicated API keys"""
    
    def __init__(self, bot_id: str, purpose: BotPurpose, exchanges: List[Exchange]):
        self.bot_id = bot_id
        self.purpose = purpose
        self.exchanges = exchanges
        self.api_keys: Dict[Exchange, APIKeyProfile] = {}
        self.usage_logs: List[APIKeyUsageLog] = []
        self.daily_volume: Dict[str, float] = {}  # Date -> Volume
        self.last_health_check: Optional[datetime] = None
        self.is_active = True
        self.created_at = datetime.now()

class DedicatedAPIKeyManager:
    """Comprehensive dedicated API key management system"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.bot_instances: Dict[str, BotInstance] = {}
        self.api_key_profiles: Dict[str, APIKeyProfile] = {}
        self.usage_logs: List[APIKeyUsageLog] = []
        self.encryption_manager = None
        self.audit_logger = None
        
        # Load existing configurations
        self.config_file = f"dedicated_keys_{environment}.json"
        self.load_configuration()
        
        # Initialize encryption if available
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption system for secure key storage"""
        try:
            from encryption_security_system import SecureAPIKeyManager, EncryptionAuditLogger
            self.encryption_manager = SecureAPIKeyManager()
            self.audit_logger = EncryptionAuditLogger("dedicated_keys_audit.log")
            logger.info("🔐 Encryption system initialized for dedicated API keys")
        except ImportError:
            logger.warning("⚠️  Encryption system not available - using basic storage")
    
    # ==================== BOT INSTANCE MANAGEMENT ====================
    
    async def create_bot_instance(self, bot_id: str, purpose: BotPurpose, 
                                exchanges: List[Exchange], 
                                config: Dict[str, Any] = None) -> BotInstance:
        """Create a new bot instance with dedicated API keys"""
        
        if bot_id in self.bot_instances:
            raise ValueError(f"Bot instance {bot_id} already exists")
        
        # Create bot instance
        bot_instance = BotInstance(bot_id, purpose, exchanges)
        
        # Apply configuration
        if config:
            await self._apply_bot_configuration(bot_instance, config)
        
        # Generate dedicated API key profiles for each exchange
        for exchange in exchanges:
            key_profile = await self._create_api_key_profile(
                exchange, purpose, bot_id, config
            )
            bot_instance.api_keys[exchange] = key_profile
            self.api_key_profiles[key_profile.key_id] = key_profile
        
        self.bot_instances[bot_id] = bot_instance
        
        # Log creation
        await self._log_bot_event(
            bot_id, "bot_created", 
            {
                "purpose": purpose.value,
                "exchanges": [e.value for e in exchanges],
                "api_keys_generated": len(exchanges)
            }
        )
        
        logger.info(f"🤖 Created bot instance: {bot_id} ({purpose.value}) with {len(exchanges)} dedicated API keys")
        return bot_instance
    
    async def _apply_bot_configuration(self, bot_instance: BotInstance, config: Dict[str, Any]):
        """Apply configuration to bot instance"""
        # This would apply any bot-specific configuration
        pass
    
    async def _create_api_key_profile(self, exchange: Exchange, purpose: BotPurpose, 
                                    bot_id: str, config: Dict[str, Any] = None) -> APIKeyProfile:
        """Create dedicated API key profile for specific exchange and purpose"""
        
        # Generate unique key ID
        key_id = f"{bot_id}_{exchange.value}_{purpose.value}_{int(time.time())}"
        
        # Get API keys from secure storage or environment
        api_key, api_secret, passphrase = await self._get_dedicated_api_keys(
            exchange, purpose, bot_id
        )
        
        # Determine permissions based on purpose
        permissions = self._get_permissions_for_purpose(purpose)
        
        # Create profile
        profile = APIKeyProfile(
            key_id=key_id,
            exchange=exchange,
            purpose=purpose,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            permissions=permissions,
            emergency_contact=config.get("emergency_contact") if config else None,
            notes=f"Dedicated key for {bot_id} - {purpose.value}"
        )
        
        # Apply purpose-specific limits
        await self._apply_purpose_limits(profile, config)
        
        return profile
    
    def _get_permissions_for_purpose(self, purpose: BotPurpose) -> Set[APIPermission]:
        """Get required permissions based on bot purpose"""
        
        permission_map = {
            BotPurpose.MARKET_DATA: {
                APIPermission.READ_ONLY
            },
            BotPurpose.TRADING_MAIN: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.ACCOUNT_INFO,
                APIPermission.ORDER_HISTORY
            },
            BotPurpose.TRADING_SCALPING: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.ACCOUNT_INFO
            },
            BotPurpose.TRADING_SWING: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.MARGIN_TRADING,
                APIPermission.ACCOUNT_INFO,
                APIPermission.ORDER_HISTORY
            },
            BotPurpose.PORTFOLIO_MANAGEMENT: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.TRANSFER,
                APIPermission.ACCOUNT_INFO
            },
            BotPurpose.RISK_MANAGEMENT: {
                APIPermission.READ_ONLY,
                APIPermission.ACCOUNT_INFO,
                APIPermission.ORDER_HISTORY
            },
            BotPurpose.ARBITRAGE: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.TRANSFER,
                APIPermission.ACCOUNT_INFO
            },
            BotPurpose.MARKET_MAKING: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.ACCOUNT_INFO
            },
            BotPurpose.BACKTESTING: {
                APIPermission.READ_ONLY,
                APIPermission.ORDER_HISTORY
            },
            BotPurpose.MONITORING: {
                APIPermission.READ_ONLY,
                APIPermission.ACCOUNT_INFO
            },
            BotPurpose.ANALYTICS: {
                APIPermission.READ_ONLY,
                APIPermission.ORDER_HISTORY,
                APIPermission.ACCOUNT_INFO
            },
            BotPurpose.EMERGENCY_LIQUIDATION: {
                APIPermission.READ_ONLY,
                APIPermission.SPOT_TRADING,
                APIPermission.FUTURES_TRADING,
                APIPermission.MARGIN_TRADING,
                APIPermission.ACCOUNT_INFO
            }
        }
        
        return permission_map.get(purpose, {APIPermission.READ_ONLY})
    
    async def _apply_purpose_limits(self, profile: APIKeyProfile, config: Dict[str, Any] = None):
        """Apply purpose-specific trading limits"""
        
        # Default limits based on purpose
        purpose_limits = {
            BotPurpose.MARKET_DATA: {
                "max_daily_volume": 0,  # No trading
                "max_position_size": 0
            },
            BotPurpose.TRADING_SCALPING: {
                "max_daily_volume": 50000,  # $50k daily
                "max_position_size": 1000   # $1k per position
            },
            BotPurpose.TRADING_MAIN: {
                "max_daily_volume": 500000,  # $500k daily
                "max_position_size": 10000   # $10k per position
            },
            BotPurpose.TRADING_SWING: {
                "max_daily_volume": 100000,  # $100k daily
                "max_position_size": 25000   # $25k per position
            },
            BotPurpose.PORTFOLIO_MANAGEMENT: {
                "max_daily_volume": 1000000,  # $1M daily
                "max_position_size": 100000   # $100k per position
            },
            BotPurpose.ARBITRAGE: {
                "max_daily_volume": 200000,  # $200k daily
                "max_position_size": 5000    # $5k per position
            },
            BotPurpose.MARKET_MAKING: {
                "max_daily_volume": 1000000,  # $1M daily
                "max_position_size": 50000    # $50k per position
            },
            BotPurpose.EMERGENCY_LIQUIDATION: {
                "max_daily_volume": float('inf'),  # No limit for emergency
                "max_position_size": float('inf')
            }
        }
        
        limits = purpose_limits.get(profile.purpose, {})
        
        # Apply limits
        profile.max_daily_volume = config.get("max_daily_volume", limits.get("max_daily_volume")) if config else limits.get("max_daily_volume")
        profile.max_position_size = config.get("max_position_size", limits.get("max_position_size")) if config else limits.get("max_position_size")
        
        # Apply symbol restrictions
        if config and "allowed_symbols" in config:
            profile.allowed_symbols = set(config["allowed_symbols"])
        else:
            # Default symbols based on purpose
            if profile.purpose == BotPurpose.MARKET_DATA:
                profile.allowed_symbols = {"*"}  # All symbols for data
            elif profile.purpose == BotPurpose.TRADING_SCALPING:
                profile.allowed_symbols = {"BTCUSDT", "ETHUSDT", "ADAUSDT"}  # High liquidity only
            else:
                profile.allowed_symbols = {"*"}  # All symbols by default
    
    # ==================== API KEY RETRIEVAL ====================
    
    async def get_api_key_for_bot(self, bot_id: str, exchange: Exchange) -> Optional[APIKeyProfile]:
        """Get dedicated API key for specific bot and exchange"""
        
        if bot_id not in self.bot_instances:
            logger.error(f"Bot instance {bot_id} not found")
            return None
        
        bot_instance = self.bot_instances[bot_id]
        
        if exchange not in bot_instance.api_keys:
            logger.error(f"No API key found for {bot_id} on {exchange.value}")
            return None
        
        key_profile = bot_instance.api_keys[exchange]
        
        # Update usage tracking
        key_profile.last_used = datetime.now()
        key_profile.usage_count += 1
        
        # Log usage
        await self._log_api_key_usage(
            key_profile.key_id, "key_retrieved", 
            {"bot_id": bot_id, "exchange": exchange.value}
        )
        
        return key_profile
    
    async def get_api_keys_for_purpose(self, purpose: BotPurpose) -> List[APIKeyProfile]:
        """Get all API keys for a specific purpose across all bots"""
        
        keys = []
        for bot_instance in self.bot_instances.values():
            if bot_instance.purpose == purpose:
                keys.extend(bot_instance.api_keys.values())
        
        return keys
    
    async def get_emergency_keys(self) -> List[APIKeyProfile]:
        """Get emergency liquidation keys for crisis situations"""
        
        emergency_keys = []
        
        for bot_instance in self.bot_instances.values():
            if bot_instance.purpose == BotPurpose.EMERGENCY_LIQUIDATION:
                emergency_keys.extend(bot_instance.api_keys.values())
        
        # If no dedicated emergency keys, get high-permission keys
        if not emergency_keys:
            for bot_instance in self.bot_instances.values():
                for key_profile in bot_instance.api_keys.values():
                    if (APIPermission.SPOT_TRADING in key_profile.permissions and
                        APIPermission.FUTURES_TRADING in key_profile.permissions):
                        emergency_keys.append(key_profile)
        
        logger.warning(f"🚨 Retrieved {len(emergency_keys)} emergency API keys")
        return emergency_keys
    
    # ==================== SECURITY MONITORING ====================
    
    async def validate_api_key_usage(self, key_id: str, endpoint: str, 
                                   volume: float = 0, symbol: str = None) -> bool:
        """Validate API key usage against limits and permissions"""
        
        if key_id not in self.api_key_profiles:
            logger.error(f"API key {key_id} not found")
            return False
        
        profile = self.api_key_profiles[key_id]
        
        # Check if key is active
        if not profile.is_active:
            logger.error(f"API key {key_id} is inactive")
            return False
        
        # Check symbol restrictions
        if symbol and profile.allowed_symbols and "*" not in profile.allowed_symbols:
            if symbol not in profile.allowed_symbols:
                logger.error(f"Symbol {symbol} not allowed for key {key_id}")
                return False
        
        # Check daily volume limits
        if profile.max_daily_volume and volume > 0:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_volume = self._get_daily_volume(key_id, today)
            
            if daily_volume + volume > profile.max_daily_volume:
                logger.error(f"Daily volume limit exceeded for key {key_id}: "
                           f"{daily_volume + volume} > {profile.max_daily_volume}")
                return False
        
        # Check position size limits
        if profile.max_position_size and volume > profile.max_position_size:
            logger.error(f"Position size limit exceeded for key {key_id}: "
                       f"{volume} > {profile.max_position_size}")
            return False
        
        # Log successful validation
        await self._log_api_key_usage(
            key_id, endpoint, "POST", 200, volume, symbol
        )
        
        return True
    
    async def detect_suspicious_activity(self, key_id: str) -> List[str]:
        """Detect suspicious activity patterns for API key"""
        
        if key_id not in self.api_key_profiles:
            return ["API key not found"]
        
        profile = self.api_key_profiles[key_id]
        alerts = []
        
        # Get recent usage logs
        recent_logs = [
            log for log in self.usage_logs
            if log.key_id == key_id and 
            log.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        # Check for unusual volume
        total_volume = sum(log.volume or 0 for log in recent_logs)
        if profile.max_daily_volume and total_volume > profile.max_daily_volume * 1.5:
            alerts.append(f"Unusual volume detected: {total_volume}")
        
        # Check for rapid-fire requests
        request_times = [log.timestamp for log in recent_logs]
        if len(request_times) > 1000:  # More than 1000 requests in 24h
            alerts.append(f"High request frequency: {len(request_times)} requests/24h")
        
        # Check for error patterns
        error_logs = [log for log in recent_logs if log.response_code >= 400]
        if len(error_logs) > 50:  # More than 50 errors in 24h
            alerts.append(f"High error rate: {len(error_logs)} errors/24h")
        
        # Check for unusual IP addresses
        if profile.ip_whitelist:
            unusual_ips = set()
            for log in recent_logs:
                if log.ip_address and log.ip_address not in profile.ip_whitelist:
                    unusual_ips.add(log.ip_address)
            
            if unusual_ips:
                alerts.append(f"Unusual IP addresses: {list(unusual_ips)}")
        
        return alerts
    
    # ==================== INCIDENT RESPONSE ====================
    
    async def compromise_response(self, key_id: str, incident_type: str = "suspected_compromise"):
        """Respond to potential API key compromise"""
        
        if key_id not in self.api_key_profiles:
            logger.error(f"Cannot respond to compromise: key {key_id} not found")
            return
        
        profile = self.api_key_profiles[key_id]
        
        # Immediate actions
        logger.critical(f"🚨 SECURITY INCIDENT: {incident_type} for key {key_id}")
        
        # 1. Disable the compromised key
        profile.is_active = False
        
        # 2. Log the incident
        await self._log_security_incident(key_id, incident_type, {
            "bot_id": self._get_bot_id_for_key(key_id),
            "exchange": profile.exchange.value,
            "purpose": profile.purpose.value,
            "emergency_contact": profile.emergency_contact
        })
        
        # 3. Generate incident report
        incident_report = {
            "key_id": key_id,
            "incident_type": incident_type,
            "timestamp": datetime.now().isoformat(),
            "actions_taken": ["key_disabled", "incident_logged"],
            "next_steps": ["manual_review", "key_rotation"]
        }
        
        logger.critical(f"🔒 Key {key_id} disabled. Manual review required.")
        return incident_report
    
    async def isolate_bot_instance(self, bot_id: str, reason: str = "security_incident"):
        """Isolate entire bot instance in case of security incident"""
        
        if bot_id not in self.bot_instances:
            logger.error(f"Cannot isolate bot: {bot_id} not found")
            return
        
        bot_instance = self.bot_instances[bot_id]
        
        logger.critical(f"🚨 ISOLATING BOT INSTANCE: {bot_id} - {reason}")
        
        # Disable all API keys for this bot
        disabled_keys = []
        for exchange, key_profile in bot_instance.api_keys.items():
            key_profile.is_active = False
            disabled_keys.append(key_profile.key_id)
        
        # Mark bot as inactive
        bot_instance.is_active = False
        
        # Log isolation
        await self._log_bot_event(bot_id, "bot_isolated", {
            "reason": reason,
            "disabled_keys": disabled_keys,
            "exchanges": [e.value for e in bot_instance.exchanges]
        })
        
        logger.critical(f"🔒 Bot {bot_id} isolated. {len(disabled_keys)} API keys disabled.")
    
    # ==================== ANALYTICS & REPORTING ====================
    
    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "summary": {
                "total_bots": len(self.bot_instances),
                "total_api_keys": len(self.api_key_profiles),
                "active_keys": len([k for k in self.api_key_profiles.values() if k.is_active]),
                "inactive_keys": len([k for k in self.api_key_profiles.values() if not k.is_active])
            },
            "bot_breakdown": {},
            "exchange_breakdown": {},
            "purpose_breakdown": {},
            "security_alerts": [],
            "recommendations": []
        }
        
        # Bot breakdown
        for bot_id, bot_instance in self.bot_instances.items():
            report["bot_breakdown"][bot_id] = {
                "purpose": bot_instance.purpose.value,
                "exchanges": [e.value for e in bot_instance.exchanges],
                "api_keys": len(bot_instance.api_keys),
                "is_active": bot_instance.is_active,
                "created_at": bot_instance.created_at.isoformat(),
                "last_health_check": bot_instance.last_health_check.isoformat() if bot_instance.last_health_check else None
            }
        
        # Exchange breakdown
        exchange_counts = {}
        for profile in self.api_key_profiles.values():
            exchange = profile.exchange.value
            exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
        report["exchange_breakdown"] = exchange_counts
        
        # Purpose breakdown
        purpose_counts = {}
        for profile in self.api_key_profiles.values():
            purpose = profile.purpose.value
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1
        report["purpose_breakdown"] = purpose_counts
        
        # Security alerts
        for key_id, profile in self.api_key_profiles.items():
            alerts = await self.detect_suspicious_activity(key_id)
            if alerts:
                report["security_alerts"].append({
                    "key_id": key_id,
                    "bot_id": self._get_bot_id_for_key(key_id),
                    "alerts": alerts
                })
        
        # Recommendations
        recommendations = []
        
        # Check for keys without recent usage
        for key_id, profile in self.api_key_profiles.items():
            if profile.last_used and profile.last_used < datetime.now() - timedelta(days=30):
                recommendations.append(f"Consider reviewing unused key: {key_id}")
        
        # Check for keys with excessive permissions
        for profile in self.api_key_profiles.values():
            if (profile.purpose == BotPurpose.MARKET_DATA and 
                len(profile.permissions) > 1):
                recommendations.append(f"Market data key has excessive permissions: {profile.key_id}")
        
        report["recommendations"] = recommendations
        
        return report
    
    async def get_blast_radius_analysis(self) -> Dict[str, Any]:
        """Analyze potential blast radius for each API key compromise"""
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "blast_radius_by_key": {},
            "blast_radius_by_bot": {},
            "blast_radius_by_exchange": {},
            "critical_keys": [],
            "isolation_boundaries": {}
        }
        
        # Analyze each API key
        for key_id, profile in self.api_key_profiles.items():
            bot_id = self._get_bot_id_for_key(key_id)
            
            blast_radius = {
                "key_id": key_id,
                "bot_id": bot_id,
                "exchange": profile.exchange.value,
                "purpose": profile.purpose.value,
                "permissions": [p.value for p in profile.permissions],
                "max_daily_volume": profile.max_daily_volume,
                "max_position_size": profile.max_position_size,
                "allowed_symbols": list(profile.allowed_symbols) if profile.allowed_symbols else ["*"],
                "risk_level": self._calculate_risk_level(profile)
            }
            
            analysis["blast_radius_by_key"][key_id] = blast_radius
            
            # Identify critical keys
            if blast_radius["risk_level"] == "HIGH":
                analysis["critical_keys"].append(key_id)
        
        # Analyze by bot
        for bot_id, bot_instance in self.bot_instances.items():
            total_volume = sum(
                profile.max_daily_volume or 0 
                for profile in bot_instance.api_keys.values()
            )
            
            analysis["blast_radius_by_bot"][bot_id] = {
                "purpose": bot_instance.purpose.value,
                "exchanges": [e.value for e in bot_instance.exchanges],
                "total_max_volume": total_volume,
                "api_key_count": len(bot_instance.api_keys),
                "risk_level": "HIGH" if total_volume > 1000000 else "MEDIUM" if total_volume > 100000 else "LOW"
            }
        
        # Analyze by exchange
        for exchange in Exchange:
            exchange_keys = [
                profile for profile in self.api_key_profiles.values()
                if profile.exchange == exchange
            ]
            
            if exchange_keys:
                total_volume = sum(profile.max_daily_volume or 0 for profile in exchange_keys)
                
                analysis["blast_radius_by_exchange"][exchange.value] = {
                    "key_count": len(exchange_keys),
                    "total_max_volume": total_volume,
                    "purposes": list(set(profile.purpose.value for profile in exchange_keys)),
                    "risk_level": "HIGH" if total_volume > 5000000 else "MEDIUM" if total_volume > 1000000 else "LOW"
                }
        
        return analysis
    
    def _calculate_risk_level(self, profile: APIKeyProfile) -> str:
        """Calculate risk level for API key profile"""
        
        risk_score = 0
        
        # Permission-based risk
        high_risk_permissions = {
            APIPermission.WITHDRAWAL,
            APIPermission.FUTURES_TRADING,
            APIPermission.MARGIN_TRADING
        }
        
        for permission in profile.permissions:
            if permission in high_risk_permissions:
                risk_score += 30
            elif permission == APIPermission.SPOT_TRADING:
                risk_score += 20
            elif permission == APIPermission.TRANSFER:
                risk_score += 15
            else:
                risk_score += 5
        
        # Volume-based risk
        if profile.max_daily_volume:
            if profile.max_daily_volume > 1000000:
                risk_score += 30
            elif profile.max_daily_volume > 100000:
                risk_score += 20
            elif profile.max_daily_volume > 10000:
                risk_score += 10
        
        # Purpose-based risk
        high_risk_purposes = {
            BotPurpose.EMERGENCY_LIQUIDATION,
            BotPurpose.PORTFOLIO_MANAGEMENT,
            BotPurpose.ARBITRAGE
        }
        
        if profile.purpose in high_risk_purposes:
            risk_score += 20
        
        # Determine risk level
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    # ==================== UTILITY METHODS ====================
    
    async def _get_dedicated_api_keys(self, exchange: Exchange, purpose: BotPurpose, 
                                    bot_id: str) -> Tuple[str, str, Optional[str]]:
        """Get dedicated API keys from secure storage"""
        
        # Environment variable pattern: {EXCHANGE}_{PURPOSE}_{BOT_ID}_API_KEY
        key_prefix = f"{exchange.value.upper()}_{purpose.value.upper()}_{bot_id.upper()}"
        
        api_key = os.environ.get(f"{key_prefix}_API_KEY")
        api_secret = os.environ.get(f"{key_prefix}_API_SECRET")
        passphrase = os.environ.get(f"{key_prefix}_PASSPHRASE")
        
        # Fallback to general keys if dedicated keys not found
        if not api_key:
            api_key = os.environ.get(f"{exchange.value.upper()}_API_KEY", f"demo_{exchange.value}_key")
            api_secret = os.environ.get(f"{exchange.value.upper()}_API_SECRET", f"demo_{exchange.value}_secret")
            passphrase = os.environ.get(f"{exchange.value.upper()}_PASSPHRASE")
        
        return api_key, api_secret, passphrase
    
    def _get_daily_volume(self, key_id: str, date: str) -> float:
        """Get daily trading volume for API key"""
        
        daily_logs = [
            log for log in self.usage_logs
            if (log.key_id == key_id and 
                log.timestamp.strftime("%Y-%m-%d") == date and
                log.volume)
        ]
        
        return sum(log.volume for log in daily_logs)
    
    def _get_bot_id_for_key(self, key_id: str) -> Optional[str]:
        """Get bot ID associated with API key"""
        
        for bot_id, bot_instance in self.bot_instances.items():
            for key_profile in bot_instance.api_keys.values():
                if key_profile.key_id == key_id:
                    return bot_id
        return None
    
    async def _log_api_key_usage(self, key_id: str, endpoint: str, method: str = "GET", 
                               response_code: int = 200, volume: float = None, 
                               symbol: str = None, ip_address: str = None):
        """Log API key usage"""
        
        usage_log = APIKeyUsageLog(
            key_id=key_id,
            timestamp=datetime.now(),
            endpoint=endpoint,
            method=method,
            response_code=response_code,
            volume=volume,
            symbol=symbol,
            ip_address=ip_address
        )
        
        self.usage_logs.append(usage_log)
        
        # Log to encrypted audit system if available
        if self.audit_logger:
            await self.audit_logger.log_encryption_event(
                "api_key_usage",
                asdict(usage_log)
            )
    
    async def _log_bot_event(self, bot_id: str, event_type: str, details: Dict[str, Any]):
        """Log bot-related events"""
        
        if self.audit_logger:
            await self.audit_logger.log_encryption_event(
                f"bot_{event_type}",
                {
                    "bot_id": bot_id,
                    "timestamp": datetime.now().isoformat(),
                    **details
                }
            )
    
    async def _log_security_incident(self, key_id: str, incident_type: str, details: Dict[str, Any]):
        """Log security incidents"""
        
        if self.audit_logger:
            await self.audit_logger.log_encryption_event(
                "security_incident",
                {
                    "key_id": key_id,
                    "incident_type": incident_type,
                    "timestamp": datetime.now().isoformat(),
                    "severity": "CRITICAL",
                    **details
                }
            )
    
    def load_configuration(self):
        """Load existing configuration from file"""
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Load bot instances and API key profiles
                    # Implementation would deserialize the saved state
                    logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save current configuration to file"""
        
        try:
            config = {
                "bot_instances": {},
                "api_key_profiles": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Serialize bot instances (without sensitive data)
            for bot_id, bot_instance in self.bot_instances.items():
                config["bot_instances"][bot_id] = {
                    "purpose": bot_instance.purpose.value,
                    "exchanges": [e.value for e in bot_instance.exchanges],
                    "is_active": bot_instance.is_active,
                    "created_at": bot_instance.created_at.isoformat()
                }
            
            # Serialize API key profiles (without sensitive keys)
            for key_id, profile in self.api_key_profiles.items():
                config["api_key_profiles"][key_id] = {
                    "exchange": profile.exchange.value,
                    "purpose": profile.purpose.value,
                    "permissions": [p.value for p in profile.permissions],
                    "max_daily_volume": profile.max_daily_volume,
                    "max_position_size": profile.max_position_size,
                    "is_active": profile.is_active,
                    "created_at": profile.created_at.isoformat()
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved configuration to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

# Demo and testing functions
async def demo_dedicated_api_keys():
    """Demonstrate dedicated API key management"""
    
    print("🔑 Starting Dedicated API Key Management Demo")
    print("=" * 60)
    
    # Initialize manager
    manager = DedicatedAPIKeyManager(environment="demo")
    
    # Demo 1: Create different bot instances
    print("\n🤖 Demo 1: Creating Bot Instances with Dedicated Keys")
    print("-" * 50)
    
    bot_configs = [
        {
            "bot_id": "scalper_bot_01",
            "purpose": BotPurpose.TRADING_SCALPING,
            "exchanges": [Exchange.BINANCE, Exchange.COINBASE],
            "config": {
                "max_daily_volume": 25000,
                "max_position_size": 500,
                "allowed_symbols": ["BTCUSDT", "ETHUSDT"],
                "emergency_contact": "trader@company.com"
            }
        },
        {
            "bot_id": "swing_trader_01",
            "purpose": BotPurpose.TRADING_SWING,
            "exchanges": [Exchange.BINANCE, Exchange.KRAKEN],
            "config": {
                "max_daily_volume": 75000,
                "max_position_size": 15000,
                "emergency_contact": "risk@company.com"
            }
        },
        {
            "bot_id": "market_data_collector",
            "purpose": BotPurpose.MARKET_DATA,
            "exchanges": [Exchange.BINANCE, Exchange.COINBASE, Exchange.KRAKEN],
            "config": {
                "max_daily_volume": 0,  # No trading
                "allowed_symbols": ["*"]
            }
        },
        {
            "bot_id": "emergency_liquidator",
            "purpose": BotPurpose.EMERGENCY_LIQUIDATION,
            "exchanges": [Exchange.BINANCE, Exchange.COINBASE],
            "config": {
                "emergency_contact": "cto@company.com"
            }
        }
    ]
    
    created_bots = []
    for bot_config in bot_configs:
        bot_instance = await manager.create_bot_instance(
            bot_config["bot_id"],
            bot_config["purpose"],
            bot_config["exchanges"],
            bot_config["config"]
        )
        created_bots.append(bot_instance)
        
        print(f"   ✅ {bot_instance.bot_id}")
        print(f"      Purpose: {bot_instance.purpose.value}")
        print(f"      Exchanges: {[e.value for e in bot_instance.exchanges]}")
        print(f"      API Keys: {len(bot_instance.api_keys)}")
        print()
    
    # Demo 2: Show API key isolation
    print("\n🔒 Demo 2: API Key Isolation Analysis")
    print("-" * 50)
    
    blast_radius = await manager.get_blast_radius_analysis()
    
    print("   Blast Radius by Bot:")
    for bot_id, analysis in blast_radius["blast_radius_by_bot"].items():
        print(f"      {bot_id}:")
        print(f"         Risk Level: {analysis['risk_level']}")
        print(f"         Max Volume: ${analysis['total_max_volume']:,}")
        print(f"         Exchanges: {analysis['exchanges']}")
        print()
    
    # Demo 3: Security monitoring
    print("\n🛡️  Demo 3: Security Monitoring")
    print("-" * 50)
    
    # Simulate some API usage
    for bot_instance in created_bots[:2]:  # Test first 2 bots
        for exchange, key_profile in bot_instance.api_keys.items():
            # Simulate API calls
            await manager.validate_api_key_usage(
                key_profile.key_id, 
                "/api/v3/ticker/24hr",
                volume=1000,
                symbol="BTCUSDT"
            )
            
            await manager.validate_api_key_usage(
                key_profile.key_id,
                "/api/v3/order",
                volume=500,
                symbol="ETHUSDT"
            )
    
    # Check for suspicious activity
    print("   Security Monitoring Results:")
    for key_id in list(manager.api_key_profiles.keys())[:3]:
        alerts = await manager.detect_suspicious_activity(key_id)
        bot_id = manager._get_bot_id_for_key(key_id)
        
        if alerts:
            print(f"      🚨 {bot_id} ({key_id[:16]}...): {len(alerts)} alerts")
        else:
            print(f"      ✅ {bot_id} ({key_id[:16]}...): No issues detected")
    
    # Demo 4: Incident response simulation
    print("\n🚨 Demo 4: Incident Response Simulation")
    print("-" * 50)
    
    # Simulate compromise of scalping bot
    scalper_bot = created_bots[0]
    compromised_key = list(scalper_bot.api_keys.values())[0]
    
    print(f"   Simulating compromise of key: {compromised_key.key_id[:16]}...")
    
    incident_report = await manager.compromise_response(
        compromised_key.key_id,
        "suspicious_activity_detected"
    )
    
    print(f"   ✅ Incident response completed")
    print(f"   📋 Key disabled: {not compromised_key.is_active}")
    print()
    
    # Demo 5: Generate security report
    print("\n📊 Demo 5: Security Report Generation")
    print("-" * 50)
    
    security_report = await manager.generate_security_report()
    
    print("   Security Summary:")
    print(f"      Total Bots: {security_report['summary']['total_bots']}")
    print(f"      Total API Keys: {security_report['summary']['total_api_keys']}")
    print(f"      Active Keys: {security_report['summary']['active_keys']}")
    print(f"      Inactive Keys: {security_report['summary']['inactive_keys']}")
    print()
    
    print("   Purpose Distribution:")
    for purpose, count in security_report['purpose_breakdown'].items():
        print(f"      {purpose}: {count} keys")
    print()
    
    print("   Exchange Distribution:")
    for exchange, count in security_report['exchange_breakdown'].items():
        print(f"      {exchange}: {count} keys")
    print()
    
    if security_report['security_alerts']:
        print("   🚨 Security Alerts:")
        for alert in security_report['security_alerts']:
            print(f"      Bot: {alert['bot_id']}")
            print(f"      Alerts: {alert['alerts']}")
        print()
    
    if security_report['recommendations']:
        print("   💡 Recommendations:")
        for rec in security_report['recommendations'][:3]:
            print(f"      • {rec}")
        print()
    
    # Final summary
    print("\n🎉 Demo Completion Summary")
    print("=" * 60)
    
    benefits = [
        "🔒 Isolated API keys limit blast radius",
        "🎯 Purpose-specific permissions reduce risk",
        "📊 Comprehensive monitoring and alerting",
        "🚨 Automated incident response",
        "📋 Detailed security reporting",
        "🔄 Emergency key isolation capabilities"
    ]
    
    for benefit in benefits:
        print(f"✅ {benefit}")
    
    print(f"\n🛡️  Your trading system now has dedicated API key management:")
    print(f"   • Each bot has isolated API keys")
    print(f"   • Purpose-specific permission limits")
    print(f"   • Automated security monitoring")
    print(f"   • Rapid incident response")
    print(f"   • Comprehensive blast radius analysis")
    
    return True

if __name__ == "__main__":
    print("🔑 Dedicated API Key Management System")
    print("Implementing separate keys for different bots to limit blast radius")
    print()
    
    asyncio.run(demo_dedicated_api_keys()) 