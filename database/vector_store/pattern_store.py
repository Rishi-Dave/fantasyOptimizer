"""
Pattern Store for the Fantasy Football AI Multi-Agent System.

Specialized storage and retrieval for fantasy football patterns including:
- Player performance patterns
- Matchup trends
- Market sentiment patterns
- Trade value trends
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .vector_manager import VectorManager
from .embeddings import FantasyEmbeddingService

logger = logging.getLogger(__name__)

@dataclass
class PlayerPattern:
    """Represents a player performance pattern."""
    player_name: str
    position: str
    team: str
    pattern_type: str  # "seasonal", "weekly", "matchup", "injury"
    timeframe: str
    metrics: Dict[str, float]
    context: Dict[str, Any]
    confidence: float
    created_at: datetime

@dataclass
class MatchupPattern:
    """Represents a matchup pattern."""
    player_position: str
    opponent_team: str
    defense_rank: int
    game_script: str
    weather_conditions: Optional[str]
    historical_performance: Dict[str, float]
    pattern_strength: float
    created_at: datetime

@dataclass
class MarketPattern:
    """Represents a market sentiment or trade pattern."""
    subject: str  # player name or general topic
    pattern_type: str  # "sentiment", "trade_value", "ownership"
    trend_direction: str  # "increasing", "decreasing", "stable"
    magnitude: float
    timeframe: str
    source: str
    confidence: float
    created_at: datetime

class PatternStore:
    """
    High-level interface for storing and retrieving fantasy football patterns.
    
    Provides specialized methods for different types of patterns while
    using the vector database for similarity search and retrieval.
    """
    
    def __init__(self, vector_manager: VectorManager = None):
        self.vector_manager = vector_manager or VectorManager()
        self.embedding_service = FantasyEmbeddingService()
        self.logger = logging.getLogger(__name__)
    
    async def store_player_pattern(self, pattern: PlayerPattern) -> bool:
        """Store a player performance pattern."""
        try:
            # Create comprehensive pattern data
            pattern_data = {
                "type": "player_pattern",
                "player_name": pattern.player_name,
                "position": pattern.position,
                "team": pattern.team,
                "pattern_type": pattern.pattern_type,
                "timeframe": pattern.timeframe,
                "metrics": pattern.metrics,
                "context": pattern.context,
                "confidence": pattern.confidence,
                "season": datetime.now().year,
                "timestamp": pattern.created_at.isoformat()
            }
            
            # Store in vector database
            success = await self.vector_manager.store_player_pattern(
                player_name=pattern.player_name,
                pattern_data=pattern_data
            )
            
            if success:
                self.logger.info(f"Stored player pattern for {pattern.player_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to store player pattern: {str(e)}")
            return False
    
    async def store_matchup_pattern(self, pattern: MatchupPattern) -> bool:
        """Store a matchup pattern."""
        try:
            # Create matchup analysis content
            analysis_data = {
                "type": "matchup_analysis",
                "analysis": f"{pattern.player_position} vs {pattern.opponent_team} defense (rank {pattern.defense_rank})",
                "game_script": pattern.game_script,
                "weather": pattern.weather_conditions,
                "historical_performance": pattern.historical_performance,
                "pattern_strength": pattern.pattern_strength,
                "source": "pattern_analysis",
                "confidence": pattern.pattern_strength,
                "timestamp": pattern.created_at.isoformat()
            }
            
            # Store in expert analysis collection
            success = await self.vector_manager.store_expert_analysis(analysis_data)
            
            if success:
                self.logger.info(f"Stored matchup pattern: {pattern.player_position} vs {pattern.opponent_team}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to store matchup pattern: {str(e)}")
            return False
    
    async def store_market_pattern(self, pattern: MarketPattern) -> bool:
        """Store a market sentiment or trade pattern."""
        try:
            # Create market analysis content
            analysis_data = {
                "type": "market_analysis",
                "subject": pattern.subject,
                "analysis": f"{pattern.pattern_type} trending {pattern.trend_direction} with magnitude {pattern.magnitude}",
                "trend_direction": pattern.trend_direction,
                "magnitude": pattern.magnitude,
                "timeframe": pattern.timeframe,
                "source": pattern.source,
                "confidence": pattern.confidence,
                "timestamp": pattern.created_at.isoformat()
            }
            
            # Store in expert analysis collection
            success = await self.vector_manager.store_expert_analysis(analysis_data)
            
            if success:
                self.logger.info(f"Stored market pattern for {pattern.subject}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to store market pattern: {str(e)}")
            return False
    
    async def find_similar_player_patterns(self, player_name: str, position: str = None, 
                                         pattern_type: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Find players with similar performance patterns."""
        try:
            # Build query
            query_parts = [f"player performance patterns for {player_name}"]
            
            if position:
                query_parts.append(f"position {position}")
            
            if pattern_type:
                query_parts.append(f"pattern type {pattern_type}")
            
            query = " ".join(query_parts)
            
            # Build metadata filter
            metadata_filter = {}
            if position:
                metadata_filter["position"] = position
            if pattern_type:
                metadata_filter["pattern_type"] = pattern_type
            
            # Search for similar patterns
            results = await self.vector_manager.find_similar_patterns(
                query=query,
                collection_name="player_patterns",
                limit=limit,
                metadata_filter=metadata_filter if metadata_filter else None
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to find similar player patterns: {str(e)}")
            return []
    
    async def find_matchup_patterns(self, position: str, opponent_team: str = None, 
                                   game_script: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Find historical matchup patterns."""
        try:
            # Build query
            query_parts = [f"{position} matchup patterns"]
            
            if opponent_team:
                query_parts.append(f"vs {opponent_team}")
            
            if game_script:
                query_parts.append(f"game script {game_script}")
            
            query = " ".join(query_parts)
            
            # Search in expert analysis collection for matchup data
            results = await self.vector_manager.find_similar_patterns(
                query=query,
                collection_name="expert_analysis",
                limit=limit
            )
            
            # Filter for matchup-related results
            matchup_results = [
                result for result in results 
                if result["metadata"].get("type") == "matchup_analysis"
            ]
            
            return matchup_results
            
        except Exception as e:
            self.logger.error(f"Failed to find matchup patterns: {str(e)}")
            return []
    
    async def find_market_trends(self, subject: str, pattern_type: str = None, 
                                timeframe: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Find market sentiment and trade trends."""
        try:
            # Build query
            query_parts = [f"market trends for {subject}"]
            
            if pattern_type:
                query_parts.append(f"{pattern_type} patterns")
            
            if timeframe:
                query_parts.append(f"timeframe {timeframe}")
            
            query = " ".join(query_parts)
            
            # Search in expert analysis collection for market data
            results = await self.vector_manager.find_similar_patterns(
                query=query,
                collection_name="expert_analysis",
                limit=limit
            )
            
            # Filter for market-related results
            market_results = [
                result for result in results 
                if result["metadata"].get("type") == "market_analysis"
            ]
            
            return market_results
            
        except Exception as e:
            self.logger.error(f"Failed to find market trends: {str(e)}")
            return []
    
    async def get_player_context(self, player_name: str, context_type: str = "all") -> Dict[str, Any]:
        """Get comprehensive context for a player."""
        try:
            context = {
                "player_name": player_name,
                "patterns": [],
                "matchups": [],
                "market_sentiment": [],
                "comparisons": []
            }
            
            # Get player patterns
            if context_type in ["all", "patterns"]:
                patterns = await self.find_similar_player_patterns(player_name, limit=10)
                context["patterns"] = patterns
            
            # Get matchup history
            if context_type in ["all", "matchups"]:
                # We need to infer position - this could be improved with player database
                matchups = await self.find_matchup_patterns("", limit=5)  # Generic search
                context["matchups"] = matchups
            
            # Get market sentiment
            if context_type in ["all", "market"]:
                market_data = await self.find_market_trends(player_name, limit=5)
                context["market_sentiment"] = market_data
            
            # Get player comparisons
            if context_type in ["all", "comparisons"]:
                comparisons = await self.vector_manager.find_player_comparisons(player_name, limit=5)
                context["comparisons"] = comparisons
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get player context: {str(e)}")
            return {"player_name": player_name, "error": str(e)}
    
    async def analyze_pattern_trends(self, pattern_type: str, timeframe_days: int = 30) -> Dict[str, Any]:
        """Analyze trends in stored patterns over time."""
        try:
            # This would require more sophisticated querying
            # For now, return a summary structure
            
            trends = {
                "pattern_type": pattern_type,
                "timeframe_days": timeframe_days,
                "analysis_timestamp": datetime.now().isoformat(),
                "trends": {
                    "emerging_players": [],
                    "declining_players": [],
                    "stable_patterns": [],
                    "volatility_metrics": {}
                },
                "recommendations": []
            }
            
            # Get recent patterns (this is simplified)
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)
            
            # In a real implementation, we would:
            # 1. Query patterns by timestamp
            # 2. Analyze trend directions
            # 3. Identify statistical significance
            # 4. Generate actionable insights
            
            self.logger.info(f"Analyzed {pattern_type} trends over {timeframe_days} days")
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Failed to analyze pattern trends: {str(e)}")
            return {"error": str(e)}
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored patterns."""
        try:
            # Get vector database stats
            db_stats = self.vector_manager.get_stats()
            
            # Calculate pattern-specific statistics
            pattern_stats = {
                "database_status": db_stats["status"],
                "collections": db_stats.get("collections", {}),
                "pattern_summary": {
                    "player_patterns": db_stats.get("collections", {}).get("player_patterns", {}).get("document_count", 0),
                    "expert_analysis": db_stats.get("collections", {}).get("expert_analysis", {}).get("document_count", 0),
                    "matchup_history": db_stats.get("collections", {}).get("matchup_history", {}).get("document_count", 0),
                    "trade_patterns": db_stats.get("collections", {}).get("trade_patterns", {}).get("document_count", 0),
                    "social_sentiment": db_stats.get("collections", {}).get("social_sentiment", {}).get("document_count", 0)
                },
                "embedding_model": self.embedding_service.get_model_info(),
                "last_updated": datetime.now().isoformat()
            }
            
            return pattern_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get pattern statistics: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup_old_patterns(self, days_to_keep: int = 30) -> int:
        """Clean up old patterns to manage storage."""
        try:
            deleted_count = await self.vector_manager.cleanup_old_data(days_to_keep)
            self.logger.info(f"Cleaned up {deleted_count} old patterns")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Failed to cleanup old patterns: {str(e)}")
            return 0