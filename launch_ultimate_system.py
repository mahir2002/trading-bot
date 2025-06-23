#!/usr/bin/env python3
"""
🚀 Ultimate All-in-One Trading System Launcher
Launch the comprehensive system that combines everything
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'dash', 'plotly', 'pandas', 'numpy', 'ccxt', 'ta', 
        'requests', 'scikit-learn', 'customtkinter', 'dash-bootstrap-components'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        install = input("Install missing packages? (y/n): ")
        if install.lower() == 'y':
            for package in missing_packages:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package])
            print("✅ Dependencies installed!")
        else:
            print("⚠️ Some features may not work without all dependencies")
    else:
        print("✅ All dependencies satisfied!")

def show_banner():
    """Show system banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║            🚀 ULTIMATE ALL-IN-ONE TRADING SYSTEM 🚀                          ║
║                                                                              ║
║                    Everything Combined Into One System                       ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🤖 ALL 5 Trading Bots COMBINED                                              ║
║  📊 ALL 3 Dashboard Interfaces (Web + Desktop + Customizable)               ║
║  🔐 ALL 13+ Security Systems Integrated                                     ║
║  🧠 ALL 12+ AI/ML Frameworks Active                                         ║
║  🛡️ ALL 8+ Risk Management Systems Enabled                                  ║
║  📊 ALL 10+ Data Systems Connected                                           ║
║                                                                              ║
║  💰 Features: Multi-exchange, AI signals, Risk management,                  ║
║              Telegram notifications, Real-time dashboards                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_interface_options():
    """Show interface options"""
    print("\n🚀 Choose Interface Mode:")
    print("1. 🌐 Web Dashboard (Browser-based)")
    print("2. 🖥️ Desktop GUI (Native application)")
    print("3. 💻 Terminal Only (Command-line)")
    print("4. 🚀 All Interfaces (Web + Desktop + Terminal)")
    print("5. ⚙️ Configuration")
    print("6. 📊 System Status")
    print("7. 🔧 Install Dependencies")
    print("8. ❌ Exit")

def launch_system(mode):
    """Launch the system with specified mode"""
    script_path = "ultimate_all_in_one_trading_system.py"
    
    if not Path(script_path).exists():
        print(f"❌ System file not found: {script_path}")
        return
    
    print(f"🚀 Launching Ultimate Trading System in {mode} mode...")
    
    try:
        if mode == "web":
            print("🌐 Starting web dashboard...")
            print("📱 Access at: http://localhost:8200")
            subprocess.run([sys.executable, script_path, "web"])
        elif mode == "gui":
            print("🖥️ Starting desktop GUI...")
            subprocess.run([sys.executable, script_path, "gui"])
        elif mode == "terminal":
            print("💻 Starting terminal interface...")
            subprocess.run([sys.executable, script_path, "terminal"])
        elif mode == "all":
            print("🚀 Starting all interfaces...")
            print("🌐 Web: http://localhost:8200")
            print("🖥️ Desktop GUI will open")
            subprocess.run([sys.executable, script_path])
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"❌ Error launching system: {e}")

def show_configuration():
    """Show configuration options"""
    print("\n⚙️ SYSTEM CONFIGURATION")
    print("=" * 50)
    
    config_file = "config.env.unified"
    
    if Path(config_file).exists():
        print(f"✅ Configuration file: {config_file}")
        
        # Read and display key settings
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        key_settings = [
            'CONFIDENCE_THRESHOLD', 'MAX_POSITIONS', 'POSITION_SIZE',
            'BINANCE_TESTNET', 'ENABLE_TELEGRAM', 'ENABLE_TWITTER'
        ]
        
        print("\n📋 Key Settings:")
        for line in lines:
            if any(setting in line for setting in key_settings) and not line.startswith('#'):
                print(f"   {line.strip()}")
        
        print(f"\n📝 Edit configuration: nano {config_file}")
        
    else:
        print(f"⚠️ Configuration file not found: {config_file}")
        print("📝 Create configuration file for custom settings")

def show_system_status():
    """Show system status"""
    print("\n📊 SYSTEM STATUS")
    print("=" * 50)
    
    # Check if system files exist
    files_to_check = [
        "ultimate_all_in_one_trading_system.py",
        "config.env.unified",
        "consolidation_report_20250622.json"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {file_path} (missing)")
    
    # Check Python version
    print(f"\n🐍 Python: {sys.version}")
    print(f"💻 Platform: {platform.system()} {platform.release()}")
    
    # Check dependencies
    print(f"\n📦 Dependencies:")
    check_dependencies()

def main():
    """Main launcher function"""
    show_banner()
    
    while True:
        show_interface_options()
        
        try:
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                launch_system("web")
            elif choice == "2":
                launch_system("gui")
            elif choice == "3":
                launch_system("terminal")
            elif choice == "4":
                launch_system("all")
            elif choice == "5":
                show_configuration()
            elif choice == "6":
                show_system_status()
            elif choice == "7":
                check_dependencies()
            elif choice == "8":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please choose 1-8.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n👋 Launcher stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 