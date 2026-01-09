"""FAISS vector store management."""

import os
from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
import config


class VectorStoreManager:
    """Manages FAISS vector store for document retrieval."""
    
    def __init__(self, embeddings: Embeddings):
        """Initialize vector store manager.
        
        Args:
            embeddings: Embeddings model instance
        """
        self.embeddings = embeddings
        self.vector_store: Optional[FAISS] = None
        self._document_count = 0
    
    def create_or_load_store(self, force_new: bool = False) -> bool:
        """Create new vector store or load existing.
        
        Args:
            force_new: If True, create new store even if one exists
            
        Returns:
            True if store was loaded, False if new store created
        """
        if not force_new and os.path.exists(config.VECTOR_STORE_PATH):
            try:
                self.vector_store = FAISS.load_local(
                    config.VECTOR_STORE_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True  # Local use only
                )
                return True
            except Exception as e:
                print(f"Warning: Could not load existing store: {e}")
        
        # Create new empty store
        self.vector_store = None
        return False
    
    def add_documents(self, documents: List[Document]) -> int:
        """Add documents to vector store.
        
        Args:
            documents: List of document chunks to add
            
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        if self.vector_store is None:
            # Create new store with first batch
            self.vector_store = FAISS.from_documents(
                documents,
                self.embeddings
            )
        else:
            # Add to existing store
            self.vector_store.add_documents(documents)
        
        self._document_count += len(documents)
        return len(documents)
    
    def save(self) -> bool:
        """Save vector store to disk.
        
        Returns:
            True if save successful
        """
        if self.vector_store is None:
            return False
        
        try:
            os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)
            self.vector_store.save_local(config.VECTOR_STORE_PATH)
            return True
        except Exception as e:
            print(f"Error saving vector store: {e}")
            return False
    
    def get_retriever(self, search_kwargs: Optional[Dict[str, Any]] = None) -> VectorStoreRetriever:
        """Get retriever with MMR search.
        
        Args:
            search_kwargs: Additional search parameters
            
        Returns:
            Configured retriever
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        default_kwargs = {
            "k": config.TOP_K_RETRIEVAL,
            "fetch_k": config.TOP_K_RETRIEVAL * 2,  # Fetch more for MMR diversity
            "lambda_mult": 1.0 - config.MMR_DIVERSITY,  # Convert to MMR lambda param
        }
        
        if search_kwargs:
            default_kwargs.update(search_kwargs)
        
        return self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=default_kwargs
        )
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Direct similarity search.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            return []
        
        return self.vector_store.similarity_search(query, k=k)
    
    @property
    def document_count(self) -> int:
        """Get total number of documents in store."""
        return self._document_count
    
    def clear(self):
        """Clear the vector store."""
        self.vector_store = None
        self._document_count = 0
        
        if os.path.exists(config.VECTOR_STORE_PATH):
            import shutil
            shutil.rmtree(config.VECTOR_STORE_PATH)