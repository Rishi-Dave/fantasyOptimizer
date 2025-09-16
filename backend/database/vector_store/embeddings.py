"""
Embedding service for generating vector embeddings from text.
"""

import asyncio
import logging
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating embeddings from text using sentence transformers.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize the embedding model."""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Initialized embedding model: {self.model_name}")
            else:
                logger.warning("sentence-transformers not available, using fallback embeddings")
                
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        
        if not self.model and SENTENCE_TRANSFORMERS_AVAILABLE:
            await self.initialize()
            
        try:
            if self.model:
                # Use sentence transformers
                embedding = self.model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
            else:
                # Fallback to simple hash-based embedding
                return self._generate_fallback_embedding(text)
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._generate_fallback_embedding(text)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        
        if not self.model and SENTENCE_TRANSFORMERS_AVAILABLE:
            await self.initialize()
            
        try:
            if self.model:
                embeddings = self.model.encode(texts, convert_to_tensor=False)
                return [emb.tolist() for emb in embeddings]
            else:
                return [self._generate_fallback_embedding(text) for text in texts]
                
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [self._generate_fallback_embedding(text) for text in texts]
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate simple fallback embedding when sentence transformers unavailable."""
        
        # Simple hash-based embedding (not ideal but functional)
        text_lower = text.lower()
        
        # Create a simple 384-dimensional vector based on text characteristics
        embedding = [0.0] * self.dimension
        
        # Use text characteristics to populate embedding
        for i, char in enumerate(text_lower[:self.dimension]):
            embedding[i] = (ord(char) - 96) / 26.0  # Normalize to 0-1
            
        # Add some text statistics
        if len(text) > 0:
            embedding[0] = len(text) / 1000.0  # Text length
            embedding[1] = text_lower.count(' ') / len(text)  # Word density
            embedding[2] = sum(1 for c in text_lower if c.isdigit()) / len(text)  # Number density
            
        # Normalize the vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = [x / norm for x in embedding]
            
        return embedding
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        return self.dimension

# Global embedding service
embedding_service = EmbeddingService()