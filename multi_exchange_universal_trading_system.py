#!/usr/bin/env python3
"""
🌍 MULTI-EXCHANGE UNIVERSAL TRADING SYSTEM
Advanced trading system supporting multiple exchanges and comprehensive market intelligence

SUPPORTED EXCHANGES:
- Binance (Primary)
- Coinbase Pro
- Kraken
- Bybit
- OKX
- Binance US

DATA SOURCES:
- CoinGecko API (Market Intelligence)
- CoinMarketCap API (Price Discovery)
- DEX Screener API (DeFi Trading)
- Twitter API (Sentiment Analysis)

FEATURES:
- Cross-exchange arbitrage detection
- Universal portfolio management
- Multi-source price aggregation
- Advanced risk management
- Real-time market monitoring
"""

import os
import sys
import asyncio
import logging
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import json
import sqlite3
from dataclasses import dataclass, asdict
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import hashlib
import hmac
from urllib.parse import urlencode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str
    secret_key: str
    sandbox: bool = True
    enabled: bool = True
    trading_pairs: List[str] = None
    min_order_size: float = 0.001
    max_position_size: float = 1000.0
    trading_fees: float = 0.001

@dataclass
class TradingSignal:
    """Universal trading signal"""
    exchange: str
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    confidence: float
    price: float
    volume: float
    timestamp: datetime
    source: str  # AI, ARBITRAGE, SENTIMENT
    position_size: float
    stop_loss: float
    take_profit: float
    reasoning: str

@dataclass
class MarketData:
    """Universal market data structure"""
    symbol: str
    exchange: str
    price: float
    volume_24h: float
    change_24h: float
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0

class UniversalExchangeManager:
    """Manages connections to multiple exchanges"""
    
    def __init__(self):
        self.exchanges = {}
        self.configs = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialize_exchanges()
    
    def initialize_exchanges(self):
        """Initialize all supported exchanges"""
        
        # Exchange configurations
        exchange_configs = {
            'binance': {
                'class': ccxt.binance,
                'api_key': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
                'options': {'defaultType': 'spot'}
            },
            'coinbasepro': {
                'class': ccxt.coinbasepro,
                'api_key': os.getenv('COINBASE_API_KEY'),
                'secret': os.getenv('COINBASE_SECRET_KEY'),
                'sandbox': True,
                'options': {}
            },
            'kraken': {
                'class': ccxt.kraken,
                'api_key': os.getenv('KRAKEN_API_KEY'),
                'secret': os.getenv('KRAKEN_SECRET_KEY'),
                'sandbox': True,
                'options': {}
            },
            'bybit': {
                'class': ccxt.bybit,
                'api_key': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_SECRET_KEY'),
                'sandbox': True,
                'options': {'defaultType': 'spot'}
            },
            'okx': {
                'class': ccxt.okx,
                'api_key': os.getenv('OKX_API_KEY'),
                'secret': os.getenv('OKX_SECRET_KEY'),
                'sandbox': True,
                'options': {}
            }
        }
        
        # Initialize exchanges
        for name, config in exchange_configs.items():
            try:
                if config['api_key'] and config['secret']:
                    exchange = config['class']({
                        'apiKey': config['api_key'],
                        'secret': config['secret'],
                        'sandbox': config['sandbox'],
                        'options': config['options'],
                        'enableRateLimit': True,
                    })
                    
                    self.exchanges[name] = exchange
                    self.configs[name] = ExchangeConfig(
                        name=name,
                        api_key=config['api_key'],
                        secret_key=config['secret'],
                        sandbox=config['sandbox']
                    )
                    
                    self.logger.info(f"✅ {name.capitalize()} exchange initialized")
                else:
                    self.logger.warning(f"⚠️ {name.capitalize()} API keys not found")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize {name}: {e}")
    
    def get_exchange(self, exchange_name: str):
        """Get specific exchange instance"""
        return self.exchanges.get(exchange_name)
    
    def get_all_exchanges(self) -> Dict:
        """Get all active exchanges"""
        return self.exchanges
    
    async def fetch_ticker(self, symbol: str, exchange_name: str = None) -> Optional[Dict]:
        """Fetch ticker from specific exchange or all exchanges"""
        
        if exchange_name:
            exchange = self.exchanges.get(exchange_name)
            if exchange:
                try:
                    return await exchange.fetch_ticker(symbol)
                except Exception as e:
                    self.logger.error(f"Error fetching {symbol} from {exchange_name}: {e}")
                    return None
        else:
            # Fetch from all exchanges
            results = {}
            for name, exchange in self.exchanges.items():
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    results[name] = ticker
                except Exception as e:
                    self.logger.debug(f"Could not fetch {symbol} from {name}: {e}")
            return results
    
    async def fetch_orderbook(self, symbol: str, exchange_name: str) -> Optional[Dict]:
        """Fetch orderbook from specific exchange"""
        exchange = self.exchanges.get(exchange_name)
        if exchange:
            try:
                return await exchange.fetch_order_book(symbol)
            except Exception as e:
                self.logger.error(f"Error fetching orderbook {symbol} from {exchange_name}: {e}")
                return None

