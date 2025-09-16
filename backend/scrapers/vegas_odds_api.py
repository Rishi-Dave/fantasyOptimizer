"""
Vegas Odds API client for NFL betting data and line movements.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class VegasOddsAPI:
    """
    Vegas Odds API client for NFL betting lines, totals, and player props.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make async HTTP request to Odds API."""
        if not self.api_key:
            logger.warning("No odds API key provided")
            return None
            
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            if not params:
                params = {}
            params['apiKey'] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Odds API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Odds request failed for {endpoint}: {str(e)}")
            return None
    
    async def get_nfl_odds(self, markets: str = "spreads,totals") -> List[Dict[str, Any]]:
        """Get current NFL odds and lines."""
        try:
            params = {
                'sport': 'americanfootball_nfl',
                'regions': 'us',
                'markets': markets,
                'oddsFormat': 'american'
            }
            
            odds_data = await self._make_request("sports/americanfootball_nfl/odds", params)
            
            if not odds_data:
                return []
            
            formatted_odds = []
            
            for game in odds_data:
                game_info = {
                    'game_id': game.get('id'),
                    'home_team': game.get('home_team'),
                    'away_team': game.get('away_team'),
                    'commence_time': game.get('commence_time'),
                    'bookmakers': []
                }
                
                # Process bookmaker odds
                for bookmaker in game.get('bookmakers', []):
                    book_data = {
                        'bookmaker': bookmaker.get('key'),
                        'title': bookmaker.get('title'),
                        'markets': {}
                    }
                    
                    for market in bookmaker.get('markets', []):
                        market_key = market.get('key')
                        book_data['markets'][market_key] = {
                            'outcomes': market.get('outcomes', [])
                        }
                    
                    game_info['bookmakers'].append(book_data)
                
                # Calculate consensus lines
                game_info['consensus'] = self._calculate_consensus_lines(game_info['bookmakers'])
                
                formatted_odds.append(game_info)
            
            return formatted_odds
            
        except Exception as e:
            logger.error(f"Failed to get NFL odds: {str(e)}")
            return []
    
    def _calculate_consensus_lines(self, bookmakers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus lines from multiple bookmakers."""
        try:
            consensus = {
                'spread': {'home': None, 'away': None},
                'total': {'over': None, 'under': None},
                'moneyline': {'home': None, 'away': None}
            }
            
            spreads = []
            totals = []
            home_ml = []
            away_ml = []
            
            for book in bookmakers:
                markets = book.get('markets', {})
                
                # Process spreads
                if 'spreads' in markets:
                    for outcome in markets['spreads']['outcomes']:
                        if outcome.get('name') == book.get('home_team'):
                            spreads.append(outcome.get('point', 0))
                
                # Process totals
                if 'totals' in markets:
                    for outcome in markets['totals']['outcomes']:
                        if outcome.get('name') == 'Over':
                            totals.append(outcome.get('point', 0))
                
                # Process moneylines
                if 'h2h' in markets:
                    for outcome in markets['h2h']['outcomes']:
                        if outcome.get('name') == book.get('home_team'):
                            home_ml.append(outcome.get('price', 100))
                        else:
                            away_ml.append(outcome.get('price', 100))
            
            # Calculate averages
            if spreads:
                avg_spread = sum(spreads) / len(spreads)
                consensus['spread']['home'] = round(avg_spread, 1)
                consensus['spread']['away'] = round(-avg_spread, 1)
            
            if totals:
                consensus['total']['over'] = round(sum(totals) / len(totals), 1)
                consensus['total']['under'] = consensus['total']['over']
            
            if home_ml:
                consensus['moneyline']['home'] = round(sum(home_ml) / len(home_ml))
            
            if away_ml:
                consensus['moneyline']['away'] = round(sum(away_ml) / len(away_ml))
            
            return consensus
            
        except Exception as e:
            logger.error(f"Failed to calculate consensus lines: {str(e)}")
            return {}
    
    async def get_line_movements(self, game_id: str, hours_back: int = 24) -> Dict[str, Any]:
        """Get line movement history for a game."""
        try:
            # This would require historical data endpoint
            # For now, return structure for when historical data is available
            
            return {
                'game_id': game_id,
                'movements': [],
                'current_lines': {},
                'opening_lines': {},
                'movement_analysis': {
                    'spread_movement': 0,
                    'total_movement': 0,
                    'sharp_money_direction': 'unknown'
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get line movements: {str(e)}")
            return {}
    
    async def get_player_props(self, game_id: str = None) -> List[Dict[str, Any]]:
        """Get player prop betting lines."""
        try:
            params = {
                'sport': 'americanfootball_nfl',
                'regions': 'us',
                'markets': 'player_pass_yds,player_rush_yds,player_receptions',
                'oddsFormat': 'american'
            }
            
            if game_id:
                # This would be for specific game props
                endpoint = f"sports/americanfootball_nfl/events/{game_id}/odds"
            else:
                endpoint = "sports/americanfootball_nfl/odds"
            
            props_data = await self._make_request(endpoint, params)
            
            if not props_data:
                return []
            
            formatted_props = []
            
            # Process player prop data
            # This would require more specific parsing based on actual API structure
            
            return formatted_props
            
        except Exception as e:
            logger.error(f"Failed to get player props: {str(e)}")
            return []
    
    async def analyze_game_environment(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """Analyze betting environment for fantasy implications."""
        try:
            # Get current odds for the game
            odds_data = await self.get_nfl_odds()
            
            game_odds = None
            for game in odds_data:
                if (game.get('home_team') == home_team and game.get('away_team') == away_team):
                    game_odds = game
                    break
            
            if not game_odds:
                return {}
            
            consensus = game_odds.get('consensus', {})
            
            # Analyze fantasy implications
            analysis = {
                'game_info': {
                    'home_team': home_team,
                    'away_team': away_team,
                    'commence_time': game_odds.get('commence_time')
                },
                'lines': consensus,
                'fantasy_implications': {},
                'game_script_prediction': {},
                'scoring_environment': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Analyze total for scoring environment
            total = consensus.get('total', {}).get('over')
            if total:
                if total >= 50:
                    analysis['scoring_environment'] = {
                        'type': 'high_scoring',
                        'fantasy_impact': 'positive_for_all_skill_positions',
                        'total': total
                    }
                elif total <= 42:
                    analysis['scoring_environment'] = {
                        'type': 'low_scoring',
                        'fantasy_impact': 'negative_for_skill_positions_positive_for_defense',
                        'total': total
                    }
                else:
                    analysis['scoring_environment'] = {
                        'type': 'moderate_scoring',
                        'fantasy_impact': 'neutral',
                        'total': total
                    }
            
            # Analyze spread for game script
            home_spread = consensus.get('spread', {}).get('home')
            if home_spread is not None:
                if abs(home_spread) >= 7:
                    favored_team = home_team if home_spread < 0 else away_team
                    underdog_team = away_team if home_spread < 0 else home_team
                    
                    analysis['game_script_prediction'] = {
                        'type': 'potential_blowout',
                        'favored_team': favored_team,
                        'underdog_team': underdog_team,
                        'spread': abs(home_spread),
                        'fantasy_impact': {
                            'favored_team_rbs': 'positive_late_game_volume',
                            'underdog_team_passing': 'positive_garbage_time',
                            'favored_team_passing': 'negative_if_lead_maintained'
                        }
                    }
                else:
                    analysis['game_script_prediction'] = {
                        'type': 'close_game',
                        'spread': abs(home_spread),
                        'fantasy_impact': {
                            'all_positions': 'neutral_to_positive',
                            'note': 'competitive_game_should_maintain_normal_usage'
                        }
                    }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze game environment: {str(e)}")
            return {}
    
    async def get_sharp_money_indicators(self) -> Dict[str, Any]:
        """Get indicators of sharp money movement."""
        try:
            # This would analyze line movements vs. public betting percentages
            # For now, return structure
            
            return {
                'sharp_plays': [],
                'reverse_line_movement': [],
                'steam_moves': [],
                'contrarian_opportunities': [],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get sharp money indicators: {str(e)}")
            return {}
    
    async def get_weekly_betting_analysis(self) -> Dict[str, Any]:
        """Get comprehensive weekly betting analysis."""
        try:
            # Get all current odds
            odds_data = await self.get_nfl_odds()
            
            analysis = {
                'total_games': len(odds_data),
                'high_total_games': [],
                'low_total_games': [],
                'large_spread_games': [],
                'close_games': [],
                'average_total': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            totals = []
            
            for game in odds_data:
                consensus = game.get('consensus', {})
                total = consensus.get('total', {}).get('over')
                home_spread = consensus.get('spread', {}).get('home')
                
                game_summary = {
                    'matchup': f"{game.get('away_team')} @ {game.get('home_team')}",
                    'total': total,
                    'spread': abs(home_spread) if home_spread is not None else None,
                    'commence_time': game.get('commence_time')
                }
                
                if total:
                    totals.append(total)
                    
                    if total >= 50:
                        analysis['high_total_games'].append(game_summary)
                    elif total <= 42:
                        analysis['low_total_games'].append(game_summary)
                
                if home_spread is not None:
                    if abs(home_spread) >= 7:
                        analysis['large_spread_games'].append(game_summary)
                    elif abs(home_spread) <= 3:
                        analysis['close_games'].append(game_summary)
            
            if totals:
                analysis['average_total'] = round(sum(totals) / len(totals), 1)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to get weekly betting analysis: {str(e)}")
            return {}
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()