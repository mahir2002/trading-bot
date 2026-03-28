#!/usr/bin/env python3
"""
🚀 ULTIMATE CRYPTO SYSTEM 🚀
Comprehensive cryptocurrency data integration system combining:
- Binance (CEX data)
- CoinMarketCap (Market intelligence)
- DEX Screener (DEX trending data)

All in one unified, beautiful dashboard!
"""

import os
import sys
import time
import logging
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import our custom fetchers
from enhanced_crypto_fetcher import EnhancedCryptoFetcher
from dexscreener_fetcher import DEXScreenerFetcher

# Dash imports
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_crypto_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateCryptoSystem:
    """Ultimate cryptocurrency data system with multi-source integration"""
    
    def __init__(self):
        """Initialize the ultimate crypto system"""
        logger.info("🚀 Initializing Ultimate Crypto System...")
        
        # Initialize data fetchers
        self.enhanced_fetcher = EnhancedCryptoFetcher()
        self.dex_fetcher = DEXScreenerFetcher()
        
        # Data storage
        self.all_crypto_data = {}
        self.dex_trending_data = []
        self.market_overview = {}
        self.last_update = None
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                dbc.themes.CYBORG,
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
            ],
            suppress_callback_exceptions=True
        )
        
        self.setup_layout()
        self.setup_callbacks()
        
    def fetch_all_data(self) -> Dict:
        """Fetch data from all sources concurrently"""
        logger.info("📡 Fetching comprehensive crypto data from all sources...")
        start_time = time.time()
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all fetch operations
            futures = {
                executor.submit(self.enhanced_fetcher.get_comprehensive_crypto_data): 'enhanced',
                executor.submit(self.dex_fetcher.get_trending_tokens): 'dex_trending',
                executor.submit(self.dex_fetcher.get_popular_pairs): 'dex_popular'
            }
            
            # Collect results
            for future in as_completed(futures):
                source = futures[future]
                try:
                    result = future.result()
                    results[source] = result
                    logger.info(f"✅ Successfully fetched {source} data")
                except Exception as e:
                    logger.error(f"❌ Error fetching {source} data: {e}")
                    results[source] = None
        
        # Process and combine data
        self.process_combined_data(results)
        
        fetch_time = time.time() - start_time
        logger.info(f"🎯 Total data fetch completed in {fetch_time:.2f} seconds")
        
        return results
    
    def process_combined_data(self, results: Dict):
        """Process and combine data from all sources"""
        logger.info("🔄 Processing and combining data from all sources...")
        
        # Enhanced crypto data (Binance + CoinMarketCap)
        if results.get('enhanced'):
            enhanced_data = results['enhanced']
            self.all_crypto_data = enhanced_data.get('cryptocurrencies', {})
            self.market_overview = enhanced_data.get('market_overview', {})
            logger.info(f"📊 Loaded {len(self.all_crypto_data)} cryptocurrencies from CEX sources")
        
        # DEX trending data
        if results.get('dex_trending'):
            self.dex_trending_data = results['dex_trending']
            logger.info(f"🔥 Loaded {len(self.dex_trending_data)} trending DEX tokens")
        
        # DEX popular pairs
        if results.get('dex_popular'):
            dex_popular = results['dex_popular']
            logger.info(f"💎 Loaded {len(dex_popular)} popular DEX pairs")
            
            # Integrate DEX data into main crypto data
            for pair in dex_popular:
                symbol = pair.get('baseToken', {}).get('symbol', '').upper()
                if symbol and symbol not in self.all_crypto_data:
                    # Add DEX token to main data
                    self.all_crypto_data[symbol] = {
                        'symbol': symbol,
                        'name': pair.get('baseToken', {}).get('name', symbol),
                        'price': float(pair.get('priceUsd', 0)),
                        'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                        'market_cap': 0,  # Not available from DEX data
                        'source': 'DEX',
                        'dex_info': {
                            'dex': pair.get('dexId', ''),
                            'chain': pair.get('chainId', ''),
                            'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                            'pair_address': pair.get('pairAddress', ''),
                            'risk_level': self.calculate_risk_level(pair)
                        }
                    }
        
        self.last_update = datetime.now()
        total_tokens = len(self.all_crypto_data)
        dex_tokens = len([c for c in self.all_crypto_data.values() if c.get('source') == 'DEX'])
        cex_tokens = total_tokens - dex_tokens
        
        logger.info(f"🎯 Combined data processing complete:")
        logger.info(f"   📈 Total tokens: {total_tokens}")
        logger.info(f"   🏦 CEX tokens: {cex_tokens}")
        logger.info(f"   🔄 DEX tokens: {dex_tokens}")
        logger.info(f"   🔥 Trending DEX: {len(self.dex_trending_data)}")
    
    def calculate_risk_level(self, pair_data: Dict) -> str:
        """Calculate risk level for DEX tokens"""
        try:
            liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
            volume_24h = float(pair_data.get('volume', {}).get('h24', 0))
            
            if liquidity > 1000000 and volume_24h > 100000:
                return 'Low'
            elif liquidity > 100000 and volume_24h > 10000:
                return 'Medium'
            elif liquidity > 10000:
                return 'High'
            else:
                return 'Very High'
        except:
            return 'Unknown'
    
    def setup_layout(self):
        """Setup the dashboard layout"""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([
                            html.I(className="fas fa-rocket me-3"),
                            "Ultimate Crypto System",
                            html.Span(" 🚀", className="text-warning")
                        ], className="text-center mb-0"),
                        html.P("CEX + DEX + Market Intelligence", 
                               className="text-center text-muted mb-4"),
                        html.Hr()
                    ])
                ])
            ]),
            
            # Control Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button([
                                        html.I(className="fas fa-sync-alt me-2"),
                                        "Refresh All Data"
                                    ], id="refresh-btn", color="primary", size="lg")
                                ], width=4),
                                dbc.Col([
                                    dcc.Dropdown(
                                        id="source-filter",
                                        options=[
                                            {'label': '🌐 All Sources', 'value': 'all'},
                                            {'label': '🏦 CEX Only', 'value': 'cex'},
                                            {'label': '🔄 DEX Only', 'value': 'dex'},
                                            {'label': '🔥 Trending', 'value': 'trending'}
                                        ],
                                        value='all',
                                        className="mb-2"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dcc.Dropdown(
                                        id="category-filter",
                                        options=[
                                            {'label': '📊 All Categories', 'value': 'all'},
                                            {'label': '🏛️ DeFi', 'value': 'defi'},
                                            {'label': '🎮 Gaming', 'value': 'gaming'},
                                            {'label': '🤖 AI', 'value': 'ai'},
                                            {'label': '🐕 Meme', 'value': 'meme'},
                                            {'label': '⚡ Layer1', 'value': 'layer-1'},
                                            {'label': '🔗 Layer2', 'value': 'layer-2'}
                                        ],
                                        value='all'
                                    )
                                ], width=4)
                            ])
                        ])
                    ], className="mb-4")
                ])
            ]),
            
            # Market Overview
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4([
                                html.I(className="fas fa-chart-line me-2"),
                                "Market Overview"
                            ])
                        ]),
                        dbc.CardBody([
                            html.Div(id="market-overview")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Main Content Tabs
            dbc.Row([
                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab(label="📊 Market Data", tab_id="market-data"),
                        dbc.Tab(label="🔥 DEX Trending", tab_id="dex-trending"),
                        dbc.Tab(label="📈 Price Charts", tab_id="price-charts"),
                        dbc.Tab(label="🎯 Analytics", tab_id="analytics")
                    ], id="main-tabs", active_tab="market-data")
                ])
            ]),
            
            # Tab Content
            dbc.Row([
                dbc.Col([
                    html.Div(id="tab-content")
                ])
            ], className="mt-4"),
            
            # Footer
            html.Hr(className="mt-5"),
            dbc.Row([
                dbc.Col([
                    html.P([
                        "Last updated: ",
                        html.Span(id="last-update", className="text-info"),
                        " | Data sources: Binance, CoinMarketCap, DEX Screener"
                    ], className="text-center text-muted")
                ])
            ])
            
        ], fluid=True, className="py-4")
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output("market-overview", "children"),
             Output("tab-content", "children"),
             Output("last-update", "children")],
            [Input("refresh-btn", "n_clicks"),
             Input("main-tabs", "active_tab"),
             Input("source-filter", "value"),
             Input("category-filter", "value")],
            prevent_initial_call=False
        )
        def update_dashboard(n_clicks, active_tab, source_filter, category_filter):
            """Update dashboard content"""
            ctx = callback_context
            
            # Fetch data if refresh button clicked or initial load
            if not ctx.triggered or ctx.triggered[0]['prop_id'] == 'refresh-btn.n_clicks':
                self.fetch_all_data()
            
            # Generate market overview
            market_overview = self.generate_market_overview()
            
            # Generate tab content
            tab_content = self.generate_tab_content(active_tab, source_filter, category_filter)
            
            # Last update time
            last_update = self.last_update.strftime("%Y-%m-%d %H:%M:%S") if self.last_update else "Never"
            
            return market_overview, tab_content, last_update
    
    def generate_market_overview(self) -> html.Div:
        """Generate market overview cards"""
        if not self.market_overview:
            return html.Div("Loading market data...", className="text-center")
        
        total_tokens = len(self.all_crypto_data)
        dex_tokens = len([c for c in self.all_crypto_data.values() if c.get('source') == 'DEX'])
        cex_tokens = total_tokens - dex_tokens
        trending_count = len(self.dex_trending_data)
        
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{self.market_overview.get('total_cryptocurrencies', 0):,}", 
                               className="text-primary mb-0"),
                        html.P("Total Cryptocurrencies", className="text-muted mb-0"),
                        html.Small("CoinMarketCap", className="text-info")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"${self.market_overview.get('total_market_cap_usd', 0)/1e12:.2f}T", 
                               className="text-success mb-0"),
                        html.P("Total Market Cap", className="text-muted mb-0"),
                        html.Small("Global", className="text-info")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{total_tokens:,}", className="text-warning mb-0"),
                        html.P("Available Tokens", className="text-muted mb-0"),
                        html.Small("Our System", className="text-info")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{cex_tokens:,}", className="text-info mb-0"),
                        html.P("CEX Tokens", className="text-muted mb-0"),
                        html.Small("Binance + CMC", className="text-info")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{dex_tokens:,}", className="text-danger mb-0"),
                        html.P("DEX Tokens", className="text-muted mb-0"),
                        html.Small("DEX Screener", className="text-info")
                    ])
                ], className="text-center")
            ], width=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(f"{trending_count}", className="text-warning mb-0"),
                        html.P("Trending DEX", className="text-muted mb-0"),
                        html.Small("Hot Tokens", className="text-info")
                    ])
                ], className="text-center")
            ], width=2)
        ])
    
    def generate_tab_content(self, active_tab: str, source_filter: str, category_filter: str) -> html.Div:
        """Generate content for active tab"""
        if active_tab == "market-data":
            return self.generate_market_data_tab(source_filter, category_filter)
        elif active_tab == "dex-trending":
            return self.generate_dex_trending_tab()
        elif active_tab == "price-charts":
            return self.generate_price_charts_tab()
        elif active_tab == "analytics":
            return self.generate_analytics_tab()
        else:
            return html.Div("Tab content loading...")
    
    def generate_market_data_tab(self, source_filter: str, category_filter: str) -> html.Div:
        """Generate market data table"""
        if not self.all_crypto_data:
            return html.Div("No data available", className="text-center")
        
        # Filter data
        filtered_data = self.filter_crypto_data(source_filter, category_filter)
        
        if not filtered_data:
            return html.Div("No data matches the selected filters", className="text-center")
        
        # Create table data
        table_data = []
        for symbol, data in list(filtered_data.items())[:100]:  # Limit to top 100
            source_badge = "🏦 CEX" if data.get('source') != 'DEX' else "🔄 DEX"
            risk_badge = ""
            if data.get('dex_info'):
                risk_level = data['dex_info'].get('risk_level', 'Unknown')
                risk_colors = {'Low': '🟢', 'Medium': '🟡', 'High': '🟠', 'Very High': '🔴'}
                risk_badge = f" {risk_colors.get(risk_level, '⚪')} {risk_level}"
            
            table_data.append([
                f"{data.get('emoji', '💰')} {symbol}",
                data.get('name', symbol),
                f"${data.get('price', 0):.6f}",
                f"{data.get('price_change_24h', 0):.2f}%",
                f"${data.get('volume_24h', 0):,.0f}",
                f"${data.get('market_cap', 0):,.0f}" if data.get('market_cap') else "N/A",
                f"{source_badge}{risk_badge}"
            ])
        
        return dbc.Card([
            dbc.CardHeader([
                html.H5(f"📊 Market Data ({len(table_data)} tokens)")
            ]),
            dbc.CardBody([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Symbol"),
                            html.Th("Name"),
                            html.Th("Price"),
                            html.Th("24h Change"),
                            html.Th("24h Volume"),
                            html.Th("Market Cap"),
                            html.Th("Source")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([html.Td(cell) for cell in row])
                        for row in table_data
                    ])
                ], striped=True, hover=True, responsive=True, size="sm")
            ])
        ])
    
    def generate_dex_trending_tab(self) -> html.Div:
        """Generate DEX trending tokens tab"""
        if not self.dex_trending_data:
            return html.Div("No trending DEX data available", className="text-center")
        
        cards = []
        for token in self.dex_trending_data[:20]:  # Top 20 trending
            try:
                symbol = token.get('tokenSymbol', 'Unknown')
                name = token.get('tokenName', symbol)
                price = float(token.get('price', 0))
                change_24h = float(token.get('priceChange24h', 0))
                volume = float(token.get('volume24h', 0))
                chain = token.get('chainId', 'Unknown')
                
                change_color = "success" if change_24h >= 0 else "danger"
                change_icon = "fa-arrow-up" if change_24h >= 0 else "fa-arrow-down"
                
                card = dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"🔥 {symbol}", className="card-title"),
                            html.P(name, className="text-muted small"),
                            html.H6(f"${price:.8f}", className="text-info"),
                            html.P([
                                html.I(className=f"fas {change_icon} me-1"),
                                f"{change_24h:.2f}%"
                            ], className=f"text-{change_color} mb-2"),
                            html.Small([
                                f"Volume: ${volume:,.0f}",
                                html.Br(),
                                f"Chain: {chain}"
                            ], className="text-muted")
                        ])
                    ], className="h-100")
                ], width=3, className="mb-3")
                
                cards.append(card)
            except Exception as e:
                logger.error(f"Error processing trending token: {e}")
                continue
        
        return html.Div([
            html.H4("🔥 Trending DEX Tokens", className="mb-4"),
            dbc.Row(cards)
        ])
    
    def generate_price_charts_tab(self) -> html.Div:
        """Generate price charts tab"""
        if not self.all_crypto_data:
            return html.Div("No data for charts", className="text-center")
        
        # Get top tokens by volume
        top_tokens = sorted(
            [(k, v) for k, v in self.all_crypto_data.items() if v.get('volume_24h', 0) > 0],
            key=lambda x: x[1].get('volume_24h', 0),
            reverse=True
        )[:20]
        
        # Create price comparison chart
        symbols = [token[0] for token in top_tokens]
        prices = [token[1].get('price', 0) for token in top_tokens]
        changes = [token[1].get('price_change_24h', 0) for token in top_tokens]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Token Prices (USD)', '24h Price Changes (%)'),
            vertical_spacing=0.1
        )
        
        # Price chart
        fig.add_trace(
            go.Bar(x=symbols, y=prices, name="Price (USD)", marker_color='lightblue'),
            row=1, col=1
        )
        
        # Change chart
        colors = ['green' if x >= 0 else 'red' for x in changes]
        fig.add_trace(
            go.Bar(x=symbols, y=changes, name="24h Change (%)", marker_color=colors),
            row=2, col=1
        )
        
        fig.update_layout(
            height=800,
            showlegend=False,
            template="plotly_dark",
            title="Top 20 Tokens by Volume"
        )
        
        return dbc.Card([
            dbc.CardHeader([
                html.H5("📈 Price Charts")
            ]),
            dbc.CardBody([
                dcc.Graph(figure=fig)
            ])
        ])
    
    def generate_analytics_tab(self) -> html.Div:
        """Generate analytics tab"""
        if not self.all_crypto_data:
            return html.Div("No data for analytics", className="text-center")
        
        # Source distribution
        source_counts = {'CEX': 0, 'DEX': 0}
        for data in self.all_crypto_data.values():
            if data.get('source') == 'DEX':
                source_counts['DEX'] += 1
            else:
                source_counts['CEX'] += 1
        
        # Create pie chart
        fig_sources = go.Figure(data=[
            go.Pie(
                labels=list(source_counts.keys()),
                values=list(source_counts.values()),
                hole=0.3,
                marker_colors=['#1f77b4', '#ff7f0e']
            )
        ])
        fig_sources.update_layout(
            title="Data Source Distribution",
            template="plotly_dark"
        )
        
        # Volume distribution
        volume_ranges = {'< $1K': 0, '$1K - $10K': 0, '$10K - $100K': 0, '$100K - $1M': 0, '> $1M': 0}
        for data in self.all_crypto_data.values():
            volume = data.get('volume_24h', 0)
            if volume < 1000:
                volume_ranges['< $1K'] += 1
            elif volume < 10000:
                volume_ranges['$1K - $10K'] += 1
            elif volume < 100000:
                volume_ranges['$10K - $100K'] += 1
            elif volume < 1000000:
                volume_ranges['$100K - $1M'] += 1
            else:
                volume_ranges['> $1M'] += 1
        
        fig_volume = go.Figure(data=[
            go.Bar(
                x=list(volume_ranges.keys()),
                y=list(volume_ranges.values()),
                marker_color='lightgreen'
            )
        ])
        fig_volume.update_layout(
            title="24h Volume Distribution",
            template="plotly_dark",
            xaxis_title="Volume Range",
            yaxis_title="Number of Tokens"
        )
        
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_sources)
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_volume)
                    ])
                ])
            ], width=6)
        ])
    
    def filter_crypto_data(self, source_filter: str, category_filter: str) -> Dict:
        """Filter cryptocurrency data based on selected filters"""
        filtered_data = {}
        
        for symbol, data in self.all_crypto_data.items():
            # Source filter
            if source_filter == 'cex' and data.get('source') == 'DEX':
                continue
            elif source_filter == 'dex' and data.get('source') != 'DEX':
                continue
            elif source_filter == 'trending':
                # Only show tokens that are in trending DEX data
                if not any(t.get('tokenSymbol', '').upper() == symbol for t in self.dex_trending_data):
                    continue
            
            # Category filter (simplified - would need more sophisticated categorization)
            if category_filter != 'all':
                categories = data.get('categories', [])
                if category_filter not in [cat.lower() for cat in categories]:
                    continue
            
            filtered_data[symbol] = data
        
        return filtered_data
    
    def run(self, host='127.0.0.1', port=8051, debug=False):
        """Run the ultimate crypto system dashboard"""
        logger.info(f"🚀 Starting Ultimate Crypto System on http://{host}:{port}")
        logger.info("📊 Features: CEX + DEX + Market Intelligence")
        logger.info("🔄 Data Sources: Binance, CoinMarketCap, DEX Screener")
        
        # Initial data fetch
        self.fetch_all_data()
        
        # Run the app
        self.app.run_server(host=host, port=port, debug=debug)

def main():
    """Main function"""
    print("🚀 ULTIMATE CRYPTO SYSTEM 🚀")
    print("=" * 50)
    print("Comprehensive cryptocurrency data integration")
    print("CEX + DEX + Market Intelligence")
    print("=" * 50)
    
    try:
        system = UltimateCryptoSystem()
        system.run(host='0.0.0.0', port=8051, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Ultimate Crypto System stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running Ultimate Crypto System: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 