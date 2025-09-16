"""
Real-time data pipeline that coordinates all scrapers and feeds fresh data to the AI system.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

# Import all scrapers
from ..scrapers.sleeper_api import SleeperAPI
from ..scrapers.fantasypros_scraper import FantasyProsScraper
from ..scrapers.reddit_scraper import RedditScraper
from ..scrapers.weather_api import WeatherAPI
from ..scrapers.vegas_odds_api import VegasOddsAPI
from ..scrapers.nfl_api import NFLAPI

logger = logging.getLogger(__name__)

@dataclass
class DataUpdate:
    """Data update with timestamp and source tracking."""
    source: str
    data_type: str
    data: Dict[str, Any]
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

class RealTimeDataPipeline:
    """
    Coordinates all data sources to provide fresh, real-time fantasy data.
    """
    
    def __init__(self):
        self.data_cache = {}
        self.last_updates = {}
        self.update_intervals = {
            'sleeper_trending': 300,     # 5 minutes
            'fantasypros_rankings': 1800, # 30 minutes  
            'reddit_sentiment': 600,      # 10 minutes
            'weather_data': 3600,         # 1 hour
            'vegas_odds': 900,            # 15 minutes
            'nfl_injuries': 1800,         # 30 minutes
        }
        self.running = False
        self.background_tasks = []
        
    async def start_pipeline(self):
        """Start all background data collection tasks."""
        self.running = True
        
        # Start individual scraper tasks
        tasks = [
            self._run_sleeper_updates(),
            self._run_fantasypros_updates(),
            self._run_reddit_updates(),
            self._run_weather_updates(),
            self._run_vegas_updates(),
            self._run_nfl_updates()
        ]
        
        self.background_tasks = [asyncio.create_task(task) for task in tasks]
        logger.info("Real-time data pipeline started with 6 active scrapers")
        
    async def stop_pipeline(self):
        """Stop all background tasks."""
        self.running = False
        for task in self.background_tasks:
            task.cancel()
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        logger.info("Data pipeline stopped")
        
    async def get_fresh_data(self, data_types: List[str] = None) -> Dict[str, Any]:
        """Get fresh data from cache with timestamps."""
        if data_types is None:
            data_types = list(self.update_intervals.keys())
            
        result = {}
        for data_type in data_types:
            if data_type in self.data_cache:
                result[data_type] = {
                    'data': self.data_cache[data_type],
                    'last_updated': self.last_updates.get(data_type),
                    'age_seconds': (datetime.now() - self.last_updates.get(data_type, datetime.min)).total_seconds()
                }
            else:
                result[data_type] = {
                    'data': None,
                    'last_updated': None,
                    'age_seconds': None
                }
                
        return result
        
    async def force_update(self, data_type: str) -> DataUpdate:
        """Force immediate update of specific data type."""
        if data_type == 'sleeper_trending':
            return await self._update_sleeper_data()
        elif data_type == 'fantasypros_rankings':
            return await self._update_fantasypros_data()
        elif data_type == 'reddit_sentiment':
            return await self._update_reddit_data()
        elif data_type == 'weather_data':
            return await self._update_weather_data()
        elif data_type == 'vegas_odds':
            return await self._update_vegas_data()
        elif data_type == 'nfl_injuries':
            return await self._update_nfl_data()
        else:
            return DataUpdate(
                source=data_type,
                data_type="unknown",
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message="Unknown data type"
            )
    
    # Background update loops
    async def _run_sleeper_updates(self):
        """Background task for Sleeper data updates."""
        while self.running:
            try:
                await self._update_sleeper_data()
                await asyncio.sleep(self.update_intervals['sleeper_trending'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sleeper update failed: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute on error
                
    async def _run_fantasypros_updates(self):
        """Background task for FantasyPros data updates."""
        while self.running:
            try:
                await self._update_fantasypros_data()
                await asyncio.sleep(self.update_intervals['fantasypros_rankings'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"FantasyPros update failed: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes on error
                
    async def _run_reddit_updates(self):
        """Background task for Reddit sentiment updates."""
        while self.running:
            try:
                await self._update_reddit_data()
                await asyncio.sleep(self.update_intervals['reddit_sentiment'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reddit update failed: {e}")
                await asyncio.sleep(120)  # Retry in 2 minutes on error
                
    async def _run_weather_updates(self):
        """Background task for weather data updates."""
        while self.running:
            try:
                await self._update_weather_data()
                await asyncio.sleep(self.update_intervals['weather_data'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Weather update failed: {e}")
                await asyncio.sleep(600)  # Retry in 10 minutes on error
                
    async def _run_vegas_updates(self):
        """Background task for Vegas odds updates."""
        while self.running:
            try:
                await self._update_vegas_data()
                await asyncio.sleep(self.update_intervals['vegas_odds'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Vegas odds update failed: {e}")
                await asyncio.sleep(180)  # Retry in 3 minutes on error
                
    async def _run_nfl_updates(self):
        """Background task for NFL injury/news updates."""
        while self.running:
            try:
                await self._update_nfl_data()
                await asyncio.sleep(self.update_intervals['nfl_injuries'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"NFL data update failed: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes on error
    
    # Individual update methods
    async def _update_sleeper_data(self) -> DataUpdate:
        """Update Sleeper trending players and league data."""
        try:
            async with SleeperAPI() as sleeper:
                trending_add = await sleeper.get_trending_players("add")
                trending_drop = await sleeper.get_trending_players("drop")
                
                data = {
                    'trending_add': trending_add[:20],  # Top 20 adds
                    'trending_drop': trending_drop[:20],  # Top 20 drops
                    'timestamp': datetime.now().isoformat()
                }
                
                self.data_cache['sleeper_trending'] = data
                self.last_updates['sleeper_trending'] = datetime.now()
                
                return DataUpdate(
                    source="sleeper",
                    data_type="trending",
                    data=data,
                    timestamp=datetime.now(),
                    success=True
                )
                
        except Exception as e:
            error_msg = f"Sleeper data update failed: {str(e)}"
            logger.error(error_msg)
            return DataUpdate(
                source="sleeper",
                data_type="trending",
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
    
    async def _update_fantasypros_data(self) -> DataUpdate:
        """Update FantasyPros rankings and expert consensus."""
        try:
            async with FantasyProsScraper() as fps:
                # Get expert consensus for current week
                qb_rankings = await fps.get_expert_consensus("QB")
                rb_rankings = await fps.get_expert_consensus("RB") 
                wr_rankings = await fps.get_expert_consensus("WR")
                te_rankings = await fps.get_expert_consensus("TE")
                
                data = {
                    'qb_rankings': qb_rankings[:30],
                    'rb_rankings': rb_rankings[:50], 
                    'wr_rankings': wr_rankings[:70],
                    'te_rankings': te_rankings[:25],
                    'timestamp': datetime.now().isoformat()
                }
                
                self.data_cache['fantasypros_rankings'] = data
                self.last_updates['fantasypros_rankings'] = datetime.now()
                
                return DataUpdate(
                    source="fantasypros",
                    data_type="rankings",
                    data=data,
                    timestamp=datetime.now(),
                    success=True
                )
                
        except Exception as e:
            error_msg = f"FantasyPros data update failed: {str(e)}"
            logger.error(error_msg)
            return DataUpdate(
                source="fantasypros",
                data_type="rankings", 
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
    
    async def _update_reddit_data(self) -> DataUpdate:
        """Update Reddit sentiment and hype data."""
        try:
            reddit = RedditScraper()
            
            # Get trending discussions and sentiment
            trending_discussions = await reddit.get_trending_discussions()
            fantasy_posts = await reddit.get_fantasyfootball_posts()
            
            data = {
                'trending_discussions': trending_discussions,
                'fantasy_posts': fantasy_posts[:15],
                'timestamp': datetime.now().isoformat()
            }
            
            self.data_cache['reddit_sentiment'] = data
            self.last_updates['reddit_sentiment'] = datetime.now()
            
            return DataUpdate(
                source="reddit",
                data_type="sentiment",
                data=data,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            error_msg = f"Reddit data update failed: {str(e)}"
            logger.error(error_msg)
            return DataUpdate(
                source="reddit",
                data_type="sentiment",
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
    
    async def _update_weather_data(self) -> DataUpdate:
        """Update weather data for outdoor games."""
        try:
            weather = WeatherAPI()
            
            # Get weather for all outdoor NFL teams
            outdoor_teams = [
                "CHI", "GB", "BUF", "NE", "DEN", "KC", "PIT", "CLE", 
                "CIN", "BAL", "WAS", "PHI", "CAR", "JAX", "MIA", "NYJ", "NYG"
            ]
            
            weather_data = {}
            for team in outdoor_teams:
                weather_info = await weather.get_current_weather(team)
                if weather_info:
                    weather_data[team] = weather_info
            
            data = {
                'outdoor_weather': weather_data,
                'timestamp': datetime.now().isoformat()
            }
            
            self.data_cache['weather_data'] = data
            self.last_updates['weather_data'] = datetime.now()
            
            return DataUpdate(
                source="weather",
                data_type="conditions",
                data=data,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            error_msg = f"Weather data update failed: {str(e)}"
            logger.error(error_msg)
            return DataUpdate(
                source="weather",
                data_type="conditions",
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
    
    async def _update_vegas_data(self) -> DataUpdate:
        """Update Vegas odds and game totals."""
        try:
            vegas = VegasOddsAPI()
            
            # Get current week's NFL odds and analysis
            game_odds = await vegas.get_nfl_odds()
            betting_analysis = await vegas.get_weekly_betting_analysis()
            
            data = {
                'game_odds': game_odds,
                'betting_analysis': betting_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            self.data_cache['vegas_odds'] = data
            self.last_updates['vegas_odds'] = datetime.now()
            
            return DataUpdate(
                source="vegas",
                data_type="odds",
                data=data,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            error_msg = f"Vegas odds update failed: {str(e)}"
            logger.error(error_msg)
            return DataUpdate(
                source="vegas",
                data_type="odds",
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
    
    async def _update_nfl_data(self) -> DataUpdate:
        """Update NFL injury reports and player news."""
        try:
            nfl = NFLAPI()
            
            # Get current injury and game data
            injury_reports = await nfl.get_injury_report()
            defensive_stats = await nfl.get_defensive_stats()
            
            data = {
                'injury_reports': injury_reports,
                'defensive_stats': defensive_stats,
                'timestamp': datetime.now().isoformat()
            }
            
            self.data_cache['nfl_injuries'] = data
            self.last_updates['nfl_injuries'] = datetime.now()
            
            return DataUpdate(
                source="nfl",
                data_type="injuries",
                data=data,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            error_msg = f"NFL data update failed: {str(e)}"
            logger.error(error_msg)
            return DataUpdate(
                source="nfl",
                data_type="injuries",
                data={},
                timestamp=datetime.now(),
                success=False,
                error_message=error_msg
            )
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current status of all data sources."""
        now = datetime.now()
        status = {
            'pipeline_running': self.running,
            'total_data_sources': len(self.update_intervals),
            'active_background_tasks': len([t for t in self.background_tasks if not t.done()]),
            'data_freshness': {}
        }
        
        for data_type, interval in self.update_intervals.items():
            last_update = self.last_updates.get(data_type)
            if last_update:
                age = (now - last_update).total_seconds()
                status['data_freshness'][data_type] = {
                    'last_updated': last_update.isoformat(),
                    'age_seconds': age,
                    'is_stale': age > (interval * 1.5),  # Consider stale if 1.5x past update interval
                    'has_data': data_type in self.data_cache
                }
            else:
                status['data_freshness'][data_type] = {
                    'last_updated': None,
                    'age_seconds': None,
                    'is_stale': True,
                    'has_data': False
                }
        
        return status

# Global pipeline instance
data_pipeline = RealTimeDataPipeline()