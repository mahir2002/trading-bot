#!/usr/bin/env python3
"""
Security Integration Utils
Easy-to-use security wrappers for all external API calls
"""

import asyncio
import logging
import requests
from typing import Dict, Any, Optional, Union
from secure_api_validator import SecureAPIValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityIntegrationUtils:
    """Comprehensive security wrappers for all external API interactions"""
    
    def __init__(self):
        self.validator = SecureAPIValidator()
        self.http_session = requests.Session()
        
    # ========================================
    # EXCHANGE API SECURITY WRAPPERS
    # ========================================
    
    async def secure_exchange_call(self, exchange, method_name: str, *args, **kwargs):
        """
        Universal secure wrapper for any exchange method call
        
        Usage:
            # Instead of: ticker = exchange.fetch_ticker('BTC/USDT')
            # Use: ticker = await security_utils.secure_exchange_call(exchange, 'fetch_ticker', 'BTC/USDT')
        """
        try:
            # Validate input parameters if they contain trading data
            if method_name in ['fetch_ticker', 'fetch_ohlcv', 'fetch_balance', 'create_order', 'cancel_order']:
                await self._validate_exchange_inputs(method_name, args, kwargs)
            
            # Make the actual exchange call
            method = getattr(exchange, method_name)
            response = method(*args, **kwargs)
            
            # Validate response if it's a dictionary (API response)
            if isinstance(response, dict):
                result = await self.validator.validate_exchange_response(response)
                
                if not result.is_valid:
                    logger.warning(f"Exchange response validation failed for {method_name}: {result.errors}")
                    return result.sanitized_data
                
                return result.sanitized_data
            
            return response
            
        except Exception as e:
            logger.error(f"Secure exchange call failed for {method_name}: {e}")
            raise
    
    async def _validate_exchange_inputs(self, method_name: str, args: tuple, kwargs: dict):
        """Validate exchange method inputs"""
        if method_name == 'fetch_ticker' and args:
            # For ticker requests, we only need to validate the symbol
            symbol = args[0].replace('/', '')
            if not symbol or len(symbol) < 3 or len(symbol) > 20:
                raise ValueError(f"Invalid symbol format: {symbol}")
            # Basic symbol format validation
            if not symbol.isalnum():
                raise ValueError(f"Symbol contains invalid characters: {symbol}")
        
        elif method_name == 'create_order' and len(args) >= 4:
            order_data = {
                "symbol": args[0].replace('/', ''),
                "order_type": args[1],
                "side": args[2],
                "quantity": args[3],
                "price": args[4] if len(args) > 4 else kwargs.get('price')
            }
            result = await self.validator.validate_exchange_request(order_data, "order")
            if not result.is_valid:
                raise ValueError(f"Invalid order data: {result.errors}")
    
    # ========================================
    # HTTP REQUESTS SECURITY WRAPPERS
    # ========================================
    
    async def secure_http_get(self, url: str, params: Optional[Dict] = None, 
                             timeout: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Secure HTTP GET request with response validation
        
        Usage:
            # Instead of: response = requests.get(url, params=params)
            # Use: response = await security_utils.secure_http_get(url, params=params)
        """
        try:
            response = self.http_session.get(url, params=params, timeout=timeout, **kwargs)
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                data = response.json()
            except ValueError:
                # Not JSON, return text
                return {"text": response.text, "status_code": response.status_code}
            
            # Validate JSON response
            if isinstance(data, dict):
                result = await self.validator.validate_exchange_response(data)
                
                if not result.is_valid:
                    logger.warning(f"HTTP response validation failed for {url}: {result.errors}")
                    return result.sanitized_data
                
                return result.sanitized_data
            
            return data
            
        except Exception as e:
            logger.error(f"Secure HTTP GET failed for {url}: {e}")
            raise
    
    async def secure_http_post(self, url: str, data: Optional[Dict] = None, 
                              json: Optional[Dict] = None, timeout: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Secure HTTP POST request with data validation
        
        Usage:
            # Instead of: response = requests.post(url, json=data)
            # Use: response = await security_utils.secure_http_post(url, json=data)
        """
        try:
            # Validate request data if provided
            if json and isinstance(json, dict):
                # Basic validation for common fields
                for key, value in json.items():
                    if isinstance(value, str) and len(value) > 10000:
                        raise ValueError(f"Request data field '{key}' is too large")
            
            response = self.http_session.post(url, data=data, json=json, timeout=timeout, **kwargs)
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                return {"text": response.text, "status_code": response.status_code}
            
            # Validate response
            if isinstance(response_data, dict):
                result = await self.validator.validate_exchange_response(response_data)
                
                if not result.is_valid:
                    logger.warning(f"HTTP POST response validation failed for {url}: {result.errors}")
                    return result.sanitized_data
                
                return result.sanitized_data
            
            return response_data
            
        except Exception as e:
            logger.error(f"Secure HTTP POST failed for {url}: {e}")
            raise
    
    # ========================================
    # TELEGRAM API SECURITY WRAPPERS
    # ========================================
    
    async def secure_telegram_send(self, bot, chat_id: Union[str, int], text: str, 
                                  parse_mode: Optional[str] = None, **kwargs):
        """
        Secure Telegram message sending with validation
        
        Usage:
            # Instead of: await bot.send_message(chat_id=chat_id, text=text)
            # Use: await security_utils.secure_telegram_send(bot, chat_id, text)
        """
        message_data = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode
        }
        
        # Validate message
        result = await self.validator.validate_telegram_message(message_data)
        
        if not result.is_valid:
            logger.error(f"Telegram message validation failed: {result.errors}")
            raise ValueError(f"Invalid Telegram message: {result.errors}")
        
        # Send with validated data
        try:
            return await bot.send_message(
                chat_id=result.sanitized_data["chat_id"],
                text=result.sanitized_data["text"],
                parse_mode=result.sanitized_data.get("parse_mode"),
                **kwargs
            )
        except Exception as e:
            logger.error(f"Telegram message sending failed: {e}")
            raise
    
    # ========================================
    # CONVENIENCE METHODS FOR COMMON OPERATIONS
    # ========================================
    
    async def secure_fetch_ticker(self, exchange, symbol: str) -> Dict[str, Any]:
        """Secure ticker fetching"""
        return await self.secure_exchange_call(exchange, 'fetch_ticker', symbol)
    
    async def secure_fetch_balance(self, exchange) -> Dict[str, Any]:
        """Secure balance fetching"""
        return await self.secure_exchange_call(exchange, 'fetch_balance')
    
    async def secure_fetch_ohlcv(self, exchange, symbol: str, timeframe: str = '1h', 
                                limit: int = 100) -> list:
        """Secure OHLCV data fetching"""
        return await self.secure_exchange_call(exchange, 'fetch_ohlcv', symbol, timeframe, None, limit)
    
    async def secure_create_order(self, exchange, symbol: str, order_type: str, 
                                 side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Secure order creation"""
        if price:
            return await self.secure_exchange_call(exchange, 'create_order', symbol, order_type, side, amount, price)
        else:
            return await self.secure_exchange_call(exchange, 'create_order', symbol, order_type, side, amount)
    
    # ========================================
    # BINANCE SPECIFIC SECURE WRAPPERS
    # ========================================
    
    async def secure_binance_ticker(self, url: str = "https://api.binance.com/api/v3/ticker/24hr") -> Dict[str, Any]:
        """Secure Binance ticker data fetching"""
        return await self.secure_http_get(url)
    
    async def secure_binance_price(self, symbol: str, 
                                  url: str = "https://api.binance.com/api/v3/ticker/price") -> Dict[str, Any]:
        """Secure Binance price fetching"""
        params = {"symbol": symbol.replace('/', '')}
        return await self.secure_http_get(url, params=params)
    
    # ========================================
    # SECURITY MONITORING & REPORTING
    # ========================================
    
    async def get_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report"""
        return await self.validator.generate_validation_report()
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get current security statistics"""
        return self.validator.validation_stats.copy()
    
    async def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for monitoring"""
        logger.info(f"🔒 Security Event: {event_type} - {details}")

# ========================================
# GLOBAL SECURITY UTILS INSTANCE
# ========================================

# Create a global instance for easy importing
security_utils = SecurityIntegrationUtils()

# ========================================
# EASY INTEGRATION FUNCTIONS
# ========================================

async def secure_exchange_call(exchange, method_name: str, *args, **kwargs):
    """Global function for secure exchange calls"""
    return await security_utils.secure_exchange_call(exchange, method_name, *args, **kwargs)

async def secure_http_get(url: str, **kwargs):
    """Global function for secure HTTP GET"""
    return await security_utils.secure_http_get(url, **kwargs)

async def secure_http_post(url: str, **kwargs):
    """Global function for secure HTTP POST"""
    return await security_utils.secure_http_post(url, **kwargs)

async def secure_telegram_send(bot, chat_id, text, **kwargs):
    """Global function for secure Telegram sending"""
    return await security_utils.secure_telegram_send(bot, chat_id, text, **kwargs)

# ========================================
# DEMO & TESTING
# ========================================

async def demo_security_integration():
    """Demo of security integration utilities"""
    print("🛡️ Security Integration Utils Demo")
    print("=" * 50)
    
    utils = SecurityIntegrationUtils()
    
    # Demo 1: Secure HTTP Request
    print("\n📡 Demo 1: Secure HTTP Request")
    try:
        # This would normally be: requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        result = await utils.secure_http_get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"}
        )
        print(f"✅ Secure HTTP request successful: BTC price = ${float(result.get('price', 0)):,.2f}")
    except Exception as e:
        print(f"❌ Secure HTTP request failed: {e}")
    
    # Demo 2: Security Statistics
    print("\n📊 Demo 2: Security Statistics")
    stats = utils.get_security_stats()
    print(f"Total validations: {stats['total_validations']}")
    print(f"Successful validations: {stats['successful_validations']}")
    print(f"Blocked attempts: {stats['blocked_attempts']}")
    
    print("\n✅ Security Integration Utils Ready!")
    print("Import this module in your trading bot files and replace direct API calls with secure wrappers.")

if __name__ == "__main__":
    asyncio.run(demo_security_integration()) 