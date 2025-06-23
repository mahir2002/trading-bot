import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import ta
from typing import Dict, List, Optional, Tuple
import json
import os
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeAnnotation:
    """Trade annotation for chart overlay"""
    timestamp: datetime
    price: float
    side: str  # 'buy' or 'sell'
    amount: float
    profit_loss: float = 0.0
    symbol: str = ""
    trade_id: str = ""

class TradingViewChart:
    """
    TradingView-like charting functionality for crypto trading analysis
    """
    
    def __init__(self, exchange_id: str = 'binance'):
        """
        Initialize the charting system
        
        Args:
            exchange_id: Exchange to use for data (binance, coinbase, etc.)
        """
        self.exchange_id = exchange_id
        self.exchange = None
        self.data_cache = {}
        self.indicators_cache = {}
        
        # Initialize exchange
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'apiKey': os.getenv(f'{exchange_id.upper()}_API_KEY'),
                'secret': os.getenv(f'{exchange_id.upper()}_SECRET_KEY'),
                'sandbox': True,  # Use sandbox for testing
                'enableRateLimit': True,
            })
        except Exception as e:
            logger.warning(f"Could not initialize exchange {exchange_id}: {e}")
            # Use demo data if exchange fails
            self.exchange = None
    
    def fetch_ohlcv_data(self, symbol: str, timeframe: str = '1h', 
                        limit: int = 500, start_date: datetime = None) -> pd.DataFrame:
        """
        Fetch OHLCV data from exchange or generate demo data
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            start_date: Start date for historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        # Check cache first
        if cache_key in self.data_cache:
            cached_data, cache_time = self.data_cache[cache_key]
            if datetime.now() - cache_time < timedelta(minutes=1):
                return cached_data
        
        try:
            if self.exchange:
                # Fetch real data
                since = None
                if start_date:
                    since = int(start_date.timestamp() * 1000)
                
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('datetime', inplace=True)
                
            else:
                # Generate demo data
                df = self._generate_demo_data(symbol, timeframe, limit)
            
            # Cache the data
            self.data_cache[cache_key] = (df, datetime.now())
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            # Fallback to demo data
            return self._generate_demo_data(symbol, timeframe, limit)
    
    def _generate_demo_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Generate realistic demo OHLCV data"""
        # Base price for different symbols
        base_prices = {
            'BTC/USDT': 45000,
            'ETH/USDT': 3000,
            'ADA/USDT': 0.5,
            'SOL/USDT': 100,
            'DOGE/USDT': 0.08
        }
        
        base_price = base_prices.get(symbol, 45000)
        
        # Generate timestamps
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        
        minutes = timeframe_minutes.get(timeframe, 60)
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes * limit)
        
        timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{minutes}min')[:limit]
        
        # Generate realistic price data with trends and volatility
        np.random.seed(42)  # For reproducible demo data
        
        # Create price movements with trend and volatility
        returns = np.random.normal(0, 0.02, limit)  # 2% volatility
        trend = np.linspace(-0.1, 0.1, limit)  # Slight upward trend
        
        prices = [base_price]
        for i in range(1, limit):
            price_change = prices[-1] * (returns[i] + trend[i] * 0.01)
            new_price = prices[-1] + price_change
            prices.append(max(new_price, base_price * 0.5))  # Prevent negative prices
        
        # Generate OHLCV data
        data = []
        for i, timestamp in enumerate(timestamps):
            if i == 0:
                open_price = prices[i]
            else:
                open_price = data[-1]['close']
            
            close_price = prices[i]
            
            # Generate high and low with some randomness
            high_low_range = abs(close_price - open_price) * np.random.uniform(1.5, 3.0)
            high = max(open_price, close_price) + high_low_range * np.random.uniform(0, 0.5)
            low = min(open_price, close_price) - high_low_range * np.random.uniform(0, 0.5)
            
            # Generate volume
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2)
            })
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive technical indicators
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dictionary of technical indicators
        """
        indicators = {}
        
        try:
            # Moving Averages
            indicators['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            indicators['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            indicators['sma_200'] = ta.trend.sma_indicator(df['close'], window=200)
            indicators['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
            indicators['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            indicators['bb_upper'] = bb.bollinger_hband()
            indicators['bb_middle'] = bb.bollinger_mavg()
            indicators['bb_lower'] = bb.bollinger_lband()
            
            # RSI
            indicators['rsi'] = ta.momentum.rsi(df['close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            indicators['macd'] = macd.macd()
            indicators['macd_signal'] = macd.macd_signal()
            indicators['macd_histogram'] = macd.macd_diff()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            indicators['stoch_k'] = stoch.stoch()
            indicators['stoch_d'] = stoch.stoch_signal()
            
            # Volume indicators
            try:
                indicators['volume_sma'] = df['volume'].rolling(window=20).mean()
                indicators['vwap'] = ta.volume.volume_weighted_average_price(df['high'], df['low'], df['close'], df['volume'])
            except Exception as e:
                logger.warning(f"Volume indicators error: {e}")
                indicators['volume_sma'] = df['volume'].rolling(window=20).mean()
                # Simple VWAP calculation
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                indicators['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
            
            # Support and Resistance levels
            indicators['support'], indicators['resistance'] = self._calculate_support_resistance(df)
            
            # Fibonacci retracements
            indicators['fib_levels'] = self._calculate_fibonacci_levels(df)
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return indicators
    
    def _calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Tuple[pd.Series, pd.Series]:
        """Calculate dynamic support and resistance levels"""
        rolling_min = df['low'].rolling(window=window).min()
        rolling_max = df['high'].rolling(window=window).max()
        
        # Simple support/resistance based on rolling windows
        support = rolling_min.shift(window//2)
        resistance = rolling_max.shift(window//2)
        
        return support, resistance
    
    def _calculate_fibonacci_levels(self, df: pd.DataFrame, period: int = 50) -> Dict:
        """Calculate Fibonacci retracement levels"""
        if len(df) < period:
            return {}
        
        recent_data = df.tail(period)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        
        diff = high - low
        
        fib_levels = {
            '0%': high,
            '23.6%': high - 0.236 * diff,
            '38.2%': high - 0.382 * diff,
            '50%': high - 0.5 * diff,
            '61.8%': high - 0.618 * diff,
            '78.6%': high - 0.786 * diff,
            '100%': low
        }
        
        return fib_levels
    
    def create_candlestick_chart(self, symbol: str, timeframe: str = '1h', 
                               limit: int = 200, indicators: List[str] = None,
                               trades: List[TradeAnnotation] = None) -> go.Figure:
        """
        Create a comprehensive candlestick chart with indicators and trade overlays
        
        Args:
            symbol: Trading pair
            timeframe: Chart timeframe
            limit: Number of candles
            indicators: List of indicators to include
            trades: List of trade annotations
            
        Returns:
            Plotly figure object
        """
        # Fetch data
        df = self.fetch_ohlcv_data(symbol, timeframe, limit)
        
        if df.empty:
            return go.Figure().add_annotation(text="No data available", 
                                            xref="paper", yref="paper",
                                            x=0.5, y=0.5, showarrow=False)
        
        # Calculate indicators
        tech_indicators = self.calculate_technical_indicators(df)
        
        # Create subplots
        subplot_titles = ['Price Chart']
        rows = 1
        
        # Add subplot for volume
        if 'volume' in (indicators or []):
            subplot_titles.append('Volume')
            rows += 1
        
        # Add subplot for oscillators (RSI, Stochastic)
        oscillators = ['rsi', 'stoch_k', 'stoch_d']
        if any(osc in (indicators or []) for osc in oscillators):
            subplot_titles.append('Oscillators')
            rows += 1
        
        # Add subplot for MACD
        if any(ind in (indicators or []) for ind in ['macd', 'macd_signal', 'macd_histogram']):
            subplot_titles.append('MACD')
            rows += 1
        
        # Create figure with subplots
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=subplot_titles,
            row_heights=[0.6] + [0.4/(rows-1)]*(rows-1) if rows > 1 else [1.0]
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
                decreasing_line_color='#ff4444'
            ),
            row=1, col=1
        )
        
        # Add technical indicators to main chart
        current_row = 1
        
        if indicators:
            # Moving averages
            ma_indicators = ['sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26']
            colors = ['orange', 'blue', 'purple', 'cyan', 'magenta']
            
            for i, ma in enumerate(ma_indicators):
                if ma in indicators and ma in tech_indicators:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=tech_indicators[ma],
                            mode='lines',
                            name=ma.upper(),
                            line=dict(color=colors[i % len(colors)], width=1)
                        ),
                        row=1, col=1
                    )
            
            # Bollinger Bands
            if 'bollinger_bands' in indicators:
                if all(key in tech_indicators for key in ['bb_upper', 'bb_middle', 'bb_lower']):
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=tech_indicators['bb_upper'],
                            mode='lines',
                            name='BB Upper',
                            line=dict(color='gray', width=1),
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=tech_indicators['bb_lower'],
                            mode='lines',
                            name='BB Lower',
                            line=dict(color='gray', width=1),
                            fill='tonexty',
                            fillcolor='rgba(128,128,128,0.1)',
                            showlegend=False
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=tech_indicators['bb_middle'],
                            mode='lines',
                            name='BB Middle',
                            line=dict(color='gray', width=1, dash='dash')
                        ),
                        row=1, col=1
                    )
            
            # Support and Resistance
            if 'support_resistance' in indicators:
                if 'support' in tech_indicators and 'resistance' in tech_indicators:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=tech_indicators['support'],
                            mode='lines',
                            name='Support',
                            line=dict(color='green', width=1, dash='dot')
                        ),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=tech_indicators['resistance'],
                            mode='lines',
                            name='Resistance',
                            line=dict(color='red', width=1, dash='dot')
                        ),
                        row=1, col=1
                    )
            
            # Fibonacci levels
            if 'fibonacci' in indicators and 'fib_levels' in tech_indicators:
                fib_levels = tech_indicators['fib_levels']
                fib_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'red']
                
                for i, (level, price) in enumerate(fib_levels.items()):
                    fig.add_hline(
                        y=price,
                        line_dash="dash",
                        line_color=fib_colors[i % len(fib_colors)],
                        annotation_text=f"Fib {level}: {price:.2f}",
                        annotation_position="right",
                        row=1, col=1
                    )
        
        # Add trade annotations
        if trades:
            for trade in trades:
                color = 'green' if trade.side == 'buy' else 'red'
                symbol_marker = '▲' if trade.side == 'buy' else '▼'
                
                fig.add_trace(
                    go.Scatter(
                        x=[trade.timestamp],
                        y=[trade.price],
                        mode='markers+text',
                        marker=dict(
                            symbol='triangle-up' if trade.side == 'buy' else 'triangle-down',
                            size=15,
                            color=color
                        ),
                        text=[f"{symbol_marker} {trade.side.upper()}<br>${trade.price:.2f}"],
                        textposition="top center" if trade.side == 'buy' else "bottom center",
                        name=f"Trade {trade.trade_id}",
                        showlegend=False
                    ),
                    row=1, col=1
                )
        
        # Volume subplot
        if 'volume' in (indicators or []):
            current_row += 1
            colors = ['green' if close >= open else 'red' 
                     for close, open in zip(df['close'], df['open'])]
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=current_row, col=1
            )
            
            # Volume SMA
            if 'volume_sma' in tech_indicators:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=tech_indicators['volume_sma'],
                        mode='lines',
                        name='Volume SMA',
                        line=dict(color='orange', width=2)
                    ),
                    row=current_row, col=1
                )
        
        # Oscillators subplot
        if any(osc in (indicators or []) for osc in oscillators):
            current_row += 1
            
            if 'rsi' in indicators and 'rsi' in tech_indicators:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=tech_indicators['rsi'],
                        mode='lines',
                        name='RSI',
                        line=dict(color='purple', width=2)
                    ),
                    row=current_row, col=1
                )
                
                # RSI overbought/oversold lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", 
                             annotation_text="Overbought", row=current_row, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", 
                             annotation_text="Oversold", row=current_row, col=1)
            
            if 'stoch_k' in indicators and 'stoch_k' in tech_indicators:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=tech_indicators['stoch_k'],
                        mode='lines',
                        name='Stoch %K',
                        line=dict(color='blue', width=2)
                    ),
                    row=current_row, col=1
                )
            
            if 'stoch_d' in indicators and 'stoch_d' in tech_indicators:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=tech_indicators['stoch_d'],
                        mode='lines',
                        name='Stoch %D',
                        line=dict(color='orange', width=2)
                    ),
                    row=current_row, col=1
                )
        
        # MACD subplot
        if any(ind in (indicators or []) for ind in ['macd', 'macd_signal', 'macd_histogram']):
            current_row += 1
            
            if 'macd' in tech_indicators:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=tech_indicators['macd'],
                        mode='lines',
                        name='MACD',
                        line=dict(color='blue', width=2)
                    ),
                    row=current_row, col=1
                )
            
            if 'macd_signal' in tech_indicators:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=tech_indicators['macd_signal'],
                        mode='lines',
                        name='MACD Signal',
                        line=dict(color='red', width=2)
                    ),
                    row=current_row, col=1
                )
            
            if 'macd_histogram' in tech_indicators:
                colors = ['green' if val >= 0 else 'red' for val in tech_indicators['macd_histogram']]
                fig.add_trace(
                    go.Bar(
                        x=df.index,
                        y=tech_indicators['macd_histogram'],
                        name='MACD Histogram',
                        marker_color=colors,
                        opacity=0.7
                    ),
                    row=current_row, col=1
                )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - {timeframe} Chart",
            xaxis_title="Time",
            yaxis_title="Price",
            template="plotly_dark",
            height=800 if rows > 1 else 600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Remove rangeslider for cleaner look
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        return fig
    
    def create_performance_chart(self, trades: List[TradeAnnotation], 
                               initial_balance: float = 10000) -> go.Figure:
        """
        Create a performance analysis chart showing P&L over time
        
        Args:
            trades: List of trade annotations
            initial_balance: Starting balance
            
        Returns:
            Plotly figure with performance metrics
        """
        if not trades:
            return go.Figure().add_annotation(text="No trades available", 
                                            xref="paper", yref="paper",
                                            x=0.5, y=0.5, showarrow=False)
        
        # Calculate cumulative P&L
        cumulative_pnl = []
        balance = initial_balance
        timestamps = []
        
        for trade in sorted(trades, key=lambda x: x.timestamp):
            balance += trade.profit_loss
            cumulative_pnl.append(balance)
            timestamps.append(trade.timestamp)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=['Portfolio Value', 'Trade P&L', 'Drawdown'],
            row_heights=[0.5, 0.25, 0.25]
        )
        
        # Portfolio value over time
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=cumulative_pnl,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue', width=2),
                fill='tonexty'
            ),
            row=1, col=1
        )
        
        # Add initial balance line
        fig.add_hline(
            y=initial_balance,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Initial: ${initial_balance:,.2f}",
            row=1, col=1
        )
        
        # Individual trade P&L
        trade_pnl = [trade.profit_loss for trade in sorted(trades, key=lambda x: x.timestamp)]
        colors = ['green' if pnl >= 0 else 'red' for pnl in trade_pnl]
        
        fig.add_trace(
            go.Bar(
                x=timestamps,
                y=trade_pnl,
                name='Trade P&L',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Calculate and plot drawdown
        peak = cumulative_pnl[0]
        drawdowns = []
        
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak * 100
            drawdowns.append(drawdown)
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=drawdowns,
                mode='lines',
                name='Drawdown %',
                line=dict(color='red', width=2),
                fill='tozeroy',
                fillcolor='rgba(255,0,0,0.3)'
            ),
            row=3, col=1
        )
        
        # Update layout
        fig.update_layout(
            title="Trading Performance Analysis",
            template="plotly_dark",
            height=800,
            showlegend=True
        )
        
        # Add performance metrics as annotations
        total_return = (cumulative_pnl[-1] - initial_balance) / initial_balance * 100
        max_drawdown = min(drawdowns)
        win_rate = len([t for t in trades if t.profit_loss > 0]) / len(trades) * 100
        
        fig.add_annotation(
            text=f"Total Return: {total_return:.2f}%<br>"
                 f"Max Drawdown: {max_drawdown:.2f}%<br>"
                 f"Win Rate: {win_rate:.1f}%<br>"
                 f"Total Trades: {len(trades)}",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor="white",
            borderwidth=1
        )
        
        return fig
    
    def create_heatmap_analysis(self, trades: List[TradeAnnotation]) -> go.Figure:
        """
        Create a heatmap showing trading performance by time periods
        
        Args:
            trades: List of trade annotations
            
        Returns:
            Plotly figure with heatmap analysis
        """
        if not trades:
            return go.Figure().add_annotation(text="No trades available", 
                                            xref="paper", yref="paper",
                                            x=0.5, y=0.5, showarrow=False)
        
        # Create DataFrame from trades
        trade_data = []
        for trade in trades:
            trade_data.append({
                'timestamp': trade.timestamp,
                'hour': trade.timestamp.hour,
                'day_of_week': trade.timestamp.strftime('%A'),
                'profit_loss': trade.profit_loss
            })
        
        df = pd.DataFrame(trade_data)
        
        # Create hour vs day of week heatmap
        pivot_table = df.pivot_table(
            values='profit_loss',
            index='day_of_week',
            columns='hour',
            aggfunc='sum',
            fill_value=0
        )
        
        # Reorder days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex(day_order)
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='RdYlGn',
            zmid=0,
            text=pivot_table.values,
            texttemplate="%{text:.1f}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Trading Performance Heatmap (P&L by Hour and Day)",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week",
            template="plotly_dark",
            height=500
        )
        
        return fig
    
    def load_trades_from_file(self, file_path: str = 'logs/trades.json') -> List[TradeAnnotation]:
        """
        Load trades from JSON file and convert to TradeAnnotation objects
        
        Args:
            file_path: Path to trades JSON file
            
        Returns:
            List of TradeAnnotation objects
        """
        trades = []
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    trade_data = json.load(f)
                
                for trade in trade_data:
                    trades.append(TradeAnnotation(
                        timestamp=datetime.fromisoformat(trade.get('timestamp', datetime.now().isoformat())),
                        price=float(trade.get('price', 0)),
                        side=trade.get('side', 'buy'),
                        amount=float(trade.get('amount', 0)),
                        profit_loss=float(trade.get('profit_loss', 0)),
                        symbol=trade.get('symbol', ''),
                        trade_id=trade.get('id', str(len(trades)))
                    ))
        except Exception as e:
            logger.error(f"Error loading trades from file: {e}")
        
        return trades
    
    def save_chart_as_html(self, fig: go.Figure, filename: str):
        """
        Save chart as interactive HTML file
        
        Args:
            fig: Plotly figure
            filename: Output filename
        """
        try:
            fig.write_html(filename)
            logger.info(f"Chart saved as {filename}")
        except Exception as e:
            logger.error(f"Error saving chart: {e}")
    
    def get_market_overview(self, symbols: List[str] = None) -> go.Figure:
        """
        Create a market overview dashboard with multiple symbols
        
        Args:
            symbols: List of trading pairs to include
            
        Returns:
            Plotly figure with market overview
        """
        if not symbols:
            symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
        
        # Create subplots for each symbol
        rows = len(symbols)
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=symbols
        )
        
        for i, symbol in enumerate(symbols, 1):
            df = self.fetch_ohlcv_data(symbol, '1h', 100)
            
            if not df.empty:
                fig.add_trace(
                    go.Candlestick(
                        x=df.index,
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=symbol,
                        increasing_line_color='#00ff88',
                        decreasing_line_color='#ff4444'
                    ),
                    row=i, col=1
                )
        
        fig.update_layout(
            title="Market Overview",
            template="plotly_dark",
            height=200 * len(symbols),
            showlegend=False
        )
        
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        return fig

# Example usage and testing
if __name__ == '__main__':
    # Initialize charting system
    chart = TradingViewChart()
    
    # Create sample trades for demonstration
    sample_trades = [
        TradeAnnotation(
            timestamp=datetime.now() - timedelta(hours=10),
            price=45000,
            side='buy',
            amount=0.001,
            profit_loss=50,
            symbol='BTC/USDT',
            trade_id='1'
        ),
        TradeAnnotation(
            timestamp=datetime.now() - timedelta(hours=5),
            price=45500,
            side='sell',
            amount=0.001,
            profit_loss=-25,
            symbol='BTC/USDT',
            trade_id='2'
        )
    ]
    
    # Create charts
    print("Creating candlestick chart...")
    candlestick_fig = chart.create_candlestick_chart(
        'BTC/USDT',
        timeframe='1h',
        indicators=['sma_20', 'sma_50', 'bollinger_bands', 'volume', 'rsi', 'macd'],
        trades=sample_trades
    )
    
    print("Creating performance chart...")
    performance_fig = chart.create_performance_chart(sample_trades)
    
    print("Creating heatmap analysis...")
    heatmap_fig = chart.create_heatmap_analysis(sample_trades)
    
    print("Creating market overview...")
    overview_fig = chart.get_market_overview()
    
    # Save charts
    chart.save_chart_as_html(candlestick_fig, 'charts/btc_analysis.html')
    chart.save_chart_as_html(performance_fig, 'charts/performance_analysis.html')
    chart.save_chart_as_html(heatmap_fig, 'charts/heatmap_analysis.html')
    chart.save_chart_as_html(overview_fig, 'charts/market_overview.html')
    
    print("Charts created and saved successfully!") 