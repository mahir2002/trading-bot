#!/usr/bin/env python3
"""
Unified Trading Dashboard - Single Interface for All Trading Operations
Replaces 25+ separate dashboards with one comprehensive interface
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np

# Dashboard configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading_dashboard_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global data store for dashboard
dashboard_data = {
    'portfolio': {},
    'positions': {},
    'orders': [],
    'market_data': {},
    'ai_predictions': {},
    'risk_metrics': {},
    'performance': {},
    'alerts': [],
    'system_status': {},
    'trading_signals': []
}

class DashboardManager:
    """Manages dashboard data and real-time updates."""
    
    def __init__(self):
        self.connected_clients = set()
        self.logger = logging.getLogger(__name__)
        
    def add_client(self, client_id: str):
        """Add connected client."""
        self.connected_clients.add(client_id)
        self.logger.info(f"Client {client_id} connected. Total clients: {len(self.connected_clients)}")
        
    def remove_client(self, client_id: str):
        """Remove disconnected client."""
        self.connected_clients.discard(client_id)
        self.logger.info(f"Client {client_id} disconnected. Total clients: {len(self.connected_clients)}")
        
    def broadcast_update(self, event_type: str, data: Dict[str, Any]):
        """Broadcast update to all connected clients."""
        try:
            socketio.emit(event_type, data, broadcast=True)
        except Exception as e:
            self.logger.error(f"Error broadcasting {event_type}: {e}")
    
    def update_portfolio(self, portfolio_data: Dict[str, Any]):
        """Update portfolio data."""
        dashboard_data['portfolio'] = portfolio_data
        self.broadcast_update('portfolio_update', portfolio_data)
    
    def update_positions(self, positions_data: Dict[str, Any]):
        """Update positions data."""
        dashboard_data['positions'] = positions_data
        self.broadcast_update('positions_update', positions_data)
    
    def update_market_data(self, symbol: str, price_data: Dict[str, Any]):
        """Update market data."""
        dashboard_data['market_data'][symbol] = price_data
        self.broadcast_update('market_data_update', {
            'symbol': symbol,
            'data': price_data
        })
    
    def add_order(self, order_data: Dict[str, Any]):
        """Add new order."""
        dashboard_data['orders'].append(order_data)
        # Keep only last 1000 orders
        if len(dashboard_data['orders']) > 1000:
            dashboard_data['orders'] = dashboard_data['orders'][-1000:]
        self.broadcast_update('order_update', order_data)
    
    def update_ai_predictions(self, predictions: Dict[str, Any]):
        """Update AI predictions."""
        dashboard_data['ai_predictions'] = predictions
        self.broadcast_update('ai_predictions_update', predictions)
    
    def update_risk_metrics(self, risk_data: Dict[str, Any]):
        """Update risk metrics."""
        dashboard_data['risk_metrics'] = risk_data
        self.broadcast_update('risk_metrics_update', risk_data)
    
    def add_alert(self, alert_data: Dict[str, Any]):
        """Add new alert."""
        alert_data['timestamp'] = datetime.now().isoformat()
        dashboard_data['alerts'].append(alert_data)
        # Keep only last 100 alerts
        if len(dashboard_data['alerts']) > 100:
            dashboard_data['alerts'] = dashboard_data['alerts'][-100:]
        self.broadcast_update('alert_update', alert_data)
    
    def update_system_status(self, status_data: Dict[str, Any]):
        """Update system status."""
        dashboard_data['system_status'] = status_data
        self.broadcast_update('system_status_update', status_data)

# Initialize dashboard manager
dashboard_manager = DashboardManager()

# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/portfolio')
def get_portfolio():
    """Get current portfolio data."""
    return jsonify(dashboard_data['portfolio'])

@app.route('/api/positions')
def get_positions():
    """Get current positions."""
    return jsonify(dashboard_data['positions'])

@app.route('/api/orders')
def get_orders():
    """Get recent orders."""
    return jsonify(dashboard_data['orders'][-100:])  # Last 100 orders

@app.route('/api/market-data')
def get_market_data():
    """Get current market data."""
    return jsonify(dashboard_data['market_data'])

@app.route('/api/ai-predictions')
def get_ai_predictions():
    """Get AI predictions."""
    return jsonify(dashboard_data['ai_predictions'])

@app.route('/api/risk-metrics')
def get_risk_metrics():
    """Get risk metrics."""
    return jsonify(dashboard_data['risk_metrics'])

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts."""
    return jsonify(dashboard_data['alerts'][-50:])  # Last 50 alerts

