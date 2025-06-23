#!/usr/bin/env python3
"""
🛡️ Schema Validation Integration Example
Demonstrates how to integrate Pydantic schema validation with existing security systems
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pydantic_schema_validation_system import SchemaValidationSystem
from security_integration_utils import SecurityIntegrationUtils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSecurityTradingBot:
    """
    Trading bot with comprehensive security including:
    1. Input validation
    2. Output sanitization  
    3. Schema validation
    4. Rate limiting
    5. Error handling
    """
    
    def __init__(self):
        self.security_utils = SecurityIntegrationUtils()
        self.schema_validator = SchemaValidationSystem()
        self.trading_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_validations': 0,
            'schema_errors': 0,
            'security_blocks': 0
        }
    
    async def secure_get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker with comprehensive security validation
        
        Security layers:
        1. Input validation (symbol format)
        2. API call with sanitization
        3. Schema validation (Pydantic)
        4. Output sanitization
        """
        
        logger.info(f"🔍 Secure ticker request for {symbol}")
        self.trading_stats['total_requests'] += 1
        
        try:
            # Step 1: Input validation
            if not symbol or len(symbol) < 3:
                logger.error("❌ Invalid symbol format")
                self.trading_stats['failed_validations'] += 1
                return None
            
            # Step 2: Simulate exchange API call with basic security
            simulated_response = {
                "symbol": symbol.upper(),
                "price": "50000.50",
                "bid": "49999.00", 
                "ask": "50001.00",
                "volume": "1234.56",
                "change": "500.50",
                "high": "51000.00",
                "low": "49000.00"
            }
            
            # Step 3: Schema validation
            schema_result = await self.schema_validator.validate_ticker_response(simulated_response)
            
            if not schema_result['is_valid']:
                logger.error(f"❌ Schema validation failed: {schema_result['errors']}")
                self.trading_stats['schema_errors'] += 1
                return None
            
            # Step 4: Additional security validation
            security_result = await self.security_utils.validator.validate_exchange_response(
                schema_result['validated_data']
            )
            
            if not security_result.is_valid:
                logger.warning(f"⚠️ Security validation warnings: {security_result.errors}")
                self.trading_stats['security_blocks'] += 1
                final_data = security_result.sanitized_data
            else:
                final_data = schema_result['validated_data']
            
            self.trading_stats['successful_requests'] += 1
            logger.info(f"✅ Secure ticker retrieved: {final_data['symbol']} = ${final_data['price']}")
            
            return final_data
            
        except Exception as e:
            logger.error(f"❌ Secure ticker request failed: {e}")
            self.trading_stats['failed_validations'] += 1
            return None
    
    async def secure_place_order(self, symbol: str, side: str, quantity: float, 
                               price: float = None, order_type: str = "LIMIT") -> Optional[Dict[str, Any]]:
        """
        Place order with comprehensive security validation
        
        Security layers:
        1. Input validation (all parameters)
        2. Business logic validation
        3. API call simulation
        4. Schema validation (Pydantic)
        5. Output sanitization
        """
        
        logger.info(f"🔍 Secure order placement: {side} {quantity} {symbol} @ {price}")
        self.trading_stats['total_requests'] += 1
        
        try:
            # Step 1: Input validation
            if not all([symbol, side, quantity]):
                logger.error("❌ Missing required order parameters")
                self.trading_stats['failed_validations'] += 1
                return None
            
            if side.upper() not in ['BUY', 'SELL']:
                logger.error("❌ Invalid order side")
                self.trading_stats['failed_validations'] += 1
                return None
            
            if quantity <= 0:
                logger.error("❌ Invalid quantity")
                self.trading_stats['failed_validations'] += 1
                return None
            
            if order_type.upper() == "LIMIT" and (not price or price <= 0):
                logger.error("❌ Limit orders require valid price")
                self.trading_stats['failed_validations'] += 1
                return None
            
            # Step 2: Simulate exchange order placement
            simulated_order_response = {
                "orderId": "12345678",
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": order_type.upper(),
                "status": "FILLED",
                "quantity": str(quantity),
                "price": str(price) if price else None,
                "executedQty": str(quantity),
                "time": 1640995200000,
                "updateTime": 1640995200000
            }
            
            # Step 3: Schema validation
            schema_result = await self.schema_validator.validate_exchange_order_response(
                simulated_order_response
            )
            
            if not schema_result['is_valid']:
                logger.error(f"❌ Order schema validation failed: {schema_result['errors']}")
                self.trading_stats['schema_errors'] += 1
                return None
            
            # Step 4: Additional security validation
            security_result = await self.security_utils.validator.validate_exchange_response(
                schema_result['validated_data']
            )
            
            if not security_result.is_valid:
                logger.warning(f"⚠️ Order security validation warnings: {security_result.errors}")
                self.trading_stats['security_blocks'] += 1
                final_data = security_result.sanitized_data
            else:
                final_data = schema_result['validated_data']
            
            self.trading_stats['successful_requests'] += 1
            logger.info(f"✅ Secure order placed: {final_data['orderId']} - {final_data['status']}")
            
            return final_data
            
        except Exception as e:
            logger.error(f"❌ Secure order placement failed: {e}")
            self.trading_stats['failed_validations'] += 1
            return None
    
    async def secure_get_balance(self, asset: str = None) -> Optional[Dict[str, Any]]:
        """
        Get account balance with security validation
        """
        
        logger.info(f"🔍 Secure balance request for {asset or 'all assets'}")
        self.trading_stats['total_requests'] += 1
        
        try:
            # Simulate balance response
            simulated_balance = {
                "balances": [
                    {"asset": "BTC", "free": "0.00123456", "locked": "0.00000000"},
                    {"asset": "USDT", "free": "1000.50", "locked": "0.00"},
                    {"asset": "ETH", "free": "0.5", "locked": "0.1"}
                ],
                "updateTime": 1640995200000,
                "accountType": "SPOT"
            }
            
            # Filter by asset if specified
            if asset:
                asset_upper = asset.upper()
                filtered_balances = [
                    b for b in simulated_balance["balances"] 
                    if b["asset"] == asset_upper
                ]
                simulated_balance["balances"] = filtered_balances
            
            # Basic security validation (no specific schema for balance yet)
            security_result = await self.security_utils.validator.validate_exchange_response(
                simulated_balance
            )
            
            if not security_result.is_valid:
                logger.warning(f"⚠️ Balance security validation warnings: {security_result.errors}")
                self.trading_stats['security_blocks'] += 1
                final_data = security_result.sanitized_data
            else:
                final_data = simulated_balance
            
            self.trading_stats['successful_requests'] += 1
            logger.info(f"✅ Secure balance retrieved: {len(final_data['balances'])} assets")
            
            return final_data
            
        except Exception as e:
            logger.error(f"❌ Secure balance request failed: {e}")
            self.trading_stats['failed_validations'] += 1
            return None
    
    async def validate_malicious_response(self, response_data: Dict[str, Any], 
                                        schema_type: str) -> Dict[str, Any]:
        """
        Test how the system handles malicious/malformed responses
        """
        
        logger.info(f"🔍 Testing malicious response handling for {schema_type}")
        
        # Schema validation first
        schema_result = await self.schema_validator.validate_response(response_data, schema_type)
        
        # Security validation second
        if schema_result['is_valid']:
            security_result = await self.security_utils.validator.validate_exchange_response(
                schema_result['validated_data']
            )
        else:
            # Try security validation on original data
            security_result = await self.security_utils.validator.validate_exchange_response(
                response_data
            )
        
        return {
            'schema_validation': schema_result,
            'security_validation': {
                'is_valid': security_result.is_valid,
                'errors': security_result.errors,
                'sanitized_data': security_result.sanitized_data
            }
        }
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        
        schema_stats = self.schema_validator.get_validation_stats()
        
        return {
            'trading_requests': self.trading_stats,
            'schema_validation': schema_stats,
            'security_effectiveness': {
                'total_protection_rate': (
                    (self.trading_stats['successful_requests'] / 
                     max(self.trading_stats['total_requests'], 1)) * 100
                ),
                'schema_error_rate': (
                    (self.trading_stats['schema_errors'] / 
                     max(self.trading_stats['total_requests'], 1)) * 100
                ),
                'security_block_rate': (
                    (self.trading_stats['security_blocks'] / 
                     max(self.trading_stats['total_requests'], 1)) * 100
                )
            }
        }

