"""
Sleeper API client for real-time fantasy football data.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SleeperAPI:
    """
    Enhanced Sleeper API client for comprehensive fantasy football data.
    """
    
    def __init__(self):
        self.base_url = "https://api.sleeper.app/v1"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make async HTTP request to Sleeper API."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            url = f"{self.base_url}/{endpoint}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Sleeper API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            return None
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data by username."""
        return await self._make_request(f"user/{username}")
    
    async def get_user_leagues(self, user_id: str, season: int = None) -> List[Dict[str, Any]]:
        """Get all leagues for a user."""
        season = season or datetime.now().year
        result = await self._make_request(f"user/{user_id}/leagues/nfl/{season}")
        return result or []
    
    async def get_league(self, league_id: str) -> Optional[Dict[str, Any]]:
        """Get league information."""
        return await self._make_request(f"league/{league_id}")
    
    async def get_league_rosters(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all rosters in a league."""
        result = await self._make_request(f"league/{league_id}/rosters")
        return result or []
    
    async def get_league_users(self, league_id: str) -> List[Dict[str, Any]]:
        """Get all users in a league."""
        result = await self._make_request(f"league/{league_id}/users")
        return result or []
    
    async def get_league_matchups(self, league_id: str, week: int) -> List[Dict[str, Any]]:
        """Get matchups for a specific week."""
        result = await self._make_request(f"league/{league_id}/matchups/{week}")
        return result or []
    
    async def get_league_transactions(self, league_id: str, week: int = None) -> List[Dict[str, Any]]:
        """Get league transactions."""
        endpoint = f"league/{league_id}/transactions"
        if week:
            endpoint += f"/{week}"
        result = await self._make_request(endpoint)
        return result or []
    
    async def get_nfl_players(self) -> Dict[str, Any]:
        """Get all NFL players."""
        result = await self._make_request("players/nfl")
        return result or {}
    
    async def get_nfl_schedule(self, season: int = None) -> List[Dict[str, Any]]:
        """Get NFL schedule."""
        season = season or datetime.now().year
        result = await self._make_request(f"schedule/nfl/regular/{season}")
        return result or []
    
    async def get_nfl_week(self) -> Optional[Dict[str, Any]]:
        """Get current NFL week information."""
        return await self._make_request("state/nfl")
    
    async def get_user_roster_in_league(self, league_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific user's roster in a league."""
        rosters = await self.get_league_rosters(league_id)
        for roster in rosters:
            if roster.get('owner_id') == user_id:
                return roster
        return None
    
    async def get_player_stats(self, season: int = None, week: int = None) -> Dict[str, Any]:
        """Get player stats for season/week."""
        season = season or datetime.now().year
        
        if week:
            result = await self._make_request(f"stats/nfl/regular/{season}/{week}")
        else:
            result = await self._make_request(f"stats/nfl/regular/{season}")
        
        return result or {}
    
    async def get_projections(self, season: int = None, week: int = None) -> Dict[str, Any]:
        """Get player projections."""
        season = season or datetime.now().year
        
        if week:
            result = await self._make_request(f"projections/nfl/regular/{season}/{week}")
        else:
            result = await self._make_request(f"projections/nfl/regular/{season}")
        
        return result or {}
    
    async def get_trending_players(self, type_: str = "add", hours: int = 24) -> List[Dict[str, Any]]:
        """Get trending players (add/drop)."""
        result = await self._make_request(f"players/nfl/trending/{type_}?lookback_hours={hours}")
        return result or []
    
    async def get_comprehensive_league_data(self, league_id: str) -> Dict[str, Any]:
        """Get comprehensive data for a league."""
        try:
            # Gather all league data concurrently
            tasks = [
                self.get_league(league_id),
                self.get_league_rosters(league_id),
                self.get_league_users(league_id),
                self.get_nfl_week()
            ]
            
            league_info, rosters, users, nfl_state = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Get current week matchups if available
            current_week = 1
            if isinstance(nfl_state, dict) and nfl_state.get('week'):
                current_week = nfl_state['week']
            
            matchups = await self.get_league_matchups(league_id, current_week)
            
            return {
                "league_info": league_info if not isinstance(league_info, Exception) else None,
                "rosters": rosters if not isinstance(rosters, Exception) else [],
                "users": users if not isinstance(users, Exception) else [],
                "current_matchups": matchups,
                "nfl_state": nfl_state if not isinstance(nfl_state, Exception) else None,
                "current_week": current_week
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive league data: {str(e)}")
            return {}
    
    async def get_user_analysis_data(self, league_id: str, username: str) -> Dict[str, Any]:
        """Get all data needed for user analysis."""
        try:
            # Get user info
            user_data = await self.get_user(username)
            if not user_data:
                return {"error": "User not found"}
            
            user_id = user_data.get('user_id')
            
            # Get comprehensive league data
            league_data = await self.get_comprehensive_league_data(league_id)
            
            # Get user's roster
            user_roster = await self.get_user_roster_in_league(league_id, user_id)
            
            # Get NFL players for name mapping
            nfl_players = await self.get_nfl_players()
            
            # Get current week stats and projections
            current_week = league_data.get('current_week', 1)
            
            stats_task = self.get_player_stats(week=current_week)
            projections_task = self.get_projections(week=current_week)
            trending_task = self.get_trending_players()
            
            stats, projections, trending = await asyncio.gather(
                stats_task, projections_task, trending_task, return_exceptions=True
            )
            
            return {
                "user_data": user_data,
                "league_data": league_data,
                "user_roster": user_roster,
                "nfl_players": nfl_players,
                "current_stats": stats if not isinstance(stats, Exception) else {},
                "projections": projections if not isinstance(projections, Exception) else {},
                "trending_players": trending if not isinstance(trending, Exception) else [],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analysis data: {str(e)}")
            return {"error": str(e)}
    
    def format_player_names(self, player_ids: List[str], nfl_players: Dict[str, Any]) -> List[str]:
        """Convert player IDs to names."""
        names = []
        for player_id in player_ids or []:
            if player_id in nfl_players:
                player = nfl_players[player_id]
                full_name = player.get('full_name', f'Player {player_id}')
                names.append(full_name)
        return names
    
    def get_roster_by_position(self, roster: Dict[str, Any], nfl_players: Dict[str, Any]) -> Dict[str, List[str]]:
        """Organize roster by position."""
        positions = {"QB": [], "RB": [], "WR": [], "TE": [], "K": [], "DEF": []}
        
        for player_id in roster.get('players', []):
            if player_id in nfl_players:
                player = nfl_players[player_id]
                position = player.get('position', 'UNKNOWN')
                if position in positions:
                    positions[position].append(player.get('full_name', player_id))
        
        return positions
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()