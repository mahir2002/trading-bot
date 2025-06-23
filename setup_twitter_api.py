#!/usr/bin/env python3
"""
🐦 Twitter API Setup and Configuration Helper
Helps users set up Twitter API credentials and test connectivity
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv, set_key
import tweepy

def print_header():
    """Print setup header"""
    print("""
🐦 TWITTER API SETUP HELPER
===========================

This script will help you configure Twitter API credentials
for the cryptocurrency news analysis system.

📋 What you'll need:
   1. Twitter Developer Account
   2. Twitter API v2 Bearer Token
   3. Twitter API Keys and Tokens

🔗 Get your credentials at: https://developer.twitter.com/
    """)

def check_existing_config():
    """Check if Twitter API is already configured"""
    load_dotenv('config.env')
    
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    api_key = os.getenv('TWITTER_API_KEY')
    
    if bearer_token and bearer_token != 'your_twitter_bearer_token_here':
        print("✅ Twitter API credentials found in config.env")
        return True
    
    print("⚠️ Twitter API credentials not configured")
    return False

def get_twitter_credentials():
    """Get Twitter API credentials from user"""
    print("\n📝 Please enter your Twitter API credentials:")
    print("(You can find these in your Twitter Developer Dashboard)")
    
    credentials = {}
    
    # Bearer Token (required for API v2)
    print("\n1. Bearer Token (Required for Twitter API v2):")
    bearer_token = input("   Enter your Bearer Token: ").strip()
    if not bearer_token:
        print("❌ Bearer Token is required!")
        return None
    credentials['TWITTER_BEARER_TOKEN'] = bearer_token
    
    # API Key and Secret
    print("\n2. API Key and Secret (Optional, for advanced features):")
    api_key = input("   Enter your API Key (or press Enter to skip): ").strip()
    api_secret = input("   Enter your API Secret (or press Enter to skip): ").strip()
    
    if api_key and api_secret:
        credentials['TWITTER_API_KEY'] = api_key
        credentials['TWITTER_API_SECRET'] = api_secret
        
        # Access Token and Secret
        print("\n3. Access Token and Secret (Optional):")
        access_token = input("   Enter your Access Token (or press Enter to skip): ").strip()
        access_token_secret = input("   Enter your Access Token Secret (or press Enter to skip): ").strip()
        
        if access_token and access_token_secret:
            credentials['TWITTER_ACCESS_TOKEN'] = access_token
            credentials['TWITTER_ACCESS_TOKEN_SECRET'] = access_token_secret
    
    return credentials

def test_twitter_connection(credentials):
    """Test Twitter API connection"""
    print("\n🔍 Testing Twitter API connection...")
    
    try:
        # Test with Bearer Token only (API v2)
        bearer_token = credentials.get('TWITTER_BEARER_TOKEN')
        
        if not bearer_token:
            print("❌ No Bearer Token provided")
            return False
        
        # Initialize Twitter client
        client = tweepy.Client(bearer_token=bearer_token)
        
        # Test API call - search for recent tweets about Bitcoin
        tweets = client.search_recent_tweets(
            query="bitcoin OR btc -is:retweet",
            max_results=10,
            tweet_fields=['created_at', 'public_metrics']
        )
        
        if tweets.data:
            print(f"✅ Twitter API connection successful!")
            print(f"   Retrieved {len(tweets.data)} test tweets")
            
            # Show sample tweet
            sample_tweet = tweets.data[0]
            print(f"   Sample tweet: \"{sample_tweet.text[:100]}...\"")
            
            return True
        else:
            print("⚠️ API connection successful but no tweets returned")
            return True
            
    except tweepy.Unauthorized:
        print("❌ Twitter API authentication failed!")
        print("   Please check your Bearer Token")
        return False
    except tweepy.TooManyRequests:
        print("⚠️ Twitter API rate limit exceeded")
        print("   Connection is working but you've hit the rate limit")
        return True
    except Exception as e:
        print(f"❌ Twitter API connection failed: {e}")
        return False

def save_credentials_to_config(credentials):
    """Save credentials to config.env file"""
    print("\n💾 Saving credentials to config.env...")
    
    config_file = 'config.env'
    
    try:
        # Ensure config file exists
        if not os.path.exists(config_file):
            print(f"⚠️ {config_file} not found, creating new file...")
            with open(config_file, 'w') as f:
                f.write("# Twitter API Configuration\n")
        
        # Save each credential
        for key, value in credentials.items():
            set_key(config_file, key, value)
            print(f"   ✅ Saved {key}")
        
        print(f"✅ All credentials saved to {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def setup_twitter_analysis_config():
    """Setup Twitter analysis configuration"""
    print("\n⚙️ Configuring Twitter analysis settings...")
    
    config_file = 'config.env'
    
    # Default settings
    settings = {
        'SENTIMENT_THRESHOLD': '0.3',
        'TWEET_LIMIT': '100',
        'ANALYSIS_INTERVAL': '300',
        'MIN_ENGAGEMENT_SCORE': '50',
        'ENABLE_NEW_COIN_DETECTION': 'true',
        'ENABLE_MEMECOIN_DETECTION': 'true',
        'TWITTER_SENTIMENT_WEIGHT': '0.3',
        'AI_CONFIDENCE_WEIGHT': '0.7',
        'MIN_COMBINED_CONFIDENCE': '75',
        'ENABLE_TWITTER_TRADING': 'false'  # Start with paper trading
    }
    
    try:
        for key, value in settings.items():
            set_key(config_file, key, value)
        
        print("✅ Twitter analysis settings configured")
        print("\n📋 Default settings applied:")
        print("   • Tweet analysis limit: 100 tweets")
        print("   • Analysis interval: 5 minutes")
        print("   • Sentiment threshold: 0.3")
        print("   • Twitter trading: DISABLED (paper trading mode)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring settings: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing required dependencies...")
    
    try:
        import subprocess
        
        # Required packages for Twitter analysis
        packages = [
            'tweepy==4.14.0',
            'textblob==0.17.1',
            'nltk==3.8.1',
            'vaderSentiment==3.3.2'
        ]
        
        for package in packages:
            print(f"   Installing {package}...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {package} installed successfully")
            else:
                print(f"   ⚠️ {package} installation warning: {result.stderr}")
        
        # Download NLTK data
        print("   Downloading NLTK data...")
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        
        print("✅ All dependencies installed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def show_next_steps():
    """Show next steps after setup"""
    print("""
