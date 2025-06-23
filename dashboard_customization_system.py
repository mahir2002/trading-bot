#!/usr/bin/env python3
"""
🎛️ Dashboard Customization & User Input System
Comprehensive system allowing users to customize trading pairs, timeframes,
and bot parameters directly from the dashboard interface.
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import numpy as np
import requests
from dataclasses import dataclass, asdict

# Import WebSocket integration
from websocket_dash_integration import DashWebSocketIntegration

@dataclass
class TradingConfiguration:
    """Trading bot configuration parameters"""
    # Trading pairs
    active_pairs: List[str]
    max_pairs: int
    pair_selection_mode: str  # 'manual', 'auto', 'volume_based'
    
    # Timeframes
    primary_timeframe: str
    secondary_timeframes: List[str]
    analysis_timeframes: List[str]
    
    # Risk management
    max_position_size: float
    stop_loss_percentage: float
    take_profit_percentage: float
    max_daily_trades: int
    max_drawdown: float
    
    # AI/ML parameters
    confidence_threshold: float
    model_retrain_interval: int
    prediction_lookback: int
    feature_importance_threshold: float
    
    # Portfolio management
    portfolio_balance: float
    position_sizing_method: str
    rebalance_frequency: str
    
    # Technical indicators
    enabled_indicators: List[str]
    indicator_periods: Dict[str, int]
    signal_combination_method: str
    
    # Notifications
    enable_notifications: bool
    notification_channels: List[str]
    alert_conditions: Dict[str, Any]

class DashboardCustomizationSystem:
    """Advanced dashboard customization and user input system"""
    
    def __init__(self, app: dash.Dash):
        self.app = app
        self.logger = self._setup_logger()
        
        # Configuration management
        self.current_config = self._load_default_config()
        self.config_history = []
        self.available_pairs = self._fetch_available_pairs()
        self.available_indicators = self._get_available_indicators()
        
        # WebSocket integration
        self.ws_integration = DashWebSocketIntegration(app)
        
        # User preferences
        self.user_preferences = {
            'theme': 'dark',
            'layout': 'advanced',
            'auto_save': True,
            'real_time_updates': True
        }
        
        self.logger.info("🎛️ Dashboard Customization System initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for customization system"""
        logger = logging.getLogger('DashboardCustomization')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_default_config(self) -> TradingConfiguration:
        """Load default trading configuration"""
        return TradingConfiguration(
            # Trading pairs
            active_pairs=['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT'],
            max_pairs=10,
            pair_selection_mode='manual',
            
            # Timeframes
            primary_timeframe='1h',
            secondary_timeframes=['15m', '4h'],
            analysis_timeframes=['1m', '5m', '15m', '1h', '4h', '1d'],
            
            # Risk management
            max_position_size=0.1,  # 10% of portfolio
            stop_loss_percentage=0.05,  # 5%
            take_profit_percentage=0.15,  # 15%
            max_daily_trades=20,
            max_drawdown=0.2,  # 20%
            
            # AI/ML parameters
            confidence_threshold=0.75,
            model_retrain_interval=24,  # hours
            prediction_lookback=100,
            feature_importance_threshold=0.05,
            
            # Portfolio management
            portfolio_balance=100000.0,
            position_sizing_method='kelly_criterion',
            rebalance_frequency='daily',
            
            # Technical indicators
            enabled_indicators=['sma', 'ema', 'rsi', 'macd', 'bollinger_bands'],
            indicator_periods={'sma': 20, 'ema': 12, 'rsi': 14, 'macd': 26},
            signal_combination_method='weighted_average',
            
            # Notifications
            enable_notifications=True,
            notification_channels=['dashboard', 'email'],
            alert_conditions={'profit_target': 0.1, 'loss_limit': -0.05}
        )
    
    def _fetch_available_pairs(self) -> List[str]:
        """Fetch available trading pairs from exchange"""
        try:
            # Binance API call to get all USDT pairs
            response = requests.get('https://api.binance.com/api/v3/exchangeInfo')
            data = response.json()
            
            pairs = []
            for symbol in data['symbols']:
                if (symbol['status'] == 'TRADING' and 
                    symbol['symbol'].endswith('USDT') and
                    symbol['permissions'] and 'SPOT' in symbol['permissions']):
                    pairs.append(symbol['symbol'])
            
            # Sort by popularity/volume (simplified)
            popular_pairs = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
                'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT',
                'UNIUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT', 'FILUSDT'
            ]
            
            # Prioritize popular pairs
            sorted_pairs = popular_pairs + [p for p in pairs if p not in popular_pairs]
            
            self.logger.info(f"📊 Fetched {len(sorted_pairs)} available trading pairs")
            return sorted_pairs[:200]  # Limit to top 200
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching trading pairs: {e}")
            # Return default pairs if API fails
            return [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
                'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
            ]
    
    def _get_available_indicators(self) -> Dict[str, Dict]:
        """Get available technical indicators with their parameters"""
        return {
            'sma': {
                'name': 'Simple Moving Average',
                'category': 'trend',
                'parameters': {'period': {'type': 'int', 'default': 20, 'min': 5, 'max': 200}}
            },
            'ema': {
                'name': 'Exponential Moving Average',
                'category': 'trend',
                'parameters': {'period': {'type': 'int', 'default': 12, 'min': 5, 'max': 200}}
            },
            'rsi': {
                'name': 'Relative Strength Index',
                'category': 'momentum',
                'parameters': {'period': {'type': 'int', 'default': 14, 'min': 5, 'max': 50}}
            },
            'macd': {
                'name': 'MACD',
                'category': 'momentum',
                'parameters': {
                    'fast': {'type': 'int', 'default': 12, 'min': 5, 'max': 50},
                    'slow': {'type': 'int', 'default': 26, 'min': 10, 'max': 100},
                    'signal': {'type': 'int', 'default': 9, 'min': 5, 'max': 20}
                }
            },
            'bollinger_bands': {
                'name': 'Bollinger Bands',
                'category': 'volatility',
                'parameters': {
                    'period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50},
                    'std_dev': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 3.0}
                }
            },
            'stochastic': {
                'name': 'Stochastic Oscillator',
                'category': 'momentum',
                'parameters': {
                    'k_period': {'type': 'int', 'default': 14, 'min': 5, 'max': 50},
                    'd_period': {'type': 'int', 'default': 3, 'min': 1, 'max': 10}
                }
            },
            'atr': {
                'name': 'Average True Range',
                'category': 'volatility',
                'parameters': {'period': {'type': 'int', 'default': 14, 'min': 5, 'max': 50}}
            },
            'volume_sma': {
                'name': 'Volume SMA',
                'category': 'volume',
                'parameters': {'period': {'type': 'int', 'default': 20, 'min': 5, 'max': 100}}
            }
        }
    
    def create_customization_layout(self):
        """Create comprehensive customization interface"""
        
        layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🎛️ Trading Bot Customization", className="text-center mb-4"),
                    html.P("Configure trading pairs, timeframes, and bot parameters", 
                          className="text-center text-muted mb-4")
                ])
            ]),
            
            # Configuration tabs
            dbc.Tabs([
                # Trading Pairs Tab
                dbc.Tab(label="📊 Trading Pairs", tab_id="pairs-tab", children=[
                    self._create_pairs_configuration()
                ]),
                
                # Timeframes Tab
                dbc.Tab(label="⏰ Timeframes", tab_id="timeframes-tab", children=[
                    self._create_timeframes_configuration()
                ]),
                
                # Risk Management Tab
                dbc.Tab(label="🛡️ Risk Management", tab_id="risk-tab", children=[
                    self._create_risk_configuration()
                ]),
                
                # AI/ML Parameters Tab
                dbc.Tab(label="🤖 AI/ML Settings", tab_id="ai-tab", children=[
                    self._create_ai_configuration()
                ]),
                
                # Technical Indicators Tab
                dbc.Tab(label="📈 Indicators", tab_id="indicators-tab", children=[
                    self._create_indicators_configuration()
                ]),
                
                # Portfolio Management Tab
                dbc.Tab(label="💼 Portfolio", tab_id="portfolio-tab", children=[
                    self._create_portfolio_configuration()
                ]),
                
                # Notifications Tab
                dbc.Tab(label="🔔 Notifications", tab_id="notifications-tab", children=[
                    self._create_notifications_configuration()
                ])
            ], id="customization-tabs", active_tab="pairs-tab"),
            
            # Action buttons
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    dbc.ButtonGroup([
                        dbc.Button("💾 Save Configuration", id="save-config-btn", 
                                 color="success", className="me-2"),
                        dbc.Button("🔄 Reset to Defaults", id="reset-config-btn", 
                                 color="warning", className="me-2"),
                        dbc.Button("📥 Load Configuration", id="load-config-btn", 
                                 color="info", className="me-2"),
                        dbc.Button("🚀 Apply & Start Bot", id="apply-start-btn", 
                                 color="primary")
                    ], className="d-flex justify-content-center")
                ])
            ], className="mt-4"),
            
            # Status and feedback
            dbc.Row([
                dbc.Col([
                    html.Div(id="config-status", className="mt-3"),
                    html.Div(id="config-preview", className="mt-3")
                ])
            ]),
            
            # Hidden stores for configuration data
            dcc.Store(id="current-config-store", data=asdict(self.current_config)),
            dcc.Store(id="config-changes-store", data={}),
            dcc.Store(id="validation-results-store", data={}),
            
            # WebSocket components
            self.ws_integration.setup_websocket_components()
            
        ], fluid=True, className="py-4")
        
        return layout
    
    def _create_pairs_configuration(self):
        """Create trading pairs configuration interface"""
        
        return dbc.Container([
            dbc.Row([
                # Available pairs selection
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Available Trading Pairs"),
                        dbc.CardBody([
                            html.Div([
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="pairs-search",
                                        placeholder="Search pairs (e.g., BTC, ETH)...",
                                        type="text"
                                    ),
                                    dbc.Button("🔍", id="search-pairs-btn", color="outline-secondary")
                                ], className="mb-3")
                            ]),
                            
                            html.Div([
                                html.Label("Filter by Category:", className="form-label"),
                                dcc.Dropdown(
                                    id="pairs-category-filter",
                                    options=[
                                        {'label': 'All Pairs', 'value': 'all'},
                                        {'label': 'Major Coins', 'value': 'major'},
                                        {'label': 'DeFi Tokens', 'value': 'defi'},
                                        {'label': 'Layer 1', 'value': 'layer1'},
                                        {'label': 'Meme Coins', 'value': 'meme'},
                                        {'label': 'High Volume', 'value': 'high_volume'}
                                    ],
                                    value='all',
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Available Pairs:", className="form-label"),
                                dcc.Dropdown(
                                    id="available-pairs-dropdown",
                                    options=[{'label': pair, 'value': pair} for pair in self.available_pairs[:50]],
                                    multi=True,
                                    placeholder="Select pairs to add...",
                                    className="mb-3"
                                )
                            ]),
                            
                            dbc.Button("➕ Add Selected Pairs", id="add-pairs-btn", 
                                     color="success", className="w-100")
                        ])
                    ])
                ], width=6),
                
                # Active pairs management
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎯 Active Trading Pairs"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Selection Mode:", className="form-label"),
                                dbc.RadioItems(
                                    id="pair-selection-mode",
                                    options=[
                                        {'label': 'Manual Selection', 'value': 'manual'},
                                        {'label': 'Auto (Volume Based)', 'value': 'auto'},
                                        {'label': 'AI Recommended', 'value': 'ai_recommended'}
                                    ],
                                    value=self.current_config.pair_selection_mode,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Maximum Active Pairs:", className="form-label"),
                                dbc.Input(
                                    id="max-pairs-input",
                                    type="number",
                                    value=self.current_config.max_pairs,
                                    min=1, max=50, step=1,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Active Pairs:", className="form-label"),
                                html.Div(id="active-pairs-list", className="mb-3")
                            ]),
                            
                            dbc.Button("🔄 Refresh Pair Data", id="refresh-pairs-btn", 
                                     color="info", className="w-100")
                        ])
                    ])
                ], width=6)
            ]),
            
            # Pair performance metrics
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Pair Performance Metrics"),
                        dbc.CardBody([
                            html.Div(id="pairs-performance-table")
                        ])
                    ])
                ])
            ], className="mt-4")
        ])
    
    def _create_timeframes_configuration(self):
        """Create timeframes configuration interface"""
        
        timeframe_options = [
            {'label': '1 Minute', 'value': '1m'},
            {'label': '5 Minutes', 'value': '5m'},
            {'label': '15 Minutes', 'value': '15m'},
            {'label': '30 Minutes', 'value': '30m'},
            {'label': '1 Hour', 'value': '1h'},
            {'label': '4 Hours', 'value': '4h'},
            {'label': '1 Day', 'value': '1d'},
            {'label': '1 Week', 'value': '1w'}
        ]
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("⏰ Timeframe Configuration"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Primary Timeframe (Main Analysis):", className="form-label"),
                                dcc.Dropdown(
                                    id="primary-timeframe",
                                    options=timeframe_options,
                                    value=self.current_config.primary_timeframe,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Secondary Timeframes (Confirmation):", className="form-label"),
                                dcc.Dropdown(
                                    id="secondary-timeframes",
                                    options=timeframe_options,
                                    value=self.current_config.secondary_timeframes,
                                    multi=True,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Analysis Timeframes (Dashboard):", className="form-label"),
                                dcc.Dropdown(
                                    id="analysis-timeframes",
                                    options=timeframe_options,
                                    value=self.current_config.analysis_timeframes,
                                    multi=True,
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Timeframe Strategy"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Multi-Timeframe Analysis:", className="form-label"),
                                dbc.Switch(
                                    id="multi-timeframe-analysis",
                                    value=True,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Timeframe Weighting:", className="form-label"),
                                html.Div(id="timeframe-weights", className="mb-3")
                            ]),
                            
                            html.Div([
                                html.Label("Signal Confirmation Requirements:", className="form-label"),
                                dbc.Input(
                                    id="signal-confirmation-count",
                                    type="number",
                                    value=2,
                                    min=1, max=5, step=1,
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ], width=6)
            ])
        ])
    
    def _create_risk_configuration(self):
        """Create risk management configuration interface"""
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🛡️ Position Risk Management"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Maximum Position Size (% of Portfolio):", className="form-label"),
                                dcc.Slider(
                                    id="max-position-size",
                                    min=0.01, max=0.5, step=0.01,
                                    value=self.current_config.max_position_size,
                                    marks={i/100: f"{i}%" for i in range(1, 51, 5)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Stop Loss Percentage:", className="form-label"),
                                dcc.Slider(
                                    id="stop-loss-percentage",
                                    min=0.01, max=0.2, step=0.005,
                                    value=self.current_config.stop_loss_percentage,
                                    marks={i/100: f"{i}%" for i in range(1, 21, 2)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Take Profit Percentage:", className="form-label"),
                                dcc.Slider(
                                    id="take-profit-percentage",
                                    min=0.05, max=0.5, step=0.01,
                                    value=self.current_config.take_profit_percentage,
                                    marks={i/100: f"{i}%" for i in range(5, 51, 5)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4"
                                )
                            ])
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Portfolio Risk Limits"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Maximum Daily Trades:", className="form-label"),
                                dbc.Input(
                                    id="max-daily-trades",
                                    type="number",
                                    value=self.current_config.max_daily_trades,
                                    min=1, max=100, step=1,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Maximum Drawdown (%):", className="form-label"),
                                dcc.Slider(
                                    id="max-drawdown",
                                    min=0.05, max=0.5, step=0.01,
                                    value=self.current_config.max_drawdown,
                                    marks={i/100: f"{i}%" for i in range(5, 51, 5)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Risk-Reward Ratio:", className="form-label"),
                                dbc.Input(
                                    id="risk-reward-ratio",
                                    type="number",
                                    value=2.0,
                                    min=1.0, max=5.0, step=0.1,
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ], width=6)
            ])
        ])
    
    def _create_ai_configuration(self):
        """Create AI/ML parameters configuration interface"""
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🤖 AI Model Configuration"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Confidence Threshold:", className="form-label"),
                                dcc.Slider(
                                    id="confidence-threshold",
                                    min=0.5, max=0.95, step=0.05,
                                    value=self.current_config.confidence_threshold,
                                    marks={i/100: f"{i}%" for i in range(50, 96, 5)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Model Retrain Interval (hours):", className="form-label"),
                                dbc.Input(
                                    id="model-retrain-interval",
                                    type="number",
                                    value=self.current_config.model_retrain_interval,
                                    min=1, max=168, step=1,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Prediction Lookback Period:", className="form-label"),
                                dbc.Input(
                                    id="prediction-lookback",
                                    type="number",
                                    value=self.current_config.prediction_lookback,
                                    min=50, max=500, step=10,
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🧠 Feature Engineering"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Feature Importance Threshold:", className="form-label"),
                                dcc.Slider(
                                    id="feature-importance-threshold",
                                    min=0.01, max=0.2, step=0.01,
                                    value=self.current_config.feature_importance_threshold,
                                    marks={i/100: f"{i}%" for i in range(1, 21, 2)},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    className="mb-4"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Model Type:", className="form-label"),
                                dcc.Dropdown(
                                    id="model-type",
                                    options=[
                                        {'label': 'Random Forest', 'value': 'random_forest'},
                                        {'label': 'XGBoost', 'value': 'xgboost'},
                                        {'label': 'LSTM Neural Network', 'value': 'lstm'},
                                        {'label': 'Ensemble', 'value': 'ensemble'}
                                    ],
                                    value='ensemble',
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Auto Feature Selection:", className="form-label"),
                                dbc.Switch(
                                    id="auto-feature-selection",
                                    value=True,
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ], width=6)
            ])
        ])
    
    def _create_indicators_configuration(self):
        """Create technical indicators configuration interface"""
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Technical Indicators"),
                        dbc.CardBody([
                            html.Div(id="indicators-checklist"),
                            html.Hr(),
                            html.Div(id="indicator-parameters")
                        ])
                    ])
                ])
            ])
        ])
    
    def _create_portfolio_configuration(self):
        """Create portfolio management configuration interface"""
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💼 Portfolio Settings"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Portfolio Balance (USDT):", className="form-label"),
                                dbc.Input(
                                    id="portfolio-balance",
                                    type="number",
                                    value=self.current_config.portfolio_balance,
                                    min=100, step=100,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Position Sizing Method:", className="form-label"),
                                dcc.Dropdown(
                                    id="position-sizing-method",
                                    options=[
                                        {'label': 'Fixed Percentage', 'value': 'fixed_percentage'},
                                        {'label': 'Kelly Criterion', 'value': 'kelly_criterion'},
                                        {'label': 'Volatility Adjusted', 'value': 'volatility_adjusted'},
                                        {'label': 'Risk Parity', 'value': 'risk_parity'}
                                    ],
                                    value=self.current_config.position_sizing_method,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Rebalance Frequency:", className="form-label"),
                                dcc.Dropdown(
                                    id="rebalance-frequency",
                                    options=[
                                        {'label': 'Never', 'value': 'never'},
                                        {'label': 'Daily', 'value': 'daily'},
                                        {'label': 'Weekly', 'value': 'weekly'},
                                        {'label': 'Monthly', 'value': 'monthly'}
                                    ],
                                    value=self.current_config.rebalance_frequency,
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Portfolio Analytics"),
                        dbc.CardBody([
                            html.Div(id="portfolio-analytics")
                        ])
                    ])
                ], width=6)
            ])
        ])
    
    def _create_notifications_configuration(self):
        """Create notifications configuration interface"""
        
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔔 Notification Settings"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Enable Notifications:", className="form-label"),
                                dbc.Switch(
                                    id="enable-notifications",
                                    value=self.current_config.enable_notifications,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Notification Channels:", className="form-label"),
                                dbc.Checklist(
                                    id="notification-channels",
                                    options=[
                                        {'label': 'Dashboard Alerts', 'value': 'dashboard'},
                                        {'label': 'Email', 'value': 'email'},
                                        {'label': 'Telegram', 'value': 'telegram'},
                                        {'label': 'Discord', 'value': 'discord'},
                                        {'label': 'Slack', 'value': 'slack'}
                                    ],
                                    value=self.current_config.notification_channels,
                                    className="mb-3"
                                )
                            ]),
                            
                            html.Div([
                                html.Label("Alert Conditions:", className="form-label"),
                                html.Div(id="alert-conditions-config")
                            ])
                        ])
                    ])
                ])
            ])
        ])
    
    def setup_customization_callbacks(self):
        """Setup callbacks for customization interface"""
        
        # Trading pairs callbacks
        @self.app.callback(
            Output('active-pairs-list', 'children'),
            [Input('current-config-store', 'data')]
        )
        def update_active_pairs_display(config_data):
            """Update active pairs display"""
            if not config_data:
                return "No active pairs"
            
            active_pairs = config_data.get('active_pairs', [])
            
            pairs_components = []
            for pair in active_pairs:
                pairs_components.append(
                    dbc.Badge([
                        pair,
                        html.Button("×", 
                                  id={'type': 'remove-pair', 'pair': pair},
                                  className="btn-close btn-close-white ms-2",
                                  style={'border': 'none', 'background': 'none'})
                    ], color="primary", className="me-2 mb-2 d-flex align-items-center")
                )
            
            return pairs_components
        
        # Configuration save callback
        @self.app.callback(
            Output('config-status', 'children'),
            [Input('save-config-btn', 'n_clicks')],
            [State('current-config-store', 'data')]
        )
        def save_configuration(n_clicks, config_data):
            """Save configuration"""
            if not n_clicks:
                return ""
            
            try:
                # Save configuration to file/database
                self._save_configuration(config_data)
                
                return dbc.Alert(
                    "✅ Configuration saved successfully!",
                    color="success",
                    dismissable=True,
                    duration=3000
                )
            except Exception as e:
                return dbc.Alert(
                    f"❌ Error saving configuration: {str(e)}",
                    color="danger",
                    dismissable=True
                )
        
        # Configuration validation callback
        @self.app.callback(
            Output('validation-results-store', 'data'),
            [Input('current-config-store', 'data')]
        )
        def validate_configuration(config_data):
            """Validate configuration parameters"""
            if not config_data:
                return {}
            
            validation_results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Validate trading pairs
            if not config_data.get('active_pairs'):
                validation_results['errors'].append("At least one trading pair must be selected")
                validation_results['valid'] = False
            
            # Validate risk parameters
            if config_data.get('max_position_size', 0) > 0.5:
                validation_results['warnings'].append("Position size >50% is very risky")
            
            if config_data.get('stop_loss_percentage', 0) > 0.2:
                validation_results['warnings'].append("Stop loss >20% may be too high")
            
            # Validate AI parameters
            if config_data.get('confidence_threshold', 0) < 0.6:
                validation_results['warnings'].append("Low confidence threshold may increase false signals")
            
            return validation_results
        
        # Real-time configuration preview
        @self.app.callback(
            Output('config-preview', 'children'),
            [Input('current-config-store', 'data'),
             Input('validation-results-store', 'data')]
        )
        def update_config_preview(config_data, validation_results):
            """Update configuration preview"""
            if not config_data:
                return ""
            
            # Create configuration summary
            summary_items = [
                f"Active Pairs: {len(config_data.get('active_pairs', []))}",
                f"Primary Timeframe: {config_data.get('primary_timeframe', 'N/A')}",
                f"Max Position Size: {config_data.get('max_position_size', 0)*100:.1f}%",
                f"Stop Loss: {config_data.get('stop_loss_percentage', 0)*100:.1f}%",
                f"Confidence Threshold: {config_data.get('confidence_threshold', 0)*100:.1f}%"
            ]
            
            preview_card = dbc.Card([
                dbc.CardHeader("📋 Configuration Preview"),
                dbc.CardBody([
                    html.Ul([html.Li(item) for item in summary_items])
                ])
            ])
            
            # Add validation alerts
            alerts = []
            if validation_results:
                if validation_results.get('errors'):
                    alerts.append(
                        dbc.Alert([
                            html.H6("❌ Configuration Errors:"),
                            html.Ul([html.Li(error) for error in validation_results['errors']])
                        ], color="danger")
                    )
                
                if validation_results.get('warnings'):
                    alerts.append(
                        dbc.Alert([
                            html.H6("⚠️ Configuration Warnings:"),
                            html.Ul([html.Li(warning) for warning in validation_results['warnings']])
                        ], color="warning")
                    )
            
            return html.Div([preview_card] + alerts)
    
    def _save_configuration(self, config_data: Dict):
        """Save configuration to persistent storage"""
        try:
            # Save to JSON file
            config_file = 'trading_bot_config.json'
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            # Add to configuration history
            self.config_history.append({
                'timestamp': datetime.now().isoformat(),
                'config': config_data
            })
            
            # Keep only last 10 configurations
            if len(self.config_history) > 10:
                self.config_history = self.config_history[-10:]
            
            self.logger.info("✅ Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving configuration: {e}")
            raise

def create_customization_app():
    """Create Dash app with customization system"""
    
    # Initialize Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # Initialize customization system
    customization_system = DashboardCustomizationSystem(app)
    
    # Set up layout
    app.layout = customization_system.create_customization_layout()
    
    # Setup callbacks
    customization_system.setup_customization_callbacks()
    
    return app, customization_system

if __name__ == "__main__":
    # Create and run the customization dashboard
    app, customization_system = create_customization_app()
    
    print("🎛️ Starting Dashboard Customization System")
    print("📊 Features available:")
    print("   • Trading pairs selection and management")
    print("   • Timeframes configuration")
    print("   • Risk management parameters")
    print("   • AI/ML model settings")
    print("   • Technical indicators configuration")
    print("   • Portfolio management settings")
    print("   • Notifications and alerts")
    print("🌐 Dashboard will be available at http://localhost:8050")
    
    app.run_server(debug=True, host='0.0.0.0', port=8050) 