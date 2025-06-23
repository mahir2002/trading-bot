#!/usr/bin/env python3
"""
Run Backtesting for AI Trading Bot
Simple script to estimate returns via backtesting
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backtesting import TradingBacktester, run_backtest
    from ai_trading_bot_simple import AITradingBot, TradingLogger
    import ccxt
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are installed")
    sys.exit(1)

def fetch_real_data(symbol: str = "BTC/USDT", timeframe: str = "1h", 
                   limit: int = 1000) -> pd.DataFrame:
    """Fetch real historical data from exchange"""
    try:
        # Initialize exchange (using testnet/sandbox mode)
        exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY', ''),
            'secret': os.getenv('BINANCE_SECRET_KEY', ''),
            'sandbox': True,  # Use testnet
            'enableRateLimit': True,
        })
        
        print(f"Fetching {limit} periods of {symbol} {timeframe} data...")
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Fetched {len(df)} periods from {df.index[0]} to {df.index[-1]}")
        return df
        
    except Exception as e:
        print(f"❌ Failed to fetch real data: {e}")
        print("📊 Generating synthetic data for demo...")
        return generate_synthetic_data(symbol, timeframe, limit)

def generate_synthetic_data(symbol: str = "BTC/USDT", timeframe: str = "1h", 
                          limit: int = 1000) -> pd.DataFrame:
    """Generate realistic synthetic price data"""
    # Create date range
    end_date = datetime.now()
    if timeframe == "1h":
        start_date = end_date - timedelta(hours=limit)
        freq = 'H'
    elif timeframe == "1d":
        start_date = end_date - timedelta(days=limit)
        freq = 'D'
    else:
        start_date = end_date - timedelta(hours=limit)
        freq = 'H'
    
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)[:limit]
    
    # Generate realistic price movements
    np.random.seed(42)  # For reproducible results
    
    # Starting price based on symbol
    if "BTC" in symbol:
        start_price = 45000
        volatility = 0.03
    elif "ETH" in symbol:
        start_price = 3000
        volatility = 0.04
    else:
        start_price = 100
        volatility = 0.05
    
    # Generate returns with some trend and volatility clustering
    returns = []
    for i in range(len(dates)):
        # Add some trend and mean reversion
        trend = 0.0001 * np.sin(i / 100)  # Cyclical trend
        noise = np.random.normal(0, volatility)
        
        # Volatility clustering
        if i > 0 and abs(returns[-1]) > volatility:
            noise *= 1.5  # Higher volatility after high volatility
        
        returns.append(trend + noise)
    
    # Generate prices
    prices = [start_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Generate OHLCV data
    df_data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC from close price
        volatility_factor = abs(np.random.normal(0, 0.01))
        
        open_price = price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, price) * (1 + volatility_factor)
        low_price = min(open_price, price) * (1 - volatility_factor)
        close_price = price
        volume = np.random.uniform(1000, 10000)
        
        df_data.append({
            'timestamp': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(df_data)
    df.set_index('timestamp', inplace=True)
    
    return df

def run_simple_backtest(symbol: str = "BTC/USDT", timeframe: str = "1h",
                       initial_capital: float = 10000, use_real_data: bool = True):
    """Run a simplified backtest with your code structure"""
    
    print(f"🚀 Starting Simple Backtest for {symbol}")
    print(f"💰 Initial Capital: ${initial_capital:,.2f}")
    print("="*50)
    
    try:
        # Fetch data
        if use_real_data:
            df = fetch_real_data(symbol, timeframe, limit=1000)
        else:
            df = generate_synthetic_data(symbol, timeframe, limit=1000)
        
        if df.empty:
            print("❌ No data available")
            return None
        
        # Initialize backtester
        backtester = TradingBacktester(initial_capital=initial_capital)
        
        # Prepare data with technical indicators
        print("🔧 Calculating technical indicators...")
        df = backtester.prepare_data(df)
        
        # Generate AI predictions
        print("🤖 Generating AI predictions...")
        df = backtester.generate_ai_predictions(df)
        
        # Simulate trading
        print("💼 Simulating trading strategy...")
        df = backtester.simulate_trading(df)
        
        # Calculate metrics
        print("📊 Calculating performance metrics...")
        metrics = backtester.calculate_metrics(df)
        
        # Print results
        backtester.print_summary()
        
        # Create plots
        print("📈 Generating performance plots...")
        backtester.plot_results(df, save_path=f'backtest_{symbol.replace("/", "_")}_{timeframe}.png')
        
        # Additional analysis
        print("\n" + "="*50)
        print("📋 DETAILED ANALYSIS")
        print("="*50)
        
        if backtester.trades:
            trades_df = pd.DataFrame(backtester.trades)
            
            print(f"\n🔍 Trade Analysis:")
            print(f"Best Trade:     {trades_df['pnl'].max():.2f} USDT ({trades_df['pnl_pct'].max():.2%})")
            print(f"Worst Trade:    {trades_df['pnl'].min():.2f} USDT ({trades_df['pnl_pct'].min():.2%})")
            print(f"Avg Trade Size: {trades_df['position_size'].abs().mean():.4f} units")
            
            # Exit reasons
            exit_reasons = trades_df['exit_reason'].value_counts()
            print(f"\n📤 Exit Reasons:")
            for reason, count in exit_reasons.items():
                print(f"  {reason}: {count} trades ({count/len(trades_df)*100:.1f}%)")
        
        # Model performance
        if 'target' in df.columns and 'predicted' in df.columns:
            from sklearn.metrics import classification_report
            valid_data = df.dropna(subset=['target', 'predicted'])
            if len(valid_data) > 0:
                print(f"\n🤖 AI Model Performance:")
                print(classification_report(valid_data['target'], valid_data['predicted'], 
                                          target_names=['Sell/Hold', 'Buy']))
        
        return backtester
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_strategies(symbol: str = "BTC/USDT", timeframe: str = "1h"):
    """Compare different strategy parameters"""
    
    print(f"🔄 Comparing Strategy Parameters for {symbol}")
    print("="*60)
    
    # Different strategy configurations
    strategies = [
        {"name": "Conservative", "confidence_threshold": 80, "max_position_size": 0.05},
        {"name": "Moderate", "confidence_threshold": 60, "max_position_size": 0.10},
        {"name": "Aggressive", "confidence_threshold": 40, "max_position_size": 0.20},
    ]
    
    results = []
    
    for strategy in strategies:
        print(f"\n🧪 Testing {strategy['name']} Strategy...")
        
        # Fetch data
        df = fetch_real_data(symbol, timeframe, limit=1000)
        if df.empty:
            df = generate_synthetic_data(symbol, timeframe, limit=1000)
        
        # Initialize backtester
        backtester = TradingBacktester(initial_capital=10000)
        
        # Prepare data
        df = backtester.prepare_data(df)
        df = backtester.generate_ai_predictions(df)
        
        # Simulate with custom parameters
        strategy_params = {
            'confidence_threshold': strategy['confidence_threshold'],
            'max_position_size': strategy['max_position_size'],
            'stop_loss': 0.05,
            'take_profit': 0.10,
            'holding_period': 24
        }
        
        df = backtester.simulate_trading(df, strategy_params)
        metrics = backtester.calculate_metrics(df)
        
        results.append({
            'strategy': strategy['name'],
            'total_return': metrics['total_return'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': metrics['max_drawdown'],
            'win_rate': metrics['win_rate'],
            'total_trades': metrics['total_trades']
        })
        
        print(f"  Return: {metrics['total_return']:.2%}")
        print(f"  Sharpe: {metrics['sharpe_ratio']:.2f}")
        print(f"  Trades: {metrics['total_trades']}")
    
    # Print comparison
    print(f"\n📊 STRATEGY COMPARISON")
    print("="*60)
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False, float_format='%.3f'))
    
    # Find best strategy
    best_strategy = results_df.loc[results_df['total_return'].idxmax()]
    print(f"\n🏆 Best Strategy: {best_strategy['strategy']}")
    print(f"   Total Return: {best_strategy['total_return']:.2%}")
    print(f"   Sharpe Ratio: {best_strategy['sharpe_ratio']:.2f}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Bot Backtesting')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading pair')
    parser.add_argument('--timeframe', default='1h', help='Timeframe')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital')
    parser.add_argument('--real-data', action='store_true', help='Use real market data')
    parser.add_argument('--compare', action='store_true', help='Compare strategies')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_strategies(args.symbol, args.timeframe)
    else:
        backtester = run_simple_backtest(
            symbol=args.symbol,
            timeframe=args.timeframe,
            initial_capital=args.capital,
            use_real_data=args.real_data
        )
        
        if backtester:
            print(f"\n✅ Backtest completed!")
            print(f"📁 Results saved to backtest_{args.symbol.replace('/', '_')}_{args.timeframe}.png")
        else:
            print("\n❌ Backtest failed!") 