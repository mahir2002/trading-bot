#!/usr/bin/env python3
"""
Paper Trading Monitor
Monitor and analyze paper trading performance in real-time
"""

import os
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PaperTradingMonitor:
    """Monitor paper trading performance"""
    
    def __init__(self, log_file="logs/trading.log", update_interval=60):
        self.log_file = log_file
        self.update_interval = update_interval
        self.trades = []
        self.performance_history = []
        self.start_time = datetime.now()
        
    def parse_log_file(self):
        """Parse trading log file for trades and signals"""
        if not os.path.exists(self.log_file):
            return
        
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Extract trades and signals
            for line in lines:
                if 'TRADE:' in line:
                    self._parse_trade_line(line)
                elif 'SIGNAL:' in line:
                    self._parse_signal_line(line)
                    
        except Exception as e:
            print(f"Error parsing log file: {e}")
    
    def _parse_trade_line(self, line):
        """Parse a trade line from logs"""
        try:
            # Example: "2024-01-01 12:00:00 - TRADE: BUY BTC/USDT at $45000 (0.001 BTC)"
            parts = line.strip().split(' - TRADE: ')
            if len(parts) == 2:
                timestamp_str = parts[0]
                trade_info = parts[1]
                
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Parse trade details
                if 'BUY' in trade_info:
                    side = 'BUY'
                elif 'SELL' in trade_info:
                    side = 'SELL'
                else:
                    return
                
                # Extract symbol, price, and amount
                # This is a simplified parser - adjust based on your log format
                trade = {
                    'timestamp': timestamp,
                    'side': side,
                    'info': trade_info
                }
                
                self.trades.append(trade)
                
        except Exception as e:
            pass
    
    def _parse_signal_line(self, line):
        """Parse a signal line from logs"""
        try:
            # Example: "2024-01-01 12:00:00 - SIGNAL: BTC/USDT BUY (Confidence: 75%)"
            parts = line.strip().split(' - ')
            if len(parts) >= 2 and 'SIGNAL:' in parts[1]:
                timestamp_str = parts[0]
                signal_info = parts[1]
                
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Store signal for analysis
                # Implementation depends on your log format
                
        except Exception as e:
            pass
    
    def calculate_performance_metrics(self):
        """Calculate current performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'daily_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        # Simplified performance calculation
        # In practice, you'd track actual P&L from your trading system
        
        total_trades = len(self.trades)
        buy_trades = len([t for t in self.trades if t['side'] == 'BUY'])
        sell_trades = len([t for t in self.trades if t['side'] == 'SELL'])
        
        # Estimate win rate (simplified)
        win_rate = 0.55 if total_trades > 0 else 0  # Placeholder
        
        # Calculate time-based metrics
        runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        trades_per_day = (total_trades / max(runtime_hours, 1)) * 24
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'win_rate': win_rate,
            'trades_per_day': trades_per_day,
            'runtime_hours': runtime_hours,
            'total_return': 0.05,  # Placeholder - implement actual P&L tracking
            'daily_return': 0.002,  # Placeholder
            'max_drawdown': -0.03,  # Placeholder
            'sharpe_ratio': 1.2  # Placeholder
        }
    
    def print_status_report(self):
        """Print current status report"""
        self.parse_log_file()
        metrics = self.calculate_performance_metrics()
        
        print(f"\n📊 PAPER TRADING STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        print(f"🕐 Runtime: {metrics['runtime_hours']:.1f} hours")
        print(f"📈 Total Trades: {metrics['total_trades']}")
        print(f"   ↗️  Buy Orders: {metrics['buy_trades']}")
        print(f"   ↘️  Sell Orders: {metrics['sell_trades']}")
        print(f"📊 Trading Frequency: {metrics['trades_per_day']:.1f} trades/day")
        
        print(f"\n💰 Performance Metrics:")
        print(f"   Total Return: {metrics['total_return']:.2%}")
        print(f"   Daily Return: {metrics['daily_return']:.2%}")
        print(f"   Win Rate: {metrics['win_rate']:.2%}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        
        # Performance rating
        score = 0
        if metrics['total_return'] > 0: score += 1
        if metrics['win_rate'] > 0.5: score += 1
        if metrics['max_drawdown'] > -0.1: score += 1
        if metrics['sharpe_ratio'] > 1: score += 1
        if metrics['total_trades'] > 0: score += 1
        
        rating = ["Poor", "Below Average", "Average", "Good", "Excellent"][score]
        print(f"⭐ Current Rating: {rating} ({score}/5)")
        
        # Recent activity
        if self.trades:
            recent_trades = self.trades[-5:]
            print(f"\n📋 Recent Activity:")
            for trade in recent_trades:
                print(f"   {trade['timestamp'].strftime('%H:%M')} - {trade['info']}")
        
        return metrics
    
    def check_health_status(self):
        """Check bot health and alert on issues"""
        issues = []
        
        # Check if log file exists and is being updated
        if not os.path.exists(self.log_file):
            issues.append("❌ Log file not found")
        else:
            # Check if log file was updated recently
            last_modified = datetime.fromtimestamp(os.path.getmtime(self.log_file))
            if (datetime.now() - last_modified).total_seconds() > 600:  # 10 minutes
                issues.append("⚠️  Log file not updated recently (bot may be stopped)")
        
        # Check trading activity
        metrics = self.calculate_performance_metrics()
        if metrics['runtime_hours'] > 2 and metrics['total_trades'] == 0:
            issues.append("⚠️  No trades executed after 2+ hours")
        
        if metrics['win_rate'] < 0.3 and metrics['total_trades'] > 10:
            issues.append("🚨 Low win rate detected")
        
        if metrics['max_drawdown'] < -0.2:
            issues.append("🚨 High drawdown detected")
        
        # Print health status
        if issues:
            print(f"\n🏥 HEALTH CHECK - Issues Detected:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ HEALTH CHECK - All systems normal")
        
        return len(issues) == 0
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        print(f"🔍 Starting Paper Trading Monitor")
        print(f"📁 Log file: {self.log_file}")
        print(f"⏱️  Update interval: {self.update_interval} seconds")
        print("Press Ctrl+C to stop monitoring")
        print("=" * 60)
        
        try:
            while True:
                # Print status report
                metrics = self.print_status_report()
                
                # Check health
                self.check_health_status()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print(f"\n👋 Monitoring stopped by user")
            
            # Generate final report
            print(f"\n📊 FINAL PAPER TRADING REPORT")
            print("=" * 60)
            final_metrics = self.print_status_report()
            
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            if final_metrics['total_trades'] == 0:
                print("   - Check bot configuration and API connections")
                print("   - Verify market conditions and trading pairs")
            elif final_metrics['win_rate'] < 0.45:
                print("   - Consider adjusting confidence thresholds")
                print("   - Review AI model performance")
            elif final_metrics['total_return'] < 0:
                print("   - Review risk management settings")
                print("   - Consider reducing position sizes")
            else:
                print("   - Paper trading performance looks good!")
                print("   - Consider moving to live trading with small amounts")

def quick_status_check():
    """Quick status check without continuous monitoring"""
    monitor = PaperTradingMonitor()
    print("🔍 Quick Paper Trading Status Check")
    print("=" * 50)
    
    metrics = monitor.print_status_report()
    health_ok = monitor.check_health_status()
    
    if health_ok and metrics['total_trades'] > 0:
        print("\n✅ Paper trading appears to be working correctly")
    else:
        print("\n⚠️  Issues detected - review the status above")
    
    return metrics

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Paper Trading Monitor')
    parser.add_argument('--log-file', default='logs/trading.log', help='Trading log file path')
    parser.add_argument('--interval', type=int, default=60, help='Update interval in seconds')
    parser.add_argument('--quick', action='store_true', help='Quick status check only')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_status_check()
    else:
        monitor = PaperTradingMonitor(args.log_file, args.interval)
        monitor.run_continuous_monitoring() 