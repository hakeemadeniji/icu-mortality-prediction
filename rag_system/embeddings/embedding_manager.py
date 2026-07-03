"""
Embedding Manager for RAG System
Handles text embeddings for medical knowledge retrieval
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


class EmbeddingManager:
    """Manages text embeddings for RAG system."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.logger = logging.getLogger("embedding_manager")
        self.model_name = model_name
        self.model = None
        self.device = self._get_device()
        
    def _get_device(self):
        """Get the best available device for embeddings."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    def initialize(self):
        """Initialize the embedding model."""
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.logger.info(f"Embedding model loaded on {self.device}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading embedding model: {e}")
            return False
    
    def encode(self, texts: Union[str, List[str]], 
              batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """
        Encode text(s) to embeddings.
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Embeddings as numpy array
        """
        if not self.model:
            if not self.initialize():
                raise RuntimeError("Failed to initialize embedding model")
        
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error encoding texts: {e}")
            raise
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text to embedding."""
        return self.encode(text)[0]
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score
        """
        try:
            # Normalize embeddings
            norm1 = embedding1 / np.linalg.norm(embedding1)
            norm2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(norm1, norm2)
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def batch_similarity(self, query_embedding: np.ndarray, 
                       document_embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate similarity between query and multiple documents.
        
        Args:
            query_embedding: Query embedding
            document_embeddings: Document embeddings
            
        Returns:
            Array of similarity scores
        """
        try:
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norms = document_embeddings / np.linalg.norm(document_embeddings, axis=1, keepdims=True)
            
            # Calculate cosine similarities
            similarities = np.dot(doc_norms, query_norm)
            
            return similarities
            
        except Exception as e:
            self.logger.error(f"Error calculating batch similarity: {e}")
            return np.zeros(len(document_embeddings))
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if not self.model:
            if not self.initialize():
                return 0
        
        return self.model.get_sentence_embedding_dimension()
    
    def is_ready(self) -> bool:
        """Check if the embedding manager is ready."""
        return self.model is not None