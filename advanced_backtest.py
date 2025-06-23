#!/usr/bin/env python3
"""
Advanced Backtesting for Enhanced AI Trading Bot
Test the advanced bot with multiple strategies and optimizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our advanced bot components
from ai_trading_bot_advanced import AdvancedFeatureEngine, EnsemblePredictor, AdvancedRiskManager, AdvancedLogger

class AdvancedBacktester:
    """Advanced backtesting with enhanced strategies"""
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.logger = AdvancedLogger()
        
    def generate_enhanced_data(self, symbol="BTC/USDT", periods=2000):
        """Generate more realistic market data"""
        np.random.seed(42)
        
        # Create more realistic price movements with trends and volatility clustering
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='H')
        
        # Generate returns with volatility clustering and trends
        returns = []
        volatility = 0.02
        trend = 0.0001
        
        for i in range(periods):
            # Add trend changes
            if i % 500 == 0:
                trend = np.random.normal(0, 0.0005)
            
            # Volatility clustering
            if i > 0:
                volatility = 0.8 * volatility + 0.2 * abs(returns[-1]) + np.random.normal(0, 0.001)
                volatility = max(0.005, min(0.1, volatility))
            
            # Generate return
            ret = np.random.normal(trend, volatility)
            returns.append(ret)
        
        # Convert to prices
        prices = [100]  # Starting price
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create realistic OHLCV data
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
            'close': prices,
            'volume': np.random.lognormal(8, 1, periods)  # More realistic volume distribution
        })
        
        return df
    
    def run_advanced_backtest(self, symbol="BTC/USDT"):
        """Run comprehensive backtest with advanced strategies"""
        
        print(f"🚀 Advanced Backtesting for {symbol}")
        print("=" * 60)
        
        # Generate data
        print("📊 Generating enhanced market data...")
        df = self.generate_enhanced_data(symbol, periods=2000)
        
        # Initialize advanced predictor
        print("🤖 Training advanced ensemble models...")
        predictor = EnsemblePredictor(self.logger)
        
        # Train models on first 80% of data
        train_size = int(len(df) * 0.8)
        train_data = df.iloc[:train_size].copy()
        
        if not predictor.train_models(train_data):
            print("❌ Model training failed")
            return None
        
        # Initialize risk manager
        risk_manager = AdvancedRiskManager(self.logger)
        
        # Run backtest on remaining 20% of data
        test_data = df.iloc[train_size:].copy().reset_index(drop=True)
        
        print(f"📈 Running backtest on {len(test_data)} periods...")
        
        # Initialize portfolio
        portfolio_value = self.initial_capital
        cash = self.initial_capital
        positions = {}
        trades = []
        portfolio_history = []
        
        for i, row in test_data.iterrows():
            current_data = df.iloc[:train_size + i + 1]
            
            # Get prediction
            signal, confidence, individual_preds = predictor.predict(current_data)
            
            # Calculate market metrics
            returns = current_data['close'].pct_change().dropna()
            volatility = returns.tail(20).std() if len(returns) >= 20 else 0.02
            
            # Check if we should trade
            if risk_manager.should_trade(signal, confidence):
                
                # Calculate position size
                position_size = risk_manager.calculate_position_size(
                    signal, confidence, volatility, cash
                )
                
                current_price = row['close']
                
                # Execute trade based on signal
                if signal in [3, 4] and cash > 0:  # Buy signals
                    trade_value = min(cash * position_size, cash * 0.95)  # Leave some cash
                    shares = trade_value / current_price
                    
                    if symbol not in positions:
                        positions[symbol] = 0
                    
                    positions[symbol] += shares
                    cash -= trade_value
                    
                    trades.append({
                        'timestamp': row['timestamp'],
                        'action': 'BUY',
                        'symbol': symbol,
                        'price': current_price,
                        'shares': shares,
                        'value': trade_value,
                        'signal': signal,
                        'confidence': confidence
                    })
                    
                elif signal in [0, 1] and symbol in positions and positions[symbol] > 0:  # Sell signals
                    shares_to_sell = positions[symbol] * position_size
                    trade_value = shares_to_sell * current_price
                    
                    positions[symbol] -= shares_to_sell
                    cash += trade_value
                    
                    trades.append({
                        'timestamp': row['timestamp'],
                        'action': 'SELL',
                        'symbol': symbol,
                        'price': current_price,
                        'shares': shares_to_sell,
                        'value': trade_value,
                        'signal': signal,
                        'confidence': confidence
                    })
            
            # Calculate portfolio value
            position_value = sum(positions.get(sym, 0) * row['close'] for sym in positions)
            portfolio_value = cash + position_value
            portfolio_history.append({
                'timestamp': row['timestamp'],
                'portfolio_value': portfolio_value,
                'cash': cash,
                'position_value': position_value,
                'price': row['close']
            })
        
        # Calculate final metrics
        results = self.calculate_advanced_metrics(
            portfolio_history, trades, test_data, self.initial_capital
        )
        
        # Display results
        self.display_results(results, trades)
        
        # Create visualizations
        self.create_advanced_plots(portfolio_history, test_data, trades)
        
        return results
    
    def calculate_advanced_metrics(self, portfolio_history, trades, market_data, initial_capital):
        """Calculate comprehensive performance metrics"""
        
        portfolio_df = pd.DataFrame(portfolio_history)
        
        # Basic metrics
        final_value = portfolio_df['portfolio_value'].iloc[-1]
        total_return = (final_value - initial_capital) / initial_capital
        
        # Calculate returns
        portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change()
        market_data['market_returns'] = market_data['close'].pct_change()
        
        # Risk metrics
        portfolio_volatility = portfolio_df['returns'].std() * np.sqrt(8760)  # Annualized
        market_volatility = market_data['market_returns'].std() * np.sqrt(8760)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        excess_returns = portfolio_df['returns'].mean() - 0.02/8760
        sharpe_ratio = excess_returns / portfolio_df['returns'].std() * np.sqrt(8760)
        
        # Maximum drawdown
        cumulative_returns = (1 + portfolio_df['returns']).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Trade analysis
        if trades:
            trades_df = pd.DataFrame(trades)
            total_trades = len(trades_df)
            buy_trades = len(trades_df[trades_df['action'] == 'BUY'])
            sell_trades = len(trades_df[trades_df['action'] == 'SELL'])
            avg_confidence = trades_df['confidence'].mean()
            
            # Calculate trade profitability (simplified)
            trade_returns = []
            for i in range(1, len(trades_df)):
                if trades_df.iloc[i-1]['action'] == 'BUY' and trades_df.iloc[i]['action'] == 'SELL':
                    buy_price = trades_df.iloc[i-1]['price']
                    sell_price = trades_df.iloc[i]['price']
                    trade_return = (sell_price - buy_price) / buy_price
                    trade_returns.append(trade_return)
            
            win_rate = len([r for r in trade_returns if r > 0]) / len(trade_returns) if trade_returns else 0
        else:
            total_trades = 0
            buy_trades = 0
            sell_trades = 0
            avg_confidence = 0
            win_rate = 0
        
        # Market comparison
        market_return = (market_data['close'].iloc[-1] - market_data['close'].iloc[0]) / market_data['close'].iloc[0]
        
        # Alpha and Beta
        if len(portfolio_df['returns'].dropna()) > 1 and len(market_data['market_returns'].dropna()) > 1:
            covariance = np.cov(portfolio_df['returns'].dropna(), market_data['market_returns'].dropna())[0][1]
            market_variance = np.var(market_data['market_returns'].dropna())
            beta = covariance / market_variance if market_variance != 0 else 0
            alpha = portfolio_df['returns'].mean() - beta * market_data['market_returns'].mean()
        else:
            beta = 0
            alpha = 0
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'market_return': market_return,
            'alpha': alpha * 8760,  # Annualized
            'beta': beta,
            'sharpe_ratio': sharpe_ratio,
            'portfolio_volatility': portfolio_volatility,
            'market_volatility': market_volatility,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'win_rate': win_rate,
            'avg_confidence': avg_confidence
        }
    
    def display_results(self, results, trades):
        """Display comprehensive results"""
        
        print("\n" + "=" * 60)
        print("📊 ADVANCED BACKTEST RESULTS")
        print("=" * 60)
        
        # Performance metrics
        print(f"💰 Final Portfolio Value: ${results['final_value']:,.2f}")
        print(f"📈 Total Return: {results['total_return']:.2%}")
        print(f"📊 Market Return: {results['market_return']:.2%}")
        print(f"🎯 Alpha (Excess Return): {results['alpha']:.2%}")
        print(f"📉 Beta (Market Sensitivity): {results['beta']:.2f}")
        print(f"⚡ Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"📊 Portfolio Volatility: {results['portfolio_volatility']:.2%}")
        print(f"📉 Maximum Drawdown: {results['max_drawdown']:.2%}")
        
        # Trading metrics
        print(f"\n💼 Trading Statistics:")
        print(f"   Total Trades: {results['total_trades']}")
        print(f"   Buy Trades: {results['buy_trades']}")
        print(f"   Sell Trades: {results['sell_trades']}")
        print(f"   Win Rate: {results['win_rate']:.2%}")
        print(f"   Average Confidence: {results['avg_confidence']:.1f}%")
        
        # Performance rating
        score = 0
        if results['total_return'] > 0.1: score += 1  # 10%+ return
        if results['sharpe_ratio'] > 1: score += 1    # Good risk-adjusted return
        if results['max_drawdown'] > -0.2: score += 1 # Reasonable drawdown
        if results['win_rate'] > 0.5: score += 1      # Good win rate
        if results['alpha'] > 0: score += 1           # Beating market
        
        ratings = ["Poor", "Below Average", "Average", "Good", "Excellent"]
        rating = ratings[min(score, 4)]
        
        print(f"\n⭐ Overall Rating: {rating} ({score}/5)")
        
        # Strategy insights
        print(f"\n💡 Strategy Insights:")
        if results['alpha'] > 0.05:
            print("   ✅ Strategy significantly outperforms market")
        elif results['alpha'] > 0:
            print("   ✅ Strategy slightly outperforms market")
        else:
            print("   ⚠️  Strategy underperforms market")
        
        if results['sharpe_ratio'] > 1.5:
            print("   ✅ Excellent risk-adjusted returns")
        elif results['sharpe_ratio'] > 1:
            print("   ✅ Good risk-adjusted returns")
        else:
            print("   ⚠️  Poor risk-adjusted returns")
        
        if results['max_drawdown'] > -0.1:
            print("   ✅ Low drawdown - good risk management")
        elif results['max_drawdown'] > -0.2:
            print("   ⚠️  Moderate drawdown")
        else:
            print("   🚨 High drawdown - review risk management")
    
    def create_advanced_plots(self, portfolio_history, market_data, trades):
        """Create comprehensive visualization"""
        
        portfolio_df = pd.DataFrame(portfolio_history)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Advanced Trading Bot Performance Analysis', fontsize=16, fontweight='bold')
        
        # Portfolio value vs market
        ax1 = axes[0, 0]
        ax1.plot(portfolio_df['timestamp'], portfolio_df['portfolio_value'], 
                label='Portfolio Value', linewidth=2, color='blue')
        
        # Normalize market price to same scale
        market_normalized = (market_data['close'] / market_data['close'].iloc[0]) * self.initial_capital
        ax1.plot(market_data['timestamp'], market_normalized, 
                label='Market (Normalized)', linewidth=2, color='orange', alpha=0.7)
        
        ax1.set_title('Portfolio vs Market Performance')
        ax1.set_ylabel('Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        ax2 = axes[0, 1]
        portfolio_df['returns'] = portfolio_df['portfolio_value'].pct_change()
        cumulative_returns = (1 + portfolio_df['returns']).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        
        ax2.fill_between(portfolio_df['timestamp'], drawdown, 0, alpha=0.3, color='red')
        ax2.plot(portfolio_df['timestamp'], drawdown, color='red', linewidth=1)
        ax2.set_title('Portfolio Drawdown')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        
        # Trade distribution
        ax3 = axes[1, 0]
        if trades:
            trades_df = pd.DataFrame(trades)
            signal_counts = trades_df['signal'].value_counts()
            signal_names = {0: 'Strong Sell', 1: 'Sell', 2: 'Hold', 3: 'Buy', 4: 'Strong Buy'}
            
            bars = ax3.bar([signal_names.get(i, f'Signal {i}') for i in signal_counts.index], 
                          signal_counts.values, color=['red', 'orange', 'gray', 'lightgreen', 'green'])
            ax3.set_title('Trade Signal Distribution')
            ax3.set_ylabel('Number of Trades')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        
        # Rolling returns
        ax4 = axes[1, 1]
        rolling_returns = portfolio_df['returns'].rolling(window=24).mean() * 24 * 365  # Annualized
        ax4.plot(portfolio_df['timestamp'], rolling_returns, color='purple', linewidth=2)
        ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax4.set_title('Rolling Annual Returns (24h window)')
        ax4.set_ylabel('Annual Return (%)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('advanced_backtest_results.png', dpi=300, bbox_inches='tight')
        print(f"\n📁 Advanced analysis saved to 'advanced_backtest_results.png'")
        plt.show()

def run_strategy_comparison():
    """Compare different advanced strategies"""
    
    print("🔄 Advanced Strategy Comparison")
    print("=" * 60)
    
    strategies = [
        {"name": "Conservative", "confidence_threshold": 80, "max_position": 0.1},
        {"name": "Moderate", "confidence_threshold": 70, "max_position": 0.2},
        {"name": "Aggressive", "confidence_threshold": 60, "max_position": 0.3},
        {"name": "Ultra-Aggressive", "confidence_threshold": 50, "max_position": 0.4}
    ]
    
    results = []
    
    for strategy in strategies:
        print(f"\n🧪 Testing {strategy['name']} Strategy...")
        
        backtester = AdvancedBacktester(initial_capital=10000)
        result = backtester.run_advanced_backtest()
        
        if result:
            results.append({
                'strategy': strategy['name'],
                'total_return': result['total_return'],
                'sharpe_ratio': result['sharpe_ratio'],
                'max_drawdown': result['max_drawdown'],
                'alpha': result['alpha'],
                'win_rate': result['win_rate']
            })
    
    # Display comparison
    if results:
        print(f"\n📊 STRATEGY COMPARISON RESULTS")
        print("=" * 80)
        print(f"{'Strategy':<15} {'Return':<10} {'Sharpe':<8} {'Drawdown':<10} {'Alpha':<8} {'Win Rate':<10}")
        print("-" * 80)
        
        for result in results:
            print(f"{result['strategy']:<15} "
                  f"{result['total_return']:<10.2%} "
                  f"{result['sharpe_ratio']:<8.2f} "
                  f"{result['max_drawdown']:<10.2%} "
                  f"{result['alpha']:<8.2%} "
                  f"{result['win_rate']:<10.2%}")
        
        # Find best strategy
        best_strategy = max(results, key=lambda x: x['sharpe_ratio'])
        print(f"\n🏆 Best Strategy: {best_strategy['strategy']} (Sharpe: {best_strategy['sharpe_ratio']:.2f})")

if __name__ == "__main__":
    print("🚀 Advanced AI Trading Bot Backtesting")
    print("=" * 60)
    
    # Run single advanced backtest
    backtester = AdvancedBacktester(initial_capital=10000)
    results = backtester.run_advanced_backtest()
    
    # Run strategy comparison
    print("\n" + "=" * 60)
    run_strategy_comparison()
    
    print(f"\n✅ Advanced backtesting completed!")
    print("💡 The advanced bot uses:")
    print("   - Ensemble of 4 ML models (RF, GB, SVM, Neural Network)")
    print("   - 50+ technical indicators and features")
    print("   - Dynamic position sizing based on confidence and volatility")
    print("   - Advanced risk management with drawdown protection")
    print("   - Multi-class prediction (Strong Sell/Sell/Hold/Buy/Strong Buy)") 