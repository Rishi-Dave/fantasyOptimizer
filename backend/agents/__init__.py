"""
Fantasy Football AI Multi-Agent System

This module contains specialized agents for comprehensive fantasy football analysis.
Each agent focuses on specific domains to provide expert-level insights.
"""

from .base_agent import BaseAgent
from .coordinator import AgentCoordinator
from .data_collection import MarketIntelligenceAgent, StatisticalAnalysisAgent
from .analysis import MatchupEvaluationAgent, InjuryNewsAgent, TradeIntelligenceAgent
from .decision import LineupOptimizationAgent, WaiverWireAgent, ChampionshipStrategyAgent

__all__ = [
    'BaseAgent',
    'AgentCoordinator', 
    'MarketIntelligenceAgent',
    'StatisticalAnalysisAgent',
    'MatchupEvaluationAgent',
    'InjuryNewsAgent',
    'TradeIntelligenceAgent',
    'LineupOptimizationAgent',
    'WaiverWireAgent',
    'ChampionshipStrategyAgent'
]