import os
from datetime import datetime
from typing import List
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langsmith import traceable

class HybridRetriever:
    """
    Hybrid retriever combining BM25 (sparse) and Vector (dense) retrieval
    using Reciprocal Rank Fusion (RRF) for merging results.
    """
    
    def __init__(self, documents: List[Document], k: int = 5, bm25_k: int = 10, vector_k: int = 10):
        """
        Initialize hybrid retriever.
        
        Args:
            documents: List of documents to index
            k: Number of final documents to return after fusion
            bm25_k: Number of documents to retrieve from BM25
            vector_k: Number of documents to retrieve from vector search
        """
        self.k = k
        self.bm25_k = bm25_k
        self.vector_k = vector_k
        
        # Initialize BM25 retriever
        print("Creating BM25 retriever...")
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = bm25_k
        
        # Initialize Vector retriever
        print("Creating vector store...")
        embeddings = OpenAIEmbeddings()
        self.vector_store = FAISS.from_documents(documents, embeddings)
        self.vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": vector_k})
        
        print(f"Hybrid retriever initialized (BM25 k={bm25_k}, Vector k={vector_k}, Final k={k})")
    
    @traceable(run_type="retriever", name="Hybrid Retrieval")
    def invoke(self, query: str) -> List[Document]:
        """
        Retrieve documents using hybrid search.
        
        Args:
            query: Search query
            
        Returns:
            List of retrieved documents after RRF fusion
        """
        # BM25 retrieval
        print(f"Retrieving with BM25 (k={self.bm25_k})...")
        bm25_docs = self.bm25_retriever.invoke(query)
        
        # Vector retrieval
        print(f"Retrieving with vector search (k={self.vector_k})...")
        vector_docs = self.vector_retriever.invoke(query)
        
        # Apply RRF fusion
        print("Applying Reciprocal Rank Fusion...")
        fused_docs = self._reciprocal_rank_fusion(
            query=query,
            bm25_docs=bm25_docs,
            vector_docs=vector_docs,
            k=self.k
        )
        
        return fused_docs
    
    @traceable(run_type="tool", name="Reciprocal Rank Fusion")
    def _reciprocal_rank_fusion(self, query: str, bm25_docs: List[Document], 
                                vector_docs: List[Document], k: int = 5) -> List[Document]:
        """
        Merge BM25 and vector search results using Reciprocal Rank Fusion.
        
        RRF formula: score(d) = sum(1 / (rank(d) + k)) for each retrieval method
        where k is a constant (typically 60)
        """
        rrf_k = 60  # RRF constant
        doc_scores = {}
        
        # Score BM25 results
        for rank, doc in enumerate(bm25_docs, start=1):
            doc_key = self._doc_key(doc)
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"doc": doc, "score": 0, "bm25_rank": None, "vector_rank": None}
            doc_scores[doc_key]["score"] += 1 / (rank + rrf_k)
            doc_scores[doc_key]["bm25_rank"] = rank
        
        # Score vector results
        for rank, doc in enumerate(vector_docs, start=1):
            doc_key = self._doc_key(doc)
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"doc": doc, "score": 0, "bm25_rank": None, "vector_rank": None}
            doc_scores[doc_key]["score"] += 1 / (rank + rrf_k)
            doc_scores[doc_key]["vector_rank"] = rank
        
        # Sort by RRF score and return top k
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
        
        # Add RRF score to metadata for debugging
        for item in sorted_docs[:k]:
            item["doc"].metadata["rrf_score"] = item["score"]
            item["doc"].metadata["bm25_rank"] = item["bm25_rank"]
            item["doc"].metadata["vector_rank"] = item["vector_rank"]
        
        return [item["doc"] for item in sorted_docs[:k]]
    
    def _doc_key(self, doc: Document) -> str:
        """Create a unique key for a document based on content and metadata."""
        source = doc.metadata.get('source', 'unknown')
        page = doc.metadata.get('page_label', 'unknown')
        content_snippet = doc.page_content[:100]  # First 100 chars as unique identifier
        return f"{source}_{page}_{hash(content_snippet)}"
