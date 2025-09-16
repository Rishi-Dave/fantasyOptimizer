"""
LangGraph workflow for coordinating multiple fantasy football agents.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import json

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .llm_integration import LLMManager
from ..data.data_enrichment import data_enrichment
from ..data.data_pipeline import data_pipeline
from ..scrapers.sleeper_api import SleeperAPI

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State shared between agents in the workflow."""
    user_request: str
    league_id: str
    username: str
    user_data: Dict[str, Any]
    league_data: Dict[str, Any] 
    roster_data: Dict[str, Any]
    fresh_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    
    # Agent outputs
    data_analysis: Dict[str, Any]
    market_intelligence: Dict[str, Any]
    statistical_analysis: Dict[str, Any]
    strategic_recommendations: Dict[str, Any]
    
    # Final output
    coordinated_analysis: str
    confidence_score: float
    action_items: List[str]
    evidence_sources: List[str]
    
    # Workflow metadata
    agents_completed: List[str]
    execution_log: List[str]

class FantasyFootballWorkflow:
    """
    LangGraph workflow that coordinates multiple specialized agents.
    """
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.workflow = None
        self.memory = MemorySaver()
        self._build_workflow()
        
    def _build_workflow(self):
        """Build the LangGraph workflow with agent coordination."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("data_collector", self._data_collection_agent)
        workflow.add_node("market_analyst", self._market_intelligence_agent)
        workflow.add_node("statistical_analyst", self._statistical_analysis_agent)
        workflow.add_node("strategist", self._strategic_planning_agent)
        workflow.add_node("coordinator", self._coordination_agent)
        
        # Define the workflow edges
        workflow.set_entry_point("data_collector")
        workflow.add_edge("data_collector", "market_analyst")
        workflow.add_edge("market_analyst", "statistical_analyst")
        workflow.add_edge("statistical_analyst", "strategist")
        workflow.add_edge("strategist", "coordinator")
        workflow.add_edge("coordinator", END)
        
        # Compile the workflow
        self.workflow = workflow.compile(checkpointer=self.memory)
        
    async def execute_analysis(self, user_request: str, league_id: str, username: str) -> Dict[str, Any]:
        """
        Execute the full multi-agent workflow for fantasy analysis.
        """
        
        # Initialize state
        initial_state = AgentState(
            user_request=user_request,
            league_id=league_id,
            username=username,
            user_data={},
            league_data={},
            roster_data={},
            fresh_data={},
            enriched_data={},
            data_analysis={},
            market_intelligence={},
            statistical_analysis={},
            strategic_recommendations={},
            coordinated_analysis="",
            confidence_score=0.0,
            action_items=[],
            evidence_sources=[],
            agents_completed=[],
            execution_log=[]
        )
        
        # Execute the workflow
        config = {"configurable": {"thread_id": f"{username}_{datetime.now().isoformat()}"}}
        
        try:
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            return {
                "success": True,
                "analysis": final_state["coordinated_analysis"],
                "confidence_score": final_state["confidence_score"],
                "action_items": final_state["action_items"],
                "evidence_sources": final_state["evidence_sources"],
                "agents_completed": final_state["agents_completed"],
                "execution_log": final_state["execution_log"],
                "agent_outputs": {
                    "data_analysis": final_state["data_analysis"],
                    "market_intelligence": final_state["market_intelligence"],
                    "statistical_analysis": final_state["statistical_analysis"],
                    "strategic_recommendations": final_state["strategic_recommendations"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _data_collection_agent(self, state: AgentState) -> Dict[str, Any]:
        """Agent responsible for collecting and enriching all data sources."""
        
        state["execution_log"].append("🔍 Data Collection Agent: Starting comprehensive data gathering")
        
        try:
            # Get Sleeper data
            async with SleeperAPI() as sleeper:
                user_data = await sleeper.get_user(state["username"])
                league_data = await sleeper.get_league(state["league_id"])
                
                if user_data and league_data:
                    user_id = user_data.get('user_id')
                    roster_data = await sleeper.get_user_roster_in_league(state["league_id"], user_id)
                    
                    state["user_data"] = user_data
                    state["league_data"] = league_data
                    state["roster_data"] = roster_data or {}
            
            # Get fresh real-time data
            fresh_data = await data_pipeline.get_fresh_data([
                'sleeper_trending', 'fantasypros_rankings', 'reddit_sentiment',
                'weather_data', 'vegas_odds', 'nfl_injuries'
            ])
            state["fresh_data"] = fresh_data
            
            # Enrich the data
            enriched_data = await data_enrichment.enrich_pipeline_data(fresh_data)
            state["enriched_data"] = enriched_data
            
            # Store analysis results
            state["data_analysis"] = {
                "sources_active": len([k for k, v in enriched_data.get('data_sources_active', {}).items() if v]),
                "actionable_insights": len(enriched_data.get('actionable_insights', [])),
                "trending_players": len(enriched_data.get('trending_analysis', {}).get('top_adds', [])),
                "weather_affected_games": len(enriched_data.get('weather_impact', {}).get('games_affected', [])),
                "high_total_games": len(enriched_data.get('vegas_insights', {}).get('high_total_games', [])),
                "key_injuries": len(enriched_data.get('injury_alerts', {}).get('key_injuries', []))
            }
            
            state["agents_completed"].append("data_collector")
            state["execution_log"].append(f"✅ Data Collection: {state['data_analysis']['sources_active']} sources active")
            
        except Exception as e:
            state["execution_log"].append(f"❌ Data Collection Failed: {str(e)}")
            
        return state
    
    async def _market_intelligence_agent(self, state: AgentState) -> Dict[str, Any]:
        """Agent focused on market trends and waiver wire intelligence."""
        
        state["execution_log"].append("📈 Market Intelligence Agent: Analyzing waiver wire and market trends")
        
        try:
            enriched_data = state["enriched_data"]
            trending = enriched_data.get('trending_analysis', {})
            
            # Analyze market trends
            market_analysis = {
                "hot_pickups": [],
                "value_plays": [],
                "avoid_players": [],
                "market_sentiment": "neutral",
                "breakout_probability": {}
            }
            
            # Process top adds for value analysis
            top_adds = trending.get('top_adds', [])[:10]
            for player in top_adds:
                add_rate = player.get('add_percentage', 0)
                
                if add_rate > 10:  # High demand
                    market_analysis["hot_pickups"].append({
                        "player": player['name'],
                        "position": player['position'],
                        "team": player['team'],
                        "add_rate": add_rate,
                        "urgency": "high" if add_rate > 15 else "medium"
                    })
                elif 5 <= add_rate <= 10:  # Value plays
                    market_analysis["value_plays"].append({
                        "player": player['name'],
                        "position": player['position'],
                        "team": player['team'], 
                        "add_rate": add_rate,
                        "value_rating": "high"
                    })
            
            # Identify avoid players from drops
            top_drops = trending.get('top_drops', [])[:5]
            for player in top_drops:
                drop_rate = player.get('drop_percentage', 0)
                if drop_rate > 5:
                    market_analysis["avoid_players"].append({
                        "player": player['name'],
                        "position": player['position'],
                        "team": player['team'],
                        "drop_rate": drop_rate,
                        "concern_level": "high" if drop_rate > 10 else "medium"
                    })
            
            # Determine market sentiment
            if len(market_analysis["hot_pickups"]) > 3:
                market_analysis["market_sentiment"] = "aggressive"
            elif len(market_analysis["value_plays"]) > 5:
                market_analysis["market_sentiment"] = "opportunistic"
            else:
                market_analysis["market_sentiment"] = "conservative"
            
            state["market_intelligence"] = market_analysis
            state["agents_completed"].append("market_analyst")
            state["execution_log"].append(f"✅ Market Intelligence: {len(market_analysis['hot_pickups'])} hot pickups, {len(market_analysis['value_plays'])} value plays")
            
        except Exception as e:
            state["execution_log"].append(f"❌ Market Intelligence Failed: {str(e)}")
            
        return state
    
    async def _statistical_analysis_agent(self, state: AgentState) -> Dict[str, Any]:
        """Agent focused on statistical analysis and game script predictions."""
        
        state["execution_log"].append("📊 Statistical Analysis Agent: Analyzing game scripts and matchups")
        
        try:
            enriched_data = state["enriched_data"]
            vegas = enriched_data.get('vegas_insights', {})
            weather = enriched_data.get('weather_impact', {})
            injuries = enriched_data.get('injury_alerts', {})
            
            # Statistical analysis
            stat_analysis = {
                "game_script_analysis": {},
                "weather_impact_predictions": {},
                "injury_impact_assessment": {},
                "lineup_optimization": {},
                "confidence_intervals": {}
            }
            
            # Analyze game scripts from Vegas data
            high_total_games = vegas.get('high_total_games', [])
            blowout_games = vegas.get('blowout_games', [])
            close_games = vegas.get('close_games', [])
            
            stat_analysis["game_script_analysis"] = {
                "high_scoring_games": len(high_total_games),
                "blowout_potential": len(blowout_games),
                "competitive_games": len(close_games),
                "pass_heavy_environments": len(high_total_games),
                "rush_heavy_environments": len(blowout_games)
            }
            
            # Weather impact predictions
            affected_games = weather.get('games_affected', [])
            stat_analysis["weather_impact_predictions"] = {
                "games_with_weather_impact": len(affected_games),
                "passing_game_downgrades": len([g for g in affected_games if g.get('passing_impact') == 'negative']),
                "rushing_game_upgrades": len([g for g in affected_games if g.get('rushing_impact') == 'positive']),
                "kicking_concerns": len([g for g in affected_games if g.get('wind_speed', 0) > 15])
            }
            
            # Injury impact assessment
            key_injuries = injuries.get('key_injuries', [])
            stat_analysis["injury_impact_assessment"] = {
                "fantasy_relevant_injuries": len(key_injuries),
                "qb_injuries": len([inj for inj in key_injuries if inj['position'] == 'QB']),
                "rb_injuries": len([inj for inj in key_injuries if inj['position'] == 'RB']),
                "wr_injuries": len([inj for inj in key_injuries if inj['position'] == 'WR']),
                "handcuff_opportunities": len([inj for inj in key_injuries if inj['position'] == 'RB'])
            }
            
            # Calculate confidence intervals
            data_sources_active = len(enriched_data.get('data_sources_active', {}))
            data_freshness_score = min(data_sources_active / 6.0, 1.0)  # 6 total sources
            
            stat_analysis["confidence_intervals"] = {
                "data_quality_score": data_freshness_score,
                "analysis_confidence": min(0.95, 0.6 + (data_freshness_score * 0.35)),
                "prediction_reliability": "high" if data_freshness_score > 0.8 else "medium"
            }
            
            state["statistical_analysis"] = stat_analysis
            state["agents_completed"].append("statistical_analyst")
            state["execution_log"].append(f"✅ Statistical Analysis: {stat_analysis['confidence_intervals']['prediction_reliability']} reliability")
            
        except Exception as e:
            state["execution_log"].append(f"❌ Statistical Analysis Failed: {str(e)}")
            
        return state
    
    async def _strategic_planning_agent(self, state: AgentState) -> Dict[str, Any]:
        """Agent focused on strategic recommendations and action planning."""
        
        state["execution_log"].append("🎯 Strategic Planning Agent: Generating actionable recommendations")
        
        try:
            # Synthesize insights from previous agents
            market_intel = state["market_intelligence"]
            stat_analysis = state["statistical_analysis"] 
            enriched_data = state["enriched_data"]
            
            # Strategic recommendations
            strategy = {
                "immediate_actions": [],
                "weekly_priorities": [],
                "long_term_strategy": [],
                "risk_assessment": {},
                "opportunity_ranking": []
            }
            
            # Immediate actions from market intelligence
            hot_pickups = market_intel.get("hot_pickups", [])
            for pickup in hot_pickups[:3]:  # Top 3 immediate actions
                strategy["immediate_actions"].append({
                    "action": "waiver_claim",
                    "player": pickup["player"],
                    "priority": pickup["urgency"],
                    "reasoning": f"{pickup['add_rate']}% add rate indicates high market demand"
                })
            
            # Weekly priorities from statistical analysis
            game_scripts = stat_analysis.get("game_script_analysis", {})
            if game_scripts.get("high_scoring_games", 0) > 0:
                strategy["weekly_priorities"].append({
                    "focus": "target_pass_catchers",
                    "games_count": game_scripts["high_scoring_games"],
                    "reasoning": "High total games favor passing offense players"
                })
            
            if game_scripts.get("blowout_potential", 0) > 0:
                strategy["weekly_priorities"].append({
                    "focus": "target_lead_rbs",
                    "games_count": game_scripts["blowout_potential"],
                    "reasoning": "Blowout games favor lead running backs in clock management"
                })
            
            # Risk assessment
            injury_impact = stat_analysis.get("injury_impact_assessment", {})
            weather_impact = stat_analysis.get("weather_impact_predictions", {})
            
            strategy["risk_assessment"] = {
                "injury_risk_level": "high" if injury_impact.get("fantasy_relevant_injuries", 0) > 5 else "medium",
                "weather_risk_games": weather_impact.get("games_with_weather_impact", 0),
                "overall_risk": "elevated" if injury_impact.get("qb_injuries", 0) > 0 else "normal"
            }
            
            # Opportunity ranking
            value_plays = market_intel.get("value_plays", [])
            for i, play in enumerate(value_plays[:5]):
                strategy["opportunity_ranking"].append({
                    "rank": i + 1,
                    "player": play["player"],
                    "position": play["position"],
                    "opportunity_type": "undervalued_waiver_target",
                    "value_score": play["add_rate"]
                })
            
            state["strategic_recommendations"] = strategy
            state["agents_completed"].append("strategist")
            state["execution_log"].append(f"✅ Strategic Planning: {len(strategy['immediate_actions'])} immediate actions, {len(strategy['opportunity_ranking'])} opportunities")
            
        except Exception as e:
            state["execution_log"].append(f"❌ Strategic Planning Failed: {str(e)}")
            
        return state
    
    async def _coordination_agent(self, state: AgentState) -> Dict[str, Any]:
        """Final agent that coordinates all insights into comprehensive analysis."""
        
        state["execution_log"].append("🤝 Coordination Agent: Synthesizing multi-agent analysis")
        
        try:
            # Synthesize all agent outputs
            data_analysis = state["data_analysis"]
            market_intel = state["market_intelligence"]
            stat_analysis = state["statistical_analysis"]
            strategy = state["strategic_recommendations"]
            enriched_data = state["enriched_data"]
            
            # Build comprehensive analysis using LLM
            context = f"""
