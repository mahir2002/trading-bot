#!/usr/bin/env python3
"""
🐦 Twitter Crypto News Analyzer
Real-time cryptocurrency news analysis and memecoin discovery
"""

import tweepy
import pandas as pd
import numpy as np
import re
import time
import logging
from datetime import datetime, timedelta
from textblob import TextBlob
from collections import Counter, defaultdict
import requests
import json
from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_crypto_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitterCryptoAnalyzer:
    def __init__(self):
        """Initialize Twitter API and analysis parameters"""
        self.setup_twitter_api()
        self.setup_keywords()
        self.setup_binance_api()
        
        # Analysis parameters
        self.sentiment_threshold = float(os.getenv('SENTIMENT_THRESHOLD', '0.3'))
        self.volume_threshold = float(os.getenv('VOLUME_THRESHOLD', '1000000'))
        self.tweet_limit = int(os.getenv('TWEET_LIMIT', '100'))
        self.analysis_interval = int(os.getenv('ANALYSIS_INTERVAL', '300'))  # 5 minutes
        
        # Data storage
        self.tweet_data = []
        self.crypto_mentions = defaultdict(list)
        self.sentiment_scores = defaultdict(list)
        self.discovered_coins = set()
        
    def setup_twitter_api(self):
        """Setup Twitter API v2 client"""
        try:
            # Twitter API credentials from environment
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            api_key = os.getenv('TWITTER_API_KEY')
            api_secret = os.getenv('TWITTER_API_SECRET')
            access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            
            if not bearer_token:
                logger.warning("⚠️ Twitter Bearer Token not found. Using demo mode.")
                self.twitter_client = None
                return
                
            # Initialize Twitter API v2 client
            self.twitter_client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )
            
            logger.info("✅ Twitter API initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Twitter API setup failed: {e}")
            self.twitter_client = None
    
    def setup_keywords(self):
        """Setup cryptocurrency and memecoin detection keywords"""
        self.crypto_keywords = {
            # Major cryptocurrencies
            'major': [
                'bitcoin', 'btc', 'ethereum', 'eth', 'binance', 'bnb',
                'cardano', 'ada', 'solana', 'sol', 'polkadot', 'dot',
                'avalanche', 'avax', 'polygon', 'matic', 'chainlink', 'link'
            ],
            
            # DeFi tokens
            'defi': [
                'uniswap', 'uni', 'aave', 'compound', 'comp', 'makerdao', 'mkr',
                'sushiswap', 'sushi', 'curve', 'crv', '1inch', 'yearn', 'yfi'
            ],
            
            # Memecoins and trending
            'meme': [
                'dogecoin', 'doge', 'shiba', 'shib', 'pepe', 'floki', 'bonk',
                'wif', 'meme', 'memecoin', 'moonshot', 'gem', 'ape', 'hodl'
            ],
            
            # Gaming and NFT
            'gaming': [
                'axie', 'axs', 'sandbox', 'sand', 'decentraland', 'mana',
                'enjin', 'enj', 'gala', 'nft', 'metaverse', 'gaming'
            ],
            
            # AI and emerging tech
            'ai': [
                'fetch', 'fet', 'ocean', 'agix', 'render', 'rndr',
                'artificial intelligence', 'ai crypto', 'machine learning'
            ],
            
            # Profit indicators
            'profit_signals': [
                'moon', 'rocket', '🚀', '📈', 'pump', 'bullish', 'breakout',
                'rally', 'surge', 'explosion', 'parabolic', 'x100', 'x10',
                'gem found', 'hidden gem', 'next big thing', 'early entry'
            ],
            
            # New coin indicators
            'new_coin_signals': [
                'new listing', 'just launched', 'presale', 'ico', 'ido',
                'new token', 'fresh launch', 'stealth launch', 'fair launch',
                'new gem', 'brand new', 'just dropped'
            ]
        }
        
        # Compile all keywords for search
        self.all_keywords = []
        for category, keywords in self.crypto_keywords.items():
            self.all_keywords.extend(keywords)
    
    def setup_binance_api(self):
        """Setup Binance API for price verification"""
        self.binance_base_url = "https://api.binance.com/api/v3"
        
    def fetch_crypto_tweets(self, max_results: int = 100) -> List[Dict]:
        """Fetch recent cryptocurrency-related tweets"""
        if not self.twitter_client:
            logger.warning("⚠️ Twitter API not available, using demo data")
            return self.generate_demo_tweets()
        
        try:
            # Build search query
            crypto_query = " OR ".join([f'"{keyword}"' for keyword in self.all_keywords[:10]])  # Limit query length
            query = f"({crypto_query}) -is:retweet lang:en"
            
            # Fetch tweets
            tweets = tweepy.Paginator(
                self.twitter_client.search_recent_tweets,
                query=query,
                max_results=min(max_results, 100),  # API limit
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations']
            ).flatten(limit=max_results)
            
            tweet_data = []
            for tweet in tweets:
                tweet_info = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'author_id': tweet.author_id,
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'like_count': tweet.public_metrics['like_count'],
                    'reply_count': tweet.public_metrics['reply_count'],
                    'quote_count': tweet.public_metrics['quote_count']
                }
                tweet_data.append(tweet_info)
            
            logger.info(f"📱 Fetched {len(tweet_data)} tweets")
            return tweet_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching tweets: {e}")
            return self.generate_demo_tweets()
    
    def generate_demo_tweets(self) -> List[Dict]:
        """Generate demo tweets for testing when API is not available"""
        demo_tweets = [
            {
                'id': 1,
                'text': '🚀 New memecoin $ROCKET just launched! Hidden gem potential 100x! #crypto #memecoin',
                'created_at': datetime.now(),
                'author_id': 'demo_user_1',
                'retweet_count': 45,
                'like_count': 120,
                'reply_count': 23,
                'quote_count': 8
            },
            {
                'id': 2,
                'text': 'Bitcoin breaking resistance! $BTC looking bullish 📈 Next target $120k',
                'created_at': datetime.now() - timedelta(minutes=5),
                'author_id': 'demo_user_2',
                'retweet_count': 89,
                'like_count': 234,
                'reply_count': 45,
                'quote_count': 12
            },
            {
                'id': 3,
                'text': 'PEPE coin surging! 🐸 Memecoin season is back! $PEPE to the moon!',
                'created_at': datetime.now() - timedelta(minutes=10),
                'author_id': 'demo_user_3',
                'retweet_count': 156,
                'like_count': 445,
                'reply_count': 67,
                'quote_count': 23
            },
            {
                'id': 4,
                'text': 'New AI token $AIBOT just listed on DEX! Early entry opportunity 🤖',
                'created_at': datetime.now() - timedelta(minutes=15),
                'author_id': 'demo_user_4',
                'retweet_count': 34,
                'like_count': 89,
                'reply_count': 12,
                'quote_count': 5
            },
            {
                'id': 5,
                'text': 'Solana ecosystem exploding! $SOL DeFi tokens pumping hard 🔥',
                'created_at': datetime.now() - timedelta(minutes=20),
                'author_id': 'demo_user_5',
                'retweet_count': 78,
                'like_count': 198,
                'reply_count': 34,
                'quote_count': 9
            }
        ]
        
        logger.info(f"📱 Generated {len(demo_tweets)} demo tweets")
        return demo_tweets
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of tweet text"""
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment
            
            # Classify sentiment
            if sentiment.polarity > 0.1:
                classification = 'positive'
            elif sentiment.polarity < -0.1:
                classification = 'negative'
            else:
                classification = 'neutral'
            
            return {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'classification': classification
            }
        except Exception as e:
            logger.error(f"❌ Sentiment analysis error: {e}")
            return {'polarity': 0, 'subjectivity': 0, 'classification': 'neutral'}
    
    def extract_crypto_mentions(self, text: str) -> List[Dict]:
        """Extract cryptocurrency mentions from tweet text"""
        mentions = []
        text_lower = text.lower()
        
        # Check for each keyword category
        for category, keywords in self.crypto_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    mentions.append({
                        'keyword': keyword,
                        'category': category,
                        'context': self.extract_context(text, keyword)
                    })
        
        # Extract potential new coins ($ symbols)
        dollar_mentions = re.findall(r'\$([A-Z]{2,10})', text.upper())
        for mention in dollar_mentions:
            mentions.append({
                'keyword': f'${mention}',
                'category': 'potential_new',
                'context': self.extract_context(text, f'${mention}')
            })
        
        return mentions
    
    def extract_context(self, text: str, keyword: str, window: int = 20) -> str:
        """Extract context around a keyword"""
        try:
            text_lower = text.lower()
            keyword_lower = keyword.lower()
            
            start_idx = text_lower.find(keyword_lower)
            if start_idx == -1:
                return text[:50]  # Return first 50 chars if keyword not found
            
            start = max(0, start_idx - window)
            end = min(len(text), start_idx + len(keyword) + window)
            
            return text[start:end].strip()
        except:
            return text[:50]
    
    def calculate_engagement_score(self, tweet: Dict) -> float:
        """Calculate engagement score for a tweet"""
        try:
            retweets = tweet.get('retweet_count', 0)
            likes = tweet.get('like_count', 0)
            replies = tweet.get('reply_count', 0)
            quotes = tweet.get('quote_count', 0)
            
            # Weighted engagement score
            score = (retweets * 3) + (likes * 1) + (replies * 2) + (quotes * 2)
            return score
        except:
            return 0
    
    def identify_profit_opportunities(self, analyzed_tweets: List[Dict]) -> List[Dict]:
        """Identify potential profit opportunities from analyzed tweets"""
        opportunities = []
        
        # Group by cryptocurrency
        crypto_data = defaultdict(list)
        for tweet in analyzed_tweets:
            for mention in tweet['mentions']:
                crypto_data[mention['keyword']].append({
                    'tweet': tweet,
                    'mention': mention,
                    'sentiment': tweet['sentiment'],
                    'engagement': tweet['engagement_score']
                })
        
        # Analyze each cryptocurrency
        for crypto, data in crypto_data.items():
            if len(data) < 2:  # Need at least 2 mentions
                continue
            
            # Calculate metrics
            avg_sentiment = np.mean([d['sentiment']['polarity'] for d in data])
            total_engagement = sum([d['engagement'] for d in data])
            mention_count = len(data)
            
            # Check for profit signals
            profit_signals = 0
            new_coin_signals = 0
            
            for d in data:
                tweet_text = d['tweet']['text'].lower()
                
                # Count profit indicators
                for signal in self.crypto_keywords['profit_signals']:
                    if signal.lower() in tweet_text:
                        profit_signals += 1
                
                # Count new coin indicators
                for signal in self.crypto_keywords['new_coin_signals']:
                    if signal.lower() in tweet_text:
                        new_coin_signals += 1
            
            # Calculate opportunity score
            opportunity_score = (
                (avg_sentiment * 30) +
                (total_engagement / 100) +
                (mention_count * 5) +
                (profit_signals * 10) +
                (new_coin_signals * 15)
            )
            
            # Determine opportunity type
            opportunity_type = 'established'
            if new_coin_signals > 0:
                opportunity_type = 'new_coin'
            elif any(mention['mention']['category'] == 'meme' for mention in data):
                opportunity_type = 'memecoin'
            
            opportunities.append({
                'symbol': crypto,
                'opportunity_score': opportunity_score,
                'opportunity_type': opportunity_type,
                'avg_sentiment': avg_sentiment,
                'total_engagement': total_engagement,
                'mention_count': mention_count,
                'profit_signals': profit_signals,
                'new_coin_signals': new_coin_signals,
                'sample_tweets': [d['tweet']['text'] for d in data[:3]]
            })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return opportunities
    
    def verify_coin_existence(self, symbol: str) -> Dict:
        """Verify if a cryptocurrency exists on Binance"""
        try:
            # Clean symbol
            clean_symbol = symbol.replace('$', '').upper()
            if not clean_symbol.endswith('USDT'):
                clean_symbol += 'USDT'
            
            # Check Binance API
            url = f"{self.binance_base_url}/ticker/24hr"
            params = {'symbol': clean_symbol}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'exists': True,
                    'symbol': clean_symbol,
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                    'volume_24h': float(data['volume'])
                }
            else:
                return {'exists': False, 'symbol': clean_symbol}
                
        except Exception as e:
            logger.error(f"❌ Error verifying coin {symbol}: {e}")
            return {'exists': False, 'symbol': symbol}
    
    def analyze_tweets(self) -> Dict:
        """Main analysis function"""
        logger.info("🔍 Starting Twitter crypto analysis...")
        
        # Fetch tweets
        tweets = self.fetch_crypto_tweets(self.tweet_limit)
        
        if not tweets:
            logger.warning("⚠️ No tweets fetched")
            return {'opportunities': [], 'summary': {}}
        
        # Analyze each tweet
        analyzed_tweets = []
        for tweet in tweets:
            try:
                # Sentiment analysis
                sentiment = self.analyze_sentiment(tweet['text'])
                
                # Extract crypto mentions
                mentions = self.extract_crypto_mentions(tweet['text'])
                
                # Calculate engagement
                engagement_score = self.calculate_engagement_score(tweet)
                
                analyzed_tweet = {
                    **tweet,
                    'sentiment': sentiment,
                    'mentions': mentions,
                    'engagement_score': engagement_score
                }
                
                analyzed_tweets.append(analyzed_tweet)
                
            except Exception as e:
                logger.error(f"❌ Error analyzing tweet {tweet.get('id', 'unknown')}: {e}")
                continue
        
        # Identify opportunities
        opportunities = self.identify_profit_opportunities(analyzed_tweets)
        
        # Verify top opportunities
        verified_opportunities = []
        for opp in opportunities[:10]:  # Check top 10
            verification = self.verify_coin_existence(opp['symbol'])
            opp['verification'] = verification
            verified_opportunities.append(opp)
        
        # Generate summary
        summary = {
            'total_tweets': len(tweets),
            'analyzed_tweets': len(analyzed_tweets),
            'total_opportunities': len(opportunities),
            'verified_opportunities': len([o for o in verified_opportunities if o['verification']['exists']]),
            'avg_sentiment': np.mean([t['sentiment']['polarity'] for t in analyzed_tweets]),
            'top_categories': self.get_top_categories(analyzed_tweets)
        }
        
        logger.info(f"✅ Analysis complete: {summary['total_opportunities']} opportunities found")
        
        return {
            'opportunities': verified_opportunities,
            'summary': summary,
            'analyzed_tweets': analyzed_tweets
        }
    
    def get_top_categories(self, analyzed_tweets: List[Dict]) -> Dict:
        """Get top mentioned categories"""
        category_counts = defaultdict(int)
        
        for tweet in analyzed_tweets:
            for mention in tweet['mentions']:
                category_counts[mention['category']] += 1
        
        return dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))
    
    def generate_report(self, analysis_results: Dict) -> str:
        """Generate a formatted analysis report"""
        opportunities = analysis_results['opportunities']
        summary = analysis_results['summary']
        
        report = f"""
