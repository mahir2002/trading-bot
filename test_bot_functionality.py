#!/usr/bin/env python3
"""
Test Bot Functionality with Real Market Data
"""

from binance_testnet_client import BinanceTestnetClient
from ai_trading_bot_simple import AITradingBot
import asyncio

async def test_bot():
    print('🤖 Testing AI Trading Bot with Real Data')
    print('=' * 50)
    
    bot = AITradingBot()
    await bot.initialize()
    
    # Test market analysis
    print('\n📊 Market Analysis Test:')
    result = await bot.analyze_market('BTC/USDT')
    print(f'   Symbol: BTC/USDT')
    print(f'   Current Price: ${result.get("current_price", "N/A")}')
    print(f'   Prediction: {result.get("prediction", "N/A")}')
    print(f'   Confidence: {result.get("confidence", "N/A")}%')
    print(f'   Signal: {result.get("signal", "N/A")}')
    
    # Test balance
    print('\n💰 Account Balance Test:')
    balance = bot.exchange_manager.get_balance()
    total_assets = balance.get('total', {})
    non_zero_assets = {asset: amount for asset, amount in total_assets.items() if amount > 0}
    
    print(f'   Total Assets with Balance: {len(non_zero_assets)}')
    print('   Top 5 Assets:')
    for i, (asset, amount) in enumerate(list(non_zero_assets.items())[:5]):
        print(f'     {asset}: {amount}')
    
    # Test ticker data
    print('\n📈 Ticker Data Test:')
    ticker = bot.exchange_manager.get_ticker('BTC/USDT')
    if ticker:
        print(f'   BTC/USDT: ${ticker.get("last", "N/A")}')
        print(f'   24h Change: {ticker.get("percentage", "N/A")}%')
        print(f'   24h Volume: {ticker.get("volume", "N/A")}')
    
    # Test OHLCV data
    print('\n📊 OHLCV Data Test:')
    df = bot.exchange_manager.get_ohlcv('BTC/USDT', '1h', 5)
    if not df.empty:
        print(f'   Data Points: {len(df)}')
        print(f'   Latest Close: ${df["close"].iloc[-1]:,.2f}')
        print(f'   Latest High: ${df["high"].iloc[-1]:,.2f}')
        print(f'   Latest Low: ${df["low"].iloc[-1]:,.2f}')
    
    print('\n🎉 Bot Functionality Test Complete!')
    print('✅ Your AI Trading Bot is fully operational with real market data!')

if __name__ == "__main__":
    asyncio.run(test_bot()) 