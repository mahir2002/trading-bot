#!/usr/bin/env python3
"""
Paper Trading Simulator
Simulates trading based on AI model predictions to track performance

Author: Trading Bot System
Date: 2025-01-22
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import sqlite3
from dataclasses import dataclass, asdict
import uuid

@dataclass
class Trade:
    """Represents a single trade"""
    id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: float = None
    quantity: float = 0.0
    entry_time: str = ""
    exit_time: str = ""
    pnl: float = 0.0
    pnl_percent: float = 0.0
    status: str = "OPEN"  # 'OPEN', 'CLOSED', 'CANCELLED'
    signal_confidence: float = 0.0
    fees: float = 0.0
    reason: str = ""

@dataclass
class Position:
    """Represents a current position"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    entry_time: str
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0

class PaperTradingSimulator:
    """Paper trading simulator with realistic trade execution"""
    
    def __init__(self, initial_balance: float = 10000.0, db_path: str = "data/paper_trading.db"):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Trading parameters
        self.max_position_size = 0.1  # 10% of balance per trade
        self.stop_loss_percent = 0.05  # 5% stop loss
        self.take_profit_percent = 0.15  # 15% take profit
        self.trading_fee = 0.001  # 0.1% trading fee
        self.min_confidence = 0.6  # Minimum signal confidence to trade
        
        # Tracking
        self.trades: List[Trade] = []
        self.positions: Dict[str, Position] = {}
        self.equity_history: List[Dict] = []
        
        # Initialize database
        self._init_database()
        
        # Load existing data
        self._load_existing_data()
    
    def _init_database(self):
        """Initialize SQLite database for trade tracking"""
        try:
            Path("data").mkdir(exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    quantity REAL,
                    entry_time TEXT,
                    exit_time TEXT,
                    pnl REAL,
                    pnl_percent REAL,
                    status TEXT,
                    signal_confidence REAL,
                    fees REAL,
                    reason TEXT
                )
            """)
            
            # Create positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    side TEXT,
                    quantity REAL,
                    entry_price REAL,
                    current_price REAL,
                    entry_time TEXT,
                    unrealized_pnl REAL,
                    unrealized_pnl_percent REAL
                )
            """)
            
            # Create equity history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equity_history (
                    timestamp TEXT,
                    balance REAL,
                    equity REAL,
                    open_positions INTEGER,
                    total_trades INTEGER,
                    win_rate REAL,
                    total_pnl REAL,
                    total_pnl_percent REAL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    def _load_existing_data(self):
        """Load existing trades and positions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Load trades
            trades_df = pd.read_sql_query("SELECT * FROM trades", conn)
            if not trades_df.empty:
                self.trades = [Trade(**row) for _, row in trades_df.iterrows()]
            
            # Load positions
            positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
            if not positions_df.empty:
                for _, row in positions_df.iterrows():
                    self.positions[row['symbol']] = Position(**row)
            
            # Load equity history
            equity_df = pd.read_sql_query("SELECT * FROM equity_history ORDER BY timestamp", conn)
            if not equity_df.empty:
                self.equity_history = equity_df.to_dict('records')
                # Update balance to latest
                if len(self.equity_history) > 0:
                    self.balance = self.equity_history[-1]['balance']
            
            conn.close()
            
            self.logger.info(f"📊 Loaded {len(self.trades)} trades, {len(self.positions)} positions")
            
        except Exception as e:
            self.logger.warning(f"Could not load existing data: {e}")
    
    async def process_signal(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading signal and execute trades"""
        try:
            symbol = prediction['symbol']
            signal = prediction['ensemble_signal']
            confidence = prediction['ensemble_confidence']
            current_price = prediction['current_price']
            
            # Skip if confidence is too low
            if confidence < self.min_confidence:
                return {
                    'action': 'SKIPPED',
                    'reason': f'Confidence too low ({confidence:.2f} < {self.min_confidence})',
                    'symbol': symbol
                }
            
            # Check if we already have a position
            existing_position = self.positions.get(symbol)
            
            if signal == 'BUY':
                if existing_position:
                    return {
                        'action': 'SKIPPED',
                        'reason': f'Already have position in {symbol}',
                        'symbol': symbol
                    }
                
                # Calculate position size
                position_value = self.balance * self.max_position_size
                quantity = position_value / current_price
                
                # Check if we have enough balance
                total_cost = quantity * current_price * (1 + self.trading_fee)
                if total_cost > self.balance:
                    return {
                        'action': 'SKIPPED',
                        'reason': f'Insufficient balance ({self.balance:.2f} < {total_cost:.2f})',
                        'symbol': symbol
                    }
                
                # Execute buy order
                return await self._execute_buy(symbol, current_price, quantity, confidence)
            
            elif signal == 'SELL':
                if not existing_position or existing_position.side != 'BUY':
                    return {
                        'action': 'SKIPPED',
                        'reason': f'No position to sell in {symbol}',
                        'symbol': symbol
                    }
                
                # Execute sell order
                return await self._execute_sell(symbol, current_price, existing_position, confidence)
            
            else:  # HOLD
                # Update position if exists
                if existing_position:
                    await self._update_position(symbol, current_price)
                
                return {
                    'action': 'HOLD',
                    'reason': f'AI signal: {signal}',
                    'symbol': symbol
                }
        
        except Exception as e:
            self.logger.error(f"Error processing signal for {symbol}: {e}")
            return {
                'action': 'ERROR',
                'reason': str(e),
                'symbol': symbol
            }
    
    async def _execute_buy(self, symbol: str, price: float, quantity: float, confidence: float) -> Dict[str, Any]:
        """Execute a buy order"""
        try:
            # Calculate costs
            total_cost = quantity * price
            fee = total_cost * self.trading_fee
            total_with_fee = total_cost + fee
            
            # Update balance
            self.balance -= total_with_fee
            
            # Create trade record
            trade = Trade(
                id=str(uuid.uuid4()),
                symbol=symbol,
                side='BUY',
                entry_price=price,
                quantity=quantity,
                entry_time=datetime.now().isoformat(),
                signal_confidence=confidence,
                fees=fee,
                reason=f'AI BUY signal (confidence: {confidence:.2f})'
            )
            
            # Create position
            position = Position(
                symbol=symbol,
                side='BUY',
                quantity=quantity,
                entry_price=price,
                current_price=price,
                entry_time=datetime.now().isoformat()
            )
            
            # Store in memory
            self.trades.append(trade)
            self.positions[symbol] = position
            
            # Save to database
            await self._save_trade(trade)
            await self._save_position(position)
            await self._update_equity_history()
            
            self.logger.info(f"�� BUY {symbol} at ${price:.4f} (qty: {quantity:.6f}, confidence: {confidence:.2f})")
            
            return {
                'action': 'BUY',
                'symbol': symbol,
                'price': price,
                'quantity': quantity,
                'total_cost': total_with_fee,
                'fee': fee,
                'confidence': confidence,
                'new_balance': self.balance
            }
            
        except Exception as e:
            self.logger.error(f"Error executing buy for {symbol}: {e}")
            return {
                'action': 'ERROR',
                'reason': str(e),
                'symbol': symbol
            }
    
    async def _execute_sell(self, symbol: str, price: float, position: Position, confidence: float) -> Dict[str, Any]:
        """Execute a sell order"""
        try:
            # Calculate proceeds
            total_proceeds = position.quantity * price
            fee = total_proceeds * self.trading_fee
            net_proceeds = total_proceeds - fee
            
            # Calculate P&L
            entry_cost = position.quantity * position.entry_price
            pnl = net_proceeds - entry_cost
            pnl_percent = (pnl / entry_cost) * 100
            
            # Update balance
            self.balance += net_proceeds
            
            # Find and update the corresponding trade
            trade = None
            for t in self.trades:
                if t.symbol == symbol and t.status == 'OPEN':
                    t.exit_price = price
                    t.exit_time = datetime.now().isoformat()
                    t.pnl = pnl
                    t.pnl_percent = pnl_percent
                    t.status = 'CLOSED'
                    t.fees += fee
                    t.reason += f' | SELL signal (confidence: {confidence:.2f})'
                    trade = t
                    break
            
            # Remove position
            if symbol in self.positions:
                del self.positions[symbol]
            
            # Save to database
            if trade:
                await self._save_trade(trade)
            await self._remove_position(symbol)
            await self._update_equity_history()
            
            self.logger.info(f"📉 SELL {symbol} at ${price:.4f} (P&L: ${pnl:.2f}, {pnl_percent:.1f}%)")
            
            return {
                'action': 'SELL',
                'symbol': symbol,
                'price': price,
                'quantity': position.quantity,
                'total_proceeds': net_proceeds,
                'fee': fee,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'confidence': confidence,
                'new_balance': self.balance
            }
            
        except Exception as e:
            self.logger.error(f"Error executing sell for {symbol}: {e}")
            return {
                'action': 'ERROR',
                'reason': str(e),
                'symbol': symbol
            }
    
    async def _update_position(self, symbol: str, current_price: float):
        """Update position with current price"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position.current_price = current_price
        
        # Calculate unrealized P&L
        if position.side == 'BUY':
            entry_cost = position.quantity * position.entry_price
            current_value = position.quantity * current_price
            position.unrealized_pnl = current_value - entry_cost
            position.unrealized_pnl_percent = (position.unrealized_pnl / entry_cost) * 100
        
        await self._save_position(position)
    
    async def _save_trade(self, trade: Trade):
        """Save trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.id, trade.symbol, trade.side, trade.entry_price, trade.exit_price,
                trade.quantity, trade.entry_time, trade.exit_time, trade.pnl,
                trade.pnl_percent, trade.status, trade.signal_confidence, trade.fees, trade.reason
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving trade: {e}")
    
    async def _save_position(self, position: Position):
        """Save position to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO positions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position.symbol, position.side, position.quantity, position.entry_price,
                position.current_price, position.entry_time, position.unrealized_pnl,
                position.unrealized_pnl_percent
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving position: {e}")
    
    async def _remove_position(self, symbol: str):
        """Remove position from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error removing position: {e}")
    
    async def _update_equity_history(self):
        """Update equity history with current status"""
        try:
            # Calculate current equity
            equity = self.balance
            for position in self.positions.values():
                equity += position.quantity * position.current_price
            
            # Calculate statistics
            closed_trades = [t for t in self.trades if t.status == 'CLOSED']
            winning_trades = len([t for t in closed_trades if t.pnl > 0])
            win_rate = (winning_trades / len(closed_trades)) * 100 if closed_trades else 0
            total_pnl = sum(t.pnl for t in closed_trades)
            total_pnl_percent = ((equity - self.initial_balance) / self.initial_balance) * 100
            
            equity_record = {
                'timestamp': datetime.now().isoformat(),
                'balance': self.balance,
                'equity': equity,
                'open_positions': len(self.positions),
                'total_trades': len(closed_trades),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent
            }
            
            self.equity_history.append(equity_record)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO equity_history VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(equity_record.values()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating equity history: {e}")
    
    async def process_multiple_signals(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple trading signals"""
        results = {}
        
        self.logger.info(f"💼 Processing {len(predictions)} trading signals...")
        
        for symbol, prediction in predictions.items():
            if 'error' not in prediction:
                result = await self.process_signal(prediction)
                results[symbol] = result
                await asyncio.sleep(0.1)  # Small delay between trades
            else:
                results[symbol] = {
                    'action': 'ERROR',
                    'reason': prediction['error'],
                    'symbol': symbol
                }
        
        # Generate summary
        actions = [r['action'] for r in results.values()]
        summary = {
            'total_signals': len(predictions),
            'actions': {
                'BUY': actions.count('BUY'),
                'SELL': actions.count('SELL'),
                'HOLD': actions.count('HOLD'),
                'SKIPPED': actions.count('SKIPPED'),
                'ERROR': actions.count('ERROR')
            },
            'current_balance': self.balance,
            'open_positions': len(self.positions),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"✅ Trading session complete: {summary['actions']}")
        
        return summary
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            # Calculate current equity
            equity = self.balance
            for position in self.positions.values():
                equity += position.quantity * position.current_price
            
            # Analyze trades
            closed_trades = [t for t in self.trades if t.status == 'CLOSED']
            winning_trades = [t for t in closed_trades if t.pnl > 0]
            losing_trades = [t for t in closed_trades if t.pnl < 0]
            
            # Calculate metrics
            total_pnl = sum(t.pnl for t in closed_trades)
            total_pnl_percent = ((equity - self.initial_balance) / self.initial_balance) * 100
            win_rate = (len(winning_trades) / len(closed_trades)) * 100 if closed_trades else 0
            
            avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
            profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades else float('inf')
            
            # Current positions summary
            positions_summary = []
            for symbol, pos in self.positions.items():
                positions_summary.append({
                    'symbol': symbol,
                    'side': pos.side,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_percent': pos.unrealized_pnl_percent
                })
            
            return {
                'initial_balance': self.initial_balance,
                'current_balance': self.balance,
                'current_equity': equity,
                'total_pnl': total_pnl,
                'total_pnl_percent': total_pnl_percent,
                'total_trades': len(closed_trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'open_positions': len(self.positions),
                'positions': positions_summary,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            return {'error': str(e)}

async def main():
    """Test the paper trading simulator"""
    logging.basicConfig(level=logging.INFO)
    
    simulator = PaperTradingSimulator(initial_balance=10000.0)
    
    print("💼 Testing Paper Trading Simulator...")
    
    # Generate demo predictions
    demo_predictions = {
        'DEMO1': {
            'symbol': 'DEMO1',
            'ensemble_signal': 'BUY',
            'ensemble_confidence': 0.85,
            'current_price': 125.50
        },
        'DEMO2': {
            'symbol': 'DEMO2',
            'ensemble_signal': 'HOLD',
            'ensemble_confidence': 0.45,
            'current_price': 67.25
        },
        'DEMO3': {
            'symbol': 'DEMO3',
            'ensemble_signal': 'BUY',
            'ensemble_confidence': 0.78,
            'current_price': 89.10
        },
        'BTC': {
            'symbol': 'BTC',
            'ensemble_signal': 'SELL',
            'ensemble_confidence': 0.82,
            'current_price': 45000.00
        }
    }
    
    # Process signals
    print("\n🔄 Processing trading signals...")
    results = await simulator.process_multiple_signals(demo_predictions)
    
    print(f"\n📊 Trading Results:")
    print(f"   Actions: {results['actions']}")
    print(f"   Balance: ${results['current_balance']:.2f}")
    print(f"   Open Positions: {results['open_positions']}")
    
    # Show performance summary
    print("\n📈 Performance Summary:")
    performance = simulator.get_performance_summary()
    
    print(f"   Initial Balance: ${performance['initial_balance']:.2f}")
    print(f"   Current Equity: ${performance['current_equity']:.2f}")
    print(f"   Total P&L: ${performance['total_pnl']:.2f} ({performance['total_pnl_percent']:.1f}%)")
    print(f"   Win Rate: {performance['win_rate']:.1f}%")
    print(f"   Open Positions: {performance['open_positions']}")

if __name__ == "__main__":
    asyncio.run(main())