🐦 TWITTER CRYPTO ANALYSIS REPORT
{'='*50}
📊 SUMMARY:
   • Total Tweets Analyzed: {summary['total_tweets']}
   • Opportunities Found: {summary['total_opportunities']}
   • Verified on Exchange: {summary['verified_opportunities']}
   • Average Sentiment: {summary['avg_sentiment']:.3f}

🚀 TOP OPPORTUNITIES:
"""
        
        for i, opp in enumerate(opportunities[:5], 1):
            status = "✅ VERIFIED" if opp['verification']['exists'] else "❌ NOT FOUND"
            price_info = ""
            
            if opp['verification']['exists']:
                price_info = f" | Price: ${opp['verification']['price']:.6f} | 24h: {opp['verification']['change_24h']:.2f}%"
            
            report += f"""
{i}. {opp['symbol']} ({opp['opportunity_type'].upper()}) - {status}
   Score: {opp['opportunity_score']:.1f} | Sentiment: {opp['avg_sentiment']:.3f} | Mentions: {opp['mention_count']}{price_info}
   Sample: "{opp['sample_tweets'][0][:100]}..."
"""
        
        report += f"""
📈 CATEGORY BREAKDOWN:
"""
        for category, count in summary['top_categories'].items():
            report += f"   • {category.title()}: {count} mentions\n"
        
        return report

def main():
    """Main execution function"""
    print("🐦 Starting Twitter Crypto News Analyzer...")
    
    analyzer = TwitterCryptoAnalyzer()
    
    try:
        while True:
            # Run analysis
            results = analyzer.analyze_tweets()
            
            # Generate and display report
            report = analyzer.generate_report(results)
            print(report)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f'twitter_analysis_{timestamp}.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"💾 Results saved to twitter_analysis_{timestamp}.json")
            
            # Wait for next analysis
            logger.info(f"⏰ Waiting {analyzer.analysis_interval} seconds for next analysis...")
            time.sleep(analyzer.analysis_interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Analysis stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 