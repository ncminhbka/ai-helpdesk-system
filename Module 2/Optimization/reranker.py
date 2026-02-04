import os
from datetime import datetime
from typing import List
from langchain_core.documents import Document
from flashrank import Ranker, RerankRequest
from langsmith import traceable

class FlashRankReranker:
    """
    Reranker using FlashRank - a lightweight, fast reranking model.
    No API key required.
    """
    
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2", top_n: int = 3):
        """
        Initialize FlashRank reranker.
        
        Args:
            model_name: FlashRank model to use
            top_n: Number of top documents to return after reranking
        """
        print(f"Initializing FlashRank with model: {model_name}")
        self.ranker = Ranker(model_name=model_name, cache_dir="./flashrank_cache")
        self.top_n = top_n
        
        print(f"FlashRank reranker initialized (top_n={top_n})")
    
    @traceable(run_type="retriever", name="FlashRank Reranking")
    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            
        Returns:
            Reranked list of top_n documents
        """
        if not documents:
            print("No documents to rerank")
            return []
        
        print(f"Reranking {len(documents)} documents...")
        
        # Prepare passages for FlashRank
        passages = []
        for i, doc in enumerate(documents):
            passages.append({
                "id": i,
                "text": doc.page_content,
                "meta": {
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page_label", "Unknown")
                }
            })
        
        # Create rerank request
        rerank_request = RerankRequest(query=query, passages=passages)
        
        # Perform reranking
        results = self.ranker.rerank(rerank_request)
        
        # Map results back to documents
        reranked_docs = []
        for result in results[:self.top_n]:
            original_idx = result["id"]
            doc = documents[original_idx]
            # Add rerank score to metadata
            doc.metadata["rerank_score"] = result["score"]
            doc.metadata["rerank_rank"] = len(reranked_docs) + 1
            reranked_docs.append(doc)
        
        print(f"Reranking complete. Returned top {len(reranked_docs)} documents.")
        return reranked_docs
