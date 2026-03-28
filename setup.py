#!/usr/bin/env python3
"""
AI Trading Bot Setup Script
Helps users install dependencies and configure the bot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🤖 AI Crypto Trading Bot Setup")
    print("=" * 50)
    print("This script will help you set up the trading bot.\n")

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def create_config_file():
    """Create configuration file from template"""
    print("\n⚙️  Setting up configuration...")
    
    template_file = 'config.env.example'
    config_file = '.env'
    
    if not os.path.exists(template_file):
        print(f"❌ Template file {template_file} not found")
        return False
    
    if os.path.exists(config_file):
        response = input(f"⚠️  {config_file} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("✅ Keeping existing configuration")
            return True
    
    try:
        shutil.copy2(template_file, config_file)
        print(f"✅ Created {config_file} from template")
        print(f"💡 Please edit {config_file} with your API keys and settings")
        return True
    except Exception as e:
        print(f"❌ Failed to create config file: {e}")
        return False

def create_directories():
    """Create required directories"""
    print("\n📁 Creating directories...")
    
    directories = ['logs', 'data', 'models']
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def setup_git_ignore():
    """Create .gitignore file"""
    print("\n🔒 Setting up .gitignore...")
    
    gitignore_content = """# Environment variables
.env
config.env

# API Keys and credentials
*.json
credentials.json

# Logs
logs/
*.log

# Data files
data/
*.csv
*.pkl

# Model files
models/
*.h5
*.pkl

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Performance data
performance.json
"""
    
    try:
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore file")
        return True
    except Exception as e:
        print(f"❌ Failed to create .gitignore: {e}")
        return False

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running setup tests...")
    
    try:
        from run_bot import run_tests
        return run_tests()
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def show_next_steps():
    """Show next steps to user"""
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - Exchange API keys (Binance, Coinbase, etc.)")
    print("   - Telegram bot token (optional)")
    print("   - Email settings (optional)")
    print("   - Google Sheets credentials (optional)")
    print("\n2. Test your setup:")
    print("   python run_bot.py --test")
    print("\n3. Start with paper trading:")
    print("   Set TRADING_MODE=paper in .env")
    print("   python run_bot.py --bot")
    print("\n4. Monitor with the dashboard:")
    print("   python run_bot.py --dashboard")
    print("   Open http://localhost:8050 in your browser")
    print("\n⚠️  Important:")
    print("   - Always test with paper trading first")
    print("   - Never invest more than you can afford to lose")
    print("   - Monitor the bot regularly")
    print("   - Read the README.md for detailed instructions")

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create config file
    if not create_config_file():
        print("\n❌ Setup failed during configuration")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Setup failed during directory creation")
        sys.exit(1)
    
    # Setup .gitignore
    setup_git_ignore()
    
    # Run tests
    print("\n" + "="*50)
    if run_tests():
        show_next_steps()
    else:
        print("\n⚠️  Setup completed with some issues.")
        print("Please check the error messages above and fix any problems.")
        print("You can run 'python run_bot.py --test' to check again.")

if __name__ == "__main__":
    main() 