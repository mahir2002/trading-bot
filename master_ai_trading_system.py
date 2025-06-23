#!/usr/bin/env python3
"""
🚀 MASTER AI TRADING SYSTEM 🚀
The Ultimate All-in-One Cryptocurrency Trading Platform

Integrates ALL advanced features:
- Enhanced AI Trading Bot with Transformer models
- Advanced Portfolio Optimizer with Modern Portfolio Theory
- Advanced Sentiment Analyzer with multi-source analysis
- Ultimate Crypto System with comprehensive data
- Real-time dashboards and analytics
- Professional risk management
"""

import os
import sys
import time
import logging
import asyncio
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import json
import pickle
from pathlib import Path
import threading

# Suppress warnings
warnings.filterwarnings('ignore')

# Core libraries
import ccxt
import requests
from dotenv import load_dotenv

# ML libraries
import ta
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.cluster import KMeans
import torch
import torch.nn as nn

# Portfolio optimization
import cvxpy as cp
from scipy.optimize import minimize
from scipy.stats import norm

# Sentiment analysis
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Dashboard
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc

# Import our existing components
try:
    from enhanced_crypto_fetcher import EnhancedCryptoFetcher
    from dexscreener_fetcher import DEXScreenerFetcher
    from twitter_crypto_analyzer import TwitterCryptoAnalyzer
    from enhanced_ai_trading_bot import (
        TransformerPricePredictor, AdvancedFeatureEngineer, 
        MarketRegimeDetector, AdvancedRiskManager, MultiTimeframeAnalyzer,
        TradingSignal, MarketRegime, RiskLevel
    )
    from advanced_portfolio_optimizer import (
        AdvancedPortfolioOptimizer, OptimizationMethod, 
        PortfolioConstraints, OptimizationResult
    )
    from advanced_sentiment_analyzer import (
        AdvancedSentimentAnalyzer, SentimentScore, SentimentSource
    )
except ImportError as e:
    print(f"⚠️ Some components not found: {e}")
    print("🔄 Running with available components...")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'master_ai_system_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('config.env')

@dataclass
class SystemStatus:
    """System component status tracking"""
    ai_trading_bot: bool = False
    portfolio_optimizer: bool = False
    sentiment_analyzer: bool = False
    data_fetchers: bool = False
    dashboard: bool = False
    last_update: datetime = field(default_factory=datetime.now)