@app.route('/api/system-status')
def get_system_status():
    """Get system status."""
    return jsonify(dashboard_data['system_status'])

@app.route('/api/performance')
def get_performance():
    """Get performance metrics."""
    return jsonify(dashboard_data['performance'])

# Trading controls
@app.route('/api/place-order', methods=['POST'])
def place_order():
    """Place a new order."""
    try:
        order_data = request.json
        
        # Validate order data
        required_fields = ['symbol', 'side', 'quantity', 'order_type']
        if not all(field in order_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Add order to dashboard (in real implementation, this would go to order execution module)
        order_data['order_id'] = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        order_data['status'] = 'PENDING'
        order_data['timestamp'] = datetime.now().isoformat()
        
        dashboard_manager.add_order(order_data)
        
        return jsonify({
            'success': True,
            'order_id': order_data['order_id'],
            'message': 'Order placed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cancel-order', methods=['POST'])
def cancel_order():
    """Cancel an order."""
    try:
        data = request.json
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'error': 'Order ID required'}), 400
        
        # Find and update order status
        for order in dashboard_data['orders']:
            if order.get('order_id') == order_id:
                order['status'] = 'CANCELLED'
                order['cancelled_at'] = datetime.now().isoformat()
                break
        
        dashboard_manager.broadcast_update('order_cancelled', {'order_id': order_id})
        
        return jsonify({
            'success': True,
            'message': f'Order {order_id} cancelled successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    client_id = request.sid
    dashboard_manager.add_client(client_id)
    
    # Send initial data to new client
    emit('initial_data', {
        'portfolio': dashboard_data['portfolio'],
        'positions': dashboard_data['positions'],
        'market_data': dashboard_data['market_data'],
        'risk_metrics': dashboard_data['risk_metrics'],
        'system_status': dashboard_data['system_status']
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    client_id = request.sid
    dashboard_manager.remove_client(client_id)

@socketio.on('request_data')
def handle_data_request(data):
    """Handle specific data requests."""
    data_type = data.get('type')
    
    if data_type == 'portfolio':
        emit('portfolio_update', dashboard_data['portfolio'])
    elif data_type == 'positions':
        emit('positions_update', dashboard_data['positions'])
    elif data_type == 'orders':
        emit('orders_update', dashboard_data['orders'][-100:])
    elif data_type == 'market_data':
        emit('market_data_update', dashboard_data['market_data'])
    elif data_type == 'ai_predictions':
        emit('ai_predictions_update', dashboard_data['ai_predictions'])
    elif data_type == 'risk_metrics':
        emit('risk_metrics_update', dashboard_data['risk_metrics'])
    elif data_type == 'alerts':
        emit('alerts_update', dashboard_data['alerts'][-50:])

# Integration with trading platform
class DashboardEventHandler:
    """Handles events from the trading platform."""
    
    def __init__(self, dashboard_manager: DashboardManager):
        self.dashboard_manager = dashboard_manager
        self.logger = logging.getLogger(__name__)
    
    async def handle_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle events from trading platform."""
        try:
            if event_type == "portfolio_update":
                self.dashboard_manager.update_portfolio(event_data)
            elif event_type == "portfolio_metrics_update":
                dashboard_data['performance'] = event_data
                self.dashboard_manager.broadcast_update('performance_update', event_data)
            elif event_type == "positions_update":
                self.dashboard_manager.update_positions(event_data)
            elif event_type == "order_submitted":
                self.dashboard_manager.add_order(event_data)
            elif event_type == "order_filled":
                self.dashboard_manager.add_order(event_data)
            elif event_type == "market_data_update":
                symbol = event_data.get('symbol')
                if symbol:
                    self.dashboard_manager.update_market_data(symbol, event_data)
            elif event_type == "ai_prediction":
                self.dashboard_manager.update_ai_predictions(event_data)
            elif event_type == "risk_alert":
                self.dashboard_manager.add_alert({
                    'type': 'risk',
                    'severity': event_data.get('severity', 'medium'),
                    'message': event_data.get('message', 'Risk alert'),
                    'data': event_data
                })
            elif event_type == "system_status_update":
                self.dashboard_manager.update_system_status(event_data)
            elif event_type == "trading_signal":
                dashboard_data['trading_signals'].append(event_data)
                if len(dashboard_data['trading_signals']) > 100:
                    dashboard_data['trading_signals'] = dashboard_data['trading_signals'][-100:]
                self.dashboard_manager.broadcast_update('trading_signal', event_data)
                
        except Exception as e:
            self.logger.error(f"Error handling event {event_type}: {e}")

# Initialize event handler
dashboard_event_handler = DashboardEventHandler(dashboard_manager)

# Mock data generation for testing
def generate_mock_data():
    """Generate mock data for testing dashboard."""
    import random
    
    # Mock portfolio data
    portfolio_data = {
        'total_value': 125000.0 + random.uniform(-5000, 5000),
        'total_pnl': 25000.0 + random.uniform(-2000, 2000),
        'total_pnl_percentage': 20.0 + random.uniform(-2, 2),
        'cash_balance': 15000.0 + random.uniform(-1000, 1000),
        'positions_count': random.randint(5, 15),
        'daily_pnl': random.uniform(-1000, 1000)
    }
    dashboard_manager.update_portfolio(portfolio_data)
    
    # Mock positions
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
    positions_data = {}
    for symbol in symbols[:random.randint(3, 5)]:
        positions_data[symbol] = {
            'symbol': symbol,
            'quantity': random.uniform(0.1, 10),
            'average_price': random.uniform(1000, 50000),
            'current_price': random.uniform(1000, 50000),
            'unrealized_pnl': random.uniform(-500, 500),
            'pnl_percentage': random.uniform(-5, 5)
        }
    dashboard_manager.update_positions(positions_data)
    
    # Mock market data
    for symbol in symbols:
        market_data = {
            'price': random.uniform(1000, 50000),
            'change_24h': random.uniform(-10, 10),
            'volume_24h': random.uniform(1000000, 100000000),
            'timestamp': datetime.now().isoformat()
        }
        dashboard_manager.update_market_data(symbol, market_data)
    
    # Mock risk metrics
    risk_data = {
        'portfolio_var_95': random.uniform(0.01, 0.05),
        'max_drawdown': random.uniform(0.05, 0.15),
        'current_drawdown': random.uniform(0, 0.05),
        'sharpe_ratio': random.uniform(0.5, 2.0),
        'volatility': random.uniform(0.15, 0.35)
    }
    dashboard_manager.update_risk_metrics(risk_data)
    
    # Mock system status
    system_status = {
        'modules': {
            'market_data': {'status': 'RUNNING', 'uptime': '2d 5h 30m'},
            'ai_models': {'status': 'RUNNING', 'uptime': '2d 5h 29m'},
            'signal_generation': {'status': 'RUNNING', 'uptime': '2d 5h 28m'},
            'order_execution': {'status': 'RUNNING', 'uptime': '2d 5h 27m'},
            'portfolio': {'status': 'RUNNING', 'uptime': '2d 5h 26m'},
            'risk_management': {'status': 'RUNNING', 'uptime': '2d 5h 25m'}
        },
        'performance': {
            'cpu_usage': random.uniform(20, 80),
            'memory_usage': random.uniform(30, 70),
            'events_per_second': random.randint(50, 200)
        }
    }
    dashboard_manager.update_system_status(system_status)

def start_mock_data_generation():
    """Start mock data generation for testing."""
    def generate_data():
        while True:
            try:
                generate_mock_data()
                socketio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logging.error(f"Error generating mock data: {e}")
                socketio.sleep(5)
    
    # Start background task
    socketio.start_background_task(generate_data)

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start mock data generation for testing
    start_mock_data_generation()
    
    # Run the dashboard
    print("Starting Unified Trading Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False) 