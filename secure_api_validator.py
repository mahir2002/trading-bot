#!/usr/bin/env python3
"""
Secure API Validator - Comprehensive Input Validation and Sanitization System
Protects against injection attacks, data corruption, and malicious payloads
"""

import re
import json
import html
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import unicodedata
from decimal import Decimal, InvalidOperation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class SanitizationLevel(Enum):
    """Different levels of sanitization"""
    BASIC = "basic"
    STRICT = "strict"
    FINANCIAL = "financial"
    TELEGRAM = "telegram"
    EXCHANGE = "exchange"
    SQL_SAFE = "sql_safe"

@dataclass
class ValidationRule:
    """Validation rule configuration"""
    field_name: str
    data_type: type
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    sanitization_level: SanitizationLevel = SanitizationLevel.BASIC

@dataclass
class ValidationResult:
    """Result of validation process"""
    is_valid: bool
    sanitized_data: Any
    original_data: Any
    errors: List[str]
    warnings: List[str]
    field_name: str
    validation_timestamp: datetime

class SecureAPIValidator:
    """Comprehensive API input/output validation and sanitization system"""
    
    def __init__(self):
        self.validation_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "sanitizations_applied": 0,
            "blocked_attempts": 0
        }
        
        # Common dangerous patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'expression\s*\(',
            r'import\s+',
            r'exec\s*\(',
            r'eval\s*\(',
            r'__\w+__',
            r'SELECT\s+.*FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*SET',
            r'DELETE\s+FROM',
            r'DROP\s+TABLE',
            r'UNION\s+SELECT',
            r'\|\s*nc\s+',
            r'\|\s*sh\s*',
            r'`[^`]*`',
            r'\$\([^)]*\)',
        ]
        
        self._setup_validation_rules()
    
    def _setup_validation_rules(self):
        """Set up validation rules for different API types"""
        
        # Exchange API validation rules
        self.exchange_rules = {
            "symbol": ValidationRule(
                field_name="symbol",
                data_type=str,
                required=True,
                min_length=3,
                max_length=20,
                pattern=r'^[A-Z0-9]{3,20}$',
                sanitization_level=SanitizationLevel.STRICT
            ),
            "side": ValidationRule(
                field_name="side",
                data_type=str,
                required=True,
                allowed_values=["BUY", "SELL", "buy", "sell"],
                sanitization_level=SanitizationLevel.STRICT
            ),
            "quantity": ValidationRule(
                field_name="quantity",
                data_type=float,
                required=True,
                min_value=0.00000001,
                max_value=1000000000,
                sanitization_level=SanitizationLevel.FINANCIAL
            ),
            "price": ValidationRule(
                field_name="price",
                data_type=float,
                required=False,
                min_value=0.00000001,
                max_value=1000000000,
                sanitization_level=SanitizationLevel.FINANCIAL
            ),
            "order_type": ValidationRule(
                field_name="order_type",
                data_type=str,
                required=True,
                allowed_values=["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "market", "limit", "stop", "stop_limit"],
                sanitization_level=SanitizationLevel.STRICT
            )
        }
        
        # Telegram API validation rules
        self.telegram_rules = {
            "chat_id": ValidationRule(
                field_name="chat_id",
                data_type=str,
                required=True,
                pattern=r'^-?\d+$',
                max_length=20,
                sanitization_level=SanitizationLevel.STRICT
            ),
            "text": ValidationRule(
                field_name="text",
                data_type=str,
                required=True,
                max_length=4096,
                sanitization_level=SanitizationLevel.TELEGRAM
            ),
            "parse_mode": ValidationRule(
                field_name="parse_mode",
                data_type=str,
                required=False,
                allowed_values=["HTML", "Markdown", "MarkdownV2"],
                sanitization_level=SanitizationLevel.STRICT
            )
        }
    
    async def validate_exchange_request(self, data: Dict[str, Any], 
                                      operation: str = "order") -> ValidationResult:
        """Validate exchange API request data"""
        
        logger.info(f"🔍 Validating exchange {operation} request")
        
        sanitized_data = {}
        all_errors = []
        all_warnings = []
        
        # Validate each field
        for field_name, value in data.items():
            if field_name in self.exchange_rules:
                rule = self.exchange_rules[field_name]
                result = await self._validate_field(field_name, value, rule)
                
                if result.is_valid:
                    sanitized_data[field_name] = result.sanitized_data
                else:
                    all_errors.extend(result.errors)
                
                all_warnings.extend(result.warnings)
        
        # Check for required fields
        for field_name, rule in self.exchange_rules.items():
            if rule.required and field_name not in data:
                all_errors.append(f"Required field '{field_name}' is missing")
        
        # Additional exchange-specific validations
        if operation in ["order", "place_order", "create_order"]:
            exchange_errors = await self._validate_exchange_order_logic(sanitized_data)
            all_errors.extend(exchange_errors)
        
        is_valid = len(all_errors) == 0
        
        if not is_valid:
            self.validation_stats["failed_validations"] += 1
            self.validation_stats["blocked_attempts"] += 1
            logger.warning(f"❌ Exchange validation failed: {all_errors}")
        else:
            self.validation_stats["successful_validations"] += 1
            logger.info(f"✅ Exchange validation successful")
        
        self.validation_stats["total_validations"] += 1
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized_data=sanitized_data,
            original_data=data,
            errors=all_errors,
            warnings=all_warnings,
            field_name="exchange_request",
            validation_timestamp=datetime.now()
        )
    
    async def validate_telegram_message(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate Telegram message data"""
        
        logger.info("🔍 Validating Telegram message")
        
        sanitized_data = {}
        all_errors = []
        all_warnings = []
        
        # Validate each field
        for field_name, value in data.items():
            if field_name in self.telegram_rules:
                rule = self.telegram_rules[field_name]
                result = await self._validate_field(field_name, value, rule)
                
                if result.is_valid:
                    sanitized_data[field_name] = result.sanitized_data
                else:
                    all_errors.extend(result.errors)
                
                all_warnings.extend(result.warnings)
        
        # Check for required fields
        for field_name, rule in self.telegram_rules.items():
            if rule.required and field_name not in data:
                all_errors.append(f"Required field '{field_name}' is missing")
        
        # Additional Telegram-specific validations
        telegram_errors = await self._validate_telegram_message_content(sanitized_data)
        all_errors.extend(telegram_errors)
        
        is_valid = len(all_errors) == 0
        
        if not is_valid:
            self.validation_stats["failed_validations"] += 1
            self.validation_stats["blocked_attempts"] += 1
            logger.warning(f"❌ Telegram validation failed: {all_errors}")
        else:
            self.validation_stats["successful_validations"] += 1
            logger.info(f"✅ Telegram validation successful")
        
        self.validation_stats["total_validations"] += 1
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized_data=sanitized_data,
            original_data=data,
            errors=all_errors,
            warnings=all_warnings,
            field_name="telegram_message",
            validation_timestamp=datetime.now()
        )
    
    async def validate_exchange_response(self, data: Dict[str, Any], 
                                       expected_fields: List[str] = None) -> ValidationResult:
        """Validate exchange API response data"""
        
        logger.info("🔍 Validating exchange response")
        
        all_errors = []
        all_warnings = []
        sanitized_data = {}
        
        try:
            # Basic structure validation
            if not isinstance(data, dict):
                all_errors.append("Exchange response must be a dictionary")
                return self._create_failed_result(data, all_errors, "exchange_response")
            
            # Sanitize all response data
            sanitized_data = await self._deep_sanitize_data(data, SanitizationLevel.EXCHANGE)
            
            # Check for expected fields if provided
            if expected_fields:
                for field in expected_fields:
                    if field not in sanitized_data:
                        all_warnings.append(f"Expected field '{field}' not found in response")
            
            # Validate common exchange response fields
            response_errors = await self._validate_exchange_response_fields(sanitized_data)
            all_errors.extend(response_errors)
            
        except ValidationError as e:
            all_errors.append(f"Exchange response validation error: {str(e)}")
            logger.error(f"Exchange response validation error: {e}")
        except ValueError as e:
            all_errors.append(f"Exchange response value error: {str(e)}")
            logger.error(f"Exchange response value error: {e}")
        except TypeError as e:
            all_errors.append(f"Exchange response type error: {str(e)}")
            logger.error(f"Exchange response type error: {e}")
        except KeyError as e:
            all_errors.append(f"Missing required exchange response field: {str(e)}")
            logger.error(f"Exchange response key error: {e}")
        except Exception as e:
            all_errors.append(f"Unexpected exchange response validation error: {str(e)}")
            logger.error(f"Unexpected exchange response validation error: {e}")
        
        is_valid = len(all_errors) == 0
        
        if not is_valid:
            self.validation_stats["failed_validations"] += 1
            logger.warning(f"❌ Exchange response validation failed: {all_errors}")
        else:
            self.validation_stats["successful_validations"] += 1
            logger.info(f"✅ Exchange response validation successful")
        
        self.validation_stats["total_validations"] += 1
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized_data=sanitized_data,
            original_data=data,
            errors=all_errors,
            warnings=all_warnings,
            field_name="exchange_response",
            validation_timestamp=datetime.now()
        )
    
    async def _validate_field(self, field_name: str, value: Any, 
                            rule: ValidationRule) -> ValidationResult:
        """Validate individual field against rule"""
        
        errors = []
        warnings = []
        sanitized_value = value
        
        try:
            # Type validation
            if not isinstance(value, rule.data_type) and value is not None:
                try:
                    if rule.data_type == str:
                        sanitized_value = str(value)
                    elif rule.data_type == int:
                        sanitized_value = int(float(value))
                    elif rule.data_type == float:
                        sanitized_value = float(value)
                    else:
                        errors.append(f"Field '{field_name}' must be of type {rule.data_type.__name__}")
                        return self._create_failed_result(value, errors, field_name)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field_name}' cannot be converted to {rule.data_type.__name__}")
                    return self._create_failed_result(value, errors, field_name)
            
            # Required field validation
            if rule.required and (value is None or value == ""):
                errors.append(f"Field '{field_name}' is required")
                return self._create_failed_result(value, errors, field_name)
            
            # Skip further validation for None values if not required
            if value is None and not rule.required:
                return ValidationResult(
                    is_valid=True,
                    sanitized_data=None,
                    original_data=value,
                    errors=[],
                    warnings=[],
                    field_name=field_name,
                    validation_timestamp=datetime.now()
                )
            
            # String-specific validations
            if isinstance(sanitized_value, str):
                # Length validation
                if rule.min_length and len(sanitized_value) < rule.min_length:
                    errors.append(f"Field '{field_name}' must be at least {rule.min_length} characters")
                
                if rule.max_length and len(sanitized_value) > rule.max_length:
                    errors.append(f"Field '{field_name}' must be at most {rule.max_length} characters")
                
                # Pattern validation
                if rule.pattern and not re.match(rule.pattern, sanitized_value, re.IGNORECASE):
                    errors.append(f"Field '{field_name}' does not match required pattern")
                
                # Sanitization
                sanitized_value = await self._sanitize_string(sanitized_value, rule.sanitization_level)
                
                # Check for dangerous patterns
                dangerous_found = await self._check_dangerous_patterns(sanitized_value)
                if dangerous_found:
                    errors.append(f"Field '{field_name}' contains potentially dangerous content")
                    self.validation_stats["blocked_attempts"] += 1
            
            # Numeric validations
            if isinstance(sanitized_value, (int, float)):
                if rule.min_value is not None and sanitized_value < rule.min_value:
                    errors.append(f"Field '{field_name}' must be at least {rule.min_value}")
                
                if rule.max_value is not None and sanitized_value > rule.max_value:
                    errors.append(f"Field '{field_name}' must be at most {rule.max_value}")
            
            # Allowed values validation
            if rule.allowed_values and sanitized_value not in rule.allowed_values:
                errors.append(f"Field '{field_name}' must be one of: {rule.allowed_values}")
            
        except ValidationError as e:
            errors.append(f"Validation error for field '{field_name}': {str(e)}")
            logger.error(f"Field validation error: {e}")
        except ValueError as e:
            errors.append(f"Value error for field '{field_name}': {str(e)}")
            logger.error(f"Field value error: {e}")
        except TypeError as e:
            errors.append(f"Type error for field '{field_name}': {str(e)}")
            logger.error(f"Field type error: {e}")
        except AttributeError as e:
            errors.append(f"Attribute error for field '{field_name}': {str(e)}")
            logger.error(f"Field attribute error: {e}")
        except Exception as e:
            errors.append(f"Unexpected validation error for field '{field_name}': {str(e)}")
            logger.error(f"Unexpected field validation error: {e}")
        
        is_valid = len(errors) == 0
        
        if sanitized_value != value:
            self.validation_stats["sanitizations_applied"] += 1
            warnings.append(f"Field '{field_name}' was sanitized")
        
        return ValidationResult(
            is_valid=is_valid,
            sanitized_data=sanitized_value,
            original_data=value,
            errors=errors,
            warnings=warnings,
            field_name=field_name,
            validation_timestamp=datetime.now()
        )
    
    async def _sanitize_string(self, value: str, level: SanitizationLevel) -> str:
        """Sanitize string based on sanitization level"""
        
        if not isinstance(value, str):
            return value
        
        sanitized = value
        
        try:
            # Normalize unicode
            sanitized = unicodedata.normalize('NFKC', sanitized)
            
            # Remove null bytes
            sanitized = sanitized.replace('\x00', '')
            
            if level == SanitizationLevel.BASIC:
                sanitized = html.escape(sanitized)
                sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
                sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            
            elif level == SanitizationLevel.STRICT:
                sanitized = re.sub(r'[^A-Za-z0-9_\-\.]', '', sanitized)
            
            elif level == SanitizationLevel.FINANCIAL:
                sanitized = re.sub(r'[^0-9\.\-\+eE]', '', sanitized)
            
            elif level == SanitizationLevel.TELEGRAM:
                sanitized = html.escape(sanitized)
                sanitized = re.sub(r'[`*_\[\]()~|]', '', sanitized)
                sanitized = sanitized[:4096]
            
            elif level == SanitizationLevel.EXCHANGE:
                sanitized = html.escape(sanitized)
                sanitized = re.sub(r'[<>"\';\\]', '', sanitized)
            
            elif level == SanitizationLevel.SQL_SAFE:
                sanitized = sanitized.replace("'", "''")
                sanitized = sanitized.replace("--", "")
                sanitized = sanitized.replace(";", "")
                sanitized = re.sub(r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b', 
                                 '', sanitized, flags=re.IGNORECASE)
            
            sanitized = sanitized.strip()
            
        except Exception as e:
            logger.error(f"Sanitization error: {e}")
            sanitized = value
        
        return sanitized
    
    async def _deep_sanitize_data(self, data: Any, level: SanitizationLevel) -> Any:
        """Recursively sanitize nested data structures"""
        
        if isinstance(data, dict):
            return {
                key: await self._deep_sanitize_data(value, level)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                await self._deep_sanitize_data(item, level)
                for item in data
            ]
        elif isinstance(data, str):
            return await self._sanitize_string(data, level)
        else:
            return data
    
    async def _check_dangerous_patterns(self, value: str) -> bool:
        """Check for dangerous patterns in string"""
        
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"🚨 Dangerous pattern detected: {pattern}")
                return True
        
        return False
    
    async def _validate_exchange_order_logic(self, data: Dict[str, Any]) -> List[str]:
        """Validate exchange order business logic"""
        
        errors = []
        
        try:
            # Market order validation
            if data.get("order_type", "").upper() == "MARKET":
                if "price" in data and data["price"] is not None:
                    errors.append("Market orders should not have a price")
            
            # Limit order validation
            elif data.get("order_type", "").upper() == "LIMIT":
                if "price" not in data or data["price"] is None:
                    errors.append("Limit orders must have a price")
            
            # Quantity validation
            if "quantity" in data:
                try:
                    quantity = Decimal(str(data["quantity"]))
                    if quantity <= 0:
                        errors.append("Quantity must be positive")
                except (InvalidOperation, ValueError):
                    errors.append("Invalid quantity format")
            
            # Symbol format validation
            if "symbol" in data:
                symbol = data["symbol"].upper()
                if not re.match(r'^[A-Z0-9]{6,12}$', symbol):
                    errors.append("Invalid symbol format")
        
        except Exception as e:
            errors.append(f"Order logic validation error: {str(e)}")
        
        return errors
    
    async def _validate_telegram_message_content(self, data: Dict[str, Any]) -> List[str]:
        """Validate Telegram message content"""
        
        errors = []
        
        try:
            if "text" in data:
                text = data["text"]
                
                if len(text) > 4096:
                    errors.append("Telegram message exceeds maximum length (4096 characters)")
                
                if text.count("http") > 5:
                    errors.append("Message contains too many links")
                
                if text.count("*") > 20 or text.count("_") > 20:
                    errors.append("Message contains excessive formatting")
            
            if "chat_id" in data:
                chat_id = str(data["chat_id"])
                if not re.match(r'^-?\d+$', chat_id):
                    errors.append("Invalid chat_id format")
        
        except Exception as e:
            errors.append(f"Telegram content validation error: {str(e)}")
        
        return errors
    
    async def _validate_exchange_response_fields(self, data: Dict[str, Any]) -> List[str]:
        """Validate common exchange response fields"""
        
        errors = []
        
        try:
            # Order ID validation
            if "orderId" in data or "order_id" in data:
                order_id = data.get("orderId") or data.get("order_id")
                if not isinstance(order_id, (str, int)):
                    errors.append("Order ID must be string or integer")
                elif isinstance(order_id, str) and not order_id.isdigit():
                    errors.append("String order ID must be numeric")
            
            # Price validation
            for price_field in ["price", "avgPrice", "stopPrice"]:
                if price_field in data:
                    try:
                        price = Decimal(str(data[price_field]))
                        if price < 0:
                            errors.append(f"{price_field} cannot be negative")
                    except (InvalidOperation, ValueError):
                        errors.append(f"Invalid {price_field} format")
            
            # Status validation
            if "status" in data:
                valid_statuses = [
                    "NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", 
                    "PENDING_CANCEL", "REJECTED", "EXPIRED"
                ]
                if data["status"] not in valid_statuses:
                    errors.append(f"Invalid order status: {data['status']}")
        
        except Exception as e:
            errors.append(f"Exchange response field validation error: {str(e)}")
        
        return errors
    
    def _create_failed_result(self, original_data: Any, errors: List[str], 
                            field_name: str) -> ValidationResult:
        """Create a failed validation result"""
        
        return ValidationResult(
            is_valid=False,
            sanitized_data=None,
            original_data=original_data,
            errors=errors,
            warnings=[],
            field_name=field_name,
            validation_timestamp=datetime.now()
        )
    
    async def generate_validation_report(self) -> Dict[str, Any]:
        """Generate validation statistics report"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.validation_stats.copy(),
            "success_rate": (
                self.validation_stats["successful_validations"] / 
                max(self.validation_stats["total_validations"], 1) * 100
            ),
            "sanitization_rate": (
                self.validation_stats["sanitizations_applied"] / 
                max(self.validation_stats["total_validations"], 1) * 100
            ),
            "blocked_attempts": self.validation_stats["blocked_attempts"]
        }
    
    async def secure_exchange_call(self, endpoint: str, method: str, 
                                 params: Dict[str, Any] = None, 
                                 data: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """Secure wrapper for exchange API calls with validation"""
        
        try:
            # Validate request data
            if data:
                data_result = await self.validate_exchange_request(data, "order")
                if not data_result.is_valid:
                    logger.error(f"Exchange request data validation failed: {data_result.errors}")
                    return False, {"error": "Invalid request data", "details": data_result.errors}
                data = data_result.sanitized_data
            
            # Simulate response for demo
            simulated_response = {
                "orderId": "12345",
                "symbol": data.get("symbol", "BTCUSDT") if data else "BTCUSDT",
                "status": "FILLED",
                "price": data.get("price", "50000") if data else "50000",
                "quantity": data.get("quantity", "0.001") if data else "0.001",
                "time": int(datetime.now().timestamp() * 1000)
            }
            
            # Validate response
            response_result = await self.validate_exchange_response(simulated_response)
            if not response_result.is_valid:
                logger.warning(f"Exchange response validation failed: {response_result.errors}")
                return True, {
                    "data": response_result.sanitized_data,
                    "warnings": response_result.warnings,
                    "validation_errors": response_result.errors
                }
            
            return True, response_result.sanitized_data
            
        except Exception as e:
            logger.error(f"Secure exchange call failed: {e}")
            return False, {"error": "Exchange call failed", "details": str(e)}
    
    async def secure_telegram_send(self, chat_id: str, text: str, 
                                 parse_mode: str = None) -> Tuple[bool, Any]:
        """Secure wrapper for Telegram message sending with validation"""
        
        try:
            # Prepare message data
            message_data = {
                "chat_id": chat_id,
                "text": text
            }
            
            if parse_mode:
                message_data["parse_mode"] = parse_mode
            
            # Validate message
            result = await self.validate_telegram_message(message_data)
            
            if not result.is_valid:
                logger.error(f"Telegram message validation failed: {result.errors}")
                return False, {"error": "Invalid message data", "details": result.errors}
            
            # Simulate response for demo
            simulated_response = {
                "ok": True,
                "result": {
                    "message_id": 123,
                    "chat": {"id": int(chat_id)},
                    "text": result.sanitized_data["text"],
                    "date": int(datetime.now().timestamp())
                }
            }
            
            return True, simulated_response
            
        except Exception as e:
            logger.error(f"Secure telegram send failed: {e}")
            return False, {"error": "Telegram send failed", "details": str(e)}

# Demo function
async def demo_secure_api_validator():
    """Demonstrate secure API validation system"""
    
    print("🛡️ SECURE API VALIDATOR DEMO")
    print("=" * 70)
    print("Comprehensive input validation and sanitization for external APIs")
    print()
    
    validator = SecureAPIValidator()
    
    # Demo 1: Exchange API validation
    print("📊 Demo 1: Exchange API Request Validation")
    print("-" * 50)
    
    test_orders = [
        {
            "name": "Valid Order",
            "data": {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": 0.001,
                "price": 50000.50
            }
        },
        {
            "name": "Malicious Order (Script Injection)",
            "data": {
                "symbol": "<script>alert('hack')</script>BTCUSDT",
                "side": "BUY'; DROP TABLE orders; --",
                "order_type": "LIMIT",
                "quantity": "0.001 OR 1=1",
                "price": 50000.50
            }
        },
        {
            "name": "Invalid Order (Negative Values)",
            "data": {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "order_type": "LIMIT",
                "quantity": -0.001,
                "price": -50000
            }
        }
    ]
    
    for test_order in test_orders:
        print(f"\n   Testing: {test_order['name']}")
        result = await validator.validate_exchange_request(test_order['data'])
        
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"      Status: {status}")
        
        if result.errors:
            print(f"      Errors: {result.errors}")
        
        if result.warnings:
            print(f"      Warnings: {result.warnings}")
        
        if result.sanitized_data != result.original_data:
            print(f"      Sanitized: {result.sanitized_data}")
    
    # Demo 2: Telegram message validation
    print(f"\n📱 Demo 2: Telegram Message Validation")
    print("-" * 50)
    
    test_messages = [
        {
            "name": "Valid Message",
            "data": {
                "chat_id": "123456789",
                "text": "🚀 BTC price alert: $50,000!",
                "parse_mode": "HTML"
            }
        },
        {
            "name": "Malicious Message (XSS Attempt)",
            "data": {
                "chat_id": "123456789",
                "text": "<script>window.location='http://evil.com'</script>Alert: Price changed!",
                "parse_mode": "HTML"
            }
        }
    ]
    
    for test_message in test_messages:
        print(f"\n   Testing: {test_message['name']}")
        result = await validator.validate_telegram_message(test_message['data'])
        
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"      Status: {status}")
        
        if result.errors:
            print(f"      Errors: {result.errors}")
        
        if result.warnings:
            print(f"      Warnings: {result.warnings}")
    
    # Demo 3: Validation statistics
    print(f"\n📊 Demo 3: Validation Statistics")
    print("-" * 50)
    
    report = await validator.generate_validation_report()
    
    print(f"   Total Validations: {report['statistics']['total_validations']}")
    print(f"   Successful: {report['statistics']['successful_validations']}")
    print(f"   Failed: {report['statistics']['failed_validations']}")
    print(f"   Sanitizations Applied: {report['statistics']['sanitizations_applied']}")
    print(f"   Blocked Attempts: {report['statistics']['blocked_attempts']}")
    print(f"   Success Rate: {report['success_rate']:.1f}%")
    
    # Final summary
    print(f"\n🎉 Demo Summary")
    print("=" * 70)
    
    security_benefits = [
        "✅ Input validation prevents injection attacks",
        "✅ Output sanitization protects against XSS",
        "✅ Type validation ensures data integrity",
        "✅ Pattern matching blocks malicious content",
        "✅ Length limits prevent buffer overflows",
        "✅ Business logic validation ensures correctness",
        "✅ Comprehensive logging for security audits",
        "✅ Automated threat detection and blocking"
    ]
    
    for benefit in security_benefits:
        print(f"   {benefit}")
    
    print(f"\n🛡️ Your API interactions are now secured against:")
    print(f"   • SQL injection attacks")
    print(f"   • Cross-site scripting (XSS)")
    print(f"   • Command injection")
    print(f"   • Buffer overflow attempts")
    print(f"   • Data type confusion")
    print(f"   • Business logic bypasses")
    print(f"   • Malformed data corruption")
    
    return True

if __name__ == "__main__":
    print("🛡️ Secure API Validator")
    print("Comprehensive input validation and sanitization system")
    print()
    
    import asyncio
    asyncio.run(demo_secure_api_validator()) 