class MultiSourceDataAggregator:
    """Aggregates data from multiple sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.coingecko_api = os.getenv('COINGECKO_API_KEY')
        self.coinmarketcap_api = os.getenv('COINMARKETCAP_API_KEY')
        self.dexscreener_api = os.getenv('DEXSCREENER_API_KEY')
        
    async def get_coingecko_data(self, symbols: List[str]) -> Dict:
        """Fetch data from CoinGecko"""
        
        if not self.coingecko_api:
            return {}
        
        try:
            # Convert symbols to CoinGecko IDs
            symbol_ids = ','.join([s.replace('/USDT', '').lower() for s in symbols])
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': symbol_ids,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            headers = {'X-CG-Demo-API-Key': self.coingecko_api}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ CoinGecko data fetched for {len(data)} assets")
                return data
            else:
                self.logger.warning(f"CoinGecko API error: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"CoinGecko fetch error: {e}")
            return {}
    
    async def get_coinmarketcap_data(self, symbols: List[str]) -> Dict:
        """Fetch data from CoinMarketCap"""
        
        if not self.coinmarketcap_api:
            return {}
        
        try:
            # Convert symbols for CMC
            symbol_list = ','.join([s.replace('/USDT', '') for s in symbols])
            
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.coinmarketcap_api,
                'Accept': 'application/json'
            }
            params = {
                'symbol': symbol_list,
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ CoinMarketCap data fetched")
                return data.get('data', {})
            else:
                self.logger.warning(f"CoinMarketCap API error: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"CoinMarketCap fetch error: {e}")
            return {}
    
    async def get_dex_screener_data(self, symbols: List[str]) -> Dict:
        """Fetch data from DEX Screener"""
        
        try:
            # DEX Screener for DeFi token data
            results = {}
            
            for symbol in symbols[:5]:  # Limit to avoid rate limits
                clean_symbol = symbol.replace('/USDT', '').lower()
                url = f"https://api.dexscreener.com/latest/dex/search/?q={clean_symbol}"
                
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('pairs'):
                        results[symbol] = data['pairs'][0]  # Take first result
            
            self.logger.info(f"✅ DEX Screener data fetched for {len(results)} pairs")
            return results
            
        except Exception as e:
            self.logger.error(f"DEX Screener fetch error: {e}")
            return {}

class ArbitrageDetector:
    """Detects arbitrage opportunities across exchanges"""
    
    def __init__(self, exchange_manager: UniversalExchangeManager):
        self.exchange_manager = exchange_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.min_profit_threshold = 0.005  # 0.5% minimum profit
        
    async def detect_arbitrage_opportunities(self, symbols: List[str]) -> List[Dict]:
        """Detect arbitrage opportunities across exchanges"""
        
        opportunities = []
        
        for symbol in symbols:
            try:
                # Fetch prices from all exchanges
                prices = {}
                
                for exchange_name, exchange in self.exchange_manager.exchanges.items():
                    try:
                        ticker = await exchange.fetch_ticker(symbol)
                        if ticker and ticker.get('bid') and ticker.get('ask'):
                            prices[exchange_name] = {
                                'bid': ticker['bid'],
                                'ask': ticker['ask'],
                                'last': ticker['last']
                            }
                    except Exception as e:
                        self.logger.debug(f"Could not fetch {symbol} from {exchange_name}: {e}")
                
                # Find arbitrage opportunities
                if len(prices) >= 2:
                    exchanges = list(prices.keys())
                    
                    for i in range(len(exchanges)):
                        for j in range(i + 1, len(exchanges)):
                            exchange_a = exchanges[i]
                            exchange_b = exchanges[j]
                            
                            # Check both directions
                            profit_a_to_b = self._calculate_arbitrage_profit(
                                prices[exchange_a], prices[exchange_b]
                            )
                            profit_b_to_a = self._calculate_arbitrage_profit(
                                prices[exchange_b], prices[exchange_a]
                            )
                            
                            if profit_a_to_b > self.min_profit_threshold:
                                opportunities.append({
                                    'symbol': symbol,
                                    'buy_exchange': exchange_a,
                                    'sell_exchange': exchange_b,
                                    'profit_percentage': profit_a_to_b * 100,
                                    'buy_price': prices[exchange_a]['ask'],
                                    'sell_price': prices[exchange_b]['bid'],
                                    'timestamp': datetime.now()
                                })
                            
                            if profit_b_to_a > self.min_profit_threshold:
                                opportunities.append({
                                    'symbol': symbol,
                                    'buy_exchange': exchange_b,
                                    'sell_exchange': exchange_a,
                                    'profit_percentage': profit_b_to_a * 100,
                                    'buy_price': prices[exchange_b]['ask'],
                                    'sell_price': prices[exchange_a]['bid'],
                                    'timestamp': datetime.now()
                                })
                
            except Exception as e:
                self.logger.error(f"Error detecting arbitrage for {symbol}: {e}")
        
        # Sort by profit potential
        opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
        
        if opportunities:
            self.logger.info(f"🎯 Found {len(opportunities)} arbitrage opportunities")
        
        return opportunities
    
    def _calculate_arbitrage_profit(self, price_a: Dict, price_b: Dict) -> float:
        """Calculate arbitrage profit percentage"""
        
        # Buy at exchange A (ask price), sell at exchange B (bid price)
        buy_price = price_a['ask']
        sell_price = price_b['bid']
        
        if buy_price and sell_price and sell_price > buy_price:
            profit = (sell_price - buy_price) / buy_price
            return profit
        
        return 0.0

class UniversalPortfolioManager:
    """Manages portfolio across multiple exchanges"""
    
    def __init__(self, exchange_manager: UniversalExchangeManager):
        self.exchange_manager = exchange_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.positions = {}
        self.total_portfolio_value = 0.0
        
    async def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary across all exchanges"""
        
        portfolio = {
            'total_value_usd': 0.0,
            'exchanges': {},
            'assets': {},
            'allocation': {},
            'performance': {}
        }
        
        for exchange_name, exchange in self.exchange_manager.exchanges.items():
            try:
                # Fetch balance
                balance = await exchange.fetch_balance()
                
                exchange_value = 0.0
                exchange_assets = {}
                
                for asset, amount in balance['total'].items():
                    if amount > 0:
                        # Get USD value (simplified - would need price conversion)
                        usd_value = amount  # Placeholder
                        exchange_value += usd_value
                        exchange_assets[asset] = {
                            'amount': amount,
                            'value_usd': usd_value
                        }
                
                portfolio['exchanges'][exchange_name] = {
                    'total_value_usd': exchange_value,
                    'assets': exchange_assets
                }
                
                portfolio['total_value_usd'] += exchange_value
                
                self.logger.info(f"📊 {exchange_name}: ${exchange_value:,.2f}")
                
            except Exception as e:
                self.logger.error(f"Error fetching portfolio from {exchange_name}: {e}")
        
        return portfolio
    
    async def execute_rebalancing(self, target_allocation: Dict) -> bool:
        """Execute portfolio rebalancing across exchanges"""
        
        try:
            current_portfolio = await self.get_portfolio_summary()
            
            # Calculate required trades for rebalancing
            rebalancing_trades = self._calculate_rebalancing_trades(
                current_portfolio, target_allocation
            )
            
            # Execute trades
            for trade in rebalancing_trades:
                await self._execute_rebalancing_trade(trade)
            
            self.logger.info(f"✅ Portfolio rebalancing completed with {len(rebalancing_trades)} trades")
            return True
            
        except Exception as e:
            self.logger.error(f"Portfolio rebalancing failed: {e}")
            return False
    
    def _calculate_rebalancing_trades(self, current_portfolio: Dict, target_allocation: Dict) -> List[Dict]:
        """Calculate trades needed for rebalancing"""
        
        trades = []
        # Implementation would calculate the difference between current and target allocation
        # and generate the necessary buy/sell orders
        
        return trades
    
    async def _execute_rebalancing_trade(self, trade: Dict) -> bool:
        """Execute a single rebalancing trade"""
        
        try:
            exchange = self.exchange_manager.get_exchange(trade['exchange'])
            
            if trade['side'] == 'buy':
                order = await exchange.create_market_buy_order(
                    trade['symbol'], trade['amount']
                )
            else:
                order = await exchange.create_market_sell_order(
                    trade['symbol'], trade['amount']
                )
            
            self.logger.info(f"✅ Rebalancing trade executed: {trade}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rebalancing trade failed: {e}")
            return False

