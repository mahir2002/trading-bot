#!/usr/bin/env python3
"""
🎯 MEME COIN SNIPER BOT CONFIGURATION 🎯
Configuration settings for the world-class meme coin sniper bot
"""

import os
from typing import Dict, Any

# =============================================================================
# BLOCKCHAIN & WEB3 CONFIGURATION
# =============================================================================

BLOCKCHAIN_CONFIG = {
    # Ethereum Mainnet
    'ethereum': {
        'rpc_url': os.getenv('ETHEREUM_RPC_URL', 'https://eth-mainnet.alchemyapi.io/v2/YOUR_ALCHEMY_KEY'),
        'chain_id': 1,
        'gas_price_gwei': 20,
        'max_gas_price_gwei': 100,
        'gas_limit': 300000,
        'block_confirmations': 1
    },
    
    # Binance Smart Chain
    'bsc': {
        'rpc_url': os.getenv('BSC_RPC_URL', 'https://bsc-dataseed1.binance.org/'),
        'chain_id': 56,
        'gas_price_gwei': 5,
        'max_gas_price_gwei': 20,
        'gas_limit': 300000,
        'block_confirmations': 1
    },
    
    # Polygon
    'polygon': {
        'rpc_url': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com/'),
        'chain_id': 137,
        'gas_price_gwei': 30,
        'max_gas_price_gwei': 100,
        'gas_limit': 300000,
        'block_confirmations': 1
    },
    
    # Base
    'base': {
        'rpc_url': os.getenv('BASE_RPC_URL', 'https://mainnet.base.org'),
        'chain_id': 8453,
        'gas_price_gwei': 0.1,
        'max_gas_price_gwei': 1,
        'gas_limit': 300000,
        'block_confirmations': 1
    }
}

# =============================================================================
# DEX ROUTER ADDRESSES
# =============================================================================

DEX_ROUTERS = {
    'ethereum': {
        'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
        'sushiswap': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'
    },
    'bsc': {
        'pancakeswap_v2': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
        'pancakeswap_v3': '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4'
    },
    'polygon': {
        'quickswap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
        'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
    },
    'base': {
        'uniswap_v3': '0x2626664c2603336E57B271c5C0b26F421741e481'
    }
}

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================

TRADING_CONFIG = {
    # Risk Management
    'max_position_size_usd': 1000,  # Maximum position size in USD
    'max_total_exposure_usd': 5000,  # Maximum total exposure
    'max_slippage_percent': 5.0,     # Maximum slippage tolerance
    'stop_loss_percent': 15.0,       # Default stop loss
    'take_profit_percent': 50.0,     # Default take profit
    
    # Position Sizing by Risk Level
    'risk_position_sizes': {
        'ULTRA_LOW': 0.005,  # 0.5% of portfolio
        'LOW': 0.01,         # 1% of portfolio
        'MEDIUM': 0.02,      # 2% of portfolio
        'HIGH': 0.05,        # 5% of portfolio
        'EXTREME': 0.1       # 10% of portfolio
    },
    
    # Minimum Requirements
    'min_liquidity_usd': 10000,      # Minimum liquidity to trade
    'min_volume_24h_usd': 5000,      # Minimum 24h volume
    'min_holders': 50,               # Minimum number of holders
    'max_buy_tax_percent': 10.0,     # Maximum buy tax
    'max_sell_tax_percent': 15.0,    # Maximum sell tax
    
    # Timing
    'signal_expiry_minutes': 30,     # Trading signal expiry
    'position_timeout_hours': 24,    # Maximum position hold time
    'cooldown_minutes': 5            # Cooldown between trades
}

# =============================================================================
# SOCIAL MEDIA API CONFIGURATION
# =============================================================================

SOCIAL_MEDIA_CONFIG = {
    # Twitter/X API
    'twitter': {
        'api_key': os.getenv('TWITTER_API_KEY', ''),
        'api_secret': os.getenv('TWITTER_API_SECRET', ''),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
        'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', ''),
        'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', ''),
        'enabled': True
    },
    
    # Reddit API
    'reddit': {
        'client_id': os.getenv('REDDIT_CLIENT_ID', ''),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
        'user_agent': 'MemeSniper/1.0',
        'enabled': True
    },
    
    # Telegram Bot
    'telegram': {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
        'enabled': False
    }
}

# =============================================================================
# MONITORING CONFIGURATION
# =============================================================================

