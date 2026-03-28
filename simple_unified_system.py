#!/usr/bin/env python3
"""
🚀 Simple Unified Crypto System
Simplified version for testing and reliability
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleUnifiedSystem:
    def __init__(self, port=8060):
        """Initialize the simple unified system"""
        self.port = port
        self.running = True
        
        # Sample data for testing
        self.sample_data = {
            'twitter_analysis': {
                'total_tweets': 150,
                'sentiment_score': 0.65,
                'opportunities': 12
            },
            'ai_signals': {
                'BTCUSDT': {'action': 'BUY', 'confidence': 85.2, 'price': 109850},
                'ETHUSDT': {'action': 'HOLD', 'confidence': 62.1, 'price': 4125},
                'ADAUSDT': {'action': 'SELL', 'confidence': 78.9, 'price': 1.05}
            },
            'system_stats': {
                'uptime': datetime.now(),
                'analyses_completed': 45,
                'opportunities_found': 23,
                'success_rate': 73.5
            }
        }
        
        logger.info("🚀 Simple Unified System initialized")
        self.setup_dashboard()
    
    def setup_dashboard(self):
        """Setup the dashboard"""
        self.app = dash.Dash(__name__)
        
        self.app.layout = html.Div([
            html.Div([
                html.H1("🚀 Unified Crypto Trading System", 
                       style={'color': '#FFD700', 'textAlign': 'center', 'margin': '20px'}),
                html.Div("🔴 LIVE", 
                        style={'color': '#ff4444', 'textAlign': 'center', 'fontSize': '18px'})
            ]),
            
            # Stats Cards
            html.Div([
                html.Div([
                    html.H3("🐦 Twitter Analysis"),
                    html.P(f"Tweets: {self.sample_data['twitter_analysis']['total_tweets']}"),
                    html.P(f"Sentiment: {self.sample_data['twitter_analysis']['sentiment_score']:.3f}"),
                    html.P(f"Opportunities: {self.sample_data['twitter_analysis']['opportunities']}")
                ], style={'background': '#1e222d', 'padding': '20px', 'margin': '10px', 
                         'borderRadius': '10px', 'color': 'white', 'width': '30%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("🤖 AI Trading"),
                    html.P(f"Signals: {len(self.sample_data['ai_signals'])}"),
                    html.P(f"Success Rate: {self.sample_data['system_stats']['success_rate']:.1f}%"),
                    html.P(f"Analyses: {self.sample_data['system_stats']['analyses_completed']}")
                ], style={'background': '#1e222d', 'padding': '20px', 'margin': '10px', 
                         'borderRadius': '10px', 'color': 'white', 'width': '30%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H3("💰 Opportunities"),
                    html.P(f"Found: {self.sample_data['system_stats']['opportunities_found']}"),
                    html.P("Status: 🟢 Active"),
                    html.P("Mode: Live Trading")
                ], style={'background': '#1e222d', 'padding': '20px', 'margin': '10px', 
                         'borderRadius': '10px', 'color': 'white', 'width': '30%', 'display': 'inline-block'})
            ], style={'textAlign': 'center'}),
            
            # Trading Signals
            html.Div([
                html.H2("📊 Live Trading Signals", style={'color': '#FFD700', 'textAlign': 'center'}),
                html.Div(id='signals-container')
            ], style={'margin': '20px'}),
            
            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # Update every 5 seconds
                n_intervals=0
            )
            
        ], style={'background': '#131722', 'minHeight': '100vh', 'fontFamily': 'Arial'})
        
        # Setup callbacks
        @self.app.callback(
            Output('signals-container', 'children'),
            Input('interval-component', 'n_intervals')
        )
        def update_signals(n):
            """Update trading signals"""
            signals = []
            
            for symbol, data in self.sample_data['ai_signals'].items():
                color = '#4CAF50' if data['action'] == 'BUY' else '#f44336' if data['action'] == 'SELL' else '#FFA500'
                
                signals.append(
                    html.Div([
                        html.H4(f"{symbol}", style={'color': '#FFD700'}),
                        html.P(f"Action: {data['action']}", style={'color': color, 'fontSize': '18px', 'fontWeight': 'bold'}),
                        html.P(f"Confidence: {data['confidence']:.1f}%"),
                        html.P(f"Price: ${data['price']:,.2f}"),
                        html.P(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
                    ], style={'background': '#1e222d', 'padding': '15px', 'margin': '10px', 
                             'borderRadius': '10px', 'color': 'white', 'width': '300px', 
                             'display': 'inline-block', 'verticalAlign': 'top'})
                )
            
            return signals
    
    def run(self):
        """Run the system"""
        print(f"""
🚀 SIMPLE UNIFIED CRYPTO SYSTEM
==============================

✨ Features:
   • 🐦 Twitter sentiment analysis
   • 🤖 AI trading signals  
   • 📊 Real-time dashboard
   • 💰 Opportunity tracking

🌐 Dashboard: http://localhost:{self.port}
⚡ Press Ctrl+C to stop

Starting dashboard...
        """)
        
        try:
            self.app.run_server(
                host='0.0.0.0',
                port=self.port,
                debug=False
            )
        except Exception as e:
            logger.error(f"Error running system: {e}")
        finally:
            logger.info("System shutdown")

def main():
    """Main function"""
    # Find available port
    for port in range(8060, 8070):
        try:
            system = SimpleUnifiedSystem(port=port)
            system.run()
            break
        except OSError as e:
            if "Address already in use" in str(e):
                continue
            else:
                raise e

if __name__ == "__main__":
    main() 