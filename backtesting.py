#!/usr/bin/env python3
"""
AI Trading Bot - Backtesting Module
Comprehensive backtesting framework for strategy evaluation
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# Suppress warnings
warnings.filterwarnings('ignore')

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_trading_bot_simple import AIPredictor
    from utils import PerformanceTracker
    import ta
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")

class TradingBacktester:
    """Comprehensive backtesting framework for AI trading strategies"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = {}
        self.trades = []
        self.portfolio_history = []
        
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data with technical indicators and features"""
        # Ensure we have OHLCV columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Technical indicators
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
        
        # Momentum indicators
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['stoch'] = ta.momentum.stoch(df['high'], df['low'], df['close'])
        
        # Volatility indicators
        df['bb_upper'] = ta.volatility.bollinger_hband(df['close'])
        df['bb_middle'] = ta.volatility.bollinger_mavg(df['close'])
        df['bb_lower'] = ta.volatility.bollinger_lband(df['close'])
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
        
        # Volume indicators (fix the function names)
        df['volume_sma'] = df['volume'].rolling(window=20).mean()  # Simple volume SMA
        df['mfi'] = ta.volume.money_flow_index(df['high'], df['low'], df['close'], df['volume'])
        
        # Price action features
        df['price_change'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Generate target labels (1 if next period price goes up, 0 if down)
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        return df.dropna()
    
    def generate_ai_predictions(self, df: pd.DataFrame, model_path: str = None) -> pd.DataFrame:
        """Generate AI predictions using the trained model"""
        try:
            # Try to load existing model
            if model_path and os.path.exists(model_path):
                predictor = joblib.load(model_path)
                print(f"Loaded model from {model_path}")
            else:
                # Create and train new model
                print("Training new AI model for backtesting...")
                from ai_trading_bot_simple import TradingLogger
                logger = TradingLogger()
                predictor = AIPredictor(logger)
                
                # Train on first 80% of data
                train_size = int(len(df) * 0.8)
                train_data = df.iloc[:train_size].copy()
                
                if predictor.train_models(train_data):
                    print("Model trained successfully")
                    # Save model for future use
                    if model_path:
                        joblib.dump(predictor, model_path)
                        print(f"Model saved to {model_path}")
                else:
                    print("Model training failed, using random predictions")
                    df['predicted_prob'] = np.random.random(len(df))
                    df['predicted'] = (df['predicted_prob'] > 0.5).astype(int)
                    df['confidence'] = abs(df['predicted_prob'] - 0.5) * 200
                    return df
            
            # Generate predictions for all data
            predictions = []
            confidences = []
            
            for i in range(len(df)):
                # Use data up to current point for prediction
                current_data = df.iloc[:i+1].copy()
                if len(current_data) >= 100:  # Minimum data for prediction
                    prob, conf = predictor.predict(current_data)
                    predictions.append(prob)
                    confidences.append(conf)
                else:
                    predictions.append(0.5)  # Neutral prediction
                    confidences.append(0.0)
            
            df['predicted_prob'] = predictions
            df['predicted'] = (df['predicted_prob'] > 0.5).astype(int)
            df['confidence'] = confidences
            
            return df
            
        except Exception as e:
            print(f"Error in AI prediction: {e}")
            # Fallback to random predictions
            df['predicted_prob'] = np.random.random(len(df))
            df['predicted'] = (df['predicted_prob'] > 0.5).astype(int)
            df['confidence'] = abs(df['predicted_prob'] - 0.5) * 200
            return df
    
    def simulate_trading(self, df: pd.DataFrame, strategy_params: Dict = None) -> pd.DataFrame:
        """Simulate trading based on AI predictions"""
        if strategy_params is None:
            strategy_params = {
                'confidence_threshold': 60,  # Minimum confidence for trade
                'max_position_size': 0.1,    # Maximum 10% of portfolio per trade
                'stop_loss': 0.05,           # 5% stop loss
                'take_profit': 0.10,         # 10% take profit
                'holding_period': 24         # Maximum holding period (hours)
            }
        
        # Initialize portfolio
        cash = self.initial_capital
        position = 0  # Number of shares/units
        position_entry_price = 0
        position_entry_time = 0
        portfolio_value = []
        
        # Track trades
        trades = []
        
        for i, row in df.iterrows():
            current_price = row['close']
            current_time = len(portfolio_value)  # Use numeric index instead of datetime
            
            # Calculate current portfolio value
            portfolio_val = cash + (position * current_price)
            portfolio_value.append(portfolio_val)
            
            # Check for exit conditions if we have a position
            if position != 0:
                # Calculate current P&L
                pnl_pct = (current_price - position_entry_price) / position_entry_price
                holding_time = current_time - position_entry_time  # Now both are numeric
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                # Stop loss
                if position > 0 and pnl_pct <= -strategy_params['stop_loss']:
                    should_exit = True
                    exit_reason = "stop_loss"
                elif position < 0 and pnl_pct >= strategy_params['stop_loss']:
                    should_exit = True
                    exit_reason = "stop_loss"
                
                # Take profit
                elif position > 0 and pnl_pct >= strategy_params['take_profit']:
                    should_exit = True
                    exit_reason = "take_profit"
                elif position < 0 and pnl_pct <= -strategy_params['take_profit']:
                    should_exit = True
                    exit_reason = "take_profit"
                
                # Maximum holding period
                elif holding_time >= strategy_params['holding_period']:
                    should_exit = True
                    exit_reason = "max_holding"
                
                # Signal reversal
                elif (position > 0 and row['predicted'] == 0 and row['confidence'] > strategy_params['confidence_threshold']) or \
                     (position < 0 and row['predicted'] == 1 and row['confidence'] > strategy_params['confidence_threshold']):
                    should_exit = True
                    exit_reason = "signal_reversal"
                
                # Execute exit
                if should_exit:
                    # Calculate trade result
                    trade_value = position * current_price
                    commission_cost = abs(trade_value) * self.commission
                    cash += trade_value - commission_cost
                    
                    # Record trade
                    trades.append({
                        'entry_time': position_entry_time,
                        'exit_time': current_time,
                        'entry_price': position_entry_price,
                        'exit_price': current_price,
                        'position_size': position,
                        'pnl': trade_value - (position * position_entry_price),
                        'pnl_pct': pnl_pct,
                        'holding_time': holding_time,
                        'exit_reason': exit_reason,
                        'commission': commission_cost
                    })
                    
                    position = 0
                    position_entry_price = 0
                    position_entry_time = 0
            
            # Check for entry conditions if we don't have a position
            if position == 0 and row['confidence'] > strategy_params['confidence_threshold']:
                # Calculate position size based on confidence and available cash
                confidence_factor = min(row['confidence'] / 100, 1.0)
                max_trade_value = cash * strategy_params['max_position_size'] * confidence_factor
                
                if row['predicted'] == 1:  # Buy signal
                    position = max_trade_value / current_price
                    commission_cost = max_trade_value * self.commission
                    cash -= max_trade_value + commission_cost
                    position_entry_price = current_price
                    position_entry_time = current_time
                    
                elif row['predicted'] == 0:  # Sell signal (short)
                    position = -max_trade_value / current_price
                    commission_cost = max_trade_value * self.commission
                    cash += max_trade_value - commission_cost
                    position_entry_price = current_price
                    position_entry_time = current_time
        
        # Close any remaining position at the end
        if position != 0:
            final_price = df['close'].iloc[-1]
            trade_value = position * final_price
            commission_cost = abs(trade_value) * self.commission
            cash += trade_value - commission_cost
            
            pnl_pct = (final_price - position_entry_price) / position_entry_price
            trades.append({
                'entry_time': position_entry_time,
                'exit_time': len(df) - 1,
                'entry_price': position_entry_price,
                'exit_price': final_price,
                'position_size': position,
                'pnl': trade_value - (position * position_entry_price),
                'pnl_pct': pnl_pct,
                'holding_time': len(df) - 1 - position_entry_time,
                'exit_reason': 'end_of_data',
                'commission': commission_cost
            })
        
        # Add portfolio values to dataframe
        df['portfolio_value'] = portfolio_value
        df['strategy_returns'] = df['portfolio_value'].pct_change()
        df['cumulative_strategy_returns'] = df['portfolio_value'] / self.initial_capital
        df['cumulative_market_returns'] = df['close'] / df['close'].iloc[0]
        
        # Store results
        self.trades = trades
        self.portfolio_history = portfolio_value
        
        return df
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive performance metrics"""
        # Basic returns
        total_return = (df['portfolio_value'].iloc[-1] / self.initial_capital) - 1
        market_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
        
        # Strategy returns
        strategy_returns = df['strategy_returns'].dropna()
        market_returns = df['returns'].dropna()
        
        # Risk metrics
        volatility = strategy_returns.std() * np.sqrt(252 * 24)  # Annualized (assuming hourly data)
        market_volatility = market_returns.std() * np.sqrt(252 * 24)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252 * 24) if strategy_returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = df['cumulative_strategy_returns']
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Trade statistics
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] < 0]
            
            win_rate = len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
            profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else float('inf')
            
            total_trades = len(trades_df)
            avg_holding_time = trades_df['holding_time'].mean()
            total_commission = trades_df['commission'].sum()
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            total_trades = 0
            avg_holding_time = 0
            total_commission = 0
        
        # Model accuracy
        if 'target' in df.columns and 'predicted' in df.columns:
            valid_predictions = df.dropna(subset=['target', 'predicted'])
            if len(valid_predictions) > 0:
                accuracy = accuracy_score(valid_predictions['target'], valid_predictions['predicted'])
            else:
                accuracy = 0
        else:
            accuracy = 0
        
        metrics = {
            'total_return': total_return,
            'market_return': market_return,
            'excess_return': total_return - market_return,
            'volatility': volatility,
            'market_volatility': market_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_holding_time': avg_holding_time,
            'total_commission': total_commission,
            'model_accuracy': accuracy,
            'final_portfolio_value': df['portfolio_value'].iloc[-1],
            'initial_capital': self.initial_capital
        }
        
        self.results = metrics
        return metrics
    
    def plot_results(self, df: pd.DataFrame, save_path: str = None):
        """Create comprehensive visualization of backtest results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('AI Trading Bot Backtest Results', fontsize=16)
        
        # 1. Cumulative returns comparison
        axes[0, 0].plot(df.index, df['cumulative_strategy_returns'], label='Strategy', linewidth=2)
        axes[0, 0].plot(df.index, df['cumulative_market_returns'], label='Buy & Hold', linewidth=2)
        axes[0, 0].set_title('Cumulative Returns Comparison')
        axes[0, 0].set_ylabel('Cumulative Return')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Drawdown
        cumulative_returns = df['cumulative_strategy_returns']
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        axes[0, 1].fill_between(df.index, drawdown, 0, alpha=0.3, color='red')
        axes[0, 1].plot(df.index, drawdown, color='red', linewidth=1)
        axes[0, 1].set_title('Strategy Drawdown')
        axes[0, 1].set_ylabel('Drawdown')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Trade distribution
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            axes[1, 0].hist(trades_df['pnl_pct'], bins=30, alpha=0.7, edgecolor='black')
            axes[1, 0].axvline(x=0, color='red', linestyle='--', alpha=0.7)
            axes[1, 0].set_title('Trade P&L Distribution')
            axes[1, 0].set_xlabel('P&L (%)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(True, alpha=0.3)
        else:
            axes[1, 0].text(0.5, 0.5, 'No trades executed', ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Trade P&L Distribution')
        
        # 4. Rolling Sharpe ratio
        rolling_returns = df['strategy_returns'].rolling(window=100)
        rolling_sharpe = (rolling_returns.mean() / rolling_returns.std()) * np.sqrt(252 * 24)
        axes[1, 1].plot(df.index, rolling_sharpe, linewidth=2)
        axes[1, 1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
        axes[1, 1].set_title('Rolling Sharpe Ratio (100-period)')
        axes[1, 1].set_ylabel('Sharpe Ratio')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        
        plt.show()
    
    def print_summary(self):
        """Print comprehensive backtest summary"""
        if not self.results:
            print("No backtest results available. Run backtest first.")
            return
        
        print("\n" + "="*60)
        print("AI TRADING BOT BACKTEST SUMMARY")
        print("="*60)
        
        print(f"\n📊 PERFORMANCE METRICS")
        print(f"Initial Capital:        ${self.results['initial_capital']:,.2f}")
        print(f"Final Portfolio Value:  ${self.results['final_portfolio_value']:,.2f}")
        print(f"Total Return:           {self.results['total_return']:.2%}")
        print(f"Market Return:          {self.results['market_return']:.2%}")
        print(f"Excess Return:          {self.results['excess_return']:.2%}")
        
        print(f"\n📈 RISK METRICS")
        print(f"Volatility:             {self.results['volatility']:.2%}")
        print(f"Market Volatility:      {self.results['market_volatility']:.2%}")
        print(f"Sharpe Ratio:           {self.results['sharpe_ratio']:.2f}")
        print(f"Maximum Drawdown:       {self.results['max_drawdown']:.2%}")
        
        print(f"\n💼 TRADING STATISTICS")
        print(f"Total Trades:           {self.results['total_trades']}")
        print(f"Win Rate:               {self.results['win_rate']:.2%}")
        print(f"Profit Factor:          {self.results['profit_factor']:.2f}")
        print(f"Average Win:            ${self.results['avg_win']:.2f}")
        print(f"Average Loss:           ${self.results['avg_loss']:.2f}")
        print(f"Average Holding Time:   {self.results['avg_holding_time']:.1f} periods")
        print(f"Total Commission:       ${self.results['total_commission']:.2f}")
        
        print(f"\n🤖 AI MODEL PERFORMANCE")
        print(f"Model Accuracy:         {self.results['model_accuracy']:.2%}")
        
        # Performance rating
        score = 0
        if self.results['total_return'] > 0.1: score += 1
        if self.results['excess_return'] > 0: score += 1
        if self.results['sharpe_ratio'] > 1: score += 1
        if self.results['max_drawdown'] > -0.2: score += 1
        if self.results['win_rate'] > 0.5: score += 1
        
        rating = ["Poor", "Below Average", "Average", "Good", "Excellent"][score]
        print(f"\n⭐ OVERALL RATING: {rating} ({score}/5)")
        
        print("="*60)

def run_backtest(symbol: str = "BTC/USDT", timeframe: str = "1h", 
                 start_date: str = None, end_date: str = None,
                 initial_capital: float = 10000) -> TradingBacktester:
    """Run a complete backtest for the AI trading bot"""
    
    print(f"🚀 Starting backtest for {symbol} ({timeframe})")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    
    # Initialize backtester
    backtester = TradingBacktester(initial_capital=initial_capital)
    
    try:
        # Get historical data (you'll need to implement this based on your data source)
        print("📊 Fetching historical data...")
        
        # For demo purposes, create sample data
        # In practice, you'd fetch real data from your exchange
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price data
        returns = np.random.normal(0.0001, 0.02, len(dates))
        prices = [100]  # Starting price
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, len(dates))
        })
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Data loaded: {len(df)} periods from {df.index[0]} to {df.index[-1]}")
        
        # Prepare data with technical indicators
        print("🔧 Preparing technical indicators...")
        df = backtester.prepare_data(df)
        
        # Generate AI predictions
        print("🤖 Generating AI predictions...")
        df = backtester.generate_ai_predictions(df)
        
        # Run trading simulation
        print("💼 Simulating trading strategy...")
        df = backtester.simulate_trading(df)
        
        # Calculate metrics
        print("📊 Calculating performance metrics...")
        metrics = backtester.calculate_metrics(df)
        
        # Print results
        backtester.print_summary()
        
        # Create plots
        print("📈 Generating performance plots...")
        backtester.plot_results(df, save_path='backtest_results.png')
        
        return backtester
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run example backtest
    backtester = run_backtest(
        symbol="BTC/USDT",
        timeframe="1h",
        initial_capital=10000
    )
    
    if backtester:
        print("\n✅ Backtest completed successfully!")
        print("📁 Results saved to 'backtest_results.png'")
    else:
        print("\n❌ Backtest failed!") 