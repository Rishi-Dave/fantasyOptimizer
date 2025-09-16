"""
Data enrichment service that transforms raw data into AI-ready context.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..scrapers.sleeper_api import SleeperAPI

logger = logging.getLogger(__name__)

class DataEnrichmentService:
    """
    Enriches raw data from scrapers into structured context for LLM analysis.
    """
    
    def __init__(self):
        self.player_cache = {}
        self.cache_timestamp = None
        
    async def enrich_pipeline_data(self, fresh_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw pipeline data into enriched context for LLM analysis.
        """
        enriched_context = {
            'data_sources_active': {},
            'trending_analysis': {},
            'weather_impact': {},
            'vegas_insights': {},
            'injury_alerts': {},
            'expert_rankings': {},
            'sentiment_analysis': {},
            'actionable_insights': []
        }
        
        # Get player names for enrichment
        await self._refresh_player_cache()
        
        # Enrich trending data
        if fresh_data.get('sleeper_trending', {}).get('data'):
            enriched_context['trending_analysis'] = await self._enrich_trending_data(
                fresh_data['sleeper_trending']['data']
            )
            enriched_context['data_sources_active']['sleeper'] = True
        
        # Enrich weather data
        if fresh_data.get('weather_data', {}).get('data'):
            enriched_context['weather_impact'] = await self._enrich_weather_data(
                fresh_data['weather_data']['data']
            )
            enriched_context['data_sources_active']['weather'] = True
        
        # Enrich Vegas odds
        if fresh_data.get('vegas_odds', {}).get('data'):
            enriched_context['vegas_insights'] = await self._enrich_vegas_data(
                fresh_data['vegas_odds']['data']
            )
            enriched_context['data_sources_active']['vegas'] = True
        
        # Enrich NFL injury data
        if fresh_data.get('nfl_injuries', {}).get('data'):
            enriched_context['injury_alerts'] = await self._enrich_injury_data(
                fresh_data['nfl_injuries']['data']
            )
            enriched_context['data_sources_active']['nfl'] = True
        
        # Enrich FantasyPros data
        if fresh_data.get('fantasypros_rankings', {}).get('data'):
            enriched_context['expert_rankings'] = await self._enrich_rankings_data(
                fresh_data['fantasypros_rankings']['data']
            )
            enriched_context['data_sources_active']['fantasypros'] = True
        
        # Enrich Reddit sentiment
        if fresh_data.get('reddit_sentiment', {}).get('data'):
            enriched_context['sentiment_analysis'] = await self._enrich_sentiment_data(
                fresh_data['reddit_sentiment']['data']
            )
            enriched_context['data_sources_active']['reddit'] = True
        
        # Generate actionable insights
        enriched_context['actionable_insights'] = await self._generate_insights(enriched_context)
        
        return enriched_context
    
    async def _refresh_player_cache(self):
        """Refresh player name cache if stale."""
        if (not self.player_cache or 
            not self.cache_timestamp or 
            (datetime.now() - self.cache_timestamp).total_seconds() > 3600):  # 1 hour cache
            
            try:
                async with SleeperAPI() as sleeper:
                    self.player_cache = await sleeper.get_nfl_players()
                    self.cache_timestamp = datetime.now()
                    logger.info(f"Refreshed player cache with {len(self.player_cache)} players")
            except Exception as e:
                logger.error(f"Failed to refresh player cache: {e}")
    
    async def _enrich_trending_data(self, trending_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich trending player data with names and analysis."""
        enriched = {
            'top_adds': [],
            'top_drops': [],
            'breakout_candidates': [],
            'injury_replacements': [],
            'analysis_summary': ""
        }
        
        # Process trending adds
        for player in trending_data.get('trending_add', [])[:10]:
            player_id = player.get('player_id')
            count = player.get('count', 0)
            
            player_info = self.player_cache.get(player_id, {})
            player_name = player_info.get('full_name', f'Unknown Player {player_id}')
            position = player_info.get('position', 'Unknown')
            team = player_info.get('team', 'Unknown')
            
            enriched['top_adds'].append({
                'name': player_name,
                'position': position,
                'team': team,
                'add_count': count,
                'add_percentage': round((count / 10000000) * 100, 2),  # Rough percentage
                'player_id': player_id
            })
        
        # Process trending drops
        for player in trending_data.get('trending_drop', [])[:10]:
            player_id = player.get('player_id')
            count = player.get('count', 0)
            
            player_info = self.player_cache.get(player_id, {})
            player_name = player_info.get('full_name', f'Unknown Player {player_id}')
            position = player_info.get('position', 'Unknown')
            team = player_info.get('team', 'Unknown')
            
            enriched['top_drops'].append({
                'name': player_name,
                'position': position, 
                'team': team,
                'drop_count': count,
                'drop_percentage': round((count / 10000000) * 100, 2),
                'player_id': player_id
            })
        
        # Identify breakout candidates (high adds, low ownership)
        for add in enriched['top_adds'][:5]:
            if add['add_percentage'] > 5.0:  # High add rate
                enriched['breakout_candidates'].append({
                    'name': add['name'],
                    'position': add['position'],
                    'team': add['team'],
                    'reason': f"High add rate: {add['add_percentage']}% of leagues"
                })
        
        # Generate summary
        top_add = enriched['top_adds'][0] if enriched['top_adds'] else None
        top_drop = enriched['top_drops'][0] if enriched['top_drops'] else None
        
        enriched['analysis_summary'] = f"""
WAIVER WIRE ACTIVITY:
• Most Added: {top_add['name'] if top_add else 'None'} ({top_add['position'] if top_add else ''})
• Most Dropped: {top_drop['name'] if top_drop else 'None'} ({top_drop['position'] if top_drop else ''})
• Breakout Candidates: {len(enriched['breakout_candidates'])} players with high add rates
• Total Players Tracked: {len(enriched['top_adds'])} adds, {len(enriched['top_drops'])} drops
"""
        
        return enriched
    
    async def _enrich_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich weather data with fantasy impact analysis."""
        enriched = {
            'games_affected': [],
            'passing_game_impact': {},
            'kicking_impact': {},
            'weather_summary': ""
        }
        
        outdoor_weather = weather_data.get('outdoor_weather', {})
        
        negative_weather_games = 0
        wind_games = 0
        rain_games = 0
        
        for team, weather in outdoor_weather.items():
            fantasy_impact = weather.get('fantasy_impact', {})
            overall_impact = fantasy_impact.get('overall', 'neutral')
            
            if overall_impact in ['negative', 'slightly_negative']:
                negative_weather_games += 1
                enriched['games_affected'].append({
                    'team': team,
                    'city': weather.get('city', 'Unknown'),
                    'temperature': weather.get('temperature'),
                    'wind_speed': weather.get('wind_speed'),
                    'conditions': weather.get('conditions'),
                    'passing_impact': fantasy_impact.get('passing_game'),
                    'rushing_impact': fantasy_impact.get('rushing_game'),
                    'overall_impact': overall_impact
                })
            
            if weather.get('wind_speed', 0) > 10:
                wind_games += 1
            
            if 'rain' in weather.get('conditions', '').lower():
                rain_games += 1
        
        enriched['weather_summary'] = f"""
WEATHER CONDITIONS:
• {len(outdoor_weather)} outdoor stadiums monitored
• {negative_weather_games} games with negative fantasy impact
• {wind_games} games with high wind (>10 mph)
• {rain_games} games with rain conditions
• Impact: Favor running games and avoid long field goals in affected cities
"""
        
        return enriched
    
    async def _enrich_vegas_data(self, vegas_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich Vegas odds with game script analysis."""
        enriched = {
            'high_total_games': [],
            'blowout_games': [],
            'close_games': [],
            'game_script_analysis': "",
            'betting_summary': ""
        }
        
        game_odds = vegas_data.get('game_odds', [])
        
        for game in game_odds:
            home_team = game.get('home_team', 'Unknown')
            away_team = game.get('away_team', 'Unknown')
            
            # Extract consensus data
            consensus = game.get('consensus', {})
            total = consensus.get('total', {}).get('over', 0)
            
            # Find spread from first bookmaker
            spread = 0
            bookmakers = game.get('bookmakers', [])
            if bookmakers:
                spreads = bookmakers[0].get('markets', {}).get('spreads', {}).get('outcomes', [])
                if spreads:
                    spread = abs(spreads[0].get('point', 0))
            
            game_info = {
                'matchup': f"{away_team} @ {home_team}",
                'total': total,
                'spread': spread,
                'game_id': game.get('game_id')
            }
            
            # Categorize games
            if total > 47:  # High-scoring game
                enriched['high_total_games'].append(game_info)
            
            if spread > 7:  # Likely blowout
                enriched['blowout_games'].append(game_info)
            
            if spread < 3:  # Close game
                enriched['close_games'].append(game_info)
        
        enriched['betting_summary'] = f"""
VEGAS GAME SCRIPTS:
• {len(enriched['high_total_games'])} high-scoring games (47+ total)
• {len(enriched['blowout_games'])} potential blowouts (7+ point spread)
• {len(enriched['close_games'])} close games (< 3 point spread)
• Strategy: Target pass-catchers in high totals, RBs in blowouts, all positions in close games
"""
        
        return enriched
    
    async def _enrich_injury_data(self, injury_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich injury data with fantasy implications."""
        enriched = {
            'key_injuries': [],
            'handcuff_opportunities': [],
            'defensive_impacts': [],
            'injury_summary': ""
        }
        
        injury_reports = injury_data.get('injury_reports', [])
        defensive_stats = injury_data.get('defensive_stats', {})
        
        # Process injury reports
        for injury in injury_reports[:10]:  # Top 10 injuries
            player_name = injury.get('player_name', 'Unknown')
            team = injury.get('team', 'Unknown')
            position = injury.get('position', 'Unknown')
            status = injury.get('status', 'Unknown')
            
            if position in ['QB', 'RB', 'WR', 'TE']:  # Fantasy relevant positions
                enriched['key_injuries'].append({
                    'player': player_name,
                    'team': team,
                    'position': position,
                    'status': status,
                    'fantasy_impact': 'High' if position in ['QB', 'RB'] else 'Medium'
                })
        
        enriched['injury_summary'] = f"""
INJURY REPORT:
• {len(enriched['key_injuries'])} fantasy-relevant injuries tracked
• Monitor handcuff values for injured RBs
• Check practice participation reports before lineups
• Defensive stats: {len(defensive_stats)} teams analyzed
"""
        
        return enriched
    
    async def _enrich_rankings_data(self, rankings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich expert rankings data."""
        enriched = {
            'position_insights': {},
            'rankings_summary': ""
        }
        
        for position in ['qb_rankings', 'rb_rankings', 'wr_rankings', 'te_rankings']:
            if position in rankings_data:
                rankings = rankings_data[position]
                enriched['position_insights'][position] = {
                    'top_players': rankings[:5] if rankings else [],
                    'total_ranked': len(rankings) if rankings else 0
                }
        
        enriched['rankings_summary'] = f"""
EXPERT CONSENSUS:
• QB: {len(enriched['position_insights'].get('qb_rankings', {}).get('top_players', []))} ranked
• RB: {len(enriched['position_insights'].get('rb_rankings', {}).get('top_players', []))} ranked  
• WR: {len(enriched['position_insights'].get('wr_rankings', {}).get('top_players', []))} ranked
• TE: {len(enriched['position_insights'].get('te_rankings', {}).get('top_players', []))} ranked
"""
        
        return enriched
    
    async def _enrich_sentiment_data(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich Reddit sentiment data."""
        enriched = {
            'community_buzz': [],
            'hype_players': [],
            'sentiment_summary': ""
        }
        
        trending_discussions = sentiment_data.get('trending_discussions', {})
        fantasy_posts = sentiment_data.get('fantasy_posts', [])
        
        enriched['sentiment_summary'] = f"""
COMMUNITY SENTIMENT:
• {len(fantasy_posts)} recent fantasy posts analyzed
• Trending discussions tracked from r/fantasyfootball
• Community hype players identified
• Use for contrarian plays and avoid overhyped players
"""
        
        return enriched
    
    async def _generate_insights(self, enriched_context: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from enriched data."""
        insights = []
        
        # Trending insights
        trending = enriched_context.get('trending_analysis', {})
        if trending.get('top_adds'):
            top_add = trending['top_adds'][0]
            insights.append(f"🔥 WAIVER PRIORITY: {top_add['name']} ({top_add['position']}) - {top_add['add_percentage']}% add rate")
        
        # Weather insights
        weather = enriched_context.get('weather_impact', {})
        affected_games = weather.get('games_affected', [])
        if affected_games:
            for game in affected_games[:2]:  # Top 2 weather concerns
                insights.append(f"🌧️ WEATHER ALERT: {game['team']} game - {game['conditions']}, favor rushing attack")
        
        # Vegas insights  
        vegas = enriched_context.get('vegas_insights', {})
        high_totals = vegas.get('high_total_games', [])
        if high_totals:
            insights.append(f"📈 HIGH-SCORING: {len(high_totals)} games with 47+ totals - target pass-catchers")
        
        blowouts = vegas.get('blowout_games', [])
        if blowouts:
            insights.append(f"💨 BLOWOUT POTENTIAL: {len(blowouts)} games with 7+ spreads - favor lead RBs")
        
        # Injury insights
        injuries = enriched_context.get('injury_alerts', {})
        key_injuries = injuries.get('key_injuries', [])
        if key_injuries:
            qb_injuries = [inj for inj in key_injuries if inj['position'] == 'QB']
            rb_injuries = [inj for inj in key_injuries if inj['position'] == 'RB']
            
            if qb_injuries:
                insights.append(f"🏥 QB CONCERN: {len(qb_injuries)} quarterbacks on injury report")
            if rb_injuries:
                insights.append(f"🏥 HANDCUFF ALERT: {len(rb_injuries)} RBs injured - check backup values")
        
        return insights

# Global enrichment service
data_enrichment = DataEnrichmentService()