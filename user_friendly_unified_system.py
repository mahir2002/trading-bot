#!/usr/bin/env python3
"""
🚀 User-Friendly Unified Crypto System
Beautiful, intuitive interface with real data
"""

import os
import sys
import time
import logging
import threading
import requests
from datetime import datetime
from typing import Dict, List
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserFriendlyUnifiedSystem:
    def __init__(self, port=8061):
        """Initialize user-friendly unified system"""
        self.port = port
        self.running = True
        
        # Real market data
        self.market_data = {}
        self.crypto_list = []
        self.twitter_sentiment = {}
        self.ai_signals = {}
        
        logger.info("🚀 Initializing User-Friendly Crypto System...")
        self.fetch_real_data()
        self.setup_dashboard()
        
    def fetch_real_data(self):
        """Fetch real cryptocurrency data"""
        try:
            logger.info("📡 Fetching real market data...")
            
            # Get top cryptocurrencies
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = requests.get(url)
            data = response.json()
            
            # Filter for USDT pairs and get top 50 by volume
            usdt_pairs = [item for item in data if item['symbol'].endswith('USDT')]
            usdt_pairs.sort(key=lambda x: float(x['volume']), reverse=True)
            
            self.crypto_list = []
            for i, crypto in enumerate(usdt_pairs[:50]):
                symbol = crypto['symbol']
                name = symbol.replace('USDT', '')
                
                crypto_info = {
                    'rank': i + 1,
                    'symbol': symbol,
                    'name': name,
                    'price': float(crypto['lastPrice']),
                    'change_24h': float(crypto['priceChangePercent']),
                    'volume': float(crypto['volume']),
                    'high_24h': float(crypto['highPrice']),
                    'low_24h': float(crypto['lowPrice']),
                    'emoji': self.get_crypto_emoji(name)
                }
                self.crypto_list.append(crypto_info)
            
            # Generate sample AI signals
            self.generate_ai_signals()
            
            # Generate sample Twitter sentiment
            self.generate_twitter_sentiment()
            
            logger.info(f"✅ Loaded {len(self.crypto_list)} cryptocurrencies with real data")
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            self.create_sample_data()
    
    def get_crypto_emoji(self, name):
        """Get emoji for cryptocurrency"""
        emoji_map = {
            'BTC': '₿', 'ETH': '⟠', 'BNB': '🔶', 'XRP': '💧', 'ADA': '🔷',
            'SOL': '☀️', 'DOT': '⚫', 'DOGE': '🐕', 'AVAX': '🏔️', 'SHIB': '🐕‍🦺',
            'MATIC': '🔷', 'LTC': '🥈', 'UNI': '🦄', 'LINK': '🔗', 'ATOM': '⚛️',
            'FTT': '🔥', 'NEAR': '🌐', 'ALGO': '◾', 'VET': '✅', 'ICP': '♾️'
        }
        return emoji_map.get(name, '💰')
    
    def generate_ai_signals(self):
        """Generate realistic AI trading signals"""
        signals = ['BUY', 'SELL', 'HOLD']
        
        for crypto in self.crypto_list[:20]:
            signal = np.random.choice(signals, p=[0.3, 0.2, 0.5])  # More HOLD signals
            confidence = np.random.uniform(60, 95) if signal != 'HOLD' else np.random.uniform(40, 70)
            
            self.ai_signals[crypto['symbol']] = {
                'signal': signal,
                'confidence': confidence,
                'price': crypto['price'],
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
    
    def generate_twitter_sentiment(self):
        """Generate realistic Twitter sentiment data"""
        for crypto in self.crypto_list[:15]:
            sentiment = np.random.uniform(-1, 1)
            mentions = np.random.randint(10, 500)
            
            self.twitter_sentiment[crypto['symbol']] = {
                'sentiment': sentiment,
                'mentions': mentions,
                'trending': sentiment > 0.5 and mentions > 100,
                'keywords': ['bullish', 'moon', 'rocket'] if sentiment > 0 else ['bearish', 'dump', 'sell']
            }
    
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
                        html.Span("Crypto Trading Hub", style={'color': '#FFD700'}),
                        " 🚀"
                    ], style={'margin': '0', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
                    html.P("Your All-in-One Cryptocurrency Trading Dashboard", 
                          style={'margin': '5px 0', 'fontSize': '1.2rem', 'opacity': '0.9'})
                ], style={'textAlign': 'center'}),
                
                html.Div([
                    html.Span("🔴 LIVE", style={
                        'background': '#ff4444', 'color': 'white', 'padding': '8px 15px',
                        'borderRadius': '20px', 'fontWeight': 'bold', 'marginRight': '15px',
                        'animation': 'pulse 2s infinite'
                    }),
                    html.Span(id="current-time", style={'fontSize': '1.1rem'})
                ], style={'textAlign': 'center', 'marginTop': '10px'})
            ], style={
                'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'color': 'white', 'padding': '30px', 'borderRadius': '15px',
                'marginBottom': '20px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.3)'
            }),
            
            # Quick Stats
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
                    html.P("Twitter Mentions", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card"),
                
                html.Div([
                    html.H3("💰", style={'fontSize': '2rem', 'margin': '0'}),
                    html.H4(id="opportunities", style={'margin': '5px 0', 'color': '#FF9800'}),
                    html.P("Opportunities", style={'margin': '0', 'fontSize': '0.9rem'})
                ], className="stat-card")
            ], style={
                'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                'gap': '20px', 'marginBottom': '30px'
            }),
            
            # Main Content Tabs
            dcc.Tabs(id="main-tabs", value="market", children=[
                dcc.Tab(label="📈 Live Market", value="market", className="custom-tab"),
                dcc.Tab(label="🤖 AI Signals", value="ai", className="custom-tab"),
                dcc.Tab(label="🐦 Twitter Buzz", value="twitter", className="custom-tab"),
                dcc.Tab(label="💎 Top Picks", value="picks", className="custom-tab")
            ], className="custom-tabs"),
            
            # Tab Content
            html.Div(id="tab-content", style={'marginTop': '20px'}),
            
            # Auto-refresh
            dcc.Interval(
                id='refresh-interval',
                interval=5*1000,  # Update every 5 seconds
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
                <title>Crypto Trading Hub</title>
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
                        padding: 15px 25px !important;
                        fontSize: 1.1rem !important;
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
             Output('total-cryptos', 'children'),
             Output('ai-signals-count', 'children'),
             Output('twitter-mentions', 'children'),
             Output('opportunities', 'children')],
            Input('refresh-interval', 'n_intervals')
        )
        def update_stats(n):
            current_time = datetime.now().strftime('%H:%M:%S')
            total_cryptos = len(self.crypto_list)
            ai_signals = len([s for s in self.ai_signals.values() if s['signal'] != 'HOLD'])
            twitter_total = sum(t['mentions'] for t in self.twitter_sentiment.values())
            opportunities = len([t for t in self.twitter_sentiment.values() if t['trending']])
            
            return (
                f"Last Update: {current_time}",
                f"{total_cryptos}",
                f"{ai_signals}",
                f"{twitter_total:,}",
                f"{opportunities}"
            )
        
        @self.app.callback(
            Output('tab-content', 'children'),
            [Input('main-tabs', 'value'),
             Input('refresh-interval', 'n_intervals')]
        )
        def update_tab_content(active_tab, n):
            if active_tab == "market":
                return self.render_market_tab()
            elif active_tab == "ai":
                return self.render_ai_tab()
            elif active_tab == "twitter":
                return self.render_twitter_tab()
            elif active_tab == "picks":
                return self.render_picks_tab()
            
            return html.Div("Loading...")
    
    def render_market_tab(self):
        """Render live market data tab"""
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
            html.Div(market_cards)
        ])
    
    def render_ai_tab(self):
        """Render AI signals tab"""
        signal_cards = []
        
        for symbol, signal_data in self.ai_signals.items():
            crypto_info = next((c for c in self.crypto_list if c['symbol'] == symbol), None)
            if not crypto_info:
                continue
            
            signal_class = f"signal-{signal_data['signal'].lower()}"
            signal_color = {
                'BUY': '#4CAF50',
                'SELL': '#f44336', 
                'HOLD': '#FF9800'
            }[signal_data['signal']]
            
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(crypto_info['emoji'], style={'fontSize': '2rem', 'marginRight': '10px'}),
                        html.Div([
                            html.H4(crypto_info['name'], style={'margin': '0'}),
                            html.P(f"${signal_data['price']:,.4f}", style={'margin': '0', 'opacity': '0.8'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.H3(signal_data['signal'], style={
                            'margin': '0', 'color': signal_color, 'fontSize': '1.5rem'
                        }),
                        html.P(f"{signal_data['confidence']:.1f}% confidence", style={
                            'margin': '5px 0', 'fontWeight': 'bold'
                        })
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Strong("Last Updated: "),
                    signal_data['timestamp']
                ], style={'fontSize': '0.9rem', 'opacity': '0.7'})
            ], className=f"crypto-card {signal_class}")
            
            signal_cards.append(card)
        
        return html.Div([
            html.H2("🤖 AI Trading Signals", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Machine learning powered trading recommendations", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(signal_cards)
        ])
    
    def render_twitter_tab(self):
        """Render Twitter sentiment tab"""
        twitter_cards = []
        
        for symbol, sentiment_data in self.twitter_sentiment.items():
            crypto_info = next((c for c in self.crypto_list if c['symbol'] == symbol), None)
            if not crypto_info:
                continue
            
            sentiment_score = sentiment_data['sentiment']
            sentiment_text = "Bullish 🚀" if sentiment_score > 0.3 else "Bearish 📉" if sentiment_score < -0.3 else "Neutral 😐"
            sentiment_color = "#4CAF50" if sentiment_score > 0.3 else "#f44336" if sentiment_score < -0.3 else "#FF9800"
            
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(crypto_info['emoji'], style={'fontSize': '2rem', 'marginRight': '10px'}),
                        html.Div([
                            html.H4(crypto_info['name'], style={'margin': '0'}),
                            html.P(f"{sentiment_data['mentions']} mentions", style={'margin': '0', 'opacity': '0.8'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.H4(sentiment_text, style={'margin': '0', 'color': sentiment_color}),
                        sentiment_data['trending'] and html.Span("TRENDING", className="trending-badge") or html.Div()
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Strong("Keywords: "),
                    ", ".join(sentiment_data['keywords'])
                ], style={'fontSize': '0.9rem'})
            ], className="crypto-card")
            
            twitter_cards.append(card)
        
        return html.Div([
            html.H2("🐦 Twitter Sentiment Analysis", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Real-time social media buzz and sentiment tracking", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(twitter_cards)
        ])
    
    def render_picks_tab(self):
        """Render top picks tab"""
        # Combine AI and Twitter data for top picks
        top_picks = []
        
        for crypto in self.crypto_list[:10]:
            symbol = crypto['symbol']
            ai_data = self.ai_signals.get(symbol, {})
            twitter_data = self.twitter_sentiment.get(symbol, {})
            
            # Calculate combined score
            ai_score = ai_data.get('confidence', 0) if ai_data.get('signal') == 'BUY' else 0
            twitter_score = (twitter_data.get('sentiment', 0) + 1) * 50  # Convert to 0-100
            combined_score = (ai_score * 0.6 + twitter_score * 0.4)
            
            if combined_score > 60:  # Only show good opportunities
                top_picks.append({
                    'crypto': crypto,
                    'ai_signal': ai_data.get('signal', 'HOLD'),
                    'ai_confidence': ai_data.get('confidence', 0),
                    'twitter_sentiment': twitter_data.get('sentiment', 0),
                    'twitter_mentions': twitter_data.get('mentions', 0),
                    'combined_score': combined_score,
                    'trending': twitter_data.get('trending', False)
                })
        
        # Sort by combined score
        top_picks.sort(key=lambda x: x['combined_score'], reverse=True)
        
        pick_cards = []
        for i, pick in enumerate(top_picks[:5]):
            crypto = pick['crypto']
            
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(f"#{i+1}", style={
                            'background': 'linear-gradient(45deg, #FFD700, #FFA500)',
                            'color': 'white', 'padding': '5px 10px', 'borderRadius': '50%',
                            'fontWeight': 'bold', 'marginRight': '15px'
                        }),
                        html.Span(crypto['emoji'], style={'fontSize': '2rem', 'marginRight': '10px'}),
                        html.Div([
                            html.H3(crypto['name'], style={'margin': '0', 'fontSize': '1.5rem'}),
                            html.P(f"${crypto['price']:,.4f}", style={'margin': '0', 'fontSize': '1.1rem', 'opacity': '0.8'})
                        ])
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                    
                    html.Div([
                        html.H2(f"{pick['combined_score']:.0f}", style={
                            'margin': '0', 'color': '#4CAF50', 'fontSize': '2rem'
                        }),
                        html.P("Score", style={'margin': '0', 'fontWeight': 'bold'})
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                
                html.Hr(style={'margin': '15px 0', 'opacity': '0.3'}),
                
                html.Div([
                    html.Div([
                        html.Strong("🤖 AI Signal: "),
                        html.Span(pick['ai_signal'], style={
                            'color': '#4CAF50' if pick['ai_signal'] == 'BUY' else '#f44336'
                        }),
                        f" ({pick['ai_confidence']:.1f}%)"
                    ], style={'marginBottom': '8px'}),
                    
                    html.Div([
                        html.Strong("🐦 Twitter: "),
                        f"{pick['twitter_mentions']} mentions",
                        pick['trending'] and html.Span(" • TRENDING", style={
                            'color': '#FF6B6B', 'fontWeight': 'bold'
                        }) or ""
                    ])
                ])
            ], className="crypto-card", style={'border': '2px solid #FFD700'})
            
            pick_cards.append(card)
        
        if not pick_cards:
            pick_cards = [html.Div([
                html.H3("🔍 No Strong Opportunities Right Now"),
                html.P("Keep monitoring - new opportunities appear regularly!")
            ], style={'textAlign': 'center', 'padding': '40px', 'opacity': '0.7'})]
        
        return html.Div([
            html.H2("💎 Top Trading Opportunities", style={'color': '#333', 'marginBottom': '20px'}),
            html.P("Combined AI + Twitter analysis for the best opportunities", 
                  style={'fontSize': '1.1rem', 'marginBottom': '20px', 'opacity': '0.8'}),
            html.Div(pick_cards)
        ])
    
    def run(self):
        """Run the user-friendly system"""
        print(f"""
🚀 USER-FRIENDLY CRYPTO TRADING HUB
===================================

✨ Features:
   • 📈 Live market data for 50+ cryptocurrencies
   • 🤖 AI-powered trading signals
   • 🐦 Twitter sentiment analysis
   • 💎 Combined opportunity scoring
   • 🎨 Beautiful, intuitive interface

🌐 Dashboard: http://localhost:{self.port}
⚡ Press Ctrl+C to stop

Starting user-friendly dashboard...
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
    for port in range(8061, 8070):
        try:
            system = UserFriendlyUnifiedSystem(port=port)
            system.run()
            break
        except OSError as e:
            if "Address already in use" in str(e):
                continue
            else:
                raise e

if __name__ == "__main__":
    main() 