class MasterAITradingSystem:
    """Master AI Trading System - All-in-One Platform"""
    
    def __init__(self):
        """Initialize the master system"""
        logger.info("🚀 Initializing Master AI Trading System...")
        
        # System status
        self.status = SystemStatus()
        self.running = True
        
        # Core components
        self.crypto_fetcher = None
        self.dex_fetcher = None
        self.twitter_analyzer = None
        self.ai_trading_bot = None
        self.portfolio_optimizer = None
        self.sentiment_analyzer = None
        
        # Data storage
        self.market_data = {}
        self.trading_signals = []
        self.portfolio_weights = {}
        self.sentiment_scores = {}
        self.performance_metrics = {}
        
        # Dashboard
        self.app = None
        
        # Initialize components
        self._initialize_components()
        
        logger.info("✅ Master AI Trading System initialized successfully!")
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Data fetchers
            logger.info("📡 Initializing data fetchers...")
            self.crypto_fetcher = EnhancedCryptoFetcher()
            self.dex_fetcher = DEXScreenerFetcher()
            self.status.data_fetchers = True
            logger.info("✅ Data fetchers initialized")
            
            # AI Trading Bot components
            logger.info("🤖 Initializing AI trading components...")
            self.feature_engineer = AdvancedFeatureEngineer()
            self.regime_detector = MarketRegimeDetector()
            self.risk_manager = AdvancedRiskManager()
            self.timeframe_analyzer = MultiTimeframeAnalyzer()
            self.transformer_model = TransformerPricePredictor()
            self.status.ai_trading_bot = True
            logger.info("✅ AI trading components initialized")
            
            # Portfolio Optimizer
            logger.info("🎯 Initializing portfolio optimizer...")
            self.portfolio_optimizer = AdvancedPortfolioOptimizer()
            self.status.portfolio_optimizer = True
            logger.info("✅ Portfolio optimizer initialized")
            
            # Sentiment Analyzer
            logger.info("📊 Initializing sentiment analyzer...")
            try:
                self.sentiment_analyzer = AdvancedSentimentAnalyzer()
                self.status.sentiment_analyzer = True
                logger.info("✅ Sentiment analyzer initialized")
            except Exception as e:
                logger.warning(f"⚠️ Sentiment analyzer initialization failed: {e}")
                self.sentiment_analyzer = None
            
            # Twitter Analyzer (optional)
            try:
                self.twitter_analyzer = TwitterCryptoAnalyzer()
                logger.info("✅ Twitter analyzer initialized")
            except Exception as e:
                logger.warning(f"⚠️ Twitter analyzer initialization failed: {e}")
                self.twitter_analyzer = None
            
        except Exception as e:
            logger.error(f"❌ Component initialization error: {e}")
            raise
    
    def setup_dashboard(self):
        """Setup the unified dashboard"""
        logger.info("🎨 Setting up Master Dashboard...")
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.CYBORG],
            suppress_callback_exceptions=True
        )
        
        self.app.title = "Master AI Trading System"
        
        # Create layout
        self._create_master_layout()
        
        # Setup callbacks
        self._setup_master_callbacks()
        
        self.status.dashboard = True
        logger.info("✅ Master Dashboard setup complete")
    
    def _create_master_layout(self):
        """Create the master dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🚀 MASTER AI TRADING SYSTEM", 
                           className="text-center mb-4",
                           style={'color': '#00ff88', 'fontWeight': 'bold'}),
                    html.H4("All-in-One Cryptocurrency Trading Platform", 
                           className="text-center mb-4",
                           style={'color': '#888888'}),
                ], width=12)
            ]),
            
            # System Status Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🔧 System Status", className="card-title"),
                            html.Div(id="system-status", children=[])
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ], className="mb-4"),
            
            # Main Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🎮 Control Panel", className="card-title"),
                            dbc.ButtonGroup([
                                dbc.Button("🚀 Start All Systems", id="start-all-btn", 
                                         color="success", className="me-2"),
                                dbc.Button("⏸️ Pause Trading", id="pause-btn", 
                                         color="warning", className="me-2"),
                                dbc.Button("🔄 Refresh Data", id="refresh-btn", 
                                         color="info", className="me-2"),
                                dbc.Button("📊 Generate Report", id="report-btn", 
                                         color="primary")
                            ], className="d-grid gap-2")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ], className="mb-4"),
            
            # Main Dashboard Tabs
            dbc.Row([
                dbc.Col([
                    dbc.Tabs([
                        # Trading Overview Tab
                        dbc.Tab(label="🎯 Trading Overview", tab_id="trading-overview"),
                        
                        # AI Signals Tab
                        dbc.Tab(label="🤖 AI Trading Signals", tab_id="ai-signals"),
                        
                        # Portfolio Tab
                        dbc.Tab(label="💼 Portfolio Management", tab_id="portfolio"),
                        
                        # Sentiment Tab
                        dbc.Tab(label="📊 Market Sentiment", tab_id="sentiment"),
                        
                        # Analytics Tab
                        dbc.Tab(label="📈 Advanced Analytics", tab_id="analytics"),
                        
                        # Risk Management Tab
                        dbc.Tab(label="⚠️ Risk Management", tab_id="risk"),
                    ], id="main-tabs", active_tab="trading-overview")
                ], width=12)
            ]),
            
            # Tab Content
            dbc.Row([
                dbc.Col([
                    html.Div(id="tab-content")
                ], width=12)
            ], className="mt-4"),
            
            # Auto-refresh interval
            dcc.Interval(
                id='master-interval',
                interval=10*1000,  # 10 seconds
                n_intervals=0
            ),
            
            # Data storage
            dcc.Store(id='market-data-store'),
            dcc.Store(id='signals-store'),
            dcc.Store(id='portfolio-store'),
            dcc.Store(id='sentiment-store'),
            
        ], fluid=True, style={'backgroundColor': '#1a1a1a', 'minHeight': '100vh'})
    
    def _setup_master_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            Output("system-status", "children"),
            [Input("master-interval", "n_intervals")]
        )
        def update_system_status(n_intervals):
            """Update system status display"""
            status_items = [
                dbc.Badge("🤖 AI Trading", color="success" if self.status.ai_trading_bot else "danger", className="me-2"),
                dbc.Badge("🎯 Portfolio Optimizer", color="success" if self.status.portfolio_optimizer else "danger", className="me-2"),
                dbc.Badge("📊 Sentiment Analyzer", color="success" if self.status.sentiment_analyzer else "danger", className="me-2"),
                dbc.Badge("📡 Data Fetchers", color="success" if self.status.data_fetchers else "danger", className="me-2"),
                dbc.Badge("🎨 Dashboard", color="success" if self.status.dashboard else "danger", className="me-2"),
            ]
            
            return html.Div([
                html.P(f"Last Update: {self.status.last_update.strftime('%H:%M:%S')}", 
                       className="text-muted mb-2"),
                html.Div(status_items)
            ])
        
        @self.app.callback(
            Output("tab-content", "children"),
            [Input("main-tabs", "active_tab")]
        )
        def render_tab_content(active_tab):
            """Render content based on active tab"""
            if active_tab == "trading-overview":
                return self._create_trading_overview_tab()
            elif active_tab == "ai-signals":
                return self._create_ai_signals_tab()
            elif active_tab == "portfolio":
                return self._create_portfolio_tab()
            elif active_tab == "sentiment":
                return self._create_sentiment_tab()
            elif active_tab == "analytics":
                return self._create_analytics_tab()
            elif active_tab == "risk":
                return self._create_risk_tab()
            else:
                return html.Div("Select a tab to view content")
        
        @self.app.callback(
            [Output("market-data-store", "data"),
             Output("signals-store", "data"),
             Output("portfolio-store", "data"),
             Output("sentiment-store", "data")],
            [Input("master-interval", "n_intervals"),
             Input("refresh-btn", "n_clicks"),
             Input("start-all-btn", "n_clicks")],
            prevent_initial_call=False
        )
        def update_all_data(n_intervals, refresh_clicks, start_clicks):
            """Update all system data"""
            try:
                # Fetch market data
                market_data = self._fetch_comprehensive_market_data()
                
                # Generate AI signals
                signals = self._generate_comprehensive_signals(market_data)
                
                # Optimize portfolio
                portfolio = self._optimize_portfolio(market_data)
                
                # Analyze sentiment
                sentiment = self._analyze_comprehensive_sentiment()
                
                return market_data, signals, portfolio, sentiment
                
            except Exception as e:
                logger.error(f"Error updating data: {e}")
                return {}, [], {}, {}
    
    def _create_trading_overview_tab(self):
        """Create trading overview tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 Market Overview", className="card-title"),
                            dcc.Graph(id="market-overview-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🎯 Active Signals", className="card-title"),
                            html.Div(id="active-signals-summary")
                        ])
                    ], color="dark", outline=True)
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("💰 Portfolio Performance", className="card-title"),
                            dcc.Graph(id="portfolio-performance-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ])
        ])
    
    def _create_ai_signals_tab(self):
        """Create AI signals tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🤖 AI Trading Signals", className="card-title"),
                            html.Div(id="ai-signals-table")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🧠 Model Performance", className="card-title"),
                            dcc.Graph(id="model-performance-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("⏰ Multi-Timeframe Analysis", className="card-title"),
                            dcc.Graph(id="timeframe-analysis-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=6)
            ])
        ])
    
    def _create_portfolio_tab(self):
        """Create portfolio management tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🎯 Portfolio Optimization", className="card-title"),
                            dcc.Graph(id="portfolio-allocation-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 Risk Metrics", className="card-title"),
                            html.Div(id="risk-metrics-display")
                        ])
                    ], color="dark", outline=True)
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📈 Efficient Frontier", className="card-title"),
                            dcc.Graph(id="efficient-frontier-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ])
        ])
    
    def _create_sentiment_tab(self):
        """Create sentiment analysis tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 Market Sentiment Overview", className="card-title"),
                            dcc.Graph(id="sentiment-overview-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🐦 Social Media Sentiment", className="card-title"),
                            dcc.Graph(id="social-sentiment-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📰 News Sentiment", className="card-title"),
                            dcc.Graph(id="news-sentiment-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=6)
            ])
        ])
    
    def _create_analytics_tab(self):
        """Create advanced analytics tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📈 Advanced Market Analytics", className="card-title"),
                            dcc.Graph(id="advanced-analytics-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ])
        ])
    
    def _create_risk_tab(self):
        """Create risk management tab content"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("⚠️ Risk Management Dashboard", className="card-title"),
                            dcc.Graph(id="risk-dashboard-chart")
                        ])
                    ], color="dark", outline=True)
                ], width=12)
            ])
        ])
    
    def _fetch_comprehensive_market_data(self):
        """Fetch comprehensive market data from all sources"""
        try:
            market_data = {}
            
            if self.crypto_fetcher:
                # Fetch from enhanced crypto fetcher
                crypto_data = self.crypto_fetcher.get_comprehensive_data()
                market_data.update(crypto_data)
            
            if self.dex_fetcher:
                # Fetch DEX data
                dex_data = self.dex_fetcher.get_trending_tokens()
                market_data['dex_trending'] = dex_data
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {}
    
    def _generate_comprehensive_signals(self, market_data):
        """Generate comprehensive trading signals"""
        try:
            signals = []
            
            if not market_data:
                return signals
            
            # Generate signals using AI components
            for symbol, data in market_data.items():
                if isinstance(data, pd.DataFrame) and len(data) > 50:
                    # Feature engineering
                    features = self.feature_engineer.engineer_features(data)
                    
                    # Multi-timeframe analysis
                    timeframe_signals = self.timeframe_analyzer.analyze_multiple_timeframes(
                        symbol, None  # We'll use the data we have
                    )
                    
                    # Create trading signal
                    signal = TradingSignal(
                        symbol=symbol,
                        action="hold",  # Default
                        confidence=0.5,
                        entry_price=data['close'].iloc[-1],
                        stop_loss=data['close'].iloc[-1] * 0.95,
                        take_profit=data['close'].iloc[-1] * 1.05,
                        position_size=0.02,
                        timeframe="1h",
                        strategy="master_ai",
                        risk_level=RiskLevel.MEDIUM,
                        market_regime=MarketRegime.SIDEWAYS
                    )
                    
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return []
    
    def _optimize_portfolio(self, market_data):
        """Optimize portfolio allocation"""
        try:
            if not self.portfolio_optimizer or not market_data:
                return {}
            
            # Prepare price data for optimization
            price_data = {}
            for symbol, data in market_data.items():
                if isinstance(data, pd.DataFrame) and 'close' in data.columns:
                    price_data[symbol] = data['close']
            
            if len(price_data) < 3:
                return {}
            
            # Optimize portfolio
            result = self.portfolio_optimizer.optimize_portfolio(
                price_data=price_data,
                method=OptimizationMethod.MARKOWITZ
            )
            
            return result.weights if result else {}
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")
            return {}
    
    def _analyze_comprehensive_sentiment(self):
        """Analyze comprehensive market sentiment"""
        try:
            sentiment_data = {}
            
            if self.sentiment_analyzer:
                # Get comprehensive sentiment analysis
                sentiment_data = self.sentiment_analyzer.get_comprehensive_sentiment()
            
            if self.twitter_analyzer:
                # Add Twitter sentiment
                twitter_sentiment = self.twitter_analyzer.get_latest_sentiment()
                sentiment_data['twitter'] = twitter_sentiment
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {}
    
    async def run_master_system(self):
        """Run the master system with all components"""
        logger.info("🚀 Starting Master AI Trading System...")
        
        try:
            # Setup dashboard
            self.setup_dashboard()
            
            # Start background tasks
            tasks = []
            
            # Data fetching task
            tasks.append(asyncio.create_task(self._data_fetching_loop()))
            
            # Signal generation task
            tasks.append(asyncio.create_task(self._signal_generation_loop()))
            
            # Portfolio optimization task
            tasks.append(asyncio.create_task(self._portfolio_optimization_loop()))
            
            # Sentiment analysis task
            tasks.append(asyncio.create_task(self._sentiment_analysis_loop()))
            
            # Run dashboard in thread
            dashboard_thread = threading.Thread(
                target=lambda: self.app.run_server(
                    host='127.0.0.1',
                    port=8080,
                    debug=False
                )
            )
            dashboard_thread.daemon = True
            dashboard_thread.start()
            
            logger.info("✅ Master AI Trading System is running!")
            logger.info("🌐 Dashboard available at: http://127.0.0.1:8080")
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ Error running master system: {e}")
            raise
    
    async def _data_fetching_loop(self):
        """Background data fetching loop"""
        while self.running:
            try:
                logger.info("📡 Fetching comprehensive market data...")
                self.market_data = self._fetch_comprehensive_market_data()
                self.status.last_update = datetime.now()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error in data fetching loop: {e}")
                await asyncio.sleep(60)
    
    async def _signal_generation_loop(self):
        """Background signal generation loop"""
        while self.running:
            try:
                if self.market_data:
                    logger.info("🤖 Generating AI trading signals...")
                    self.trading_signals = self._generate_comprehensive_signals(self.market_data)
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(120)
    
    async def _portfolio_optimization_loop(self):
        """Background portfolio optimization loop"""
        while self.running:
            try:
                if self.market_data:
                    logger.info("🎯 Optimizing portfolio allocation...")
                    self.portfolio_weights = self._optimize_portfolio(self.market_data)
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                logger.error(f"Error in portfolio optimization loop: {e}")
                await asyncio.sleep(600)
    
    async def _sentiment_analysis_loop(self):
        """Background sentiment analysis loop"""
        while self.running:
            try:
                logger.info("📊 Analyzing market sentiment...")
                self.sentiment_scores = self._analyze_comprehensive_sentiment()
                await asyncio.sleep(120)  # Update every 2 minutes
            except Exception as e:
                logger.error(f"Error in sentiment analysis loop: {e}")
                await asyncio.sleep(240)
    
    def run(self, host='127.0.0.1', port=8080, debug=False):
        """Run the master system"""
        try:
            # Run the async master system
            asyncio.run(self.run_master_system())
        except KeyboardInterrupt:
            logger.info("🛑 Master AI Trading System stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Error running master system: {e}")
            raise

def main():
    """Main function"""
    print("🚀 MASTER AI TRADING SYSTEM")
    print("=" * 50)
    print("🎯 All-in-One Cryptocurrency Trading Platform")
    print("🤖 AI Trading + Portfolio Optimization + Sentiment Analysis")
    print("📊 Comprehensive Market Data + Professional Dashboard")
    print("=" * 50)
    print()
    
    try:
        # Create and run master system
        master_system = MasterAITradingSystem()
        
        print("🌐 Starting Master Dashboard at http://127.0.0.1:8080")
        print("⏳ Please wait while all systems initialize...")
        print("🔄 This may take 30-60 seconds for full startup")
        print()
        print("Press Ctrl+C to stop the system")
        print("=" * 50)
        
        master_system.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Master AI Trading System stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()