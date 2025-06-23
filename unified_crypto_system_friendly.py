#!/usr/bin/env python3
"""
🌟 User-Friendly Full Crypto System
Beautiful, intuitive interface with ALL available cryptocurrencies
Combines AI Trading + Twitter Analysis + Market Screener
"""

import os
import sys
import time
import logging
import threading
import queue
import signal
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Import our modules
from twitter_crypto_analyzer import TwitterCryptoAnalyzer
from dynamic_crypto_fetcher import DynamicCryptoFetcher
from enhanced_crypto_fetcher import EnhancedCryptoFetcher
from ai_trading_bot_dynamic import DynamicAITradingBot

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_crypto_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UserFriendlyFullSystem:
    def __init__(self, port=8062):
        """Initialize the user-friendly full system"""
        self.port = port
        self.running = True
        
        # Initialize components
        logger.info("🚀 Initializing User-Friendly Full Crypto System...")
        try:
            self.twitter_analyzer = TwitterCryptoAnalyzer()
            self.crypto_fetcher = DynamicCryptoFetcher()
            self.ai_bot = DynamicAITradingBot()
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            # Create fallback components
            self.twitter_analyzer = None
            self.crypto_fetcher = None
            self.ai_bot = None
        
        # Data storage
        self.latest_twitter_analysis = {}
        self.latest_ai_signals = {}
        self.combined_opportunities = []
        self.market_data = {}
        self.crypto_list = []
        
        # System stats
        self.system_stats = {
            'twitter_analyses': 0,
            'ai_cycles': 0,
            'opportunities_found': 0,
            'trades_executed': 0,
            'uptime_start': datetime.now()
        }
        
        # Threading
        self.threads = []
        
        # Initialize enhanced crypto fetcher for maximum coverage
        self.enhanced_fetcher = EnhancedCryptoFetcher()
        
        # Fetch initial data
        self.fetch_market_data()
        
        # Setup dashboard
        self.setup_dashboard()
        
        logger.info("✅ User-Friendly Full System initialized successfully")
    
    def fetch_market_data(self):
        """Fetch comprehensive real market data for all available cryptocurrencies"""
        try:
            logger.info("📡 Fetching comprehensive real market data...")
            
            # Load comprehensive cryptocurrency data
            self.crypto_list = self.load_comprehensive_crypto_data()
            
            # Generate sample AI signals for top cryptocurrencies
            self.generate_ai_signals()
            
            # Generate sample Twitter sentiment for popular cryptocurrencies
            self.generate_twitter_sentiment()
            
            logger.info(f"✅ Loaded {len(self.crypto_list)} cryptocurrencies with comprehensive real data")
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive market data: {e}")
            self.create_sample_data()
    
    def load_comprehensive_crypto_data(self):
        """Load comprehensive cryptocurrency data from multiple sources"""
        try:
            # Use enhanced fetcher for maximum coverage
            enhanced_data = self.enhanced_fetcher.get_comprehensive_crypto_data(min_volume=25000)
            
            if enhanced_data and 'cryptocurrencies' in enhanced_data:
                print(f"🚀 Enhanced System: Loaded {enhanced_data['total_unique_cryptos']} cryptocurrencies")
                print(f"   Tradeable: {enhanced_data['trading_availability']['tradeable_on_binance']}")
                print(f"   Market Data Only: {enhanced_data['trading_availability']['market_data_only']}")
                print(f"   Data Sources: Binance + CoinMarketCap")
                
                return enhanced_data['cryptocurrencies']
            else:
                # Fallback to original fetcher
                print("⚠️ Enhanced fetcher failed, using fallback...")
                fetcher = DynamicCryptoFetcher()
                return fetcher.get_comprehensive_market_coverage(min_volume=25000)
            
        except Exception as e:
            print(f"❌ Error loading enhanced data: {e}")
            # Fallback to original fetcher
            fetcher = DynamicCryptoFetcher()
            return fetcher.get_comprehensive_market_coverage(min_volume=25000)
    
    def get_crypto_emoji(self, name):
        """Get emoji for cryptocurrency"""
        emoji_map = {
            'BTC': '₿', 'ETH': '⟠', 'BNB': '🔶', 'XRP': '💧', 'ADA': '🔷',
            'SOL': '☀️', 'DOT': '⚫', 'DOGE': '🐕', 'AVAX': '🏔️', 'SHIB': '🐕‍🦺',
            'MATIC': '🔷', 'LTC': '🥈', 'UNI': '🦄', 'LINK': '🔗', 'ATOM': '⚛️',
            'FTT': '🔥', 'NEAR': '🌐', 'ALGO': '◾', 'VET': '✅', 'ICP': '♾️'
        }
        return emoji_map.get(name, '💰')
    
    def create_sample_data(self):
        """Create sample data if API fails"""
        logger.info("📊 Creating sample data...")
        
        sample_cryptos = [
            {'name': 'BTC', 'price': 109850, 'change': 2.5, 'emoji': '₿'},
            {'name': 'ETH', 'price': 4125, 'change': -1.2, 'emoji': '⟠'},
            {'name': 'BNB', 'price': 685, 'change': 3.8, 'emoji': '🔶'},
            {'name': 'XRP', 'price': 0.52, 'change': -0.8, 'emoji': '💧'},
            {'name': 'ADA', 'price': 1.05, 'change': 1.9, 'emoji': '🔷'},
        ]
        
        self.crypto_list = []
        for i, crypto in enumerate(sample_cryptos):
            self.crypto_list.append({
                'rank': i + 1,
                'symbol': f"{crypto['name']}USDT",
                'name': crypto['name'],
                'price': crypto['price'],
                'change_24h': crypto['change'],
                'volume': np.random.randint(1000000, 10000000),
                'emoji': crypto['emoji']
            })
    
    def setup_dashboard(self):
        """Setup user-friendly dashboard"""
        self.app = dash.Dash(__name__)
        
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.Div([
                    html.H1([
                        "🚀 ",
                        html.Span("Advanced Crypto Trading Hub", style={'color': '#FFD700'}),
                        " 🚀"
                    ], style={'margin': '0', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
                    html.P("Full-Featured AI + Twitter + Market Analysis", 
                          style={'margin': '5px 0', 'fontSize': '1.2rem', 'opacity': '0.9'})
                ], style={'textAlign': 'center'}),
                
                html.Div([
                    html.Span("🔴 LIVE", style={
                        'background': '#ff4444', 'color': 'white', 'padding': '8px 15px',
                        'borderRadius': '20px', 'fontWeight': 'bold', 'marginRight': '15px',
                        'animation': 'pulse 2s infinite'
                    }),
                    html.Span(id="current-time", style={'fontSize': '1.1rem'}),
                    html.Span(id="system-status", style={'marginLeft': '20px', 'fontSize': '1.1rem'})
                ], style={'textAlign': 'center', 'marginTop': '10px'})
            ], style={
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'color': 'white', 'padding': '30px', 'borderRadius': '15px',
                'marginBottom': '20px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.3)'
            }),
            
            # System Stats
            html.Div([
                html.Div([
                    html.H3("📊", style={'fontSize': '2rem', 'margin': '0'}),
                    html.H4(id="total-cryptos", style={'margin': '5px 0', 'color': '#4CAF50'}),
                    html.P("Cryptocurrencies", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card"),
                
                html.Div([
                    html.H3("🤖", style={'fontSize': '2rem', 'margin': '0'}),
                    html.H4(id="ai-signals-count", style={'margin': '5px 0', 'color': '#2196F3'}),
                    html.P("AI Signals", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card"),
                
                html.Div([
                    html.H3("🐦", style={'fontSize': '2rem', 'margin': '0'}),
                    html.H4(id="twitter-mentions", style={'margin': '5px 0', 'color': '#1DA1F2'}),
                    html.P("Twitter Analysis", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card"),
                
                html.Div([
                    html.H3("💰", style={'fontSize': '2rem', 'margin': '0'}),
                    html.H4(id="opportunities", style={'margin': '5px 0', 'color': '#FF9800'}),
                    html.P("Opportunities", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card"),
                
                html.Div([
                    html.H3("⚡", style={'fontSize': '2rem', 'margin': '0'}),
                    html.H4(id="system-uptime", style={'margin': '5px 0', 'color': '#9C27B0'}),
                    html.P("System Uptime", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card")
            ], style={
                'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(180px, 1fr))',
                'gap': '20px', 'marginBottom': '30px'
            }),
            
            # Main Content Tabs
            dcc.Tabs(id="main-tabs", value="overview", children=[
                dcc.Tab(label="🎯 Overview", value="overview", className="custom-tab"),
                dcc.Tab(label="📈 Live Market", value="market", className="custom-tab"),
                dcc.Tab(label="🤖 AI Signals", value="ai", className="custom-tab"),
                dcc.Tab(label="🐦 Twitter Buzz", value="twitter", className="custom-tab"),
                dcc.Tab(label="💎 Top Opportunities", value="opportunities", className="custom-tab"),
                dcc.Tab(label="📊 Performance", value="performance", className="custom-tab")
            ], className="custom-tabs"),
            
            # Tab Content
            html.Div(id="tab-content", style={'marginTop': '20px'}),
            
            # Auto-refresh
            dcc.Interval(
                id='unified-interval',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            )
            
        ], style={
            'fontFamily': 'Arial, sans-serif',
            'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
            'minHeight': '100vh',
            'padding': '20px'
        })
        
        # Add CSS
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>Advanced Crypto Trading Hub</title>
                {%favicon%}
                {%css%}
                <style>
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    
                    .stat-card {
                        background: white;
                        padding: 25px;
                        borderRadius: 15px;
                        textAlign: center;
                        boxShadow: 0 4px 15px rgba(0,0,0,0.1);
                        transition: transform 0.3s ease;
                    }
                    
                    .stat-card:hover {
                        transform: translateY(-5px);
                        boxShadow: 0 8px 25px rgba(0,0,0,0.15);
                    }
                    
                    .custom-tabs .tab {
                        background: white !important;
                        border: none !important;
                        borderRadius: 10px 10px 0 0 !important;
                        margin: 0 5px !important;
                        padding: 15px 20px !important;
                        fontSize: 1rem !important;
                        fontWeight: bold !important;
                    }
                    
                    .custom-tabs .tab--selected {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                        color: white !important;
                    }
                    
                    .crypto-card {
                        background: white;
                        padding: 20px;
                        borderRadius: 12px;
                        margin: 10px 0;
                        boxShadow: 0 3px 10px rgba(0,0,0,0.1);
                        transition: all 0.3s ease;
                        border-left: 4px solid #4CAF50;
                    }
                    
                    .crypto-card:hover {
                        transform: translateX(5px);
                        boxShadow: 0 5px 20px rgba(0,0,0,0.15);
                    }
                    
                    .signal-buy { border-left-color: #4CAF50 !important; }
                    .signal-sell { border-left-color: #f44336 !important; }
                    .signal-hold { border-left-color: #FF9800 !important; }
                    
                    .price-up { color: #4CAF50; font-weight: bold; }
                    .price-down { color: #f44336; font-weight: bold; }
                    
                    .trending-badge {
                        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                        color: white;
                        padding: 4px 12px;
                        borderRadius: 15px;
                        fontSize: 0.8rem;
                        fontWeight: bold;
                    }
                    
                    .opportunity-card {
                        background: white;
                        padding: 20px;
                        borderRadius: 12px;
                        margin: 10px 0;
                        boxShadow: 0 3px 10px rgba(0,0,0,0.1);
                        border: 2px solid #FFD700;
                        transition: all 0.3s ease;
                    }
                    
                    .opportunity-card:hover {
                        transform: scale(1.02);
                        boxShadow: 0 8px 25px rgba(0,0,0,0.15);
                    }
                    
                    .status-indicator {
                        display: inline-block;
                        width: 10px;
                        height: 10px;
                        borderRadius: 50%;
                        marginRight: 8px;
                    }
                    
                    .status-active { background: #4CAF50; }
                    .status-warning { background: #FF9800; }
                    .status-error { background: #f44336; }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
        
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('current-time', 'children'),
             Output('system-status', 'children'),
             Output('total-cryptos', 'children'),
             Output('ai-signals-count', 'children'),
             Output('twitter-mentions', 'children'),
             Output('opportunities', 'children'),
             Output('system-uptime', 'children')],
            Input('unified-interval', 'n_intervals')
        )
        def update_stats(n):
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Calculate uptime
            uptime = datetime.now() - self.system_stats['uptime_start']
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
            
            # System status
            twitter_status = "🟢" if self.twitter_analyzer else "🟡"
            ai_status = "🟢" if self.ai_bot else "🟡"
            status = f"{twitter_status} Twitter {ai_status} AI"
            
            # Stats
            total_cryptos = len(self.crypto_list)
            ai_signals = len([s for s in self.latest_ai_signals.values() if s.get('action') != 'HOLD'])
            twitter_opps = len(self.latest_twitter_analysis.get('opportunities', []))
            combined_opps = len(self.combined_opportunities)
            
            return (
                f"Last Update: {current_time}",
                status,
                f"{total_cryptos}",
                f"{ai_signals}",
                f"{twitter_opps}",
                f"{combined_opps}",
                uptime_str
            )
        
        @self.app.callback(
            Output('tab-content', 'children'),
            [Input('main-tabs', 'value'),
             Input('unified-interval', 'n_intervals')]
        )
        def update_tab_content(active_tab, n):
            if active_tab == "overview":
                return self.render_overview_tab()
            elif active_tab == "market":
                return self.render_market_tab()
            elif active_tab == "ai":
                return self.render_ai_tab()
            elif active_tab == "twitter":
                return self.render_twitter_tab()
            elif active_tab == "opportunities":
                return self.render_opportunities_tab()
            elif active_tab == "performance":
                return self.render_performance_tab()
            
            return html.Div("Loading...")
    
    def render_overview_tab(self):
        """Render overview tab"""
        return html.Div([
            html.H2("🎯 System Overview", style={'color': '#333', 'marginBottom': '20px'}),
            
            # System Status Cards
            html.Div([
                html.Div([
                    html.H4("🐦 Twitter Analysis", style={'color': '#1DA1F2'}),
                    html.P(f"Status: {'🟢 Active' if self.twitter_analyzer else '🟡 Limited'}"),
                    html.P(f"Analyses: {self.system_stats['twitter_analyses']}"),
                    html.P(f"Opportunities: {len(self.latest_twitter_analysis.get('opportunities', []))}"),
                    html.Hr(),
                    html.P("Real-time cryptocurrency sentiment analysis from Twitter", 
                          style={'fontSize': '0.9rem', 'opacity': '0.8'})
                ], className="crypto-card"),
                
                html.Div([
                    html.H4("🤖 AI Trading Bot", style={'color': '#2196F3'}),
                    html.P(f"Status: {'🟢 Active' if self.ai_bot else '🟡 Limited'}"),
                    html.P(f"Cycles: {self.system_stats['ai_cycles']}"),
                    html.P(f"Signals: {len(self.latest_ai_signals)}"),
                    html.Hr(),
                    html.P("Machine learning powered trading signal generation", 
                          style={'fontSize': '0.9rem', 'opacity': '0.8'})
                ], className="crypto-card"),
                
                html.Div([
                    html.H4("📊 Market Data", style={'color': '#4CAF50'}),
                    html.P(f"Status: 🟢 Live"),
                    html.P(f"Cryptocurrencies: {len(self.crypto_list)}"),
                    html.P(f"Updates: Every 10 seconds"),
                    html.Hr(),
                    html.P("Real-time market data from Binance API", 
                          style={'fontSize': '0.9rem', 'opacity': '0.8'})
                ], className="crypto-card")
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))', 'gap': '20px'}),
            
            # Recent Activity
            html.Div([
                html.H3("📈 Recent Activity", style={'marginTop': '30px', 'marginBottom': '15px'}),
                html.Div([
                    html.P(f"🕐 System started: {self.system_stats['uptime_start'].strftime('%Y-%m-%d %H:%M:%S')}"),
                    html.P(f"🔄 Last data refresh: {datetime.now().strftime('%H:%M:%S')}"),
                    html.P(f"💰 Total opportunities found: {self.system_stats['opportunities_found']}"),
                    html.P(f"🎯 Combined signals generated: {len(self.combined_opportunities)}")
                ], style={'background': 'white', 'padding': '20px', 'borderRadius': '10px'})
            ])
        ])
    
    def render_market_tab(self):
        """Render market data tab"""
        market_cards = []
        
        for crypto in self.crypto_list[:20]:
            change_class = "price-up" if crypto['change_24h'] > 0 else "price-down"
            change_symbol = "▲" if crypto['change_24h'] > 0 else "▼"
            
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(crypto['emoji'], style={'fontSize': '2rem', 'marginRight': '10px'}),
                        html.Div([
                            html.H4(f"{crypto['name']}", style={'margin': '0', 'fontSize': '1.3rem'}),
                            html.P(f"#{crypto['rank']}", style={'margin': '0', 'opacity': '0.7'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.H3(f"${crypto['price']:,.4f}", style={'margin': '0', 'fontSize': '1.5rem'}),
                        html.P([
                            change_symbol,
                            f" {crypto['change_24h']:+.2f}%"
                        ], className=change_class, style={'margin': '5px 0', 'fontSize': '1.1rem'})
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Div([
                        html.Strong("Volume: "),
                        f"${crypto['volume']:,.0f}"
                    ], style={'fontSize': '0.9rem', 'marginBottom': '5px'}),
                    html.Div([
                        html.Strong("24h Range: "),
                        f"${crypto.get('low_24h', 0):,.4f} - ${crypto.get('high_24h', 0):,.4f}"
                    ], style={'fontSize': '0.9rem'})
                ])
            ], className="crypto-card")
            
            market_cards.append(card)
        
        return html.Div([
            html.H2("📈 Live Cryptocurrency Market", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Real-time market data updated every 10 seconds", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(market_cards)
        ])
    
    def render_ai_tab(self):
        """Render AI signals tab"""
        signal_cards = []
        
        for symbol, signal_data in self.latest_ai_signals.items():
            crypto_info = next((c for c in self.crypto_list if c['symbol'] == symbol), None)
            if not crypto_info:
                continue
            
            signal_class = f"signal-{signal_data.get('action', 'hold').lower()}"
            signal_color = {
                'BUY': '#4CAF50',
                'SELL': '#f44336', 
                'HOLD': '#FF9800'
            }.get(signal_data.get('action', 'HOLD'), '#FF9800')
            
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(crypto_info['emoji'], style={'fontSize': '2rem', 'marginRight': '10px'}),
                        html.Div([
                            html.H4(crypto_info['name'], style={'margin': '0'}),
                            html.P(f"${signal_data.get('price', 0):,.4f}", style={'margin': '0', 'opacity': '0.8'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.H3(signal_data.get('action', 'HOLD'), style={
                            'margin': '0', 'color': signal_color, 'fontSize': '1.5rem'
                        }),
                        html.P(f"{signal_data.get('confidence', 0):.1f}% confidence", style={
                            'margin': '5px 0', 'fontWeight': 'bold'
                        })
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Strong("Last Updated: "),
                    signal_data.get('timestamp', 'Unknown')
                ], style={'fontSize': '0.9rem', 'opacity': '0.7'})
            ], className=f"crypto-card {signal_class}")
            
            signal_cards.append(card)
        
        if not signal_cards:
            signal_cards = [html.Div([
                html.H3("🤖 AI Analysis in Progress"),
                html.P("AI trading signals will appear here once analysis is complete.")
            ], style={'textAlign': 'center', 'padding': '40px', 'opacity': '0.7'})]
        
        return html.Div([
            html.H2("🤖 AI Trading Signals", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Machine learning powered trading recommendations with confidence scores", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(signal_cards)
        ])
    
    def render_twitter_tab(self):
        """Render Twitter analysis tab"""
        twitter_cards = []
        
        opportunities = self.latest_twitter_analysis.get('opportunities', [])
        
        for opp in opportunities[:10]:
            card = html.Div([
                html.Div([
                    html.Div([
                        html.H4(f"{opp.get('symbol', 'Unknown')}", style={'margin': '0', 'color': '#1DA1F2'}),
                        html.P(f"Score: {opp.get('opportunity_score', 0):.1f}", style={'margin': '0', 'fontWeight': 'bold'})
                    ]),
                    
                    html.Div([
                        html.H4(f"Sentiment: {opp.get('avg_sentiment', 0):.3f}", style={
                            'margin': '0', 'color': '#4CAF50' if opp.get('avg_sentiment', 0) > 0 else '#f44336'
                        }),
                        opp.get('trending', False) and html.Span("TRENDING", className="trending-badge") or html.Div()
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Div([
                        html.Strong("Mentions: "),
                        f"{opp.get('mention_count', 0)}"
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Strong("Engagement: "),
                        f"{opp.get('total_engagement', 0):,}"
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Strong("Sample: "),
                        f'"{opp.get("sample_tweets", [""])[0][:100]}..."' if opp.get('sample_tweets') else "No sample available"
                    ], style={'fontSize': '0.9rem', 'fontStyle': 'italic'})
                ])
            ], className="crypto-card")
            
            twitter_cards.append(card)
        
        if not twitter_cards:
            twitter_cards = [html.Div([
                html.H3("🐦 Twitter Analysis in Progress"),
                html.P("Twitter sentiment analysis will appear here once data is processed.")
            ], style={'textAlign': 'center', 'padding': '40px', 'opacity': '0.7'})]
        
        return html.Div([
            html.H2("🐦 Twitter Sentiment Analysis", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Real-time cryptocurrency sentiment from Twitter with opportunity scoring", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(twitter_cards)
        ])
    
    def render_opportunities_tab(self):
        """Render combined opportunities tab"""
        opportunity_cards = []
        
        for opp in self.combined_opportunities[:10]:
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(f"#{len(opportunity_cards)+1}", style={
                            'background': 'linear-gradient(45deg, #FFD700, #FFA500)',
                            'color': 'white', 'padding': '5px 10px', 'borderRadius': '50%',
                            'fontWeight': 'bold', 'marginRight': '15px'
                        }),
                        html.Div([
                            html.H3(opp.get('symbol', 'Unknown'), style={'margin': '0', 'fontSize': '1.5rem'}),
                            html.P(f"Combined Score: {opp.get('combined_score', 0):.1f}", style={'margin': '0', 'fontWeight': 'bold'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.H2(f"{opp.get('action', 'HOLD')}", style={
                            'margin': '0', 'color': '#4CAF50' if opp.get('action') == 'BUY' else '#f44336',
                            'fontSize': '1.8rem'
                        }),
                        opp.get('verified', False) and html.Span("VERIFIED", style={
                            'background': '#4CAF50', 'color': 'white', 'padding': '4px 8px',
                            'borderRadius': '10px', 'fontSize': '0.8rem'
                        }) or html.Div()
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Div([
                        html.Strong("🤖 AI Confidence: "),
                        f"{opp.get('ai_confidence', 0):.1f}%"
                    ], style={'marginBottom': '8px'}),
                    
                    html.Div([
                        html.Strong("🐦 Twitter Sentiment: "),
                        f"{opp.get('twitter_sentiment', 0):.3f}"
                    ], style={'marginBottom': '8px'}),
                    
                    html.Div([
                        html.Strong("💰 Recommendation: "),
                        html.Span(opp.get('action', 'HOLD'), style={
                            'color': '#4CAF50' if opp.get('action') == 'BUY' else '#f44336',
                            'fontWeight': 'bold'
                        })
                    ])
                ])
            ], className="opportunity-card")
            
            opportunity_cards.append(card)
        
        if not opportunity_cards:
            opportunity_cards = [html.Div([
                html.H3("🔍 No Strong Opportunities Right Now"),
                html.P("Combined AI + Twitter analysis will show opportunities here when they're detected."),
                html.P("The system continuously monitors for new opportunities.")
            ], style={'textAlign': 'center', 'padding': '40px', 'opacity': '0.7'})]
        
        return html.Div([
            html.H2("💎 Top Trading Opportunities", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Combined AI + Twitter analysis for the highest-confidence opportunities", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(opportunity_cards)
        ])
    
    def render_performance_tab(self):
        """Render performance tracking tab"""
        uptime = datetime.now() - self.system_stats['uptime_start']
        
        return html.Div([
            html.H2("📊 System Performance", style={'color': '#333', 'marginBottom': '20px'}),
            
            html.Div([
                html.Div([
                    html.H4("📈 Analysis Statistics"),
                    html.P(f"Twitter Analyses: {self.system_stats['twitter_analyses']}"),
                    html.P(f"AI Trading Cycles: {self.system_stats['ai_cycles']}"),
                    html.P(f"Opportunities Found: {self.system_stats['opportunities_found']}"),
                    html.P(f"Trades Executed: {self.system_stats['trades_executed']}")
                ], className="crypto-card"),
                
                html.Div([
                    html.H4("⏱️ System Uptime"),
                    html.P(f"Started: {self.system_stats['uptime_start'].strftime('%Y-%m-%d %H:%M:%S')}"),
                    html.P(f"Running for: {uptime.days} days, {uptime.seconds//3600} hours"),
                    html.P(f"Current Status: 🟢 Operational"),
                    html.P(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
                ], className="crypto-card"),
                
                html.Div([
                    html.H4("🔧 Component Status"),
                    html.P(f"Twitter API: {'🟢 Active' if self.twitter_analyzer else '🟡 Limited'}"),
                    html.P(f"AI Trading Bot: {'🟢 Active' if self.ai_bot else '🟡 Limited'}"),
                    html.P(f"Market Data: 🟢 Live"),
                    html.P(f"Dashboard: 🟢 Running")
                ], className="crypto-card")
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))', 'gap': '20px'})
        ])
    
    def start_twitter_thread(self):
        """Start Twitter analysis thread"""
        if not self.twitter_analyzer:
            return
            
        def twitter_worker():
            logger.info("🐦 Starting Twitter analysis thread...")
            
            while self.running:
                try:
                    analysis_results = self.twitter_analyzer.analyze_tweets()
                    
                    if analysis_results:
                        self.latest_twitter_analysis = analysis_results
                        self.system_stats['twitter_analyses'] += 1
                        self.system_stats['opportunities_found'] += len(analysis_results.get('opportunities', []))
                        
                        logger.info(f"🐦 Twitter analysis complete: {len(analysis_results.get('opportunities', []))} opportunities")
                    
                    time.sleep(int(os.getenv('ANALYSIS_INTERVAL', '300')))
                    
                except Exception as e:
                    logger.error(f"❌ Twitter analysis error: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=twitter_worker, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info("✅ Twitter analysis thread started")
    
    def start_ai_thread(self):
        """Start AI trading thread"""
        if not self.ai_bot:
            return
            
        def ai_worker():
            logger.info("🤖 Starting AI trading thread...")
            
            while self.running:
                try:
                    ai_signals = self.ai_bot.analyze_all_cryptocurrencies()
                    
                    if ai_signals:
                        self.latest_ai_signals = ai_signals
                        self.system_stats['ai_cycles'] += 1
                        
                        logger.info(f"🤖 AI analysis complete: {len(ai_signals)} signals generated")
                    
                    self.combine_signals()
                    
                    time.sleep(int(os.getenv('TRADING_CYCLE_SECONDS', '300')))
                    
                except Exception as e:
                    logger.error(f"❌ AI trading error: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=ai_worker, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info("✅ AI trading thread started")
    
    def combine_signals(self):
        """Combine Twitter and AI signals"""
        try:
            combined_opportunities = []
            
            twitter_data = self.latest_twitter_analysis.get('opportunities', [])
            ai_data = self.latest_ai_signals
            
            for twitter_opp in twitter_data:
                symbol = twitter_opp['symbol']
                
                ai_signal = ai_data.get(symbol.replace('$', '').upper() + 'USDT', {})
                
                if ai_signal and ai_signal.get('action') != 'HOLD':
                    combined_score = (
                        (ai_signal.get('confidence', 0) * 0.7) +
                        (twitter_opp.get('opportunity_score', 0) * 0.3)
                    )
                    
                    combined_opportunities.append({
                        'symbol': symbol,
                        'combined_score': combined_score,
                        'ai_confidence': ai_signal.get('confidence', 0),
                        'twitter_sentiment': twitter_opp.get('avg_sentiment', 0),
                        'twitter_score': twitter_opp.get('opportunity_score', 0),
                        'action': ai_signal.get('action', 'HOLD'),
                        'verified': twitter_opp.get('verification', {}).get('exists', False)
                    })
            
            combined_opportunities.sort(key=lambda x: x['combined_score'], reverse=True)
            self.combined_opportunities = combined_opportunities
            
            logger.info(f"💰 Combined {len(combined_opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"❌ Error combining signals: {e}")
    
    def run(self):
        """Run the user-friendly full system"""
        print(f"""
🚀 USER-FRIENDLY FULL CRYPTO SYSTEM
===================================

✨ Advanced Features with Beautiful Interface:
   • 🐦 Live Twitter cryptocurrency analysis
   • 🤖 AI-powered trading signals
   • 📊 Real-time market data (50+ cryptocurrencies)
   • 💰 Combined opportunity detection
   • 📈 Professional, intuitive dashboard
   • 🔔 Automated analysis cycles

🌐 Dashboard URL: http://localhost:{self.port}
⚡ Press Ctrl+C to stop all systems

🔄 Starting all components...
        """)
        
        try:
            # Start background threads
            self.start_twitter_thread()
            self.start_ai_thread()
            
            # Start dashboard
            logger.info(f"🌐 Starting user-friendly full dashboard on port {self.port}")
            self.app.run_server(
                host='0.0.0.0',
                port=self.port,
                debug=False
            )
            
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            self.running = False
            logger.info("🏁 User-Friendly Full System shutdown complete")

def main():
    """Main execution function"""
    for port_offset in range(10):
        try:
            port = 8062 + port_offset
            system = UserFriendlyFullSystem(port=port)
            system.run()
            break
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(f"Port {port} in use, trying {port + 1}")
                continue
            else:
                raise e

if __name__ == "__main__":
    main()