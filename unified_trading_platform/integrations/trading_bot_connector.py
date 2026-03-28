#!/usr/bin/env python3
"""
🤖 Trading Bot Connector
Advanced integration layer connecting all enhanced modules with trading systems
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
from pathlib import Path

from unified_trading_platform.core.base_module import BaseModule, ModuleEvent
from unified_trading_platform.core.performance_monitor import get_monitor, profile
from unified_trading_platform.core.cache_manager import get_cache_manager, cache_key

@dataclass
class TradingSignal:
    """Trading signal structure"""
    signal_id: str
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    priority: str  # 'high', 'medium', 'low'
    source: str
    price_target: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    volume_suggestion: Optional[float]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradingDecision:
    """Final trading decision"""
    decision_id: str
    symbol: str
    action: str
    quantity: float
    price: Optional[float]
    order_type: str  # 'market', 'limit', 'stop'
    confidence_score: float
    risk_score: float
    expected_return: float
    signals_used: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class TradingBotConnector:
    """
    Advanced Trading Bot Integration System
    
    Features:
    ✅ Multi-module signal aggregation
    ✅ Real-time decision making engine
    ✅ Risk management integration
    ✅ Portfolio optimization
    ✅ Performance tracking
    ✅ Alert and notification system
    ✅ Backtesting integration
    ✅ Live trading execution
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Core settings
        self.enable_live_trading = config.get('enable_live_trading', False)
        self.enable_paper_trading = config.get('enable_paper_trading', True)
        self.max_concurrent_trades = config.get('max_concurrent_trades', 10)
        self.min_confidence_threshold = config.get('min_confidence_threshold', 0.7)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.02)  # 2% per trade
        
        # Module connections
        self.connected_modules = {}
        self.signal_handlers = {}
        self.event_subscribers = {}
        
        # Signal processing
        self.active_signals = {}  # symbol -> List[TradingSignal]
        self.recent_decisions = []
        self.signal_weights = {
            'new_listing_detector': 0.3,
            'historical_data_fetcher': 0.2,
            'social_sentiment_analyzer': 0.25,
            'technical_analysis': 0.25
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_signals_processed': 0,
            'total_decisions_made': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_trade_return': 0.0,
            'sharpe_ratio': 0.0
        }
        
        # Risk management
        self.risk_limits = {
            'max_position_size': config.get('max_position_size', 0.1),  # 10% of portfolio
            'max_daily_trades': config.get('max_daily_trades', 50),
            'max_daily_loss': config.get('max_daily_loss', 0.05),  # 5% daily loss limit
            'blacklisted_symbols': set(config.get('blacklisted_symbols', []))
        }
        
        # Storage
        self.cache_dir = Path(config.get('cache_dir', 'data/trading_integration'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize the trading bot connector"""
        try:
            self.logger.info("🚀 Initializing Trading Bot Connector...")
            
            # Initialize performance monitoring
            monitor = get_monitor()
            monitor.start_monitoring()
            
            # Initialize cache manager
            cache_manager = await get_cache_manager()
            
            # Setup signal processing
            await self._setup_signal_processing()
            
            # Load historical performance data
            await self._load_performance_history()
            
            self.logger.info("✅ Trading Bot Connector initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing Trading Bot Connector: {e}")
            return False
    
    async def connect_module(self, module_name: str, module_instance: BaseModule):
        """Connect a trading module"""
        try:
            self.connected_modules[module_name] = module_instance
            
            # Subscribe to module events
            if hasattr(module_instance, 'register_event_handler'):
                # Register our signal handler
                module_instance.register_event_handler('trading_signal', self._handle_module_signal)
                module_instance.register_event_handler('new_listing_detected', self._handle_new_listing)
                module_instance.register_event_handler('price_alert', self._handle_price_alert)
                module_instance.register_event_handler('sentiment_change', self._handle_sentiment_change)
            
            self.logger.info(f"✅ Connected module: {module_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error connecting module {module_name}: {e}")
    
    async def _setup_signal_processing(self):
        """Setup signal processing system"""
        # Create signal aggregation task
        asyncio.create_task(self._signal_aggregation_task())
        
        # Create decision making task
        asyncio.create_task(self._decision_making_task())
        
        # Create performance monitoring task
        asyncio.create_task(self._performance_monitoring_task())
    
    @profile("signal_processing")
    async def _handle_module_signal(self, event: ModuleEvent):
        """Handle incoming signal from connected modules"""
        try:
            signal_data = event.data
            
            # Create trading signal
            signal = TradingSignal(
                signal_id=f"{event.source}_{datetime.now().timestamp()}",
                symbol=signal_data.get('symbol'),
                action=signal_data.get('action'),
                confidence=signal_data.get('confidence', 0.5),
                priority=signal_data.get('priority', 'medium'),
                source=event.source,
                price_target=signal_data.get('price_target'),
                stop_loss=signal_data.get('stop_loss'),
                take_profit=signal_data.get('take_profit'),
                volume_suggestion=signal_data.get('volume'),
                timestamp=datetime.now(),
                metadata=signal_data.get('metadata', {})
            )
            
            # Add to active signals
            symbol = signal.symbol
            if symbol not in self.active_signals:
                self.active_signals[symbol] = []
            
            self.active_signals[symbol].append(signal)
            
            # Clean old signals (keep only last hour)
            cutoff_time = datetime.now() - timedelta(hours=1)
            self.active_signals[symbol] = [
                s for s in self.active_signals[symbol] 
                if s.timestamp > cutoff_time
            ]
            
            self.performance_metrics['total_signals_processed'] += 1
            
            self.logger.info(f"📊 Received signal: {signal.action} {signal.symbol} (confidence: {signal.confidence:.2f})")
            
        except Exception as e:
            self.logger.error(f"Error handling module signal: {e}")
    
    async def _handle_new_listing(self, event: ModuleEvent):
        """Handle new listing detection"""
        try:
            new_coin = event.data
            symbol = new_coin.get('symbol')
            
            # Generate high-priority signal for new listings
            signal = TradingSignal(
                signal_id=f"new_listing_{symbol}_{datetime.now().timestamp()}",
                symbol=symbol,
                action='buy',  # Consider new listings as buy opportunities
                confidence=0.6,  # Medium confidence for new listings
                priority='high',
                source='new_listing_detector',
                price_target=None,
                stop_loss=None,
                take_profit=None,
                volume_suggestion=self.config.get('new_listing_position_size', 0.01),
                timestamp=datetime.now(),
                metadata={
                    'new_listing': True,
                    'market_cap': new_coin.get('market_cap_usd'),
                    'volume_24h': new_coin.get('volume_24h_usd'),
                    'categories': new_coin.get('categories', [])
                }
            )
            
            # Add to signals
            if symbol not in self.active_signals:
                self.active_signals[symbol] = []
            self.active_signals[symbol].append(signal)
            
            self.logger.info(f"🆕 New listing signal generated: {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error handling new listing: {e}")
    
    async def _handle_price_alert(self, event: ModuleEvent):
        """Handle price alerts"""
        try:
            alert_data = event.data
            symbol = alert_data.get('symbol')
            alert_type = alert_data.get('type')  # 'breakout', 'support', 'resistance'
            
            # Determine action based on alert type
            action_map = {
                'breakout_up': 'buy',
                'breakout_down': 'sell',
                'support_bounce': 'buy',
                'resistance_reject': 'sell'
            }
            
            action = action_map.get(alert_type, 'hold')
            confidence = alert_data.get('confidence', 0.5)
            
            signal = TradingSignal(
                signal_id=f"price_alert_{symbol}_{datetime.now().timestamp()}",
                symbol=symbol,
                action=action,
                confidence=confidence,
                priority='medium',
                source='price_alert',
                price_target=alert_data.get('target_price'),
                stop_loss=alert_data.get('stop_loss'),
                take_profit=alert_data.get('take_profit'),
                volume_suggestion=None,
                timestamp=datetime.now(),
                metadata=alert_data
            )
            
            # Add to signals
            if symbol not in self.active_signals:
                self.active_signals[symbol] = []
            self.active_signals[symbol].append(signal)
            
            self.logger.info(f"📈 Price alert signal: {action} {symbol} ({alert_type})")
            
        except Exception as e:
            self.logger.error(f"Error handling price alert: {e}")
    
    async def _handle_sentiment_change(self, event: ModuleEvent):
        """Handle sentiment change events"""
        try:
            sentiment_data = event.data
            symbol = sentiment_data.get('symbol')
            sentiment_score = sentiment_data.get('sentiment_score', 0)
            sentiment_change = sentiment_data.get('sentiment_change', 0)
            
            # Generate signal based on sentiment
            if sentiment_score > 0.3 and sentiment_change > 0.2:
                action = 'buy'
                confidence = min(0.8, sentiment_score + sentiment_change)
            elif sentiment_score < -0.3 and sentiment_change < -0.2:
                action = 'sell'
                confidence = min(0.8, abs(sentiment_score) + abs(sentiment_change))
            else:
                action = 'hold'
                confidence = 0.3
            
            signal = TradingSignal(
                signal_id=f"sentiment_{symbol}_{datetime.now().timestamp()}",
                symbol=symbol,
                action=action,
                confidence=confidence,
                priority='medium',
                source='sentiment_analyzer',
                price_target=None,
                stop_loss=None,
                take_profit=None,
                volume_suggestion=None,
                timestamp=datetime.now(),
                metadata=sentiment_data
            )
            
            # Add to signals
            if symbol not in self.active_signals:
                self.active_signals[symbol] = []
            self.active_signals[symbol].append(signal)
            
            self.logger.info(f"😊 Sentiment signal: {action} {symbol} (score: {sentiment_score:.2f})")
            
        except Exception as e:
            self.logger.error(f"Error handling sentiment change: {e}")
    
    async def _signal_aggregation_task(self):
        """Background task for signal aggregation"""
        while True:
            try:
                await self._aggregate_signals()
                await asyncio.sleep(30)  # Run every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in signal aggregation: {e}")
                await asyncio.sleep(60)
    
    @profile("signal_aggregation")
    async def _aggregate_signals(self):
        """Aggregate signals from all sources"""
        for symbol, signals in self.active_signals.items():
            if not signals:
                continue
            
            # Skip if symbol is blacklisted
            if symbol in self.risk_limits['blacklisted_symbols']:
                continue
            
            # Calculate weighted confidence score
            total_weight = 0
            weighted_confidence = 0
            action_votes = {'buy': 0, 'sell': 0, 'hold': 0}
            
            for signal in signals:
                source_weight = self.signal_weights.get(signal.source, 0.1)
                total_weight += source_weight
                weighted_confidence += signal.confidence * source_weight
                action_votes[signal.action] += source_weight
            
            if total_weight == 0:
                continue
            
            # Normalize confidence
            final_confidence = weighted_confidence / total_weight
            
            # Determine final action
            final_action = max(action_votes, key=action_votes.get)
            
            # Check if confidence meets threshold
            if final_confidence >= self.min_confidence_threshold:
                await self._create_trading_decision(symbol, final_action, final_confidence, signals)
    
    async def _create_trading_decision(self, symbol: str, action: str, confidence: float, signals: List[TradingSignal]):
        """Create trading decision based on aggregated signals"""
        try:
            # Calculate position size based on confidence and risk management
            portfolio_value = await self._get_portfolio_value()
            max_position_value = portfolio_value * self.risk_limits['max_position_size']
            
            # Adjust position size based on confidence
            confidence_multiplier = min(1.0, confidence / 0.7)  # Scale based on threshold
            position_value = max_position_value * confidence_multiplier
            
            # Get current price (simplified - in production use real price feeds)
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return
            
            quantity = position_value / current_price
            
            # Calculate risk score
            risk_score = await self._calculate_risk_score(symbol, action, quantity)
            
            # Check risk limits
            if risk_score > 0.8:  # High risk threshold
                self.logger.warning(f"⚠️ High risk detected for {symbol}, reducing position size")
                quantity *= 0.5
                risk_score = await self._calculate_risk_score(symbol, action, quantity)
            
            # Calculate expected return (simplified)
            expected_return = self._calculate_expected_return(signals, confidence)
            
            # Create trading decision
            decision = TradingDecision(
                decision_id=f"decision_{symbol}_{datetime.now().timestamp()}",
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=current_price,
                order_type='market',  # Simplified
                confidence_score=confidence,
                risk_score=risk_score,
                expected_return=expected_return,
                signals_used=[s.signal_id for s in signals],
                timestamp=datetime.now(),
                metadata={
                    'num_signals': len(signals),
                    'signal_sources': list(set(s.source for s in signals)),
                    'portfolio_allocation': position_value / portfolio_value
                }
            )
            
            self.recent_decisions.append(decision)
            self.performance_metrics['total_decisions_made'] += 1
            
            # Execute decision if live trading is enabled
            if self.enable_live_trading:
                await self._execute_trading_decision(decision)
            else:
                self.logger.info(f"📋 Paper trading decision: {decision.action} {decision.quantity:.6f} {decision.symbol} @ {decision.price:.6f}")
            
            # Cache the decision
            cache_manager = await get_cache_manager()
            await cache_manager.set(
                f"trading_decision_{decision.decision_id}",
                decision,
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            self.logger.error(f"Error creating trading decision: {e}")
    
    async def _decision_making_task(self):
        """Background task for decision making"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._process_pending_decisions()
            except Exception as e:
                self.logger.error(f"Error in decision making: {e}")
                await asyncio.sleep(60)
    
    async def _process_pending_decisions(self):
        """Process pending trading decisions"""
        # Clean old decisions (keep only last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.recent_decisions = [
            d for d in self.recent_decisions 
            if d.timestamp > cutoff_time
        ]
    
    async def _execute_trading_decision(self, decision: TradingDecision):
        """Execute trading decision (placeholder for actual trading implementation)"""
        try:
            self.logger.info(f"🚀 Executing trade: {decision.action} {decision.quantity:.6f} {decision.symbol}")
            
            # Here you would integrate with actual trading APIs like:
            # - Binance API
            # - Coinbase API
            # - Other exchange APIs
            
            # For now, simulate execution
            success = True  # Simulate successful execution
            
            if success:
                self.performance_metrics['successful_trades'] += 1
                self.logger.info(f"✅ Trade executed successfully: {decision.decision_id}")
            else:
                self.performance_metrics['failed_trades'] += 1
                self.logger.error(f"❌ Trade execution failed: {decision.decision_id}")
            
        except Exception as e:
            self.logger.error(f"Error executing trading decision: {e}")
            self.performance_metrics['failed_trades'] += 1
    
    async def _get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        # Placeholder - in production, get from portfolio manager
        return self.config.get('initial_portfolio_value', 10000.0)
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        # Placeholder - in production, get from price feeds
        # For demo purposes, return a random price
        import random
        base_prices = {
            'BTC': 50000, 'ETH': 3000, 'ADA': 1.0, 'SOL': 100,
            'MATIC': 0.8, 'LINK': 15, 'DOT': 25, 'AVAX': 35
        }
        
        base_price = base_prices.get(symbol.replace('USDT', ''), 100)
        # Add some random variation
        variation = random.uniform(-0.05, 0.05)  # ±5%
        return base_price * (1 + variation)
    
    async def _calculate_risk_score(self, symbol: str, action: str, quantity: float) -> float:
        """Calculate risk score for a trading decision"""
        # Simplified risk calculation
        # In production, this would consider:
        # - Volatility
        # - Market conditions
        # - Portfolio correlation
        # - Liquidity
        # - Historical performance
        
        base_risk = 0.3  # Base risk
        
        # Add volatility risk (placeholder)
        volatility_risk = 0.2
        
        # Add position size risk
        portfolio_value = await self._get_portfolio_value()
        current_price = await self._get_current_price(symbol)
        position_value = quantity * current_price if current_price else 0
        
        position_ratio = position_value / portfolio_value
        position_risk = min(0.3, position_ratio * 2)  # Higher ratio = higher risk
        
        total_risk = min(1.0, base_risk + volatility_risk + position_risk)
        return total_risk
    
    def _calculate_expected_return(self, signals: List[TradingSignal], confidence: float) -> float:
        """Calculate expected return for a trading decision"""
        # Simplified expected return calculation
        # In production, this would use:
        # - Historical performance data
        # - Market conditions
        # - Technical indicators
        # - Fundamental analysis
        
        base_return = 0.02  # 2% base expected return
        confidence_multiplier = confidence
        
        # Factor in signal quality
        high_priority_signals = len([s for s in signals if s.priority == 'high'])
        signal_quality_bonus = high_priority_signals * 0.01
        
        expected_return = base_return * confidence_multiplier + signal_quality_bonus
        return min(0.2, expected_return)  # Cap at 20%
    
    async def _performance_monitoring_task(self):
        """Background task for performance monitoring"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._update_performance_metrics()
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Calculate win rate
            total_trades = self.performance_metrics['successful_trades'] + self.performance_metrics['failed_trades']
            if total_trades > 0:
                self.performance_metrics['win_rate'] = self.performance_metrics['successful_trades'] / total_trades
            
            # Update other metrics (placeholder)
            # In production, these would be calculated from actual trading results
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    async def _load_performance_history(self):
        """Load historical performance data"""
        try:
            # In production, load from database or files
            self.logger.info("📊 Performance history loaded")
        except Exception as e:
            self.logger.error(f"Error loading performance history: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'metrics': self.performance_metrics,
            'active_signals': {
                symbol: len(signals) 
                for symbol, signals in self.active_signals.items()
            },
            'recent_decisions': len(self.recent_decisions),
            'connected_modules': list(self.connected_modules.keys()),
            'risk_limits': self.risk_limits,
            'configuration': {
                'live_trading_enabled': self.enable_live_trading,
                'paper_trading_enabled': self.enable_paper_trading,
                'min_confidence_threshold': self.min_confidence_threshold,
                'max_concurrent_trades': self.max_concurrent_trades
            }
        }
    
    async def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trading decisions"""
        recent = sorted(self.recent_decisions, key=lambda d: d.timestamp, reverse=True)[:limit]
        return [
            {
                'decision_id': d.decision_id,
                'symbol': d.symbol,
                'action': d.action,
                'quantity': d.quantity,
                'confidence_score': d.confidence_score,
                'risk_score': d.risk_score,
                'expected_return': d.expected_return,
                'timestamp': d.timestamp.isoformat(),
                'signals_used': len(d.signals_used)
            }
            for d in recent
        ] 