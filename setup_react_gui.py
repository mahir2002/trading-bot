#!/usr/bin/env python3
"""
🚀 React GUI Setup Script
Complete setup for React frontend integration with AI trading bot
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if required software is installed"""
    print("🔍 Checking requirements...")
    
    requirements = {
        'python': True,
        'pip': True,
        'node': False,
        'npm': False
    }
    
    # Check Python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Python: {result.stdout.strip()}")
        else:
            print("❌ Python not found")
            requirements['python'] = False
    except FileNotFoundError:
        print("❌ Python not found")
        requirements['python'] = False
    
    # Check pip
    try:
        result = subprocess.run(['pip', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pip: {result.stdout.strip()}")
        else:
            print("❌ pip not found")
            requirements['pip'] = False
    except FileNotFoundError:
        print("❌ pip not found")
        requirements['pip'] = False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
            requirements['node'] = True
        else:
            print("⚠️ Node.js not found (optional)")
    except FileNotFoundError:
        print("⚠️ Node.js not found (optional - needed for React frontend)")
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
            requirements['npm'] = True
        else:
            print("⚠️ npm not found (optional)")
    except FileNotFoundError:
        print("⚠️ npm not found (optional - needed for React frontend)")
    
    return requirements

def install_python_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    dependencies = [
        'flask',
        'flask-cors', 
        'flask-socketio'
    ]
    
    try:
        for dep in dependencies:
            print(f"Installing {dep}...")
            subprocess.run(['pip', 'install', dep], check=True, capture_output=True)
        print("✅ Python dependencies installed!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error installing Python dependencies")
        return False

def create_react_frontend():
    """Create React frontend structure"""
    print("⚛️ Creating React frontend...")
    
    # Create directories
    frontend_dir = Path('react_frontend')
    frontend_dir.mkdir(exist_ok=True)
    
    (frontend_dir / 'src' / 'components').mkdir(parents=True, exist_ok=True)
    (frontend_dir / 'public').mkdir(exist_ok=True)
    
    # Create package.json
    package_json = {
        "name": "ai-trading-bot-gui",
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "socket.io-client": "^4.7.2",
            "lucide-react": "^0.263.1"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.0.3",
            "vite": "^4.4.5",
            "tailwindcss": "^3.3.3"
        }
    }
    
    with open(frontend_dir / 'package.json', 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Create index.html
    index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Trading Bot Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''
    
    with open(frontend_dir / 'index.html', 'w') as f:
        f.write(index_html)
    
    print("✅ React frontend created!")

def create_start_scripts():
    """Create start scripts"""
    print("📝 Creating start scripts...")
    
    # Backend script
    backend_script = '''#!/usr/bin/env python3
from react_gui_backend import ReactGUIBackend

if __name__ == "__main__":
    print("🚀 Starting AI Trading Bot Backend...")
    backend = ReactGUIBackend(port=5000)
    backend.run()
'''
    
    with open('start_backend.py', 'w') as f:
        f.write(backend_script)
    
    print("✅ Start scripts created!")

def install_node_dependencies(requirements):
    """Install Node.js dependencies if available"""
    if not requirements['node'] or not requirements['npm']:
        print("\n⚠️ Node.js/npm not available - skipping frontend dependencies")
        print("💡 Install Node.js from https://nodejs.org to use the React frontend")
        return False
    
    print("\n📦 Installing Node.js dependencies...")
    
    try:
        os.chdir('react_frontend')
        subprocess.run(['npm', 'install'], check=True)
        os.chdir('..')
        print("✅ Node.js dependencies installed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Node.js dependencies: {e}")
        os.chdir('..')
        return False

def create_documentation():
    """Create setup documentation"""
    print("\n📚 Creating documentation...")
    
    doc_content = '''# 🚀 AI Trading Bot React GUI

## Quick Start

### 1. Start the Backend
```bash
python start_backend.py
```

### 2. Start the Frontend (if Node.js is installed)
```bash
./start_frontend.sh
```

### 3. Or start both together
```bash
./start_gui.sh
```

### 4. Access the Dashboard
Open http://localhost:3000 in your browser

## Manual Setup

If the automatic setup didn't work:

### Backend Setup
1. Install Python dependencies:
   ```bash
   pip install flask flask-cors flask-socketio
   ```

2. Start the backend:
   ```bash
   python react_gui_backend.py
   ```

### Frontend Setup (Optional)
1. Install Node.js and npm from https://nodejs.org

2. Install dependencies:
   ```bash
   cd react_frontend
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Integration with Your Existing Bot

To connect this GUI to your existing AI trading bot systems:

1. Edit `react_gui_backend.py`
2. Replace the demo data with calls to your actual trading systems
3. Import your existing modules:
   ```python
   from your_ai_trading_bot import AdvancedTradingBot
   from your_portfolio_system import PortfolioRiskSystem
   ```

## Features

- Real-time bot control (start/stop/pause)
- Live market data display
- Portfolio tracking
- Trade history
- WebSocket communication for real-time updates
- Modern responsive UI

## Troubleshooting

- **Backend won't start**: Check if port 5000 is available
- **Frontend won't connect**: Ensure backend is running on port 5000
- **Missing dependencies**: Run the setup script again

## Files Created

- `react_gui_backend.py` - Python backend server
- `react_frontend/` - React frontend application
- `start_backend.py` - Backend startup script
- `start_frontend.sh` - Frontend startup script
- `start_gui.sh` - Combined startup script
'''
    
    with open('REACT_GUI_SETUP.md', 'w') as f:
        f.write(doc_content)
    
    print("✅ Documentation created!")

def main():
    """Main setup function"""
    print("🚀 AI TRADING BOT REACT GUI SETUP")
    print("=" * 50)
    
    # Check requirements
    requirements = check_requirements()
    
    if not requirements['python'] or not requirements['pip']:
        print("\n❌ Python and pip are required!")
        print("Please install Python and pip before running this setup.")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Create React frontend
    create_react_frontend()
    
    # Create start scripts
    create_start_scripts()
    
    # Install Node.js dependencies if available
    node_success = install_node_dependencies(requirements)
    
    # Create documentation
    create_documentation()
    
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 50)
    
    print("✅ Files created:")
    print("  • react_gui_backend.py - Python backend server")
    print("  • react_frontend/ - React frontend application")
    print("  • start_backend.py - Backend startup script")
    print("  • start_frontend.sh - Frontend startup script")
    print("  • start_gui.sh - Combined startup script")
    print("  • REACT_GUI_SETUP.md - Setup documentation")
    
    print("\n🚀 Next steps:")
    print("1. Start the backend: python start_backend.py")
    
    if node_success:
        print("2. Start the frontend: ./start_frontend.sh")
        print("3. Or start both: ./start_gui.sh")
        print("4. Open http://localhost:3000")
    else:
        print("2. Install Node.js from https://nodejs.org")
        print("3. Run: cd react_frontend && npm install")
        print("4. Run: npm run dev")
        print("5. Open http://localhost:3000")
    
    print("\n💡 To integrate with your existing bot:")
    print("Edit react_gui_backend.py and replace demo data with your actual systems")
    
    print("\n🌐 Backend API will be available at: http://localhost:5000")
    print("📊 Frontend dashboard will be at: http://localhost:3000")

if __name__ == "__main__":
    main() 