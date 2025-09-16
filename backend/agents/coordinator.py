"""
Agent Coordinator using LangGraph for orchestrating multi-agent workflows.

This module manages the complex interactions between different agents,
routing queries to appropriate specialists and synthesizing results.
"""

import asyncio
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import logging
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentType
from .data_collection import MarketIntelligenceAgent, StatisticalAnalysisAgent
from .analysis import MatchupEvaluationAgent, InjuryNewsAgent, TradeIntelligenceAgent
from .decision import LineupOptimizationAgent, WaiverWireAgent, ChampionshipStrategyAgent

logger = logging.getLogger(__name__)

@dataclass
class WorkflowState:
    """State object passed through the LangGraph workflow."""
    context: AgentContext
    agent_results: Dict[str, AgentResult]
    current_step: str
    messages: List[BaseMessage]
    final_result: Optional[Dict[str, Any]] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class AgentCoordinator:
    """
    Coordinates multiple agents using LangGraph for complex fantasy football analysis.
    
    Features:
    - Intelligent routing based on query type
    - Parallel agent execution for efficiency
    - Result synthesis and confidence scoring
    - Error handling and fallback strategies
    """
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.llm_config = llm_config or {}
        self.agents = self._initialize_agents()
        self.workflow = self._build_workflow()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all specialized agents."""
        agents = {}
        
        # Data Collection Agents
        agents["market_intelligence"] = MarketIntelligenceAgent(
            agent_id="market_intel_001",
            llm_config=self.llm_config
        )
        agents["statistical_analysis"] = StatisticalAnalysisAgent(
            agent_id="stats_analysis_001", 
            llm_config=self.llm_config
        )
        
        # Analysis Agents
        agents["matchup_evaluation"] = MatchupEvaluationAgent(
            agent_id="matchup_eval_001",
            llm_config=self.llm_config
        )
        agents["injury_news"] = InjuryNewsAgent(
            agent_id="injury_news_001",
            llm_config=self.llm_config
        )
        agents["trade_intelligence"] = TradeIntelligenceAgent(
            agent_id="trade_intel_001",
            llm_config=self.llm_config
        )
        
        # Decision Agents
        agents["lineup_optimization"] = LineupOptimizationAgent(
            agent_id="lineup_opt_001",
            llm_config=self.llm_config
        )
        agents["waiver_wire"] = WaiverWireAgent(
            agent_id="waiver_wire_001",
            llm_config=self.llm_config
        )
        agents["championship_strategy"] = ChampionshipStrategyAgent(
            agent_id="championship_001",
            llm_config=self.llm_config
        )
        
        return agents
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for agent coordination."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each step
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("collect_data", self._collect_data)
        workflow.add_node("analyze_situation", self._analyze_situation)
        workflow.add_node("make_decisions", self._make_decisions)
        workflow.add_node("synthesize_results", self._synthesize_results)
        
        # Define the workflow edges
        workflow.set_entry_point("analyze_query")
        
        workflow.add_edge("analyze_query", "collect_data")
        workflow.add_edge("collect_data", "analyze_situation")
        workflow.add_edge("analyze_situation", "make_decisions")
        workflow.add_edge("make_decisions", "synthesize_results")
        workflow.add_edge("synthesize_results", END)
        
        return workflow.compile()
    
    async def process_query(self, context: AgentContext) -> Dict[str, Any]:
        """
        Main entry point for processing fantasy football queries.
        
        Orchestrates the multi-agent workflow and returns synthesized results.
        """
        try:
            # Initialize workflow state
            initial_state = WorkflowState(
                context=context,
                agent_results={},
                current_step="analyze_query",
                messages=[HumanMessage(content=context.query)]
            )
            
            # Execute the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            return result["final_result"]
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis": "I encountered an error while analyzing your request. Please try again.",
                "confidence": 0.0,
                "agent_results": {}
            }
    
    async def _analyze_query(self, state: WorkflowState) -> WorkflowState:
        """Analyze the incoming query to determine which agents to activate."""
        context = state.context
        query_lower = context.query.lower()
        
        # Determine query type and required agents
        query_analysis = {
            "query_type": self._classify_query(query_lower),
            "required_agents": self._select_agents(query_lower),
            "priority": self._determine_priority(query_lower),
            "complexity": self._assess_complexity(query_lower)
        }
        
        # Update context with analysis
        context.query_type = query_analysis["query_type"]
        
        # Store analysis results
        state.agent_results["query_analysis"] = AgentResult(
            agent_id="coordinator",
            agent_type=AgentType.COORDINATOR,
            data=query_analysis,
            confidence=0.95,
            reasoning="Query classification based on keyword analysis and pattern matching",
            sources=["internal_classifier"],
            timestamp=datetime.now(),
            execution_time_ms=5.0
        )
        
        state.current_step = "collect_data"
        return state
    
    async def _collect_data(self, state: WorkflowState) -> WorkflowState:
        """Collect data from relevant sources using data collection agents."""
        context = state.context
        query_analysis = state.agent_results["query_analysis"].data
        required_agents = query_analysis["required_agents"]
        
        # Run data collection agents in parallel
        data_tasks = []
        
        if "market_intelligence" in required_agents:
            data_tasks.append(self.agents["market_intelligence"].execute(context))
        
        if "statistical_analysis" in required_agents:
            data_tasks.append(self.agents["statistical_analysis"].execute(context))
        
        # Execute data collection tasks
        if data_tasks:
            data_results = await asyncio.gather(*data_tasks, return_exceptions=True)
            
            for result in data_results:
                if isinstance(result, AgentResult):
                    state.agent_results[result.agent_id] = result
                elif isinstance(result, Exception):
                    state.errors.append(f"Data collection failed: {str(result)}")
        
        state.current_step = "analyze_situation"
        return state
    
    async def _analyze_situation(self, state: WorkflowState) -> WorkflowState:
        """Analyze the situation using specialized analysis agents."""
        context = state.context
        query_analysis = state.agent_results["query_analysis"].data
        required_agents = query_analysis["required_agents"]
        
        # Run analysis agents in parallel
        analysis_tasks = []
        
        if "matchup_evaluation" in required_agents:
            analysis_tasks.append(self.agents["matchup_evaluation"].execute(context))
        
        if "injury_news" in required_agents:
            analysis_tasks.append(self.agents["injury_news"].execute(context))
        
        if "trade_intelligence" in required_agents:
            analysis_tasks.append(self.agents["trade_intelligence"].execute(context))
        
        # Execute analysis tasks
        if analysis_tasks:
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            for result in analysis_results:
                if isinstance(result, AgentResult):
                    state.agent_results[result.agent_id] = result
                elif isinstance(result, Exception):
                    state.errors.append(f"Analysis failed: {str(result)}")
        
        state.current_step = "make_decisions"
        return state
    
    async def _make_decisions(self, state: WorkflowState) -> WorkflowState:
        """Make decisions using decision engine agents."""
        context = state.context
        query_analysis = state.agent_results["query_analysis"].data
        required_agents = query_analysis["required_agents"]
        
        # Run decision agents in parallel
        decision_tasks = []
        
        if "lineup_optimization" in required_agents:
            decision_tasks.append(self.agents["lineup_optimization"].execute(context))
        
        if "waiver_wire" in required_agents:
            decision_tasks.append(self.agents["waiver_wire"].execute(context))
        
        if "championship_strategy" in required_agents:
            decision_tasks.append(self.agents["championship_strategy"].execute(context))
        
        # Execute decision tasks
        if decision_tasks:
            decision_results = await asyncio.gather(*decision_tasks, return_exceptions=True)
            
            for result in decision_results:
                if isinstance(result, AgentResult):
                    state.agent_results[result.agent_id] = result
                elif isinstance(result, Exception):
                    state.errors.append(f"Decision making failed: {str(result)}")
        
        state.current_step = "synthesize_results"
        return state
    
    async def _synthesize_results(self, state: WorkflowState) -> WorkflowState:
        """Synthesize results from all agents into a cohesive response."""
        # Calculate overall confidence based on agent results
        confidences = [result.confidence for result in state.agent_results.values() 
                      if result.agent_id != "coordinator"]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Synthesize reasoning from all agents
        reasoning_parts = []
        for result in state.agent_results.values():
            if result.agent_id != "coordinator" and result.reasoning:
                reasoning_parts.append(f"{result.agent_id}: {result.reasoning}")
        
        combined_reasoning = "\n".join(reasoning_parts)
        
        # Extract key data points
        key_insights = self._extract_key_insights(state.agent_results)
        
        # Generate final response
        state.final_result = {
            "success": True,
            "analysis": self._generate_final_analysis(state),
            "confidence": overall_confidence,
            "key_insights": key_insights,
            "agent_results": {k: v.data for k, v in state.agent_results.items()},
            "reasoning": combined_reasoning,
            "execution_summary": {
                "agents_executed": list(state.agent_results.keys()),
                "total_execution_time": sum(r.execution_time_ms for r in state.agent_results.values()),
                "errors": state.errors
            }
        }
        
        return state
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query to determine processing approach."""
        query_patterns = {
            "start_sit": ["start", "sit", "lineup", "bench", "play"],
            "waiver": ["waiver", "pickup", "drop", "add", "claim"],
            "trade": ["trade", "deal", "swap", "exchange", "offer"],
            "matchup": ["matchup", "opponent", "defense", "against"],
            "injury": ["injury", "hurt", "questionable", "doubtful", "out"],
            "analysis": ["analyze", "team", "grade", "review", "assess"],
            "strategy": ["strategy", "plan", "championship", "playoff"]
        }
        
        for query_type, keywords in query_patterns.items():
            if any(keyword in query for keyword in keywords):
                return query_type
        
        return "general"
    
    def _select_agents(self, query: str) -> List[str]:
        """Select which agents should be activated based on the query."""
        query_type = self._classify_query(query)
        
        agent_mappings = {
            "start_sit": ["statistical_analysis", "matchup_evaluation", "injury_news", "lineup_optimization"],
            "waiver": ["market_intelligence", "statistical_analysis", "waiver_wire"],
            "trade": ["statistical_analysis", "trade_intelligence", "championship_strategy"],
            "matchup": ["statistical_analysis", "matchup_evaluation"],
            "injury": ["injury_news", "statistical_analysis"],
            "analysis": ["market_intelligence", "statistical_analysis", "matchup_evaluation"],
            "strategy": ["championship_strategy", "statistical_analysis"],
            "general": ["market_intelligence", "statistical_analysis", "matchup_evaluation"]
        }
        
        return agent_mappings.get(query_type, ["statistical_analysis"])
    
    def _determine_priority(self, query: str) -> str:
        """Determine the priority level of the query."""
        urgent_keywords = ["urgent", "now", "today", "tonight", "emergency"]
        high_keywords = ["important", "championship", "playoff", "must"]
        
        if any(keyword in query for keyword in urgent_keywords):
            return "urgent"
        elif any(keyword in query for keyword in high_keywords):
            return "high"
        else:
            return "normal"
    
    def _assess_complexity(self, query: str) -> str:
        """Assess the complexity of the query."""
        complex_keywords = ["strategy", "championship", "multiple", "compare", "analyze"]
        
        if any(keyword in query for keyword in complex_keywords):
            return "high"
        elif len(query.split()) > 10:
            return "medium"
        else:
            return "low"
    
    def _extract_key_insights(self, agent_results: Dict[str, AgentResult]) -> List[str]:
        """Extract key insights from agent results."""
        insights = []
        
        for result in agent_results.values():
            if result.agent_id != "coordinator" and result.data:
                # Extract key points from each agent's data
                if "recommendations" in result.data:
                    insights.extend(result.data["recommendations"])
                if "key_insight" in result.data:
                    insights.append(result.data["key_insight"])
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_final_analysis(self, state: WorkflowState) -> str:
        """Generate the final analysis text from all agent results."""
        # This would use an LLM to synthesize the results
        # For now, return a structured summary
        
        query_type = state.context.query_type
        insights = self._extract_key_insights(state.agent_results)
        
        analysis = f"Based on your {query_type} query, here's my analysis:\n\n"
        
        if insights:
            analysis += "Key Insights:\n"
            for i, insight in enumerate(insights, 1):
                analysis += f"{i}. {insight}\n"
        
        analysis += f"\nI analyzed your request using {len(state.agent_results) - 1} specialized agents "
        analysis += f"with an overall confidence of {state.agent_results.get('query_analysis', type('obj', (object,), {'data': {'complexity': 'medium'}})).data.get('complexity', 'medium')} complexity."
        
        return analysis