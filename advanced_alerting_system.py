#!/usr/bin/env python3
"""
Advanced Alerting System for Cryptocurrency Trading
Multi-channel notifications, smart filtering, and escalation
"""

import smtplib
import logging
import json
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import requests
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class AlertChannel(Enum):
    """Available alert channels"""
    EMAIL = "EMAIL"
    SLACK = "SLACK"
    DISCORD = "DISCORD"
    TELEGRAM = "TELEGRAM"
    WEBHOOK = "WEBHOOK"
    SMS = "SMS"

@dataclass
class Alert:
    """Alert data structure"""
    title: str
    message: str
    level: AlertLevel
    timestamp: datetime
    symbol: Optional[str] = None
    price: Optional[float] = None
    change_percent: Optional[float] = None
    metadata: Optional[Dict] = None

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, config: Dict):
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.from_email = config.get('from_email', self.username)
        self.to_emails = config.get('to_emails', [])
        self.enabled = bool(self.username and self.password and self.to_emails)
        
        if self.enabled:
            logger.info("✅ Email notifications enabled")
        else:
            logger.warning("⚠️ Email notifications disabled - missing configuration")
    
    def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        if not self.enabled:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"🚨 {alert.level.value}: {alert.title}"
            
            # Create HTML body
            html_body = self._create_html_body(alert)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ Email alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
            return False
    
    def _create_html_body(self, alert: Alert) -> str:
        """Create HTML email body"""
        color_map = {
            AlertLevel.INFO: "#17a2b8",
            AlertLevel.WARNING: "#ffc107", 
            AlertLevel.CRITICAL: "#dc3545",
            AlertLevel.EMERGENCY: "#6f42c1"
        }
        
        color = color_map.get(alert.level, "#6c757d")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 Trading Alert</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px;">{alert.level.value}</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2 style="color: #333; margin-top: 0;">{alert.title}</h2>
                    <p style="color: #666; font-size: 16px; line-height: 1.5;">{alert.message}</p>
                    
                    {self._create_alert_details(alert)}
                    
                    <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                        <p style="margin: 0; color: #666; font-size: 14px;">
                            <strong>Timestamp:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                            <strong>System:</strong> AI Crypto Trading Bot
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_alert_details(self, alert: Alert) -> str:
        """Create alert details section"""
        if not alert.symbol:
            return ""
        
        details = f"""
        <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background-color: #f8f9fa;">
            <h3 style="margin-top: 0; color: #333;">Trading Details</h3>
            <p style="margin: 5px 0; color: #666;">
                <strong>Symbol:</strong> {alert.symbol}<br>
        """
        
        if alert.price:
            details += f"<strong>Price:</strong> ${alert.price:,.2f}<br>"
        
        if alert.change_percent:
            change_color = "#28a745" if alert.change_percent > 0 else "#dc3545"
            details += f"<strong>Change:</strong> <span style='color: {change_color};'>{alert.change_percent:+.2f}%</span><br>"
        
        details += "</p></div>"
        return details

