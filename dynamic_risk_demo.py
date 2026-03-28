#!/usr/bin/env python3
"""
🛡️ Dynamic Risk Management Demo
Realistic demonstration of adaptive risk adjustment based on market conditions
"""

import asyncio
import time
import numpy as np
from datetime import datetime, timedelta
import logging
from dynamic_risk_manager import DynamicRiskManager, RiskLevel, MarketRegime

class RealisticMarketSimulator:
    """Simulate realistic market conditions for risk testing"""
    
    def __init__(self):
        self.btc_price = 50000
        self.eth_price = 3000
        self.market_phase = "normal"
        self.day = 0
        
    def simulate_day(self, phase="normal"):
        """Simulate one day of market data"""
        self.day += 1
        
        if phase == "normal":
            # Normal market conditions
            btc_return = np.random.normal(0.001, 0.02)  # 2% daily vol
            eth_return = np.random.normal(0.001, 0.025)  # 2.5% daily vol
            volume_multiplier = 1.0
            
        elif phase == "volatile":
            # High volatility period
            btc_return = np.random.normal(-0.005, 0.05)  # 5% daily vol, slight negative drift
            eth_return = np.random.normal(-0.005, 0.06)  # 6% daily vol
            volume_multiplier = 2.0
            
        elif phase == "crash":
            # Market crash
            btc_return = np.random.normal(-0.03, 0.04)  # 4% vol, -3% daily drift
            eth_return = np.random.normal(-0.035, 0.045)  # 4.5% vol, -3.5% drift
            volume_multiplier = 3.0
            
        elif phase == "recovery":
            # Recovery phase
            btc_return = np.random.normal(0.02, 0.03)  # 3% vol, +2% drift
            eth_return = np.random.normal(0.025, 0.035)  # 3.5% vol, +2.5% drift
            volume_multiplier = 1.5
        
        # Update prices
        self.btc_price *= (1 + btc_return)
        self.eth_price *= (1 + eth_return)
        
        # Generate volume
        btc_volume = np.random.uniform(800000, 1200000) * volume_multiplier
        eth_volume = np.random.uniform(400000, 600000) * volume_multiplier
        
        return {
            'BTC/USDT': {'price': self.btc_price, 'volume': btc_volume, 'return': btc_return},
            'ETH/USDT': {'price': self.eth_price, 'volume': eth_volume, 'return': eth_return}
        }

