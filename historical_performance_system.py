#!/usr/bin/env python3
"""
📊 Historical Performance Tracking & Visualization System
Comprehensive performance analytics with advanced metrics including
Sharpe ratio, Sortino ratio, maximum drawdown, win rate, and more.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Individual trade record"""
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    commission: float
    pnl: float
    trade_id: str
    strategy: str = "default"
    confidence: float = 0.0
    duration_minutes: float = 0.0

@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a point in time"""
    timestamp: datetime
    total_value: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    daily_pnl: float
    drawdown: float

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # Basic metrics
    total_return: float
    annualized_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Risk metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    
    # Trade metrics
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    avg_trade_duration: float
    
    # Advanced metrics
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional Value at Risk 95%
    beta: float
    alpha: float
    information_ratio: float
    
    # Time-based metrics
    best_day: float
    worst_day: float
    positive_days: int
    negative_days: int
    
    # Benchmark comparison
    benchmark_return: float
    excess_return: float
    tracking_error: float

class HistoricalPerformanceSystem:
    """Comprehensive historical performance tracking and analysis system"""
    
    def __init__(self, db_path: str = "performance_history.db", 
                 initial_capital: float = 10000.0,
                 benchmark_symbol: str = "BTC"):
        self.db_path = db_path
        self.initial_capital = initial_capital
        self.benchmark_symbol = benchmark_symbol
        
        # Initialize database
        self._init_database()
        
        # Performance cache
        self.trades_cache = []
        self.portfolio_cache = []
        self.metrics_cache = None
        self.last_update = None
        
        logger.info(f"📊 Historical Performance System initialized with ${initial_capital:,.2f} initial capital")
    
    def _init_database(self):
        """Initialize SQLite database for performance tracking"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                commission REAL DEFAULT 0,
                pnl REAL NOT NULL,
                trade_id TEXT UNIQUE NOT NULL,
                strategy TEXT DEFAULT 'default',
                confidence REAL DEFAULT 0,
                duration_minutes REAL DEFAULT 0
            )
        ''')
        
        # Portfolio snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_value REAL NOT NULL,
                cash REAL NOT NULL,
                positions_value REAL NOT NULL,
                unrealized_pnl REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                daily_pnl REAL DEFAULT 0,
                drawdown REAL DEFAULT 0
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                period TEXT NOT NULL,
                metrics_json TEXT NOT NULL
            )
        ''')
        
        # Benchmark data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS benchmark_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                return_1d REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Performance database initialized")
    
    def add_trade(self, trade: Trade):
        """Add a trade to the performance tracking system"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO trades (
                    timestamp, symbol, side, quantity, price, commission,
                    pnl, trade_id, strategy, confidence, duration_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.timestamp.isoformat(),
                trade.symbol,
                trade.side,
                trade.quantity,
                trade.price,
                trade.commission,
                trade.pnl,
                trade.trade_id,
                trade.strategy,
                trade.confidence,
                trade.duration_minutes
            ))
            
            conn.commit()
            
            # Update cache
            self.trades_cache.append(trade)
            self._invalidate_cache()
            
            logger.info(f"✅ Trade added: {trade.symbol} {trade.side} {trade.quantity} @ {trade.price} (P&L: {trade.pnl:+.2f})")
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Trade {trade.trade_id} already exists")
        finally:
            conn.close()
    
    def add_portfolio_snapshot(self, snapshot: PortfolioSnapshot):
        """Add a portfolio snapshot"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO portfolio_snapshots (
                timestamp, total_value, cash, positions_value,
                unrealized_pnl, realized_pnl, daily_pnl, drawdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            snapshot.timestamp.isoformat(),
            snapshot.total_value,
            snapshot.cash,
            snapshot.positions_value,
            snapshot.unrealized_pnl,
            snapshot.realized_pnl,
            snapshot.daily_pnl,
            snapshot.drawdown
        ))
        
        conn.commit()
        conn.close()
        
        # Update cache
        self.portfolio_cache.append(snapshot)
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        """Invalidate performance metrics cache"""
        self.metrics_cache = None
        self.last_update = datetime.now()
    
    def get_trades(self, start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None,
                   symbol: Optional[str] = None) -> List[Trade]:
        """Get trades with optional filtering"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append(Trade(
                timestamp=datetime.fromisoformat(row[1]),
                symbol=row[2],
                side=row[3],
                quantity=row[4],
                price=row[5],
                commission=row[6],
                pnl=row[7],
                trade_id=row[8],
                strategy=row[9],
                confidence=row[10],
                duration_minutes=row[11]
            ))
        
        return trades
    
    def get_portfolio_snapshots(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots with optional filtering"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM portfolio_snapshots WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        snapshots = []
        for row in rows:
            snapshots.append(PortfolioSnapshot(
                timestamp=datetime.fromisoformat(row[1]),
                total_value=row[2],
                cash=row[3],
                positions_value=row[4],
                unrealized_pnl=row[5],
                realized_pnl=row[6],
                daily_pnl=row[7],
                drawdown=row[8]
            ))
        
        return snapshots
    
    def calculate_performance_metrics(self, start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        
        # Get data
        trades = self.get_trades(start_date, end_date)
        snapshots = self.get_portfolio_snapshots(start_date, end_date)
        
        if not trades and not snapshots:
            logger.warning("⚠️ No data available for performance calculation")
            return self._empty_metrics()
        
        # Convert to DataFrames for easier analysis
        trades_df = pd.DataFrame([asdict(trade) for trade in trades]) if trades else pd.DataFrame()
        snapshots_df = pd.DataFrame([asdict(snapshot) for snapshot in snapshots]) if snapshots else pd.DataFrame()
        
        # Basic trade metrics
        if not trades_df.empty:
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            losing_trades = len(trades_df[trades_df['pnl'] < 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 and losing_trades > 0 else 0
            expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
            avg_trade_duration = trades_df['duration_minutes'].mean()
        else:
            total_trades = winning_trades = losing_trades = 0
            win_rate = avg_win = avg_loss = profit_factor = expectancy = avg_trade_duration = 0
        
        # Portfolio-based metrics
        if not snapshots_df.empty:
            snapshots_df['timestamp'] = pd.to_datetime(snapshots_df['timestamp'])
            snapshots_df = snapshots_df.sort_values('timestamp')
            
            # Returns calculation
            snapshots_df['returns'] = snapshots_df['total_value'].pct_change()
            daily_returns = snapshots_df['returns'].dropna()
            
            # Basic return metrics
            total_return = (snapshots_df['total_value'].iloc[-1] - self.initial_capital) / self.initial_capital
            
            # Annualized return (assuming daily data)
            days = (snapshots_df['timestamp'].iloc[-1] - snapshots_df['timestamp'].iloc[0]).days
            annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 0 else 0
            
            # Risk metrics
            if len(daily_returns) > 1:
                volatility = daily_returns.std() * np.sqrt(365)
                
                # Sharpe ratio (assuming 2% risk-free rate)
                risk_free_rate = 0.02
                sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
                
                # Sortino ratio (downside deviation)
                downside_returns = daily_returns[daily_returns < 0]
                downside_deviation = downside_returns.std() * np.sqrt(365) if len(downside_returns) > 0 else 0
                sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
                
                # Maximum drawdown
                cumulative_returns = (1 + daily_returns).cumprod()
                rolling_max = cumulative_returns.expanding().max()
                drawdown_series = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = drawdown_series.min()
                
                # Calmar ratio
                calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
                
                # VaR and CVaR (95% confidence)
                var_95 = np.percentile(daily_returns, 5)
                cvar_95 = daily_returns[daily_returns <= var_95].mean()
                
                # Drawdown duration
                drawdown_periods = self._calculate_drawdown_periods(drawdown_series)
                max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
                
                # Daily performance metrics
                best_day = daily_returns.max()
                worst_day = daily_returns.min()
                positive_days = len(daily_returns[daily_returns > 0])
                negative_days = len(daily_returns[daily_returns < 0])
                
            else:
                volatility = sharpe_ratio = sortino_ratio = calmar_ratio = 0
                max_drawdown = var_95 = cvar_95 = 0
                max_drawdown_duration = 0
                best_day = worst_day = 0
                positive_days = negative_days = 0
        else:
            total_return = annualized_return = volatility = sharpe_ratio = sortino_ratio = 0
            calmar_ratio = max_drawdown = var_95 = cvar_95 = 0
            max_drawdown_duration = 0
            best_day = worst_day = 0
            positive_days = negative_days = 0
        
        # Benchmark comparison (placeholder - would need actual benchmark data)
        benchmark_return = 0.10  # Placeholder 10% benchmark return
        excess_return = annualized_return - benchmark_return
        tracking_error = volatility  # Simplified
        beta = 1.0  # Placeholder
        alpha = excess_return - (beta * (benchmark_return - 0.02))
        information_ratio = excess_return / tracking_error if tracking_error > 0 else 0
        
        return PerformanceMetrics(
            # Basic metrics
            total_return=total_return,
            annualized_return=annualized_return,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            
            # Risk metrics
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            
            # Trade metrics
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_trade_duration=avg_trade_duration,
            
            # Advanced metrics
            var_95=var_95,
            cvar_95=cvar_95,
            beta=beta,
            alpha=alpha,
            information_ratio=information_ratio,
            
            # Time-based metrics
            best_day=best_day,
            worst_day=worst_day,
            positive_days=positive_days,
            negative_days=negative_days,
            
            # Benchmark comparison
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            tracking_error=tracking_error
        )
    
    def _calculate_drawdown_periods(self, drawdown_series: pd.Series) -> List[int]:
        """Calculate drawdown periods in days"""
        
        periods = []
        current_period = 0
        in_drawdown = False
        
        for dd in drawdown_series:
            if dd < 0:
                if not in_drawdown:
                    in_drawdown = True
                    current_period = 1
                else:
                    current_period += 1
            else:
                if in_drawdown:
                    periods.append(current_period)
                    in_drawdown = False
                    current_period = 0
        
        # Handle case where we end in drawdown
        if in_drawdown:
            periods.append(current_period)
        
        return periods
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty performance metrics"""
        return PerformanceMetrics(
            total_return=0, annualized_return=0, total_trades=0, winning_trades=0,
            losing_trades=0, win_rate=0, volatility=0, sharpe_ratio=0, sortino_ratio=0,
            calmar_ratio=0, max_drawdown=0, max_drawdown_duration=0, avg_win=0,
            avg_loss=0, profit_factor=0, expectancy=0, avg_trade_duration=0,
            var_95=0, cvar_95=0, beta=0, alpha=0, information_ratio=0,
            best_day=0, worst_day=0, positive_days=0, negative_days=0,
            benchmark_return=0, excess_return=0, tracking_error=0
        )
    
    def create_performance_dashboard(self, start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> go.Figure:
        """Create comprehensive performance dashboard"""
        
        # Get data
        trades = self.get_trades(start_date, end_date)
        snapshots = self.get_portfolio_snapshots(start_date, end_date)
        metrics = self.calculate_performance_metrics(start_date, end_date)
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=2,
            subplot_titles=[
                'Portfolio Value Over Time', 'Daily Returns Distribution',
                'Cumulative Returns vs Benchmark', 'Drawdown Analysis',
                'Monthly Returns Heatmap', 'Trade Analysis',
                'Risk Metrics', 'Performance Summary'
            ],
            specs=[
                [{"colspan": 2}, None],
                [{"type": "scatter"}, {"type": "histogram"}],
                [{"type": "scatter"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "table"}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.1,
            row_heights=[0.3, 0.25, 0.25, 0.2]
        )
        
        if snapshots:
            # Portfolio value over time
            snapshots_df = pd.DataFrame([asdict(s) for s in snapshots])
            snapshots_df['timestamp'] = pd.to_datetime(snapshots_df['timestamp'])
            
            fig.add_trace(
                go.Scatter(
                    x=snapshots_df['timestamp'],
                    y=snapshots_df['total_value'],
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='#00ff88', width=2),
                    fill='tonexty'
                ),
                row=1, col=1
            )
            
            # Add initial capital line
            fig.add_hline(
                y=self.initial_capital,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Initial: ${self.initial_capital:,.0f}",
                row=1, col=1
            )
            
            # Daily returns
            snapshots_df['returns'] = snapshots_df['total_value'].pct_change()
            daily_returns = snapshots_df['returns'].dropna()
            
            if len(daily_returns) > 0:
                # Returns distribution
                fig.add_trace(
                    go.Histogram(
                        x=daily_returns * 100,
                        nbinsx=30,
                        name='Daily Returns %',
                        marker_color='rgba(0, 255, 136, 0.7)'
                    ),
                    row=2, col=2
                )
                
                # Cumulative returns
                cumulative_returns = (1 + daily_returns).cumprod()
                benchmark_returns = np.random.normal(0.0003, 0.02, len(daily_returns))  # Simulated benchmark
                benchmark_cumulative = (1 + pd.Series(benchmark_returns)).cumprod()
                
                fig.add_trace(
                    go.Scatter(
                        x=snapshots_df['timestamp'][1:],
                        y=cumulative_returns,
                        mode='lines',
                        name='Portfolio',
                        line=dict(color='#00ff88', width=2)
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=snapshots_df['timestamp'][1:],
                        y=benchmark_cumulative,
                        mode='lines',
                        name='Benchmark',
                        line=dict(color='#ff6b6b', width=2, dash='dash')
                    ),
                    row=2, col=1
                )
                
                # Drawdown analysis
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max * 100
                
                fig.add_trace(
                    go.Scatter(
                        x=snapshots_df['timestamp'][1:],
                        y=drawdown,
                        mode='lines',
                        name='Drawdown %',
                        line=dict(color='#ff4444', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(255, 68, 68, 0.3)'
                    ),
                    row=3, col=1
                )
        
        # Trade analysis
        if trades:
            trades_df = pd.DataFrame([asdict(trade) for trade in trades])
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
            
            # Monthly returns heatmap data
            trades_df['month'] = trades_df['timestamp'].dt.month
            trades_df['year'] = trades_df['timestamp'].dt.year
            monthly_pnl = trades_df.groupby(['year', 'month'])['pnl'].sum().reset_index()
            
            if len(monthly_pnl) > 0:
                # Create pivot table for heatmap
                heatmap_data = monthly_pnl.pivot(index='year', columns='month', values='pnl')
                
                fig.add_trace(
                    go.Heatmap(
                        z=heatmap_data.values,
                        x=[f'M{i}' for i in heatmap_data.columns],
                        y=heatmap_data.index,
                        colorscale='RdYlGn',
                        name='Monthly P&L'
                    ),
                    row=3, col=2
                )
        
        # Performance metrics table
        metrics_data = [
            ['Total Return', f'{metrics.total_return:.2%}'],
            ['Annualized Return', f'{metrics.annualized_return:.2%}'],
            ['Sharpe Ratio', f'{metrics.sharpe_ratio:.2f}'],
            ['Sortino Ratio', f'{metrics.sortino_ratio:.2f}'],
            ['Max Drawdown', f'{metrics.max_drawdown:.2%}'],
            ['Win Rate', f'{metrics.win_rate:.2%}'],
            ['Profit Factor', f'{metrics.profit_factor:.2f}'],
            ['Total Trades', f'{metrics.total_trades}']
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=['Metric', 'Value'], fill_color='paleturquoise'),
                cells=dict(values=list(zip(*metrics_data)), fill_color='lavender')
            ),
            row=4, col=2
        )
        
        # Risk metrics bar chart
        risk_metrics = ['Volatility', 'VaR 95%', 'CVaR 95%', 'Max DD']
        risk_values = [metrics.volatility * 100, metrics.var_95 * 100, 
                      metrics.cvar_95 * 100, abs(metrics.max_drawdown) * 100]
        
        fig.add_trace(
            go.Bar(
                x=risk_metrics,
                y=risk_values,
                name='Risk Metrics %',
                marker_color=['#ff6b6b', '#ffa500', '#ff4444', '#8b0000']
            ),
            row=4, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="📊 Comprehensive Performance Dashboard",
                x=0.5,
                font=dict(size=20)
            ),
            template="plotly_dark",
            height=1200,
            showlegend=True,
            font=dict(size=10)
        )
        
        return fig
    
    def create_detailed_metrics_chart(self, start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> go.Figure:
        """Create detailed metrics visualization"""
        
        metrics = self.calculate_performance_metrics(start_date, end_date)
        
        # Create subplots for different metric categories
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Return Metrics', 'Risk Metrics', 
                'Trade Metrics', 'Advanced Metrics'
            ],
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "indicator"}]
            ]
        )
        
        # Return metrics
        return_metrics = ['Total Return', 'Annualized Return', 'Excess Return']
        return_values = [metrics.total_return * 100, metrics.annualized_return * 100, 
                        metrics.excess_return * 100]
        return_colors = ['green' if v > 0 else 'red' for v in return_values]
        
        fig.add_trace(
            go.Bar(
                x=return_metrics,
                y=return_values,
                name='Return %',
                marker_color=return_colors,
                text=[f'{v:.1f}%' for v in return_values],
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # Risk metrics
        risk_metrics = ['Volatility', 'Max Drawdown', 'VaR 95%', 'CVaR 95%']
        risk_values = [metrics.volatility * 100, abs(metrics.max_drawdown) * 100,
                      abs(metrics.var_95) * 100, abs(metrics.cvar_95) * 100]
        
        fig.add_trace(
            go.Bar(
                x=risk_metrics,
                y=risk_values,
                name='Risk %',
                marker_color='red',
                text=[f'{v:.1f}%' for v in risk_values],
                textposition='auto'
            ),
            row=1, col=2
        )
        
        # Trade metrics
        trade_metrics = ['Win Rate', 'Profit Factor', 'Expectancy']
        trade_values = [metrics.win_rate * 100, metrics.profit_factor, metrics.expectancy]
        
        fig.add_trace(
            go.Bar(
                x=trade_metrics,
                y=trade_values,
                name='Trade Metrics',
                marker_color='blue',
                text=[f'{v:.1f}' for v in trade_values],
                textposition='auto'
            ),
            row=2, col=1
        )
        
        # Sharpe ratio indicator
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=metrics.sharpe_ratio,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Sharpe Ratio"},
                delta={'reference': 1.0},
                gauge={
                    'axis': {'range': [None, 3]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 1], 'color': "lightgray"},
                        {'range': [1, 2], 'color': "yellow"},
                        {'range': [2, 3], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 2.0
                    }
                }
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="📈 Detailed Performance Metrics",
            template="plotly_dark",
            height=800,
            showlegend=False
        )
        
        return fig
    
    def create_rolling_metrics_chart(self, window_days: int = 30,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> go.Figure:
        """Create rolling performance metrics chart"""
        
        snapshots = self.get_portfolio_snapshots(start_date, end_date)
        
        if not snapshots:
            return go.Figure().add_annotation(
                text="No portfolio data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
        
        # Convert to DataFrame
        df = pd.DataFrame([asdict(s) for s in snapshots])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate returns
        df['returns'] = df['total_value'].pct_change()
        
        # Rolling metrics
        df['rolling_return'] = df['returns'].rolling(window=window_days).mean() * 365
        df['rolling_volatility'] = df['returns'].rolling(window=window_days).std() * np.sqrt(365)
        df['rolling_sharpe'] = (df['rolling_return'] - 0.02) / df['rolling_volatility']
        
        # Rolling drawdown
        df['cumulative'] = (1 + df['returns']).cumprod()
        df['rolling_max'] = df['cumulative'].rolling(window=window_days).max()
        df['rolling_drawdown'] = (df['cumulative'] - df['rolling_max']) / df['rolling_max']
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            subplot_titles=[
                f'{window_days}-Day Rolling Return',
                f'{window_days}-Day Rolling Volatility', 
                f'{window_days}-Day Rolling Sharpe Ratio',
                f'{window_days}-Day Rolling Drawdown'
            ],
            vertical_spacing=0.05
        )
        
        # Rolling return
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rolling_return'] * 100,
                mode='lines',
                name='Rolling Return %',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
        
        # Rolling volatility
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rolling_volatility'] * 100,
                mode='lines',
                name='Rolling Volatility %',
                line=dict(color='orange', width=2)
            ),
            row=2, col=1
        )
        
        # Rolling Sharpe ratio
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rolling_sharpe'],
                mode='lines',
                name='Rolling Sharpe',
                line=dict(color='blue', width=2)
            ),
            row=3, col=1
        )
        
        # Add Sharpe ratio reference lines
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", 
                     annotation_text="Good (1.0)", row=3, col=1)
        fig.add_hline(y=2.0, line_dash="dash", line_color="green", 
                     annotation_text="Excellent (2.0)", row=3, col=1)
        
        # Rolling drawdown
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['rolling_drawdown'] * 100,
                mode='lines',
                name='Rolling Drawdown %',
                line=dict(color='red', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 0, 0, 0.3)'
            ),
            row=4, col=1
        )
        
        fig.update_layout(
            title=f"📊 {window_days}-Day Rolling Performance Metrics",
            template="plotly_dark",
            height=1000,
            showlegend=False
        )
        
        return fig
    
    def export_performance_report(self, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                format: str = 'json') -> str:
        """Export comprehensive performance report"""
        
        metrics = self.calculate_performance_metrics(start_date, end_date)
        trades = self.get_trades(start_date, end_date)
        snapshots = self.get_portfolio_snapshots(start_date, end_date)
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'performance_metrics': asdict(metrics),
            'summary': {
                'total_trades': len(trades),
                'total_snapshots': len(snapshots),
                'initial_capital': self.initial_capital,
                'final_value': snapshots[-1].total_value if snapshots else self.initial_capital
            }
        }
        
        if format.lower() == 'json':
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=4, default=str)
        
        return filename
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get quick performance summary"""
        
        metrics = self.calculate_performance_metrics()
        
        return {
            'total_return': f"{metrics.total_return:.2%}",
            'annualized_return': f"{metrics.annualized_return:.2%}",
            'sharpe_ratio': f"{metrics.sharpe_ratio:.2f}",
            'sortino_ratio': f"{metrics.sortino_ratio:.2f}",
            'max_drawdown': f"{metrics.max_drawdown:.2%}",
            'win_rate': f"{metrics.win_rate:.2%}",
            'total_trades': metrics.total_trades,
            'profit_factor': f"{metrics.profit_factor:.2f}",
            'volatility': f"{metrics.volatility:.2%}"
        }

def create_demo_data(performance_system: HistoricalPerformanceSystem, 
                    num_trades: int = 100, num_days: int = 30):
    """Create demo data for testing"""
    
    import random
    
    print(f"📊 Creating demo data: {num_trades} trades over {num_days} days")
    
    # Generate demo trades
    start_date = datetime.now() - timedelta(days=num_days)
    current_price = 45000  # Starting BTC price
    
    for i in range(num_trades):
        # Random trade timing
        trade_time = start_date + timedelta(
            days=random.randint(0, num_days),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Random price movement
        price_change = random.uniform(-0.05, 0.05)
        current_price *= (1 + price_change)
        
        # Random trade parameters
        side = random.choice(['buy', 'sell'])
        quantity = random.uniform(0.001, 0.01)
        
        # Simulate realistic P&L (70% win rate)
        if random.random() < 0.7:  # Winning trade
            pnl = random.uniform(10, 100)
        else:  # Losing trade
            pnl = random.uniform(-80, -10)
        
        trade = Trade(
            timestamp=trade_time,
            symbol='BTC/USDT',
            side=side,
            quantity=quantity,
            price=current_price,
            commission=quantity * current_price * 0.001,  # 0.1% commission
            pnl=pnl,
            trade_id=f"demo_trade_{i+1}",
            strategy="demo_strategy",
            confidence=random.uniform(0.6, 0.95),
            duration_minutes=random.uniform(5, 120)
        )
        
        performance_system.add_trade(trade)
    
    # Generate portfolio snapshots
    portfolio_value = performance_system.initial_capital
    
    for day in range(num_days + 1):
        snapshot_time = start_date + timedelta(days=day)
        
        # Daily portfolio change
        daily_change = random.uniform(-0.03, 0.04)  # -3% to +4% daily
        portfolio_value *= (1 + daily_change)
        
        # Calculate drawdown
        peak_value = max(performance_system.initial_capital, portfolio_value)
        drawdown = (portfolio_value - peak_value) / peak_value
        
        snapshot = PortfolioSnapshot(
            timestamp=snapshot_time,
            total_value=portfolio_value,
            cash=portfolio_value * 0.1,  # 10% cash
            positions_value=portfolio_value * 0.9,  # 90% in positions
            unrealized_pnl=random.uniform(-100, 100),
            realized_pnl=portfolio_value - performance_system.initial_capital,
            daily_pnl=portfolio_value * daily_change,
            drawdown=drawdown
        )
        
        performance_system.add_portfolio_snapshot(snapshot)
    
    print(f"✅ Demo data created successfully!")

if __name__ == "__main__":
    print("📊 HISTORICAL PERFORMANCE SYSTEM DEMO")
    print("=" * 60)
    
    # Initialize system
    performance_system = HistoricalPerformanceSystem(
        db_path="demo_performance.db",
        initial_capital=10000.0
    )
    
    # Create demo data
    create_demo_data(performance_system, num_trades=150, num_days=60)
    
    # Calculate metrics
    print("\n📈 Calculating Performance Metrics...")
    metrics = performance_system.calculate_performance_metrics()
    
    print(f"\n🎯 PERFORMANCE SUMMARY")
    print("-" * 40)
    print(f"📊 Total Return: {metrics.total_return:.2%}")
    print(f"📈 Annualized Return: {metrics.annualized_return:.2%}")
    print(f"⚡ Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"🛡️ Sortino Ratio: {metrics.sortino_ratio:.2f}")
    print(f"📉 Max Drawdown: {metrics.max_drawdown:.2%}")
    print(f"🎯 Win Rate: {metrics.win_rate:.2%}")
    print(f"💰 Profit Factor: {metrics.profit_factor:.2f}")
    print(f"📊 Total Trades: {metrics.total_trades}")
    print(f"📈 Volatility: {metrics.volatility:.2%}")
    print(f"⚠️ VaR 95%: {metrics.var_95:.2%}")
    print(f"🔥 CVaR 95%: {metrics.cvar_95:.2%}")
    
    # Create visualizations
    print(f"\n📊 Creating Performance Dashboard...")
    dashboard_fig = performance_system.create_performance_dashboard()
    dashboard_fig.write_html("performance_dashboard.html")
    
    print(f"📈 Creating Detailed Metrics Chart...")
    metrics_fig = performance_system.create_detailed_metrics_chart()
    metrics_fig.write_html("detailed_metrics.html")
    
    print(f"📊 Creating Rolling Metrics Chart...")
    rolling_fig = performance_system.create_rolling_metrics_chart(window_days=14)
    rolling_fig.write_html("rolling_metrics.html")
    
    # Export report
    print(f"\n📄 Exporting Performance Report...")
    report_file = performance_system.export_performance_report()
    
    print(f"\n✅ DEMO COMPLETED SUCCESSFULLY!")
    print(f"📁 Files created:")
    print(f"   • performance_dashboard.html")
    print(f"   • detailed_metrics.html") 
    print(f"   • rolling_metrics.html")
    print(f"   • {report_file}")
    print(f"   • demo_performance.db")
    
    print(f"\n🌟 Historical Performance System Ready!")
    print(f"   Open the HTML files in your browser to view the charts") 