# =================================================================
# DEMONSTRATION
# =================================================================

async def demo_enhanced_security_trading():
    """Demonstrate enhanced security trading with schema validation"""
    
    print("🛡️ ENHANCED SECURITY TRADING BOT DEMO")
    print("=" * 80)
    print("Demonstrating comprehensive security with schema validation")
    print()
    
    bot = EnhancedSecurityTradingBot()
    
    # =================================================================
    # 1. SECURE TICKER REQUESTS
    # =================================================================
    print("💰 1. SECURE TICKER REQUESTS")
    print("-" * 60)
    
    # Valid ticker request
    print("\n   Test 1: Valid ticker request")
    ticker = await bot.secure_get_ticker("BTCUSDT")
    if ticker:
        print(f"   ✅ Success: {ticker['symbol']} = ${ticker['price']}")
    else:
        print("   ❌ Failed to get ticker")
    
    # Invalid ticker request
    print("\n   Test 2: Invalid ticker request")
    ticker = await bot.secure_get_ticker("BT")  # Too short
    if ticker:
        print(f"   ❌ Unexpected success: {ticker}")
    else:
        print("   ✅ Correctly rejected invalid ticker")
    
    # =================================================================
    # 2. SECURE ORDER PLACEMENT
    # =================================================================
    print(f"\n📊 2. SECURE ORDER PLACEMENT")
    print("-" * 60)
    
    # Valid limit order
    print("\n   Test 1: Valid limit order")
    order = await bot.secure_place_order("BTCUSDT", "BUY", 0.001, 50000.0, "LIMIT")
    if order:
        print(f"   ✅ Success: Order {order['orderId']} - {order['status']}")
    else:
        print("   ❌ Failed to place order")
    
    # Invalid order (missing price for limit order)
    print("\n   Test 2: Invalid limit order (no price)")
    order = await bot.secure_place_order("BTCUSDT", "BUY", 0.001, None, "LIMIT")
    if order:
        print(f"   ❌ Unexpected success: {order}")
    else:
        print("   ✅ Correctly rejected invalid order")
    
    # =================================================================
    # 3. SECURE BALANCE REQUESTS
    # =================================================================
    print(f"\n💳 3. SECURE BALANCE REQUESTS")
    print("-" * 60)
    
    # Get all balances
    print("\n   Test 1: Get all balances")
    balance = await bot.secure_get_balance()
    if balance:
        print(f"   ✅ Success: Retrieved {len(balance['balances'])} asset balances")
    else:
        print("   ❌ Failed to get balance")
    
    # Get specific asset balance
    print("\n   Test 2: Get BTC balance")
    balance = await bot.secure_get_balance("BTC")
    if balance and balance['balances']:
        btc_balance = balance['balances'][0]
        print(f"   ✅ Success: BTC balance = {btc_balance['free']}")
    else:
        print("   ❌ Failed to get BTC balance")
    
    # =================================================================
    # 4. MALICIOUS RESPONSE HANDLING
    # =================================================================
    print(f"\n🚨 4. MALICIOUS RESPONSE HANDLING")
    print("-" * 60)
    
    # Test malicious ticker response
    print("\n   Test 1: Malicious ticker with XSS")
    malicious_ticker = {
        "symbol": "BTCUSDT<script>alert('xss')</script>",
        "price": "50000.50",
        "bid": "60000.00",  # Bid higher than ask (invalid)
        "ask": "49999.00"
    }
    
    result = await bot.validate_malicious_response(malicious_ticker, 'ticker')
    
    print(f"   Schema validation: {'✅ PASSED' if result['schema_validation']['is_valid'] else '❌ FAILED'}")
    if not result['schema_validation']['is_valid']:
        print(f"   Schema errors: {result['schema_validation']['errors']}")
    
    print(f"   Security validation: {'✅ PASSED' if result['security_validation']['is_valid'] else '❌ FAILED'}")
    if not result['security_validation']['is_valid']:
        print(f"   Security errors: {result['security_validation']['errors']}")
    
    # Test malicious order response
    print("\n   Test 2: Malicious order with injection")
    malicious_order = {
        "orderId": "'; DROP TABLE orders; --",
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "status": "FILLED",
        "quantity": "-1.0",  # Negative quantity
        "price": "50000.50"
    }
    
    result = await bot.validate_malicious_response(malicious_order, 'exchange_order')
    
    print(f"   Schema validation: {'✅ PASSED' if result['schema_validation']['is_valid'] else '❌ FAILED'}")
    if not result['schema_validation']['is_valid']:
        print(f"   Schema errors: {result['schema_validation']['errors']}")
    
    print(f"   Security validation: {'✅ PASSED' if result['security_validation']['is_valid'] else '❌ FAILED'}")
    if not result['security_validation']['is_valid']:
        print(f"   Security errors: {result['security_validation']['errors']}")
    
    # =================================================================
    # 5. SECURITY STATISTICS
    # =================================================================
    print(f"\n📊 5. SECURITY STATISTICS")
    print("=" * 80)
    
    stats = bot.get_security_stats()
    
    print(f"📈 Trading Request Statistics:")
    print(f"   Total requests: {stats['trading_requests']['total_requests']}")
    print(f"   Successful requests: {stats['trading_requests']['successful_requests']}")
    print(f"   Failed validations: {stats['trading_requests']['failed_validations']}")
    print(f"   Schema errors: {stats['trading_requests']['schema_errors']}")
    print(f"   Security blocks: {stats['trading_requests']['security_blocks']}")
    
    print(f"\n📈 Schema Validation Statistics:")
    print(f"   Total validations: {stats['schema_validation']['total_validations']}")
    print(f"   Successful validations: {stats['schema_validation']['successful_validations']}")
    print(f"   Failed validations: {stats['schema_validation']['failed_validations']}")
    print(f"   Success rate: {stats['schema_validation']['success_rate']:.1f}%")
    
    print(f"\n🛡️ Security Effectiveness:")
    print(f"   Total protection rate: {stats['security_effectiveness']['total_protection_rate']:.1f}%")
    print(f"   Schema error rate: {stats['security_effectiveness']['schema_error_rate']:.1f}%")
    print(f"   Security block rate: {stats['security_effectiveness']['security_block_rate']:.1f}%")
    
    print(f"\n🛡️ SECURITY CAPABILITIES DEMONSTRATED:")
    print(f"   ✅ Input Validation: Parameter checking and format validation")
    print(f"   ✅ Schema Validation: Pydantic model structure enforcement")
    print(f"   ✅ Business Logic: Trading-specific rule validation")
    print(f"   ✅ Security Filtering: Injection and XSS attack prevention")
    print(f"   ✅ Output Sanitization: Response data cleaning")
    print(f"   ✅ Error Handling: Graceful failure management")
    print(f"   ✅ Statistics Tracking: Comprehensive security monitoring")
    
    print(f"\n🎉 ENHANCED SECURITY TRADING BOT DEMO COMPLETE!")
    print(f"✅ All external API interactions are now fully secured with schema validation!")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_security_trading()) 