class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self, config: Dict):
        self.webhook_url = config.get('webhook_url', '')
        self.channel = config.get('channel', '#trading-alerts')
        self.username = config.get('username', 'Trading Bot')
        self.enabled = bool(self.webhook_url)
        
        if self.enabled:
            logger.info("✅ Slack notifications enabled")
        else:
            logger.warning("⚠️ Slack notifications disabled - missing webhook URL")
    
    def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        if not self.enabled:
            return False
        
        try:
            # Create Slack message
            color_map = {
                AlertLevel.INFO: "#36a64f",
                AlertLevel.WARNING: "#ff9500",
                AlertLevel.CRITICAL: "#ff0000", 
                AlertLevel.EMERGENCY: "#800080"
            }
            
            emoji_map = {
                AlertLevel.INFO: ":information_source:",
                AlertLevel.WARNING: ":warning:",
                AlertLevel.CRITICAL: ":rotating_light:",
                AlertLevel.EMERGENCY: ":fire:"
            }
            
            payload = {
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": ":robot_face:",
                "attachments": [{
                    "color": color_map.get(alert.level, "#36a64f"),
                    "title": f"{emoji_map.get(alert.level, ':bell:')} {alert.title}",
                    "text": alert.message,
                    "fields": self._create_slack_fields(alert),
                    "footer": "AI Crypto Trading Bot",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Slack alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Slack alert: {e}")
            return False
    
    def _create_slack_fields(self, alert: Alert) -> List[Dict]:
        """Create Slack message fields"""
        fields = [
            {
                "title": "Level",
                "value": alert.level.value,
                "short": True
            },
            {
                "title": "Time",
                "value": alert.timestamp.strftime('%H:%M:%S UTC'),
                "short": True
            }
        ]
        
        if alert.symbol:
            fields.append({
                "title": "Symbol",
                "value": alert.symbol,
                "short": True
            })
        
        if alert.price:
            fields.append({
                "title": "Price",
                "value": f"${alert.price:,.2f}",
                "short": True
            })
        
        if alert.change_percent:
            fields.append({
                "title": "Change",
                "value": f"{alert.change_percent:+.2f}%",
                "short": True
            })
        
        return fields

class DiscordNotifier:
    """Discord notification handler"""
    
    def __init__(self, config: Dict):
        self.webhook_url = config.get('webhook_url', '')
        self.username = config.get('username', 'Trading Bot')
        self.enabled = bool(self.webhook_url)
        
        if self.enabled:
            logger.info("✅ Discord notifications enabled")
        else:
            logger.warning("⚠️ Discord notifications disabled - missing webhook URL")
    
    def send_alert(self, alert: Alert) -> bool:
        """Send Discord alert"""
        if not self.enabled:
            return False
        
        try:
            # Create Discord embed
            color_map = {
                AlertLevel.INFO: 0x3498db,
                AlertLevel.WARNING: 0xf39c12,
                AlertLevel.CRITICAL: 0xe74c3c,
                AlertLevel.EMERGENCY: 0x9b59b6
            }
            
            embed = {
                "title": f"🚨 {alert.title}",
                "description": alert.message,
                "color": color_map.get(alert.level, 0x95a5a6),
                "timestamp": alert.timestamp.isoformat(),
                "footer": {
                    "text": "AI Crypto Trading Bot"
                },
                "fields": []
            }
            
            # Add fields
            embed["fields"].append({
                "name": "Alert Level",
                "value": alert.level.value,
                "inline": True
            })
            
            if alert.symbol:
                embed["fields"].append({
                    "name": "Symbol",
                    "value": alert.symbol,
                    "inline": True
                })
            
            if alert.price:
                embed["fields"].append({
                    "name": "Price",
                    "value": f"${alert.price:,.2f}",
                    "inline": True
                })
            
            if alert.change_percent:
                embed["fields"].append({
                    "name": "Change",
                    "value": f"{alert.change_percent:+.2f}%",
                    "inline": True
                })
            
            payload = {
                "username": self.username,
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Discord alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Discord alert: {e}")
            return False

class AlertFilter:
    """Smart alert filtering to prevent spam"""
    
    def __init__(self):
        self.recent_alerts = {}
        self.cooldown_periods = {
            AlertLevel.INFO: 300,      # 5 minutes
            AlertLevel.WARNING: 180,   # 3 minutes
            AlertLevel.CRITICAL: 60,   # 1 minute
            AlertLevel.EMERGENCY: 0    # No cooldown
        }
    
    def should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent based on filtering rules"""
        alert_key = f"{alert.title}_{alert.symbol}_{alert.level.value}"
        current_time = time.time()
        
        # Check cooldown period
        if alert_key in self.recent_alerts:
            last_sent = self.recent_alerts[alert_key]
            cooldown = self.cooldown_periods.get(alert.level, 300)
            
            if current_time - last_sent < cooldown:
                logger.debug(f"Alert filtered due to cooldown: {alert.title}")
                return False
        
        # Update last sent time
        self.recent_alerts[alert_key] = current_time
        
        # Clean old entries
        self._cleanup_old_alerts()
        
        return True
    
    def _cleanup_old_alerts(self):
        """Remove old alert entries"""
        current_time = time.time()
        max_age = 3600  # 1 hour
        
        keys_to_remove = []
        for key, timestamp in self.recent_alerts.items():
            if current_time - timestamp > max_age:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.recent_alerts[key]

class AdvancedAlertingSystem:
    """Main alerting system coordinating all notification channels"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._load_default_config()
        self.notifiers = {}
        self.alert_filter = AlertFilter()
        self.alert_queue = []
        self.queue_lock = threading.Lock()
        
        # Initialize notifiers
        self._initialize_notifiers()
        
        # Start background worker
        self._start_background_worker()
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': os.getenv('EMAIL_USERNAME', ''),
                'password': os.getenv('EMAIL_PASSWORD', ''),
                'to_emails': os.getenv('EMAIL_RECIPIENTS', '').split(',') if os.getenv('EMAIL_RECIPIENTS') else []
            },
            'slack': {
                'enabled': False,
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
                'channel': '#trading-alerts'
            },
            'discord': {
                'enabled': False,
                'webhook_url': os.getenv('DISCORD_WEBHOOK_URL', ''),
                'username': 'Trading Bot'
            }
        }
    
    def _initialize_notifiers(self):
        """Initialize notification handlers"""
        if self.config.get('email', {}).get('enabled', False):
            self.notifiers[AlertChannel.EMAIL] = EmailNotifier(self.config['email'])
        
        if self.config.get('slack', {}).get('enabled', False):
            self.notifiers[AlertChannel.SLACK] = SlackNotifier(self.config['slack'])
        
        if self.config.get('discord', {}).get('enabled', False):
            self.notifiers[AlertChannel.DISCORD] = DiscordNotifier(self.config['discord'])
        
        logger.info(f"✅ Initialized {len(self.notifiers)} notification channels")
    
    def _start_background_worker(self):
        """Start background worker for processing alerts"""
        def worker():
            while True:
                try:
                    if self.alert_queue:
                        with self.queue_lock:
                            if self.alert_queue:
                                alert = self.alert_queue.pop(0)
                                self._process_alert(alert)
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    logger.error(f"Error in alert worker: {e}")
        
        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()
        logger.info("✅ Alert background worker started")
    
    def send_alert(self, title: str, message: str, level: AlertLevel = AlertLevel.INFO,
                   symbol: str = None, price: float = None, change_percent: float = None,
                   metadata: Dict = None, channels: List[AlertChannel] = None) -> bool:
        """Send alert through specified channels"""
        
        alert = Alert(
            title=title,
            message=message,
            level=level,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            price=price,
            change_percent=change_percent,
            metadata=metadata
        )
        
        # Apply filtering
        if not self.alert_filter.should_send_alert(alert):
            return False
        
        # Add to queue for processing
        with self.queue_lock:
            self.alert_queue.append((alert, channels))
        
        return True
    
    def _process_alert(self, alert_data: tuple):
        """Process alert through notification channels"""
        alert, channels = alert_data
        
        # Use all available channels if none specified
        if not channels:
            channels = list(self.notifiers.keys())
        
        success_count = 0
        for channel in channels:
            if channel in self.notifiers:
                try:
                    if self.notifiers[channel].send_alert(alert):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error sending alert via {channel.value}: {e}")
        
        logger.info(f"Alert sent via {success_count}/{len(channels)} channels: {alert.title}")
    
    def send_trading_signal_alert(self, symbol: str, direction: str, confidence: float,
                                  price: float, model_name: str = "AI Model"):
        """Send trading signal alert"""
        level = AlertLevel.INFO
        if confidence >= 0.8:
            level = AlertLevel.WARNING
        if confidence >= 0.9:
            level = AlertLevel.CRITICAL
        
        title = f"Trading Signal: {direction} {symbol}"
        message = f"AI model '{model_name}' generated a {direction} signal for {symbol} with {confidence:.1%} confidence at ${price:,.2f}"
        
        self.send_alert(
            title=title,
            message=message,
            level=level,
            symbol=symbol,
            price=price,
            metadata={'model': model_name, 'confidence': confidence}
        )
    
    def send_price_alert(self, symbol: str, current_price: float, change_percent: float,
                         threshold: float = 5.0):
        """Send price movement alert"""
        if abs(change_percent) < threshold:
            return
        
        direction = "increased" if change_percent > 0 else "decreased"
        level = AlertLevel.WARNING if abs(change_percent) >= 10 else AlertLevel.INFO
        
        title = f"Price Alert: {symbol} {direction} {abs(change_percent):.1f}%"
        message = f"{symbol} has {direction} by {abs(change_percent):.2f}% to ${current_price:,.2f}"
        
        self.send_alert(
            title=title,
            message=message,
            level=level,
            symbol=symbol,
            price=current_price,
            change_percent=change_percent
        )
    
    def send_system_alert(self, title: str, message: str, level: AlertLevel = AlertLevel.WARNING):
        """Send system status alert"""
        self.send_alert(
            title=f"System Alert: {title}",
            message=message,
            level=level
        )

# Usage example and testing
if __name__ == "__main__":
    print("🚨 Advanced Alerting System Test")
    print("=" * 50)
    
    # Initialize alerting system
    alerting_system = AdvancedAlertingSystem()
    
    # Test trading signal alert
    print("📡 Testing trading signal alert...")
    alerting_system.send_trading_signal_alert(
        symbol="BTC",
        direction="BUY",
        confidence=0.85,
        price=50000.0,
        model_name="LSTM Ensemble"
    )
    
    # Test price alert
    print("💰 Testing price alert...")
    alerting_system.send_price_alert(
        symbol="ETH",
        current_price=3200.0,
        change_percent=8.5
    )
    
    # Test system alert
    print("⚙️ Testing system alert...")
    alerting_system.send_system_alert(
        title="High CPU Usage",
        message="System CPU usage has exceeded 90% for the last 5 minutes",
        level=AlertLevel.WARNING
    )
    
    # Wait for alerts to process
    time.sleep(3)
    
    print("\n✅ Advanced Alerting System test completed!")
    print("Note: Actual notifications require proper configuration of email/Slack/Discord webhooks") 