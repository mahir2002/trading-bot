#!/usr/bin/env python3
"""
🌐 Multi-Exchange Manager
Comprehensive support for major cryptocurrency exchanges
Addresses: "While it has a structure for multiple exchanges, it primarily focuses on Binance"
Solution: True multi-exchange support with unified interface
"""

import os
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
import json

class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    COINBASE_PRO = "coinbasepro"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    KUCOIN = "kucoin"
    HUOBI = "huobi"
    OKX = "okx"
    BITFINEX = "bitfinex"

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None
    sandbox: bool = True
    rate_limit: bool = True
    timeout: int = 30000
    custom_settings: Dict = None

@dataclass
class UnifiedTicker:
    """Unified ticker data across exchanges"""
    symbol: str
    exchange: str
    last_price: float
    bid: float
    ask: float
    high_24h: float
    low_24h: float
    volume_24h: float
    change_24h: float
    change_percent_24h: float
    timestamp: datetime

@dataclass
class UnifiedBalance:
    """Unified balance data across exchanges"""
    exchange: str
    currency: str
    free: float
    used: float
    total: float
    usd_value: Optional[float] = None

@dataclass
class UnifiedOrder:
    """Unified order data across exchanges"""
    id: str
    exchange: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    order_type: str  # 'market', 'limit', etc.
    status: str
    filled: float
    remaining: float
    timestamp: datetime
    fee: Optional[Dict] = None

