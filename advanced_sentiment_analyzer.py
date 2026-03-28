#!/usr/bin/env python3
"""
📊 ADVANCED SENTIMENT ANALYZER 📊
Comprehensive sentiment analysis combining:
- Twitter sentiment analysis
- Reddit sentiment tracking
- News sentiment analysis
- On-chain sentiment indicators
- Fear & Greed Index
- Social volume analysis
- Influencer tracking
"""

import os
import sys
import time
import logging
import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Core libraries
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

# NLP libraries
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import transformers
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Social media APIs
import tweepy
import praw  # Reddit API

# Web scraping
from bs4 import BeautifulSoup
import feedparser

# Visualization
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Dashboard
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SentimentSource(Enum):
    """Sentiment data sources"""
    TWITTER = "twitter"
    REDDIT = "reddit"
    NEWS = "news"
    FEAR_GREED = "fear_greed"
    ON_CHAIN = "on_chain"
    SOCIAL_VOLUME = "social_volume"
    INFLUENCER = "influencer"

class SentimentPolarity(Enum):
    """Sentiment polarity levels"""
    EXTREMELY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    EXTREMELY_BULLISH = 2

@dataclass
class SentimentData:
    """Sentiment analysis result"""
    source: SentimentSource
    symbol: str
    sentiment_score: float  # -1 to 1
    confidence: float  # 0 to 1
    volume: int
    polarity: SentimentPolarity
    timestamp: datetime
    raw_data: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    influencer_mentions: int = 0
    viral_score: float = 0.0

@dataclass
class ComprehensiveSentiment:
    """Comprehensive sentiment analysis result"""
    symbol: str
    overall_sentiment: float
    confidence: float
    sentiment_breakdown: Dict[SentimentSource, float]
    volume_weighted_sentiment: float
    trend_direction: str
    key_drivers: List[str]
    risk_level: str
    timestamp: datetime

