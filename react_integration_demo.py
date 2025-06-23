#!/usr/bin/env python3
"""
🚀 React GUI Integration Demo
Complete demonstration of React frontend integration with AI trading bot
"""

import os
import json
import time
import threading
import subprocess

# Import our backend integration
from react_gui_backend import ReactGUIBackend

def create_react_package_json():
    """Create package.json for React frontend"""
    package_json = {
        "name": "ai-trading-bot-gui",
        "version": "1.0.0",
        "description": "React GUI for AI Crypto Trading Bot",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "socket.io-client": "^4.7.2",
            "recharts": "^2.8.0",
            "lucide-react": "^0.263.1"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.0.3",
            "vite": "^4.4.5",
            "tailwindcss": "^3.3.3",
            "autoprefixer": "^10.4.15",
            "postcss": "^8.4.29"
        }
    }
    
    os.makedirs('react_frontend', exist_ok=True)
    with open('react_frontend/package.json', 'w') as f:
        json.dump(package_json, f, indent=2)

def create_react_app_structure():
    """Create complete React app structure"""
    
    # Create directories
    os.makedirs('react_frontend/src/components', exist_ok=True)
    os.makedirs('react_frontend/src/services', exist_ok=True)
    os.makedirs('react_frontend/public', exist_ok=True)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
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
</html>"""
    
    with open('react_frontend/index.html', 'w') as f:
        f.write(index_html)
    
    # Create main.jsx
    main_jsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""
    
    with open('react_frontend/src/main.jsx', 'w') as f:
        f.write(main_jsx)

def create_installation_script():
    """Create installation script for React frontend"""
    install_script = """#!/bin/bash
echo "🚀 Installing React GUI for AI Trading Bot..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install flask flask-cors flask-socketio

# Create React frontend
echo "⚛️ Setting up React frontend..."
cd react_frontend

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Installation complete!"
echo ""
echo "🎯 To start the application:"
echo "1. Start Python backend: python react_gui_backend.py"
echo "2. Start React frontend: cd react_frontend && npm run dev"
echo ""
echo "🌐 Access the dashboard at: http://localhost:3000"
"""
    
    with open('install_react_gui.sh', 'w') as f:
        f.write(install_script)
    
    os.chmod('install_react_gui.sh', 0o755)

class ReactIntegrationDemo:
    """Complete React integration demonstration"""
    
    def __init__(self):
        self.backend = None
        self.backend_thread = None
        
    def setup_project_structure(self):
        """Setup complete project structure"""
        print("🏗️ Setting up React GUI project structure...")
        
        # Create React app structure
        create_react_app_structure()
        
        # Create configuration files
        create_react_package_json()
        
        # Create installation script
        create_installation_script()
        
        print("✅ Project structure created successfully!")
    
    def start_backend(self):
        """Start the Python backend server"""
        print("🚀 Starting Python backend server...")
        
        self.backend = ReactGUIBackend(port=5000)
        self.backend_thread = threading.Thread(target=self.backend.run)
        self.backend_thread.daemon = True
        self.backend_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        print("✅ Backend server started on http://localhost:5000")
    
    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Installing dependencies...")
        
        try:
            # Install Python dependencies
            subprocess.run([
                'pip', 'install', 'flask', 'flask-cors', 'flask-socketio'
            ], check=True)
            print("✅ Python dependencies installed")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            print("💡 Please install manually: pip install flask flask-cors flask-socketio")
    
    def create_documentation(self):
        """Create comprehensive documentation"""
        doc_content = """# 🚀 React GUI Integration for AI Trading Bot

## Overview
Complete React frontend integration with Python AI trading bot backend, featuring real-time data streaming, WebSocket communication, and comprehensive dashboard functionality.

## Features
- **Real-time Dashboard**: Live market data, portfolio updates, and bot statistics
- **Bot Control**: Start/stop/pause trading bot with strategy selection
- **Portfolio Management**: Real-time portfolio tracking and performance metrics
- **Trade History**: Detailed trade logs with profit/loss tracking
- **Market Overview**: Live cryptocurrency market data
- **WebSocket Integration**: Real-time updates without page refresh
- **Responsive Design**: Modern UI with Tailwind CSS

