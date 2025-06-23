import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

class TradingBotAPIClient:
    """
    Python client for the AI Trading Bot API
    """
    
    def __init__(self, base_url: str = "http://localhost:5000", api_key: str = None, token: str = None):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the API server
            api_key: API key for authentication
            token: JWT token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.token = token
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TradingBot-API-Client/1.0'
        })
        
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """
        Make HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from API")
    
    # Authentication methods
    def login(self, username: str, password: str) -> Dict:
        """
        Login and get JWT token
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Login response with token
        """
        data = {
            'username': username,
            'password': password
        }
        
        response = self._make_request('POST', '/api/auth/login', data)
        
        if 'token' in response:
            self.token = response['token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
        
        return response
    
    def register(self, username: str, password: str) -> Dict:
        """
        Register new API user
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Registration response
        """
        data = {
            'username': username,
            'password': password
        }
        
        return self._make_request('POST', '/api/auth/register', data)
    
    # Bot control methods
    def start_bot(self, config: Dict = None) -> Dict:
        """
        Start the trading bot
        
        Args:
            config: Bot configuration
            
        Returns:
            Start response
        """
        return self._make_request('POST', '/api/bot/start', config or {})
    
    def stop_bot(self) -> Dict:
        """
        Stop the trading bot
        
        Returns:
            Stop response
        """
        return self._make_request('POST', '/api/bot/stop')
    
    def restart_bot(self) -> Dict:
        """
        Restart the trading bot
        
        Returns:
            Restart response
        """
        return self._make_request('POST', '/api/bot/restart')
    
    def get_bot_status(self) -> Dict:
        """
        Get current bot status
        
        Returns:
            Bot status information
        """
        return self._make_request('GET', '/api/bot/status')
    
    # Trading data methods
    def get_trades(self, limit: int = 100, offset: int = 0, symbol: str = None, 
                   start_date: str = None, end_date: str = None) -> Dict:
        """
        Get trading history
        
        Args:
            limit: Number of trades to return
            offset: Offset for pagination
            symbol: Filter by symbol
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            Trading history
        """
        params = {'limit': limit, 'offset': offset}
        if symbol:
            params['symbol'] = symbol
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/api/trades', params=params)
    
    def get_trade_stats(self) -> Dict:
        """
        Get trading statistics
        
        Returns:
            Trading statistics
        """
        return self._make_request('GET', '/api/trades/stats')
    
    # Market data methods
    def get_current_price(self, symbol: str) -> Dict:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Current price data
        """
        return self._make_request('GET', f'/api/market/price/{symbol}')
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Dict:
        """
        Get OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of candles to return
            
        Returns:
            OHLCV data
        """
        params = {'timeframe': timeframe, 'limit': limit}
        return self._make_request('GET', f'/api/market/ohlcv/{symbol}', params=params)
    
    def get_technical_indicators(self, symbol: str, timeframe: str = '1h') -> Dict:
        """
        Get technical indicators for a symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Technical indicators
        """
        params = {'timeframe': timeframe}
        return self._make_request('GET', f'/api/market/indicators/{symbol}', params=params)
    
    # Portfolio methods
    def get_portfolio_balance(self) -> Dict:
        """
        Get current portfolio balance
        
        Returns:
            Portfolio balance
        """
        return self._make_request('GET', '/api/portfolio/balance')
    
    def get_open_positions(self) -> Dict:
        """
        Get current open positions
        
        Returns:
            Open positions
        """
        return self._make_request('GET', '/api/portfolio/positions')
    
    # Configuration methods
    def get_config(self) -> Dict:
        """
        Get current bot configuration
        
        Returns:
            Bot configuration
        """
        return self._make_request('GET', '/api/config')
    
    def update_config(self, config: Dict) -> Dict:
        """
        Update bot configuration
        
        Args:
            config: New configuration
            
        Returns:
            Update response
        """
        return self._make_request('PUT', '/api/config', config)
    
    # Logs methods
    def get_logs(self, log_type: str = 'main', lines: int = 100) -> Dict:
        """
        Get bot logs
        
        Args:
            log_type: Type of logs (main, trades, errors)
            lines: Number of lines to return
            
        Returns:
            Log data
        """
        params = {'type': log_type, 'lines': lines}
        return self._make_request('GET', '/api/logs', params=params)
    
    # Utility methods
    def health_check(self) -> Dict:
        """
        Check API health
        
        Returns:
            Health status
        """
        return self._make_request('GET', '/api/health')
    
    def get_api_docs(self) -> Dict:
        """
        Get API documentation
        
        Returns:
            API documentation
        """
        return self._make_request('GET', '/api/docs')
    
    # Convenience methods
    def wait_for_bot_status(self, target_status: str, timeout: int = 60) -> bool:
        """
        Wait for bot to reach a specific status
        
        Args:
            target_status: Target status ('running' or 'stopped')
            timeout: Timeout in seconds
            
        Returns:
            True if status reached, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_bot_status()
                current_status = 'running' if status.get('running') else 'stopped'
                
                if current_status == target_status:
                    return True
                
                time.sleep(1)
            except Exception:
                time.sleep(1)
        
        return False
    
    def get_latest_trades(self, count: int = 10) -> List[Dict]:
        """
        Get the latest trades
        
        Args:
            count: Number of latest trades to return
            
        Returns:
            List of latest trades
        """
        response = self.get_trades(limit=count)
        return response.get('trades', [])
    
    def get_symbol_performance(self, symbol: str, days: int = 7) -> Dict:
        """
        Get performance metrics for a specific symbol
        
        Args:
            symbol: Trading symbol
            days: Number of days to analyze
            
        Returns:
            Performance metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        trades_response = self.get_trades(
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        trades = trades_response.get('trades', [])
        
        if not trades:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'profit_loss': 0,
                'win_rate': 0
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('profit_loss', 0) > 0])
        total_profit_loss = sum([t.get('profit_loss', 0) for t in trades])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'symbol': symbol,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'profit_loss': round(total_profit_loss, 2),
            'win_rate': round(win_rate, 2),
            'period_days': days
        }

# Example usage
if __name__ == '__main__':
    # Initialize client
    client = TradingBotAPIClient('http://localhost:5000')
    
    try:
        # Check API health
        health = client.health_check()
        print(f"API Health: {health}")
        
        # Login (you'll need to register first or use default admin credentials)
        # login_response = client.login('admin', 'admin123')
        # print(f"Login: {login_response}")
        
        # Get bot status
        # status = client.get_bot_status()
        # print(f"Bot Status: {status}")
        
        # Get current price
        # price = client.get_current_price('BTC/USDT')
        # print(f"BTC Price: {price}")
        
        # Get trading stats
        # stats = client.get_trade_stats()
        # print(f"Trading Stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}") 