class TradingSimulator:
    """Simulate trading performance based on market conditions"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trade_count = 0
        
    def simulate_trading_day(self, market_data, risk_params):
        """Simulate one day of trading"""
        
        # Calculate daily portfolio return based on market performance
        portfolio_return = 0.0
        
        for symbol, data in market_data.items():
            # Simulate position based on risk parameters
            position_size = risk_params.max_position_size * 0.5  # Use 50% of max allowed
            
            # Add some trading skill/alpha
            skill_factor = np.random.normal(0.0002, 0.001)  # Small positive alpha with noise
            
            # Position return
            position_return = (data['return'] + skill_factor) * position_size
            portfolio_return += position_return
        
        # Update capital
        self.current_capital *= (1 + portfolio_return)
        
        # Generate trade record
        if np.random.random() < 0.7:  # 70% chance of trade
            self.trade_count += 1
            symbol = np.random.choice(['BTC/USDT', 'ETH/USDT'])
            
            # Simulate trade outcome
            trade_return = np.random.normal(0.005, 0.02)  # Slight positive bias
            trade_pnl = self.current_capital * risk_params.max_position_size * trade_return
            
            trade = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': 'buy',
                'quantity': 0.01,
                'entry_price': market_data[symbol]['price'],
                'exit_price': market_data[symbol]['price'] * (1 + trade_return),
                'pnl': trade_pnl,
                'pnl_percentage': trade_return
            }
            
            return trade
        
        return None

async def demo_dynamic_risk_management():
    """Comprehensive demo of dynamic risk management"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("🛡️ DYNAMIC RISK MANAGEMENT DEMO")
    print("=" * 45)
    
    # Initialize components
    risk_mgr = DynamicRiskManager(initial_capital=100000, logger=logger)
    market_sim = RealisticMarketSimulator()
    trading_sim = TradingSimulator(100000)
    
    print(f"💰 Initial Capital: ${risk_mgr.initial_capital:,.2f}")
    print(f"🎯 Initial Risk Parameters:")
    print(f"   Max Position Size: {risk_mgr.risk_parameters.max_position_size:.1%}")
    print(f"   Stop Loss: {risk_mgr.risk_parameters.stop_loss_percentage:.1%}")
    print(f"   Max Leverage: {risk_mgr.risk_parameters.max_leverage:.1f}x")
    print(f"   Max Exposure: {risk_mgr.risk_parameters.max_total_exposure:.1%}")
    print()
    
    # Phase 1: Normal Market Conditions (20 days)
    print("📊 PHASE 1: Normal Market Conditions (20 days)")
    print("-" * 40)
    
    for day in range(20):
        # Simulate market
        market_data = market_sim.simulate_day("normal")
        
        # Update risk manager with market data
        for symbol, data in market_data.items():
            risk_mgr.update_market_data(symbol, data['price'], data['volume'])
        
        # Simulate trading
        trade = trading_sim.simulate_trading_day(market_data, risk_mgr.risk_parameters)
        if trade:
            risk_mgr.add_trade(trade)
        
        # Update portfolio value
        risk_mgr.update_portfolio_value(trading_sim.current_capital)
        
        # Check for risk adjustments every 5 days
        if day % 5 == 4:
            adjustment = risk_mgr.adjust_risk_parameters()
            if adjustment['status'] == 'adjusted':
                print(f"   Day {day+1}: Risk adjusted - {list(adjustment['adjustments'].keys())}")
    
    # Show Phase 1 results
    dashboard = risk_mgr.get_risk_dashboard()
    print(f"\n📈 Phase 1 Results:")
    print(f"   Portfolio Value: ${dashboard['portfolio']['value']:,.2f}")
    print(f"   Return: {(dashboard['portfolio']['value'] / risk_mgr.initial_capital - 1):.1%}")
    print(f"   Risk Level: {dashboard['risk_level']}")
    print(f"   Max Position Size: {dashboard['risk_parameters']['max_position_size']}")
    print(f"   Volatility: {dashboard['market']['volatility']}")
    
    # Phase 2: High Volatility Period (15 days)
    print(f"\n⚡ PHASE 2: High Volatility Period (15 days)")
    print("-" * 40)
    
    for day in range(15):
        # Simulate volatile market
        market_data = market_sim.simulate_day("volatile")
        
        # Update risk manager
        for symbol, data in market_data.items():
            risk_mgr.update_market_data(symbol, data['price'], data['volume'])
        
        # Simulate trading
        trade = trading_sim.simulate_trading_day(market_data, risk_mgr.risk_parameters)
        if trade:
            risk_mgr.add_trade(trade)
        
        # Update portfolio
        risk_mgr.update_portfolio_value(trading_sim.current_capital)
        
        # More frequent adjustments during volatility
        if day % 3 == 2:
            adjustment = risk_mgr.adjust_risk_parameters()
            if adjustment['status'] == 'adjusted':
                print(f"   Day {day+1}: Risk adjusted - {list(adjustment['adjustments'].keys())}")
                print(f"      New Risk Level: {adjustment['risk_level']}")
    
    # Show Phase 2 results
    dashboard = risk_mgr.get_risk_dashboard()
    print(f"\n📈 Phase 2 Results:")
    print(f"   Portfolio Value: ${dashboard['portfolio']['value']:,.2f}")
    print(f"   Return: {(dashboard['portfolio']['value'] / risk_mgr.initial_capital - 1):.1%}")
    print(f"   Risk Level: {dashboard['risk_level']}")
    print(f"   Max Position Size: {dashboard['risk_parameters']['max_position_size']}")
    print(f"   Volatility: {dashboard['market']['volatility']}")
    print(f"   Current Drawdown: {dashboard['portfolio']['drawdown_current']}")
    
    # Phase 3: Market Crash (10 days)
    print(f"\n📉 PHASE 3: Market Crash (10 days)")
    print("-" * 40)
    
    for day in range(10):
        # Simulate market crash
        market_data = market_sim.simulate_day("crash")
        
        # Update risk manager
        for symbol, data in market_data.items():
            risk_mgr.update_market_data(symbol, data['price'], data['volume'])
        
        # Simulate trading (reduced due to risk controls)
        trade = trading_sim.simulate_trading_day(market_data, risk_mgr.risk_parameters)
        if trade:
            risk_mgr.add_trade(trade)
        
        # Update portfolio
        risk_mgr.update_portfolio_value(trading_sim.current_capital)
        
        # Daily risk adjustments during crisis
        adjustment = risk_mgr.adjust_risk_parameters()
        if adjustment['status'] == 'adjusted':
            print(f"   Day {day+1}: EMERGENCY ADJUSTMENT - {list(adjustment['adjustments'].keys())}")
            print(f"      Risk Level: {adjustment['risk_level']} (Score: {adjustment['risk_score']:.1f})")
        
        # Check if trading should be halted
        halt_trading, halt_reason = risk_mgr.should_halt_trading()
        if halt_trading:
            print(f"   Day {day+1}: 🚨 TRADING HALTED - {halt_reason}")
            break
    
    # Show Phase 3 results
    dashboard = risk_mgr.get_risk_dashboard()
    print(f"\n📈 Phase 3 Results:")
    print(f"   Portfolio Value: ${dashboard['portfolio']['value']:,.2f}")
    print(f"   Return: {(dashboard['portfolio']['value'] / risk_mgr.initial_capital - 1):.1%}")
    print(f"   Risk Level: {dashboard['risk_level']}")
    print(f"   Max Position Size: {dashboard['risk_parameters']['max_position_size']}")
    print(f"   Current Drawdown: {dashboard['portfolio']['drawdown_current']}")
    print(f"   Emergency Mode: {dashboard['controls']['emergency_mode']}")
    
    # Phase 4: Recovery (10 days)
    print(f"\n🚀 PHASE 4: Market Recovery (10 days)")
    print("-" * 40)
    
    for day in range(10):
        # Simulate recovery
        market_data = market_sim.simulate_day("recovery")
        
        # Update risk manager
        for symbol, data in market_data.items():
            risk_mgr.update_market_data(symbol, data['price'], data['volume'])
        
        # Simulate trading
        trade = trading_sim.simulate_trading_day(market_data, risk_mgr.risk_parameters)
        if trade:
            risk_mgr.add_trade(trade)
        
        # Update portfolio
        risk_mgr.update_portfolio_value(trading_sim.current_capital)
        
        # Risk adjustments during recovery
        if day % 2 == 1:
            adjustment = risk_mgr.adjust_risk_parameters()
            if adjustment['status'] == 'adjusted':
                print(f"   Day {day+1}: Recovery adjustment - {list(adjustment['adjustments'].keys())}")
    
    # Final Results
    print(f"\n📊 FINAL RESULTS")
    print("=" * 30)
    
    final_dashboard = risk_mgr.get_risk_dashboard()
    
    print(f"🎯 Risk Assessment:")
    print(f"   Final Risk Level: {final_dashboard['risk_level'].upper()}")
    print(f"   Risk Score: {final_dashboard['risk_score']:.1f}/100")
    print(f"   Market Regime: {final_dashboard['market_regime']}")
    
    print(f"\n💰 Portfolio Performance:")
    initial_value = risk_mgr.initial_capital
    final_value = final_dashboard['portfolio']['value']
    total_return = (final_value / initial_value - 1) * 100
    
    print(f"   Initial Capital: ${initial_value:,.2f}")
    print(f"   Final Value: ${final_value:,.2f}")
    print(f"   Total Return: {total_return:+.1f}%")
    print(f"   Max Drawdown: {final_dashboard['portfolio']['drawdown_max']}")
    print(f"   Current Drawdown: {final_dashboard['portfolio']['drawdown_current']}")
    print(f"   Sharpe Ratio: {final_dashboard['portfolio']['sharpe_ratio']}")
    
    print(f"\n📈 Market Analysis:")
    print(f"   Final Volatility: {final_dashboard['market']['volatility']}")
    print(f"   Volatility Percentile: {final_dashboard['market']['volatility_percentile']}")
    print(f"   Market Stress Index: {final_dashboard['market']['stress_index']}")
    
    print(f"\n⚙️ Final Risk Parameters:")
    print(f"   Max Position Size: {final_dashboard['risk_parameters']['max_position_size']}")
    print(f"   Stop Loss: {final_dashboard['risk_parameters']['stop_loss']}")
    print(f"   Max Leverage: {final_dashboard['risk_parameters']['max_leverage']}")
    print(f"   Max Exposure: {final_dashboard['risk_parameters']['max_exposure']}")
    
    print(f"\n🚨 Risk Controls:")
    print(f"   Emergency Mode: {final_dashboard['controls']['emergency_mode']}")
    print(f"   Trading Halted: {final_dashboard['controls']['halt_trading']}")
    if final_dashboard['controls']['halt_trading']:
        print(f"   Halt Reason: {final_dashboard['controls']['halt_reason']}")
    
    print(f"\n📋 Adjustment Summary:")
    print(f"   Total Adjustments: {final_dashboard['recent_adjustments']}")
    print(f"   Total Trades: {trading_sim.trade_count}")
    
    # Demonstrate current recommendations
    print(f"\n🎯 Current Recommendations:")
    
    # Position sizing
    for symbol in ['BTC/USDT', 'ETH/USDT']:
        size_low = risk_mgr.get_position_size_recommendation(symbol, signal_strength=0.3)
        size_high = risk_mgr.get_position_size_recommendation(symbol, signal_strength=1.0)
        print(f"   {symbol} Position Size: {size_low:.1%} (weak signal) to {size_high:.1%} (strong signal)")
    
    # Stop losses
    current_btc = market_sim.btc_price
    current_eth = market_sim.eth_price
    
    btc_stop = risk_mgr.get_stop_loss_recommendation('BTC/USDT', current_btc, 'buy')
    eth_stop = risk_mgr.get_stop_loss_recommendation('ETH/USDT', current_eth, 'buy')
    
    print(f"   BTC/USDT Stop Loss: ${btc_stop:,.2f} ({((btc_stop/current_btc)-1):.1%})")
    print(f"   ETH/USDT Stop Loss: ${eth_stop:,.2f} ({((eth_stop/current_eth)-1):.1%})")
    
    print(f"\n🎉 DYNAMIC RISK MANAGEMENT DEMO COMPLETE!")
    print("=" * 50)
    print("✅ Adaptive risk parameters based on market volatility")
    print("✅ Performance-driven position sizing adjustments")
    print("✅ Emergency controls during market stress")
    print("✅ Real-time risk monitoring and dashboard")
    print("✅ Intelligent stop loss recommendations")
    print("✅ Market regime detection and response")
    print("✅ Comprehensive risk metrics tracking")
    
    # Show the power of dynamic vs static risk management
    print(f"\n💡 DYNAMIC vs STATIC RISK MANAGEMENT:")
    print(f"   📊 Dynamic System Adapted {final_dashboard['recent_adjustments']} times")
    print(f"   📈 Responded to market volatility changes")
    print(f"   🛡️ Implemented emergency controls during crash")
    print(f"   🎯 Optimized position sizes based on conditions")
    print(f"   ⚡ Static system would have used same parameters throughout!")

if __name__ == "__main__":
    asyncio.run(demo_dynamic_risk_management()) 