MULTI-AGENT FANTASY FOOTBALL ANALYSIS SYNTHESIS

USER REQUEST: {state["user_request"]}
LEAGUE: {state["league_data"].get("name", "Unknown")}
USER: {state["username"]}

=== AGENT OUTPUTS ===

DATA COLLECTION AGENT:
- {data_analysis.get("sources_active", 0)} data sources active
- {data_analysis.get("actionable_insights", 0)} actionable insights identified
- {data_analysis.get("trending_players", 0)} trending players tracked
- {data_analysis.get("weather_affected_games", 0)} weather-affected games
- {data_analysis.get("key_injuries", 0)} key injuries monitored

MARKET INTELLIGENCE AGENT:
- Market Sentiment: {market_intel.get("market_sentiment", "neutral").upper()}
- Hot Pickups: {len(market_intel.get("hot_pickups", []))} high-demand players
- Value Plays: {len(market_intel.get("value_plays", []))} undervalued targets
- Avoid Players: {len(market_intel.get("avoid_players", []))} declining assets

STATISTICAL ANALYSIS AGENT:
- {stat_analysis.get("game_script_analysis", {}).get("high_scoring_games", 0)} high-scoring games this week
- {stat_analysis.get("game_script_analysis", {}).get("blowout_potential", 0)} potential blowouts
- Weather Impact: {stat_analysis.get("weather_impact_predictions", {}).get("games_with_weather_impact", 0)} affected games
- Analysis Confidence: {stat_analysis.get("confidence_intervals", {}).get("analysis_confidence", 0):.0%}

