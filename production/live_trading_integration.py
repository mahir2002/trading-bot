#!/usr/bin/env python3
"""Live Trading Integration"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger('LiveTrading')

class LiveTradingIntegration:
    """Live trading with safety controls"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.live_mode = config.get('live_trading', False)
        
        if self.live_mode:
            logger.warning("🚨 LIVE TRADING ENABLED - REAL MONEY AT RISK!")
        else:
            logger.info("📝 Paper trading mode - Safe testing")
    
    async def execute_trade(self, symbol: str, signal: str, confidence: float):
        """Execute trade with safety checks"""
        try:
            # Safety checks
            if confidence < 0.7:
                logger.info(f"Skipping {symbol} - low confidence: {confidence}")
                return {'status': 'skipped', 'reason': 'low_confidence'}
            
            # Execute trade (simulation for now)
            trade_result = {
                'symbol': symbol,
                'signal': signal,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'status': 'executed' if self.live_mode else 'simulated'
            }
            
            logger.info(f"Trade: {signal} {symbol} (conf: {confidence:.3f})")
            return trade_result
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}

if __name__ == "__main__":
    # Demo
    config = {'live_trading': False}
    trader = LiveTradingIntegration(config)
    
    # Test trade
    import asyncio
    result = asyncio.run(trader.execute_trade('BTC/USDT', 'BUY', 0.85))
    print(f"Trade result: {result}")
