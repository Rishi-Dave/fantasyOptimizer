"""
FantasyPros scraper for expert consensus rankings and analysis.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class FantasyProsScraper:
    """
    Web scraper for FantasyPros expert consensus data.
    """
    
    def __init__(self):
        self.base_url = "https://www.fantasypros.com"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str) -> Optional[str]:
        """Make async HTTP request and return HTML content."""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
            
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"FantasyPros scraping error {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    async def get_expert_consensus(self, position: str = "all", week: int = None) -> Dict[str, Any]:
        """Get expert consensus rankings."""
        try:
            # Construct URL for consensus rankings
            if week:
                url = f"{self.base_url}/nfl/rankings/consensus-cheatsheets.php?week={week}"
            else:
                url = f"{self.base_url}/nfl/rankings/consensus-cheatsheets.php"
            
            html_content = await self._make_request(url)
            if not html_content:
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Parse consensus rankings table
            rankings = {}
            
            # Look for ranking tables
            tables = soup.find_all('table', class_='table')
            
            for table in tables:
                position_rankings = self._parse_rankings_table(table, position)
                if position_rankings:
                    rankings.update(position_rankings)
            
            return {
                "consensus_rankings": rankings,
                "expert_count": self._extract_expert_count(soup),
                "last_updated": datetime.now().isoformat(),
                "source": "fantasypros_consensus"
            }
            
        except Exception as e:
            logger.error(f"Failed to get expert consensus: {str(e)}")
            return {}
    
    def _parse_rankings_table(self, table, target_position: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse a rankings table from HTML."""
        try:
            rankings = {}
            
            # Find table headers to identify columns
            headers = []
            header_row = table.find('thead')
            if header_row:
                for th in header_row.find_all('th'):
                    headers.append(th.get_text(strip=True).lower())
            
            # Parse table rows
            tbody = table.find('tbody')
            if not tbody:
                return {}
            
            current_position = None
            position_players = []
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if not cells:
                    continue
                
                # Try to extract player data
                player_data = self._extract_player_data(cells, headers)
                
                if player_data:
                    # Determine position
                    position = player_data.get('position', '').upper()
                    
                    if position and position != current_position:
                        if current_position and position_players:
                            rankings[current_position] = position_players
                        current_position = position
                        position_players = []
                    
                    if target_position == "all" or position == target_position.upper():
                        position_players.append(player_data)
            
            # Add the last position
            if current_position and position_players:
                rankings[current_position] = position_players
            
            return rankings
            
        except Exception as e:
            logger.error(f"Failed to parse rankings table: {str(e)}")
            return {}
    
    def _extract_player_data(self, cells, headers) -> Optional[Dict[str, Any]]:
        """Extract player data from table row cells."""
        try:
            if len(cells) < 2:
                return None
            
            player_data = {}
            
            # Extract player name (usually in first or second cell)
            for i, cell in enumerate(cells[:3]):
                text = cell.get_text(strip=True)
                
                # Look for player name pattern (Name Team - POS)
                name_match = re.search(r'^([A-Za-z\.\s]+)\s+([A-Z]{2,4})\s*-?\s*([A-Z]{1,3})', text)
                if name_match:
                    player_data['name'] = name_match.group(1).strip()
                    player_data['team'] = name_match.group(2).strip()
                    player_data['position'] = name_match.group(3).strip()
                    break
                elif re.match(r'^[A-Za-z\.\s]+$', text) and len(text) > 3:
                    player_data['name'] = text
            
            # Extract rank if available
            if cells and cells[0].get_text(strip=True).isdigit():
                player_data['rank'] = int(cells[0].get_text(strip=True))
            
            # Extract additional data based on headers
            for i, header in enumerate(headers):
                if i < len(cells):
                    cell_text = cells[i].get_text(strip=True)
                    
                    if 'tier' in header:
                        player_data['tier'] = cell_text
                    elif 'proj' in header or 'points' in header:
                        try:
                            player_data['projected_points'] = float(cell_text)
                        except ValueError:
                            pass
            
            return player_data if player_data.get('name') else None
            
        except Exception as e:
            logger.error(f"Failed to extract player data: {str(e)}")
            return None
    
    def _extract_expert_count(self, soup) -> int:
        """Extract number of experts contributing to consensus."""
        try:
            # Look for expert count in various locations
            expert_text = soup.find(text=re.compile(r'\d+\s+experts?', re.IGNORECASE))
            if expert_text:
                match = re.search(r'(\d+)', expert_text)
                if match:
                    return int(match.group(1))
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to extract expert count: {str(e)}")
            return 0
    
    async def get_start_sit_advice(self, week: int = None) -> Dict[str, Any]:
        """Get start/sit advice from experts."""
        try:
            if week:
                url = f"{self.base_url}/nfl/start-sit.php?week={week}"
            else:
                url = f"{self.base_url}/nfl/start-sit.php"
            
            html_content = await self._make_request(url)
            if not html_content:
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            start_sit_data = {
                "start_recommendations": [],
                "sit_recommendations": [],
                "last_updated": datetime.now().isoformat()
            }
            
            # Look for start/sit sections
            start_sections = soup.find_all(['div', 'section'], class_=re.compile(r'start', re.IGNORECASE))
            sit_sections = soup.find_all(['div', 'section'], class_=re.compile(r'sit', re.IGNORECASE))
            
            # Parse start recommendations
            for section in start_sections:
                recommendations = self._parse_start_sit_section(section, "start")
                start_sit_data["start_recommendations"].extend(recommendations)
            
            # Parse sit recommendations
            for section in sit_sections:
                recommendations = self._parse_start_sit_section(section, "sit")
                start_sit_data["sit_recommendations"].extend(recommendations)
            
            return start_sit_data
            
        except Exception as e:
            logger.error(f"Failed to get start/sit advice: {str(e)}")
            return {}
    
    def _parse_start_sit_section(self, section, recommendation_type: str) -> List[Dict[str, Any]]:
        """Parse start/sit recommendation section."""
        try:
            recommendations = []
            
            # Look for player mentions
            player_elements = section.find_all(['p', 'div', 'span'])
            
            for element in player_elements:
                text = element.get_text(strip=True)
                
                # Look for player names in the text
                player_mentions = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text)
                
                for player_name in player_mentions:
                    # Extract reasoning from surrounding text
                    reasoning = text[:200]  # First 200 chars as reasoning
                    
                    recommendations.append({
                        "player": player_name,
                        "recommendation": recommendation_type,
                        "reasoning": reasoning,
                        "confidence": "medium"  # Would need more parsing for actual confidence
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to parse start/sit section: {str(e)}")
            return []
    
    async def get_injury_analysis(self) -> Dict[str, Any]:
        """Get injury analysis and reports."""
        try:
            url = f"{self.base_url}/nfl/injury-report.php"
            
            html_content = await self._make_request(url)
            if not html_content:
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            injury_data = {
                "injury_reports": [],
                "analysis": [],
                "last_updated": datetime.now().isoformat()
            }
            
            # Parse injury tables
            tables = soup.find_all('table')
            
            for table in tables:
                injury_reports = self._parse_injury_table(table)
                injury_data["injury_reports"].extend(injury_reports)
            
            return injury_data
            
        except Exception as e:
            logger.error(f"Failed to get injury analysis: {str(e)}")
            return {}
    
    def _parse_injury_table(self, table) -> List[Dict[str, Any]]:
        """Parse injury report table."""
        try:
            injury_reports = []
            
            tbody = table.find('tbody')
            if not tbody:
                return []
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    
                    player_name = cells[0].get_text(strip=True)
                    injury_status = cells[1].get_text(strip=True)
                    injury_type = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    
                    if player_name and injury_status:
                        injury_reports.append({
                            "player": player_name,
                            "status": injury_status,
                            "injury_type": injury_type,
                            "source": "fantasypros"
                        })
            
            return injury_reports
            
        except Exception as e:
            logger.error(f"Failed to parse injury table: {str(e)}")
            return []
    
    async def get_trade_analyzer_data(self) -> Dict[str, Any]:
        """Get trade analyzer data and values."""
        try:
            url = f"{self.base_url}/nfl/trade.php"
            
            html_content = await self._make_request(url)
            if not html_content:
                return {}
            
            # This would require more sophisticated parsing
            # For now, return structure
            return {
                "trade_values": {},
                "trending_players": [],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get trade analyzer data: {str(e)}")
            return {}
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()