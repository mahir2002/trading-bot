#!/usr/bin/env python3
"""
📱 SOCIAL SENTIMENT ANALYZER 📱
Advanced social media monitoring for meme coin trends and sentiment analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import re
import requests
import time
from datetime import datetime, timedelta
import numpy as np
from textblob import TextBlob
import tweepy
import praw
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class SentimentLevel(Enum):
    EXTREMELY_BEARISH = ("📉 Extremely Bearish", -1.0)
    BEARISH = ("🔴 Bearish", -0.5)
    NEUTRAL = ("⚪ Neutral", 0.0)
    BULLISH = ("🟢 Bullish", 0.5)
    EXTREMELY_BULLISH = ("🚀 Extremely Bullish", 1.0)

class TrendStrength(Enum):
    WEAK = ("🔸 Weak", 1)
    MODERATE = ("🔶 Moderate", 2)
    STRONG = ("🔥 Strong", 3)
    VIRAL = ("💥 Viral", 4)

@dataclass
class SocialMetrics:
    """Social media metrics for a token"""
    mentions_count: int
    sentiment_score: float
    sentiment_level: SentimentLevel
    trend_strength: TrendStrength
    engagement_rate: float
    influencer_mentions: int
    hashtag_volume: int
    reddit_posts: int
    reddit_upvotes: int
    telegram_messages: int
    twitter_followers_reached: int
    last_updated: datetime

@dataclass
class SocialSignal:
    """Individual social media signal"""
    platform: str
    content: str
    author: str
    followers_count: int
    engagement: int
    sentiment: float
    timestamp: datetime
    token_mentioned: str
    influence_score: float

@dataclass
class TrendingToken:
    """Trending token information"""
    symbol: str
    contract_address: str
    mentions_24h: int
    sentiment_change: float
    trend_score: float
    viral_potential: float
    risk_signals: List[str]
    opportunity_signals: List[str]

class SocialSentimentAnalyzer:
    """Advanced social sentiment analyzer for meme coins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Social media APIs
        self.twitter_api = None
        self.reddit_api = None
        
        # Sentiment tracking
        self.sentiment_history = defaultdict(lambda: deque(maxlen=1000))
        self.mention_tracker = defaultdict(int)
        self.influencer_tracker = {}
        
        # Meme coin keywords and patterns
        self.meme_keywords = self._load_meme_keywords()
        self.scam_patterns = self._load_scam_patterns()
        
        # Initialize APIs
        self._initialize_apis()
        
        logger.info("📱 Social Sentiment Analyzer initialized")
    
    def _load_meme_keywords(self) -> List[str]:
        """Load meme coin related keywords"""
        return [
            # General crypto terms
            'memecoin', 'meme coin', 'altcoin', 'shitcoin', 'moonshot',
            'gem', 'diamond hands', 'paper hands', 'hodl', 'ape in',
            'to the moon', 'lambo', 'when moon', 'pump', 'dump',
            
            # Popular meme coins
            'doge', 'dogecoin', 'shib', 'shiba', 'pepe', 'floki',
            'safemoon', 'babydoge', 'dogelon', 'kishu', 'akita',
            
            # Trading terms
            'buy the dip', 'btd', 'diamond hands', 'paper hands',
            'fomo', 'fud', 'rekt', 'moon', 'mars', 'jupiter',
            
            # Hashtags
            '#memecoin', '#altcoin', '#crypto', '#defi', '#nft',
            '#dogecoin', '#shibainu', '#pepe', '#moonshot'
        ]
    
    def _load_scam_patterns(self) -> List[str]:
        """Load patterns that indicate potential scams"""
        return [
            'guaranteed profit', 'risk free', 'get rich quick',
            'double your money', 'insider information', 'pump group',
            'coordinated buy', 'rug pull', 'exit scam', 'honeypot',
            'send me crypto', 'giveaway scam', 'fake elon',
            'impersonation', 'phishing', 'private key'
        ]
    
    def _initialize_apis(self):
        """Initialize social media APIs"""
        try:
            # Initialize Twitter API
            if self.config.get('twitter_bearer_token'):
                self.twitter_api = tweepy.Client(
                    bearer_token=self.config['twitter_bearer_token'],
                    wait_on_rate_limit=True
                )
                logger.info("✅ Twitter API initialized")
            
            # Initialize Reddit API
            if all(key in self.config for key in ['reddit_client_id', 'reddit_client_secret']):
                self.reddit_api = praw.Reddit(
                    client_id=self.config['reddit_client_id'],
                    client_secret=self.config['reddit_client_secret'],
                    user_agent='MemeSniper/1.0'
                )
                logger.info("✅ Reddit API initialized")
        
        except Exception as e:
            logger.error(f"Error initializing APIs: {e}")
    
    async def analyze_token_sentiment(self, token_symbol: str, 
                                    contract_address: str = None) -> Optional[SocialMetrics]:
        """Analyze sentiment for a specific token"""
        try:
            logger.info(f"📊 Analyzing sentiment for {token_symbol}")
            
            # Collect data from all platforms
            twitter_data = await self._analyze_twitter_sentiment(token_symbol)
            reddit_data = await self._analyze_reddit_sentiment(token_symbol)
            telegram_data = await self._analyze_telegram_sentiment(token_symbol)
            
            # Aggregate metrics
            total_mentions = (
                twitter_data.get('mentions', 0) +
                reddit_data.get('mentions', 0) +
                telegram_data.get('mentions', 0)
            )
            
            # Calculate weighted sentiment
            sentiment_scores = []
            weights = []
            
            if twitter_data.get('sentiment') is not None:
                sentiment_scores.append(twitter_data['sentiment'])
                weights.append(twitter_data.get('weight', 1.0))
            
            if reddit_data.get('sentiment') is not None:
                sentiment_scores.append(reddit_data['sentiment'])
                weights.append(reddit_data.get('weight', 1.0))
            
            if telegram_data.get('sentiment') is not None:
                sentiment_scores.append(telegram_data['sentiment'])
                weights.append(telegram_data.get('weight', 1.0))
            
            if not sentiment_scores:
                return None
            
            # Weighted average sentiment
            weighted_sentiment = np.average(sentiment_scores, weights=weights)
            
            # Determine sentiment level
            sentiment_level = self._classify_sentiment(weighted_sentiment)
            
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(total_mentions, weighted_sentiment)
            
            # Calculate engagement rate
            total_engagement = (
                twitter_data.get('engagement', 0) +
                reddit_data.get('engagement', 0) +
                telegram_data.get('engagement', 0)
            )
            
            engagement_rate = total_engagement / max(total_mentions, 1)
            
            metrics = SocialMetrics(
                mentions_count=total_mentions,
                sentiment_score=weighted_sentiment,
                sentiment_level=sentiment_level,
                trend_strength=trend_strength,
                engagement_rate=engagement_rate,
                influencer_mentions=twitter_data.get('influencer_mentions', 0),
                hashtag_volume=twitter_data.get('hashtag_volume', 0),
                reddit_posts=reddit_data.get('posts', 0),
                reddit_upvotes=reddit_data.get('upvotes', 0),
                telegram_messages=telegram_data.get('messages', 0),
                twitter_followers_reached=twitter_data.get('followers_reached', 0),
                last_updated=datetime.now()
            )
            
            # Store in history
            self.sentiment_history[token_symbol].append({
                'timestamp': datetime.now(),
                'sentiment': weighted_sentiment,
                'mentions': total_mentions
            })
            
            logger.info(f"✅ Sentiment analysis complete for {token_symbol}: {sentiment_level.value[0]}")
            return metrics
        
        except Exception as e:
            logger.error(f"Error analyzing token sentiment: {e}")
            return None
    
    async def _analyze_twitter_sentiment(self, token_symbol: str) -> Dict:
        """Analyze Twitter sentiment for a token"""
        try:
            if not self.twitter_api:
                return {}
            
            # Search for tweets mentioning the token
            query = f"${token_symbol} OR {token_symbol} -is:retweet lang:en"
            
            tweets = tweepy.Paginator(
                self.twitter_api.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations']
            ).flatten(limit=500)
            
            sentiments = []
            total_engagement = 0
            total_followers_reached = 0
            influencer_mentions = 0
            hashtag_volume = 0
            
            for tweet in tweets:
                # Analyze sentiment
                sentiment = self._analyze_text_sentiment(tweet.text)
                sentiments.append(sentiment)
                
                # Calculate engagement
                metrics = tweet.public_metrics
                engagement = (
                    metrics.get('like_count', 0) +
                    metrics.get('retweet_count', 0) +
                    metrics.get('reply_count', 0)
                )
                total_engagement += engagement
                
                # Check for influencer (simplified)
                if metrics.get('like_count', 0) > 100:
                    influencer_mentions += 1
                
                # Count hashtags
                hashtag_volume += len(re.findall(r'#\w+', tweet.text))
            
            avg_sentiment = np.mean(sentiments) if sentiments else 0.0
            
            return {
                'mentions': len(sentiments),
                'sentiment': avg_sentiment,
                'engagement': total_engagement,
                'influencer_mentions': influencer_mentions,
                'hashtag_volume': hashtag_volume,
                'followers_reached': total_followers_reached,
                'weight': 1.5  # Twitter gets higher weight
            }
        
        except Exception as e:
            logger.error(f"Error analyzing Twitter sentiment: {e}")
            return {}
    
    async def _analyze_reddit_sentiment(self, token_symbol: str) -> Dict:
        """Analyze Reddit sentiment for a token"""
        try:
            if not self.reddit_api:
                return {}
            
            # Search relevant subreddits
            subreddits = [
                'CryptoMoonShots',
                'SatoshiStreetBets',
                'altcoin',
                'CryptoCurrency',
                'defi'
            ]
            
            sentiments = []
            total_upvotes = 0
            total_posts = 0
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit_api.subreddit(subreddit_name)
                    
                    # Search for posts mentioning the token
                    for submission in subreddit.search(token_symbol, limit=50):
                        # Analyze title and selftext sentiment
                        text = f"{submission.title} {submission.selftext}"
                        sentiment = self._analyze_text_sentiment(text)
                        sentiments.append(sentiment)
                        
                        total_upvotes += submission.score
                        total_posts += 1
                
                except Exception as e:
                    logger.warning(f"Error accessing subreddit {subreddit_name}: {e}")
                    continue
            
            avg_sentiment = np.mean(sentiments) if sentiments else 0.0
            
            return {
                'mentions': len(sentiments),
                'sentiment': avg_sentiment,
                'engagement': total_upvotes,
                'posts': total_posts,
                'upvotes': total_upvotes,
                'weight': 1.2  # Reddit gets moderate weight
            }
        
        except Exception as e:
            logger.error(f"Error analyzing Reddit sentiment: {e}")
            return {}
    
    async def _analyze_telegram_sentiment(self, token_symbol: str) -> Dict:
        """Analyze Telegram sentiment for a token"""
        try:
            # Telegram analysis would require Telethon or similar
            # For demo purposes, simulate data
            
            # Simulate telegram metrics
            messages = np.random.randint(10, 200)
            sentiment = np.random.uniform(-0.5, 0.8)
            
            return {
                'mentions': messages,
                'sentiment': sentiment,
                'engagement': messages * 2,
                'messages': messages,
                'weight': 1.0
            }
        
        except Exception as e:
            logger.error(f"Error analyzing Telegram sentiment: {e}")
            return {}
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using TextBlob and custom rules"""
        try:
            # Clean text
            text = re.sub(r'http\S+', '', text)  # Remove URLs
            text = re.sub(r'@\w+', '', text)     # Remove mentions
            text = re.sub(r'#\w+', '', text)     # Remove hashtags for sentiment analysis
            
            # Use TextBlob for basic sentiment
            blob = TextBlob(text)
            base_sentiment = blob.sentiment.polarity
            
            # Apply custom rules for crypto-specific terms
            bullish_terms = [
                'moon', 'lambo', 'diamond hands', 'hodl', 'buy', 'pump',
                'bullish', 'gem', 'rocket', 'mars', 'jupiter', 'ape in'
            ]
            
            bearish_terms = [
                'dump', 'crash', 'rekt', 'paper hands', 'sell', 'bearish',
                'scam', 'rug', 'honeypot', 'exit', 'dead', 'worthless'
            ]
            
            # Count bullish/bearish terms
            text_lower = text.lower()
            bullish_count = sum(1 for term in bullish_terms if term in text_lower)
            bearish_count = sum(1 for term in bearish_terms if term in text_lower)
            
            # Adjust sentiment based on crypto-specific terms
            crypto_sentiment_adjustment = (bullish_count - bearish_count) * 0.1
            
            # Final sentiment
            final_sentiment = base_sentiment + crypto_sentiment_adjustment
            
            # Clamp between -1 and 1
            return max(-1.0, min(1.0, final_sentiment))
        
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {e}")
            return 0.0
    
    def _classify_sentiment(self, sentiment_score: float) -> SentimentLevel:
        """Classify sentiment score into levels"""
        if sentiment_score >= 0.6:
            return SentimentLevel.EXTREMELY_BULLISH
        elif sentiment_score >= 0.2:
            return SentimentLevel.BULLISH
        elif sentiment_score >= -0.2:
            return SentimentLevel.NEUTRAL
        elif sentiment_score >= -0.6:
            return SentimentLevel.BEARISH
        else:
            return SentimentLevel.EXTREMELY_BEARISH
    
    def _calculate_trend_strength(self, mentions: int, sentiment: float) -> TrendStrength:
        """Calculate trend strength based on mentions and sentiment"""
        # Base score from mentions
        if mentions >= 1000:
            base_strength = 4
        elif mentions >= 500:
            base_strength = 3
        elif mentions >= 100:
            base_strength = 2
        else:
            base_strength = 1
        
        # Adjust based on sentiment intensity
        sentiment_multiplier = abs(sentiment)
        if sentiment_multiplier >= 0.8:
            base_strength = min(4, base_strength + 1)
        elif sentiment_multiplier <= 0.2:
            base_strength = max(1, base_strength - 1)
        
        return TrendStrength(list(TrendStrength)[base_strength - 1])
    
    async def detect_trending_tokens(self, limit: int = 10) -> List[TrendingToken]:
        """Detect trending tokens across social media"""
        try:
            logger.info("🔍 Detecting trending tokens...")
            
            # Get trending hashtags and mentions
            trending_data = await self._get_trending_crypto_mentions()
            
            trending_tokens = []
            
            for token_data in trending_data[:limit]:
                symbol = token_data['symbol']
                
                # Analyze sentiment for this token
                metrics = await self.analyze_token_sentiment(symbol)
                
                if metrics:
                    # Calculate trend score
                    trend_score = self._calculate_trend_score(metrics, token_data)
                    
                    # Calculate viral potential
                    viral_potential = self._calculate_viral_potential(metrics, token_data)
                    
                    # Detect risk and opportunity signals
                    risk_signals = self._detect_risk_signals(token_data)
                    opportunity_signals = self._detect_opportunity_signals(metrics, token_data)
                    
                    trending_token = TrendingToken(
                        symbol=symbol,
                        contract_address=token_data.get('contract_address', ''),
                        mentions_24h=metrics.mentions_count,
                        sentiment_change=token_data.get('sentiment_change', 0.0),
                        trend_score=trend_score,
                        viral_potential=viral_potential,
                        risk_signals=risk_signals,
                        opportunity_signals=opportunity_signals
                    )
                    
                    trending_tokens.append(trending_token)
            
            # Sort by trend score
            trending_tokens.sort(key=lambda x: x.trend_score, reverse=True)
            
            logger.info(f"✅ Found {len(trending_tokens)} trending tokens")
            return trending_tokens
        
        except Exception as e:
            logger.error(f"Error detecting trending tokens: {e}")
            return []
    
    async def _get_trending_crypto_mentions(self) -> List[Dict]:
        """Get trending cryptocurrency mentions"""
        try:
            # This would integrate with social media APIs to get trending topics
            # For demo, simulate trending data
            
            trending_symbols = [
                'PEPE', 'DOGE', 'SHIB', 'FLOKI', 'BABYDOGE',
                'SAFEMOON', 'KISHU', 'AKITA', 'DOGELON', 'HOGE'
            ]
            
            trending_data = []
            for symbol in trending_symbols:
                trending_data.append({
                    'symbol': symbol,
                    'mentions_24h': np.random.randint(50, 2000),
                    'sentiment_change': np.random.uniform(-0.5, 0.5),
                    'contract_address': f"0x{''.join(['a'] * 40)}"  # Dummy address
                })
            
            return trending_data
        
        except Exception as e:
            logger.error(f"Error getting trending mentions: {e}")
            return []
    
    def _calculate_trend_score(self, metrics: SocialMetrics, token_data: Dict) -> float:
        """Calculate overall trend score"""
        try:
            # Base score from mentions
            mention_score = min(100, metrics.mentions_count / 10)
            
            # Sentiment score (positive sentiment gets higher score)
            sentiment_score = (metrics.sentiment_score + 1) * 50  # Convert -1,1 to 0,100
            
            # Engagement score
            engagement_score = min(100, metrics.engagement_rate * 100)
            
            # Trend strength score
            trend_score = metrics.trend_strength.value[1] * 25
            
            # Weighted average
            weights = [0.3, 0.25, 0.25, 0.2]
            scores = [mention_score, sentiment_score, engagement_score, trend_score]
            
            return sum(w * s for w, s in zip(weights, scores))
        
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.0
    
    def _calculate_viral_potential(self, metrics: SocialMetrics, token_data: Dict) -> float:
        """Calculate viral potential score"""
        try:
            # Factors that contribute to viral potential
            factors = []
            
            # High engagement rate
            if metrics.engagement_rate > 2.0:
                factors.append(0.3)
            
            # Influencer mentions
            if metrics.influencer_mentions > 5:
                factors.append(0.25)
            
            # Strong positive sentiment
            if metrics.sentiment_score > 0.5:
                factors.append(0.2)
            
            # High hashtag volume
            if metrics.hashtag_volume > 50:
                factors.append(0.15)
            
            # Cross-platform presence
            if metrics.reddit_posts > 10 and metrics.telegram_messages > 20:
                factors.append(0.1)
            
            return sum(factors)
        
        except Exception as e:
            logger.error(f"Error calculating viral potential: {e}")
            return 0.0
    
    def _detect_risk_signals(self, token_data: Dict) -> List[str]:
        """Detect risk signals in social media data"""
        risk_signals = []
        
        # Check for scam patterns in mentions
        # This would analyze actual social media content
        
        # Simulate risk detection
        import random
        potential_risks = [
            "Coordinated pump mentions detected",
            "Suspicious influencer promotion",
            "Fake giveaway posts",
            "Impersonation accounts active",
            "Pump group activity"
        ]
        
        # Randomly add some risk signals for demo
        if random.random() < 0.3:  # 30% chance of risk signals
            risk_signals.extend(random.sample(potential_risks, random.randint(1, 2)))
        
        return risk_signals
    
    def _detect_opportunity_signals(self, metrics: SocialMetrics, token_data: Dict) -> List[str]:
        """Detect opportunity signals"""
        opportunity_signals = []
        
        if metrics.sentiment_score > 0.6:
            opportunity_signals.append("Strong positive sentiment")
        
        if metrics.trend_strength in [TrendStrength.STRONG, TrendStrength.VIRAL]:
            opportunity_signals.append("High trend strength")
        
        if metrics.engagement_rate > 2.0:
            opportunity_signals.append("High engagement rate")
        
        if metrics.influencer_mentions > 3:
            opportunity_signals.append("Influencer attention")
        
        return opportunity_signals
    
    async def monitor_social_signals(self, tokens: List[str]) -> Dict[str, SocialMetrics]:
        """Monitor social signals for multiple tokens"""
        try:
            logger.info(f"📊 Monitoring social signals for {len(tokens)} tokens")
            
            results = {}
            
            # Analyze each token
            for token in tokens:
                metrics = await self.analyze_token_sentiment(token)
                if metrics:
                    results[token] = metrics
                
                # Rate limiting
                await asyncio.sleep(1)
            
            logger.info(f"✅ Social monitoring complete for {len(results)} tokens")
            return results
        
        except Exception as e:
            logger.error(f"Error monitoring social signals: {e}")
            return {}
    
    def get_sentiment_history(self, token_symbol: str, hours: int = 24) -> List[Dict]:
        """Get sentiment history for a token"""
        try:
            history = self.sentiment_history.get(token_symbol, [])
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_history = [
                entry for entry in history
                if entry['timestamp'] > cutoff_time
            ]
            
            return filtered_history
        
        except Exception as e:
            logger.error(f"Error getting sentiment history: {e}")
            return []

# Example usage
async def example_usage():
    """Example of how to use the Social Sentiment Analyzer"""
    
    config = {
        'twitter_bearer_token': 'YOUR_TWITTER_BEARER_TOKEN',
        'reddit_client_id': 'YOUR_REDDIT_CLIENT_ID',
        'reddit_client_secret': 'YOUR_REDDIT_CLIENT_SECRET'
    }
    
    # Initialize analyzer
    analyzer = SocialSentimentAnalyzer(config)
    
    # Analyze sentiment for a specific token
    metrics = await analyzer.analyze_token_sentiment('PEPE')
    
    if metrics:
        print(f"📊 Social Sentiment Analysis for PEPE")
        print(f"Mentions: {metrics.mentions_count}")
        print(f"Sentiment: {metrics.sentiment_level.value[0]}")
        print(f"Trend Strength: {metrics.trend_strength.value[0]}")
        print(f"Engagement Rate: {metrics.engagement_rate:.2f}")
    
    # Detect trending tokens
    trending = await analyzer.detect_trending_tokens(limit=5)
    
    print("\n🔥 Trending Tokens:")
    for token in trending:
        print(f"  {token.symbol}: Score {token.trend_score:.1f}, "
              f"Viral Potential {token.viral_potential:.1%}")

if __name__ == "__main__":
    asyncio.run(example_usage()) 