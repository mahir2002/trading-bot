#!/usr/bin/env python3
"""
📊 ADVANCED ANALYTICS & REPORTING SYSTEM
========================================
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import sqlite3
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AdvancedAnalytics')

class AnalyticsType(Enum):
    PERFORMANCE = "performance"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    MARKET = "market"

@dataclass
class PerformanceMetrics:
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profit_factor: float = 0.0

@dataclass
class RiskMetrics:
    var_95: float = 0.0
    var_99: float = 0.0
    beta: float = 0.0
    volatility: float = 0.0

class AdvancedAnalyticsReportingSystem:
    def __init__(self, database_path: str = "analytics.db"):
        self.database_path = database_path
        self.performance_cache = {}
        self.risk_cache = {}
        self._initialize_database()
        logger.info("📊 Advanced Analytics & Reporting System initialized")
    
    def _initialize_database(self):
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    portfolio_value REAL,
                    total_return REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Analytics database initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    async def update_performance_metrics(self, portfolio_data: Dict[str, Any]) -> PerformanceMetrics:
        try:
            logger.info("📈 Updating performance metrics...")
            
            portfolio_values = portfolio_data.get('portfolio_values', [])
            trades = portfolio_data.get('trades', [])
            
            if not portfolio_values:
                return PerformanceMetrics()
            
            # Calculate metrics
            portfolio_series = pd.Series(portfolio_values)
            returns = portfolio_series.pct_change().dropna()
            
            total_return = (portfolio_series.iloc[-1] - portfolio_series.iloc[0]) / portfolio_series.iloc[0]
            annual_return = (1 + total_return) ** (252 / len(portfolio_series)) - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
            
            # Trading statistics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Profit factor
            gross_profit = sum([t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0])
            gross_loss = abs(sum([t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            metrics = PerformanceMetrics(
                total_return=total_return,
                annual_return=annual_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=total_trades,
                profit_factor=profit_factor
            )
            
            self.performance_cache = {
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'profit_factor': profit_factor
            }
            
            logger.info("✅ Performance metrics updated")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Performance metrics update failed: {e}")
            return PerformanceMetrics()
    
    async def calculate_risk_metrics(self, returns_data: List[float]) -> RiskMetrics:
        try:
            logger.info("⚠️ Calculating risk metrics...")
            
            if not returns_data:
                return RiskMetrics()
            
            returns = pd.Series(returns_data)
            
            # Value at Risk
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # Volatility
            volatility = returns.std() * np.sqrt(252)
            
            # Beta (simplified)
            beta = 1.0
            
            metrics = RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                beta=beta,
                volatility=volatility
            )
            
            self.risk_cache = {
                'var_95': var_95,
                'var_99': var_99,
                'beta': beta,
                'volatility': volatility
            }
            
            logger.info("✅ Risk metrics calculated")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Risk metrics calculation failed: {e}")
            return RiskMetrics()
    
    async def generate_comprehensive_report(self, report_type: AnalyticsType = AnalyticsType.PERFORMANCE) -> str:
        try:
            logger.info(f"📋 Generating {report_type.value} report...")
            
            import os
            report_path = f"reports/{report_type.value}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            os.makedirs('reports', exist_ok=True)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Advanced Analytics Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; }}
                    .metric {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007acc; }}
                    .positive {{ color: green; }}
                    .negative {{ color: red; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📊 Advanced Analytics Report</h1>
                    <p>Generated: {datetime.now()}</p>
                </div>
                
                <h2>📈 Performance Metrics</h2>
                <div class="metric">
                    <strong>Total Return:</strong> {self.performance_cache.get('total_return', 0):.2%}
                </div>
                <div class="metric">
                    <strong>Sharpe Ratio:</strong> {self.performance_cache.get('sharpe_ratio', 0):.2f}
                </div>
                <div class="metric">
                    <strong>Max Drawdown:</strong> {self.performance_cache.get('max_drawdown', 0):.2%}
                </div>
                
                <h2>⚠️ Risk Metrics</h2>
                <div class="metric">
                    <strong>VaR (95%):</strong> {self.risk_cache.get('var_95', 0):.4f}
                </div>
                <div class="metric">
                    <strong>Volatility:</strong> {self.risk_cache.get('volatility', 0):.2%}
                </div>
            </body>
            </html>
            """
            
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            logger.info(f"✅ Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
            return ""

async def run_advanced_analytics_demo():
    try:
        logger.info("🚀 Starting Advanced Analytics Demo...")
        
        analytics = AdvancedAnalyticsReportingSystem()
        
        # Generate sample data
        np.random.seed(42)
        n_days = 100
        returns = np.random.normal(0.001, 0.02, n_days)
        portfolio_values = 100000 * np.cumprod(1 + returns)
        
        # Sample trades
        trades = []
        for i in range(50):
            trades.append({
                'timestamp': datetime.now() - timedelta(days=n_days-i),
                'symbol': np.random.choice(['BTC/USDT', 'ETH/USDT']),
                'pnl': np.random.normal(50, 200)
            })
        
        portfolio_data = {
            'portfolio_values': portfolio_values.tolist(),
            'trades': trades
        }
        
        # Update metrics
        perf_metrics = await analytics.update_performance_metrics(portfolio_data)
        risk_metrics = await analytics.calculate_risk_metrics(returns.tolist())
        
        # Generate report
        report_path = await analytics.generate_comprehensive_report(AnalyticsType.PERFORMANCE)
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("📊 ADVANCED ANALYTICS DEMO RESULTS")
        logger.info("="*60)
        
        logger.info(f"📈 Performance Metrics:")
        logger.info(f"   Total Return: {perf_metrics.total_return:.2%}")
        logger.info(f"   Annual Return: {perf_metrics.annual_return:.2%}")
        logger.info(f"   Sharpe Ratio: {perf_metrics.sharpe_ratio:.2f}")
        logger.info(f"   Max Drawdown: {perf_metrics.max_drawdown:.2%}")
        logger.info(f"   Win Rate: {perf_metrics.win_rate:.2%}")
        
        logger.info(f"\n⚠️ Risk Metrics:")
        logger.info(f"   VaR (95%): {risk_metrics.var_95:.4f}")
        logger.info(f"   VaR (99%): {risk_metrics.var_99:.4f}")
        logger.info(f"   Volatility: {risk_metrics.volatility:.2%}")
        
        logger.info(f"\n📋 Report Generated: {report_path}")
        logger.info("✅ Advanced Analytics Demo completed successfully!")
        
        return {
            'performance_metrics': perf_metrics,
            'risk_metrics': risk_metrics,
            'report_path': report_path
        }
        
    except Exception as e:
        logger.error(f"❌ Advanced Analytics Demo failed: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(run_advanced_analytics_demo())
