#!/usr/bin/env python3
"""
🎯 Advanced Order Execution Demo
Demonstrates: All sophisticated order types and intelligent execution strategies
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from advanced_order_manager import (
    AdvancedOrderManager, OrderType, OrderSide, OrderStatus,
    create_market_order, create_limit_order, create_stop_loss_order,
    create_trailing_stop_order, create_iceberg_order, create_twap_order,
    create_bracket_order
)
import logging

class MarketDataSimulator:
    """Simulates realistic market data for order execution testing"""
    
    def __init__(self, initial_price: float = 50000):
        self.current_price = initial_price
        self.trend = 0.0
        self.volatility = 0.002
        
    def get_next_price(self) -> float:
        """Generate next price with realistic movement"""
        
        # Add trend and random volatility
        price_change = self.trend + random.gauss(0, self.volatility)
        self.current_price *= (1 + price_change)
        
        # Occasionally change trend
        if random.random() < 0.05:
            self.trend = random.gauss(0, 0.001)
        
        return self.current_price
    
    def get_market_data(self) -> dict:
        """Get complete market data"""
        
        price = self.get_next_price()
        spread = price * 0.0001  # 0.01% spread
        
        return {
            'price': price,
            'bid': price - spread/2,
            'ask': price + spread/2,
            'volume': random.uniform(1000, 5000),
            'timestamp': datetime.now()
        }

async def demo_advanced_orders():
    """Comprehensive demo of all advanced order types"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print("🎯 ADVANCED ORDER EXECUTION DEMO")
    print("=" * 40)
    
    # Initialize order manager and market simulator
    order_manager = AdvancedOrderManager(logger)
    market_sim = MarketDataSimulator(50000)  # Start at $50,000
    
    # Start background processing
    await order_manager.start_background_processing()
    
    print(f"📊 Starting price: ${market_sim.current_price:,.2f}")
    print()
    
    # Demo 1: Basic Order Types
    print("🔸 DEMO 1: Basic Order Types")
    print("-" * 30)
    
    # Market Order
    market_order = create_market_order("BTC/USDT", OrderSide.BUY, 0.01, strategy_name="Demo_Market")
    await order_manager.submit_order(market_order)
    print(f"📝 Market Order: {market_order.order_id}")
    
    # Limit Order
    current_price = market_sim.current_price
    limit_price = current_price * 0.99  # 1% below current price
    limit_order = create_limit_order("BTC/USDT", OrderSide.BUY, 0.02, limit_price, strategy_name="Demo_Limit")
    await order_manager.submit_order(limit_order)
    print(f"📝 Limit Order: {limit_order.order_id} @ ${limit_price:,.2f}")
    
    # Stop Loss Order
    stop_price = current_price * 0.95  # 5% below current price
    stop_order = create_stop_loss_order("BTC/USDT", OrderSide.SELL, 0.01, stop_price, strategy_name="Demo_StopLoss")
    await order_manager.submit_order(stop_order)
    print(f"📝 Stop Loss: {stop_order.order_id} @ ${stop_price:,.2f}")
    
    # Process some market updates
    for i in range(5):
        market_data = market_sim.get_market_data()
        order_manager.update_market_data("BTC/USDT", market_data)
        await order_manager.process_orders()
        await asyncio.sleep(0.2)
    
    print(f"💹 Current price: ${market_sim.current_price:,.2f}")
    print()
    
    # Demo 2: Advanced Order Types
    print("🔸 DEMO 2: Advanced Order Types")
    print("-" * 30)
    
    # Trailing Stop Order
    trail_order = create_trailing_stop_order("BTC/USDT", OrderSide.SELL, 0.015, 2.0, strategy_name="Demo_TrailingStop")
    await order_manager.submit_order(trail_order)
    print(f"📝 Trailing Stop: {trail_order.order_id} (2% trail)")
    
    # Iceberg Order
    iceberg_price = market_sim.current_price * 1.01  # 1% above current
    iceberg_order = create_iceberg_order("BTC/USDT", OrderSide.SELL, 0.1, iceberg_price, 0.02, strategy_name="Demo_Iceberg")
    await order_manager.submit_order(iceberg_order)
    print(f"📝 Iceberg Order: {iceberg_order.order_id} (0.1 total, 0.02 visible)")
    
    # TWAP Order
    twap_order = create_twap_order("BTC/USDT", OrderSide.BUY, 0.05, 5, strategy_name="Demo_TWAP")  # 5 minutes
    await order_manager.submit_order(twap_order)
    print(f"📝 TWAP Order: {twap_order.order_id} (5 min duration)")
    
    # Bracket Order
    entry_price = market_sim.current_price * 0.98
    profit_price = entry_price * 1.03  # 3% profit
    loss_price = entry_price * 0.97    # 3% loss
    bracket_order = create_bracket_order("BTC/USDT", OrderSide.BUY, 0.02, entry_price, profit_price, loss_price, strategy_name="Demo_Bracket")
    await order_manager.submit_order(bracket_order)
    print(f"📝 Bracket Order: {bracket_order.order_id}")
    print(f"   Entry: ${entry_price:,.2f}, Profit: ${profit_price:,.2f}, Stop: ${loss_price:,.2f}")
    
    print()
    
    # Demo 3: Market Simulation and Order Execution
    print("🔸 DEMO 3: Live Order Execution")
    print("-" * 30)
    
    print("🎬 Running market simulation...")
    
    # Simulate market for 30 seconds
    start_time = time.time()
    update_count = 0
    
    while time.time() - start_time < 30:
        # Generate market data
        market_data = market_sim.get_market_data()
        order_manager.update_market_data("BTC/USDT", market_data)
        
        # Process orders
        await order_manager.process_orders()
        
        # Show periodic updates
        update_count += 1
        if update_count % 20 == 0:
            print(f"💹 Price: ${market_data['price']:,.2f}, Active orders: {len([o for o in order_manager.orders.values() if o.status == OrderStatus.OPEN])}")
        
        await asyncio.sleep(0.1)
    
    print()
    
    # Demo 4: Order Status and Results
    print("🔸 DEMO 4: Order Status and Results")
    print("-" * 30)
    
    # Show all order statuses
    all_orders = list(order_manager.orders.values())
    
    for order in all_orders:
        status = order_manager.get_order_status(order.order_id)
        if status:
            print(f"📋 {status['order_type'].upper()} Order ({status['strategy_name']}):")
            print(f"   ID: {status['order_id']}")
            print(f"   Status: {status['status']}")
            print(f"   Quantity: {status['quantity']} (Filled: {status['filled_quantity']})")
            if status['average_price']:
                print(f"   Avg Price: ${status['average_price']:,.2f}")
            print(f"   Created: {status['created_at'][:19]}")
            print()
    
    # Demo 5: Performance Metrics
    print("🔸 DEMO 5: Performance Metrics")
    print("-" * 30)
    
    metrics = order_manager.get_performance_metrics()
    
    print(f"📊 Order Execution Performance:")
    print(f"   Total Orders: {metrics['total_orders']}")
    print(f"   Filled Orders: {metrics['filled_orders']}")
    print(f"   Cancelled Orders: {metrics['cancelled_orders']}")
    print(f"   Fill Rate: {metrics['fill_rate']}")
    print(f"   Active Orders: {metrics['active_orders']}")
    
    print(f"\n📈 Order Type Distribution:")
    for order_type, count in metrics['order_type_distribution'].items():
        print(f"   {order_type.upper()}: {count}")
    
    # Demo 6: Advanced Execution Scenarios
    print("\n🔸 DEMO 6: Advanced Execution Scenarios")
    print("-" * 30)
    
    # Scenario 1: High-frequency market making
    print("🏪 Scenario 1: Market Making Strategy")
    
    current_price = market_sim.current_price
    spread = 0.002  # 0.2% spread
    
    # Place bid and ask orders
    bid_price = current_price * (1 - spread)
    ask_price = current_price * (1 + spread)
    
    bid_order = create_limit_order("BTC/USDT", OrderSide.BUY, 0.01, bid_price, strategy_name="MarketMaking_Bid")
    ask_order = create_limit_order("BTC/USDT", OrderSide.SELL, 0.01, ask_price, strategy_name="MarketMaking_Ask")
    
    await order_manager.submit_order(bid_order)
    await order_manager.submit_order(ask_order)
    
    print(f"   Bid: ${bid_price:,.2f}, Ask: ${ask_price:,.2f}")
    
    # Scenario 2: Risk management with stops
    print("\n🛡️ Scenario 2: Risk Management")
    
    # Large position with multiple stop levels
    position_size = 0.1
    entry_price = current_price
    
    # Tight stop (2%)
    tight_stop = create_stop_loss_order("BTC/USDT", OrderSide.SELL, position_size * 0.3, entry_price * 0.98, strategy_name="Risk_TightStop")
    
    # Medium stop (5%)
    medium_stop = create_stop_loss_order("BTC/USDT", OrderSide.SELL, position_size * 0.4, entry_price * 0.95, strategy_name="Risk_MediumStop")
    
    # Wide stop (10%)
    wide_stop = create_stop_loss_order("BTC/USDT", OrderSide.SELL, position_size * 0.3, entry_price * 0.90, strategy_name="Risk_WideStop")
    
    await order_manager.submit_order(tight_stop)
    await order_manager.submit_order(medium_stop)
    await order_manager.submit_order(wide_stop)
    
    print(f"   Layered stops: 2%, 5%, 10% below ${entry_price:,.2f}")
    
    # Scenario 3: Large order execution
    print("\n🐋 Scenario 3: Large Order Execution")
    
    # Use TWAP for large order
    large_twap = create_twap_order("BTC/USDT", OrderSide.BUY, 0.5, 10, slice_count=20, strategy_name="LargeOrder_TWAP")
    await order_manager.submit_order(large_twap)
    
    # Use Iceberg for stealth execution
    stealth_iceberg = create_iceberg_order("BTC/USDT", OrderSide.SELL, 0.3, current_price * 1.005, 0.05, strategy_name="LargeOrder_Stealth")
    await order_manager.submit_order(stealth_iceberg)
    
    print(f"   TWAP: 0.5 BTC over 10 minutes")
    print(f"   Iceberg: 0.3 BTC (0.05 visible)")
    
    # Run final simulation
    print("\n🎬 Final execution simulation (10 seconds)...")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        market_data = market_sim.get_market_data()
        order_manager.update_market_data("BTC/USDT", market_data)
        await order_manager.process_orders()
        await asyncio.sleep(0.1)
    
    # Final metrics
    print("\n📊 FINAL RESULTS")
    print("=" * 20)
    
    final_metrics = order_manager.get_performance_metrics()
    final_price = market_sim.current_price
    
    print(f"💹 Final Price: ${final_price:,.2f}")
    print(f"📈 Total Orders Created: {final_metrics['total_orders']}")
    print(f"✅ Orders Filled: {final_metrics['filled_orders']}")
    print(f"📊 Fill Rate: {final_metrics['fill_rate']}")
    print(f"🔄 Active Orders: {final_metrics['active_orders']}")
    
    # Show filled orders
    filled_orders = [o for o in order_manager.orders.values() if o.status == OrderStatus.FILLED]
    if filled_orders:
        print(f"\n✅ FILLED ORDERS ({len(filled_orders)}):")
        for order in filled_orders[-5:]:  # Show last 5 filled orders
            print(f"   {order.order_type.value.upper()}: {order.filled_quantity} @ ${order.average_price:,.2f} ({order.strategy_name})")
    
    # Show active orders
    active_orders = [o for o in order_manager.orders.values() if o.status == OrderStatus.OPEN]
    if active_orders:
        print(f"\n🔄 ACTIVE ORDERS ({len(active_orders)}):")
        for order in active_orders[:5]:  # Show first 5 active orders
            price_str = f"${order.price:,.2f}" if order.price else "MARKET"
            print(f"   {order.order_type.value.upper()}: {order.quantity} @ {price_str} ({order.strategy_name})")
    
    # Stop background processing
    await order_manager.stop_background_processing()
    
    print("\n🎉 ADVANCED ORDER EXECUTION DEMO COMPLETE!")
    print("=" * 45)
    print("✅ Market Orders - Immediate execution")
    print("✅ Limit Orders - Price-conditional execution")
    print("✅ Stop Loss Orders - Risk management")
    print("✅ Trailing Stops - Dynamic profit protection")
    print("✅ Iceberg Orders - Stealth execution")
    print("✅ TWAP Orders - Time-distributed execution")
    print("✅ Bracket Orders - Complete trade management")
    print("✅ Multi-strategy coordination")
    print("✅ Real-time order processing")
    print("✅ Comprehensive performance tracking")

if __name__ == "__main__":
    asyncio.run(demo_advanced_orders()) 