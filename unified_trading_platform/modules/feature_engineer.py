#!/usr/bin/env python3
"""
Feature Engineering Module
Generates trading features from historical OHLCV data

Author: Trading Bot System
Date: 2025-01-22
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import sqlite3
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineer:
    """Feature engineering for trading data"""
    
    def __init__(self, db_path: str = "data/historical_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Create features directory
        Path("data/features").mkdir(parents=True, exist_ok=True)
        
    async def generate_features_for_coin(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive features for a single coin"""
        try:
            # Load historical data
            df = await self._load_historical_data(symbol, days)
            if df is None or len(df) < 10:
                return {'error': f'Insufficient data for {symbol}'}
            
            # Generate all features
            df = self._generate_all_features(df)
            
            # Generate trading signals
            signals = self._generate_trading_signals(df)
            
            # Save features
            features_file = f"data/features/{symbol}_features.json"
            feature_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'data_points': len(df),
                'signals': signals,
                'latest_values': self._get_latest_values(df),
                'features_csv': f"data/features/{symbol}_features.csv"
            }
            
            # Save CSV with all features
            df.to_csv(f"data/features/{symbol}_features.csv", index=False)
            
            # Save JSON summary
            with open(features_file, 'w') as f:
                json.dump(feature_data, f, indent=2, default=str)
            
            self.logger.info(f"✅ Generated {len(df.columns)} features for {symbol}")
            
            return {
                'symbol': symbol,
                'features_generated': len(df.columns),
                'data_points': len(df),
                'feature_file': features_file,
                'signals': signals,
                'latest_price': float(df['close'].iloc[-1]),
                'price_change_24h': float(df['price_change_1d'].iloc[-1]) if 'price_change_1d' in df.columns and not pd.isna(df['price_change_1d'].iloc[-1]) else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating features for {symbol}: {e}")
            return {'error': str(e)}
    
    async def _load_historical_data(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Load historical data from database or generate demo data"""
        try:
            # Try to load from database
            if Path(self.db_path).exists():
                conn = sqlite3.connect(self.db_path)
                query = """
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(symbol, days))
                conn.close()
                
                if len(df) > 0:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    return df.sort_values('timestamp').reset_index(drop=True)
            
            # Generate demo data if no database or no data
            return self._generate_demo_data(symbol, days)
            
        except Exception as e:
            self.logger.warning(f"Error loading data for {symbol}: {e}")
            return self._generate_demo_data(symbol, days)
    
    def _generate_demo_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Generate demo OHLCV data for testing"""
        np.random.seed(hash(symbol) % 2**32)  # Consistent random data per symbol
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate realistic price movements
        base_price = 100 + (hash(symbol) % 1000)  # Base price 100-1100
        price_changes = np.random.normal(0, 0.05, days)  # 5% daily volatility
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 0.01))  # Minimum price
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices],
            'close': prices,
            'volume': [abs(np.random.normal(1000000, 200000)) for _ in range(days)]
        })
        
        # Ensure OHLC relationships
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        
        return df
    
    def _generate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate all trading features"""
        df = df.copy()
        
        # Price features
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_3d'] = df['close'].pct_change(3)
        df['price_change_7d'] = df['close'].pct_change(7)
        
        # Volatility
        df['volatility_7d'] = df['price_change_1d'].rolling(7).std()
        df['volatility_14d'] = df['price_change_1d'].rolling(14).std()
        
        # Moving averages
        df['sma_7'] = df['close'].rolling(7).mean()
        df['sma_14'] = df['close'].rolling(14).mean()
        df['sma_30'] = df['close'].rolling(30).mean()
        
        # Volume features
        df['volume_change_1d'] = df['volume'].pct_change(1)
        df['volume_ma_7d'] = df['volume'].rolling(7).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_7d']
        
        # Technical indicators (simplified)
        df['rsi_14'] = self._calculate_rsi(df['close'], 14)
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'], 20)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Market structure
        df['resistance_7d'] = df['high'].rolling(7).max()
        df['support_7d'] = df['low'].rolling(7).min()
        
        # Trend indicators
        df['trend_7d'] = np.where(df['close'] > df['sma_7'], 1, -1)
        df['trend_14d'] = np.where(df['close'] > df['sma_14'], 1, -1)
        
        # Fill NaN values
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        rolling_std = prices.rolling(period).std()
        upper = sma + (rolling_std * std)
        lower = sma - (rolling_std * std)
        return upper, lower
    
    def _generate_trading_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on features"""
        if len(df) < 2:
            return {'signal': 'HOLD', 'confidence': 0, 'reasons': []}
        
        signals = []
        reasons = []
        
        # Get latest values
        latest = df.iloc[-1]
        
        # RSI signals
        if 'rsi_14' in df.columns and not pd.isna(latest['rsi_14']):
            if latest['rsi_14'] < 30:
                signals.append(1)  # Buy signal
                reasons.append(f"RSI oversold ({latest['rsi_14']:.1f})")
            elif latest['rsi_14'] > 70:
                signals.append(-1)  # Sell signal  
                reasons.append(f"RSI overbought ({latest['rsi_14']:.1f})")
        
        # Bollinger Bands signals
        if 'bb_position' in df.columns and not pd.isna(latest['bb_position']):
            if latest['bb_position'] < 0:
                signals.append(1)
                reasons.append("Price below lower Bollinger Band")
            elif latest['bb_position'] > 1:
                signals.append(-1)
                reasons.append("Price above upper Bollinger Band")
        
        # Trend signals
        if 'trend_7d' in df.columns and 'trend_14d' in df.columns:
            if latest['trend_7d'] == 1 and latest['trend_14d'] == 1:
                signals.append(0.5)
                reasons.append("Bullish trend (both MA)")
            elif latest['trend_7d'] == -1 and latest['trend_14d'] == -1:
                signals.append(-0.5)
                reasons.append("Bearish trend (both MA)")
        
        # Volume confirmation
        if 'volume_ratio' in df.columns and not pd.isna(latest['volume_ratio']):
            if latest['volume_ratio'] > 1.5:
                reasons.append(f"High volume ({latest['volume_ratio']:.1f}x average)")
        
        # Price momentum
        if 'price_change_1d' in df.columns and not pd.isna(latest['price_change_1d']):
            if latest['price_change_1d'] > 0.05:  # 5% gain
                signals.append(0.5)
                reasons.append(f"Strong momentum (+{latest['price_change_1d']*100:.1f}%)")
            elif latest['price_change_1d'] < -0.05:  # 5% loss
                signals.append(-0.5)
                reasons.append(f"Negative momentum ({latest['price_change_1d']*100:.1f}%)")
        
        # Calculate final signal
        if not signals:
            final_signal = 'HOLD'
            confidence = 0
        else:
            avg_signal = np.mean(signals)
            if avg_signal > 0.3:
                final_signal = 'BUY'
                confidence = min(avg_signal, 1.0)
            elif avg_signal < -0.3:
                final_signal = 'SELL'
                confidence = min(abs(avg_signal), 1.0)
            else:
                final_signal = 'HOLD'
                confidence = abs(avg_signal)
        
        return {
            'signal': final_signal,
            'confidence': float(confidence),
            'reasons': reasons,
            'signal_strength': len([s for s in signals if abs(s) > 0.3]),
            'price': float(latest['close']) if 'close' in latest else 0,
            'rsi': float(latest['rsi_14']) if 'rsi_14' in latest and not pd.isna(latest['rsi_14']) else None
        }
    
    def _get_latest_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get latest values for key metrics"""
        latest = df.iloc[-1]
        return {
            'price': float(latest['close']),
            'volume': float(latest['volume']),
            'price_change_1d': float(latest['price_change_1d']) if 'price_change_1d' in latest and not pd.isna(latest['price_change_1d']) else 0,
            'rsi': float(latest['rsi_14']) if 'rsi_14' in latest and not pd.isna(latest['rsi_14']) else None,
            'volatility': float(latest['volatility_7d']) if 'volatility_7d' in latest and not pd.isna(latest['volatility_7d']) else None
        }
    
    async def generate_features_batch(self, symbols: List[str], days: int = 30) -> Dict[str, Any]:
        """Generate features for multiple coins"""
        results = {}
        
        self.logger.info(f"🔧 Generating features for {len(symbols)} coins...")
        
        for symbol in symbols:
            try:
                result = await self.generate_features_for_coin(symbol, days)
                results[symbol] = result
                await asyncio.sleep(0.1)  # Small delay
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        # Generate summary
        successful = len([r for r in results.values() if 'error' not in r])
        failed = len(results) - successful
        
        summary = {
            'total_coins': len(symbols),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(symbols) if symbols else 0,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save batch summary
        summary_file = f"data/features/batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"✅ Feature generation complete: {successful}/{len(symbols)} successful")
        
        return summary

async def main():
    """Test the feature engineer"""
    logging.basicConfig(level=logging.INFO)
    
    engineer = FeatureEngineer()
    
    # Test with demo coins
    test_coins = ['DEMO1', 'DEMO2', 'DEMO3', 'BTC', 'ETH']
    
    print("🔧 Testing Feature Engineer...")
    results = await engineer.generate_features_batch(test_coins, days=30)
    
    print(f"\n📊 Results Summary:")
    print(f"   Total coins: {results['total_coins']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Success rate: {results['success_rate']:.1%}")
    
    print(f"\n🎯 Individual Results:")
    for symbol, result in results['results'].items():
        if 'error' not in result:
            signal = result.get('signals', {})
            print(f"   {symbol}: {result['features_generated']} features, "
                  f"Signal: {signal.get('signal', 'N/A')} "
                  f"(confidence: {signal.get('confidence', 0):.2f})")
        else:
            print(f"   {symbol}: ERROR - {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
