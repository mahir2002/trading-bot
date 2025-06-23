#!/usr/bin/env python3
"""
🚨 Quick Visual Alerts Integration Example
Simple example showing how to integrate visual alerts with existing dashboard
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime
import random
import time

# Import the visual alerts system
try:
    from visual_alerts_system import VisualAlertsSystem, AlertSeverity, AlertCategory
    ALERTS_AVAILABLE = True
except ImportError:
    print("⚠️ Visual alerts system not available - running without alerts")
    ALERTS_AVAILABLE = False

class QuickAlertsDemo:
    """Quick demonstration of visual alerts integration"""
    
    def __init__(self):
        # Initialize Dash app
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        # Initialize alerts system if available
        if ALERTS_AVAILABLE:
            self.alerts_system = VisualAlertsSystem(self.app)
        else:
            self.alerts_system = None
        
        # Demo data
        self.portfolio_value = 50000
        self.daily_pnl = 0.025
        self.btc_price = 45000
        
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup dashboard layout with alerts"""
        
        layout_components = [
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("📊 Trading Dashboard with Visual Alerts", className="text-center mb-4"),
                    html.P("Demonstration of integrated visual alerts system", className="text-center text-muted")
                ])
            ]),
            
            # Metrics cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("💰 Portfolio Value"),
                            html.H2(id="portfolio-display", className="text-primary"),
                            html.P(id="portfolio-change", className="mb-0")
                        ])
                    ])
                ], width=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("📈 Daily P&L"),
                            html.H2(id="pnl-display"),
                            html.P("Performance today", className="mb-0")
                        ])
                    ])
                ], width=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("₿ Bitcoin Price"),
                            html.H2(id="btc-display", className="text-warning"),
                            html.P(id="btc-change", className="mb-0")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Control buttons
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("🚨 Test Critical Alert", id="test-critical-btn", color="danger"),
                        dbc.Button("⚠️ Test Warning", id="test-warning-btn", color="warning"),
                        dbc.Button("✅ Test Success", id="test-success-btn", color="success"),
                        dbc.Button("📊 Simulate Data", id="simulate-btn", color="info"),
                        dbc.Button("🗑️ Clear Alerts", id="clear-btn", color="secondary")
                    ], className="mb-3")
                ])
            ]),
            
            # Chart
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Portfolio Performance"),
                        dbc.CardBody([
                            dcc.Graph(id="portfolio-chart")
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Data stores and intervals
            dcc.Store(id="demo-data-store", data={}),
            dcc.Interval(id="update-interval", interval=3000, n_intervals=0)
        ]
        
        # Add alerts overlay if available
        if self.alerts_system:
            layout_components.append(self.alerts_system.create_alerts_layout())
        
        self.app.layout = dbc.Container(layout_components, fluid=True)
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        # Setup alerts callbacks if available
        if self.alerts_system:
            self.alerts_system.setup_alert_callbacks()
        
        # Main update callback
        @self.app.callback(
            [Output('portfolio-display', 'children'),
             Output('portfolio-change', 'children'),
             Output('pnl-display', 'children'),
             Output('pnl-display', 'className'),
             Output('btc-display', 'children'),
             Output('btc-change', 'children'),
             Output('portfolio-chart', 'figure'),
             Output('demo-data-store', 'data')],
            [Input('update-interval', 'n_intervals'),
             Input('simulate-btn', 'n_clicks')],
            [State('demo-data-store', 'data')]
        )
        def update_dashboard(n_intervals, simulate_clicks, stored_data):
            """Update dashboard with simulated data"""
            
            # Simulate market changes
            if simulate_clicks or n_intervals > 0:
                self.portfolio_value *= (1 + random.uniform(-0.02, 0.02))
                self.daily_pnl += random.uniform(-0.01, 0.01)
                self.btc_price *= (1 + random.uniform(-0.03, 0.03))
            
            # Check for alert conditions
            if self.alerts_system:
                self._check_alert_conditions()
            
            # Format displays
            portfolio_display = f"${self.portfolio_value:,.2f}"
            portfolio_change = f"{random.uniform(-0.05, 0.05):+.2%} today"
            
            pnl_display = f"{self.daily_pnl:+.2%}"
            pnl_class = "text-success" if self.daily_pnl > 0 else "text-danger"
            
            btc_display = f"${self.btc_price:,.0f}"
            btc_change = f"{random.uniform(-0.08, 0.08):+.2%} 24h"
            
            # Create chart
            chart_fig = self._create_portfolio_chart()
            
            # Store data
            demo_data = {
                'portfolio_value': self.portfolio_value,
                'daily_pnl': self.daily_pnl,
                'btc_price': self.btc_price,
                'timestamp': datetime.now().isoformat()
            }
            
            return (portfolio_display, portfolio_change, pnl_display, pnl_class,
                   btc_display, btc_change, chart_fig, demo_data)
        
        # Test alert callbacks
        if self.alerts_system:
            @self.app.callback(
                Output('test-critical-btn', 'n_clicks'),
                [Input('test-critical-btn', 'n_clicks')],
                prevent_initial_call=True
            )
            def test_critical_alert(n_clicks):
                if n_clicks:
                    self.alerts_system.add_alert(
                        title="🔥 CRITICAL: Emergency Drawdown",
                        message="Portfolio drawdown exceeded 30% - Immediate action required!",
                        severity=AlertSeverity.CRITICAL,
                        category=AlertCategory.RISK,
                        value=0.32,
                        threshold=0.30,
                        persistent=True,
                        flash_alert=True,
                        sound_alert=True
                    )
                return 0
            
            @self.app.callback(
                Output('test-warning-btn', 'n_clicks'),
                [Input('test-warning-btn', 'n_clicks')],
                prevent_initial_call=True
            )
            def test_warning_alert(n_clicks):
                if n_clicks:
                    self.alerts_system.add_alert(
                        title="⚠️ WARNING: High Daily Loss",
                        message=f"Daily P&L is below warning threshold: {self.daily_pnl:.2%}",
                        severity=AlertSeverity.WARNING,
                        category=AlertCategory.PORTFOLIO,
                        value=self.daily_pnl,
                        threshold=-0.05
                    )
                return 0
            
            @self.app.callback(
                Output('test-success-btn', 'n_clicks'),
                [Input('test-success-btn', 'n_clicks')],
                prevent_initial_call=True
            )
            def test_success_alert(n_clicks):
                if n_clicks:
                    self.alerts_system.add_alert(
                        title="✅ SUCCESS: Excellent Performance",
                        message="Daily P&L exceeded target - Great trading day!",
                        severity=AlertSeverity.SUCCESS,
                        category=AlertCategory.PORTFOLIO,
                        value=0.087,
                        threshold=0.05
                    )
                return 0
            
            @self.app.callback(
                Output('clear-btn', 'n_clicks'),
                [Input('clear-btn', 'n_clicks')],
                prevent_initial_call=True
            )
            def clear_alerts(n_clicks):
                if n_clicks:
                    self.alerts_system.clear_all_alerts()
                return 0
    
    def _check_alert_conditions(self):
        """Check current data for alert conditions"""
        
        if not self.alerts_system:
            return
        
        # Portfolio balance alerts
        if self.portfolio_value < 1000:
            self.alerts_system.add_alert(
                title="🚨 CRITICAL: Low Portfolio Balance",
                message=f"Portfolio balance critically low: ${self.portfolio_value:,.2f}",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.PORTFOLIO,
                value=self.portfolio_value,
                threshold=1000
            )
        elif self.portfolio_value < 5000:
            self.alerts_system.add_alert(
                title="⚠️ WARNING: Low Portfolio Balance",
                message=f"Portfolio balance below warning threshold: ${self.portfolio_value:,.2f}",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PORTFOLIO,
                value=self.portfolio_value,
                threshold=5000
            )
        
        # Daily P&L alerts
        if self.daily_pnl < -0.10:
            self.alerts_system.add_alert(
                title="🔥 CRITICAL: High Daily Loss",
                message=f"Daily P&L critically low: {self.daily_pnl:.2%}",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.PORTFOLIO,
                value=self.daily_pnl,
                threshold=-0.10
            )
        elif self.daily_pnl < -0.05:
            self.alerts_system.add_alert(
                title="⚠️ WARNING: Daily Loss",
                message=f"Daily P&L below warning threshold: {self.daily_pnl:.2%}",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PORTFOLIO,
                value=self.daily_pnl,
                threshold=-0.05
            )
        elif self.daily_pnl > 0.05:
            self.alerts_system.add_alert(
                title="✅ SUCCESS: Excellent Performance",
                message=f"Daily P&L exceeds target: {self.daily_pnl:.2%}",
                severity=AlertSeverity.SUCCESS,
                category=AlertCategory.PORTFOLIO,
                value=self.daily_pnl,
                threshold=0.05
            )
        
        # Bitcoin price movement alerts
        btc_change_24h = random.uniform(-0.15, 0.15)  # Simulate 24h change
        if abs(btc_change_24h) > 0.10:
            severity = AlertSeverity.DANGER if abs(btc_change_24h) > 0.15 else AlertSeverity.WARNING
            self.alerts_system.add_alert(
                title=f"📊 MARKET: Bitcoin Movement",
                message=f"BTC moved {btc_change_24h:+.2%} in 24h",
                severity=severity,
                category=AlertCategory.MARKET,
                symbol="BTCUSDT",
                value=btc_change_24h
            )
    
    def _create_portfolio_chart(self):
        """Create portfolio performance chart"""
        
        # Generate sample data
        import numpy as np
        dates = [datetime.now().replace(hour=h) for h in range(24)]
        values = [self.portfolio_value * (1 + np.random.normal(0, 0.01)) for _ in range(24)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Portfolio Value (24h)",
            xaxis_title="Time",
            yaxis_title="Value ($)",
            template="plotly_white",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def run(self, debug=True, port=8050):
        """Run the dashboard"""
        
        # Start alerts monitoring if available
        if self.alerts_system:
            self.alerts_system.start_monitoring()
        
        print("🚨 QUICK VISUAL ALERTS INTEGRATION DEMO")
        print("=" * 50)
        
        if ALERTS_AVAILABLE:
            print("✅ Visual Alerts System: ENABLED")
            print("🎯 Features Available:")
            print("   • Real-time visual alerts")
            print("   • Multi-level severity system")
            print("   • Smart alert filtering")
            print("   • Auto-dismissal")
            print("   • Test alert buttons")
        else:
            print("⚠️ Visual Alerts System: DISABLED")
            print("   Install visual_alerts_system.py to enable alerts")
        
        print(f"🌐 Dashboard: http://localhost:{port}")
        print("🎮 Controls:")
        print("   • Click 'Test' buttons to generate sample alerts")
        print("   • Click 'Simulate Data' to trigger realistic alerts")
        print("   • Watch for automatic alerts based on thresholds")
        
        try:
            self.app.run_server(debug=debug, host='0.0.0.0', port=port)
        finally:
            if self.alerts_system:
                self.alerts_system.stop_monitoring()

def main():
    """Run the quick alerts integration demo"""
    
    # Create and run demo
    demo = QuickAlertsDemo()
    demo.run()

if __name__ == "__main__":
    main() 