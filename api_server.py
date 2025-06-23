from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
import hashlib
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
from functools import wraps
import logging
from typing import Dict, List, Optional
import redis
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Import your trading bot components
try:
    from ai_trading_bot_simple import AITradingBot as TradingBot
    from utils import calculate_technical_indicators, calculate_performance_metrics
    from redis_utils import RedisManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Some features may not be available")
    TradingBot = None

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('API_SECRET_KEY', 'your-secret-key-change-this')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-this')

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Global variables
trading_bot = None
bot_thread = None
bot_running = False
redis_manager = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis connection
try:
    redis_manager = RedisManager()
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_manager = None

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)
    return decorated

# Database setup for API users
def init_db():
    conn = sqlite3.connect('api_users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  api_key TEXT UNIQUE NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active BOOLEAN DEFAULT 1)''')
    
    # Create default admin user if not exists
    admin_exists = c.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',)).fetchone()[0]
    if admin_exists == 0:
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        password_hash = generate_password_hash(admin_password)
        api_key = hashlib.sha256(f"admin{datetime.now()}".encode()).hexdigest()
        c.execute('INSERT INTO users (username, password_hash, api_key) VALUES (?, ?, ?)',
                  ('admin', password_hash, api_key))
        print(f"Default admin user created with API key: {api_key}")
    
    conn.commit()
    conn.close()

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    
    conn = sqlite3.connect('api_users.db')
    c = conn.cursor()
    user = c.execute('SELECT password_hash, api_key FROM users WHERE username = ? AND is_active = 1',
                     (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user[0], password):
        token = jwt.encode({
            'username': username,
            'api_key': user[1],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'api_key': user[1],
            'expires_in': 86400  # 24 hours
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("3 per hour")
def register():
    """Register new API user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    
    if len(password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    
    conn = sqlite3.connect('api_users.db')
    c = conn.cursor()
    
    # Check if user exists
    existing = c.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,)).fetchone()[0]
    if existing > 0:
        conn.close()
        return jsonify({'message': 'Username already exists'}), 409
    
    # Create new user
    password_hash = generate_password_hash(password)
    api_key = hashlib.sha256(f"{username}{datetime.now()}".encode()).hexdigest()
    
    try:
        c.execute('INSERT INTO users (username, password_hash, api_key) VALUES (?, ?, ?)',
                  (username, password_hash, api_key))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'User created successfully',
            'api_key': api_key
        }), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Error creating user'}), 500

# Bot Control Endpoints
@app.route('/api/bot/start', methods=['POST'])
@token_required
def start_bot():
    """Start the trading bot"""
    global trading_bot, bot_thread, bot_running
    
    if bot_running:
        return jsonify({'message': 'Bot is already running', 'status': 'running'}), 200
    
    try:
        if TradingBot is None:
            return jsonify({'message': 'Trading bot not available - check imports', 'status': 'error'}), 500
            
        data = request.get_json() or {}
        config = {
            'trading_mode': data.get('trading_mode', 'paper'),
            'symbols': data.get('symbols', ['BTC/USDT']),
            'timeframe': data.get('timeframe', '1h'),
            'trade_amount': data.get('trade_amount', 100)
        }
        
        trading_bot = TradingBot()
        bot_running = True
        
        def run_bot():
            try:
                trading_bot.run()
            except Exception as e:
                logger.error(f"Bot error: {e}")
                global bot_running
                bot_running = False
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        return jsonify({
            'message': 'Bot started successfully',
            'status': 'running',
            'config': config
        })
    except Exception as e:
        return jsonify({'message': f'Error starting bot: {str(e)}'}), 500

@app.route('/api/bot/stop', methods=['POST'])
@token_required
def stop_bot():
    """Stop the trading bot"""
    global trading_bot, bot_running
    
    if not bot_running:
        return jsonify({'message': 'Bot is not running', 'status': 'stopped'}), 200
    
    try:
        bot_running = False
        if trading_bot:
            trading_bot.stop()
        
        return jsonify({
            'message': 'Bot stopped successfully',
            'status': 'stopped'
        })
    except Exception as e:
        return jsonify({'message': f'Error stopping bot: {str(e)}'}), 500

@app.route('/api/bot/status', methods=['GET'])
@token_required
def get_bot_status():
    """Get current bot status"""
    global bot_running, trading_bot
    
    status = {
        'running': bot_running,
        'uptime': None,
        'last_trade': None,
        'total_trades': 0,
        'current_balance': 0,
        'profit_loss': 0
    }
    
    if trading_bot and bot_running:
        try:
            # Get bot statistics
            stats = trading_bot.get_statistics()
            status.update(stats)
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
    
    return jsonify(status)

@app.route('/api/bot/restart', methods=['POST'])
@token_required
def restart_bot():
    """Restart the trading bot"""
    # Stop the bot first
    stop_response = stop_bot()
    if stop_response[1] not in [200]:
        return stop_response
    
    # Wait a moment
    time.sleep(2)
    
    # Start the bot again
    return start_bot()

# Trading Data Endpoints
@app.route('/api/trades', methods=['GET'])
@token_required
def get_trades():
    """Get trading history"""
    try:
        # Parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Load trades from file or database
        trades_file = 'logs/trades.json'
        if os.path.exists(trades_file):
            with open(trades_file, 'r') as f:
                trades = json.load(f)
        else:
            trades = []
        
        # Filter trades
        filtered_trades = trades
        if symbol:
            filtered_trades = [t for t in filtered_trades if t.get('symbol') == symbol]
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_trades = [t for t in filtered_trades 
                             if datetime.fromisoformat(t.get('timestamp', '1970-01-01')) >= start_dt]
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_trades = [t for t in filtered_trades 
                             if datetime.fromisoformat(t.get('timestamp', '1970-01-01')) <= end_dt]
        
        # Pagination
        total = len(filtered_trades)
        paginated_trades = filtered_trades[offset:offset + limit]
        
        return jsonify({
            'trades': paginated_trades,
            'total': total,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        return jsonify({'message': f'Error fetching trades: {str(e)}'}), 500

@app.route('/api/trades/stats', methods=['GET'])
@token_required
def get_trade_stats():
    """Get trading statistics"""
    try:
        trades_file = 'logs/trades.json'
        if os.path.exists(trades_file):
            with open(trades_file, 'r') as f:
                trades = json.load(f)
        else:
            trades = []
        
        if not trades:
            return jsonify({
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'average_profit': 0,
                'average_loss': 0
            })
        
        # Calculate statistics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('profit_loss', 0) > 0])
        losing_trades = len([t for t in trades if t.get('profit_loss', 0) < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profits = [t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) > 0]
        losses = [t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) < 0]
        
        total_profit_loss = sum([t.get('profit_loss', 0) for t in trades])
        average_profit = sum(profits) / len(profits) if profits else 0
        average_loss = sum(losses) / len(losses) if losses else 0
        
        return jsonify({
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_profit_loss': round(total_profit_loss, 2),
            'average_profit': round(average_profit, 2),
            'average_loss': round(average_loss, 2)
        })
    except Exception as e:
        return jsonify({'message': f'Error calculating stats: {str(e)}'}), 500

# Market Data Endpoints
@app.route('/api/market/price/<symbol>', methods=['GET'])
@token_required
def get_current_price(symbol):
    """Get current price for a symbol"""
    try:
        if trading_bot and hasattr(trading_bot, 'exchange'):
            ticker = trading_bot.exchange.fetch_ticker(symbol)
            return jsonify({
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'timestamp': ticker['timestamp']
            })
        else:
            return jsonify({'message': 'Trading bot not initialized'}), 503
    except Exception as e:
        return jsonify({'message': f'Error fetching price: {str(e)}'}), 500

@app.route('/api/market/ohlcv/<symbol>', methods=['GET'])
@token_required
def get_ohlcv_data(symbol):
    """Get OHLCV data for a symbol"""
    try:
        timeframe = request.args.get('timeframe', '1h')
        limit = request.args.get('limit', 100, type=int)
        
        if trading_bot and hasattr(trading_bot, 'exchange'):
            ohlcv = trading_bot.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to more readable format
            data = []
            for candle in ohlcv:
                data.append({
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0] / 1000).isoformat(),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return jsonify({
                'symbol': symbol,
                'timeframe': timeframe,
                'data': data
            })
        else:
            return jsonify({'message': 'Trading bot not initialized'}), 503
    except Exception as e:
        return jsonify({'message': f'Error fetching OHLCV data: {str(e)}'}), 500

@app.route('/api/market/indicators/<symbol>', methods=['GET'])
@token_required
def get_technical_indicators(symbol):
    """Get technical indicators for a symbol"""
    try:
        timeframe = request.args.get('timeframe', '1h')
        
        if trading_bot and hasattr(trading_bot, 'exchange'):
            # Fetch OHLCV data
            ohlcv = trading_bot.exchange.fetch_ohlcv(symbol, timeframe, limit=200)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate technical indicators
            indicators = calculate_technical_indicators(df)
            
            # Get the latest values
            latest_indicators = {}
            for key, values in indicators.items():
                if hasattr(values, 'iloc'):
                    latest_indicators[key] = float(values.iloc[-1]) if not pd.isna(values.iloc[-1]) else None
                else:
                    latest_indicators[key] = float(values) if not pd.isna(values) else None
            
            return jsonify({
                'symbol': symbol,
                'timeframe': timeframe,
                'indicators': latest_indicators,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'message': 'Trading bot not initialized'}), 503
    except Exception as e:
        return jsonify({'message': f'Error calculating indicators: {str(e)}'}), 500

# Portfolio Endpoints
@app.route('/api/portfolio/balance', methods=['GET'])
@token_required
def get_portfolio_balance():
    """Get current portfolio balance"""
    try:
        if trading_bot and hasattr(trading_bot, 'exchange'):
            balance = trading_bot.exchange.fetch_balance()
            
            # Filter out zero balances
            non_zero_balance = {}
            for currency, amounts in balance.items():
                if currency not in ['info', 'free', 'used', 'total']:
                    if amounts['total'] > 0:
                        non_zero_balance[currency] = amounts
            
            return jsonify({
                'balance': non_zero_balance,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'message': 'Trading bot not initialized'}), 503
    except Exception as e:
        return jsonify({'message': f'Error fetching balance: {str(e)}'}), 500

@app.route('/api/portfolio/positions', methods=['GET'])
@token_required
def get_open_positions():
    """Get current open positions"""
    try:
        if trading_bot and hasattr(trading_bot, 'get_open_positions'):
            positions = trading_bot.get_open_positions()
            return jsonify({
                'positions': positions,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'positions': [], 'message': 'No positions available'})
    except Exception as e:
        return jsonify({'message': f'Error fetching positions: {str(e)}'}), 500

# Configuration Endpoints
@app.route('/api/config', methods=['GET'])
@token_required
def get_config():
    """Get current bot configuration"""
    try:
        config = {}
        if trading_bot:
            config = trading_bot.get_config()
        
        return jsonify({
            'config': config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'message': f'Error fetching config: {str(e)}'}), 500

@app.route('/api/config', methods=['PUT'])
@token_required
def update_config():
    """Update bot configuration"""
    try:
        new_config = request.get_json()
        
        if trading_bot and hasattr(trading_bot, 'update_config'):
            trading_bot.update_config(new_config)
            return jsonify({
                'message': 'Configuration updated successfully',
                'config': new_config
            })
        else:
            return jsonify({'message': 'Bot not available for configuration'}), 503
    except Exception as e:
        return jsonify({'message': f'Error updating config: {str(e)}'}), 500

# Logs Endpoints
@app.route('/api/logs', methods=['GET'])
@token_required
def get_logs():
    """Get bot logs"""
    try:
        log_type = request.args.get('type', 'main')  # main, trades, errors
        lines = request.args.get('lines', 100, type=int)
        
        log_files = {
            'main': 'logs/trading_bot.log',
            'trades': 'logs/trades.log',
            'errors': 'logs/errors.log'
        }
        
        log_file = log_files.get(log_type, log_files['main'])
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
            return jsonify({
                'logs': [line.strip() for line in recent_lines],
                'total_lines': len(all_lines),
                'returned_lines': len(recent_lines),
                'log_type': log_type
            })
        else:
            return jsonify({
                'logs': [],
                'message': f'Log file {log_file} not found'
            })
    except Exception as e:
        return jsonify({'message': f'Error fetching logs: {str(e)}'}), 500

# Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'bot_running': bot_running
    })

# API Documentation
@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'title': 'AI Trading Bot API',
        'version': '1.0.0',
        'description': 'REST API for controlling and monitoring the AI trading bot',
        'endpoints': {
            'Authentication': {
                'POST /api/auth/login': 'Login and get JWT token',
                'POST /api/auth/register': 'Register new API user'
            },
            'Bot Control': {
                'POST /api/bot/start': 'Start the trading bot',
                'POST /api/bot/stop': 'Stop the trading bot',
                'GET /api/bot/status': 'Get bot status',
                'POST /api/bot/restart': 'Restart the trading bot'
            },
            'Trading Data': {
                'GET /api/trades': 'Get trading history',
                'GET /api/trades/stats': 'Get trading statistics'
            },
            'Market Data': {
                'GET /api/market/price/<symbol>': 'Get current price',
                'GET /api/market/ohlcv/<symbol>': 'Get OHLCV data',
                'GET /api/market/indicators/<symbol>': 'Get technical indicators'
            },
            'Portfolio': {
                'GET /api/portfolio/balance': 'Get portfolio balance',
                'GET /api/portfolio/positions': 'Get open positions'
            },
            'Configuration': {
                'GET /api/config': 'Get bot configuration',
                'PUT /api/config': 'Update bot configuration'
            },
            'Logs': {
                'GET /api/logs': 'Get bot logs'
            },
            'Utility': {
                'GET /api/health': 'Health check',
                'GET /api/docs': 'API documentation'
            }
        },
        'authentication': {
            'type': 'JWT Bearer Token',
            'header': 'Authorization: Bearer <token>',
            'login_endpoint': '/api/auth/login'
        }
    }
    return jsonify(docs)

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Configuration
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting AI Trading Bot API on {host}:{port}")
    print("API Documentation available at: /api/docs")
    print("Health check available at: /api/health")
    
    app.run(host=host, port=port, debug=debug) 