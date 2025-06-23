#!/usr/bin/env python3
"""
🎯 DEX Screener + Advanced Position Sizing Integration
Combines DEX token discovery with sophisticated position sizing strategies
for optimal DEX trading with intelligent risk management.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

# Import existing systems
from dexscreener_fetcher import DEXScreenerFetcher
from advanced_position_sizing_manager import (
    AdvancedPositionSizingManager, PositionSizingMethod, PositionSizingParameters,
    TradingSignal, RiskLevel, MarketRegime, create_trading_signal
)

@dataclass
class DEXTradingOpportunity:
    """Enhanced DEX trading opportunity with position sizing"""
    # DEX token data
    symbol: str
    name: str
    chain_id: str
    dex_id: str
    
    # Market data
    price_usd: float
    volume_24h: float
    liquidity_usd: float
    price_change_24h: float
    
    # Risk assessment
    risk_score: str
    risk_level: RiskLevel
    category: str
    
    # Position sizing
    recommended_position_size: float
    position_sizing_method: str
    confidence_score: float
    expected_return: float
    
    # Additional metrics
    emoji: str
    timestamp: datetime

class DEXPositionSizingIntegration:
    """Integration system for DEX screening and position sizing"""
    
    def __init__(self, position_sizing_params: Optional[PositionSizingParameters] = None):
        self.logger = self._setup_logger()
        
        # Initialize components
        self.dex_fetcher = DEXScreenerFetcher()
        
        # Configure position sizing for DEX trading (more conservative)
        if position_sizing_params is None:
            position_sizing_params = PositionSizingParameters(
                max_position_size=0.08,      # 8% max for DEX (more risky)
                max_total_exposure=0.50,     # 50% max total DEX exposure
                min_position_size=0.005,     # 0.5% minimum
                kelly_safety_factor=0.15,    # More conservative Kelly (15%)
                confidence_threshold=0.70    # Higher confidence threshold (70%)
            )
        
        self.position_manager = AdvancedPositionSizingManager(position_sizing_params, self.logger)
        
        # DEX-specific risk adjustments
        self.dex_risk_multipliers = {
            'Very High': 0.3,  # 30% of normal size for very high risk
            'High': 0.5,       # 50% of normal size for high risk
            'Medium': 0.7,     # 70% of normal size for medium risk
            'Low': 1.0,        # Normal size for low risk
            'Unknown': 0.4     # 40% of normal size for unknown risk
        }
        
        # Chain risk factors
        self.chain_risk_factors = {
            'ethereum': 1.0,     # Most established
            'bsc': 0.9,          # Well established
            'solana': 0.8,       # Good but more volatile
            'polygon': 0.9,      # Stable L2
            'arbitrum': 0.9,     # Stable L2
            'base': 0.8,         # Newer but backed by Coinbase
            'unknown': 0.5       # Unknown chains
        }
        
        self.logger.info("🎯 DEX Position Sizing Integration initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for integration system"""
        logger = logging.getLogger('DEXPositionSizing')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _convert_dex_risk_to_risk_level(self, dex_risk_score: str) -> RiskLevel:
        """Convert DEX risk score to position sizing risk level"""
        risk_mapping = {
            'Low': RiskLevel.LOW,
            'Medium': RiskLevel.MODERATE,
            'High': RiskLevel.HIGH,
            'Very High': RiskLevel.AGGRESSIVE,
            'Unknown': RiskLevel.HIGH
        }
        return risk_mapping.get(dex_risk_score, RiskLevel.HIGH)
    
    def _calculate_dex_confidence(self, token_data: Dict) -> float:
        """Calculate confidence score for DEX token"""
        try:
            confidence = 50.0  # Base confidence
            
            # Liquidity factor (higher liquidity = higher confidence)
            liquidity = float(token_data.get('liquidity', {}).get('usd', 0))
            if liquidity > 1000000:  # > $1M
                confidence += 20
            elif liquidity > 500000:  # > $500K
                confidence += 15
            elif liquidity > 100000:  # > $100K
                confidence += 10
            elif liquidity > 50000:   # > $50K
                confidence += 5
            else:
                confidence -= 10  # Low liquidity penalty
            
            # Volume factor
            volume_24h = float(token_data.get('volume', {}).get('h24', 0))
            if volume_24h > 1000000:  # > $1M volume
                confidence += 15
            elif volume_24h > 500000:  # > $500K volume
                confidence += 10
            elif volume_24h > 100000:  # > $100K volume
                confidence += 5
            else:
                confidence -= 5  # Low volume penalty
            
            # Chain factor
            chain_id = token_data.get('chainId', 'unknown').lower()
            chain_factor = self.chain_risk_factors.get(chain_id, 0.5)
            confidence *= chain_factor
            
            # Risk score penalty
            risk_score = token_data.get('risk_score', 'Unknown')
            risk_multiplier = self.dex_risk_multipliers.get(risk_score, 0.4)
            confidence *= risk_multiplier
            
            # Ensure confidence is within bounds
            confidence = max(10.0, min(confidence, 95.0))
            
            return confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating DEX confidence: {e}")
            return 30.0  # Low default confidence
    
    def _estimate_expected_return(self, token_data: Dict, confidence: float) -> float:
        """Estimate expected return for DEX token"""
        try:
            # Base expected return based on category
            category = token_data.get('category', 'Other')
            base_returns = {
                'Meme': 0.15,      # High volatility meme tokens
                'DeFi': 0.08,      # Moderate DeFi returns
                'Gaming': 0.10,    # Gaming token potential
                'AI': 0.12,        # AI token trend
                'Trending': 0.10,  # Trending tokens
                'Other': 0.06      # Conservative estimate
            }
            
            base_return = base_returns.get(category, 0.06)
            
            # Adjust based on recent price change
            price_change_24h = float(token_data.get('priceChange', {}).get('h24', 0))
            momentum_factor = 1.0
            
            if price_change_24h > 20:  # Strong positive momentum
                momentum_factor = 1.3
            elif price_change_24h > 10:  # Moderate positive momentum
                momentum_factor = 1.2
            elif price_change_24h > 0:  # Slight positive momentum
                momentum_factor = 1.1
            else:  # Negative or no momentum
                momentum_factor = 0.9
            
            # Adjust based on confidence
            confidence_factor = confidence / 100
            
            # Calculate expected return
            expected_return = base_return * momentum_factor * confidence_factor
            
            # Cap expected returns for risk management
            expected_return = max(-0.20, min(expected_return, 0.30))  # -20% to +30%
            
            return expected_return
            
        except Exception as e:
            self.logger.error(f"Error estimating expected return: {e}")
            return 0.05  # Conservative default
    
    def _create_dex_trading_signal(self, token_data: Dict) -> TradingSignal:
        """Create trading signal from DEX token data"""
        
        # Calculate confidence and expected return
        confidence = self._calculate_dex_confidence(token_data)
        expected_return = self._estimate_expected_return(token_data, confidence)
        
        # Determine action based on expected return and confidence
        if expected_return > 0.05 and confidence > 70:
            action = "BUY"
        elif expected_return < -0.05:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Estimate win rate based on confidence
        base_win_rate = 0.55  # Base 55% win rate
        confidence_boost = (confidence - 50) / 100 * 0.2  # Up to 20% boost
        win_rate = max(0.3, min(0.8, base_win_rate + confidence_boost))
        
        # Estimate average win/loss based on category volatility
        category = token_data.get('category', 'Other')
        volatility_map = {
            'Meme': (0.25, 0.15),      # High volatility
            'DeFi': (0.12, 0.08),      # Moderate volatility
            'Gaming': (0.15, 0.10),    # Moderate-high volatility
            'AI': (0.18, 0.12),        # High volatility (trending)
            'Trending': (0.20, 0.12),  # High volatility
            'Other': (0.10, 0.07)      # Conservative estimate
        }
        
        avg_win, avg_loss = volatility_map.get(category, (0.10, 0.07))
        
        # Determine market regime
        if expected_return > 0.10:
            regime = MarketRegime.BULL
        elif expected_return < -0.05:
            regime = MarketRegime.BEAR
        else:
            regime = MarketRegime.SIDEWAYS
        
        # Get risk level
        risk_level = self._convert_dex_risk_to_risk_level(token_data.get('risk_score', 'Unknown'))
        
        # Create symbol
        base_token = token_data.get('baseToken', {})
        quote_token = token_data.get('quoteToken', {})
        symbol = f"{base_token.get('symbol', 'UNKNOWN')}/{quote_token.get('symbol', 'USD')}"
        
        return TradingSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            expected_return=expected_return,
            expected_volatility=avg_win,  # Use avg_win as volatility estimate
            win_probability=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            holding_period=3,  # Shorter holding for DEX tokens
            market_regime=regime,
            risk_level=risk_level
        )
    
    async def analyze_dex_opportunities(self, limit: int = 30) -> List[DEXTradingOpportunity]:
        """Analyze DEX opportunities with position sizing"""
        
        self.logger.info(f"🔍 Analyzing {limit} DEX opportunities...")
        
        opportunities = []
        
        try:
            # Get comprehensive DEX data
            dex_data = self.dex_fetcher.get_comprehensive_dex_data(limit)
            
            if not dex_data or 'tokens' not in dex_data:
                self.logger.warning("No DEX data available")
                return opportunities
            
            tokens = dex_data['tokens']
            self.logger.info(f"📊 Processing {len(tokens)} DEX tokens...")
            
            for symbol, token_data in tokens.items():
                try:
                    # Create trading signal
                    signal = self._create_dex_trading_signal(token_data)
                    
                    # Skip if confidence too low
                    if signal.confidence < 40:  # Lower threshold for DEX
                        continue
                    
                    # Get position sizing recommendation
                    position_result = self.position_manager.get_ensemble_recommendation(signal)
                    
                    # Create opportunity
                    opportunity = DEXTradingOpportunity(
                        symbol=signal.symbol,
                        name=token_data.get('baseToken', {}).get('name', 'Unknown'),
                        chain_id=token_data.get('chainId', 'unknown'),
                        dex_id=token_data.get('dexId', 'unknown'),
                        
                        price_usd=float(token_data.get('priceUsd', 0)),
                        volume_24h=float(token_data.get('volume', {}).get('h24', 0)),
                        liquidity_usd=float(token_data.get('liquidity', {}).get('usd', 0)),
                        price_change_24h=float(token_data.get('priceChange', {}).get('h24', 0)),
                        
                        risk_score=token_data.get('risk_score', 'Unknown'),
                        risk_level=signal.risk_level,
                        category=token_data.get('category', 'Other'),
                        
                        recommended_position_size=position_result.recommended_size,
                        position_sizing_method=position_result.method.value,
                        confidence_score=signal.confidence,
                        expected_return=signal.expected_return,
                        
                        emoji=token_data.get('emoji', '💎'),
                        timestamp=datetime.now()
                    )
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    self.logger.error(f"Error processing token {symbol}: {e}")
                    continue
            
            # Sort by opportunity score (expected return * position size * confidence)
            opportunities.sort(
                key=lambda x: x.expected_return * x.recommended_position_size * (x.confidence_score/100),
                reverse=True
            )
            
            self.logger.info(f"✅ Found {len(opportunities)} viable DEX opportunities")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error analyzing DEX opportunities: {e}")
            return opportunities
    
    def generate_dex_opportunity_report(self, opportunities: List[DEXTradingOpportunity]) -> Dict[str, Any]:
        """Generate comprehensive DEX opportunity report"""
        
        if not opportunities:
            return {'error': 'No opportunities available'}
        
        # Calculate statistics
        total_opportunities = len(opportunities)
        avg_confidence = np.mean([op.confidence_score for op in opportunities])
        avg_expected_return = np.mean([op.expected_return for op in opportunities])
        avg_position_size = np.mean([op.recommended_position_size for op in opportunities])
        
        # Category breakdown
        categories = {}
        for op in opportunities:
            categories[op.category] = categories.get(op.category, 0) + 1
        
        # Risk level breakdown
        risk_levels = {}
        for op in opportunities:
            risk_levels[op.risk_level.value[0]] = risk_levels.get(op.risk_level.value[0], 0) + 1
        
        # Chain breakdown
        chains = {}
        for op in opportunities:
            chains[op.chain_id] = chains.get(op.chain_id, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_opportunities': total_opportunities,
                'avg_confidence': f"{avg_confidence:.1f}%",
                'avg_expected_return': f"{avg_expected_return:+.2%}",
                'avg_position_size': f"{avg_position_size:.2%}",
                'total_recommended_exposure': f"{sum(op.recommended_position_size for op in opportunities):.2%}"
            },
            'breakdowns': {
                'categories': categories,
                'risk_levels': risk_levels,
                'chains': chains
            },
            'top_opportunities': opportunities[:10]
        }