class MultiExchangeManager:
    """
    Comprehensive multi-exchange manager with unified interface
    Supports: Binance, Coinbase Pro, Kraken, Bybit, KuCoin, Huobi, OKX, Bitfinex
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.exchange_configs: Dict[str, ExchangeConfig] = {}
        self.active_exchanges: List[str] = []
        self.primary_exchange: Optional[str] = None
        
        # Exchange-specific configurations
        self.exchange_settings = self._get_exchange_settings()
        
        # Initialize exchanges
        self._initialize_all_exchanges()
        
    def _get_exchange_settings(self) -> Dict[str, Dict]:
        """Get exchange-specific settings and configurations"""
        return {
            ExchangeType.BINANCE.value: {
                'class': ccxt.binance,
                'env_prefix': 'BINANCE',
                'supports_sandbox': True,
                'sandbox_urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                },
                'rate_limit': 1200,  # requests per minute
                'min_trade_amount': 0.001,
                'fee_structure': {'maker': 0.001, 'taker': 0.001},
                'supported_order_types': ['market', 'limit', 'stop_loss', 'take_profit'],
                'popular_pairs': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT']
            },
            ExchangeType.COINBASE_PRO.value: {
                'class': ccxt.coinbasepro,
                'env_prefix': 'COINBASE',
                'supports_sandbox': True,
                'sandbox_urls': {
                    'api': 'https://api-public.sandbox.pro.coinbase.com'
                },
                'rate_limit': 600,  # requests per minute
                'min_trade_amount': 0.001,
                'fee_structure': {'maker': 0.005, 'taker': 0.005},
                'supported_order_types': ['market', 'limit', 'stop'],
                'popular_pairs': ['BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD'],
                'requires_passphrase': True
            },
            ExchangeType.KRAKEN.value: {
                'class': ccxt.kraken,
                'env_prefix': 'KRAKEN',
                'supports_sandbox': False,
                'rate_limit': 60,  # requests per minute
                'min_trade_amount': 0.002,
                'fee_structure': {'maker': 0.0016, 'taker': 0.0026},
                'supported_order_types': ['market', 'limit', 'stop-loss', 'take-profit'],
                'popular_pairs': ['BTC/USD', 'ETH/USD', 'XRP/USD', 'ADA/USD']
            },
            ExchangeType.BYBIT.value: {
                'class': ccxt.bybit,
                'env_prefix': 'BYBIT',
                'supports_sandbox': True,
                'sandbox_urls': {
                    'api': {
                        'public': 'https://api-testnet.bybit.com',
                        'private': 'https://api-testnet.bybit.com',
                    }
                },
                'rate_limit': 600,  # requests per minute
                'min_trade_amount': 0.001,
                'fee_structure': {'maker': 0.001, 'taker': 0.001},
                'supported_order_types': ['market', 'limit', 'stop', 'take_profit'],
                'popular_pairs': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT']
            },
            ExchangeType.KUCOIN.value: {
                'class': ccxt.kucoin,
                'env_prefix': 'KUCOIN',
                'supports_sandbox': True,
                'sandbox_urls': {
                    'api': {
                        'public': 'https://openapi-sandbox.kucoin.com',
                        'private': 'https://openapi-sandbox.kucoin.com',
                    }
                },
                'rate_limit': 1800,  # requests per minute
                'min_trade_amount': 0.0001,
                'fee_structure': {'maker': 0.001, 'taker': 0.001},
                'supported_order_types': ['market', 'limit', 'stop'],
                'popular_pairs': ['BTC/USDT', 'ETH/USDT', 'KCS/USDT', 'USDC/USDT'],
                'requires_passphrase': True
            },
            ExchangeType.HUOBI.value: {
                'class': ccxt.huobi,
                'env_prefix': 'HUOBI',
                'supports_sandbox': False,
                'rate_limit': 600,  # requests per minute
                'min_trade_amount': 0.001,
                'fee_structure': {'maker': 0.002, 'taker': 0.002},
                'supported_order_types': ['market', 'limit', 'stop-limit'],
                'popular_pairs': ['BTC/USDT', 'ETH/USDT', 'HT/USDT', 'LTC/USDT']
            },
            ExchangeType.OKX.value: {
                'class': ccxt.okx,
                'env_prefix': 'OKX',
                'supports_sandbox': True,
                'sandbox_urls': {
                    'api': {
                        'public': 'https://www.okx.com',
                        'private': 'https://www.okx.com',
                    }
                },
                'rate_limit': 600,  # requests per minute
                'min_trade_amount': 0.001,
                'fee_structure': {'maker': 0.0008, 'taker': 0.001},
                'supported_order_types': ['market', 'limit', 'stop', 'post_only'],
                'popular_pairs': ['BTC/USDT', 'ETH/USDT', 'OKB/USDT', 'DOT/USDT']
            },
            ExchangeType.BITFINEX.value: {
                'class': ccxt.bitfinex,
                'env_prefix': 'BITFINEX',
                'supports_sandbox': False,
                'rate_limit': 90,  # requests per minute
                'min_trade_amount': 0.002,
                'fee_structure': {'maker': 0.001, 'taker': 0.002},
                'supported_order_types': ['market', 'limit', 'stop', 'trailing-stop'],
                'popular_pairs': ['BTC/USD', 'ETH/USD', 'LEO/USD', 'XRP/USD']
            }
        }
    
    def _initialize_all_exchanges(self):
        """Initialize all available exchanges based on environment variables"""
        
        self.logger.info("🌐 Initializing multi-exchange support...")
        
        for exchange_type, settings in self.exchange_settings.items():
            try:
                config = self._load_exchange_config(exchange_type, settings)
                if config:
                    exchange = self._create_exchange_instance(exchange_type, config, settings)
                    if exchange:
                        self.exchanges[exchange_type] = exchange
                        self.exchange_configs[exchange_type] = config
                        self.active_exchanges.append(exchange_type)
                        
                        # Set primary exchange (first successful one)
                        if not self.primary_exchange:
                            self.primary_exchange = exchange_type
                        
                        self.logger.info(f"✅ {exchange_type.upper()} initialized successfully")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize {exchange_type}: {e}")
        
        if self.active_exchanges:
            self.logger.info(f"🎉 Successfully initialized {len(self.active_exchanges)} exchanges: {', '.join(self.active_exchanges)}")
            self.logger.info(f"🎯 Primary exchange: {self.primary_exchange}")
        else:
            self.logger.error("❌ No exchanges initialized! Check your API credentials.")
    
    def _load_exchange_config(self, exchange_type: str, settings: Dict) -> Optional[ExchangeConfig]:
        """Load configuration for a specific exchange"""
        
        env_prefix = settings['env_prefix']
        
        # Check for required API credentials
        api_key = os.getenv(f'{env_prefix}_API_KEY')
        secret_key = os.getenv(f'{env_prefix}_SECRET_KEY')
        
        if not api_key or not secret_key:
            self.logger.debug(f"No API credentials found for {exchange_type}")
            return None
        
        # Optional passphrase for exchanges that require it
        passphrase = None
        if settings.get('requires_passphrase'):
            passphrase = os.getenv(f'{env_prefix}_PASSPHRASE')
            if not passphrase:
                self.logger.warning(f"{exchange_type} requires passphrase but none provided")
                return None
        
        # Sandbox mode
        sandbox = os.getenv(f'{env_prefix}_SANDBOX', 'true').lower() == 'true'
        
        return ExchangeConfig(
            name=exchange_type,
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase,
            sandbox=sandbox and settings.get('supports_sandbox', False),
            rate_limit=True,
            timeout=30000
        )
    
    def _create_exchange_instance(self, exchange_type: str, config: ExchangeConfig, settings: Dict) -> Optional[ccxt.Exchange]:
        """Create exchange instance with proper configuration"""
        
        try:
            exchange_class = settings['class']
            
            # Base configuration
            exchange_config = {
                'apiKey': config.api_key,
                'secret': config.secret_key,
                'enableRateLimit': config.rate_limit,
                'timeout': config.timeout,
            }
            
            # Add passphrase if required
            if config.passphrase:
                exchange_config['passphrase'] = config.passphrase
            
            # Configure sandbox/testnet
            if config.sandbox and settings.get('supports_sandbox'):
                exchange_config['sandbox'] = True
                if 'sandbox_urls' in settings:
                    exchange_config['urls'] = settings['sandbox_urls']
            
            # Create exchange instance
            exchange = exchange_class(exchange_config)
            
            # Test connection with a simple public API call
            exchange.fetch_ticker(settings['popular_pairs'][0])
            
            return exchange
            
        except Exception as e:
            self.logger.error(f"Failed to create {exchange_type} instance: {e}")
            return None
    
    def get_exchange(self, exchange_name: Optional[str] = None) -> Optional[ccxt.Exchange]:
        """Get exchange instance by name or return primary exchange"""
        
        if exchange_name:
            return self.exchanges.get(exchange_name)
        elif self.primary_exchange:
            return self.exchanges.get(self.primary_exchange)
        else:
            return None
    
    def get_available_exchanges(self) -> List[str]:
        """Get list of available/initialized exchanges"""
        return self.active_exchanges.copy()
    
    def set_primary_exchange(self, exchange_name: str) -> bool:
        """Set primary exchange for default operations"""
        
        if exchange_name in self.active_exchanges:
            self.primary_exchange = exchange_name
            self.logger.info(f"🎯 Primary exchange set to: {exchange_name}")
            return True
        else:
            self.logger.error(f"❌ Exchange {exchange_name} not available")
            return False
    
    def get_unified_ticker(self, symbol: str, exchange_name: Optional[str] = None) -> Optional[UnifiedTicker]:
        """Get unified ticker data from specified exchange or primary"""
        
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return None
        
        try:
            ticker = exchange.fetch_ticker(symbol)
            
            return UnifiedTicker(
                symbol=symbol,
                exchange=exchange_name or self.primary_exchange,
                last_price=ticker.get('last', 0.0),
                bid=ticker.get('bid', 0.0),
                ask=ticker.get('ask', 0.0),
                high_24h=ticker.get('high', 0.0),
                low_24h=ticker.get('low', 0.0),
                volume_24h=ticker.get('baseVolume', 0.0),
                change_24h=ticker.get('change', 0.0),
                change_percent_24h=ticker.get('percentage', 0.0),
                timestamp=datetime.fromtimestamp(ticker.get('timestamp', 0) / 1000)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker for {symbol} from {exchange_name}: {e}")
            return None
    
    def get_unified_balance(self, exchange_name: Optional[str] = None) -> List[UnifiedBalance]:
        """Get unified balance data from specified exchange or primary"""
        
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return []
        
        try:
            balance = exchange.fetch_balance()
            unified_balances = []
            
            for currency, amounts in balance['free'].items():
                if amounts > 0 or balance['used'].get(currency, 0) > 0:
                    unified_balances.append(UnifiedBalance(
                        exchange=exchange_name or self.primary_exchange,
                        currency=currency,
                        free=amounts,
                        used=balance['used'].get(currency, 0),
                        total=balance['total'].get(currency, 0)
                    ))
            
            return unified_balances
            
        except Exception as e:
            self.logger.error(f"Failed to fetch balance from {exchange_name}: {e}")
            return []
    
    def get_unified_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500, 
                         exchange_name: Optional[str] = None) -> pd.DataFrame:
        """Get unified OHLCV data from specified exchange or primary"""
        
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return pd.DataFrame()
        
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['exchange'] = exchange_name or self.primary_exchange
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV for {symbol} from {exchange_name}: {e}")
            return pd.DataFrame()
    
    def place_unified_order(self, symbol: str, side: str, amount: float, 
                           price: Optional[float] = None, order_type: str = 'market',
                           exchange_name: Optional[str] = None) -> Optional[UnifiedOrder]:
        """Place unified order on specified exchange or primary"""
        
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return None
        
        try:
            if order_type == 'market':
                order = exchange.create_market_order(symbol, side, amount)
            elif order_type == 'limit':
                if not price:
                    raise ValueError("Price required for limit orders")
                order = exchange.create_limit_order(symbol, side, amount, price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            return UnifiedOrder(
                id=order['id'],
                exchange=exchange_name or self.primary_exchange,
                symbol=symbol,
                side=side,
                amount=amount,
                price=price or order.get('price', 0),
                order_type=order_type,
                status=order.get('status', 'unknown'),
                filled=order.get('filled', 0),
                remaining=order.get('remaining', amount),
                timestamp=datetime.fromtimestamp(order.get('timestamp', 0) / 1000),
                fee=order.get('fee')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to place order on {exchange_name}: {e}")
            return None
    
    def get_best_price_across_exchanges(self, symbol: str, side: str = 'buy') -> Dict[str, Dict]:
        """Find best price across all available exchanges"""
        
        prices = {}
        
        for exchange_name in self.active_exchanges:
            ticker = self.get_unified_ticker(symbol, exchange_name)
            if ticker:
                if side == 'buy':
                    prices[exchange_name] = {
                        'price': ticker.ask,
                        'exchange': exchange_name,
                        'side': 'buy'
                    }
                else:
                    prices[exchange_name] = {
                        'price': ticker.bid,
                        'exchange': exchange_name,
                        'side': 'sell'
                    }
        
        if not prices:
            return {}
        
        # Find best price
        if side == 'buy':
            best_exchange = min(prices.keys(), key=lambda x: prices[x]['price'])
        else:
            best_exchange = max(prices.keys(), key=lambda x: prices[x]['price'])
        
        return {
            'best': {
                'exchange': best_exchange,
                'price': prices[best_exchange]['price']
            },
            'all_prices': prices
        }
    
    def get_arbitrage_opportunities(self, symbol: str, min_profit_percent: float = 0.5) -> List[Dict]:
        """Find arbitrage opportunities across exchanges"""
        
        opportunities = []
        tickers = {}
        
        # Get tickers from all exchanges
        for exchange_name in self.active_exchanges:
            ticker = self.get_unified_ticker(symbol, exchange_name)
            if ticker:
                tickers[exchange_name] = ticker
        
        if len(tickers) < 2:
            return opportunities
        
        # Find arbitrage opportunities
        exchanges = list(tickers.keys())
        for i in range(len(exchanges)):
            for j in range(i + 1, len(exchanges)):
                exchange_a = exchanges[i]
                exchange_b = exchanges[j]
                
                ticker_a = tickers[exchange_a]
                ticker_b = tickers[exchange_b]
                
                # Calculate potential profit
                if ticker_a.ask > 0 and ticker_b.bid > 0:
                    # Buy on A, sell on B
                    profit_percent = ((ticker_b.bid - ticker_a.ask) / ticker_a.ask) * 100
                    if profit_percent > min_profit_percent:
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': exchange_a,
                            'sell_exchange': exchange_b,
                            'buy_price': ticker_a.ask,
                            'sell_price': ticker_b.bid,
                            'profit_percent': profit_percent,
                            'profit_absolute': ticker_b.bid - ticker_a.ask
                        })
                
                # Buy on B, sell on A
                if ticker_b.ask > 0 and ticker_a.bid > 0:
                    profit_percent = ((ticker_a.bid - ticker_b.ask) / ticker_b.ask) * 100
                    if profit_percent > min_profit_percent:
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': exchange_b,
                            'sell_exchange': exchange_a,
                            'buy_price': ticker_b.ask,
                            'sell_price': ticker_a.bid,
                            'profit_percent': profit_percent,
                            'profit_absolute': ticker_a.bid - ticker_b.ask
                        })
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
        
        return opportunities
    
    def get_exchange_status(self) -> Dict[str, Dict]:
        """Get status of all exchanges"""
        
        status = {}
        
        for exchange_name in self.active_exchanges:
            exchange = self.exchanges[exchange_name]
            config = self.exchange_configs[exchange_name]
            settings = self.exchange_settings[exchange_name]
            
            try:
                # Test with a simple API call
                exchange.fetch_ticker(settings['popular_pairs'][0])
                
                status[exchange_name] = {
                    'status': 'online',
                    'sandbox': config.sandbox,
                    'rate_limit': settings['rate_limit'],
                    'fee_structure': settings['fee_structure'],
                    'supported_pairs': len(exchange.symbols) if hasattr(exchange, 'symbols') else 'unknown',
                    'last_check': datetime.now().isoformat()
                }
                
            except Exception as e:
                status[exchange_name] = {
                    'status': 'offline',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
        
        return status
    
    def get_supported_symbols(self, exchange_name: Optional[str] = None) -> List[str]:
        """Get supported trading symbols for exchange"""
        
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            return []
        
        try:
            exchange.load_markets()
            return list(exchange.symbols)
        except Exception as e:
            self.logger.error(f"Failed to load symbols from {exchange_name}: {e}")
            return []
    
    def compare_fees_across_exchanges(self, symbol: str, amount: float) -> Dict[str, Dict]:
        """Compare trading fees across exchanges for a specific trade"""
        
        fee_comparison = {}
        
        for exchange_name in self.active_exchanges:
            settings = self.exchange_settings[exchange_name]
            fee_structure = settings['fee_structure']
            
            # Calculate estimated fees
            maker_fee = amount * fee_structure['maker']
            taker_fee = amount * fee_structure['taker']
            
            fee_comparison[exchange_name] = {
                'maker_fee': maker_fee,
                'taker_fee': taker_fee,
                'maker_rate': fee_structure['maker'],
                'taker_rate': fee_structure['taker'],
                'estimated_cost': taker_fee  # Assume taker for market orders
            }
        
        return fee_comparison
    
    def get_multi_exchange_summary(self) -> Dict:
        """Get comprehensive summary of multi-exchange setup"""
        
        return {
            'total_exchanges': len(self.active_exchanges),
            'active_exchanges': self.active_exchanges,
            'primary_exchange': self.primary_exchange,
            'exchange_status': self.get_exchange_status(),
            'supported_features': {
                'arbitrage_detection': True,
                'best_price_routing': True,
                'unified_interface': True,
                'cross_exchange_comparison': True,
                'multi_exchange_balances': True
            },
            'initialization_time': datetime.now().isoformat()
        }

def main():
    """Demo of multi-exchange functionality"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🌐 MULTI-EXCHANGE MANAGER DEMO")
    print("=" * 40)
    
    # Initialize multi-exchange manager
    manager = MultiExchangeManager(logger)
    
    if not manager.active_exchanges:
        print("❌ No exchanges initialized. Please check your API credentials.")
        return
    
    # Show summary
    summary = manager.get_multi_exchange_summary()
    print(f"✅ Initialized {summary['total_exchanges']} exchanges:")
    for exchange in summary['active_exchanges']:
        print(f"   - {exchange.upper()}")
    
    print(f"🎯 Primary exchange: {summary['primary_exchange'].upper()}")
    
    # Test unified ticker
    print(f"\n📊 Testing unified ticker (BTC/USDT):")
    for exchange in manager.active_exchanges:
        ticker = manager.get_unified_ticker('BTC/USDT', exchange)
        if ticker:
            print(f"   {exchange.upper()}: ${ticker.last_price:.2f}")
    
    # Find best price
    print(f"\n💰 Best price comparison:")
    best_prices = manager.get_best_price_across_exchanges('BTC/USDT')
    if best_prices:
        best = best_prices['best']
        print(f"   Best buy price: ${best['price']:.2f} on {best['exchange'].upper()}")
    
    # Check arbitrage opportunities
    print(f"\n🔄 Arbitrage opportunities:")
    arbitrage = manager.get_arbitrage_opportunities('BTC/USDT', min_profit_percent=0.1)
    if arbitrage:
        for opp in arbitrage[:3]:  # Show top 3
            print(f"   Buy {opp['buy_exchange'].upper()} @ ${opp['buy_price']:.2f}, "
                  f"Sell {opp['sell_exchange'].upper()} @ ${opp['sell_price']:.2f} "
                  f"({opp['profit_percent']:.2f}% profit)")
    else:
        print("   No arbitrage opportunities found")
    
    print(f"\n🎉 Multi-exchange setup complete!")
    print("✅ True multi-exchange support implemented!")
    print("✅ No longer Binance-centric!")

if __name__ == "__main__":
    main() 