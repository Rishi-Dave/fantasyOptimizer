"""
Vector Database module for Fantasy Football AI Multi-Agent System.

Provides vector storage and retrieval capabilities for:
- Historical player performance patterns
- Expert analysis and insights
- Social sentiment data
- Matchup pattern recognition
- Trade value trends
"""

from .vector_manager import VectorManager
from .embeddings import EmbeddingService
from .pattern_store import PatternStore

__all__ = ['VectorManager', 'EmbeddingService', 'PatternStore']