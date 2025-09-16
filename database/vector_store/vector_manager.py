"""
Vector Database Manager for the Fantasy Football AI Multi-Agent System.

Manages vector storage and retrieval using ChromaDB for historical patterns,
expert analysis, and similarity-based recommendations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available. Vector operations will be simulated.")

from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Represents a document stored in the vector database."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: Optional[datetime] = None

class VectorManager:
    """
    Manages vector database operations for fantasy football data.
    
    Features:
    - Historical pattern storage and retrieval
    - Similarity-based player comparisons
    - Expert analysis archival
    - Trend identification through embeddings
    """
    
    def __init__(self, db_path: str = "./database/vector_store/chroma_db"):
        self.db_path = db_path
        self.embedding_service = EmbeddingService()
        self.client = None
        self.collections = {}
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Initialize ChromaDB client and collections."""
        try:
            if CHROMADB_AVAILABLE:
                self.client = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                self._create_collections()
            else:
                logger.warning("ChromaDB not available. Using simulation mode.")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            self.client = None
    
    def _create_collections(self) -> None:
        """Create vector collections for different data types."""
        if not self.client:
            return
        
        collection_configs = {
            "player_patterns": {
                "description": "Historical player performance patterns and trends",
                "metadata": {"type": "player_data", "version": "1.0"}
            },
            "expert_analysis": {
                "description": "Expert rankings, analysis, and recommendations",
                "metadata": {"type": "expert_data", "version": "1.0"}
            },
            "matchup_history": {
                "description": "Historical matchup data and outcomes",
                "metadata": {"type": "matchup_data", "version": "1.0"}
            },
            "trade_patterns": {
                "description": "Historical trade values and market patterns",
                "metadata": {"type": "trade_data", "version": "1.0"}
            },
            "social_sentiment": {
                "description": "Social media sentiment and discussion analysis",
                "metadata": {"type": "sentiment_data", "version": "1.0"}
            }
        }
        
        for name, config in collection_configs.items():
            try:
                collection = self.client.get_or_create_collection(
                    name=name,
                    metadata=config["metadata"]
                )
                self.collections[name] = collection
                logger.info(f"Initialized collection: {name}")
            except Exception as e:
                logger.error(f"Failed to create collection {name}: {str(e)}")
    
    async def store_player_pattern(self, player_name: str, pattern_data: Dict[str, Any]) -> bool:
        """Store a player performance pattern in the vector database."""
        try:
            if not self.client:
                return self._simulate_storage()
            
            # Create content for embedding
            content = self._create_player_pattern_content(player_name, pattern_data)
            
            # Generate embedding
            embedding = await self.embedding_service.embed_text(content)
            
            # Create document
            doc_id = f"player_pattern_{player_name}_{datetime.now().isoformat()}"
            metadata = {
                "player_name": player_name,
                "pattern_type": pattern_data.get("type", "general"),
                "season": pattern_data.get("season", 2023),
                "position": pattern_data.get("position", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in collection
            collection = self.collections.get("player_patterns")
            if collection:
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata]
                )
                logger.info(f"Stored player pattern for {player_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to store player pattern: {str(e)}")
            return False
    
    async def store_expert_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Store expert analysis in the vector database."""
        try:
            if not self.client:
                return self._simulate_storage()
            
            # Create content for embedding
            content = self._create_expert_analysis_content(analysis_data)
            
            # Generate embedding
            embedding = await self.embedding_service.embed_text(content)
            
            # Create document
            doc_id = f"expert_analysis_{analysis_data.get('source', 'unknown')}_{datetime.now().isoformat()}"
            metadata = {
                "source": analysis_data.get("source", "unknown"),
                "expert": analysis_data.get("expert", "unknown"),
                "analysis_type": analysis_data.get("type", "general"),
                "confidence": analysis_data.get("confidence", 0.5),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in collection
            collection = self.collections.get("expert_analysis")
            if collection:
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata]
                )
                logger.info(f"Stored expert analysis from {analysis_data.get('source')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to store expert analysis: {str(e)}")
            return False
    
    async def find_similar_patterns(self, query: str, collection_name: str, 
                                   limit: int = 5, metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find similar patterns using vector similarity search."""
        try:
            if not self.client:
                return self._simulate_similarity_search(query, limit)
            
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)
            
            # Get collection
            collection = self.collections.get(collection_name)
            if not collection:
                logger.error(f"Collection {collection_name} not found")
                return []
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=metadata_filter
            )
            
            # Format results
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity_score": 1.0 - results['distances'][0][i] if 'distances' in results else 0.9
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to find similar patterns: {str(e)}")
            return []
    
    async def find_player_comparisons(self, player_name: str, position: str = None, 
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """Find players with similar patterns to the given player."""
        try:
            # Create query for player comparison
            query = f"Player performance patterns for {player_name}"
            if position:
                query += f" at {position} position"
            
            # Filter by position if provided
            metadata_filter = {"position": position} if position else None
            
            # Search for similar patterns
            similar_patterns = await self.find_similar_patterns(
                query=query,
                collection_name="player_patterns",
                limit=limit,
                metadata_filter=metadata_filter
            )
            
            # Extract player comparisons
            comparisons = []
            for pattern in similar_patterns:
                if pattern["metadata"].get("player_name") != player_name:
                    comparisons.append({
                        "player": pattern["metadata"].get("player_name"),
                        "position": pattern["metadata"].get("position"),
                        "similarity_score": pattern["similarity_score"],
                        "pattern_type": pattern["metadata"].get("pattern_type"),
                        "season": pattern["metadata"].get("season")
                    })
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Failed to find player comparisons: {str(e)}")
            return []
    
    async def get_historical_context(self, context_query: str, 
                                   context_type: str = "all") -> List[Dict[str, Any]]:
        """Get historical context for decision making."""
        try:
            contexts = []
            
            # Determine which collections to search
            collections_to_search = []
            if context_type == "all":
                collections_to_search = list(self.collections.keys())
            else:
                collections_to_search = [context_type]
            
            # Search each relevant collection
            for collection_name in collections_to_search:
                if collection_name in self.collections:
                    results = await self.find_similar_patterns(
                        query=context_query,
                        collection_name=collection_name,
                        limit=3
                    )
                    
                    for result in results:
                        contexts.append({
                            "source": collection_name,
                            "content": result["content"],
                            "metadata": result["metadata"],
                            "relevance_score": result["similarity_score"]
                        })
            
            # Sort by relevance and return top results
            contexts.sort(key=lambda x: x["relevance_score"], reverse=True)
            return contexts[:10]
            
        except Exception as e:
            logger.error(f"Failed to get historical context: {str(e)}")
            return []
    
    def _create_player_pattern_content(self, player_name: str, pattern_data: Dict[str, Any]) -> str:
        """Create textual content for player pattern embedding."""
        content_parts = [f"Player: {player_name}"]
        
        if "position" in pattern_data:
            content_parts.append(f"Position: {pattern_data['position']}")
        
        if "performance_metrics" in pattern_data:
            metrics = pattern_data["performance_metrics"]
            content_parts.append(f"Performance metrics: {json.dumps(metrics)}")
        
        if "trends" in pattern_data:
            trends = pattern_data["trends"]
            content_parts.append(f"Trends: {json.dumps(trends)}")
        
        if "matchup_data" in pattern_data:
            content_parts.append(f"Matchup data: {json.dumps(pattern_data['matchup_data'])}")
        
        return " | ".join(content_parts)
    
    def _create_expert_analysis_content(self, analysis_data: Dict[str, Any]) -> str:
        """Create textual content for expert analysis embedding."""
        content_parts = []
        
        if "analysis" in analysis_data:
            content_parts.append(f"Analysis: {analysis_data['analysis']}")
        
        if "recommendation" in analysis_data:
            content_parts.append(f"Recommendation: {analysis_data['recommendation']}")
        
        if "reasoning" in analysis_data:
            content_parts.append(f"Reasoning: {analysis_data['reasoning']}")
        
        if "players_mentioned" in analysis_data:
            players = ", ".join(analysis_data["players_mentioned"])
            content_parts.append(f"Players: {players}")
        
        return " | ".join(content_parts)
    
    def _simulate_storage(self) -> bool:
        """Simulate vector storage when ChromaDB is not available."""
        logger.info("Simulating vector storage operation")
        return True
    
    def _simulate_similarity_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Simulate similarity search when ChromaDB is not available."""
        logger.info(f"Simulating similarity search for: {query}")
        
        # Return mock results
        mock_results = []
        for i in range(min(limit, 3)):
            mock_results.append({
                "id": f"mock_result_{i}",
                "content": f"Mock content related to {query[:50]}...",
                "metadata": {
                    "source": "simulation",
                    "confidence": 0.8 - (i * 0.1),
                    "timestamp": datetime.now().isoformat()
                },
                "similarity_score": 0.9 - (i * 0.1)
            })
        
        return mock_results
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old vector data to manage storage."""
        try:
            if not self.client:
                logger.info("Simulating cleanup operation")
                return 100  # Mock cleanup count
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            total_deleted = 0
            
            for collection_name, collection in self.collections.items():
                try:
                    # Get all documents with timestamps
                    results = collection.get(include=["metadatas"])
                    
                    ids_to_delete = []
                    for i, metadata in enumerate(results['metadatas']):
                        timestamp_str = metadata.get('timestamp')
                        if timestamp_str:
                            try:
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if timestamp < cutoff_date:
                                    ids_to_delete.append(results['ids'][i])
                            except ValueError:
                                continue
                    
                    # Delete old documents
                    if ids_to_delete:
                        collection.delete(ids=ids_to_delete)
                        total_deleted += len(ids_to_delete)
                        logger.info(f"Deleted {len(ids_to_delete)} old documents from {collection_name}")
                
                except Exception as e:
                    logger.error(f"Failed to cleanup collection {collection_name}: {str(e)}")
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics."""
        try:
            if not self.client:
                return {"status": "simulation_mode", "collections": {}}
            
            stats = {
                "status": "active",
                "collections": {}
            }
            
            for name, collection in self.collections.items():
                try:
                    count = collection.count()
                    stats["collections"][name] = {
                        "document_count": count,
                        "status": "active"
                    }
                except Exception as e:
                    stats["collections"][name] = {
                        "document_count": 0,
                        "status": f"error: {str(e)}"
                    }
            
            return stats
            
        except Exception as e:
            return {"status": f"error: {str(e)}", "collections": {}}