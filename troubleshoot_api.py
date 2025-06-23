#!/usr/bin/env python3
"""
🔧 Binance API Troubleshooting Tool
Diagnose and fix common API key issues
"""

import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

def analyze_api_key():
    """Analyze API key format and potential issues"""
    print("🔍 Analyzing API Key Configuration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('config.env')
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    print(f"📊 Checking API Key Format...")
    
    # Check if keys exist
    if not api_key or api_key in ['your_binance_api_key', 'your_binance_api_key_here']:
        print("❌ API Key is not set or still has placeholder value")
        return False
    
    if not secret_key or secret_key in ['your_binance_secret_key', 'your_binance_secret_key_here']:
        print("❌ Secret Key is not set or still has placeholder value")
        return False
    
    # Display key info
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-8:]}")
    print(f"✅ Secret Key found: {secret_key[:8]}...{secret_key[-8:]}")
    print(f"📏 API Key length: {len(api_key)} characters")
    print(f"📏 Secret Key length: {len(secret_key)} characters")
    
    # Check key format
    issues = []
    
    # Binance API keys should be 64 characters
    if len(api_key) != 64:
        issues.append(f"API key should be 64 characters, got {len(api_key)}")
    
    if len(secret_key) != 64:
        issues.append(f"Secret key should be 64 characters, got {len(secret_key)}")
    
    # Check for invalid characters
    if not re.match(r'^[A-Za-z0-9]+$', api_key):
        issues.append("API key contains invalid characters (should be alphanumeric only)")
    
    if not re.match(r'^[A-Za-z0-9]+$', secret_key):
        issues.append("Secret key contains invalid characters (should be alphanumeric only)")
    
    # Check for whitespace
    if api_key != api_key.strip():
        issues.append("API key has leading/trailing whitespace")
    
    if secret_key != secret_key.strip():
        issues.append("Secret key has leading/trailing whitespace")
    
    if issues:
        print("\n⚠️  Issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ API key format looks correct")
        return True

def check_binance_api_status():
    """Check if Binance API is accessible"""
    print("\n🌐 Checking Binance API Status...")
    
    try:
        # Test basic connectivity
        response = requests.get('https://api.binance.com/api/v3/ping', timeout=10)
        if response.status_code == 200:
            print("✅ Binance API is accessible")
        else:
            print(f"⚠️  Binance API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Binance API: {e}")
        return False
    
    # Test server time
    try:
        response = requests.get('https://api.binance.com/api/v3/time', timeout=10)
        if response.status_code == 200:
            server_time = response.json()['serverTime']
            print(f"✅ Server time: {datetime.fromtimestamp(server_time/1000)}")
        else:
            print("⚠️  Could not get server time")
    except Exception as e:
        print(f"⚠️  Server time error: {e}")
    
    return True

def suggest_solutions():
    """Suggest solutions for common API key issues"""
    print("\n💡 Troubleshooting Steps:")
    print("=" * 30)
    
    print("\n1. 🔑 Check Your Binance API Key Setup:")
    print("   • Go to https://www.binance.com/en/my/settings/api-management")
    print("   • Make sure your API key is:")
    print("     ✓ Created and active")
    print("     ✓ Has 'Enable Reading' permission")
    print("     ✓ Has 'Enable Spot & Margin Trading' permission")
    print("     ✓ Does NOT have IP restrictions (unless needed)")
    
    print("\n2. 🔐 Verify API Key Format:")
    print("   • API keys should be exactly 64 characters")
    print("   • Only alphanumeric characters (A-Z, a-z, 0-9)")
    print("   • No spaces, dashes, or special characters")
    
    print("\n3. 📋 Copy/Paste Carefully:")
    print("   • Copy the ENTIRE key (all 64 characters)")
    print("   • Don't include extra spaces")
    print("   • Make sure you copy the right key (API key vs Secret key)")
    
    print("\n4. 🌍 Check IP Restrictions:")
    print("   • If you enabled IP restrictions on Binance:")
    print("   • Add your current IP address to the whitelist")
    print("   • Or disable IP restrictions for testing")
    
    print("\n5. ⏰ Wait for Activation:")
    print("   • New API keys might take a few minutes to activate")
    print("   • Try again in 5-10 minutes")
    
    print("\n6. 🔄 Create New API Keys:")
    print("   • If nothing works, delete old keys and create new ones")
    print("   • Make sure to save both API key AND secret key")

def interactive_key_checker():
    """Interactive key validation"""
    print("\n🔧 Interactive Key Validation")
    print("=" * 35)
    
    print("Let's check your keys step by step...")
    
    # Get current keys
    load_dotenv('config.env')
    current_api = os.getenv('BINANCE_API_KEY', '')
    current_secret = os.getenv('BINANCE_SECRET_KEY', '')
    
    print(f"\nCurrent API Key: {current_api[:8]}...{current_api[-8:] if len(current_api) > 16 else ''}")
    print(f"Current Secret: {current_secret[:8]}...{current_secret[-8:] if len(current_secret) > 16 else ''}")
    
    # Ask user to verify
    print("\n❓ Do these look correct? (y/n): ", end="")
    response = input().lower().strip()
    
    if response != 'y':
        print("\n🔄 Would you like to re-enter your API keys? (y/n): ", end="")
        reenter = input().lower().strip()
        
        if reenter == 'y':
            print("\n📝 Please re-enter your keys carefully:")
            print("   (Make sure to copy the full 64-character keys)")
            return True
    
    return False

def main():
    """Main troubleshooting function"""
    print("🔧 Binance API Troubleshooting Tool")
    print("=" * 40)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Analyze current configuration
    if not analyze_api_key():
        suggest_solutions()
        if interactive_key_checker():
            print("\n🔄 Please run: python update_binance_keys.py")
        return False
    
    # Step 2: Check Binance API connectivity
    if not check_binance_api_status():
        print("\n❌ Binance API connectivity issues detected")
        return False
    
    # Step 3: If keys look good but still failing
    print("\n🤔 Your API keys look correct, but authentication is still failing.")
    print("This usually means:")
    print("1. IP restrictions are enabled on your Binance account")
    print("2. The API key is not fully activated yet")
    print("3. Required permissions are not enabled")
    
    suggest_solutions()
    
    return False

if __name__ == "__main__":
    main() 