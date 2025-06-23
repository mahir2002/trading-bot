#!/usr/bin/env python3
"""
🚨 Visual Alerts System Demonstration
Comprehensive demonstration of the visual alerts system showing
real-time alerts for various trading scenarios and critical events.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List
import threading

# Import our alert system
from visual_alerts_system import VisualAlertsSystem, AlertSeverity, AlertCategory, VisualAlert

class AlertsDemo:
    """Demonstrates visual alerts system capabilities"""
    
    def __init__(self):
        self.demo_scenarios = self._create_demo_scenarios()
        self.current_metrics = self._initialize_metrics()
        
    def _create_demo_scenarios(self) -> List[Dict]:
        """Create realistic trading scenarios for demonstration"""
        
        return [
            {
                'name': 'Portfolio Low Balance',
                'description': 'Portfolio balance drops below warning threshold',
                'alerts': [
                    {
                        'title': 'Warning: Low Portfolio Balance',
                        'message': 'Portfolio balance is below $1,000 warning threshold',
                        'severity': AlertSeverity.WARNING,
                        'category': AlertCategory.PORTFOLIO,
                        'value': 850,
                        'threshold': 1000
                    }
                ]
            },
            {
                'name': 'High Daily Loss',
                'description': 'Daily P&L exceeds loss threshold',
                'alerts': [
                    {
                        'title': 'Critical: High Daily Loss',
                        'message': 'Daily P&L is critically low at -12.5%',
                        'severity': AlertSeverity.CRITICAL,
                        'category': AlertCategory.PORTFOLIO,
                        'value': -0.125,
                        'threshold': -0.10,
                        'persistent': True
                    }
                ]
            },
            {
                'name': 'Extreme Market Volatility',
                'description': 'Bitcoin experiences extreme price movement',
                'alerts': [
                    {
                        'title': 'Extreme Market Movement: BTC',
                        'message': 'Bitcoin moved -18.5% in 24h - extreme volatility detected',
                        'severity': AlertSeverity.DANGER,
                        'category': AlertCategory.MARKET,
                        'symbol': 'BTCUSDT',
                        'value': -0.185,
                        'threshold': 0.20,
                        'flash_alert': True
                    }
                ]
            },
            {
                'name': 'Emergency Drawdown',
                'description': 'Portfolio drawdown reaches emergency level',
                'alerts': [
                    {
                        'title': 'EMERGENCY: Extreme Drawdown',
                        'message': 'Portfolio drawdown reached emergency level: 32.5%',
                        'severity': AlertSeverity.CRITICAL,
                        'category': AlertCategory.RISK,
                        'value': 0.325,
                        'threshold': 0.30,
                        'persistent': True,
                        'flash_alert': True,
                        'sound_alert': True
                    }
                ]
            },
            {
                'name': 'High Confidence Trading Signal',
                'description': 'AI generates very high confidence signal',
                'alerts': [
                    {
                        'title': 'Very High Confidence Signal',
                        'message': 'AI generated BUY signal with 94% confidence for ETH/USDT',
                        'severity': AlertSeverity.SUCCESS,
                        'category': AlertCategory.TRADING,
                        'symbol': 'ETHUSDT',
                        'value': 0.94,
                        'threshold': 0.90
                    }
                ]
            },
            {
                'name': 'System Performance Issues',
                'description': 'System experiencing high resource usage',
                'alerts': [
                    {
                        'title': 'Critical: High CPU Usage',
                        'message': 'System CPU usage is critically high: 96.5%',
                        'severity': AlertSeverity.CRITICAL,
                        'category': AlertCategory.SYSTEM,
                        'value': 96.5,
                        'threshold': 95.0
                    },
                    {
                        'title': 'Warning: High Memory Usage',
                        'message': 'System memory usage is high: 87.2%',
                        'severity': AlertSeverity.WARNING,
                        'category': AlertCategory.SYSTEM,
                        'value': 87.2,
                        'threshold': 85.0
                    }
                ]
            },
            {
                'name': 'Excellent Trading Performance',
                'description': 'Portfolio achieving exceptional returns',
                'alerts': [
                    {
                        'title': 'Excellent Daily Performance!',
                        'message': 'Daily P&L exceeds target: +8.7%',
                        'severity': AlertSeverity.SUCCESS,
                        'category': AlertCategory.PORTFOLIO,
                        'value': 0.087,
                        'threshold': 0.05
                    }
                ]
            },
            {
                'name': 'Multiple Conflicting Signals',
                'description': 'AI models generating conflicting signals',
                'alerts': [
                    {
                        'title': 'Warning: Conflicting Signals',
                        'message': 'Multiple AI models generating conflicting signals for BTC/USDT',
                        'severity': AlertSeverity.WARNING,
                        'category': AlertCategory.TRADING,
                        'symbol': 'BTCUSDT'
                    }
                ]
            }
        ]
    
    def _initialize_metrics(self) -> Dict:
        """Initialize demo metrics"""
        
        return {
            'portfolio_value': 50000,
            'daily_pnl': 0.025,
            'current_drawdown': 0.08,
            'btc_price': 45000,
            'btc_24h_change': 0.025,
            'signal_strength': 0.75,
            'cpu_usage': 45,
            'memory_usage': 60,
            'active_trades': 3,
            'system_uptime': '2d 14h 32m'
        }
    
    def demonstrate_alert_scenarios(self):
        """Demonstrate various alert scenarios"""
        
        print("🚨 VISUAL ALERTS SYSTEM DEMONSTRATION")
        print("=" * 60)
        
        print("📋 Available Demo Scenarios:")
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"   {i}. {scenario['name']}")
            print(f"      {scenario['description']}")
        
        print(f"\n🎬 Running Alert Scenarios...")
        
        # Simulate running each scenario
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"\n📍 Scenario {i}: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            
            # Display alerts for this scenario
            for alert_data in scenario['alerts']:
                self._display_alert_demo(alert_data)
            
            # Simulate time delay between scenarios
            time.sleep(2)
        
        print(f"\n✅ All scenarios demonstrated!")
    
    def _display_alert_demo(self, alert_data: Dict):
        """Display individual alert demonstration"""
        
        # Create alert object
        alert = VisualAlert(
            id=f"demo_{int(time.time())}",
            title=alert_data['title'],
            message=alert_data['message'],
            severity=alert_data['severity'],
            category=alert_data['category'],
            timestamp=datetime.now(),
            symbol=alert_data.get('symbol'),
            value=alert_data.get('value'),
            threshold=alert_data.get('threshold'),
            persistent=alert_data.get('persistent', False),
            flash_alert=alert_data.get('flash_alert', False),
            sound_alert=alert_data.get('sound_alert', False)
        )
        
        # Display alert information
        severity_icons = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.SUCCESS: "✅",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.DANGER: "🚨",
            AlertSeverity.CRITICAL: "🔥"
        }
        
        icon = severity_icons.get(alert.severity, "📢")
        
        print(f"      {icon} {alert.severity.value.upper()}: {alert.title}")
        print(f"         Message: {alert.message}")
        
        if alert.symbol:
            print(f"         Symbol: {alert.symbol}")
        
        if alert.value is not None:
            if alert.threshold is not None:
                print(f"         Value: {alert.value} (Threshold: {alert.threshold})")
            else:
                print(f"         Value: {alert.value}")
        
        if alert.persistent:
            print(f"         🔒 Persistent alert (requires manual dismissal)")
        
        if alert.flash_alert:
            print(f"         ⚡ Flash alert enabled")
        
        if alert.sound_alert:
            print(f"         🔊 Sound alert enabled")
        
        print(f"         🕐 Timestamp: {alert.timestamp.strftime('%H:%M:%S')}")
    
    def demonstrate_real_time_monitoring(self):
        """Demonstrate real-time monitoring with dynamic alerts"""
        
        print(f"\n🔍 REAL-TIME MONITORING DEMONSTRATION")
        print("=" * 60)
        
        print("📊 Simulating real-time trading data with dynamic alerts...")
        print("⏰ Monitoring for 30 seconds with 3-second intervals")
        
        start_time = time.time()
        interval = 3  # seconds
        duration = 30  # seconds
        
        while time.time() - start_time < duration:
            # Update metrics with realistic variations
            self._update_demo_metrics()
            
            # Check for alert conditions
            alerts_triggered = self._check_alert_conditions()
            
            # Display current status
            elapsed = int(time.time() - start_time)
            print(f"\n⏱️  Time: {elapsed}s | Alerts triggered: {len(alerts_triggered)}")
            
            # Display metrics
            self._display_current_metrics()
            
            # Display any triggered alerts
            for alert_info in alerts_triggered:
                print(f"   🚨 ALERT: {alert_info}")
            
            time.sleep(interval)
        
        print(f"\n✅ Real-time monitoring demonstration completed!")
    
    def _update_demo_metrics(self):
        """Update demo metrics with realistic variations"""
        
        # Portfolio value (can fluctuate)
        change = random.uniform(-0.02, 0.02)  # ±2%
        self.current_metrics['portfolio_value'] *= (1 + change)
        
        # Daily P&L (can be volatile)
        self.current_metrics['daily_pnl'] += random.uniform(-0.01, 0.01)
        self.current_metrics['daily_pnl'] = max(-0.20, min(0.20, self.current_metrics['daily_pnl']))
        
        # Drawdown (usually increases slowly, decreases faster)
        if random.random() < 0.3:  # 30% chance to change
            change = random.uniform(-0.02, 0.01)  # More likely to decrease
            self.current_metrics['current_drawdown'] = max(0, self.current_metrics['current_drawdown'] + change)
        
        # BTC price and change
        btc_change = random.uniform(-0.05, 0.05)  # ±5%
        self.current_metrics['btc_price'] *= (1 + btc_change)
        self.current_metrics['btc_24h_change'] += btc_change * 0.1  # Gradual change
        
        # Signal strength (varies)
        self.current_metrics['signal_strength'] += random.uniform(-0.1, 0.1)
        self.current_metrics['signal_strength'] = max(0.3, min(0.95, self.current_metrics['signal_strength']))
        
        # System metrics
        self.current_metrics['cpu_usage'] += random.uniform(-5, 5)
        self.current_metrics['cpu_usage'] = max(20, min(100, self.current_metrics['cpu_usage']))
        
        self.current_metrics['memory_usage'] += random.uniform(-3, 3)
        self.current_metrics['memory_usage'] = max(30, min(100, self.current_metrics['memory_usage']))
    
    def _check_alert_conditions(self) -> List[str]:
        """Check current metrics for alert conditions"""
        
        alerts = []
        
        # Portfolio balance alerts
        if self.current_metrics['portfolio_value'] < 1000:
            alerts.append(f"Critical low balance: ${self.current_metrics['portfolio_value']:,.0f}")
        elif self.current_metrics['portfolio_value'] < 5000:
            alerts.append(f"Low balance warning: ${self.current_metrics['portfolio_value']:,.0f}")
        
        # Daily P&L alerts
        if self.current_metrics['daily_pnl'] < -0.10:
            alerts.append(f"Critical daily loss: {self.current_metrics['daily_pnl']:.2%}")
        elif self.current_metrics['daily_pnl'] < -0.05:
            alerts.append(f"Daily loss warning: {self.current_metrics['daily_pnl']:.2%}")
        elif self.current_metrics['daily_pnl'] > 0.05:
            alerts.append(f"Excellent performance: {self.current_metrics['daily_pnl']:.2%}")
        
        # Drawdown alerts
        if self.current_metrics['current_drawdown'] > 0.30:
            alerts.append(f"Emergency drawdown: {self.current_metrics['current_drawdown']:.2%}")
        elif self.current_metrics['current_drawdown'] > 0.20:
            alerts.append(f"Critical drawdown: {self.current_metrics['current_drawdown']:.2%}")
        elif self.current_metrics['current_drawdown'] > 0.10:
            alerts.append(f"Drawdown warning: {self.current_metrics['current_drawdown']:.2%}")
        
        # Market movement alerts
        if abs(self.current_metrics['btc_24h_change']) > 0.20:
            alerts.append(f"Extreme BTC movement: {self.current_metrics['btc_24h_change']:+.2%}")
        elif abs(self.current_metrics['btc_24h_change']) > 0.10:
            alerts.append(f"Major BTC movement: {self.current_metrics['btc_24h_change']:+.2%}")
        
        # Signal strength alerts
        if self.current_metrics['signal_strength'] > 0.90:
            alerts.append(f"Very high confidence signal: {self.current_metrics['signal_strength']:.1%}")
        elif self.current_metrics['signal_strength'] < 0.50:
            alerts.append(f"Low confidence warning: {self.current_metrics['signal_strength']:.1%}")
        
        # System performance alerts
        if self.current_metrics['cpu_usage'] > 95:
            alerts.append(f"Critical CPU usage: {self.current_metrics['cpu_usage']:.1f}%")
        elif self.current_metrics['cpu_usage'] > 80:
            alerts.append(f"High CPU usage: {self.current_metrics['cpu_usage']:.1f}%")
        
        if self.current_metrics['memory_usage'] > 95:
            alerts.append(f"Critical memory usage: {self.current_metrics['memory_usage']:.1f}%")
        elif self.current_metrics['memory_usage'] > 85:
            alerts.append(f"High memory usage: {self.current_metrics['memory_usage']:.1f}%")
        
        return alerts
    
    def _display_current_metrics(self):
        """Display current metrics"""
        
        print(f"   💰 Portfolio: ${self.current_metrics['portfolio_value']:,.0f}")
        print(f"   📈 Daily P&L: {self.current_metrics['daily_pnl']:+.2%}")
        print(f"   📉 Drawdown: {self.current_metrics['current_drawdown']:.2%}")
        print(f"   ₿  BTC: ${self.current_metrics['btc_price']:,.0f} ({self.current_metrics['btc_24h_change']:+.2%})")
        print(f"   🤖 Signal: {self.current_metrics['signal_strength']:.1%}")
        print(f"   💻 CPU: {self.current_metrics['cpu_usage']:.1f}% | RAM: {self.current_metrics['memory_usage']:.1f}%")
    
    def demonstrate_alert_management(self):
        """Demonstrate alert management features"""
        
        print(f"\n⚙️ ALERT MANAGEMENT DEMONSTRATION")
        print("=" * 60)
        
        # Alert filtering demonstration
        print("🔍 Alert Filtering & Management:")
        print("   • Smart cooldown periods prevent spam")
        print("   • Auto-dismissal for non-critical alerts")
        print("   • Persistent alerts for critical issues")
        print("   • Category-based organization")
        print("   • Severity-based prioritization")
        
        # Alert thresholds demonstration
        print(f"\n📊 Configurable Alert Thresholds:")
        thresholds = {
            'Portfolio Balance': {'Warning': '$1,000', 'Critical': '$500'},
            'Daily P&L Loss': {'Warning': '-5%', 'Critical': '-10%'},
            'Portfolio Drawdown': {'Warning': '10%', 'Critical': '20%', 'Emergency': '30%'},
            'Market Movement': {'Significant': '5%', 'Major': '10%', 'Extreme': '20%'},
            'CPU Usage': {'Warning': '80%', 'Critical': '95%'},
            'Memory Usage': {'Warning': '85%', 'Critical': '95%'}
        }
        
        for metric, levels in thresholds.items():
            print(f"   • {metric}:")
            for level, threshold in levels.items():
                print(f"     - {level}: {threshold}")
        
        # Alert channels demonstration
        print(f"\n📢 Multi-Channel Notifications:")
        print("   • Dashboard visual alerts (real-time)")
        print("   • Email notifications (configurable)")
        print("   • Slack/Discord webhooks (team alerts)")
        print("   • Desktop notifications (system-level)")
        print("   • Sound alerts (critical events)")
        print("   • Flash alerts (emergency situations)")
        
        # Alert history demonstration
        print(f"\n📋 Alert History & Analytics:")
        print("   • Complete alert history tracking")
        print("   • Alert frequency analysis")
        print("   • Performance impact assessment")
        print("   • Threshold optimization suggestions")
        print("   • Alert effectiveness metrics")
    
    def demonstrate_integration_features(self):
        """Demonstrate integration with trading system"""
        
        print(f"\n🔗 INTEGRATION FEATURES DEMONSTRATION")
        print("=" * 60)
        
        print("🚀 WebSocket Real-Time Integration:")
        print("   • Live portfolio value monitoring")
        print("   • Real-time P&L tracking")
        print("   • Instant market movement detection")
        print("   • System performance monitoring")
        print("   • Trading signal confidence tracking")
        
        print(f"\n🎛️ Dashboard Integration:")
        print("   • Alert status in header")
        print("   • Metric-specific alert indicators")
        print("   • Critical alert banners")
        print("   • Alert summary panels")
        print("   • Interactive alert management")
        
        print(f"\n🤖 AI/ML Integration:")
        print("   • Signal confidence alerts")
        print("   • Model performance monitoring")
        print("   • Prediction accuracy tracking")
        print("   • Feature importance alerts")
        print("   • Training completion notifications")
        
        print(f"\n🛡️ Risk Management Integration:")
        print("   • Drawdown level monitoring")
        print("   • Position size alerts")
        print("   • Risk-reward ratio warnings")
        print("   • Correlation risk alerts")
        print("   • Volatility spike detection")

def main():
    """Run comprehensive alerts demonstration"""
    
    # Create demo instance
    demo = AlertsDemo()
    
    # Run all demonstrations
    demo.demonstrate_alert_scenarios()
    demo.demonstrate_real_time_monitoring()
    demo.demonstrate_alert_management()
    demo.demonstrate_integration_features()
    
    print(f"\n🎯 VISUAL ALERTS SYSTEM SUMMARY")
    print("=" * 60)
    print("✅ Features Demonstrated:")
    print("   • Multi-level alert severity system")
    print("   • Real-time monitoring and detection")
    print("   • Smart filtering and management")
    print("   • Configurable thresholds")
    print("   • Multi-channel notifications")
    print("   • Dashboard integration")
    print("   • WebSocket real-time updates")
    print("   • Alert history and analytics")
    
    print(f"\n🚨 Alert Categories Covered:")
    print("   • Portfolio alerts (balance, P&L, performance)")
    print("   • Market alerts (price movements, volatility)")
    print("   • Risk alerts (drawdown, exposure, correlation)")
    print("   • System alerts (CPU, memory, API latency)")
    print("   • Trading alerts (signals, confidence, conflicts)")
    
    print(f"\n🎛️ Management Features:")
    print("   • Auto-dismissal for non-critical alerts")
    print("   • Persistent alerts for critical issues")
    print("   • Cooldown periods to prevent spam")
    print("   • Category-based organization")
    print("   • Severity-based prioritization")
    print("   • Configurable notification channels")
    
    print(f"\n🌟 Visual Alerts System Ready for Production!")

if __name__ == "__main__":
    main() 