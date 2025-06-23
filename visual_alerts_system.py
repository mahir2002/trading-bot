#!/usr/bin/env python3
"""
🚨 Visual Alerts & Notifications System
Advanced visual alert system for trading dashboard with real-time notifications,
critical event monitoring, and multi-level alert management.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
import numpy as np
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Import WebSocket integration
from websocket_dash_integration import DashWebSocketIntegration

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"

class AlertCategory(Enum):
    """Alert categories"""
    SYSTEM = "system"
    TRADING = "trading"
    PORTFOLIO = "portfolio"
    MARKET = "market"
    RISK = "risk"
    PERFORMANCE = "performance"

@dataclass
class VisualAlert:
    """Visual alert data structure"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    category: AlertCategory
    timestamp: datetime
    symbol: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    auto_dismiss: bool = True
    dismiss_after: int = 5000  # milliseconds
    persistent: bool = False
    sound_alert: bool = False
    flash_alert: bool = False

class VisualAlertsSystem:
    """Advanced visual alerts and notifications system"""
    
    def __init__(self, app: dash.Dash):
        self.app = app
        self.logger = self._setup_logger()
        
        # Alert management
        self.active_alerts: Dict[str, VisualAlert] = {}
        self.alert_history: List[VisualAlert] = []
        self.alert_queue = []
        self.max_history = 1000
        
        # Alert thresholds and configurations
        self.alert_thresholds = self._initialize_alert_thresholds()
        self.notification_settings = self._initialize_notification_settings()
        
        # WebSocket integration for real-time data
        self.ws_integration = DashWebSocketIntegration(app)
        
        # Alert monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = None
        
        self.logger.info("🚨 Visual Alerts System initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for alerts system"""
        logger = logging.getLogger('VisualAlerts')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_alert_thresholds(self) -> Dict[str, Dict]:
        """Initialize alert thresholds for different metrics"""
        return {
            # Portfolio thresholds
            'portfolio_balance': {
                'low_balance_warning': 1000,  # $1,000
                'low_balance_critical': 500,  # $500
            },
            'daily_pnl': {
                'loss_warning': -0.05,  # -5%
                'loss_critical': -0.10,  # -10%
                'gain_celebration': 0.05,  # +5%
            },
            'drawdown': {
                'warning_level': 0.10,  # 10%
                'critical_level': 0.20,  # 20%
                'emergency_level': 0.30,  # 30%
            },
            
            # Market movement thresholds
            'price_movement': {
                'significant_move': 0.05,  # 5%
                'major_move': 0.10,  # 10%
                'extreme_move': 0.20,  # 20%
            },
            'volume_spike': {
                'unusual_volume': 2.0,  # 2x normal
                'extreme_volume': 5.0,  # 5x normal
            },
            
            # System performance thresholds
            'system_performance': {
                'cpu_warning': 80,  # 80%
                'cpu_critical': 95,  # 95%
                'memory_warning': 85,  # 85%
                'memory_critical': 95,  # 95%
                'api_latency_warning': 2000,  # 2 seconds
                'api_latency_critical': 5000,  # 5 seconds
            },
            
            # Trading signal thresholds
            'trading_signals': {
                'high_confidence': 0.8,  # 80%
                'very_high_confidence': 0.9,  # 90%
                'conflicting_signals': 3,  # 3+ conflicting signals
            }
        }
    
    def _initialize_notification_settings(self) -> Dict[str, Any]:
        """Initialize notification settings"""
        return {
            'enable_sound': True,
            'enable_flash': True,
            'enable_desktop_notifications': True,
            'auto_dismiss_info': True,
            'auto_dismiss_success': True,
            'auto_dismiss_warning': False,
            'auto_dismiss_danger': False,
            'auto_dismiss_critical': False,
            'max_concurrent_alerts': 5,
            'alert_position': 'top-right',
            'theme': 'dark'
        }
    
    def create_alerts_layout(self):
        """Create visual alerts layout components"""
        
        return html.Div([
            # Alert container (positioned overlay)
            html.Div(
                id="alerts-container",
                className="alerts-overlay",
                style={
                    'position': 'fixed',
                    'top': '20px',
                    'right': '20px',
                    'zIndex': '9999',
                    'maxWidth': '400px',
                    'pointerEvents': 'none'
                }
            ),
            
            # Alert banner for critical system-wide alerts
            html.Div(
                id="alert-banner",
                className="alert-banner",
                style={'display': 'none'}
            ),
            
            # Alert status indicator
            html.Div([
                dbc.Badge(
                    id="alert-status-badge",
                    children="System OK",
                    color="success",
                    className="position-fixed",
                    style={
                        'top': '10px',
                        'left': '10px',
                        'zIndex': '1000',
                        'fontSize': '12px'
                    }
                )
            ]),
            
            # Alert history modal
            dbc.Modal([
                dbc.ModalHeader("📋 Alert History"),
                dbc.ModalBody([
                    html.Div(id="alert-history-content")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Clear History", id="clear-history-btn", color="warning"),
                    dbc.Button("Close", id="close-history-modal", color="secondary")
                ])
            ], id="alert-history-modal", size="lg"),
            
            # Alert settings modal
            dbc.Modal([
                dbc.ModalHeader("⚙️ Alert Settings"),
                dbc.ModalBody([
                    self._create_alert_settings_content()
                ]),
                dbc.ModalFooter([
                    dbc.Button("Save Settings", id="save-alert-settings", color="primary"),
                    dbc.Button("Close", id="close-settings-modal", color="secondary")
                ])
            ], id="alert-settings-modal", size="lg"),
            
            # Hidden components for alert management
            dcc.Store(id="active-alerts-store", data={}),
            dcc.Store(id="alert-settings-store", data=self.notification_settings),
            dcc.Store(id="alert-thresholds-store", data=self.alert_thresholds),
            
            # Alert monitoring interval
            dcc.Interval(
                id="alert-monitor-interval",
                interval=1000,  # Check every second
                n_intervals=0
            ),
            
            # WebSocket components
            self.ws_integration.setup_websocket_components()
        ])
    
    def _create_alert_settings_content(self):
        """Create alert settings configuration interface"""
        
        return dbc.Container([
            # General settings
            dbc.Row([
                dbc.Col([
                    html.H5("🔔 General Settings"),
                    dbc.Switch(
                        id="enable-sound-alerts",
                        label="Enable Sound Alerts",
                        value=self.notification_settings['enable_sound']
                    ),
                    dbc.Switch(
                        id="enable-flash-alerts",
                        label="Enable Flash Alerts",
                        value=self.notification_settings['enable_flash']
                    ),
                    dbc.Switch(
                        id="enable-desktop-notifications",
                        label="Enable Desktop Notifications",
                        value=self.notification_settings['enable_desktop_notifications']
                    )
                ])
            ], className="mb-4"),
            
            # Auto-dismiss settings
            dbc.Row([
                dbc.Col([
                    html.H5("⏰ Auto-Dismiss Settings"),
                    dbc.Switch(
                        id="auto-dismiss-info",
                        label="Auto-dismiss Info alerts",
                        value=self.notification_settings['auto_dismiss_info']
                    ),
                    dbc.Switch(
                        id="auto-dismiss-success",
                        label="Auto-dismiss Success alerts",
                        value=self.notification_settings['auto_dismiss_success']
                    ),
                    dbc.Switch(
                        id="auto-dismiss-warning",
                        label="Auto-dismiss Warning alerts",
                        value=self.notification_settings['auto_dismiss_warning']
                    )
                ])
            ], className="mb-4"),
            
            # Threshold settings
            dbc.Row([
                dbc.Col([
                    html.H5("📊 Alert Thresholds"),
                    html.Label("Portfolio Low Balance Warning ($):"),
                    dbc.Input(
                        id="low-balance-threshold",
                        type="number",
                        value=self.alert_thresholds['portfolio_balance']['low_balance_warning'],
                        className="mb-2"
                    ),
                    html.Label("Daily Loss Warning (%):"),
                    dbc.Input(
                        id="daily-loss-threshold",
                        type="number",
                        value=abs(self.alert_thresholds['daily_pnl']['loss_warning'] * 100),
                        className="mb-2"
                    ),
                    html.Label("Drawdown Warning (%):"),
                    dbc.Input(
                        id="drawdown-threshold",
                        type="number",
                        value=self.alert_thresholds['drawdown']['warning_level'] * 100,
                        className="mb-2"
                    )
                ])
            ])
        ])
    
    def create_alert_component(self, alert: VisualAlert) -> dbc.Alert:
        """Create individual alert component"""
        
        # Determine alert styling
        color_map = {
            AlertSeverity.INFO: "info",
            AlertSeverity.SUCCESS: "success", 
            AlertSeverity.WARNING: "warning",
            AlertSeverity.DANGER: "danger",
            AlertSeverity.CRITICAL: "danger"
        }
        
        icon_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.SUCCESS: "✅",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.DANGER: "🚨",
            AlertSeverity.CRITICAL: "🔥"
        }
        
        # Create alert content
        alert_content = [
            html.Div([
                html.Strong([
                    icon_map.get(alert.severity, "📢"),
                    f" {alert.title}"
                ]),
                html.Br(),
                html.Span(alert.message, className="small")
            ])
        ]
        
        # Add symbol and value if available
        if alert.symbol or alert.value is not None:
            details = []
            if alert.symbol:
                details.append(f"Symbol: {alert.symbol}")
            if alert.value is not None:
                if alert.threshold is not None:
                    details.append(f"Value: {alert.value:.2f} (Threshold: {alert.threshold:.2f})")
                else:
                    details.append(f"Value: {alert.value:.2f}")
            
            if details:
                alert_content.append(html.Hr(className="my-2"))
                alert_content.append(html.Small(" | ".join(details)))
        
        # Add timestamp
        alert_content.append(html.Hr(className="my-2"))
        alert_content.append(html.Small(
            f"🕐 {alert.timestamp.strftime('%H:%M:%S')}",
            className="text-muted"
        ))
        
        # Create dismissible alert
        return dbc.Alert(
            alert_content,
            id={'type': 'alert-item', 'alert_id': alert.id},
            color=color_map.get(alert.severity, "info"),
            dismissable=not alert.persistent,
            className=f"alert-{alert.severity.value} {'flash-alert' if alert.flash_alert else ''}",
            style={
                'pointerEvents': 'auto',
                'marginBottom': '10px',
                'boxShadow': '0 4px 8px rgba(0,0,0,0.1)',
                'border': f'2px solid {"#dc3545" if alert.severity == AlertSeverity.CRITICAL else "transparent"}'
            }
        )
    
    def add_alert(self, title: str, message: str, severity: AlertSeverity = AlertSeverity.INFO,
                  category: AlertCategory = AlertCategory.SYSTEM, symbol: str = None,
                  value: float = None, threshold: float = None, metadata: Dict = None,
                  auto_dismiss: bool = None, persistent: bool = False,
                  sound_alert: bool = None, flash_alert: bool = None) -> str:
        """Add new visual alert"""
        
        # Generate unique alert ID
        alert_id = str(uuid.uuid4())
        
        # Apply default settings if not specified
        if auto_dismiss is None:
            auto_dismiss = self.notification_settings.get(f'auto_dismiss_{severity.value}', True)
        
        if sound_alert is None:
            sound_alert = self.notification_settings['enable_sound'] and severity in [AlertSeverity.WARNING, AlertSeverity.DANGER, AlertSeverity.CRITICAL]
        
        if flash_alert is None:
            flash_alert = self.notification_settings['enable_flash'] and severity in [AlertSeverity.DANGER, AlertSeverity.CRITICAL]
        
        # Create alert
        alert = VisualAlert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            category=category,
            timestamp=datetime.now(),
            symbol=symbol,
            value=value,
            threshold=threshold,
            metadata=metadata or {},
            auto_dismiss=auto_dismiss,
            persistent=persistent,
            sound_alert=sound_alert,
            flash_alert=flash_alert
        )
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # Log alert
        self.logger.info(f"🚨 Alert added: {severity.value.upper()} - {title}")
        
        return alert_id
    
    def remove_alert(self, alert_id: str):
        """Remove alert from active alerts"""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            self.logger.debug(f"Alert removed: {alert_id}")
    
    def clear_all_alerts(self):
        """Clear all active alerts"""
        self.active_alerts.clear()
        self.logger.info("All alerts cleared")
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of active alerts by severity"""
        summary = {severity.value: 0 for severity in AlertSeverity}
        
        for alert in self.active_alerts.values():
            summary[alert.severity.value] += 1
        
        return summary
    
    def setup_alert_callbacks(self):
        """Setup callbacks for alert system"""
        
        # Main alert display callback
        @self.app.callback(
            [Output('alerts-container', 'children'),
             Output('alert-status-badge', 'children'),
             Output('alert-status-badge', 'color')],
            [Input('alert-monitor-interval', 'n_intervals'),
             Input('websocket-data-store', 'data'),
             Input({'type': 'alert-item', 'alert_id': ALL}, 'is_open')],
            [State('active-alerts-store', 'data'),
             State('alert-settings-store', 'data')]
        )
        def update_alerts_display(n_intervals, websocket_data, alert_states, active_alerts_data, settings):
            """Update alerts display"""
            
            # Process WebSocket data for new alerts
            if websocket_data:
                self._process_websocket_alerts(websocket_data)
            
            # Create alert components
            alert_components = []
            for alert in list(self.active_alerts.values()):
                # Check if alert should be auto-dismissed
                if alert.auto_dismiss and not alert.persistent:
                    age = (datetime.now() - alert.timestamp).total_seconds() * 1000
                    if age > alert.dismiss_after:
                        self.remove_alert(alert.id)
                        continue
                
                alert_components.append(self.create_alert_component(alert))
            
            # Limit concurrent alerts
            max_alerts = settings.get('max_concurrent_alerts', 5)
            if len(alert_components) > max_alerts:
                alert_components = alert_components[:max_alerts]
            
            # Update status badge
            summary = self.get_alert_summary()
            total_alerts = sum(summary.values())
            
            if summary['critical'] > 0:
                badge_text = f"🔥 {summary['critical']} Critical"
                badge_color = "danger"
            elif summary['danger'] > 0:
                badge_text = f"🚨 {summary['danger']} Alerts"
                badge_color = "danger"
            elif summary['warning'] > 0:
                badge_text = f"⚠️ {summary['warning']} Warnings"
                badge_color = "warning"
            elif total_alerts > 0:
                badge_text = f"📢 {total_alerts} Alerts"
                badge_color = "info"
            else:
                badge_text = "✅ System OK"
                badge_color = "success"
            
            return alert_components, badge_text, badge_color
        
        # Alert history callback
        @self.app.callback(
            Output('alert-history-content', 'children'),
            [Input('alert-history-modal', 'is_open')]
        )
        def update_alert_history(is_open):
            """Update alert history display"""
            if not is_open:
                return []
            
            if not self.alert_history:
                return [dbc.Alert("No alerts in history", color="info")]
            
            history_items = []
            for alert in reversed(self.alert_history[-50:]):  # Show last 50 alerts
                severity_color = {
                    AlertSeverity.INFO: "info",
                    AlertSeverity.SUCCESS: "success",
                    AlertSeverity.WARNING: "warning", 
                    AlertSeverity.DANGER: "danger",
                    AlertSeverity.CRITICAL: "danger"
                }.get(alert.severity, "secondary")
                
                history_items.append(
                    dbc.ListGroupItem([
                        html.Div([
                            dbc.Badge(alert.severity.value.upper(), color=severity_color, className="me-2"),
                            html.Strong(alert.title),
                            html.Small(f" - {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", className="text-muted ms-2")
                        ]),
                        html.P(alert.message, className="mb-1 mt-2"),
                        html.Small([
                            f"Category: {alert.category.value}",
                            f" | Symbol: {alert.symbol}" if alert.symbol else "",
                            f" | Value: {alert.value:.2f}" if alert.value is not None else ""
                        ], className="text-muted")
                    ])
                )
            
            return [dbc.ListGroup(history_items)]
        
        # Clear history callback
        @self.app.callback(
            Output('alert-history-modal', 'is_open', allow_duplicate=True),
            [Input('clear-history-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def clear_alert_history(n_clicks):
            """Clear alert history"""
            if n_clicks:
                self.alert_history.clear()
                self.logger.info("Alert history cleared")
            return False
    
    def _process_websocket_alerts(self, websocket_data: Dict):
        """Process WebSocket data and generate alerts"""
        
        try:
            # Portfolio balance alerts
            portfolio_value = websocket_data.get('portfolio_value', 0)
            if portfolio_value > 0:
                low_balance_threshold = self.alert_thresholds['portfolio_balance']['low_balance_warning']
                critical_balance_threshold = self.alert_thresholds['portfolio_balance']['low_balance_critical']
                
                if portfolio_value <= critical_balance_threshold:
                    self.add_alert(
                        title="Critical: Low Portfolio Balance",
                        message=f"Portfolio balance is critically low: ${portfolio_value:,.2f}",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.PORTFOLIO,
                        value=portfolio_value,
                        threshold=critical_balance_threshold,
                        persistent=True
                    )
                elif portfolio_value <= low_balance_threshold:
                    self.add_alert(
                        title="Warning: Low Portfolio Balance",
                        message=f"Portfolio balance is below warning threshold: ${portfolio_value:,.2f}",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.PORTFOLIO,
                        value=portfolio_value,
                        threshold=low_balance_threshold
                    )
            
            # Daily P&L alerts
            daily_pnl = websocket_data.get('daily_pnl_percent', 0)
            if daily_pnl != 0:
                loss_warning = self.alert_thresholds['daily_pnl']['loss_warning']
                loss_critical = self.alert_thresholds['daily_pnl']['loss_critical']
                gain_celebration = self.alert_thresholds['daily_pnl']['gain_celebration']
                
                if daily_pnl <= loss_critical:
                    self.add_alert(
                        title="Critical: High Daily Loss",
                        message=f"Daily P&L is critically low: {daily_pnl:.2%}",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.PORTFOLIO,
                        value=daily_pnl,
                        threshold=loss_critical,
                        persistent=True
                    )
                elif daily_pnl <= loss_warning:
                    self.add_alert(
                        title="Warning: Daily Loss Threshold",
                        message=f"Daily P&L below warning threshold: {daily_pnl:.2%}",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.PORTFOLIO,
                        value=daily_pnl,
                        threshold=loss_warning
                    )
                elif daily_pnl >= gain_celebration:
                    self.add_alert(
                        title="Excellent Daily Performance!",
                        message=f"Daily P&L exceeds target: {daily_pnl:.2%}",
                        severity=AlertSeverity.SUCCESS,
                        category=AlertCategory.PORTFOLIO,
                        value=daily_pnl,
                        threshold=gain_celebration
                    )
            
            # Drawdown alerts
            current_drawdown = websocket_data.get('current_drawdown', 0)
            if current_drawdown > 0:
                warning_level = self.alert_thresholds['drawdown']['warning_level']
                critical_level = self.alert_thresholds['drawdown']['critical_level']
                emergency_level = self.alert_thresholds['drawdown']['emergency_level']
                
                if current_drawdown >= emergency_level:
                    self.add_alert(
                        title="EMERGENCY: Extreme Drawdown",
                        message=f"Portfolio drawdown reached emergency level: {current_drawdown:.2%}",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.RISK,
                        value=current_drawdown,
                        threshold=emergency_level,
                        persistent=True,
                        flash_alert=True,
                        sound_alert=True
                    )
                elif current_drawdown >= critical_level:
                    self.add_alert(
                        title="Critical: High Drawdown",
                        message=f"Portfolio drawdown is critically high: {current_drawdown:.2%}",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.RISK,
                        value=current_drawdown,
                        threshold=critical_level,
                        persistent=True
                    )
                elif current_drawdown >= warning_level:
                    self.add_alert(
                        title="Warning: Drawdown Alert",
                        message=f"Portfolio drawdown above warning level: {current_drawdown:.2%}",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.RISK,
                        value=current_drawdown,
                        threshold=warning_level
                    )
            
            # Market movement alerts
            btc_change = websocket_data.get('btc_24h_change', 0)
            if abs(btc_change) > 0:
                significant_move = self.alert_thresholds['price_movement']['significant_move']
                major_move = self.alert_thresholds['price_movement']['major_move']
                extreme_move = self.alert_thresholds['price_movement']['extreme_move']
                
                if abs(btc_change) >= extreme_move:
                    self.add_alert(
                        title=f"Extreme Market Movement: BTC",
                        message=f"Bitcoin moved {btc_change:+.2%} in 24h - extreme volatility detected",
                        severity=AlertSeverity.DANGER,
                        category=AlertCategory.MARKET,
                        symbol="BTCUSDT",
                        value=btc_change,
                        threshold=extreme_move
                    )
                elif abs(btc_change) >= major_move:
                    self.add_alert(
                        title=f"Major Market Movement: BTC",
                        message=f"Bitcoin moved {btc_change:+.2%} in 24h - significant market activity",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.MARKET,
                        symbol="BTCUSDT",
                        value=btc_change,
                        threshold=major_move
                    )
                elif abs(btc_change) >= significant_move:
                    self.add_alert(
                        title=f"Market Movement: BTC",
                        message=f"Bitcoin moved {btc_change:+.2%} in 24h",
                        severity=AlertSeverity.INFO,
                        category=AlertCategory.MARKET,
                        symbol="BTCUSDT",
                        value=btc_change,
                        threshold=significant_move
                    )
            
            # Trading signal alerts
            signal_strength = websocket_data.get('signal_strength', 0)
            if signal_strength > 0:
                high_confidence = self.alert_thresholds['trading_signals']['high_confidence']
                very_high_confidence = self.alert_thresholds['trading_signals']['very_high_confidence']
                
                if signal_strength >= very_high_confidence:
                    self.add_alert(
                        title="Very High Confidence Signal",
                        message=f"AI generated signal with {signal_strength:.1%} confidence",
                        severity=AlertSeverity.SUCCESS,
                        category=AlertCategory.TRADING,
                        value=signal_strength,
                        threshold=very_high_confidence
                    )
                elif signal_strength >= high_confidence:
                    self.add_alert(
                        title="High Confidence Signal",
                        message=f"AI generated signal with {signal_strength:.1%} confidence",
                        severity=AlertSeverity.INFO,
                        category=AlertCategory.TRADING,
                        value=signal_strength,
                        threshold=high_confidence
                    )
            
            # System performance alerts
            cpu_usage = websocket_data.get('cpu_usage', 0)
            memory_usage = websocket_data.get('memory_usage', 0)
            
            if cpu_usage > 0:
                cpu_critical = self.alert_thresholds['system_performance']['cpu_critical']
                cpu_warning = self.alert_thresholds['system_performance']['cpu_warning']
                
                if cpu_usage >= cpu_critical:
                    self.add_alert(
                        title="Critical: High CPU Usage",
                        message=f"System CPU usage is critically high: {cpu_usage:.1f}%",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.SYSTEM,
                        value=cpu_usage,
                        threshold=cpu_critical
                    )
                elif cpu_usage >= cpu_warning:
                    self.add_alert(
                        title="Warning: High CPU Usage",
                        message=f"System CPU usage is high: {cpu_usage:.1f}%",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.SYSTEM,
                        value=cpu_usage,
                        threshold=cpu_warning
                    )
            
            if memory_usage > 0:
                memory_critical = self.alert_thresholds['system_performance']['memory_critical']
                memory_warning = self.alert_thresholds['system_performance']['memory_warning']
                
                if memory_usage >= memory_critical:
                    self.add_alert(
                        title="Critical: High Memory Usage",
                        message=f"System memory usage is critically high: {memory_usage:.1f}%",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.SYSTEM,
                        value=memory_usage,
                        threshold=memory_critical
                    )
                elif memory_usage >= memory_warning:
                    self.add_alert(
                        title="Warning: High Memory Usage",
                        message=f"System memory usage is high: {memory_usage:.1f}%",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.SYSTEM,
                        value=memory_usage,
                        threshold=memory_warning
                    )
        
        except Exception as e:
            self.logger.error(f"❌ Error processing WebSocket alerts: {e}")
    
    def start_monitoring(self):
        """Start alert monitoring thread"""
        
        def monitoring_loop():
            """Main monitoring loop"""
            while self.monitoring_active:
                try:
                    # Perform periodic checks
                    self._check_system_health()
                    self._check_trading_conditions()
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in monitoring loop: {e}")
                    time.sleep(10)  # Wait longer on error
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("🔍 Alert monitoring started")
    
    def _check_system_health(self):
        """Check system health and generate alerts if needed"""
        # This would integrate with actual system monitoring
        # For now, it's a placeholder for system health checks
        pass
    
    def _check_trading_conditions(self):
        """Check trading conditions and generate alerts if needed"""
        # This would integrate with actual trading system
        # For now, it's a placeholder for trading condition checks
        pass
    
    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("🛑 Alert monitoring stopped")

def create_alerts_dashboard():
    """Create dashboard with visual alerts system"""
    
    # Initialize Dash app
    app = dash.Dash(__name__, external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ])
    
    # Initialize alerts system
    alerts_system = VisualAlertsSystem(app)
    
    # Create layout
    app.layout = dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("🚨 Visual Alerts & Notifications System", className="text-center mb-4"),
                html.P("Real-time visual alerts for critical trading events", className="text-center text-muted")
            ])
        ]),
        
        # Control panel
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("📋 Alert History", id="show-history-btn", color="info"),
                    dbc.Button("⚙️ Settings", id="show-settings-btn", color="secondary"),
                    dbc.Button("🧪 Test Alerts", id="test-alerts-btn", color="warning"),
                    dbc.Button("🗑️ Clear All", id="clear-all-btn", color="danger")
                ], className="mb-4")
            ])
        ]),
        
        # Demo metrics (simulating real trading data)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Simulated Trading Metrics"),
                    dbc.CardBody([
                        html.Div(id="demo-metrics")
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Alerts layout
        alerts_system.create_alerts_layout(),
        
        # Demo data interval
        dcc.Interval(
            id="demo-data-interval",
            interval=3000,  # Update every 3 seconds
            n_intervals=0
        )
        
    ], fluid=True)
    
    # Setup callbacks
    alerts_system.setup_alert_callbacks()
    
    # Demo callbacks
    @app.callback(
        [Output('demo-metrics', 'children'),
         Output('websocket-data-store', 'data')],
        [Input('demo-data-interval', 'n_intervals')]
    )
    def update_demo_metrics(n_intervals):
        """Update demo metrics and simulate WebSocket data"""
        
        # Simulate realistic trading data
        import random
        
        # Generate simulated data
        portfolio_value = 50000 + random.uniform(-5000, 5000)
        daily_pnl = random.uniform(-0.15, 0.15)
        current_drawdown = max(0, random.uniform(-0.05, 0.25))
        btc_change = random.uniform(-0.20, 0.20)
        signal_strength = random.uniform(0.5, 0.95)
        cpu_usage = random.uniform(30, 100)
        memory_usage = random.uniform(40, 95)
        
        # Create demo metrics display
        metrics_display = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Portfolio Value"),
                        html.H4(f"${portfolio_value:,.2f}")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Daily P&L"),
                        html.H4(f"{daily_pnl:+.2%}", 
                               style={'color': 'green' if daily_pnl > 0 else 'red'})
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Current Drawdown"),
                        html.H4(f"{current_drawdown:.2%}",
                               style={'color': 'red' if current_drawdown > 0.1 else 'orange' if current_drawdown > 0.05 else 'green'})
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("BTC 24h Change"),
                        html.H4(f"{btc_change:+.2%}",
                               style={'color': 'green' if btc_change > 0 else 'red'})
                    ])
                ])
            ], width=3)
        ])
        
        # Simulate WebSocket data
        websocket_data = {
            'portfolio_value': portfolio_value,
            'daily_pnl_percent': daily_pnl,
            'current_drawdown': current_drawdown,
            'btc_24h_change': btc_change,
            'signal_strength': signal_strength,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'timestamp': datetime.now().isoformat()
        }
        
        return metrics_display, websocket_data
    
    # Test alerts callback
    @app.callback(
        Output('test-alerts-btn', 'n_clicks'),
        [Input('test-alerts-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def test_alerts(n_clicks):
        """Generate test alerts"""
        if n_clicks:
            # Generate various test alerts
            alerts_system.add_alert(
                title="Test Info Alert",
                message="This is a test information alert",
                severity=AlertSeverity.INFO,
                category=AlertCategory.SYSTEM
            )
            
            alerts_system.add_alert(
                title="Test Success Alert",
                message="This is a test success alert",
                severity=AlertSeverity.SUCCESS,
                category=AlertCategory.TRADING
            )
            
            alerts_system.add_alert(
                title="Test Warning Alert",
                message="This is a test warning alert",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PORTFOLIO
            )
            
            alerts_system.add_alert(
                title="Test Critical Alert",
                message="This is a test critical alert",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.RISK,
                persistent=True
            )
        
        return 0
    
    # Clear all alerts callback
    @app.callback(
        Output('clear-all-btn', 'n_clicks'),
        [Input('clear-all-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def clear_all_alerts(n_clicks):
        """Clear all alerts"""
        if n_clicks:
            alerts_system.clear_all_alerts()
        return 0
    
    # Modal callbacks
    @app.callback(
        Output('alert-history-modal', 'is_open'),
        [Input('show-history-btn', 'n_clicks'),
         Input('close-history-modal', 'n_clicks')],
        [State('alert-history-modal', 'is_open')]
    )
    def toggle_history_modal(show_clicks, close_clicks, is_open):
        """Toggle alert history modal"""
        if show_clicks or close_clicks:
            return not is_open
        return is_open
    
    @app.callback(
        Output('alert-settings-modal', 'is_open'),
        [Input('show-settings-btn', 'n_clicks'),
         Input('close-settings-modal', 'n_clicks')],
        [State('alert-settings-modal', 'is_open')]
    )
    def toggle_settings_modal(show_clicks, close_clicks, is_open):
        """Toggle alert settings modal"""
        if show_clicks or close_clicks:
            return not is_open
        return is_open
    
    return app, alerts_system

if __name__ == "__main__":
    # Create and run the alerts dashboard
    app, alerts_system = create_alerts_dashboard()
    
    # Start monitoring
    alerts_system.start_monitoring()
    
    print("🚨 VISUAL ALERTS & NOTIFICATIONS SYSTEM")
    print("=" * 50)
    print("🎯 Features:")
    print("   • Real-time visual alerts for critical events")
    print("   • Multi-level alert severity (Info, Success, Warning, Danger, Critical)")
    print("   • Smart alert filtering and auto-dismissal")
    print("   • Configurable thresholds and notifications")
    print("   • Alert history and management")
    print("   • WebSocket integration for real-time data")
    print("🌐 Dashboard available at: http://localhost:8050")
    
    try:
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    finally:
        alerts_system.stop_monitoring() 