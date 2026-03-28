#!/usr/bin/env python3
"""
Utility functions for the AI Trading Bot
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import ta
import yfinance as yf

class DataProcessor:
    """Data processing utilities"""
    
    @staticmethod
    def clean_ohlcv_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate OHLCV data"""
        if df.empty:
            return df
        
        # Remove rows with missing values
        df = df.dropna()
        
        # Ensure positive values
        df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
        
        # Ensure high >= low
        df = df[df['high'] >= df['low']]
        
        # Sort by timestamp
        df = df.sort_index()
        
        return df
    
    @staticmethod
    def resample_data(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample OHLCV data to different timeframe"""
        if df.empty:
            return df
        
        # Define aggregation rules
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Resample
        resampled = df.resample(timeframe).agg(agg_dict)
        
        # Remove rows with NaN values
        resampled = resampled.dropna()
        
        return resampled
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame, periods: int = 1) -> pd.Series:
        """Calculate returns for given periods"""
        if df.empty or 'close' not in df.columns:
            return pd.Series()
        
        return df['close'].pct_change(periods=periods)
    
    @staticmethod
    def detect_outliers(series: pd.Series, method: str = 'iqr', threshold: float = 1.5) -> pd.Series:
        """Detect outliers in a series"""
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            return (series < lower_bound) | (series > upper_bound)
        
        elif method == 'zscore':
            z_scores = np.abs((series - series.mean()) / series.std())
            return z_scores > threshold
        
        return pd.Series([False] * len(series), index=series.index)

class TechnicalAnalysis:
    """Advanced technical analysis functions"""
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict:
        """Calculate support and resistance levels"""
        if df.empty or len(df) < window:
            return {'support': [], 'resistance': []}
        
        # Find local minima and maxima
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        # Identify support and resistance levels
        resistance_levels = df[df['high'] == highs]['high'].dropna().unique()
        support_levels = df[df['low'] == lows]['low'].dropna().unique()
        
        return {
            'support': sorted(support_levels),
            'resistance': sorted(resistance_levels, reverse=True)
        }
    
    @staticmethod
    def calculate_fibonacci_levels(df: pd.DataFrame, period: int = 50) -> Dict:
        """Calculate Fibonacci retracement levels"""
        if df.empty or len(df) < period:
            return {}
        
        # Get recent high and low
        recent_data = df.tail(period)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        
        # Calculate Fibonacci levels
        diff = high - low
        levels = {
            '0%': high,
            '23.6%': high - 0.236 * diff,
            '38.2%': high - 0.382 * diff,
            '50%': high - 0.5 * diff,
            '61.8%': high - 0.618 * diff,
            '78.6%': high - 0.786 * diff,
            '100%': low
        }
        
        return levels
    
    @staticmethod
    def calculate_pivot_points(df: pd.DataFrame) -> Dict:
        """Calculate pivot points for the latest day"""
        if df.empty:
            return {}
        
        # Get previous day's data
        prev_day = df.iloc[-1]
        high = prev_day['high']
        low = prev_day['low']
        close = prev_day['close']
        
        # Calculate pivot point
        pivot = (high + low + close) / 3
        
        # Calculate support and resistance levels
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> float:
        """Calculate historical volatility"""
        if df.empty or len(df) < window:
            return 0.0
        
        returns = df['close'].pct_change().dropna()
        volatility = returns.rolling(window=window).std().iloc[-1]
        
        # Annualize volatility (assuming daily data)
        return volatility * np.sqrt(365) if not np.isnan(volatility) else 0.0
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if returns.empty:
            return 0.0
        
        excess_returns = returns.mean() - risk_free_rate / 365  # Daily risk-free rate
        volatility = returns.std()
        
        if volatility == 0:
            return 0.0
        
        return (excess_returns / volatility) * np.sqrt(365)  # Annualized

class MarketRegime:
    """Market regime detection utilities"""
    
    @staticmethod
    def detect_trend(df: pd.DataFrame, window: int = 20) -> str:
        """Detect market trend"""
        if df.empty or len(df) < window:
            return 'unknown'
        
        # Calculate moving averages
        sma_short = df['close'].rolling(window=window//2).mean()
        sma_long = df['close'].rolling(window=window).mean()
        
        if sma_short.iloc[-1] > sma_long.iloc[-1]:
            return 'uptrend'
        elif sma_short.iloc[-1] < sma_long.iloc[-1]:
            return 'downtrend'
        else:
            return 'sideways'
    
    @staticmethod
    def calculate_market_strength(df: pd.DataFrame, window: int = 14) -> float:
        """Calculate market strength using ADX"""
        if df.empty or len(df) < window:
            return 0.0
        
        try:
            adx = ta.trend.adx(df['high'], df['low'], df['close'], window=window)
            return adx.iloc[-1] if not adx.empty else 0.0
        except:
            return 0.0
    
    @staticmethod
    def detect_volatility_regime(df: pd.DataFrame, window: int = 20) -> str:
        """Detect volatility regime"""
        if df.empty or len(df) < window:
            return 'unknown'
        
        # Calculate rolling volatility
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=window).std()
        
        # Get current and historical volatility
        current_vol = volatility.iloc[-1]
        avg_vol = volatility.mean()
        
        if current_vol > avg_vol * 1.5:
            return 'high_volatility'
        elif current_vol < avg_vol * 0.5:
            return 'low_volatility'
        else:
            return 'normal_volatility'

class RiskMetrics:
    """Risk calculation utilities"""
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk"""
        if returns.empty:
            return 0.0
        
        return np.percentile(returns.dropna(), confidence_level * 100)
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Conditional Value at Risk"""
        if returns.empty:
            return 0.0
        
        var = RiskMetrics.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> Dict:
        """Calculate maximum drawdown"""
        if prices.empty:
            return {'max_drawdown': 0.0, 'duration': 0}
        
        # Calculate running maximum
        running_max = prices.expanding().max()
        
        # Calculate drawdown
        drawdown = (prices - running_max) / running_max
        
        # Find maximum drawdown
        max_drawdown = drawdown.min()
        
        # Calculate duration
        drawdown_start = None
        max_duration = 0
        current_duration = 0
        
        for i, dd in enumerate(drawdown):
            if dd < 0:
                if drawdown_start is None:
                    drawdown_start = i
                current_duration = i - drawdown_start + 1
            else:
                if current_duration > max_duration:
                    max_duration = current_duration
                drawdown_start = None
                current_duration = 0
        
        return {
            'max_drawdown': abs(max_drawdown),
            'duration': max_duration
        }
    
    @staticmethod
    def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for position sizing"""
        if avg_loss == 0:
            return 0.0
        
        win_loss_ratio = avg_win / abs(avg_loss)
        kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Cap at 25% for safety
        return min(max(kelly_pct, 0.0), 0.25)

class ConfigManager:
    """Configuration management utilities"""
    
    @staticmethod
    def load_config(config_file: str = 'config.json') -> Dict:
        """Load configuration from file"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return {}
        return {}
    
    @staticmethod
    def save_config(config: Dict, config_file: str = 'config.json'):
        """Save configuration to file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    @staticmethod
    def validate_config(config: Dict) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        required_keys = [
            'BINANCE_API_KEY', 'BINANCE_SECRET_KEY',
            'TRADING_MODE', 'DEFAULT_TRADE_AMOUNT'
        ]
        
        for key in required_keys:
            if key not in config or not config[key]:
                errors.append(f"Missing required configuration: {key}")
        
        # Validate numeric values
        numeric_keys = ['DEFAULT_TRADE_AMOUNT', 'RISK_PERCENTAGE', 'STOP_LOSS_PERCENTAGE']
        for key in numeric_keys:
            if key in config:
                try:
                    float(config[key])
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {key}: {config[key]}")
        
        return errors

class DataFetcher:
    """External data fetching utilities"""
    
    @staticmethod
    def get_fear_greed_index() -> Dict:
        """Get Fear & Greed Index from alternative.me"""
        try:
            import requests
            response = requests.get('https://api.alternative.me/fng/', timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'value': int(data['data'][0]['value']),
                    'classification': data['data'][0]['value_classification'],
                    'timestamp': data['data'][0]['timestamp']
                }
        except Exception as e:
            print(f"Error fetching Fear & Greed Index: {e}")
        
        return {'value': 50, 'classification': 'Neutral', 'timestamp': str(int(datetime.now().timestamp()))}
    
    @staticmethod
    def get_market_cap_data(symbol: str) -> Dict:
        """Get market cap data from CoinGecko"""
        try:
            import requests
            # Convert symbol format (e.g., BTC/USDT -> bitcoin)
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'ADA': 'cardano',
                'DOT': 'polkadot'
            }
            
            base_symbol = symbol.split('/')[0]
            coin_id = symbol_map.get(base_symbol, base_symbol.lower())
            
            url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'market_cap': data['market_data']['market_cap']['usd'],
                    'volume_24h': data['market_data']['total_volume']['usd'],
                    'price_change_24h': data['market_data']['price_change_percentage_24h'],
                    'market_cap_rank': data['market_data']['market_cap_rank']
                }
        except Exception as e:
            print(f"Error fetching market cap data: {e}")
        
        return {}

