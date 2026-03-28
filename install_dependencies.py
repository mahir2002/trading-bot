#!/usr/bin/env python3
"""
📦 UNIFIED MASTER TRADING BOT - DEPENDENCY INSTALLER
Automatically installs all required packages for the ultimate trading bot
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main installation function"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║          📦 UNIFIED MASTER TRADING BOT INSTALLER             ║
    ║                                                              ║
    ║              Installing Required Dependencies                ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Core trading and data packages
    core_packages = [
        "ccxt>=4.0.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "ta>=0.10.0",
        "python-dotenv>=0.19.0",
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
    ]
    
    # Machine Learning packages
    ml_packages = [
        "scikit-learn>=1.1.0",
        "joblib>=1.2.0",
        "scipy>=1.9.0",
    ]
    
    # Optional advanced packages
    advanced_packages = [
        "plotly>=5.0.0",
        "dash>=2.0.0",
        "websockets>=10.0",
        "asyncio-mqtt>=0.11.0",
        "python-telegram-bot>=20.0",
        "tweepy>=4.0.0",
        "yfinance>=0.2.0",
        "beautifulsoup4>=4.11.0",
        "selenium>=4.0.0",
    ]
    
    # Web3 and DEX packages (optional)
    web3_packages = [
        "web3>=6.0.0",
        "eth-account>=0.8.0",
        "solana>=0.30.0",
    ]
    
    all_packages = core_packages + ml_packages + advanced_packages
    
    print("🔄 Installing core packages...")
    failed_packages = []
    
    for i, package in enumerate(all_packages, 1):
        print(f"[{i}/{len(all_packages)}] Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
            failed_packages.append(package)
    
    # Optional Web3 packages
    print("\n🌐 Installing optional Web3 packages...")
    for package in web3_packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"⚠️ Optional package {package} failed to install")
    
    # Summary
    print("\n" + "="*60)
    if failed_packages:
        print(f"❌ Installation completed with {len(failed_packages)} failures:")
        for package in failed_packages:
            print(f"  - {package}")
        print("\nYou can try installing failed packages manually:")
        print(f"pip install {' '.join(failed_packages)}")
    else:
        print("✅ All packages installed successfully!")
    
    print("\n🚀 Installation complete! You can now run:")
    print("python start_unified_bot.py --check-only")
    print("\nOr start trading with:")
    print("python start_unified_bot.py --mode paper")

if __name__ == "__main__":
    main() 