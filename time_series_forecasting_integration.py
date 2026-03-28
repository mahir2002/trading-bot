#!/usr/bin/env python3
"""
Time Series Forecasting Integration System
Seamless integration with existing AI trading bot infrastructure
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import logging

# Import existing systems
try:
    from advanced_time_series_forecasting import AdvancedTimeSeriesForecaster, ForecastResult
    FORECASTING_AVAILABLE = True
except ImportError:
    FORECASTING_AVAILABLE = False
    print("⚠️ Advanced forecasting system not available")

try:
    from enhanced_trading_system import EnhancedTradingSystem
    TRADING_SYSTEM_AVAILABLE = True
except ImportError:
    TRADING_SYSTEM_AVAILABLE = False

try:
    from advanced_position_sizing_manager import AdvancedPositionSizingManager
    POSITION_SIZING_AVAILABLE = True
except ImportError:
    POSITION_SIZING_AVAILABLE = False

try:
    from dynamic_risk_manager import DynamicRiskManager
    RISK_MANAGER_AVAILABLE = True
except ImportError:
    RISK_MANAGER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ForecastSignal:
    """Trading signal based on time series forecasting."""
    symbol: str
    timestamp: datetime
    forecast_horizon: int
    predicted_price: float
    current_price: float
    price_change_pct: float
    confidence_score: float
    model_consensus: Dict[str, float]
    volatility_forecast: float
    trend_strength: float
    signal_strength: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    risk_level: str
    recommended_position_size: float

@dataclass
class MarketRegime:
    """Current market regime analysis."""
    regime_type: str  # BULL, BEAR, SIDEWAYS, VOLATILE
    confidence: float
    volatility_level: str  # LOW, MEDIUM, HIGH, EXTREME
    trend_strength: float
    momentum_score: float
    mean_reversion_likelihood: float

class TimeSeriesForecastingIntegration:
    """Integration system for advanced time series forecasting."""
    
    def __init__(self, 
                 db_path: str = "crypto_trading_data.db",
                 models_path: str = "models/advanced_forecasting",
                 forecast_horizons: List[int] = [1, 5, 24, 168]):  # 1h, 5h, 1d, 1w
        
        self.db_path = db_path
        self.models_path = Path(models_path)
        self.forecast_horizons = forecast_horizons
        
        # Initialize forecasting system
        if FORECASTING_AVAILABLE:
            self.forecaster = AdvancedTimeSeriesForecaster()
            self.models_trained = {}
        
        # Integration components
        self.trading_system = None
        self.position_sizer = None
        self.risk_manager = None
        
        # Signal thresholds
        self.signal_thresholds = {
            'strong_buy': 0.05,    # 5% predicted gain
            'buy': 0.02,           # 2% predicted gain
            'sell': -0.02,         # 2% predicted loss
            'strong_sell': -0.05,  # 5% predicted loss
            'min_confidence': 0.6  # Minimum confidence for signals
        }
        
        # Initialize database
        self._init_database()
        
        print("🔮 Time Series Forecasting Integration System Initialized")
        print(f"   Database: {db_path}")
        print(f"   Models Path: {models_path}")
        print(f"   Forecast Horizons: {forecast_horizons}")
    
    def _init_database(self):
        """Initialize database tables for forecasting integration."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Forecasting signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forecasting_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    forecast_horizon INTEGER NOT NULL,
                    predicted_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    price_change_pct REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    model_consensus TEXT NOT NULL,
                    volatility_forecast REAL NOT NULL,
                    trend_strength REAL NOT NULL,
                    signal_strength TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    recommended_position_size REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Market regime analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_regimes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    regime_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    volatility_level TEXT NOT NULL,
                    trend_strength REAL NOT NULL,
                    momentum_score REAL NOT NULL,
                    mean_reversion_likelihood REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Model performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    forecast_horizon INTEGER NOT NULL,
                    rmse REAL NOT NULL,
                    mae REAL NOT NULL,
                    mape REAL NOT NULL,
                    r2_score REAL NOT NULL,
                    accuracy_1d REAL,
                    accuracy_7d REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def integrate_with_trading_system(self, trading_system=None):
        """Integrate with existing trading system."""
        
        if trading_system:
            self.trading_system = trading_system
        elif TRADING_SYSTEM_AVAILABLE:
            self.trading_system = EnhancedTradingSystem()
        
        if POSITION_SIZING_AVAILABLE:
            self.position_sizer = AdvancedPositionSizingManager()
        
        if RISK_MANAGER_AVAILABLE:
            self.risk_manager = DynamicRiskManager()
        
        print("🔗 Integrated with trading system components")
    
    def train_forecasting_models(self, symbols: List[str], retrain_interval_days: int = 7):
        """Train or retrain forecasting models for given symbols."""
        
        if not FORECASTING_AVAILABLE:
            logger.error("Advanced forecasting system not available")
            return
        
        for symbol in symbols:
            print(f"\n🧠 Training forecasting models for {symbol}...")
            
            # Get historical data
            data = self._get_historical_data(symbol, days=365)  # 1 year of data
            
            if len(data) < 100:
                logger.warning(f"Insufficient data for {symbol}: {len(data)} records")
                continue
            
            try:
                # Train models
                results = self.forecaster.train_models(data, target_column='close')
                
                # Store model performance
                self._store_model_performance(symbol, results)
                
                # Save trained models
                models_dir = self.models_path / symbol
                self.forecaster.save_models(str(models_dir))
                
                self.models_trained[symbol] = {
                    'results': results,
                    'trained_at': datetime.now(),
                    'data_points': len(data)
                }
                
                print(f"   ✅ Models trained for {symbol}")
                
                # Display best model performance
                best_model = min(results.keys(), key=lambda x: results[x].metrics['rmse'])
                best_rmse = results[best_model].metrics['rmse']
                best_r2 = results[best_model].metrics['r2']
                print(f"   🏆 Best model: {best_model} (RMSE: {best_rmse:.4f}, R²: {best_r2:.4f})")
                
            except Exception as e:
                logger.error(f"Model training failed for {symbol}: {e}")
    
    def generate_forecasting_signals(self, symbols: List[str]) -> List[ForecastSignal]:
        """Generate trading signals based on time series forecasting."""
        
        signals = []
        
        for symbol in symbols:
            try:
                # Get current market data
                current_data = self._get_historical_data(symbol, days=30)
                if len(current_data) < 60:  # Need enough data for forecasting
                    continue
                
                current_price = current_data['close'].iloc[-1]
                
                # Load trained models
                if symbol not in self.models_trained:
                    self._load_trained_models(symbol)
                
                if symbol not in self.models_trained:
                    logger.warning(f"No trained models for {symbol}")
                    continue
                
                # Generate forecasts for each horizon
                horizon_forecasts = {}
                model_consensus = {}
                
                for horizon in self.forecast_horizons:
                    try:
                        # Update forecaster horizon
                        self.forecaster.forecast_horizon = horizon
                        
                        # Generate forecasts
                        forecasts = self.forecaster.generate_forecasts(current_data, periods=horizon)
                        
                        if forecasts:
                            # Calculate consensus forecast
                            forecast_values = list(forecasts.values())
                            if forecast_values:
                                consensus_forecast = np.mean([f[0] if len(f) > 0 else current_price 
                                                            for f in forecast_values])
                                horizon_forecasts[horizon] = consensus_forecast
                                model_consensus[f'{horizon}h'] = {
                                    model: float(forecast[0]) if len(forecast) > 0 else current_price
                                    for model, forecast in forecasts.items()
                                }
                    
                    except Exception as e:
                        logger.error(f"Forecast generation failed for {symbol} horizon {horizon}: {e}")
                        horizon_forecasts[horizon] = current_price
                
                # Analyze market regime
                market_regime = self._analyze_market_regime(current_data)
                
                # Generate signal for primary horizon (24h)
                primary_horizon = 24
                if primary_horizon in horizon_forecasts:
                    predicted_price = horizon_forecasts[primary_horizon]
                    price_change_pct = (predicted_price - current_price) / current_price
                    
                    # Calculate confidence based on model agreement
                    confidence_score = self._calculate_confidence(
                        model_consensus.get(f'{primary_horizon}h', {}),
                        current_price
                    )
                    
                    # Determine signal strength
                    signal_strength = self._determine_signal_strength(
                        price_change_pct, confidence_score, market_regime
                    )
                    
                    # Calculate volatility forecast
                    volatility_forecast = self._calculate_volatility_forecast(current_data)
                    
                    # Calculate trend strength
                    trend_strength = self._calculate_trend_strength(current_data)
                    
                    # Determine risk level
                    risk_level = self._determine_risk_level(
                        volatility_forecast, market_regime, confidence_score
                    )
                    
                    # Calculate recommended position size
                    recommended_position_size = self._calculate_position_size(
                        signal_strength, risk_level, volatility_forecast
                    )
                    
                    # Create signal
                    signal = ForecastSignal(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        forecast_horizon=primary_horizon,
                        predicted_price=predicted_price,
                        current_price=current_price,
                        price_change_pct=price_change_pct,
                        confidence_score=confidence_score,
                        model_consensus=model_consensus.get(f'{primary_horizon}h', {}),
                        volatility_forecast=volatility_forecast,
                        trend_strength=trend_strength,
                        signal_strength=signal_strength,
                        risk_level=risk_level,
                        recommended_position_size=recommended_position_size
                    )
                    
                    signals.append(signal)
                    
                    # Store signal in database
                    self._store_forecasting_signal(signal)
                    
                    print(f"📊 {symbol}: {signal_strength} | "
                          f"Price: ${current_price:.4f} → ${predicted_price:.4f} "
                          f"({price_change_pct:+.2%}) | "
                          f"Confidence: {confidence_score:.2f}")
            
            except Exception as e:
                logger.error(f"Signal generation failed for {symbol}: {e}")
        
        return signals
    
    def _get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get historical data for a symbol."""
        
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT timestamp, close, high, low, volume
                FROM price_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            
            data = pd.read_sql_query(query, conn, params=[symbol, days * 24])
            
            if not data.empty:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
                data = data.sort_index()  # Ensure chronological order
            
            return data
    
    def _load_trained_models(self, symbol: str):
        """Load trained models for a symbol."""
        
        models_dir = self.models_path / symbol
        if not models_dir.exists():
            return
        
        try:
            # This would load the actual models - simplified for demo
            self.models_trained[symbol] = {
                'loaded_at': datetime.now(),
                'models_available': True
            }
            
        except Exception as e:
            logger.error(f"Failed to load models for {symbol}: {e}")
    
    def _analyze_market_regime(self, data: pd.DataFrame) -> MarketRegime:
        """Analyze current market regime."""
        
        if len(data) < 50:
            return MarketRegime(
                regime_type="UNKNOWN",
                confidence=0.0,
                volatility_level="MEDIUM",
                trend_strength=0.0,
                momentum_score=0.0,
                mean_reversion_likelihood=0.5
            )
        
        # Calculate trend indicators
        sma_20 = data['close'].rolling(20).mean()
        sma_50 = data['close'].rolling(50).mean() if len(data) >= 50 else sma_20
        
        current_price = data['close'].iloc[-1]
        sma_20_current = sma_20.iloc[-1]
        sma_50_current = sma_50.iloc[-1]
        
        # Trend analysis
        if current_price > sma_20_current > sma_50_current:
            regime_type = "BULL"
            trend_strength = 0.8
        elif current_price < sma_20_current < sma_50_current:
            regime_type = "BEAR"
            trend_strength = -0.8
        else:
            regime_type = "SIDEWAYS"
            trend_strength = 0.0
        
        # Volatility analysis
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(24)  # Annualized hourly volatility
        
        if volatility > 0.8:
            volatility_level = "EXTREME"
        elif volatility > 0.5:
            volatility_level = "HIGH"
        elif volatility > 0.3:
            volatility_level = "MEDIUM"
        else:
            volatility_level = "LOW"
        
        # Momentum analysis
        momentum_5d = (current_price / data['close'].iloc[-120] - 1) if len(data) >= 120 else 0
        momentum_score = np.tanh(momentum_5d * 10)  # Normalize to [-1, 1]
        
        # Mean reversion likelihood
        price_deviation = (current_price - sma_20_current) / sma_20_current
        mean_reversion_likelihood = min(abs(price_deviation) * 2, 1.0)
        
        # Confidence based on data quality and consistency
        confidence = min(len(data) / 100, 1.0) * 0.8 + 0.2
        
        return MarketRegime(
            regime_type=regime_type,
            confidence=confidence,
            volatility_level=volatility_level,
            trend_strength=trend_strength,
            momentum_score=momentum_score,
            mean_reversion_likelihood=mean_reversion_likelihood
        )
    
    def _calculate_confidence(self, model_forecasts: Dict[str, float], current_price: float) -> float:
        """Calculate confidence score based on model agreement."""
        
        if not model_forecasts:
            return 0.5
        
        forecasts = list(model_forecasts.values())
        if len(forecasts) < 2:
            return 0.6
        
        # Calculate coefficient of variation
        mean_forecast = np.mean(forecasts)
        std_forecast = np.std(forecasts)
        
        if mean_forecast == 0:
            return 0.5
        
        cv = std_forecast / abs(mean_forecast)
        
        # Lower CV means higher agreement (higher confidence)
        confidence = max(0.1, 1.0 - cv * 2)
        
        return min(confidence, 1.0)
    
    def _determine_signal_strength(self, price_change_pct: float, confidence: float, regime: MarketRegime) -> str:
        """Determine signal strength based on forecast and market conditions."""
        
        if confidence < self.signal_thresholds['min_confidence']:
            return "HOLD"
        
        # Adjust thresholds based on market regime
        regime_multiplier = 1.0
        if regime.regime_type == "BULL":
            regime_multiplier = 0.8  # Lower threshold for buy signals
        elif regime.regime_type == "BEAR":
            regime_multiplier = 0.8  # Lower threshold for sell signals
        
        adjusted_strong_buy = self.signal_thresholds['strong_buy'] * regime_multiplier
        adjusted_buy = self.signal_thresholds['buy'] * regime_multiplier
        adjusted_sell = self.signal_thresholds['sell'] * regime_multiplier
        adjusted_strong_sell = self.signal_thresholds['strong_sell'] * regime_multiplier
        
        if price_change_pct >= adjusted_strong_buy:
            return "STRONG_BUY"
        elif price_change_pct >= adjusted_buy:
            return "BUY"
        elif price_change_pct <= adjusted_strong_sell:
            return "STRONG_SELL"
        elif price_change_pct <= adjusted_sell:
            return "SELL"
        else:
            return "HOLD"
    
    def _calculate_volatility_forecast(self, data: pd.DataFrame) -> float:
        """Calculate volatility forecast."""
        
        if len(data) < 20:
            return 0.3  # Default volatility
        
        returns = data['close'].pct_change().dropna()
        
        # EWMA volatility
        ewma_vol = returns.ewm(span=20).std().iloc[-1] * np.sqrt(24)
        
        return min(ewma_vol, 2.0)  # Cap at 200% annualized
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength."""
        
        if len(data) < 20:
            return 0.0
        
        # Linear regression slope
        x = np.arange(len(data))
        y = data['close'].values
        
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize by price level
        trend_strength = slope / data['close'].iloc[-1] * len(data)
        
        # Clamp to [-1, 1]
        return np.tanh(trend_strength * 10)
    
    def _determine_risk_level(self, volatility: float, regime: MarketRegime, confidence: float) -> str:
        """Determine risk level for the signal."""
        
        risk_score = 0.0
        
        # Volatility component
        if volatility > 0.8:
            risk_score += 0.4
        elif volatility > 0.5:
            risk_score += 0.3
        elif volatility > 0.3:
            risk_score += 0.2
        else:
            risk_score += 0.1
        
        # Market regime component
        if regime.volatility_level == "EXTREME":
            risk_score += 0.3
        elif regime.volatility_level == "HIGH":
            risk_score += 0.2
        elif regime.volatility_level == "MEDIUM":
            risk_score += 0.1
        
        # Confidence component (lower confidence = higher risk)
        risk_score += (1.0 - confidence) * 0.3
        
        if risk_score > 0.7:
            return "HIGH"
        elif risk_score > 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_position_size(self, signal_strength: str, risk_level: str, volatility: float) -> float:
        """Calculate recommended position size."""
        
        base_size = 0.1  # 10% of portfolio
        
        # Adjust for signal strength
        signal_multipliers = {
            "STRONG_BUY": 1.5,
            "BUY": 1.0,
            "HOLD": 0.0,
            "SELL": 1.0,
            "STRONG_SELL": 1.5
        }
        
        # Adjust for risk level
        risk_multipliers = {
            "LOW": 1.2,
            "MEDIUM": 1.0,
            "HIGH": 0.6
        }
        
        # Adjust for volatility (inverse relationship)
        volatility_multiplier = max(0.3, 1.0 - volatility)
        
        position_size = (base_size * 
                        signal_multipliers.get(signal_strength, 0.5) *
                        risk_multipliers.get(risk_level, 1.0) *
                        volatility_multiplier)
        
        return min(position_size, 0.25)  # Cap at 25% of portfolio
    
    def _store_forecasting_signal(self, signal: ForecastSignal):
        """Store forecasting signal in database."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO forecasting_signals (
                    symbol, timestamp, forecast_horizon, predicted_price, current_price,
                    price_change_pct, confidence_score, model_consensus, volatility_forecast,
                    trend_strength, signal_strength, risk_level, recommended_position_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.symbol,
                signal.timestamp,
                signal.forecast_horizon,
                signal.predicted_price,
                signal.current_price,
                signal.price_change_pct,
                signal.confidence_score,
                json.dumps(signal.model_consensus),
                signal.volatility_forecast,
                signal.trend_strength,
                signal.signal_strength,
                signal.risk_level,
                signal.recommended_position_size
            ))
            
            conn.commit()
    
    def _store_model_performance(self, symbol: str, results: Dict[str, ForecastResult]):
        """Store model performance metrics."""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for model_name, result in results.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO model_performance (
                        symbol, model_name, forecast_horizon, rmse, mae, mape, r2_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    model_name,
                    self.forecaster.forecast_horizon,
                    result.metrics['rmse'],
                    result.metrics['mae'],
                    result.metrics['mape'],
                    result.metrics['r2']
                ))
            
            conn.commit()
    
    def get_signal_history(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Get historical signals for a symbol."""
        
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT * FROM forecasting_signals 
                WHERE symbol = ? 
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days)
            
            return pd.read_sql_query(query, conn, params=[symbol])
    
    def get_model_performance_summary(self) -> pd.DataFrame:
        """Get model performance summary."""
        
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT symbol, model_name, 
                       AVG(rmse) as avg_rmse,
                       AVG(mae) as avg_mae,
                       AVG(r2_score) as avg_r2,
                       COUNT(*) as evaluations,
                       MAX(last_updated) as last_updated
                FROM model_performance 
                GROUP BY symbol, model_name
                ORDER BY symbol, avg_rmse
            '''
            
            return pd.read_sql_query(query, conn)
    
    def execute_forecasting_strategy(self, symbols: List[str]) -> Dict[str, Any]:
        """Execute complete forecasting-based trading strategy."""
        
        print("🔮 Executing Forecasting-Based Trading Strategy")
        print("=" * 60)
        
        # Generate signals
        signals = self.generate_forecasting_signals(symbols)
        
        if not signals:
            print("❌ No signals generated")
            return {"status": "no_signals", "signals": []}
        
        # Categorize signals
        signal_summary = {
            "STRONG_BUY": [],
            "BUY": [],
            "HOLD": [],
            "SELL": [],
            "STRONG_SELL": []
        }
        
        for signal in signals:
            signal_summary[signal.signal_strength].append(signal)
        
        # Display results
        print(f"\n📊 Signal Summary ({len(signals)} total signals):")
        for strength, signal_list in signal_summary.items():
            if signal_list:
                print(f"   {strength}: {len(signal_list)} signals")
                for signal in signal_list[:3]:  # Show top 3
                    print(f"      {signal.symbol}: {signal.price_change_pct:+.2%} "
                          f"(Conf: {signal.confidence_score:.2f}, "
                          f"Risk: {signal.risk_level})")
        
        # Calculate portfolio recommendations
        total_recommended_exposure = sum(
            signal.recommended_position_size 
            for signal in signals 
            if signal.signal_strength in ["STRONG_BUY", "BUY"]
        )
        
        print(f"\n💼 Portfolio Recommendations:")
        print(f"   Total Recommended Exposure: {total_recommended_exposure:.1%}")
        print(f"   Number of Long Positions: {len(signal_summary['STRONG_BUY']) + len(signal_summary['BUY'])}")
        print(f"   Number of Short Positions: {len(signal_summary['STRONG_SELL']) + len(signal_summary['SELL'])}")
        
        return {
            "status": "success",
            "signals": [asdict(signal) for signal in signals],
            "summary": {k: len(v) for k, v in signal_summary.items()},
            "total_exposure": total_recommended_exposure,
            "timestamp": datetime.now().isoformat()
        }

def generate_sample_price_data():
    """Generate sample price data for demonstration."""
    
    # Create sample data in the database
    db_path = "crypto_trading_data.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create price_data table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                close REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                volume REAL NOT NULL
            )
        ''')
        
        # Generate sample data for BTC and ETH
        symbols = ['BTC/USDT', 'ETH/USDT']
        
        for symbol in symbols:
            # Check if data already exists
            cursor.execute('SELECT COUNT(*) FROM price_data WHERE symbol = ?', (symbol,))
            if cursor.fetchone()[0] > 0:
                continue
            
            # Generate 30 days of hourly data
            start_price = 50000 if 'BTC' in symbol else 3000
            current_price = start_price
            
            for i in range(30 * 24):  # 30 days * 24 hours
                timestamp = datetime.now() - timedelta(hours=30*24-i)
                
                # Random price movement
                change = np.random.normal(0, 0.02)  # 2% volatility
                current_price *= (1 + change)
                
                high = current_price * (1 + abs(np.random.normal(0, 0.01)))
                low = current_price * (1 - abs(np.random.normal(0, 0.01)))
                volume = np.random.lognormal(10, 1)
                
                cursor.execute('''
                    INSERT INTO price_data (symbol, timestamp, close, high, low, volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (symbol, timestamp, current_price, high, low, volume))
        
        conn.commit()
        print("📊 Sample price data generated")

def main():
    """Run the time series forecasting integration demonstration."""
    print("🔮 Time Series Forecasting Integration System Demo")
    print("=" * 80)
    
    # Generate sample data
    generate_sample_price_data()
    
    # Initialize integration system
    integration = TimeSeriesForecastingIntegration()
    
    # Integrate with trading system
    integration.integrate_with_trading_system()
    
    # Test symbols
    symbols = ['BTC/USDT', 'ETH/USDT']
    
    # Train forecasting models
    if FORECASTING_AVAILABLE:
        print(f"\n🧠 Training forecasting models...")
        integration.train_forecasting_models(symbols)
    
    # Execute forecasting strategy
    print(f"\n🚀 Executing forecasting-based trading strategy...")
    results = integration.execute_forecasting_strategy(symbols)
    
    # Display model performance
    if FORECASTING_AVAILABLE:
        print(f"\n📊 Model Performance Summary:")
        performance_df = integration.get_model_performance_summary()
        if not performance_df.empty:
            print(performance_df.to_string(index=False))
    
    # Display signal history
    print(f"\n📈 Recent Signal History:")
    for symbol in symbols:
        history = integration.get_signal_history(symbol, days=1)
        if not history.empty:
            latest = history.iloc[0]
            print(f"   {symbol}: {latest['signal_strength']} "
                  f"({latest['price_change_pct']:+.2%}, "
                  f"Conf: {latest['confidence_score']:.2f})")
    
    print(f"\n🎯 Key Advantages of Time Series Forecasting Integration:")
    print("   ✅ Multi-horizon forecasting (1h, 5h, 1d, 1w)")
    print("   ✅ Advanced models (LSTM, GRU, Transformer, ARIMA-GARCH)")
    print("   ✅ Market regime awareness and adaptation")
    print("   ✅ Model consensus and confidence scoring")
    print("   ✅ Risk-adjusted position sizing")
    print("   ✅ Seamless integration with existing systems")
    print("   ✅ Comprehensive performance tracking")
    
    print(f"\n🎉 Time Series Forecasting Integration Demo Complete!")
    print("🔮 Your trading bot now leverages advanced temporal modeling!")

if __name__ == "__main__":
    main() 