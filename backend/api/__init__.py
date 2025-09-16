"""
Advanced Analytics API for Fantasy Football AI Multi-Agent System.
"""

from .multi_agent_server import MultiAgentFantasyServer
from .endpoints import router
from .middleware import setup_middleware

__all__ = ['MultiAgentFantasyServer', 'router', 'setup_middleware']