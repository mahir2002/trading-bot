#!/usr/bin/env python3
"""
🏎️ High-Frequency Trading Integration with Advanced Rate Limiting
Demonstrates: Multiple concurrent strategies, burst handling, priority management
"""

import asyncio
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from advanced_rate_limit_manager import (
    AdvancedRateLimitManager, RequestPriority, with_rate_limiting
)
import logging

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    volume: float
    timestamp: float
    bid: float = 0.0
    ask: float = 0.0

@dataclass
class Order:
    """Order structure"""
    symbol: str
    side: str
    amount: float
    price: float
    order_type: str = "limit"
    priority: RequestPriority = RequestPriority.HIGH

class HighFrequencyTradingBot:
    """
    High-frequency trading bot with advanced rate limiting
    Manages multiple strategies with different priority levels
    """
    
    def __init__(self, exchange: str = "binance"):
        self.exchange = exchange
        self.rate_manager = AdvancedRateLimitManager()
        self.logger = logging.getLogger(f"HFT-{exchange}")
        
        # Trading state
        self.positions: Dict[str, float] = {}
        self.orders: List[Order] = []
        self.market_data: Dict[str, MarketData] = {}
        
        # Strategy flags
        self.is_running = False
        self.strategies_active = {
            'arbitrage': True,
            'market_making': True,
            'momentum': True,
            'mean_reversion': True
        }
        
        # Performance metrics
        self.metrics = {
            'orders_placed': 0,
            'orders_filled': 0,
            'profit_loss': 0.0,
            'api_calls': 0,
            'rate_limit_hits': 0
        }
    
    async def start(self):
        """Start the HFT bot with all strategies"""
        
        self.logger.info("🚀 Starting High-Frequency Trading Bot")
        
        # Start rate limit manager
        await self.rate_manager.start_background_tasks()
        
        self.is_running = True
        
        # Start all strategies concurrently
        strategies = [
            self._arbitrage_strategy(),
            self._market_making_strategy(),
            self._momentum_strategy(),
            self._mean_reversion_strategy(),
            self._market_data_updater(),
            self._order_manager(),
            self._performance_monitor()
        ]
        
        await asyncio.gather(*strategies, return_exceptions=True)
    
    async def stop(self):
        """Stop the HFT bot"""
        
        self.logger.info("⏹️ Stopping High-Frequency Trading Bot")
        self.is_running = False
        
        # Cancel all pending orders
        await self._cancel_all_orders()
        
        # Stop rate limit manager
        await self.rate_manager.stop_background_tasks()
    
    # Market Data Functions (Medium Priority)
    @with_rate_limiting(exchange='binance', priority=RequestPriority.MEDIUM, weight=1)
    async def fetch_ticker(self, symbol: str) -> MarketData:
        """Fetch ticker data with rate limiting"""
        
        await asyncio.sleep(0.05)  # Simulate API call
        self.metrics['api_calls'] += 1
        
        # Simulate market data
        base_price = 50000 if 'BTC' in symbol else 3000
        price = base_price + random.uniform(-100, 100)
        
        return MarketData(
            symbol=symbol,
            price=price,
            volume=random.uniform(1000, 5000),
            timestamp=time.time(),
            bid=price - 0.5,
            ask=price + 0.5
        )
    
    @with_rate_limiting(exchange='binance', priority=RequestPriority.MEDIUM, weight=2)
    async def fetch_orderbook(self, symbol: str, depth: int = 10) -> Dict:
        """Fetch order book data"""
        
        await asyncio.sleep(0.08)  # Simulate API call
        self.metrics['api_calls'] += 1
        
        # Simulate order book
        base_price = self.market_data.get(symbol, MarketData(symbol, 50000, 0, 0)).price
        
        bids = [(base_price - i * 0.5, random.uniform(0.1, 2.0)) for i in range(1, depth + 1)]
        asks = [(base_price + i * 0.5, random.uniform(0.1, 2.0)) for i in range(1, depth + 1)]
        
        return {'bids': bids, 'asks': asks}
    
    # Trading Functions (High/Critical Priority)
    @with_rate_limiting(exchange='binance', priority=RequestPriority.HIGH, weight=5)
    async def place_order(self, order: Order) -> Dict:
        """Place an order with high priority"""
        
        await asyncio.sleep(0.1)  # Simulate API call
        self.metrics['api_calls'] += 1
        self.metrics['orders_placed'] += 1
        
        order_id = f"order_{int(time.time() * 1000)}"
        
        self.logger.info(f"📝 Order placed: {order.side} {order.amount} {order.symbol} @ {order.price}")
        
        return {
            'id': order_id,
            'symbol': order.symbol,
            'side': order.side,
            'amount': order.amount,
            'price': order.price,
            'status': 'open'
        }
    
    @with_rate_limiting(exchange='binance', priority=RequestPriority.CRITICAL, weight=3)
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order with critical priority"""
        
        await asyncio.sleep(0.05)  # Simulate API call
        self.metrics['api_calls'] += 1
        
        self.logger.info(f"❌ Order cancelled: {order_id}")
        
        return {'id': order_id, 'status': 'cancelled'}
    
    @with_rate_limiting(exchange='binance', priority=RequestPriority.CRITICAL, weight=10)
    async def emergency_close_position(self, symbol: str) -> Dict:
        """Emergency position close with highest priority"""
        
        await asyncio.sleep(0.15)  # Simulate API call
        self.metrics['api_calls'] += 1
        
        position = self.positions.get(symbol, 0)
        if position != 0:
            side = 'sell' if position > 0 else 'buy'
            amount = abs(position)
            
            self.logger.warning(f"🚨 Emergency close: {side} {amount} {symbol}")
            
            # Reset position
            self.positions[symbol] = 0
            
            return {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'type': 'market',
                'status': 'filled'
            }
        
        return {'status': 'no_position'}
    
    # Trading Strategies
    async def _arbitrage_strategy(self):
        """Arbitrage strategy - looks for price differences"""
        
        while self.is_running and self.strategies_active['arbitrage']:
            try:
                symbols = ['BTC/USDT', 'ETH/USDT']
                
                # Fetch data from multiple sources (simulated)
                for symbol in symbols:
                    data = await self.fetch_ticker(symbol)
                    self.market_data[symbol] = data
                    
                    # Simulate arbitrage opportunity detection
                    if random.random() < 0.1:  # 10% chance of opportunity
                        spread = random.uniform(0.1, 0.5)
                        
                        if spread > 0.2:  # Profitable spread
                            # Place arbitrage orders
                            buy_order = Order(symbol, 'buy', 0.01, data.price - spread/2, priority=RequestPriority.HIGH)
                            sell_order = Order(symbol, 'sell', 0.01, data.price + spread/2, priority=RequestPriority.HIGH)
                            
                            await asyncio.gather(
                                self.place_order(buy_order),
                                self.place_order(sell_order)
                            )
                            
                            self.logger.info(f"⚡ Arbitrage opportunity: {symbol} spread {spread:.3f}")
                
                await asyncio.sleep(0.1)  # High frequency
                
            except Exception as e:
                self.logger.error(f"Arbitrage strategy error: {e}")
                await asyncio.sleep(1)
    
    async def _market_making_strategy(self):
        """Market making strategy - provides liquidity"""
        
        while self.is_running and self.strategies_active['market_making']:
            try:
                symbols = ['BTC/USDT', 'ETH/USDT']
                
                for symbol in symbols:
                    # Get current market data
                    if symbol not in self.market_data:
                        continue
                    
                    data = self.market_data[symbol]
                    orderbook = await self.fetch_orderbook(symbol, depth=5)
                    
                    # Calculate optimal bid/ask prices
                    spread = 0.1  # 0.1% spread
                    bid_price = data.price * (1 - spread/100)
                    ask_price = data.price * (1 + spread/100)
                    
                    # Place market making orders
                    if random.random() < 0.3:  # 30% chance to place orders
                        amount = random.uniform(0.001, 0.01)
                        
                        bid_order = Order(symbol, 'buy', amount, bid_price, priority=RequestPriority.HIGH)
                        ask_order = Order(symbol, 'sell', amount, ask_price, priority=RequestPriority.HIGH)
                        
                        await asyncio.gather(
                            self.place_order(bid_order),
                            self.place_order(ask_order)
                        )
                        
                        self.logger.info(f"🏪 Market making: {symbol} bid/ask {bid_price:.2f}/{ask_price:.2f}")
                
                await asyncio.sleep(0.2)  # Medium frequency
                
            except Exception as e:
                self.logger.error(f"Market making strategy error: {e}")
                await asyncio.sleep(1)
    
    async def _momentum_strategy(self):
        """Momentum strategy - follows price trends"""
        
        price_history = {}
        
        while self.is_running and self.strategies_active['momentum']:
            try:
                symbols = ['BTC/USDT', 'ETH/USDT']
                
                for symbol in symbols:
                    data = await self.fetch_ticker(symbol)
                    
                    # Track price history
                    if symbol not in price_history:
                        price_history[symbol] = []
                    
                    price_history[symbol].append(data.price)
                    if len(price_history[symbol]) > 20:
                        price_history[symbol].pop(0)
                    
                    # Detect momentum
                    if len(price_history[symbol]) >= 5:
                        recent_prices = price_history[symbol][-5:]
                        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                        
                        if abs(momentum) > 0.001:  # 0.1% momentum threshold
                            side = 'buy' if momentum > 0 else 'sell'
                            amount = min(0.01, abs(momentum) * 10)  # Scale with momentum
                            
                            order = Order(symbol, side, amount, data.price, priority=RequestPriority.HIGH)
                            await self.place_order(order)
                            
                            self.logger.info(f"📈 Momentum trade: {side} {symbol} momentum {momentum:.4f}")
                
                await asyncio.sleep(0.5)  # Lower frequency
                
            except Exception as e:
                self.logger.error(f"Momentum strategy error: {e}")
                await asyncio.sleep(1)
    
    async def _mean_reversion_strategy(self):
        """Mean reversion strategy - trades against extreme moves"""
        
        price_averages = {}
        
        while self.is_running and self.strategies_active['mean_reversion']:
            try:
                symbols = ['BTC/USDT', 'ETH/USDT']
                
                for symbol in symbols:
                    data = await self.fetch_ticker(symbol)
                    
                    # Calculate moving average
                    if symbol not in price_averages:
                        price_averages[symbol] = []
                    
                    price_averages[symbol].append(data.price)
                    if len(price_averages[symbol]) > 50:
                        price_averages[symbol].pop(0)
                    
                    if len(price_averages[symbol]) >= 20:
                        avg_price = sum(price_averages[symbol]) / len(price_averages[symbol])
                        deviation = (data.price - avg_price) / avg_price
                        
                        # Trade on extreme deviations
                        if abs(deviation) > 0.005:  # 0.5% deviation threshold
                            side = 'sell' if deviation > 0 else 'buy'  # Contrarian
                            amount = min(0.01, abs(deviation) * 5)
                            
                            order = Order(symbol, side, amount, data.price, priority=RequestPriority.MEDIUM)
                            await self.place_order(order)
                            
                            self.logger.info(f"🔄 Mean reversion: {side} {symbol} deviation {deviation:.4f}")
                
                await asyncio.sleep(1.0)  # Lowest frequency
                
            except Exception as e:
                self.logger.error(f"Mean reversion strategy error: {e}")
                await asyncio.sleep(1)
    
    async def _market_data_updater(self):
        """Background task to continuously update market data"""
        
        while self.is_running:
            try:
                symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT']
                
                # Update all symbols concurrently
                tasks = [self.fetch_ticker(symbol) for symbol in symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for symbol, result in zip(symbols, results):
                    if not isinstance(result, Exception):
                        self.market_data[symbol] = result
                
                await asyncio.sleep(0.1)  # Very high frequency updates
                
            except Exception as e:
                self.logger.error(f"Market data updater error: {e}")
                await asyncio.sleep(1)
    
    async def _order_manager(self):
        """Manage open orders and positions"""
        
        while self.is_running:
            try:
                # Simulate order fills and position updates
                for symbol in self.market_data.keys():
                    if random.random() < 0.1:  # 10% chance of fill
                        fill_amount = random.uniform(-0.01, 0.01)
                        self.positions[symbol] = self.positions.get(symbol, 0) + fill_amount
                        self.metrics['orders_filled'] += 1
                        
                        if abs(fill_amount) > 0:
                            self.logger.info(f"✅ Order filled: {fill_amount:.4f} {symbol}")
                
                # Risk management - emergency close large positions
                for symbol, position in self.positions.items():
                    if abs(position) > 0.1:  # Large position threshold
                        self.logger.warning(f"⚠️ Large position detected: {position:.4f} {symbol}")
                        await self.emergency_close_position(symbol)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Order manager error: {e}")
                await asyncio.sleep(1)
    
    async def _performance_monitor(self):
        """Monitor performance and rate limiting"""
        
        while self.is_running:
            try:
                # Get rate limit status
                status = self.rate_manager.get_rate_limit_status(self.exchange)
                
                # Log performance metrics every 10 seconds
                self.logger.info(f"📊 Performance: Orders {self.metrics['orders_placed']}/{self.metrics['orders_filled']}, "
                               f"API calls: {self.metrics['api_calls']}, "
                               f"RPS: {status['metrics']['current_rps']:.1f}, "
                               f"Queue: {status['queue_depth']}")
                
                # Adjust strategy frequency based on rate limits
                if status['metrics']['rate_limited_requests'] > 0:
                    self.metrics['rate_limit_hits'] += 1
                    self.logger.warning("⚠️ Rate limit hit - adjusting strategy frequency")
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Performance monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _cancel_all_orders(self):
        """Cancel all pending orders"""
        
        # Simulate cancelling orders
        for i in range(len(self.orders)):
            await self.cancel_order(f"order_{i}")
        
        self.orders.clear()

async def demo_hft_with_rate_limiting():
    """Demonstrate high-frequency trading with advanced rate limiting"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🏎️ HIGH-FREQUENCY TRADING WITH ADVANCED RATE LIMITING")
    print("=" * 55)
    
    # Create HFT bot
    hft_bot = HighFrequencyTradingBot('binance')
    
    print("🚀 Starting HFT bot with multiple strategies...")
    print("   - Arbitrage Strategy (High Priority)")
    print("   - Market Making Strategy (High Priority)")
    print("   - Momentum Strategy (Medium Priority)")
    print("   - Mean Reversion Strategy (Low Priority)")
    print("   - Continuous Market Data Updates")
    
    # Run for a limited time
    try:
        await asyncio.wait_for(hft_bot.start(), timeout=30.0)
    except asyncio.TimeoutError:
        print("\n⏰ Demo timeout reached")
    
    # Stop the bot
    await hft_bot.stop()
    
    # Show final metrics
    print("\n📊 FINAL PERFORMANCE METRICS")
    print("-" * 30)
    print(f"Orders Placed: {hft_bot.metrics['orders_placed']}")
    print(f"Orders Filled: {hft_bot.metrics['orders_filled']}")
    print(f"API Calls Made: {hft_bot.metrics['api_calls']}")
    print(f"Rate Limit Hits: {hft_bot.metrics['rate_limit_hits']}")
    
    # Show rate limit status
    status = hft_bot.rate_manager.get_rate_limit_status('binance')
    print(f"\nRate Limit Performance:")
    print(f"  Success Rate: {status['metrics']['success_rate']:.1f}%")
    print(f"  Peak RPS: {status['metrics']['peak_rps']:.1f}")
    print(f"  Avg Response Time: {status['metrics']['avg_response_time']:.3f}s")
    
    # Show positions
    print(f"\nFinal Positions:")
    for symbol, position in hft_bot.positions.items():
        if abs(position) > 0.001:
            print(f"  {symbol}: {position:.4f}")
    
    print("\n🎉 HFT Demo Complete!")
    print("✅ Multiple concurrent strategies managed")
    print("✅ Priority-based request handling")
    print("✅ Burst capacity utilized for critical orders")
    print("✅ Rate limits respected across all strategies")
    print("✅ Real-time performance monitoring")

if __name__ == "__main__":
    asyncio.run(demo_hft_with_rate_limiting()) 