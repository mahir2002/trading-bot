-- AI Crypto Trading Bot Database Schema
-- Comprehensive database design for multi-exchange, multi-coin trading system

-- Create database
CREATE DATABASE IF NOT EXISTS crypto_trading_bot;
USE crypto_trading_bot;

-- 1. Coins table - Master list of all tracked cryptocurrencies
CREATE TABLE IF NOT EXISTS coins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    contract_address VARCHAR(100),
    network VARCHAR(50), -- ethereum, bsc, polygon, solana, etc.
    exchange VARCHAR(50), -- binance, coinbase, uniswap, etc.
    launch_date TIMESTAMP,
    market_cap DECIMAL(20, 2),
    total_supply DECIMAL(30, 8),
    circulating_supply DECIMAL(30, 8),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    risk_score DECIMAL(3, 2), -- 0.00 to 10.00
    liquidity_score DECIMAL(3, 2),
    social_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_coin (symbol, network, exchange)
);

-- 2. Trading pairs table
CREATE TABLE IF NOT EXISTS trading_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_coin_id INTEGER,
    quote_coin_id INTEGER,
    exchange VARCHAR(50) NOT NULL,
    pair_symbol VARCHAR(50) NOT NULL, -- BTCUSDT, ETHBTC, etc.
    is_active BOOLEAN DEFAULT TRUE,
    min_trade_amount DECIMAL(20, 8),
    max_trade_amount DECIMAL(20, 8),
    price_precision INTEGER,
    quantity_precision INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_coin_id) REFERENCES coins(id),
    FOREIGN KEY (quote_coin_id) REFERENCES coins(id),
    UNIQUE KEY unique_pair (base_coin_id, quote_coin_id, exchange)
);

-- 3. Price history table - Historical price data
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    price_change_24h DECIMAL(10, 4),
    volume_change_24h DECIMAL(10, 4),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    exchange VARCHAR(50),
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    INDEX idx_coin_timestamp (coin_id, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- 4. Bot trades table - All trading activity
CREATE TABLE IF NOT EXISTS bot_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id VARCHAR(100) UNIQUE, -- Exchange trade ID
    coin_id INTEGER NOT NULL,
    trading_pair_id INTEGER,
    action ENUM('BUY', 'SELL', 'HOLD') NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    total_value DECIMAL(20, 2) NOT NULL,
    fees DECIMAL(20, 8) DEFAULT 0,
    profit_loss DECIMAL(20, 2),
    profit_loss_percentage DECIMAL(10, 4),
    strategy_used VARCHAR(100),
    confidence_score DECIMAL(3, 2),
    exchange VARCHAR(50) NOT NULL,
    order_type ENUM('MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT'),
    status ENUM('PENDING', 'FILLED', 'CANCELLED', 'FAILED') DEFAULT 'PENDING',
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    FOREIGN KEY (trading_pair_id) REFERENCES trading_pairs(id),
    INDEX idx_coin_date (coin_id, created_at),
    INDEX idx_strategy (strategy_used),
    INDEX idx_profit_loss (profit_loss)
);

-- 5. Trading signals table - AI-generated signals
CREATE TABLE IF NOT EXISTS trading_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    signal_type ENUM('BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL') NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL, -- 0.00 to 1.00
    price_target DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    timeframe VARCHAR(10), -- 1m, 5m, 15m, 1h, 4h, 1d
    strategy_name VARCHAR(100),
    indicators_used TEXT, -- JSON array of indicators
    market_conditions TEXT, -- JSON object
    risk_level ENUM('LOW', 'MEDIUM', 'HIGH', 'EXTREME'),
    is_executed BOOLEAN DEFAULT FALSE,
    execution_trade_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    FOREIGN KEY (execution_trade_id) REFERENCES bot_trades(id),
    INDEX idx_coin_signal (coin_id, signal_type),
    INDEX idx_confidence (confidence),
    INDEX idx_created_at (created_at)
);

-- 6. Technical indicators table - Calculated indicators
CREATE TABLE IF NOT EXISTS technical_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    rsi_14 DECIMAL(5, 2),
    rsi_21 DECIMAL(5, 2),
    macd_line DECIMAL(10, 6),
    macd_signal DECIMAL(10, 6),
    macd_histogram DECIMAL(10, 6),
    bb_upper DECIMAL(20, 8),
    bb_middle DECIMAL(20, 8),
    bb_lower DECIMAL(20, 8),
    sma_20 DECIMAL(20, 8),
    sma_50 DECIMAL(20, 8),
    sma_200 DECIMAL(20, 8),
    ema_12 DECIMAL(20, 8),
    ema_26 DECIMAL(20, 8),
    volume_sma_20 DECIMAL(20, 2),
    stoch_k DECIMAL(5, 2),
    stoch_d DECIMAL(5, 2),
    williams_r DECIMAL(5, 2),
    atr_14 DECIMAL(10, 6),
    adx_14 DECIMAL(5, 2),
    cci_20 DECIMAL(8, 2),
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    UNIQUE KEY unique_indicator (coin_id, timeframe, timestamp),
    INDEX idx_coin_timeframe (coin_id, timeframe),
    INDEX idx_timestamp (timestamp)
);