class PerformanceTracker:
    """Performance tracking utilities"""
    
    def __init__(self, filename: str = 'performance.json'):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load performance data from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading performance data: {e}")
        
        return {
            'trades': [],
            'daily_pnl': {},
            'metrics': {}
        }
    
    def save_data(self):
        """Save performance data to file"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=4, default=str)
        except Exception as e:
            print(f"Error saving performance data: {e}")
    
    def add_trade(self, trade_data: Dict):
        """Add trade to performance tracking"""
        trade_data['timestamp'] = datetime.now().isoformat()
        self.data['trades'].append(trade_data)
        self.save_data()
    
    def update_daily_pnl(self, date: str, pnl: float):
        """Update daily P&L"""
        if date not in self.data['daily_pnl']:
            self.data['daily_pnl'][date] = 0.0
        
        self.data['daily_pnl'][date] += pnl
        self.save_data()
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        trades = self.data['trades']
        
        if not trades:
            return {}
        
        # Extract trade data
        pnls = [trade.get('pnl', 0) for trade in trades if 'pnl' in trade]
        
        if not pnls:
            return {}
        
        # Calculate metrics
        total_trades = len(pnls)
        winning_trades = len([pnl for pnl in pnls if pnl > 0])
        losing_trades = len([pnl for pnl in pnls if pnl < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([pnl for pnl in pnls if pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([pnl for pnl in pnls if pnl < 0]) if losing_trades > 0 else 0
        
        total_pnl = sum(pnls)
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': total_pnl,
            'profit_factor': abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 and losing_trades > 0 else 0
        }
        
        self.data['metrics'] = metrics
        self.save_data()
        
        return metrics 