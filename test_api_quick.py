#!/usr/bin/env python3
"""
Quick API Test
"""

from binance_testnet_client import BinanceTestnetClient

def test_api():
    print("🔗 Testing Binance API...")
    
    try:
        client = BinanceTestnetClient()
        
        # Test ticker price
        print("Getting BTC price...")
        ticker = client.get_ticker_price('BTCUSDT')
        price = float(ticker['price'])
        print(f"✅ BTC Price: ${price:,.2f}")
        
        # Test OHLCV data
        print("Getting OHLCV data...")
        df = client.get_ohlcv_dataframe('BTCUSDT', '1h', 10)
        print(f"✅ OHLCV Data: {len(df)} candles")
        
        if not df.empty:
            latest_close = df['close'].iloc[-1]
            print(f"✅ Latest close: ${latest_close:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

if __name__ == '__main__':
    test_api() 