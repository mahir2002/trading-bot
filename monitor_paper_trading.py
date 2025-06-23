#!/usr/bin/env python3
"""
📊 Paper Trading Monitor
Monitor your paper trading performance to decide when to go live
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class PaperTradingMonitor:
    def __init__(self):
        self.project_root = Path.cwd()
        self.logs_dir = self.project_root / 'logs'
        
        print("📊 PAPER TRADING PERFORMANCE MONITOR")
        print("=" * 50)
        print("Monitor your paper trading to decide when to go live")
        print("=" * 50)
    
    def check_system_status(self):
        """Check if the paper trading system is running"""
        print("\n🔍 SYSTEM STATUS CHECK")
        print("-" * 30)
        
        # Check if logs directory exists
        if not self.logs_dir.exists():
            print("❌ No logs directory found")
            print("   Start paper trading first:")
            print("   python ultimate_all_in_one_trading_system.py web")
            return False
        
        # Check for recent log files
        log_files = list(self.logs_dir.glob('*.log'))
        if not log_files:
            print("❌ No log files found")
            print("   Paper trading may not be running")
            return False
        
        # Check if logs are recent (within last hour)
        recent_logs = []
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        for log_file in log_files:
            if log_file.stat().st_mtime > one_hour_ago.timestamp():
                recent_logs.append(log_file)
        
        if recent_logs:
            print(f"✅ System appears to be running")
            print(f"   Recent log files: {len(recent_logs)}")
        else:
            print("⚠️  No recent log activity")
            print("   System may not be running or may be idle")
        
        return True
    
    def analyze_paper_trading_performance(self):
        """Analyze paper trading performance from logs"""
        print("\n📈 PAPER TRADING PERFORMANCE ANALYSIS")
        print("-" * 45)
        
        try:
            # Look for trading data in various possible locations
            data_files = [
                self.project_root / 'data' / 'paper_trading.db',
                self.project_root / 'paper_trading.json',
                self.project_root / 'trading_data.json'
            ]
            
            trading_data = None
            for data_file in data_files:
                if data_file.exists():
                    print(f"📁 Found trading data: {data_file.name}")
                    break
            else:
                print("📊 SIMULATED PERFORMANCE ANALYSIS")
                print("   (Since specific trading data format varies)")
                print("\n   WHAT TO LOOK FOR:")
                print("   ✅ Consistent profits over time")
                print("   ✅ Good risk management (small losses)")
                print("   ✅ Win rate > 50%")
                print("   ✅ Average profit > average loss")
                print("   ✅ Maximum drawdown < 10%")
                
                return self.show_performance_questions()
        
        except Exception as e:
            print(f"❌ Error analyzing performance: {e}")
            return self.show_performance_questions()
    
    def show_performance_questions(self):
        """Ask user about their paper trading performance"""
        print("\n❓ PAPER TRADING SELF-ASSESSMENT")
        print("-" * 35)
        print("Answer these questions about your paper trading:")
        
        questions = [
            ("How many days has paper trading been running?", "days"),
            ("What's your current paper trading balance? (started with $10,000)", "balance"),
            ("How many trades have been executed?", "trades"),
            ("What's your approximate win rate? (% of profitable trades)", "win_rate"),
            ("What's your largest single loss? ($)", "max_loss"),
            ("Are you comfortable with the bot's trading decisions?", "comfort")
        ]
        
        answers = {}
        
        for question, key in questions:
            if key == "comfort":
                answer = input(f"{question} (y/n): ").strip().lower()
                answers[key] = answer == 'y'
            else:
                answer = input(f"{question}: ").strip()
                try:
                    if key in ["days", "trades"]:
                        answers[key] = int(answer)
                    elif key in ["balance", "max_loss"]:
                        answers[key] = float(answer.replace('$', '').replace(',', ''))
                    elif key == "win_rate":
                        answers[key] = float(answer.replace('%', ''))
                    else:
                        answers[key] = answer
                except ValueError:
                    answers[key] = 0
        
        return self.evaluate_readiness(answers)
    
    def evaluate_readiness(self, answers):
        """Evaluate if user is ready for live trading"""
        print("\n🎯 READINESS EVALUATION")
        print("-" * 25)
        
        score = 0
        max_score = 6
        
        # Check duration
        if answers.get('days', 0) >= 14:
            print("✅ Duration: 14+ days (excellent)")
            score += 1
        elif answers.get('days', 0) >= 7:
            print("⚠️  Duration: 7-13 days (acceptable)")
            score += 0.5
        else:
            print("❌ Duration: <7 days (too short)")
        
        # Check profitability
        balance = answers.get('balance', 10000)
        if balance > 11000:
            print(f"✅ Profitability: ${balance:,.2f} (+{((balance/10000-1)*100):.1f}%)")
            score += 1
        elif balance > 10000:
            print(f"⚠️  Profitability: ${balance:,.2f} (small profit)")
            score += 0.5
        else:
            print(f"❌ Profitability: ${balance:,.2f} (loss)")
        
        # Check trade volume
        trades = answers.get('trades', 0)
        if trades >= 20:
            print(f"✅ Trade Volume: {trades} trades (good sample)")
            score += 1
        elif trades >= 10:
            print(f"⚠️  Trade Volume: {trades} trades (acceptable)")
            score += 0.5
        else:
            print(f"❌ Trade Volume: {trades} trades (too few)")
        
        # Check win rate
        win_rate = answers.get('win_rate', 0)
        if win_rate >= 60:
            print(f"✅ Win Rate: {win_rate}% (excellent)")
            score += 1
        elif win_rate >= 50:
            print(f"⚠️  Win Rate: {win_rate}% (acceptable)")
            score += 0.5
        else:
            print(f"❌ Win Rate: {win_rate}% (too low)")
        
        # Check risk management
        max_loss = answers.get('max_loss', 0)
        if max_loss <= 300:  # 3% of $10k
            print(f"✅ Risk Management: Max loss ${max_loss} (good)")
            score += 1
        elif max_loss <= 500:  # 5% of $10k
            print(f"⚠️  Risk Management: Max loss ${max_loss} (acceptable)")
            score += 0.5
        else:
            print(f"❌ Risk Management: Max loss ${max_loss} (too high)")
        
        # Check comfort level
        if answers.get('comfort', False):
            print("✅ Comfort Level: Comfortable with bot behavior")
            score += 1
        else:
            print("❌ Comfort Level: Not comfortable yet")
        
        # Final recommendation
        print(f"\n📊 READINESS SCORE: {score}/{max_score}")
        
        if score >= 5:
            print("🎉 READY FOR LIVE TRADING!")
            print("   You've demonstrated good paper trading performance")
            print("   Consider starting with small amounts")
            return True
        elif score >= 3:
            print("⚠️  PARTIALLY READY")
            print("   Consider more paper trading or start with very small amounts")
            return False
        else:
            print("❌ NOT READY FOR LIVE TRADING")
            print("   Continue paper trading until performance improves")
            return False
    
    def show_next_steps(self, ready_for_live):
        """Show next steps based on readiness"""
        if ready_for_live:
            print("\n🚀 NEXT STEPS FOR LIVE TRADING:")
            print("1. Run: python setup_live_trading_complete.py")
            print("2. Get real Binance API keys")
            print("3. Fund your Binance account ($500+ recommended)")
            print("4. Start with small trade amounts ($25-50)")
            print("5. Monitor closely for first 24 hours")
        else:
            print("\n📝 CONTINUE PAPER TRADING:")
            print("1. Let paper trading run longer")
            print("2. Monitor performance daily")
            print("3. Learn from the bot's decisions")
            print("4. Run this monitor again in a few days")
            print("5. Dashboard: http://localhost:8200")
    
    def run_continuous_monitor(self):
        """Run continuous monitoring"""
        print("\n🔄 CONTINUOUS MONITORING MODE")
        print("Press Ctrl+C to stop")
        print("-" * 30)
        
        try:
            while True:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{current_time}] Checking system status...")
                
                if self.check_system_status():
                    print("✅ Paper trading system running")
                else:
                    print("❌ Paper trading system not detected")
                
                # Wait 5 minutes
                time.sleep(300)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

def main():
    monitor = PaperTradingMonitor()
    
    # Check system status
    if not monitor.check_system_status():
        return
    
    # Analyze performance
    ready = monitor.analyze_paper_trading_performance()
    
    # Show next steps
    monitor.show_next_steps(ready)
    
    # Ask if user wants continuous monitoring
    continuous = input("\nStart continuous monitoring? (y/N): ").strip().lower()
    if continuous == 'y':
        monitor.run_continuous_monitor()

if __name__ == "__main__":
    main() 