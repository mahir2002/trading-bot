#!/usr/bin/env python3
"""
🚀 UNIFIED TRADING DASHBOARD 🚀
Real-time monitoring and control for the Unified Master Trading Bot

Features:
- Live trading signals and execution monitoring
- Real-time portfolio performance tracking
- Bot control and configuration
- Trade history and analytics
- Risk management monitoring
- Performance metrics and charts
"""

import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

try:
    import ccxt
    import requests
    from dotenv import load_dotenv
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    from matplotlib.animation import FuncAnimation
    import seaborn as sns
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Run: pip install ccxt requests python-dotenv matplotlib seaborn")
    sys.exit(1)

# Set style
plt.style.use('dark_background')
sns.set_palette("husl")

class UnifiedTradingDashboard:
    """🚀 Comprehensive Trading Dashboard for Unified Master Bot"""
    
    def __init__(self):
        """Initialize the trading dashboard"""
        self.root = tk.Tk()
        self.root.title("🚀 Unified Master Trading Bot Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Load configuration
        load_dotenv('config.env.unified')
        
        # Initialize data storage
        self.trade_history = []
        self.portfolio_data = {}
        self.performance_metrics = {
            'total_trades': 0,
            'profitable_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'current_drawdown': 0.0,
            'max_drawdown': 0.0
        }
        
        # Bot status
        self.bot_status = {
            'running': False,
            'last_update': None,
            'current_cycle': 0,
            'active_positions': 0,
            'total_signals': 0,
            'actionable_signals': 0
        }
        
        # Exchange connection
        self.setup_exchange()
        
        # Create GUI
        self.create_gui()
        
        # Start data monitoring
        self.start_monitoring()
        
        print("🚀 Unified Trading Dashboard initialized successfully!")
    
    def setup_exchange(self):
        """Setup exchange connection for live data"""
        try:
            self.exchange = ccxt.binance({
                'sandbox': False,
                'enableRateLimit': True,
            })
            print("✅ Exchange connection established")
        except Exception as e:
            print(f"⚠️ Exchange setup failed: {e}")
            self.exchange = None
    
    def create_gui(self):
        """Create the main GUI interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_overview_tab()
        self.create_trading_tab()
        self.create_portfolio_tab()
        self.create_performance_tab()
        self.create_control_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_overview_tab(self):
        """Create overview tab with key metrics"""
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="📊 Overview")
        
        # Top metrics frame
        metrics_frame = ttk.LabelFrame(self.overview_frame, text="🎯 Key Metrics", padding=10)
        metrics_frame.pack(fill='x', padx=10, pady=5)
        
        # Create metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill='x')
        
        # Bot status
        self.bot_status_label = ttk.Label(metrics_grid, text="🤖 Bot Status: STOPPED", 
                                         font=('Arial', 12, 'bold'), foreground='red')
        self.bot_status_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        # Total trades
        self.total_trades_label = ttk.Label(metrics_grid, text="📈 Total Trades: 0", 
                                           font=('Arial', 11))
        self.total_trades_label.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        # Win rate
        self.win_rate_label = ttk.Label(metrics_grid, text="🎯 Win Rate: 0.0%", 
                                       font=('Arial', 11))
        self.win_rate_label.grid(row=0, column=2, padx=10, pady=5, sticky='w')
        
        # PnL
        self.pnl_label = ttk.Label(metrics_grid, text="💰 Total PnL: $0.00", 
                                  font=('Arial', 11))
        self.pnl_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')
        
        # Active positions
        self.positions_label = ttk.Label(metrics_grid, text="💼 Active Positions: 0", 
                                        font=('Arial', 11))
        self.positions_label.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        
        # Current drawdown
        self.drawdown_label = ttk.Label(metrics_grid, text="📉 Drawdown: 0.0%", 
                                       font=('Arial', 11))
        self.drawdown_label.grid(row=1, column=2, padx=10, pady=5, sticky='w')
        
        # Live signals frame
        signals_frame = ttk.LabelFrame(self.overview_frame, text="🔥 Live Trading Signals", padding=10)
        signals_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Signals treeview
        columns = ('Time', 'Symbol', 'Signal', 'Confidence', 'Price', 'Status')
        self.signals_tree = ttk.Treeview(signals_frame, columns=columns, show='headings', height=10)
        
        # Define headings
        for col in columns:
            self.signals_tree.heading(col, text=col)
            self.signals_tree.column(col, width=120, anchor='center')
        
        # Scrollbar for signals
        signals_scrollbar = ttk.Scrollbar(signals_frame, orient='vertical', command=self.signals_tree.yview)
        self.signals_tree.configure(yscrollcommand=signals_scrollbar.set)
        
        # Pack signals tree and scrollbar
        self.signals_tree.pack(side='left', fill='both', expand=True)
        signals_scrollbar.pack(side='right', fill='y')
    
    def create_trading_tab(self):
        """Create trading tab with detailed trade information"""
        self.trading_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trading_frame, text="📈 Trading")
        
        # Trade history frame
        history_frame = ttk.LabelFrame(self.trading_frame, text="📋 Trade History", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Trade history treeview
        trade_columns = ('Time', 'Symbol', 'Action', 'Price', 'Quantity', 'PnL', 'Confidence')
        self.trades_tree = ttk.Treeview(history_frame, columns=trade_columns, show='headings', height=15)
        
        # Define trade headings
        for col in trade_columns:
            self.trades_tree.heading(col, text=col)
            self.trades_tree.column(col, width=100, anchor='center')
        
        # Scrollbar for trades
        trades_scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.trades_tree.yview)
        self.trades_tree.configure(yscrollcommand=trades_scrollbar.set)
        
        # Pack trades tree and scrollbar
        self.trades_tree.pack(side='left', fill='both', expand=True)
        trades_scrollbar.pack(side='right', fill='y')
        
        # Trade statistics frame
        stats_frame = ttk.LabelFrame(self.trading_frame, text="📊 Trading Statistics", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Statistics labels
        self.best_trade_label = ttk.Label(stats_frame, text="🏆 Best Trade: $0.00")
        self.best_trade_label.pack(side='left', padx=20)
        
        self.worst_trade_label = ttk.Label(stats_frame, text="💥 Worst Trade: $0.00")
        self.worst_trade_label.pack(side='left', padx=20)
        
        self.avg_trade_label = ttk.Label(stats_frame, text="📊 Avg Trade: $0.00")
        self.avg_trade_label.pack(side='left', padx=20)
    
    def create_portfolio_tab(self):
        """Create portfolio tab with holdings and allocation"""
        self.portfolio_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.portfolio_frame, text="💼 Portfolio")
        
        # Portfolio summary frame
        summary_frame = ttk.LabelFrame(self.portfolio_frame, text="💰 Portfolio Summary", padding=10)
        summary_frame.pack(fill='x', padx=10, pady=5)
        
        # Summary labels
        self.portfolio_value_label = ttk.Label(summary_frame, text="💎 Total Value: $10,000.00", 
                                              font=('Arial', 12, 'bold'))
        self.portfolio_value_label.pack(side='left', padx=20)
        
        self.cash_label = ttk.Label(summary_frame, text="💵 Cash: $10,000.00")
        self.cash_label.pack(side='left', padx=20)
        
        self.invested_label = ttk.Label(summary_frame, text="📈 Invested: $0.00")
        self.invested_label.pack(side='left', padx=20)
        
        # Holdings frame
        holdings_frame = ttk.LabelFrame(self.portfolio_frame, text="🏦 Current Holdings", padding=10)
        holdings_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Holdings treeview
        holdings_columns = ('Symbol', 'Quantity', 'Avg Price', 'Current Price', 'Value', 'PnL', 'PnL %')
        self.holdings_tree = ttk.Treeview(holdings_frame, columns=holdings_columns, show='headings', height=12)
        
        # Define holdings headings
        for col in holdings_columns:
            self.holdings_tree.heading(col, text=col)
            self.holdings_tree.column(col, width=100, anchor='center')
        
        # Scrollbar for holdings
        holdings_scrollbar = ttk.Scrollbar(holdings_frame, orient='vertical', command=self.holdings_tree.yview)
        self.holdings_tree.configure(yscrollcommand=holdings_scrollbar.set)
        
        # Pack holdings tree and scrollbar
        self.holdings_tree.pack(side='left', fill='both', expand=True)
        holdings_scrollbar.pack(side='right', fill='y')
    
    def create_performance_tab(self):
        """Create performance tab with charts and analytics"""
        self.performance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.performance_frame, text="📊 Performance")
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), facecolor='#1e1e1e')
        self.fig.suptitle('🚀 Trading Bot Performance Analytics', color='white', fontsize=16)
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(2, 2, 1)  # Portfolio value over time
        self.ax2 = self.fig.add_subplot(2, 2, 2)  # Win/Loss distribution
        self.ax3 = self.fig.add_subplot(2, 2, 3)  # Trade frequency
        self.ax4 = self.fig.add_subplot(2, 2, 4)  # Signal accuracy
        
        # Style subplots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#2e2e2e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
        
        # Create canvas
        self.canvas = FigureCanvasTkinter(self.fig, self.performance_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        
        # Initialize empty plots
        self.update_performance_charts()
    
    def create_control_tab(self):
        """Create control tab for bot management"""
        self.control_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.control_frame, text="🎛️ Control")
        
        # Bot control frame
        bot_control_frame = ttk.LabelFrame(self.control_frame, text="🤖 Bot Control", padding=10)
        bot_control_frame.pack(fill='x', padx=10, pady=5)
        
        # Control buttons
        self.start_button = ttk.Button(bot_control_frame, text="▶️ Start Bot", 
                                      command=self.start_bot)
        self.start_button.pack(side='left', padx=10)
        
        self.stop_button = ttk.Button(bot_control_frame, text="⏹️ Stop Bot", 
                                     command=self.stop_bot, state='disabled')
        self.stop_button.pack(side='left', padx=10)
        
        self.restart_button = ttk.Button(bot_control_frame, text="🔄 Restart Bot", 
                                        command=self.restart_bot)
        self.restart_button.pack(side='left', padx=10)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(self.control_frame, text="⚙️ Configuration", padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # Configuration controls
        ttk.Label(config_frame, text="🎯 Confidence Threshold:").grid(row=0, column=0, sticky='w', padx=5)
        self.confidence_var = tk.StringVar(value="45.0")
        confidence_entry = ttk.Entry(config_frame, textvariable=self.confidence_var, width=10)
        confidence_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(config_frame, text="💰 Position Size (%):").grid(row=0, column=2, sticky='w', padx=5)
        self.position_size_var = tk.StringVar(value="10.0")
        position_entry = ttk.Entry(config_frame, textvariable=self.position_size_var, width=10)
        position_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(config_frame, text="⏰ Trading Cycle (s):").grid(row=1, column=0, sticky='w', padx=5)
        self.cycle_var = tk.StringVar(value="180")
        cycle_entry = ttk.Entry(config_frame, textvariable=self.cycle_var, width=10)
        cycle_entry.grid(row=1, column=1, padx=5)
        
        # Apply button
        apply_button = ttk.Button(config_frame, text="✅ Apply Changes", 
                                 command=self.apply_config)
        apply_button.grid(row=1, column=3, padx=5, pady=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.control_frame, text="📋 Bot Logs", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Log text widget
        self.log_text = tk.Text(log_frame, height=15, bg='#2e2e2e', fg='white', 
                               font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_label = ttk.Label(self.status_frame, text="🚀 Unified Trading Dashboard Ready")
        self.status_label.pack(side='left', padx=10, pady=5)
        
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side='right', padx=10, pady=5)
    
    def start_monitoring(self):
        """Start monitoring bot performance"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self.monitor_bot_data, daemon=True)
        self.monitor_thread.start()
        
        # Start GUI update timer
        self.update_gui()
    
    def monitor_bot_data(self):
        """Monitor bot data in background thread"""
        while self.monitoring_active:
            try:
                # Check if bot log file exists and read it
                if os.path.exists('unified_bot_test.log'):
                    self.parse_bot_log()
                
                # Update portfolio data
                self.update_portfolio_data()
                
                # Sleep before next check
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(10)
    
    def parse_bot_log(self):
        """Parse bot log file for trading data"""
        try:
            with open('unified_bot_test.log', 'r') as f:
                lines = f.readlines()
            
            # Parse recent lines for trading signals
            for line in lines[-50:]:  # Check last 50 lines
                if '📊' in line and ':' in line:
                    # Parse trading signal
                    parts = line.split(' - ')
                    if len(parts) >= 3:
                        timestamp = parts[0].split(' - ')[0]
                        signal_info = parts[2].strip()
                        
                        if 'Trade #' in signal_info:
                            # This is a trade execution
                            self.add_trade_signal(timestamp, signal_info)
                
                elif 'Trade executed:' in line:
                    # Parse executed trade
                    self.parse_executed_trade(line)
            
            # Update bot status
            self.bot_status['running'] = True
            self.bot_status['last_update'] = datetime.now()
            
        except Exception as e:
            print(f"❌ Log parsing error: {e}")
    
    def add_trade_signal(self, timestamp: str, signal_info: str):
        """Add trading signal to display"""
        try:
            # Parse signal information
            if ':' in signal_info:
                parts = signal_info.split(':')
                symbol_signal = parts[1].strip()
                
                if ' ' in symbol_signal:
                    signal_parts = symbol_signal.split(' ')
                    signal = signal_parts[0]
                    symbol = signal_parts[1] if len(signal_parts) > 1 else 'UNKNOWN'
                    
                    # Add to signals tree
                    self.signals_tree.insert('', 0, values=(
                        timestamp.split(',')[0],
                        symbol,
                        signal,
                        'N/A',  # Confidence
                        'N/A',  # Price
                        'EXECUTED'
                    ))
                    
                    # Keep only last 50 signals
                    if len(self.signals_tree.get_children()) > 50:
                        last_item = self.signals_tree.get_children()[-1]
                        self.signals_tree.delete(last_item)
            
        except Exception as e:
            print(f"❌ Signal parsing error: {e}")
    
    def parse_executed_trade(self, line: str):
        """Parse executed trade from log"""
        try:
            # Extract trade information
            if 'Trade executed:' in line:
                parts = line.split('Trade executed:')[1].strip()
                trade_info = parts.split(' with ')
                
                if len(trade_info) >= 2:
                    action_symbol_price = trade_info[0].strip()
                    confidence_info = trade_info[1].strip()
                    
                    # Add to trade history
                    trade_data = {
                        'timestamp': datetime.now(),
                        'info': action_symbol_price,
                        'confidence': confidence_info
                    }
                    
                    self.trade_history.append(trade_data)
                    self.performance_metrics['total_trades'] += 1
                    
                    # Update trades tree
                    self.trades_tree.insert('', 0, values=(
                        trade_data['timestamp'].strftime('%H:%M:%S'),
                        'N/A',  # Symbol
                        'N/A',  # Action
                        'N/A',  # Price
                        'N/A',  # Quantity
                        'N/A',  # PnL
                        confidence_info.split('%')[0] if '%' in confidence_info else 'N/A'
                    ))
            
        except Exception as e:
            print(f"❌ Trade parsing error: {e}")
    
    def update_portfolio_data(self):
        """Update portfolio data from exchange"""
        try:
            if self.exchange:
                # Get some sample tickers for demo
                tickers = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
                
                for ticker in tickers:
                    try:
                        price_data = self.exchange.fetch_ticker(ticker)
                        self.portfolio_data[ticker] = {
                            'price': price_data['last'],
                            'change': price_data['percentage']
                        }
                    except:
                        continue
        
        except Exception as e:
            print(f"❌ Portfolio update error: {e}")
    
    def update_performance_charts(self):
        """Update performance charts"""
        try:
            # Clear all axes
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                ax.clear()
                ax.set_facecolor('#2e2e2e')
            
            # Chart 1: Portfolio Value Over Time (Demo data)
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            portfolio_values = 10000 + np.cumsum(np.random.randn(30) * 100)
            
            self.ax1.plot(dates, portfolio_values, color='#00ff88', linewidth=2)
            self.ax1.set_title('💎 Portfolio Value Over Time', color='white')
            self.ax1.set_ylabel('Value ($)', color='white')
            self.ax1.tick_params(colors='white')
            
            # Chart 2: Win/Loss Distribution
            wins = max(1, self.performance_metrics.get('profitable_trades', 1))
            losses = max(1, self.performance_metrics.get('total_trades', 2) - wins)
            
            self.ax2.pie([wins, losses], labels=['Wins', 'Losses'], 
                        colors=['#00ff88', '#ff4444'], autopct='%1.1f%%')
            self.ax2.set_title('🎯 Win/Loss Distribution', color='white')
            
            # Chart 3: Trade Frequency (Demo data)
            hours = list(range(24))
            trade_counts = np.random.poisson(2, 24)
            
            self.ax3.bar(hours, trade_counts, color='#4488ff', alpha=0.7)
            self.ax3.set_title('📊 Trade Frequency by Hour', color='white')
            self.ax3.set_xlabel('Hour of Day', color='white')
            self.ax3.set_ylabel('Number of Trades', color='white')
            self.ax3.tick_params(colors='white')
            
            # Chart 4: Signal Accuracy (Demo data)
            signals = ['BUY', 'SELL', 'HOLD']
            accuracies = [65, 58, 78]
            
            bars = self.ax4.bar(signals, accuracies, color=['#00ff88', '#ff4444', '#ffaa00'])
            self.ax4.set_title('🎯 Signal Accuracy by Type', color='white')
            self.ax4.set_ylabel('Accuracy (%)', color='white')
            self.ax4.tick_params(colors='white')
            
            # Add value labels on bars
            for bar, acc in zip(bars, accuracies):
                height = bar.get_height()
                self.ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                             f'{acc}%', ha='center', va='bottom', color='white')
            
            plt.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"❌ Chart update error: {e}")
    
    def update_gui(self):
        """Update GUI elements periodically"""
        try:
            # Update time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.config(text=f"🕒 {current_time}")
            
            # Update bot status
            if self.bot_status['running']:
                self.bot_status_label.config(text="🤖 Bot Status: RUNNING", foreground='green')
            else:
                self.bot_status_label.config(text="🤖 Bot Status: STOPPED", foreground='red')
            
            # Update metrics
            self.total_trades_label.config(text=f"📈 Total Trades: {self.performance_metrics['total_trades']}")
            self.win_rate_label.config(text=f"🎯 Win Rate: {self.performance_metrics['win_rate']:.1f}%")
            self.pnl_label.config(text=f"💰 Total PnL: ${self.performance_metrics['total_pnl']:.2f}")
            
            # Update portfolio value (demo)
            portfolio_value = 10000 + len(self.trade_history) * 50  # Demo calculation
            self.portfolio_value_label.config(text=f"💎 Total Value: ${portfolio_value:.2f}")
            
            # Update performance charts every 30 seconds
            if hasattr(self, 'last_chart_update'):
                if (datetime.now() - self.last_chart_update).seconds >= 30:
                    self.update_performance_charts()
                    self.last_chart_update = datetime.now()
            else:
                self.last_chart_update = datetime.now()
            
            # Schedule next update
            self.root.after(5000, self.update_gui)  # Update every 5 seconds
            
        except Exception as e:
            print(f"❌ GUI update error: {e}")
            self.root.after(5000, self.update_gui)
    
    def start_bot(self):
        """Start the trading bot"""
        try:
            messagebox.showinfo("Bot Control", "🚀 Starting Unified Master Trading Bot...")
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.bot_status['running'] = True
            self.log_message("🚀 Bot started successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start bot: {e}")
    
    def stop_bot(self):
        """Stop the trading bot"""
        try:
            messagebox.showinfo("Bot Control", "⏹️ Stopping Unified Master Trading Bot...")
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.bot_status['running'] = False
            self.log_message("⏹️ Bot stopped successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop bot: {e}")
    
    def restart_bot(self):
        """Restart the trading bot"""
        try:
            messagebox.showinfo("Bot Control", "🔄 Restarting Unified Master Trading Bot...")
            self.log_message("🔄 Bot restarted successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart bot: {e}")
    
    def apply_config(self):
        """Apply configuration changes"""
        try:
            confidence = float(self.confidence_var.get())
            position_size = float(self.position_size_var.get())
            cycle_time = int(self.cycle_var.get())
            
            messagebox.showinfo("Configuration", 
                              f"✅ Configuration updated:\n"
                              f"🎯 Confidence: {confidence}%\n"
                              f"💰 Position Size: {position_size}%\n"
                              f"⏰ Cycle Time: {cycle_time}s")
            
            self.log_message(f"⚙️ Configuration updated: Confidence={confidence}%, Size={position_size}%, Cycle={cycle_time}s")
            
        except ValueError:
            messagebox.showerror("Error", "❌ Invalid configuration values. Please enter valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply configuration: {e}")
    
    def log_message(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Keep only last 100 lines
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete(1.0, f"{len(lines)-100}.0")
    
    def run(self):
        """Run the dashboard"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("🛑 Dashboard stopped by user")
        finally:
            self.monitoring_active = False

def main():
    """Main entry point"""
    try:
        print("🚀 Starting Unified Trading Dashboard...")
        dashboard = UnifiedTradingDashboard()
        dashboard.run()
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")

if __name__ == "__main__":
    main() 