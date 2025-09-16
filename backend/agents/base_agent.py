"""
Base Agent class for the Fantasy Football AI Multi-Agent System.

Provides common functionality and interfaces for all specialized agents.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of agents in the system."""
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis" 
    DECISION = "decision"
    COORDINATOR = "coordinator"

class ConfidenceLevel(Enum):
    """Confidence levels for agent recommendations."""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

@dataclass
class AgentResult:
    """Standardized result format for all agents."""
    agent_id: str
    agent_type: AgentType
    data: Dict[str, Any]
    confidence: float
    reasoning: str
    sources: List[str]
    timestamp: datetime
    execution_time_ms: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AgentContext:
    """Context passed between agents in the workflow."""
    league_id: str
    username: str
    user_id: str
    query: str
    query_type: str
    league_settings: Dict[str, Any]
    roster_data: Dict[str, Any]
    historical_data: Optional[Dict[str, Any]] = None
    real_time_data: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """
    Abstract base class for all fantasy football agents.
    
    Provides common functionality including:
    - Standardized input/output formats
    - Logging and monitoring
    - Error handling
    - Performance tracking
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType, name: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self._performance_metrics = {
            "calls_made": 0,
            "avg_execution_time": 0.0,
            "success_rate": 0.0,
            "errors": []
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Main execution method for the agent.
        
        Handles timing, error handling, and result formatting.
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting execution for query: {context.query_type}")
            
            # Validate input context
            self._validate_context(context)
            
            # Execute the agent's core logic
            result_data, confidence, reasoning, sources = await self._process(context)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create standardized result
            result = AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                data=result_data,
                confidence=confidence,
                reasoning=reasoning,
                sources=sources,
                timestamp=datetime.now(),
                execution_time_ms=execution_time
            )
            
            # Update performance metrics
            self._update_metrics(execution_time, success=True)
            
            self.logger.info(f"Execution completed in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_metrics(execution_time, success=False, error=str(e))
            self.logger.error(f"Execution failed: {str(e)}")
            
            # Return error result
            return AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Agent execution failed: {str(e)}",
                sources=[],
                timestamp=datetime.now(),
                execution_time_ms=execution_time,
                metadata={"error": True}
            )
    
    @abstractmethod
    async def _process(self, context: AgentContext) -> tuple[Dict[str, Any], float, str, List[str]]:
        """
        Core processing logic for the agent.
        
        Must be implemented by each specific agent.
        
        Returns:
            tuple: (result_data, confidence, reasoning, sources)
        """
        pass
    
    def _validate_context(self, context: AgentContext) -> None:
        """Validate the input context for the agent."""
        required_fields = ['league_id', 'username', 'user_id', 'query', 'query_type']
        
        for field in required_fields:
            if not getattr(context, field, None):
                raise ValueError(f"Missing required context field: {field}")
    
    def _update_metrics(self, execution_time: float, success: bool, error: str = None) -> None:
        """Update performance metrics for the agent."""
        self._performance_metrics["calls_made"] += 1
        
        # Update average execution time
        prev_avg = self._performance_metrics["avg_execution_time"]
        calls = self._performance_metrics["calls_made"]
        self._performance_metrics["avg_execution_time"] = (prev_avg * (calls - 1) + execution_time) / calls
        
        # Update success rate
        if success:
            success_count = int(self._performance_metrics["success_rate"] * (calls - 1)) + 1
        else:
            success_count = int(self._performance_metrics["success_rate"] * (calls - 1))
            if error:
                self._performance_metrics["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error
                })
        
        self._performance_metrics["success_rate"] = success_count / calls
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics for the agent."""
        return self._performance_metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self._performance_metrics = {
            "calls_made": 0,
            "avg_execution_time": 0.0,
            "success_rate": 0.0,
            "errors": []
        }
    
    @property
    def is_healthy(self) -> bool:
        """Check if the agent is operating within healthy parameters."""
        metrics = self._performance_metrics
        
        # Consider healthy if success rate > 80% and avg execution time < 5 seconds
        return (metrics["success_rate"] > 0.8 and 
                metrics["avg_execution_time"] < 5000 and
                len(metrics["errors"]) < 10)

class LLMMixin:
    """Mixin class for agents that use LLM capabilities."""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.llm_config = llm_config or {}
        self.primary_model = self.llm_config.get("primary_model", "claude-3-5-sonnet-20241022")
        self.secondary_model = self.llm_config.get("secondary_model", "gpt-4o-mini")
    
    async def _query_llm(self, prompt: str, model: str = None, **kwargs) -> str:
        """Query LLM with the given prompt."""
        # This will be implemented with actual LLM clients
        # For now, return a placeholder
        return f"LLM response for: {prompt[:100]}..."

class DataMixin:
    """Mixin class for agents that need data access capabilities."""
    
    def __init__(self, data_sources: Dict[str, Any] = None):
        self.data_sources = data_sources or {}
    
    async def _fetch_sleeper_data(self, endpoint: str, **params) -> Dict[str, Any]:
        """Fetch data from Sleeper API."""
        # Implementation will be added
        pass
    
    async def _fetch_external_data(self, source: str, endpoint: str, **params) -> Dict[str, Any]:
        """Fetch data from external sources."""
        # Implementation will be added
        pass