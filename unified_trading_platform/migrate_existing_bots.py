#!/usr/bin/env python3
"""
🔄 Bot Migration Tool
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

def scan_for_bots(directory: str) -> List[str]:
    """Scan directory for Python files that might be trading bots"""
    bot_files = []
    scan_dir = Path(directory)
    
    if not scan_dir.exists():
        return bot_files
    
    patterns = ['*bot*.py', '*trading*.py', '*crypto*.py']
    
    for pattern in patterns:
        for file_path in scan_dir.rglob(pattern):
            if file_path.is_file() and not file_path.name.startswith('__'):
                bot_files.append(str(file_path))
    
    return bot_files

def create_migration_config(bot_files: List[str]) -> Dict[str, Any]:
    """Create a migration configuration"""
    config = {
        'platform': {
            'name': 'Migrated Trading Platform',
            'version': '1.0.0',
            'environment': 'development',
            'log_level': 'INFO'
        },
        'modules': {
            'market_data': {
                'enabled': True,
                'priority': 1,
                'config': {
                    'symbols': ['BTC/USDT', 'ETH/USDT'],
                    'update_interval': 1,
                    'data_sources': ['binance']
                }
            }
        },
        'critical_modules': ['market_data'],
        'restart_policy': 'automatic',
        'migration': {
            'original_bots': bot_files,
            'migration_date': '2024-01-01',
            'notes': 'Migrated from existing bot files'
        }
    }
    
    return config

def main():
    """Main migration function"""
    print("🔄 Bot Migration Tool")
    print("=====================")
    
    # Get scan directory
    scan_dir = input("Enter directory to scan for bots (default: .): ").strip()
    if not scan_dir:
        scan_dir = "."
    
    # Scan for bots
    print(f"🔍 Scanning {scan_dir} for trading bots...")
    bots = scan_for_bots(scan_dir)
    
    if not bots:
        print("❌ No trading bots found")
        return
    
    print(f"✅ Found {len(bots)} potential trading bots:")
    for bot in bots:
        print(f"   • {bot}")
    
    # Create config
    print("\n⚙️ Creating migration configuration...")
    config = create_migration_config(bots)
    
    # Save config
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / "migrated_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print(f"📁 Configuration saved to: {config_path}")
    print("\n🚀 Next steps:")
    print("1. Review the generated configuration")
    print("2. Start the unified platform with:")
    print(f"   python -m unified_trading_platform.main --config {config_path}")
    print("3. Begin migrating your bot functionality to modules")

if __name__ == "__main__":
    main() 