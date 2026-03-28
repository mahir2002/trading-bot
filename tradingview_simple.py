#!/usr/bin/env python3
"""
TradingView-Style Dashboard - Simplified Working Version
Professional trading interface that actually works
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta
from binance_testnet_client import BinanceTestnetClient

class SimpleTradingViewDashboard:
    def __init__(self, port=8053):
        self.port = port
        self.binance_client = BinanceTestnetClient()
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup simplified TradingView-style layout"""
        self.app.layout = html.Div([
            # Top Bar
            html.Div([
                html.H1("📈 TradingView Pro", style={
                    'color': '#ffffff', 'margin': '0', 'fontSize': '24px',
                    'display': 'inline-block', 'marginRight': '20px'
                }),
                html.Span("🟢 LIVE", style={
                    'backgroundColor': '#00ff88', 'color': '#000000', 
                    'padding': '6px 12px', 'borderRadius': '4px', 
                    'fontSize': '14px', 'fontWeight': 'bold'
                })
            ], style={
                'backgroundColor': '#1e222d', 'padding': '15px 25px',
                'borderBottom': '2px solid #2a2e39', 'display': 'flex',
                'alignItems': 'center', 'justifyContent': 'space-between'
            }),
            
            # Main Container
            html.Div([
                # Left Sidebar
                html.Div([
                    html.H3("Markets", style={
                        'color': '#ffffff', 'marginBottom': '20px', 'fontSize': '18px'
                    }),
                    
                    # Symbol Cards
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span("₿", style={'fontSize': '20px', 'marginRight': '10px'}),
                                html.Div([
                                    html.Div("BTC/USDT", style={
                                        'color': '#ffffff', 'fontSize': '16px', 'fontWeight': 'bold'
                                    }),
                                    html.Div(id='btc-sidebar-price', children="$0.00", style={
                                        'color': '#00ff88', 'fontSize': '14px'
                                    })
                                ])
                            ], style={'display': 'flex', 'alignItems': 'center'})
                        ], id='btc-card', style={
                            'backgroundColor': '#2a2e39', 'padding': '15px', 'borderRadius': '8px',
                            'marginBottom': '10px', 'cursor': 'pointer', 'border': '2px solid #0096ff'
                        }),
                        
                        html.Div([
                            html.Div([
                                html.Span("⟠", style={'fontSize': '20px', 'marginRight': '10px'}),
                                html.Div([
                                    html.Div("ETH/USDT", style={
                                        'color': '#ffffff', 'fontSize': '16px', 'fontWeight': 'bold'
                                    }),
                                    html.Div(id='eth-sidebar-price', children="$0.00", style={
                                        'color': '#00ff88', 'fontSize': '14px'
                                    })
                                ])
                            ], style={'display': 'flex', 'alignItems': 'center'})
                        ], id='eth-card', style={
                            'backgroundColor': '#2a2e39', 'padding': '15px', 'borderRadius': '8px',
                            'marginBottom': '10px', 'cursor': 'pointer'
                        }),
                        
                        html.Div([
                            html.Div([
                                html.Span("🔷", style={'fontSize': '20px', 'marginRight': '10px'}),
                                html.Div([
                                    html.Div("ADA/USDT", style={
                                        'color': '#ffffff', 'fontSize': '16px', 'fontWeight': 'bold'
                                    }),
                                    html.Div(id='ada-sidebar-price', children="$0.00", style={
                                        'color': '#00ff88', 'fontSize': '14px'
                                    })
                                ])
                            ], style={'display': 'flex', 'alignItems': 'center'})
                        ], id='ada-card', style={
                            'backgroundColor': '#2a2e39', 'padding': '15px', 'borderRadius': '8px',
                            'marginBottom': '10px', 'cursor': 'pointer'
                        }),
                        
                        html.Div([
                            html.Div([
                                html.Span("🌟", style={'fontSize': '20px', 'marginRight': '10px'}),
                                html.Div([
                                    html.Div("SOL/USDT", style={
                                        'color': '#ffffff', 'fontSize': '16px', 'fontWeight': 'bold'
                                    }),
                                    html.Div(id='sol-sidebar-price', children="$0.00", style={
                                        'color': '#00ff88', 'fontSize': '14px'
                                    })
                                ])
                            ], style={'display': 'flex', 'alignItems': 'center'})
                        ], id='sol-card', style={
                            'backgroundColor': '#2a2e39', 'padding': '15px', 'borderRadius': '8px',
                            'marginBottom': '10px', 'cursor': 'pointer'
                        })
                    ])
                ], style={
                    'width': '280px', 'backgroundColor': '#1e222d', 'padding': '20px',
                    'borderRight': '2px solid #2a2e39', 'height': 'calc(100vh - 80px)',
                    'overflowY': 'auto'
                }),
                
                # Main Chart Area
                html.Div([
                    # Chart Header
                    html.Div([
                        html.Div([
                            html.H2(id='main-symbol', children="BTC/USDT", style={
                                'color': '#ffffff', 'margin': '0', 'fontSize': '28px', 'fontWeight': 'bold'
                            }),
                            html.Div([
                                html.Span(id='main-price', children="$0.00", style={
                                    'color': '#00ff88', 'fontSize': '24px', 'fontWeight': 'bold',
                                    'marginRight': '20px'
                                }),
                                html.Span(id='main-change', children="+0.00%", style={
                                    'color': '#00ff88', 'fontSize': '18px'
                                })
                            ])
                        ]),
                        
                        # Timeframe Buttons
                        html.Div([
                            dcc.RadioItems(
                                id='timeframe-selector',
                                options=[
                                    {'label': '1m', 'value': '1m'},
                                    {'label': '5m', 'value': '5m'},
                                    {'label': '15m', 'value': '15m'},
                                    {'label': '1h', 'value': '1h'},
                                    {'label': '4h', 'value': '4h'},
                                    {'label': '1d', 'value': '1d'}
                                ],
                                value='1h',
                                inline=True,
                                style={'color': '#ffffff'}
                            )
                        ])
                    ], style={
                        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                        'padding': '20px 25px', 'borderBottom': '2px solid #2a2e39'
                    }),
                    
                    # Indicators Bar
                    html.Div([
                        dcc.Checklist(
                            id='indicators-selector',
                            options=[
                                {'label': ' Moving Averages', 'value': 'ma'},
                                {'label': ' RSI', 'value': 'rsi'},
                                {'label': ' MACD', 'value': 'macd'},
                                {'label': ' Bollinger Bands', 'value': 'bb'},
                                {'label': ' Volume', 'value': 'volume'}
                            ],
                            value=['ma', 'volume'],
                            inline=True,
                            style={'color': '#ffffff', 'fontSize': '14px'}
                        )
                    ], style={
                        'padding': '15px 25px', 'borderBottom': '1px solid #2a2e39',
                        'backgroundColor': '#1e222d'
                    }),
                    
                    # Main Chart
                    dcc.Graph(
                        id='tradingview-chart',
                        style={'height': 'calc(100vh - 250px)'},
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                        }
                    )
                ], style={'flex': '1', 'backgroundColor': '#131722'})
            ], style={'display': 'flex'}),
            
            # Hidden stores
            dcc.Store(id='current-symbol', data='BTCUSDT'),
            
            # Auto-refresh
            dcc.Interval(
                id='update-interval',
                interval=5*1000,  # 5 seconds
                n_intervals=0
            )
            
        ], style={
            'backgroundColor': '#131722', 'fontFamily': 'Arial, sans-serif',
            'margin': '0', 'padding': '0', 'height': '100vh'
        })
    
    def setup_callbacks(self):
        """Setup callbacks"""
        
        # Symbol selection
        @self.app.callback(
            Output('current-symbol', 'data'),
            [Input('btc-card', 'n_clicks'),
             Input('eth-card', 'n_clicks'),
             Input('ada-card', 'n_clicks'),
             Input('sol-card', 'n_clicks')],
            prevent_initial_call=True
        )
        def update_symbol(btc_clicks, eth_clicks, ada_clicks, sol_clicks):
            ctx = dash.callback_context
            if not ctx.triggered:
                return 'BTCUSDT'
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            symbol_map = {
                'btc-card': 'BTCUSDT',
                'eth-card': 'ETHUSDT',
                'ada-card': 'ADAUSDT',
                'sol-card': 'SOLUSDT'
            }
            return symbol_map.get(button_id, 'BTCUSDT')
        
        # Main chart update
        @self.app.callback(
            [Output('tradingview-chart', 'figure'),
             Output('main-symbol', 'children'),
             Output('main-price', 'children'),
             Output('main-change', 'children'),
             Output('main-change', 'style'),
             Output('btc-sidebar-price', 'children'),
             Output('eth-sidebar-price', 'children'),
             Output('ada-sidebar-price', 'children'),
             Output('sol-sidebar-price', 'children')],
            [Input('current-symbol', 'data'),
             Input('timeframe-selector', 'value'),
             Input('indicators-selector', 'value'),
             Input('update-interval', 'n_intervals')]
        )
        def update_dashboard(symbol, timeframe, indicators, n_intervals):
            try:
                print(f"🔄 Updating dashboard: {symbol} - {timeframe}")
                
                # Get market data
                df = self.binance_client.get_ohlcv_dataframe(symbol, timeframe, 200)
                
                if df.empty:
                    return self.create_empty_chart(), symbol, "$0.00", "+0.00%", {'color': '#00ff88'}, "$0.00", "$0.00", "$0.00", "$0.00"
                
                # Get all prices
                prices = {}
                for sym in ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']:
                    try:
                        ticker = self.binance_client.get_ticker_price(sym)
                        stats = self.binance_client.get_ticker_24hr(sym)
                        prices[sym] = {
                            'price': float(ticker['price']),
                            'change': float(stats['priceChangePercent'])
                        }
                    except:
                        prices[sym] = {'price': 0, 'change': 0}
                
                # Create chart
                fig = self.create_professional_chart(df, symbol, indicators or [])
                
                # Format main symbol data
                current_data = prices.get(symbol, {'price': 0, 'change': 0})
                main_price = f"${current_data['price']:,.2f}"
                change_pct = current_data['change']
                change_text = f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%"
                change_color = '#00ff88' if change_pct >= 0 else '#ff4444'
                
                # Format sidebar prices
                btc_price = f"${prices['BTCUSDT']['price']:,.0f}"
                eth_price = f"${prices['ETHUSDT']['price']:,.0f}"
                ada_price = f"${prices['ADAUSDT']['price']:.3f}"
                sol_price = f"${prices['SOLUSDT']['price']:,.0f}"
                
                symbol_display = symbol.replace('USDT', '/USDT')
                
                print(f"💰 {symbol}: {main_price} ({change_text})")
                
                return (fig, symbol_display, main_price, change_text, 
                       {'color': change_color, 'fontSize': '18px'},
                       btc_price, eth_price, ada_price, sol_price)
                
            except Exception as e:
                print(f"❌ Dashboard error: {e}")
                return self.create_empty_chart(), symbol, "$0.00", "+0.00%", {'color': '#00ff88'}, "$0.00", "$0.00", "$0.00", "$0.00"
    
    def create_professional_chart(self, df, symbol, indicators):
        """Create professional TradingView-style chart"""
        
        # Calculate subplot configuration
        subplot_count = 1
        row_heights = [0.7]
        subplot_titles = ['']
        
        if 'rsi' in indicators:
            subplot_count += 1
            row_heights.append(0.15)
            subplot_titles.append('RSI')
        
        if 'macd' in indicators:
            subplot_count += 1
            row_heights.append(0.15)
            subplot_titles.append('MACD')
        
        if 'volume' in indicators:
            subplot_count += 1
            row_heights = [h * 0.85 for h in row_heights] + [0.15]
            subplot_titles.append('Volume')
        
        # Create subplots
        fig = make_subplots(
            rows=subplot_count,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=row_heights,
            subplot_titles=subplot_titles
        )
        
        # Main candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=symbol,
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444',
                increasing_fillcolor='#00ff88',
                decreasing_fillcolor='#ff4444'
            ),
            row=1, col=1
        )
        
        # Add Moving Averages
        if 'ma' in indicators and len(df) >= 50:
            # EMA 20
            df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['ema20'], mode='lines', name='EMA 20',
                    line=dict(color='#ffaa00', width=2), opacity=0.8
                ),
                row=1, col=1
            )
            
            # EMA 50
            df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['ema50'], mode='lines', name='EMA 50',
                    line=dict(color='#0096ff', width=2), opacity=0.8
                ),
                row=1, col=1
            )
        
        # Add Bollinger Bands
        if 'bb' in indicators and len(df) >= 20:
            bb = ta.volatility.BollingerBands(df['close'], window=20)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['bb_upper'], mode='lines', name='BB Upper',
                    line=dict(color='#9c27b0', width=1), opacity=0.6
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['bb_lower'], mode='lines', name='BB Lower',
                    line=dict(color='#9c27b0', width=1), fill='tonexty',
                    fillcolor='rgba(156, 39, 176, 0.1)', opacity=0.6
                ),
                row=1, col=1
            )
        
        current_row = 2
        
        # Add RSI
        if 'rsi' in indicators and len(df) >= 14:
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['rsi'], mode='lines', name='RSI',
                    line=dict(color='#ff9800', width=2)
                ),
                row=current_row, col=1
            )
            
            # RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", opacity=0.5, row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", opacity=0.5, row=current_row, col=1)
            
            current_row += 1
        
        # Add MACD
        if 'macd' in indicators and len(df) >= 26:
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_histogram'] = macd.macd_diff()
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['macd'], mode='lines', name='MACD',
                    line=dict(color='#2196f3', width=2)
                ),
                row=current_row, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['macd_signal'], mode='lines', name='Signal',
                    line=dict(color='#ff5722', width=2)
                ),
                row=current_row, col=1
            )
            
            current_row += 1
        
        # Add Volume
        if 'volume' in indicators:
            colors = ['#00ff88' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ff4444' 
                     for i in range(len(df))]
            
            fig.add_trace(
                go.Bar(
                    x=df.index, y=df['volume'], name='Volume',
                    marker_color=colors, opacity=0.7
                ),
                row=current_row, col=1
            )
        
        # Update layout
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#131722',
            paper_bgcolor='#131722',
            font=dict(color='#d1d4dc', size=12),
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_rangeslider_visible=False
        )
        
        # Update axes
        for i in range(1, subplot_count + 1):
            fig.update_xaxes(
                gridcolor='#2a2e39', gridwidth=1, showgrid=True,
                zeroline=False, row=i, col=1
            )
            fig.update_yaxes(
                gridcolor='#2a2e39', gridwidth=1, showgrid=True,
                zeroline=False, side='right', row=i, col=1
            )
        
        return fig
    
    def create_empty_chart(self):
        """Create empty chart"""
        fig = go.Figure()
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#131722',
            paper_bgcolor='#131722',
            title="Loading Chart Data...",
            font=dict(color='#d1d4dc')
        )
        return fig
    
    def run(self, debug=False):
        """Run the dashboard"""
        print(f"🚀 Starting TradingView Dashboard on http://localhost:{self.port}")
        print("✨ Professional Features:")
        print("   • 📊 TradingView-style interface")
        print("   • 📈 Real-time candlestick charts")
        print("   • 📉 Technical indicators (EMA, RSI, MACD, BB)")
        print("   • 🎨 Professional dark theme")
        print("   • ⚡ Live price updates every 5 seconds")
        print("   • 🖱️ Interactive symbol selection")
        print(f"\n🌐 Open: http://localhost:{self.port}")
        print("⚡ Press Ctrl+C to stop")
        
        self.app.run_server(debug=debug, host='0.0.0.0', port=self.port)

if __name__ == '__main__':
    dashboard = SimpleTradingViewDashboard()
    dashboard.run() 