class TwitterSentimentAnalyzer:
    """Twitter sentiment analysis"""
    
    def __init__(self):
        """Initialize Twitter API"""
        load_dotenv('config.env')
        
        # Twitter API credentials
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Initialize Twitter client
        if self.bearer_token:
            self.client = tweepy.Client(bearer_token=self.bearer_token)
        else:
            self.client = None
            logger.warning("Twitter API credentials not found")
        
        # Sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Crypto influencers list
        self.crypto_influencers = [
            'elonmusk', 'michael_saylor', 'VitalikButerin', 'cz_binance',
            'SBF_FTX', 'APompliano', 'DocumentingBTC', 'WhalePanda',
            'PlanB_99', 'RaoulGMI', 'novogratz', 'tyler', 'cameron'
        ]
    
    def analyze_twitter_sentiment(self, symbol: str, limit: int = 100) -> SentimentData:
        """Analyze Twitter sentiment for a cryptocurrency"""
        try:
            if not self.client:
                return self._create_dummy_sentiment(symbol, SentimentSource.TWITTER)
            
            # Search for tweets
            query = f"${symbol} OR {symbol} -is:retweet lang:en"
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=limit,
                tweet_fields=['created_at', 'public_metrics', 'author_id']
            )
            
            if not tweets.data:
                return self._create_dummy_sentiment(symbol, SentimentSource.TWITTER)
            
            # Analyze sentiment
            sentiments = []
            total_engagement = 0
            influencer_mentions = 0
            
            for tweet in tweets.data:
                # Clean tweet text
                text = self._clean_tweet_text(tweet.text)
                
                # Calculate sentiment
                sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
                sentiment = sentiment_scores['compound']
                
                # Weight by engagement
                metrics = tweet.public_metrics
                engagement = metrics['like_count'] + metrics['retweet_count'] + metrics['reply_count']
                total_engagement += engagement
                
                # Check for influencer
                if self._is_influencer_tweet(tweet.author_id):
                    influencer_mentions += 1
                    sentiment *= 1.5  # Weight influencer tweets more
                
                sentiments.append(sentiment * (1 + np.log(1 + engagement)))
            
            # Calculate overall sentiment
            if sentiments:
                overall_sentiment = np.mean(sentiments)
                confidence = min(len(sentiments) / 50, 1.0)  # More tweets = higher confidence
            else:
                overall_sentiment = 0.0
                confidence = 0.0
            
            # Calculate viral score
            viral_score = min(total_engagement / 10000, 1.0)
            
            return SentimentData(
                source=SentimentSource.TWITTER,
                symbol=symbol,
                sentiment_score=overall_sentiment,
                confidence=confidence,
                volume=len(sentiments),
                polarity=self._score_to_polarity(overall_sentiment),
                timestamp=datetime.now(),
                influencer_mentions=influencer_mentions,
                viral_score=viral_score,
                raw_data={'total_engagement': total_engagement}
            )
            
        except Exception as e:
            logger.error(f"Error analyzing Twitter sentiment for {symbol}: {e}")
            return self._create_dummy_sentiment(symbol, SentimentSource.TWITTER)
    
    def _clean_tweet_text(self, text: str) -> str:
        """Clean tweet text for sentiment analysis"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove user mentions and hashtags for cleaner analysis
        text = re.sub(r'@\w+|#\w+', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def _is_influencer_tweet(self, author_id: str) -> bool:
        """Check if tweet is from a crypto influencer"""
        # This would require mapping author_id to username
        # For now, return False as placeholder
        return False
    
    def _create_dummy_sentiment(self, symbol: str, source: SentimentSource) -> SentimentData:
        """Create dummy sentiment data when API is unavailable"""
        return SentimentData(
            source=source,
            symbol=symbol,
            sentiment_score=0.0,
            confidence=0.0,
            volume=0,
            polarity=SentimentPolarity.NEUTRAL,
            timestamp=datetime.now()
        )
    
    def _score_to_polarity(self, score: float) -> SentimentPolarity:
        """Convert sentiment score to polarity enum"""
        if score <= -0.6:
            return SentimentPolarity.EXTREMELY_BEARISH
        elif score <= -0.2:
            return SentimentPolarity.BEARISH
        elif score >= 0.6:
            return SentimentPolarity.EXTREMELY_BULLISH
        elif score >= 0.2:
            return SentimentPolarity.BULLISH
        else:
            return SentimentPolarity.NEUTRAL

class RedditSentimentAnalyzer:
    """Reddit sentiment analysis"""
    
    def __init__(self):
        """Initialize Reddit API"""
        load_dotenv('config.env')
        
        # Reddit API credentials
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'CryptoSentimentBot/1.0')
        
        if client_id and client_secret:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
        else:
            self.reddit = None
            logger.warning("Reddit API credentials not found")
        
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Crypto subreddits
        self.crypto_subreddits = [
            'cryptocurrency', 'bitcoin', 'ethereum', 'altcoin',
            'cryptomarkets', 'defi', 'nft', 'dogecoin'
        ]
    
    def analyze_reddit_sentiment(self, symbol: str, limit: int = 50) -> SentimentData:
        """Analyze Reddit sentiment for a cryptocurrency"""
        try:
            if not self.reddit:
                return self._create_dummy_sentiment(symbol, SentimentSource.REDDIT)
            
            sentiments = []
            total_score = 0
            
            for subreddit_name in self.crypto_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search for posts about the symbol
                    for submission in subreddit.search(symbol, limit=limit//len(self.crypto_subreddits)):
                        # Analyze title sentiment
                        title_sentiment = self.sentiment_analyzer.polarity_scores(submission.title)
                        
                        # Weight by upvotes and comments
                        weight = np.log(1 + submission.score + submission.num_comments)
                        weighted_sentiment = title_sentiment['compound'] * weight
                        
                        sentiments.append(weighted_sentiment)
                        total_score += submission.score
                        
                except Exception as e:
                    logger.warning(f"Error accessing subreddit {subreddit_name}: {e}")
                    continue
            
            # Calculate overall sentiment
            if sentiments:
                overall_sentiment = np.mean(sentiments)
                confidence = min(len(sentiments) / 25, 1.0)
            else:
                overall_sentiment = 0.0
                confidence = 0.0
            
            return SentimentData(
                source=SentimentSource.REDDIT,
                symbol=symbol,
                sentiment_score=overall_sentiment,
                confidence=confidence,
                volume=len(sentiments),
                polarity=self._score_to_polarity(overall_sentiment),
                timestamp=datetime.now(),
                raw_data={'total_score': total_score}
            )
            
        except Exception as e:
            logger.error(f"Error analyzing Reddit sentiment for {symbol}: {e}")
            return self._create_dummy_sentiment(symbol, SentimentSource.REDDIT)
    
    def _create_dummy_sentiment(self, symbol: str, source: SentimentSource) -> SentimentData:
        """Create dummy sentiment data"""
        return SentimentData(
            source=source,
            symbol=symbol,
            sentiment_score=0.0,
            confidence=0.0,
            volume=0,
            polarity=SentimentPolarity.NEUTRAL,
            timestamp=datetime.now()
        )
    
    def _score_to_polarity(self, score: float) -> SentimentPolarity:
        """Convert sentiment score to polarity enum"""
        if score <= -0.6:
            return SentimentPolarity.EXTREMELY_BEARISH
        elif score <= -0.2:
            return SentimentPolarity.BEARISH
        elif score >= 0.6:
            return SentimentPolarity.EXTREMELY_BULLISH
        elif score >= 0.2:
            return SentimentPolarity.BULLISH
        else:
            return SentimentPolarity.NEUTRAL

class NewsSentimentAnalyzer:
    """News sentiment analysis"""
    
    def __init__(self):
        """Initialize news sentiment analyzer"""
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # News sources
        self.news_sources = [
            'https://cointelegraph.com/rss',
            'https://coindesk.com/arc/outboundfeeds/rss/',
            'https://decrypt.co/feed',
            'https://www.coinbase.com/blog/rss.xml'
        ]
        
        # Initialize transformer model for better sentiment analysis
        try:
            self.transformer_sentiment = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment"
            )
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}")
            self.transformer_sentiment = None
    
    def analyze_news_sentiment(self, symbol: str) -> SentimentData:
        """Analyze news sentiment for a cryptocurrency"""
        try:
            articles = []
            
            for source_url in self.news_sources:
                try:
                    feed = feedparser.parse(source_url)
                    
                    for entry in feed.entries[:10]:  # Limit per source
                        title = entry.title
                        summary = getattr(entry, 'summary', '')
                        
                        # Check if article mentions the symbol
                        text = f"{title} {summary}".lower()
                        if symbol.lower() in text or f"${symbol.lower()}" in text:
                            articles.append({
                                'title': title,
                                'summary': summary,
                                'published': getattr(entry, 'published', ''),
                                'link': getattr(entry, 'link', '')
                            })
                            
                except Exception as e:
                    logger.warning(f"Error fetching from {source_url}: {e}")
                    continue
            
            if not articles:
                return self._create_dummy_sentiment(symbol, SentimentSource.NEWS)
            
            # Analyze sentiment
            sentiments = []
            
            for article in articles:
                text = f"{article['title']} {article['summary']}"
                
                # Use VADER sentiment
                vader_scores = self.sentiment_analyzer.polarity_scores(text)
                sentiment = vader_scores['compound']
                
                # Use transformer model if available
                if self.transformer_sentiment:
                    try:
                        transformer_result = self.transformer_sentiment(text[:512])  # Limit length
                        transformer_score = transformer_result[0]['score']
                        if transformer_result[0]['label'] in ['NEGATIVE', '1 star', '2 stars']:
                            transformer_score = -transformer_score
                        elif transformer_result[0]['label'] in ['POSITIVE', '4 stars', '5 stars']:
                            pass  # Keep positive
                        else:
                            transformer_score = 0  # Neutral
                        
                        # Combine VADER and transformer
                        sentiment = (sentiment + transformer_score) / 2
                    except Exception as e:
                        logger.warning(f"Error with transformer sentiment: {e}")
                
                sentiments.append(sentiment)
            
            # Calculate overall sentiment
            overall_sentiment = np.mean(sentiments) if sentiments else 0.0
            confidence = min(len(sentiments) / 10, 1.0)
            
            return SentimentData(
                source=SentimentSource.NEWS,
                symbol=symbol,
                sentiment_score=overall_sentiment,
                confidence=confidence,
                volume=len(sentiments),
                polarity=self._score_to_polarity(overall_sentiment),
                timestamp=datetime.now(),
                raw_data={'articles_count': len(articles)}
            )
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {e}")
            return self._create_dummy_sentiment(symbol, SentimentSource.NEWS)
    
    def _create_dummy_sentiment(self, symbol: str, source: SentimentSource) -> SentimentData:
        """Create dummy sentiment data"""
        return SentimentData(
            source=source,
            symbol=symbol,
            sentiment_score=0.0,
            confidence=0.0,
            volume=0,
            polarity=SentimentPolarity.NEUTRAL,
            timestamp=datetime.now()
        )
    
    def _score_to_polarity(self, score: float) -> SentimentPolarity:
        """Convert sentiment score to polarity enum"""
        if score <= -0.6:
            return SentimentPolarity.EXTREMELY_BEARISH
        elif score <= -0.2:
            return SentimentPolarity.BEARISH
        elif score >= 0.6:
            return SentimentPolarity.EXTREMELY_BULLISH
        elif score >= 0.2:
            return SentimentPolarity.BULLISH
        else:
            return SentimentPolarity.NEUTRAL

class FearGreedAnalyzer:
    """Fear & Greed Index analyzer"""
    
    def __init__(self):
        """Initialize Fear & Greed analyzer"""
        self.api_url = "https://api.alternative.me/fng/"
    
    def get_fear_greed_index(self) -> SentimentData:
        """Get current Fear & Greed Index"""
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['data']:
                fng_data = data['data'][0]
                value = int(fng_data['value'])
                classification = fng_data['value_classification']
                
                # Convert to sentiment score (-1 to 1)
                sentiment_score = (value - 50) / 50  # 0-100 to -1 to 1
                
                # Determine polarity
                if value <= 20:
                    polarity = SentimentPolarity.EXTREMELY_BEARISH
                elif value <= 40:
                    polarity = SentimentPolarity.BEARISH
                elif value >= 80:
                    polarity = SentimentPolarity.EXTREMELY_BULLISH
                elif value >= 60:
                    polarity = SentimentPolarity.BULLISH
                else:
                    polarity = SentimentPolarity.NEUTRAL
                
                return SentimentData(
                    source=SentimentSource.FEAR_GREED,
                    symbol="MARKET",
                    sentiment_score=sentiment_score,
                    confidence=0.9,  # High confidence in official index
                    volume=1,
                    polarity=polarity,
                    timestamp=datetime.now(),
                    raw_data={
                        'value': value,
                        'classification': classification,
                        'timestamp': fng_data['timestamp']
                    }
                )
            
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
        
        # Return neutral sentiment if error
        return SentimentData(
            source=SentimentSource.FEAR_GREED,
            symbol="MARKET",
            sentiment_score=0.0,
            confidence=0.0,
            volume=0,
            polarity=SentimentPolarity.NEUTRAL,
            timestamp=datetime.now()
        )

class AdvancedSentimentAnalyzer:
    """Main sentiment analyzer combining all sources"""
    
    def __init__(self):
        """Initialize the advanced sentiment analyzer"""
        logger.info("🔄 Initializing Advanced Sentiment Analyzer...")
        
        # Initialize individual analyzers
        self.twitter_analyzer = TwitterSentimentAnalyzer()
        self.reddit_analyzer = RedditSentimentAnalyzer()
        self.news_analyzer = NewsSentimentAnalyzer()
        self.fear_greed_analyzer = FearGreedAnalyzer()
        
        # Sentiment weights for different sources
        self.source_weights = {
            SentimentSource.TWITTER: 0.25,
            SentimentSource.REDDIT: 0.20,
            SentimentSource.NEWS: 0.30,
            SentimentSource.FEAR_GREED: 0.15,
            SentimentSource.ON_CHAIN: 0.10
        }
        
        logger.info("✅ Advanced Sentiment Analyzer initialized")
    
    def analyze_comprehensive_sentiment(self, symbol: str) -> ComprehensiveSentiment:
        """Analyze comprehensive sentiment from all sources"""
        logger.info(f"📊 Analyzing comprehensive sentiment for {symbol}")
        
        try:
            # Collect sentiment from all sources
            sentiments = {}
            
            # Twitter sentiment
            twitter_sentiment = self.twitter_analyzer.analyze_twitter_sentiment(symbol)
            sentiments[SentimentSource.TWITTER] = twitter_sentiment
            
            # Reddit sentiment
            reddit_sentiment = self.reddit_analyzer.analyze_reddit_sentiment(symbol)
            sentiments[SentimentSource.REDDIT] = reddit_sentiment
            
            # News sentiment
            news_sentiment = self.news_analyzer.analyze_news_sentiment(symbol)
            sentiments[SentimentSource.NEWS] = news_sentiment
            
            # Fear & Greed Index (market-wide)
            fear_greed_sentiment = self.fear_greed_analyzer.get_fear_greed_index()
            sentiments[SentimentSource.FEAR_GREED] = fear_greed_sentiment
            
            # Calculate weighted overall sentiment
            overall_sentiment = self._calculate_weighted_sentiment(sentiments)
            
            # Calculate volume-weighted sentiment
            volume_weighted_sentiment = self._calculate_volume_weighted_sentiment(sentiments)
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(sentiments)
            
            # Identify key drivers
            key_drivers = self._identify_key_drivers(sentiments)
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(sentiments)
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(sentiments)
            
            # Create sentiment breakdown
            sentiment_breakdown = {
                source: sentiment.sentiment_score 
                for source, sentiment in sentiments.items()
            }
            
            result = ComprehensiveSentiment(
                symbol=symbol,
                overall_sentiment=overall_sentiment,
                confidence=confidence,
                sentiment_breakdown=sentiment_breakdown,
                volume_weighted_sentiment=volume_weighted_sentiment,
                trend_direction=trend_direction,
                key_drivers=key_drivers,
                risk_level=risk_level,
                timestamp=datetime.now()
            )
            
            logger.info(f"✅ Sentiment analysis completed for {symbol}")
            logger.info(f"   Overall Sentiment: {overall_sentiment:.3f}")
            logger.info(f"   Confidence: {confidence:.3f}")
            logger.info(f"   Trend: {trend_direction}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive sentiment analysis for {symbol}: {e}")
            
            # Return neutral sentiment on error
            return ComprehensiveSentiment(
                symbol=symbol,
                overall_sentiment=0.0,
                confidence=0.0,
                sentiment_breakdown={},
                volume_weighted_sentiment=0.0,
                trend_direction="neutral",
                key_drivers=[],
                risk_level="medium",
                timestamp=datetime.now()
            )
    
    def _calculate_weighted_sentiment(self, sentiments: Dict[SentimentSource, SentimentData]) -> float:
        """Calculate weighted overall sentiment"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for source, sentiment_data in sentiments.items():
            weight = self.source_weights.get(source, 0.1)
            confidence_weight = sentiment_data.confidence
            
            # Adjust weight by confidence
            adjusted_weight = weight * confidence_weight
            
            weighted_sum += sentiment_data.sentiment_score * adjusted_weight
            total_weight += adjusted_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_volume_weighted_sentiment(self, sentiments: Dict[SentimentSource, SentimentData]) -> float:
        """Calculate volume-weighted sentiment"""
        volume_weighted_sum = 0.0
        total_volume = 0
        
        for sentiment_data in sentiments.values():
            if sentiment_data.volume > 0:
                volume_weighted_sum += sentiment_data.sentiment_score * sentiment_data.volume
                total_volume += sentiment_data.volume
        
        return volume_weighted_sum / total_volume if total_volume > 0 else 0.0
    
    def _determine_trend_direction(self, sentiments: Dict[SentimentSource, SentimentData]) -> str:
        """Determine overall trend direction"""
        overall_sentiment = self._calculate_weighted_sentiment(sentiments)
        
        if overall_sentiment > 0.3:
            return "bullish"
        elif overall_sentiment < -0.3:
            return "bearish"
        else:
            return "neutral"
    
    def _identify_key_drivers(self, sentiments: Dict[SentimentSource, SentimentData]) -> List[str]:
        """Identify key sentiment drivers"""
        drivers = []
        
        for source, sentiment_data in sentiments.items():
            if abs(sentiment_data.sentiment_score) > 0.5 and sentiment_data.confidence > 0.5:
                direction = "positive" if sentiment_data.sentiment_score > 0 else "negative"
                drivers.append(f"{source.value}_{direction}")
        
        return drivers
    
    def _calculate_risk_level(self, sentiments: Dict[SentimentSource, SentimentData]) -> str:
        """Calculate overall risk level"""
        # Calculate sentiment volatility
        sentiment_scores = [s.sentiment_score for s in sentiments.values()]
        sentiment_std = np.std(sentiment_scores) if sentiment_scores else 0
        
        # Calculate average confidence
        avg_confidence = np.mean([s.confidence for s in sentiments.values()]) if sentiments else 0
        
        # Determine risk level
        if sentiment_std > 0.5 or avg_confidence < 0.3:
            return "high"
        elif sentiment_std > 0.3 or avg_confidence < 0.6:
            return "medium"
        else:
            return "low"
    
    def _calculate_overall_confidence(self, sentiments: Dict[SentimentSource, SentimentData]) -> float:
        """Calculate overall confidence score"""
        if not sentiments:
            return 0.0
        
        # Weight confidence by source importance and data volume
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for source, sentiment_data in sentiments.items():
            source_weight = self.source_weights.get(source, 0.1)
            volume_factor = min(sentiment_data.volume / 10, 1.0)  # Cap at 1.0
            
            weight = source_weight * (0.5 + 0.5 * volume_factor)
            weighted_confidence += sentiment_data.confidence * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def create_sentiment_dashboard(self) -> dash.Dash:
        """Create sentiment analysis dashboard"""
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.CYBORG]
        )
        
        app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("🧠 Advanced Sentiment Analyzer", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(id="symbol-input", placeholder="Enter crypto symbol (e.g., BTC)", value="BTC"),
                        dbc.Button("Analyze", id="analyze-btn", color="primary")
                    ])
                ], width=6),
                dbc.Col([
                    html.Div(id="last-update")
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Overall Sentiment", className="card-title"),
                            html.Div(id="overall-sentiment")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Trend Direction", className="card-title"),
                            html.Div(id="trend-direction")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Risk Level", className="card-title"),
                            html.Div(id="risk-level")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="sentiment-breakdown-chart")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="sentiment-timeline-chart")
                ], width=6)
            ]),
            
            dcc.Interval(
                id='sentiment-interval',
                interval=60000,  # Update every minute
                n_intervals=0
            )
        ], fluid=True)
        
        @app.callback(
            [Output("overall-sentiment", "children"),
             Output("trend-direction", "children"),
             Output("risk-level", "children"),
             Output("sentiment-breakdown-chart", "figure"),
             Output("last-update", "children")],
            [Input("analyze-btn", "n_clicks"),
             Input("sentiment-interval", "n_intervals")],
            [State("symbol-input", "value")]
        )
        def update_sentiment_analysis(n_clicks, n_intervals, symbol):
            if not symbol:
                symbol = "BTC"
            
            # Analyze sentiment
            sentiment_result = self.analyze_comprehensive_sentiment(symbol.upper())
            
            # Overall sentiment display
            sentiment_color = "success" if sentiment_result.overall_sentiment > 0 else "danger" if sentiment_result.overall_sentiment < 0 else "warning"
            overall_sentiment = dbc.Alert([
                html.H4(f"{sentiment_result.overall_sentiment:.3f}"),
                html.P(f"Confidence: {sentiment_result.confidence:.1%}")
            ], color=sentiment_color)
            
            # Trend direction
            trend_colors = {"bullish": "success", "bearish": "danger", "neutral": "warning"}
            trend_color = trend_colors.get(sentiment_result.trend_direction, "secondary")
            trend_direction = dbc.Alert([
                html.H4(sentiment_result.trend_direction.title()),
                html.P(f"Key Drivers: {len(sentiment_result.key_drivers)}")
            ], color=trend_color)
            
            # Risk level
            risk_colors = {"low": "success", "medium": "warning", "high": "danger"}
            risk_color = risk_colors.get(sentiment_result.risk_level, "secondary")
            risk_level = dbc.Alert([
                html.H4(sentiment_result.risk_level.title()),
                html.P("Risk Assessment")
            ], color=risk_color)
            
            # Sentiment breakdown chart
            breakdown_fig = self._create_sentiment_breakdown_chart(sentiment_result)
            
            # Last update
            last_update = html.P(f"Last updated: {sentiment_result.timestamp.strftime('%H:%M:%S')}")
            
            return overall_sentiment, trend_direction, risk_level, breakdown_fig, last_update
        
        return app
    
    def _create_sentiment_breakdown_chart(self, sentiment_result: ComprehensiveSentiment) -> go.Figure:
        """Create sentiment breakdown chart"""
        sources = list(sentiment_result.sentiment_breakdown.keys())
        values = list(sentiment_result.sentiment_breakdown.values())
        
        colors = ['green' if v > 0 else 'red' if v < 0 else 'gray' for v in values]
        
        fig = go.Figure(data=[
            go.Bar(
                x=[s.value for s in sources],
                y=values,
                marker_color=colors,
                text=[f"{v:.3f}" for v in values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Sentiment Breakdown by Source",
            xaxis_title="Source",
            yaxis_title="Sentiment Score",
            yaxis=dict(range=[-1, 1]),
            template="plotly_dark"
        )
        
        return fig

def main():
    """Example usage"""
    analyzer = AdvancedSentimentAnalyzer()
    
    # Test sentiment analysis
    symbols = ['BTC', 'ETH', 'ADA']
    
    for symbol in symbols:
        print(f"\n🔍 Analyzing sentiment for {symbol}:")
        result = analyzer.analyze_comprehensive_sentiment(symbol)
        
        print(f"Overall Sentiment: {result.overall_sentiment:.3f}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Trend Direction: {result.trend_direction}")
        print(f"Risk Level: {result.risk_level}")
        print(f"Key Drivers: {result.key_drivers}")
        
        print("\nSentiment Breakdown:")
        for source, score in result.sentiment_breakdown.items():
            print(f"  {source.value}: {score:.3f}")

if __name__ == "__main__":
    main() 