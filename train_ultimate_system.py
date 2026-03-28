#!/usr/bin/env python3
"""
🎓 Ultimate Trading System - AI/ML Model Training
==============================================

Comprehensive training script for the Ultimate All-in-One Trading System.
Trains all AI/ML models with real market data and saves them for production use.

Usage:
    python train_ultimate_system.py                    # Quick training (10 pairs, 7 days)
    python train_ultimate_system.py --extensive        # Extensive training (20 pairs, 30 days)
    python train_ultimate_system.py --full             # Full training (all pairs, 60 days)
    python train_ultimate_system.py --custom           # Custom configuration
"""

import asyncio
import argparse
import sys
from datetime import datetime
import logging

# Import the ultimate system
from ultimate_all_in_one_trading_system import UltimateAllInOneTradingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print training banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║            🎓 ULTIMATE TRADING SYSTEM - AI/ML TRAINING 🎓                    ║
║                                                                              ║
║                    Train All Models with Real Market Data                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🧠 Machine Learning Models: Random Forest, Gradient Boosting               ║
║  🤖 Deep Learning Models: LSTM, GRU, Transformer                           ║
║  📊 Feature Engineering: 50+ Technical Indicators                          ║
║  ⚡ Real-time Training: Live Market Data Collection                         ║
║  💾 Model Persistence: Automatic Saving & Loading                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

def get_training_configs():
    """Get predefined training configurations"""
    return {
        'quick': {
            'name': 'Quick Training',
            'description': 'Fast training for testing (10 pairs, 7 days)',
            'pairs': 10,
            'days': 7,
            'duration': '~5 minutes'
        },
        'extensive': {
            'name': 'Extensive Training',
            'description': 'Balanced training for development (20 pairs, 30 days)',
            'pairs': 20,
            'days': 30,
            'duration': '~15 minutes'
        },
        'full': {
            'name': 'Full Training',
            'description': 'Complete training for production (all pairs, 60 days)',
            'pairs': 45,
            'days': 60,
            'duration': '~30 minutes'
        }
    }

def display_training_options():
    """Display available training options"""
    configs = get_training_configs()
    
    print("\n🎯 Available Training Configurations:\n")
    
    for i, (key, config) in enumerate(configs.items(), 1):
        print(f"  {i}. {config['name']}")
        print(f"     {config['description']}")
        print(f"     📊 Trading Pairs: {config['pairs']}")
        print(f"     📅 Historical Data: {config['days']} days")
        print(f"     ⏱️ Estimated Duration: {config['duration']}")
        print()

def get_user_choice():
    """Get user choice for training configuration"""
    while True:
        try:
            choice = input("Enter your choice (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n🛑 Training cancelled by user")
            sys.exit(0)

def get_custom_config():
    """Get custom training configuration from user"""
    print("\n🔧 Custom Training Configuration:")
    
    try:
        pairs = int(input("Number of trading pairs (1-45): "))
        if not 1 <= pairs <= 45:
            pairs = 10
            print(f"⚠️ Invalid range. Using default: {pairs}")
        
        days = int(input("Historical data days (1-90): "))
        if not 1 <= days <= 90:
            days = 30
            print(f"⚠️ Invalid range. Using default: {days}")
        
        return pairs, days
        
    except ValueError:
        print("⚠️ Invalid input. Using defaults: 10 pairs, 30 days")
        return 10, 30
    except KeyboardInterrupt:
        print("\n🛑 Training cancelled by user")
        sys.exit(0)

async def run_training(pairs_count: int, training_days: int):
    """Run the training process"""
    print(f"\n🚀 Starting training with {pairs_count} pairs and {training_days} days of data...")
    
    # Initialize the ultimate system
    system = UltimateAllInOneTradingSystem()
    
    try:
        # Select trading pairs for training
        training_pairs = system.trading_pairs[:pairs_count]
        
        print(f"📊 Training pairs: {', '.join(training_pairs)}")
        print(f"📅 Historical data: {training_days} days")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n⏳ Training in progress...")
        
        # Run training
        results = await system.train_system(
            training_pairs=training_pairs,
            training_days=training_days
        )
        
        # Display results
        print("\n" + "="*80)
        print("🎓 TRAINING COMPLETED!")
        print("="*80)
        
        if 'error' in results:
            print(f"❌ Training failed: {results['error']}")
            return False
        
        print(f"✅ Models trained: {results['models_trained']}")
        print(f"📊 Data points used: {results['data_points']:,}")
        print(f"⏱️ Training time: {results['training_time']:.1f} seconds")
        
        if results['validation_accuracy']:
            print("\n📈 Model Performance:")
            for model, accuracy in results['validation_accuracy'].items():
                print(f"   • {model.title()}: {accuracy:.1%}")
            
            best_model = max(results['validation_accuracy'], key=results['validation_accuracy'].get)
            print(f"\n🏆 Best performing model: {best_model.title()} ({results['validation_accuracy'][best_model]:.1%})")
        
        print("\n💾 Models saved to: trained_models/")
        print("🚀 Ready for enhanced trading performance!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        logger.error(f"Training failed: {e}")
        return False

def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train Ultimate Trading System AI/ML Models')
    parser.add_argument('--quick', action='store_true', help='Quick training (10 pairs, 7 days)')
    parser.add_argument('--extensive', action='store_true', help='Extensive training (20 pairs, 30 days)')
    parser.add_argument('--full', action='store_true', help='Full training (all pairs, 60 days)')
    parser.add_argument('--custom', action='store_true', help='Custom training configuration')
    parser.add_argument('--pairs', type=int, help='Number of trading pairs')
    parser.add_argument('--days', type=int, help='Days of historical data')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Determine training configuration
    if args.quick:
        pairs_count, training_days = 10, 7
        print("🏃 Quick Training Selected")
    elif args.extensive:
        pairs_count, training_days = 20, 30
        print("📊 Extensive Training Selected")
    elif args.full:
        pairs_count, training_days = 45, 60
        print("🎯 Full Training Selected")
    elif args.custom:
        pairs_count, training_days = get_custom_config()
        print("🔧 Custom Training Configuration")
    elif args.pairs and args.days:
        pairs_count, training_days = args.pairs, args.days
        print("⚙️ Manual Configuration")
    else:
        # Interactive mode
        display_training_options()
        choice = get_user_choice()
        
        configs = list(get_training_configs().values())
        config = configs[choice - 1]
        pairs_count, training_days = config['pairs'], config['days']
        print(f"✅ {config['name']} Selected")
    
    # Validate configuration
    pairs_count = max(1, min(45, pairs_count))
    training_days = max(1, min(90, training_days))
    
    print(f"\n📋 Final Configuration:")
    print(f"   • Trading Pairs: {pairs_count}")
    print(f"   • Historical Data: {training_days} days")
    print(f"   • Estimated Time: {training_days * pairs_count // 10} minutes")
    
    # Confirm before starting
    try:
        confirm = input("\n▶️ Start training? [Y/n]: ").strip().lower()
        if confirm in ['n', 'no']:
            print("🛑 Training cancelled")
            return
    except KeyboardInterrupt:
        print("\n🛑 Training cancelled by user")
        return
    
    # Run training
    success = asyncio.run(run_training(pairs_count, training_days))
    
    if success:
        print("\n🎉 Training completed successfully!")
        print("💡 You can now run the trading system with trained models:")
        print("   python ultimate_all_in_one_trading_system.py web")
    else:
        print("\n❌ Training failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Training interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1) 