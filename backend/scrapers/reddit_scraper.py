"""
Reddit scraper for fantasy football sentiment analysis.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import re
import os

logger = logging.getLogger(__name__)

class RedditScraper:
    """
    Reddit scraper for fantasy football sentiment and discussion analysis.
    """
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://oauth.reddit.com"
        self.session = None
        self.access_token = None
        
        self.headers = {
            'User-Agent': 'fantasy-football-analyzer/1.0'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        await self._authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _authenticate(self):
        """Authenticate with Reddit API."""
        if not self.client_id or not self.client_secret:
            logger.warning("Reddit credentials not provided, using public access")
            return
        
        try:
            auth_data = {
                'grant_type': 'client_credentials'
            }
            
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            
            async with self.session.post(
                'https://www.reddit.com/api/v1/access_token',
                data=auth_data,
                auth=auth
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get('access_token')
                    
                    # Update headers for authenticated requests
                    self.headers['Authorization'] = f'Bearer {self.access_token}'
                    
        except Exception as e:
            logger.error(f"Reddit authentication failed: {str(e)}")
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make request to Reddit API."""
        try:
            if self.access_token:
                url = f"{self.oauth_url}/{endpoint}"
            else:
                url = f"{self.base_url}/{endpoint}.json"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Reddit API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Reddit request failed for {endpoint}: {str(e)}")
            return None
    
    async def get_fantasyfootball_posts(self, sort: str = "hot", limit: int = 25, 
                                      time_filter: str = "day") -> List[Dict[str, Any]]:
        """Get posts from r/fantasyfootball."""
        try:
            params = {
                'limit': limit,
                't': time_filter
            }
            
            endpoint = f"r/fantasyfootball/{sort}"
            data = await self._make_request(endpoint, params)
            
            if not data:
                return []
            
            posts = []
            
            # Handle Reddit's nested data structure
            if 'data' in data and 'children' in data['data']:
                for post_data in data['data']['children']:
                    post = post_data.get('data', {})
                    
                    formatted_post = {
                        'id': post.get('id'),
                        'title': post.get('title'),
                        'author': post.get('author'),
                        'score': post.get('score', 0),
                        'upvote_ratio': post.get('upvote_ratio', 0.5),
                        'num_comments': post.get('num_comments', 0),
                        'created_utc': post.get('created_utc'),
                        'selftext': post.get('selftext', ''),
                        'url': post.get('url'),
                        'permalink': post.get('permalink'),
                        'flair_text': post.get('link_flair_text'),
                        'subreddit': post.get('subreddit')
                    }
                    
                    # Extract player mentions
                    formatted_post['player_mentions'] = self._extract_player_mentions(
                        formatted_post['title'] + ' ' + formatted_post['selftext']
                    )
                    
                    # Calculate sentiment score
                    formatted_post['sentiment_score'] = self._calculate_sentiment(
                        formatted_post['title'] + ' ' + formatted_post['selftext']
                    )
                    
                    posts.append(formatted_post)
            
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get fantasyfootball posts: {str(e)}")
            return []
    
    async def get_post_comments(self, post_id: str, sort: str = "top", limit: int = 100) -> List[Dict[str, Any]]:
        """Get comments for a specific post."""
        try:
            endpoint = f"r/fantasyfootball/comments/{post_id}"
            params = {
                'sort': sort,
                'limit': limit
            }
            
            data = await self._make_request(endpoint, params)
            
            if not data or len(data) < 2:
                return []
            
            comments = []
            comments_data = data[1].get('data', {}).get('children', [])
            
            for comment_data in comments_data:
                comment = comment_data.get('data', {})
                
                if comment.get('body') and comment.get('body') != '[deleted]':
                    formatted_comment = {
                        'id': comment.get('id'),
                        'author': comment.get('author'),
                        'body': comment.get('body'),
                        'score': comment.get('score', 0),
                        'created_utc': comment.get('created_utc'),
                        'parent_id': comment.get('parent_id'),
                        'player_mentions': self._extract_player_mentions(comment.get('body', '')),
                        'sentiment_score': self._calculate_sentiment(comment.get('body', ''))
                    }
                    
                    comments.append(formatted_comment)
            
            return comments
            
        except Exception as e:
            logger.error(f"Failed to get post comments: {str(e)}")
            return []
    
    def _extract_player_mentions(self, text: str) -> List[str]:
        """Extract player name mentions from text."""
        try:
            # Common fantasy football player name patterns
            player_patterns = [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
                r'\b[A-Z]\.?\s*[A-Z][a-z]+\b',     # J. Smith
            ]
            
            mentioned_players = []
            
            for pattern in player_patterns:
                matches = re.findall(pattern, text)
                mentioned_players.extend(matches)
            
            # Filter out common false positives
            false_positives = {
                'Fantasy Football', 'Trade Thread', 'Week Thread', 'Daily Thread',
                'Start Sit', 'Add Drop', 'WDIS Thread', 'Official Thread'
            }
            
            # Remove duplicates and false positives
            clean_players = []
            for player in mentioned_players:
                if player not in false_positives and player not in clean_players:
                    clean_players.append(player)
            
            return clean_players[:10]  # Limit to top 10 mentions
            
        except Exception as e:
            logger.error(f"Failed to extract player mentions: {str(e)}")
            return []
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate basic sentiment score for text."""
        try:
            positive_words = {
                'good', 'great', 'excellent', 'amazing', 'awesome', 'best', 'top',
                'start', 'play', 'must', 'definitely', 'love', 'like', 'solid',
                'strong', 'buy', 'upgrade', 'breakout', 'bounce', 'back'
            }
            
            negative_words = {
                'bad', 'terrible', 'awful', 'worst', 'avoid', 'drop', 'bench',
                'sit', 'sell', 'bust', 'disappointing', 'concerned', 'worried',
                'decline', 'downgrade', 'fade', 'injury', 'hurt', 'questionable'
            }
            
            words = re.findall(r'\b[a-z]+\b', text.lower())
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            total_words = len(words)
            if total_words == 0:
                return 0.5
            
            # Calculate sentiment score (-1 to 1)
            sentiment = (positive_count - negative_count) / max(total_words * 0.1, 1)
            return max(-1, min(1, sentiment))
            
        except Exception as e:
            logger.error(f"Failed to calculate sentiment: {str(e)}")
            return 0.5
    
    async def get_player_sentiment(self, player_name: str, time_filter: str = "day") -> Dict[str, Any]:
        """Get sentiment analysis for a specific player."""
        try:
            # Search for posts mentioning the player
            search_query = f'"{player_name}"'
            params = {
                'q': search_query,
                'restrict_sr': 'true',
                'sort': 'relevance',
                't': time_filter,
                'limit': 50
            }
            
            endpoint = "r/fantasyfootball/search"
            data = await self._make_request(endpoint, params)
            
            if not data:
                return {}
            
            mentions = []
            sentiment_scores = []
            total_score = 0
            total_comments = 0
            
            if 'data' in data and 'children' in data['data']:
                for post_data in data['data']['children']:
                    post = post_data.get('data', {})
                    
                    # Check if player is actually mentioned
                    full_text = post.get('title', '') + ' ' + post.get('selftext', '')
                    if player_name.lower() in full_text.lower():
                        
                        mention = {
                            'post_id': post.get('id'),
                            'title': post.get('title'),
                            'score': post.get('score', 0),
                            'num_comments': post.get('num_comments', 0),
                            'created_utc': post.get('created_utc'),
                            'sentiment': self._calculate_sentiment(full_text)
                        }
                        
                        mentions.append(mention)
                        sentiment_scores.append(mention['sentiment'])
                        total_score += post.get('score', 0)
                        total_comments += post.get('num_comments', 0)
            
            # Calculate overall sentiment
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                sentiment_trend = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
            else:
                avg_sentiment = 0.5
                sentiment_trend = "neutral"
            
            return {
                'player_name': player_name,
                'mentions_found': len(mentions),
                'average_sentiment': avg_sentiment,
                'sentiment_trend': sentiment_trend,
                'total_upvotes': total_score,
                'total_comments': total_comments,
                'recent_mentions': mentions[:10],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get player sentiment for {player_name}: {str(e)}")
            return {}
    
    async def get_trending_discussions(self, limit: int = 25) -> Dict[str, Any]:
        """Get trending fantasy football discussions."""
        try:
            hot_posts = await self.get_fantasyfootball_posts("hot", limit)
            
            # Analyze trending topics
            trending_players = {}
            discussion_themes = {}
            
            for post in hot_posts:
                # Count player mentions
                for player in post.get('player_mentions', []):
                    if player not in trending_players:
                        trending_players[player] = {
                            'mentions': 0,
                            'total_score': 0,
                            'avg_sentiment': 0,
                            'sentiments': []
                        }
                    
                    trending_players[player]['mentions'] += 1
                    trending_players[player]['total_score'] += post.get('score', 0)
                    trending_players[player]['sentiments'].append(post.get('sentiment_score', 0.5))
                
                # Categorize discussion themes
                flair = post.get('flair_text', '').lower()
                title = post.get('title', '').lower()
                
                if any(word in title for word in ['trade', 'deal']):
                    theme = 'trade_discussion'
                elif any(word in title for word in ['start', 'sit', 'wdis']):
                    theme = 'start_sit'
                elif any(word in title for word in ['waiver', 'pickup', 'drop']):
                    theme = 'waiver_wire'
                elif any(word in title for word in ['injury', 'hurt', 'report']):
                    theme = 'injury_news'
                else:
                    theme = 'general_discussion'
                
                if theme not in discussion_themes:
                    discussion_themes[theme] = 0
                discussion_themes[theme] += 1
            
            # Calculate average sentiment for trending players
            for player_data in trending_players.values():
                if player_data['sentiments']:
                    player_data['avg_sentiment'] = sum(player_data['sentiments']) / len(player_data['sentiments'])
            
            # Sort trending players by mentions and score
            sorted_players = sorted(
                trending_players.items(),
                key=lambda x: (x[1]['mentions'], x[1]['total_score']),
                reverse=True
            )
            
            return {
                'trending_players': dict(sorted_players[:20]),
                'discussion_themes': discussion_themes,
                'total_posts_analyzed': len(hot_posts),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get trending discussions: {str(e)}")
            return {}
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()