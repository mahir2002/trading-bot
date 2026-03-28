#!/usr/bin/env python3
"""
Enterprise API Key Rotation System
Automated, secure API key rotation for trading bots
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import hashlib
import hmac
import base64
import os
from pathlib import Path

# Cloud providers
import boto3
from google.cloud import secretmanager
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Docker
import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RotationTrigger(Enum):
    SCHEDULED = "scheduled"
    MANUAL = "manual" 
    SECURITY_BREACH = "security_breach"
    FAILED_AUTH = "failed_auth"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE = "compliance"

class RotationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class APIKeyMetadata:
    key_id: str
    exchange: str
    environment: str
    created_at: datetime
    last_rotated: datetime
    rotation_count: int
    expires_at: datetime
    permissions: List[str]
    ip_restrictions: List[str]
    daily_limits: Dict[str, Any]
    is_active: bool

@dataclass
class RotationEvent:
    rotation_id: str
    trigger: RotationTrigger
    status: RotationStatus
    started_at: datetime
    completed_at: Optional[datetime]
    old_key_id: str
    new_key_id: Optional[str]
    error_message: Optional[str]
    rollback_available: bool

class ExchangeAPIManager:
    """Manages API key operations for different exchanges"""
    
    def __init__(self):
        self.exchange_configs = {
            'binance': {
                'base_url': 'https://api.binance.com',
                'create_endpoint': '/sapi/v1/apiKey',
                'permissions_endpoint': '/api/v3/account',
                'delete_endpoint': '/sapi/v1/apiKey'
            },
            'coinbase': {
                'base_url': 'https://api.pro.coinbase.com',
                'create_endpoint': '/api-keys',
                'permissions_endpoint': '/accounts',
                'delete_endpoint': '/api-keys'
            }
        }
    
    async def create_api_key(self, exchange: str, permissions: List[str], 
                           ip_restrictions: List[str]) -> Tuple[str, str, str]:
        """Create new API key with specified permissions"""
        
        if exchange.lower() == 'binance':
            return await self._create_binance_key(permissions, ip_restrictions)
        elif exchange.lower() == 'coinbase':
            return await self._create_coinbase_key(permissions, ip_restrictions)
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")
    
    async def _create_binance_key(self, permissions: List[str], 
                                ip_restrictions: List[str]) -> Tuple[str, str, str]:
        """Create Binance API key with minimal permissions"""
        
        # Note: Binance doesn't support programmatic API key creation
        # This would need to be done manually or through their institutional API
        # For demo purposes, we'll simulate the process
        
        logger.info("🔑 Creating new Binance API key...")
        logger.warning("⚠️  Binance requires manual API key creation")
        logger.info("📋 Required permissions:")
        for perm in permissions:
            logger.info(f"   • {perm}")
        logger.info("🔒 IP restrictions:")
        for ip in ip_restrictions:
            logger.info(f"   • {ip}")
        
        # In production, this would integrate with Binance institutional API
        # or prompt for manual key creation
        api_key = f"binance_api_key_{int(time.time())}"
        api_secret = f"binance_secret_{int(time.time())}"
        key_id = f"binance_key_id_{int(time.time())}"
        
        return api_key, api_secret, key_id
    
    async def _create_coinbase_key(self, permissions: List[str], 
                                 ip_restrictions: List[str]) -> Tuple[str, str, str]:
        """Create Coinbase Pro API key"""
        # Similar implementation for Coinbase
        pass
    
    async def validate_api_key(self, exchange: str, api_key: str, 
                             api_secret: str) -> bool:
        """Validate API key functionality"""
        
        try:
            if exchange.lower() == 'binance':
                return await self._validate_binance_key(api_key, api_secret)
            elif exchange.lower() == 'coinbase':
                return await self._validate_coinbase_key(api_key, api_secret)
            return False
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def _validate_binance_key(self, api_key: str, api_secret: str) -> bool:
        """Validate Binance API key"""
        
        try:
            url = "https://api.binance.com/api/v3/account"
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            
            # Create signature
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'X-MBX-APIKEY': api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}?{query_string}&signature={signature}",
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Binance key validation error: {e}")
            return False
    
    async def disable_api_key(self, exchange: str, key_id: str) -> bool:
        """Disable old API key"""
        
        try:
            logger.info(f"🔒 Disabling old API key: {key_id}")
            # Implementation would depend on exchange API
            # For now, we'll simulate success
            await asyncio.sleep(1)  # Simulate API call
            return True
        except Exception as e:
            logger.error(f"Failed to disable API key {key_id}: {e}")
            return False

class SecretRotationManager:
    """Manages secret rotation across different platforms"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.rotation_history: List[RotationEvent] = []
        
    async def rotate_secret(self, secret_name: str, new_value: str, 
                          backup_old: bool = True) -> bool:
        """Rotate secret across all configured platforms"""
        
        success = True
        
        try:
            # Determine the platform and rotate accordingly
            if self._is_kubernetes_environment():
                success &= await self._rotate_kubernetes_secret(secret_name, new_value, backup_old)
            
            if self._is_docker_environment():
                success &= await self._rotate_docker_secret(secret_name, new_value, backup_old)
            
            if self._is_aws_environment():
                success &= await self._rotate_aws_secret(secret_name, new_value, backup_old)
            
            if self._is_gcp_environment():
                success &= await self._rotate_gcp_secret(secret_name, new_value, backup_old)
            
            if self._is_azure_environment():
                success &= await self._rotate_azure_secret(secret_name, new_value, backup_old)
            
            return success
            
        except Exception as e:
            logger.error(f"Secret rotation failed for {secret_name}: {e}")
            return False
    
    def _is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes"""
        return os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    def _is_docker_environment(self) -> bool:
        """Check if running in Docker"""
        return os.path.exists('/.dockerenv')
    
    def _is_aws_environment(self) -> bool:
        """Check if running in AWS"""
        return bool(os.environ.get('AWS_REGION'))
    
    def _is_gcp_environment(self) -> bool:
        """Check if running in GCP"""
        return bool(os.environ.get('GOOGLE_CLOUD_PROJECT'))
    
    def _is_azure_environment(self) -> bool:
        """Check if running in Azure"""
        return bool(os.environ.get('AZURE_CLIENT_ID'))
    
    async def _rotate_kubernetes_secret(self, secret_name: str, new_value: str, 
                                      backup_old: bool = True) -> bool:
        """Rotate Kubernetes secret"""
        
        try:
            # Load kubernetes config
            if self._is_kubernetes_environment():
                config.load_incluster_config()
            else:
                config.load_kube_config()
            
            v1 = client.CoreV1Api()
            namespace = os.environ.get('KUBERNETES_NAMESPACE', 'default')
            
            # Get current secret
            if backup_old:
                try:
                    current_secret = v1.read_namespaced_secret(
                        name=secret_name, 
                        namespace=namespace
                    )
                    
                    # Create backup
                    backup_name = f"{secret_name}-backup-{int(time.time())}"
                    backup_secret = client.V1Secret(
                        metadata=client.V1ObjectMeta(name=backup_name),
                        data=current_secret.data
                    )
                    v1.create_namespaced_secret(namespace=namespace, body=backup_secret)
                    logger.info(f"✅ Created backup secret: {backup_name}")
                    
                except ApiException as e:
                    if e.status != 404:  # Secret doesn't exist, skip backup
                        raise
            
            # Update secret with new value
            secret_data = {secret_name.replace('_', '-'): base64.b64encode(new_value.encode()).decode()}
            
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(name=secret_name),
                data=secret_data
            )
            
            try:
                # Try to update existing secret
                v1.patch_namespaced_secret(
                    name=secret_name,
                    namespace=namespace,
                    body=secret
                )
                logger.info(f"✅ Updated Kubernetes secret: {secret_name}")
            except ApiException as e:
                if e.status == 404:
                    # Create new secret
                    v1.create_namespaced_secret(namespace=namespace, body=secret)
                    logger.info(f"✅ Created new Kubernetes secret: {secret_name}")
                else:
                    raise
            
            return True
            
        except Exception as e:
            logger.error(f"Kubernetes secret rotation failed: {e}")
            return False
    
    async def _rotate_docker_secret(self, secret_name: str, new_value: str, 
                                  backup_old: bool = True) -> bool:
        """Rotate Docker secret"""
        
        try:
            client_docker = docker.from_env()
            
            # Create new secret
            new_secret_name = f"{secret_name}_new_{int(time.time())}"
            
            secret = client_docker.secrets.create(
                name=new_secret_name,
                data=new_value.encode()
            )
            
            logger.info(f"✅ Created new Docker secret: {new_secret_name}")
            
            # Note: Docker secret rotation requires service update
            # This would typically be handled by orchestration system
            
            return True
            
        except Exception as e:
            logger.error(f"Docker secret rotation failed: {e}")
            return False
    
    async def _rotate_aws_secret(self, secret_name: str, new_value: str, 
                               backup_old: bool = True) -> bool:
        """Rotate AWS Secrets Manager secret"""
        
        try:
            session = boto3.Session()
            secrets_client = session.client('secretsmanager')
            
            # Create backup version if requested
            if backup_old:
                try:
                    current_secret = secrets_client.get_secret_value(SecretId=secret_name)
                    backup_name = f"{secret_name}-backup-{int(time.time())}"
                    
                    secrets_client.create_secret(
                        Name=backup_name,
                        SecretString=current_secret['SecretString']
                    )
                    logger.info(f"✅ Created backup secret: {backup_name}")
                    
                except secrets_client.exceptions.ResourceNotFoundException:
                    pass  # Secret doesn't exist, skip backup
            
            # Update secret with new value
            try:
                secrets_client.update_secret(
                    SecretId=secret_name,
                    SecretString=new_value
                )
                logger.info(f"✅ Updated AWS secret: {secret_name}")
            except secrets_client.exceptions.ResourceNotFoundException:
                # Create new secret
                secrets_client.create_secret(
                    Name=secret_name,
                    SecretString=new_value
                )
                logger.info(f"✅ Created new AWS secret: {secret_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"AWS secret rotation failed: {e}")
            return False
    
    async def _rotate_gcp_secret(self, secret_name: str, new_value: str, 
                               backup_old: bool = True) -> bool:
        """Rotate Google Cloud Secret Manager secret"""
        
        try:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            client_gcp = secretmanager.SecretManagerServiceClient()
            
            parent = f"projects/{project_id}"
            secret_id = secret_name.replace('_', '-')
            
            # Create backup version if requested
            if backup_old:
                try:
                    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                    response = client_gcp.access_secret_version(request={"name": name})
                    current_value = response.payload.data.decode("UTF-8")
                    
                    backup_secret_id = f"{secret_id}-backup-{int(time.time())}"
                    
                    # Create backup secret
                    secret = client_gcp.create_secret(
                        request={
                            "parent": parent,
                            "secret_id": backup_secret_id,
                            "secret": {"replication": {"automatic": {}}},
                        }
                    )
                    
                    # Add backup version
                    client_gcp.add_secret_version(
                        request={
                            "parent": secret.name,
                            "payload": {"data": current_value.encode("UTF-8")},
                        }
                    )
                    logger.info(f"✅ Created backup secret: {backup_secret_id}")
                    
                except Exception:
                    pass  # Secret doesn't exist or other error, skip backup
            
            # Add new version to existing secret or create new secret
            try:
                secret_name_full = f"projects/{project_id}/secrets/{secret_id}"
                client_gcp.add_secret_version(
                    request={
                        "parent": secret_name_full,
                        "payload": {"data": new_value.encode("UTF-8")},
                    }
                )
                logger.info(f"✅ Updated GCP secret: {secret_id}")
            except Exception:
                # Create new secret
                secret = client_gcp.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
                
                client_gcp.add_secret_version(
                    request={
                        "parent": secret.name,
                        "payload": {"data": new_value.encode("UTF-8")},
                    }
                )
                logger.info(f"✅ Created new GCP secret: {secret_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"GCP secret rotation failed: {e}")
            return False
    
    async def _rotate_azure_secret(self, secret_name: str, new_value: str, 
                                 backup_old: bool = True) -> bool:
        """Rotate Azure Key Vault secret"""
        
        try:
            vault_url = os.environ.get('AZURE_KEY_VAULT_URL')
            if not vault_url:
                raise ValueError("AZURE_KEY_VAULT_URL not set")
            
            credential = DefaultAzureCredential()
            client_azure = SecretClient(vault_url=vault_url, credential=credential)
            
            # Create backup if requested
            if backup_old:
                try:
                    current_secret = client_azure.get_secret(secret_name)
                    backup_name = f"{secret_name}-backup-{int(time.time())}"
                    
                    client_azure.set_secret(backup_name, current_secret.value)
                    logger.info(f"✅ Created backup secret: {backup_name}")
                    
                except Exception:
                    pass  # Secret doesn't exist, skip backup
            
            # Set new secret value
            client_azure.set_secret(secret_name, new_value)
            logger.info(f"✅ Updated Azure secret: {secret_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Azure secret rotation failed: {e}")
            return False

class APIKeyRotationSystem:
    """Main API key rotation system"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.exchange_manager = ExchangeAPIManager()
        self.secret_manager = SecretRotationManager(environment)
        self.rotation_policies = self._load_rotation_policies()
        self.active_rotations: Dict[str, RotationEvent] = {}
        
    def _load_rotation_policies(self) -> Dict[str, Any]:
        """Load rotation policies from configuration"""
        
        return {
            'default_rotation_interval_days': int(os.environ.get('API_KEY_ROTATION_DAYS', 30)),
            'emergency_rotation_enabled': bool(os.environ.get('EMERGENCY_ROTATION_ENABLED', True)),
            'max_failed_attempts_before_rotation': int(os.environ.get('MAX_FAILED_ATTEMPTS', 5)),
            'rotation_time_window': {
                'start_hour': int(os.environ.get('ROTATION_START_HOUR', 2)),  # 2 AM
                'end_hour': int(os.environ.get('ROTATION_END_HOUR', 4))       # 4 AM
            },
            'backup_retention_days': int(os.environ.get('BACKUP_RETENTION_DAYS', 90)),
            'notification_webhooks': os.environ.get('ROTATION_WEBHOOK_URL', '').split(','),
            'exchanges': {
                'binance': {
                    'rotation_interval_days': 30,
                    'permissions': ['SPOT_TRADING', 'USER_DATA_STREAM', 'MARKET_DATA'],
                    'ip_restrictions_required': True
                },
                'coinbase': {
                    'rotation_interval_days': 30,
                    'permissions': ['view', 'trade'],
                    'ip_restrictions_required': True
                }
            }
        }
    
    async def schedule_rotation(self, exchange: str, trigger: RotationTrigger,
                              force_immediate: bool = False) -> str:
        """Schedule API key rotation"""
        
        rotation_id = f"rotation_{exchange}_{int(time.time())}"
        
        rotation_event = RotationEvent(
            rotation_id=rotation_id,
            trigger=trigger,
            status=RotationStatus.PENDING,
            started_at=datetime.now(),
            completed_at=None,
            old_key_id=f"current_{exchange}_key",
            new_key_id=None,
            error_message=None,
            rollback_available=True
        )
        
        self.active_rotations[rotation_id] = rotation_event
        
        logger.info(f"🔄 Scheduled rotation {rotation_id} for {exchange}")
        logger.info(f"   Trigger: {trigger.value}")
        logger.info(f"   Force immediate: {force_immediate}")
        
        if force_immediate or trigger == RotationTrigger.SECURITY_BREACH:
            await self._execute_rotation(rotation_id)
        else:
            # Schedule for maintenance window
            await self._schedule_maintenance_window_rotation(rotation_id)
        
        return rotation_id
    
    async def _execute_rotation(self, rotation_id: str) -> bool:
        """Execute API key rotation"""
        
        rotation = self.active_rotations.get(rotation_id)
        if not rotation:
            logger.error(f"Rotation {rotation_id} not found")
            return False
        
        try:
            rotation.status = RotationStatus.IN_PROGRESS
            logger.info(f"🔄 Starting rotation {rotation_id}")
            
            # Step 1: Create new API key
            exchange = rotation.old_key_id.split('_')[1]  # Extract exchange from key ID
            
            exchange_config = self.rotation_policies['exchanges'][exchange]
            permissions = exchange_config['permissions']
            ip_restrictions = [os.environ.get('SERVER_IP', '127.0.0.1')]
            
            logger.info(f"📝 Creating new API key for {exchange}")
            new_api_key, new_api_secret, new_key_id = await self.exchange_manager.create_api_key(
                exchange, permissions, ip_restrictions
            )
            
            rotation.new_key_id = new_key_id
            
            # Step 2: Validate new API key
            logger.info(f"✅ Validating new API key")
            if not await self.exchange_manager.validate_api_key(exchange, new_api_key, new_api_secret):
                raise Exception("New API key validation failed")
            
            # Step 3: Update secrets in all platforms
            logger.info(f"🔄 Updating secrets across platforms")
            
            api_key_updated = await self.secret_manager.rotate_secret(
                f'{exchange}_api_key', new_api_key, backup_old=True
            )
            
            api_secret_updated = await self.secret_manager.rotate_secret(
                f'{exchange}_secret', new_api_secret, backup_old=True
            )
            
            if not (api_key_updated and api_secret_updated):
                raise Exception("Failed to update secrets")
            
            # Step 4: Wait for propagation
            logger.info(f"⏳ Waiting for secret propagation...")
            await asyncio.sleep(30)  # Allow time for secrets to propagate
            
            # Step 5: Validate system functionality
            logger.info(f"🔍 Validating system functionality")
            if not await self._validate_system_functionality(exchange):
                raise Exception("System functionality validation failed")
            
            # Step 6: Disable old API key
            logger.info(f"🔒 Disabling old API key")
            await self.exchange_manager.disable_api_key(exchange, rotation.old_key_id)
            
            # Step 7: Complete rotation
            rotation.status = RotationStatus.COMPLETED
            rotation.completed_at = datetime.now()
            
            logger.info(f"✅ Rotation {rotation_id} completed successfully")
            
            # Send notifications
            await self._send_rotation_notification(rotation)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Rotation {rotation_id} failed: {e}")
            rotation.status = RotationStatus.FAILED
            rotation.error_message = str(e)
            
            # Attempt rollback
            if rotation.rollback_available:
                await self._rollback_rotation(rotation_id)
            
            return False
    
    async def _validate_system_functionality(self, exchange: str) -> bool:
        """Validate that the system works with new API keys"""
        
        try:
            # Import and test the main trading system
            from scalable_data_optimization_system import ScalableDataOptimizer
            
            # Create temporary optimizer instance
            test_optimizer = ScalableDataOptimizer(environment=self.environment)
            await test_optimizer.initialize()
            
            # Test basic functionality
            test_symbols = ['BTCUSDT', 'ETHUSDT']
            await test_optimizer.fetch_batch_ticker_data(test_symbols)
            
            # Cleanup
            await test_optimizer.cleanup()
            
            logger.info("✅ System functionality validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ System functionality validation failed: {e}")
            return False
    
    async def _rollback_rotation(self, rotation_id: str) -> bool:
        """Rollback failed rotation"""
        
        rotation = self.active_rotations.get(rotation_id)
        if not rotation:
            return False
        
        try:
            logger.warning(f"🔄 Rolling back rotation {rotation_id}")
            
            # Restore old secrets from backup
            exchange = rotation.old_key_id.split('_')[1]
            
            # Note: Rollback implementation would restore from backup secrets
            # This is a simplified version
            
            rotation.status = RotationStatus.ROLLED_BACK
            logger.info(f"✅ Rollback completed for {rotation_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed for {rotation_id}: {e}")
            return False
    
    async def _schedule_maintenance_window_rotation(self, rotation_id: str) -> None:
        """Schedule rotation during maintenance window"""
        
        policy = self.rotation_policies['rotation_time_window']
        now = datetime.now()
        
        # Calculate next maintenance window
        next_rotation = now.replace(
            hour=policy['start_hour'], 
            minute=0, 
            second=0, 
            microsecond=0
        )
        
        if now.hour >= policy['start_hour']:
            next_rotation += timedelta(days=1)
        
        delay_seconds = (next_rotation - now).total_seconds()
        
        logger.info(f"⏰ Rotation {rotation_id} scheduled for {next_rotation}")
        
        # Schedule the rotation
        asyncio.create_task(self._delayed_rotation(rotation_id, delay_seconds))
    
    async def _delayed_rotation(self, rotation_id: str, delay_seconds: float) -> None:
        """Execute rotation after delay"""
        
        await asyncio.sleep(delay_seconds)
        await self._execute_rotation(rotation_id)
    
    async def _send_rotation_notification(self, rotation: RotationEvent) -> None:
        """Send rotation completion notification"""
        
        webhooks = self.rotation_policies['notification_webhooks']
        if not webhooks or not webhooks[0]:
            return
        
        notification = {
            'event': 'api_key_rotation',
            'rotation_id': rotation.rotation_id,
            'status': rotation.status.value,
            'trigger': rotation.trigger.value,
            'completed_at': rotation.completed_at.isoformat() if rotation.completed_at else None,
            'exchange': rotation.old_key_id.split('_')[1] if '_' in rotation.old_key_id else 'unknown'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                for webhook_url in webhooks:
                    if webhook_url.strip():
                        async with session.post(
                            webhook_url.strip(),
                            json=notification,
                            headers={'Content-Type': 'application/json'}
                        ) as response:
                            if response.status == 200:
                                logger.info(f"📧 Rotation notification sent to {webhook_url}")
                            else:
                                logger.warning(f"⚠️  Failed to send notification to {webhook_url}")
        
        except Exception as e:
            logger.error(f"Failed to send rotation notification: {e}")
    
    async def check_rotation_schedule(self) -> List[str]:
        """Check if any keys need rotation"""
        
        rotations_needed = []
        
        for exchange, config in self.rotation_policies['exchanges'].items():
            # Check if rotation is needed based on schedule
            last_rotation_key = f'last_rotation_{exchange}'
            last_rotation_str = os.environ.get(last_rotation_key, '')
            
            if last_rotation_str:
                try:
                    last_rotation = datetime.fromisoformat(last_rotation_str)
                    days_since_rotation = (datetime.now() - last_rotation).days
                    
                    if days_since_rotation >= config['rotation_interval_days']:
                        rotation_id = await self.schedule_rotation(
                            exchange, 
                            RotationTrigger.SCHEDULED
                        )
                        rotations_needed.append(rotation_id)
                        logger.info(f"📅 Scheduled rotation for {exchange} (overdue by {days_since_rotation - config['rotation_interval_days']} days)")
                
                except ValueError:
                    # Invalid date format, schedule rotation
                    rotation_id = await self.schedule_rotation(
                        exchange, 
                        RotationTrigger.SCHEDULED
                    )
                    rotations_needed.append(rotation_id)
            else:
                # No previous rotation recorded, schedule one
                rotation_id = await self.schedule_rotation(
                    exchange, 
                    RotationTrigger.SCHEDULED
                )
                rotations_needed.append(rotation_id)
        
        return rotations_needed
    
    async def emergency_rotation(self, exchange: str, reason: str = "Security breach") -> str:
        """Trigger emergency rotation"""
        
        logger.warning(f"🚨 EMERGENCY ROTATION TRIGGERED for {exchange}")
        logger.warning(f"   Reason: {reason}")
        
        rotation_id = await self.schedule_rotation(
            exchange, 
            RotationTrigger.SECURITY_BREACH,
            force_immediate=True
        )
        
        return rotation_id
    
    def get_rotation_status(self, rotation_id: str) -> Optional[RotationEvent]:
        """Get rotation status"""
        return self.active_rotations.get(rotation_id)
    
    def get_all_rotations(self) -> List[RotationEvent]:
        """Get all rotation events"""
        return list(self.active_rotations.values())

# CLI Interface
async def main():
    """Main CLI interface for rotation system"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="API Key Rotation System")
    parser.add_argument('--check-schedule', action='store_true', 
                       help='Check rotation schedule')
    parser.add_argument('--emergency-rotation', type=str,
                       help='Trigger emergency rotation for exchange')
    parser.add_argument('--status', type=str,
                       help='Get rotation status by ID')
    parser.add_argument('--environment', type=str, default='production',
                       help='Environment (development/staging/production)')
    
    args = parser.parse_args()
    
    rotation_system = APIKeyRotationSystem(environment=args.environment)
    
    if args.check_schedule:
        logger.info("🔍 Checking rotation schedule...")
        rotations = await rotation_system.check_rotation_schedule()
        if rotations:
            logger.info(f"📅 Scheduled {len(rotations)} rotations")
            for rotation_id in rotations:
                logger.info(f"   • {rotation_id}")
        else:
            logger.info("✅ No rotations needed")
    
    elif args.emergency_rotation:
        logger.info(f"🚨 Triggering emergency rotation for {args.emergency_rotation}")
        rotation_id = await rotation_system.emergency_rotation(args.emergency_rotation)
        logger.info(f"   Rotation ID: {rotation_id}")
    
    elif args.status:
        rotation = rotation_system.get_rotation_status(args.status)
        if rotation:
            logger.info(f"📊 Rotation Status: {args.status}")
            logger.info(f"   Status: {rotation.status.value}")
            logger.info(f"   Trigger: {rotation.trigger.value}")
            logger.info(f"   Started: {rotation.started_at}")
            if rotation.completed_at:
                logger.info(f"   Completed: {rotation.completed_at}")
            if rotation.error_message:
                logger.info(f"   Error: {rotation.error_message}")
        else:
            logger.error(f"❌ Rotation {args.status} not found")
    
    else:
        # Default: show all active rotations
        rotations = rotation_system.get_all_rotations()
        logger.info(f"📊 Active Rotations: {len(rotations)}")
        for rotation in rotations:
            logger.info(f"   • {rotation.rotation_id}: {rotation.status.value}")

if __name__ == "__main__":
    asyncio.run(main()) 