🎉 TWITTER API SETUP COMPLETE!

🚀 Next Steps:

1. 📊 Test the Twitter Analysis:
   python twitter_crypto_analyzer.py

2. 🖥️ Launch the Twitter Dashboard:
   python twitter_dashboard.py

3. 🤖 Run the Integrated Trading Bot:
   python integrated_twitter_trading_bot.py

4. ⚙️ Configuration Tips:
   • Edit config.env to adjust analysis settings
   • Set ENABLE_TWITTER_TRADING=true for live trading
   • Configure Telegram for notifications

5. 📚 Documentation:
   • Check the generated log files for detailed analysis
   • Monitor twitter_analysis_*.json files for results

⚠️ Important Notes:
   • Start with paper trading (ENABLE_TWITTER_TRADING=false)
   • Monitor API rate limits
   • Twitter API has usage quotas - check your developer dashboard

🔗 Useful Links:
   • Twitter Developer Portal: https://developer.twitter.com/
   • API Documentation: https://developer.twitter.com/en/docs/twitter-api
   • Rate Limits: https://developer.twitter.com/en/docs/twitter-api/rate-limits

Happy Trading! 🚀📈
    """)

def main():
    """Main setup function"""
    print_header()
    
    # Check if already configured
    if check_existing_config():
        response = input("\nTwitter API is already configured. Reconfigure? (y/N): ").strip().lower()
        if response != 'y':
            print("✅ Using existing configuration")
            show_next_steps()
            return
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Please install manually.")
        return
    
    # Get credentials from user
    credentials = get_twitter_credentials()
    if not credentials:
        print("❌ Setup cancelled - no credentials provided")
        return
    
    # Test connection
    if not test_twitter_connection(credentials):
        response = input("\n⚠️ API test failed. Save credentials anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Setup cancelled")
            return
    
    # Save credentials
    if not save_credentials_to_config(credentials):
        print("❌ Failed to save credentials")
        return
    
    # Setup analysis configuration
    if not setup_twitter_analysis_config():
        print("❌ Failed to configure analysis settings")
        return
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main() 