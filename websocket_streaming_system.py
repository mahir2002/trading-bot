#!/usr/bin/env python3
"""
🌐 WebSocket Real-Time Data Streaming System
Advanced real-time data streaming for trading dashboards using WebSockets
to replace dcc.Interval with true real-time updates for critical metrics.
"""

import asyncio
import websockets
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import ssl
import certifi

# WebSocket server imports
from websockets.server import serve
from websockets.exceptions import ConnectionClosed, WebSocketException

# Trading system imports
try:
    from advanced_position_sizing_manager import AdvancedPositionSizingManager
    from dex_position_sizing_integration import DEXPositionSizingIntegration
except ImportError:
    print("⚠️ Advanced position sizing modules not found - using mock data")

@dataclass
class StreamingMetric:
    """Real-time streaming metric data"""
    metric_id: str
    name: str
    value: Any
    timestamp: datetime
    priority: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'price', 'volume', 'signal', 'portfolio', 'risk'
    metadata: Dict[str, Any] = None

@dataclass
class ClientSubscription:
    """Client subscription configuration"""
    client_id: str
    websocket: Any
    subscribed_metrics: List[str]
    update_frequency: float  # seconds
    last_update: datetime
    is_active: bool = True

class WebSocketDataStreamer:
    """Advanced WebSocket data streaming system"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.logger = self._setup_logger()
        
        # Client management
        self.clients: Dict[str, ClientSubscription] = {}
        self.active_connections = set()
        
        # Data management
        self.metrics_cache: Dict[str, StreamingMetric] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.data_providers: Dict[str, Callable] = {}
        
        # Streaming configuration
        self.streaming_active = False
        self.update_frequencies = {
            'critical': 0.1,    # 100ms for critical metrics
            'high': 0.5,        # 500ms for high priority
            'medium': 1.0,      # 1s for medium priority
            'low': 5.0          # 5s for low priority
        }
        
        # Performance monitoring
        self.performance_stats = {
            'messages_sent': 0,
            'bytes_sent': 0,
            'active_clients': 0,
            'uptime_start': datetime.now(),
            'errors': 0
        }
        
        # Initialize data providers
        self._initialize_data_providers()
        
        self.logger.info("🌐 WebSocket Data Streamer initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for WebSocket streamer"""
        logger = logging.getLogger('WebSocketStreamer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_data_providers(self):
        """Initialize data provider functions"""
        
        # Market data providers
        self.data_providers.update({
            'btc_price': self._get_btc_price,
            'eth_price': self._get_eth_price,
            'market_cap': self._get_market_cap,
            'volume_24h': self._get_volume_24h,
            'fear_greed_index': self._get_fear_greed_index,
            
            # Portfolio metrics
            'portfolio_value': self._get_portfolio_value,
            'daily_pnl': self._get_daily_pnl,
            'open_positions': self._get_open_positions,
            'available_balance': self._get_available_balance,
            
            # Trading signals
            'active_signals': self._get_active_signals,
            'signal_strength': self._get_signal_strength,
            'position_recommendations': self._get_position_recommendations,
            
            # Risk metrics
            'portfolio_risk': self._get_portfolio_risk,
            'var_95': self._get_var_95,
            'drawdown': self._get_drawdown,
            'sharpe_ratio': self._get_sharpe_ratio,
            
            # System metrics
            'system_status': self._get_system_status,
            'api_latency': self._get_api_latency,
            'error_rate': self._get_error_rate
        })
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.logger.info(f"🚀 Starting WebSocket server on {self.host}:{self.port}")
        
        try:
            # Start the WebSocket server
            server = await serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.streaming_active = True
            
            # Start data streaming loop
            asyncio.create_task(self.data_streaming_loop())
            
            self.logger.info("✅ WebSocket server started successfully")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start WebSocket server: {e}")
            raise
    
    async def handle_client(self, websocket, path):
        """Handle new client connections"""
        client_id = f"client_{int(time.time() * 1000)}"
        
        try:
            self.logger.info(f"🔗 New client connected: {client_id}")
            
            # Register client
            subscription = ClientSubscription(
                client_id=client_id,
                websocket=websocket,
                subscribed_metrics=[],
                update_frequency=1.0,
                last_update=datetime.now()
            )
            
            self.clients[client_id] = subscription
            self.active_connections.add(websocket)
            self.performance_stats['active_clients'] = len(self.active_connections)
            
            # Send welcome message
            await self.send_to_client(websocket, {
                'type': 'connection',
                'status': 'connected',
                'client_id': client_id,
                'available_metrics': list(self.data_providers.keys()),
                'server_time': datetime.now().isoformat()
            })
            
            # Handle client messages
            async for message in websocket:
                await self.handle_client_message(client_id, message)
                
        except ConnectionClosed:
            self.logger.info(f"🔌 Client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"❌ Error handling client {client_id}: {e}")
            self.performance_stats['errors'] += 1
        finally:
            # Cleanup client
            if client_id in self.clients:
                del self.clients[client_id]
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            self.performance_stats['active_clients'] = len(self.active_connections)
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self.handle_subscription(client_id, data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscription(client_id, data)
            elif message_type == 'configure':
                await self.handle_configuration(client_id, data)
            elif message_type == 'ping':
                await self.handle_ping(client_id)
            else:
                self.logger.warning(f"⚠️ Unknown message type from {client_id}: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error(f"❌ Invalid JSON from client {client_id}")
        except Exception as e:
            self.logger.error(f"❌ Error handling message from {client_id}: {e}")
    
    async def handle_subscription(self, client_id: str, data: Dict):
        """Handle client subscription requests"""
        if client_id not in self.clients:
            return
        
        metrics = data.get('metrics', [])
        frequency = data.get('frequency', 1.0)
        
        client = self.clients[client_id]
        client.subscribed_metrics = metrics
        client.update_frequency = max(0.1, min(frequency, 10.0))  # Limit frequency
        
        self.logger.info(f"📊 Client {client_id} subscribed to {len(metrics)} metrics")
        
        # Send confirmation
        await self.send_to_client(client.websocket, {
            'type': 'subscription_confirmed',
            'metrics': metrics,
            'frequency': client.update_frequency
        })
    
    async def handle_unsubscription(self, client_id: str, data: Dict):
        """Handle client unsubscription requests"""
        if client_id not in self.clients:
            return
        
        metrics_to_remove = data.get('metrics', [])
        client = self.clients[client_id]
        
        for metric in metrics_to_remove:
            if metric in client.subscribed_metrics:
                client.subscribed_metrics.remove(metric)
        
        self.logger.info(f"📊 Client {client_id} unsubscribed from {len(metrics_to_remove)} metrics")
    
    async def handle_configuration(self, client_id: str, data: Dict):
        """Handle client configuration updates"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        if 'frequency' in data:
            client.update_frequency = max(0.1, min(data['frequency'], 10.0))
        
        self.logger.info(f"⚙️ Client {client_id} configuration updated")
    
    async def handle_ping(self, client_id: str):
        """Handle ping requests"""
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        await self.send_to_client(client.websocket, {
            'type': 'pong',
            'server_time': datetime.now().isoformat()
        })
    
    async def send_to_client(self, websocket, data: Dict):
        """Send data to a specific client"""
        try:
            message = json.dumps(data, default=str)
            await websocket.send(message)
            
            # Update performance stats
            self.performance_stats['messages_sent'] += 1
            self.performance_stats['bytes_sent'] += len(message)
            
        except ConnectionClosed:
            pass  # Client disconnected
        except Exception as e:
            self.logger.error(f"❌ Error sending to client: {e}")
            self.performance_stats['errors'] += 1
    
    async def broadcast_to_subscribers(self, metric_id: str, metric_data: StreamingMetric):
        """Broadcast metric updates to subscribed clients"""
        if not self.active_connections:
            return
        
        message = {
            'type': 'metric_update',
            'data': asdict(metric_data)
        }
        
        # Send to subscribed clients
        for client in self.clients.values():
            if metric_id in client.subscribed_metrics and client.is_active:
                # Check if it's time to update this client
                time_since_update = (datetime.now() - client.last_update).total_seconds()
                if time_since_update >= client.update_frequency:
                    await self.send_to_client(client.websocket, message)
                    client.last_update = datetime.now()
    
    async def data_streaming_loop(self):
        """Main data streaming loop"""
        self.logger.info("🔄 Starting data streaming loop")
        
        while self.streaming_active:
            try:
                # Update all metrics
                for metric_id, provider_func in self.data_providers.items():
                    try:
                        # Get metric data
                        value = provider_func()
                        
                        # Determine priority and category
                        priority, category = self._get_metric_priority_category(metric_id)
                        
                        # Create streaming metric
                        metric = StreamingMetric(
                            metric_id=metric_id,
                            name=metric_id.replace('_', ' ').title(),
                            value=value,
                            timestamp=datetime.now(),
                            priority=priority,
                            category=category
                        )
                        
                        # Cache metric
                        self.metrics_cache[metric_id] = metric
                        self.metric_history[metric_id].append(metric)
                        
                        # Broadcast to subscribers
                        await self.broadcast_to_subscribers(metric_id, metric)
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error updating metric {metric_id}: {e}")
                        self.performance_stats['errors'] += 1
                
                # Wait before next update cycle
                await asyncio.sleep(0.1)  # 100ms base cycle
                
            except Exception as e:
                self.logger.error(f"❌ Error in streaming loop: {e}")
                await asyncio.sleep(1)
    
    def _get_metric_priority_category(self, metric_id: str) -> tuple:
        """Determine metric priority and category"""
        
        # Critical metrics (100ms updates)
        if metric_id in ['btc_price', 'eth_price', 'portfolio_value', 'system_status']:
            return 'critical', 'price' if 'price' in metric_id else 'portfolio'
        
        # High priority metrics (500ms updates)
        elif metric_id in ['daily_pnl', 'active_signals', 'portfolio_risk']:
            return 'high', 'portfolio' if 'portfolio' in metric_id else 'signal'
        
        # Medium priority metrics (1s updates)
        elif metric_id in ['volume_24h', 'open_positions', 'signal_strength']:
            return 'medium', 'volume' if 'volume' in metric_id else 'signal'
        
        # Low priority metrics (5s updates)
        else:
            return 'low', 'other'
    
    # Mock data provider functions (replace with real implementations)
    def _get_btc_price(self) -> float:
        """Get current BTC price"""
        # Mock implementation - replace with real API call
        base_price = 45000
        variation = np.random.normal(0, 100)
        return round(base_price + variation, 2)
    
    def _get_eth_price(self) -> float:
        """Get current ETH price"""
        base_price = 3000
        variation = np.random.normal(0, 50)
        return round(base_price + variation, 2)
    
    def _get_market_cap(self) -> float:
        """Get total market cap"""
        return round(np.random.uniform(1.8e12, 2.2e12), 0)
    
    def _get_volume_24h(self) -> float:
        """Get 24h trading volume"""
        return round(np.random.uniform(80e9, 120e9), 0)
    
    def _get_fear_greed_index(self) -> int:
        """Get Fear & Greed Index"""
        return np.random.randint(20, 80)
    
    def _get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        base_value = 100000
        variation = np.random.normal(0, 1000)
        return round(base_value + variation, 2)
    
    def _get_daily_pnl(self) -> float:
        """Get daily P&L"""
        return round(np.random.normal(500, 200), 2)
    
    def _get_open_positions(self) -> int:
        """Get number of open positions"""
        return np.random.randint(3, 8)
    
    def _get_available_balance(self) -> float:
        """Get available balance"""
        return round(np.random.uniform(10000, 50000), 2)
    
    def _get_active_signals(self) -> int:
        """Get number of active signals"""
        return np.random.randint(5, 15)
    
    def _get_signal_strength(self) -> float:
        """Get average signal strength"""
        return round(np.random.uniform(0.6, 0.9), 3)
    
    def _get_position_recommendations(self) -> List[Dict]:
        """Get position recommendations"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
        recommendations = []
        
        for symbol in np.random.choice(symbols, np.random.randint(2, 4), replace=False):
            recommendations.append({
                'symbol': symbol,
                'action': np.random.choice(['BUY', 'SELL', 'HOLD']),
                'confidence': round(np.random.uniform(0.7, 0.95), 3),
                'size': round(np.random.uniform(0.02, 0.08), 3)
            })
        
        return recommendations
    
    def _get_portfolio_risk(self) -> float:
        """Get portfolio risk score"""
        return round(np.random.uniform(0.3, 0.7), 3)
    
    def _get_var_95(self) -> float:
        """Get 95% Value at Risk"""
        return round(np.random.uniform(2000, 5000), 2)
    
    def _get_drawdown(self) -> float:
        """Get current drawdown"""
        return round(np.random.uniform(0.02, 0.08), 3)
    
    def _get_sharpe_ratio(self) -> float:
        """Get Sharpe ratio"""
        return round(np.random.uniform(1.2, 2.5), 2)
    
    def _get_system_status(self) -> str:
        """Get system status"""
        statuses = ['online', 'trading', 'monitoring', 'maintenance']
        return np.random.choice(statuses)
    
    def _get_api_latency(self) -> float:
        """Get API latency in ms"""
        return round(np.random.uniform(50, 200), 1)
    
    def _get_error_rate(self) -> float:
        """Get error rate percentage"""
        return round(np.random.uniform(0.1, 2.0), 2)
    
    def get_performance_stats(self) -> Dict:
        """Get streaming performance statistics"""
        uptime = (datetime.now() - self.performance_stats['uptime_start']).total_seconds()
        
        return {
            **self.performance_stats,
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'messages_per_second': self.performance_stats['messages_sent'] / max(uptime, 1),
            'bytes_per_second': self.performance_stats['bytes_sent'] / max(uptime, 1),
            'error_rate': (self.performance_stats['errors'] / max(self.performance_stats['messages_sent'], 1)) * 100
        }
    
    def stop_streaming(self):
        """Stop the streaming system"""
        self.streaming_active = False
        self.logger.info("🛑 WebSocket streaming stopped")

class WebSocketDashboardClient:
    """Client-side WebSocket handler for dashboards"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.subscribed_metrics = []
        self.message_handlers = {}
        self.logger = logging.getLogger('WebSocketClient')
        
        # Data storage
        self.latest_data = {}
        self.data_callbacks = {}
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            self.logger.info(f"🔗 Connected to WebSocket server: {self.server_url}")
            
            # Start message handling loop
            asyncio.create_task(self.message_loop())
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to WebSocket server: {e}")
            raise
    
    async def message_loop(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except ConnectionClosed:
            self.connected = False
            self.logger.info("🔌 WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"❌ Error in message loop: {e}")
    
    async def handle_message(self, data: Dict):
        """Handle incoming message"""
        message_type = data.get('type')
        
        if message_type == 'metric_update':
            await self.handle_metric_update(data['data'])
        elif message_type == 'connection':
            self.logger.info(f"✅ Connection confirmed: {data.get('status')}")
        elif message_type == 'subscription_confirmed':
            self.logger.info(f"📊 Subscription confirmed for {len(data.get('metrics', []))} metrics")
        
        # Call custom handlers
        if message_type in self.message_handlers:
            await self.message_handlers[message_type](data)
    
    async def handle_metric_update(self, metric_data: Dict):
        """Handle metric update"""
        metric_id = metric_data['metric_id']
        self.latest_data[metric_id] = metric_data
        
        # Call data callbacks
        if metric_id in self.data_callbacks:
            for callback in self.data_callbacks[metric_id]:
                try:
                    callback(metric_data)
                except Exception as e:
                    self.logger.error(f"❌ Error in data callback for {metric_id}: {e}")
    
    async def subscribe(self, metrics: List[str], frequency: float = 1.0):
        """Subscribe to metrics"""
        if not self.connected:
            raise ConnectionError("Not connected to WebSocket server")
        
        message = {
            'type': 'subscribe',
            'metrics': metrics,
            'frequency': frequency
        }
        
        await self.websocket.send(json.dumps(message))
        self.subscribed_metrics.extend(metrics)
        self.logger.info(f"📊 Subscribed to {len(metrics)} metrics")
    
    async def unsubscribe(self, metrics: List[str]):
        """Unsubscribe from metrics"""
        if not self.connected:
            return
        
        message = {
            'type': 'unsubscribe',
            'metrics': metrics
        }
        
        await self.websocket.send(json.dumps(message))
        for metric in metrics:
            if metric in self.subscribed_metrics:
                self.subscribed_metrics.remove(metric)
    
    def register_data_callback(self, metric_id: str, callback: Callable):
        """Register callback for metric updates"""
        if metric_id not in self.data_callbacks:
            self.data_callbacks[metric_id] = []
        self.data_callbacks[metric_id].append(callback)
    
    def get_latest_data(self, metric_id: str) -> Optional[Dict]:
        """Get latest data for a metric"""
        return self.latest_data.get(metric_id)
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False

async def main():
    """Demonstration of WebSocket streaming system"""
    
    print("🌐 WEBSOCKET REAL-TIME DATA STREAMING SYSTEM")
    print("=" * 60)
    
    # Initialize streamer
    streamer = WebSocketDataStreamer()
    
    print(f"🚀 Starting WebSocket server on {streamer.host}:{streamer.port}")
    print(f"📊 Available metrics: {len(streamer.data_providers)}")
    print(f"⚡ Update frequencies: {streamer.update_frequencies}")
    
    try:
        # Start the server
        await streamer.start_server()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down WebSocket server...")
        streamer.stop_streaming()
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 