#!/usr/bin/env python3
"""
🔧 MULTI-EXCHANGE TRADING SYSTEM CONFIGURATION
Comprehensive configuration management for universal trading system
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

@dataclass
class ExchangeSettings:
    """Exchange-specific settings"""
    name: str
    enabled: bool = True
    api_key: str = ""
    secret_key: str = ""
    passphrase: str = ""  # For some exchanges like Coinbase Pro
    sandbox: bool = True
    
    # Trading settings
    max_position_size: float = 1000.0
    min_order_size: float = 0.001
    trading_fee: float = 0.001
    
    # Risk settings
    max_daily_trades: int = 50
    max_portfolio_allocation: float = 0.3  # 30% max per exchange
    
    # Supported pairs
    trading_pairs: List[str] = field(default_factory=lambda: [
        'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT'
    ])

@dataclass
class TradingSettings:
    """General trading settings"""
    
    # Strategy settings
    confidence_threshold: float = 55.0
    max_positions: int = 10
    position_size_percentage: float = 2.0  # 2% per position
    
    # Risk management
    stop_loss_percentage: float = 5.0
    take_profit_percentage: float = 10.0
    max_drawdown_percentage: float = 15.0
    
    # Arbitrage settings
    min_arbitrage_profit: float = 0.5  # 0.5% minimum
    max_arbitrage_positions: int = 3
    arbitrage_timeout: int = 30  # seconds
    
    # Update intervals
    market_data_interval: int = 60  # seconds
    portfolio_update_interval: int = 300  # 5 minutes
    rebalance_interval: int = 3600  # 1 hour

@dataclass
class APISettings:
    """External API settings"""
    
    # CoinGecko
    coingecko_api_key: str = ""
    coingecko_rate_limit: int = 50  # requests per minute
    
    # CoinMarketCap
    coinmarketcap_api_key: str = ""
    coinmarketcap_rate_limit: int = 333  # requests per day for free tier
    
    # DEX Screener
    dexscreener_api_key: str = ""
    dexscreener_rate_limit: int = 300  # requests per minute
    
    # Twitter (for sentiment)
    twitter_bearer_token: str = ""
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    
    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

class MultiExchangeConfig:
    """Main configuration class"""
    
    def __init__(self):
        self.exchanges = self._load_exchange_configs()
        self.trading = self._load_trading_settings()
        self.apis = self._load_api_settings()
        
    def _load_exchange_configs(self) -> Dict[str, ExchangeSettings]:
        """Load exchange configurations"""
        
        exchanges = {
            'binance': ExchangeSettings(
                name='binance',
                enabled=True,
                api_key=os.getenv('BINANCE_API_KEY', ''),
                secret_key=os.getenv('BINANCE_SECRET_KEY', ''),
                sandbox=os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
                trading_fee=0.001,
                max_position_size=5000.0,
                max_portfolio_allocation=0.4,  # Primary exchange
                trading_pairs=[
                    'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT',
                    'DOT/USDT', 'LINK/USDT', 'UNI/USDT', 'AVAX/USDT', 'ATOM/USDT'
                ]
            ),
            
            'coinbase': ExchangeSettings(
                name='coinbase',
                enabled=bool(os.getenv('COINBASE_API_KEY')),
                api_key=os.getenv('COINBASE_API_KEY', ''),
                secret_key=os.getenv('COINBASE_SECRET_KEY', ''),
                passphrase=os.getenv('COINBASE_PASSPHRASE', ''),
                sandbox=True,
                trading_fee=0.005,
                max_position_size=2000.0,
                max_portfolio_allocation=0.25,
                trading_pairs=['BTC/USD', 'ETH/USD', 'ADA/USD', 'SOL/USD']
            ),
            
            'kraken': ExchangeSettings(
                name='kraken',
                enabled=bool(os.getenv('KRAKEN_API_KEY')),
                api_key=os.getenv('KRAKEN_API_KEY', ''),
                secret_key=os.getenv('KRAKEN_SECRET_KEY', ''),
                sandbox=True,
                trading_fee=0.0026,
                max_position_size=2000.0,
                max_portfolio_allocation=0.2,
                trading_pairs=['BTC/USD', 'ETH/USD', 'ADA/USD', 'SOL/USD']
            ),
            
            'bybit': ExchangeSettings(
                name='bybit',
                enabled=bool(os.getenv('BYBIT_API_KEY')),
                api_key=os.getenv('BYBIT_API_KEY', ''),
                secret_key=os.getenv('BYBIT_SECRET_KEY', ''),
                sandbox=True,
                trading_fee=0.001,
                max_position_size=3000.0,
                max_portfolio_allocation=0.25,
                trading_pairs=[
                    'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT'
                ]
            ),
            
            'okx': ExchangeSettings(
                name='okx',
                enabled=bool(os.getenv('OKX_API_KEY')),
                api_key=os.getenv('OKX_API_KEY', ''),
                secret_key=os.getenv('OKX_SECRET_KEY', ''),
                sandbox=True,
                trading_fee=0.0008,
                max_position_size=3000.0,
                max_portfolio_allocation=0.2,
                trading_pairs=[
                    'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'MATIC/USDT'
                ]
            )
        }
        
        return exchanges
    
    def _load_trading_settings(self) -> TradingSettings:
        """Load trading settings"""
        
        return TradingSettings(
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '55.0')),
            max_positions=int(os.getenv('MAX_POSITIONS', '10')),
            position_size_percentage=float(os.getenv('POSITION_SIZE_PCT', '2.0')),
            
            stop_loss_percentage=float(os.getenv('STOP_LOSS_PCT', '5.0')),
            take_profit_percentage=float(os.getenv('TAKE_PROFIT_PCT', '10.0')),
            max_drawdown_percentage=float(os.getenv('MAX_DRAWDOWN_PCT', '15.0')),
            
            min_arbitrage_profit=float(os.getenv('MIN_ARBITRAGE_PROFIT', '0.5')),
            max_arbitrage_positions=int(os.getenv('MAX_ARBITRAGE_POSITIONS', '3')),
            
            market_data_interval=int(os.getenv('MARKET_DATA_INTERVAL', '60')),
            portfolio_update_interval=int(os.getenv('PORTFOLIO_UPDATE_INTERVAL', '300')),
            rebalance_interval=int(os.getenv('REBALANCE_INTERVAL', '3600'))
        )
    
    def _load_api_settings(self) -> APISettings:
        """Load API settings"""
        
        return APISettings(
            coingecko_api_key=os.getenv('COINGECKO_API_KEY', ''),
            coinmarketcap_api_key=os.getenv('COINMARKETCAP_API_KEY', ''),
            dexscreener_api_key=os.getenv('DEXSCREENER_API_KEY', ''),
            
            twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN', ''),
            twitter_api_key=os.getenv('TWITTER_API_KEY', ''),
            twitter_api_secret=os.getenv('TWITTER_API_SECRET', ''),
            
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID', '')
        )
    
    def get_enabled_exchanges(self) -> Dict[str, ExchangeSettings]:
        """Get only enabled exchanges"""
        return {name: config for name, config in self.exchanges.items() if config.enabled}
    
    def get_all_trading_pairs(self) -> List[str]:
        """Get all unique trading pairs across exchanges"""
        all_pairs = set()
        for exchange in self.exchanges.values():
            if exchange.enabled:
                all_pairs.update(exchange.trading_pairs)
        return list(all_pairs)
    
    def save_config(self, filepath: str = 'multi_exchange_config.json'):
        """Save configuration to file"""
        
        config_data = {
            'exchanges': {name: {
                'enabled': ex.enabled,
                'sandbox': ex.sandbox,
                'trading_fee': ex.trading_fee,
                'max_position_size': ex.max_position_size,
                'max_portfolio_allocation': ex.max_portfolio_allocation,
                'trading_pairs': ex.trading_pairs
            } for name, ex in self.exchanges.items()},
            
            'trading': {
                'confidence_threshold': self.trading.confidence_threshold,
                'max_positions': self.trading.max_positions,
                'position_size_percentage': self.trading.position_size_percentage,
                'stop_loss_percentage': self.trading.stop_loss_percentage,
                'take_profit_percentage': self.trading.take_profit_percentage,
                'max_drawdown_percentage': self.trading.max_drawdown_percentage,
                'min_arbitrage_profit': self.trading.min_arbitrage_profit,
                'max_arbitrage_positions': self.trading.max_arbitrage_positions,
                'market_data_interval': self.trading.market_data_interval,
                'portfolio_update_interval': self.trading.portfolio_update_interval,
                'rebalance_interval': self.trading.rebalance_interval
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def print_config_summary(self):
        """Print configuration summary"""
        
        print("\n🔧 MULTI-EXCHANGE TRADING CONFIGURATION")
        print("=" * 60)
        
        print("\n📊 ENABLED EXCHANGES:")
        enabled_exchanges = self.get_enabled_exchanges()
        for name, config in enabled_exchanges.items():
            status = "🟢" if config.api_key else "🔴"
            print(f"   {status} {name.upper()} - {len(config.trading_pairs)} pairs")
        
        print(f"\n🎯 TRADING SETTINGS:")
        print(f"   Confidence Threshold: {self.trading.confidence_threshold}%")
        print(f"   Max Positions: {self.trading.max_positions}")
        print(f"   Position Size: {self.trading.position_size_percentage}%")
        print(f"   Stop Loss: {self.trading.stop_loss_percentage}%")
        print(f"   Take Profit: {self.trading.take_profit_percentage}%")
        
        print(f"\n⚡ ARBITRAGE SETTINGS:")
        print(f"   Min Profit: {self.trading.min_arbitrage_profit}%")
        print(f"   Max Positions: {self.trading.max_arbitrage_positions}")
        
        print(f"\n📡 API STATUS:")
        print(f"   CoinGecko: {'✅' if self.apis.coingecko_api_key else '❌'}")
        print(f"   CoinMarketCap: {'✅' if self.apis.coinmarketcap_api_key else '❌'}")
        print(f"   DEX Screener: {'✅' if self.apis.dexscreener_api_key else '❌'}")
        print(f"   Telegram: {'✅' if self.apis.telegram_bot_token else '❌'}")
        
        print(f"\n🔄 UPDATE INTERVALS:")
        print(f"   Market Data: {self.trading.market_data_interval}s")
        print(f"   Portfolio: {self.trading.portfolio_update_interval}s")
        print(f"   Rebalance: {self.trading.rebalance_interval}s")
        
        total_pairs = len(self.get_all_trading_pairs())
        print(f"\n📈 TOTAL TRADING PAIRS: {total_pairs}")
        print("=" * 60)

# Global configuration instance
config = MultiExchangeConfig()

def main():
    """Demo configuration"""
    config.print_config_summary()
    config.save_config()
    print("\n✅ Configuration saved to multi_exchange_config.json")

if __name__ == "__main__":
    main() 