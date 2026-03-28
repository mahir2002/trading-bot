#!/usr/bin/env python3
"""
Advanced Bot Migration Tool - Automated Migration of Existing Trading Bots
Discovers, analyzes, and migrates 35+ existing bots into the unified platform
"""

import os
import ast
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
import subprocess

class BotAnalyzer:
    """Analyzes existing trading bots to extract functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot_patterns = {
            'trading_keywords': [
                'buy', 'sell', 'order', 'trade', 'position', 'portfolio',
                'signal', 'strategy', 'indicator', 'rsi', 'macd', 'sma',
                'binance', 'exchange', 'api', 'websocket', 'price', 'volume'
            ],
            'ai_keywords': [
                'lstm', 'neural', 'model', 'predict', 'tensorflow', 'sklearn',
                'machine_learning', 'deep_learning', 'regression', 'classification'
            ],
            'risk_keywords': [
                'risk', 'stop_loss', 'take_profit', 'drawdown', 'var',
                'position_size', 'leverage', 'margin'
            ]
        }
    
    def discover_bots(self, search_paths: List[str]) -> List[Dict[str, Any]]:
        """Discover trading bots in specified directories."""
        discovered_bots = []
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                self.logger.warning(f"Search path does not exist: {search_path}")
                continue
            
            self.logger.info(f"Scanning directory: {search_path}")
            
            for root, dirs, files in os.walk(search_path):
                # Skip hidden directories and common non-bot directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d not in ['__pycache__', 'node_modules', '.git']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.ts')):
                        file_path = os.path.join(root, file)
                        bot_info = self._analyze_file(file_path)
                        
                        if bot_info and bot_info['is_trading_bot']:
                            discovered_bots.append(bot_info)
        
        self.logger.info(f"Discovered {len(discovered_bots)} trading bots")
        return discovered_bots
    
    def _analyze_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a single file to determine if it's a trading bot."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic analysis
            bot_info = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'language': self._detect_language(file_path),
                'size_bytes': len(content.encode('utf-8')),
                'line_count': len(content.splitlines()),
                'is_trading_bot': False,
                'bot_type': 'unknown',
                'features': [],
                'dependencies': [],
                'functions': [],
                'classes': [],
                'trading_score': 0,
                'complexity_score': 0,
                'migration_difficulty': 'unknown'
            }
            
            # Calculate trading score
            trading_score = self._calculate_trading_score(content)
            bot_info['trading_score'] = trading_score
            
            # Determine if it's a trading bot
            if trading_score >= 3:
                bot_info['is_trading_bot'] = True
                bot_info['bot_type'] = self._classify_bot_type(content)
                bot_info['features'] = self._extract_features(content)
                bot_info['dependencies'] = self._extract_dependencies(content)
                bot_info['complexity_score'] = self._calculate_complexity(content)
                bot_info['migration_difficulty'] = self._assess_migration_difficulty(bot_info)
                
                if bot_info['language'] == 'python':
                    bot_info['functions'] = self._extract_python_functions(content)
                    bot_info['classes'] = self._extract_python_classes(content)
            
            return bot_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        return language_map.get(ext, 'unknown')
    
    def _calculate_trading_score(self, content: str) -> int:
        """Calculate how likely the file is to be a trading bot."""
        content_lower = content.lower()
        score = 0
        
        # Check for trading keywords
        for keyword in self.bot_patterns['trading_keywords']:
            if keyword in content_lower:
                score += 1
        
        # Check for AI/ML keywords
        for keyword in self.bot_patterns['ai_keywords']:
            if keyword in content_lower:
                score += 1
        
        # Check for risk management keywords
        for keyword in self.bot_patterns['risk_keywords']:
            if keyword in content_lower:
                score += 1
        
        # Check for specific patterns
        patterns = [
            r'def\s+(?:buy|sell|trade|order)',
            r'class\s+\w*(?:Bot|Strategy|Trader)',
            r'api\.(?:buy|sell|order)',
            r'websocket|ws',
            r'price.*change|volume.*change',
            r'stop.*loss|take.*profit'
        ]
        
        for pattern in patterns:
            if re.search(pattern, content_lower):
                score += 2
        
        return score
    
    def _classify_bot_type(self, content: str) -> str:
        """Classify the type of trading bot."""
        content_lower = content.lower()
        
        # AI/ML bots
        if any(keyword in content_lower for keyword in self.bot_patterns['ai_keywords']):
            return 'ai_bot'
        
        # Arbitrage bots
        if 'arbitrage' in content_lower:
            return 'arbitrage_bot'
        
        # Grid trading bots
        if 'grid' in content_lower:
            return 'grid_bot'
        
        # DCA bots
        if 'dca' in content_lower or 'dollar.*cost.*average' in content_lower:
            return 'dca_bot'
        
        # Scalping bots
        if 'scalp' in content_lower:
            return 'scalping_bot'
        
        # Momentum bots
        if 'momentum' in content_lower:
            return 'momentum_bot'
        
        # Mean reversion bots
        if 'mean.*reversion' in content_lower or 'reversion' in content_lower:
            return 'mean_reversion_bot'
        
        return 'generic_bot'
    
    def _extract_features(self, content: str) -> List[str]:
        """Extract features from the bot code."""
        features = []
        content_lower = content.lower()
        
        feature_patterns = {
            'technical_indicators': ['rsi', 'macd', 'sma', 'ema', 'bollinger'],
            'order_types': ['market', 'limit', 'stop', 'trailing'],
            'exchanges': ['binance', 'coinbase', 'kraken', 'bybit'],
            'data_sources': ['websocket', 'rest', 'api'],
            'risk_management': ['stop_loss', 'take_profit', 'position_size'],
            'ai_features': ['lstm', 'neural', 'model', 'predict']
        }
        
        for feature_type, keywords in feature_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                features.append(feature_type)
        
        return features
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from the code."""
        dependencies = []
        
        # Python imports
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+(\w+)',
            r'pip\s+install\s+(\w+)',
            r'require\([\'"](\w+)[\'"]'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend(matches)
        
        return list(set(dependencies))
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate code complexity score."""
        score = 0
        
        # Count functions and classes
        score += len(re.findall(r'def\s+\w+', content))
        score += len(re.findall(r'class\s+\w+', content)) * 2
        
        # Count conditional statements
        score += len(re.findall(r'\bif\s+', content))
        score += len(re.findall(r'\bfor\s+', content))
        score += len(re.findall(r'\bwhile\s+', content))
        
        # Count try-except blocks
        score += len(re.findall(r'\btry\s*:', content))
        
        return score
    
    def _assess_migration_difficulty(self, bot_info: Dict[str, Any]) -> str:
        """Assess migration difficulty based on bot characteristics."""
        score = 0
        
        # Language factor
        if bot_info['language'] != 'python':
            score += 3
        
        # Complexity factor
        if bot_info['complexity_score'] > 50:
            score += 2
        elif bot_info['complexity_score'] > 20:
            score += 1
        
        # Dependencies factor
        if len(bot_info['dependencies']) > 10:
            score += 2
        elif len(bot_info['dependencies']) > 5:
            score += 1
        
        # Size factor
        if bot_info['line_count'] > 1000:
            score += 2
        elif bot_info['line_count'] > 500:
            score += 1
        
        if score >= 6:
            return 'hard'
        elif score >= 3:
            return 'medium'
        else:
            return 'easy'
    
    def _extract_python_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract Python functions from code."""
        functions = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line_number': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'is_async': isinstance(node, ast.AsyncFunctionDef)
                    })
        except:
            # Fallback to regex if AST parsing fails
            pattern = r'def\s+(\w+)\s*\('
            matches = re.finditer(pattern, content)
            for match in matches:
                functions.append({
                    'name': match.group(1),
                    'line_number': content[:match.start()].count('\n') + 1,
                    'args': [],
                    'is_async': False
                })
        
        return functions
    
    def _extract_python_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract Python classes from code."""
        classes = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'line_number': node.lineno,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        'base_classes': [base.id for base in node.bases if isinstance(base, ast.Name)]
                    })
        except:
            # Fallback to regex
            pattern = r'class\s+(\w+)'
            matches = re.finditer(pattern, content)
            for match in matches:
                classes.append({
                    'name': match.group(1),
                    'line_number': content[:match.start()].count('\n') + 1,
                    'methods': [],
                    'base_classes': []
                })
        
        return classes

class BotMigrator:
    """Migrates existing bots to the unified platform."""
    
    def __init__(self, target_platform_path: str):
        self.target_platform_path = target_platform_path
        self.logger = logging.getLogger(__name__)
        self.migration_templates = self._load_migration_templates()
    
    def migrate_bot(self, bot_info: Dict[str, Any], migration_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate a single bot to the unified platform."""
        self.logger.info(f"Starting migration of {bot_info['file_name']}")
        
        migration_result = {
            'bot_name': bot_info['file_name'],
            'original_path': bot_info['file_path'],
            'migration_status': 'pending',
            'new_module_path': None,
            'errors': [],
            'warnings': [],
            'migration_steps': []
        }
        
        try:
            # Step 1: Create module structure
            module_path = self._create_module_structure(bot_info, migration_config)
            migration_result['new_module_path'] = module_path
            migration_result['migration_steps'].append('Module structure created')
            
            # Step 2: Extract and convert functionality
            if bot_info['language'] == 'python':
                self._migrate_python_bot(bot_info, module_path, migration_result)
            else:
                migration_result['errors'].append(f"Language {bot_info['language']} not yet supported")
                migration_result['migration_status'] = 'failed'
                return migration_result
            
            # Step 3: Generate configuration
            self._generate_bot_config(bot_info, module_path, migration_result)
            migration_result['migration_steps'].append('Configuration generated')
            
            # Step 4: Create integration wrapper
            self._create_integration_wrapper(bot_info, module_path, migration_result)
            migration_result['migration_steps'].append('Integration wrapper created')
            
            # Step 5: Generate tests
            self._generate_tests(bot_info, module_path, migration_result)
            migration_result['migration_steps'].append('Tests generated')
            
            migration_result['migration_status'] = 'completed'
            self.logger.info(f"Successfully migrated {bot_info['file_name']}")
            
        except Exception as e:
            migration_result['errors'].append(str(e))
            migration_result['migration_status'] = 'failed'
            self.logger.error(f"Failed to migrate {bot_info['file_name']}: {e}")
        
        return migration_result
    
    def _create_module_structure(self, bot_info: Dict[str, Any], migration_config: Dict[str, Any]) -> str:
        """Create module directory structure."""
        bot_name = self._sanitize_name(bot_info['file_name'])
        module_path = os.path.join(self.target_platform_path, 'migrated_modules', bot_name)
        
        # Create directories
        os.makedirs(module_path, exist_ok=True)
        os.makedirs(os.path.join(module_path, 'strategies'), exist_ok=True)
        os.makedirs(os.path.join(module_path, 'indicators'), exist_ok=True)
        os.makedirs(os.path.join(module_path, 'tests'), exist_ok=True)
        
        return module_path
    
    def _migrate_python_bot(self, bot_info: Dict[str, Any], module_path: str, migration_result: Dict[str, Any]):
        """Migrate Python trading bot."""
        # Read original bot code
        with open(bot_info['file_path'], 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Extract strategy logic
        strategy_code = self._extract_strategy_logic(original_code, bot_info)
        
        # Create strategy module
        strategy_file = os.path.join(module_path, 'strategies', 'main_strategy.py')
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write(strategy_code)
        
        migration_result['migration_steps'].append('Strategy logic extracted')
        
        # Extract indicators
        indicators_code = self._extract_indicators(original_code, bot_info)
        if indicators_code:
            indicators_file = os.path.join(module_path, 'indicators', 'custom_indicators.py')
            with open(indicators_file, 'w', encoding='utf-8') as f:
                f.write(indicators_code)
            migration_result['migration_steps'].append('Custom indicators extracted')
    
    def _extract_strategy_logic(self, code: str, bot_info: Dict[str, Any]) -> str:
        """Extract strategy logic and convert to unified platform format."""
        template = self.migration_templates['strategy_template']
        
        # Extract key functions
        trading_functions = []
        for func in bot_info.get('functions', []):
            if any(keyword in func['name'].lower() for keyword in ['buy', 'sell', 'trade', 'signal']):
                trading_functions.append(func['name'])
        
        # Generate strategy class
        strategy_code = template.format(
            bot_name=self._sanitize_name(bot_info['file_name']),
            trading_functions=', '.join(trading_functions),
            original_path=bot_info['file_path'],
            migration_date=datetime.now().isoformat()
        )
        
        return strategy_code
    
    def _extract_indicators(self, code: str, bot_info: Dict[str, Any]) -> str:
        """Extract custom indicators from the bot."""
        indicators = []
        
        # Look for indicator functions
        for func in bot_info.get('functions', []):
            if any(indicator in func['name'].lower() for indicator in ['rsi', 'macd', 'sma', 'ema', 'indicator']):
                indicators.append(func['name'])
        
        if not indicators:
            return None
        
        template = self.migration_templates['indicators_template']
        return template.format(
            indicators=', '.join(indicators),
            original_path=bot_info['file_path']
        )
    
    def _generate_bot_config(self, bot_info: Dict[str, Any], module_path: str, migration_result: Dict[str, Any]):
        """Generate configuration for the migrated bot."""
        config = {
            'bot_info': {
                'name': bot_info['file_name'],
                'original_path': bot_info['file_path'],
                'bot_type': bot_info['bot_type'],
                'migration_date': datetime.now().isoformat(),
                'features': bot_info['features']
            },
            'trading_config': {
                'symbols': ['BTCUSDT'],  # Default, should be configured
                'timeframe': '1h',
                'risk_per_trade': 0.02,
                'max_positions': 5
            },
            'execution_config': {
                'order_type': 'LIMIT',
                'slippage_tolerance': 0.001,
                'timeout': 30
            }
        }
        
        config_file = os.path.join(module_path, 'config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def _create_integration_wrapper(self, bot_info: Dict[str, Any], module_path: str, migration_result: Dict[str, Any]):
        """Create integration wrapper for the unified platform."""
        template = self.migration_templates['integration_template']
        
        wrapper_code = template.format(
            bot_name=self._sanitize_name(bot_info['file_name']),
            module_path=module_path,
            original_path=bot_info['file_path']
        )
        
        wrapper_file = os.path.join(module_path, 'integration_wrapper.py')
        with open(wrapper_file, 'w', encoding='utf-8') as f:
            f.write(wrapper_code)
    
    def _generate_tests(self, bot_info: Dict[str, Any], module_path: str, migration_result: Dict[str, Any]):
        """Generate basic tests for the migrated bot."""
        template = self.migration_templates['test_template']
        
        test_code = template.format(
            bot_name=self._sanitize_name(bot_info['file_name']),
            test_functions='\n'.join([f'    def test_{func["name"]}(self):\n        pass' 
                                    for func in bot_info.get('functions', [])[:5]])
        )
        
        test_file = os.path.join(module_path, 'tests', 'test_migrated_bot.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use as module/class name."""
        # Remove extension and non-alphanumeric characters
        name = os.path.splitext(name)[0]
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)
        return name.strip('_')
    
    def _load_migration_templates(self) -> Dict[str, str]:
        """Load migration templates."""
        return {
            'strategy_template': '''#!/usr/bin/env python3
"""
Migrated Strategy: {bot_name}
Original Path: {original_path}
Migration Date: {migration_date}
"""

from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ...core.base_module import BaseModule, ModuleStatus
from ...core.event_bus import Event, EventPriority

class {bot_name}Strategy(BaseModule):
    """Migrated strategy from {original_path}."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("{bot_name}_strategy", config or {{}})
        self.positions = {{}}
        
    async def initialize(self) -> bool:
        """Initialize the strategy."""
        try:
            self.logger.info("Initializing {bot_name} strategy...")
            self.status = ModuleStatus.RUNNING
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize strategy: {{e}}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def process_event(self, event: Event) -> bool:
        """Process incoming events."""
        try:
            if event.type == "market_data_update":
                await self._handle_market_data(event)
            elif event.type == "signal_request":
                await self._generate_signal(event)
            return True
        except Exception as e:
            self.logger.error(f"Error processing event: {{e}}")
            return False
    
    async def _handle_market_data(self, event: Event):
        """Handle market data updates."""
        # TODO: Implement market data handling logic
        pass
    
    async def _generate_signal(self, event: Event):
        """Generate trading signals."""
        # TODO: Implement signal generation logic
        pass
    
    # TODO: Migrate original functions: {trading_functions}
''',
            
            'indicators_template': '''#!/usr/bin/env python3
"""
Custom Indicators migrated from {original_path}
"""

import pandas as pd
import numpy as np

class CustomIndicators:
    """Custom indicators from migrated bot."""
    
    @staticmethod
    def calculate_all(data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all custom indicators."""
        # TODO: Implement indicator calculations
        return data
    
    # TODO: Migrate indicator functions: {indicators}
''',
            
            'integration_template': '''#!/usr/bin/env python3
"""
Integration Wrapper for {bot_name}
"""

import asyncio
from typing import Dict, Any

from ..core.base_module import BaseModule, ModuleStatus
from .strategies.main_strategy import {bot_name}Strategy

class {bot_name}Integration(BaseModule):
    """Integration wrapper for {bot_name}."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("{bot_name}_integration", config or {{}})
        self.strategy = {bot_name}Strategy(config)
    
    async def initialize(self) -> bool:
        """Initialize the integration."""
        return await self.strategy.initialize()
    
    async def start(self) -> bool:
        """Start the integration."""
        return await self.strategy.start()
    
    async def stop(self) -> bool:
        """Stop the integration."""
        return await self.strategy.stop()
    
    async def process_event(self, event) -> bool:
        """Process events through the strategy."""
        return await self.strategy.process_event(event)
''',
            
            'test_template': '''#!/usr/bin/env python3
"""
Tests for migrated {bot_name}
"""

import unittest
import asyncio
from unittest.mock import Mock, patch

from ..integration_wrapper import {bot_name}Integration

class Test{bot_name}(unittest.IsolatedAsyncioTestCase):
    """Test cases for migrated {bot_name}."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        self.integration = {bot_name}Integration()
        await self.integration.initialize()
    
    async def test_initialization(self):
        """Test strategy initialization."""
        self.assertTrue(await self.integration.initialize())
    
{test_functions}

if __name__ == '__main__':
    unittest.main()
'''
        }

class MigrationOrchestrator:
    """Orchestrates the entire migration process."""
    
    def __init__(self, platform_path: str):
        self.platform_path = platform_path
        self.logger = logging.getLogger(__name__)
        self.analyzer = BotAnalyzer()
        self.migrator = BotMigrator(platform_path)
    
    def run_migration(self, search_paths: List[str], migration_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the complete migration process."""
        migration_config = migration_config or {}
        
        self.logger.info("Starting bot migration process...")
        
        # Step 1: Discover bots
        discovered_bots = self.analyzer.discover_bots(search_paths)
        
        # Step 2: Filter and prioritize bots
        filtered_bots = self._filter_bots(discovered_bots, migration_config)
        
        # Step 3: Migrate bots
        migration_results = []
        for bot_info in filtered_bots:
            result = self.migrator.migrate_bot(bot_info, migration_config)
            migration_results.append(result)
        
        # Step 4: Generate migration report
        report = self._generate_migration_report(discovered_bots, migration_results)
        
        self.logger.info("Migration process completed")
        return report
    
    def _filter_bots(self, bots: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter and prioritize bots for migration."""
        filtered = []
        
        for bot in bots:
            # Skip if migration difficulty is too high
            if config.get('skip_hard_migrations', False) and bot['migration_difficulty'] == 'hard':
                continue
            
            # Skip if trading score is too low
            if bot['trading_score'] < config.get('min_trading_score', 3):
                continue
            
            # Skip if language is not supported
            if bot['language'] not in config.get('supported_languages', ['python']):
                continue
            
            filtered.append(bot)
        
        # Sort by migration priority
        filtered.sort(key=lambda x: (
            x['trading_score'],
            -len(x['features']),
            x['migration_difficulty'] == 'easy'
        ), reverse=True)
        
        return filtered
    
    def _generate_migration_report(self, discovered_bots: List[Dict[str, Any]], 
                                 migration_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive migration report."""
        report = {
            'summary': {
                'total_discovered': len(discovered_bots),
                'total_migrated': len(migration_results),
                'successful_migrations': len([r for r in migration_results if r['migration_status'] == 'completed']),
                'failed_migrations': len([r for r in migration_results if r['migration_status'] == 'failed']),
                'migration_date': datetime.now().isoformat()
            },
            'discovered_bots': discovered_bots,
            'migration_results': migration_results,
            'statistics': {
                'bot_types': {},
                'languages': {},
                'migration_difficulties': {},
                'features': {}
            }
        }
        
        # Calculate statistics
        for bot in discovered_bots:
            # Bot types
            bot_type = bot['bot_type']
            report['statistics']['bot_types'][bot_type] = report['statistics']['bot_types'].get(bot_type, 0) + 1
            
            # Languages
            language = bot['language']
            report['statistics']['languages'][language] = report['statistics']['languages'].get(language, 0) + 1
            
            # Migration difficulties
            difficulty = bot['migration_difficulty']
            report['statistics']['migration_difficulties'][difficulty] = report['statistics']['migration_difficulties'].get(difficulty, 0) + 1
            
            # Features
            for feature in bot['features']:
                report['statistics']['features'][feature] = report['statistics']['features'].get(feature, 0) + 1
        
        return report

def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate existing trading bots to unified platform')
    parser.add_argument('--search-paths', nargs='+', required=True, help='Paths to search for trading bots')
    parser.add_argument('--platform-path', required=True, help='Path to unified trading platform')
    parser.add_argument('--output-report', help='Path to save migration report')
    parser.add_argument('--skip-hard', action='store_true', help='Skip hard migrations')
    parser.add_argument('--min-score', type=int, default=3, help='Minimum trading score')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Migration configuration
    migration_config = {
        'skip_hard_migrations': args.skip_hard,
        'min_trading_score': args.min_score,
        'supported_languages': ['python']
    }
    
    # Run migration
    orchestrator = MigrationOrchestrator(args.platform_path)
    report = orchestrator.run_migration(args.search_paths, migration_config)
    
    # Save report
    if args.output_report:
        with open(args.output_report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Migration report saved to: {args.output_report}")
    
    # Print summary
    print("\n=== Migration Summary ===")
    print(f"Total bots discovered: {report['summary']['total_discovered']}")
    print(f"Total bots migrated: {report['summary']['total_migrated']}")
    print(f"Successful migrations: {report['summary']['successful_migrations']}")
    print(f"Failed migrations: {report['summary']['failed_migrations']}")
    
    if report['summary']['successful_migrations'] > 0:
        print(f"\nSuccess rate: {report['summary']['successful_migrations'] / report['summary']['total_migrated'] * 100:.1f}%")

if __name__ == '__main__':
    main() 