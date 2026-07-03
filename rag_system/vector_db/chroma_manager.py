"""
ChromaDB Vector Database Manager for RAG System
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import json


class ChromaManager:
    """Manages ChromaDB vector database for RAG system."""
    
    def __init__(self, persist_directory: str = "./rag_system/vector_db/chroma"):
        self.logger = logging.getLogger("chroma_manager")
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection for medical knowledge
        self.collection_name = "medical_knowledge"
        self.collection = None
        
    def initialize_collection(self):
        """Initialize or get the medical knowledge collection."""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Medical knowledge for ICU mortality prediction"}
            )
            self.logger.info(f"Collection '{self.collection_name}' ready")
        except Exception as e:
            self.logger.error(f"Error initializing collection: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], 
                     ids: Optional[List[str]] = None):
        """
        Add documents to the vector database.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
        """
        if not self.collection:
            self.initialize_collection()
        
        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to collection")
            
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            raise
    
    def query(self, query_text: str, n_results: int = 5, 
             where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the vector database.
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Query results
        """
        if not self.collection:
            self.initialize_collection()
        
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error querying collection: {e}")
            raise
    
    def delete_collection(self):
        """Delete the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = None
            self.logger.info(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            self.logger.error(f"Error deleting collection: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.collection:
            self.initialize_collection()
        
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def reset_database(self):
        """Reset the entire database."""
        try:
            self.client.reset()
            self.logger.info("Database reset complete")
            self.collection = None
        except Exception as e:
            self.logger.error(f"Error resetting database: {e}")
            raise