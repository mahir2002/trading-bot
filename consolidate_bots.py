#!/usr/bin/env python3
"""
🚀 Trading Bot Consolidation Script
Automatically organize and archive redundant trading bots and dashboards
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class TradingBotConsolidator:
    def __init__(self):
        self.base_dir = Path(".")
        self.archive_date = datetime.now().strftime("%Y%m%d")
        
        # Define what to keep vs archive
        self.core_bots = {
            "unified_master_trading_bot.py": "Main production system",
            "live_optimized_bot.py": "Live trading focused",
            "ai_trading_bot_simple.py": "Learning/testing",
            "telegram_ai_trading_bot.py": "Mobile notifications",
            "binance_testnet_client.py": "Safe testing environment"
        }
        
        self.core_dashboards = {
            "unified_trading_dashboard.py": "Main dashboard",
            "crypto_dashboard_gui.py": "Desktop interface", 
            "dashboard_customization_system.py": "Customizable interface"
        }
        
        self.bots_to_archive = [
            "ai_trading_bot.py",
            "ai_trading_bot_advanced.py",
            "enhanced_ai_trading_bot.py", 
            "ai_trading_bot_dynamic.py",
            "multi_exchange_universal_trading_bot.py",
            "comprehensive_ai_crypto_trading_bot.py",
            "integrated_twitter_trading_bot.py",
            "ai_trading_bot_with_screener.py",
            "enhanced_ai_crypto_bot.py"
        ]
        
        self.dashboards_to_archive = [
            "dashboard.py",
            "advanced_paper_trading_dashboard.py",
            "crypto_screener_dashboard.py",
            "chart_dashboard.py",
            "enhanced_dashboard_with_alerts.py",
            "integrated_customization_dashboard.py"
        ]
    
    def create_archive_structure(self):
        """Create archive directory structure"""
        print("📁 Creating archive directories...")
        
        archive_dirs = [
            f"archived_bots_{self.archive_date}",
            f"archived_dashboards_{self.archive_date}", 
            f"archived_systems_{self.archive_date}"
        ]
        
        for dir_name in archive_dirs:
            os.makedirs(dir_name, exist_ok=True)
            print(f"✅ Created: {dir_name}")
    
    def analyze_current_setup(self):
        """Analyze current bot and dashboard setup"""
        print("\n📊 CURRENT SETUP ANALYSIS")
        print("=" * 50)
        
        # Check which core bots exist
        print("\n🚀 CORE BOTS STATUS:")
        for bot_file, description in self.core_bots.items():
            if self.base_dir / bot_file in list(self.base_dir.glob("*.py")):
                print(f"✅ {bot_file} - {description}")
            else:
                print(f"❌ {bot_file} - {description} (MISSING)")
        
        # Check which core dashboards exist  
        print("\n📊 CORE DASHBOARDS STATUS:")
        for dash_file, description in self.core_dashboards.items():
            if self.base_dir / dash_file in list(self.base_dir.glob("*.py")):
                print(f"✅ {dash_file} - {description}")
            else:
                print(f"❌ {dash_file} - {description} (MISSING)")
        
        # Check which bots can be archived
        print(f"\n📦 BOTS TO ARCHIVE ({len(self.bots_to_archive)}):")
        existing_to_archive = []
        for bot_file in self.bots_to_archive:
            if (self.base_dir / bot_file).exists():
                print(f"📁 {bot_file}")
                existing_to_archive.append(bot_file)
            else:
                print(f"⚠️ {bot_file} (not found)")
        
        # Check which dashboards can be archived
        print(f"\n📊 DASHBOARDS TO ARCHIVE ({len(self.dashboards_to_archive)}):")
        existing_dash_to_archive = []
        for dash_file in self.dashboards_to_archive:
            if (self.base_dir / dash_file).exists():
                print(f"📁 {dash_file}")
                existing_dash_to_archive.append(dash_file)
            else:
                print(f"⚠️ {dash_file} (not found)")
        
        return existing_to_archive, existing_dash_to_archive
    
    def create_consolidation_report(self, archived_bots, archived_dashboards):
        """Create a consolidation report"""
        report = {
            "consolidation_date": self.archive_date,
            "core_systems_kept": {
                "bots": self.core_bots,
                "dashboards": self.core_dashboards
            },
            "archived_systems": {
                "bots": archived_bots,
                "dashboards": archived_dashboards
            },
            "statistics": {
                "total_bots_before": len(self.core_bots) + len(archived_bots),
                "total_bots_after": len(self.core_bots),
                "total_dashboards_before": len(self.core_dashboards) + len(archived_dashboards),
                "total_dashboards_after": len(self.core_dashboards),
                "reduction_percentage": {
                    "bots": round((len(archived_bots) / (len(self.core_bots) + len(archived_bots))) * 100, 1),
                    "dashboards": round((len(archived_dashboards) / (len(self.core_dashboards) + len(archived_dashboards))) * 100, 1)
                }
            }
        }
        
        # Save report
        with open(f"consolidation_report_{self.archive_date}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def archive_files(self, files_to_archive, destination_folder):
        """Archive specified files to destination folder"""
        archived_files = []
        
        for file_name in files_to_archive:
            if (self.base_dir / file_name).exists():
                try:
                    # Copy file to archive
                    shutil.copy2(file_name, destination_folder)
                    print(f"📁 Archived: {file_name}")
                    archived_files.append(file_name)
                    
                    # Create backup info
                    info_file = f"{destination_folder}/{file_name}.info"
                    with open(info_file, "w") as f:
                        f.write(f"Original location: {os.path.abspath(file_name)}\n")
                        f.write(f"Archived on: {datetime.now()}\n")
                        f.write(f"File size: {os.path.getsize(file_name)} bytes\n")
                    
                except Exception as e:
                    print(f"❌ Failed to archive {file_name}: {e}")
            else:
                print(f"⚠️ File not found: {file_name}")
        
        return archived_files
    
    def consolidate(self, dry_run=True):
        """Main consolidation process"""
        print("🚀 TRADING BOT CONSOLIDATION PROCESS")
        print("=" * 50)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be moved")
        else:
            print("⚠️ LIVE MODE - Files will be moved to archive")
        
        # Analyze current setup
        existing_bots, existing_dashboards = self.analyze_current_setup()
        
        if not dry_run:
            # Create archive structure
            self.create_archive_structure()
            
            # Archive bots
            if existing_bots:
                print(f"\n📦 Archiving {len(existing_bots)} trading bots...")
                archived_bots = self.archive_files(
                    existing_bots, 
                    f"archived_bots_{self.archive_date}"
                )
            else:
                archived_bots = []
            
            # Archive dashboards
            if existing_dashboards:
                print(f"\n📊 Archiving {len(existing_dashboards)} dashboards...")
                archived_dashboards = self.archive_files(
                    existing_dashboards,
                    f"archived_dashboards_{self.archive_date}"
                )
            else:
                archived_dashboards = []
            
            # Create report
            report = self.create_consolidation_report(archived_bots, archived_dashboards)
            
            print(f"\n📋 CONSOLIDATION COMPLETE!")
            print(f"📁 Archived {len(archived_bots)} bots and {len(archived_dashboards)} dashboards")
            print(f"📊 Report saved: consolidation_report_{self.archive_date}.json")
            
        else:
            print(f"\n📋 DRY RUN SUMMARY:")
            print(f"📁 Would archive {len(existing_bots)} bots")
            print(f"📊 Would archive {len(existing_dashboards)} dashboards")
            print(f"✅ Would keep {len(self.core_bots)} core bots")
            print(f"✅ Would keep {len(self.core_dashboards)} core dashboards")
    
    def restore_from_archive(self, archive_date=None):
        """Restore files from archive"""
        if not archive_date:
            archive_date = self.archive_date
        
        print(f"🔄 Restoring from archive dated: {archive_date}")
        
        # Find archive directories
        bot_archive = f"archived_bots_{archive_date}"
        dashboard_archive = f"archived_dashboards_{archive_date}"
        
        restored_count = 0
        
        for archive_dir in [bot_archive, dashboard_archive]:
            if os.path.exists(archive_dir):
                for file_path in Path(archive_dir).glob("*.py"):
                    try:
                        shutil.copy2(file_path, ".")
                        print(f"✅ Restored: {file_path.name}")
                        restored_count += 1
                    except Exception as e:
                        print(f"❌ Failed to restore {file_path.name}: {e}")
            else:
                print(f"⚠️ Archive not found: {archive_dir}")
        
        print(f"🔄 Restored {restored_count} files")

def main():
    """Main function"""
    consolidator = TradingBotConsolidator()
    
    print("🚀 Trading Bot Consolidation Tool")
    print("1. Analyze current setup")
    print("2. Dry run consolidation")
    print("3. Execute consolidation")
    print("4. Restore from archive")
    print("5. Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        consolidator.analyze_current_setup()
    elif choice == "2":
        consolidator.consolidate(dry_run=True)
    elif choice == "3":
        confirm = input("⚠️ This will archive files. Confirm? (yes/no): ")
        if confirm.lower() == "yes":
            consolidator.consolidate(dry_run=False)
        else:
            print("❌ Consolidation cancelled")
    elif choice == "4":
        archive_date = input("Enter archive date (YYYYMMDD) or press Enter for today: ").strip()
        consolidator.restore_from_archive(archive_date if archive_date else None)
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main() 