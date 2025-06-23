#!/usr/bin/env python3
"""
🔗 WebSocket Dash Integration
Integration helper for Dash applications to replace dcc.Interval with WebSocket-based real-time streaming for critical metrics.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, clientside_callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import numpy as np

from websocket_streaming_system import WebSocketDashboardClient

class DashWebSocketIntegration:
    """Integration helper for Dash applications with WebSocket streaming"""
    
    def __init__(self, app: dash.Dash, server_url: str = "ws://localhost:8765"):
        self.app = app
        self.server_url = server_url
        self.client = None
        self.data_store = {}
        self.logger = logging.getLogger('DashWebSocketIntegration')
        
        # WebSocket connection status
        self.connected = False
        self.connection_thread = None
        
        # Data update tracking
        self.last_updates = {}
        self.update_counters = {}
        
        self.logger.info("🔗 Dash WebSocket Integration initialized")
    
    def setup_websocket_components(self):
        """Add WebSocket components to the app layout"""
        
        # Add WebSocket status indicator and data stores to layout
        websocket_components = html.Div([
            # WebSocket status indicator
            html.Div([
                html.Span("🔴", id="websocket-status-icon"),
                html.Span("Disconnected", id="websocket-status-text", className="ms-2")
            ], id="websocket-status", className="websocket-status"),
            
            # Data stores for WebSocket data
            dcc.Store(id="websocket-data-store", data={}),
            dcc.Store(id="websocket-metrics-store", data={}),
            dcc.Store(id="websocket-config-store", data={
                'connected': False,
                'subscribed_metrics': [],
                'update_frequency': 1.0
            }),
            
            # Hidden div to trigger updates
            html.Div(id="websocket-trigger", style={'display': 'none'}),
            
            # Client-side callback trigger
            dcc.Interval(
                id="websocket-heartbeat",
                interval=100,  # 100ms heartbeat for WebSocket updates
                n_intervals=0
            )
        ], style={'display': 'none'})
        
        return websocket_components
    
    def setup_websocket_callbacks(self):
        """Setup WebSocket-based callbacks to replace dcc.Interval"""
        
        # WebSocket connection status callback
        @self.app.callback(
            [Output("websocket-status-icon", "children"),
             Output("websocket-status-text", "children"),
             Output("websocket-config-store", "data")],
            [Input("websocket-heartbeat", "n_intervals")],
            [State("websocket-config-store", "data")]
        )
        def update_websocket_status(n_intervals, config):
            """Update WebSocket connection status"""
            
            # Check connection status
            if self.client and self.client.connected:
                if not config.get('connected', False):
                    # Just connected
                    self.logger.info("✅ WebSocket connected")
                
                return "🟢", "Connected", {
                    **config,
                    'connected': True,
                    'last_heartbeat': datetime.now().isoformat()
                }
            else:
                if config.get('connected', False):
                    # Just disconnected
                    self.logger.warning("🔴 WebSocket disconnected")
                
                return "🔴", "Disconnected", {
                    **config,
                    'connected': False
                }
        
        # Main data update callback
        @self.app.callback(
            [Output("websocket-data-store", "data"),
             Output("websocket-metrics-store", "data")],
            [Input("websocket-heartbeat", "n_intervals")],
            [State("websocket-data-store", "data"),
             State("websocket-metrics-store", "data")]
        )
        def update_websocket_data(n_intervals, current_data, current_metrics):
            """Update data from WebSocket"""
            
            if not self.client or not self.client.connected:
                return current_data, current_metrics
            
            # Get latest data from WebSocket client
            updated_data = {}
            updated_metrics = {}
            
            for metric_id, data in self.client.latest_data.items():
                updated_data[metric_id] = data['value']
                updated_metrics[metric_id] = {
                    'timestamp': data['timestamp'],
                    'priority': data['priority'],
                    'category': data['category']
                }
                
                # Track updates
                self.update_counters[metric_id] = self.update_counters.get(metric_id, 0) + 1
                self.last_updates[metric_id] = datetime.now()
            
            return updated_data, updated_metrics
        
        # Setup metric-specific callbacks
        self._setup_metric_callbacks()
    
    def _setup_metric_callbacks(self):
        """Setup callbacks for specific metrics"""
        
        # Price update callbacks
        @self.app.callback(
            [Output("btc-price-display", "children"),
             Output("eth-price-display", "children")],
            [Input("websocket-data-store", "data")]
        )
        def update_price_displays(data):
            """Update price displays"""
            btc_price = data.get('btc_price', 0)
            eth_price = data.get('eth_price', 0)
            
            btc_display = f"${btc_price:,.2f}" if btc_price else "Loading..."
            eth_display = f"${eth_price:,.2f}" if eth_price else "Loading..."
            
            return btc_display, eth_display
        
        # Portfolio update callbacks
        @self.app.callback(
            [Output("portfolio-value-display", "children"),
             Output("daily-pnl-display", "children"),
             Output("daily-pnl-display", "className")],
            [Input("websocket-data-store", "data")]
        )
        def update_portfolio_displays(data):
            """Update portfolio displays"""
            portfolio_value = data.get('portfolio_value', 0)
            daily_pnl = data.get('daily_pnl', 0)
            
            portfolio_display = f"${portfolio_value:,.2f}" if portfolio_value else "Loading..."
            pnl_display = f"${daily_pnl:+,.2f}" if daily_pnl else "Loading..."
            pnl_class = "text-success" if daily_pnl >= 0 else "text-danger"
            
            return portfolio_display, pnl_display, pnl_class
        
        # Trading signals callback
        @self.app.callback(
            Output("active-signals-display", "children"),
            [Input("websocket-data-store", "data")]
        )
        def update_signals_display(data):
            """Update trading signals display"""
            active_signals = data.get('active_signals', 0)
            signal_strength = data.get('signal_strength', 0)
            
            return html.Div([
                html.H4(f"{active_signals}", className="mb-0"),
                html.Small(f"Avg Strength: {signal_strength:.1%}", className="text-muted")
            ])
        
        # Risk metrics callback
        @self.app.callback(
            [Output("portfolio-risk-display", "children"),
             Output("var-95-display", "children"),
             Output("drawdown-display", "children")],
            [Input("websocket-data-store", "data")]
        )
        def update_risk_displays(data):
            """Update risk metric displays"""
            portfolio_risk = data.get('portfolio_risk', 0)
            var_95 = data.get('var_95', 0)
            drawdown = data.get('drawdown', 0)
            
            risk_display = f"{portfolio_risk:.1%}" if portfolio_risk else "Loading..."
            var_display = f"${var_95:,.0f}" if var_95 else "Loading..."
            drawdown_display = f"{drawdown:.1%}" if drawdown else "Loading..."
            
            return risk_display, var_display, drawdown_display
    
    def start_websocket_connection(self):
        """Start WebSocket connection in background thread"""
        
        def run_websocket():
            """Run WebSocket client in asyncio loop"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._websocket_client_loop())
            except Exception as e:
                self.logger.error(f"❌ WebSocket client error: {e}")
            finally:
                loop.close()
        
        self.connection_thread = threading.Thread(target=run_websocket, daemon=True)
        self.connection_thread.start()
        self.logger.info("🚀 WebSocket connection thread started")
    
    async def _websocket_client_loop(self):
        """WebSocket client main loop"""
        
        while True:
            try:
                # Create and connect client
                self.client = WebSocketDashboardClient(self.server_url)
                await self.client.connect()
                
                # Subscribe to critical metrics
                critical_metrics = [
                    'btc_price', 'eth_price', 'portfolio_value', 'daily_pnl',
                    'active_signals', 'signal_strength', 'portfolio_risk',
                    'var_95', 'drawdown', 'system_status'
                ]
                
                await self.client.subscribe(critical_metrics, frequency=0.5)
                
                # Keep connection alive
                while self.client.connected:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"❌ WebSocket connection error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
    
    def create_websocket_dashboard_layout(self):
        """Create enhanced dashboard layout with WebSocket integration"""
        
        layout = dbc.Container([
            # Header with WebSocket status
            dbc.Row([
                dbc.Col([
                    html.H1("🚀 Real-Time Trading Dashboard", className="text-center mb-4"),
                    html.Div([
                        html.Span("WebSocket Status: "),
                        self.setup_websocket_components()
                    ], className="text-center mb-4")
                ])
            ]),
            
            # Real-time metrics cards
            dbc.Row([
                # Price Cards
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("₿ Bitcoin", className="card-title"),
                            html.H3(id="btc-price-display", className="text-warning"),
                            html.Small("Real-time price", className="text-muted")
                        ])
                    ], className="mb-3")
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("⟠ Ethereum", className="card-title"),
                            html.H3(id="eth-price-display", className="text-info"),
                            html.Small("Real-time price", className="text-muted")
                        ])
                    ], className="mb-3")
                ], width=3),
                
                # Portfolio Cards
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("💼 Portfolio", className="card-title"),
                            html.H3(id="portfolio-value-display", className="text-success"),
                            html.Small("Total value", className="text-muted")
                        ])
                    ], className="mb-3")
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📈 Daily P&L", className="card-title"),
                            html.H3(id="daily-pnl-display"),
                            html.Small("Today's performance", className="text-muted")
                        ])
                    ], className="mb-3")
                ], width=3)
            ]),
            
            # Trading signals and risk metrics
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🎯 Active Signals", className="card-title"),
                            html.Div(id="active-signals-display")
                        ])
                    ])
                ], width=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("⚠️ Portfolio Risk", className="card-title"),
                            html.H3(id="portfolio-risk-display", className="text-warning"),
                            html.Small("Risk level", className="text-muted")
                        ])
                    ])
                ], width=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🛡️ Value at Risk", className="card-title"),
                            html.H3(id="var-95-display", className="text-danger"),
                            html.Small("95% confidence", className="text-muted")
                        ])
                    ])
                ], width=4)
            ], className="mt-4"),
            
            # Real-time charts
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 Real-Time Price Chart", className="card-title"),
                            dcc.Graph(id="realtime-price-chart")
                        ])
                    ])
                ], width=8),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📈 Portfolio Performance", className="card-title"),
                            dcc.Graph(id="portfolio-performance-chart")
                        ])
                    ])
                ], width=4)
            ], className="mt-4"),
            
            # Performance metrics
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 WebSocket Performance", className="card-title"),
                            html.Div(id="websocket-performance-display")
                        ])
                    ])
                ])
            ], className="mt-4")
            
        ], fluid=True)
        
        return layout
    
    def setup_chart_callbacks(self):
        """Setup callbacks for real-time charts"""
        
        @self.app.callback(
            Output("realtime-price-chart", "figure"),
            [Input("websocket-data-store", "data"),
             Input("websocket-metrics-store", "data")]
        )
        def update_price_chart(data, metrics):
            """Update real-time price chart"""
            
            fig = go.Figure()
            
            # Add BTC price line
            if 'btc_price' in data:
                fig.add_trace(go.Scatter(
                    x=[datetime.now()],
                    y=[data['btc_price']],
                    mode='lines+markers',
                    name='BTC/USD',
                    line=dict(color='orange', width=2)
                ))
            
            # Add ETH price line
            if 'eth_price' in data:
                fig.add_trace(go.Scatter(
                    x=[datetime.now()],
                    y=[data['eth_price']],
                    mode='lines+markers',
                    name='ETH/USD',
                    line=dict(color='blue', width=2),
                    yaxis='y2'
                ))
            
            fig.update_layout(
                title="Real-Time Cryptocurrency Prices",
                xaxis_title="Time",
                yaxis_title="BTC Price (USD)",
                yaxis2=dict(
                    title="ETH Price (USD)",
                    overlaying='y',
                    side='right'
                ),
                height=400,
                showlegend=True
            )
            
            return fig
        
        @self.app.callback(
            Output("portfolio-performance-chart", "figure"),
            [Input("websocket-data-store", "data")]
        )
        def update_portfolio_chart(data):
            """Update portfolio performance chart"""
            
            portfolio_value = data.get('portfolio_value', 100000)
            daily_pnl = data.get('daily_pnl', 0)
            
            # Create simple performance indicator
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=portfolio_value,
                delta={'reference': portfolio_value - daily_pnl},
                gauge={
                    'axis': {'range': [None, portfolio_value * 1.2]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, portfolio_value * 0.8], 'color': "lightgray"},
                        {'range': [portfolio_value * 0.8, portfolio_value * 1.1], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': portfolio_value * 1.1
                    }
                },
                title={'text': "Portfolio Value"}
            ))
            
            fig.update_layout(height=300)
            return fig
        
        @self.app.callback(
            Output("websocket-performance-display", "children"),
            [Input("websocket-metrics-store", "data")]
        )
        def update_performance_display(metrics):
            """Update WebSocket performance display"""
            
            if not metrics:
                return "No performance data available"
            
            total_metrics = len(metrics)
            recent_updates = sum(1 for metric_id in metrics.keys() 
                               if metric_id in self.last_updates and 
                               (datetime.now() - self.last_updates[metric_id]).seconds < 5)
            
            return html.Div([
                html.P(f"📊 Total Metrics: {total_metrics}"),
                html.P(f"🔄 Recent Updates: {recent_updates}"),
                html.P(f"⚡ Update Rate: {recent_updates/5:.1f} updates/sec"),
                html.P(f"🔗 Connection: {'Active' if self.client and self.client.connected else 'Inactive'}")
            ])

def create_websocket_enhanced_app():
    """Create a Dash app with WebSocket integration"""
    
    # Initialize Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Initialize WebSocket integration
    ws_integration = DashWebSocketIntegration(app)
    
    # Set up layout
    app.layout = ws_integration.create_websocket_dashboard_layout()
    
    # Setup callbacks
    ws_integration.setup_websocket_callbacks()
    ws_integration.setup_chart_callbacks()
    
    # Start WebSocket connection
    ws_integration.start_websocket_connection()
    
    return app, ws_integration

if __name__ == "__main__":
    # Create and run the enhanced dashboard
    app, ws_integration = create_websocket_enhanced_app()
    
    print("🚀 Starting WebSocket-Enhanced Trading Dashboard")
    print("📊 Real-time streaming enabled")
    print("🔗 WebSocket server should be running on localhost:8765")
    print("🌐 Dashboard will be available at http://localhost:8050")
    
    app.run_server(debug=True, host='0.0.0.0', port=8050) 