STRATEGIC PLANNING AGENT:
- {len(strategy.get("immediate_actions", []))} immediate actions recommended
- {len(strategy.get("weekly_priorities", []))} weekly priorities identified
- Risk Level: {strategy.get("risk_assessment", {}).get("overall_risk", "normal").upper()}
- {len(strategy.get("opportunity_ranking", []))} ranked opportunities

=== DETAILED INSIGHTS ===
{json.dumps(enriched_data.get("actionable_insights", []), indent=2)}

Please provide a comprehensive fantasy football analysis that synthesizes all agent outputs into actionable advice.
"""
            
            # Get LLM synthesis
            coordinated_analysis = await self.llm_manager.team_analysis({
                "user_data": state["user_data"],
                "league_data": state["league_data"],
                "user_roster": state["roster_data"],
                "agent_results": {
                    "data_analysis": data_analysis,
                    "market_intelligence": market_intel,
                    "statistical_analysis": stat_analysis,
                    "strategic_recommendations": strategy
                }
            })
            
            state["coordinated_analysis"] = coordinated_analysis.get("analysis", "Multi-agent analysis completed")
            
            # Calculate overall confidence
            confidence_factors = [
                data_analysis.get("sources_active", 0) / 6.0,  # Data completeness
                stat_analysis.get("confidence_intervals", {}).get("analysis_confidence", 0.7),  # Statistical confidence
                min(len(strategy.get("immediate_actions", [])) / 3.0, 1.0),  # Strategic clarity
                min(len(market_intel.get("hot_pickups", [])) / 5.0, 1.0)  # Market intelligence depth
            ]
            state["confidence_score"] = sum(confidence_factors) / len(confidence_factors)
            
            # Extract action items
            state["action_items"] = []
            for action in strategy.get("immediate_actions", [])[:5]:
                state["action_items"].append(f"{action['action']}: {action['player']} ({action['priority']} priority)")
            
            for priority in strategy.get("weekly_priorities", [])[:3]:
                state["action_items"].append(f"Weekly focus: {priority['focus']} ({priority['reasoning']})")
            
            # Evidence sources
            state["evidence_sources"] = [
                f"Real-time data from {data_analysis.get('sources_active', 0)} sources",
                f"Market intelligence on {len(market_intel.get('hot_pickups', []))} trending players",
                f"Statistical analysis of {stat_analysis.get('game_script_analysis', {}).get('high_scoring_games', 0)} games",
                f"Strategic assessment with {strategy.get('risk_assessment', {}).get('overall_risk', 'normal')} risk level"
            ]
            
            state["agents_completed"].append("coordinator")
            state["execution_log"].append(f"✅ Coordination Complete: {state['confidence_score']:.0%} confidence")
            
        except Exception as e:
            state["execution_log"].append(f"❌ Coordination Failed: {str(e)}")
            state["coordinated_analysis"] = "Multi-agent coordination encountered an error, but individual agent insights are available."
            state["confidence_score"] = 0.5
            
        return state

# Global workflow instance
fantasy_workflow = FantasyFootballWorkflow()