"""
LLM Integration with ReAct prompting for Fantasy Football AI Multi-Agent System.

Provides sophisticated LLM reasoning using ReAct (Reasoning + Acting) methodology
for complex fantasy football analysis and decision making.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import os

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class ReActPromptGenerator:
    """
    Generates ReAct (Reasoning + Acting) prompts for fantasy football analysis.
    """
    
    def __init__(self):
        self.base_prompt = """
You are an expert fantasy football analyst with access to real-time data. Use the ReAct framework to analyze situations:

Thought: Reason about what information you need and what analysis to perform
Action: Describe what data you would use or what calculation you would make  
Observation: Analyze the data you have and what it tells you
Thought: Continue reasoning based on your observations
Action: Take the next analytical step
Observation: Draw insights from your analysis
... (continue until you reach a conclusion)
Final Answer: Provide your recommendation with confidence level and reasoning

Guidelines:
- Be brutally honest about player and team weaknesses
- Focus on actionable fantasy football advice
- Consider all relevant factors: matchups, weather, injuries, trends
- Provide specific confidence levels (0-100%)
- Include both ceiling and floor projections when relevant
"""
    
    def generate_team_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Generate ReAct prompt for team analysis."""
        
        user_data = context.get('user_data', {})
        roster_data = context.get('user_roster', {})
        league_data = context.get('league_data', {})
        
        prompt = f"""{self.base_prompt}

TASK: Analyze {user_data.get('username', 'this user')}'s fantasy team and provide brutally honest assessment.

LEAGUE CONTEXT:
- League: {league_data.get('league_info', {}).get('name', 'Unknown')}
- Teams: {league_data.get('league_info', {}).get('total_rosters', 'Unknown')}
- Scoring: {league_data.get('league_info', {}).get('scoring_settings', {}).get('rec', 0)} PPR
- Current Week: {league_data.get('current_week', 'Unknown')}

ROSTER DATA:
{json.dumps(roster_data, indent=2) if roster_data else 'No roster data available'}

AVAILABLE DATA:
- Current player stats and projections
- Injury reports and practice participation  
- Expert consensus rankings
- Vegas odds and game totals
- Social media sentiment
- Weather forecasts for outdoor games

Now analyze this team using the ReAct framework. Be specific about strengths, weaknesses, and actionable recommendations.
"""
        return prompt
    
    def generate_matchup_analysis_prompt(self, context: Dict[str, Any], players: List[str]) -> str:
        """Generate ReAct prompt for matchup analysis."""
        
        prompt = f"""{self.base_prompt}

TASK: Analyze matchups for these players: {', '.join(players)}

CONTEXT:
- Current NFL Week: {context.get('current_week', 'Unknown')}
- Weather data available for outdoor games
- Vegas odds and totals available
- Defensive rankings by position
- Recent snap count and target share trends

PLAYERS TO ANALYZE:
{json.dumps(players, indent=2)}

AVAILABLE DATA:
- Opponent defensive rankings vs position
- Game scripts based on Vegas lines
- Weather conditions for outdoor games
- Recent usage trends and snap counts
- Injury reports and practice participation

Use ReAct framework to analyze each player's matchup. Consider:
1. Opponent defensive strength vs position
2. Game script implications from betting lines
3. Weather impact for outdoor games
4. Recent usage trends
5. Injury concerns

Provide start/sit recommendations with confidence levels.
"""
        return prompt
    
    def generate_waiver_wire_prompt(self, context: Dict[str, Any], available_players: List[Dict[str, Any]]) -> str:
        """Generate ReAct prompt for waiver wire analysis."""
        
        prompt = f"""{self.base_prompt}

TASK: Analyze waiver wire pickups and FAAB bidding strategy.

ROSTER CONTEXT:
{json.dumps(context.get('user_roster', {}), indent=2)}

AVAILABLE PLAYERS:
{json.dumps(available_players[:10], indent=2)}  # Limit for prompt size

LEAGUE SETTINGS:
- FAAB Budget Remaining: {context.get('faab_remaining', 'Unknown')}
- Weeks Remaining: {context.get('weeks_remaining', 'Unknown')}
- League Size: {context.get('league_size', 'Unknown')}

AVAILABLE DATA:
- Trending players (adds/drops)
- Opportunity changes (injuries ahead of them)
- Target share and snap count trends
- Upcoming schedule difficulty
- Handcuff values based on starter injury risk

Use ReAct framework to:
1. Identify which players address roster needs
2. Assess breakout probability for trending players
3. Calculate optimal FAAB bid amounts
4. Prioritize players by value and urgency
5. Recommend drop candidates

Provide specific FAAB bid ranges and reasoning for each recommendation.
"""
        return prompt
    
    def generate_trade_analysis_prompt(self, context: Dict[str, Any], trade_proposal: Dict[str, Any]) -> str:
        """Generate ReAct prompt for trade analysis."""
        
        prompt = f"""{self.base_prompt}

TASK: Analyze this trade proposal for value and fit.

TRADE PROPOSAL:
Giving: {trade_proposal.get('giving', [])}
Receiving: {trade_proposal.get('receiving', [])}

ROSTER CONTEXT:
{json.dumps(context.get('user_roster', {}), indent=2)}

LEAGUE CONTEXT:
- Current Record: {context.get('record', 'Unknown')}
- Playoff Position: {context.get('playoff_position', 'Unknown')}
- Weeks to Playoffs: {context.get('weeks_to_playoffs', 'Unknown')}

AVAILABLE DATA:
- Rest of season schedules for all players
- Playoff schedules (weeks 15-17)
- Position scarcity in league
- Injury risk assessments
- Recent performance trends

Use ReAct framework to analyze:
1. Player values in current format (redraft/dynasty)
2. Positional needs and depth chart impact
3. Schedule advantages for playoffs
4. Injury risk vs reward for each player
5. Overall trade value and league context

Provide accept/decline recommendation with detailed reasoning.
"""
        return prompt

