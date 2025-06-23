#!/usr/bin/env python3
"""
Telegram Bot Setup Helper
Helps you configure and test Telegram notifications for your trading bot
"""

import os
import asyncio
import requests
from dotenv import load_dotenv

def update_config_file(bot_token, chat_id):
    """Update config.env file with Telegram credentials"""
    
    # Read current config
    with open('config.env', 'r') as f:
        content = f.read()
    
    # Replace Telegram settings
    content = content.replace('TELEGRAM_BOT_TOKEN=your_telegram_bot_token', f'TELEGRAM_BOT_TOKEN={bot_token}')
    content = content.replace('TELEGRAM_CHAT_ID=your_telegram_chat_id', f'TELEGRAM_CHAT_ID={chat_id}')
    
    # Write updated config
    with open('config.env', 'w') as f:
        f.write(content)
    
    print("✅ Config file updated successfully!")

def get_chat_id_from_token(bot_token):
    """Get chat ID from bot token by checking recent messages"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url)
        data = response.json()
        
        if data['ok'] and data['result']:
            # Get the most recent message
            latest_message = data['result'][-1]
            chat_id = latest_message['message']['chat']['id']
            return str(chat_id)
        else:
            return None
    except Exception as e:
        print(f"Error getting chat ID: {e}")
        return None

async def test_telegram_notification(bot_token, chat_id):
    """Test sending a Telegram notification"""
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        
        bot = Bot(token=bot_token)
        
        test_message = """
🤖 AI Trading Bot - Test Notification

✅ Telegram integration successful!
📊 Your bot is ready to send trading alerts
🚀 Setup complete!

This is a test message to confirm your Telegram notifications are working.
        """
        
        await bot.send_message(chat_id=chat_id, text=test_message)
        print("✅ Test notification sent successfully!")
        return True
        
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🤖 Telegram Bot Setup for AI Trading Bot")
    print("=" * 50)
    
    print("\n📋 Instructions:")
    print("1. Message @BotFather on Telegram")
    print("2. Send: /newbot")
    print("3. Follow the prompts to create your bot")
    print("4. Copy the bot token")
    print("5. Message your new bot (send any message)")
    print("6. Enter the details below")
    
    # Get bot token
    print("\n🔑 Enter your bot token:")
    bot_token = input("Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot token is required!")
        return
    
    # Try to get chat ID automatically
    print("\n🔍 Trying to get your chat ID automatically...")
    chat_id = get_chat_id_from_token(bot_token)
    
    if chat_id:
        print(f"✅ Found chat ID: {chat_id}")
    else:
        print("⚠️  Could not get chat ID automatically.")
        print("Please message your bot first, then enter your chat ID manually:")
        chat_id = input("Chat ID: ").strip()
    
    if not chat_id:
        print("❌ Chat ID is required!")
        return
    
    # Update config file
    print("\n📝 Updating configuration...")
    update_config_file(bot_token, chat_id)
    
    # Test notification
    print("\n📱 Testing notification...")
    try:
        success = asyncio.run(test_telegram_notification(bot_token, chat_id))
        if success:
            print("\n🎉 Telegram setup complete!")
            print("Your trading bot will now send notifications to Telegram.")
        else:
            print("\n❌ Test notification failed. Please check your token and chat ID.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Your configuration has been saved, but please test manually.")

if __name__ == "__main__":
    main() 