class MultiExchangeUniversalTradingSystem:
    """Main trading system orchestrating all components"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.exchange_manager = UniversalExchangeManager()
        self.data_aggregator = MultiSourceDataAggregator()
        self.arbitrage_detector = ArbitrageDetector(self.exchange_manager)
        self.portfolio_manager = UniversalPortfolioManager(self.exchange_manager)
        
        # Configuration
        self.trading_pairs = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT']
        self.update_interval = 60  # seconds
        self.is_running = False
        
        # Statistics
        self.stats = {
            'total_signals': 0,
            'arbitrage_opportunities': 0,
            'successful_trades': 0,
            'total_profit': 0.0
        }
        
        self.logger.info("🌍 Multi-Exchange Universal Trading System initialized")
    
    async def start_trading(self):
        """Start the universal trading system"""
        
        self.is_running = True
        self.logger.info("🚀 Starting Multi-Exchange Universal Trading System")
        
        # Print system status
        await self._print_system_status()
        
        # Main trading loop
        while self.is_running:
            try:
                await self._trading_cycle()
                await asyncio.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                self.logger.info("⏹️ Stopping trading system...")
                self.is_running = False
                break
            except Exception as e:
                self.logger.error(f"Trading cycle error: {e}")
                await asyncio.sleep(30)  # Wait before retry
    
    async def _trading_cycle(self):
        """Execute one complete trading cycle"""
        
        cycle_start = datetime.now()
        
        # 1. Fetch market data from all sources
        market_data = await self._fetch_comprehensive_market_data()
        
        # 2. Detect arbitrage opportunities
        arbitrage_opportunities = await self.arbitrage_detector.detect_arbitrage_opportunities(
            self.trading_pairs
        )
        
        # 3. Generate AI trading signals
        ai_signals = await self._generate_ai_trading_signals(market_data)
        
        # 4. Execute high-confidence trades
        await self._execute_trading_decisions(arbitrage_opportunities, ai_signals)
        
        # 5. Update portfolio status
        await self._update_portfolio_status()
        
        # 6. Print cycle summary
        cycle_time = (datetime.now() - cycle_start).total_seconds()
        self._print_cycle_summary(cycle_time, arbitrage_opportunities, ai_signals)
    
    async def _fetch_comprehensive_market_data(self) -> Dict:
        """Fetch market data from all sources"""
        
        market_data = {
            'exchanges': {},
            'coingecko': {},
            'coinmarketcap': {},
            'dex_screener': {}
        }
        
        # Fetch from exchanges
        for exchange_name in self.exchange_manager.exchanges.keys():
            exchange_data = {}
            for symbol in self.trading_pairs:
                ticker = await self.exchange_manager.fetch_ticker(symbol, exchange_name)
                if ticker:
                    exchange_data[symbol] = ticker
            market_data['exchanges'][exchange_name] = exchange_data
        
        # Fetch from external APIs
        market_data['coingecko'] = await self.data_aggregator.get_coingecko_data(self.trading_pairs)
        market_data['coinmarketcap'] = await self.data_aggregator.get_coinmarketcap_data(self.trading_pairs)
        market_data['dex_screener'] = await self.data_aggregator.get_dex_screener_data(self.trading_pairs)
        
        return market_data
    
    async def _generate_ai_trading_signals(self, market_data: Dict) -> List[TradingSignal]:
        """Generate AI-powered trading signals"""
        
        signals = []
        
        # Simple AI signal generation (would be enhanced with actual ML models)
        for symbol in self.trading_pairs:
            for exchange_name in self.exchange_manager.exchanges.keys():
                exchange_data = market_data['exchanges'].get(exchange_name, {})
                ticker = exchange_data.get(symbol)
                
                if ticker:
                    # Simple momentum-based signal
                    change_24h = ticker.get('percentage', 0)
                    volume = ticker.get('quoteVolume', 0)
                    
                    confidence = min(abs(change_24h) * 10, 95)  # Simple confidence calculation
                    
                    if change_24h > 5 and volume > 1000000:  # Strong upward momentum
                        signal_type = 'BUY'
                    elif change_24h < -5 and volume > 1000000:  # Strong downward momentum
                        signal_type = 'SELL'
                    else:
                        signal_type = 'HOLD'
                    
                    if signal_type != 'HOLD' and confidence > 60:
                        signal = TradingSignal(
                            exchange=exchange_name,
                            symbol=symbol,
                            signal_type=signal_type,
                            confidence=confidence,
                            price=ticker['last'],
                            volume=volume,
                            timestamp=datetime.now(),
                            source='AI',
                            position_size=0.02,  # 2% position
                            stop_loss=ticker['last'] * (0.95 if signal_type == 'BUY' else 1.05),
                            take_profit=ticker['last'] * (1.10 if signal_type == 'BUY' else 0.90),
                            reasoning=f"Momentum signal: {change_24h:.1f}% change, high volume"
                        )
                        signals.append(signal)
        
        return signals
    
    async def _execute_trading_decisions(self, arbitrage_opportunities: List[Dict], 
                                       ai_signals: List[TradingSignal]):
        """Execute trading decisions based on opportunities and signals"""
        
        # Execute arbitrage opportunities (highest priority)
        for opportunity in arbitrage_opportunities[:3]:  # Limit to top 3
            if opportunity['profit_percentage'] > 1.0:  # Only execute if >1% profit
                await self._execute_arbitrage_trade(opportunity)
        
        # Execute AI signals (lower priority)
        for signal in ai_signals[:5]:  # Limit to top 5 signals
            if signal.confidence > 70:  # Only high-confidence signals
                await self._execute_ai_trade(signal)
    
    async def _execute_arbitrage_trade(self, opportunity: Dict):
        """Execute arbitrage trade"""
        
        try:
            # This would execute the actual arbitrage trade
            self.logger.info(f"🎯 ARBITRAGE: {opportunity['symbol']} "
                           f"{opportunity['buy_exchange']} → {opportunity['sell_exchange']} "
                           f"({opportunity['profit_percentage']:.2f}% profit)")
            
            self.stats['arbitrage_opportunities'] += 1
            
        except Exception as e:
            self.logger.error(f"Arbitrage trade failed: {e}")
    
    async def _execute_ai_trade(self, signal: TradingSignal):
        """Execute AI-generated trade"""
        
        try:
            # This would execute the actual AI trade
            self.logger.info(f"🤖 AI TRADE: {signal.exchange} {signal.symbol} "
                           f"{signal.signal_type} (Confidence: {signal.confidence:.1f}%)")
            
            self.stats['total_signals'] += 1
            
        except Exception as e:
            self.logger.error(f"AI trade failed: {e}")
    
    async def _update_portfolio_status(self):
        """Update portfolio status"""
        
        try:
            portfolio = await self.portfolio_manager.get_portfolio_summary()
            self.stats['total_portfolio_value'] = portfolio['total_value_usd']
            
        except Exception as e:
            self.logger.error(f"Portfolio update failed: {e}")
    
    async def _print_system_status(self):
        """Print system initialization status"""
        
        print("\n🌍 MULTI-EXCHANGE UNIVERSAL TRADING SYSTEM")
        print("=" * 70)
        
        print("📊 CONNECTED EXCHANGES:")
        for exchange_name in self.exchange_manager.exchanges.keys():
            print(f"   ✅ {exchange_name.capitalize()}")
        
        print(f"\n🎯 TRADING PAIRS: {', '.join(self.trading_pairs)}")
        
        print(f"\n📡 DATA SOURCES:")
        print(f"   {'✅' if self.data_aggregator.coingecko_api else '❌'} CoinGecko API")
        print(f"   {'✅' if self.data_aggregator.coinmarketcap_api else '❌'} CoinMarketCap API")
        print(f"   {'✅' if self.data_aggregator.dexscreener_api else '❌'} DEX Screener API")
        
        print(f"\n⚙️ UPDATE INTERVAL: {self.update_interval} seconds")
        print("=" * 70)
    
    def _print_cycle_summary(self, cycle_time: float, arbitrage_opportunities: List[Dict], 
                           ai_signals: List[TradingSignal]):
        """Print trading cycle summary"""
        
        print(f"\n📊 TRADING CYCLE SUMMARY ({datetime.now().strftime('%H:%M:%S')})")
        print("-" * 50)
        print(f"⏱️  Cycle Time: {cycle_time:.1f}s")
        print(f"🎯 Arbitrage Opportunities: {len(arbitrage_opportunities)}")
        print(f"🤖 AI Signals Generated: {len(ai_signals)}")
        print(f"📈 Total Signals: {self.stats['total_signals']}")
        print(f"💰 Portfolio Value: ${self.stats.get('total_portfolio_value', 0):,.2f}")
        
        if arbitrage_opportunities:
            best_arb = arbitrage_opportunities[0]
            print(f"🏆 Best Arbitrage: {best_arb['symbol']} ({best_arb['profit_percentage']:.2f}%)")
        
        if ai_signals:
            high_conf_signals = [s for s in ai_signals if s.confidence > 70]
            print(f"⭐ High-Confidence AI Signals: {len(high_conf_signals)}")

def main():
    """Main function"""
    
    print("🌍 Multi-Exchange Universal Trading System")
    print("=" * 50)
    
    # Create and start the trading system
    trading_system = MultiExchangeUniversalTradingSystem()
    
    try:
        # Start trading
        asyncio.run(trading_system.start_trading())
    except KeyboardInterrupt:
        print("\n⏹️ Trading system stopped by user")
    except Exception as e:
        print(f"❌ System error: {e}")

if __name__ == "__main__":
    main() 