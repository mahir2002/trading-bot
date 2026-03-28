#!/usr/bin/env python3
"""
Simple script to update Telegram configuration
"""

def update_telegram_config():
    print("🤖 Update Telegram Configuration")
    print("=" * 40)
    
    # Get bot token
    print("\n🔑 Enter your bot token from BotFather:")
    print("(It should look like: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)")
    bot_token = input("Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot token is required!")
        return
    
    # Get chat ID
    print(f"\n💬 To get your chat ID:")
    print(f"1. Message your bot (send 'hello')")
    print(f"2. Visit: https://api.telegram.org/bot{bot_token}/getUpdates")
    print(f"3. Look for 'id': followed by a number")
    
    chat_id = input("\nEnter your chat ID (number): ").strip()
    
    if not chat_id:
        print("❌ Chat ID is required!")
        return
    
    # Update config file
    try:
        with open('config.env', 'r') as f:
            content = f.read()
        
        # Replace the lines
        content = content.replace(
            'TELEGRAM_BOT_TOKEN=your_telegram_bot_token',
            f'TELEGRAM_BOT_TOKEN={bot_token}'
        )
        content = content.replace(
            'TELEGRAM_CHAT_ID=your_telegram_chat_id',
            f'TELEGRAM_CHAT_ID={chat_id}'
        )
        
        with open('config.env', 'w') as f:
            f.write(content)
        
        print(f"\n✅ Config file updated successfully!")
        print(f"Bot Token: {bot_token[:20]}...")
        print(f"Chat ID: {chat_id}")
        
        print(f"\n🧪 Now run: python test_telegram_notifications.py")
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")

if __name__ == "__main__":
    update_telegram_config() 