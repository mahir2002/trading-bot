#!/usr/bin/env python3
"""
🛡️ Stop-Loss and Take-Profit System Demonstration
Shows comprehensive SL/TP management with multiple strategies and scenarios
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
import logging
from typing import Dict, List

from stop_loss_take_profit_manager import (
    StopLossTakeProfitManager, StopLossType, TakeProfitType, OrderSide,
    create_position_with_sltp, create_trailing_stop_position
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sltp_demo.log')
    ]
)

logger = logging.getLogger(__name__)

class MarketSimulator:
    """Simulate realistic market price movements"""
    
    def __init__(self):
        self.prices = {
            'BTC/USDT': 45000.0,
            'ETH/USDT': 3000.0,
            'ADA/USDT': 0.50,
            'SOL/USDT': 100.0
        }
        
        self.volatilities = {
            'BTC/USDT': 0.02,
            'ETH/USDT': 0.025,
            'ADA/USDT': 0.03,
            'SOL/USDT': 0.035
        }
        
        self.trends = {
            'BTC/USDT': 'sideways',
            'ETH/USDT': 'bullish',
            'ADA/USDT': 'bearish',
            'SOL/USDT': 'volatile'
        }
    
    def get_next_price(self, symbol: str) -> Dict:
        """Generate next price with realistic movement"""
        
        current_price = self.prices[symbol]
        volatility = self.volatilities[symbol]
        trend = self.trends[symbol]
        
        # Base random movement
        random_change = random.gauss(0, volatility)
        
        # Apply trend bias
        trend_bias = 0
        if trend == 'bullish':
            trend_bias = 0.0005  # 0.05% upward bias
        elif trend == 'bearish':
            trend_bias = -0.0005  # 0.05% downward bias
        elif trend == 'volatile':
            trend_bias = random.choice([-0.001, 0.001])  # Random strong moves
        
        # Calculate new price
        price_change = random_change + trend_bias
        new_price = current_price * (1 + price_change)
        
        # Update stored price
        self.prices[symbol] = new_price
        
        # Calculate additional metrics
        high_24h = new_price * (1 + abs(random.gauss(0, volatility * 0.5)))
        low_24h = new_price * (1 - abs(random.gauss(0, volatility * 0.5)))
        volume = random.uniform(1000000, 10000000)
        atr = new_price * volatility * 2  # Approximate ATR
        
        return {
            'symbol': symbol,
            'price': new_price,
            'bid': new_price * 0.9995,
            'ask': new_price * 1.0005,
            'volume': volume,
            'high_24h': high_24h,
            'low_24h': low_24h,
            'volatility': volatility,
            'atr': atr
        }

async def demo_basic_stop_loss_take_profit():
    """Demonstrate basic SL/TP functionality"""
    
    print("\n" + "="*80)
    print("🛡️ BASIC STOP-LOSS AND TAKE-PROFIT DEMONSTRATION")
    print("="*80)
    
    # Initialize manager
    sltp_manager = StopLossTakeProfitManager(logger)
    market_sim = MarketSimulator()
    
    # Create positions with basic SL/TP
    print("\n📍 Creating positions with basic SL/TP orders...")
    
    positions_data = [
        ('BTC/USDT', OrderSide.BUY, 0.1, 45000.0, 0.02, 0.04),   # 2% SL, 4% TP
        ('ETH/USDT', OrderSide.BUY, 1.0, 3000.0, 0.015, 0.03),   # 1.5% SL, 3% TP
        ('ADA/USDT', OrderSide.SELL, 1000, 0.50, 0.025, 0.05),   # 2.5% SL, 5% TP (short)
    ]
    
    created_positions = []
    for symbol, side, quantity, entry_price, sl_pct, tp_pct in positions_data:
        position, sl_order, tp_order = create_position_with_sltp(
            symbol, side, quantity, entry_price, sl_pct, tp_pct
        )
        created_positions.append((position, sl_order, tp_order))
        
        print(f"  ✅ {side.value.upper()} {quantity} {symbol} @ ${entry_price:,.2f}")
        print(f"     🛡️ Stop-Loss: ${sl_order.trigger_price:,.2f} ({sl_pct*100:.1f}%)")
        print(f"     💰 Take-Profit: ${tp_order.trigger_price:,.2f} ({tp_pct*100:.1f}%)")
    
    # Start background processing
    await sltp_manager.start_background_processing()
    
    # Simulate market movements
    print(f"\n📈 Simulating market movements for 30 seconds...")
    
    start_time = time.time()
    update_count = 0
    
    while time.time() - start_time < 30:
        # Update market data for all symbols
        for symbol in ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']:
            market_data = market_sim.get_next_price(symbol)
            sltp_manager.update_market_data(**market_data)
        
        update_count += 1
        
        # Show periodic updates
        if update_count % 50 == 0:
            elapsed = time.time() - start_time
            print(f"  ⏱️ {elapsed:.1f}s - Market updates: {update_count}")
            
            # Show current prices and position status
            for symbol in ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']:
                current_price = sltp_manager.market_data[symbol].price
                print(f"    {symbol}: ${current_price:,.2f}")
        
        await asyncio.sleep(0.1)
    
    # Stop processing
    await sltp_manager.stop_background_processing()
    
    # Show final results
    print(f"\n📊 Final Results:")
    metrics = sltp_manager.get_performance_metrics()
    
    print(f"  Stop-Loss Orders:")
    print(f"    Total: {metrics['stop_loss_metrics']['total_orders']}")
    print(f"    Triggered: {metrics['stop_loss_metrics']['triggered_orders']}")
    print(f"    Trigger Rate: {metrics['stop_loss_metrics']['trigger_rate']}")
    
    print(f"  Take-Profit Orders:")
    print(f"    Total: {metrics['take_profit_metrics']['total_orders']}")
    print(f"    Triggered: {metrics['take_profit_metrics']['triggered_orders']}")
    print(f"    Trigger Rate: {metrics['take_profit_metrics']['trigger_rate']}")
    
    print(f"  Active Positions: {metrics['overall']['active_positions']}")
    
    return sltp_manager

async def demo_trailing_stop_loss():
    """Demonstrate trailing stop-loss functionality"""
    
    print("\n" + "="*80)
    print("📈 TRAILING STOP-LOSS DEMONSTRATION")
    print("="*80)
    
    # Initialize manager
    sltp_manager = StopLossTakeProfitManager(logger)
    market_sim = MarketSimulator()
    
    # Force bullish trend for demonstration
    market_sim.trends['SOL/USDT'] = 'bullish'
    
    # Create position with trailing stop
    print("\n📍 Creating position with trailing stop-loss...")
    
    position, sl_order, tp_order = create_trailing_stop_position(
        'SOL/USDT', OrderSide.BUY, 10.0, 100.0, 0.03, 0.08  # 3% trailing, 8% TP
    )
    
    print(f"  ✅ BUY 10.0 SOL/USDT @ $100.00")
    print(f"     🔄 Trailing Stop: $97.00 (3% trail)")
    print(f"     💰 Take-Profit: $108.00 (8%)")
    
    # Start background processing
    await sltp_manager.start_background_processing()
    
    # Track trailing stop updates
    print(f"\n📈 Tracking trailing stop adjustments...")
    
    last_stop_price = sl_order.trigger_price
    last_price = 100.0
    
    for i in range(100):  # 10 seconds of updates
        # Update market data
        market_data = market_sim.get_next_price('SOL/USDT')
        sltp_manager.update_market_data(**market_data)
        
        current_price = market_data['price']
        
        # Check if trailing stop was updated
        current_sl = sltp_manager.stop_loss_orders[sl_order.sl_id]
        if current_sl.trigger_price != last_stop_price:
            print(f"  🔄 Price: ${current_price:.2f} → Stop updated: ${last_stop_price:.2f} → ${current_sl.trigger_price:.2f}")
            last_stop_price = current_sl.trigger_price
        
        # Show significant price moves
        price_change = (current_price - last_price) / last_price
        if abs(price_change) > 0.01:  # 1% move
            direction = "📈" if price_change > 0 else "📉"
            print(f"  {direction} Price move: ${last_price:.2f} → ${current_price:.2f} ({price_change*100:+.1f}%)")
            last_price = current_price
        
        # Check if position still exists
        if position.position_id not in sltp_manager.positions:
            print(f"  🎯 Position closed!")
            break
        
        await asyncio.sleep(0.1)
    
    # Stop processing
    await sltp_manager.stop_background_processing()
    
    # Show results
    print(f"\n📊 Trailing Stop Results:")
    if position.position_id in sltp_manager.positions:
        final_position = sltp_manager.positions[position.position_id]
        final_sl = sltp_manager.stop_loss_orders[sl_order.sl_id]
        print(f"  Position still active:")
        print(f"    Current Price: ${final_position.current_price:.2f}")
        print(f"    Current Stop: ${final_sl.trigger_price:.2f}")
        print(f"    Unrealized P&L: ${final_position.unrealized_pnl:+.2f}")
    else:
        print(f"  Position was closed by SL/TP trigger")
    
    return sltp_manager

async def demo_advanced_strategies():
    """Demonstrate advanced SL/TP strategies"""
    
    print("\n" + "="*80)
    print("🎯 ADVANCED STOP-LOSS AND TAKE-PROFIT STRATEGIES")
    print("="*80)
    
    # Initialize manager
    sltp_manager = StopLossTakeProfitManager(logger)
    market_sim = MarketSimulator()
    
    print("\n📍 Creating positions with advanced strategies...")
    
    # 1. Volatility-based stop-loss
    position1 = sltp_manager.add_position('pos_vol', 'BTC/USDT', OrderSide.BUY, 0.1, 45000.0)
    sl1 = sltp_manager.create_stop_loss('pos_vol', StopLossType.VOLATILITY_BASED, volatility_multiplier=2.5)
    tp1 = sltp_manager.create_take_profit('pos_vol', TakeProfitType.FIXED_PERCENTAGE, percentage=0.05)
    
    print(f"  ✅ Volatility-based SL: BTC/USDT @ ${position1.entry_price:,.0f}")
    print(f"     🛡️ Vol-based Stop: ${sl1.trigger_price:,.2f}")
    
    # 2. ATR-based stop-loss
    position2 = sltp_manager.add_position('pos_atr', 'ETH/USDT', OrderSide.BUY, 1.0, 3000.0)
    sl2 = sltp_manager.create_stop_loss('pos_atr', StopLossType.ATR_BASED, atr_multiplier=2.0)
    tp2 = sltp_manager.create_take_profit('pos_atr', TakeProfitType.RISK_REWARD_RATIO, 
                                         stop_price=sl2.trigger_price, risk_reward_ratio=3.0)
    
    print(f"  ✅ ATR-based SL: ETH/USDT @ ${position2.entry_price:,.0f}")
    print(f"     🛡️ ATR-based Stop: ${sl2.trigger_price:,.2f}")
    print(f"     💰 Risk-Reward TP: ${tp2.trigger_price:,.2f} (3:1 ratio)")
    
    # 3. Scaled take-profit
    position3 = sltp_manager.add_position('pos_scaled', 'ADA/USDT', OrderSide.BUY, 1000, 0.50)
    sl3 = sltp_manager.create_stop_loss('pos_scaled', StopLossType.FIXED_PERCENTAGE, percentage=0.03)
    
    # Create multiple take-profit levels
    scale_levels = [
        {'percentage': 0.02, 'quantity_pct': 0.3},  # 2% profit, 30% position
        {'percentage': 0.04, 'quantity_pct': 0.4},  # 4% profit, 40% position
        {'percentage': 0.08, 'quantity_pct': 0.3},  # 8% profit, 30% position
    ]
    tp3 = sltp_manager.create_take_profit('pos_scaled', TakeProfitType.SCALED_PROFIT, scale_levels=scale_levels)
    
    print(f"  ✅ Scaled TP: ADA/USDT @ ${position3.entry_price:.3f}")
    print(f"     💰 Scaled levels: 2%/4%/8% profit targets")
    
    # Start background processing
    await sltp_manager.start_background_processing()
    
    # Simulate volatile market conditions
    print(f"\n📈 Simulating volatile market conditions...")
    
    # Increase volatility for demonstration
    market_sim.volatilities = {k: v * 2 for k, v in market_sim.volatilities.items()}
    
    for i in range(200):  # 20 seconds
        # Update all symbols
        for symbol in ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']:
            market_data = market_sim.get_next_price(symbol)
            sltp_manager.update_market_data(**market_data)
        
        # Show periodic updates
        if i % 50 == 0:
            print(f"  ⏱️ Update {i}: Checking strategy performance...")
            
            # Check position statuses
            active_positions = len(sltp_manager.positions)
            print(f"    Active positions: {active_positions}")
            
            if active_positions == 0:
                print(f"    All positions closed!")
                break
        
        await asyncio.sleep(0.1)
    
    # Stop processing
    await sltp_manager.stop_background_processing()
    
    # Show final results
    print(f"\n📊 Advanced Strategy Results:")
    metrics = sltp_manager.get_performance_metrics()
    
    print(f"  Overall Performance:")
    print(f"    Total Orders: {metrics['overall']['total_orders']}")
    print(f"    SL Trigger Rate: {metrics['stop_loss_metrics']['trigger_rate']}")
    print(f"    TP Trigger Rate: {metrics['take_profit_metrics']['trigger_rate']}")
    print(f"    Saved Loss: {metrics['stop_loss_metrics']['total_saved_loss']}")
    print(f"    Locked Profit: {metrics['take_profit_metrics']['total_locked_profit']}")
    
    return sltp_manager

async def demo_bracket_orders():
    """Demonstrate bracket order functionality (SL + TP together)"""
    
    print("\n" + "="*80)
    print("🎯 BRACKET ORDER DEMONSTRATION (SL + TP)")
    print("="*80)
    
    # Initialize manager
    sltp_manager = StopLossTakeProfitManager(logger)
    market_sim = MarketSimulator()
    
    print("\n📍 Creating bracket orders...")
    
    # Create multiple bracket orders with different strategies
    bracket_configs = [
        {
            'symbol': 'BTC/USDT', 'side': OrderSide.BUY, 'quantity': 0.05, 'entry': 45000.0,
            'sl_type': StopLossType.FIXED_PERCENTAGE, 'sl_kwargs': {'percentage': 0.02},
            'tp_type': TakeProfitType.FIXED_PERCENTAGE, 'tp_kwargs': {'percentage': 0.04}
        },
        {
            'symbol': 'ETH/USDT', 'side': OrderSide.BUY, 'quantity': 0.5, 'entry': 3000.0,
            'sl_type': StopLossType.TRAILING_STOP, 'sl_kwargs': {'trail_percentage': 0.025},
            'tp_type': TakeProfitType.FIXED_PERCENTAGE, 'tp_kwargs': {'percentage': 0.06}
        },
        {
            'symbol': 'SOL/USDT', 'side': OrderSide.SELL, 'quantity': 5.0, 'entry': 100.0,
            'sl_type': StopLossType.VOLATILITY_BASED, 'sl_kwargs': {'volatility_multiplier': 2.0},
            'tp_type': TakeProfitType.FIXED_PERCENTAGE, 'tp_kwargs': {'percentage': 0.05}
        }
    ]
    
    created_brackets = []
    for config in bracket_configs:
        # Create position
        position = sltp_manager.add_position(
            f"bracket_{len(created_brackets)}", 
            config['symbol'], 
            config['side'], 
            config['quantity'], 
            config['entry']
        )
        
        # Create bracket order
        sl_order, tp_order = sltp_manager.create_bracket_order(
            position.position_id,
            config['sl_type'],
            config['tp_type'],
            config['sl_kwargs'],
            config['tp_kwargs']
        )
        
        created_brackets.append((position, sl_order, tp_order))
        
        print(f"  ✅ {config['side'].value.upper()} {config['quantity']} {config['symbol']} @ ${config['entry']:,.2f}")
        print(f"     🛡️ {config['sl_type'].value}: ${sl_order.trigger_price:,.2f}")
        print(f"     💰 {config['tp_type'].value}: ${tp_order.trigger_price:,.2f}")
    
    # Start background processing
    await sltp_manager.start_background_processing()
    
    # Monitor bracket orders
    print(f"\n📊 Monitoring bracket orders...")
    
    start_time = time.time()
    last_summary_time = start_time
    
    while time.time() - start_time < 25:  # 25 seconds
        # Update market data
        for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
            market_data = market_sim.get_next_price(symbol)
            sltp_manager.update_market_data(**market_data)
        
        # Show summary every 5 seconds
        current_time = time.time()
        if current_time - last_summary_time >= 5:
            elapsed = current_time - start_time
            print(f"\n  ⏱️ {elapsed:.1f}s - Bracket Order Status:")
            
            active_positions = 0
            for i, (position, sl_order, tp_order) in enumerate(created_brackets):
                if position.position_id in sltp_manager.positions:
                    active_positions += 1
                    current_pos = sltp_manager.positions[position.position_id]
                    current_sl = sltp_manager.stop_loss_orders[sl_order.sl_id]
                    current_tp = sltp_manager.take_profit_orders[tp_order.tp_id]
                    
                    print(f"    Bracket {i+1}: {position.symbol}")
                    print(f"      Price: ${current_pos.current_price:.2f} | P&L: {current_pos.unrealized_pnl_percentage:+.1f}%")
                    print(f"      SL: ${current_sl.trigger_price:.2f} | TP: ${current_tp.trigger_price:.2f}")
                else:
                    print(f"    Bracket {i+1}: {position.symbol} - CLOSED")
            
            print(f"    Active brackets: {active_positions}/{len(created_brackets)}")
            
            if active_positions == 0:
                print(f"    All bracket orders completed!")
                break
            
            last_summary_time = current_time
        
        await asyncio.sleep(0.1)
    
    # Stop processing
    await sltp_manager.stop_background_processing()
    
    # Final summary
    print(f"\n📊 Bracket Order Results:")
    metrics = sltp_manager.get_performance_metrics()
    
    print(f"  Execution Summary:")
    print(f"    Stop-Loss Triggers: {metrics['stop_loss_metrics']['triggered_orders']}")
    print(f"    Take-Profit Triggers: {metrics['take_profit_metrics']['triggered_orders']}")
    print(f"    Average SL Slippage: {metrics['stop_loss_metrics']['avg_slippage']}")
    print(f"    Average TP Slippage: {metrics['take_profit_metrics']['avg_slippage']}")
    
    return sltp_manager

async def demo_position_management():
    """Demonstrate comprehensive position management with SL/TP"""
    
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE POSITION MANAGEMENT DEMONSTRATION")
    print("="*80)
    
    # Initialize manager
    sltp_manager = StopLossTakeProfitManager(logger)
    market_sim = MarketSimulator()
    
    # Create diverse portfolio
    print("\n📍 Creating diversified portfolio with SL/TP protection...")
    
    portfolio_positions = [
        ('BTC/USDT', OrderSide.BUY, 0.1, 45000.0),
        ('ETH/USDT', OrderSide.BUY, 1.0, 3000.0),
        ('ADA/USDT', OrderSide.BUY, 2000, 0.50),
        ('SOL/USDT', OrderSide.SELL, 10.0, 100.0),  # Short position
    ]
    
    created_positions = []
    for i, (symbol, side, quantity, entry_price) in enumerate(portfolio_positions):
        position_id = f"portfolio_{i}"
        
        # Create position
        position = sltp_manager.add_position(position_id, symbol, side, quantity, entry_price)
        
        # Create adaptive SL/TP based on position characteristics
        if symbol == 'BTC/USDT':
            # Conservative for BTC
            sl_order = sltp_manager.create_stop_loss(position_id, StopLossType.FIXED_PERCENTAGE, percentage=0.015)
            tp_order = sltp_manager.create_take_profit(position_id, TakeProfitType.FIXED_PERCENTAGE, percentage=0.03)
        elif symbol == 'ETH/USDT':
            # Trailing stop for ETH
            sl_order = sltp_manager.create_stop_loss(position_id, StopLossType.TRAILING_STOP, trail_percentage=0.02)
            tp_order = sltp_manager.create_take_profit(position_id, TakeProfitType.FIXED_PERCENTAGE, percentage=0.04)
        elif symbol == 'ADA/USDT':
            # Volatility-based for altcoin
            sl_order = sltp_manager.create_stop_loss(position_id, StopLossType.VOLATILITY_BASED, volatility_multiplier=2.0)
            tp_order = sltp_manager.create_take_profit(position_id, TakeProfitType.SCALED_PROFIT)
        else:  # SOL/USDT short
            # Fixed percentage for short
            sl_order = sltp_manager.create_stop_loss(position_id, StopLossType.FIXED_PERCENTAGE, percentage=0.025)
            tp_order = sltp_manager.create_take_profit(position_id, TakeProfitType.FIXED_PERCENTAGE, percentage=0.04)
        
        created_positions.append((position, sl_order, tp_order))
        
        print(f"  ✅ {side.value.upper()} {quantity} {symbol} @ ${entry_price:,.2f}")
        print(f"     🛡️ {sl_order.sl_type.value}: ${sl_order.trigger_price:,.2f}")
        print(f"     💰 {tp_order.tp_type.value}: ${tp_order.trigger_price:,.2f}")
    
    # Start background processing
    await sltp_manager.start_background_processing()
    
    # Portfolio monitoring
    print(f"\n📊 Portfolio monitoring with real-time SL/TP management...")
    
    monitoring_duration = 30  # 30 seconds
    start_time = time.time()
    last_report_time = start_time
    
    while time.time() - start_time < monitoring_duration:
        # Update market data for all symbols
        for symbol in ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']:
            market_data = market_sim.get_next_price(symbol)
            sltp_manager.update_market_data(**market_data)
        
        # Generate portfolio report every 10 seconds
        current_time = time.time()
        if current_time - last_report_time >= 10:
            elapsed = current_time - start_time
            print(f"\n  📊 Portfolio Report ({elapsed:.1f}s):")
            
            total_value = 0
            total_pnl = 0
            active_count = 0
            
            for i, (position, sl_order, tp_order) in enumerate(created_positions):
                if position.position_id in sltp_manager.positions:
                    active_count += 1
                    current_pos = sltp_manager.positions[position.position_id]
                    
                    total_value += current_pos.value
                    total_pnl += current_pos.unrealized_pnl
                    
                    print(f"    {current_pos.symbol}: ${current_pos.current_price:,.2f} | "
                          f"P&L: {current_pos.unrealized_pnl_percentage:+.1f}% (${current_pos.unrealized_pnl:+.2f})")
                else:
                    print(f"    {position.symbol}: CLOSED")
            
            print(f"    Portfolio Summary:")
            print(f"      Active Positions: {active_count}/{len(created_positions)}")
            print(f"      Total Value: ${total_value:,.2f}")
            print(f"      Total P&L: ${total_pnl:+.2f}")
            
            if active_count == 0:
                print(f"    All positions closed by SL/TP!")
                break
            
            last_report_time = current_time
        
        await asyncio.sleep(0.1)
    
    # Stop processing
    await sltp_manager.stop_background_processing()
    
    # Final portfolio analysis
    print(f"\n📊 Final Portfolio Analysis:")
    metrics = sltp_manager.get_performance_metrics()
    
    print(f"  Risk Management Performance:")
    print(f"    Stop-Loss Orders: {metrics['stop_loss_metrics']['total_orders']} created, {metrics['stop_loss_metrics']['triggered_orders']} triggered")
    print(f"    Take-Profit Orders: {metrics['take_profit_metrics']['total_orders']} created, {metrics['take_profit_metrics']['triggered_orders']} triggered")
    print(f"    Protection Effectiveness: {((metrics['stop_loss_metrics']['triggered_orders'] + metrics['take_profit_metrics']['triggered_orders']) / max(1, metrics['overall']['total_orders'])) * 100:.1f}%")
    
    # Show remaining positions
    remaining_positions = len(sltp_manager.positions)
    if remaining_positions > 0:
        print(f"  Remaining Positions: {remaining_positions}")
        for pos_id, position in sltp_manager.positions.items():
            print(f"    {position.symbol}: P&L {position.unrealized_pnl_percentage:+.1f}%")
    
    return sltp_manager

async def main():
    """Run comprehensive SL/TP demonstration"""
    
    print("🛡️ COMPREHENSIVE STOP-LOSS AND TAKE-PROFIT SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("Addresses: 'No explicit stop-loss or take-profit mechanisms are evident.'")
    print("Solution: Advanced SL/TP system with multiple strategies and intelligent execution")
    print("=" * 80)
    
    try:
        # Run all demonstrations
        await demo_basic_stop_loss_take_profit()
        await asyncio.sleep(2)
        
        await demo_trailing_stop_loss()
        await asyncio.sleep(2)
        
        await demo_advanced_strategies()
        await asyncio.sleep(2)
        
        await demo_bracket_orders()
        await asyncio.sleep(2)
        
        await demo_position_management()
        
        print("\n" + "="*80)
        print("🎉 STOP-LOSS AND TAKE-PROFIT DEMONSTRATION COMPLETED")
        print("="*80)
        print("✅ Successfully demonstrated:")
        print("  • Basic fixed percentage SL/TP orders")
        print("  • Trailing stop-loss with dynamic adjustments")
        print("  • Advanced strategies (volatility-based, ATR-based)")
        print("  • Risk-reward ratio and scaled take-profits")
        print("  • Bracket orders (SL + TP together)")
        print("  • Comprehensive portfolio protection")
        print("  • Real-time monitoring and execution")
        print("  • Performance metrics and analysis")
        print("\n🛡️ Your trading system now has professional-grade risk management!")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 