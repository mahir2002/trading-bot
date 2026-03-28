#!/usr/bin/env python3
"""
Simple Telegram Info Helper
Get your bot token and chat ID easily
"""

import requests
import json

def get_chat_id(bot_token):
    """Get chat ID from bot token"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url)
        data = response.json()
        
        print(f"API Response: {json.dumps(data, indent=2)}")
        
        if data['ok'] and data['result']:
            for update in data['result']:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    username = update['message']['chat'].get('username', 'No username')
                    first_name = update['message']['chat'].get('first_name', 'No name')
                    print(f"\n✅ Found Chat ID: {chat_id}")
                    print(f"   Username: @{username}")
                    print(f"   Name: {first_name}")
                    return str(chat_id)
        else:
            print("❌ No messages found. Please message your bot first!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_bot_token(bot_token):
    """Test if bot token is valid"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url)
        data = response.json()
        
        if data['ok']:
            bot_info = data['result']
            print(f"✅ Bot Token Valid!")
            print(f"   Bot Name: {bot_info['first_name']}")
            print(f"   Bot Username: @{bot_info['username']}")
            return True
        else:
            print(f"❌ Invalid bot token: {data.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def main():
    print("🤖 Telegram Bot Info Helper")
    print("=" * 40)
    
    print("\n📋 Steps to follow:")
    print("1. Message @BotFather on Telegram")
    print("2. Send: /newbot")
    print("3. Create your bot and get the token")
    print("4. Message your new bot (send 'hello')")
    print("5. Enter your bot token below")
    
    # Get bot token
    bot_token = input("\n🔑 Enter your bot token: ").strip()
    
    if not bot_token:
        print("❌ Bot token is required!")
        return
    
    # Test bot token
    print(f"\n🧪 Testing bot token...")
    if not test_bot_token(bot_token):
        return
    
    # Get chat ID
    print(f"\n🔍 Looking for your chat ID...")
    print("(Make sure you've sent a message to your bot first)")
    
    chat_id = get_chat_id(bot_token)
    
    if chat_id:
        print(f"\n🎉 Success! Here are your credentials:")
        print(f"Bot Token: {bot_token}")
        print(f"Chat ID: {chat_id}")
        
        print(f"\n📝 Add these to your config.env file:")
        print(f"TELEGRAM_BOT_TOKEN={bot_token}")
        print(f"TELEGRAM_CHAT_ID={chat_id}")
        
        # Update config file
        try:
            with open('config.env', 'r') as f:
                content = f.read()
            
            content = content.replace('TELEGRAM_BOT_TOKEN=your_telegram_bot_token', f'TELEGRAM_BOT_TOKEN={bot_token}')
            content = content.replace('TELEGRAM_CHAT_ID=your_telegram_chat_id', f'TELEGRAM_CHAT_ID={chat_id}')
            
            with open('config.env', 'w') as f:
                f.write(content)
            
            print(f"\n✅ Config file updated automatically!")
            print(f"Now run: python test_telegram_notifications.py")
            
        except Exception as e:
            print(f"\n⚠️  Could not update config file: {e}")
            print("Please update it manually.")
    else:
        print(f"\n❌ Could not find chat ID.")
        print("Make sure you:")
        print("1. Messaged your bot first")
        print("2. Used the correct bot token")

if __name__ == "__main__":
    main() 