-- 7. Social sentiment table - Social media and news sentiment
CREATE TABLE IF NOT EXISTS social_sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    platform VARCHAR(50) NOT NULL, -- twitter, reddit, telegram, news
    sentiment_score DECIMAL(3, 2), -- -1.00 to 1.00
    mention_count INTEGER DEFAULT 0,
    positive_mentions INTEGER DEFAULT 0,
    negative_mentions INTEGER DEFAULT 0,
    neutral_mentions INTEGER DEFAULT 0,
    influence_score DECIMAL(3, 2), -- Weighted by follower count
    trending_rank INTEGER,
    keywords TEXT, -- JSON array
    sample_text TEXT,
    data_source VARCHAR(100),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    INDEX idx_coin_platform (coin_id, platform),
    INDEX idx_sentiment_score (sentiment_score),
    INDEX idx_collected_at (collected_at)
);

-- 8. Portfolio holdings table - Current bot positions
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    average_buy_price DECIMAL(20, 8),
    current_price DECIMAL(20, 8),
    total_invested DECIMAL(20, 2),
    current_value DECIMAL(20, 2),
    unrealized_pnl DECIMAL(20, 2),
    unrealized_pnl_percentage DECIMAL(10, 4),
    first_buy_date TIMESTAMP,
    last_trade_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    UNIQUE KEY unique_holding (coin_id, exchange),
    INDEX idx_exchange (exchange),
    INDEX idx_unrealized_pnl (unrealized_pnl)
);

-- 9. Risk management table - Risk parameters and limits
CREATE TABLE IF NOT EXISTS risk_management (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER,
    exchange VARCHAR(50),
    max_position_size DECIMAL(10, 4), -- Percentage of portfolio
    stop_loss_percentage DECIMAL(5, 2),
    take_profit_percentage DECIMAL(5, 2),
    daily_loss_limit DECIMAL(10, 2),
    max_trades_per_day INTEGER,
    min_liquidity_requirement DECIMAL(20, 2),
    max_risk_score DECIMAL(3, 2),
    blacklisted BOOLEAN DEFAULT FALSE,
    blacklist_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    INDEX idx_coin_exchange (coin_id, exchange)
);

-- 10. API usage tracking table - Monitor API calls and limits
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_provider VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    calls_made INTEGER DEFAULT 0,
    calls_limit INTEGER,
    reset_time TIMESTAMP,
    last_call_time TIMESTAMP,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    date DATE DEFAULT (DATE('now')),
    UNIQUE KEY unique_api_daily (api_provider, endpoint, date),
    INDEX idx_provider_date (api_provider, date)
);

-- 11. Strategy performance table - Track strategy effectiveness
CREATE TABLE IF NOT EXISTS strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name VARCHAR(100) NOT NULL,
    timeframe VARCHAR(10),
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5, 2),
    total_profit_loss DECIMAL(20, 2),
    average_profit_per_trade DECIMAL(20, 2),
    max_drawdown DECIMAL(10, 4),
    sharpe_ratio DECIMAL(6, 4),
    sortino_ratio DECIMAL(6, 4),
    profit_factor DECIMAL(6, 4),
    largest_win DECIMAL(20, 2),
    largest_loss DECIMAL(20, 2),
    average_hold_time INTEGER, -- in minutes
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start DATE,
    period_end DATE,
    UNIQUE KEY unique_strategy_period (strategy_name, timeframe, period_start),
    INDEX idx_strategy_performance (strategy_name, win_rate),
    INDEX idx_profit_loss (total_profit_loss)
);

-- 12. Market conditions table - Overall market state
CREATE TABLE IF NOT EXISTS market_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    market_trend ENUM('BULL', 'BEAR', 'SIDEWAYS', 'VOLATILE') NOT NULL,
    fear_greed_index INTEGER, -- 0-100
    total_market_cap DECIMAL(20, 2),
    btc_dominance DECIMAL(5, 2),
    eth_dominance DECIMAL(5, 2),
    volume_24h DECIMAL(20, 2),
    active_cryptocurrencies INTEGER,
    market_cap_change_24h DECIMAL(10, 4),
    volatility_index DECIMAL(5, 2),
    sentiment_score DECIMAL(3, 2), -- -1.00 to 1.00
    news_sentiment DECIMAL(3, 2),
    social_sentiment DECIMAL(3, 2),
    INDEX idx_timestamp (timestamp),
    INDEX idx_market_trend (market_trend)
);