MONITORING_CONFIG = {
    # New Token Detection
    'monitor_new_tokens': True,
    'new_token_check_interval': 10,  # seconds
    'min_token_age_minutes': 5,      # Minimum age before trading
    
    # Price Monitoring
    'price_update_interval': 5,      # seconds
    'price_change_threshold': 0.05,  # 5% price change alert
    
    # Social Sentiment
    'sentiment_update_interval': 300,  # 5 minutes
    'sentiment_threshold': 0.6,        # Minimum sentiment score
    
    # Mempool Monitoring
    'monitor_mempool': True,
    'mempool_check_interval': 1,     # seconds
    'mev_opportunity_threshold': 0.02, # 2% profit threshold
    
    # Contract Analysis
    'analyze_new_contracts': True,
    'honeypot_check_enabled': True,
    'rug_pull_detection_enabled': True
}

# =============================================================================
# DASHBOARD CONFIGURATION
# =============================================================================

DASHBOARD_CONFIG = {
    'host': '127.0.0.1',
    'port': 8098,
    'debug': True,
    'update_interval_ms': 5000,      # 5 seconds
    'slow_update_interval_ms': 30000, # 30 seconds
    'max_trending_tokens': 50,
    'max_trading_signals': 20
}

# =============================================================================
# WALLET CONFIGURATION
# =============================================================================

WALLET_CONFIG = {
    # Private keys (NEVER commit these to version control!)
    'ethereum_private_key': os.getenv('ETHEREUM_PRIVATE_KEY', ''),
    'bsc_private_key': os.getenv('BSC_PRIVATE_KEY', ''),
    'polygon_private_key': os.getenv('POLYGON_PRIVATE_KEY', ''),
    'base_private_key': os.getenv('BASE_PRIVATE_KEY', ''),
    
    # Wallet addresses (derived from private keys)
    'ethereum_address': os.getenv('ETHEREUM_ADDRESS', ''),
    'bsc_address': os.getenv('BSC_ADDRESS', ''),
    'polygon_address': os.getenv('POLYGON_ADDRESS', ''),
    'base_address': os.getenv('BASE_ADDRESS', ''),
    
    # Initial balances (for simulation)
    'initial_balance_eth': 1.0,
    'initial_balance_bnb': 10.0,
    'initial_balance_matic': 1000.0,
    'initial_balance_base': 1.0
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'meme_sniper.log',
    'max_file_size_mb': 100,
    'backup_count': 5
}

# =============================================================================
# MAIN CONFIGURATION FUNCTION
# =============================================================================

def get_config() -> Dict[str, Any]:
    """Get complete configuration for the meme coin sniper bot"""
    return {
        'blockchain': BLOCKCHAIN_CONFIG,
        'dex_routers': DEX_ROUTERS,
        'trading': TRADING_CONFIG,
        'social_media': SOCIAL_MEDIA_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'wallet': WALLET_CONFIG,
        'logging': LOGGING_CONFIG
    }

# =============================================================================
# ENVIRONMENT SETUP HELPER
# =============================================================================

def create_env_template():
    """Create a .env template file with all required environment variables"""
    env_template = """# Meme Coin Sniper Bot Environment Variables
# Copy this file to .env and fill in your actual values

# =============================================================================
# BLOCKCHAIN RPC URLS
# =============================================================================
ETHEREUM_RPC_URL=https://eth-mainnet.alchemyapi.io/v2/YOUR_ALCHEMY_KEY
BSC_RPC_URL=https://bsc-dataseed1.binance.org/
POLYGON_RPC_URL=https://polygon-rpc.com/
BASE_RPC_URL=https://mainnet.base.org

# =============================================================================
# WALLET PRIVATE KEYS (KEEP THESE SECRET!)
# =============================================================================
ETHEREUM_PRIVATE_KEY=your_ethereum_private_key_here
BSC_PRIVATE_KEY=your_bsc_private_key_here
POLYGON_PRIVATE_KEY=your_polygon_private_key_here
BASE_PRIVATE_KEY=your_base_private_key_here

# =============================================================================
# WALLET ADDRESSES
# =============================================================================
ETHEREUM_ADDRESS=your_ethereum_address_here
BSC_ADDRESS=your_bsc_address_here
POLYGON_ADDRESS=your_polygon_address_here
BASE_ADDRESS=your_base_address_here

# =============================================================================
# SOCIAL MEDIA API KEYS
# =============================================================================
# Twitter/X API
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_template)
    
    print("📝 Created .env.template file")
    print("🔑 Copy this to .env and fill in your API keys and private keys")
    print("⚠️  NEVER commit your .env file to version control!")

if __name__ == "__main__":
    create_env_template() 