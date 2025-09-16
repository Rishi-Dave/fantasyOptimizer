"""
Embedding Service for the Fantasy Football AI Multi-Agent System.

Provides text embedding capabilities using various embedding models
for vector similarity search and pattern recognition.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("SentenceTransformers not available. Using mock embeddings.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings for vector storage.
    
    Supports multiple embedding models:
    - SentenceTransformers (local)
    - OpenAI text-embedding-ada-002 (API)
    - Mock embeddings (fallback)
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_openai: bool = False):
        self.model_name = model_name
        self.use_openai = use_openai
        self.model = None
        self.embedding_dimension = 384  # Default for all-MiniLM-L6-v2
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the embedding model."""
        try:
            if self.use_openai and OPENAI_AVAILABLE:
                self.embedding_dimension = 1536  # OpenAI ada-002 dimension
                logger.info("Using OpenAI embeddings")
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                self.model = SentenceTransformer(self.model_name)
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Initialized SentenceTransformer model: {self.model_name}")
            else:
                logger.warning("No embedding models available. Using mock embeddings.")
                self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            self.model = None
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            if self.use_openai and OPENAI_AVAILABLE:
                return await self._embed_with_openai(text)
            elif self.model is not None:
                return await self._embed_with_sentence_transformer(text)
            else:
                return self._generate_mock_embedding(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return self._generate_mock_embedding(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            if self.use_openai and OPENAI_AVAILABLE:
                return await self._embed_batch_with_openai(texts)
            elif self.model is not None:
                return await self._embed_batch_with_sentence_transformer(texts)
            else:
                return [self._generate_mock_embedding(text) for text in texts]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            return [self._generate_mock_embedding(text) for text in texts]
    
    async def _embed_with_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            return self._generate_mock_embedding(text)
    
    async def _embed_batch_with_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts using OpenAI API."""
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=texts
            )
            return [item['embedding'] for item in response['data']]
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {str(e)}")
            return [self._generate_mock_embedding(text) for text in texts]
    
    async def _embed_with_sentence_transformer(self, text: str) -> List[float]:
        """Generate embedding using SentenceTransformer."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                lambda: self.model.encode([text])[0]
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"SentenceTransformer embedding failed: {str(e)}")
            return self._generate_mock_embedding(text)
    
    async def _embed_batch_with_sentence_transformer(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts using SentenceTransformer."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts)
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"SentenceTransformer batch embedding failed: {str(e)}")
            return [self._generate_mock_embedding(text) for text in texts]
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding based on text hash."""
        # Create deterministic but varied embedding based on text
        hash_value = hash(text)
        np.random.seed(abs(hash_value) % 2**32)
        
        # Generate random vector with appropriate dimension
        embedding = np.random.normal(0, 1, self.embedding_dimension)
        
        # Normalize to unit vector
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {str(e)}")
            return 0.0
    
    async def find_most_similar(self, query_embedding: List[float], 
                               candidate_embeddings: List[List[float]]) -> List[Tuple[int, float]]:
        """Find most similar embeddings to the query."""
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities
        except Exception as e:
            logger.error(f"Failed to find most similar: {str(e)}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model."""
        return {
            "model_name": self.model_name,
            "use_openai": self.use_openai,
            "embedding_dimension": self.embedding_dimension,
            "model_available": self.model is not None or (self.use_openai and OPENAI_AVAILABLE),
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "openai_available": OPENAI_AVAILABLE
        }

class FantasyEmbeddingService(EmbeddingService):
    """
    Specialized embedding service for fantasy football content.
    
    Provides fantasy-specific text preprocessing and embedding strategies.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_openai: bool = False):
        super().__init__(model_name, use_openai)
        self.fantasy_keywords = self._load_fantasy_keywords()
    
    def _load_fantasy_keywords(self) -> Dict[str, List[str]]:
        """Load fantasy football specific keywords for better embeddings."""
        return {
            "positions": ["QB", "RB", "WR", "TE", "K", "DEF", "quarterback", "running back", "wide receiver", "tight end"],
            "stats": ["points", "yards", "touchdowns", "targets", "carries", "receptions", "fantasy points"],
            "analysis": ["start", "sit", "trade", "waiver", "pickup", "drop", "buy low", "sell high"],
            "matchups": ["vs", "against", "defense", "matchup", "favorable", "difficult"],
            "trends": ["trending up", "trending down", "breakout", "regression", "consistent", "boom", "bust"],
            "timing": ["this week", "ROS", "playoff", "championship", "rest of season"]
        }
    
    def preprocess_fantasy_text(self, text: str) -> str:
        """Preprocess text for better fantasy football embeddings."""
        # Convert common abbreviations
        text = text.replace(" vs ", " versus ")
        text = text.replace(" w/ ", " with ")
        text = text.replace(" w/o ", " without ")
        
        # Expand position abbreviations
        position_expansions = {
            "QB": "quarterback",
            "RB": "running back", 
            "WR": "wide receiver",
            "TE": "tight end"
        }
        
        for abbrev, full in position_expansions.items():
            text = text.replace(f" {abbrev} ", f" {abbrev} {full} ")
        
        # Add context markers for better embeddings
        if any(keyword in text.lower() for keyword in ["start", "sit"]):
            text = f"lineup decision: {text}"
        elif any(keyword in text.lower() for keyword in ["trade", "deal"]):
            text = f"trade analysis: {text}"
        elif any(keyword in text.lower() for keyword in ["waiver", "pickup"]):
            text = f"waiver wire: {text}"
        
        return text
    
    async def embed_fantasy_text(self, text: str) -> List[float]:
        """Generate embedding for fantasy football text with preprocessing."""
        processed_text = self.preprocess_fantasy_text(text)
        return await self.embed_text(processed_text)
    
    async def embed_player_profile(self, player_data: Dict[str, Any]) -> List[float]:
        """Generate embedding for a player profile."""
        # Create comprehensive text representation
        profile_parts = []
        
        if "name" in player_data:
            profile_parts.append(f"Player: {player_data['name']}")
        
        if "position" in player_data:
            profile_parts.append(f"Position: {player_data['position']}")
        
        if "team" in player_data:
            profile_parts.append(f"Team: {player_data['team']}")
        
        if "stats" in player_data:
            stats_text = ", ".join([f"{k}: {v}" for k, v in player_data["stats"].items()])
            profile_parts.append(f"Stats: {stats_text}")
        
        if "trends" in player_data:
            trends_text = ", ".join(player_data["trends"])
            profile_parts.append(f"Trends: {trends_text}")
        
        if "analysis" in player_data:
            profile_parts.append(f"Analysis: {player_data['analysis']}")
        
        profile_text = " | ".join(profile_parts)
        return await self.embed_fantasy_text(profile_text)
    
    async def embed_matchup_analysis(self, matchup_data: Dict[str, Any]) -> List[float]:
        """Generate embedding for matchup analysis."""
        matchup_parts = []
        
        if "player" in matchup_data:
            matchup_parts.append(f"Player: {matchup_data['player']}")
        
        if "opponent" in matchup_data:
            matchup_parts.append(f"Opponent: {matchup_data['opponent']}")
        
        if "defense_rank" in matchup_data:
            matchup_parts.append(f"Defense rank: {matchup_data['defense_rank']}")
        
        if "game_script" in matchup_data:
            matchup_parts.append(f"Game script: {matchup_data['game_script']}")
        
        if "weather" in matchup_data:
            matchup_parts.append(f"Weather: {matchup_data['weather']}")
        
        if "analysis" in matchup_data:
            matchup_parts.append(f"Analysis: {matchup_data['analysis']}")
        
        matchup_text = " | ".join(matchup_parts)
        return await self.embed_fantasy_text(matchup_text)