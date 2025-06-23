#!/usr/bin/env python3
"""
API Extension for Advanced Trading Strategies
Adds educational trading strategies to the existing API server
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional

# Import the advanced strategies
try:
    from advanced_trading_strategies import AdvancedTradingStrategies, TradingSignal, RiskLevel, StrategyType
    from integrate_strategies import IntegratedTradingBot
except ImportError as e:
    print(f"Error importing strategies: {e}")
    AdvancedTradingStrategies = None
    IntegratedTradingBot = None

# Create Blueprint for strategies
strategies_bp = Blueprint('strategies', __name__, url_prefix='/api/strategies')

# Global strategy instance
strategy_engine = None
integrated_bot = None

def init_strategies():
    """Initialize the strategy engine"""
    global strategy_engine, integrated_bot
    
    if AdvancedTradingStrategies:
        strategy_engine = AdvancedTradingStrategies()
        
        # Configuration for integrated bot
        config = {
            'portfolio_value': 10000,
            'max_daily_loss': 0.05,
            'max_positions': 5,
            'enabled_strategies': [
                'moving_average_crossover',
                'rsi_oversold_overbought',
                'scalping',
                'memecoin_momentum'
            ]
        }
        
        if IntegratedTradingBot:
            integrated_bot = IntegratedTradingBot(config)

@strategies_bp.route('/health', methods=['GET'])
def strategies_health():
    """Health check for strategies module"""
    return jsonify({
        'status': 'healthy',
        'strategies_available': strategy_engine is not None,
        'integrated_bot_available': integrated_bot is not None,
        'timestamp': datetime.now().isoformat()
    })

@strategies_bp.route('/list', methods=['GET'])
def list_strategies():
    """List all available trading strategies"""
    if not strategy_engine:
        return jsonify({'error': 'Strategy engine not available'}), 500
    
    strategies = [
        {
            'name': 'Moving Average Crossover',
            'type': 'ma_crossover',
            'description': 'Golden Cross and Death Cross signals using moving averages',
            'risk_level': 'Low to High',
            'timeframe': 'Medium to Long term',
            'suitable_for': ['BTC', 'ETH', 'Major Altcoins']
        },
        {
            'name': 'RSI Oversold/Overbought',
            'type': 'rsi_levels',
            'description': 'Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought)',
            'risk_level': 'Low to High',
            'timeframe': 'Short to Medium term',
            'suitable_for': ['All cryptocurrencies']
        },
        {
            'name': 'Scalping Strategy',
            'type': 'scalping',
            'description': 'High-frequency trading for small price changes',
            'risk_level': 'Low to Medium',
            'timeframe': 'Very Short term',
            'suitable_for': ['BTC', 'ETH', 'High liquidity assets']
        },
        {
            'name': 'Memecoin Momentum',
            'type': 'memecoin_momentum',
            'description': 'EXTREME RISK: Momentum trading for memecoins',
            'risk_level': 'EXTREME',
            'timeframe': 'Very Short term',
            'suitable_for': ['Memecoins only - VERY RISKY']
        },
        {
            'name': 'Dollar Cost Averaging',
            'type': 'dca',
            'description': 'Regular purchases regardless of price',
            'risk_level': 'Low to Medium',
            'timeframe': 'Long term',
            'suitable_for': ['BTC', 'ETH', 'Stable projects']
        }
    ]
    
    return jsonify({
        'strategies': strategies,
        'total_count': len(strategies),
        'disclaimer': 'Educational purposes only. High risk of loss.'
    })

@strategies_bp.route('/analyze', methods=['POST'])
def analyze_signals():
    """Analyze trading signals for given symbols"""
    if not integrated_bot:
        return jsonify({'error': 'Integrated bot not available'}), 500
    
    try:
        data = request.get_json()
        symbols = data.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        execute_trades = data.get('execute_trades', False)
        
        # Validate symbols
        if not isinstance(symbols, list) or len(symbols) == 0:
            return jsonify({'error': 'Invalid symbols list'}), 400
        
        # Run analysis
        results = integrated_bot.run_analysis(symbols, execute_trades=execute_trades)
        
        # Convert datetime objects to strings for JSON serialization
        if 'timestamp' in results:
            results['timestamp'] = results['timestamp'].isoformat()
        
        # Convert any datetime objects in executed trades
        for trade in results.get('executed_trades', []):
            if 'signal' in trade and hasattr(trade['signal'], 'timestamp'):
                trade['signal_timestamp'] = trade['signal'].timestamp.isoformat()
        
        return jsonify({
            'success': True,
            'results': results,
            'disclaimer': 'Educational simulation only. Not financial advice.'
        })
        
    except Exception as e:
        logging.error(f"Error in analyze_signals: {e}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/risk-assessment', methods=['POST'])
def assess_risk():
    """Assess risk level for given symbols"""
    if not strategy_engine:
        return jsonify({'error': 'Strategy engine not available'}), 500
    
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        assessments = []
        for symbol in symbols:
            risk_level = strategy_engine.classify_asset_risk(symbol)
            risk_params = strategy_engine.risk_params[risk_level]
            
            assessment = {
                'symbol': symbol,
                'risk_level': risk_level.value,
                'max_position_size': f"{risk_params.max_position_size:.1%}",
                'stop_loss_percentage': f"{risk_params.stop_loss_percentage:.1%}",
                'take_profit_percentage': f"{risk_params.take_profit_percentage:.1%}",
                'risk_reward_ratio': risk_params.risk_reward_ratio,
                'warnings': []
            }
            
            # Add warnings based on risk level
            if risk_level == RiskLevel.EXTREME:
                assessment['warnings'] = [
                    "EXTREME RISK: Memecoins are highly speculative",
                    "Prone to pump-and-dump schemes",
                    "Can lose 90%+ of value rapidly",
                    "Only invest what you can afford to lose entirely"
                ]
            elif risk_level == RiskLevel.HIGH:
                assessment['warnings'] = [
                    "HIGH RISK: Smaller altcoins are volatile",
                    "Lower liquidity may affect trading",
                    "Higher chance of significant losses"
                ]
            elif risk_level == RiskLevel.MEDIUM:
                assessment['warnings'] = [
                    "MEDIUM RISK: Established altcoins but still volatile",
                    "Market cap and adoption provide some stability"
                ]
            else:
                assessment['warnings'] = [
                    "LOW RISK: Major cryptocurrencies with high liquidity",
                    "Still subject to crypto market volatility"
                ]
            
            assessments.append(assessment)
        
        return jsonify({
            'assessments': assessments,
            'disclaimer': 'Risk assessment is educational only. Always do your own research.'
        })
        
    except Exception as e:
        logging.error(f"Error in assess_risk: {e}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/portfolio-summary', methods=['GET'])
def portfolio_summary():
    """Get current portfolio summary"""
    if not integrated_bot:
        return jsonify({'error': 'Integrated bot not available'}), 500
    
    try:
        summary = integrated_bot.get_portfolio_summary()
        return jsonify({
            'success': True,
            'portfolio': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in portfolio_summary: {e}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/strategy-config', methods=['GET', 'POST'])
def strategy_config():
    """Get or update strategy configuration"""
    if not integrated_bot:
        return jsonify({'error': 'Integrated bot not available'}), 500
    
    try:
        if request.method == 'GET':
            # Return current configuration
            config = {
                'portfolio_value': integrated_bot.portfolio_value,
                'max_daily_loss': integrated_bot.max_daily_loss,
                'max_positions': integrated_bot.max_positions,
                'enabled_strategies': integrated_bot.enabled_strategies
            }
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            # Update configuration
            data = request.get_json()
            
            if 'portfolio_value' in data:
                integrated_bot.portfolio_value = float(data['portfolio_value'])
            
            if 'max_daily_loss' in data:
                integrated_bot.max_daily_loss = float(data['max_daily_loss'])
            
            if 'max_positions' in data:
                integrated_bot.max_positions = int(data['max_positions'])
            
            if 'enabled_strategies' in data:
                integrated_bot.enabled_strategies = data['enabled_strategies']
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            })
            
    except Exception as e:
        logging.error(f"Error in strategy_config: {e}")
        return jsonify({'error': str(e)}), 500

@strategies_bp.route('/educational-info', methods=['GET'])
def educational_info():
    """Get educational information about trading strategies"""
    
    educational_content = {
        'disclaimer': {
            'title': 'IMPORTANT DISCLAIMER',
            'content': [
                'This information is for educational purposes only',
                'Not financial advice - consult a qualified professional',
                'Trading involves substantial risk of loss',
                'Never invest more than you can afford to lose',
                'Past performance does not guarantee future results'
            ]
        },
        'risk_management': {
            'title': 'Risk Management Principles',
            'principles': [
                'Only invest what you can afford to lose',
                'Diversify your portfolio across different assets',
                'Set stop-loss orders to limit potential losses',
                'Take profit orders to secure gains',
                'Position sizing based on risk tolerance',
                'Avoid emotional trading decisions'
            ]
        },
        'strategy_explanations': {
            'moving_averages': {
                'title': 'Moving Average Crossovers',
                'description': 'Uses intersection of short and long-term moving averages',
                'golden_cross': 'Short MA crosses above Long MA (bullish signal)',
                'death_cross': 'Short MA crosses below Long MA (bearish signal)',
                'best_for': 'Trending markets, medium to long-term trading'
            },
            'rsi': {
                'title': 'Relative Strength Index (RSI)',
                'description': 'Momentum oscillator measuring speed of price changes',
                'oversold': 'RSI < 30 suggests potential buying opportunity',
                'overbought': 'RSI > 70 suggests potential selling opportunity',
                'best_for': 'Identifying potential reversal points'
            },
            'scalping': {
                'title': 'Scalping Strategy',
                'description': 'High-frequency trading for small, quick profits',
                'characteristics': 'Very short holding periods, tight risk management',
                'requirements': 'High liquidity, low transaction costs, constant monitoring',
                'best_for': 'Experienced traders with time for active monitoring'
            },
            'memecoin_trading': {
                'title': 'Memecoin Trading (EXTREME RISK)',
                'description': 'Trading meme-based cryptocurrencies',
                'extreme_risks': [
                    'Extreme volatility and unpredictable price swings',
                    'Lack of fundamental value or utility',
                    'Susceptible to pump-and-dump schemes',
                    'Regulatory uncertainty',
                    'High risk of total loss'
                ],
                'warning': 'Only trade with money you can afford to lose entirely'
            }
        },
        'market_types': {
            'trending': 'Moving averages work well in trending markets',
            'ranging': 'RSI and oscillators work better in sideways markets',
            'volatile': 'Increased risk but potentially higher rewards',
            'low_volume': 'Harder to execute trades, wider spreads'
        }
    }
    
    return jsonify({
        'educational_content': educational_content,
        'last_updated': datetime.now().isoformat()
    })

# Initialize strategies when module is imported
init_strategies()

# Function to register the blueprint with the main Flask app
def register_strategies_blueprint(app):
    """Register the strategies blueprint with the Flask app"""
    app.register_blueprint(strategies_bp)
    print("✅ Advanced Trading Strategies API endpoints registered")

if __name__ == "__main__":
    # Test the strategies endpoints
    from flask import Flask
    
    app = Flask(__name__)
    register_strategies_blueprint(app)
    
    print("🧪 Testing Advanced Strategies API")
    print("Available endpoints:")
    print("- GET  /api/strategies/health")
    print("- GET  /api/strategies/list")
    print("- POST /api/strategies/analyze")
    print("- POST /api/strategies/risk-assessment")
    print("- GET  /api/strategies/portfolio-summary")
    print("- GET/POST /api/strategies/strategy-config")
    print("- GET  /api/strategies/educational-info")
    
    # Run test server
    app.run(host='0.0.0.0', port=5002, debug=True) 