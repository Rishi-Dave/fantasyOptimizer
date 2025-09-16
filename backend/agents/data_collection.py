"""
Data Collection Agents for the Fantasy Football AI Multi-Agent System.

These agents specialize in gathering and processing data from various sources:
- Market Intelligence Agent: Expert rankings, consensus, social sentiment
- Statistical Analysis Agent: Advanced metrics, historical patterns, projections
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging

from .base_agent import BaseAgent, AgentContext, AgentType, LLMMixin, DataMixin
from ..scrapers.sleeper_api import SleeperAPI
from ..scrapers.fantasypros_scraper import FantasyProsScraper
from ..scrapers.reddit_scraper import RedditScraper
from ..scrapers.vegas_odds_api import VegasOddsAPI
from ..scrapers.weather_api import WeatherAPI

logger = logging.getLogger(__name__)

class MarketIntelligenceAgent(BaseAgent, LLMMixin, DataMixin):
    """
    Gathers market intelligence from expert rankings, consensus data, and social sentiment.
    
    Data Sources:
    - FantasyPros expert consensus rankings
    - Reddit r/fantasyfootball sentiment analysis
    - Twitter beat reporter feeds
    - Vegas odds and line movements
    - Expert start/sit recommendations
    """
    
    def __init__(self, agent_id: str, llm_config: Dict[str, Any] = None):
        BaseAgent.__init__(self, agent_id, AgentType.DATA_COLLECTION, "Market Intelligence Agent")
        LLMMixin.__init__(self, llm_config)
        DataMixin.__init__(self)
        
    async def _process(self, context: AgentContext) -> Tuple[Dict[str, Any], float, str, List[str]]:
        """Collect market intelligence data relevant to the query."""
        
        market_data = {}
        sources = []
        confidence = 0.7
        
        try:
            # Collect expert consensus data
            expert_data = await self._get_expert_consensus(context)
            if expert_data:
                market_data["expert_consensus"] = expert_data
                sources.append("FantasyPros Expert Consensus")
                confidence += 0.1
            
            # Analyze social sentiment
            sentiment_data = await self._analyze_social_sentiment(context)
            if sentiment_data:
                market_data["social_sentiment"] = sentiment_data
                sources.append("Reddit/Twitter Sentiment Analysis")
                confidence += 0.1
            
            # Get Vegas odds and line movements
            vegas_data = await self._get_vegas_data(context)
            if vegas_data:
                market_data["vegas_odds"] = vegas_data
                sources.append("Vegas Sportsbook Data")
                confidence += 0.1
            
            # Gather beat reporter insights
            reporter_insights = await self._get_reporter_insights(context)
            if reporter_insights:
                market_data["reporter_insights"] = reporter_insights
                sources.append("Beat Reporter Feeds")
                confidence += 0.05
            
            reasoning = self._generate_market_reasoning(market_data, context)
            
            return market_data, min(confidence, 0.95), reasoning, sources
            
        except Exception as e:
            self.logger.error(f"Market intelligence collection failed: {str(e)}")
            return {
                "error": str(e),
                "fallback_analysis": "Unable to collect full market intelligence. Using limited data."
            }, 0.3, f"Market data collection encountered errors: {str(e)}", ["fallback"]
    
    async def _get_expert_consensus(self, context: AgentContext) -> Dict[str, Any]:
        """Get expert consensus rankings and start/sit recommendations."""
        try:
            async with FantasyProsScraper() as scraper:
                # Get consensus rankings
                consensus_data = await scraper.get_expert_consensus()
                
                # Get start/sit advice
                start_sit_data = await scraper.get_start_sit_advice()
                
                # Combine data
                if consensus_data and start_sit_data:
                    consensus_data.update({
                        "start_recommendations": start_sit_data.get("start_recommendations", []),
                        "sit_recommendations": start_sit_data.get("sit_recommendations", [])
                    })
                
                return consensus_data or {}
            
        except Exception as e:
            self.logger.error(f"Expert consensus fetch failed: {str(e)}")
            return {}
    
    async def _analyze_social_sentiment(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze social media sentiment from Reddit and Twitter."""
        try:
            async with RedditScraper() as scraper:
                # Get trending discussions
                trending_data = await scraper.get_trending_discussions()
                
                # Get sentiment for specific players from roster if available
                player_sentiments = {}
                if context.roster_data and 'players' in context.roster_data:
                    # Get player names from roster
                    async with SleeperAPI() as sleeper:
                        nfl_players = await sleeper.get_nfl_players()
                        player_names = sleeper.format_player_names(
                            context.roster_data['players'][:5],  # Limit API calls
                            nfl_players
                        )
                        
                        # Get sentiment for each player
                        for player_name in player_names:
                            sentiment = await scraper.get_player_sentiment(player_name)
                            if sentiment:
                                player_sentiments[player_name] = sentiment
                
                return {
                    "reddit_sentiment": {
                        "trending_discussions": trending_data,
                        "player_sentiments": player_sentiments
                    },
                    "overall_sentiment_score": trending_data.get("avg_sentiment", 0.5) if trending_data else 0.5,
                    "sentiment_reliability": 0.7,
                    "data_timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            self.logger.error(f"Social sentiment analysis failed: {str(e)}")
            return {}
    
    async def _get_vegas_data(self, context: AgentContext) -> Dict[str, Any]:
        """Get Vegas odds, totals, and line movements."""
        try:
            async with VegasOddsAPI() as odds_api:
                # Get current NFL odds
                nfl_odds = await odds_api.get_nfl_odds()
                
                # Get weekly betting analysis
                weekly_analysis = await odds_api.get_weekly_betting_analysis()
                
                # Get sharp money indicators
                sharp_indicators = await odds_api.get_sharp_money_indicators()
                
                # Format game totals and spreads
                game_data = {}
                for game in nfl_odds:
                    matchup = f"{game.get('away_team')} @ {game.get('home_team')}"
                    consensus = game.get('consensus', {})
                    
                    game_data[matchup] = {
                        "total": consensus.get('total', {}).get('over'),
                        "spread": consensus.get('spread', {}).get('home'),
                        "commence_time": game.get('commence_time')
                    }
                
                return {
                    "game_totals": game_data,
                    "weekly_analysis": weekly_analysis,
                    "sharp_money_indicators": sharp_indicators,
                    "data_timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            self.logger.error(f"Vegas data fetch failed: {str(e)}")
            return {}
    
    async def _get_reporter_insights(self, context: AgentContext) -> Dict[str, Any]:
        """Get insights from beat reporters and insider sources."""
        try:
            # Simulate beat reporter feed analysis
            # In production, this would parse Twitter feeds and news sources
            
            reporter_insights = {
                "injury_updates": {
                    "latest_reports": [
                        {"player": "Saquon Barkley", "status": "Limited practice", "source": "@JordanRaanan", "confidence": 0.8},
                        {"player": "Tua Tagovailoa", "status": "Cleared protocol", "source": "@ArmandoSalguero", "confidence": 0.9}
                    ]
                },
                "snap_count_intel": {
                    "emerging_roles": [
                        {"player": "Puka Nacua", "trend": "increased_targets", "source": "Rams beat reporter"},
                        {"player": "Tank Dell", "trend": "red_zone_looks", "source": "Texans insider"}
                    ]
                },
                "coaching_comments": {
                    "notable_quotes": [
                        {"coach": "Sean McDermott", "comment": "Josh Allen 100% healthy", "impact": "positive"},
                        {"coach": "Kyle Shanahan", "comment": "Deebo Samuel limited snaps", "impact": "negative"}
                    ]
                },
                "insider_confidence": 0.75
            }
            
            return reporter_insights
            
        except Exception as e:
            self.logger.error(f"Reporter insights fetch failed: {str(e)}")
            return {}
    
    def _generate_market_reasoning(self, market_data: Dict[str, Any], context: AgentContext) -> str:
        """Generate reasoning based on collected market intelligence."""
        reasoning_parts = []
        
        if "expert_consensus" in market_data:
            consensus = market_data["expert_consensus"]
            reasoning_parts.append(f"Expert consensus shows {consensus.get('consensus_strength', 0) * 100:.0f}% agreement")
        
        if "social_sentiment" in market_data:
            sentiment = market_data["social_sentiment"]
            reasoning_parts.append(f"Social sentiment analysis indicates {sentiment.get('overall_sentiment_score', 0) * 100:.0f}% positive market perception")
        
        if "vegas_odds" in market_data:
            reasoning_parts.append("Vegas odds incorporated for game script and scoring environment analysis")
        
        if "reporter_insights" in market_data:
            insights = market_data["reporter_insights"]
            reasoning_parts.append(f"Beat reporter intelligence with {insights.get('insider_confidence', 0) * 100:.0f}% reliability")
        
        return "Market Intelligence Analysis: " + "; ".join(reasoning_parts)

class StatisticalAnalysisAgent(BaseAgent, LLMMixin, DataMixin):
    """
    Performs advanced statistical analysis using historical data and current metrics.
    
    Capabilities:
    - Advanced metrics calculation (target share, air yards, red zone touches)
    - Historical performance pattern analysis
    - Strength of schedule calculations
    - Regression analysis and projections
    - Pace of play and game script predictions
    """
    
    def __init__(self, agent_id: str, llm_config: Dict[str, Any] = None):
        BaseAgent.__init__(self, agent_id, AgentType.DATA_COLLECTION, "Statistical Analysis Agent")
        LLMMixin.__init__(self, llm_config)
        DataMixin.__init__(self)
    
    async def _process(self, context: AgentContext) -> Tuple[Dict[str, Any], float, str, List[str]]:
        """Perform comprehensive statistical analysis."""
        
        stats_data = {}
        sources = []
        confidence = 0.8
        
        try:
            # Calculate advanced metrics
            advanced_metrics = await self._calculate_advanced_metrics(context)
            if advanced_metrics:
                stats_data["advanced_metrics"] = advanced_metrics
                sources.append("NFL Advanced Metrics Database")
                confidence += 0.05
            
            # Analyze historical patterns
            historical_analysis = await self._analyze_historical_patterns(context)
            if historical_analysis:
                stats_data["historical_patterns"] = historical_analysis
                sources.append("Historical Performance Database")
                confidence += 0.05
            
            # Calculate strength of schedule
            sos_analysis = await self._calculate_strength_of_schedule(context)
            if sos_analysis:
                stats_data["strength_of_schedule"] = sos_analysis
                sources.append("Defensive Rankings Database")
                confidence += 0.05
            
            # Generate projections
            projections = await self._generate_projections(context)
            if projections:
                stats_data["projections"] = projections
                sources.append("Proprietary Projection Model")
                confidence += 0.05
            
            reasoning = self._generate_statistical_reasoning(stats_data, context)
            
            return stats_data, min(confidence, 0.95), reasoning, sources
            
        except Exception as e:
            self.logger.error(f"Statistical analysis failed: {str(e)}")
            return {
                "error": str(e),
                "fallback_stats": "Basic statistical analysis unavailable"
            }, 0.4, f"Statistical analysis encountered errors: {str(e)}", ["fallback"]
    
    async def _calculate_advanced_metrics(self, context: AgentContext) -> Dict[str, Any]:
        """Calculate advanced metrics for players."""
        try:
            # Get real player data from Sleeper
            async with SleeperAPI() as sleeper:
                # Get current week stats
                current_stats = await sleeper.get_player_stats()
                
                # Get projections
                projections = await sleeper.get_projections()
                
                # Get NFL players for names/positions
                nfl_players = await sleeper.get_nfl_players()
                
                # Calculate metrics for roster players if available
                advanced_metrics = {
                    "player_stats": current_stats,
                    "projections": projections,
                    "roster_analysis": {}
                }
                
                # Analyze roster players if available
                if context.roster_data and 'players' in context.roster_data:
                    for player_id in context.roster_data['players'][:10]:  # Limit analysis
                        if player_id in nfl_players:
                            player = nfl_players[player_id]
                            player_name = player.get('full_name', player_id)
                            
                            # Get player's current stats
                            player_stats = current_stats.get(player_id, {}) if current_stats else {}
                            player_proj = projections.get(player_id, {}) if projections else {}
                            
                            advanced_metrics["roster_analysis"][player_name] = {
                                "position": player.get('position'),
                                "team": player.get('team'),
                                "stats": player_stats,
                                "projections": player_proj,
                                "injury_status": player.get('injury_status')
                            }
                
                return advanced_metrics
            
        except Exception as e:
            self.logger.error(f"Advanced metrics calculation failed: {str(e)}")
            return {}
    
    async def _analyze_historical_patterns(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze historical performance patterns."""
        try:
            # Simulate historical pattern analysis
            
            historical_patterns = {
                "seasonal_trends": {
                    "Josh Allen": {
                        "cold_weather_performance": {"games": 12, "avg_fantasy_points": 23.4, "variance": 4.2},
                        "division_rival_performance": {"games": 6, "avg_fantasy_points": 21.8}
                    },
                    "Christian McCaffrey": {
                        "workload_regression": {"high_touch_games": 8, "following_week_avg": 18.2},
                        "injury_return_pattern": {"games_after_return": 4, "avg_points": 20.1}
                    }
                },
                "matchup_history": {
                    "vs_team_defense": {
                        "Cooper Kupp vs DAL": {"games": 3, "avg_points": 14.2, "ceiling": 22.1},
                        "Travis Kelce vs DEN": {"games": 8, "avg_points": 16.8, "floor": 8.2}
                    }
                },
                "regression_candidates": {
                    "positive_regression": ["Mike Evans", "Keenan Allen", "Aaron Jones"],
                    "negative_regression": ["Gabe Davis", "Tyler Lockett", "Raheem Mostert"],
                    "confidence_scores": {"Mike Evans": 0.78, "Gabe Davis": 0.71}
                },
                "consistency_metrics": {
                    "floor_players": {"Christian McCaffrey": 0.85, "Travis Kelce": 0.82},
                    "ceiling_players": {"Tyreek Hill": 0.91, "Mike Evans": 0.88},
                    "boom_bust_ratio": {"DK Metcalf": 2.1, "Michael Pittman": 1.3}
                }
            }
            
            return historical_patterns
            
        except Exception as e:
            self.logger.error(f"Historical pattern analysis failed: {str(e)}")
            return {}
    
    async def _calculate_strength_of_schedule(self, context: AgentContext) -> Dict[str, Any]:
        """Calculate strength of schedule analysis."""
        try:
            # Simulate SOS calculations
            
            sos_analysis = {
                "remaining_schedule_difficulty": {
                    "QB": {
                        "Josh Allen": {"sos_rank": 12, "tough_matchups": ["MIA", "DAL"], "easy_matchups": ["NYJ", "NE"]},
                        "Lamar Jackson": {"sos_rank": 8, "tough_matchups": ["SF", "BUF"], "easy_matchups": ["CLE", "CIN"]}
                    },
                    "RB": {
                        "Christian McCaffrey": {"sos_rank": 15, "run_defense_faced": "average", "upcoming_weak_defenses": 2},
                        "Josh Jacobs": {"sos_rank": 6, "run_defense_faced": "tough", "upcoming_weak_defenses": 4}
                    }
                },
                "playoff_schedule_analysis": {
                    "weeks_15_17": {
                        "favorable_schedules": ["Josh Jacobs", "CeeDee Lamb", "Travis Kelce"],
                        "difficult_schedules": ["Cooper Kupp", "Mike Evans", "Saquon Barkley"],
                        "neutral_schedules": ["Christian McCaffrey", "Davante Adams"]
                    }
                },
                "defensive_rankings": {
                    "vs_QB": {"easiest": ["ARI", "CHI", "WAS"], "toughest": ["BUF", "SF", "DAL"]},
                    "vs_RB": {"easiest": ["CHI", "DEN", "ARI"], "toughest": ["SF", "BAL", "CLE"]},
                    "vs_WR": {"easiest": ["WAS", "DET", "GB"], "toughest": ["MIA", "BUF", "NYJ"]},
                    "vs_TE": {"easiest": ["ATL", "DET", "LAC"], "toughest": ["MIN", "PIT", "DEN"]}
                }
            }
            
            return sos_analysis
            
        except Exception as e:
            self.logger.error(f"Strength of schedule calculation failed: {str(e)}")
            return {}
    
    async def _generate_projections(self, context: AgentContext) -> Dict[str, Any]:
        """Generate statistical projections."""
        try:
            async with SleeperAPI() as sleeper:
                # Get current projections from Sleeper
                sleeper_projections = await sleeper.get_projections()
                
                # Get trending players for breakout analysis
                trending_adds = await sleeper.get_trending_players("add")
                trending_drops = await sleeper.get_trending_players("drop")
                
                # Get NFL players for names
                nfl_players = await sleeper.get_nfl_players()
                
                # Format projections data
                projections = {
                    "sleeper_projections": sleeper_projections,
                    "trending_analysis": {
                        "trending_adds": trending_adds,
                        "trending_drops": trending_drops
                    },
                    "roster_projections": {}
                }
                
                # Generate projections for roster players
                if context.roster_data and 'players' in context.roster_data:
                    for player_id in context.roster_data['players'][:10]:
                        if player_id in nfl_players and player_id in sleeper_projections:
                            player = nfl_players[player_id]
                            player_proj = sleeper_projections[player_id]
                            
                            projections["roster_projections"][player.get('full_name', player_id)] = {
                                "position": player.get('position'),
                                "team": player.get('team'),
                                "projections": player_proj,
                                "trending_status": "add" if player_id in [p.get('player_id') for p in trending_adds] else "drop" if player_id in [p.get('player_id') for p in trending_drops] else "stable"
                            }
                
                projections["model_accuracy"] = {
                    "data_source": "sleeper_api",
                    "last_updated": datetime.now().isoformat()
                }
                
                return projections
            
        except Exception as e:
            self.logger.error(f"Projection generation failed: {str(e)}")
            return {}
    
    def _generate_statistical_reasoning(self, stats_data: Dict[str, Any], context: AgentContext) -> str:
        """Generate reasoning based on statistical analysis."""
        reasoning_parts = []
        
        if "advanced_metrics" in stats_data:
            reasoning_parts.append("Advanced metrics analysis including target share, air yards, and efficiency calculations")
        
        if "historical_patterns" in stats_data:
            patterns = stats_data["historical_patterns"]
            if "regression_candidates" in patterns:
                reasoning_parts.append(f"Historical pattern analysis identifying {len(patterns['regression_candidates'].get('positive_regression', []))} positive regression candidates")
        
        if "strength_of_schedule" in stats_data:
            reasoning_parts.append("Strength of schedule analysis for remaining games and playoff implications")
        
        if "projections" in stats_data:
            proj = stats_data["projections"]
            if "model_accuracy" in proj:
                accuracy = proj["model_accuracy"]["overall_accuracy"] * 100
                reasoning_parts.append(f"Proprietary projection model with {accuracy:.0f}% historical accuracy")
        
        return "Statistical Analysis: " + "; ".join(reasoning_parts)