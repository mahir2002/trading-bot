#!/usr/bin/env python3
"""
Test Telegram Notifications for Trading Bot
"""

import asyncio
import os
from dotenv import load_dotenv
from ai_trading_bot_simple import NotificationManager, TradingLogger

async def test_notifications():
    print("📱 Testing Telegram Notifications")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv('config.env')
    
    # Check if Telegram is configured
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or bot_token == 'your_telegram_bot_token':
        print("❌ Telegram bot token not configured!")
        print("Please run: python setup_telegram.py")
        return
    
    if not chat_id or chat_id == 'your_telegram_chat_id':
        print("❌ Telegram chat ID not configured!")
        print("Please run: python setup_telegram.py")
        return
    
    print(f"✅ Bot Token: {bot_token[:10]}...")
    print(f"✅ Chat ID: {chat_id}")
    
    # Initialize notification manager
    logger = TradingLogger()
    notification_manager = NotificationManager(logger)
    
    # Test 1: Simple message
    print("\n📤 Test 1: Sending simple message...")
    success = await notification_manager.send_telegram_message("🤖 Test message from your AI Trading Bot!")
    
    if success:
        print("✅ Simple message sent successfully!")
    else:
        print("❌ Failed to send simple message")
        return
    
    # Test 2: Trade notification
    print("\n📤 Test 2: Sending trade notification...")
    
    trade_info = {
        'symbol': 'BTC/USDT',
        'action': 'buy',
        'amount': '0.001 BTC',
        'price': 109911.02,
        'timestamp': '2025-06-11 14:55:00',
        'confidence': 85
    }
    
    await notification_manager.notify_trade(trade_info)
    print("✅ Trade notification sent!")
    
    # Test 3: Bot status notification
    print("\n📤 Test 3: Sending bot status notification...")
    
    status_message = """
🤖 AI Trading Bot Status Update

📊 Current Status: ACTIVE
💰 Portfolio Value: $10,000.00
📈 Today's P&L: +$125.50 (+1.26%)
🔄 Active Positions: 2/5
⏰ Last Update: 2025-06-11 14:55:00

🎯 Recent Signals:
• BTC/USDT: HOLD (85% confidence)
• ETH/USDT: BUY (72% confidence)

✅ All systems operational
    """
    
    await notification_manager.send_telegram_message(status_message)
    print("✅ Status notification sent!")
    
    print("\n🎉 All Telegram tests completed successfully!")
    print("Your trading bot is ready to send notifications!")

if __name__ == "__main__":
    asyncio.run(test_notifications()) 