-- 13. New coin alerts table - Track newly discovered coins
CREATE TABLE IF NOT EXISTS new_coin_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    discovery_source VARCHAR(100), -- coingecko, cmc, dexscreener, etc.
    initial_price DECIMAL(20, 8),
    initial_market_cap DECIMAL(20, 2),
    initial_volume_24h DECIMAL(20, 2),
    liquidity_pools TEXT, -- JSON array
    social_links TEXT, -- JSON object
    contract_verified BOOLEAN DEFAULT FALSE,
    audit_status VARCHAR(50),
    team_info TEXT, -- JSON object
    tokenomics TEXT, -- JSON object
    risk_assessment TEXT, -- JSON object
    recommendation ENUM('BUY', 'WATCH', 'AVOID') DEFAULT 'WATCH',
    alert_sent BOOLEAN DEFAULT FALSE,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    INDEX idx_discovery_source (discovery_source),
    INDEX idx_discovered_at (discovered_at),
    INDEX idx_recommendation (recommendation)
);

-- 14. Backtesting results table - Store backtesting data
CREATE TABLE IF NOT EXISTS backtesting_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name VARCHAR(100) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(20, 2) NOT NULL,
    final_capital DECIMAL(20, 2) NOT NULL,
    total_return DECIMAL(10, 4),
    annual_return DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    sharpe_ratio DECIMAL(6, 4),
    sortino_ratio DECIMAL(6, 4),
    win_rate DECIMAL(5, 2),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    average_trade_duration INTEGER, -- in hours
    largest_win DECIMAL(20, 2),
    largest_loss DECIMAL(20, 2),
    profit_factor DECIMAL(6, 4),
    volatility DECIMAL(6, 4),
    beta DECIMAL(6, 4),
    alpha DECIMAL(6, 4),
    test_parameters TEXT, -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strategy_name (strategy_name),
    INDEX idx_total_return (total_return),
    INDEX idx_created_at (created_at)
);

-- 15. System logs table - Application logging
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    component VARCHAR(100), -- data_collector, trading_engine, etc.
    message TEXT NOT NULL,
    details TEXT, -- JSON object with additional data
    coin_id INTEGER,
    trade_id INTEGER,
    exception_type VARCHAR(100),
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coin_id) REFERENCES coins(id),
    FOREIGN KEY (trade_id) REFERENCES bot_trades(id),
    INDEX idx_level_component (level, component),
    INDEX idx_created_at (created_at)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_coins_symbol ON coins(symbol);
CREATE INDEX IF NOT EXISTS idx_coins_exchange ON coins(exchange);
CREATE INDEX IF NOT EXISTS idx_coins_risk_score ON coins(risk_score);
CREATE INDEX IF NOT EXISTS idx_price_history_coin_time ON price_history(coin_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_bot_trades_profit ON bot_trades(profit_loss DESC);
CREATE INDEX IF NOT EXISTS idx_signals_confidence ON trading_signals(confidence DESC);

-- Insert default data
INSERT OR IGNORE INTO coins (symbol, name, network, exchange, is_verified) VALUES
('BTC', 'Bitcoin', 'bitcoin', 'binance', TRUE),
('ETH', 'Ethereum', 'ethereum', 'binance', TRUE),
('BNB', 'Binance Coin', 'bsc', 'binance', TRUE),
('ADA', 'Cardano', 'cardano', 'binance', TRUE),
('SOL', 'Solana', 'solana', 'binance', TRUE),
('USDT', 'Tether', 'ethereum', 'binance', TRUE),
('USDC', 'USD Coin', 'ethereum', 'binance', TRUE);

-- Insert default risk management parameters
INSERT OR IGNORE INTO risk_management (
    coin_id, max_position_size, stop_loss_percentage, take_profit_percentage,
    daily_loss_limit, max_trades_per_day, min_liquidity_requirement, max_risk_score
) VALUES
(1, 20.0, 5.0, 10.0, 500.0, 10, 1000000.0, 3.0), -- BTC
(2, 15.0, 5.0, 12.0, 400.0, 8, 500000.0, 3.0),   -- ETH
(3, 10.0, 6.0, 15.0, 300.0, 6, 200000.0, 4.0),   -- BNB
(4, 8.0, 7.0, 18.0, 250.0, 5, 100000.0, 5.0),    -- ADA
(5, 8.0, 7.0, 18.0, 250.0, 5, 100000.0, 5.0);    -- SOL 