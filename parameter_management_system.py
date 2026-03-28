#!/usr/bin/env python3
"""
⚙️ Parameter Management System
Advanced system for managing and validating trading bot parameters
with real-time updates and configuration persistence.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from pathlib import Path
import pandas as pd
import numpy as np
from enum import Enum

class ParameterCategory(Enum):
    """Parameter categories for organization"""
    TRADING_PAIRS = "trading_pairs"
    TIMEFRAMES = "timeframes"
    RISK_MANAGEMENT = "risk_management"
    AI_ML = "ai_ml"
    TECHNICAL_INDICATORS = "technical_indicators"
    PORTFOLIO = "portfolio"
    NOTIFICATIONS = "notifications"
    SYSTEM = "system"

@dataclass
class ParameterDefinition:
    """Definition of a configurable parameter"""
    name: str
    category: ParameterCategory
    data_type: str  # 'int', 'float', 'str', 'bool', 'list', 'dict'
    default_value: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    description: str = ""
    validation_rules: List[str] = field(default_factory=list)
    requires_restart: bool = False
    affects_trading: bool = True

@dataclass
class ConfigurationProfile:
    """Trading bot configuration profile"""
    profile_name: str
    description: str
    parameters: Dict[str, Any]
    created_at: datetime
    last_modified: datetime
    is_active: bool = False
    performance_metrics: Dict[str, float] = field(default_factory=dict)

class ParameterValidator:
    """Validates parameter values and configurations"""
    
    def __init__(self):
        self.logger = logging.getLogger('ParameterValidator')
    
    def validate_parameter(self, param_def: ParameterDefinition, value: Any) -> Dict[str, Any]:
        """Validate a single parameter value"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'normalized_value': value
        }
        
        try:
            # Type validation
            if param_def.data_type == 'int':
                value = int(value)
            elif param_def.data_type == 'float':
                value = float(value)
            elif param_def.data_type == 'bool':
                value = bool(value)
            elif param_def.data_type == 'str':
                value = str(value)
            elif param_def.data_type == 'list':
                if not isinstance(value, list):
                    result['errors'].append(f"Expected list, got {type(value)}")
                    result['valid'] = False
            elif param_def.data_type == 'dict':
                if not isinstance(value, dict):
                    result['errors'].append(f"Expected dict, got {type(value)}")
                    result['valid'] = False
            
            result['normalized_value'] = value
            
            # Range validation
            if param_def.min_value is not None and value < param_def.min_value:
                result['errors'].append(f"Value {value} below minimum {param_def.min_value}")
                result['valid'] = False
            
            if param_def.max_value is not None and value > param_def.max_value:
                result['errors'].append(f"Value {value} above maximum {param_def.max_value}")
                result['valid'] = False
            
            # Allowed values validation
            if param_def.allowed_values and value not in param_def.allowed_values:
                result['errors'].append(f"Value {value} not in allowed values: {param_def.allowed_values}")
                result['valid'] = False
            
            # Custom validation rules
            for rule in param_def.validation_rules:
                rule_result = self._apply_validation_rule(rule, value, param_def)
                if not rule_result['valid']:
                    result['errors'].extend(rule_result['errors'])
                    result['warnings'].extend(rule_result['warnings'])
                    result['valid'] = False
            
        except (ValueError, TypeError) as e:
            result['errors'].append(f"Type conversion error: {str(e)}")
            result['valid'] = False
        
        return result
    
    def _apply_validation_rule(self, rule: str, value: Any, param_def: ParameterDefinition) -> Dict[str, Any]:
        """Apply custom validation rule"""
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        if rule == 'positive':
            if value <= 0:
                result['errors'].append("Value must be positive")
                result['valid'] = False
        
        elif rule == 'percentage':
            if not (0 <= value <= 1):
                result['errors'].append("Percentage must be between 0 and 1")
                result['valid'] = False
        
        elif rule == 'trading_pair_format':
            if not isinstance(value, str) or not value.endswith('USDT'):
                result['errors'].append("Trading pair must end with 'USDT'")
                result['valid'] = False
        
        elif rule == 'timeframe_format':
            valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
            if value not in valid_timeframes:
                result['errors'].append(f"Invalid timeframe. Must be one of: {valid_timeframes}")
                result['valid'] = False
        
        elif rule == 'risk_reward_ratio':
            if value < 1.0:
                result['warnings'].append("Risk-reward ratio below 1.0 may not be profitable")
        
        return result
    
    def validate_configuration(self, config: Dict[str, Any], param_definitions: Dict[str, ParameterDefinition]) -> Dict[str, Any]:
        """Validate entire configuration"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'parameter_results': {}
        }
        
        # Validate individual parameters
        for param_name, param_def in param_definitions.items():
            if param_name in config:
                param_result = self.validate_parameter(param_def, config[param_name])
                result['parameter_results'][param_name] = param_result
                
                if not param_result['valid']:
                    result['valid'] = False
                    result['errors'].extend([f"{param_name}: {error}" for error in param_result['errors']])
                
                result['warnings'].extend([f"{param_name}: {warning}" for warning in param_result['warnings']])
        
        # Cross-parameter validation
        cross_validation = self._validate_parameter_relationships(config)
        result['errors'].extend(cross_validation['errors'])
        result['warnings'].extend(cross_validation['warnings'])
        if cross_validation['errors']:
            result['valid'] = False
        
        return result
    
    def _validate_parameter_relationships(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate relationships between parameters"""
        result = {'errors': [], 'warnings': []}
        
        # Stop loss vs take profit validation
        stop_loss = config.get('stop_loss_percentage', 0)
        take_profit = config.get('take_profit_percentage', 0)
        
        if stop_loss > 0 and take_profit > 0:
            risk_reward = take_profit / stop_loss
            if risk_reward < 1.5:
                result['warnings'].append(f"Risk-reward ratio {risk_reward:.2f} is below recommended 1.5")
        
        # Position size vs max drawdown validation
        max_position = config.get('max_position_size', 0)
        max_drawdown = config.get('max_drawdown', 0)
        
        if max_position > max_drawdown / 2:
            result['warnings'].append("Position size should be less than half of max drawdown tolerance")
        
        # Trading pairs vs max pairs validation
        active_pairs = config.get('active_pairs', [])
        max_pairs = config.get('max_pairs', 10)
        
        if len(active_pairs) > max_pairs:
            result['errors'].append(f"Active pairs ({len(active_pairs)}) exceeds maximum ({max_pairs})")
        
        return result

