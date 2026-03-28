// API Service for React GUI Integration
import io from 'socket.io-client';

const API_BASE_URL = 'http://localhost:5000';

class TradingBotAPI {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.eventHandlers = new Map();
  }

  // Initialize WebSocket connection
  initializeSocket() {
    if (this.socket) {
      this.socket.disconnect();
    }

    this.socket = io(API_BASE_URL, {
      transports: ['websocket', 'polling']
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to trading bot backend');
      this.isConnected = true;
      this.emit('connection_status', { connected: true });
    });

    this.socket.on('disconnect', () => {
      console.log('❌ Disconnected from trading bot backend');
      this.isConnected = false;
      this.emit('connection_status', { connected: false });
    });

    // Handle real-time updates
    this.socket.on('market_update', (data) => {
      this.emit('market_update', data);
    });

    this.socket.on('portfolio_update', (data) => {
      this.emit('portfolio_update', data);
    });

    this.socket.on('bot_stats_update', (data) => {
      this.emit('bot_stats_update', data);
    });

    this.socket.on('signals_update', (data) => {
      this.emit('signals_update', data);
    });

    this.socket.on('new_trade', (data) => {
      this.emit('new_trade', data);
    });

    return this.socket;
  }

  // Event emitter methods
  on(event, handler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event).push(handler);
  }

  off(event, handler) {
    if (this.eventHandlers.has(event)) {
      const handlers = this.eventHandlers.get(event);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.eventHandlers.has(event)) {
      this.eventHandlers.get(event).forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  // API Methods
  async makeRequest(endpoint, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Bot Control Methods
  async getBotStatus() {
    return this.makeRequest('/api/bot/status');
  }

  async controlBot(action) {
    return this.makeRequest('/api/bot/control', {
      method: 'POST',
      body: JSON.stringify({ action })
    });
  }

  async updateStrategy(strategy) {
    return this.makeRequest('/api/bot/strategy', {
      method: 'POST',
      body: JSON.stringify({ strategy })
    });
  }

  // Market Data Methods
  async getMarketOverview() {
    return this.makeRequest('/api/market/overview');
  }

  // Portfolio Methods
  async getPortfolio() {
    return this.makeRequest('/api/portfolio');
  }

  // Trading Methods
  async getTradeHistory(limit = 50) {
    return this.makeRequest(`/api/trades/history?limit=${limit}`);
  }

  async getActiveSignals() {
    return this.makeRequest('/api/signals/active');
  }

  // Manual trading via WebSocket
  executeManualTrade(symbol, action, amount) {
    if (this.socket && this.isConnected) {
      this.socket.emit('manual_trade', { symbol, action, amount });
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  // Configuration Methods
  async getConfig() {
    return this.makeRequest('/api/config');
  }

  async updateConfig(config) {
    return this.makeRequest('/api/config', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }

  // Utility Methods
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }
}

// Create singleton instance
const tradingBotAPI = new TradingBotAPI();

// React Hooks for API integration
export const useTradingBotAPI = () => {
  return tradingBotAPI;
};

export const useSocket = () => {
  return tradingBotAPI.socket;
};

export const useRealTimeData = (eventType, handler) => {
  React.useEffect(() => {
    tradingBotAPI.on(eventType, handler);
    return () => {
      tradingBotAPI.off(eventType, handler);
    };
  }, [eventType, handler]);
};

export default tradingBotAPI; 