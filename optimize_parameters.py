#!/usr/bin/env python3
"""
Parameter Optimization Script
Find optimal trading strategy parameters using grid search
"""

import os
import sys
import pandas as pd
import numpy as np
import itertools
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backtesting import TradingBacktester
    from run_backtest import fetch_real_data, generate_synthetic_data
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class ParameterOptimizer:
    """Optimize trading strategy parameters"""
    
    def __init__(self, symbol="BTC/USDT", timeframe="1h", initial_capital=10000):
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.results = []
        
    def optimize_parameters(self, use_real_data=True, optimization_metric='sharpe_ratio'):
        """Run parameter optimization"""
        
        print(f"🔧 Optimizing Parameters for {self.symbol}")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        print(f"📊 Optimization Metric: {optimization_metric}")
        print("=" * 60)
        
        # Parameter ranges to test
        parameter_grid = {
            'confidence_threshold': [50, 60, 70, 80],
            'max_position_size': [0.05, 0.10, 0.15, 0.20],
            'stop_loss': [0.03, 0.05, 0.07],
            'take_profit': [0.06, 0.10, 0.15],
            'holding_period': [12, 24, 48]
        }
        
        # Get data
        print("📊 Fetching market data...")
        if use_real_data:
            try:
                df = fetch_real_data(self.symbol, self.timeframe, limit=2000)
            except:
                print("⚠️  Failed to fetch real data, using synthetic data")
                df = generate_synthetic_data(self.symbol, self.timeframe, limit=2000)
        else:
            df = generate_synthetic_data(self.symbol, self.timeframe, limit=2000)
        
        if df.empty:
            print("❌ No data available")
            return None
        
        print(f"✅ Data loaded: {len(df)} periods")
        
        # Generate all parameter combinations
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        combinations = list(itertools.product(*param_values))
        
        print(f"🧪 Testing {len(combinations)} parameter combinations...")
        
        # Test each combination
        for i, params in enumerate(combinations):
            param_dict = dict(zip(param_names, params))
            
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i + 1}/{len(combinations)} ({(i + 1)/len(combinations)*100:.1f}%)")
            
            try:
                # Run backtest with these parameters
                result = self._test_parameters(df.copy(), param_dict)
                if result:
                    self.results.append(result)
                    
            except Exception as e:
                print(f"   Error testing parameters {param_dict}: {e}")
                continue
        
        # Analyze results
        if self.results:
            self._analyze_results(optimization_metric)
            return self._get_best_parameters(optimization_metric)
        else:
            print("❌ No valid results obtained")
            return None
    
    def _test_parameters(self, df, params):
        """Test a specific parameter combination"""
        try:
            # Initialize backtester
            backtester = TradingBacktester(initial_capital=self.initial_capital)
            
            # Prepare data
            df = backtester.prepare_data(df)
            df = backtester.generate_ai_predictions(df)
            
            # Run simulation with custom parameters
            strategy_params = {
                'confidence_threshold': params['confidence_threshold'],
                'max_position_size': params['max_position_size'],
                'stop_loss': params['stop_loss'],
                'take_profit': params['take_profit'],
                'holding_period': params['holding_period']
            }
            
            df = backtester.simulate_trading(df, strategy_params)
            metrics = backtester.calculate_metrics(df)
            
            # Combine parameters and metrics
            result = {**params, **metrics}
            return result
            
        except Exception as e:
            return None
    
    def _analyze_results(self, optimization_metric):
        """Analyze optimization results"""
        if not self.results:
            return
        
        results_df = pd.DataFrame(self.results)
        
        print(f"\n📊 OPTIMIZATION RESULTS")
        print("=" * 60)
        
        # Summary statistics
        print(f"Valid combinations tested: {len(results_df)}")
        print(f"Best {optimization_metric}: {results_df[optimization_metric].max():.3f}")
        print(f"Worst {optimization_metric}: {results_df[optimization_metric].min():.3f}")
        print(f"Average {optimization_metric}: {results_df[optimization_metric].mean():.3f}")
        
        # Top 5 parameter combinations
        top_results = results_df.nlargest(5, optimization_metric)
        
        print(f"\n🏆 TOP 5 PARAMETER COMBINATIONS (by {optimization_metric}):")
        print("-" * 60)
        
        for i, (idx, row) in enumerate(top_results.iterrows(), 1):
            print(f"\n{i}. {optimization_metric.upper()}: {row[optimization_metric]:.3f}")
            print(f"   Confidence Threshold: {row['confidence_threshold']}%")
            print(f"   Max Position Size: {row['max_position_size']*100:.1f}%")
            print(f"   Stop Loss: {row['stop_loss']*100:.1f}%")
            print(f"   Take Profit: {row['take_profit']*100:.1f}%")
            print(f"   Holding Period: {row['holding_period']} hours")
            print(f"   Total Return: {row['total_return']:.2%}")
            print(f"   Win Rate: {row['win_rate']:.2%}")
            print(f"   Max Drawdown: {row['max_drawdown']:.2%}")
            print(f"   Total Trades: {row['total_trades']}")
        
        # Parameter sensitivity analysis
        print(f"\n📈 PARAMETER SENSITIVITY ANALYSIS:")
        print("-" * 60)
        
        for param in ['confidence_threshold', 'max_position_size', 'stop_loss', 'take_profit']:
            correlation = results_df[param].corr(results_df[optimization_metric])
            print(f"{param}: {correlation:.3f} correlation with {optimization_metric}")
    
    def _get_best_parameters(self, optimization_metric):
        """Get the best parameter combination"""
        if not self.results:
            return None
        
        results_df = pd.DataFrame(self.results)
        best_idx = results_df[optimization_metric].idxmax()
        best_params = results_df.loc[best_idx]
        
        return {
            'confidence_threshold': best_params['confidence_threshold'],
            'max_position_size': best_params['max_position_size'],
            'stop_loss': best_params['stop_loss'],
            'take_profit': best_params['take_profit'],
            'holding_period': best_params['holding_period'],
            'expected_return': best_params['total_return'],
            'expected_sharpe': best_params['sharpe_ratio'],
            'expected_drawdown': best_params['max_drawdown'],
            'expected_win_rate': best_params['win_rate']
        }
    
    def save_results(self, filename=None):
        """Save optimization results to CSV"""
        if not self.results:
            print("No results to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_results_{self.symbol.replace('/', '_')}_{timestamp}.csv"
        
        results_df = pd.DataFrame(self.results)
        results_df.to_csv(filename, index=False)
        print(f"📁 Results saved to {filename}")

def quick_optimization(symbol="BTC/USDT", use_real_data=True):
    """Run a quick optimization with fewer parameters"""
    
    print(f"⚡ Quick Parameter Optimization for {symbol}")
    print("=" * 50)
    
    # Simplified parameter grid for faster testing
    parameter_grid = {
        'confidence_threshold': [60, 70, 80],
        'max_position_size': [0.05, 0.10, 0.15],
        'stop_loss': [0.03, 0.05],
        'take_profit': [0.08, 0.12]
    }
    
    # Get data
    if use_real_data:
        try:
            df = fetch_real_data(symbol, "1h", limit=1000)
        except:
            df = generate_synthetic_data(symbol, "1h", limit=1000)
    else:
        df = generate_synthetic_data(symbol, "1h", limit=1000)
    
    results = []
    param_names = list(parameter_grid.keys())
    param_values = list(parameter_grid.values())
    combinations = list(itertools.product(*param_values))
    
    print(f"Testing {len(combinations)} combinations...")
    
    for i, params in enumerate(combinations):
        param_dict = dict(zip(param_names, params))
        
        try:
            backtester = TradingBacktester(initial_capital=10000)
            df_test = backtester.prepare_data(df.copy())
            df_test = backtester.generate_ai_predictions(df_test)
            
            strategy_params = {
                'confidence_threshold': param_dict['confidence_threshold'],
                'max_position_size': param_dict['max_position_size'],
                'stop_loss': param_dict['stop_loss'],
                'take_profit': param_dict['take_profit'],
                'holding_period': 24
            }
            
            df_test = backtester.simulate_trading(df_test, strategy_params)
            metrics = backtester.calculate_metrics(df_test)
            
            result = {**param_dict, **metrics}
            results.append(result)
            
        except Exception as e:
            continue
    
    if results:
        results_df = pd.DataFrame(results)
        best_idx = results_df['sharpe_ratio'].idxmax()
        best_params = results_df.loc[best_idx]
        
        print(f"\n🏆 BEST PARAMETERS FOUND:")
        print(f"Confidence Threshold: {best_params['confidence_threshold']}%")
        print(f"Max Position Size: {best_params['max_position_size']*100:.1f}%")
        print(f"Stop Loss: {best_params['stop_loss']*100:.1f}%")
        print(f"Take Profit: {best_params['take_profit']*100:.1f}%")
        print(f"Expected Sharpe Ratio: {best_params['sharpe_ratio']:.2f}")
        print(f"Expected Return: {best_params['total_return']:.2%}")
        print(f"Expected Win Rate: {best_params['win_rate']:.2%}")
        
        return best_params
    else:
        print("❌ No valid results obtained")
        return None

def generate_env_config(best_params):
    """Generate .env configuration from best parameters"""
    if not best_params:
        return
    
    print(f"\n📝 RECOMMENDED .ENV CONFIGURATION:")
    print("=" * 50)
    print("# Optimized Trading Parameters")
    print(f"PREDICTION_CONFIDENCE_THRESHOLD={best_params['confidence_threshold']}")
    print(f"RISK_PERCENTAGE={best_params['max_position_size']*100:.1f}")
    print(f"STOP_LOSS_PERCENTAGE={best_params['stop_loss']*100:.1f}")
    print(f"TAKE_PROFIT_PERCENTAGE={best_params['take_profit']*100:.1f}")
    
    if 'holding_period' in best_params:
        print(f"MAX_HOLDING_PERIOD={best_params['holding_period']}")
    
    print(f"\n# Expected Performance")
    print(f"# Expected Annual Return: {best_params.get('expected_return', 0)*100:.1f}%")
    print(f"# Expected Sharpe Ratio: {best_params.get('expected_sharpe', 0):.2f}")
    print(f"# Expected Win Rate: {best_params.get('expected_win_rate', 0)*100:.1f}%")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize Trading Parameters')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading pair')
    parser.add_argument('--real-data', action='store_true', help='Use real market data')
    parser.add_argument('--quick', action='store_true', help='Quick optimization (fewer parameters)')
    parser.add_argument('--metric', default='sharpe_ratio', 
                       choices=['sharpe_ratio', 'total_return', 'win_rate'],
                       help='Optimization metric')
    
    args = parser.parse_args()
    
    if args.quick:
        best_params = quick_optimization(args.symbol, args.real_data)
        if best_params is not None:
            generate_env_config(best_params)
    else:
        optimizer = ParameterOptimizer(args.symbol)
        best_params = optimizer.optimize_parameters(args.real_data, args.metric)
        
        if best_params:
            generate_env_config(best_params)
            optimizer.save_results()
        
    print(f"\n✅ Parameter optimization completed!")
    print("💡 Update your .env file with the recommended parameters above.") 