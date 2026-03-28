#!/usr/bin/env python3
"""
Comprehensive Bot Validation System
Systematic testing and validation before live trading
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

class BotValidationSystem:
    def __init__(self):
        self.logger = self._setup_logging()
        self.db_path = "crypto_trading_data.db"
        self.validation_results = {}
        
    def _setup_logging(self):
        """Setup logging for validation system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - BotValidator - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('validation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🧪 COMPREHENSIVE BOT VALIDATION")
        print("=" * 50)
        
        # Phase 1: Technical Validation
        tech_results = self.validate_technical_setup()
        
        # Phase 2: Performance Validation  
        perf_results = self.validate_performance_metrics()
        
        # Phase 3: Risk Management Validation
        risk_results = self.validate_risk_management()
        
        # Phase 4: Model Validation
        model_results = self.validate_model_performance()
        
        # Generate Final Report
        final_score = self.generate_validation_report(
            tech_results, perf_results, risk_results, model_results
        )
        
        return final_score
    
    def validate_technical_setup(self):
        """Validate technical configuration"""
        print("\n🔧 PHASE 1: Technical Setup Validation")
        print("-" * 30)
        
        results = {}
        
        # Check database connection
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions LIMIT 1")
            results['database_connection'] = True
            conn.close()
            print("✅ Database connection: PASS")
        except Exception as e:
            results['database_connection'] = False
            print(f"❌ Database connection: FAIL - {e}")
        
        # Check configuration files
        config_files = ['config.env', 'ai_trading_bot_simple.py']
        config_score = 0
        for file in config_files:
            if Path(file).exists():
                config_score += 1
                print(f"✅ {file}: EXISTS")
            else:
                print(f"❌ {file}: MISSING")
        
        results['config_completeness'] = config_score / len(config_files)
        
        # Check data availability
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT COUNT(*) as count, 
                       MIN(timestamp) as earliest,
                       MAX(timestamp) as latest
                FROM predictions
            """, conn)
            
            if df['count'].iloc[0] > 0:
                results['data_availability'] = True
                earliest = df['earliest'].iloc[0]
                latest = df['latest'].iloc[0]
                print(f"✅ Data available: {df['count'].iloc[0]} records")
                print(f"   Period: {earliest} to {latest}")
            else:
                results['data_availability'] = False
                print("❌ No prediction data found")
            
            conn.close()
        except Exception as e:
            results['data_availability'] = False
            print(f"❌ Data check failed: {e}")
        
        return results
    
    def validate_performance_metrics(self):
        """Validate bot performance metrics"""
        print("\n📊 PHASE 2: Performance Metrics Validation")
        print("-" * 30)
        
        results = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get recent predictions (last 7 days)
            df = pd.read_sql_query("""
                SELECT * FROM predictions 
                WHERE timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
            """, conn)
            
            if len(df) == 0:
                print("❌ No recent data for performance validation")
                return {'performance_score': 0}
            
            # Calculate key metrics
            total_predictions = len(df)
            
            # Signal distribution
            signal_dist = df['action'].value_counts()
            hold_percentage = (signal_dist.get('HOLD', 0) / total_predictions) * 100
            
            # Confidence analysis
            avg_confidence = df['confidence'].mean()
            high_conf_pct = (df['confidence'] > 70).sum() / total_predictions * 100
            
            # Model accuracy (if we have actual vs predicted)
            if 'actual_return' in df.columns:
                # Calculate directional accuracy
                df['predicted_direction'] = df['predicted_return'] > 0
                df['actual_direction'] = df['actual_return'] > 0
                accuracy = (df['predicted_direction'] == df['actual_direction']).mean()
                results['directional_accuracy'] = accuracy
            else:
                results['directional_accuracy'] = None
            
            # Performance scoring
            performance_score = 0
            
            # Conservative approach (high HOLD percentage is good)
            if hold_percentage > 60:
                performance_score += 25
                print(f"✅ Conservative approach: {hold_percentage:.1f}% HOLD signals")
            else:
                print(f"⚠️ Low HOLD percentage: {hold_percentage:.1f}%")
            
            # High confidence predictions
            if avg_confidence > 50:
                performance_score += 25
                print(f"✅ Good confidence: {avg_confidence:.1f}% average")
            else:
                print(f"❌ Low confidence: {avg_confidence:.1f}% average")
            
            # Consistent activity
            if total_predictions > 50:  # At least ~7 per day
                performance_score += 25
                print(f"✅ Active monitoring: {total_predictions} predictions in 7 days")
            else:
                print(f"⚠️ Low activity: {total_predictions} predictions in 7 days")
            
            # Model diversity (checking different symbols)
            unique_symbols = df['symbol'].nunique()
            if unique_symbols >= 2:
                performance_score += 25
                print(f"✅ Multi-asset coverage: {unique_symbols} symbols")
            else:
                print(f"⚠️ Limited coverage: {unique_symbols} symbols")
            
            results['performance_score'] = performance_score
            results['total_predictions'] = total_predictions
            results['hold_percentage'] = hold_percentage
            results['avg_confidence'] = avg_confidence
            results['high_confidence_pct'] = high_conf_pct
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Performance validation failed: {e}")
            results['performance_score'] = 0
        
        return results
    
    def validate_risk_management(self):
        """Validate risk management systems"""
        print("\n🛡️ PHASE 3: Risk Management Validation")
        print("-" * 30)
        
        results = {}
        risk_score = 0
        
        # Check for risk management components
        risk_files = [
            'comprehensive_portfolio_risk_system.py',
            'advanced_signal_generation_system.py',
            'dynamic_risk_manager.py'
        ]
        
        risk_components = 0
        for file in risk_files:
            if Path(file).exists():
                risk_components += 1
                print(f"✅ {file}: Available")
            else:
                print(f"⚠️ {file}: Not found")
        
        if risk_components >= 2:
            risk_score += 30
        
        # Check configuration for risk parameters
        try:
            with open('config.env', 'r') as f:
                config_content = f.read()
                
            risk_params = [
                'RISK_PERCENTAGE',
                'MAX_DRAWDOWN',
                'DEFAULT_TRADE_AMOUNT'
            ]
            
            configured_params = 0
            for param in risk_params:
                if param in config_content:
                    configured_params += 1
                    print(f"✅ {param}: Configured")
                else:
                    print(f"⚠️ {param}: Not configured")
            
            if configured_params >= 2:
                risk_score += 30
                
        except Exception as e:
            print(f"⚠️ Config check failed: {e}")
        
        # Check for conservative position sizing
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT action, confidence FROM predictions 
                WHERE timestamp >= datetime('now', '-7 days')
            """, conn)
            
            # Conservative signal generation (high HOLD percentage)
            hold_pct = (df['action'] == 'HOLD').mean() * 100
            if hold_pct > 70:
                risk_score += 40
                print(f"✅ Conservative signaling: {hold_pct:.1f}% HOLD")
            elif hold_pct > 50:
                risk_score += 20
                print(f"⚠️ Moderate signaling: {hold_pct:.1f}% HOLD")
            else:
                print(f"❌ Aggressive signaling: {hold_pct:.1f}% HOLD")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Signal analysis failed: {e}")
        
        results['risk_score'] = risk_score
        return results
    
    def validate_model_performance(self):
        """Validate AI model performance"""
        print("\n🤖 PHASE 4: Model Performance Validation")
        print("-" * 30)
        
        results = {}
        model_score = 0
        
        # Check for advanced AI components
        ai_files = [
            'advanced_ai_models_framework.py',
            'advanced_time_series_forecasting.py',
            'dynamic_model_retraining_demo.py'
        ]
        
        ai_components = 0
        for file in ai_files:
            if Path(file).exists():
                ai_components += 1
                print(f"✅ {file}: Available")
            else:
                print(f"⚠️ {file}: Not found")
        
        if ai_components >= 2:
            model_score += 40
        
        # Check model diversity and ensemble methods
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT confidence, action FROM predictions 
                WHERE timestamp >= datetime('now', '-7 days')
                AND confidence > 0
            """, conn)
            
            if len(df) > 0:
                # Confidence distribution analysis
                conf_std = df['confidence'].std()
                if conf_std > 20:  # Good variance in confidence
                    model_score += 30
                    print(f"✅ Confidence variance: {conf_std:.1f}")
                else:
                    print(f"⚠️ Low confidence variance: {conf_std:.1f}")
                
                # Signal quality
                high_conf_signals = df[df['confidence'] > 70]
                if len(high_conf_signals) > 0:
                    model_score += 30
                    print(f"✅ High confidence signals: {len(high_conf_signals)}")
                else:
                    print("⚠️ No high confidence signals")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Model analysis failed: {e}")
        
        results['model_score'] = model_score
        return results
    
    def generate_validation_report(self, tech_results, perf_results, risk_results, model_results):
        """Generate comprehensive validation report"""
        print("\n📋 FINAL VALIDATION REPORT")
        print("=" * 50)
        
        # Calculate overall scores
        tech_score = (
            (tech_results.get('database_connection', False) * 30) +
            (tech_results.get('config_completeness', 0) * 30) +
            (tech_results.get('data_availability', False) * 40)
        )
        
        perf_score = perf_results.get('performance_score', 0)
        risk_score = risk_results.get('risk_score', 0)
        model_score = model_results.get('model_score', 0)
        
        overall_score = (tech_score + perf_score + risk_score + model_score) / 4
        
        print(f"🔧 Technical Setup:     {tech_score:.1f}/100")
        print(f"📊 Performance:        {perf_score:.1f}/100")
        print(f"🛡️ Risk Management:    {risk_score:.1f}/100")
        print(f"🤖 Model Quality:      {model_score:.1f}/100")
        print("-" * 30)
        print(f"🎯 OVERALL SCORE:      {overall_score:.1f}/100")
        
        # Determine readiness level
        if overall_score >= 80:
            readiness = "🟢 READY FOR LIVE TRADING"
            recommendation = "Your system shows excellent validation scores. Consider starting with small position sizes."
        elif overall_score >= 60:
            readiness = "🟡 ALMOST READY"
            recommendation = "Continue paper trading for 2-4 more weeks. Address any identified issues."
        elif overall_score >= 40:
            readiness = "🟠 NEEDS IMPROVEMENT"
            recommendation = "Significant improvements needed. Focus on identified weak areas."
        else:
            readiness = "🔴 NOT READY"
            recommendation = "System requires major improvements before considering live trading."
        
        print(f"\n{readiness}")
        print(f"💡 Recommendation: {recommendation}")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'readiness': readiness,
            'recommendation': recommendation,
            'detailed_scores': {
                'technical': tech_score,
                'performance': perf_score,
                'risk': risk_score,
                'model': model_score
            },
            'detailed_results': {
                'technical': tech_results,
                'performance': perf_results,
                'risk': risk_results,
                'model': model_results
            }
        }
        
        with open(f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return overall_score

def main():
    """Run comprehensive bot validation"""
    validator = BotValidationSystem()
    score = validator.run_comprehensive_validation()
    
    print(f"\n🎯 Validation complete! Score: {score:.1f}/100")
    print("📄 Detailed report saved to validation_report_*.json")

if __name__ == "__main__":
    main() 