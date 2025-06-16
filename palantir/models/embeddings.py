"""Text embedding models and utilities."""

from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np
from openai import OpenAI
from pydantic import BaseModel


class EmbeddingVector(BaseModel):
    """Represents an embedding vector with metadata."""
    
    text: str
    vector: List[float]
    metadata: Optional[dict] = None


class BaseEmbeddingModel(ABC):
    """Base class for embedding models."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingVector:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generate embeddings for multiple texts."""
        pass


class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI's text embedding model."""
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        client: Optional[OpenAI] = None
    ):
        """Initialize the OpenAI embedding model.
        
        Args:
            model: The OpenAI model to use for embeddings.
            batch_size: Maximum number of texts to embed in one API call.
            client: Optional pre-configured OpenAI client.
        """
        self.model = model
        self.batch_size = batch_size
        self.client = client or OpenAI()
    
    async def embed_text(self, text: str) -> EmbeddingVector:
        """Generate embedding for a single text.
        
        Args:
            text: The text to embed.
            
        Returns:
            EmbeddingVector containing the text and its embedding.
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return EmbeddingVector(
            text=text,
            vector=response.data[0].embedding
        )
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List of EmbeddingVector objects.
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            
            batch_vectors = [
                EmbeddingVector(text=text, vector=data.embedding)
                for text, data in zip(batch, response.data)
            ]
            results.extend(batch_vectors)
        
        return results


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_array = np.array(a)
    b_array = np.array(b)
    
    dot_product = np.dot(a_array, b_array)
    norm_a = np.linalg.norm(a_array)
    norm_b = np.linalg.norm(b_array)
    
    return dot_product / (norm_a * norm_b) 