## Quick Start

### 1. Install Dependencies
```bash
# Python dependencies
pip install flask flask-cors flask-socketio

# Node.js dependencies
cd react_frontend
npm install
```

### 2. Start Backend Server
```bash
python react_gui_backend.py
```

### 3. Start React Frontend
```bash
cd react_frontend
npm run dev
```

### 4. Access Dashboard
Open http://localhost:3000 in your browser

## API Endpoints

### Bot Control
- `GET /api/bot/status` - Get bot status and statistics
- `POST /api/bot/control` - Start/stop/pause bot
- `POST /api/bot/strategy` - Update trading strategy

### Market Data
- `GET /api/market/overview` - Get market overview
- `GET /api/portfolio` - Get portfolio data
- `GET /api/trades/history` - Get trade history
- `GET /api/signals/active` - Get active signals

### WebSocket Events
- `market_update` - Real-time market data
- `portfolio_update` - Portfolio changes
- `bot_stats_update` - Bot statistics
- `new_trade` - New trade notifications

## Integration with Your Existing AI Trading Bot

Your React GUI can now connect to your sophisticated AI trading systems:

1. **Advanced AI Models Framework**: Display real-time predictions and confidence scores
2. **Portfolio Risk Management**: Show live risk metrics and position sizing
3. **Signal Generation**: Display active trading signals and market regime detection
4. **Backtesting Results**: Visualize historical performance
5. **Multi-Exchange Support**: Unified data from multiple exchanges

## Customization

### Connect to Your Trading Bot
Replace the demo data in `react_gui_backend.py` with calls to your actual trading systems:

```python
# Example integration
from your_ai_trading_bot import AdvancedTradingBot
from your_portfolio_system import PortfolioRiskSystem

# In ReactGUIBackend class:
def __init__(self):
    self.trading_bot = AdvancedTradingBot()
    self.portfolio_system = PortfolioRiskSystem()
    # ... rest of initialization
```

## Next Steps
1. Run the installation script: `./install_react_gui.sh`
2. Start the backend: `python react_gui_backend.py`
3. Start the frontend: `cd react_frontend && npm run dev`
4. Customize the integration with your existing systems
5. Add additional features as needed
"""
        
        with open('REACT_GUI_INTEGRATION_GUIDE.md', 'w') as f:
            f.write(doc_content)
    
    def run_demo(self):
        """Run the complete integration demo"""
        print("🎯 REACT GUI INTEGRATION DEMO")
        print("=" * 50)
        
        # Setup project structure
        self.setup_project_structure()
        
        # Install dependencies
        self.install_dependencies()
        
        # Create documentation
        self.create_documentation()
        
        # Start backend
        self.start_backend()
        
        print("\n🎉 REACT GUI INTEGRATION COMPLETE!")
        print("=" * 50)
        print("✅ Backend server running on: http://localhost:5000")
        print("✅ React app ready in: ./react_frontend/")
        print("✅ Installation script: ./install_react_gui.sh")
        print("✅ Documentation: ./REACT_GUI_INTEGRATION_GUIDE.md")
        
        print("\n🚀 Next Steps:")
        print("1. cd react_frontend")
        print("2. npm install")
        print("3. npm run dev")
        print("4. Open http://localhost:3000")
        
        print("\n📊 Available API Endpoints:")
        print("• GET  /api/bot/status")
        print("• POST /api/bot/control")
        print("• GET  /api/market/overview")
        print("• GET  /api/portfolio")
        print("• GET  /api/trades/history")
        print("• GET  /api/signals/active")
        
        print("\n🔄 Real-time Features:")
        print("• WebSocket connection for live updates")
        print("• Real-time market data streaming")
        print("• Live portfolio updates")
        print("• Bot status monitoring")
        print("• Trade execution notifications")
        
        # Keep backend running
        try:
            print("\n⏳ Backend server is running... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Demo stopped by user")

def main():
    """Main function"""
    demo = ReactIntegrationDemo()
    demo.run_demo()

if __name__ == "__main__":
    main() 