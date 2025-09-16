"""
Weather API client for NFL game weather conditions.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class WeatherAPI:
    """
    Weather API client for getting game-day weather conditions.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('WEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = None
        
        # NFL stadium locations
        self.stadium_locations = {
            "ARI": {"city": "Glendale", "state": "AZ", "lat": 33.5276, "lon": -112.2626, "dome": True},
            "ATL": {"city": "Atlanta", "state": "GA", "lat": 33.7554, "lon": -84.4006, "dome": True},
            "BAL": {"city": "Baltimore", "state": "MD", "lat": 39.2780, "lon": -76.6227, "dome": False},
            "BUF": {"city": "Orchard Park", "state": "NY", "lat": 42.7738, "lon": -78.7870, "dome": False},
            "CAR": {"city": "Charlotte", "state": "NC", "lat": 35.2258, "lon": -80.8528, "dome": False},
            "CHI": {"city": "Chicago", "state": "IL", "lat": 41.8623, "lon": -87.6167, "dome": False},
            "CIN": {"city": "Cincinnati", "state": "OH", "lat": 39.0955, "lon": -84.5160, "dome": False},
            "CLE": {"city": "Cleveland", "state": "OH", "lat": 41.5061, "lon": -81.6995, "dome": False},
            "DAL": {"city": "Arlington", "state": "TX", "lat": 32.7473, "lon": -97.0945, "dome": True},
            "DEN": {"city": "Denver", "state": "CO", "lat": 39.7439, "lon": -105.0201, "dome": False},
            "DET": {"city": "Detroit", "state": "MI", "lat": 42.3400, "lon": -83.0456, "dome": True},
            "GB": {"city": "Green Bay", "state": "WI", "lat": 44.5013, "lon": -88.0622, "dome": False},
            "HOU": {"city": "Houston", "state": "TX", "lat": 29.6847, "lon": -95.4107, "dome": True},
            "IND": {"city": "Indianapolis", "state": "IN", "lat": 39.7601, "lon": -86.1639, "dome": True},
            "JAX": {"city": "Jacksonville", "state": "FL", "lat": 30.3240, "lon": -81.6373, "dome": False},
            "KC": {"city": "Kansas City", "state": "MO", "lat": 39.0489, "lon": -94.4839, "dome": False},
            "LV": {"city": "Las Vegas", "state": "NV", "lat": 36.0909, "lon": -115.1833, "dome": True},
            "LAC": {"city": "Los Angeles", "state": "CA", "lat": 33.8644, "lon": -118.2623, "dome": False},
            "LAR": {"city": "Los Angeles", "state": "CA", "lat": 34.0139, "lon": -118.2879, "dome": True},
            "MIA": {"city": "Miami Gardens", "state": "FL", "lat": 25.9580, "lon": -80.2389, "dome": False},
            "MIN": {"city": "Minneapolis", "state": "MN", "lat": 44.9778, "lon": -93.2576, "dome": True},
            "NE": {"city": "Foxborough", "state": "MA", "lat": 42.0909, "lon": -71.2643, "dome": False},
            "NO": {"city": "New Orleans", "state": "LA", "lat": 29.9511, "lon": -90.0812, "dome": True},
            "NYG": {"city": "East Rutherford", "state": "NJ", "lat": 40.8135, "lon": -74.0745, "dome": False},
            "NYJ": {"city": "East Rutherford", "state": "NJ", "lat": 40.8135, "lon": -74.0745, "dome": False},
            "PHI": {"city": "Philadelphia", "state": "PA", "lat": 39.9008, "lon": -75.1675, "dome": False},
            "PIT": {"city": "Pittsburgh", "state": "PA", "lat": 40.4468, "lon": -80.0158, "dome": False},
            "SF": {"city": "Santa Clara", "state": "CA", "lat": 37.4030, "lon": -121.9696, "dome": False},
            "SEA": {"city": "Seattle", "state": "WA", "lat": 47.5952, "lon": -122.3316, "dome": False},
            "TB": {"city": "Tampa", "state": "FL", "lat": 27.9759, "lon": -82.5033, "dome": False},
            "TEN": {"city": "Nashville", "state": "TN", "lat": 36.1665, "lon": -86.7713, "dome": False},
            "WAS": {"city": "Landover", "state": "MD", "lat": 38.9076, "lon": -76.8645, "dome": False}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make async HTTP request to Weather API."""
        if not self.api_key:
            logger.warning("No weather API key provided")
            return None
            
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            params['appid'] = self.api_key
            params['units'] = 'imperial'  # Fahrenheit, mph
            
            url = f"{self.base_url}/{endpoint}"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Weather API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Weather request failed for {endpoint}: {str(e)}")
            return None
    
    async def get_current_weather(self, team: str) -> Optional[Dict[str, Any]]:
        """Get current weather for a team's stadium."""
        try:
            stadium = self.stadium_locations.get(team.upper())
            if not stadium:
                logger.error(f"Unknown team: {team}")
                return None
            
            # Skip weather for dome stadiums
            if stadium["dome"]:
                return {
                    "team": team,
                    "city": stadium["city"],
                    "state": stadium["state"],
                    "dome": True,
                    "weather_impact": "none",
                    "conditions": "indoor_controlled"
                }
            
            params = {
                "lat": stadium["lat"],
                "lon": stadium["lon"]
            }
            
            weather_data = await self._make_request("weather", params)
            if not weather_data:
                return None
            
            return self._format_weather_data(weather_data, team, stadium)
            
        except Exception as e:
            logger.error(f"Failed to get current weather for {team}: {str(e)}")
            return None
    
    async def get_game_forecast(self, home_team: str, game_time: datetime) -> Optional[Dict[str, Any]]:
        """Get weather forecast for a specific game."""
        try:
            stadium = self.stadium_locations.get(home_team.upper())
            if not stadium:
                logger.error(f"Unknown team: {home_team}")
                return None
            
            # Skip weather for dome stadiums
            if stadium["dome"]:
                return {
                    "home_team": home_team,
                    "game_time": game_time.isoformat(),
                    "city": stadium["city"],
                    "state": stadium["state"],
                    "dome": True,
                    "weather_impact": "none",
                    "conditions": "indoor_controlled"
                }
            
            # Use 5-day forecast endpoint
            params = {
                "lat": stadium["lat"],
                "lon": stadium["lon"]
            }
            
            forecast_data = await self._make_request("forecast", params)
            if not forecast_data:
                return None
            
            # Find forecast closest to game time
            game_forecast = self._find_closest_forecast(forecast_data, game_time)
            
            if game_forecast:
                return self._format_weather_data(game_forecast, home_team, stadium, game_time)
            else:
                return None
            
        except Exception as e:
            logger.error(f"Failed to get game forecast for {home_team}: {str(e)}")
            return None
    
    def _find_closest_forecast(self, forecast_data: Dict[str, Any], target_time: datetime) -> Optional[Dict[str, Any]]:
        """Find the forecast entry closest to the game time."""
        try:
            forecasts = forecast_data.get("list", [])
            if not forecasts:
                return None
            
            closest_forecast = None
            min_time_diff = float('inf')
            
            for forecast in forecasts:
                forecast_time = datetime.fromtimestamp(forecast["dt"])
                time_diff = abs((forecast_time - target_time).total_seconds())
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_forecast = forecast
            
            return closest_forecast
            
        except Exception as e:
            logger.error(f"Failed to find closest forecast: {str(e)}")
            return None
    
    def _format_weather_data(self, weather_data: Dict[str, Any], team: str, 
                           stadium: Dict[str, Any], game_time: datetime = None) -> Dict[str, Any]:
        """Format weather data into standardized structure."""
        try:
            main = weather_data.get("main", {})
            weather = weather_data.get("weather", [{}])[0]
            wind = weather_data.get("wind", {})
            
            temperature = main.get("temp", 70)
            humidity = main.get("humidity", 50)
            wind_speed = wind.get("speed", 0)
            wind_direction = wind.get("deg", 0)
            conditions = weather.get("main", "Clear")
            description = weather.get("description", "clear sky")
            
            # Calculate weather impact
            impact_level = self._calculate_weather_impact(temperature, wind_speed, conditions)
            
            formatted_data = {
                "team": team,
                "city": stadium["city"],
                "state": stadium["state"],
                "dome": stadium["dome"],
                "temperature": round(temperature),
                "humidity": humidity,
                "wind_speed": round(wind_speed),
                "wind_direction": wind_direction,
                "conditions": conditions,
                "description": description,
                "weather_impact": impact_level,
                "fantasy_impact": self._get_fantasy_impact(temperature, wind_speed, conditions),
                "last_updated": datetime.now().isoformat()
            }
            
            if game_time:
                formatted_data["game_time"] = game_time.isoformat()
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Failed to format weather data: {str(e)}")
            return {}
    
    def _calculate_weather_impact(self, temperature: float, wind_speed: float, conditions: str) -> str:
        """Calculate overall weather impact level."""
        impact_score = 0
        
        # Temperature impact
        if temperature < 32:
            impact_score += 2
        elif temperature < 45:
            impact_score += 1
        elif temperature > 85:
            impact_score += 1
        
        # Wind impact
        if wind_speed > 20:
            impact_score += 3
        elif wind_speed > 15:
            impact_score += 2
        elif wind_speed > 10:
            impact_score += 1
        
        # Precipitation impact
        if any(cond in conditions.lower() for cond in ["rain", "snow", "storm"]):
            impact_score += 2
        
        if impact_score >= 4:
            return "high"
        elif impact_score >= 2:
            return "moderate"
        else:
            return "low"
    
    def _get_fantasy_impact(self, temperature: float, wind_speed: float, conditions: str) -> Dict[str, str]:
        """Get fantasy-specific impact analysis."""
        impact = {
            "passing_game": "neutral",
            "rushing_game": "neutral",
            "kicking_game": "neutral",
            "overall": "neutral"
        }
        
        # Wind impact on passing
        if wind_speed > 15:
            impact["passing_game"] = "negative"
            impact["kicking_game"] = "negative"
        elif wind_speed > 10:
            impact["passing_game"] = "slightly_negative"
        
        # Cold weather impact
        if temperature < 32:
            impact["passing_game"] = "negative"
            impact["kicking_game"] = "negative"
            impact["rushing_game"] = "positive"
        elif temperature < 45:
            impact["passing_game"] = "slightly_negative"
        
        # Precipitation impact
        if any(cond in conditions.lower() for cond in ["rain", "snow"]):
            impact["passing_game"] = "negative"
            impact["rushing_game"] = "positive"
        
        # Overall impact
        negative_count = sum(1 for v in impact.values() if "negative" in v)
        if negative_count >= 2:
            impact["overall"] = "negative"
        elif negative_count == 1:
            impact["overall"] = "slightly_negative"
        
        return impact
    
    async def get_weekly_weather_report(self, week_games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get weather report for all games in a week."""
        try:
            weather_reports = []
            
            for game in week_games:
                home_team = game.get("home_team")
                game_time = game.get("game_time")
                
                if home_team and game_time:
                    if isinstance(game_time, str):
                        game_time = datetime.fromisoformat(game_time)
                    
                    weather = await self.get_game_forecast(home_team, game_time)
                    if weather:
                        weather["away_team"] = game.get("away_team")
                        weather_reports.append(weather)
            
            # Identify games with significant weather impact
            impacted_games = [
                report for report in weather_reports 
                if report.get("weather_impact") in ["moderate", "high"]
            ]
            
            return {
                "week_weather": weather_reports,
                "impacted_games": impacted_games,
                "weather_summary": self._generate_weather_summary(weather_reports),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get weekly weather report: {str(e)}")
            return {}
    
    def _generate_weather_summary(self, weather_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of weather impacts for the week."""
        try:
            summary = {
                "total_games": len(weather_reports),
                "dome_games": 0,
                "outdoor_games": 0,
                "high_impact_games": 0,
                "moderate_impact_games": 0,
                "wind_affected_games": 0,
                "cold_weather_games": 0,
                "precipitation_games": 0
            }
            
            for report in weather_reports:
                if report.get("dome"):
                    summary["dome_games"] += 1
                else:
                    summary["outdoor_games"] += 1
                
                impact = report.get("weather_impact", "low")
                if impact == "high":
                    summary["high_impact_games"] += 1
                elif impact == "moderate":
                    summary["moderate_impact_games"] += 1
                
                if report.get("wind_speed", 0) > 15:
                    summary["wind_affected_games"] += 1
                
                if report.get("temperature", 70) < 45:
                    summary["cold_weather_games"] += 1
                
                conditions = report.get("conditions", "").lower()
                if any(cond in conditions for cond in ["rain", "snow", "storm"]):
                    summary["precipitation_games"] += 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate weather summary: {str(e)}")
            return {}
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()