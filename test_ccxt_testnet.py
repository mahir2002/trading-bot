#!/usr/bin/env python3
"""
Test different CCXT configurations for Binance testnet
"""

import os
import ccxt
from dotenv import load_dotenv

load_dotenv('config.env')

def test_ccxt_configurations():
    """Test different CCXT configurations"""
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    configurations = [
        {
            'name': 'Method 1: sandbox=True',
            'config': {
                'apiKey': api_key,
                'secret': secret_key,
                'sandbox': True,
                'enableRateLimit': True,
            }
        },
        {
            'name': 'Method 2: Custom URLs',
            'config': {
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            }
        },
        {
            'name': 'Method 3: Both sandbox and URLs',
            'config': {
                'apiKey': api_key,
                'secret': secret_key,
                'sandbox': True,
                'enableRateLimit': True,
                'urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    },
                    'test': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            }
        },
        {
            'name': 'Method 4: Override hostname',
            'config': {
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'hostname': 'testnet.binance.vision',
            }
        }
    ]
    
    for test_config in configurations:
        print(f"\n🧪 Testing {test_config['name']}...")
        
        try:
            exchange = ccxt.binance(test_config['config'])
            
            # Test public endpoint
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"✅ Public API: BTC/USDT = ${ticker['last']}")
            
            # Test private endpoint
            balance = exchange.fetch_balance()
            print(f"✅ Private API: Account has {len(balance['info']['balances'])} assets")
            
            print(f"🎉 {test_config['name']} WORKS!")
            return test_config['config']
            
        except Exception as e:
            print(f"❌ {test_config['name']} failed: {e}")
    
    return None

if __name__ == "__main__":
    print("🚀 CCXT Binance Testnet Configuration Test")
    print("=" * 60)
    
    working_config = test_ccxt_configurations()
    
    if working_config:
        print(f"\n✅ Found working configuration!")
        print("Use this configuration in your bot:")
        print(working_config)
    else:
        print(f"\n❌ No working configuration found")
        print("You may need to use direct API calls instead of CCXT") 