#!/usr/bin/env python3
"""
AI Trading Bot API Example
This script demonstrates how to use the trading bot API
"""

import time
import json
from api_client import TradingBotAPIClient

def main():
    """
    Example usage of the Trading Bot API
    """
    print("🤖 AI Trading Bot API Example")
    print("=" * 50)
    
    # Initialize API client
    client = TradingBotAPIClient('http://localhost:5000')
    
    try:
        # 1. Health Check
        print("\n1. 🏥 Health Check")
        health = client.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Bot Running: {health.get('bot_running')}")
        
        # 2. API Documentation
        print("\n2. 📚 API Documentation")
        docs = client.get_api_docs()
        print(f"   Title: {docs.get('title')}")
        print(f"   Version: {docs.get('version')}")
        print(f"   Available Endpoints: {len(docs.get('endpoints', {}))}")
        
        # 3. User Registration (optional - comment out if user exists)
        print("\n3. 👤 User Registration")
        try:
            register_response = client.register('testuser', 'testpassword123')
            print(f"   Registration: {register_response.get('message')}")
            print(f"   API Key: {register_response.get('api_key', 'N/A')[:20]}...")
        except Exception as e:
            print(f"   Registration failed (user may already exist): {e}")
        
        # 4. Login
        print("\n4. 🔐 Login")
        try:
            # Try with test user first, then fall back to admin
            login_response = client.login('testuser', 'testpassword123')
            print(f"   Login successful for testuser")
        except:
            try:
                login_response = client.login('admin', 'admin123')
                print(f"   Login successful for admin")
            except Exception as e:
                print(f"   Login failed: {e}")
                return
        
        print(f"   Token received: {login_response.get('token', 'N/A')[:20]}...")
        
        # 5. Bot Status
        print("\n5. 🤖 Bot Status")
        status = client.get_bot_status()
        print(f"   Running: {status.get('running')}")
        print(f"   Total Trades: {status.get('total_trades', 0)}")
        print(f"   Current Balance: ${status.get('current_balance', 0)}")
        print(f"   P&L: ${status.get('profit_loss', 0)}")
        
        # 6. Trading Statistics
        print("\n6. 📊 Trading Statistics")
        stats = client.get_trade_stats()
        print(f"   Total Trades: {stats.get('total_trades', 0)}")
        print(f"   Win Rate: {stats.get('win_rate', 0)}%")
        print(f"   Total P&L: ${stats.get('total_profit_loss', 0)}")
        
        # 7. Market Data (if bot is initialized)
        print("\n7. 💹 Market Data")
        try:
            price = client.get_current_price('BTC/USDT')
            print(f"   BTC/USDT Price: ${price.get('price', 'N/A')}")
            print(f"   Volume: {price.get('volume', 'N/A')}")
        except Exception as e:
            print(f"   Market data unavailable: {e}")
        
        # 8. Technical Indicators (if bot is initialized)
        print("\n8. 📈 Technical Indicators")
        try:
            indicators = client.get_technical_indicators('BTC/USDT')
            indicator_data = indicators.get('indicators', {})
            if indicator_data:
                print(f"   RSI: {indicator_data.get('rsi', 'N/A')}")
                print(f"   MACD: {indicator_data.get('macd', 'N/A')}")
                print(f"   SMA_20: {indicator_data.get('sma_20', 'N/A')}")
            else:
                print("   No indicators available")
        except Exception as e:
            print(f"   Indicators unavailable: {e}")
        
        # 9. Portfolio Balance (if bot is initialized)
        print("\n9. 💰 Portfolio Balance")
        try:
            balance = client.get_portfolio_balance()
            balance_data = balance.get('balance', {})
            if balance_data:
                for currency, amounts in balance_data.items():
                    if amounts.get('total', 0) > 0:
                        print(f"   {currency}: {amounts.get('total', 0)}")
            else:
                print("   No balance data available")
        except Exception as e:
            print(f"   Balance unavailable: {e}")
        
        # 10. Recent Trades
        print("\n10. 📋 Recent Trades")
        trades = client.get_trades(limit=5)
        trade_list = trades.get('trades', [])
        if trade_list:
            for i, trade in enumerate(trade_list[:3], 1):
                print(f"   Trade {i}: {trade.get('symbol', 'N/A')} - "
                      f"{trade.get('side', 'N/A')} - "
                      f"P&L: ${trade.get('profit_loss', 0)}")
        else:
            print("   No trades found")
        
        # 11. Configuration
        print("\n11. ⚙️  Configuration")
        try:
            config = client.get_config()
            config_data = config.get('config', {})
            if config_data:
                print(f"   Trading Mode: {config_data.get('trading_mode', 'N/A')}")
                print(f"   Symbols: {config_data.get('symbols', 'N/A')}")
            else:
                print("   No configuration available")
        except Exception as e:
            print(f"   Configuration unavailable: {e}")
        
        # 12. Logs
        print("\n12. 📝 Recent Logs")
        try:
            logs = client.get_logs(log_type='main', lines=3)
            log_lines = logs.get('logs', [])
            if log_lines:
                for log_line in log_lines[-3:]:
                    print(f"   {log_line}")
            else:
                print("   No logs available")
        except Exception as e:
            print(f"   Logs unavailable: {e}")
        
        # 13. Bot Control Example (commented out for safety)
        print("\n13. 🎮 Bot Control (Demo)")
        print("   Bot control commands available:")
        print("   - client.start_bot({'trading_mode': 'paper'})")
        print("   - client.stop_bot()")
        print("   - client.restart_bot()")
        print("   (Commands not executed in demo mode)")
        
        # 14. Performance Analysis
        print("\n14. 📊 Performance Analysis")
        try:
            performance = client.get_symbol_performance('BTC/USDT', days=7)
            print(f"   Symbol: {performance.get('symbol')}")
            print(f"   Total Trades (7d): {performance.get('total_trades', 0)}")
            print(f"   Win Rate (7d): {performance.get('win_rate', 0)}%")
            print(f"   P&L (7d): ${performance.get('profit_loss', 0)}")
        except Exception as e:
            print(f"   Performance analysis unavailable: {e}")
        
        print("\n" + "=" * 50)
        print("✅ API Example completed successfully!")
        print("\n💡 Tips:")
        print("   - Start the API server with: python api_server.py")
        print("   - Use the API client in your own scripts")
        print("   - Check /api/docs for full documentation")
        print("   - Monitor logs for debugging")
        
    except Exception as e:
        print(f"\n❌ Error during API example: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure the API server is running")
        print("   2. Check your credentials")
        print("   3. Verify network connectivity")
        print("   4. Check the logs for more details")

if __name__ == '__main__':
    main() 