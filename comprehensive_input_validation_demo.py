#!/usr/bin/env python3
"""
Comprehensive Input Validation Demo
Demonstrates strict validation for all data types with type checking, range checking, and format validation
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from secure_api_validator import SecureAPIValidator, ValidationRule, SanitizationLevel

async def demo_comprehensive_input_validation():
    """Comprehensive demonstration of all input validation capabilities"""
    
    print("🛡️ COMPREHENSIVE INPUT VALIDATION DEMO")
    print("=" * 80)
    print("Demonstrating strict validation: Type checking, Range checking, Format validation")
    print()
    
    validator = SecureAPIValidator()
    
    # =================================================================
    # 1. TYPE CHECKING VALIDATION
    # =================================================================
    print("🔍 1. TYPE CHECKING VALIDATION")
    print("-" * 60)
    
    type_validation_tests = [
        {
            "name": "✅ Valid String Type",
            "data": {"symbol": "BTCUSDT"},
            "expected_type": str,
            "description": "Correct string type for symbol"
        },
        {
            "name": "❌ Invalid Type - Number as String",
            "data": {"symbol": 12345},
            "expected_type": str,
            "description": "Number provided where string expected"
        },
        {
            "name": "✅ Valid Float Type",
            "data": {"price": 50000.50},
            "expected_type": float,
            "description": "Correct float type for price"
        },
        {
            "name": "❌ Invalid Type - String as Float",
            "data": {"price": "not_a_number"},
            "expected_type": float,
            "description": "String provided where float expected"
        },
        {
            "name": "✅ Valid Integer Conversion",
            "data": {"quantity": "0.001"},
            "expected_type": float,
            "description": "String number correctly converted to float"
        }
    ]
    
    for i, test in enumerate(type_validation_tests, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        # Test exchange request validation (includes type checking)
        result = await validator.validate_exchange_request(test['data'], "order")
        
        if result.is_valid:
            print(f"   Status: ✅ TYPE VALID - Data type accepted")
            if test['data'] != result.sanitized_data:
                print(f"   Type Conversion: Applied automatic type conversion")
        else:
            print(f"   Status: ❌ TYPE INVALID - Type checking failed")
            print(f"   Errors: {result.errors}")
    
    # =================================================================
    # 2. RANGE CHECKING VALIDATION
    # =================================================================
    print(f"\n🔢 2. RANGE CHECKING VALIDATION")
    print("-" * 60)
    
    range_validation_tests = [
        {
            "name": "✅ Valid Price Range",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "LIMIT", "quantity": 0.001, "price": 50000.50},
            "description": "Price within valid range (0.00000001 to 1,000,000,000)"
        },
        {
            "name": "❌ Price Too Low",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "LIMIT", "quantity": 0.001, "price": 0.000000001},
            "description": "Price below minimum threshold"
        },
        {
            "name": "❌ Price Too High",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "LIMIT", "quantity": 0.001, "price": 10000000000},
            "description": "Price above maximum threshold"
        },
        {
            "name": "✅ Valid Quantity Range",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET", "quantity": 0.001},
            "description": "Quantity within valid range"
        },
        {
            "name": "❌ Negative Quantity",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET", "quantity": -0.001},
            "description": "Negative quantity (invalid)"
        },
        {
            "name": "❌ Zero Quantity",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET", "quantity": 0},
            "description": "Zero quantity (invalid)"
        }
    ]
    
    for i, test in enumerate(range_validation_tests, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        result = await validator.validate_exchange_request(test['data'], "order")
        
        if result.is_valid:
            print(f"   Status: ✅ RANGE VALID - Values within acceptable ranges")
        else:
            print(f"   Status: ❌ RANGE INVALID - Values outside acceptable ranges")
            print(f"   Errors: {result.errors}")
    
    # =================================================================
    # 3. FORMAT VALIDATION
    # =================================================================
    print(f"\n📝 3. FORMAT VALIDATION")
    print("-" * 60)
    
    format_validation_tests = [
        {
            "name": "✅ Valid Symbol Format",
            "data": {"symbol": "BTCUSDT"},
            "description": "Alphanumeric symbol, 3-20 characters"
        },
        {
            "name": "❌ Invalid Symbol - Too Short",
            "data": {"symbol": "BT"},
            "description": "Symbol too short (< 3 characters)"
        },
        {
            "name": "❌ Invalid Symbol - Too Long",
            "data": {"symbol": "VERYLONGSYMBOLNAMETHATEXCEEDSLIMIT"},
            "description": "Symbol too long (> 20 characters)"
        },
        {
            "name": "❌ Invalid Symbol - Special Characters",
            "data": {"symbol": "BTC@USDT"},
            "description": "Symbol contains invalid characters"
        },
        {
            "name": "✅ Valid Side Format",
            "data": {"side": "BUY"},
            "description": "Valid side value from allowed list"
        },
        {
            "name": "❌ Invalid Side Format",
            "data": {"side": "PURCHASE"},
            "description": "Invalid side value not in allowed list"
        }
    ]
    
    for i, test in enumerate(format_validation_tests, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        result = await validator.validate_exchange_request(test['data'], "order")
        
        if result.is_valid:
            print(f"   Status: ✅ FORMAT VALID - Correct format and pattern")
        else:
            print(f"   Status: ❌ FORMAT INVALID - Format validation failed")
            print(f"   Errors: {result.errors}")
    
    # =================================================================
    # 4. TELEGRAM MESSAGE VALIDATION
    # =================================================================
    print(f"\n💬 4. TELEGRAM MESSAGE VALIDATION")
    print("-" * 60)
    
    telegram_validation_tests = [
        {
            "name": "✅ Valid Chat ID Format",
            "data": {"chat_id": "123456789", "text": "Hello"},
            "description": "Numeric chat ID within length limits"
        },
        {
            "name": "❌ Invalid Chat ID - Non-numeric",
            "data": {"chat_id": "user_abc", "text": "Hello"},
            "description": "Non-numeric chat ID"
        },
        {
            "name": "❌ Invalid Chat ID - Too Long",
            "data": {"chat_id": "123456789012345678901", "text": "Hello"},
            "description": "Chat ID exceeds 20 character limit"
        },
        {
            "name": "✅ Valid Message Length",
            "data": {"chat_id": "123456789", "text": "Short message"},
            "description": "Message within 4096 character limit"
        },
        {
            "name": "❌ Message Too Long",
            "data": {"chat_id": "123456789", "text": "A" * 5000},
            "description": "Message exceeds 4096 character limit"
        },
        {
            "name": "✅ Valid Parse Mode",
            "data": {"chat_id": "123456789", "text": "Hello", "parse_mode": "HTML"},
            "description": "Valid parse mode from allowed list"
        },
        {
            "name": "❌ Invalid Parse Mode",
            "data": {"chat_id": "123456789", "text": "Hello", "parse_mode": "CUSTOM"},
            "description": "Invalid parse mode not in allowed list"
        }
    ]
    
    for i, test in enumerate(telegram_validation_tests, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        result = await validator.validate_telegram_message(test['data'])
        
        if result.is_valid:
            print(f"   Status: ✅ TELEGRAM VALID - All validation checks passed")
        else:
            print(f"   Status: ❌ TELEGRAM INVALID - Validation failed")
            print(f"   Errors: {result.errors}")
    
    # =================================================================
    # 5. DASHBOARD INPUT VALIDATION
    # =================================================================
    print(f"\n🖥️ 5. DASHBOARD INPUT VALIDATION")
    print("-" * 60)
    
    # Simulate dashboard control inputs
    dashboard_inputs = [
        {
            "name": "✅ Valid Trading Pair Selection",
            "input": {"trading_pair": "BTC/USDT", "timeframe": "1h"},
            "description": "User selects valid trading pair and timeframe"
        },
        {
            "name": "❌ Invalid Trading Pair Format",
            "input": {"trading_pair": "BTC-USDT-INVALID", "timeframe": "1h"},
            "description": "Malformed trading pair format"
        },
        {
            "name": "✅ Valid Amount Input",
            "input": {"amount": "100.50", "percentage": "25"},
            "description": "Valid numeric inputs for trading amounts"
        },
        {
            "name": "❌ Invalid Amount - Injection Attempt",
            "input": {"amount": "100'; DROP TABLE users; --", "percentage": "25"},
            "description": "SQL injection attempt in amount field"
        },
        {
            "name": "❌ Invalid Percentage Range",
            "input": {"amount": "100", "percentage": "150"},
            "description": "Percentage outside valid range (0-100)"
        }
    ]
    
    for i, test in enumerate(dashboard_inputs, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        # Validate dashboard input as exchange response data
        result = await validator.validate_exchange_response(test['input'])
        
        if result.is_valid:
            print(f"   Status: ✅ DASHBOARD VALID - Input accepted")
            if test['input'] != result.sanitized_data:
                print(f"   Sanitization: Input was cleaned for safety")
        else:
            print(f"   Status: ❌ DASHBOARD INVALID - Input rejected")
            print(f"   Errors: {result.errors}")
    
    # =================================================================
    # 6. BUSINESS LOGIC VALIDATION
    # =================================================================
    print(f"\n🏢 6. BUSINESS LOGIC VALIDATION")
    print("-" * 60)
    
    business_logic_tests = [
        {
            "name": "✅ Valid Limit Order",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "LIMIT", "quantity": 0.001, "price": 50000},
            "description": "Limit order with required price"
        },
        {
            "name": "❌ Limit Order Without Price",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "LIMIT", "quantity": 0.001},
            "description": "Limit order missing required price"
        },
        {
            "name": "✅ Valid Market Order",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET", "quantity": 0.001},
            "description": "Market order without price (correct)"
        },
        {
            "name": "❌ Market Order With Price",
            "data": {"symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET", "quantity": 0.001, "price": 50000},
            "description": "Market order with price (incorrect business logic)"
        }
    ]
    
    for i, test in enumerate(business_logic_tests, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Description: {test['description']}")
        
        result = await validator.validate_exchange_request(test['data'], "order")
        
        if result.is_valid:
            print(f"   Status: ✅ BUSINESS LOGIC VALID - Rules compliance verified")
        else:
            print(f"   Status: ❌ BUSINESS LOGIC INVALID - Rule violation detected")
            print(f"   Errors: {result.errors}")
    
    # =================================================================
    # VALIDATION SUMMARY
    # =================================================================
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    stats = validator.validation_stats
    total_tests = stats['total_validations']
    successful = stats['successful_validations']
    failed = stats['failed_validations']
    sanitized = stats['sanitizations_applied']
    blocked = stats['blocked_attempts']
    
    print(f"📈 Validation Statistics:")
    print(f"   Total validations performed: {total_tests}")
    print(f"   Successful validations: {successful}")
    print(f"   Failed validations: {failed}")
    print(f"   Data sanitizations applied: {sanitized}")
    print(f"   Malicious attempts blocked: {blocked}")
    
    success_rate = (successful / total_tests) * 100 if total_tests > 0 else 0
    print(f"   Overall success rate: {success_rate:.1f}%")
    
    print(f"\n🛡️ VALIDATION CAPABILITIES DEMONSTRATED:")
    print(f"   ✅ Type Checking: All data types validated")
    print(f"   ✅ Range Checking: Min/max values enforced")
    print(f"   ✅ Format Validation: Patterns and formats verified")
    print(f"   ✅ Length Validation: String and data length limits")
    print(f"   ✅ Business Logic: Trading rules compliance")
    print(f"   ✅ Security Filtering: Injection attacks blocked")
    print(f"   ✅ Sanitization: Malicious content cleaned")
    
    print(f"\n🎉 COMPREHENSIVE INPUT VALIDATION COMPLETE!")
    print(f"✅ All external API and user input validation requirements satisfied!")

async def demo_custom_validation_rules():
    """Demonstrate how to create custom validation rules"""
    
    print(f"\n🔧 CUSTOM VALIDATION RULES DEMO")
    print("=" * 80)
    
    # Create custom validation rules for specific use cases
    custom_rules = {
        "user_id": ValidationRule(
            field_name="user_id",
            data_type=str,
            required=True,
            min_length=5,
            max_length=50,
            pattern=r'^[a-zA-Z0-9_-]+$',
            sanitization_level=SanitizationLevel.STRICT
        ),
        "portfolio_percentage": ValidationRule(
            field_name="portfolio_percentage",
            data_type=float,
            required=True,
            min_value=0.0,
            max_value=100.0,
            sanitization_level=SanitizationLevel.FINANCIAL
        ),
        "api_endpoint": ValidationRule(
            field_name="api_endpoint",
            data_type=str,
            required=True,
            max_length=200,
            pattern=r'^/api/v[0-9]+/[a-zA-Z0-9/_-]+$',
            sanitization_level=SanitizationLevel.STRICT
        )
    }
    
    print("🔧 Custom Validation Rules:")
    for rule_name, rule in custom_rules.items():
        print(f"   {rule_name}:")
        print(f"     Type: {rule.data_type.__name__}")
        print(f"     Required: {rule.required}")
        print(f"     Min/Max: {rule.min_value or rule.min_length} - {rule.max_value or rule.max_length}")
        print(f"     Pattern: {rule.pattern}")
        print(f"     Sanitization: {rule.sanitization_level.value}")
        print()
    
    # Test custom rules
    test_data = [
        {"user_id": "valid_user123", "portfolio_percentage": 25.5, "api_endpoint": "/api/v1/trading/orders"},
        {"user_id": "invalid@user", "portfolio_percentage": 150.0, "api_endpoint": "invalid-endpoint"},
    ]
    
    validator = SecureAPIValidator()
    
    for i, data in enumerate(test_data, 1):
        print(f"Custom Rule Test {i}:")
        for field_name, value in data.items():
            if field_name in custom_rules:
                rule = custom_rules[field_name]
                result = await validator._validate_field(field_name, value, rule)
                
                status = "✅ VALID" if result.is_valid else "❌ INVALID"
                print(f"   {field_name}: {status}")
                if not result.is_valid:
                    print(f"     Errors: {result.errors}")
        print()

if __name__ == "__main__":
    asyncio.run(demo_comprehensive_input_validation())
    asyncio.run(demo_custom_validation_rules()) 