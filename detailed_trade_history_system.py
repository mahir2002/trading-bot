#!/usr/bin/env python3
"""
📋 Detailed Trade History System
Comprehensive trade tracking with entry/exit points, P&L analysis, and trade reasoning.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict, field
import logging
from enum import Enum
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeStatus(Enum):
    """Trade status enumeration"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

class TradeType(Enum):
    """Trade type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"

class ExitReason(Enum):
    """Exit reason enumeration"""
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    MANUAL = "manual"
    SIGNAL_REVERSAL = "signal_reversal"
    TIME_LIMIT = "time_limit"
    RISK_MANAGEMENT = "risk_management"
    MARKET_CLOSE = "market_close"
    TRAILING_STOP = "trailing_stop"

@dataclass
class TradeEntry:
    """Trade entry details"""
    timestamp: datetime
    price: float
    quantity: float
    order_type: TradeType
    commission: float = 0.0
    slippage: float = 0.0
    market_conditions: Dict = field(default_factory=dict)

@dataclass
class TradeExit:
    """Trade exit details"""
    timestamp: datetime
    price: float
    quantity: float
    reason: ExitReason
    commission: float = 0.0
    slippage: float = 0.0
    market_conditions: Dict = field(default_factory=dict)

@dataclass
class TradingSignal:
    """Trading signal information"""
    signal_type: str
    confidence: float
    strength: float
    indicators: Dict = field(default_factory=dict)
    ai_prediction: Optional[float] = None
    technical_score: Optional[float] = None

@dataclass
class RiskMetrics:
    """Risk metrics for trade"""
    position_size_pct: float
    risk_reward_ratio: float
    max_risk_amount: float
    volatility: float
    correlation_risk: float = 0.0
    portfolio_heat: float = 0.0

@dataclass
class DetailedTrade:
    """Comprehensive trade record with full details"""
    # Basic trade info
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    status: TradeStatus
    
    # Entry details
    entry: TradeEntry
    
    # Exit details (optional for open trades)
    exit: Optional[TradeExit] = None
    
    # Strategy and reasoning
    strategy: str = "manual"
    reasoning: str = ""
    signal: Optional[TradingSignal] = None
    
    # Risk management
    risk_metrics: Optional[RiskMetrics] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    
    # Performance metrics
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    pnl_percentage: float = 0.0
    holding_duration: Optional[timedelta] = None
    
    # Market context
    market_context: Dict = field(default_factory=dict)
    
    # Notes and tags
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.exit and self.status == TradeStatus.OPEN:
            self.status = TradeStatus.CLOSED
            self.holding_duration = self.exit.timestamp - self.entry.timestamp
            self._calculate_pnl()
    
    def _calculate_pnl(self):
        """Calculate P&L for closed trades"""
        if self.exit:
            if self.side == 'buy':
                self.realized_pnl = (self.exit.price - self.entry.price) * self.entry.quantity
            else:  # sell
                self.realized_pnl = (self.entry.price - self.exit.price) * self.entry.quantity
            
            # Subtract commissions
            self.realized_pnl -= (self.entry.commission + self.exit.commission)
            
            # Calculate percentage
            cost_basis = self.entry.price * self.entry.quantity
            self.pnl_percentage = (self.realized_pnl / cost_basis) * 100 if cost_basis > 0 else 0

class DetailedTradeHistorySystem:
    """Comprehensive trade history tracking and analysis system"""
    
    def __init__(self, db_path: str = "detailed_trade_history.db"):
        self.db_path = db_path
        self.trades_cache = {}
        self.open_positions = {}
        
        # Initialize database
        self._init_database()
        
        logger.info("📋 Detailed Trade History System initialized")
    
    def _init_database(self):
        """Initialize SQLite database for detailed trade tracking"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detailed_trades (
                trade_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                status TEXT NOT NULL,
                strategy TEXT,
                reasoning TEXT,
                notes TEXT,
                tags TEXT,
                
                -- Entry details
                entry_timestamp TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_quantity REAL NOT NULL,
                entry_order_type TEXT,
                entry_commission REAL DEFAULT 0,
                entry_slippage REAL DEFAULT 0,
                
                -- Exit details
                exit_timestamp TEXT,
                exit_price REAL,
                exit_quantity REAL,
                exit_reason TEXT,
                exit_commission REAL DEFAULT 0,
                exit_slippage REAL DEFAULT 0,
                
                -- Risk management
                stop_loss_price REAL,
                take_profit_price REAL,
                position_size_pct REAL,
                risk_reward_ratio REAL,
                max_risk_amount REAL,
                
                -- Performance
                realized_pnl REAL DEFAULT 0,
                unrealized_pnl REAL DEFAULT 0,
                pnl_percentage REAL DEFAULT 0,
                holding_duration_seconds INTEGER,
                
                -- Signal data
                signal_type TEXT,
                signal_confidence REAL,
                signal_strength REAL,
                ai_prediction REAL,
                technical_score REAL,
                
                -- Market context
                market_conditions TEXT,
                volatility REAL,
                
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trade analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT,
                analysis_type TEXT,
                analysis_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES detailed_trades (trade_id)
            )
        ''')
        
        # Performance snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_trades INTEGER,
                open_trades INTEGER,
                closed_trades INTEGER,
                total_pnl REAL,
                win_rate REAL,
                avg_holding_time REAL,
                best_trade REAL,
                worst_trade REAL,
                snapshot_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Detailed trade history database initialized")
    
    def create_trade(self, symbol: str, side: str, entry_price: float, quantity: float,
                    strategy: str = "manual", reasoning: str = "", 
                    signal: Optional[TradingSignal] = None,
                    risk_metrics: Optional[RiskMetrics] = None,
                    stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None,
                    order_type: TradeType = TradeType.MARKET,
                    market_context: Dict = None) -> str:
        """Create a new detailed trade record"""
        
        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create entry record
        entry = TradeEntry(
            timestamp=datetime.now(),
            price=entry_price,
            quantity=quantity,
            order_type=order_type,
            commission=self._calculate_commission(entry_price * quantity),
            market_conditions=market_context or {}
        )
        
        # Create detailed trade
        trade = DetailedTrade(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            status=TradeStatus.OPEN,
            entry=entry,
            strategy=strategy,
            reasoning=reasoning,
            signal=signal,
            risk_metrics=risk_metrics,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            market_context=market_context or {}
        )
        
        # Store in database
        self._store_trade(trade)
        
        # Cache for quick access
        self.trades_cache[trade_id] = trade
        self.open_positions[trade_id] = trade
        
        logger.info(f"📝 Created trade: {trade_id} - {side.upper()} {quantity} {symbol} @ {entry_price}")
        
        return trade_id
    
    def close_trade(self, trade_id: str, exit_price: float, exit_reason: ExitReason,
                   exit_quantity: Optional[float] = None, notes: str = "") -> bool:
        """Close an existing trade"""
        
        if trade_id not in self.open_positions:
            logger.warning(f"⚠️ Trade {trade_id} not found in open positions")
            return False
        
        trade = self.open_positions[trade_id]
        
        # Create exit record
        exit_qty = exit_quantity or trade.entry.quantity
        exit = TradeExit(
            timestamp=datetime.now(),
            price=exit_price,
            quantity=exit_qty,
            reason=exit_reason,
            commission=self._calculate_commission(exit_price * exit_qty)
        )
        
        # Update trade
        trade.exit = exit
        trade.status = TradeStatus.CLOSED
        trade.notes += f" | {notes}" if notes else ""
        trade.holding_duration = exit.timestamp - trade.entry.timestamp
        trade._calculate_pnl()
        
        # Update database
        self._update_trade(trade)
        
        # Move from open to closed
        del self.open_positions[trade_id]
        self.trades_cache[trade_id] = trade
        
        logger.info(f"✅ Closed trade: {trade_id} - P&L: {trade.realized_pnl:+.2f} ({trade.pnl_percentage:+.2f}%)")
        
        return True
    
    def update_trade_reasoning(self, trade_id: str, reasoning: str, notes: str = ""):
        """Update trade reasoning and notes"""
        
        if trade_id in self.trades_cache:
            trade = self.trades_cache[trade_id]
            trade.reasoning = reasoning
            if notes:
                trade.notes += f" | {notes}"
            
            self._update_trade(trade)
            logger.info(f"📝 Updated reasoning for trade: {trade_id}")
    
    def add_trade_analysis(self, trade_id: str, analysis_type: str, analysis_data: Dict):
        """Add analysis data to a trade"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trade_analysis (trade_id, analysis_type, analysis_data)
            VALUES (?, ?, ?)
        ''', (trade_id, analysis_type, json.dumps(analysis_data)))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Added {analysis_type} analysis to trade: {trade_id}")
    
    def get_trade_details(self, trade_id: str) -> Optional[DetailedTrade]:
        """Get detailed information for a specific trade"""
        
        if trade_id in self.trades_cache:
            return self.trades_cache[trade_id]
        
        # Load from database
        trade = self._load_trade_from_db(trade_id)
        if trade:
            self.trades_cache[trade_id] = trade
        
        return trade
    
    def get_trades_by_criteria(self, symbol: Optional[str] = None,
                              strategy: Optional[str] = None,
                              status: Optional[TradeStatus] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              min_pnl: Optional[float] = None,
                              max_pnl: Optional[float] = None) -> List[DetailedTrade]:
        """Get trades matching specific criteria"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT trade_id FROM detailed_trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        if start_date:
            query += " AND entry_timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND entry_timestamp <= ?"
            params.append(end_date.isoformat())
        
        if min_pnl is not None:
            query += " AND realized_pnl >= ?"
            params.append(min_pnl)
        
        if max_pnl is not None:
            query += " AND realized_pnl <= ?"
            params.append(max_pnl)
        
        query += " ORDER BY entry_timestamp DESC"
        
        cursor.execute(query, params)
        trade_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Load trade details
        trades = []
        for trade_id in trade_ids:
            trade = self.get_trade_details(trade_id)
            if trade:
                trades.append(trade)
        
        return trades
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trade statistics"""
        
        all_trades = self.get_trades_by_criteria()
        closed_trades = [t for t in all_trades if t.status == TradeStatus.CLOSED]
        open_trades = [t for t in all_trades if t.status == TradeStatus.OPEN]
        
        if not closed_trades:
            return {"message": "No closed trades available for statistics"}
        
        # Basic statistics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.realized_pnl > 0]
        losing_trades = [t for t in closed_trades if t.realized_pnl < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # P&L statistics
        total_pnl = sum(t.realized_pnl for t in closed_trades)
        avg_win = np.mean([t.realized_pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.realized_pnl for t in losing_trades]) if losing_trades else 0
        
        best_trade = max(closed_trades, key=lambda t: t.realized_pnl) if closed_trades else None
        worst_trade = min(closed_trades, key=lambda t: t.realized_pnl) if closed_trades else None
        
        # Holding time statistics
        holding_times = [t.holding_duration.total_seconds() / 3600 for t in closed_trades if t.holding_duration]
        avg_holding_time = np.mean(holding_times) if holding_times else 0
        
        # Strategy breakdown
        strategy_stats = {}
        for trade in closed_trades:
            strategy = trade.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'count': 0, 'pnl': 0, 'wins': 0}
            
            strategy_stats[strategy]['count'] += 1
            strategy_stats[strategy]['pnl'] += trade.realized_pnl
            if trade.realized_pnl > 0:
                strategy_stats[strategy]['wins'] += 1
        
        # Calculate win rates for strategies
        for strategy in strategy_stats:
            stats = strategy_stats[strategy]
            stats['win_rate'] = stats['wins'] / stats['count'] if stats['count'] > 0 else 0
        
        # Exit reason analysis
        exit_reasons = {}
        for trade in closed_trades:
            if trade.exit:
                reason = trade.exit.reason.value
                if reason not in exit_reasons:
                    exit_reasons[reason] = {'count': 0, 'pnl': 0}
                exit_reasons[reason]['count'] += 1
                exit_reasons[reason]['pnl'] += trade.realized_pnl
        
        return {
            'total_trades': total_trades,
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if avg_loss != 0 and losing_trades else 0,
            'best_trade': {
                'id': best_trade.trade_id,
                'pnl': best_trade.realized_pnl,
                'symbol': best_trade.symbol,
                'strategy': best_trade.strategy
            } if best_trade else None,
            'worst_trade': {
                'id': worst_trade.trade_id,
                'pnl': worst_trade.realized_pnl,
                'symbol': worst_trade.symbol,
                'strategy': worst_trade.strategy
            } if worst_trade else None,
            'avg_holding_time_hours': avg_holding_time,
            'strategy_breakdown': strategy_stats,
            'exit_reasons': exit_reasons
        }
    
    def create_trade_history_visualization(self) -> go.Figure:
        """Create comprehensive trade history visualization"""
        
        trades = self.get_trades_by_criteria(status=TradeStatus.CLOSED)
        
        if not trades:
            fig = go.Figure()
            fig.add_annotation(text="No closed trades available", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=2,
            subplot_titles=[
                'Trade P&L Over Time', 'P&L Distribution',
                'Cumulative P&L', 'Win/Loss by Strategy',
                'Holding Time Analysis', 'Exit Reasons',
                'Trade Size Distribution', 'Performance Heatmap'
            ],
            specs=[
                [{"colspan": 2}, None],
                [{"type": "scatter"}, {"type": "histogram"}],
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "histogram"}, {"type": "heatmap"}]
            ],
            vertical_spacing=0.08
        )
        
        # Sort trades by entry time
        trades.sort(key=lambda t: t.entry.timestamp)
        
        # Trade P&L over time
        timestamps = [t.entry.timestamp for t in trades]
        pnl_values = [t.realized_pnl for t in trades]
        colors = ['green' if pnl > 0 else 'red' for pnl in pnl_values]
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=pnl_values,
                mode='markers+lines',
                name='Trade P&L',
                marker=dict(color=colors, size=8),
                line=dict(color='gray', width=1)
            ),
            row=1, col=1
        )
        
        # Cumulative P&L
        cumulative_pnl = np.cumsum(pnl_values)
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=cumulative_pnl,
                mode='lines',
                name='Cumulative P&L',
                line=dict(color='blue', width=3),
                fill='tonexty'
            ),
            row=2, col=1
        )
        
        # P&L distribution
        fig.add_trace(
            go.Histogram(
                x=pnl_values,
                nbinsx=20,
                name='P&L Distribution',
                marker_color='rgba(0, 100, 200, 0.7)'
            ),
            row=2, col=2
        )
        
        # Strategy performance
        strategy_stats = {}
        for trade in trades:
            strategy = trade.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            
            if trade.realized_pnl > 0:
                strategy_stats[strategy]['wins'] += 1
            else:
                strategy_stats[strategy]['losses'] += 1
            strategy_stats[strategy]['total_pnl'] += trade.realized_pnl
        
        strategies = list(strategy_stats.keys())
        wins = [strategy_stats[s]['wins'] for s in strategies]
        losses = [strategy_stats[s]['losses'] for s in strategies]
        
        fig.add_trace(
            go.Bar(x=strategies, y=wins, name='Wins', marker_color='green'),
            row=3, col=1
        )
        fig.add_trace(
            go.Bar(x=strategies, y=losses, name='Losses', marker_color='red'),
            row=3, col=1
        )
        
        # Exit reasons pie chart
        exit_reasons = {}
        for trade in trades:
            if trade.exit:
                reason = trade.exit.reason.value
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        fig.add_trace(
            go.Pie(
                labels=list(exit_reasons.keys()),
                values=list(exit_reasons.values()),
                name='Exit Reasons'
            ),
            row=3, col=2
        )
        
        # Holding time distribution
        holding_times = [t.holding_duration.total_seconds() / 3600 for t in trades if t.holding_duration]
        fig.add_trace(
            go.Histogram(
                x=holding_times,
                nbinsx=15,
                name='Holding Time (hours)',
                marker_color='rgba(200, 100, 0, 0.7)'
            ),
            row=4, col=1
        )
        
        # Performance heatmap by day of week and hour
        trade_data = []
        for trade in trades:
            trade_data.append({
                'day_of_week': trade.entry.timestamp.weekday(),
                'hour': trade.entry.timestamp.hour,
                'pnl': trade.realized_pnl
            })
        
        if trade_data:
            df = pd.DataFrame(trade_data)
            heatmap_data = df.groupby(['day_of_week', 'hour'])['pnl'].sum().unstack(fill_value=0)
            
            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data.values,
                    x=list(range(24)),
                    y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    colorscale='RdYlGn',
                    name='Performance Heatmap'
                ),
                row=4, col=2
            )
        
        fig.update_layout(
            title="📋 Comprehensive Trade History Analysis",
            template="plotly_dark",
            height=1200,
            showlegend=True
        )
        
        return fig
    
    def create_detailed_trade_table(self, limit: int = 50) -> go.Figure:
        """Create detailed trade table visualization"""
        
        trades = self.get_trades_by_criteria()[:limit]
        
        if not trades:
            fig = go.Figure()
            fig.add_annotation(text="No trades available", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Prepare table data
        table_data = {
            'Trade ID': [],
            'Symbol': [],
            'Side': [],
            'Entry Time': [],
            'Entry Price': [],
            'Exit Time': [],
            'Exit Price': [],
            'Quantity': [],
            'P&L': [],
            'P&L %': [],
            'Duration': [],
            'Strategy': [],
            'Exit Reason': [],
            'Reasoning': []
        }
        
        for trade in trades:
            table_data['Trade ID'].append(trade.trade_id[:12] + '...')
            table_data['Symbol'].append(trade.symbol)
            table_data['Side'].append(trade.side.upper())
            table_data['Entry Time'].append(trade.entry.timestamp.strftime('%Y-%m-%d %H:%M'))
            table_data['Entry Price'].append(f"${trade.entry.price:.4f}")
            
            if trade.exit:
                table_data['Exit Time'].append(trade.exit.timestamp.strftime('%Y-%m-%d %H:%M'))
                table_data['Exit Price'].append(f"${trade.exit.price:.4f}")
                table_data['Exit Reason'].append(trade.exit.reason.value.replace('_', ' ').title())
            else:
                table_data['Exit Time'].append('Open')
                table_data['Exit Price'].append('-')
                table_data['Exit Reason'].append('-')
            
            table_data['Quantity'].append(f"{trade.entry.quantity:.6f}")
            table_data['P&L'].append(f"${trade.realized_pnl:+.2f}")
            table_data['P&L %'].append(f"{trade.pnl_percentage:+.2f}%")
            
            if trade.holding_duration:
                hours = trade.holding_duration.total_seconds() / 3600
                table_data['Duration'].append(f"{hours:.1f}h")
            else:
                table_data['Duration'].append('-')
            
            table_data['Strategy'].append(trade.strategy)
            table_data['Reasoning'].append(trade.reasoning[:50] + '...' if len(trade.reasoning) > 50 else trade.reasoning)
        
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(table_data.keys()),
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12)
            ),
            cells=dict(
                values=list(table_data.values()),
                fill_color='lavender',
                align='left',
                font=dict(size=10)
            )
        )])
        
        fig.update_layout(
            title="📋 Detailed Trade History Table",
            template="plotly_dark",
            height=600
        )
        
        return fig
    
    def export_trade_history(self, format: str = 'csv', filename: Optional[str] = None) -> str:
        """Export trade history to file"""
        
        trades = self.get_trades_by_criteria()
        
        if not trades:
            logger.warning("No trades to export")
            return ""
        
        # Prepare export data
        export_data = []
        for trade in trades:
            row = {
                'trade_id': trade.trade_id,
                'symbol': trade.symbol,
                'side': trade.side,
                'status': trade.status.value,
                'strategy': trade.strategy,
                'reasoning': trade.reasoning,
                'entry_timestamp': trade.entry.timestamp.isoformat(),
                'entry_price': trade.entry.price,
                'entry_quantity': trade.entry.quantity,
                'entry_commission': trade.entry.commission,
                'stop_loss_price': trade.stop_loss_price,
                'take_profit_price': trade.take_profit_price,
                'realized_pnl': trade.realized_pnl,
                'pnl_percentage': trade.pnl_percentage,
                'notes': trade.notes
            }
            
            if trade.exit:
                row.update({
                    'exit_timestamp': trade.exit.timestamp.isoformat(),
                    'exit_price': trade.exit.price,
                    'exit_quantity': trade.exit.quantity,
                    'exit_reason': trade.exit.reason.value,
                    'exit_commission': trade.exit.commission,
                    'holding_duration_hours': trade.holding_duration.total_seconds() / 3600 if trade.holding_duration else 0
                })
            
            if trade.signal:
                row.update({
                    'signal_type': trade.signal.signal_type,
                    'signal_confidence': trade.signal.confidence,
                    'signal_strength': trade.signal.strength
                })
            
            export_data.append(row)
        
        # Export to file
        df = pd.DataFrame(export_data)
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trade_history_{timestamp}.{format}"
        
        if format.lower() == 'csv':
            df.to_csv(filename, index=False)
        elif format.lower() == 'json':
            df.to_json(filename, orient='records', indent=2)
        elif format.lower() == 'excel':
            df.to_excel(filename, index=False)
        
        logger.info(f"📁 Trade history exported to: {filename}")
        return filename
    
    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate commission for trade value"""
        return trade_value * 0.001  # 0.1% commission
    
    def _store_trade(self, trade: DetailedTrade):
        """Store trade in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare data
        entry_data = (
            trade.trade_id, trade.symbol, trade.side, trade.status.value,
            trade.strategy, trade.reasoning, trade.notes, json.dumps(trade.tags),
            trade.entry.timestamp.isoformat(), trade.entry.price, trade.entry.quantity,
            trade.entry.order_type.value, trade.entry.commission, trade.entry.slippage
        )
        
        # Add optional fields
        exit_data = (None, None, None, None, None, None) if not trade.exit else (
            trade.exit.timestamp.isoformat(), trade.exit.price, trade.exit.quantity,
            trade.exit.reason.value, trade.exit.commission, trade.exit.slippage
        )
        
        risk_data = (None, None, None, None) if not trade.risk_metrics else (
            trade.risk_metrics.position_size_pct, trade.risk_metrics.risk_reward_ratio,
            trade.risk_metrics.max_risk_amount, trade.risk_metrics.volatility
        )
        
        signal_data = (None, None, None, None, None) if not trade.signal else (
            trade.signal.signal_type, trade.signal.confidence, trade.signal.strength,
            trade.signal.ai_prediction, trade.signal.technical_score
        )
        
        all_data = entry_data + exit_data + (trade.stop_loss_price, trade.take_profit_price) + risk_data + (
            trade.realized_pnl, trade.unrealized_pnl, trade.pnl_percentage,
            trade.holding_duration.total_seconds() if trade.holding_duration else None
        ) + signal_data + (json.dumps(trade.market_context),)
        
        cursor.execute('''
            INSERT OR REPLACE INTO detailed_trades (
                trade_id, symbol, side, status, strategy, reasoning, notes, tags,
                entry_timestamp, entry_price, entry_quantity, entry_order_type, 
                entry_commission, entry_slippage,
                exit_timestamp, exit_price, exit_quantity, exit_reason, 
                exit_commission, exit_slippage,
                stop_loss_price, take_profit_price, position_size_pct, 
                risk_reward_ratio, max_risk_amount, volatility,
                realized_pnl, unrealized_pnl, pnl_percentage, holding_duration_seconds,
                signal_type, signal_confidence, signal_strength, ai_prediction, 
                technical_score, market_conditions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', all_data)
        
        conn.commit()
        conn.close()
    
    def _update_trade(self, trade: DetailedTrade):
        """Update existing trade in database"""
        self._store_trade(trade)  # Using REPLACE functionality
    
    def _load_trade_from_db(self, trade_id: str) -> Optional[DetailedTrade]:
        """Load trade from database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM detailed_trades WHERE trade_id = ?', (trade_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Reconstruct trade object (simplified for brevity)
        # In practice, you'd fully reconstruct all nested objects
        return None  # Placeholder - implement full reconstruction

def create_demo_detailed_trades(trade_system: DetailedTradeHistorySystem, num_trades: int = 20):
    """Create demo detailed trades for testing"""
    
    import random
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT']
    strategies = ['momentum', 'mean_reversion', 'breakout', 'ai_prediction']
    
    print(f"📋 Creating {num_trades} detailed demo trades...")
    
    for i in range(num_trades):
        symbol = random.choice(symbols)
        side = random.choice(['buy', 'sell'])
        strategy = random.choice(strategies)
        
        # Random entry details
        entry_price = random.uniform(30000, 50000) if 'BTC' in symbol else random.uniform(2000, 4000)
        quantity = random.uniform(0.001, 0.01)
        
        # Create signal
        signal = TradingSignal(
            signal_type=f"{strategy}_signal",
            confidence=random.uniform(0.6, 0.95),
            strength=random.uniform(0.5, 1.0),
            indicators={'rsi': random.uniform(30, 70), 'macd': random.uniform(-1, 1)}
        )
        
        # Create risk metrics
        risk_metrics = RiskMetrics(
            position_size_pct=random.uniform(1, 5),
            risk_reward_ratio=random.uniform(1.5, 3.0),
            max_risk_amount=random.uniform(100, 500),
            volatility=random.uniform(0.02, 0.08)
        )
        
        # Generate reasoning
        reasoning = f"Strong {strategy} signal detected with {signal.confidence:.1%} confidence. " \
                   f"RSI at {signal.indicators['rsi']:.1f}, favorable risk/reward ratio."
        
        # Create trade
        trade_id = trade_system.create_trade(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            strategy=strategy,
            reasoning=reasoning,
            signal=signal,
            risk_metrics=risk_metrics,
            stop_loss=entry_price * (0.95 if side == 'buy' else 1.05),
            take_profit=entry_price * (1.08 if side == 'buy' else 0.92)
        )
        
        # Randomly close some trades
        if random.random() < 0.7:  # 70% chance to close
            # Random exit price and reason
            price_change = random.uniform(-0.1, 0.15)
            exit_price = entry_price * (1 + price_change)
            
            exit_reasons = [ExitReason.TAKE_PROFIT, ExitReason.STOP_LOSS, 
                          ExitReason.SIGNAL_REVERSAL, ExitReason.MANUAL]
            exit_reason = random.choice(exit_reasons)
            
            # Wait a bit to simulate holding time
            import time
            time.sleep(0.1)
            
            trade_system.close_trade(
                trade_id=trade_id,
                exit_price=exit_price,
                exit_reason=exit_reason,
                notes=f"Closed due to {exit_reason.value.replace('_', ' ')}"
            )
    
    print(f"✅ Created {num_trades} detailed demo trades")

if __name__ == "__main__":
    print("📋 DETAILED TRADE HISTORY SYSTEM DEMO")
    print("=" * 60)
    
    # Initialize system
    trade_system = DetailedTradeHistorySystem("demo_detailed_trades.db")
    
    # Create demo trades
    create_demo_detailed_trades(trade_system, 25)
    
    # Get statistics
    print("\n📊 TRADE STATISTICS:")
    stats = trade_system.get_trade_statistics()
    
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Open Trades: {stats['open_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2%}")
    print(f"Total P&L: ${stats['total_pnl']:+.2f}")
    print(f"Profit Factor: {stats['profit_factor']:.2f}")
    print(f"Avg Holding Time: {stats['avg_holding_time_hours']:.1f} hours")
    
    if stats['best_trade']:
        print(f"Best Trade: {stats['best_trade']['id'][:12]}... (${stats['best_trade']['pnl']:+.2f})")
    
    if stats['worst_trade']:
        print(f"Worst Trade: {stats['worst_trade']['id'][:12]}... (${stats['worst_trade']['pnl']:+.2f})")
    
    # Strategy breakdown
    print(f"\n📈 STRATEGY BREAKDOWN:")
    for strategy, data in stats['strategy_breakdown'].items():
        print(f"  {strategy}: {data['count']} trades, {data['win_rate']:.2%} win rate, ${data['pnl']:+.2f} P&L")
    
    # Create visualizations
    print(f"\n📊 Creating visualizations...")
    
    # Trade history chart
    history_fig = trade_system.create_trade_history_visualization()
    history_fig.write_html("detailed_trade_history.html")
    
    # Trade table
    table_fig = trade_system.create_detailed_trade_table()
    table_fig.write_html("detailed_trade_table.html")
    
    # Export data
    print(f"\n📁 Exporting trade data...")
    csv_file = trade_system.export_trade_history('csv')
    json_file = trade_system.export_trade_history('json')
    
    print(f"\n✅ DEMO COMPLETED!")
    print(f"📁 Files created:")
    print(f"   • demo_detailed_trades.db")
    print(f"   • detailed_trade_history.html")
    print(f"   • detailed_trade_table.html")
    print(f"   • {csv_file}")
    print(f"   • {json_file}")
    
    print(f"\n🌟 Detailed Trade History System Ready!")
    print(f"   Open the HTML files to view comprehensive trade analysis") 