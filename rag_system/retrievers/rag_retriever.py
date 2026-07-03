"""
RAG Retriever - Main retrieval system for medical knowledge
"""

import logging
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from rag_system.vector_db.chroma_manager import ChromaManager
from rag_system.embeddings.embedding_manager import EmbeddingManager


class RAGRetriever:
    """
    Retrieval-Augmented Generation system for medical knowledge.
    
    Combines vector database search with embedding-based similarity
    to retrieve relevant medical literature and guidelines.
    """
    
    def __init__(self, 
                 vector_db_path: str = "./rag_system/vector_db/chroma",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.logger = logging.getLogger("rag_retriever")
        self.vector_db = ChromaManager(vector_db_path)
        self.embedding_manager = EmbeddingManager(embedding_model)
        self._ready = False
        
    async def initialize(self):
        """Initialize the RAG system."""
        try:
            self.logger.info("Initializing RAG Retriever...")
            
            # Initialize vector database
            self.vector_db.initialize_collection()
            
            # Initialize embedding manager
            if not self.embedding_manager.initialize():
                raise RuntimeError("Failed to initialize embedding manager")
            
            # Load sample medical knowledge if empty
            stats = self.vector_db.get_collection_stats()
            if stats.get("document_count", 0) == 0:
                await self._load_sample_knowledge()
            
            self._ready = True
            self.logger.info("RAG Retriever initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing RAG Retriever: {e}")
            raise
    
    async def _load_sample_knowledge(self):
        """Load sample medical knowledge into the vector database."""
        self.logger.info("Loading sample medical knowledge...")
        
        sample_documents = [
            "Sepsis is a life-threatening condition that arises when the body's response to infection causes injury to its own tissues and organs.",
            "Acute respiratory distress syndrome (ARDS) is a type of respiratory failure characterized by rapid onset of widespread inflammation in the lungs.",
            "Septic shock is a subset of sepsis in which particularly profound circulatory, cellular, and metabolic abnormalities are associated with a greater risk of mortality than sepsis alone.",
            "Mechanical ventilation is a method to mechanically assist or replace spontaneous breathing when patients cannot breathe sufficiently on their own.",
            "Vasopressors are medications that cause vasoconstriction and are used to treat hypotension in septic shock.",
            "Acute kidney injury (AKI) is an abrupt loss of kidney function that develops within 7 days.",
            "Multiple organ dysfunction syndrome (MODS) is the presence of altered organ function in an acutely ill patient requiring medical intervention.",
            "ICU mortality risk factors include age, comorbidities, severity of illness, and organ failure.",
            "APACHE II score is a severity-of-disease classification system for ICU patients.",
            "SOFA score is used to track a patient's status during a stay in an intensive care unit."
        ]
        
        sample_metadata = [
            {"category": "condition", "severity": "high"},
            {"category": "condition", "severity": "high"},
            {"category": "condition", "severity": "critical"},
            {"category": "treatment", "type": "ventilation"},
            {"category": "treatment", "type": "medication"},
            {"category": "condition", "severity": "high"},
            {"category": "condition", "severity": "critical"},
            {"category": "risk_factor", "domain": "prognosis"},
            {"category": "scoring", "system": "apache"},
            {"category": "scoring", "system": "sofa"}
        ]
        
        self.vector_db.add_documents(sample_documents, sample_metadata)
        self.logger.info(f"Loaded {len(sample_documents)} sample documents")
    
    async def retrieve(self, query: str, top_k: int = 5, 
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant medical knowledge for a query.
        
        Args:
            query: Query text
            top_k: Number of results to retrieve
            filters: Optional metadata filters
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        if not self._ready:
            await self.initialize()
        
        try:
            # Query vector database
            results = self.vector_db.query(query, n_results=top_k, where=filters)
            
            # Format results
            formatted_results = []
            if results and 'documents' in results and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                for i, doc in enumerate(documents):
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "score": 1.0 / (1.0 + distances[i]) if i < len(distances) else 0.0,
                        "rank": i + 1
                    })
            
            self.logger.info(f"Retrieved {len(formatted_results)} documents for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge: {e}")
            return []
    
    async def retrieve_with_context(self, query: str, context: Dict[str, Any],
                                   top_k: int = 5) -> Dict[str, Any]:
        """
        Retrieve knowledge with additional context.
        
        Args:
            query: Query text
            context: Additional context (patient data, etc.)
            top_k: Number of results to retrieve
            
        Returns:
            Retrieved knowledge with context-aware ranking
        """
        # Enhance query with context
        enhanced_query = self._enhance_query(query, context)
        
        # Retrieve knowledge
        results = await self.retrieve(enhanced_query, top_k)
        
        # Re-rank based on context
        reranked_results = self._rerank_results(results, context)
        
        return {
            "query": query,
            "enhanced_query": enhanced_query,
            "results": reranked_results,
            "context": context
        }
    
    def _enhance_query(self, query: str, context: Dict[str, Any]) -> str:
        """Enhance query with context information."""
        enhanced_parts = [query]
        
        # Add relevant context to query
        if context.get("primary_condition"):
            enhanced_parts.append(f"related to {context['primary_condition']}")
        
        if context.get("age"):
            enhanced_parts.append(f"for age {context['age']}")
        
        return " ".join(enhanced_parts)
    
    def _rerank_results(self, results: List[Dict[str, Any]], 
                       context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Re-rank results based on context."""
        # Simple re-ranking based on metadata matching
        for result in results:
            metadata = result.get("metadata", {})
            boost = 1.0
            
            # Boost results matching context
            if context.get("category") and metadata.get("category") == context["category"]:
                boost *= 1.2
            
            if context.get("severity") and metadata.get("severity") == context["severity"]:
                boost *= 1.1
            
            result["score"] *= boost
        
        # Sort by adjusted score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Re-assign ranks
        for i, result in enumerate(results):
            result["rank"] = i + 1
        
        return results
    
    async def add_knowledge(self, documents: List[str], 
                           metadata: List[Dict[str, Any]]):
        """
        Add new knowledge to the system.
        
        Args:
            documents: List of document texts
            metadata: List of metadata dictionaries
        """
        try:
            self.vector_db.add_documents(documents, metadata)
            self.logger.info(f"Added {len(documents)} new documents to knowledge base")
        except Exception as e:
            self.logger.error(f"Error adding knowledge: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        try:
            db_stats = self.vector_db.get_collection_stats()
            embedding_dim = self.embedding_manager.get_embedding_dimension()
            
            return {
                "vector_database": db_stats,
                "embedding_model": self.embedding_manager.model_name,
                "embedding_dimension": embedding_dim,
                "device": self.embedding_manager.device,
                "ready": self._ready
            }
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    def is_ready(self) -> bool:
        """Check if RAG system is ready."""
        return self._ready
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up RAG Retriever...")
        self._ready = False