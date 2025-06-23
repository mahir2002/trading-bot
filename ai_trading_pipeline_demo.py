#!/usr/bin/env python3
"""
Complete AI Trading Pipeline Demo
Demonstrates the full pipeline: Feature Engineering → AI Models → Paper Trading

Author: Trading Bot System
Date: 2025-01-22
"""

import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add unified trading platform to path
sys.path.append('unified_trading_platform')

async def main():
    """Run complete AI trading pipeline demo"""
    print("🤖 AI CRYPTO TRADING PIPELINE DEMO")
    print("=" * 80)
    print("   Complete automated pipeline demonstration")
    print("   Features → AI Models → Paper Trading → Performance Tracking")
    print("=" * 80)
    
    logging.basicConfig(level=logging.INFO)
    
    # Step 1: Feature Engineering Demo
    print("\n🔧 STEP 1: FEATURE ENGINEERING")
    print("-" * 50)
    
    try:
        from modules.feature_engineer import FeatureEngineer
        
        engineer = FeatureEngineer()
        
        # Test coins (mix of new and popular)
        test_coins = ['DEMO1', 'DEMO2', 'DEMO3', 'BTC', 'ETH', 'ADA']
        
        print(f"🔄 Generating features for {len(test_coins)} coins...")
        feature_results = await engineer.generate_features_batch(test_coins, days=30)
        
        print(f"✅ Feature Engineering Results:")
        print(f"   Success Rate: {feature_results['success_rate']:.1%}")
        print(f"   Successful: {feature_results['successful']}/{feature_results['total_coins']}")
        
        # Show individual results
        for symbol, result in feature_results['results'].items():
            if 'error' not in result:
                signal = result.get('signals', {})
                print(f"   📊 {symbol}: {result['features_generated']} features, "
                      f"Signal: {signal.get('signal', 'N/A')} "
                      f"(conf: {signal.get('confidence', 0):.2f})")
        
    except Exception as e:
        print(f"❌ Feature Engineering Demo Failed: {e}")
        return
    
    # Step 2: AI Model Training Demo
    print("\n🤖 STEP 2: AI MODEL TRAINING")
    print("-" * 50)
    
    try:
        from modules.ai_trading_model import AITradingModel
        
        model = AITradingModel()
        
        print("🔄 Training AI models...")
        training_results = await model.train_models()
        
        if 'error' not in training_results:
            print(f"✅ AI Model Training Results:")
            print(f"   Models Trained: 2 (Random Forest + Gradient Boosting)")
            print(f"   Training Samples: {training_results['training_samples']}")
            print(f"   Test Samples: {training_results['test_samples']}")
            print(f"   RF Accuracy: {training_results['random_forest']['accuracy']:.3f}")
            print(f"   GB Accuracy: {training_results['gradient_boosting']['accuracy']:.3f}")
            print(f"   Features Used: {training_results['features_used']}")
        else:
            print(f"❌ Training failed: {training_results['error']}")
            return
        
    except Exception as e:
        print(f"❌ AI Model Training Demo Failed: {e}")
        return
    
    # Step 3: AI Predictions Demo
    print("\n🎯 STEP 3: AI PREDICTIONS")
    print("-" * 50)
    
    try:
        print("🔄 Generating AI predictions...")
        predictions = await model.batch_predict(test_coins)
        
        print(f"✅ AI Prediction Results:")
        print(f"   Successful: {predictions['successful']}/{predictions['total_predictions']}")
        print(f"   BUY signals: {predictions['signals']['BUY']}")
        print(f"   SELL signals: {predictions['signals']['SELL']}")
        print(f"   HOLD signals: {predictions['signals']['HOLD']}")
        
        # Show individual predictions
        print(f"\n📊 Individual Predictions:")
        for symbol, result in predictions['results'].items():
            if 'error' not in result:
                signal = result['ensemble_signal']
                confidence = result['ensemble_confidence']
                price = result.get('current_price', 0)
                print(f"   {symbol}: {signal} (conf: {confidence:.2f}, price: ${price:.2f})")
        
    except Exception as e:
        print(f"❌ AI Predictions Demo Failed: {e}")
        return
    
    # Step 4: Paper Trading Demo
    print("\n💼 STEP 4: PAPER TRADING SIMULATION")
    print("-" * 50)
    
    try:
        from modules.paper_trading_simulator import PaperTradingSimulator
        
        # Initialize with $10,000 demo balance
        simulator = PaperTradingSimulator(initial_balance=10000.0)
        
        print("🔄 Processing trading signals...")
        
        # Use predictions from AI model
        trading_results = await simulator.process_multiple_signals(predictions['results'])
        
        print(f"✅ Paper Trading Results:")
        print(f"   Signals Processed: {trading_results['total_signals']}")
        print(f"   Actions: {trading_results['actions']}")
        print(f"   Current Balance: ${trading_results['current_balance']:.2f}")
        print(f"   Open Positions: {trading_results['open_positions']}")
        
        # Show individual trade results
        print(f"\n📋 Trade Results:")
        for symbol, result in trading_results['results'].items():
            action = result['action']
            reason = result.get('reason', 'No reason')
            
            if action in ['BUY', 'SELL']:
                price = result.get('price', 0)
                pnl = result.get('pnl', 0)
                print(f"   {symbol}: {action} at ${price:.4f} "
                      f"{'(P&L: $' + str(pnl) + ')' if action == 'SELL' else ''}")
            else:
                print(f"   {symbol}: {action} - {reason}")
        
    except Exception as e:
        print(f"❌ Paper Trading Demo Failed: {e}")
        return
    
    # Step 5: Performance Summary
    print("\n📈 STEP 5: PERFORMANCE SUMMARY")
    print("-" * 50)
    
    try:
        performance = simulator.get_performance_summary()
        
        print(f"✅ Portfolio Performance:")
        print(f"   Initial Balance: ${performance['initial_balance']:.2f}")
        print(f"   Current Balance: ${performance['current_balance']:.2f}")
        print(f"   Current Equity: ${performance['current_equity']:.2f}")
        print(f"   Total P&L: ${performance['total_pnl']:.2f} ({performance['total_pnl_percent']:.2f}%)")
        print(f"   Total Trades: {performance['total_trades']}")
        print(f"   Win Rate: {performance['win_rate']:.1f}%")
        print(f"   Open Positions: {performance['open_positions']}")
        
        if performance['positions']:
            print(f"\n💰 Current Positions:")
            for pos in performance['positions']:
                unrealized_pnl = pos['unrealized_pnl']
                pnl_percent = pos['unrealized_pnl_percent']
                print(f"   {pos['symbol']}: {pos['side']} {pos['quantity']:.6f} @ ${pos['entry_price']:.4f} "
                      f"(current: ${pos['current_price']:.4f}, "
                      f"P&L: ${unrealized_pnl:.2f}, {pnl_percent:.1f}%)")
        
    except Exception as e:
        print(f"❌ Performance Summary Failed: {e}")
    
    # Step 6: Data Files Summary
    print("\n📁 STEP 6: GENERATED DATA FILES")
    print("-" * 50)
    
    data_files = [
        ("Features", "data/features/", "*.csv"),
        ("AI Models", "trained_models/", "*.joblib"),
        ("Trading Database", "data/", "paper_trading.db"),
        ("Pipeline Results", "data/pipeline_results/", "*.json")
    ]
    
    for desc, path, pattern in data_files:
        if Path(path).exists():
            if pattern == "*.csv":
                files = list(Path(path).glob(pattern))
                print(f"   📊 {desc}: {len(files)} feature files in {path}")
            elif pattern == "*.joblib":
                files = list(Path(path).glob(pattern))
                print(f"   🤖 {desc}: {len(files)} model files in {path}")
            elif pattern.endswith(".db"):
                db_path = Path(path) / pattern.split("/")[-1]
                if db_path.exists():
                    print(f"   💾 {desc}: {db_path}")
            else:
                files = list(Path(path).glob(pattern))
                print(f"   📁 {desc}: {len(files)} files in {path}")
        else:
            print(f"   📁 {desc}: Directory not found ({path})")
    
    # Final Summary
    print("\n🎉 DEMO COMPLETE!")
    print("=" * 80)
    print("   The complete AI trading pipeline has been demonstrated:")
    print("   ✅ Feature Engineering: Generate 40+ trading features")
    print("   ✅ AI Model Training: Random Forest + Gradient Boosting")
    print("   ✅ AI Predictions: BUY/SELL/HOLD signals with confidence")
    print("   ✅ Paper Trading: Realistic trade simulation")
    print("   ✅ Performance Tracking: P&L, win rate, positions")
    print("=" * 80)
    print(f"   🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Future Enhancement Info
    print("\n🚀 NEXT STEPS:")
    print("   1. Add live trading via CCXT (replace paper trading)")
    print("   2. Implement real-time data feeds")
    print("   3. Add advanced risk management")
    print("   4. Deploy with automated scheduling")
    print("   5. Add web dashboard for monitoring")

if __name__ == "__main__":
    asyncio.run(main())
