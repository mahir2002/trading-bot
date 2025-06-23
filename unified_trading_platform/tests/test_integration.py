#!/usr/bin/env python3
"""
Integration Testing Framework - End-to-End Testing
"""

import asyncio
import unittest
import time
import logging
from datetime import datetime
from typing import Dict, Any
import pandas as pd
import numpy as np

# Import platform modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trading_engine import TradingEngine
from core.event_bus import Event, EventPriority

class IntegrationTestFramework:
    """Integration testing framework."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trading_engine = None
        
    async def setup_test_environment(self):
        """Set up test environment."""
        try:
            test_config = {
                'trading_engine': {'max_events_per_second': 1000},
                'market_data': {'symbols': ['BTCUSDT', 'ETHUSDT']},
                'portfolio': {'initial_capital': 100000.0}
            }
            
            self.trading_engine = TradingEngine(test_config)
            await self.trading_engine.start()
            
            self.logger.info("Test environment setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup test environment: {e}")
            return False
    
    async def teardown_test_environment(self):
        """Clean up test environment."""
        try:
            if self.trading_engine:
                await self.trading_engine.stop()
            self.logger.info("Test environment teardown completed")
        except Exception as e:
            self.logger.error(f"Error during teardown: {e}")

class TradingScenarioTests(unittest.IsolatedAsyncioTestCase):
    """Integration tests for trading scenarios."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        self.framework = IntegrationTestFramework()
        self.assertTrue(await self.framework.setup_test_environment())
        
    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.framework.teardown_test_environment()
    
    async def test_complete_trading_cycle(self):
        """Test complete trading cycle."""
        self.framework.logger.info("Starting complete trading cycle test")
        
        start_time = time.time()
        
        # Market data update
        market_event = Event(
            type="market_data_update",
            data={
                'symbol': 'BTCUSDT',
                'price': 45000.0,
                'volume': 1000000,
                'timestamp': datetime.now().isoformat()
            },
            priority=EventPriority.HIGH
        )
        
        await self.framework.trading_engine.event_bus.emit(market_event)
        await asyncio.sleep(0.1)
        
        # AI prediction request
        ai_event = Event(
            type="prediction_request",
            data={'symbol': 'BTCUSDT'},
            priority=EventPriority.NORMAL
        )
        
        await self.framework.trading_engine.event_bus.emit(ai_event)
        await asyncio.sleep(0.5)
        
        # Trading signal
        signal_event = Event(
            type="signal_request",
            data={'symbol': 'BTCUSDT'},
            priority=EventPriority.NORMAL
        )
        
        await self.framework.trading_engine.event_bus.emit(signal_event)
        await asyncio.sleep(0.2)
        
        # Execute trade
        execution_event = Event(
            type="execution_signal",
            data={
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'quantity': 0.1,
                'order_type': 'MARKET'
            },
            priority=EventPriority.HIGH
        )
        
        await self.framework.trading_engine.event_bus.emit(execution_event)
        await asyncio.sleep(0.3)
        
        execution_time = time.time() - start_time
        self.assertLess(execution_time, 2.0, "Trading cycle took too long")
        
        self.framework.logger.info(f"Trading cycle completed in {execution_time:.3f}s")
    
    async def test_system_performance_under_load(self):
        """Test system performance under load."""
        self.framework.logger.info("Starting performance test")
        
        start_time = time.time()
        event_count = 0
        
        # Generate high-frequency events
        for i in range(100):
            market_event = Event(
                type="market_data_update",
                data={
                    'symbol': 'BTCUSDT',
                    'price': 45000.0 + np.random.uniform(-100, 100),
                    'volume': 1000000,
                    'timestamp': datetime.now().isoformat()
                },
                priority=EventPriority.HIGH
            )
            
            await self.framework.trading_engine.event_bus.emit(market_event)
            event_count += 1
            
            if i % 10 == 0:
                signal_event = Event(
                    type="execution_signal",
                    data={
                        'symbol': 'BTCUSDT',
                        'side': 'BUY' if i % 20 == 0 else 'SELL',
                        'quantity': 0.01,
                        'order_type': 'MARKET'
                    },
                    priority=EventPriority.HIGH
                )
                
                await self.framework.trading_engine.event_bus.emit(signal_event)
                event_count += 1
            
            await asyncio.sleep(0.01)
        
        await asyncio.sleep(2.0)
        
        total_time = time.time() - start_time
        events_per_second = event_count / total_time
        
        self.assertGreater(events_per_second, 50, "Performance below threshold")
        
        self.framework.logger.info(f"Performance: {events_per_second:.1f} events/second")
    
    async def test_error_handling(self):
        """Test error handling and recovery."""
        self.framework.logger.info("Starting error handling test")
        
        # Send malformed event
        malformed_event = Event(
            type="invalid_event",
            data={'invalid': 'data'},
            priority=EventPriority.NORMAL
        )
        
        await self.framework.trading_engine.event_bus.emit(malformed_event)
        await asyncio.sleep(0.1)
        
        # Verify system still operational
        test_event = Event(
            type="market_data_update",
            data={
                'symbol': 'BTCUSDT',
                'price': 45000.0,
                'volume': 1000000,
                'timestamp': datetime.now().isoformat()
            },
            priority=EventPriority.HIGH
        )
        
        await self.framework.trading_engine.event_bus.emit(test_event)
        await asyncio.sleep(0.1)
        
        self.assertTrue(self.framework.trading_engine.is_running())
        
        self.framework.logger.info("Error handling test completed")

class PerformanceBenchmarkTests(unittest.IsolatedAsyncioTestCase):
    """Performance benchmark tests."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        self.framework = IntegrationTestFramework()
        self.assertTrue(await self.framework.setup_test_environment())
        
    async def asyncTearDown(self):
        """Clean up after tests."""
        await self.framework.teardown_test_environment()
    
    async def test_event_throughput(self):
        """Benchmark event processing throughput."""
        self.framework.logger.info("Starting throughput benchmark")
        
        event_count = 1000
        start_time = time.time()
        
        for i in range(event_count):
            event = Event(
                type="benchmark_event",
                data={'sequence': i},
                priority=EventPriority.NORMAL
            )
            
            await self.framework.trading_engine.event_bus.emit(event)
        
        await asyncio.sleep(1.0)
        
        total_time = time.time() - start_time
        throughput = event_count / total_time
        
        self.assertGreater(throughput, 500, "Throughput below minimum")
        
        self.framework.logger.info(f"Throughput: {throughput:.1f} events/second")
    
    async def test_latency_benchmark(self):
        """Benchmark system latency."""
        self.framework.logger.info("Starting latency benchmark")
        
        latencies = []
        
        for i in range(100):
            start_time = time.time()
            
            event = Event(
                type="latency_test",
                data={'timestamp': start_time},
                priority=EventPriority.HIGH
            )
            
            await self.framework.trading_engine.event_bus.emit(event)
            await asyncio.sleep(0.001)
            
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
        
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        
        self.assertLess(avg_latency, 10.0, "Average latency too high")
        self.assertLess(p95_latency, 50.0, "P95 latency too high")
        
        self.framework.logger.info(f"Avg latency: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")

def run_integration_tests():
    """Run all integration tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TradingScenarioTests))
    suite.addTest(unittest.makeSuite(PerformanceBenchmarkTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1) 