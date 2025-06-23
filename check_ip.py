#!/usr/bin/env python3
"""
🌐 Check Your Current IP Address
For Binance API IP whitelist configuration
"""

import requests

def get_public_ip():
    """Get your public IP address"""
    print("🌐 Checking Your Public IP Address")
    print("=" * 40)
    
    services = [
        ('ipify.org', 'https://api.ipify.org'),
        ('httpbin.org', 'https://httpbin.org/ip'),
        ('icanhazip.com', 'https://icanhazip.com'),
    ]
    
    for service_name, url in services:
        try:
            print(f"📡 Trying {service_name}...")
            response = requests.get(url, timeout=10)
            
            if service_name == 'ipify.org':
                ip = response.text.strip()
            elif service_name == 'httpbin.org':
                ip = response.json()['origin']
            else:  # icanhazip.com
                ip = response.text.strip()
            
            print(f"✅ Your public IP: {ip}")
            print(f"\n📋 To whitelist this IP on Binance:")
            print(f"   1. Go to: https://www.binance.com/en/my/settings/api-management")
            print(f"   2. Edit your API key")
            print(f"   3. Add this IP to 'Restrict access to trusted IPs only'")
            print(f"   4. IP to add: {ip}")
            
            return ip
            
        except Exception as e:
            print(f"❌ {service_name} failed: {e}")
            continue
    
    print("❌ Could not determine your IP address")
    return None

if __name__ == "__main__":
    get_public_ip() 