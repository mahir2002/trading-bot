#!/usr/bin/env python3
"""
🔧 Advanced Feature Engineering for Cryptocurrency Trading
Comprehensive feature engineering including lagged features, volatility measures,
market microstructure, and external data integration
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Statistical libraries
try:
    from scipy import stats
    from scipy.signal import find_peaks
    from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest, f_regression
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Technical analysis
try:
    import ta
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

# Time series analysis
try:
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """
    Advanced feature engineering for cryptocurrency trading
    Includes lagged features, volatility measures, microstructure, and external data
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.feature_cache = {}
        self.scalers = {}
        
        logger.info("🔧 Advanced Feature Engineer initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for feature engineering"""
        return {
            # Lagged features
            'price_lags': [1, 2, 3, 5, 10, 20, 50],
            'volume_lags': [1, 2, 3, 5, 10],
            'return_lags': [1, 2, 3, 5, 10, 20],
            
            # Volatility windows
            'volatility_windows': [5, 10, 20, 50, 100],
            'garch_windows': [20, 50],
            
            # Technical indicators
            'sma_periods': [5, 10, 20, 50, 100, 200],
            'ema_periods': [5, 10, 20, 50, 100],
            'rsi_periods': [14, 21, 30],
            'bb_periods': [20, 50],
            
            # Microstructure
            'order_book_levels': 10,
            'trade_size_buckets': [100, 1000, 10000, 100000],
            
            # External data
            'sentiment_sources': ['twitter', 'reddit', 'news', 'fear_greed'],
            'macro_indicators': ['vix', 'dxy', 'gold', 'bonds'],
            
            # Feature selection
            'max_features': 200,
            'correlation_threshold': 0.95,
            'importance_threshold': 0.001
        }
    
    def engineer_comprehensive_features(self, 
                                     df: pd.DataFrame,
                                     sentiment_data: Optional[Dict] = None,
                                     macro_data: Optional[Dict] = None,
                                     order_book_data: Optional[pd.DataFrame] = None,
                                     options_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Engineer comprehensive features from all available data sources
        """
        logger.info("🔧 Starting comprehensive feature engineering...")
        
        # Start with base data
        features_df = df.copy()
        
        # 1. Basic price and volume features
        features_df = self._add_basic_features(features_df)
        
        # 2. Lagged features
        features_df = self._add_lagged_features(features_df)
        
        # 3. Advanced volatility measures
        features_df = self._add_volatility_features(features_df)
        
        # 4. Technical indicators (comprehensive)
        features_df = self._add_technical_indicators(features_df)
        
        # 5. Market microstructure features
        if order_book_data is not None:
            features_df = self._add_microstructure_features(features_df, order_book_data)
        else:
            features_df = self._add_simulated_microstructure_features(features_df)
        
        # 6. Time-based features
        features_df = self._add_temporal_features(features_df)
        
        # 7. Statistical features
        features_df = self._add_statistical_features(features_df)
        
        # 8. Sentiment and external data
        if sentiment_data:
            features_df = self._add_sentiment_features(features_df, sentiment_data)
        
        if macro_data:
            features_df = self._add_macro_features(features_df, macro_data)
        
        # 9. Options-based features (if available)
        if options_data is not None:
            features_df = self._add_options_features(features_df, options_data)
        
        # 10. Advanced derived features
        features_df = self._add_derived_features(features_df)
        
        # 11. Feature interactions
        features_df = self._add_feature_interactions(features_df)
        
        # 12. Clean and select features
        features_df = self._clean_and_select_features(features_df)
        
        logger.info(f"✅ Feature engineering complete: {len(features_df.columns)} features created")
        return features_df
    
    def _add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic price and volume features"""
        logger.info("📊 Adding basic price and volume features...")
        
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['abs_returns'] = np.abs(df['returns'])
        
        # Price ratios
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        df['high_close_ratio'] = df['high'] / df['close']
        df['low_close_ratio'] = df['low'] / df['close']
        
        # Volume features
        df['volume_change'] = df['volume'].pct_change()
        df['price_volume'] = df['close'] * df['volume']
        df['volume_price_trend'] = df['volume'] * df['returns']
        
        # Intraday features
        df['intraday_return'] = (df['close'] - df['open']) / df['open']
        df['overnight_return'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        df['intraday_range'] = (df['high'] - df['low']) / df['open']
        
        return df
    
    def _add_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive lagged features"""
        logger.info("⏰ Adding lagged features...")
        
        # Price lags
        for lag in self.config['price_lags']:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'high_lag_{lag}'] = df['high'].shift(lag)
            df[f'low_lag_{lag}'] = df['low'].shift(lag)
            df[f'price_change_{lag}'] = (df['close'] - df['close'].shift(lag)) / df['close'].shift(lag)
        
        # Volume lags
        for lag in self.config['volume_lags']:
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            df[f'volume_change_{lag}'] = (df['volume'] - df['volume'].shift(lag)) / df['volume'].shift(lag)
        
        # Return lags
        for lag in self.config['return_lags']:
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            df[f'abs_returns_lag_{lag}'] = df['abs_returns'].shift(lag)
        
        # Rolling statistics of lags
        for window in [5, 10, 20]:
            df[f'price_lag_mean_{window}'] = df['close'].shift(1).rolling(window).mean()
            df[f'price_lag_std_{window}'] = df['close'].shift(1).rolling(window).std()
            df[f'volume_lag_mean_{window}'] = df['volume'].shift(1).rolling(window).mean()
            df[f'returns_lag_mean_{window}'] = df['returns'].shift(1).rolling(window).mean()
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add advanced volatility measures"""
        logger.info("📈 Adding advanced volatility features...")
        
        # Historical volatility (multiple windows)
        for window in self.config['volatility_windows']:
            df[f'hist_vol_{window}'] = df['returns'].rolling(window).std() * np.sqrt(252)
            df[f'hist_vol_adj_{window}'] = df['returns'].rolling(window).std() * np.sqrt(252) * df['close']
            
            # Parkinson volatility (high-low estimator)
            df[f'parkinson_vol_{window}'] = np.sqrt(
                (1/(4*np.log(2))) * 
                (np.log(df['high']/df['low'])**2).rolling(window).mean()
            ) * np.sqrt(252)
            
            # Garman-Klass volatility
            df[f'gk_vol_{window}'] = np.sqrt(
                0.5 * (np.log(df['high']/df['low'])**2).rolling(window).mean() -
                (2*np.log(2)-1) * (np.log(df['close']/df['open'])**2).rolling(window).mean()
            ) * np.sqrt(252)
            
            # Rogers-Satchell volatility
            df[f'rs_vol_{window}'] = np.sqrt(
                (np.log(df['high']/df['close']) * np.log(df['high']/df['open']) +
                 np.log(df['low']/df['close']) * np.log(df['low']/df['open'])).rolling(window).mean()
            ) * np.sqrt(252)
        
        # Volatility clustering measures
        df['vol_clustering'] = df['abs_returns'].rolling(20).corr(df['abs_returns'].shift(1))
        
        # Volatility regime detection
        vol_20 = df['returns'].rolling(20).std()
        vol_100 = df['returns'].rolling(100).std()
        df['vol_regime'] = (vol_20 / vol_100).fillna(1)
        
        # Volatility skewness and kurtosis
        for window in [20, 50]:
            df[f'vol_skew_{window}'] = df['returns'].rolling(window).skew()
            df[f'vol_kurt_{window}'] = df['returns'].rolling(window).kurt()
        
        # GARCH-like features
        df['garch_vol'] = self._calculate_garch_volatility(df['returns'])
        
        return df
    
    def _calculate_garch_volatility(self, returns: pd.Series, alpha: float = 0.1, beta: float = 0.85) -> pd.Series:
        """Calculate GARCH(1,1) volatility estimate"""
        vol = pd.Series(index=returns.index, dtype=float)
        vol.iloc[0] = returns.std()
        
        for i in range(1, len(returns)):
            if pd.notna(returns.iloc[i-1]) and pd.notna(vol.iloc[i-1]):
                vol.iloc[i] = np.sqrt(
                    (1 - alpha - beta) * returns.var() +
                    alpha * returns.iloc[i-1]**2 +
                    beta * vol.iloc[i-1]**2
                )
            else:
                vol.iloc[i] = vol.iloc[i-1] if pd.notna(vol.iloc[i-1]) else returns.std()
        
        return vol
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators"""
        logger.info("📊 Adding technical indicators...")
        
        # Moving averages
        for period in self.config['sma_periods']:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'price_sma_ratio_{period}'] = df['close'] / df[f'sma_{period}']
        
        for period in self.config['ema_periods']:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            df[f'price_ema_ratio_{period}'] = df['close'] / df[f'ema_{period}']
        
        # RSI variations
        for period in self.config['rsi_periods']:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD variations
        for fast, slow, signal in [(12, 26, 9), (5, 35, 5), (19, 39, 9)]:
            exp1 = df['close'].ewm(span=fast).mean()
            exp2 = df['close'].ewm(span=slow).mean()
            macd = exp1 - exp2
            macd_signal = macd.ewm(span=signal).mean()
            df[f'macd_{fast}_{slow}'] = macd
            df[f'macd_signal_{fast}_{slow}'] = macd_signal
            df[f'macd_histogram_{fast}_{slow}'] = macd - macd_signal
        
        # Bollinger Bands
        for period in self.config['bb_periods']:
            sma = df['close'].rolling(period).mean()
            std = df['close'].rolling(period).std()
            df[f'bb_upper_{period}'] = sma + (std * 2)
            df[f'bb_lower_{period}'] = sma - (std * 2)
            df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / sma
            df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])
        
        # Stochastic oscillators
        for k_period, d_period in [(14, 3), (21, 3), (5, 3)]:
            low_min = df['low'].rolling(k_period).min()
            high_max = df['high'].rolling(k_period).max()
            k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
            df[f'stoch_k_{k_period}'] = k_percent
            df[f'stoch_d_{k_period}'] = k_percent.rolling(d_period).mean()
        
        # Williams %R
        for period in [14, 21]:
            high_max = df['high'].rolling(period).max()
            low_min = df['low'].rolling(period).min()
            df[f'williams_r_{period}'] = -100 * ((high_max - df['close']) / (high_max - low_min))
        
        # Commodity Channel Index (CCI)
        for period in [14, 20]:
            tp = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = tp.rolling(period).mean()
            mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            df[f'cci_{period}'] = (tp - sma_tp) / (0.015 * mad)
        
        # Average True Range (ATR)
        for period in [14, 21, 50]:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df[f'atr_{period}'] = true_range.rolling(period).mean()
            df[f'atr_ratio_{period}'] = df[f'atr_{period}'] / df['close']
        
        return df
    
    def _add_microstructure_features(self, df: pd.DataFrame, order_book_data: pd.DataFrame) -> pd.DataFrame:
        """Add market microstructure features from order book data"""
        logger.info("🏗️ Adding market microstructure features...")
        
        # Bid-ask spread
        df['bid_ask_spread'] = order_book_data['ask_price_1'] - order_book_data['bid_price_1']
        df['bid_ask_spread_pct'] = df['bid_ask_spread'] / order_book_data['mid_price']
        
        # Order book imbalance
        total_bid_volume = order_book_data[[f'bid_volume_{i}' for i in range(1, self.config['order_book_levels']+1)]].sum(axis=1)
        total_ask_volume = order_book_data[[f'ask_volume_{i}' for i in range(1, self.config['order_book_levels']+1)]].sum(axis=1)
        df['order_imbalance'] = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)
        
        # Weighted mid price
        df['weighted_mid_price'] = (
            order_book_data['bid_price_1'] * order_book_data['ask_volume_1'] +
            order_book_data['ask_price_1'] * order_book_data['bid_volume_1']
        ) / (order_book_data['bid_volume_1'] + order_book_data['ask_volume_1'])
        
        # Price impact measures
        df['price_impact'] = np.abs(df['close'] - df['weighted_mid_price']) / df['weighted_mid_price']
        
        # Liquidity measures
        df['bid_liquidity'] = total_bid_volume
        df['ask_liquidity'] = total_ask_volume
        df['total_liquidity'] = total_bid_volume + total_ask_volume
        df['liquidity_imbalance'] = (total_bid_volume - total_ask_volume) / df['total_liquidity']
        
        return df
    
    def _add_simulated_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add simulated microstructure features when order book data is not available"""
        logger.info("🏗️ Adding simulated microstructure features...")
        
        # Simulate bid-ask spread based on volatility
        volatility = df['returns'].rolling(20).std()
        df['simulated_spread'] = volatility * df['close'] * 0.001  # 0.1% of price * volatility
        df['simulated_spread_pct'] = df['simulated_spread'] / df['close']
        
        # Simulate order imbalance based on price momentum
        momentum = df['close'].pct_change(5)
        df['simulated_imbalance'] = np.tanh(momentum * 10)  # Bounded between -1 and 1
        
        # Simulate liquidity based on volume
        df['simulated_liquidity'] = df['volume'] / df['volume'].rolling(50).mean()
        
        # Price impact proxy
        df['price_impact_proxy'] = np.abs(df['returns']) / (df['volume'] / df['volume'].rolling(20).mean())
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features"""
        logger.info("⏰ Adding temporal features...")
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Hour of day
            df['hour'] = df['timestamp'].dt.hour
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            
            # Day of week
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Day of month
            df['day_of_month'] = df['timestamp'].dt.day
            df['dom_sin'] = np.sin(2 * np.pi * df['day_of_month'] / 31)
            df['dom_cos'] = np.cos(2 * np.pi * df['day_of_month'] / 31)
            
            # Month of year
            df['month'] = df['timestamp'].dt.month
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
            
            # Market session indicators
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_market_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 16)).astype(int)
            df['is_asian_session'] = ((df['hour'] >= 0) & (df['hour'] <= 8)).astype(int)
            df['is_european_session'] = ((df['hour'] >= 8) & (df['hour'] <= 16)).astype(int)
            df['is_american_session'] = ((df['hour'] >= 16) & (df['hour'] <= 24)).astype(int)
        
        return df
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add statistical features"""
        logger.info("📊 Adding statistical features...")
        
        # Rolling statistics
        for window in [5, 10, 20, 50]:
            # Moments
            df[f'price_mean_{window}'] = df['close'].rolling(window).mean()
            df[f'price_std_{window}'] = df['close'].rolling(window).std()
            df[f'price_skew_{window}'] = df['close'].rolling(window).skew()
            df[f'price_kurt_{window}'] = df['close'].rolling(window).kurt()
            
            # Quantiles
            df[f'price_q25_{window}'] = df['close'].rolling(window).quantile(0.25)
            df[f'price_q75_{window}'] = df['close'].rolling(window).quantile(0.75)
            df[f'price_iqr_{window}'] = df[f'price_q75_{window}'] - df[f'price_q25_{window}']
            
            # Volume statistics
            df[f'volume_mean_{window}'] = df['volume'].rolling(window).mean()
            df[f'volume_std_{window}'] = df['volume'].rolling(window).std()
            df[f'volume_skew_{window}'] = df['volume'].rolling(window).skew()
        
        # Autocorrelation features
        for lag in [1, 5, 10]:
            df[f'price_autocorr_{lag}'] = df['close'].rolling(50).apply(
                lambda x: x.autocorr(lag=lag) if len(x) > lag else np.nan
            )
            df[f'returns_autocorr_{lag}'] = df['returns'].rolling(50).apply(
                lambda x: x.autocorr(lag=lag) if len(x) > lag else np.nan
            )
        
        # Hurst exponent (market efficiency measure)
        df['hurst_exponent'] = df['close'].rolling(100).apply(self._calculate_hurst_exponent)
        
        # Fractal dimension
        df['fractal_dimension'] = 2 - df['hurst_exponent']
        
        return df
    
    def _calculate_hurst_exponent(self, series: pd.Series) -> float:
        """Calculate Hurst exponent for market efficiency measurement"""
        try:
            if len(series) < 10:
                return np.nan
            
            # Convert to numpy array and remove NaN
            data = series.dropna().values
            if len(data) < 10:
                return np.nan
            
            # Calculate log returns
            log_returns = np.diff(np.log(data))
            
            # Calculate R/S statistic
            n = len(log_returns)
            if n < 2:
                return np.nan
            
            # Mean and standard deviation
            mean_return = np.mean(log_returns)
            std_return = np.std(log_returns)
            
            if std_return == 0:
                return 0.5  # Random walk
            
            # Cumulative deviations
            cumulative_deviations = np.cumsum(log_returns - mean_return)
            
            # Range
            R = np.max(cumulative_deviations) - np.min(cumulative_deviations)
            
            # R/S ratio
            rs_ratio = R / std_return if std_return > 0 else 1
            
            # Hurst exponent approximation
            hurst = np.log(rs_ratio) / np.log(n)
            
            # Bound between 0 and 1
            return max(0, min(1, hurst))
            
        except:
            return 0.5  # Default to random walk
    
    def _add_sentiment_features(self, df: pd.DataFrame, sentiment_data: Dict) -> pd.DataFrame:
        """Add sentiment and social media features"""
        logger.info("💭 Adding sentiment features...")
        
        # Basic sentiment scores
        df['fear_greed_index'] = sentiment_data.get('fear_greed_index', 50)
        df['twitter_sentiment'] = sentiment_data.get('twitter_sentiment', 0)
        df['reddit_sentiment'] = sentiment_data.get('reddit_sentiment', 0)
        df['news_sentiment'] = sentiment_data.get('news_sentiment', 0)
        
        # Composite sentiment
        df['overall_sentiment'] = (
            df['twitter_sentiment'] * 0.3 +
            df['reddit_sentiment'] * 0.2 +
            df['news_sentiment'] * 0.4 +
            (df['fear_greed_index'] - 50) / 100 * 0.1
        )
        
        # Sentiment momentum
        df['sentiment_momentum'] = df['overall_sentiment'].diff()
        df['sentiment_volatility'] = df['overall_sentiment'].rolling(20).std()
        
        # Sentiment extremes
        df['sentiment_extreme'] = (
            (df['fear_greed_index'] < 25) | (df['fear_greed_index'] > 75)
        ).astype(int)
        
        # Social volume metrics
        df['social_volume'] = sentiment_data.get('social_volume', 100)
        df['social_volume_ma'] = df['social_volume'].rolling(20).mean()
        df['social_volume_ratio'] = df['social_volume'] / df['social_volume_ma']
        
        return df
    
    def _add_macro_features(self, df: pd.DataFrame, macro_data: Dict) -> pd.DataFrame:
        """Add macroeconomic features"""
        logger.info("🌍 Adding macroeconomic features...")
        
        # Traditional macro indicators
        df['vix'] = macro_data.get('vix', 20)  # Volatility index
        df['dxy'] = macro_data.get('dxy', 100)  # Dollar index
        df['gold_price'] = macro_data.get('gold', 2000)  # Gold price
        df['bond_yield'] = macro_data.get('bonds', 0.05)  # 10Y treasury yield
        
        # Crypto-specific macro
        df['btc_dominance'] = macro_data.get('btc_dominance', 50)
        df['total_market_cap'] = macro_data.get('total_market_cap', 1e12)
        
        # Macro momentum
        df['vix_momentum'] = df['vix'].diff()
        df['dxy_momentum'] = df['dxy'].diff()
        df['gold_momentum'] = df['gold_price'].diff()
        
        return df
    
    def _add_options_features(self, df: pd.DataFrame, options_data: pd.DataFrame) -> pd.DataFrame:
        """Add options-based features (implied volatility, etc.)"""
        logger.info("📊 Adding options-based features...")
        
        # Implied volatility
        df['implied_volatility'] = options_data.get('iv', 0.5)
        df['iv_rank'] = df['implied_volatility'].rolling(252).rank(pct=True)
        df['iv_percentile'] = df['implied_volatility'].rolling(252).apply(
            lambda x: stats.percentileofscore(x, x.iloc[-1]) / 100
        )
        
        # IV vs HV
        hist_vol = df['returns'].rolling(20).std() * np.sqrt(252)
        df['iv_hv_ratio'] = df['implied_volatility'] / hist_vol
        
        # Put-call ratio
        df['put_call_ratio'] = options_data.get('put_call_ratio', 1.0)
        df['pcr_ma'] = df['put_call_ratio'].rolling(20).mean()
        df['pcr_deviation'] = df['put_call_ratio'] - df['pcr_ma']
        
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add advanced derived features"""
        logger.info("🔬 Adding derived features...")
        
        # Price momentum features
        for period in [5, 10, 20, 50]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'momentum_rank_{period}'] = df[f'momentum_{period}'].rolling(100).rank(pct=True)
        
        # Volatility-adjusted returns
        vol_20 = df['returns'].rolling(20).std()
        df['vol_adj_returns'] = df['returns'] / vol_20
        df['sharpe_ratio_20'] = df['returns'].rolling(20).mean() / vol_20 * np.sqrt(252)
        
        # Support and resistance levels
        df['resistance_level'] = df['high'].rolling(50).max()
        df['support_level'] = df['low'].rolling(50).min()
        df['distance_to_resistance'] = (df['resistance_level'] - df['close']) / df['close']
        df['distance_to_support'] = (df['close'] - df['support_level']) / df['close']
        
        return df
    
    def _add_feature_interactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add feature interactions"""
        logger.info("🔗 Adding feature interactions...")
        
        # Key interaction features (limited to avoid explosion)
        if 'rsi_14' in df.columns and 'hist_vol_20' in df.columns:
            df['rsi_vol_interaction'] = df['rsi_14'] * df['hist_vol_20']
        
        if 'momentum_20' in df.columns and 'volume' in df.columns:
            volume_ratio = df['volume'] / df['volume'].rolling(20).mean()
            df['momentum_volume_interaction'] = df['momentum_20'] * volume_ratio
        
        return df
    
    def _clean_and_select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean features and select the most important ones"""
        logger.info("🧹 Cleaning and selecting features...")
        
        # Remove infinite and NaN values
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Get numeric columns only
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove columns with too many NaN values (>50%)
        valid_cols = []
        for col in numeric_cols:
            if df[col].notna().sum() / len(df) > 0.5:
                valid_cols.append(col)
        
        df_clean = df[valid_cols].copy()
        
        # Forward fill remaining NaN values
        df_clean = df_clean.fillna(method='ffill').fillna(method='bfill')
        
        # Remove highly correlated features
        if len(df_clean.columns) > 10:
            df_clean = self._remove_correlated_features(df_clean)
        
        # Feature selection based on importance (if target is available)
        if 'target' in df.columns and len(df_clean.columns) > self.config['max_features']:
            df_clean = self._select_important_features(df_clean, df['target'])
        
        logger.info(f"✅ Feature cleaning complete: {len(df_clean.columns)} features retained")
        return df_clean
    
    def _remove_correlated_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove highly correlated features"""
        corr_matrix = df.corr().abs()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        
        # Find features with correlation greater than threshold
        to_drop = [column for column in upper_triangle.columns 
                  if any(upper_triangle[column] > self.config['correlation_threshold'])]
        
        return df.drop(columns=to_drop)
    
    def _select_important_features(self, df: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        """Select most important features using statistical tests"""
        try:
            # Align dataframes
            common_index = df.index.intersection(target.index)
            df_aligned = df.loc[common_index]
            target_aligned = target.loc[common_index]
            
            # Remove NaN values
            mask = target_aligned.notna() & df_aligned.notna().all(axis=1)
            df_clean = df_aligned[mask]
            target_clean = target_aligned[mask]
            
            if len(df_clean) < 10:
                return df
            
            # Feature selection
            selector = SelectKBest(score_func=f_regression, k=min(self.config['max_features'], len(df_clean.columns)))
            selected_features = selector.fit_transform(df_clean, target_clean)
            selected_columns = df_clean.columns[selector.get_support()]
            
            return df[selected_columns]
        except:
            return df

def main():
    """Example usage of advanced feature engineering"""
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=1000, freq='1H')
    
    # Create realistic OHLCV data
    base_price = 50000
    returns = np.random.randn(1000) * 0.02
    prices = base_price * np.exp(np.cumsum(returns))
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(1000) * 0.001),
        'high': prices * (1 + np.abs(np.random.randn(1000)) * 0.002),
        'low': prices * (1 - np.abs(np.random.randn(1000)) * 0.002),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 1000)
    })
    
    # Ensure OHLC consistency
    sample_data['high'] = np.maximum(sample_data[['open', 'close']].max(axis=1), sample_data['high'])
    sample_data['low'] = np.minimum(sample_data[['open', 'close']].min(axis=1), sample_data['low'])
    
    # Sample sentiment data
    sentiment_data = {
        'fear_greed_index': np.random.randint(20, 80, 1000),
        'twitter_sentiment': np.random.uniform(-0.3, 0.3, 1000),
        'reddit_sentiment': np.random.uniform(-0.2, 0.2, 1000),
        'news_sentiment': np.random.uniform(-0.1, 0.1, 1000),
        'social_volume': np.random.randint(100, 1000, 1000)
    }
    
    # Sample macro data
    macro_data = {
        'vix': np.random.uniform(15, 35, 1000),
        'dxy': np.random.uniform(95, 105, 1000),
        'gold': np.random.uniform(1800, 2200, 1000),
        'bonds': np.random.uniform(0.02, 0.06, 1000),
        'btc_dominance': np.random.uniform(40, 60, 1000)
    }
    
    # Initialize feature engineer
    feature_engineer = AdvancedFeatureEngineer()
    
    # Engineer features
    print("🔧 Starting advanced feature engineering demonstration...")
    
    # Convert data to proper format for feature engineering
    for key, values in sentiment_data.items():
        sample_data[key] = values[:len(sample_data)]
    
    for key, values in macro_data.items():
        sample_data[key] = values[:len(sample_data)]
    
    # Add target for demonstration
    sample_data['target'] = sample_data['close'].shift(-1)
    
    # Engineer comprehensive features
    featured_data = feature_engineer.engineer_comprehensive_features(
        sample_data,
        sentiment_data=sentiment_data,
        macro_data=macro_data
    )
    
    print(f"\n✅ Feature Engineering Results:")
    print(f"📊 Original features: {len(sample_data.columns)}")
    print(f"📊 Engineered features: {len(featured_data.columns)}")
    print(f"📊 Data points: {len(featured_data)}")
    
    print(f"\n🔧 Feature Categories:")
    feature_categories = {
        'Lagged': len([col for col in featured_data.columns if 'lag' in col]),
        'Volatility': len([col for col in featured_data.columns if 'vol' in col or 'atr' in col]),
        'Technical': len([col for col in featured_data.columns if any(x in col for x in ['sma', 'ema', 'rsi', 'macd', 'bb'])]),
        'Microstructure': len([col for col in featured_data.columns if any(x in col for x in ['spread', 'imbalance', 'liquidity'])]),
        'Temporal': len([col for col in featured_data.columns if any(x in col for x in ['hour', 'day', 'session'])]),
        'Sentiment': len([col for col in featured_data.columns if any(x in col for x in ['sentiment', 'fear', 'social'])]),
        'Statistical': len([col for col in featured_data.columns if any(x in col for x in ['skew', 'kurt', 'hurst'])]),
        'Derived': len([col for col in featured_data.columns if any(x in col for x in ['momentum', 'resistance', 'support'])])
    }
    
    for category, count in feature_categories.items():
        print(f"   {category}: {count} features")
    
    print(f"\n📈 Sample of engineered features:")
    sample_features = featured_data.columns[:10].tolist()
    for feature in sample_features:
        print(f"   • {feature}")
    
    print(f"\n🎯 Advanced feature engineering demonstration completed!")

if __name__ == "__main__":
    main() 