class LLMManager:
    """
    Manages LLM interactions with support for multiple models and ReAct prompting.
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.prompt_generator = ReActPromptGenerator()
        
        # Initialize clients if API keys are available
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
        
        if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
    
    async def analyze_with_react(self, prompt: str, model: str = "claude") -> Dict[str, Any]:
        """
        Perform analysis using ReAct prompting methodology.
        """
        try:
            if model == "claude" and self.anthropic_client:
                response = await self._query_claude(prompt)
            elif model == "gpt4" and self.openai_client:
                response = await self._query_gpt4(prompt)
            else:
                # Fallback to structured analysis
                response = self._generate_structured_fallback(prompt)
            
            # Parse ReAct response
            parsed_response = self._parse_react_response(response)
            
            return {
                "analysis": response,
                "structured_output": parsed_response,
                "model_used": model,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "structured_output": {},
                "model_used": "fallback",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _query_claude(self, prompt: str) -> str:
        """Query Claude using Anthropic API."""
        try:
            message = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude query failed: {str(e)}")
            raise
    
    async def _query_gpt4(self, prompt: str) -> str:
        """Query GPT-4 using OpenAI API."""
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert fantasy football analyst using ReAct methodology."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT-4 query failed: {str(e)}")
            raise
    
    def _generate_structured_fallback(self, prompt: str) -> str:
        """Generate structured fallback response when LLMs are unavailable."""
        
        fallback = """
Thought: I need to analyze the fantasy football situation presented.

Action: Review the available data including roster composition, league settings, and current context.

Observation: Based on the limited data processing capability in fallback mode, I can provide general fantasy football principles.

Thought: I should focus on the most important fantasy football factors.

Action: Apply standard fantasy football analysis framework considering:
- Start/sit decisions based on matchup difficulty
- Waiver wire priorities focusing on opportunity and usage
- Trade values considering positional scarcity
- Weather and injury impacts on player performance

Observation: Without real-time LLM processing, I can provide structured analysis based on fantasy football best practices.

Final Answer: 
RECOMMENDATION: Follow standard fantasy football principles
CONFIDENCE: 60% (limited by fallback mode)
REASONING: Unable to access advanced LLM analysis. Recommend using real-time data sources and expert consensus for more detailed insights.

KEY FACTORS TO CONSIDER:
1. Opportunity over talent (targets, carries, red zone looks)
2. Matchup difficulty vs opposing defenses
3. Weather conditions for outdoor games
4. Injury reports and practice participation
5. Vegas implied game scripts

NEXT STEPS:
- Check injury reports before lineup decisions
- Monitor weather for outdoor games
- Review expert consensus rankings
- Consider opponent defensive rankings by position
"""
        
        return fallback
    
    def _parse_react_response(self, response: str) -> Dict[str, Any]:
        """Parse ReAct response into structured output."""
        try:
            parsed = {
                "thoughts": [],
                "actions": [],
                "observations": [],
                "final_answer": "",
                "confidence": 0,
                "recommendations": []
            }
            
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('Thought:'):
                    parsed["thoughts"].append(line.replace('Thought:', '').strip())
                elif line.startswith('Action:'):
                    parsed["actions"].append(line.replace('Action:', '').strip())
                elif line.startswith('Observation:'):
                    parsed["observations"].append(line.replace('Observation:', '').strip())
                elif line.startswith('Final Answer:'):
                    current_section = "final_answer"
                    parsed["final_answer"] = line.replace('Final Answer:', '').strip()
                elif current_section == "final_answer" and line:
                    parsed["final_answer"] += " " + line
                
                # Extract confidence if mentioned
                if 'confidence' in line.lower() and '%' in line:
                    try:
                        confidence_match = [int(s) for s in line.split() if s.isdigit()]
                        if confidence_match:
                            parsed["confidence"] = confidence_match[0] / 100
                    except:
                        pass
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse ReAct response: {str(e)}")
            return {"error": str(e)}
    
    async def team_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive team analysis using ReAct prompting."""
        prompt = self.prompt_generator.generate_team_analysis_prompt(context)
        return await self.analyze_with_react(prompt, "claude")
    
    async def matchup_analysis(self, context: Dict[str, Any], players: List[str]) -> Dict[str, Any]:
        """Perform matchup analysis using ReAct prompting."""
        prompt = self.prompt_generator.generate_matchup_analysis_prompt(context, players)
        return await self.analyze_with_react(prompt, "gpt4")
    
    async def waiver_wire_analysis(self, context: Dict[str, Any], available_players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform waiver wire analysis using ReAct prompting."""
        prompt = self.prompt_generator.generate_waiver_wire_prompt(context, available_players)
        return await self.analyze_with_react(prompt, "claude")
    
    async def trade_analysis(self, context: Dict[str, Any], trade_proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Perform trade analysis using ReAct prompting."""
        prompt = self.prompt_generator.generate_trade_analysis_prompt(context, trade_proposal)
        return await self.analyze_with_react(prompt, "gpt4")