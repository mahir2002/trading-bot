#!/usr/bin/env python3
"""
Custom Binance Testnet Client
Direct API implementation since CCXT has testnet issues
"""

import os
import requests
import hmac
import hashlib
import time
import pandas as pd
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv('config.env')

class BinanceTestnetClient:
    """Custom Binance Testnet Client using direct API calls"""
    
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY')
        self.use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if self.use_testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        self.session = requests.Session()
        
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if signed and self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
            
            # Add timestamp
            if params is None:
                params = {}
            params['timestamp'] = int(time.time() * 1000)
            
            # Create query string and signature
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self._generate_signature(query_string)
            params['signature'] = signature
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def get_server_time(self) -> Dict:
        """Get server time"""
        return self._make_request('GET', '/api/v3/time')
    
    def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        return self._make_request('GET', '/api/v3/exchangeInfo')
    
    def get_ticker_price(self, symbol: str) -> Dict:
        """Get ticker price for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/api/v3/ticker/price', params)
    
    def get_ticker_24hr(self, symbol: str) -> Dict:
        """Get 24hr ticker statistics"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/api/v3/ticker/24hr', params)
    
    def get_account_info(self) -> Dict:
        """Get account information (requires authentication)"""
        return self._make_request('GET', '/api/v3/account', signed=True)
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List:
        """Get kline/candlestick data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/api/v3/klines', params)
    
    def get_ohlcv_dataframe(self, symbol: str, interval: str = '1h', limit: int = 500) -> pd.DataFrame:
        """Get OHLCV data as pandas DataFrame"""
        klines = self.get_klines(symbol, interval, limit)
        
        if not klines:
            return pd.DataFrame()
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convert to proper types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Return only OHLCV columns
        return df[['open', 'high', 'low', 'close', 'volume']]
    
    def place_test_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> Dict:
        """Place a test order (doesn't actually execute)"""
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity,
        }
        
        if price and order_type.upper() == 'LIMIT':
            params['price'] = price
            params['timeInForce'] = 'GTC'
        
        return self._make_request('POST', '/api/v3/order/test', params, signed=True)
    
    def get_balance(self) -> Dict:
        """Get account balance in a simplified format"""
        account_info = self.get_account_info()
        
        balance = {
            'free': {},
            'used': {},
            'total': {}
        }
        
        for asset in account_info.get('balances', []):
            asset_name = asset['asset']
            free = float(asset['free'])
            locked = float(asset['locked'])
            total = free + locked
            
            if total > 0:  # Only include assets with balance
                balance['free'][asset_name] = free
                balance['used'][asset_name] = locked
                balance['total'][asset_name] = total
        
        return balance
    
    def test_connection(self) -> bool:
        """Test the connection to Binance API"""
        try:
            # Test public endpoint
            server_time = self.get_server_time()
            print(f"✅ Server time: {server_time['serverTime']}")
            
            # Test authenticated endpoint
            if self.api_key and self.secret_key:
                account_info = self.get_account_info()
                print(f"✅ Account type: {account_info.get('accountType', 'Unknown')}")
                return True
            else:
                print("⚠️  No API credentials provided")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

def main():
    """Test the Binance client"""
    print("🚀 Testing Custom Binance Testnet Client")
    print("=" * 50)
    
    client = BinanceTestnetClient()
    
    # Test connection
    if not client.test_connection():
        print("❌ Connection test failed")
        return
    
    # Test market data
    print("\n📊 Testing Market Data...")
    try:
        # Get BTC price
        btc_price = client.get_ticker_price('BTCUSDT')
        print(f"✅ BTC/USDT Price: ${float(btc_price['price']):,.2f}")
        
        # Get 24hr stats
        btc_24hr = client.get_ticker_24hr('BTCUSDT')
        print(f"✅ 24hr Change: {float(btc_24hr['priceChangePercent']):.2f}%")
        
        # Get OHLCV data
        df = client.get_ohlcv_dataframe('BTCUSDT', '1h', 10)
        print(f"✅ OHLCV Data: {len(df)} candles retrieved")
        print(f"   Latest close: ${df['close'].iloc[-1]:,.2f}")
        
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
    
    # Test account data
    print("\n💰 Testing Account Data...")
    try:
        balance = client.get_balance()
        print(f"✅ Account Balance:")
        for asset, amount in balance['total'].items():
            if amount > 0:
                print(f"   {asset}: {amount}")
        
    except Exception as e:
        print(f"❌ Account data test failed: {e}")
    
    # Test order placement (test mode)
    print("\n📝 Testing Order Placement (Test Mode)...")
    try:
        test_order = client.place_test_order('BTCUSDT', 'BUY', 'MARKET', 0.001)
        print(f"✅ Test order placed successfully")
        
    except Exception as e:
        print(f"❌ Test order failed: {e}")
    
    print("\n🎉 Custom Binance client test complete!")

if __name__ == "__main__":
    main() 