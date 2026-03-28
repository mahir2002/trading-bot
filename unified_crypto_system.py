#!/usr/bin/env python3
"""
🚀 Unified Crypto Trading System
All-in-one: Twitter Analysis + AI Trading + Dashboard
"""

import os
import sys
import time
import logging
import threading
import queue
import signal
from datetime import datetime
from typing import Dict, List, Optional
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Import our modules
from twitter_crypto_analyzer import TwitterCryptoAnalyzer
from dynamic_crypto_fetcher import DynamicCryptoFetcher
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

class UnifiedCryptoSystem:
    def __init__(self, port=8059):
        """Initialize the unified crypto trading system"""
        self.port = port
        self.running = True
        
        # Initialize components
        logger.info("🚀 Initializing Unified Crypto Trading System...")
        self.twitter_analyzer = TwitterCryptoAnalyzer()
        self.crypto_fetcher = DynamicCryptoFetcher()
        self.ai_bot = DynamicAITradingBot()
        
        # Data storage
        self.latest_twitter_analysis = {}
        self.latest_ai_signals = {}
        self.combined_opportunities = []
        self.system_stats = {
            'twitter_analyses': 0,
            'ai_cycles': 0,
            'opportunities_found': 0,
            'trades_executed': 0,
            'uptime_start': datetime.now()
        }
        
        # Threading
        self.data_queue = queue.Queue()
        self.threads = []
        
        # Setup dashboard
        self.setup_dashboard()
        
        logger.info("✅ Unified Crypto System initialized successfully")
    
    def setup_dashboard(self):
        """Setup the unified dashboard"""
        self.app = dash.Dash(__name__)
        
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🚀 Unified Crypto Trading System", className="main-title"),
                html.Div([
                    html.Span("🔴 LIVE", className="live-indicator"),
                    html.Span(id="system-status", className="status-text")
                ], className="header-status")
            ], className="header"),
            
            # System Stats
            html.Div([
                html.Div(id="system-stats", className="stats-container")
            ], className="stats-section"),
            
            # Main Content Tabs
            dcc.Tabs(id="main-tabs", value="overview", children=[
                dcc.Tab(label="📊 Overview", value="overview"),
                dcc.Tab(label="🐦 Twitter Analysis", value="twitter"),
                dcc.Tab(label="🤖 AI Trading", value="ai"),
                dcc.Tab(label="💰 Opportunities", value="opportunities"),
                dcc.Tab(label="📈 Performance", value="performance")
            ], className="main-tabs"),
            
            # Tab Content
            html.Div(id="tab-content", className="tab-content"),
            
            # Auto-refresh
            dcc.Interval(
                id='unified-interval',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            ),
            
            # Data stores
            dcc.Store(id='unified-data'),
            dcc.Store(id='twitter-data'),
            dcc.Store(id='ai-data')
            
        ], className="unified-container")
        
        # Setup callbacks
        self.setup_callbacks()
        
        # Add CSS
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>Unified Crypto Trading System</title>
                {%favicon%}
                {%css%}
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min-height: 100vh;
                    }
                    
                    .unified-container {
                        max-width: 1600px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    
                    .header {
                        background: rgba(255,255,255,0.1);
                        padding: 20px;
                        border-radius: 15px;
                        margin-bottom: 20px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        backdrop-filter: blur(10px);
                    }
                    
                    .main-title {
                        margin: 0;
                        font-size: 2.5em;
                        background: linear-gradient(45deg, #FFD700, #FFA500);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }
                    
                    .live-indicator {
                        background: #ff4444;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-weight: bold;
                        animation: pulse 2s infinite;
                        margin-right: 10px;
                    }
                    
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    
                    .stats-section {
                        margin-bottom: 20px;
                    }
                    
                    .stats-container {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                    }
                    
                    .stat-card {
                        background: rgba(255,255,255,0.1);
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    }
                    
                    .stat-value {
                        font-size: 2em;
                        font-weight: bold;
                        color: #FFD700;
                    }
                    
                    .stat-label {
                        font-size: 0.9em;
                        opacity: 0.8;
                        margin-top: 5px;
                    }
                    
                    .main-tabs {
                        margin-bottom: 20px;
                    }
                    
                    .tab-content {
                        background: rgba(255,255,255,0.1);
                        padding: 20px;
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                        min-height: 500px;
                    }
                    
                    .opportunity-card {
                        background: rgba(255,255,255,0.1);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 10px 0;
                        border-left: 4px solid #FFD700;
                    }
                    
                    .tweet-card {
                        background: rgba(255,255,255,0.05);
                        padding: 12px;
                        border-radius: 8px;
                        margin: 8px 0;
                        border-left: 3px solid #1DA1F2;
                    }
                    
                    .signal-card {
                        background: rgba(255,255,255,0.1);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 10px 0;
                        border-left: 4px solid #4CAF50;
                    }
                    
                    .grid-2 {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 20px;
                    }
                    
                    .grid-3 {
                        display: grid;
                        grid-template-columns: 1fr 1fr 1fr;
                        gap: 20px;
                    }
                    
                    @media (max-width: 768px) {
                        .grid-2, .grid-3 {
                            grid-template-columns: 1fr;
                        }
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
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('unified-data', 'data'),
             Output('system-status', 'children')],
            Input('unified-interval', 'n_intervals')
        )
        def update_unified_data(n_intervals):
            """Update unified system data"""
            try:
                # Calculate uptime
                uptime = datetime.now() - self.system_stats['uptime_start']
                uptime_str = f"Uptime: {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
                
                unified_data = {
                    'twitter_analysis': self.latest_twitter_analysis,
                    'ai_signals': self.latest_ai_signals,
                    'opportunities': self.combined_opportunities,
                    'stats': self.system_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
                return unified_data, uptime_str
                
            except Exception as e:
                logger.error(f"Error updating unified data: {e}")
                return {}, f"Error: {str(e)}"
        
        @self.app.callback(
            Output('system-stats', 'children'),
            Input('unified-data', 'data')
        )
        def update_system_stats(unified_data):
            """Update system statistics"""
            if not unified_data or 'stats' not in unified_data:
                return html.Div("Loading system stats...")
            
            stats = unified_data['stats']
            
            stat_cards = [
                html.Div([
                    html.Div(f"{stats.get('twitter_analyses', 0)}", className="stat-value"),
                    html.Div("Twitter Analyses", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.Div(f"{stats.get('ai_cycles', 0)}", className="stat-value"),
                    html.Div("AI Trading Cycles", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.Div(f"{stats.get('opportunities_found', 0)}", className="stat-value"),
                    html.Div("Opportunities Found", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.Div(f"{stats.get('trades_executed', 0)}", className="stat-value"),
                    html.Div("Trades Executed", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.Div(f"{len(self.combined_opportunities)}", className="stat-value"),
                    html.Div("Active Opportunities", className="stat-label")
                ], className="stat-card")
            ]
            
            return stat_cards
        
        @self.app.callback(
            Output('tab-content', 'children'),
            [Input('main-tabs', 'value'),
             Input('unified-data', 'data')]
        )
        def update_tab_content(active_tab, unified_data):
            """Update tab content based on selection"""
            if not unified_data:
                return html.Div("Loading...")
            
            if active_tab == "overview":
                return self.render_overview_tab(unified_data)
            elif active_tab == "twitter":
                return self.render_twitter_tab(unified_data)
            elif active_tab == "ai":
                return self.render_ai_tab(unified_data)
            elif active_tab == "opportunities":
                return self.render_opportunities_tab(unified_data)
            elif active_tab == "performance":
                return self.render_performance_tab(unified_data)
            
            return html.Div("Tab not found")
    
    def render_overview_tab(self, data):
        """Render overview tab"""
        twitter_data = data.get('twitter_analysis', {})
        ai_data = data.get('ai_signals', {})
        opportunities = data.get('opportunities', [])
        
        return html.Div([
            html.H3("🎯 System Overview"),
            
            html.Div([
                # Twitter Summary
                html.Div([
                    html.H4("🐦 Twitter Analysis"),
                    html.P(f"Tweets Analyzed: {twitter_data.get('summary', {}).get('total_tweets', 0)}"),
                    html.P(f"Sentiment: {twitter_data.get('summary', {}).get('avg_sentiment', 0):.3f}"),
                    html.P(f"Opportunities: {twitter_data.get('summary', {}).get('total_opportunities', 0)}")
                ], className="stat-card"),
                
                # AI Summary
                html.Div([
                    html.H4("🤖 AI Trading"),
                    html.P(f"Signals Generated: {len(ai_data)}"),
                    html.P(f"Active Positions: {self.system_stats.get('active_positions', 0)}"),
                    html.P(f"Success Rate: {self.system_stats.get('success_rate', 0):.1f}%")
                ], className="stat-card"),
                
                # Combined Opportunities
                html.Div([
                    html.H4("💰 Combined Opportunities"),
                    html.P(f"Total Found: {len(opportunities)}"),
                    html.P(f"High Confidence: {len([o for o in opportunities if o.get('confidence', 0) > 80])}"),
                    html.P(f"Verified Coins: {len([o for o in opportunities if o.get('verified', False)])}")
                ], className="stat-card")
            ], className="grid-3"),
            
            # Recent Activity
            html.Div([
                html.H4("📈 Recent Activity"),
                html.Div([
                    html.P(f"Last Twitter Analysis: {datetime.now().strftime('%H:%M:%S')}"),
                    html.P(f"Last AI Cycle: {datetime.now().strftime('%H:%M:%S')}"),
                    html.P(f"System Status: 🟢 All systems operational")
                ])
            ], className="stat-card")
        ])
    
    def render_twitter_tab(self, data):
        """Render Twitter analysis tab"""
        twitter_data = data.get('twitter_analysis', {})
        
        if not twitter_data:
            return html.Div("No Twitter data available")
        
        opportunities = twitter_data.get('opportunities', [])
        tweets = twitter_data.get('analyzed_tweets', [])
        
        return html.Div([
            html.H3("🐦 Twitter Cryptocurrency Analysis"),
            
            # Top Opportunities
            html.Div([
                html.H4("🚀 Top Twitter Opportunities"),
                html.Div([
                    html.Div([
                        html.H5(f"{opp['symbol']} ({opp['opportunity_type'].title()})"),
                        html.P(f"Score: {opp['opportunity_score']:.1f} | Sentiment: {opp['avg_sentiment']:.3f}"),
                        html.P(f"Mentions: {opp['mention_count']} | Engagement: {opp['total_engagement']}"),
                        html.P(f"Sample: \"{opp['sample_tweets'][0][:100]}...\"" if opp['sample_tweets'] else "")
                    ], className="opportunity-card")
                    for opp in opportunities[:5]
                ])
            ]),
            
            # Recent Tweets
            html.Div([
                html.H4("📱 Recent Crypto Tweets"),
                html.Div([
                    html.Div([
                        html.P(tweet['text'][:200] + "..." if len(tweet['text']) > 200 else tweet['text']),
                        html.P(f"Sentiment: {tweet.get('sentiment', {}).get('polarity', 0):.3f} | "
                              f"Engagement: {tweet.get('engagement_score', 0)}")
                    ], className="tweet-card")
                    for tweet in tweets[:5]
                ])
            ])
        ])
    
    def render_ai_tab(self, data):
        """Render AI trading tab"""
        ai_data = data.get('ai_signals', {})
        
        return html.Div([
            html.H3("🤖 AI Trading Analysis"),
            
            html.Div([
                html.H4("📊 AI Trading Signals"),
                html.Div([
                    html.Div([
                        html.H5(f"{symbol}"),
                        html.P(f"Action: {signal.get('action', 'HOLD')}"),
                        html.P(f"Confidence: {signal.get('confidence', 0):.1f}%"),
                        html.P(f"Price: ${signal.get('price', 0):.6f}")
                    ], className="signal-card")
                    for symbol, signal in list(ai_data.items())[:10]
                ])
            ])
        ])
    
    def render_opportunities_tab(self, data):
        """Render combined opportunities tab"""
        opportunities = data.get('opportunities', [])
        
        return html.Div([
            html.H3("💰 Combined Trading Opportunities"),
            
            html.Div([
                html.Div([
                    html.H5(f"{opp.get('symbol', 'Unknown')}"),
                    html.P(f"Combined Score: {opp.get('combined_score', 0):.1f}"),
                    html.P(f"AI Confidence: {opp.get('ai_confidence', 0):.1f}%"),
                    html.P(f"Twitter Sentiment: {opp.get('twitter_sentiment', 0):.3f}"),
                    html.P(f"Recommendation: {opp.get('action', 'HOLD')}")
                ], className="opportunity-card")
                for opp in opportunities[:10]
            ])
        ])
    
    def render_performance_tab(self, data):
        """Render performance tracking tab"""
        stats = data.get('stats', {})
        
        return html.Div([
            html.H3("📈 System Performance"),
            
            html.Div([
                html.H4("📊 Performance Metrics"),
                html.P(f"Total Analyses: {stats.get('twitter_analyses', 0) + stats.get('ai_cycles', 0)}"),
                html.P(f"Opportunities Found: {stats.get('opportunities_found', 0)}"),
                html.P(f"Success Rate: {stats.get('success_rate', 0):.1f}%"),
                html.P(f"Uptime: {datetime.now() - stats.get('uptime_start', datetime.now())}")
            ], className="stat-card")
        ])
    
    def start_twitter_thread(self):
        """Start Twitter analysis thread"""
        def twitter_worker():
            logger.info("🐦 Starting Twitter analysis thread...")
            
            while self.running:
                try:
                    # Run Twitter analysis
                    analysis_results = self.twitter_analyzer.analyze_tweets()
                    
                    if analysis_results:
                        self.latest_twitter_analysis = analysis_results
                        self.system_stats['twitter_analyses'] += 1
                        self.system_stats['opportunities_found'] += len(analysis_results.get('opportunities', []))
                        
                        logger.info(f"🐦 Twitter analysis complete: {len(analysis_results.get('opportunities', []))} opportunities")
                    
                    # Wait for next analysis
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
        def ai_worker():
            logger.info("🤖 Starting AI trading thread...")
            
            while self.running:
                try:
                    # Run AI analysis
                    ai_signals = self.ai_bot.analyze_all_cryptocurrencies()
                    
                    if ai_signals:
                        self.latest_ai_signals = ai_signals
                        self.system_stats['ai_cycles'] += 1
                        
                        logger.info(f"🤖 AI analysis complete: {len(ai_signals)} signals generated")
                    
                    # Combine with Twitter data
                    self.combine_signals()
                    
                    # Wait for next cycle
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
            
            # Get data
            twitter_data = self.latest_twitter_analysis.get('opportunities', [])
            ai_data = self.latest_ai_signals
            
            # Combine signals
            for twitter_opp in twitter_data:
                symbol = twitter_opp['symbol']
                
                # Find matching AI signal
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
            
            # Sort by combined score
            combined_opportunities.sort(key=lambda x: x['combined_score'], reverse=True)
            self.combined_opportunities = combined_opportunities
            
            logger.info(f"💰 Combined {len(combined_opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"❌ Error combining signals: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("🛑 Shutdown signal received")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Run the unified system"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"""
🚀 UNIFIED CRYPTO TRADING SYSTEM
================================

✨ All-in-One Features:
   • 🐦 Live Twitter cryptocurrency analysis
   • 🤖 AI-powered trading signals
   • 📊 Real-time sentiment tracking
   • 💰 Combined opportunity detection
   • 📈 Professional dashboard interface
   • 🔔 Automated trading capabilities

🌐 Dashboard URL: http://localhost:{self.port}
⚡ Press Ctrl+C to stop all systems

🔄 Starting all components...
        """)
        
        try:
            # Start background threads
            self.start_twitter_thread()
            self.start_ai_thread()
            
            # Start dashboard
            logger.info(f"🌐 Starting unified dashboard on port {self.port}")
            self.app.run_server(
                host='0.0.0.0',
                port=self.port,
                debug=False
            )
            
        except Exception as e:
            logger.error(f"❌ System error: {e}")
        finally:
            self.running = False
            logger.info("🏁 Unified Crypto System shutdown complete")

def main():
    """Main execution function"""
    # Check for port conflicts and find available port
    base_port = 8059
    for port_offset in range(10):
        try:
            port = base_port + port_offset
            system = UnifiedCryptoSystem(port=port)
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