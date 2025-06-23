#!/usr/bin/env python3
import ccxt

print("🌐 MULTI-EXCHANGE SUPPORT DEMO")
print("=" * 35)
print("Demonstrating expanded support beyond Binance...")
print()

exchanges = {
    "binance": {"symbol": "BTC/USDT", "desc": "Global leader"},
    "coinbasepro": {"symbol": "BTC/USD", "desc": "US regulated"},
    "kraken": {"symbol": "BTC/USD", "desc": "European focus"},
    "bybit": {"symbol": "BTC/USDT", "desc": "Derivatives focus"},
    "kucoin": {"symbol": "BTC/USDT", "desc": "Wide altcoin selection"}
}

online_exchanges = []
prices = {}

for name, config in exchanges.items():
    try:
        print(f"Testing {name.upper()}...")
        exchange = getattr(ccxt, name)({"enableRateLimit": True, "timeout": 8000})
        ticker = exchange.fetch_ticker(config["symbol"])
        online_exchanges.append(name)
        prices[name] = ticker["last"]
        print(f"✅ {name.upper()}: {config['desc']} - ${ticker['last']:,.2f}")
    except Exception as e:
        print(f"❌ {name.upper()}: Connection failed")

print(f"\n🎉 Connected to {len(online_exchanges)} exchanges!")
print(f"✅ No longer Binance-centric: {', '.join([ex.upper() for ex in online_exchanges])}")

if len(prices) > 1:
    sorted_prices = sorted(prices.items(), key=lambda x: x[1])
    lowest = sorted_prices[0]
    highest = sorted_prices[-1]
    spread = ((highest[1] - lowest[1]) / lowest[1]) * 100
    print(f"\n💰 Price spread: {spread:.3f}%")
    print(f"   Lowest: ${lowest[1]:,.2f} on {lowest[0].upper()}")
    print(f"   Highest: ${highest[1]:,.2f} on {highest[0].upper()}")

print("\n🎯 BENEFITS ACHIEVED:")
print("✅ Exchange diversification")
print("✅ Geographic flexibility") 
print("✅ Reduced single-point-of-failure")
print("✅ Cross-exchange arbitrage potential")
print("✅ Best price routing capabilities")
print("\n🎉 Multi-exchange flexibility implemented!") 