async def main():
    """Demonstration of DEX Position Sizing Integration"""
    
    print("🚀 DEX SCREENER + POSITION SIZING INTEGRATION")
    print("=" * 60)
    
    # Initialize integration system
    integration = DEXPositionSizingIntegration()
    
    try:
        # Analyze DEX opportunities
        print("\n📊 ANALYZING DEX OPPORTUNITIES")
        print("-" * 40)
        
        opportunities = await integration.analyze_dex_opportunities(20)
        
        if opportunities:
            print(f"✅ Found {len(opportunities)} viable opportunities")
            
            print(f"\n🏆 TOP 5 DEX OPPORTUNITIES:")
            print(f"{'Symbol':<15} {'Confidence':<12} {'Return':<10} {'Size':<8} {'Risk':<10} {'Chain'}")
            print("-" * 75)
            
            for i, op in enumerate(opportunities[:5]):
                print(f"{op.emoji} {op.symbol:<13} {op.confidence_score:>8.1f}% "
                      f"{op.expected_return:>+8.2%} {op.recommended_position_size:>6.2%} "
                      f"{op.risk_level.value[0]:<10} {op.chain_id}")
        
        # Generate comprehensive report
        print(f"\n📋 COMPREHENSIVE DEX OPPORTUNITY REPORT")
        print("-" * 40)
        
        report = integration.generate_dex_opportunity_report(opportunities)
        
        if 'summary' in report:
            summary = report['summary']
            print(f"Total Opportunities: {summary['total_opportunities']}")
            print(f"Average Confidence: {summary['avg_confidence']}")
            print(f"Average Expected Return: {summary['avg_expected_return']}")
            print(f"Average Position Size: {summary['avg_position_size']}")
            print(f"Total Recommended Exposure: {summary['total_recommended_exposure']}")
            
            print(f"\n📊 Category Breakdown:")
            for category, count in sorted(report['breakdowns']['categories'].items(), 
                                        key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count} opportunities")
            
            print(f"\n⚠️ Risk Level Distribution:")
            for risk, count in sorted(report['breakdowns']['risk_levels'].items(), 
                                    key=lambda x: x[1], reverse=True):
                print(f"   {risk}: {count} opportunities")
        
        print(f"\n✅ DEX POSITION SIZING INTEGRATION COMPLETE!")
        print(f"🎯 Intelligent position sizing for DEX tokens")
        print(f"🛡️ Risk-adjusted recommendations")
        print(f"📈 Optimized for DEX market characteristics")
        
    except Exception as e:
        print(f"❌ Integration error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 