class ParameterManager:
    """Manages trading bot parameters and configurations"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logger()
        self.validator = ParameterValidator()
        
        # Parameter definitions
        self.parameter_definitions = self._initialize_parameter_definitions()
        
        # Configuration profiles
        self.profiles: Dict[str, ConfigurationProfile] = {}
        self.active_profile: Optional[str] = None
        
        # Load existing configurations
        self._load_configurations()
        
        self.logger.info("⚙️ Parameter Manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for parameter manager"""
        logger = logging.getLogger('ParameterManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_parameter_definitions(self) -> Dict[str, ParameterDefinition]:
        """Initialize parameter definitions"""
        
        definitions = {}
        
        # Trading Pairs Parameters
        definitions['active_pairs'] = ParameterDefinition(
            name='active_pairs',
            category=ParameterCategory.TRADING_PAIRS,
            data_type='list',
            default_value=['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
            description='List of active trading pairs',
            validation_rules=['trading_pair_format'],
            affects_trading=True
        )
        
        definitions['max_pairs'] = ParameterDefinition(
            name='max_pairs',
            category=ParameterCategory.TRADING_PAIRS,
            data_type='int',
            default_value=10,
            min_value=1,
            max_value=50,
            description='Maximum number of trading pairs',
            affects_trading=True
        )
        
        # Timeframe Parameters
        definitions['primary_timeframe'] = ParameterDefinition(
            name='primary_timeframe',
            category=ParameterCategory.TIMEFRAMES,
            data_type='str',
            default_value='1h',
            allowed_values=['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'],
            description='Primary analysis timeframe',
            validation_rules=['timeframe_format'],
            affects_trading=True
        )
        
        definitions['secondary_timeframes'] = ParameterDefinition(
            name='secondary_timeframes',
            category=ParameterCategory.TIMEFRAMES,
            data_type='list',
            default_value=['15m', '4h'],
            description='Secondary confirmation timeframes',
            affects_trading=True
        )
        
        # Risk Management Parameters
        definitions['max_position_size'] = ParameterDefinition(
            name='max_position_size',
            category=ParameterCategory.RISK_MANAGEMENT,
            data_type='float',
            default_value=0.1,
            min_value=0.01,
            max_value=0.5,
            description='Maximum position size as percentage of portfolio',
            validation_rules=['percentage'],
            affects_trading=True
        )
        
        definitions['stop_loss_percentage'] = ParameterDefinition(
            name='stop_loss_percentage',
            category=ParameterCategory.RISK_MANAGEMENT,
            data_type='float',
            default_value=0.05,
            min_value=0.01,
            max_value=0.2,
            description='Stop loss percentage',
            validation_rules=['percentage'],
            affects_trading=True
        )
        
        definitions['take_profit_percentage'] = ParameterDefinition(
            name='take_profit_percentage',
            category=ParameterCategory.RISK_MANAGEMENT,
            data_type='float',
            default_value=0.15,
            min_value=0.02,
            max_value=0.5,
            description='Take profit percentage',
            validation_rules=['percentage'],
            affects_trading=True
        )
        
        definitions['max_daily_trades'] = ParameterDefinition(
            name='max_daily_trades',
            category=ParameterCategory.RISK_MANAGEMENT,
            data_type='int',
            default_value=20,
            min_value=1,
            max_value=100,
            description='Maximum trades per day',
            affects_trading=True
        )
        
        definitions['max_drawdown'] = ParameterDefinition(
            name='max_drawdown',
            category=ParameterCategory.RISK_MANAGEMENT,
            data_type='float',
            default_value=0.2,
            min_value=0.05,
            max_value=0.5,
            description='Maximum portfolio drawdown',
            validation_rules=['percentage'],
            affects_trading=True
        )
        
        # AI/ML Parameters
        definitions['confidence_threshold'] = ParameterDefinition(
            name='confidence_threshold',
            category=ParameterCategory.AI_ML,
            data_type='float',
            default_value=0.75,
            min_value=0.5,
            max_value=0.95,
            description='Minimum confidence for trade signals',
            validation_rules=['percentage'],
            affects_trading=True
        )
        
        definitions['model_retrain_interval'] = ParameterDefinition(
            name='model_retrain_interval',
            category=ParameterCategory.AI_ML,
            data_type='int',
            default_value=24,
            min_value=1,
            max_value=168,
            description='Model retraining interval in hours',
            requires_restart=True
        )
        
        definitions['prediction_lookback'] = ParameterDefinition(
            name='prediction_lookback',
            category=ParameterCategory.AI_ML,
            data_type='int',
            default_value=100,
            min_value=50,
            max_value=500,
            description='Historical data points for prediction',
            affects_trading=True
        )
        
        # Portfolio Parameters
        definitions['portfolio_balance'] = ParameterDefinition(
            name='portfolio_balance',
            category=ParameterCategory.PORTFOLIO,
            data_type='float',
            default_value=100000.0,
            min_value=100.0,
            description='Portfolio balance in USDT',
            validation_rules=['positive'],
            affects_trading=True
        )
        
        definitions['position_sizing_method'] = ParameterDefinition(
            name='position_sizing_method',
            category=ParameterCategory.PORTFOLIO,
            data_type='str',
            default_value='kelly_criterion',
            allowed_values=['fixed_percentage', 'kelly_criterion', 'volatility_adjusted', 'risk_parity'],
            description='Position sizing calculation method',
            affects_trading=True
        )
        
        # Technical Indicators Parameters
        definitions['enabled_indicators'] = ParameterDefinition(
            name='enabled_indicators',
            category=ParameterCategory.TECHNICAL_INDICATORS,
            data_type='list',
            default_value=['sma', 'ema', 'rsi', 'macd'],
            description='List of enabled technical indicators',
            affects_trading=True
        )
        
        definitions['rsi_period'] = ParameterDefinition(
            name='rsi_period',
            category=ParameterCategory.TECHNICAL_INDICATORS,
            data_type='int',
            default_value=14,
            min_value=5,
            max_value=50,
            description='RSI calculation period',
            affects_trading=True
        )
        
        definitions['sma_period'] = ParameterDefinition(
            name='sma_period',
            category=ParameterCategory.TECHNICAL_INDICATORS,
            data_type='int',
            default_value=20,
            min_value=5,
            max_value=200,
            description='SMA calculation period',
            affects_trading=True
        )
        
        # Notification Parameters
        definitions['enable_notifications'] = ParameterDefinition(
            name='enable_notifications',
            category=ParameterCategory.NOTIFICATIONS,
            data_type='bool',
            default_value=True,
            description='Enable trading notifications',
            requires_restart=False
        )
        
        definitions['notification_channels'] = ParameterDefinition(
            name='notification_channels',
            category=ParameterCategory.NOTIFICATIONS,
            data_type='list',
            default_value=['dashboard', 'email'],
            allowed_values=['dashboard', 'email', 'telegram', 'discord', 'slack'],
            description='Enabled notification channels'
        )
        
        return definitions
    
    def create_profile(self, name: str, description: str, parameters: Dict[str, Any]) -> bool:
        """Create new configuration profile"""
        try:
            # Validate parameters
            validation_result = self.validator.validate_configuration(parameters, self.parameter_definitions)
            
            if not validation_result['valid']:
                self.logger.error(f"❌ Invalid parameters for profile {name}: {validation_result['errors']}")
                return False
            
            # Create profile
            profile = ConfigurationProfile(
                profile_name=name,
                description=description,
                parameters=parameters,
                created_at=datetime.now(),
                last_modified=datetime.now()
            )
            
            self.profiles[name] = profile
            self._save_profile(profile)
            
            self.logger.info(f"✅ Created configuration profile: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating profile {name}: {e}")
            return False
    
    def update_parameter(self, param_name: str, value: Any, profile_name: Optional[str] = None) -> bool:
        """Update single parameter"""
        try:
            if profile_name is None:
                profile_name = self.active_profile
            
            if profile_name not in self.profiles:
                self.logger.error(f"❌ Profile {profile_name} not found")
                return False
            
            if param_name not in self.parameter_definitions:
                self.logger.error(f"❌ Parameter {param_name} not defined")
                return False
            
            # Validate parameter
            param_def = self.parameter_definitions[param_name]
            validation_result = self.validator.validate_parameter(param_def, value)
            
            if not validation_result['valid']:
                self.logger.error(f"❌ Invalid value for {param_name}: {validation_result['errors']}")
                return False
            
            # Update parameter
            profile = self.profiles[profile_name]
            profile.parameters[param_name] = validation_result['normalized_value']
            profile.last_modified = datetime.now()
            
            self._save_profile(profile)
            
            self.logger.info(f"✅ Updated parameter {param_name} = {value}")
            
            # Log warnings if any
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    self.logger.warning(f"⚠️ {param_name}: {warning}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating parameter {param_name}: {e}")
            return False
    
    def get_parameter(self, param_name: str, profile_name: Optional[str] = None) -> Any:
        """Get parameter value"""
        if profile_name is None:
            profile_name = self.active_profile
        
        if profile_name not in self.profiles:
            # Return default value if profile not found
            if param_name in self.parameter_definitions:
                return self.parameter_definitions[param_name].default_value
            return None
        
        profile = self.profiles[profile_name]
        return profile.parameters.get(param_name, 
                                    self.parameter_definitions.get(param_name, {}).default_value)
    
    def get_configuration(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get complete configuration"""
        if profile_name is None:
            profile_name = self.active_profile
        
        if profile_name not in self.profiles:
            # Return default configuration
            return {name: param_def.default_value 
                   for name, param_def in self.parameter_definitions.items()}
        
        return self.profiles[profile_name].parameters.copy()
    
    def set_active_profile(self, profile_name: str) -> bool:
        """Set active configuration profile"""
        if profile_name not in self.profiles:
            self.logger.error(f"❌ Profile {profile_name} not found")
            return False
        
        # Deactivate current profile
        if self.active_profile and self.active_profile in self.profiles:
            self.profiles[self.active_profile].is_active = False
        
        # Activate new profile
        self.profiles[profile_name].is_active = True
        self.active_profile = profile_name
        
        self._save_active_profile()
        
        self.logger.info(f"✅ Activated profile: {profile_name}")
        return True
    
    def get_parameters_by_category(self, category: ParameterCategory) -> Dict[str, Any]:
        """Get parameters filtered by category"""
        filtered_params = {}
        config = self.get_configuration()
        
        for param_name, param_def in self.parameter_definitions.items():
            if param_def.category == category:
                filtered_params[param_name] = config.get(param_name, param_def.default_value)
        
        return filtered_params
    
    def export_configuration(self, profile_name: str, file_path: str) -> bool:
        """Export configuration to file"""
        try:
            if profile_name not in self.profiles:
                self.logger.error(f"❌ Profile {profile_name} not found")
                return False
            
            profile = self.profiles[profile_name]
            export_data = {
                'profile_name': profile.profile_name,
                'description': profile.description,
                'parameters': profile.parameters,
                'created_at': profile.created_at.isoformat(),
                'last_modified': profile.last_modified.isoformat(),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"✅ Exported configuration to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, file_path: str) -> bool:
        """Import configuration from file"""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)
            
            profile_name = import_data['profile_name']
            description = import_data['description']
            parameters = import_data['parameters']
            
            return self.create_profile(profile_name, description, parameters)
            
        except Exception as e:
            self.logger.error(f"❌ Error importing configuration: {e}")
            return False
    
    def _load_configurations(self):
        """Load existing configuration profiles"""
        try:
            profiles_dir = self.config_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            # Load profiles
            for profile_file in profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r') as f:
                        profile_data = json.load(f)
                    
                    profile = ConfigurationProfile(
                        profile_name=profile_data['profile_name'],
                        description=profile_data['description'],
                        parameters=profile_data['parameters'],
                        created_at=datetime.fromisoformat(profile_data['created_at']),
                        last_modified=datetime.fromisoformat(profile_data['last_modified']),
                        is_active=profile_data.get('is_active', False)
                    )
                    
                    self.profiles[profile.profile_name] = profile
                    
                    if profile.is_active:
                        self.active_profile = profile.profile_name
                    
                except Exception as e:
                    self.logger.error(f"❌ Error loading profile {profile_file}: {e}")
            
            # Create default profile if none exist
            if not self.profiles:
                self._create_default_profile()
            
            # Set active profile if none set
            if not self.active_profile and self.profiles:
                self.active_profile = list(self.profiles.keys())[0]
                self.profiles[self.active_profile].is_active = True
            
            self.logger.info(f"📁 Loaded {len(self.profiles)} configuration profiles")
            
        except Exception as e:
            self.logger.error(f"❌ Error loading configurations: {e}")
    
    def _create_default_profile(self):
        """Create default configuration profile"""
        default_params = {name: param_def.default_value 
                         for name, param_def in self.parameter_definitions.items()}
        
        self.create_profile(
            name="default",
            description="Default trading bot configuration",
            parameters=default_params
        )
        
        self.set_active_profile("default")
    
    def _save_profile(self, profile: ConfigurationProfile):
        """Save profile to file"""
        try:
            profiles_dir = self.config_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            profile_file = profiles_dir / f"{profile.profile_name}.json"
            
            profile_data = {
                'profile_name': profile.profile_name,
                'description': profile.description,
                'parameters': profile.parameters,
                'created_at': profile.created_at.isoformat(),
                'last_modified': profile.last_modified.isoformat(),
                'is_active': profile.is_active
            }
            
            with open(profile_file, 'w') as f:
                json.dump(profile_data, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"❌ Error saving profile {profile.profile_name}: {e}")
    
    def _save_active_profile(self):
        """Save active profile information"""
        try:
            active_file = self.config_dir / "active_profile.txt"
            with open(active_file, 'w') as f:
                f.write(self.active_profile or "")
        except Exception as e:
            self.logger.error(f"❌ Error saving active profile: {e}")
    
    def get_parameter_definitions(self) -> Dict[str, ParameterDefinition]:
        """Get all parameter definitions"""
        return self.parameter_definitions.copy()
    
    def get_profile_list(self) -> List[Dict[str, Any]]:
        """Get list of all profiles"""
        profile_list = []
        for profile in self.profiles.values():
            profile_list.append({
                'name': profile.profile_name,
                'description': profile.description,
                'created_at': profile.created_at.isoformat(),
                'last_modified': profile.last_modified.isoformat(),
                'is_active': profile.is_active,
                'parameter_count': len(profile.parameters)
            })
        return profile_list

def main():
    """Demonstration of parameter management system"""
    
    print("⚙️ PARAMETER MANAGEMENT SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Initialize parameter manager
    param_manager = ParameterManager()
    
    print(f"📊 Parameter Manager Status:")
    print(f"   • Parameter Definitions: {len(param_manager.parameter_definitions)}")
    print(f"   • Configuration Profiles: {len(param_manager.profiles)}")
    print(f"   • Active Profile: {param_manager.active_profile}")
    
    # Show parameter categories
    print(f"\n📋 Parameter Categories:")
    categories = {}
    for param_name, param_def in param_manager.parameter_definitions.items():
        category = param_def.category.value
        if category not in categories:
            categories[category] = []
        categories[category].append(param_name)
    
    for category, params in categories.items():
        print(f"   • {category}: {len(params)} parameters")
    
    # Demonstrate parameter operations
    print(f"\n🔧 Parameter Operations:")
    
    # Update a parameter
    success = param_manager.update_parameter('confidence_threshold', 0.8)
    print(f"   • Update confidence_threshold: {'✅' if success else '❌'}")
    
    # Get parameter value
    confidence = param_manager.get_parameter('confidence_threshold')
    print(f"   • Current confidence_threshold: {confidence}")
    
    # Create new profile
    new_params = param_manager.get_configuration()
    new_params['max_position_size'] = 0.05  # More conservative
    new_params['stop_loss_percentage'] = 0.03
    
    success = param_manager.create_profile(
        name="conservative",
        description="Conservative trading configuration",
        parameters=new_params
    )
    print(f"   • Create conservative profile: {'✅' if success else '❌'}")
    
    # Show all profiles
    print(f"\n📁 Configuration Profiles:")
    profiles = param_manager.get_profile_list()
    for profile in profiles:
        status = "🟢 ACTIVE" if profile['is_active'] else "⚪ INACTIVE"
        print(f"   • {profile['name']}: {profile['description']} {status}")
        print(f"     Parameters: {profile['parameter_count']}, Modified: {profile['last_modified'][:19]}")
    
    # Demonstrate validation
    print(f"\n✅ Parameter Validation:")
    validator = ParameterValidator()
    
    # Test valid parameter
    param_def = param_manager.parameter_definitions['confidence_threshold']
    result = validator.validate_parameter(param_def, 0.75)
    print(f"   • confidence_threshold = 0.75: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    
    # Test invalid parameter
    result = validator.validate_parameter(param_def, 1.5)
    print(f"   • confidence_threshold = 1.5: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
    if result['errors']:
        print(f"     Errors: {', '.join(result['errors'])}")
    
    print(f"\n🎯 Parameter Management System Ready!")
    print(f"   • Real-time parameter updates")
    print(f"   • Configuration validation")
    print(f"   • Profile management")
    print(f"   • Import/export capabilities")

if __name__ == "__main__":
    main() 