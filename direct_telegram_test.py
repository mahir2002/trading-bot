#!/usr/bin/env python3
"""
Direct Telegram Test
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError

async def test_telegram():
    print("🤖 Direct Telegram Test")
    print("=" * 30)
    
    # Use the values directly
    bot_token = "7908950533:AAExifV6woXkFyaaDPAYoIUquCPjsZrhlJU"
    chat_id = "6479040221"
    
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"Chat ID: {chat_id}")
    
    try:
        # Create bot instance
        bot = Bot(token=bot_token)
        
        # Test message
        test_message = """
🤖 AI Trading Bot - Telegram Test

✅ Connection successful!
🎉 Your Telegram notifications are working!

This is a test message from your AI Trading Bot.
        """
        
        print("\n📤 Sending test message...")
        await bot.send_message(chat_id=chat_id, text=test_message)
        print("✅ Test message sent successfully!")
        
        # Send a trading notification example
        trade_message = """
🚨 TRADE ALERT 🚨

📊 Symbol: BTC/USDT
📈 Action: BUY
💰 Amount: 0.001 BTC
💵 Price: $109,911.02
🎯 Confidence: 85%
⏰ Time: Now

🤖 AI Trading Bot
        """
        
        print("\n📤 Sending trade alert example...")
        await bot.send_message(chat_id=chat_id, text=trade_message)
        print("✅ Trade alert sent successfully!")
        
        print("\n🎉 Telegram setup complete!")
        print("Your trading bot will now send notifications to Telegram.")
        
        return True
        
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_telegram()) 